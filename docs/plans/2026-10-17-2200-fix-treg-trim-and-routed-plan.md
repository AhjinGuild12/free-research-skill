---
title: "fix: Trim treg results and cap every treg call server-side - Plan"
type: fix
date: 2026-10-17
artifact_contract: ce-unified-plan/v1
product_contract_source: ce-plan-bootstrap
execution: code
---

# fix: Trim treg results and cap every treg call server-side - Plan

**Target repo:** `free-research-skill`. Paths below are relative to it. Builds on `docs/plans/2026-10-17-1846-feat-treg-free-research-plan.md` (v1.2.0).

## Goal Capsule

- **Objective:** a `/free-research` run that touches treg brings back only the rows and fields the remaining-gap gate needs, and cannot be charged more than the Modes-table per-call ceiling (or anything at all on a free endpoint), even if a catalog price is wrong.
- **Means:** AnyAPI trim options in the MCP `call` `query` slot (KTD1), and an `X-Treg-Route-Max-Cost` header on every treg `call` (KTD2, KTD3). Routed `treg.*` endpoints stay never-use for the reasons now verified (KTD4).
- **Authority:** SKILL.md's gate rules and Modes table outrank this plan. R-IDs win on behavior; KTDs win on mechanism.
- **Stop conditions:** stop and report if a live call shows the header is not honored over MCP, or that a trimmed AnyAPI result costs more than an untrimmed one.
- **Execution profile:** skill text, reference docs, and contract tests. No frontend. Codex gpt-6.1-sol at medium effort implements it; this session checks the diff, runs the tests, syncs copies, and commits.

---

## Product Contract

### Summary

Teach the treg ops card to request small AnyAPI pages through the `query` slot and to keep free TinyFish calls lean. Add a server-enforced dollar cap header to every treg call: the remaining per-call ceiling on paid calls, `0` on free calls. Keep the four routed endpoints banned, but replace the outdated "no pre-call price" reason with the verified ones. Bump the skill to 1.2.1.

### Problem Frame

The v1.2.0 smoke runs found two gaps. First, `anyapi.x.search.posts` ignored body `limit: 5` and returned 20 posts (~14 KB) into context. Its own hint names `fields`, `max_items`, `summary=true`, and `jq`, but `max_items` in the body was rejected (400 `invalid_input`, no charge). Second, the skill bans routed endpoints as having "no pre-call price" and tells the agent never to guess a max-cost option. treg does document a max-cost header, so that wording is wrong and the skill passes up a server-side spend guard.

### Requirements

- R1. Paid treg calls to `anyapi.*` endpoints send `max_items` and `fields` in the MCP `call` `query` slot, never in `body`, sized to what the gate needs.
- R2. Paid treg calls to non-AnyAPI endpoints request their smallest documented page and extract only gate-relevant fields; the skill never invents trim parameters for them.
- R3. Free TinyFish-via-treg calls stay lean: search never attaches page content, and fetch requests only the selected URLs with link, image, and metadata extras off.
- R4. Every paid treg `call` carries `X-Treg-Route-Max-Cost` set to the lesser of the Modes-table per-call ceiling and the remaining invocation dollar budget. Client-side reservation and post-call cost checks stay.
- R5. Every free-allowlist treg `call` carries `X-Treg-Route-Max-Cost: 0`. Step 3's post-call nonzero-charge stop rule stays.
- R6. A `402` with `detail.error` `route_max_cost` is a cap or price rejection with nothing charged. It is never read as a balance failure, whatever the MCP `hint` says, and it still counts as an attempt.
- R7. `treg.web.search`, `treg.web.extract`, `treg.companies.enrich`, and `treg.x.search.posts` stay never-use, with the reason stated as the verified behavior (KTD4) instead of "no pre-call price".
- R8. Contract tests pin R1, R4 to R7, and fail when the retired wording returns.

### Scope Boundaries

- Not changing Modes-table limits, the paid allowlist IDs, or the ladder order.
- Not using `summary=true` (an outline is not evidence) or `jq` (fields and max_items cover the need; `jq` adds a failure mode with a full-result fallback).
- Not using the routed `402` plan listing to discover prices. It is a call attempt, and the skill bans calls made to discover price.
- Considered, not built: a `X-Treg-Route-Strict-Filters` header. It only matters on routed endpoints, which stay banned.

#### Deferred to Follow-Up Work

- `/forjan` update of `FOR_Jan_FreeResearchSkill.md` (its routing lesson repeats the old routed reason). That skill commits and pushes, so it runs on Jan's call.
- Re-evaluate routed endpoints if treg forwards trim params to children and drops the duplicate `raw` payload.

