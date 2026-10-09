"""Skill-local run-note codec and exclusive writer. Stdlib only.

The repository linter imports this file. A skill-only install still has it,
because it lives under the skill directory next to SKILL.md.
"""

from __future__ import annotations

import argparse
import errno
import hashlib
import json
import os
import re
import secrets
import stat
import sys
from datetime import datetime
from pathlib import Path

CLOSING_LINE = "your agent is only as good as the worst source it believed."
KEY_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+){1,3}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TOKEN_RE = re.compile(r"^[0-9a-f]{8,64}$")
FILENAME_SUFFIX_RE = r"(?:-[1-9][0-9]*)?\.md$"
KEY_MAX_BYTES = 48
FILENAME_MAX_BYTES = 67
MARKER = "run-note"
SCHEMA_V2 = "2"
RUNS_DIRNAME = "runs"

# Every character str.splitlines() treats as a boundary. JSON leaves the last
# three raw when ensure_ascii is false, and the frontmatter parser must not
# split a topic on them either.
SPLITLINES_BREAKS = frozenset(
    {
        "\n",
        "\r",
        "\v",
        "\f",
        "\x1c",
        "\x1d",
        "\x1e",
        "\x85",
        "\u2028",
        "\u2029",
    }
)
_JSON_EXTRA_ESCAPES = {
    "\u0085": "\\u0085",
    "\u2028": "\\u2028",
    "\u2029": "\\u2029",
}
_OPEN_FLAGS = os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_WRONLY


class WriteError(Exception):
    """A refused write. The message is safe to print: it has no vault path."""


def encode_topic(topic: str) -> str:
    """Return the one-line value written after ``topic: ``.

    Plain topics are unchanged. A topic that is empty, has leading or trailing
    whitespace, or contains a double quote, a backslash, or a line break is one
    JSON string. Line breaks are every character ``str.splitlines()`` splits on.
    ``json.dumps`` leaves U+0085, U+2028, and U+2029 raw; those are escaped so
    the stored value stays one line. ``decode_topic`` is the inverse.
    """
    if _topic_is_plain(topic):
        return topic
    encoded = json.dumps(topic, ensure_ascii=False)
    for character, escape in _JSON_EXTRA_ESCAPES.items():
        encoded = encoded.replace(character, escape)
    if any(character in encoded for character in SPLITLINES_BREAKS):
        raise RuntimeError("encoded topic still contains a line break")
    return encoded


def decode_topic(raw: str) -> str:
    """Inverse of ``encode_topic``. A JSON string is unescaped; other text stays literal."""
    value = raw.strip()
    if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError:
            return value
        if isinstance(decoded, str):
            return decoded
    return value


def split_record_lines(text: str) -> list[str]:
    """Split on U+000A and U+000D only.

    ``str.splitlines()`` also breaks on U+000B, U+000C, U+001C, U+001D, U+001E,
    U+0085, U+2028, and U+2029. The codec escapes those. A stored topic that
    still contains one stays one frontmatter field.
    """
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    if normalized == "":
        return []
    if normalized.endswith("\n"):
        normalized = normalized[:-1]
    return normalized.split("\n")


def parse_frontmatter(text: str) -> tuple[dict[str, str] | None, str | None]:
    """Preserve fields for schema classification; None body means an unclosed block."""
    lines = split_record_lines(text)
    if not lines or lines[0].strip() != "---":
        return None, text
    fields: dict[str, str] = {}
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return fields, "\n".join(lines[index + 1 :])
        if not line.strip() or ":" not in line:
            continue
        name, value = line.split(":", 1)
        field_name = name.strip()
        raw_value = value.strip()
        if field_name == "topic":
            fields[field_name] = decode_topic(raw_value)
        else:
            fields[field_name] = unquote(raw_value)
    return fields, None


def note_filename(key: str, topic: str, suffix: str = "") -> str:
    """`<key>--<first 8 hex of the normalized topic>[-n].md`."""
    extra = f"-{suffix}" if suffix else ""
    return f"{key}--{topic_hash(topic)}{extra}.md"


def topic_hash(topic: str) -> str:
    normalized = re.sub(r"\s+", " ", topic.strip().lower())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:8]


def write_note(project: Path, filename: str, text: str, token: str | None = None) -> str:
    """Validate ``text`` and publish it under the project `runs` directory.

    Returns the scratch token that was used. Raises ``WriteError`` without
    following or unlinking a symlink.
    """
    chosen = token if token is not None else secrets.token_hex(16)
    _validate_token(chosen)
    validate_note(filename, text)
    runs = validated_runs(project)
    if validated_runs(project) != runs:
        raise WriteError("runs escapes the project folder")
    _write_exclusive(runs, filename, chosen, text)
    return chosen


