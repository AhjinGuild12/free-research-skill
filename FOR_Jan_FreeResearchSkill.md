# FOR_Jan: Free Research — spend last, then decide what you actually believe

> *"You already have the page. Why is the agent buying another copy of the headline?"*

## Current state (2026-10-24)

Version 1.4.0 is on `feat/treg-social-price-review-facets`. The run card and all four manifests use that version. Version 1.3.0, prepared on `feat/thorough-portable-install`, added `--thorough` above free, balanced, and deep; free stays the default. The old modes keep their close test and budgets. Thorough turns a full intent checklist into named facets before the gate, and keeps decision-bearing facets open until two independent origins or one primary source answer them. It asks for a report with enough concrete detail to work from, and lists what it still could not answer. Two non-primary origins can close a thorough facet without confirming its claim: the verification tail still wants three origins or one primary.

Every host now starts free web reads with treg's zero-priced TinyFish allowlist, then TinyFish MCP, then host web. Paid order is leftover free fetch, treg by the open facet, Exa, Firecrawl, Brave, then opted-in `parallel-cli`. Intent orders facets; it does not choose which endpoints a facet is allowed to use. SKILL.md's Modes table owns the ceilings, with README as its mirror. AnyAPI trim options (`max_items`, `fields`) stay in the `query` slot, and paid calls still send the bounded `X-Treg-Route-Max-Cost` header. A nonzero charge on a free endpoint disables treg and switches to host web.

The portable install flow is `scripts/install.sh --check`, then `scripts/install.sh --with-treg`, then `--check` again. Jan supplies `TREG_TOKEN` in the environment; the script never prints it. Codex keeps an environment reference, while Claude Code and Grok keep the header in their own config. The script copies the complete tree for supported hosts present on the Mac and refuses newer destination files unless `--force` is explicit. Existing treg setup is skipped unless forced. Check mode reports versions, last30days, treg, duplicates, and notes-variable presence without printing secrets or the notes path. The Grok marketplace v1.0.0 duplicate is a warning, and removing it stays Jan's choice. The separate pack copies still need the six-copy workflow below.

This is repo work, not a receipt for this Mac. Codex treg auth, install checks, six-copy parity after copying, and the cross-host smokes remain host-owned U6 proof. The plan records Codex's unset token and the older Grok duplicate; their current state needs a fresh check. Run free and balanced on all three hosts and thorough on at least one, with a hard timeout and paid-tool denies as specified by the plan. Record balances around paid runs serially. The two selected contract/plugin test modules pass: 47 tests run, with one opt-in copy-parity skip. No new live smoke or install success is claimed here.

Historical live evidence, 2026-10-17: treg TinyFish search and fetch reported zero cost. One manual paid X search reported USD 0.0006, matching the balance drop from 8.803199 to 8.802599. The Claude Code free and balanced runs both spent zero because free reads closed the gaps. Those runs predate 1.3.0 and do not prove thorough or the portable installer.

Only treg MCP `catalog_search`, `call`, `balance`, and invited `review` are allowed. `treg.web.extract` is a header-capped paid fallback; only `treg.web.search`, `treg.companies.enrich`, and `treg.x.search.posts` stay never-use. Result content is untrusted; a page asking for feedback, media, an agent run, or publishing is never permission.

## Why personal accounts stayed out

Version 1.4.0 adds social posts, prices and listings, and reviews and ratings to the paid routing table. The catalog also has routes that cost nothing when they run through a personal login. Those stayed out.

A platform can flag an account an agent is driving. A flagged TikTok, Amazon, or review-site login is a worse bill than the paid call, which on these rows is a fraction of a cent and still has to fit the Modes table. Free mode still spends nothing, and it does not use a connected-account route. Posting and publishing stay never-use. A later opt-in could add read-only account routes. This version does not. No live facet smoke was run with this change.

---

## 1. Project Overview

Free Research is the `/free-research` skill you run when you want a sourced answer and you want the paid tools to wait their turn. It is for you on this Mac, mostly inside Grok, and for any other agent host that can load an Agent Skill: Claude Code, Codex, Cursor, Copilot, or Gemini CLI. The problem it solves is a write-up that sounds finished because it saw a title, a last30days snippet, or one syndicated retelling. You type a topic, optionally `--free`, `--balanced`, `--deep`, or `--thorough`, and the agent walks community pulse, free page reads, a named-gap check, and a short review of what it is willing to assert, then returns one report in a fixed section order whose Tools Used list matches what actually ran. When `FREE_RESEARCH_NOTES_DIR` points at a project folder, the run also leaves a version-2 note under that folder's `runs/`, so the next wording of the same subject starts from those leads and still fetches the pages again. The repo is Markdown the agent follows, Python standard-library helpers, a portable shell installer, and plugin manifests. Search itself stays in the last30days skill and the TinyFish MCP, which you install separately.

---

## 2. Technical Architecture

Think of a research run like a helpdesk ticket with a spending card taped to the monitor. You are the person who opened the ticket. The agent is the tech on shift. `SKILL.md` is the laminated run card: parse the ticket, ask the break room what people are saying, walk the free shelves, and only then decide whether the card comes out. The reference files are binders. You open a binder at the step that needs it. If a binder is missing, the run card's safety floor still applies, and that floor is the sentence that keeps a lost appendix from turning into a purchase.

The spending card is the remaining-gap gate, and it is the only spend switch. After the free layer, the agent writes `gap: <facet> — <why the free layer missed it>`, or `remaining-gaps: none`. In free, balanced, and deep, a facet is closed when a usable body answers it. Thorough adds the checklist and decision-bearing origin test described above. An empty or failed family keeps the gap open for the next family in line. Only when the last eligible family comes back with no new URLs does the search for that facet end, and then the report calls it unresolved. A usable body is extracted main text that answers that named question. A title, a last30days snippet, an empty or paywalled page, nav-only markdown, and an Exa highlight are leads. Outside thorough's pre-gate decision-bearing origin test, wanting a stronger source is a wish. It is a closed shelf. `--free` never takes the card out: no Exa, no Brave, no Firecrawl (including `firecrawl --status`), no `parallel-cli`, no Parallel Task API. If the free pass is thin, the report says so and offers `--balanced` or `--deep`.

Paid mode runs one family per turn and stops when gaps close. Free-fetch leftover URLs, probe connected tools, try treg's priced route for the open facet, then Exa, Firecrawl leftover reads, Brave, and opted-in `parallel-cli`. Parallel still needs explicit invocation opt-in, a paid mode, the real CLI already on PATH, and an open gap. All treg/Exa/Firecrawl/Brave ceilings live in SKILL.md's Modes table; the routing reference owns Parallel caps. When no family remains eligible, return the gate and report unanswered facets as unresolved.

Confirmation is a stamp you put on a claim after the card is back in the drawer. Think of it like accepting a change record: three independent publisher chains agree, or you have the organization's own artifact (its post, paper, filing, commit, or docs page). Three articles that all repeat one press release are one origin, the way three forwarded emails are still one announcement. The verification tail then runs three skeptic passes (correctness, recency, source quality) and, if anything is still confirmed, one dissent sweep that looks for someone saying the claim is wrong. A majority of failing passes, or a contradicting primary you actually fetched, knocks the claim down to unconfirmed. A thinner objection stays attached and the claim can remain confirmed, but the Executive Summary has to say "confirmed with dissent attached" and include the objection. An unconfirmed label does not reopen the paid line. The tail loads once, after the gate is marked returned, in every mode including free. The safety floor stays in `SKILL.md` on purpose: a floor that lives in a file which failed to load protects nothing. If `tool-routing.md` fails to load, no paid call is made. If `verification-tail.md` fails to load, findings whose review did not finish stay unconfirmed, no further paid call is made, and no note is written. Calls that already happened still show up under Tools Used. The report ships either way.

