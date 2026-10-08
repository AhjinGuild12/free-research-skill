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

## T9. Confirmation is not a spend switch

- **Happy:** Free mode. TinyFish fetched the organization's own docs page for the claim. No second origin is in hand. The facet closes because that page is a usable body. The evidence label may be confirmed. The Executive Summary may state that finding. No Exa, Firecrawl, Brave, or `parallel-cli`.
- **Edge:** Free mode. Three articles syndicate one press release. No primary body is in hand. That is one origin. The finding stays unconfirmed. Do not write `gap:` because it is unconfirmed or short of three origins. No Exa, Firecrawl, Brave, or Parallel call.
- **Error:** An Exa highlight arrives with no page body. The highlight is a lead. It does not enter the url-ledger, does not close the facet, and does not confirm the finding.
- **Rule home:** the confirmation bar and origin rules are in `references/verification-tail.md`, loaded after the gate returns. The gap list stays in Step 4.
- **Second turn, free:** The gap list is already empty and the finding is unconfirmed. The next message does not set a mode, does not opt into Parallel, and does not name a new topic. Re-read Step 4 and the safety floor. Do not append `gap:`. Do not call Exa, Firecrawl, Brave, or Parallel.
- **Second turn, balanced:** Same empty gap list and the same unconfirmed label. The original invocation was balanced. Re-read Step 4. Still no Exa, Firecrawl, Brave, or Parallel call.
- **Tools Used:** last30days stays one line. Paid tools appear only if Step 4 actually ran them before the gate returned.

## T17. Summary does not assert an unconfirmed claim

- **Input:** A finished run. One finding is unconfirmed. The remaining-gap list is empty, including when the mode is balanced.
- **Headings:** names and order through Follow-up Options stay Executive Summary, Key Developments, Community Sentiment, Deep Insights, Best Takes, Comparison / Gaps, Actionable Takeaways, Tools Used, Follow-up Options. Deep Insights and Comparison / Gaps stay conditional, as the template already says.
- **Executive Summary:** does not assert the unconfirmed claim. When nothing is confirmed, it says the run did not confirm an answer.
- **Actionable Takeaways:** same rule. A confirmed-with-dissent finding appears in either of those two sections only in a sentence that includes the label "confirmed with dissent attached" and the objection.
- **Other sections:** may carry the finding with the label unconfirmed.
- **Last line,** after Follow-up Options: `your agent is only as good as the worst source it believed.`
- **Forbidden:** renaming a section; asserting the unconfirmed claim in the summary; an Exa, Firecrawl, Brave, or Parallel call caused by the unconfirmed label when the gap list is empty.

## T13. Missing transcript

- **Error:** A report-level claim depends on one discovered video. The transcript package does not import, or the video has no captions. Tools Used says the captions are missing. No captions are invented. No `pip install` runs. The watch page is not sent to Firecrawl, Exa, or Brave to recover captions.
- **Happy:** Person intent. One load-bearing video id and one post URL. The run reads and follows the transcript skill for that video's captions and does not search inside that skill. It thread-fetches that one post. Those bodies can enter the url-ledger and the evidence ledger as full text.
- **Edge:** A third discovered video is not fetched. At most two videos, and only when a report-level claim depends on them. A last30days transcript excerpt is not full text.
- **Tools Used:** the transcript fetch is its own line when it ran. last30days stays one line.

## T14. Keyword hit is not a body

- **Integration:** An X keyword hit or semantic hit without a thread fetch is a lead, not full text. It does not confirm a finding and does not enter the url-ledger.
- **Edge:** A general intent does not run live X before the gate. Person or news may fetch at most three threads before the gate. A fourth thread is not fetched.
- **Forbidden:** Treating the keyword hit as caption text or as a page body. Sending a YouTube watch page to Firecrawl to recover captions. Pip-installing the transcript package.
- **Tools Used:** a thread fetch is its own line when it ran. A keyword hit is not listed as a thread fetch. last30days stays one line.

## T10. Vote flip