def validate_note(filename: str, text: str) -> dict[str, str]:
    """Refuse a note the writer must not publish. The message names no path."""
    _one_segment(filename, "filename must be one path segment")
    if len(filename.encode("utf-8")) > FILENAME_MAX_BYTES:
        raise WriteError("invalid note: filename is over 67 bytes")
    fields, body = parse_frontmatter(text)
    if fields is None or body is None:
        raise WriteError("invalid note: frontmatter is missing a delimiter")
    if fields.get("marker") != MARKER:
        raise WriteError("invalid note: marker must be run-note")
    if fields.get("schema") != SCHEMA_V2:
        raise WriteError("invalid note: schema must be 2")
    key = fields.get("key", "")
    if not _valid_key(key):
        raise WriteError("invalid note: key is invalid")
    topic = fields.get("topic", "")
    if topic.strip() == "":
        raise WriteError("invalid note: topic is empty")
    if _raw_topic(text) != encode_topic(topic):
        raise WriteError("invalid note: topic is not canonical")
    if parse_date(fields.get("run_date", "")) is None:
        raise WriteError("invalid note: run_date is not a date")
    if parse_date(fields.get("expires", "")) is None:
        raise WriteError("invalid note: expires is not a date")
    pattern = re.compile(rf"^{re.escape(key)}--{topic_hash(topic)}{FILENAME_SUFFIX_RE}")
    if pattern.fullmatch(filename) is None:
        raise WriteError("invalid note: filename does not match key and topic")
    content_lines = [line.strip() for line in split_record_lines(body) if line.strip()]
    if not content_lines or content_lines[-1] != CLOSING_LINE:
        raise WriteError("invalid note: closing line is missing")
    return fields


def validated_runs(project: Path) -> Path:
    """Return the real `runs` directory, or refuse a relative, missing, or escaping path."""
    if not project.is_absolute():
        raise WriteError("project path is relative")
    try:
        resolved_project = project.resolve(strict=True)
    except OSError:
        raise WriteError("project path is missing") from None
    if not resolved_project.is_dir():
        raise WriteError("project path is not a directory")
    expected = resolved_project / RUNS_DIRNAME
    given = project / RUNS_DIRNAME
    if _missing(given) and _missing(expected):
        try:
            os.mkdir(expected, 0o700)
        except FileExistsError:
            pass
    try:
        resolved = given.resolve(strict=True)
    except OSError:
        raise WriteError("runs escapes the project folder") from None
    if resolved.parent != resolved_project or resolved.name != RUNS_DIRNAME:
        raise WriteError("runs escapes the project folder")
    if not resolved.is_dir():
        raise WriteError("runs is not a directory")
    return resolved


def parse_date(value: str) -> datetime | None:
    if DATE_RE.fullmatch(value) is None:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return None


def unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Encode, decode, or write one free-research run note.")
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("encode-topic", help="read a topic from stdin and write the stored value")
    subcommands.add_parser("decode-topic", help="read a stored topic value from stdin and write the topic")
    write = subcommands.add_parser("write", help="read a note from stdin and publish it")
    write.add_argument("--project", required=True, type=Path)
    write.add_argument("--filename", required=True)
    write.add_argument("--token", default=None)
    args = parser.parse_args(argv)
    try:
        if args.command == "encode-topic":
            sys.stdout.buffer.write(encode_topic(_read_stdin()).encode("utf-8"))
            return 0
        if args.command == "decode-topic":
            sys.stdout.buffer.write(decode_topic(_stored_stdin(_read_stdin())).encode("utf-8"))
            return 0
        write_note(args.project, args.filename, _read_stdin(), args.token)
    except WriteError as exc:
        print(f"run_note: {exc}", file=sys.stderr)
        return 1
    except UnicodeError:
        print("run_note: stdin is not utf-8", file=sys.stderr)
        return 1
    sys.stdout.write(f"wrote {args.filename}\n")
    return 0


def _topic_is_plain(topic: str) -> bool:
    if topic == "" or topic != topic.strip():
        return False
    for character in topic:
        if character in {'"', "\\"} or character in SPLITLINES_BREAKS or ord(character) < 32:
            return False
    return True


def _raw_topic(text: str) -> str | None:
    lines = split_record_lines(text)
    if not lines or lines[0].strip() != "---":
        return None
    found: str | None = None
    for line in lines[1:]:
        if line.strip() == "---":
            return found
        if not line.strip() or ":" not in line:
            continue
        name, value = line.split(":", 1)
        if name.strip() == "topic":
            found = value.strip()
    return found


def _valid_key(key: str) -> bool:
    if len(key.encode("utf-8")) > KEY_MAX_BYTES:
        return False
    return KEY_RE.fullmatch(key) is not None