The vault note is a sticky on the filing cabinet, filed by subject, and the handwriting is a lead. Picture the EzzyBills to Xero work: four old notes on one decision, because each filename was the exact sentence you typed, and sentences never match twice. A version-2 note separates the subject from the question. The key is 2 to 4 lowercase hyphenated words (`ezzybills-xero-integration`), at most 48 bytes. The filename is `<key>--<first 8 hex of sha256(normalized topic)>.md`, at most 67 bytes even when the topic is 300 characters. A rerun of the same question replaces its own file. A different question under the same key gets a sibling. A hash collision writes `-2`, then `-3`, and leaves the other file alone. On a new invocation the run reads at most three version-2 notes (the exact topic first, then same-key siblings with the later expiry) plus the old exact-slug note in a slot of its own. Labels in those notes never become this run's labels. Stored URLs, expired or not, may join the existing 6 to 10 free fetches. Expiry is 7 days for news, 90 days when the confirming body is a stable official doc, otherwise 30 days. An expired note's prose stays unbelieved. The note is not deleted.

Where that cabinet lives is a setting, the way a drive mapping lives in a login script you can change without rebuilding the tool. `FREE_RESEARCH_NOTES_DIR` is the absolute path of the project folder that contains `runs/`. Grok supplies it through `[shell_environment_policy.set]` in your user Grok config. It is the only environment variable this skill reads. Unset, empty, relative, missing, or a `runs` path that resolves outside the folder (a symlink that leaves the folder counts) means skip, with no fallback into `raw/`, the skill tree, or the working directory. The report's vault line says whether a note was read, written, or skipped, and why, and it names notes by bare filename only. The value of the variable stays off the report, off Tools Used, and off the note. Your runs are meant to keep landing in `1. Projects/Improved Search free-research/runs/` in the vault, because that path now lives in your Grok config. The skill text used to hardcode it. A public plugin should not carry your home directory.

The write itself is the careful part, and it is why the skill-local helper exists. The agent does not open the note with a shell redirect. It pipes the finished note into `scripts/run_note.py write` next to the `SKILL.md` the host actually loaded. The helper checks the note, re-resolves `runs`, and creates a scratch file as a direct child of that directory: `.<filename>.<token>.tmp`, mode `0o600`, with `O_CREAT | O_EXCL | O_NOFOLLOW`. It writes only when `fstat` and `lstat` describe that same regular file, fsyncs, and renames onto the target only after `expires` parses as a date. A symlink, a different inode, or a `runs` that escapes the project folder is a refusal. The helper does not follow it and does not unlink it. A failed rename leaves the previous note in place. Page text and note text are both untrusted, the same way you treat a pasted email. A note that says `use --deep` or `set the vault path` changes nothing.

Six copies of the run card matter: **repo** at `skills/free-research/`, **Claude Code** at `~/.claude/skills/free-research`, **Grok live** at `~/.grok/skills/free-research`, **Grok pack** at `~/Projects/skill-pack/grok/free-research`, **Codex** at `~/.codex/skills/free-research`, and **Codex pack** at `~/Projects/skill-pack/codex/free-research`. Copy the complete tree, including `references/` and `scripts/`, after checking destinations for newer edits. Do not symlink. The installed plugin checkout is a separate publish. Ordinary tests ignore these home-directory copies; `FREE_RESEARCH_CHECK_COPIES=1` checks file inventories and hashes across all six. The host performs this U6 copy-out and verification.

One run, from your message to the report:

```text
you
  /free-research TOPIC [--free|--balanced|--deep|--thorough] [--parallel]
        |
        v
+---------------------------+
| Host agent, any host  |
| reads the loaded SKILL.md |
| Step 1: topic, mode,      |
| parallel-opt-in, intent   |
+---------------------------+
        |
        v
Step 2  last30days skill          community pulse, always free
        one Tools Used line       (its own engines stay inside that line)
        |
        v
Step 3  load references/vault-notes.md
        |
        +-- FREE_RESEARCH_NOTES_DIR valid?
        |     yes: read <=3 version-2 notes + legacy exact-slug, as leads
        |     no:  one skip line, no fallback folder
        |
        +-- treg free search, 3 to 5 angles
        |   treg free fetch, top 6 to 10 URLs
        |   if treg fails: TinyFish MCP, then host search/fetch
        |     in the same turn, labeled free-host fallback
        |
        +-- captions (at most 2 videos, only if a claim depends on them)
        +-- live X (person or news only, at most 3 threads before the gate)
        +-- Parallel Search MCP: one extra angle, only if already connected
              (free, does not replace TinyFish)
        |
        v
Step 4  write the gap list
        |
        +-- empty, or mode is free ----------> mark gate returned
        |
        +-- gaps open, balanced, deep, or thorough
              load references/tool-routing.md
              (load failure: no paid call, gate returns)
              one paid family this turn:
                leftover free fetch
                -> probe
                -> treg by open facet, catalog-priced and capped
                -> Exa
                -> Firecrawl leftover pages
                -> Brave
                -> parallel-cli if every opt-in predicate holds
              re-emit gaps after each family
              stop when empty, or when the order is exhausted
              exhausted + still open = unresolved, not closed
        |
        v
gate returned
        |
        v
load references/verification-tail.md once, every mode
  confirmation bar -> 3 skeptic passes -> one dissent sweep
  (load failure: unreviewed stays unconfirmed, no note, report still ships)
        |
        v
load references/vault-notes.md again
  python3 <loaded SKILL_DIR>/scripts/run_note.py write
        -> <project>/runs/<key>--<8 hex>.md
        |
        v
Step 6 report, fixed sections, this last line:
  your agent is only as good as the worst source it believed.
```

A later message is the same invocation only when it does not set a mode, does not opt into Parallel, and does not name a new topic. Saying yes to the report's offer of balanced, deep, or thorough is a new invocation. The same invocation does not look notes up again, does not spawn a second set of skeptics, and does not sweep again.

The shape came in two passes, and the second one refused to touch the spend rules. Late September 2026 ported the live remaining-gap contract into this repo and added the ledger, the skeptics, the one dissent sweep, YouTube captions, live X, the opt-in Parallel lanes, and a vault note that cannot count as proof. The copy-out replaced a symlink. On 9 October 2026 the spec was slimmed (version 1.1.0): contract tests landed before the prose moved, the tail moved into its own reference, notes gained the subject key, and the vault path moved into your Grok config. What free, balanced, and deep may call, in what order, and how many times, stayed put.

---

## 3. Codebase Structure

The repo is small on purpose. There is no app server, no `package.json`, and no dependency file. Python is the standard library, and the tests are `unittest`.

```text
free-research-skill/                          git: AhjinGuild12/free-research-skill
├── README.md                                 install, modes, the vault setting, what this is
├── LICENSE                                   MIT
├── TASK_PLAN.md                              short split of the 9 Oct plan (backend only)
├── docs/plans/
│   ├── 2026-09-26-2006-feat-improved-search-gates-plan.md
│   ├── 2026-10-09-1122-feat-reusable-notes-lean-spec-plan.md
│   ├── 2026-10-17-1846-feat-treg-free-research-plan.md
│   └── 2026-10-17-2200-fix-treg-trim-and-routed-plan.md
├── .claude-plugin/
│   ├── plugin.json                           name + version, no "skills" key
│   └── marketplace.json                      source "./", description under metadata
├── .grok-plugin/
│   ├── plugin.json                           "skills": "./skills/"
│   └── marketplace.json                      source url = this git repo
├── skills/free-research/                     the tree you copy to live and to the pack
│   ├── SKILL.md                              version 1.2.1, the run card + safety floor
│   ├── references/
│   │   ├── vault-notes.md                    read at Step 3, write after the tail
│   │   ├── tool-routing.md                   paid path, probe, Firecrawl ops, parallel-cli caps
│   │   ├── verification-tail.md              confirmation bar, skeptics, one dissent sweep
│   │   └── eval-scenarios.md                 tabletop traces T1-T23, T18a/T18b, live smokes L1/L2
│   └── scripts/
│       └── run_note.py                       encode-topic, decode-topic, write
├── scripts/
│   └── lint_run_notes.py                     read-only check of a runs folder (repo tool)
└── tests/
    ├── test_plugin_contract.py               manifests and version lockstep
    ├── test_skill_contract.py                ceilings, report shape, traces, opt-in copy parity
    ├── test_run_note.py                      topic codec and the exclusive write
    ├── test_lint_run_notes.py                version-2 errors, legacy warnings
    └── fixtures/run-notes/
        ├── ezzybills-xero-integration--a1b2c3d4.md
        ├── ezzybills-xero-integration--b2c3d4e5.md
        ├── legacy-bare-label.md
        └── legacy-readable.md
```

