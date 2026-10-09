"""The skill-local run-note helper is the one codec and the one writer."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import lint_run_notes  # noqa: E402

HELPER = ROOT / "skills" / "free-research" / "scripts" / "run_note.py"
CLOSING_LINE = "your agent is only as good as the worst source it believed."
KEY = "line-separator-round"
SPLITLINES_BREAKS = (
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
)


def _run(args: list[str], data: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        [sys.executable, str(HELPER), *args],
        input=data.encode("utf-8"),
        capture_output=True,
        check=False,
    )


def _note(stored_topic: str, key: str) -> str:
    return (
        "---\n"
        "marker: run-note\n"
        "schema: 2\n"
        f"key: {key}\n"
        f"topic: {stored_topic}\n"
        "run_date: 2026-10-01\n"
        "expires: 2026-10-31\n"
        "---\n"
        "- confirmed: EzzyBills documents a Xero connector.\n"
        "https://example.com/xero\n"
        f"{CLOSING_LINE}\n"
    )


class TestRunNoteHelper(unittest.TestCase):
    def test_linter_uses_the_skill_helper_codec(self) -> None:
        helper = lint_run_notes.run_note
        self.assertEqual(HELPER.resolve(), Path(helper.__file__).resolve())
        self.assertIs(lint_run_notes.encode_topic, helper.encode_topic)
        self.assertIs(lint_run_notes.decode_topic, helper.decode_topic)
        self.assertIs(lint_run_notes.parse_frontmatter, helper.parse_frontmatter)
        source = (ROOT / "scripts" / "lint_run_notes.py").read_text(encoding="utf-8")
        self.assertNotIn("def encode_topic", source)
        self.assertNotIn("def decode_topic", source)

    def test_every_splitlines_break_round_trips_through_parse(self) -> None:
        for index, character in enumerate(SPLITLINES_BREAKS):
            topic = f"left{character}right{index}"
            with self.subTest(codepoint=f"U+{ord(character):04X}"):
                encoded = lint_run_notes.encode_topic(topic)
                self.assertEqual([encoded], encoded.splitlines())
                self.assertNotIn(character, encoded)
                self.assertEqual(topic, lint_run_notes.decode_topic(encoded))
                fields, _body = lint_run_notes.parse_frontmatter(_note(encoded, KEY))
                self.assertIsNotNone(fields)
                assert fields is not None
                self.assertEqual(topic, fields["topic"])
                if character not in {"\n", "\r"}:
                    raw_fields, _body = lint_run_notes.parse_frontmatter(_note(topic, KEY))
                    assert raw_fields is not None
                    self.assertEqual(topic, raw_fields["topic"])

    def test_unicode_separators_round_trip_through_encode_write_parse(self) -> None:
        topics = (
            "alpha\u2028beta",
            "gamma\u2029delta",
            "epsilon\u0085zeta",
            "one\u2028two\u2029three\u0085four",
        )
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            (project / "runs").mkdir(parents=True)
            for topic in topics:
                with self.subTest(topic=topic):
                    encoded_run = _run(["encode-topic"], topic)
                    self.assertEqual(0, encoded_run.returncode, encoded_run.stderr)
                    encoded = encoded_run.stdout.decode("utf-8")
                    self.assertEqual(lint_run_notes.encode_topic(topic), encoded)
                    for character in ("\u2028", "\u2029", "\u0085"):
                        self.assertNotIn(character, encoded)
                    decoded_run = _run(["decode-topic"], encoded)
                    self.assertEqual(topic.encode("utf-8"), decoded_run.stdout)
                    filename = lint_run_notes.run_note.note_filename(KEY, topic)
                    wrote = _run(
                        ["write", "--project", str(project), "--filename", filename],
                        _note(encoded, KEY),
                    )
                    self.assertEqual(0, wrote.returncode, wrote.stderr)
                    self.assertEqual(f"wrote {filename}\n".encode("utf-8"), wrote.stdout)
                    written = (project / "runs" / filename).read_text(encoding="utf-8")
                    for character in ("\u2028", "\u2029", "\u0085"):
                        self.assertNotIn(character, written)
                    topic_lines = [line for line in written.splitlines() if line.startswith("topic:")]
                    self.assertEqual([f"topic: {encoded}"], topic_lines)
                    fields, _body = lint_run_notes.parse_frontmatter(written)
                    assert fields is not None
                    self.assertEqual(topic, fields["topic"])
                    leftovers = [
                        path.name
                        for path in (project / "runs").iterdir()
                        if path.name.endswith(".tmp")
                    ]
                    self.assertEqual([], leftovers)
                    result = lint_run_notes.lint_text(filename, written, date(2026, 10, 1))
                    self.assertEqual([], [issue.code for issue in result.issues])

    def test_write_refuses_preexisting_symlink_scratch(self) -> None:
        topic = "Can a finance team build a custom EzzyBills to Xero integration"
        key = "ezzybills-xero-integration"
        filename = lint_run_notes.run_note.note_filename(key, topic)
        token = "abcdef0123456789"
        encoded = lint_run_notes.encode_topic(topic)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "project"
            runs = project / "runs"
            runs.mkdir(parents=True)
            outside = root / "outside.txt"
            outside.write_text("secret-marker", encoding="utf-8")
            scratch = runs / f".{filename}.{token}.tmp"
            scratch.symlink_to(outside)
            completed = _run(
                [
                    "write",
                    "--project",
                    str(project),
                    "--filename",
                    filename,
                    "--token",
                    token,
                ],
                _note(encoded, key),
            )
            self.assertNotEqual(0, completed.returncode)
            self.assertIn(b"refused symlink scratch", completed.stderr)
            self.assertNotIn(str(project).encode("utf-8"), completed.stderr)
            self.assertTrue(scratch.is_symlink())
            self.assertEqual(outside.resolve(), scratch.resolve())
            self.assertEqual("secret-marker", outside.read_text(encoding="utf-8"))
            self.assertFalse((runs / filename).exists())
            self.assertEqual([scratch.name], sorted(path.name for path in runs.iterdir()))


if __name__ == "__main__":
    unittest.main()
