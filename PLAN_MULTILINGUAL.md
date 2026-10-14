# PLAN — Multilingual Site (German)

> Goal: Make The GalNet Chronicle fully multilingual — UI/UX first, then content
> (articles incl. bodies, arcs, entities, AI analyses) with gradual translations and
> English fallback. German TTS audio is part of the plan. English remains the canonical
> source language.

## Current State (facts from code exploration)

- Astro 6.2 static site, `base: '/ed-lore'`, **no i18n config, no router, no state library**
- Article reading is **client-side only** (`/?article=<uuid>`, rendered from JSON)
- Static pages: `/entity/[id]/` (~3,349), `/arc/[id]/` (38), `/map/`, `/logs/`, `/chronicles/` + 4 feeds
- UI chrome: **~100–120 hardcoded English strings** (~40 in React components, ~60–80 in Astro pages/layout — ~40 of those on the entity page alone)
- Data pipeline: `scripts/build_graph.py` → `galnet-meta.json` (articles+entities+arcs), `galnet-bodies.json`, `search-index.json`, `entities-index.json`, `graph-data.json`, `version.json`
- Content: 2,618 articles (EN bodies), 3,349 entities (EN bios), 38 arcs (EN) — all canonical in `Archive/*.md` + `Entities/**/*.md` frontmatter
- Feeds declare `<language>en</language>` / `xml:lang="en"`
- Audio TTS: `en-GB-SoniaNeural` (GitHub Actions → R2)

## Key Decisions (proposed — confirm before Phase 1)

1. **English stays canonical + default.** German is additive; every German view falls back to English per-field when no translation exists.
2. **URL strategy: locale sub-paths.** `/de/entity/[id]/`, `/de/arc/[id]/` generated alongside English pages (Astro `getStaticPaths` with a `lang` param). Home/map/logs/chronicles get `/de/` variants with translated chrome. Feeds stay English-only for now.
3. **Content translations live in the same frontmatter** as the canonical text (`*_de` fields), so translations travel with the source and are edited/validated in the same files.
4. **No new heavy dependencies.** A small dictionary module + React context beats an i18n framework at this scale. Astro pages import the same dictionary in frontmatter.

---

## Phase 1 — UI/UX i18n Infrastructure

**Goal: every button, label, panel title, badge, placeholder in DE + EN.**

1. `website/src/i18n/dict.ts` — typed dictionary:
   ```ts
   export const dict = {
     en: { search: 'Search', ... },
     de: { search: 'Suche', ... },
   }
   export type Lang = 'en' | 'de'
   export function t(lang: Lang, key: string): string
   ```
2. `website/src/i18n/LanguageContext.tsx` — React context, persists `galnet-lang` in localStorage (same pattern as `galnet-theme`), sets `<html lang>`, exposes `lang` + `setLang`.
3. `LanguageToggle.astro` component in the HUD header (next to theme/AI toggles).
4. Migrate ~40 React strings to `t()` — AppShell, Timeline, ContextPanel, CommandConsole, AudioPlayer, SearchIsland, EntityGraph.
5. Migrate ~60–80 Astro strings: `BaseLayout.astro` (title/description slots, `lang` attr), `index.astro`, `entity/[id].astro` (`typeLabels` map + ~40 field labels), `arc/[id].astro` (panel titles), `map.astro`, `logs.astro`, `chronicles.astro`.
6. Static pages: add `lang` param to `getStaticPaths()` in `entity/[id].astro` + `arc/[id].astro`; render `/de/...` variants with DE chrome. Language switcher links to the same page in the other locale.
7. `<html lang>` correct per page; feeds: switch `<language>` dynamically later if feed translation is ever wanted (skip for now).

**Acceptance:** `pnpm build` produces EN + DE pages; switching language in the header persists and translates all chrome; untranslated content still shows EN.

## Phase 2 — Translation Data Format (pipeline)

**Goal: a defined, validated place for content translations.**

1. **Article frontmatter** (add gradually):
   ```yaml
   summary_de: "..."
   player_impact_de: "..."
   modern_impact_de: "..."
   ```
   Body translation (optional, later): `body_de:` — see Phase 4.
2. **Entity files**: `bio_de:` (YAML, same length cap as EN) — optional `## Biography (DE)`? No: single `bio_de` field, rendered via the same markdown path (`marked.parse`) as `bio_full`.
3. **Arc files**: `description_de`, `summary_de`, `outcome_de`; `phases_de` optional.
4. `scripts/build_graph.py`:
   - Collect `*_de` fields alongside EN fields (same merge lists, `*_de` keys).
   - Entities: extract `bio_de` from frontmatter → `bio_full_de`.
   - Emit `website/public/data/translations-de.json`:
     ```json
     { "articles": { "<uuid>": {"summary_de": "...", "player_impact_de": "...", "modern_impact_de": "..."} },
       "entities": { "<id>": {"bio_de": "..."} },
       "arcs":     { "<id>": {"description_de": "...", "summary_de": "...", "outcome_de": "..."} } }
     ```
     Only items that HAVE a translation — small file, lazy-loaded when `lang=de`.
   - `version.json`: add `translated: { articles: n, entities: n, arcs: n }` for progress visibility.
5. `scripts/validate_enrichment.py`: YAML-parse check already covers the new fields implicitly; add soft stat output (translation coverage %) — no hard failures.

