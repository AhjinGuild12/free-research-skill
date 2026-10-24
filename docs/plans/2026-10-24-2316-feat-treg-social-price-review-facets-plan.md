---
title: "free-research treg social, price, and review facets - Plan"
type: feat
date: 2026-10-24
artifact_contract: ce-unified-plan/v1
product_contract_source: ce-plan-bootstrap
execution: code
---

# free-research treg social, price, and review facets - Plan

**Builds on:** PR #5 (v1.3.0: `--thorough`, treg-first, header-capped `treg.web.extract`). Land this after PR #5 merges, on a branch from `main`.

## Goal Capsule

- **Objective:** When Jan researches a product, app, company, place, or public reaction, the report carries the actual social posts, current prices, and review ratings from the platforms that hold them. He should not have to open TikTok, Amazon, or Trustpilot himself.
- **Means:** Add three facet types (social, price/listing, reviews) to the treg paid allowlist. Endpoints are explicit and priced. They are used in balanced, deep, and thorough under the existing caps (KTD1, KTD2).
- **Authority:** SKILL.md's Modes table and gate rules stay the single owner of spend. `references/tool-routing.md` owns the facet table.
- **Stop conditions:**
  - A needed endpoint is priced per result or row, so the per-call bound cannot be reserved before the call.
  - A change would need `my_tools` or a connected personal account.
- **Execution profile:** Codex gpt-6.1-sol at medium effort, or Grok, Gemini 4 Argon, or Sonnet 5.5 when the Codex quota is out. Claude Code reviews, tests, and runs smokes.

---

## Product Contract

### Summary

Extend treg's facet routing from Reddit, X, YouTube captions, SERP competitors, and page extraction to three more gap types:

- **Social:** TikTok, Instagram, YouTube, LinkedIn, Facebook, and Threads.
- **Price and listing:** Google Shopping, Amazon, Walmart, eBay, Etsy, and Shopify stores.
- **Reviews and ratings:** App Store, Google Play, Trustpilot, Yelp, Glassdoor, Tripadvisor, and Google Maps.

Each facet maps to explicit catalog endpoints under USD 0.02 per call. Intents gain default facet orders, and thorough checklists name these facets. Free mode stays zero-spend with no account access, and a free report tells Jan when social, price, or review data is available one level up.

### Problem Frame

The treg catalog covers dozens of social, e-commerce, and review platforms. Today the skill only knows Reddit, X, YouTube captions, SERP competitors, and page extraction. A question like "is this app any good", "what does it cost on Amazon", or "what are people saying on TikTok" therefore ends as an unresolved gap, or as a web page that summarizes reviews second-hand. Jan wants enough detail in one report that he does not search again.

### Requirements

**New facets**

- R1. The treg paid allowlist adds three facet types. Each facet type names explicit catalog endpoints with observed prices.
  - **Social posts:** TikTok, Instagram hashtag, YouTube search, LinkedIn, Facebook page, and Threads.
  - **Prices and listings:** Google Shopping, Amazon, Walmart, eBay, Etsy, and Shopify store.
  - **Reviews and ratings:** App Store, Google Play, Trustpilot, Yelp, Glassdoor, Tripadvisor, and Google Maps.
- R2. Only endpoints billed per call or per success with a known price at or under the per-call ceiling are allowed. Per-result or per-row billing and anything above USD 0.02 per call are excluded.
- R3. An endpoint that needs an identifier (app id, business URL, ASIN, place id, profile URL) is called only after the free layer found that identifier. The skill never guesses ids.

**Routing**

- R4. Intents get a default facet order:
  - recommendations: reviews, prices, social;
  - competitor: prices, reviews, SERP competitors;
  - person: LinkedIn, X, YouTube;
  - news: X, Reddit, TikTok;
  - general: unchanged.
- R5. Thorough checklists name these facets where they apply. For example, a product checklist item "current prices" maps to the price facet.

**Boundaries**

- R6. Free mode stays zero-spend. It uses no connected-account routes and no paid facet endpoints.
- R7. A free report adds one line under Follow-up Options when an open or thin facet is a social, price, or review facet: "social, price, or review data for this topic is available with `--balanced`".
- R8. `my_tools`, connected personal accounts, posting, and publishing stay forbidden. Platforms in Chinese markets are out unless the topic is in Chinese or about the China market, and then still under the same caps.

**Quality**

- R9. Contract tests pin the new allowlist, the price ceiling, the identifier-first rule, and the free-mode ban. One eval trace per facet type, and one live balanced smoke that hits each facet type once.

### Success Criteria

- A balanced run on an app or product topic returns real ratings and review quotes plus at least one current price, attributed to their platforms. Treg spend stays within USD 0.05.
- A free run on the same topic says which of those facets `--balanced` would add.

