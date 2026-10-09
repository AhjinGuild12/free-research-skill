"""Read-only run-note linter. Version-2 notes error. Legacy notes warn."""

from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import lint_run_notes  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures" / "run-notes"
CLOSING_LINE = "your agent is only as good as the worst source it believed."
VALID_NAME = "ezzybills-xero-integration--a1b2c3d4.md"
DISSENT_NAME = "ezzybills-xero-integration--b2c3d4e5.md"


def _codes(result: lint_run_notes.FileResult) -> list[str]:
    return [issue.code for issue in result.issues]


def _errors(result: lint_run_notes.FileResult) -> list[str]:
    return [issue.code for issue in result.issues if issue.severity == "error"]


class TestLintRunNotes(unittest.TestCase):
    def test_valid_v2_fixture_has_no_findings_and_exits_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            shutil.copy(FIXTURES / VALID_NAME, folder / VALID_NAME)
            code, output = _run(folder)
            result = lint_run_notes.lint_folder(folder)[0]
        self.assertEqual(0, code)
        self.assertNotIn("\terror\t", output)
        self.assertNotIn("\twarning\t", output)
        self.assertEqual("v2", result.classification)
        self.assertEqual("current", result.status)
        self.assertEqual([], result.issues)

    def test_dissent_without_objection_is_one_error(self) -> None:
        result, code = _lint_fixture(DISSENT_NAME)
        self.assertEqual(["missing-objection"], _errors(result))
        self.assertEqual(1, code)

    def test_empty_claim_bad_key_and_bad_run_date_are_named_errors(self) -> None:
        cases = (
            ("empty-claim", {"findings": ["- confirmed:"]}),
            ("invalid-key", {"key": "Xero_API"}),
            ("invalid-run-date", {"run_date": "soon"}),
        )
        for expected, overrides in cases:
            with self.subTest(expected=expected):
                result, code = _lint_v2(**overrides)
                self.assertEqual([expected], _errors(result))
                self.assertEqual(1, code)

    def test_schema_3_is_unsupported_schema(self) -> None:
        text = _v2_text(schema="3")
        result, code = _lint_named("ezzybills-xero-integration--c3d4e5f6.md", text)
        self.assertEqual("unsupported", result.classification)
        self.assertEqual(["unsupported-schema"], _errors(result))
        self.assertEqual(1, code)

    def test_unclosed_schema_3_frontmatter_is_unsupported_schema(self) -> None:
        result, code = _lint_named(VALID_NAME, "---\nmarker: run-note\nschema: 3\n")
        self.assertEqual("unsupported", result.classification)
        self.assertEqual(["unsupported-schema"], _errors(result))
        self.assertEqual(1, code)

    def test_markdown_link_destinations_reject_non_http_schemes(self) -> None:
        for url in ("data:text/plain,hello", "mailto:hello@example.com", "custom:payload"):
            with self.subTest(url=url):
                result, code = _lint_v2(urls=[f"[source]({url})"])
                self.assertEqual(["non-http-url"], _errors(result))
                self.assertEqual(1, code)
        result, code = _lint_v2(urls=["[source](https://example.com)"])
        self.assertEqual([], _errors(result))
        self.assertEqual(0, code)

    def test_unknown_label_without_space_is_invalid_label(self) -> None:
        result, code = _lint_v2(findings=["- nope:claim"])
        self.assertEqual(["invalid-label"], _errors(result))
        self.assertEqual(1, code)

    def test_legacy_bare_label_warns_and_exits_zero(self) -> None:
        result, code = _lint_fixture("legacy-bare-label.md")
        self.assertEqual(0, code)
        self.assertIn("bare-label", _codes(result))
        self.assertEqual([], _errors(result))
        self.assertEqual("legacy", result.classification)

    def test_plain_markdown_is_skipped_not_failed(self) -> None:
        result, code = _lint_named("scratch.md", "# Notes\n\nNot a run note.\n")
        self.assertEqual(0, code)
        self.assertEqual("skipped", result.classification)
        self.assertEqual(["skipped"], _codes(result))
        self.assertEqual("skip", result.issues[0].severity)
        self.assertEqual([], _errors(result))

    def test_schema_2_without_marker_is_missing_marker_not_skip(self) -> None:
        text = _v2_text(omit=("marker",))
        result, code = _lint_named("ezzybills-xero-integration--d4e5f6a7.md", text)
        self.assertEqual("v2", result.classification)
        self.assertNotEqual("skipped", result.classification)
        self.assertEqual(["missing-marker"], _errors(result))
        self.assertEqual(1, code)

    def test_lint_does_not_change_fixture_mtime_or_content(self) -> None:
        before = {
            path: (path.stat().st_mtime_ns, hashlib.sha256(path.read_bytes()).hexdigest())
            for path in FIXTURES.glob("*.md")
        }
        names_before = sorted(path.name for path in FIXTURES.iterdir())
        code, _output = _run(FIXTURES)
        after = {
            path: (path.stat().st_mtime_ns, hashlib.sha256(path.read_bytes()).hexdigest())
            for path in FIXTURES.glob("*.md")
        }
        names_after = sorted(path.name for path in FIXTURES.iterdir())
        self.assertEqual(before, after)
        self.assertEqual(names_before, names_after)
        self.assertEqual(1, code)

    def test_expired_is_status_not_failure(self) -> None:
        result, code = _lint_v2(expires="2000-01-01")
        self.assertEqual(0, code)
        self.assertEqual("expired", result.status)
        self.assertEqual([], result.issues)

    def test_remaining_v2_errors_are_named(self) -> None:
        long_key = "abcdefghijkl-abcdefghijk-abcdefghijk-abcdefghijk"
        self.assertEqual(48, len(long_key.encode("utf-8")))
        too_long_name = f"{long_key}--01234567-100000.md"
        self.assertGreater(len(too_long_name.encode("utf-8")), 67)
        cases = (
            ("empty-objection", {"findings": ["- confirmed with dissent attached: X — objection:"]}),
            ("invalid-label", {"findings": ["- nope: a claim"]}),
            ("non-http-url", {"urls": ["ftp://example.com/file"]}),
            ("missing-closing-line", {"closing": ""}),
            ("filename-mismatch", {"filename": "notes.md"}),
            ("filename-too-long", {"key": long_key, "filename": too_long_name}),
            ("invalid-key", {"key": long_key + "x", "filename": f"{long_key}x--01234567.md"}),
            ("empty-topic", {"topic": ""}),
            ("invalid-expires", {"expires": "2026-02-31"}),
            ("missing-key", {"omit": ("key",), "filename": "notes.md"}),
        )
        for expected, overrides in cases:
            with self.subTest(expected=expected):
                result, code = _lint_v2(**overrides)
                self.assertIn(expected, _errors(result))
                self.assertEqual(1, code)

    def test_legacy_noncanonical_alternate_closing_and_long_name(self) -> None:
        noncanonical, code = _lint_named(
            "legacy-labels.md",
            _legacy_text("Labels: accessory-approval-confirmed, cabinet-ex-gst-only\n"),
        )
        self.assertEqual(0, code)
        self.assertIn("noncanonical-label", _codes(noncanonical))

        alternate, code = _lint_named(
            "legacy-close.md",
            _legacy_text("confirmed: A claim.\nClosing line: run note only, not proof.\n", closing=False),
        )
        self.assertEqual(0, code)
        self.assertIn("alternate-closing-line", _codes(alternate))

        long_name = "b" * 98 + ".md"
        self.assertGreater(len(long_name.encode("utf-8")), 100)
        long_file, code = _lint_named(long_name, _legacy_text("confirmed: A claim.\n"))
        self.assertEqual(0, code)
        self.assertIn("filename-too-long", _codes(long_file))
        self.assertEqual("warning", _issue(long_file, "filename-too-long").severity)

    def test_legacy_readable_fixture_suggests_a_key_without_bare_label(self) -> None:
        result, code = _lint_fixture("legacy-readable.md")
        self.assertEqual(0, code)
        self.assertEqual(["suggest-key"], _codes(result))
        self.assertEqual("legacy-readable", result.issues[0].detail)

    def test_bare_f_suffix_warns_and_claimed_f_line_does_not(self) -> None:
        bare, _code = _lint_named("legacy-f5a.md", _legacy_text("F5a confirmed\n"))
        self.assertIn("bare-label", _codes(bare))
        claimed, _code = _lint_named(
            "legacy-claimed.md",
            _legacy_text("F1 confirmed. The pricing page states no keyword count.\n"),
        )
        self.assertNotIn("bare-label", _codes(claimed))
        self.assertNotIn("noncanonical-label", _codes(claimed))

    def test_suggest_key_from_slug(self) -> None:
        self.assertEqual(
            "auckland-nz-law-firms",
            lint_run_notes.suggest_key("auckland-nz-law-firms-callback-leak.md"),
        )

    def test_data_scheme_url_is_non_http_url(self) -> None:
        result, code = _lint_v2(urls=["data:text/plain,hello"])
        self.assertEqual(["non-http-url"], _errors(result))
        self.assertEqual(1, code)
        finding, finding_code = _lint_v2(findings=["- confirmed:OneWord"])
        self.assertEqual([], _errors(finding))
        self.assertEqual(0, finding_code)

    def test_unclosed_schema_2_frontmatter_is_an_error(self) -> None:
        text = (
            "---\n"
            "marker: run-note\n"
            "schema: 2\n"
            "key: ezzybills-xero-integration\n"
            "topic: Can a finance team build a custom EzzyBills to Xero integration\n"
            "run_date: 2026-10-01\n"
            "expires: 2099-01-01\n"
            "- confirmed: EzzyBills documents a Xero connector.\n"
            "https://example.com/xero\n"
            f"{CLOSING_LINE}\n"
        )
        result, code = _lint_named("ezzybills-xero-integration--a1b2c3d4.md", text)
        self.assertNotEqual("skipped", result.classification)
        self.assertEqual(["malformed-frontmatter"], _errors(result))
        self.assertEqual(1, code)

    def test_whitespace_only_topic_is_empty_topic(self) -> None:
        result, code = _lint_v2(topic='"   "')
        self.assertEqual(["empty-topic"], _errors(result))
        self.assertEqual(1, code)

    def test_legacy_unknown_label_prefix_warns(self) -> None:
        result, code = _lint_named("legacy-verified.md", _legacy_text("verified: A claim.\n"))
        self.assertEqual(0, code)
        self.assertIn("noncanonical-label", _codes(result))
        self.assertEqual([], _errors(result))

    def test_dissent_marker_without_claim_is_empty_claim(self) -> None:
        result, code = _lint_v2(
            findings=["- confirmed with dissent attached: — objection: counterevidence"]
        )
        self.assertEqual(["empty-claim"], _errors(result))
        self.assertNotIn("missing-objection", _errors(result))
        self.assertEqual(1, code)

    def test_key_words_may_include_digits(self) -> None:
        valid, valid_code = _lint_v2(key="microsoft-ms-102")
        self.assertEqual([], _errors(valid))
        self.assertEqual(0, valid_code)
        invalid, invalid_code = _lint_v2(key="Xero_API")
        self.assertEqual(["invalid-key"], _errors(invalid))
        self.assertEqual(1, invalid_code)

    def test_vault_notes_example_validates_through_lint_text(self) -> None:
        filename, text = _vault_note_example()
        self.assertTrue(text.startswith("---\n"), text)
        self.assertIn("\n---\n", text)
        result = lint_run_notes.lint_text(filename, text, date(2026, 10, 1))
        self.assertEqual("v2", result.classification)
        self.assertNotEqual("skipped", result.classification)
        self.assertEqual([], result.issues)
        self.assertEqual("current", result.status)
        fields, _body = lint_run_notes.parse_frontmatter(text)
        assert fields is not None
        normalized = re.sub(r"\s+", " ", fields["topic"].strip().lower())
        digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:8]
        self.assertEqual(f"{fields['key']}--{digest}.md", filename)
        run_date = date.fromisoformat(fields["run_date"])
        expires = date.fromisoformat(fields["expires"])
        span = (expires - run_date).days
        self.assertIn(span, (7, 30, 90))
        notes = (ROOT / "skills" / "free-research" / "references" / "vault-notes.md").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "7 days for a news intent, 90 days when the confirming body is a stable official doc, otherwise 30 days",
            notes,
        )
        self.assertIn(
            "This example is not a news intent, and the confirming body is not a stable official doc, so it uses the 30-day bucket.",
            notes,
        )
        self.assertEqual(timedelta(days=30), expires - run_date)
        self.assertNotEqual(date(2099, 1, 1), expires)

    def test_topic_quotes_and_newlines_round_trip(self) -> None:
        samples = (
            '"Can Xero sync?"',
            "one\ntwo",
            'he said "hi"\nthen \\ left',
            "  spaced  ",
            "plain topic",
            "Can Xero: sync?",
            "",
            "line\r\nbreak",
            'quote " and newline\n',
        )
        for topic in samples:
            with self.subTest(topic=topic):
                encoded = lint_run_notes.encode_topic(topic)
                self.assertNotIn("\n", encoded)
                self.assertNotIn("\r", encoded)
                self.assertEqual(topic, lint_run_notes.decode_topic(encoded))
                fields, _body = lint_run_notes.parse_frontmatter(_v2_text(topic=encoded))
                self.assertIsNotNone(fields)
                assert fields is not None
                self.assertEqual(topic, fields["topic"])

    def test_encoded_quoted_and_newline_topics_validate(self) -> None:
        topics = ('"Can Xero sync?"', "Can Xero sync?\nSecond line")
        for topic in topics:
            with self.subTest(topic=topic):
                encoded = lint_run_notes.encode_topic(topic)
                text = _v2_text(topic=encoded)
                result = lint_run_notes.lint_text(VALID_NAME, text, date(2026, 10, 1))
                self.assertEqual("v2", result.classification)
                self.assertNotEqual("skipped", result.classification)
                self.assertEqual([], result.issues)
                fields, _body = lint_run_notes.parse_frontmatter(text)
                assert fields is not None
                self.assertEqual(topic, fields["topic"])
        naive = '"Can Xero sync?"'
        self.assertNotEqual(naive, lint_run_notes.decode_topic(naive))
        self.assertEqual(naive, lint_run_notes.decode_topic(lint_run_notes.encode_topic(naive)))

    def test_script_entrypoint_exits_zero_for_valid_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            shutil.copy(FIXTURES / VALID_NAME, folder / VALID_NAME)
            completed = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "lint_run_notes.py"), str(folder)],
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(0, completed.returncode)
        self.assertIn("status\tseverity\tcode\tfile\tdetail", completed.stdout)
        self.assertIn("current\tok\t-", completed.stdout)
        self.assertEqual("", completed.stderr)


