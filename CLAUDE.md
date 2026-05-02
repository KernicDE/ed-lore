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

## Current Status (as of 2026-05-02)

### Data Completeness

| Metric | Count | Status |
|--------|-------|--------|
| Articles | **2,551** | 100% archived |
| Articles with summary | 2,551 | 100% enriched |
| Articles with player_impact | 2,551 | 100% enriched |
| Entity profiles | **3,484** | 100% have bios |
| Arc profiles | 30 | 100% have descriptions |
| Audio coverage | **2,551** | **100%** — hosted on Cloudflare R2 |

### Features Deployed

- ✅ Interactive timeline (newest-first, year slider, article expansion)
- ✅ Entity profile pages (bios, related entities, mention timeline)
- ✅ Arc profile pages (descriptions, key figures, chronology)
- ✅ Context panel (dynamic related arcs + top entities based on viewport)
- ✅ Search modal (Cmd+K, article/entity/arc search)
- ✅ Audio player (mini-player loading from Cloudflare R2, en-GB-SoniaNeural voice)
- ✅ Cache-busted JSON loading (`?v=<build-timestamp>`)
- ✅ Dynamic article count in header (from `version.json`)
- ✅ Self-healing audio pipeline (hourly generation + R2 upload)

### Audio Pipeline

- **Hosting**: Cloudflare R2 (`ed-lore-audio` bucket)
- **Public URL**: `https://pub-4404b20907c141e1b68f3dc578038230.r2.dev/audio/{uuid}.mp3`
- **Generation**: GitHub Actions `audio-generation` workflow (hourly + manual trigger)
- **Voice**: `en-GB-SoniaNeural`
- **Deduplication**: MD5/etag comparison prevents re-uploading unchanged files
- **Full rebuild**: Manual trigger with `full_rebuild` checkbox (~2–3 hours)

### Known Limitations

1. **Entity bios**: Auto-generated from article summaries — functional but repetitive for lesser-known entities
2. **EDSM coverage**: Many stations, nebulae, planets are not in EDSM (only star systems are reliably mapped)
3. **R2 dependency**: Audio requires Cloudflare R2 bucket to be accessible; if R2 is down, audio fails gracefully with "Audio not available"

---

## Architecture Decisions

### Why Astro + React?
- Astro for static site generation (~3,477 pages)
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
- Incremental generation via text hash manifest

### Why Cloudflare R2 for audio?
- 10 GB free tier (1.44 GB used)
- Zero egress fees (critical for a public website)
- S3-compatible API
- Decouples audio from GitHub Pages deploy artifact (shrinks artifact from 1.5 GB to ~50 MB)

### Why GitHub Pages?
- Free hosting for static sites
- GitHub Actions integration for CI/CD
- Automatic deploy on every push to `main`

---

## Security & Secrets

**API keys, tokens, and passwords must NEVER be committed to this repository or shown in any code/output.**
- No `.env` files, no hardcoded keys in scripts, no secrets in workflow files
- The repo is public on GitHub — treat everything as publicly visible
- Cloudflare R2 token is stored in GitHub Secrets (`CLOUDFLARE_R2_TOKEN`)
- If an external API requires a key, it must be passed via environment variables at runtime
- `.gitignore` blocks `.env*`, `*.key`, `secrets/`, `website/public/audio/`, and generated JSONs

---

## Workflow Philosophy

### Enrichment over extraction
We don't just archive raw text — we add structured metadata (entities, arcs, impacts) that makes the lore explorable.

### Incremental everything
- Audio: hourly generation with hash-based skip + R2 deduplication
- Entity bios: generated automatically from article analysis
- Deploy: triggered on every push to main

### Human-in-the-loop for quality
- Auto-generation for scale (bios, audio)
- Manual review for important content (arc descriptions, key entity bios, new articles)
- Validation scripts catch common errors

---

## File Reference

| File | Purpose |
|------|---------|
| `scripts/fetch.py` | Download new articles from Frontier API |
| `scripts/build_graph.py` | Build `lore_graph.json` + split client JSONs + `version.json` |
| `scripts/generate_audio.py` | TTS audio generation with incremental skip |
| `scripts/sync_audio_to_r2.py` | Upload MP3s to Cloudflare R2 with MD5/etag dedup |
| `scripts/enrich.py` | Bulk enrichment (initial import only) |
| `scripts/validate_enrichment.py` | Check article frontmatter for errors |
| `scripts/audit_api_vs_archive.py` | Compare API with local archive |
| `scripts/audit_arcs_and_uuids.py` | Check arc consistency |
| `.kimi/prompts/fetch-enrich-deploy.md` | Step-by-step guide for importing & enriching new articles |
| `AGENTS.md` | Technical conventions and operational details |

---

## When to Run What

| Trigger | Action |
|---------|--------|
| New GalNet season announced | Run `scripts/fetch.py`, then manual enrichment per `.kimi/prompts/fetch-enrich-deploy.md` |
| After enrichment edits | `python scripts/build_graph.py && cd website && pnpm build` |
| Before committing | `python scripts/validate_enrichment.py` |
| Audio missing / corrupted | GitHub Actions → Audio Generation → Run workflow → ✅ full_rebuild |
| Format cleanup | Manual editing (format_articles.py was removed) |

---

*Last updated: 2026-05-02*
