# CLAUDE.md — GalNet Chronicle Project Context

> This file provides high-level project context for Claude and other AI assistants.
> It complements AGENTS.md (which covers technical details) with strategic context.

---

## Project Mission

**The GalNet Chronicle** is a comprehensive, AI-enriched archive of all Elite Dangerous GalNet articles (3301–3312+).

Goals:
- Preserve every GalNet article with structured metadata
- Map all entities (persons, factions, locations, technologies) and their relationships
- Trace story arcs across the timeline
- Make the lore searchable, browsable, and explorable
- Provide audio versions of articles for accessibility

Live site: https://kernicde.github.io/ed-lore/

---

## Current Status (as of 2026-05-01)

### Data Completeness

| Metric | Count | Status |
|--------|-------|--------|
| Articles | 2,543 | 100% archived |
| Articles with summary | 2,543 | 100% enriched |
| Articles with player_impact | 2,543 | 100% enriched |
| Articles with related_uuids | 2,543 | 100% linked |
| Entity profiles | 3,447 | 100% have auto-generated bios |
| Arc profiles | 30 | 100% have descriptions |
| Locations with EDSM coords | ~769 | ~55% of star systems mapped |

### Features Deployed

- ✅ Interactive timeline (newest-first, year slider, article expansion)
- ✅ Entity profile pages (bios, related entities, mention timeline, EDSM data)
- ✅ Arc profile pages (descriptions, key figures, chronology)
- ✅ Context panel (dynamic related arcs + top entities based on viewport)
- ✅ Search modal (Cmd+K, article/entity/arc search)
- ✅ Audio player (mini-player for article TTS, en-GB-SoniaNeural voice)
- ✅ Daily audio generation cron (500 articles/night, newest first)

### Audio Generation Pipeline

- **Local**: `python scripts/generate_audio.py --sort recent --concurrency 8`
- **CI**: `.github/workflows/audio-generation.yml` runs daily at midnight UTC
- **Batch size**: 500 articles/day
- **Voice**: `en-GB-SoniaNeural`
- **Structure**: "Title on date" → body → "AI analysis: Arc. Player impact. Future impact."
- **Manifest**: `scripts/audio_manifest.json` tracks which articles have audio

### Known Limitations

1. **Audio coverage**: ~135/2,543 articles have audio (batch in progress, 500/day)
2. **Entity bios**: Auto-generated from article summaries — functional but repetitive
3. **EDSM coverage**: 644 locations unmatched (mostly stations, nebulae, planets — not star systems)
4. **Bio quality**: Top 1,000 entities have the best bios; remaining 2,400+ are template-based

---

## Architecture Decisions

### Why Astro + React?
- Astro for static site generation (3,400+ pages)
- React for interactive components (timeline, search, audio player)
- Split JSON loading: `galnet-meta.json` (async) + `galnet-bodies.json` (lazy)

### Why Markdown + YAML frontmatter?
- Human-readable and editable
- Git-friendly (diffable)
- Easy to extend with new fields
- Frontmatter parsed at build time

### Why edge-tts?
- Free, no API key needed
- High quality neural voices
- `en-GB-SoniaNeural` matches the British sci-fi aesthetic of Elite Dangerous
- Incremental generation via hash manifest

### Why GitHub Pages?
- Free hosting for static sites
- Custom domain support
- GitHub Actions integration for CI/CD

---

## Workflow Philosophy

### Enrichment over extraction
We don't just archive raw text — we add structured metadata (entities, arcs, impacts) that makes the lore explorable.

### Incremental everything
- Audio: 500 files/day batches
- Entity bios: generated automatically from article analysis
- Deploy: triggered on every push to main

### Human-in-the-loop for quality
- Auto-generation for scale (bios, audio)
- Manual review for important content (arc descriptions, key entity bios)
- Validation scripts catch common errors

---

## File Reference

| File | Purpose |
|------|---------|
| `fetch.py` | Download new articles from Frontier API + GitHub |
| `scripts/build_graph.py` | Build `lore_graph.json` + split async JSON |
| `scripts/generate_audio.py` | TTS audio generation with incremental skip |
| `scripts/generate_entity_bios.py` | Auto-generate entity bios from articles |
| `scripts/validate_enrichment.py` | Check article frontmatter for errors |
| `scripts/format_articles.py` | Idempotent formatting pass |
| `scripts/populate_related_uuids.py` | Add related article links |
| `scripts/enrich_locations_from_edsm.py` | Query EDSM API for system coords |
| `DAILY_PROMPT.md` | Copy-paste prompt for daily automation |
| `AGENTS.md` | Technical conventions and operational details |

---

## When to Run What

| Trigger | Action |
|---------|--------|
| New GalNet season announced | Run `fetch.py` immediately, then enrichment |
| Daily / every few days | Run DAILY_PROMPT.md workflow |
| After enrichment edits | `python scripts/build_graph.py && cd website && pnpm build` |
| Before committing | `python scripts/validate_enrichment.py` |
| Audio batch needed | `python scripts/generate_audio.py --batch-size 500 --sort recent` |
| Format cleanup | `python scripts/format_articles.py` |

---

*Last updated: 2026-05-01*
