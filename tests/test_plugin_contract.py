"""Lockstep plugin contract for the free-research skill repo."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_MD = ROOT / "skills" / "free-research" / "SKILL.md"
VERSION_RE = re.compile(r'^version:\s*"([^"]+)"\s*$', re.MULTILINE)


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _skill_version() -> str:
    match = VERSION_RE.search(SKILL_MD.read_text(encoding="utf-8"))
    if not match:
        raise AssertionError("SKILL.md version frontmatter not found")
    return match.group(1)


class TestPluginContract(unittest.TestCase):
    def test_skill_lives_under_skills_tree(self) -> None:
        self.assertTrue(SKILL_MD.is_file())
        self.assertTrue((ROOT / "skills" / "free-research" / "references" / "tool-routing.md").is_file())

    def test_grok_plugin_manifest_uses_repo_skill_root(self) -> None:
        manifest = _json(ROOT / ".grok-plugin" / "plugin.json")
        self.assertEqual("free-research", manifest["name"])
        self.assertEqual("./skills/", manifest["skills"])

    def test_claude_plugin_omits_skills_key(self) -> None:
        manifest = _json(ROOT / ".claude-plugin" / "plugin.json")
        self.assertEqual("free-research", manifest["name"])
        self.assertNotIn("skills", manifest)

    def test_grok_marketplace_points_at_git_url(self) -> None:
        marketplace = _json(ROOT / ".grok-plugin" / "marketplace.json")
        plugins = {plugin["name"]: plugin for plugin in marketplace.get("plugins") or []}
        self.assertEqual("free-research-skill", marketplace["name"])
        self.assertIn("free-research", plugins)
        self.assertEqual(
            {
                "source": "url",
                "url": "https://github.com/AhjinGuild12/free-research-skill.git",
            },
            plugins["free-research"]["source"],
        )

    def test_claude_marketplace_has_current_schema_shape(self) -> None:
        marketplace = _json(ROOT / ".claude-plugin" / "marketplace.json")
        self.assertNotIn("$schema", marketplace)
        self.assertNotIn("description", marketplace)
        self.assertIn("metadata", marketplace)
        self.assertIn("description", marketplace["metadata"])
        plugins = marketplace.get("plugins") or []
        self.assertEqual(1, len(plugins))
        self.assertEqual("./", plugins[0]["source"])
        self.assertEqual("free-research", plugins[0]["name"])

    def test_grok_marketplace_has_current_schema_shape(self) -> None:
        marketplace = _json(ROOT / ".grok-plugin" / "marketplace.json")
        self.assertNotIn("$schema", marketplace)
        self.assertNotIn("metadata", marketplace)
        self.assertIsInstance(marketplace["description"], str)

    def test_versions_match_across_manifests(self) -> None:
        version = _skill_version()
        self.assertEqual("1.3.0", version)
        self.assertEqual(version, _json(ROOT / ".claude-plugin" / "plugin.json")["version"])
        self.assertEqual(version, _json(ROOT / ".grok-plugin" / "plugin.json")["version"])
        claude_plugins = _json(ROOT / ".claude-plugin" / "marketplace.json")["plugins"]
        grok_plugins = _json(ROOT / ".grok-plugin" / "marketplace.json")["plugins"]
        self.assertEqual(version, claude_plugins[0]["version"])
        self.assertEqual(version, grok_plugins[0]["version"])


if __name__ == "__main__":
    unittest.main()