### Scope Boundaries

- No connected-account (free with your account) routes and no opt-in flag for them in this plan.
- No change to any Modes-table cap, the paid order, or report sections.
- Routed `treg.*` endpoints other than `treg.web.extract` stay forbidden.

#### Deferred to Follow-Up Work

- A `--use-accounts` opt-in for read-only routes through Jan's own connected accounts.
- China-market platform facets (Douyin, Weibo, Xiaohongshu, Bilibili, Taobao, JD) as their own table.
- Investigating `youtube.youtube.search.videos`, listed as free, as a free-layer candidate.

---

## Planning Contract

### Key Technical Decisions

- KTD1. **Paid catalog endpoints in balanced and up, no personal accounts.** (session-settled: user-approved - chosen over using "free with your account" routes in free mode: personal accounts risk being flagged by the platforms, and the paid routes cost USD 0.0001-0.015 per success.)
- KTD2. **Facet table rows list a primary and a backup endpoint per platform, chosen by inputs held, then reliability, then price.** This follows the treg skill's provider-choice order. Candidate endpoints observed on 2026-10-24 (confirm price at implementation):

| Facet | Platform | Primary / backup | Observed USD |
| --- | --- | --- | --- |
| social | TikTok search | `crawl4ai.tiktok.search.videos` / `tikhub.tiktok.search.videos` | 0.0005 / 0.001 per success |
| social | Instagram hashtag | `crawl4ai.instagram.hashtag.posts` / `tikhub.x.instagram-v1-fetch-hashtag-posts` | 0.0009 / 0.001 |
| social | YouTube search | `crawl4ai.youtube.search.videos` / `tikhub.x.youtube-web-search-video` | 0.0009 / 0.001 |
| social | LinkedIn posts | `anyapi.linkedin.search.posts` / `scrapecreators.x.v1-linkedin-search-posts` | 0.002 / 0.00188 per call |
| social | Facebook page posts (URL known) | `crawl4ai.facebook.user.posts` / `anyapi.facebook.user.posts` | 0.00135 / 0.002 |
| social | Threads search | `scrapecreators.x.v1-threads-search` / `tikhub.x.threads-web-search-recent` | 0.00188 / 0.002 |
| price | Google Shopping | `crawl4ai.google.serp.shopping` / `litescrape.google.serp.shopping` | 0.00015 / 0.00015 |
| price | Amazon search | `crawl4ai.amazon.search.products` / `justoneapi.x.amazon-search-products-v1` | 0.0135 / 0.0148 |
| price | Walmart product (id known) | `crawl4ai.walmart.product.detail` | 0.00135 |
| price | eBay search | `serpapi.x.ebay-search` | 0.015 |
| price | Etsy search | `crawl4ai.etsy.search.products` | 0.00015 |
| price | Shopify store (URL known) | `crawl4ai.shopify.store.products` | 0.00015 |
| reviews | App Store (app id known) | `litescrape.app_store.reviews` / `crawl4ai.app-store.app.detail` | 0.00015 / 0.00015 |
| reviews | Google Play (app id known) | `litescrape.google_play.reviews` | 0.00015 |
| reviews | Trustpilot (domain known) | `crawl4ai.trustpilot.business.reviews` | 0.00135 |
| reviews | Yelp (business known) | `crawl4ai.yelp.business.reviews` / `litescrape.yelp.business.reviews` | 0.00015 / 0.00015 |
| reviews | Glassdoor (company known) | `crawl4ai.glassdoor.company.reviews` | 0.00015 |
| reviews | Tripadvisor (place known) | `litescrape.tripadvisor.business.reviews` | 0.00015 |
| reviews | Google Maps (place id known) | `crawl4ai.google.maps.reviews` / `litescrape.google.maps.reviews` | 0.00015 / 0.00015 |

  Excluded by R2: Facebook keyword search (USD 0.0295-0.0661), all `brightdata.*` per-result rows, and `apify.*` per-result rows.
- KTD3. **Cheapest-first ordering inside one facet turn.** Google Shopping comes before Amazon (100x cheaper), so balanced's 4 calls and USD 0.05 can cover three facets. Amazon at USD 0.0135 is used only when Shopping did not answer the price facet.
- KTD4. **Results are leads until a body answers the facet.** A row of posts or reviews with text, rating, and date is a usable body for that facet. Titles-only rows stay leads, as today.

### Assumptions

- Catalog prices and ids observed on 2026-10-24 still hold. Implementation re-checks each with `catalog_search` and drops any that moved above the ceiling.
- Per-success endpoints charge nothing on a miss, as the catalog states.

### Risks & Dependencies

- PR #5 must merge first. This plan edits the same facet table and tests.
- Scraped platforms change often. Each facet keeps a backup endpoint, and failure is "returned no URLs" for that facet.
- Review and post rows can be large. Trim to the gate-relevant fields (text, rating, date, author, link) per the existing trim rules.

