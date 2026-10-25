# /free-research

Free-first multi-source research for AI agents. Community pulse from [last30days](https://github.com/mvanhorn/last30days-skill), then treg's zero-priced TinyFish allowlist, TinyFish MCP, and host search and fetch in that fallback order on every host. Paid escalation waits on the remaining-gap gate: treg first, then Exa, Firecrawl, Brave, and opted-in `parallel-cli`.

This repo is a skill, not a search engine. It does not bundle last30days or TinyFish.

The runtime spec lives in [skills/free-research/SKILL.md](skills/free-research/SKILL.md).

## Install

On a Mac, run these from the repo root:

```bash
scripts/install.sh --check
scripts/install.sh --with-treg
scripts/install.sh --check
```

`--check` reports each host's installed skill version, last30days presence, treg MCP configuration, older duplicate installs, and whether `FREE_RESEARCH_NOTES_DIR` is set. It reports presence only and never prints that variable's value or a token. Check mode does not install or change anything.

`scripts/install.sh` copies the complete `skills/free-research/` tree, including `references/` and `scripts/`, into each detected host's skills folder:

| Host | Install method | Skill destination | Detected by |
| --- | --- | --- | --- |
| Claude Code | `scripts/install.sh` | `~/.claude/skills/free-research/` | `claude` on PATH or `~/.claude` |
| Grok | `scripts/install.sh` | `~/.grok/skills/free-research/` | `grok` on PATH or `~/.grok` |
| Codex | `scripts/install.sh` | `~/.codex/skills/free-research/` | `codex` on PATH or `~/.codex` |
| Gemini (agy) | `scripts/install.sh` | `~/.gemini/skills/free-research/` | `agy` on PATH or `~/.gemini` |
| any Agent Skills host | `scripts/install.sh` | `~/.agents/skills/free-research/` | Existing `~/.agents/skills`, or explicit `--agents-dir PATH` |

`--agents-dir PATH` selects and enables a custom shared skills directory, creating it if needed. Without that flag, an absent `~/.agents/skills` is skipped quietly. Gemini's Antigravity CLI (`agy`) loads skills from `~/.gemini/skills`. Copies are regular files, without symlinks. The installer names and refuses a destination file newer than the repo copy unless you pass `--force`; inspect and reconcile those edits before forcing an update.

`--with-treg` also adds the treg MCP connection through each available host CLI. It reads `TREG_TOKEN` from the environment; supply the token there before running it. The token is never printed or stored in the repo or skill files. Codex stores an environment-variable reference; Claude Code, Grok, and Gemini (agy) store the auth header in their own user config. A missing token leaves MCP setup pending, without making MCP add calls. An existing treg configuration is skipped unless `--force` is supplied. A detected config directory without its CLI can receive the skill copy, but MCP setup needs that host CLI. The shared Agent Skills target receives files only; each agent must have treg MCP configured itself. Plain `scripts/install.sh` copies the skill without configuring treg.

`--force` permits replacement of newer destination files and, with `--with-treg`, replacement of an existing treg MCP configuration. It is an explicit overwrite choice, not needed for an ordinary update. After pulling repo updates, repeat the check/install/check flow and start a new host session.

**Grok duplicate warning:** the marketplace plugin can leave an older v1.0.0 install alongside the native skill copy. Check mode flags that duplicate; removal stays your choice through its original install method. Use one install method per host to avoid duplicate `/free-research` commands. The script does not update the separate skill-pack trees; keep the copy-parity workflow below.

Other [Agent Skills](https://agentskills.io) hosts can use the shared skills folder through this macOS installer, or `npx skills add AhjinGuild12/free-research-skill -g`. Install last30days with `npx skills add mvanhorn/last30days-skill -g`, or copy an existing last30days skill folder into each host's skills directory.

## Prerequisites

A full free run needs both companions. This plugin does not include them.

1. **last30days** — community pulse (Reddit, X, HN, YouTube, and more)

   ```text
   /plugin marketplace add mvanhorn/last30days-skill
   /plugin install last30days
   ```

   or `npx skills add mvanhorn/last30days-skill -g`

2. **treg, with TinyFish MCP fallback** - free search and fetch

   - Grok: `grok plugin install tinyfish --trust`, then `/mcps` → tinyfish → Authenticate
   - Claude Code: `claude mcp add --transport http tinyfish https://agent.tinyfish.ai/mcp`
   - Configure treg with the install flow above, or use an already connected treg MCP. Its allowlisted TinyFish search, fetch, news, and publications endpoints need no provider key and must be catalog-priced at zero. Every host tries treg first, then TinyFish MCP, then host web. A nonzero charge on a free endpoint still disables treg and switches directly to host web.

If last30days fails, or both TinyFish MCP and treg are unavailable, the skill still loads. It labels the gap under **Tools Used** and continues with free host tools. It does not pretend those tools ran.

**treg paid endpoints**, **Exa**, **Firecrawl**, and **Brave Search** are optional paid layers for `--balanced` / `--deep` / `--thorough` only. They never run in free mode. treg verifies price before each call and records actual cost or a labeled catalog estimate; an unexpected charge on a free endpoint stops treg for that run and switches to host web. As a capped fallback for pages the free fetch could not read, treg may call `treg.web.extract` (header-capped, never in free mode, never for discovery); Firecrawl then reads only the URLs it did not answer.

Paid treg facets beyond Reddit, X, YouTube captions, SERP competitors, and page extraction are social posts (TikTok, Instagram, YouTube, LinkedIn, Facebook page, Threads), prices and listings (Google Shopping, Amazon, Walmart, eBay, Etsy, Shopify), and reviews and ratings (App Store, Google Play, Trustpilot, Yelp, Glassdoor, Tripadvisor, Google Maps). The routing reference owns that endpoint table. Free mode does not call those endpoints. When a free report still has an open or thin social, price, or review facet, Follow-up Options says that data is available with `--balanced`.

## Examples

### Free mode — last30days + TinyFish

```text
/free-research Claude Code vs Codex
```

Default. Community pulse first, then treg free search (3–5 angles) and free fetch on the top pages, falling back to TinyFish MCP and then host web. No paid APIs.

Tools Used looks like:

```text
- last30days — community pulse (free)
- TinyFish via treg (free) — tinyfish.web.search × 4, discovery angles, USD 0.00
- TinyFish via treg (free) — tinyfish.web.fetch, 8 pages, USD 0.00
- treg spend total — USD 0.00
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
- TinyFish via treg (free) — tinyfish.web.search × 5, discovery angles, USD 0.00
- TinyFish via treg (free) — tinyfish.web.fetch, 10 pages, USD 0.00
- treg paid - skipped: no eligible priced route for this gap
- Exa — gap queries on the launch timeline (deep, ≤4)
- Firecrawl — leftover pages the free fetch could not read (deep, ≤6 leftover ops)
- Brave — independent index after Firecrawl (deep, ≤2)
```

If the free layer already closed the gaps, the report says treg paid was skipped, makes no `balance` call, and does not call Exa, Firecrawl, or Brave.

When any host uses treg's free layer, Tools Used names each endpoint under `TinyFish via treg (free)` with cost USD 0.00 or a labeled catalog estimate, plus the treg spend total. A paid person gap might use `anyapi.x.search.posts` after a catalog price check; it lists the actual cost and stops the ladder if a usable body closes the gap. Search snippets remain leads.

### Force free, even when coverage is thin

```text
/free-research --free what's happening with OpenClaw
```

Never calls treg paid endpoints, `balance`, Exa, Firecrawl, `firecrawl --status`, Brave, or `parallel-cli`. If the pass is thin, the report offers `--balanced` or `--deep`.

### Thorough mode — cover the intent checklist

```text
/free-research --thorough Claude Code vs Codex
```

Escalate free → balanced → deep → thorough when the previous report is not enough. Thorough builds the full intent checklist before the gate. Decision-bearing facets need two independent origins or one primary source; unanswered items and unmet origin requirements stay named gaps. It uses the same paid order under the table's caps and the same `parallel-cli` caps as deep, still requiring explicit Parallel opt-in. If free bodies meet the checklist and origin bar, it spends nothing. The unchanged verification tail still requires three origins or a primary to confirm a claim. The report carries concrete sourced detail and checklist coverage under Comparison / Gaps, with unmet facets listed honestly. Section order and the closing line stay fixed.

## Modes

| Mode | Tools | Credits |
|------|--------|---------|
| **free** (default) | last30days + treg free allowlist, then TinyFish MCP, then host web | Zero paid; treg ≤0 calls / USD 0.00 total / USD 0.00 per call (paid endpoints) |
| **balanced** | free layer + sequential paid tools on remaining gaps (treg ≤4 calls / USD 0.05 total / USD 0.02 per call; Exa ≤2, Firecrawl ≤3 leftover ops, Brave ≤1) | Minimal paid |
| **deep** | same order; treg ≤10 calls / USD 0.25 total / USD 0.02 per call; Exa ≤4, Firecrawl ≤6 leftover ops, Brave ≤2; stop when remaining gaps empty | Paid, capped |
| **thorough** | same order; treg ≤25 calls / USD 0.50 total / USD 0.02 per call; Exa ≤6, Firecrawl ≤10 leftover ops, Brave ≤3; checklist coverage and decision-bearing facet bar | Paid, capped |

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
- Not an Exa, Firecrawl, or Brave wrapper. Those run only after the decision gate, and only in `--balanced` / `--deep` / `--thorough`.
- Not a bundled search engine, MCP server, or `.mcpb` / `.skill` release factory.

## Manual (developer)

Keep all eight parity targets in sync: repo (`skills/free-research/`), Claude Code (`~/.claude/skills/free-research`), Grok live (`~/.grok/skills/free-research`), Grok pack (`~/Projects/skill-pack/grok/free-research`), Codex (`~/.codex/skills/free-research`), Codex pack (`~/Projects/skill-pack/codex/free-research`), Gemini (`~/.gemini/skills/free-research`), and other agents (`~/.agents/skills/free-research`). Copy the complete skill tree, including `references/` and `scripts/`. `scripts/run_note.py` is the skill-local note helper. Do not symlink this repo over a newer live tree. The installed plugin checkout is a separate publish and is not updated by that copy.

```bash
git clone https://github.com/AhjinGuild12/free-research-skill.git
```

```bash
python3 -m unittest tests.test_plugin_contract
grok plugin validate .
```

## License

MIT. See [LICENSE](LICENSE).