def _one_segment(name: str, message: str) -> None:
    if name in {"", ".", ".."} or "/" in name or "\\" in name or "\x00" in name:
        raise WriteError(message)
    if any(character in name for character in SPLITLINES_BREAKS):
        raise WriteError(message)
    if Path(name).is_absolute():
        raise WriteError(message)


def _validate_token(token: str) -> None:
    _one_segment(token, "token must be one path segment")
    if TOKEN_RE.fullmatch(token) is None:
        raise WriteError("token must be hex")


def _missing(path: Path) -> bool:
    try:
        os.lstat(path)
    except OSError:
        return True
    return False


def _write_exclusive(runs: Path, filename: str, token: str, text: str) -> None:
    scratch_name = f".{filename}.{token}.tmp"
    _one_segment(scratch_name, "scratch must be one path segment")
    scratch = runs / scratch_name
    if scratch.parent != runs:
        raise WriteError("scratch is not a direct child of runs")
    _refuse_existing(scratch)
    try:
        descriptor = os.open(scratch, _OPEN_FLAGS, 0o600)
    except OSError as exc:
        _raise_create_error(scratch, exc)
        return
    owned: tuple[int, int] | None = None
    try:
        owned = _owned_regular_file(descriptor, scratch)
        try:
            _write_all(descriptor, text.encode("utf-8"))
            os.fsync(descriptor)
        except OSError:
            raise WriteError("scratch create failed") from None
        _owned_regular_file(descriptor, scratch)
        if parse_date(validate_note(filename, text).get("expires", "")) is None:
            raise WriteError("invalid note: expires is not a date")
        target = runs / filename
        _refuse_symlink(target, "refused symlink target")
        try:
            os.rename(scratch, target)
        except OSError:
            raise WriteError("scratch create failed") from None
        owned = None
        try:
            _fsync_dir(runs)
        except OSError:
            raise WriteError("scratch create failed") from None
    finally:
        os.close(descriptor)
        if owned is not None:
            _cleanup_scratch(scratch, owned[0], owned[1])


def _refuse_existing(path: Path) -> None:
    try:
        info = os.lstat(path)
    except OSError:
        return
    if stat.S_ISLNK(info.st_mode):
        raise WriteError("refused symlink scratch")
    raise WriteError("scratch already exists")


def _raise_create_error(path: Path, exc: OSError) -> None:
    if exc.errno == errno.ELOOP:
        raise WriteError("refused symlink scratch") from None
    if exc.errno == errno.EEXIST:
        try:
            info = os.lstat(path)
        except OSError:
            info = None
        if info is not None and stat.S_ISLNK(info.st_mode):
            raise WriteError("refused symlink scratch") from None
        raise WriteError("scratch already exists") from None
    raise WriteError("scratch create failed") from None


def _owned_regular_file(descriptor: int, path: Path) -> tuple[int, int]:
    info = os.fstat(descriptor)
    if not stat.S_ISREG(info.st_mode):
        raise WriteError("refused symlink scratch")
    try:
        linked = os.lstat(path)
    except OSError:
        raise WriteError("scratch create failed") from None
    same = linked.st_dev == info.st_dev and linked.st_ino == info.st_ino
    if stat.S_ISLNK(linked.st_mode) or not same:
        raise WriteError("refused symlink scratch")
    return info.st_dev, info.st_ino


def _refuse_symlink(path: Path, message: str) -> None:
    try:
        info = os.lstat(path)
    except OSError:
        return
    if stat.S_ISLNK(info.st_mode):
        raise WriteError(message)


def _write_all(descriptor: int, payload: bytes) -> None:
    view = memoryview(payload)
    while view:
        written = os.write(descriptor, view)
        if written <= 0:
            raise WriteError("scratch create failed")
        view = view[written:]


def _fsync_dir(path: Path) -> None:
    flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY
    descriptor = os.open(path, flags)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _cleanup_scratch(path: Path, device: int, inode: int) -> None:
    """Unlink only the regular file this run created. Leave a symlink alone."""
    try:
        info = os.lstat(path)
    except OSError:
        return
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        return
    if info.st_dev != device or info.st_ino != inode:
        return
    try:
        os.unlink(path)
    except OSError:
        return


def _read_stdin() -> str:
    return sys.stdin.buffer.read().decode("utf-8")


def _stored_stdin(raw: str) -> str:
    """Drop one trailing record newline added by a line-oriented pipe."""
    if raw.endswith("\r\n"):
        return raw[:-2]
    if raw.endswith("\n") or raw.endswith("\r"):
        return raw[:-1]
    return raw


if __name__ == "__main__":
    sys.exit(main())
