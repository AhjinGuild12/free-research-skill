# /free-research

Free-first multi-source research for AI agents. Community pulse from [last30days](https://github.com/mvanhorn/last30days-skill), then TinyFish search and fetch. Paid escalation waits on the remaining-gap gate, and Firecrawl reads pages the free fetch could not.

This repo is a skill, not a search engine. It does not bundle last30days or TinyFish.

The runtime spec lives in [skills/free-research/SKILL.md](skills/free-research/SKILL.md).

## Install

| Surface | Install |
| --- | --- |
| **Claude Code** | `/plugin marketplace add AhjinGuild12/free-research-skill` then `/plugin install free-research` |
| **Grok** (xAI Build CLI) | `grok plugin marketplace add AhjinGuild12/free-research-skill` then `grok plugin install free-research` |
| **Codex, Cursor, Copilot, Gemini CLI, or any [Agent Skills](https://agentskills.io) host** | `npx skills add AhjinGuild12/free-research-skill -g` |

Grok also accepts a direct install:

```bash
grok plugin install AhjinGuild12/free-research-skill
```

Add `--trust` to skip the install confirmation. Update later with `grok plugin update free-research` or `npx skills update free-research -g`.

Claude Code does not dedupe marketplace plugin vs `npx skills`. Use one install method per host or `/free-research` will show twice.

## Prerequisites

A full free run needs both companions. This plugin does not include them.

1. **last30days** — community pulse (Reddit, X, HN, YouTube, and more)

   ```text
   /plugin marketplace add mvanhorn/last30days-skill
   /plugin install last30days
   ```

   or `npx skills add mvanhorn/last30days-skill -g`

2. **TinyFish MCP** — free `search` + `fetch_content`

   - Grok: `grok plugin install tinyfish --trust`, then `/mcps` → tinyfish → Authenticate
   - Claude Code: `claude mcp add --transport http tinyfish https://agent.tinyfish.ai/mcp`

If last30days or TinyFish is missing, the skill still loads. It labels the gap under **Tools Used** and continues with whatever free host tools are available. It does not pretend those tools ran.

**Exa**, **Firecrawl**, and **Brave Search** are optional paid layers for `--balanced` / `--deep` only. They are not required and are never called in free mode.

## Examples

### Free mode — last30days + TinyFish

```text
/free-research Claude Code vs Codex
```

Default. Community pulse first, then TinyFish search (3–5 angles) and `fetch_content` on the top pages. No paid APIs.

Tools Used looks like:

```text
- last30days — community pulse (free)
- TinyFish search × 4 — discovery angles (free)
- TinyFish fetch_content — 8 pages (free)
- Exa — not used
- Firecrawl — not used
- Brave — not used
```

### Deep mode — escalate only if the free layer is thin

```text
/free-research --deep Cloudflare Agents Week
```

Same free layer first. If remaining gaps are still open, paid tools run in this order: Exa, then Firecrawl, then Brave. Deep ceilings are Exa ≤4, Firecrawl ≤6 leftover ops, and Brave ≤2. The run stops when remaining gaps are empty. New URLs from Exa or Brave are still fetched with TinyFish when that fetch is free. Firecrawl reads leftover pages the free fetch could not.

Tools Used after a real escalate:

```text
- last30days — community pulse (free)
- TinyFish search × 5 — discovery angles (free)
- TinyFish fetch_content — 10 pages (free)
- Exa — gap queries on the launch timeline (deep, ≤4)
- Firecrawl — leftover pages the free fetch could not read (deep, ≤6 leftover ops)
- Brave — independent index after Firecrawl (deep, ≤2)
```

If the free layer already closed the gaps, the report says so and does not call Exa, Firecrawl, or Brave.

### Force free, even when coverage is thin

```text
/free-research --free what's happening with OpenClaw
```

Never calls Exa, Firecrawl, `firecrawl --status`, Brave, or `parallel-cli`. If the pass is thin, the report offers `--balanced` or `--deep`.

## Modes

| Mode | Tools | Credits |
|------|--------|---------|
| **free** (default) | last30days + TinyFish only (host web tools if TinyFish is down) | Zero paid |
| **balanced** | free layer + sequential paid tools on remaining gaps (Exa ≤2, Firecrawl ≤3 leftover ops, Brave ≤1) | Minimal paid |
| **deep** | same order; Exa ≤4, Firecrawl ≤6 leftover ops, Brave ≤2; stop when remaining gaps empty | Paid, capped |

This table mirrors [skills/free-research/SKILL.md](skills/free-research/SKILL.md). That file owns these Exa, Firecrawl, and Brave ceilings. [skills/free-research/references/tool-routing.md](skills/free-research/references/tool-routing.md) owns the `parallel-cli` caps.

## Run notes

A run can read and write a version-2 note when `FREE_RESEARCH_NOTES_DIR` is set. The value is the absolute path of the project folder that contains `runs/`. Grok supplies it through `[shell_environment_policy.set]` in the user Grok config (Grok user guide `26-config-reference.md`). The skill reads that one variable by name. Unset, empty, relative, missing, or a resolved `runs/` path that escapes the folder means the run skips the note. There is no fallback location. The run never prints the value of `FREE_RESEARCH_NOTES_DIR`. The filesystem-path ban is the vault location and the vault-note line only. That line does not include the vault location or a filesystem path. It says only whether a note was read, written, or skipped, and why. Other Tools Used lines may name a tool output path, including the Firecrawl output path.

```toml
[shell_environment_policy.set]
FREE_RESEARCH_NOTES_DIR = "/absolute/path/to/the-project-folder"
```

Check the notes without writing or fetching:

```bash
python3 scripts/lint_run_notes.py /absolute/path/to/the-project-folder/runs
```

`scripts/lint_run_notes.py` is read-only. Exit 0 means no version-2 errors. Legacy-note problems are warnings and do not fail that exit.

## What this is not

- Not last30days. Install that separately for a pure community pass.
- Not TinyFish. Auth lives on the TinyFish MCP, not in this repo.
- Not an Exa, Firecrawl, or Brave wrapper. Those run only after the decision gate, and only in `--balanced` / `--deep`.
- Not a bundled search engine, MCP server, or `.mcpb` / `.skill` release factory.

## Manual (developer)

Copy the repo skill directory onto the live skills-folder copy and the skill-pack copy, including `references/` and `scripts/`. `scripts/run_note.py` is the skill-local note helper. Do not symlink this repo over a newer live tree. The installed plugin checkout is a separate publish and is not updated by that copy.

```bash
git clone https://github.com/AhjinGuild12/free-research-skill.git
```

```bash
python3 -m unittest tests.test_plugin_contract
grok plugin validate .
```

## License

MIT. See [LICENSE](LICENSE).
