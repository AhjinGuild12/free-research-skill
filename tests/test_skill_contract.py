"""Pin free-research ceilings, report shape, traces, and opt-in copy parity."""

from __future__ import annotations

import hashlib
import os
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README_MD = ROOT / "README.md"
SKILL_DIR = ROOT / "skills" / "free-research"
SKILL_MD = SKILL_DIR / "SKILL.md"
TOOL_ROUTING = SKILL_DIR / "references" / "tool-routing.md"
EVAL_SCENARIOS = SKILL_DIR / "references" / "eval-scenarios.md"
VERIFICATION_TAIL = SKILL_DIR / "references" / "verification-tail.md"
VAULT_NOTES = SKILL_DIR / "references" / "vault-notes.md"

TOOLS = ("Exa", "Firecrawl", "Brave")
MODES = ("free", "balanced", "deep")
REPORT_SECTIONS = (
    "Executive Summary",
    "Key Developments",
    "Community Sentiment",
    "Deep Insights",
    "Best Takes",
    "Comparison / Gaps",
    "Actionable Takeaways",
    "Tools Used",
    "Follow-up Options",
)
CLOSING_LINE = "your agent is only as good as the worst source it believed."
TRACE_IDS = (
    tuple(f"T{number}" for number in range(1, 18))
    + ("T18a", "T18b", "T19", "T20", "T21", "T22", "T23", "L1", "L2")
)
KEY_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+){1,3}$")
KEY_MAX_BYTES = 48
FILENAME_MAX_BYTES = 67
VAULT_LOAD_READ = (
    "On a new invocation, load `references/vault-notes.md` before the free-web search and follow it for the read."
)
VAULT_LOAD_WRITE = (
    "After the verification tail reaches its write step, load `references/vault-notes.md` again and follow it for the write."
)
ENV_READ_RULE = (
    "Read `FREE_RESEARCH_NOTES_DIR` by name only. "
    "It is the only environment variable this skill reads."
)
VAULT_TOOLS_USED = (
    "The vault-note line is one line. It says whether a note was read, written, or skipped, and why. "
    "It does not include `FREE_RESEARCH_NOTES_DIR` or a filesystem path."
)
VAULT_BARE_FILENAME_EXAMPLE = "ezzybills-xero-integration--c30f01f3.md"
VAULT_BARE_FILENAME_RULE = (
    "When a note was read, name each note that was read by its bare filename only, "
    f"for example `{VAULT_BARE_FILENAME_EXAMPLE}`. "
    "When a note was written, name the new note's bare filename too. "
    "Never include a directory or the vault path. "
    "A bare filename has no directory and is not the vault path."
)
NORMALIZED_TOPIC_RULE = (
    "The normalized topic is the topic lowercased, with leading and trailing whitespace trimmed "
    "and each internal whitespace run collapsed to a single space."
)
VAULT_NOTE_PHRASES = (
    "FREE_RESEARCH_NOTES_DIR",
    "[shell_environment_policy.set]",
    "26-config-reference.md",
    r"^[a-z0-9]+(?:-[a-z0-9]+){1,3}$",
    "microsoft-ms-102",
    "Each hyphenated word may contain digits.",
    "48 bytes",
    "67 bytes",
    "schema: 2",
    "marker: run-note",
    "sha256",
    "UTF-8",
    "first 8 hex",
    NORMALIZED_TOPIC_RULE,
    "legacy exact-slug",
    "lowercase, digits and hyphens kept, other characters collapsed to a single hyphen",
    "<key>--<hash>-2.md",
    "at most three version-2 notes",
    "not proof, not a gap",
    "use --deep",
    "set the vault path",
    "7 days for a news intent, 90 days when the confirming body is a stable official doc, otherwise 30 days",
)
VAULT_TRACE_PHRASES = (
    "ezzybills-xero-integration--1a2b3c4d.md",
    "can we build the EzzyBills to Xero sync ourselves",
    "not proof, not a gap",
    "300-character topic",
    "at most 67 bytes",
    "first 250 characters",
    "<key>--<hash>-2.md",
    "legacy exact-slug",
    "latest `expires`",
    "FREE_RESEARCH_NOTES_DIR",
    "relative path",
    "symlink",
    "use --deep",
    "set the vault path",
    "two sibling files",
)
SAFETY_FLOOR_STATEMENTS = (
    "The gate is marked returned before the tail loads.",
    "An unreviewed finding is unconfirmed.",
    "Executive Summary and Actionable Takeaways assert only confirmed findings.",
    "After the gate, no Exa, Firecrawl, Brave, or `parallel-cli`.",
    "A failed reference load means the report ships and no note is written.",
    "If `references/tool-routing.md` fails to load, no paid call is made, and the gate returns.",
    "If `references/verification-tail.md` fails to load, no further paid call is made, and no note is written.",
    "Calls made before the gate returned still count, and are listed under Tools Used.",
)
PARALLEL_RUNS_BALANCED = 1
PARALLEL_EXTRACTS_BALANCED = 2
COPY_CHECK_ENV = "FREE_RESEARCH_CHECK_COPIES"
COPY_PARITY_FILES = (
    "SKILL.md",
    "references/eval-scenarios.md",
    "references/tool-routing.md",
    "references/vault-notes.md",
    "references/verification-tail.md",
    "scripts/run_note.py",
)

