"""Pin scripts/install.sh: copy, refuse newer files, treg opt-in, check secrets.

The fake claude, grok, and codex binaries append each invocation's argv to a
log outside the repo. They do not talk to a real host.
"""

from __future__ import annotations

import os
import stat
import subprocess
import tempfile
import unittest
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INSTALL = ROOT / "scripts" / "install.sh"
SKILL_SRC = ROOT / "skills" / "free-research"
EXCLUDED_DIRS = {"__pycache__"}
EXCLUDED_FILES = {".DS_Store"}
SAFE_PATH = os.pathsep.join(["/usr/bin", "/bin"])

FAKE_CLI = """#!/bin/sh
{
  printf '%s' "$0"
  for arg in "$@"; do
    printf '\\t%s' "$arg"
  done
  printf '\\n'
} >> "$FAKE_CLI_LOG"
if [ "${1:-}" = "mcp" ] && [ "${2:-}" = "list" ]; then
  if [ -n "${FAKE_MCP_LIST:-}" ] && [ -f "$FAKE_MCP_LIST" ]; then
    cat "$FAKE_MCP_LIST"
  fi
fi
fake_name=$(basename "$0")
if [ "${1:-}" = "mcp" ] && [ "${2:-}" = "add" ]; then
  case " ${FAKE_ADD_FAIL_CLIS:-} " in
    *" $fake_name "*)
      printf '%s\\n' "MCP server treg already exists in user config" >&2
      printf '%s\\n' "Authorization: Bearer ${TREG_TOKEN:-}" >&2
      exit 1
      ;;
  esac
fi
if [ "${1:-}" = "mcp" ] && [ "${2:-}" = "remove" ]; then
  case " ${FAKE_REMOVE_NOTFOUND_CLIS:-} " in
    *" $fake_name "*)
      printf '%s\\n' "No MCP server found with name: treg" >&2
      exit 1
      ;;
  esac
  case " ${FAKE_REMOVE_FAIL_CLIS:-} " in
    *" $fake_name "*)
      printf '%s\\n' "permission denied: Authorization: Bearer ${TREG_TOKEN:-}" >&2
      exit 1
      ;;
  esac
fi
if [ -n "${FAKE_MCP_FAIL:-}" ]; then
  printf '%s\\n' "mcp add failed: Authorization: Bearer ${TREG_TOKEN:-}" >&2
  printf '%s\\n' "notes=${FREE_RESEARCH_NOTES_DIR:-}" >&2
  exit 1
fi
exit 0
"""


def skill_snapshot(root: Path) -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    if not root.exists():
        return files
    for path in root.rglob("*"):
        if not path.is_file() or path.is_symlink():
            continue
        if any(part in EXCLUDED_DIRS for part in path.parts):
            continue
        if path.name in EXCLUDED_FILES:
            continue
        files[path.relative_to(root).as_posix()] = path.read_bytes()
    return files


def repo_files_containing(needle: str) -> list[str]:
    encoded = needle.encode()
    hits: list[str] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.is_symlink():
            continue
        try:
            data = path.read_bytes()
        except OSError:
            continue
        if encoded in data:
            hits.append(str(path.relative_to(ROOT)))
    return hits


class InstallScriptTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name) / "home"
        self.bin_dir = Path(self.tmp.name) / "bin"
        self.home.mkdir()
        self.bin_dir.mkdir()
        self.log_path = Path(self.tmp.name) / "cli.log"
        self.log_path.write_text("")
        self.mcp_list_path = Path(self.tmp.name) / "mcp-list.txt"
        self.mcp_list_path.write_text("")

    def write_fake(self, name: str) -> None:
        path = self.bin_dir / name
        path.write_text(FAKE_CLI)
        path.chmod(path.stat().st_mode | stat.S_IEXEC)

    def write_fakes(self, names: tuple[str, ...] = ("claude", "grok", "codex")) -> None:
        for name in names:
            self.write_fake(name)

    def env(self, **extra: str) -> dict[str, str]:
        clean = {
            key: value
            for key, value in os.environ.items()
            if key
            not in {
                "TREG_TOKEN",
                "FREE_RESEARCH_NOTES_DIR",
                "FAKE_MCP_FAIL",
                "FAKE_ADD_FAIL_CLIS",
                "FAKE_REMOVE_NOTFOUND_CLIS",
                "FAKE_REMOVE_FAIL_CLIS",
                "BASH_ENV",
                "ENV",
                "SHELLOPTS",
                "CDPATH",
            }
        }
        clean["HOME"] = str(self.home)
        clean["PATH"] = os.pathsep.join([str(self.bin_dir), SAFE_PATH])
        clean["FAKE_CLI_LOG"] = str(self.log_path)
        clean["FAKE_MCP_LIST"] = str(self.mcp_list_path)
        clean.update(extra)
        return clean

    def run_install(
        self, args: list[str], **env_extra: str
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["/bin/bash", str(INSTALL), *args],
            cwd=str(ROOT),
            env=self.env(**env_extra),
            capture_output=True,
            text=True,
            check=False,
        )

    def calls_for(self, cli: str) -> list[list[str]]:
        rows: list[list[str]] = []
        for line in self.log_path.read_text().splitlines():
            if not line:
                continue
            parts = line.split("\t")
            if Path(parts[0]).name == cli:
                rows.append(parts[1:])
        return rows

    def mcp_adds(self, cli: str) -> list[list[str]]:
        return [args for args in self.calls_for(cli) if args[:2] == ["mcp", "add"]]

    def all_mcp_adds(self) -> list[tuple[str, list[str]]]:
        found: list[tuple[str, list[str]]] = []
        for line in self.log_path.read_text().splitlines():
            if not line:
                continue
            parts = line.split("\t")
            args = parts[1:]
            if args[:2] == ["mcp", "add"]:
                found.append((Path(parts[0]).name, args))
        return found

    def mcp_writes(self) -> list[tuple[str, str]]:
        """Return (cli, verb) for every mcp add/remove call, in call order."""
        found: list[tuple[str, str]] = []
        for line in self.log_path.read_text().splitlines():
            if not line:
                continue
            parts = line.split("\t")
            args = parts[1:]
            if args[:1] == ["mcp"] and args[1:2] in (["add"], ["remove"]):
                found.append((Path(parts[0]).name, args[1]))
        return found

    def configure_treg_everywhere(self) -> None:
        (self.home / ".claude.json").write_text(
            '{"mcpServers": {"treg": {"type": "http", "url": "https://treg.to/mcp/"}}}\n'
        )
        grok = self.home / ".grok"
        grok.mkdir()
        (grok / "config.toml").write_text('[mcp_servers.treg]\nurl = "https://treg.to/mcp/"\n')
        codex = self.home / ".codex"
        codex.mkdir()
        (codex / "config.toml").write_text(
            '[mcp_servers.treg]\nbearer_token_env_var = "TREG_TOKEN"\n'
        )

    def assert_real_tree(self, dest: Path) -> None:
        self.assertTrue(dest.is_dir(), dest)
        self.assertFalse(dest.is_symlink(), dest)
        self.assertEqual(skill_snapshot(SKILL_SRC), skill_snapshot(dest))
        for path in dest.rglob("*"):
            self.assertFalse(path.is_symlink(), str(path))

    def test_three_hosts_receive_byte_identical_copies(self) -> None:
        self.write_fakes()
        result = self.run_install([])
        self.assertEqual(result.returncode, 0, result.stderr)
        for host in (".claude", ".grok", ".codex"):
            self.assert_real_tree(self.home / host / "skills" / "free-research")

    def test_only_claude_present_names_missing_hosts(self) -> None:
        self.write_fake("claude")
        result = self.run_install([])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_real_tree(self.home / ".claude" / "skills" / "free-research")
        self.assertFalse((self.home / ".grok").exists())
        self.assertFalse((self.home / ".codex").exists())
        self.assertIn("Grok and Codex were not found.", result.stdout)

    def test_config_dir_without_cli_still_receives_skill(self) -> None:
        (self.home / ".grok").mkdir()
        result = self.run_install([])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_real_tree(self.home / ".grok" / "skills" / "free-research")
        self.assertFalse((self.home / ".claude").exists())
        self.assertFalse((self.home / ".codex").exists())
        self.assertIn("Claude Code and Codex were not found.", result.stdout)
        self.assertEqual(self.all_mcp_adds(), [])

    def test_with_treg_sends_mcp_add_and_hides_token(self) -> None:
        self.write_fakes()
        token = "frtok-" + uuid.uuid4().hex
        result = self.run_install(["--with-treg"], TREG_TOKEN=token)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn(token, result.stdout)
        self.assertNotIn(token, result.stderr)
        self.assertEqual(repo_files_containing(token), [])
        self.assertEqual(
            self.mcp_adds("claude"),
            [[
                "mcp",
                "add",
                "--scope",
                "user",
                "--transport",
                "http",
                "treg",
                "https://treg.to/mcp/",
                "-H",
                f"Authorization: Bearer {token}",
            ]],
        )
        self.assertEqual(
            self.mcp_adds("grok"),
            [[
                "mcp",
                "add",
                "treg",
                "https://treg.to/mcp/",
                "-H",
                f"Authorization: Bearer {token}",
            ]],
        )
        codex_adds = self.mcp_adds("codex")
        self.assertEqual(
            codex_adds,
            [[
                "mcp",
                "add",
                "treg",
                "--url",
                "https://treg.to/mcp/",
                "--bearer-token-env-var",
                "TREG_TOKEN",
            ]],
        )
        self.assertNotIn(token, " ".join(codex_adds[0]))

    def test_with_treg_token_unset_skips_mcp(self) -> None:
        self.write_fakes()
        result = self.run_install(["--with-treg"])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.all_mcp_adds(), [])
        self.assertIn("TREG_TOKEN is missing.", result.stdout)
        self.assert_real_tree(self.home / ".claude" / "skills" / "free-research")

    def test_newer_destination_file_is_kept_unless_force(self) -> None:
        self.write_fakes()
        first = self.run_install([])
        self.assertEqual(first.returncode, 0, first.stderr)
        dest = self.home / ".claude" / "skills" / "free-research" / "SKILL.md"
        marker = b"local edit marker\n"
        dest.write_bytes(marker)
        ahead = dest.stat().st_mtime + (10 * 365 * 24 * 3600)
        os.utime(dest, (ahead, ahead))
        second = self.run_install([])
        combined = second.stdout + second.stderr
        self.assertNotEqual(second.returncode, 0)
        self.assertEqual(dest.read_bytes(), marker)
        self.assertIn("refusing to overwrite newer file: SKILL.md", combined)
        self.log_path.write_text("")
        forced = self.run_install(["--force"])
        self.assertEqual(forced.returncode, 0, forced.stderr)
        self.assertEqual(dest.read_bytes(), (SKILL_SRC / "SKILL.md").read_bytes())

    def test_already_configured_treg_is_not_added_again_without_force(self) -> None:
        self.write_fakes()
        (self.home / ".claude.json").write_text(
            '{"mcpServers": {"treg": {"type": "http", "url": "https://treg.to/mcp/"}}}\n'
        )
        grok = self.home / ".grok"
        grok.mkdir()
        (grok / "config.toml").write_text("[mcp_servers.treg]\nurl = \"https://treg.to/mcp/\"\n")
        codex = self.home / ".codex"
        codex.mkdir()
        (codex / "config.toml").write_text(
            "[mcp_servers.treg]\nbearer_token_env_var = \"TREG_TOKEN\"\n"
        )
        token = "frtok-" + uuid.uuid4().hex
        result = self.run_install(["--with-treg"], TREG_TOKEN=token)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.all_mcp_adds(), [])
        self.assertNotIn(token, result.stdout + result.stderr)
        self.log_path.write_text("")
        forced = self.run_install(["--with-treg", "--force"], TREG_TOKEN=token)
        self.assertEqual(forced.returncode, 0, forced.stderr)
        self.assertNotIn(token, forced.stdout + forced.stderr)
        self.assertEqual(
            sorted(name for name, _args in self.all_mcp_adds()),
            ["claude", "codex", "grok"],
        )

    def test_force_removes_then_adds_for_each_configured_host(self) -> None:
        self.write_fakes()
        self.configure_treg_everywhere()
        token = "frtok-" + uuid.uuid4().hex
        result = self.run_install(["--with-treg", "--force"], TREG_TOKEN=token)
        self.assertEqual(result.returncode, 0, result.stderr)
        for cli in ("claude", "grok", "codex"):
            self.assertEqual(
                [verb for name, verb in self.mcp_writes() if name == cli],
                ["remove", "add"],
                cli,
            )
        self.assertEqual(
            [args for args in self.calls_for("claude") if args[:2] == ["mcp", "remove"]],
            [["mcp", "remove", "treg", "-s", "user"]],
        )
        for cli in ("grok", "codex"):
            self.assertEqual(
                [args for args in self.calls_for(cli) if args[:2] == ["mcp", "remove"]],
                [["mcp", "remove", "treg"]],
            )
        self.assertIn("Claude Code: treg MCP replaced", result.stdout)
        self.assertIn("Grok: treg MCP replaced", result.stdout)
        self.assertIn("Codex: treg MCP replaced", result.stdout)
        self.assertNotIn(token, result.stdout + result.stderr)

    def test_force_without_existing_treg_does_not_remove(self) -> None:
        self.write_fakes()
        result = self.run_install(["--with-treg", "--force"], TREG_TOKEN="frtok-x")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            sorted(self.mcp_writes()),
            [("claude", "add"), ("codex", "add"), ("grok", "add")],
        )

    def test_failed_remove_is_ignored_only_when_server_was_missing(self) -> None:
        self.write_fakes()
        self.configure_treg_everywhere()
        token = "frtok-" + uuid.uuid4().hex
        missing = self.run_install(
            ["--with-treg", "--force"],
            TREG_TOKEN=token,
            FAKE_REMOVE_NOTFOUND_CLIS="claude",
        )
        self.assertEqual(missing.returncode, 0, missing.stderr)
        self.assertEqual(
            [verb for name, verb in self.mcp_writes() if name == "claude"],
            ["remove", "add"],
        )
        self.log_path.write_text("")
        broken = self.run_install(
            ["--with-treg", "--force"],
            TREG_TOKEN=token,
            FAKE_REMOVE_FAIL_CLIS="claude",
        )
        combined = broken.stdout + broken.stderr
        self.assertNotEqual(broken.returncode, 0)
        self.assertEqual(
            [verb for name, verb in self.mcp_writes() if name == "claude"], ["remove"]
        )
        self.assertIn("Claude Code: treg MCP FAILED (remove)", broken.stdout)
        self.assertEqual(
            [verb for name, verb in self.mcp_writes() if name in ("grok", "codex")],
            ["remove", "add", "remove", "add"],
        )
        self.assertNotIn(token, combined)

    def test_one_host_add_failure_does_not_stop_other_hosts(self) -> None:
        self.write_fakes()
        self.configure_treg_everywhere()
        token = "frtok-" + uuid.uuid4().hex
        result = self.run_install(
            ["--with-treg", "--force"],
            TREG_TOKEN=token,
            FAKE_ADD_FAIL_CLIS="claude",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(
            sorted(name for name, _args in self.all_mcp_adds()),
            ["claude", "codex", "grok"],
        )
        self.assertIn("claude mcp add failed.", result.stderr)
        self.assertIn("Claude Code: treg MCP FAILED (add)", result.stdout)
        self.assertIn("Grok: treg MCP replaced", result.stdout)
        self.assertIn("Codex: treg MCP replaced", result.stdout)
        self.assertNotIn(token, result.stdout + result.stderr)

    def test_token_never_appears_in_output_across_mcp_paths(self) -> None:
        self.write_fakes()
        self.configure_treg_everywhere()
        token = "frtok-" + uuid.uuid4().hex
        scenarios = (
            {},
            {"FAKE_ADD_FAIL_CLIS": "claude grok codex"},
            {"FAKE_REMOVE_FAIL_CLIS": "claude grok codex"},
            {"FAKE_REMOVE_NOTFOUND_CLIS": "claude grok codex"},
            {"FAKE_MCP_FAIL": "1"},
        )
        for extra in scenarios:
            with self.subTest(extra=extra):
                result = self.run_install(
                    ["--with-treg", "--force"], TREG_TOKEN=token, **extra
                )
                self.assertNotIn(token, result.stdout + result.stderr)
        self.assertEqual(repo_files_containing(token), [])

    def test_mcp_add_error_redacts_token_and_notes_dir(self) -> None:
        self.write_fakes()
        token = "frtok-" + uuid.uuid4().hex
        notes = "/fr-notes-" + uuid.uuid4().hex
        result = self.run_install(
            ["--with-treg"],
            TREG_TOKEN=token,
            FREE_RESEARCH_NOTES_DIR=notes,
            FAKE_MCP_FAIL="1",
        )
        combined = result.stdout + result.stderr
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("mcp add failed", combined)
        self.assertNotIn(token, combined)
        self.assertNotIn(notes, combined)
        self.assertEqual(repo_files_containing(token), [])
        self.assertEqual(repo_files_containing(notes), [])

    def test_check_never_prints_token_or_notes_dir(self) -> None:
        self.write_fakes()
        token = "frtok-" + uuid.uuid4().hex
        notes = "/fr-notes-" + uuid.uuid4().hex
        self.mcp_list_path.write_text(
            "treg\n"
            f"Authorization: Bearer {token}\n"
            f"notes={notes}\n"
        )
        (self.home / ".claude.json").write_text(
            '{"mcpServers": {"treg": {"headers": {"Authorization": "Bearer '
            + token
            + '"}}}}\n'
        )
        plugin = self.home / ".grok" / "installed-plugins" / "free-research-skill-abc"
        plugin.mkdir(parents=True)
        (plugin / "SKILL.md").write_text(token + "\n" + notes + "\n")
        skill = self.home / ".grok" / "skills" / "free-research"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text('---\nname: free-research\nversion: "9.9.9"\n---\n\n')
        last30 = self.home / ".claude" / "skills" / "last30days"
        last30.mkdir(parents=True)
        (last30 / "SKILL.md").write_text("name: last30days\n")
        result = self.run_install(
            ["--check"],
            TREG_TOKEN=token,
            FREE_RESEARCH_NOTES_DIR=notes,
        )
        combined = result.stdout + result.stderr
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn(token, combined)
        self.assertNotIn(notes, combined)
        self.assertIn("Next steps", result.stdout)
        self.assertIn("FREE_RESEARCH_NOTES_DIR: set", result.stdout)
        blocks = _status_blocks(result.stdout)
        self.assertIn("skill: not installed", blocks["Claude Code"])
        self.assertIn("last30days: present", blocks["Claude Code"])
        self.assertIn("treg MCP: configured", blocks["Claude Code"])
        self.assertIn("skill: installed 9.9.9", blocks["Grok"])
        self.assertIn("marketplace duplicate: yes", blocks["Grok"])
        self.assertIn("free-research-skill-abc", blocks["Grok"])
        self.assertIn("skill: not installed", blocks["Codex"])
        self.assertIn("treg MCP: configured", blocks["Codex"])
        self.assertFalse((self.home / ".codex").exists())
        self.assertEqual(self.all_mcp_adds(), [])

    def test_check_codex_token_env_unset_empty_and_set(self) -> None:
        codex = self.home / ".codex"
        codex.mkdir()
        env_name = "FREE_RESEARCH_TEST_TOKEN_" + uuid.uuid4().hex
        config_secret = "config-secret-" + uuid.uuid4().hex
        (codex / "config.toml").write_text(
            '[mcp_servers.other]\n'
            'bearer_token_env_var = "OTHER_TOKEN"\n'
            '[mcp_servers.treg]\n'
            f'bearer_token_env_var = "{env_name}"\n'
            f'url = "https://example.test/{config_secret}"\n'
            '[unrelated]\n'
            'bearer_token_env_var = "UNRELATED_TOKEN"\n'
        )
        token = "frtok-" + uuid.uuid4().hex
        for value in (None, "", token):
            with self.subTest(state="unset" if value is None else "set" if value else "empty"):
                extra = {} if value is None else {env_name: value}
                result = self.run_install(["--check"], **extra)
                self.assertEqual(result.returncode, 0, result.stderr)
                combined = result.stdout + result.stderr
                self.assertNotIn(token, combined)
                self.assertNotIn(config_secret, combined)
                block = _status_blocks(result.stdout)["Codex"]
                next_steps = result.stdout.split("Next steps\n", 1)[1]
                if value:
                    self.assertIn(f"treg MCP: configured ({env_name} set)", block)
                    self.assertNotIn(f"Export {env_name}", next_steps)
                else:
                    self.assertIn(
                        f"treg MCP: configured, but {env_name} is not set in this environment "
                        "(Codex cannot authenticate)",
                        block,
                    )
                    self.assertIn(
                        f"Export {env_name} in the environment where Codex reads it",
                        next_steps,
                    )
        self.assertEqual(self.all_mcp_adds(), [])

    def test_check_grok_notes_dir_set_via_config_hides_value(self) -> None:
        grok = self.home / ".grok"
        grok.mkdir()
        notes = "/config-notes-" + uuid.uuid4().hex
        env_notes = "/env-notes-" + uuid.uuid4().hex
        for key in ("FREE_RESEARCH_NOTES_DIR", '"FREE_RESEARCH_NOTES_DIR"'):
            (grok / "config.toml").write_text(
                '[shell_environment_policy.set]\n'
                f'{key} = "{notes}"\n'
            )
            for extra in ({}, {"FREE_RESEARCH_NOTES_DIR": env_notes}):
                with self.subTest(key=key, env_set=bool(extra)):
                    result = self.run_install(["--check"], **extra)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    combined = result.stdout + result.stderr
                    self.assertNotIn(notes, combined)
                    self.assertNotIn(env_notes, combined)
                    self.assertIn(
                        "FREE_RESEARCH_NOTES_DIR: set via Grok config",
                        _status_blocks(result.stdout)["Grok"],
                    )
                    self.assertNotIn(
                        "FREE_RESEARCH_NOTES_DIR",
                        result.stdout.split("Next steps\n", 1)[1],
                    )
        self.assertEqual(self.all_mcp_adds(), [])

    def test_help_lists_modes(self) -> None:
        result = self.run_install(["--help"])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--check", result.stdout)
        self.assertIn("--with-treg", result.stdout)
        self.assertIn("--force", result.stdout)
        self.assertIn("Usage:", result.stdout)


def _status_blocks(stdout: str) -> dict[str, str]:
    blocks: dict[str, str] = {}
    current: str | None = None
    lines: list[str] = []
    for line in stdout.splitlines():
        if line.startswith("== ") and line.endswith(" =="):
            if current is not None:
                blocks[current] = "\n".join(lines)
            current = line[3:-3]
            lines = []
            continue
        if current is not None and line == "Next steps":
            blocks[current] = "\n".join(lines)
            current = None
            lines = []
            continue
        lines.append(line)
    if current is not None:
        blocks[current] = "\n".join(lines)
    return blocks


if __name__ == "__main__":
    unittest.main()