---

## Implementation Units

### U1. Pin the facets in tests

- **Goal:** Tests encode the new allowlist and rules before the text changes.
- **Requirements:** R1, R2, R3, R6, R8, R9
- **Dependencies:** PR #5 merged
- **Files:** `tests/test_skill_contract.py`
- **Approach:**
  1. Extend the paid allowlist constant with the KTD2 ids.
  2. Assert every id has an observed price at or under the per-call ceiling in the routing table, and that no `brightdata.` or `apify.` id is allowed.
  3. Assert the identifier-first sentence and the free-mode ban sentence exist.
- **Execution note:** Test-first.
- **Test scenarios:**
  - A routing table that adds `anyapi.facebook.search_posts` fails the price-ceiling test.
  - A routing table missing the reviews facet row fails.
  - SKILL.md free-mode text that permits a facet endpoint fails.
  - The existing ceiling, second-owner, and `$<digit>` tests still pass.
- **Verification:** Tests fail for the right reasons, then pass after U2.

### U2. Facet table, intent order, and free-report hint

- **Goal:** The skill knows the new facets and when to use them.
- **Requirements:** R1-R8
- **Dependencies:** U1
- **Files:** `skills/free-research/references/tool-routing.md`, `skills/free-research/SKILL.md`
- **Approach:**
  1. Add the KTD2 rows to the treg paid allowlist with the identifier-first rule (R3) and the cheapest-first rule (KTD3).
  2. In SKILL.md Step 5, add the R4 default facet order per intent and map thorough checklist items to facets (R5). Cite the routing table without restating it.
  3. Add the R7 line to the Follow-up Options rule for free reports.
- **Patterns to follow:** the existing facet table and the treg ops card.
- **Test scenarios:**
  - Recommendations intent in balanced with an open "user ratings" gap and a known app id: `litescrape.app_store.reviews` runs, and Exa does not.
  - Price gap with no product id: Google Shopping runs, and Amazon does not run unless Shopping returned nothing.
  - Reviews gap with no business URL found by the free layer: no review endpoint is called, and the gap stays open with that reason.
  - Free run with a price gap: no treg paid call, and the R7 line appears.
- **Verification:** U1 tests green.

### U3. Eval traces and docs

- **Goal:** Traces and docs explain the new facets.
- **Requirements:** R9
- **Dependencies:** U2
- **Files:** `skills/free-research/references/eval-scenarios.md`, `README.md`, `FOR_Jan_FreeResearchSkill.md`, version files
- **Approach:**
  1. Add traces T37 (social), T38 (price), and T39 (reviews).
  2. Add one README paragraph listing facet types.
  3. Add a FOR_Jan section on why personal accounts were left out.
  4. Bump to 1.4.0 in lockstep.
- **Test scenarios:**
  - New trace ids each appear once.
  - Plugin lockstep test passes at 1.4.0.
- **Verification:** All tests green.

### U4. Live proof

- **Goal:** Each facet type works for real within caps.
- **Requirements:** R9
- **Dependencies:** U1-U3, installed with `scripts/install.sh`
- **Files:** none in the repo
- **Approach:**
  1. Check the balance.
  2. Run one `--balanced` run on an app-and-product topic, for example a popular note-taking app, in Claude Code (after restart) or in Grok under a timeout.
  3. Check that Tools Used shows one social, one price, and one review endpoint, with costs.
  4. Check the balance again.
- **Execution note:** Smoke verification over unit coverage.
- **Test scenarios:**
  - Test expectation: none -- manual smoke recorded in FOR_Jan.
- **Verification:** The report quotes real reviews, a price, and posts. Reported treg spend equals the balance change and stays at or under USD 0.05.

---

## Verification Contract

| Gate | Command | Applies to |
| --- | --- | --- |
| Contract and plugin tests | `python3 -m unittest discover -s tests` | U1-U3 |
| Install and parity | `scripts/install.sh` then `FREE_RESEARCH_CHECK_COPIES=1 python3 -m unittest discover -s tests` | U4 |
| Live balanced smoke | `/free-research <app or product topic> --balanced`, with treg `balance` before and after | U4 |

## Definition of Done

- R1-R9 each trace to a test or the recorded smoke.
- Free, balanced, deep, and thorough caps unchanged. Free mode still spends nothing.
- No per-result endpoint, no `my_tools`, no account route in the allowlist.
- Version 1.4.0 everywhere, and copies synced.

## Open Questions

### Deferred to Implementation

- Exact request params per endpoint (read once with `treg catalog get` into a temp file, never at run time).
- Whether `crawl4ai.app-store.app.detail` carries enough review text, or only the rating summary.