_PAIR_RE = re.compile(
    r"\b(Exa|Firecrawl|Brave)\b[^≤\n]{0,160}?(?:≤|\bat most\b)\s*(\d+)",
    re.IGNORECASE,
)
_BARE_CEILING_RE = re.compile(r"(?:≤|\bat most\b)\s*(\d+)", re.IGNORECASE)
_MODE_FLAG_RE = re.compile(r"--(free|balanced|deep)\b")
_ROW_MODE_RE = re.compile(r"\*\*(free|balanced|deep)\*\*", re.IGNORECASE)
_BLOCK_TOOL_RE = re.compile(r"^\d+\.\s+\*\*(Exa|Firecrawl|Brave)\*\*")
_TRACE_HEADING_RE = re.compile(r"^#{2,3} ((?:T\d+[a-z]?|L\d+))\.", re.MULTILINE)
_REFERENCE_RE = re.compile(r"references/[A-Za-z0-9_.-]+\.md")
_PARALLEL_CAP_RE = re.compile(
    r"at most (one|two|three|four|\d+) `research run` and (one|two|three|four|\d+) extracts",
    re.IGNORECASE,
)
_NUMBER_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4}
_DEEP_DOUBLES = "Deep mode doubles those caps"
_CONCURRENCY_RE = re.compile(r"concurren|parallelism|cap parallel", re.IGNORECASE)
_TOOL_CANONICAL = {name.lower(): name for name in TOOLS}


def _clauses(line: str) -> list[str]:
    pieces: list[str] = []
    for sentence in re.split(r"(?<=[.;])\s+", line):
        pieces.extend(part for part in re.split(r";\s*", sentence) if part.strip())
    return pieces


def _mode_for(clause: str, line: str, section_mode: str | None) -> str | None:
    flags = list(dict.fromkeys(_MODE_FLAG_RE.findall(clause)))
    if len(flags) == 1:
        return flags[0]
    if len(flags) > 1:
        return None
    if line.startswith("|"):
        row_mode = _ROW_MODE_RE.search(line)
        if row_mode:
            return row_mode.group(1).lower()
    return section_mode