`SKILL.md` is the only file the agent is guaranteed to read at the start. It owns the mode table, the six steps, the report template, the url-ledger, the usable-body rule, and the safety floor. Each reference owns one job, and the run card says when to load it:

| File | When the agent opens it | What it is allowed to change |
|---|---|---|
| `vault-notes.md` | Start of Step 3, and again after the tail's write step | Which notes get read, and how the new note is shaped |
| `tool-routing.md` | When Step 4 may fire (balanced or deep, gaps still open) | Probe, Firecrawl commands, `parallel-cli` caps |
| `verification-tail.md` | Once, after the gate is marked returned, including on free | The stamp on each finding |
| `eval-scenarios.md` | When you are checking a trace, not during a normal run | Nothing at runtime. It is the tabletop |

Start ceiling changes in SKILL.md's Modes table. README mirrors it; `tests/test_skill_contract.py` rejects drift. treg, Exa, Firecrawl, and Brave limits belong there; `parallel-cli` limits belong in `tool-routing.md`. Report names and order remain pinned through Follow-up Options and the closing line. Deep Insights and Comparison / Gaps stay conditional.

How a note moves through the files, once the tail says it is time to write:

```text
agent has the finished note text in memory
        |
        |  SKILL_DIR = the directory of the SKILL.md this host loaded
        |  (not the repo root, not scripts/lint_run_notes.py)
        v
printf note | python3 "$SKILL_DIR/scripts/run_note.py" write \
    --project "$FREE_RESEARCH_NOTES_DIR" \
    --filename "<key>--<8 hex>.md" \
    --token "<fresh hex>"
        |
        v
run_note.py
  encode/decode topic so the stored line matches the question
  validate_note: marker, schema 2, key, dates, filename, closing line
  validated_runs: absolute project dir, runs is that dir plus /runs
  exclusive create inside runs, fsync, rename
        |
        v
<project>/runs/ezzybills-xero-integration--4989e7d4.md
```

Lookup uses the same codec. `encode-topic` and `decode-topic` read stdin and write stdout with no added newline. A plain topic is stored as itself. A topic that is empty, has odd whitespace, or contains a quote, a backslash, or a line break is stored as one JSON string. The replace walk and the lookup compare the decoded topic with this run's full topic. Comparing the raw frontmatter line will miss, and then you get a sibling file for a question you already answered. The extra escapes for the line breaks Python's JSON leaves raw are in Technology Choices, and the bug that forced them is in Lessons Learned.

`scripts/lint_run_notes.py` is the flashlight, not the writer. You point it at a `runs` folder:

```bash
python3 scripts/lint_run_notes.py /absolute/path/to/the-project-folder/runs
```

It loads the topic codec by importing `skills/free-research/scripts/run_note.py` from this checkout. Exit 0 means no version-2 errors. Legacy notes (marker present, no `schema` field) produce warnings and still exit 0. Copying the linter without that helper prints one line, `lint_run_notes: run-note helper is missing from the skill tree`, and no traceback. The four fixtures are the two shapes it has to tell apart: two version-2 EzzyBills siblings, and two legacy notes, one of them the old "bare label" style that says `confirmed` with no claim sentence.

The tests do not run a research pass and they do not spend credits.

- `test_plugin_contract.py` checks the skill root, host-specific manifest shape, and version `1.2.1` across SKILL.md and both plugin and marketplace manifests.
- `test_skill_contract.py` reads the Markdown and fails when a ceiling, a report heading, the closing line, a trace id, the vault-load sentences, or the "read this one environment variable" rule drifts. Copy parity is off unless `FREE_RESEARCH_CHECK_COPIES=1`, and then it hashes `SKILL.md`, the four references, and `scripts/run_note.py`.
- `test_run_note.py` checks that the linter borrows the skill helper's topic codec instead of keeping a second copy, that every line-break the codec cares about survives encode, write, and parse, and that a write refuses a scratch path that is already a symlink or a `runs` directory swapped for a symlink mid-open. A permission error on stderr leaves the vault path out of the message.
- `test_lint_run_notes.py` checks that a bad version-2 note is an error and a messy legacy note is a warning.

Claude Code uses copy-out for this setup; follow README from the repo root. Plugin manifests remain packaged for existing hosts. Grok's marketplace points at the Git URL; other Agent Skills hosts can use `npx skills add AhjinGuild12/free-research-skill -g`. Pick one install method per host to avoid duplicates. Copy-out does not update an installed plugin checkout.

The two plans are the reason the tree looks like this. The September plan is the spend-and-belief contract. The October plan is the lean spec and the reusable notes, and it says, in writing, that the gate, the paid order, and the ceilings were not up for revision. `TASK_PLAN.md` is the five backend units of that October plan: pin the contract, slim `SKILL.md`, add version-2 notes, add the linter, then match the README and bump to 1.1.0. There is no frontend in this repo.

---

## 4. Technology Choices

The tree above is the recipe. These are the choices that decide where money goes, where memory goes, and which copy of the recipe Grok actually loads. A research run still works like a change on a Friday afternoon: you read the ticket comments, then the vendor's own page, and you open a paid support case only when a named question is still empty. The note you leave is a sticky on the monitor. The signed change record is still the page you fetch again. last30days and TinyFish stay separate installs. Version 1.1.0 is the recipe after the October notes work.

