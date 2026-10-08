"""Pin free-research ceilings, report shape, traces, and opt-in copy parity."""

from __future__ import annotations

import hashlib
import os
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "free-research"
SKILL_MD = SKILL_DIR / "SKILL.md"
TOOL_ROUTING = SKILL_DIR / "references" / "tool-routing.md"
EVAL_SCENARIOS = SKILL_DIR / "references" / "eval-scenarios.md"

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
TRACE_IDS = tuple(f"T{number}" for number in range(1, 18)) + ("L1", "L2")
PARALLEL_RUNS_BALANCED = 1
PARALLEL_EXTRACTS_BALANCED = 2
COPY_CHECK_ENV = "FREE_RESEARCH_CHECK_COPIES"

_PAIR_RE = re.compile(
    r"\b(Exa|Firecrawl|Brave)\b[^≤\n]{0,160}?(?:≤|\bat most\b)\s*(\d+)",
    re.IGNORECASE,
)
_BARE_CEILING_RE = re.compile(r"(?:≤|\bat most\b)\s*(\d+)", re.IGNORECASE)
_MODE_FLAG_RE = re.compile(r"--(free|balanced|deep)\b")
_ROW_MODE_RE = re.compile(r"\*\*(free|balanced|deep)\*\*", re.IGNORECASE)
_BLOCK_TOOL_RE = re.compile(r"^\d+\.\s+\*\*(Exa|Firecrawl|Brave)\*\*")
_TRACE_HEADING_RE = re.compile(r"^#{2,3} ((?:T\d+|L\d+))\.", re.MULTILINE)
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
        relative_paths = sorted(set().union(*(set(inventory) for inventory in inventories.values())))
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
