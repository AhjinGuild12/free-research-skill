"""Read-only linter for free-research run notes.

Classify each markdown file from its frontmatter, then report version-2
problems as errors and legacy problems as warnings. Expiry is a status
column. This script never writes and never fetches.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

CLOSING_LINE = "your agent is only as good as the worst source it believed."
CANONICAL_LABELS = (
    "confirmed with dissent attached",
    "unconfirmed",
    "confirmed",
)
KEY_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+){1,3}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
FINDING_RE = re.compile(
    r"^-\s+(confirmed with dissent attached|unconfirmed|confirmed):\s?(.*)$"
)
# Scheme-prefixed URLs do not require "//". http and https stay; every other scheme is an error.
URL_RE = re.compile(r"^(?:-\s+)?([A-Za-z][A-Za-z0-9+.-]*:\S+)$")
MARKDOWN_URL_RE = re.compile(r"\[[^\]\n]*\]\(<?([A-Za-z][A-Za-z0-9+.-]*:[^\s)>]+)>?(?:\s+[^)]+)?\)")
# Opaque bullet destinations need a known scheme to distinguish them from labels.
URL_SCHEMES = frozenset({"http", "https", "ftp", "ftps", "data", "file", "mailto", "javascript", "tel", "urn"})
OBJECTION_RE = re.compile(r"^(.*?)\s*— objection:\s?(.*)$")
LABEL_PREFIX_RE = re.compile(r"^([^:]+):\s*\S")
BARE_LABEL_RE = re.compile(
    r"^F\d+[a-z]?\s+(confirmed with dissent attached|unconfirmed|confirmed)\s*$"
)
F_LINE_RE = re.compile(r"^F\d+[a-z]?\s+(.*)$")
PREFIX_LABEL_RE = re.compile(
    r"^(confirmed with dissent attached|unconfirmed|confirmed)(?::|\.)\s*\S"
)
SUFFIX_LABEL_RE = re.compile(
    r":\s*(confirmed with dissent attached|unconfirmed|confirmed)\s*$"
)
ALTERNATE_CLOSING_RE = re.compile(r"(?i)^closing line:")
NOT_CONFIRMED_RE = re.compile(r":\s*not confirmed\b", re.IGNORECASE)
FILENAME_RE_SUFFIX = r"--[0-9a-f]{8}(?:-[1-9][0-9]*)?\.md"

KEY_MAX_BYTES = 48
FILENAME_MAX_V2 = 67
FILENAME_MAX_LEGACY = 100
SCHEMA_V2 = "2"
MARKER = "run-note"
STOPWORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "for",
        "of",
        "and",
        "or",
        "to",
        "with",
        "vs",
        "on",
        "in",
        "by",
        "from",
        "whose",
        "that",
        "this",
        "also",
        "their",
    }
)


@dataclass(frozen=True)
class Issue:
    severity: str
    code: str
    detail: str


@dataclass
class FileResult:
    filename: str
    classification: str
    status: str
    issues: list[Issue] = field(default_factory=list)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only linter for free-research run notes.")
    parser.add_argument("folder", type=Path, help="runs folder to check")
    args = parser.parse_args(argv)
    folder = args.folder
    if not folder.is_dir():
        print(f"not a directory: {folder}", file=sys.stderr)
        return 2
    results = lint_folder(folder)
    sys.stdout.write(render(results))
    return exit_code(results)


def lint_folder(folder: Path, today: date | None = None) -> list[FileResult]:
    current_day = today or date.today()
    paths = sorted(
        (path for path in folder.iterdir() if path.is_file() and path.suffix == ".md"),
        key=lambda path: path.name,
    )
    return [lint_text(path.name, path.read_text(encoding="utf-8"), current_day) for path in paths]


def lint_text(filename: str, text: str, today: date) -> FileResult:
    fields, body = parse_frontmatter(text)
    kind = classify(fields)
    if kind == "v2" and body is None:
        return FileResult(
            filename,
            "v2",
            "n/a",
            [
                Issue(
                    "error",
                    "malformed-frontmatter",
                    "frontmatter is missing its closing delimiter",
                )
            ],
        )
    if kind == "skipped":
        return FileResult(filename, "skipped", "n/a", [Issue("skip", "skipped", "not a run note")])
    if fields is None:
        return FileResult(filename, "skipped", "n/a", [Issue("skip", "skipped", "not a run note")])
    if kind == "unsupported":
        schema = fields.get("schema", "")
        return FileResult(
            filename,
            "unsupported",
            expiry_status(fields, today),
            [Issue("error", "unsupported-schema", f"schema {schema} is not supported")],
        )
    if body is None:
        return FileResult(filename, "skipped", "n/a", [Issue("skip", "skipped", "not a run note")])
    if kind == "legacy":
        return lint_legacy(filename, fields, body, today)
    return lint_v2(filename, fields, body, today)


def classify(fields: dict[str, str] | None) -> str:
    """Schema wins over marker. A schema 2 file stays version 2 after it loses its marker."""
    if not fields or "schema" not in fields and fields.get("marker") != MARKER:
        return "skipped"
    if "schema" in fields:
        if fields["schema"] == SCHEMA_V2:
            return "v2"
        return "unsupported"
    return "legacy"


def parse_frontmatter(text: str) -> tuple[dict[str, str] | None, str | None]:
    """Preserve fields for schema classification; None body means an unclosed block."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, text
    fields: dict[str, str] = {}
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return fields, "\n".join(lines[index + 1 :])
        if not line.strip() or ":" not in line:
            continue
        name, value = line.split(":", 1)
        fields[name.strip()] = unquote(value.strip())
    return fields, None