| Technology | Why | Alternatives considered |
|---|---|---|
| Claude Code, Grok, and Codex | The same path-free run card loads from each host's skills tree. treg is first on all three; host MCP controls handle authentication. Grok can supply the notes setting through `[shell_environment_policy.set]`. | Three separate run cards that drift. Hardcoded MacBook paths in a public skill. A hosted research service off the laptop remains outside the product. |
| Free, balanced, deep, and thorough | Free is the default and spends nothing. Paid modes use one order, with ceilings, and stop when their named facets meet the close test. Thorough requires the intent checklist and decision-bearing origin bar. A free layer that already answered the question skips paid tools even on `--deep`. | Spending because coverage "feels thin." Firing Exa, Firecrawl, and Brave in one batch. Letting an unconfirmed label, a skeptic downgrade, or an expired note reopen the wallet. |
| last30days | First step, every run, free. Community pulse from Reddit, X, YouTube, Hacker News, and the rest. One Tools Used line. | Opening on web search. Adding `--web-backend parallel-mcp` unless you asked for that backend. Editing last30days from this repo, or vendoring it. |
| treg free allowlist, then TinyFish MCP | Free discovery, 3 to 5 real angles, then free page bodies for the top 6 to 10 URLs, up to 10 URLs in one fetch. | Host `web_search` and `open_page` as the primary reader. They follow treg and TinyFish MCP failures in the same turn. TinyFish `run_web_automation`, which bills. Firecrawl as the first reader of every URL. |
| Exa, then Firecrawl, then Brave | Paid, on balanced, deep, or thorough, and only while a named facet is still open under that mode's close test. Ceilings live in the SKILL.md Modes table. | Exa fetch as the default way to read a leftover URL. An Exa highlight is not a page body. Firecrawl search on a gap Exa already covered. Parallel as the replacement for this order. |
| `parallel-cli`, and Parallel Search MCP | Search MCP is a free extra angle when it is already connected, including on free mode. `parallel-cli` is paid, sits after Brave, and runs only with `--parallel`, a balanced, deep, or thorough mode, the real binary on `PATH`, and a named gap still open. Thorough shares deep's caps; `tool-routing.md` owns those caps. | Parallel as the default engine. Installing it during a run. Calling the Parallel Task API. Treating GNU `parallel` as this tool. On 26 September 2026 the CLI was absent and `PARALLEL_API_KEY` was unset, which is why it stayed opt-in. |
| `scripts/run_note.py` | Stdlib-only Python shipped inside the skill directory, so a skill-only install still has it. One topic codec, and one exclusive writer. The repo linter imports that same codec. | Asking the model to do `O_EXCL` and `fstat` with its own file tools. Hand-copying the encode functions into the skill prose. PyYAML or python-frontmatter. A shell `>` redirect onto the note path. |
| Vault notes | Short Obsidian markdown in the project folder's `runs/` directory. A 2 to 4 word subject key, plus 8 hex characters of the full topic, so related questions meet and different questions do not overwrite each other. Labels are leads. Expiry is 7, 30, or 90 days. | Exact-sentence filenames. Hardcoding the Obsidian path in SKILL.md. A fallback into `raw/` or `3. Resources/X Articles/`. Rewriting the older notes. Per-URL provenance tags. A separate file that remembers budgets across turns. |
| Copy-out to the live skill and the pack | After both destinations still match a recorded baseline, copy the repo skill tree onto `~/.grok/skills/free-research` and `skill-pack/grok/free-research`, including `references/` and `scripts/`. | A symlink from the live skills folder back to this repo. Copying older repo bytes over a newer live tree. Treating the installed plugin checkout, or the Codex pack copy, as part of that copy. |

### Grok is the machine this runs on

Grok is where much of the earlier proof came from. The 24 October plan makes the everyday invocation the same in Claude Code, Grok, and Codex. The portable installer copies one complete skill tree to each supported host present. Other Agent Skills hosts can still use `npx skills add`. Pick one method per host, or the skill can show twice.

The run card loads last30days from whichever skills tree or plugin cache the host loaded. On Grok, TinyFish auth recovery is `/mcps`, then tinyfish, then authenticate. The free fallback order stays treg, TinyFish MCP, then host web without waiting for re-authentication. The notes directory arrives because Grok's user guide lets `[shell_environment_policy.set]` inject environment variables into the shell. The skill reads one variable by name, `FREE_RESEARCH_NOTES_DIR`.

Grok's own skill discovery is why the copy target matters. A native skill wins over a plugin skill with the same name. Updating `~/.grok/skills/free-research` changes the run you get tomorrow. The installed plugin checkout under `~/.grok/installed-plugins/` stays on the published commit until you publish. That checkout is a different drawer. Check the pack copies for drift before updating them; the portable installer does not update those separate trees.

### Free first, then a capped paid queue

Free mode is the default because most of your runs should spend nothing. It calls last30days, then treg's free TinyFish allowlist, with TinyFish MCP and the host's `web_search` and `open_page` as fallbacks. YouTube captions join when a claim depends on a video (at most two, through the transcript skill, with no `pip install` during the run). Up to three X thread fetches join before the gate when the intent is a person or news. Parallel Search MCP may add one angle if you have already connected it. An excerpt-capped result stays a lead. The order, the ceilings, and the opt-in predicates are the architecture above. The choice was a queue, one family per turn, against a batch that fires Exa, Firecrawl, and Brave because coverage feels thin.

The spend switch is boring on purpose. Spend is allowed when the invocation said `--balanced`, `--deep`, or `--thorough`, and a named facet stays open under its mode's close test. Thorough's decision-bearing origin requirement is evaluated before the gate returns. Outside that test, "I wish this had a nicer source" is not a gap. An unconfirmed label, a skeptic vote, a missing third origin, dissent, an expired note, and a truncated excerpt do not open Exa, Firecrawl, Brave, or `parallel-cli`. The gate returns, then the review tail runs. The tail can downgrade a claim. It cannot go back to the wallet. After each paid family the run writes the gap list again. An empty list ends the queue, including on `--deep` or `--thorough`. If every family has run, failed, been skipped as disconnected, or hit its ceiling, leftover facets are reported as unresolved.

Firecrawl's concurrency cap is an ops detail you would recognize. This host's Firecrawl free plan allows 2 concurrent jobs, so leftover scrapes stay at 2 even if a later status line claims more. `search --scrape` counts as one leftover op. `scrape --query` is extra credits, so the skill does not use it. Interact is a last resort for one JavaScript-blocked page, and the session has to be stopped. The probe's `firecrawl --status` runs only if Firecrawl work is still needed, and free mode never calls it. That probe is context. It does not count as a leftover op.

The 9 October free-mode smokes behaved like that queue. The first EzzyBills run listed last30days and TinyFish, wrote `remaining-gaps: none`, and recorded that Exa was disconnected and that Firecrawl and Brave were not called. The second run, worded as what EzzyBills syncs and how the connection is set up, read the prior note as a lead, refetched, and again stopped with no remaining gaps. It also used `web_search` / `open_page` as the free-host fallback for supplements and the dissent sweep. TinyFish still fetched the docs. How those two runs were almost cancelled, and how the second one hid the filename, is in the war stories.

### last30days, then TinyFish

last30days answers a different question from a web search. A web search asks what pages exist. last30days asks what people have been saying for the last month, on Reddit, X, YouTube, Hacker News, and the other sources that skill already knows. That is why it goes first, on every mode, and why a failure there is a labeled gap the run walks past. The raw engine dump stays out of the report. Tools Used shows one line. If last30days used some engine of its own, that engine is still last30days. This skill does not list it as "we called Exa."

A last30days snippet, a video highlight, or a keyword hit is a lead. The body is the thing you can argue from: a TinyFish or host page fetch, caption text, or a fetched X thread.

treg's fixed zero-priced TinyFish allowlist supplies free search/fetch first. If absent or failed, TinyFish MCP supplies those reads; then host web is the fallback. TinyFish OAuth credentials stay with its MCP. treg uses ambient MCP auth and runtime catalog price checks. Failures stay on the free layer and Tools Used names the layer that actually ran.

`run_web_automation` is the TinyFish tool that clicks around a site. It costs credits. Research reads leave it alone, including on a free run. If a page is so script-heavy that a fetch comes back empty, that is a leftover Firecrawl problem for balanced, deep, or thorough, and only while the gap is still open.

### The note helper is stdlib on purpose

The writer is `skills/free-research/scripts/run_note.py`. It uses the Python standard library and nothing else: `argparse`, `hashlib`, `json`, `os`, `secrets`, `pathlib`. There is no `requirements.txt` for it. A fresh machine can run it with the `python3` already on the path. Tests are stdlib `unittest` too, rooted at the repo, same shape as the old plugin contract test. The copy-parity test runs only when `FREE_RESEARCH_CHECK_COPIES=1`, so a normal test run does not need your home directory, and a half-finished unit does not fail before the copy-out.

The helper has three subcommands an agent can call from the shell. `encode-topic` and `decode-topic` are the only topic serialization. `write` reads the finished note on stdin, checks it, and publishes it. The skill tells the agent to resolve `SKILL_DIR` as the directory that contains the loaded `SKILL.md`, then call `scripts/run_note.py` under that directory. The working directory, the repo root, and the linter path are the wrong places to look. A skill-only install still has the helper, because it sits next to `SKILL.md`.