- **Rule home:** `references/verification-tail.md`, loaded after the gate returns.
- **Happy:** One primary full text is in hand. Correctness, recency, and source quality all pass. The finding stays confirmed. The Executive Summary may state it.
- **Edge:** The recency pass has no date, so that pass fails. A second pass also fails. The majority failure flips the label to unconfirmed. The sentence stays in the report, outside the Executive Summary and Actionable Takeaways. An abstention counts as a failure. A missing critique is not a pass and is not an abstention. The finding stays unconfirmed until all three critiques are recorded.
- **Error:** A pass that searches or calls Exa is out of contract. Deep-research is not invoked. The passes do not raise an unconfirmed finding to confirmed.
- **Second turn:** The tally is already written. The next message does not set a mode, does not opt into Parallel, and does not name a new topic. Do not spawn a second set of passes. Finish a missing critique in place and do not discard a finished one. Do not spend.

## T11. One sweep

- **Rule home:** `references/verification-tail.md`, loaded after the gate returns.
- **Happy:** One finding is still confirmed after the vote. The sweep's only hit is a thinner objection, with no contradicting primary body in hand. The label is confirmed with dissent attached. The objection is on the ledger. The sentence stays.
- **Flip:** The sweep fetches a contradicting primary and that full text is in hand. That finding becomes unconfirmed. A search hit alone does not flip it.
- **Skip:** Nothing is still confirmed. Write an explicit skip. Do not search.
- **Not the sweep:** The Step 3 limitations angle does not count as this sweep and does not open the remaining-gap gate.
- **Budget:** At most one TinyFish or host search, one free fetch of the single strongest contradicting web URL, and one X keyword search plus one thread fetch. A sweep that already issued its one search is finished. A second sweep does not run.
- **Integration:** Sweep URLs do not add a `gap:` line and do not call Firecrawl, Exa, Brave, or `parallel-cli`.
- **Second turn:** Does not spawn passes, does not sweep, and does not spend. A dissent label does not add a `gap:` line.

## T15. Vault note is not proof

- **Happy:** One finished run resolves `~/Documents/Jan Obsidian/Jan M/1. Projects/Improved Search free-research/runs/`. It writes one slug file. Frontmatter has a parseable `expires` date and `marker: run-note`. The marker is not a source type. The body has the finding labels, the http or https URLs fetched this run, and the closing line. Nothing else.
- **Edge:** A resume and a later run on the same topic replace that file. They do not create a second file. A sibling slug is neither read nor deleted. An unexpired note's confirmed labels do not enter the ledger, do not count as a usable body, and do not close a facet.
- **Expired:** The note's `expires` date is before today. Its prose is not proof. The run free-fetches the stored URLs and judges those fetches as new bodies. The old labels are not restored if a fetch succeeds or fails. Expiry does not create a `gap:` line. The note is not deleted.
- **Undated:** A missing `expires`, or a value that is not a date, counts as expired. Same unbelieved prose. No `gap:` line.
- **Rename:** A failed rename leaves the previous slug file unchanged and does not leave the scratch as a second note.
- **Missed root:** The project folder cannot be resolved, or the slug contains `..` or a slash. No file is written under `raw/`, `3. Resources/X Articles/`, `.firecrawl/`, the skill tree, or the working directory. Tools Used records one skip line. The chat report still returns.
- **Same invocation:** A later turn does not read the note as a new run.
- **Secrets:** The note, the report, Tools Used, and the skill files do not contain API keys, environment values, or credential-file contents.

## T12. Missing parallel-cli

- **Error:** `parallel-cli` is not on PATH, or the only `parallel` on PATH is GNU parallel. Any mode, including a topic that contains the word Parallel. Do not install a package. Do not invoke GNU `parallel`. Do not call the Parallel Task API. Tools Used has a skip line and does not list `parallel-cli` as used.
- **Integration:** Free mode. The topic string contains "Parallel". There is no `--parallel` flag and no unquoted instruction to use Parallel. `parallel-opt-in` stays false. The CLI does not run. `--deep` alone, including when research-to-x-article passed `--deep`, does not set the opt-in.
- **last30days:** do not add `--web-backend parallel-mcp` unless the user asked for that backend.
- **Default:** with no flag and no explicit instruction, the CLI stays off. This trace does not call it.