def lint_v2(filename: str, fields: dict[str, str], body: str, today: date) -> FileResult:
    issues: list[Issue] = []
    issues.extend(frontmatter_issues(fields))
    issues.extend(filename_issues(filename, fields.get("key", "")))
    issues.extend(body_issues(body))
    return FileResult(filename, "v2", expiry_status(fields, today), issues)


def frontmatter_issues(fields: dict[str, str]) -> list[Issue]:
    issues: list[Issue] = []
    if fields.get("marker") != MARKER:
        issues.append(Issue("error", "missing-marker", "marker must be run-note"))
    issues.extend(key_issues(fields))
    issues.extend(topic_issues(fields))
    issues.extend(date_issues(fields, "run_date", "missing-run-date", "invalid-run-date"))
    issues.extend(date_issues(fields, "expires", "missing-expires", "invalid-expires"))
    return issues


def key_issues(fields: dict[str, str]) -> list[Issue]:
    if "key" not in fields:
        return [Issue("error", "missing-key", "key is missing")]
    if not valid_key(fields["key"]):
        return [
            Issue(
                "error",
                "invalid-key",
                "key must be 2-4 lowercase hyphenated words and at most 48 bytes",
            )
        ]
    return []


def topic_issues(fields: dict[str, str]) -> list[Issue]:
    if "topic" not in fields:
        return [Issue("error", "missing-topic", "topic is missing")]
    if fields["topic"].strip() == "":
        return [Issue("error", "empty-topic", "topic is empty")]
    return []


def date_issues(fields: dict[str, str], name: str, missing_code: str, invalid_code: str) -> list[Issue]:
    if name not in fields:
        return [Issue("error", missing_code, f"{name} is missing")]
    if parse_date(fields[name]) is None:
        return [Issue("error", invalid_code, f"{name} is not a YYYY-MM-DD date")]
    return []


def filename_issues(filename: str, key: str) -> list[Issue]:
    issues: list[Issue] = []
    pattern = re.escape(key) + FILENAME_RE_SUFFIX if key else None
    if pattern is None or re.fullmatch(pattern, filename) is None:
        issues.append(Issue("error", "filename-mismatch", "filename must be <key>--<8 hex>[-<n>].md"))
    if len(filename.encode("utf-8")) > FILENAME_MAX_V2:
        issues.append(Issue("error", "filename-too-long", "filename is over 67 bytes"))
    return issues


def body_issues(body: str) -> list[Issue]:
    issues: list[Issue] = []
    content_lines = [line.strip() for line in body.splitlines() if line.strip()]
    if not content_lines or content_lines[-1] != CLOSING_LINE:
        issues.append(Issue("error", "missing-closing-line", "closing line is missing"))
    for line in content_lines:
        if line == CLOSING_LINE:
            continue
        for markdown_url in MARKDOWN_URL_RE.finditer(line):
            issues.extend(url_issues(markdown_url.group(1)))
        url_match = URL_RE.fullmatch(line)
        if url_match and FINDING_RE.fullmatch(line) is None:
            url = url_match.group(1)
            scheme = url.split(":", 1)[0].lower()
            if not line.startswith("-") or scheme in URL_SCHEMES or "://" in url:
                issues.extend(url_issues(url))
                continue
        if line.startswith("-"):
            issues.extend(finding_issues(line))
    return issues


def url_issues(url: str) -> list[Issue]:
    scheme = url.split(":", 1)[0].lower()
    if scheme in {"http", "https"}:
        return []
    return [Issue("error", "non-http-url", url)]


def finding_issues(line: str) -> list[Issue]:
    match = FINDING_RE.fullmatch(line)
    if match is None:
        return [
            Issue(
                "error",
                "invalid-label",
                "finding label is not confirmed, unconfirmed, or confirmed with dissent attached",
            )
        ]
    label, claim = match.group(1), match.group(2)
    issues: list[Issue] = []
    objection = None
    if label == "confirmed with dissent attached":
        objection_match = OBJECTION_RE.fullmatch(claim)
        if objection_match is None:
            issues.append(Issue("error", "missing-objection", "dissent finding has no objection"))
            claim = claim.strip()
        else:
            claim = objection_match.group(1).strip()
            objection = objection_match.group(2).strip()
    else:
        claim = claim.strip()
    if claim == "":
        issues.append(Issue("error", "empty-claim", "finding claim is empty"))
    if objection == "":
        issues.append(Issue("error", "empty-objection", "dissent objection is empty"))
    return issues