The codec exists because a topic has to survive as one frontmatter line, and some topics are hostile. A plain sentence is stored as itself. An empty topic, odd whitespace, a quote, a backslash, or any character `str.splitlines()` treats as a break becomes one JSON string. Python's `json.dumps` leaves U+0085, U+2028, and U+2029 raw, which would split the field later, so the helper escapes those three. The parser splits records on ordinary newlines only. `decode-topic` of `encode-topic` is the original topic. The filename hash is the first 8 hex characters of SHA-256 over the full normalized topic, so two sentences that share a long prefix and differ at the end still get different files. The hash is computed on the decoded topic.

The writer exists because prose that says "open this file exclusively and fstat it" does not make a model do that. Review asked for a program. `write` pins the `runs` directory with `O_DIRECTORY` and `O_NOFOLLOW`, checks that the file descriptor and `lstat` name that same directory, and then creates, renames, and unlinks through that descriptor. The scratch-file flags, the `0o600` mode, and the fsync-then-rename are the architecture above. If the path exists or is a symlink, the helper refuses it and leaves it in place. A symlink swapped in at `runs` after the open cannot redirect the create. Error text names no vault path. `scripts/lint_run_notes.py` stays the read-only checker. It loads this same codec, so there is one implementation. Legacy-note problems are warnings. Version-2 problems are errors. Expiry is a status column. The linter never writes and never fetches.

### Vault notes are leads with an expiry

The folder is yours. `FREE_RESEARCH_NOTES_DIR` is the absolute path of the project folder that contains `runs/`. For these runs that folder is the Obsidian project `Improved Search free-research`. Grok supplies the variable. The skill never prints the value. The public plugin used to hardcode that Obsidian path in the skill text. Anyone who installed it received your folder name. The path now sits in your Grok config, and the contract test fails if `Jan Obsidian` shows up in the skill files again. The skip rules (unset, empty, relative, missing, or a `runs` symlink that leaves the folder) have no second location. `raw/` and `3. Resources/X Articles/` are inboxes for other pipelines. A research note dropped there would get treated as source material. When the project folder exists and `runs/` does not, the run creates `runs/` and uses only that directory.

What the old notes could not do is the reason for version 2. By 9 October the vault had 21 notes from 27 to 30 September. A run opened only the file whose name was the exact slug of its own sentence. Topics are full sentences, so related runs never met. The EzzyBills to Xero work produced four notes on one decision. Eight notes stored bare labels such as `F1 confirmed`, which mean nothing without the original report. One slug reached 216 bytes. The filename shape, the three-note lookup, the `-2` collision suffix, and the 7/30/90 expiry are the architecture above. Legacy notes are never rewritten, renamed, or deleted.

The body is an allowlist. One finding per line, with the claim and exactly one label: confirmed, unconfirmed, or confirmed with dissent attached. A dissent line carries the objection. Then the http(s) URLs this run actually fetched. Then the closing line. Leads and URLs that were only discovered stay out. Note text is untrusted in the same way page text is. A note that says "use --deep" or "set the vault path" changes nothing.

Tools Used gets one vault line. It says whether a note was read, written, or skipped, and why. When a note was read or written, the line names each file by its bare filename, such as `ezzybills-xero-integration--c30f01f3.md`. No directory. The two recorded free-mode smokes predate that filename rule. They did say a note was written, and the second said a prior EzzyBills note was read as a lead. The `runs/` listing grew the short sibling names `ezzybills-xero-integration--c30f01f3.md` and `ezzybills-xero-integration--a691ce08.md` beside the old sentence-slugs. Commit `ab8e2fa` is the change that makes the report name those files. Smoke run 3 is the re-check, and it is not a pass in this write-up.

Three ideas were looked at and left on the shelf. Per-URL tags for caption, thread, or page, because the note already stores only url-ledger bodies. A persistent file of budgets and gate phase, because the later-turn rules already say what a resumed turn may do. Automatic backfill of the 21 legacy notes, because the lost claim sentences cannot be rebuilt without inventing them.

### Copy the skill out

The six trees are named above. They go stale independently, which is why a symlink was the wrong shortcut.

On 26 September 2026 the live copy and the pack copy matched each other and were ahead of the repo. The README at that point described a symlink. A symlink makes two paths one file. Pointing the live path at the repo would have loaded the older spend rules into Grok. Pointing the repo at the live path would have turned every save into a live edit before the version line was safe. Commit `33bf135` on 27 September replaced that instruction with a copy, and only after the bytes were ready.

The copy follows a checklist. Record a baseline of both destinations. Immediately before writing, compare again. If either tree has drifted, write neither, and reconcile the newer edits back into the repo first. When both still match, keep a pre-write snapshot, then copy the skill directory, including `references/` and `scripts/`. Vault notes stay in the vault. The installed plugin checkout stays out of the copy. The 9 October copy-out found no drift, rsynced both trees, and left `run_note.py` with the same SHA-256 in the repo, the live copy, and the pack. `FREE_RESEARCH_CHECK_COPIES=1` then ran 57 tests, all passing. The plugin checkout's fingerprint was unchanged, and so was the Codex pack.

The recipe above is what a clean run follows. The next section is where that recipe tore while it was being written.

---

## 5. Lessons Learned

**Route the ticket by the missing fact.**
A news topic can still be missing Reddit discussion. Sending it only to X because the intent says news is like routing every email with "printer" in the subject to the same queue, even when the fault is the network. The open facet selects treg's endpoint; intent only sets the order in which facets are considered. The routing reference owns that table, so the run card points there instead of copying a second list.
**Rule:** Match the endpoint to the unresolved facet, regardless of topic intent.

**A status update is not the report.**
A denied Firecrawl call or a disconnected Exa server can leave the agent narrating what it would try next and then stopping. The gap is still there, and Jan still needs the answer the available evidence supports. Step 4 owns the recovery: skip unavailable families in the same turn, return the gate when the order is exhausted, then finish the verification tail, note procedure, and full Step 6 report. T32 pins that path. The closing line is part of the receipt.
**Rule:** Never end a run without the report; unresolved gaps belong in Comparison / Gaps.

**The Grok process can outlive its answer.**
The 19 October headless run exposed a different hang: Grok can reach `end_turn` and still not exit. Empty stdout is not enough to tell whether research is running, finished, or stuck after the answer. The plan keeps the CLI fix out of scope. Smokes need a hard timeout, paid-tool denies, and a read of the host session log when stdout is empty. An `end_turn` entry alone does not prove the Step 6 report was written; inspect the actual report too.
**Rule:** Bound headless Grok runs with a timeout and recover the evidence from the session log before calling the run a failure or a pass.

**A balance is a shared meter.**
A balance change tells you what the account spent during an interval. It does not say which overlapping process spent it. Until there is a shared per-call charge helper, timing is the attribution tool: run smokes serially, record balance before and after each paid run, and line up call times and reported costs. An unrelated call inside that interval makes the attribution uncertain. The old manual USD 0.0006 match is useful evidence for that call, not a blanket pass for future runs.
**Rule:** Compare reported treg spend with an isolated before/after balance window; keep a mismatch explicit until timing explains it.

**A bigger truck does not widen the loading dock.**
Grok 4.7 on xhigh writes a huge adapter log. The first U1 and U4 attempts died because that log blew past the controller's 10 MB raw cap. The handoff answer was to start the job with `CE_WORK_MAX_RAW_BYTES` at 100 MB, and 200 MB for U4, so the run could finish. That only raises the cap on the way in. `terminalize` still reads `adapter.log` with a hardcoded 10 MB limit, 10485760 bytes, and there is no environment variable for that read. U2 finished with a 20,376,170-byte log and stayed stuck in `authoring`. U3 was 10,522,089 bytes. U5 was 12,837,291 bytes. The recovery was to copy each full log to `/tmp/fr-packets/U2-adapter.log.full`, `U3-adapter.log.full`, and `U5-adapter.log.full`, then cut the controller's copy down to exactly 10 MB so the receipt could be hashed. `RUN_VERIFIED` is real for the code and the 38 tests. It is hashed against the short logs. Think of it like a removals van you paid to carry a full filing cabinet, and a dock scale that still refuses anything over 10 MB. The van and the scale are different machines.
**Rule:** Before a long Grok unit, make the write cap and the terminalize read cap the same number. If you raise only the write cap, copy the full log out before you truncate, and say so in the result file. The lasting fix is in the ce-work controller, not in this repo.