def _ceiling_statements(text: str) -> list[tuple[str | None, str, int]]:
    section_mode: str | None = None
    found: list[tuple[str | None, str, int]] = []
    for line in text.splitlines():
        if line.startswith("#"):
            flags = list(dict.fromkeys(_MODE_FLAG_RE.findall(line)))
            section_mode = flags[0] if len(flags) == 1 else None
            continue
        block_tool = None
        block_match = _BLOCK_TOOL_RE.match(line)
        if block_match:
            block_tool = block_match.group(1)
        for clause in _clauses(line):
            if _CONCURRENCY_RE.search(clause):
                continue
            mode = _mode_for(clause, line, section_mode)
            pairs = list(_PAIR_RE.finditer(clause))
            if pairs:
                for pair in pairs:
                    tool = _TOOL_CANONICAL[pair.group(1).lower()]
                    found.append((mode, tool, int(pair.group(2))))
                continue
            bare = _BARE_CEILING_RE.search(clause)
            if bare and block_tool:
                found.append((mode, block_tool, int(bare.group(1))))
    return found


def _modes_table_rows(text: str) -> list[str]:
    lines = text.splitlines()
    start = next((index for index, line in enumerate(lines) if line.strip() == "## Modes"), None)
    if start is None:
        raise AssertionError("## Modes section not found")
    rows: list[str] = []
    for line in lines[start + 1 :]:
        if line.startswith("|"):
            rows.append(" ".join(line.split()))
        elif rows:
            break
    if len(rows) < 3:
        raise AssertionError("Modes table not found")
    return rows[2:]


def _modes_table(text: str) -> dict[str, dict[str, int]]:
    lines = text.splitlines()
    start = next((index for index, line in enumerate(lines) if line.strip() == "## Modes"), None)
    if start is None:
        raise AssertionError("SKILL.md ## Modes section not found")
    rows: list[str] = []
    for line in lines[start + 1 :]:
        if line.startswith("|"):
            rows.append(line)
        elif rows:
            break
    if len(rows) < 3:
        raise AssertionError("SKILL.md Modes table not found")
    ceilings: dict[str, dict[str, int]] = {}
    deep_cell = ""
    for row in rows[2:]:
        cells = [cell.strip() for cell in row.strip().strip("|").split("|")]
        if len(cells) < 2:
            raise AssertionError(f"Modes table row is short: {row}")
        mode_match = re.search(r"\b(free|balanced|deep)\b", cells[0], re.IGNORECASE)
        if not mode_match:
            raise AssertionError(f"Modes table row has no mode: {row}")
        mode = mode_match.group(1).lower()
        found = {
            _TOOL_CANONICAL[tool.lower()]: int(count)
            for tool, count in _PAIR_RE.findall(cells[1])
        }
        ceilings[mode] = found
        if mode == "deep":
            deep_cell = cells[1]
    if set(ceilings) != set(MODES):
        raise AssertionError(f"Modes table modes: {sorted(ceilings)}")
    if set(ceilings["balanced"]) != set(TOOLS):
        raise AssertionError(f"Modes table balanced ceilings: {ceilings['balanced']}")
    if not ceilings["free"]:
        ceilings["free"] = {tool: 0 for tool in TOOLS}
    elif set(ceilings["free"]) != set(TOOLS):
        raise AssertionError(f"Modes table free ceilings: {ceilings['free']}")
    if not ceilings["deep"]:
        if not re.search(r"2\s*[×x]\s*balanced", deep_cell, re.IGNORECASE):
            raise AssertionError("Modes table deep ceilings are not explicit and not 2× balanced")
        ceilings["deep"] = {tool: count * 2 for tool, count in ceilings["balanced"].items()}
    elif set(ceilings["deep"]) != set(TOOLS):
        raise AssertionError(f"Modes table deep ceilings: {ceilings['deep']}")
    return ceilings


def _step6_template(text: str) -> str:
    start = text.find("## Step 6:")
    if start < 0:
        raise AssertionError("Step 6 heading not found")
    fence = text.find("```markdown", start)
    if fence < 0:
        raise AssertionError("Step 6 template fence not found")
    body_start = text.find("\n", fence) + 1
    body_end = text.find("```", body_start)
    if body_end < 0:
        raise AssertionError("Step 6 template fence does not close")
    return text[body_start:body_end]


