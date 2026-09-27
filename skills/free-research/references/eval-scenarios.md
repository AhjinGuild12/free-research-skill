# Free Research — Eval Scenarios

Tabletop traces for the routing contract. Walk them without spending credits. Live smokes L1/L2 are the runbook U4 executes; pass bars live here, not in a second document.

Each trace names allowed tools, forbidden tools, file writes, feedback timing, and Tools Used lines.

---

## T1. `--free` + TinyFish down

Covers AE1, F1, R1.

- **Input:** `/free-research widgets --free`. TinyFish MCP unauthenticated. Exa MCP connected.
- **Allowed:** last30days; host `web_search` / `open_page` / `web_fetch`; re-auth hint for TinyFish.
- **Forbidden:** `firecrawl` (any subcommand, including `--status`); Exa MCP; Brave MCP; TinyFish `run_web_automation`; claiming TinyFish ran.
- **Files:** none under `.firecrawl/`.
- **Feedback:** none.
- **Gate:** emit `remaining-gaps: none` or remaining `gap:` lines; either way, no paid calls.
- **Tools Used:** last30days (one line); `web_search / open_page (free-host fallback)`. No Firecrawl, Exa, or Brave.
- **Report:** omit Deep Insights. If thin, offer `--balanced` / `--deep`.

## T2. `--balanced` + TinyFish down + strong host coverage

Covers F3, R4.

- **Input:** `/free-research widgets --balanced`. TinyFish down. Host fetches already answer the asked facets.
- **Allowed:** last30days; host web tools.
- **Forbidden:** Firecrawl; Exa; Brave; treating TinyFish-down as the escalate reason.
- **Files:** no `.firecrawl/` writes.
- **Gate:** emit `remaining-gaps: none`. Closed.
- **Tools Used:** last30days; host fallback; `remaining-gaps: none`. Not TinyFish. Not Firecrawl. Not Exa.

## T3. `--balanced` + strong free coverage

Covers AE2, R4, R5.

- **Input:** `/free-research widgets --balanced`. TinyFish works. Six recent primary sources already answer the question.
- **Allowed:** last30days; TinyFish search + fetch.
- **Forbidden:** Firecrawl "because mode allows it"; Exa; Brave.
- **Files:** no `.firecrawl/`.
- **Gate:** emit `remaining-gaps: none`. Closed. Omit Deep Insights.
- **Tools Used:** last30days; TinyFish search × N; TinyFish fetch_content; `remaining-gaps: none`.

## T4. `--balanced` + named gap + Exa connected

Covers AE3, F2, R2, R3, R5.

- **Input:** `/free-research widgets --balanced`. Free layer missed official pricing. Exa connected. Firecrawl authed. Brave connected.
- **Required before first paid call:** `gap: official pricing — <why>`.
- **Allowed:** last30days; TinyFish or host free layer; free-fetch leftover URLs already in hand; MCP-list probe; Exa search on the pricing facet (≤2); Firecrawl leftover scrape only if those URLs still lack a usable body after Exa; Brave only if remaining gaps remain after Firecrawl (≤1).
- **Forbidden:** `scrape --query`; nested `firecrawl-search` skill; Firecrawl before `--status` when Firecrawl leftover work is needed; Firecrawl search while Exa returned URLs; skipping connected Exa because Firecrawl exists; firing Exa + Firecrawl + Brave in one turn; “every connected paid tool” as the happy path.
- **Files:** `./.firecrawl/` only if Firecrawl leftover work ran. Do not git-add.
- **Feedback:** one `search-feedback` per non-empty Firecrawl **search**, background, before synthesis; skip if no Firecrawl search ran, opt-out env, or empty results.
- **Happy leftover-empty:** Exa returns usable bodies for pricing → remaining-gaps empty → Firecrawl and Brave **must not** run. This is success, not a miss.
- **Tools Used:** free layer tools that ran; probe; each Step 4 paid tool that actually ran, with why. last30days one line. Not `firecrawl-search` skill.
- **Report:** include Deep Insights only if a Step 4 paid tool ran.

## T5. `--deep` + Firecrawl missing

Covers F4, R2, R7.

- **Input:** `/free-research widgets --deep`. Named gap exists. `firecrawl` not on PATH or `--status` unauthenticated / 401 / 402 / 429 / zero credits.
- **Allowed:** last30days; TinyFish or host free layer; one `--status` if the binary exists and leftover Firecrawl work would otherwise run; Exa MCP and Brave MCP if connected.
- **Forbidden:** retry loops; claiming Firecrawl ran; skipping connected Exa because Firecrawl failed.
- **Files:** no successful Firecrawl writes required.
- **Tools Used:** free layer; Exa/Brave if they ran; never list Firecrawl as used.
- **Report:** keep free-layer evidence. Deep Insights if any Step 4 paid MCP contributed.