**`nohup` starts the job and drops the pager.**
The continue run was launched as `nohup grok -p "$(cat /tmp/fr-packets/grok-continue.md)" ... --permission-mode bypassPermissions ... &`. That process was pid 29019. `nohup` detaches it from the tool that started it, so there is no completion notification and no tracked background task. A `grok -p` run also writes `grok-continue.out.json` only when it exits, so an empty error log and a missing result file look the same as "still thinking." The only checks on offer were `ps -p 29019` and `ls` on the result folder. That is a person refreshing a ticket queue by hand. The process had already integrated U1 (`1722b73`) and U4 (`59b7481`) while it was invisible, and the controller's U2 job (`20261008T231602Z-90ff9438`) was still alive, so killing 29019 did not throw away the unit work. The relaunch used the shell tool's own background runner, waited for the notification, and left that U2 job alone.
**Rule:** Dispatch Grok and Codex with the tool's background run. Never `nohup`, and never a poll loop. Wait for the notification, then read the result file.

**A sandbox that can think and cannot write is still a finished review.**
Codex gpt-6.1-sol medium, read-only, finished the wave-1 review and then could not write `/tmp/fr-packets/codex-review-wave1.result.md`. The sandbox will not create the file. The same wall showed up when Codex fixed those findings in the worktree: the commit was blocked because git metadata lives outside the directory the sandbox may write. HEAD stayed `59b7481`. The host committed that work locally as `33586ac`. Later, the full unittest run failed inside the sandbox because it could not create temporary files. The same suite, run on the host, passed. The review text was sitting in the job log the whole time. It is the same shape as a contractor who finished the punch list and then found the site office locked. You photograph the clipboard. You do not pretend the punch list was never done, and you do not ask the contractor to file it themselves.
**Rule:** Tell a Codex review, up front, that the host saves the findings file and makes the commit. If the result file is missing, read the job log before you relaunch. Run the test suite on the host when the sandbox cannot write temp files.

**`str.splitlines()` is a bigger knife than "newline."**
The topic codec used `json.dumps(..., ensure_ascii=False)`. Ordinary quotes, backslashes, and real newlines round-tripped. U+2028 (line separator), U+2029 (paragraph separator), and U+0085 (next line) were left as raw characters. The frontmatter parser then called `splitlines()`, which treats all three as line breaks. `one\u2028two` survived encode-then-decode and came back from the parser as `one`. The linter accepted the damaged note. Two runs of the same subject would miss each other, because the stored topic was no longer the topic. The direct round-trip never touched the parser, so the test was green. The fix lives in `skills/free-research/scripts/run_note.py` (`e9f7a25`): every character `splitlines()` would break on is escaped, including those three as `\u0085`, `\u2028`, and `\u2029`, and `parse_frontmatter` splits records on U+000A and U+000D only. `tests/test_run_note.py` now walks encode, then write, then parse.
**Rule:** A codec test has to go through the parser that will read the file. Include U+2028, U+2029, and U+0085. A round-trip that never parses the file will bless a topic that cannot be found again.

**Checking the door, then letting go of the handle, is how a symlink wins.**
The first scratch-file fix refused a symlink at `runs/.<filename>.tmp` and created `.<filename>.<token>.tmp` with `O_CREAT|O_EXCL|O_NOFOLLOW`. That flag protects the last path component. It does not protect the parent. The helper validated `runs`, then later created and renamed by path. Swap `runs` for a symlink pointing outside the project between those two steps, and the note lands outside the vault folder. `O_NOFOLLOW` on the scratch file will happily follow a parent that was replaced. Codex found this by reading the order of operations. It did not run the race. `d9a6db2` opens the validated directory once with `O_RDONLY|O_DIRECTORY|O_NOFOLLOW`, checks `fstat` against `lstat`, and does the create, rename, and unlink through that directory descriptor. A test swaps `runs` for an outside symlink on the open and checks the note still lands in the original directory.
**Rule:** Validate a directory by holding it. Open it with `O_DIRECTORY|O_NOFOLLOW`, then do every child operation on that descriptor. A path you checked earlier is a path someone else can replace.

**A caught error that still prints a traceback is a path leak.**
The vault path is `FREE_RESEARCH_NOTES_DIR`. The skill is not allowed to print it. Directory creation caught `FileExistsError` and let every other `OSError` escape. A `PermissionError`, or a read-only filesystem, came out as a Python traceback with the vault location in it. Codex reproduced that in memory. The CLI's tidy handlers never saw it. The fix turns `OSError` from `mkdir`, from the directory open, and from the write into a path-free `WriteError` (`from None`). The CLI prints `run_note: ...` and exits 1. `test_permission_error_stderr_hides_the_vault_path` mocks `PermissionError` on `mkdir` and on the scratch `open`, and checks that stderr has no vault path, no `Traceback`, and no `PermissionError`.
**Rule:** Every filesystem failure on the write path becomes one path-free line. Test it by mocking `PermissionError` and asserting the secret string is absent. Catching the happy error (`FileExistsError`) leaves the ugly ones as tracebacks.

**`--permission-mode default` cancels when nobody is there to approve.**
The handoff was right that `--permission-mode plan` produces an empty research run, and wrong that headless work should use `--permission-mode default` plus denies. The free-mode smoke (EzzyBills and Xero, two wordings, launched from `/tmp/fr-packets/smoke` so Grok would load the installed skill) used that default. Both runs stopped after 4 turns with `stopReason: cancelled` and wrote no note. In a single-prompt `grok -p` run the first tool that needs approval has nobody to ask, so Grok cancels. It is a change window whose first approval page rings an empty chair. About $0.09 of usage per attempt, and one useful fact: run 2 had already reached "Vault notes exist," so `FREE_RESEARCH_NOTES_DIR` from `~/.grok/config.toml` does reach the shell. The rerun used `--always-approve`, with Exa, Brave, Firecrawl, Parallel, `rm`, and `git push` denied. Those two runs finished `end_turn` in 19 turns each (about $0.75 and $0.89).
**Rule:** A headless `grok -p` skill smoke uses `--always-approve` and an explicit deny list for paid tools and `git push`. `--permission-mode default` is for a human at the keyboard.

**"Do not print a path" made the model hide the filename too.**
The plan's smoke says the second run, worded differently on the same subject, lists the first note's filename under Tools Used. Run 1 wrote `ezzybills-xero-integration--c30f01f3.md`. Run 2 found that version-2 note, read it as a lead, re-checked the links, and wrote `ezzybills-xero-integration--a691ce08.md` beside it. The vault path was absent. Paid tools did not run. The linter said both new notes were current, and the older notes were untouched. Tools Used said: "Vault note — a prior note on how EzzyBills integrates with Xero was read as a lead and re-fetched. A new note for this topic was written." The filename was in the model's reasoning and not in the report. The rule had said to record whether a note was read, written, or skipped, and why, and had banned a filesystem path. A bare filename looked enough like a path that the model left it off. `ab8e2fa` requires each read note and each written note by bare filename only, for example `ezzybills-xero-integration--c30f01f3.md`. A directory and the vault path stay off that line. `test_vault_note_tools_used_names_bare_filename` locks the wording in `SKILL.md` and `references/vault-notes.md`.
**Rule:** When a report line must name a file and must not name a path, put the exact bare filename in the example. "Say whether, and why" is not "say which file."