def _parse_count(token: str) -> int:
    lowered = token.lower()
    if lowered.isdigit():
        return int(lowered)
    return _NUMBER_WORDS[lowered]


def _normalize_topic(topic: str) -> str:
    return re.sub(r"\s+", " ", topic.strip().lower())


def _topic_filename(key: str, topic: str, suffix: str = "") -> str:
    digest = hashlib.sha256(_normalize_topic(topic).encode("utf-8")).hexdigest()[:8]
    extra = f"-{suffix}" if suffix else ""
    return f"{key}--{digest}{extra}.md"


def _file_inventory(root: Path) -> dict[str, str]:
    if not root.is_dir():
        raise AssertionError(f"missing copy: {root}")
    inventory: dict[str, str] = {}
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        inventory[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return inventory


class TestSkillContract(unittest.TestCase):
    def test_at_most_ceilings_cannot_evade_contract(self) -> None:
        text = TOOL_ROUTING.read_text(encoding="utf-8")
        expected = _modes_table(SKILL_MD.read_text(encoding="utf-8"))
        for original, replacement, statement in (
            ("Brave ≤1", "Brave at most 9", ("balanced", "Brave", 9)),
            ("Exa ≤4", "Exa at most 9", ("deep", "Exa", 9)),
        ):
            with self.subTest(replacement=replacement):
                self.assertIn(original, text)
                parsed = _ceiling_statements(text.replace(original, replacement))
                self.assertIn(statement, parsed)
                mode, tool, count = statement
                self.assertNotEqual(expected[mode][tool], count)
        self.assertEqual(
            [("deep", "Exa", 9)],
            _ceiling_statements("3. **Exa**: `--deep` at most 9 search calls."),
        )

    def test_paid_ceilings_match_modes_table(self) -> None:
        expected = _modes_table(SKILL_MD.read_text(encoding="utf-8"))
        problems: list[str] = []
        for path in (SKILL_MD, TOOL_ROUTING, EVAL_SCENARIOS):
            relative = path.relative_to(ROOT).as_posix()
            statements = _ceiling_statements(path.read_text(encoding="utf-8"))
            if not statements:
                problems.append(f"{relative}: no Exa, Firecrawl, or Brave ceiling statements parsed")
            for mode, tool, count in statements:
                if mode not in expected or tool not in expected[mode]:
                    problems.append(f"{relative}: unresolved {mode} {tool} ≤{count}")
                    continue
                wanted = expected[mode][tool]
                if count != wanted:
                    problems.append(
                        f"{relative}: {mode} {tool} ≤{count} != Modes table ≤{wanted}"
                    )
        self.assertEqual([], problems, "\n".join(problems))

    def test_readme_modes_table_matches_skill(self) -> None:
        skill_text = SKILL_MD.read_text(encoding="utf-8")
        readme_text = README_MD.read_text(encoding="utf-8")
        self.assertEqual(_modes_table_rows(skill_text), _modes_table_rows(readme_text))
        self.assertEqual(_modes_table(skill_text), _modes_table(readme_text))

    def test_parallel_cli_caps(self) -> None:
        problems: list[str] = []
        for path in (TOOL_ROUTING, EVAL_SCENARIOS):
            relative = path.relative_to(ROOT).as_posix()
            text = path.read_text(encoding="utf-8")
            if path is EVAL_SCENARIOS:
                heading = re.search(r"^## T16\..*$", text, re.MULTILINE)
                self.assertIsNotNone(heading, "T16 heading missing")
                next_heading = re.search(r"^## ", text[heading.end() :], re.MULTILINE)
                end = heading.end() + next_heading.start() if next_heading else len(text)
                text = text[heading.start() : end]
                relative = f"{relative} T16"
            matches = list(_PARALLEL_CAP_RE.finditer(text))
            if len(matches) != 1:
                problems.append(f"{relative}: expected one balanced parallel-cli cap, found {len(matches)}")
                continue
            runs = _parse_count(matches[0].group(1))
            extracts = _parse_count(matches[0].group(2))
            if runs != PARALLEL_RUNS_BALANCED:
                problems.append(f"{relative}: balanced research runs {runs} != {PARALLEL_RUNS_BALANCED}")
            if extracts != PARALLEL_EXTRACTS_BALANCED:
                problems.append(
                    f"{relative}: balanced extracts {extracts} != {PARALLEL_EXTRACTS_BALANCED}"
                )
            if _DEEP_DOUBLES not in text:
                problems.append(f"{relative}: deep caps are not twice the balanced caps")
        self.assertEqual([], problems, "\n".join(problems))

    def test_report_section_order_and_closing_line(self) -> None:
        template = _step6_template(SKILL_MD.read_text(encoding="utf-8"))
        headings = re.findall(r"^## (.+)$", template, re.MULTILINE)
        self.assertEqual(list(REPORT_SECTIONS), headings)
        last_line = [line for line in template.splitlines() if line.strip()][-1]
        self.assertEqual(CLOSING_LINE, last_line)
        eval_text = EVAL_SCENARIOS.read_text(encoding="utf-8")
        listed = re.search(
            r"names and order through Follow-up Options stay (.+?)\.",
            eval_text,
        )
        self.assertIsNotNone(listed, "T17 section order not found")
        self.assertEqual(list(REPORT_SECTIONS), [part.strip() for part in listed.group(1).split(", ")])
        self.assertIn(f"`{CLOSING_LINE}`", eval_text)

    def test_referenced_files_exist(self) -> None:
        named = sorted(set(_REFERENCE_RE.findall(SKILL_MD.read_text(encoding="utf-8"))))
        self.assertTrue(named, "SKILL.md names no references/ files")
        missing = [ref for ref in named if not (SKILL_DIR / ref).is_file()]
        self.assertEqual([], missing, f"missing referenced files: {missing}")

    def test_verification_tail_exists_and_safety_floor(self) -> None:
        skill = SKILL_MD.read_text(encoding="utf-8")
        self.assertTrue(VERIFICATION_TAIL.is_file(), "references/verification-tail.md is missing")
        self.assertIn("references/verification-tail.md", skill)
        missing = [statement for statement in SAFETY_FLOOR_STATEMENTS if statement not in skill]
        self.assertEqual([], missing, "safety floor missing from SKILL.md:\n" + "\n".join(missing))

    def test_vault_notes_contract(self) -> None:
        self.assertTrue(VAULT_NOTES.is_file(), "references/vault-notes.md is missing")
        skill = SKILL_MD.read_text(encoding="utf-8")
        notes = VAULT_NOTES.read_text(encoding="utf-8")
        scenarios = EVAL_SCENARIOS.read_text(encoding="utf-8")
        self.assertIn("references/vault-notes.md", skill)
        self.assertIn(VAULT_LOAD_READ, skill)
        self.assertIn(VAULT_LOAD_WRITE, skill)
        self.assertIn(ENV_READ_RULE, skill)
        self.assertIn(VAULT_TOOLS_USED, skill)
        for text, label in ((skill, "SKILL.md"), (notes, "vault-notes.md"), (scenarios, "eval-scenarios.md")):
            self.assertNotIn("Jan Obsidian", text, label)
            self.assertNotIn("1. Projects/Improved Search free-research", text, label)
        missing_notes = [phrase for phrase in VAULT_NOTE_PHRASES if phrase not in notes]
        self.assertEqual([], missing_notes, "vault-notes.md missing:\n" + "\n".join(missing_notes))
        missing_scenarios = [phrase for phrase in VAULT_TRACE_PHRASES if phrase not in scenarios]
        self.assertEqual([], missing_scenarios, "eval-scenarios.md missing:\n" + "\n".join(missing_scenarios))
        self.assertNotIn("letters only", notes.lower())
        self.assertNotIn("sibling slug is neither read", skill)
        self.assertIn(r"^[a-z0-9]+(?:-[a-z0-9]+){1,3}$", notes)

    def test_checklist_order_puts_synthesis_last(self) -> None:
        checklist = SKILL_MD.read_text(encoding="utf-8").split("## Execution Checklist", 1)[1]
        self.assertIn(
            "gate return → safety floor + verification tail → note write → synthesis",
            checklist,
        )
        self.assertNotIn("Walk Step 1 through Step 6 in order, then the safety floor", checklist)

    def test_legacy_lookup_requires_absent_schema(self) -> None:
        notes = VAULT_NOTES.read_text(encoding="utf-8")
        self.assertIn("the `schema` field is absent", notes)
        self.assertIn("Skip unsupported schemas.", notes)
        self.assertNotIn("no `schema: 2`", notes)

    def test_filesystem_path_ban_is_vault_line_only(self) -> None:
        notes = VAULT_NOTES.read_text(encoding="utf-8")
        readme = README_MD.read_text(encoding="utf-8")
        scoped = "The filesystem-path ban is only the vault location and the vault-note line"
        self.assertIn(scoped, notes)
        self.assertIn("Firecrawl output path", notes)
        self.assertNotIn("any filesystem path in the report or under Tools Used", notes)
        self.assertIn(
            "The filesystem-path ban is the vault location and the vault-note line only.",
            readme,
        )
        self.assertIn("including the Firecrawl output path", readme)
        self.assertNotIn("never print the value or a filesystem path", readme)

    def test_vault_note_tools_used_names_bare_filename(self) -> None:
        notes = VAULT_NOTES.read_text(encoding="utf-8")
        skill = SKILL_MD.read_text(encoding="utf-8")
        self.assertNotIn("/", VAULT_BARE_FILENAME_EXAMPLE)
        self.assertNotIn("\\", VAULT_BARE_FILENAME_EXAMPLE)
        for text, label in ((notes, "vault-notes.md"), (skill, "SKILL.md")):
            self.assertIn(VAULT_TOOLS_USED, text, label)
            self.assertIn(VAULT_BARE_FILENAME_RULE, text, label)
            self.assertNotIn(f"/{VAULT_BARE_FILENAME_EXAMPLE}", text, label)
            self.assertNotIn(f"\\{VAULT_BARE_FILENAME_EXAMPLE}", text, label)
        self.assertIn("that line does not include the vault location or a filesystem path", notes)

    def test_scratch_create_is_unique_exclusive_and_scoped(self) -> None:
        notes = VAULT_NOTES.read_text(encoding="utf-8")
        self.assertIn(".<filename>.<token>.tmp", notes)
        self.assertIn("O_EXCL", notes)
        self.assertIn("O_NOFOLLOW", notes)
        self.assertIn("Clean up only the scratch this run created.", notes)
        self.assertIn("do not unlink it", notes)
        self.assertNotIn("runs/.<filename>.tmp", notes)
        self.assertIn("Do not create, open, fstat, or rename the scratch yourself.", notes)
        self.assertIn(
            'printf \'%s\' "$NOTE" | python3 "$SKILL_DIR/scripts/run_note.py" write '
            '--project "$FREE_RESEARCH_NOTES_DIR" --filename "$FILENAME" --token "$TOKEN"',
            notes,
        )
        self.assertIn('python3 "$SKILL_DIR/scripts/run_note.py" encode-topic', notes)
        self.assertIn('python3 "$SKILL_DIR/scripts/run_note.py" decode-topic', notes)

    def test_run_note_helper_is_in_the_skill_tree(self) -> None:
        helper = SKILL_DIR / "scripts" / "run_note.py"
        self.assertTrue(helper.is_file(), "scripts/run_note.py is missing from the skill tree")
        inventory = _file_inventory(SKILL_DIR)
        missing = [relative for relative in COPY_PARITY_FILES if relative not in inventory]
        self.assertEqual([], missing)

    def test_key_grammar_allows_digits_and_bounds_filenames(self) -> None:
        self.assertIsNotNone(KEY_RE.fullmatch("microsoft-ms-102"))
        self.assertIsNotNone(KEY_RE.fullmatch("ezzybills-xero-integration"))
        self.assertIsNone(KEY_RE.fullmatch("xero"))
        self.assertIsNone(KEY_RE.fullmatch("a-b-c-d-e"))
        self.assertLessEqual(len("microsoft-ms-102".encode("utf-8")), KEY_MAX_BYTES)
        long_key = "abcdefghijkl-abcdefghijk-abcdefghijk-abcdefghijk"
        self.assertEqual(KEY_MAX_BYTES, len(long_key.encode("utf-8")))
        self.assertIsNotNone(KEY_RE.fullmatch(long_key))
        collided = f"{long_key}--01234567-2.md"
        self.assertLessEqual(len(collided.encode("utf-8")), FILENAME_MAX_BYTES)
        first_topic = "w" * 300
        second_topic = ("w" * 250) + ("x" * 50)
        self.assertEqual(300, len(first_topic))
        self.assertTrue(second_topic.startswith(first_topic[:250]))
        self.assertNotEqual(first_topic, second_topic)
        key = "ezzybills-xero-integration"
        first_name = _topic_filename(key, f"  {first_topic}  ")
        second_name = _topic_filename(key, second_topic)
        self.assertLessEqual(len(first_name.encode("utf-8")), FILENAME_MAX_BYTES)
        self.assertNotEqual(first_name, second_name)
        self.assertEqual(
            _topic_filename(key, "  EzzyBills   Xero\n"),
            _topic_filename(key, "ezzybills xero"),
        )
        notes = VAULT_NOTES.read_text(encoding="utf-8")
        self.assertIn(NORMALIZED_TOPIC_RULE, notes)
        self.assertIn("microsoft-ms-102", notes)

    def test_trace_ids_appear_once(self) -> None:
        counts: dict[str, int] = {trace_id: 0 for trace_id in TRACE_IDS}
        for trace_id in _TRACE_HEADING_RE.findall(EVAL_SCENARIOS.read_text(encoding="utf-8")):
            if trace_id in counts:
                counts[trace_id] += 1
        problems = [f"{trace_id} appears {count} times" for trace_id, count in counts.items() if count != 1]
        self.assertEqual([], problems, "; ".join(problems))

    @unittest.skipUnless(os.environ.get(COPY_CHECK_ENV) == "1", "set FREE_RESEARCH_CHECK_COPIES=1 to compare copies")
    def test_repo_live_and_pack_copies_match(self) -> None:
        copies = {
            "repo": SKILL_DIR,
            "live": Path.home() / ".grok" / "skills" / "free-research",
            "pack": Path.home() / "Projects" / "skill-pack" / "grok" / "free-research",
        }
        inventories = {label: _file_inventory(path) for label, path in copies.items()}
        problems: list[str] = []
        relative_paths = sorted(
            set().union(
                *(set(inventory) for inventory in inventories.values()),
                set(COPY_PARITY_FILES),
            )
        )
        for relative in relative_paths:
            present = {label: inventories[label].get(relative) for label in inventories}
            missing = [label for label, digest in present.items() if digest is None]
            if missing:
                problems.append(f"{relative}: missing from {', '.join(missing)}")
                continue
            digests = set(present.values())
            if len(digests) != 1:
                problems.append(f"{relative}: sha256 differs across repo, live, and pack")
        self.assertEqual([], problems, "\n".join(problems))


if __name__ == "__main__":
    unittest.main()