def lint_legacy(filename: str, fields: dict[str, str], body: str, today: date) -> FileResult:
    issues: list[Issue] = []
    if len(filename.encode("utf-8")) > FILENAME_MAX_LEGACY:
        issues.append(Issue("warning", "filename-too-long", "filename is over 100 bytes"))
    lines = [line.strip() for line in body.splitlines() if line.strip()]
    has_closing_line = any(line == CLOSING_LINE for line in lines)
    if not has_closing_line and any(ALTERNATE_CLOSING_RE.match(line) for line in lines):
        issues.append(
            Issue("warning", "alternate-closing-line", "closing line is not the canonical sentence")
        )
    for line in lines:
        if line == CLOSING_LINE or URL_RE.fullmatch(line):
            continue
        if BARE_LABEL_RE.fullmatch(line):
            issues.append(Issue("warning", "bare-label", line))
            continue
        if noncanonical_label(line):
            issues.append(Issue("warning", "noncanonical-label", line))
    issues.append(Issue("warning", "suggest-key", suggest_key(filename)))
    return FileResult(filename, "legacy", expiry_status(fields, today), issues)


def noncanonical_label(line: str) -> bool:
    if PREFIX_LABEL_RE.match(line):
        return False
    if line.lower().startswith("labels:"):
        tokens = [token.strip() for token in line.split(":", 1)[1].split(",") if token.strip()]
        return any(token not in CANONICAL_LABELS for token in tokens)
    f_match = F_LINE_RE.fullmatch(line)
    if f_match:
        return split_canonical(f_match.group(1)) is None
    if SUFFIX_LABEL_RE.search(line):
        return False
    if line.startswith("- "):
        return split_canonical(line[2:].strip()) is None
    if unknown_label_prefix(line) is not None:
        return True
    return NOT_CONFIRMED_RE.search(line) is not None


def unknown_label_prefix(line: str) -> str | None:
    """A '<label>: <claim>' prefix that is not one of the three canonical labels."""
    if ALTERNATE_CLOSING_RE.match(line):
        return None
    match = LABEL_PREFIX_RE.match(line)
    if match is None:
        return None
    prefix = match.group(1).strip()
    if split_canonical(prefix) is not None:
        return None
    return prefix


def split_canonical(text: str) -> str | None:
    for label in CANONICAL_LABELS:
        if text == label or text.startswith(label + ":") or text.startswith(label + "."):
            return label
    return None


def suggest_key(filename: str) -> str:
    stem = filename[:-3] if filename.lower().endswith(".md") else filename
    words = [word for word in (letters_only(piece) for piece in stem.split("-")) if word]
    picked = [word for word in words if word not in STOPWORDS]
    if len(picked) < 2:
        picked = words
    if len(picked) < 2:
        picked = ["legacy", "note"]
    key = "-".join(picked[:4])
    while len(key.encode("utf-8")) > KEY_MAX_BYTES and "-" in key:
        key = key.rsplit("-", 1)[0]
    if len(key.encode("utf-8")) > KEY_MAX_BYTES:
        key = key.encode("utf-8")[:KEY_MAX_BYTES].decode("ascii").strip("-")
    if "-" not in key:
        trimmed = key[:42].strip("-") or "legacy"
        key = f"{trimmed}-note"
    return key


def letters_only(piece: str) -> str:
    return "".join(character for character in piece.lower() if "a" <= character <= "z")


def valid_key(key: str) -> bool:
    if len(key.encode("utf-8")) > KEY_MAX_BYTES:
        return False
    return KEY_RE.fullmatch(key) is not None


def parse_date(value: str) -> date | None:
    if DATE_RE.fullmatch(value) is None:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def expiry_status(fields: dict[str, str], today: date) -> str:
    """A missing or non-date expires counts as expired, and expired is not a failure."""
    parsed = parse_date(fields.get("expires", ""))
    if parsed is None or parsed < today:
        return "expired"
    return "current"


def render(results: list[FileResult]) -> str:
    rows = ["status\tseverity\tcode\tfile\tdetail"]
    for result in results:
        if not result.issues:
            rows.append(f"{result.status}\tok\t-\t{result.filename}\t-")
            continue
        for issue in result.issues:
            detail = issue.detail.replace("\t", " ").replace("\n", " ")
            rows.append(f"{result.status}\t{issue.severity}\t{issue.code}\t{result.filename}\t{detail}")
    return "\n".join(rows) + "\n"


def exit_code(results: list[FileResult]) -> int:
    for result in results:
        for issue in result.issues:
            if issue.severity == "error":
                return 1
    return 0


def unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


if __name__ == "__main__":
    sys.exit(main())
