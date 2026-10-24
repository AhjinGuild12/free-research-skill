# /free-research

Free-first multi-source research for AI agents. Community pulse from [last30days](https://github.com/mvanhorn/last30days-skill), then TinyFish MCP, TinyFish via treg, or host search and fetch. Paid escalation waits on the remaining-gap gate: treg first, then Exa, Firecrawl, Brave, and opted-in `parallel-cli`.

This repo is a skill, not a search engine. It does not bundle last30days or TinyFish.

The runtime spec lives in [skills/free-research/SKILL.md](skills/free-research/SKILL.md).

## Install

| Surface | Install |
| --- | --- |
| **Claude Code** | Copy `skills/free-research/` from this checkout to `~/.claude/skills/free-research/` (commands below) |
| **Grok** (xAI Build CLI) | `grok plugin marketplace add AhjinGuild12/free-research-skill` then `grok plugin install free-research` |
| **Codex, Cursor, Copilot, Gemini CLI, or any [Agent Skills](https://agentskills.io) host** | `npx skills add AhjinGuild12/free-research-skill -g` |

From the repo root, install the complete skill tree for Claude Code:

```bash
mkdir -p ~/.claude/skills/free-research
cp -R skills/free-research/. ~/.claude/skills/free-research/
```

Include `references/` and `scripts/`. Inspect an existing destination for newer edits before replacing it. Start a new Claude Code session and run `/free-research <topic>`. Updates use the same copy after pulling this repo.

Grok also accepts a direct install:

```bash
grok plugin install AhjinGuild12/free-research-skill
```

Add `--trust` to skip the install confirmation. Update later with `grok plugin update free-research` or `npx skills update free-research -g`.

Claude Code does not dedupe copy-out, marketplace plugin, and `npx skills` installs. Use one install method per host or `/free-research` will show twice. This setup uses copy-out; remove an older duplicate through its original install method.

## Prerequisites

A full free run needs both companions. This plugin does not include them.

1. **last30days** — community pulse (Reddit, X, HN, YouTube, and more)

   ```text
   /plugin marketplace add mvanhorn/last30days-skill
   /plugin install last30days
   ```

   or `npx skills add mvanhorn/last30days-skill -g`

2. **TinyFish MCP or treg** - free search and fetch

   - Grok: `grok plugin install tinyfish --trust`, then `/mcps` → tinyfish → Authenticate
   - Claude Code: `claude mcp add --transport http tinyfish https://agent.tinyfish.ai/mcp`
   - Or use an already connected treg MCP. Its allowlisted TinyFish search, fetch, news, and publications endpoints need no key and must be catalog-priced at zero. On Grok, TinyFish MCP stays first; treg is fallback. This repo does not install or authenticate treg.

If last30days fails, or both TinyFish MCP and treg are unavailable, the skill still loads. It labels the gap under **Tools Used** and continues with free host tools. It does not pretend those tools ran.

**treg paid endpoints**, **Exa**, **Firecrawl**, and **Brave Search** are optional paid layers for `--balanced` / `--deep` only. They never run in free mode. treg verifies price before each call and records actual cost or a labeled catalog estimate; an unexpected charge on a free endpoint stops treg for that run and switches to host web.

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

Same free layer first, including leftover free fetches. If remaining gaps are still open, paid tools run in this order: treg, Exa, Firecrawl, Brave, then opted-in `parallel-cli`. Limits are in the Modes table below. The run stops when gaps are empty. New URLs are still fetched free when possible. Missing, unauthenticated, empty, or out-of-balance treg falls through to Exa. Firecrawl reads leftover pages the free fetch could not.

Tools Used after a real escalate:

```text
- last30days — community pulse (free)
- TinyFish search × 5 — discovery angles (free)
- TinyFish fetch_content — 10 pages (free)
- treg paid - skipped: no eligible priced route for this gap
- Exa — gap queries on the launch timeline (deep, ≤4)
- Firecrawl — leftover pages the free fetch could not read (deep, ≤6 leftover ops)
- Brave — independent index after Firecrawl (deep, ≤2)
```

If the free layer already closed the gaps, the report says treg paid was skipped, makes no `balance` call, and does not call Exa, Firecrawl, or Brave.

When Claude Code uses treg's free layer, Tools Used names each endpoint under `TinyFish via treg (free)` with cost USD 0 or a labeled catalog estimate, plus the treg spend total. A paid person gap might use `anyapi.x.search.posts` after a catalog price check; it lists the actual cost and stops the ladder if a usable body closes the gap. Search snippets remain leads.

### Force free, even when coverage is thin

```text
/free-research --free what's happening with OpenClaw
```

Never calls treg paid endpoints, `balance`, Exa, Firecrawl, `firecrawl --status`, Brave, or `parallel-cli`. If the pass is thin, the report offers `--balanced` or `--deep`.

## Modes

| Mode | Tools | Credits |
|------|--------|---------|
| **free** (default) | last30days + TinyFish MCP or treg free allowlist, then host web | Zero paid; treg ≤0 calls / USD 0.00 total / USD 0.00 per call (paid endpoints) |
| **balanced** | free layer + sequential paid tools on remaining gaps (treg ≤4 calls / USD 0.05 total / USD 0.02 per call; Exa ≤2, Firecrawl ≤3 leftover ops, Brave ≤1) | Minimal paid |
| **deep** | same order; treg ≤10 calls / USD 0.25 total / USD 0.02 per call; Exa ≤4, Firecrawl ≤6 leftover ops, Brave ≤2; stop when remaining gaps empty | Paid, capped |

This table mirrors [skills/free-research/SKILL.md](skills/free-research/SKILL.md), the single owner of treg, Exa, Firecrawl, and Brave ceilings. treg limits count paid-endpoint attempts, including failures; free-allowlist calls do not consume that quota. [skills/free-research/references/tool-routing.md](skills/free-research/references/tool-routing.md) owns the `parallel-cli` caps.

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

`scripts/lint_run_notes.py` is read-only and is a repository tool. It loads the topic codec from `skills/free-research/scripts/run_note.py` in this checkout. Exit 0 means no version-2 errors. Legacy-note problems are warnings and do not fail that exit. Copying the linter file without that helper fails with one line, `lint_run_notes: run-note helper is missing from the skill tree`, and no traceback.

## What this is not

- Not last30days. Install that separately for a pure community pass.
- Not TinyFish. Auth lives on the TinyFish MCP, not in this repo.
- Not an Exa, Firecrawl, or Brave wrapper. Those run only after the decision gate, and only in `--balanced` / `--deep`.
- Not a bundled search engine, MCP server, or `.mcpb` / `.skill` release factory.

## Manual (developer)

Keep all six copies in sync: repo (`skills/free-research/`), Claude Code (`~/.claude/skills/free-research`), Grok live (`~/.grok/skills/free-research`), Grok pack (`~/Projects/skill-pack/grok/free-research`), Codex (`~/.codex/skills/free-research`), and Codex pack (`~/Projects/skill-pack/codex/free-research`). Copy the complete skill tree, including `references/` and `scripts/`. `scripts/run_note.py` is the skill-local note helper. Do not symlink this repo over a newer live tree. The installed plugin checkout is a separate publish and is not updated by that copy.

```bash
git clone https://github.com/AhjinGuild12/free-research-skill.git
```

```bash
python3 -m unittest tests.test_plugin_contract
grok plugin validate .
```

## License

MIT. See [LICENSE](LICENSE).
