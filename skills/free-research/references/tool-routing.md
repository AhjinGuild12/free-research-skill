# Free Research — Tool Routing

## Default path (free)

```
TOPIC
  → last30days (community pulse)
  → TinyFish search (3–5 angles)
  → TinyFish fetch_content (6–10 URLs)
  → synthesize
```

## Escalation path (balanced / deep only)

```
free layer complete
  → decision gate
  → if gaps: Exa (selective in balanced; broader in deep)
  → fetch new URLs with TinyFish (still free)
  → if still thin: Brave independent index
  → synthesize (+ Deep Insights section)
```

## Cost map

| Tool | Layer | Cost |
|------|--------|------|
| last30days engine | Community | Free (user's configured free sources) |
| TinyFish `search` | Discovery | Free |
| TinyFish `fetch_content` | Reading | Free (≤10 URLs/call) |
| TinyFish `run_web_automation` | Acting | **Paid — do not use for research reads** |
| Exa | Semantic discovery | Paid — balanced/deep only |
| Brave | Independent web index | Paid — last resort after Exa |
| Host `web_search` / `open_page` | Fallback | Free host tools; label honestly |

## Decision gate (quick)

Stay free when:

- Multiple high-quality recent sources answer the question
- Community + fetched pages agree on the main story
- User forced `--free`

Escalate when (and mode allows it):

- Technical multi-hop question with missing intermediate sources
- Free results are thin, off-topic, or outdated
- Competitor matrix missing a critical axis after free pass
- User asked `--deep` and free layer left clear holes

## Intent → emphasis

| Intent | last30days | TinyFish | Extra section |
|--------|------------|----------|---------------|
| general | normal topic | docs + news + practice | — |
| news | news-framed topic | primary announcements | Key Developments heavy |
| person | person preflight | bio, shipping, interviews | Community Sentiment heavy |
| competitor | comparison / peers | each product site + comparisons | **Comparison / Gaps** required |
| recommendations | recommendations framing | reviews + practitioner posts | ranked picks in Takeaways |

## Anti-patterns

- Calling Exa "just in case" on a free run
- Fetching one URL at a time with TinyFish (batch up to 10)
- Using automation tools to read static pages
- Dumping last30days raw evidence clusters into the free-research report
- Claiming a tool ran when a substitute was used
- Inventing citations not present in tool output