### Sources

- Findings note with probe results: `side-session-notes/.../treg-trim-and-routed-findings.md` (outside the repo).
- treg docs `https://treg.to/llms.txt`: "Hard ceiling before you spend" and "Routed endpoints" sections.
- AnyAPI OpenAPI `https://api.getanyapi.com/openapi.json`: `POST /v1/run/{sku}` declares `fields`, `max_items`, `summary`, `jq` as query parameters that "do not change cost".

---

## Planning Contract

### Key Technical Decisions

- KTD1. Trim options ride in the MCP `call` `query` slot alongside the `body` slot. Probe: `anyapi.x.search.posts` with `body={query, limit:5}` and `query={max_items:3, fields:"url,text,createdUtc,authorUsername"}` returned 3 rows of 4 keys plus `_truncated:{shown:3,total:20}`, about 1 KB, `cost_usd` 0.0006, the same charge as untrimmed. The options are AnyAPI's, not treg's, so R2 handles other providers.
- KTD2. The paid cap header value is `min(per-call ceiling, remaining dollar budget)`. Probe: a `0.0001` cap on a `$0.00075` endpoint returned `402 route_max_cost` with nothing charged. treg sets no default cap on direct calls, so without the header a wrong catalog price is caught only after the charge.
- KTD3. Free calls send cap `0`. Probe: `tinyfish.web.search` with `X-Treg-Route-Max-Cost: 0` returned 200 at `cost_usd` 0. A free endpoint that turns paid then fails before any charge. That `402` means the free price check failed: skip that endpoint and use host web.
- KTD4. Routed endpoints stay banned. The cap header does make them cost-safe: a `0.0001` cap with `X-Treg-Route-Waterfall: 0` returned `402`, `charged_micro: 0`. The ban stands for three verified reasons:
  - They dropped the `query` trim params and returned all 20 rows.
  - They return both `output` and `raw`, so the same rows arrive twice (~28 KB).
  - The catalog headline for `treg.web.search` and `treg.web.extract` reads "free" while misses bill (child range up to $0.16 and $0.01). That headline could pass Step 3's zero-price check.

  The explicit child endpoints are already on the paid allowlist and can be trimmed.

### Assumptions

- The MCP `call` `headers` slot keeps passing `X-Treg-*` headers to treg rather than only upstream. Verified today on direct, routed, and free calls.
- `max_items: 5` is enough rows for one gap facet. The implementer may state a smaller number if the gap list is narrow.

---

## Implementation Units

### U1. Response trimming in the treg ops card and free layer

- **Goal:** treg results arrive at gate size (R1, R2, R3).
- **Requirements:** R1, R2, R3; KTD1.
- **Dependencies:** none.
- **Files:** `skills/free-research/references/tool-routing.md` (treg ops card, new trim step or rule next to step 2), `skills/free-research/SKILL.md` (Step 3 treg free allowlist paragraph and 3b fetch sentence).
- **Approach:**
  1. In the ops card, say AnyAPI endpoints take `max_items` and `fields` in the `query` slot with the request in `body`, never in the body (400 `invalid_input`). Give the X field set (`url,text,createdUtc,authorUsername`) as the example. Body `limit` is advisory.
  2. Add the R2 rule for other providers.
  3. In SKILL.md Step 3, add R3: treg search never sends `fetch`; treg fetch sends only selected URLs and leaves `links`, `image_links`, and `page_metadata` off.
- **Patterns to follow:** the ops card's numbered steps; keep one owner per rule (the card owns paid trimming, SKILL.md Step 3 owns free calls).
- **Test scenarios:** covered in U4.
- **Verification:** a reader of the ops card alone can build a trimmed `anyapi.x.search.posts` call.

### U2. Server-side cap header on every treg call

- **Goal:** treg refuses any call above the remaining ceiling before it charges (R4, R5, R6).
- **Requirements:** R4, R5, R6; KTD2, KTD3.
- **Dependencies:** none.
- **Files:** `skills/free-research/SKILL.md` (Step 3 free allowlist paragraph, Step 4 item 3, the "treg MCP tool boundary" paragraph), `skills/free-research/references/tool-routing.md` (ops card intro and steps 2-4).
- **Approach:**
  1. Replace the ops card's "Never guess a max-cost parameter. If the loaded `call` schema offers one…" with the R4 header rule in the `headers` slot.
  2. Replace SKILL.md's "do not invent arguments or a server-side max-cost option" with a pointer to the header rule. The tool boundary sentence and its four tools stay as they are; the existing test parses it.
  3. Add R5 to the Step 3 free allowlist paragraph, plus the KTD3 handling of a free-endpoint `402`.
  4. Add R6 to ops card step 4 (or step 3): `route_max_cost` is a cap rejection, nothing charged, counted as an attempt, not a balance failure.