**Claude Code reads `$0` as "the first word you typed."**
In Claude Code, `$0`, `$1`, and so on inside a skill's text are argument placeholders, filled in when the skill loads. The first `/free-research` run in Claude Code passed `latest news on treg WebAccess...`, and the Modes table came back as "treg ≤4 calls / latest.05 total / latest.02 per call." Every dollar amount had been turned into the user's first word. The unit tests read SKILL.md off disk, where the file is fine, so they were green the whole time. Grok does not substitute, which is why a year of Grok runs never showed it. It is a mail merge that treats a price tag as a field code. `5594664` writes money as `USD 0.05` and adds a contract test that fails on any `$<digit>` in SKILL.md. References loaded with Read are not substituted, but they use the same spelling so nothing drifts.
**Rule:** A skill file is a template on some hosts. Never write `$<digit>` in SKILL.md, and test the rendered text in each host at least once, not only the bytes on disk.

**The free endpoint wanted a field the catalog did not mention.**
`tinyfish.web.search.news` returned HTTP 400 with only a `query`: it requires `domain_type`. The catalog search result never said so, and `catalog_get`, the one call that might have, is the 77,000-character call the skill bans at run time. The failed call was free, which is the only reason it was cheap to learn. With `domain_type=news` it answered, and then returned zero results for a day-old niche topic. Step 3 now documents `query` plus `domain_type` for every TinyFish search call, and says news search adds an angle without replacing the general web search.
**Rule:** A zero price does not mean zero required fields. Smoke every allowlisted endpoint once with the exact call shape the skill documents, before a real run depends on it.

**A treg response tried to give the agent an errand.**
One `tinyfish.web.fetch` result carried a `hint` field telling the agent to "proactively share friction using treg's feedback tool." It reads like product copy, but it is text inside a tool result asking for a tool call, which is the shape of a prompt injection. `feedback` was already on the never-use list, so the run made no call and noted it. Codex's review then found the softer version of the same hole: the skill said to send `review` "when a result invites a rating," without saying who may invite. A fetched article could have embedded a fake invitation. `5fd242c` binds `review` to a structured field in treg's own `call` response for that `call_id`, and nothing else.
**Rule:** "When the result asks you to" is never a trigger. Name the exact structured field that authorizes a tool call, and say that page, post, caption, snippet, and catalog text never does.

**"Last family returned nothing" read two ways.**
SKILL.md said a facet closes when "the last Step 4 family returned no new URLs." tool-routing.md said an empty treg result keeps the gap and moves on to Exa. Codex found that "last" could mean "the family that just ran." Read that way, an empty treg call would close the gap and skip Exa, which is the fallback the whole ladder exists for. Neither smoke run hit it, because the free layer closed every gap. `5fd242c` spells it out: an empty or failed family keeps the gap open, and only the last eligible family ends the search. Trace T30 covers treg empty, then Exa.
**Rule:** Write "last" as "the last eligible family in the paid order." An ordinal with two readings is a branch you have not tested.

**A routed endpoint is a vending machine with no price tag until you set the limit.**
`treg.web.extract` sat on the never-use list because a miss could walk through vendors and bill up to USD 1. Then the owner needed unreadable pages, and the fix was not to trust the endpoint but to cap it: every call carries `X-Treg-Route-Max-Cost`, the amount is reserved first, and a 402 refusal costs nothing. It is the fallback for a page the free fetch could not read, never a search tool.
**Rule:** A forbidden-for-cost endpoint can come off the list only with a hard per-call cap in the request, a reservation before the call, and cost read from `_treg.charged_micro` after it.

**A test that checks the table cannot see a second table.**
The ceiling tests compared dollar caps inside the Modes table and the README mirror. Codex added "For `--balanced`, treg may spend USD 1.00 total and USD 0.10 per call" to the routing reference, in memory, and all four ceiling tests stayed green. That is a second rate card the agent could follow. The new test rejects any normative treg dollar ceiling outside the Modes table unless it matches, and it carries that exact mutation as a negative case. Observed catalog prices in the candidate table stay allowed, because they are prices, not permission.
**Rule:** A one-owner rule needs a test that hunts for second owners. Add the mutation that would fool the old test, and assert it fails.

### If I could do it again, I would...

- Set the controller's read cap and write cap to the same number before U1, and keep the full adapter log next to any truncated copy.
- Launch every Grok and Codex worker with the tool's background runner. Pid 29019 would have been a tracked task from the first minute.
- Put in the Codex prompt: "You cannot write the findings file or the git commit. Print the verdict. The host saves it and commits it." Then run unittest on the host.
- Test Unicode line separators through encode, write, and parse on the first codec, not after a review caught `splitlines()`.
- Open `runs` once and keep the directory descriptor on the first version of `write`, instead of discovering the parent-symlink hole after the scratch-file hole was closed.
- Turn every write-path `OSError` into `run_note: ...` with `from None` before any smoke, and unit-test a mocked `PermissionError`.
- Smoke with `--always-approve` and the paid-tool denies on the first attempt. The handoff note about `--permission-mode default` cost two cancelled 4-turn runs.
- Show a bare filename in the Tools Used example the day the vault-note line was written, so run 2 had a label to copy.
- Load the skill in every target host and read the rendered Modes table before writing any tests. The `$0` substitution was visible on the first screen.
- Smoke each treg endpoint with the documented call shape before writing the allowlist, so `domain_type` lands in the spec instead of in a 400.
- Pick a smoke topic the free layer cannot close, so a balanced run actually opens the paid family.
- Keep Codex on medium effort from the start. The first U1-U5 dispatch ran at high and was cancelled and restarted at medium.

---

## 6. War Stories

**The stamp that would not fit on the parcel.**
U2's Grok job actually finished. The skill file was slimmer, `verification-tail.md` existed, the contract test had moved. Then `terminalize` refused the parcel. The adapter log was 20,376,170 bytes. The reader allows 10,485,760. Raising `CE_WORK_MAX_RAW_BYTES` had done its job too well: the run survived, and the receipt printer did not. For a while the honest options all looked bad. Truncating the log changes the hash. Patching the ce-work script mid-run edits the referee. Starting over with a 10 MB write cap would throw away a finished unit and might kill the next one the same way U1 and U4 attempt-1 died. What shipped is the boring sysadmin move. Copy the full log aside. Cut the controller's copy to the cap. Let `terminalize` hash the short one. Do the same when U3 comes in 36 KB over the line and when U5 comes in at 12.8 MB. The full logs are still in `/tmp/fr-packets/`. Future Jan, if a unit sits in `authoring` with `failure null` and a fat `adapter.log`, the job is done. The scale is the thing that failed.

**The Grok that was running in the other room.**
The continue prompt went out with `nohup` and an ampersand. Pid 29019. Bypass permissions, `git push` denied, output redirected at files that stay empty until the process exits. From the chair it looked responsible: "still running, 1.5 seconds of CPU, empty error log, come back in a few minutes and `ls` the result files." That is not orchestration. That is hoping. `nohup` had detached the process from the tool session, so there was never going to be a notification. The instruction that fixed it was blunt: kill 29019, that Grok is not tracked, relaunch with the background runner, do not poll. The kill was safe in a way that was easy to miss. U1 and U4 were already commits. The controller's own U2 job was a different process and was left running. The relaunched Grok was told to wait for that job, then terminalize it, and not to start a second U2. The memory line written the same hour is the whole lesson: background runner, no `nohup`, no polling. Read the result when the notification arrives.

**Codex finished the review and could not put the paper down.**
The wave-1 review came back "fix first" with four real defects: the ceiling test only understood `≤`, an unclosed frontmatter with `schema: 3` was skipped instead of an error, a `data:` URL inside a Markdown link slipped through, and `- nope:claim` was reported as `non-http-url` instead of `invalid-label`. Codex was then not allowed to write the findings file. The sandbox said no. The verdict was in the job log. The host copied it into `codex-review-wave1.result.md`. The fix pass hit the same wall one step later. The edits were in the worktree. `git commit` needs to write metadata outside that directory. The sandbox denied it. HEAD did not move. The host committed `33586ac` (3 files, +59/−26) and re-ran the suite: 38 tests, the opt-in one skipped, all passing. Same story on the acceptance check. Codex reported the suite as failed because it could not create temp files. The host ran it and got a pass. From then on the split was explicit. Codex reads and judges. The host writes the file, makes the commit, and runs unittest.

