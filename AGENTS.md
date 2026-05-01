# AGENTS.md — ed-lore / The GalNet Chronicle

> This file describes the project structure, conventions, and operational details for AI coding agents working on this repository.

---

## 1. Project Overview

This project is **"The GalNet Chronicle"** — an archive and knowledge system for *Elite: Dangerous* GalNet articles.

**Current state:**
- 2,543 Markdown articles in `Archive/YYYY/MM/DD_slug.md` (in-game year/month/day)
- Entity profiles in `Entities/` (persons, factions, arcs, technologies, locations)
- Static website built with **Astro 6.2 + React 19**, deployed to **GitHub Pages**
- Data pipeline: `scripts/build_graph.py` → `lore_graph.json` + split async JSON → website

**Output:** ~3,264 static pages (articles, entities, arcs, timeline) deployed to `https://kernicde.github.io/ed-lore/`

---

## 2. Technology Stack

| Layer | Technology |
|-------|------------|
| Fetcher | Python 3, `asyncio` |
| HTTP client | `httpx` (async) |
| Frontmatter | `pyyaml` |
| Data format | Markdown + YAML frontmatter |
| Build pipeline | `scripts/build_graph.py` → `lore_graph.json` |
| SSG | Astro 6.2 + React 19 |
| Package manager | `pnpm` |
| Deployment | GitHub Actions → GitHub Pages |

Python dependencies: `pyyaml`, `httpx`, `tqdm`

---

## 3. Project Structure

```
ed-lore/
├── fetch.py                   # Async article fetcher & normalizer
├── lore_graph.json            # Built data file (auto-generated)
├── prompt.md                  # High-level product vision
├── AGENTS.md                  # This file
├── scripts/
│   ├── build_graph.py         # Builds lore_graph.json + split async JSON
│   ├── format_articles.py     # Idempotent formatting pass for all Archive/*.md
│   └── validate_enrichment.py # Validates article frontmatter
├── Archive/                   # Canonical article archive (YYYY/MM/DD_slug.md)
│   ├── 3301/02/08_....md
│   ├── 3307/08/02_....md
│   └── ... 3301–3312
├── Entities/                  # Auto-generated + hand-curated entity profiles
│   ├── Arcs/
│   ├── faction/
│   ├── person/
│   ├── technology/
│   └── location/
└── website/                   # Astro 6.2 static site
    ├── src/
    │   └── data/
    │       └── lore_graph.json   # MUST copy root lore_graph.json here before build
    ├── public/
    │   └── data/
    │       ├── galnet-meta.json  # Articles (no body_full) + entities + arcs — loaded async
    │       └── galnet-bodies.json # {uuid: body_full} — loaded lazily on first expand
    ├── astro.config.mjs
    └── package.json
```

**Article path convention:** `Archive/<YYYY>/<MM>/<DD>_<slug>.md`
- `YYYY` = in-game year (e.g. `3307`)
- `MM` = month (zero-padded)
- `DD` = day (zero-padded)
- `slug` = lowercased, underscores, no special chars

---

## 4. Article Data Format

Every article has YAML frontmatter followed by a blank line and the article body.

### Core fields (always present)

| Field | Description |
|-------|-------------|
| `uuid` | Deterministic UUIDv5 from `date + lowercase title` |
| `title` | Original headline |
| `slug` | URL-safe slug |
| `date` | In-game date `YYYY-MM-DD` (quoted string) |
| `source` | `"GitHub"` or `"API"` |

### Enrichment fields (added manually)

| Field | Description |
|-------|-------------|
| `summary` | 1–3 sentence summary of the article's content |
| `player_impact` | What pilots could do / did in this event |
| `persons` | List of named individuals (canonical full names) |
| `groups` | List of factions, corporations, political bodies |
| `locations` | List of star systems or significant places |
| `technologies` | List of named ships, weapons, gadgets |
| `topics` | Tags like `terrorism`, `diplomacy`, `corporate expansion` |
| `arc_id` | Single story-arc identifier (or omitted) |
| `related_uuids` | List of related article UUIDs |
| `modern_impact` | Why this still matters today |
| `legacy_weight` | 1–5 scale of long-term importance |
| `significance` | `low` / `medium` / `high` |

### Banned topics (remove unless explicitly legitimate)

`ship`, `sport`, `trade`, `construction`, `medicine`, `safety`, `treasure hunt`

Legitimate exceptions exist (e.g. `medicine` for Titan quarantine articles).

### Body characteristics

- Plain text / minimal Markdown
- No images, no inline links, no headings, no blockquotes
- Older GitHub-sourced files may have `*` bullet prefixes
- API-sourced bodies have HTML stripped

---

## 5. The Fetch Script (`fetch.py`)

**WARNING:** `fetch.py` is a **destructive-sync** script. It re-downloads and overwrites articles every run.

1. **GitHub Phase** — Scrapes `elitedangereuse/LoreExplorer` (`.org` files, years 3300–3306)
2. **API Phase** — Paginates Frontier's JSON API (`cms.zaonce.net`)
3. **Write Phase** — Writes to `Archive/YYYY/MM/DD_slug.md`

**DO NOT RUN** while enriching or editing articles, as it will overwrite your work.

---

## 6. Build Pipeline

### Step 1: Build the graph

```bash
python scripts/build_graph.py
```