def _run(folder: Path) -> tuple[int, str]:
    from io import StringIO
    from contextlib import redirect_stdout

    buffer = StringIO()
    with redirect_stdout(buffer):
        code = lint_run_notes.main([str(folder)])
    return code, buffer.getvalue()


def _lint_fixture(name: str) -> tuple[lint_run_notes.FileResult, int]:
    with tempfile.TemporaryDirectory() as tmp:
        folder = Path(tmp)
        shutil.copy(FIXTURES / name, folder / name)
        code, _output = _run(folder)
        result = lint_run_notes.lint_folder(folder)[0]
    return result, code


def _lint_named(name: str, text: str) -> tuple[lint_run_notes.FileResult, int]:
    with tempfile.TemporaryDirectory() as tmp:
        folder = Path(tmp)
        (folder / name).write_text(text, encoding="utf-8")
        code, _output = _run(folder)
        result = lint_run_notes.lint_folder(folder)[0]
    return result, code


def _lint_v2(**overrides: object) -> tuple[lint_run_notes.FileResult, int]:
    filename = str(overrides.pop("filename", "")) or _filename_for(overrides)
    text = _v2_text(**overrides)
    return _lint_named(filename, text)


def _filename_for(overrides: dict[str, object]) -> str:
    key = str(overrides.get("key", "ezzybills-xero-integration"))
    return f"{key}--a1b2c3d4.md"