Do not tag this trace as R9. Live smokes are L1/L2 only. Strip legacy Firecrawl-plan eval tags R9/R10 (not this skill’s live-smoke requirement).

## T6. Exa + Firecrawl both in play on `--deep`

Covers connected-MCP-use, R2, KTD5.

- **Input:** `/free-research widgets --deep`. Named gap exists. Exa MCP is connected. Firecrawl CLI is authed.
- **Allowed:** Exa MCP on facets that still lack URLs (≤4 search calls); Firecrawl leftover scrape/JS if URLs still lack a usable body after Exa; Firecrawl search only if Exa returned no URLs.
- **Forbidden:** skipping Exa because Firecrawl exists; running Exa search and Firecrawl search together; skipping Firecrawl leftover scrape while URLs still lack a body **and** remaining gaps remain.
- **Required skip:** skipping Firecrawl because remaining gaps closed and the leftover URL set is empty.
- **Tools Used:** Exa (gap queries) if it ran; Firecrawl CLI if leftover work ran. Both listed only if both ran.

## T7. URL already in the ledger is not Firecrawl-scraped

Covers AE4, R6.

- **Input:** `--balanced` or `--deep`. TinyFish or Exa already returned a usable body for `https://example.com/pricing`. Remaining gaps otherwise empty or that URL is the leftover candidate.
- **Allowed:** ledger records that URL as fetched.
- **Forbidden:** Firecrawl scrape or `search --scrape` of that URL.
- **Tools Used:** does not list a Firecrawl scrape of that URL.

## T8. `--deep` + strong coverage

Covers R4 including `--deep`.

- **Input:** `/free-research widgets --deep`. Free layer already answers with usable primary bodies.
- **Allowed:** last30days; TinyFish or host free layer.
- **Forbidden:** Exa, Brave, Firecrawl, including `--status`.
- **Gate:** emit `remaining-gaps: none`. Zero paid calls.
- **Tools Used:** free layer; `remaining-gaps: none`. Omit Deep Insights.

---

## Live smokes (U4 runs these; this file is the pass bar)

`--free` first. Spend Exa/Firecrawl only on L2, and only for remaining gaps. Do not add a `research-to-x-article` smoke. L1 audits free-research Step 4, not last30days internals.

### L1. `--free` (zero Step 4 spend)

Run a real `--free` topic with TinyFish in whatever state the host is in.

- **Pass:** Step 4 / tool log has no Exa MCP, no Brave MCP, no `firecrawl` process (including `--status`), no TinyFish `run_web_automation`. Quote the full tool list, not “no firecrawl process.”
- **Fail:** any of those tools ran, even if Firecrawl was absent.
- Covers AE1.

### L2. `--balanced` (one spend, brake not unban)

One real `--balanced` run on a topic with a real official-docs or pricing gap. If the free layer is actually strong, that is T3 evidence — pick another topic; do not force Firecrawl so this smoke can pass.

**Pass checklist (fail-closed):**

1. MCP probe recorded (Exa / Brave / Firecrawl: connected | disconnected | unauthed).
2. Written `gap: … — …` **before** the first paid call (chat / log order). Empty list is invalid for L2.
3. If Exa connected → Tools Used lists Exa on that facet, search-call count ≤2.
4. After Exa (or after free leftover fetch), leftover URL set is **empty** and Firecrawl plus Brave call counts are **zero**. If the first topic cannot produce that skip, change topic rather than treating Firecrawl absence as optional.
5. Firecrawl only leftover URLs / JS if leftovers were not empty; do **not** require search-feedback unless a Firecrawl **search** actually ran.
6. Brave only if remaining gaps remained, ≤1.
7. Firecrawl leftover ops ≤3, parallel ≤2.
8. Fail if Exa connected and omitted. Fail if Firecrawl searched or scraped a URL that already had a usable body.

Handoff quotes: probe result, verbatim `gap:` lines, Exa/Firecrawl/Brave call counts, leftover-URL note, both Tools Used blocks. “We ran `--balanced`” is not done.

Covers AE3 only when Exa-if-connected is mandatory and the leftover-empty skip is observed.

Do not spend credits on interact for these smokes.