Reads all articles in `Archive/` and entity files in `Entities/`, then writes:
- `lore_graph.json` — full graph (used by entity/arc static pages)
- `website/public/data/galnet-meta.json` — articles without `body_full` + entities + arcs (~6.7MB, loaded async by the timeline)
- `website/public/data/galnet-bodies.json` — `{uuid: body_full}` map (~3.1MB, loaded lazily on first article expand)

**Critical:** The script handles `None`/null values in list fields safely:
```python
for g in fm.get("groups") or []:
```

### Step 2: Copy to website (for entity/arc pages only)

```bash
cp lore_graph.json website/src/data/lore_graph.json
```

Only needed for entity/arc static page generation. The main index.astro no longer imports it — it fetches `galnet-meta.json` async at runtime.

### Step 3: Build

```bash
cd website && pnpm build
```

Output goes to `website/dist/`. The `public/data/*.json` files are automatically included.

### Step 4: Deploy

**CRITICAL:** Deployment is handled by the GitHub Actions workflow `.github/workflows/deploy.yml`. It triggers **only on pushes to `main`**.

The `git subtree push --prefix website/dist origin gh-pages` approach is **legacy and inactive**. Pushing to the `gh-pages` branch does **not** trigger a deployment.

**Correct deployment flow:**
1. Make your changes (enrich articles, fix bugs, etc.)
2. Build locally: `python scripts/build_graph.py && cd website && pnpm build`
3. Commit everything (including `website/dist/` changes if you want them tracked, though the CI rebuilds from scratch)
4. Push to `main`: `git push origin main`
5. The GitHub Actions workflow will rebuild and deploy to GitHub Pages automatically

Monitor deployment status at: https://github.com/KernicDE/ed-lore/actions

### Formatting pass (optional, idempotent)

```bash
python scripts/format_articles.py           # full run
python scripts/format_articles.py --dry-run  # preview only
python scripts/format_articles.py --sample 5 # test on 5 files
```

Normalizes YAML key order, strips duplicate titles, collapses blank lines, normalizes `*italic*` → `**bold**`. Safe to re-run any time. See `project_formatting.md` in Claude memory for details and known broken files.

---

## 7. Validation

```bash
python scripts/validate_enrichment.py
```

Checks:
- Required fields present (`summary`, `player_impact`)
- No duplicate persons/groups
- No banned topics
- No bad locations (sentence fragments)
- YAML parseable
- Arc consistency (warns for large arcs with empty `related_uuids`)

---

## 8. Article Enrichment Workflow

Articles dated before 3309 require manual enrichment. Start with the most recent unenriched files and work backwards.

### Rules
- **Read every file fully** before editing. No Python scripts, no batch processing, no guessing, no hallucination.
- **Skip already-enriched files** (those with `summary` and `player_impact` fields).
- Add fields: `summary`, `player_impact`, `persons`, `groups`, `locations`, `technologies`, `related_uuids` where appropriate.
- **Clean garbage auto-extraction:**
  - Remove `entities:` field entirely.
  - Remove sentence-fragment locations like `"With the"`, `"Our endeavour in"`.
  - Never put `"Thargoid"` as a location.
  - Deduplicate groups (e.g. `"Sirius Corp"` → `"Sirius Corporation"`).
  - Do **not** use `ACT` as an entity — it is a procedural taskforce, not a narrative entity.
- Fix `modern_impact` when it is clearly wrong.
- Use `ReadFile` to inspect each file, then `StrReplaceFile` with exact old text.
- Validate YAML after edits with `python scripts/validate_enrichment.py`.

### Deployment cadence

Deploy after every ~50 enriched files by committing and pushing `main`.

---

## 9. Entity Files

Entity profiles live in `Entities/` and are auto-generated stubs plus hand-curated enrichment.

**Auto-generated stubs** have this format:
```yaml
---
id: person-name
name: Person Name
type: person
first_seen_date: '3307-08-16'
last_seen_date: '3307-08-26'
mention_count: 3
---

<!-- AUTO-GENERATED -->
```

When new persons or groups are introduced in articles, the build script may create stubs. These can be enriched later with biographical details.

---

## 10. Git & GitHub

- Repository: `https://github.com/KernicDE/ed-lore.git`
- Branch: `main`
- The `gh` CLI is authenticated for user **KernicDE**
- GitHub Actions auto-deploys the website on every push to `main` via `.github/workflows/deploy.yml`
- **Do not use** `git subtree push` to `gh-pages` — it is legacy and does not trigger deployments
- The CI pipeline rebuilds the site from scratch (runs `build_graph.py`, `pnpm install`, `pnpm build`, then `deploy-pages`)
- Always verify deployment succeeded at https://github.com/KernicDE/ed-lore/deployments

---

## 11. Quick Reference

| Task | Command |
|------|---------|
| Install Python deps | `pip install pyyaml httpx tqdm` |
| Fetch / refresh archive | `python fetch.py` *(destructive)* |
| Validate enrichment | `python scripts/validate_enrichment.py` |
| Build graph + split JSON | `python scripts/build_graph.py` |
| Copy graph to website | `cp lore_graph.json website/src/data/lore_graph.json` |
| Format archive articles | `python scripts/format_articles.py` |
| Build website | `cd website && pnpm build` |
| Count articles | `find Archive -type f \| wc -l` |
| Push to GitHub (triggers deploy) | `git push origin main` |
| Check deployment status | https://github.com/KernicDE/ed-lore/actions |

---

*Last updated: 2026-05-01*