def _v2_text(**overrides: object) -> str:
    omit = set(overrides.get("omit", ()))
    key = overrides.get("key", "ezzybills-xero-integration")
    topic = overrides.get("topic", "Can a finance team build a custom EzzyBills to Xero integration")
    run_date = overrides.get("run_date", "2026-10-01")
    expires = overrides.get("expires", "2099-01-01")
    marker = overrides.get("marker", "run-note")
    schema = overrides.get("schema", "2")
    findings = list(overrides.get("findings", ["- confirmed: EzzyBills documents a Xero connector."]))
    urls = list(overrides.get("urls", ["https://example.com/xero"]))
    closing = CLOSING_LINE if "closing" not in overrides else str(overrides["closing"])
    fields = []
    if "marker" not in omit:
        fields.append(f"marker: {marker}")
    if "schema" not in omit:
        fields.append(f"schema: {schema}")
    if "key" not in omit:
        fields.append(f"key: {key}")
    if "topic" not in omit:
        fields.append(f"topic: {topic}")
    if "run_date" not in omit:
        fields.append(f"run_date: {run_date}")
    if "expires" not in omit:
        fields.append(f"expires: {expires}")
    body = list(findings) + list(urls)
    if closing:
        body.append(closing)
    return "---\n" + "\n".join(str(field) for field in fields) + "\n---\n" + "\n".join(body) + "\n"


def _vault_note_example() -> tuple[str, str]:
    notes = (ROOT / "skills" / "free-research" / "references" / "vault-notes.md").read_text(
        encoding="utf-8"
    )
    match = re.search(r"filename `([^`]+\.md)`:\n\n```run-note\n(.*?)\n```", notes, re.DOTALL)
    if match is None:
        raise AssertionError("vault-notes.md has no delimited run-note example")
    return match.group(1), match.group(2) + "\n"


def _legacy_text(body: str, *, closing: bool = True) -> str:
    tail = CLOSING_LINE + "\n" if closing else ""
    return f"---\nexpires: 2099-01-01\nmarker: run-note\n---\n{body}{tail}"


def _issue(result: lint_run_notes.FileResult, code: str) -> lint_run_notes.Issue:
    for issue in result.issues:
        if issue.code == code:
            return issue
    raise AssertionError(code)


if __name__ == "__main__":
    unittest.main()