**Acceptance:** adding a `*_de` field to any article/entity/arc surfaces it in `translations-de.json` after build.

## Phase 3 — Frontend Content Switch

**Goal: German users see translated summaries/impacts/bios with EN fallback.**

1. `AppShell` loads `translations-de.json` when `lang=de` (small, one fetch; cache-busted by `?v=` like the others).
2. **Timeline article view**: prefer `summary_de` / `player_impact_de` / `modern_impact_de`, fall back per-field to EN. Optional subtle badge "DE ✓" on articles with full translation (nice-to-have).
3. **Entity/arc static pages**: `/de/entity/[id]/` renders `bio_full_de ?? bio_full`, `/de/arc/[id]/` renders the DE frontmatter fields. Requires the DE pages to be generated with lang-aware rendering (Phase 1 already splits routes; here the *content* becomes lang-aware via `lore_graph.json`, which carries `bio_full_de` after Phase 2).
4. **Search (v1: unchanged)** — titles/names stay EN; translated summaries enter the index in Phase 4.
5. ContextPanel/SearchIsland labels already translated in Phase 1.

**Acceptance:** a fully translated article/entity/arc shows 100% German in DE mode; a partially translated one mixes DE/EN gracefully with no broken layout.

## Phase 4 — Gradual Content Translation Workflow

**Goal: sustainable process for adding translations over time (user-driven).**

1. **During enrichment** (`.kimi/prompts/fetch-enrich-deploy.md`): add `*_de` fields alongside the EN ones for every newly enriched article. AI-assisted, human-reviewed. Same for new entities/arcs (`bio_de`, `summary_de`...).
2. **Backlog sweep (optional, batched)**: translate high-traffic arcs/entities first (e.g. arc key entities), then chronologically. Batch jobs must follow the same frontmatter convention; validate with `validate_enrichment.py`.
3. **Body translations (`body_de`)** — planned, after Phases 1–3 are stable:
   - Storage: `body_de` in article frontmatter → `galnet-bodies-de.json` (lazy-loaded, same shape as EN bodies map).
   - Process: AI-translate in small batches (e.g. 50–100 articles per run), write `body_de` into frontmatter, rebuild. Frontmatter files grow (~+1.5–2×), which is acceptable.
   - Bodies are the bulk of the work (2,618 × ~300 words) but are required for the "completely German" goal; summaries/impacts/bios (steps 1–2) come first because they deliver the most visible value per effort.
4. **Search translation**: once body/summary coverage is significant, emit `search-index-de.json` (translated titles + summaries) and let fuse.js search the active language's index.

## Phase 5 — German TTS Audio

**Goal: DE-mode articles get German voice audio.**

1. Voice: an `edge-tts` German neural voice (e.g. `de-DE-KatjaNeural` or `de-DE-ConradNeural`) — switch in `scripts/generate_audio.py` based on a language parameter.
2. R2 layout: language-prefixed paths — `audio/de/{uuid}.mp3` alongside `audio/{uuid}.mp3` (EN unchanged; no invalidation of existing cache).
3. `scripts/audio_manifest.json`: extend to `{uuid: {en: hash, de: hash}}` (or a parallel `audio_manifest_de.json` to stay backward-compatible — decide at implementation; parallel file is lower-risk).
4. `build_graph.py`: mark `has_audio_de` on articles; AudioPlayer picks the URL by active `lang` (EN fallback when DE audio missing — which is the norm during the gradual rollout).
5. GitHub Actions `audio-generation` workflow: generate DE audio only for articles that have `body_de` and lack a DE MP3; hourly self-healing pattern unchanged.
6. Rollout: DE audio appears automatically as `body_de` coverage grows — zero manual steps after setup.

## Phase 6 — Optional Extras (later)

- Feed localization (`/de/rss.xml`, `<language>de</language>`).
- hreflang link tags between EN/DE page variants.
- Third+ language later (dictionary + pipeline are lang-agnostic by then).

## Effort Estimate

| Phase | Scope | Rough size |
|-------|-------|-----------|
| 1 | i18n infra + ~120 strings | ~1–2 days |
| 2 | pipeline `*_de` fields + JSON | ~0.5 day |
| 3 | frontend switch + DE routes content | ~1 day |
| 4 | summaries/impacts/bios ongoing (user-paced); `body_de` batches | continuous + bulk translation runs |
| 5 | German TTS (workflow + manifest + player) | ~0.5–1 day setup, then self-healing |
| 6 | optional extras | on demand |

## Risks / Notes

- **Build size**: +3,349 entity pages + 38 arc pages (DE variants) — HTML only, deploy grows ~2× pages but stays small vs. the 50 MB budget.
- **Cache busting**: `translations-de.json` / `galnet-bodies-de.json` need the `?v=` treatment (reuse `window.GALNET_BUILD`).
- **Keep EN canonical**: never edit EN text via DE fields; DE is derived, not source of truth.
- **Style guide**: `bio_de` obeys the same ≤47-line cap as EN profiles.
- **TTS cost**: ~2,600 German TTS runs — within free tiers; R2 storage doubles (~2× audio objects), still far below the 10 GB free tier.
- **Manifest migration** (Phase 5): parallel `audio_manifest_de.json` is the low-risk option; the audio workflow's MD5/etag dedup logic applies per language independently.