- **Patterns to follow:** existing reservation wording in ops card step 3; the header supplements client checks and does not replace them.
- **Test scenarios:** covered in U4.
- **Verification:** no remaining text tells the agent the max-cost option is unknown or forbidden.

### U3. Corrected routed-endpoint reason

- **Goal:** the ban reads as the verified behavior (R7).
- **Requirements:** R7; KTD4.
- **Dependencies:** none.
- **Files:** `skills/free-research/SKILL.md` (Never-use paragraph), `skills/free-research/references/tool-routing.md` (Never-use paragraph and cost-map row "treg fixed paid allowlist"), `skills/free-research/references/eval-scenarios.md` (T29 Required line).
- **Approach:** replace "Routed endpoints have no pre-call price and are forbidden" / "Routed endpoints lack pre-call prices" / T29's "routed endpoint with no pre-call price" with one short reason: routed endpoints drop trim params, return `output` plus `raw`, and can show a free headline while misses bill. Keep every Never-use ID list unchanged.
- **Patterns to follow:** the existing Never-use paragraphs; the full KTD4 detail belongs in this plan, not the skill text.
- **Test scenarios:** covered in U4.
- **Verification:** no routed-endpoint text in `skills/` claims a missing pre-call price. Legitimate free-endpoint "pre-call price checks" wording (eval-scenarios T26 missing-cost variant) stays.

### U4. Contract tests and version bump

- **Goal:** the new rules cannot drift silently (R8).
- **Requirements:** R8.
- **Dependencies:** U1, U2, U3.
- **Files:** `tests/test_skill_contract.py`, `tests/test_plugin_contract.py`, `skills/free-research/SKILL.md` (frontmatter `version`), `.claude-plugin/plugin.json`, `.grok-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `.grok-plugin/marketplace.json`.
- **Approach:** add focused tests next to the existing treg tests; bump 1.2.0 to 1.2.1 in all five version sites (SKILL.md, both `plugin.json`, both `marketplace.json`) and in the `test_versions_match_across_manifests` expectation.
- **Patterns to follow:** `test_treg_evidence_and_spend_boundaries` (phrase assertions) and `test_treg_read_only_and_fixed_paid_routes` (block extraction plus mutation check).
- **Test scenarios:**
  - The ops card names the `query` slot together with `max_items` and `fields`, and says they never go in the body.
  - Mutating the ops card so `max_items` sits in the body makes the trim test fail.
  - SKILL.md and the ops card both contain `X-Treg-Route-Max-Cost`; the ops card states the lesser-of rule.
  - The SKILL.md treg free allowlist block (between `### treg free allowlist` and `### 3a.`) contains `X-Treg-Route-Max-Cost: 0`.
  - The ops card names `route_max_cost` and says nothing was charged.
  - The retired claims "no pre-call price", "lack pre-call prices", "Never guess a max-cost parameter", and "server-side max-cost option" are absent from SKILL.md, tool-routing.md, and eval-scenarios.md.
  - The Never-use blocks still list every `TREG_NEVER` ID (existing test, unchanged).
  - `_skill_version()` is `1.2.1` and both plugin and both marketplace manifests match.
- **Verification:** the full unittest run passes.

### U5. Sync installed copies

- **Goal:** the three installed copies match the repo skill tree.
- **Requirements:** Definition of Done.
- **Dependencies:** U4.
- **Files:** none in the repo; copies at `~/.claude/skills/free-research`, `~/.grok/skills/free-research`, `~/Projects/skill-pack/grok/free-research`.
- **Approach:** mirror `skills/free-research/` into each copy so file inventories match, with no extra files.
- **Test expectation:** none -- copy operation; the copy-parity test is the check.
- **Verification:** the copy-parity test passes with its env flag set.

---

## Verification Contract

- `python3 -m unittest discover -s tests` passes from the repo root.
- `FREE_RESEARCH_CHECK_COPIES=1 python3 -m unittest discover -s tests` passes after U5.
- `grep -rniE "no pre-call price|lack pre-call prices" skills/` returns nothing.

## Definition of Done

- R1 to R8 hold in the skill text and are pinned by tests.
- Version is 1.2.1 in SKILL.md, both plugin manifests, and both marketplace manifests.
- Both verification commands pass; the copy check covers all three installed copies.
- No leftover experimental text or abandoned test code in the diff.
- Work is committed on `fix/treg-trim-and-routed`.