## T16. Search MCP and the opt-in lane

- **Disconnected:** Parallel Search MCP is not connected. Do not connect it. Do not call it. Do not install. Free mode still runs TinyFish.
- **Happy:** Parallel Search MCP is already connected. Free mode. One extra angle. TinyFish still runs. A fetched complete body still faces the confirmation bar. An excerpt-capped result is a lead, not a url-ledger body, and it does not close or open a gap. This lane is not spend and does not need `--parallel`.
- **Edge:** The user passes `--parallel` on balanced mode. A named gap is still open after Brave. `parallel-cli` is on PATH. At most one `research run` and two extracts for the whole invocation, including a later turn. Deep mode doubles those caps. An open gap without the opt-in does not fire the CLI. The opt-in without an open gap does not fire it.
- **Extract:** A `research run`'s prose is a lead, not a usable body, not Deep Insights, and not a new gap. An extract enters the url-ledger only when it returns the full article body. Default excerpt output does not close a facet and does not set the confirmation label.
- **Off by default:** no flag and no explicit instruction means `parallel-opt-in` is false. Do not call the CLI in that case.

---

## T18a. tool-routing.md fails to load

- **Input:** `/free-research widgets --balanced`. A named gap is still open. `references/tool-routing.md` fails to load.
- **Allowed:** last30days; TinyFish or host free web tools.
- **Forbidden:** Exa; Firecrawl, including `firecrawl --status`; Brave; `parallel-cli`; the Parallel Task API; any other paid call. No paid family runs.
- **Gate:** the gate returns.
- **Note:** no note is written.
- **Tools Used:** free-layer tools only. No paid tool listed as used.
- **Report:** still returns, with the closing line.

## T18b. verification-tail.md fails to load

- **Input:** `/free-research widgets --deep`. One Exa call ran while a gap was open. The gate has since returned. `references/verification-tail.md` then fails to load.
- **Allowed:** that one Exa call, which ran before the gate returned.
- **Forbidden:** any further Exa, Firecrawl, Brave, or `parallel-cli` call. No second Exa call. No note write. No sweep that spends.
- **Findings:** a finding whose review did not finish stays unconfirmed. Executive Summary and Actionable Takeaways do not assert it.
- **Tools Used:** Exa appears once. Calls made before the gate returned still count.
- **Report:** ships, with the closing line.

## T22. Paid order exhausted, facet unresolved

- **Input:** `/free-research widgets --balanced`. One named gap is open. Exa is connected and returns no URLs. Firecrawl is unauthenticated. Brave is disconnected. There is no `--parallel` opt-in.
- **Order:** Exa runs one search call and returns no URLs. It does not run again. Firecrawl then runs one `--status` and stops. No scrape, no search, no second `--status`. Brave is skipped with no query. `parallel-cli` does not run.
- **Forbidden:** repeating any of those calls; running a family out of that order; a call past a Modes table ceiling.
- **Gate:** the gate returns. The facet is not marked closed.
- **Report:** the facet is unresolved under Comparison / Gaps.

## T23. Balanced ceilings, then the gate returns

- **Input:** `/free-research widgets --balanced`. A named gap is still open after Exa hits its ceiling. Firecrawl is authed. Brave is connected. There is no `--parallel` opt-in. The gap is still open after Firecrawl.
- **Order:** `--balanced` Exa ≤2 search calls, and no third. Then Firecrawl, one leftover scrape, inside `--balanced` Firecrawl ≤3 leftover ops. Then `--balanced` Brave ≤1 query, and no second. Then the gate returns. `parallel-cli` does not run.
- **Forbidden:** a family running twice, or past its ceiling; Exa after Firecrawl has started; Brave before Firecrawl; any call after the gate returns.
- **Gate:** the gate returns because no paid family remains eligible. The facet stays unresolved under Comparison / Gaps. It is not marked closed.

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