**Three reviews, three different holes in the same door.**
The run-note work did not fail one big test. It failed three small ones, each invisible to the test that came before it.

The first re-review, on `f41820e`, said the topic codec was fine for quotes and ordinary newlines. Then it fed the parser `one` plus U+2028 plus `two`. Encode and decode returned the whole string. The parser returned `one`. U+2029 did the same. U+0085 came back as `one` as well. Lint was happy. A second research run would not find the first note, because the stored topic had been sawed in half by a character almost nobody types on purpose. `splitlines()` does. `e9f7a25` put one stdlib helper inside the skill tree, `skills/free-research/scripts/run_note.py`, escaped every line break `splitlines()` knows, and stopped splitting frontmatter on those three characters.

The next review agreed the Unicode hole was closed. It opened the next one. The scratch file was now exclusive, and `O_NOFOLLOW` guarded that file. The parent directory was still a path. Check `runs`, look away, and a symlink can stand where `runs` stood. The create and the rename follow it. Codex did not exploit this. It read lines 322 and 340 against the earlier validation and wrote the finding down. In the same report, a mocked `PermissionError` on `mkdir` printed a traceback that contained the vault path. The sanitizer only knew about `FileExistsError`.

`d9a6db2` holds the directory open and does the rest of the write through that handle, and it turns the ugly `OSError`s into `run_note: ...` with no path and no traceback. The test swaps `runs` for an outside symlink halfway through and watches the note stay put. Codex's last pass said ship. It had mocked the writes rather than doing them. The suite does the real writes, including that swap. The merge is `a555837`.

The feeling, afterwards, is a filing-cabinet inspection. First the label maker. Then the drawer the folder actually goes in. Then the error slip taped to the drawer, which had the home address written on it. Each inspection was right. None of them was the whole cabinet.

**Four turns and a cancel.**
The smoke was the test the plan said unit tests could not replace. Free mode. How EzzyBills connects to Xero. Then the same subject in other words, which should read the first note. Launched from a neutral directory so the installed skill was the one on the hook. Flags came from the handoff: `--permission-mode default`, plus denies. Both runs died at turn 4. `stopReason: cancelled`. No new file in the vault `runs/` folder. In a one-shot prompt, default mode asks a person before the first real tool call. Nobody was sitting there. Grok hung up. The annoying part is that the handoff had already learned this lesson once, in the other direction. `--permission-mode plan` had produced nothing, and the note said to use `default`. `default` is the right mode when Jan is at the keyboard. It is the wrong mode when the prompt is the whole session. The rerun, `--always-approve` with the paid tools denied, is the one in `smoke/run1.json` and `smoke/run2.json`: 19 turns, `end_turn`, a version-2 note, a second note, no vault path, no Exa, no Brave, no Firecrawl. The cancelled json was overwritten by that rerun. The cancel itself is the thing worth remembering, because the flag looked conservative and it was a hang-up.

**The filename that stayed in the model's head.**
Run 2 did the hard part. It found `ezzybills-xero-integration--c30f01f3.md`, treated it as a lead, and went back to the sources. Tools Used described "a prior note on how EzzyBills integrates with Xero" and never named the file. The plan's sentence is specific: the second run lists the first note's filename. The skill's sentence was softer, and it sat next to a ban on filesystem paths. The model kept the ban and dropped the name. You can watch it happen in the run json. The reasoning has `c30f01f3`. The report does not. That is a ticket where the tech was told "don't paste the server path" and also left off the hostname operations needed to find the box. `ab8e2fa` makes the example a bare filename and adds a contract test so the wording cannot drift back into "say whether, and why" alone. A third wording was started to watch that line in a real report. Run 3 passed. Its Tools Used line read both earlier notes, `…a691ce08.md` and `…c30f01f3.md`, as leads and named the new `…e955e080.md`, and it printed no vault path.

**The Modes table that said "latest."**
The first real `/free-research` run in Claude Code got as far as loading the skill, and the very first thing on screen was wrong: "treg ≤4 calls / latest.05 total / latest.02 per call." Not a parse error, not a crash. Just a budget that had become a word. The topic started with "latest news on," and Claude Code had filled every `$0` with it. Every test passed, because every test read the file and the file was correct. The only way to see it was to run the skill in the host and read what the model was handed. The run kept going on the repo's numbers, the bug went to the side session with Codex, and `5594664` ended the `$` spelling for good. It is the best argument for end-to-end smokes in this repo: three days of contract tests, and the most visible bug showed up in the first second of a real run.

**The balanced run that refused to spend.**
The plan was to watch `--balanced` open the treg paid family. The free run had left one gap: the WebAccess launch date, which existed only as X search snippets. Then the balanced run's free layer fetched the founder's launch post through TinyFish via treg, for nothing, and got the full text, the timestamp (Oct 16, 11:03), and 228.6K views. Gap closed. `remaining-gaps: none`. No `balance` call, no paid treg, no Exa. The skill did exactly what it is for, and the smoke test learned nothing about the paid path. The only paid evidence is a single manual X search earlier that day, which cost USD 0.0006 and matched the balance drop to the micro-dollar. The PR test plan says so in an unchecked box.

**Codex ran hot, then cold.**
The U1-U5 hand-off went to Codex `gpt-6.1-sol` at high effort. Mid-run, the instruction came back: medium only for sol. Stopping the shell did not stop Codex. The job kept running on the app-server side, reading eval scenarios, until `codex-companion.mjs cancel` killed it. The tree was still clean, so the restart at medium lost nothing. That run implemented all five units, 62 tests green, in one pass. The cancel is now part of the routine: stop the shell task, then cancel the companion job, then check `git status` before relaunching.

---

## Quick Reference

- Ceilings for treg, Exa, Firecrawl, and Brave: SKILL.md's Modes table. README must match. `parallel-cli` caps live in `references/tool-routing.md`.
- Tests, from the repo root: `python3 -m unittest discover -s tests`. They do not spend credits. Copy parity is opt-in: `FREE_RESEARCH_CHECK_COPIES=1`.
- Lint a notes folder: `python3 scripts/lint_run_notes.py /absolute/path/to/the-project-folder/runs`. Version-2 problems are errors. Legacy notes are warnings. Exit 0 can still print warnings.
- Headless smoke: use a hard timeout around `grok -p` with `--always-approve`, and deny Exa, Brave, Firecrawl, Parallel, `rm`, and `git push`. Launch from a neutral directory so the installed skill is the one that loads. `--permission-mode default` cancels when nobody is there to approve.
- Edit `skills/free-research/` in this repo. Use the portable check/install/check flow for Claude Code, Grok, and Codex; the host updates the pack copies and runs six-copy parity plus live smokes in U6. Use one install method per host to avoid duplicate commands.
- The only environment variable the research skill reads is `FREE_RESEARCH_NOTES_DIR`, set in your Grok config. The skill must not print it. Notes land in that folder's `runs/`.
- Money in SKILL.md is written `USD 0.05`, never with a dollar sign before a digit. Claude Code substitutes `$0`, `$1`, and so on with arguments.
- treg call shapes: TinyFish search takes `query` plus `domain_type` (`web` or `news`) in the `query` slot. Fetch takes `body` `{"urls": [...], "format": "markdown"}`. AnyAPI trims (`max_items`, `fields`) go in `query`, never `body`. Every paid call sends `X-Treg-Route-Max-Cost` in `headers`.
- Stopping a Codex shell task does not stop the Codex job. Run `codex-companion.mjs cancel <job>`, then check `git status` before relaunching.
