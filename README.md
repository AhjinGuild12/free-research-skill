# /free-research

Free-first multi-source research for AI agents. Community pulse from [last30days](https://github.com/mvanhorn/last30days-skill), then TinyFish search and fetch. Escalate to Exa or Brave only when the free layer is thin.

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

**Brave Search** and **Exa** are optional paid layers for `--balanced` / `--deep` only. They are not required and are never called in free mode.

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
- Brave — not used
```

### Deep mode — escalate only if the free layer is thin

```text
/free-research --deep Cloudflare Agents Week
```

Same free layer first. If coverage still has holes, selective Exa, then Brave Search as an independent index. New URLs still get fetched with TinyFish (free).

Tools Used after a real escalate:

```text
- last30days — community pulse (free)
- TinyFish search × 5 — discovery angles (free)
- TinyFish fetch_content — 10 pages (free)
- Exa — 2 gap queries on launch timeline (deep)
- Brave — independent index after Exa still missed X coverage
```

If free mode is already enough, the report says so and does not burn Brave credits.

### Force free, even when coverage is thin

```text
/free-research --free what's happening with OpenClaw
```

Never calls Exa or Brave. If the pass is thin, the report offers `--balanced` or `--deep`.

## Modes

| Mode | Tools | Credits |
| --- | --- | --- |
| **free** (default) | last30days + TinyFish only | Zero paid |
| **balanced** | free layer + selective Exa on high-value gaps | Minimal paid |
| **deep** | last30days + TinyFish + Exa + Brave if needed | Full |

## What this is not

- Not last30days. Install that separately for a pure community pass.
- Not TinyFish. Auth lives on the TinyFish MCP, not in this repo.
- Not a Brave or Exa wrapper. Those run only after the decision gate, and only in `--balanced` / `--deep`.
- Not a bundled search engine, MCP server, or `.mcpb` / `.skill` release factory.

## Manual (developer)

```bash
git clone https://github.com/AhjinGuild12/free-research-skill.git
ln -s "$(pwd)/free-research-skill/skills/free-research" ~/.grok/skills/free-research
```

```bash
python3 -m unittest tests.test_plugin_contract
grok plugin validate .
```

## License

MIT. See [LICENSE](LICENSE).
