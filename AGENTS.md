# AGENTS.md — ed-lore / The GalNet Chronicle

> This file describes the project structure, conventions, and operational details for AI coding agents. The reader is assumed to know nothing about the project.

---

## 1. Project Overview

This project is **"The GalNet Chronicle"** — an archive and knowledge system for *Elite: Dangerous* GalNet articles.

**Current state:** A local Python fetcher plus ~2,550 Markdown articles organized by in-game year.

**Intended future state (per `prompt.md`):**
1. An **Obsidian-compatible Markdown vault** with cross-linked entity profiles (`[[Wiki_Link]]` syntax), story arcs, and "modern relevance" annotations.
2. A **static website** (Astro or Next.js, SSG) with a diegetic "Elite HUD" visual theme, deployed to GitHub Pages.

The project has **no version control initialized** (no `.git` directory). There is **no build system, test suite, CI/CD, or package manager manifest** yet.

---

## 2. Technology Stack

| Layer | Technology |
|-------|------------|
| Fetcher | Python 3, `asyncio` |
| HTTP client | `httpx` (async) |
| Progress bars | `tqdm` (`tqdm.asyncio`) |
| Frontmatter | `pyyaml` |
| Data format | Markdown + YAML frontmatter |
| Planned SSG | Astro or Next.js (not yet chosen or implemented) |

**No `requirements.txt`, `pyproject.toml`, `package.json`, or similar manifest exists.** Dependencies must be installed manually (see §5).

---

## 3. Project Structure

```
ed-lore/
├── fetch.py          # Async article fetcher & normalizer (~180 lines)
├── prompt.md         # High-level product vision & feature spec
├── AGENTS.md         # This file
└── GalNet/           # Archive root — all articles as Markdown
    ├── 2015-3301/    # Real-year-Elite-year pairs
    ├── 2016-3302/
    ├── 2017-3303/
    ├── 2018-3304/
    ├── 2019-3305/
    ├── 2020-3306/
    ├── 2021-3307/
    ├── 2022-3308/
    ├── 2023-3309/
    ├── 2024-3310/
    ├── 2025-3311/
    └── 2026-3312/
```

**Folder naming convention:** `YYYY-EDED` where:
- `YYYY` = real-world calendar year
- `EDED` = Elite Dangerous in-game year (`YYYY + 1286`)

**File naming convention:** `EDED-MM-DD-<slug>.md`
- Example: `3310-01-04-empire_continues_protective_sanctuary_for_abductees.md`
- Slug is derived from the article title: lowercased, non-alphanumeric chars removed, spaces/hyphens collapsed to underscores.

---

## 4. Article Data Format

Every `.md` file has YAML frontmatter followed by a blank line and the article body.

```yaml
---
uuid: 023030b3-b87d-5220-9488-e82e00d7f4c4
title: Empire Continues 'Protective Sanctuary' for Abductees
slug: empire_continues_protective_sanctuary_for_abductees
ed_date: '3310-01-04'
lang: en
source: API
---

Emperor Arissa Lavigny-Duval has decided that all Imperial citizens recovered from Thargoid Titans will remain in quarantine indefinitely...
```

### Frontmatter fields

| Field | Description |
|-------|-------------|
| `uuid` | Deterministic UUIDv5 generated from `date + lowercase title`. Namespace is hard-coded in `fetch.py`. |
| `title` | Article headline (preserves original casing and punctuation). |
| `slug` | URL-safe slug used in the filename. |
| `ed_date` | In-game date string `EDED-MM-DD`. Quoted to force string type in YAML. |
| `lang` | Always `"en"` at present. |
| `source` | `"GitHub"` or `"API"` — indicates provenance. |

### Body characteristics

- **Plain text / minimal Markdown.** No images, no inline links, no headings (`#`), no blockquotes.
- Some older GitHub-sourced files retain an asterisk bullet prefix on the first line (e.g., `* Underground Racers Spotted...`) and an italicized date line (e.g., `/08 Feb 3301/`). These are artifacts of the upstream `.org` format.
- API-sourced bodies have HTML tags stripped by the fetcher.
- Average article length is ~39 lines.

### Source provenance

| Source | Count | Notes |
|--------|-------|-------|
| `GitHub` | ~1,696 | Scraped from `elitedangereuse/LoreExplorer` (`.org` files, years 3300–3306). |
| `API` | ~854 | Fetched from Frontier's JSON API (`cms.zaonce.net`). |
| **Total** | **~2,550** | Spanning in-game dates `3301-02-08` through `3312-04-28`. |

---

## 5. The Fetch Script (`fetch.py`)

### What it does
`fetch.py` is a **destructive-sync** script. It re-downloads and overwrites articles every run.

1. **GitHub Phase** — Lists `.org` files in `elitedangereuse/LoreExplorer/references/Galnet/<year_ed>/` for years 3300–3306. Extracts title from `#+TITLE:` metadata or falls back to filename. Strips all `#+` metadata lines to produce the body.
2. **API Phase** — Paginates Frontier's JSON API (`sort=-published_at`, 50 per page). Strips HTML tags from `body.value`.
3. **Write Phase** — Generates deterministic UUID, assembles YAML frontmatter, writes to `GalNet/<folder>/<file>.md`.

### Key constants

```python
BASE_DIR = "GalNet"
ED_YEAR_OFFSET = 1286          # Real year -> Elite year
MAX_PARALLEL_TASKS = 15        # Semaphore limit
RETRIES = 3                    # Per-request retries
```

### Running the fetcher

```bash
python fetch.py
```

**Prerequisites:** Python 3 with `pyyaml`, `httpx`, and `tqdm` installed.

```bash
pip install pyyaml httpx tqdm
```

**Important:** The script is idempotent in terms of output paths and UUIDs (same input → same filename + same UUID), but it **rewrites every file on every run**. Do not run it while another process is reading the archive unless you can tolerate brief inconsistency.

---

## 6. Dependencies & Environment

There is **no virtual environment, lockfile, or dependency manifest** in the repo. Before modifying or running code, ensure the following are available:

- `python` ≥ 3.10 (uses `asyncio.to_thread`)
- `pyyaml`
- `httpx`
- `tqdm`

If you introduce a package manager (e.g., `requirements.txt`, `pyproject.toml`, or `package.json` for the frontend), update this file accordingly.

---

## 7. Development Conventions

- **Comments in `fetch.py` are in German** (e.g., `"Erzeugt einen sauberen URL-konformen Namen"`, `"Fehler beim Schreiben"`). New code should use **English** comments to match `prompt.md` and the article content.
- **No tests exist.** Any new modules (parsers, entity extractors, site generators) should include their own tests.
- **No linting or type-checking is configured.** Consider adding `ruff` / `mypy` if the Python surface grows.
- **No Git history.** If you initialize `git`, add `__pycache__/`, `.venv/`, `node_modules/`, and any build outputs to `.gitignore`.

---

## 8. Planned Architecture (from `prompt.md`)

The product vision document (`prompt.md`) describes two major deliverables not yet built:

### Phase 1 — Digital Archive (Obsidian Vault)
- New directory `/Archive/YYYY/MM/DD_Title.md` (redundant re-organization of `GalNet/`).
- Enhanced YAML frontmatter with `entities`, `arc_id`, and `modern_impact`.
- Wiki-style internal links (`[[Entity Name]]`).
- Auto-generated entity profiles in `/Entities/`.

### Phase 2 — Time-Machine Website
- Static site generator (Astro or Next.js).
- Dual-pane layout: chronological article list (left) + contextual entity cards (right).
- "Spoiler control" — context reflects only knowledge available up to the scrolled date.
- Global search ("Command Console") filtering by system, character, or keyword.
- `lore_graph.json` as the website's data source.

### Maintenance Loop
1. Run `python fetch.py` to ingest new articles.
2. Detect new files.
3. Extract entities, update `lore_graph.json`, generate entity profiles.
4. Rebuild and redeploy the static site.

> **Agent note:** These phases are aspirational. Do not assume any of this infrastructure exists. Verify filesystem state before acting on it.

---

## 9. Security Considerations

- `fetch.py` makes outbound HTTPS requests to `cms.zaonce.net` and `api.github.com`. It does not send any auth tokens.
- GitHub API unauthenticated rate limits apply (60 requests/hour per IP). The script only hits the repo contents API ~7 times, but if you expand it, you may hit the limit.
- The deterministic UUID uses a **hard-coded namespace** (`12345678-1234-5678-1234-567812345678`). This is fine for local stability but is not a cryptographically secure secret.
- There is **no input sanitization on filenames beyond `slugify`**. The slug strips most non-alphanumeric characters, but ensure `os.makedirs` targets remain under `BASE_DIR` if you modify path logic.

---

## 10. Quick Reference

| Task | Command |
|------|---------|
| Install Python deps | `pip install pyyaml httpx tqdm` |
| Fetch / refresh archive | `python fetch.py` |
| Count articles | `find GalNet -type f \| wc -l` |
| List all unique sources | `grep -r "^source:" GalNet/ \| sed 's/.*source: //' \| sort \| uniq -c` |
| Find article by date | `ls GalNet/YYYY-EDED/EDED-MM-DD-*.md` |
| Read article | `cat GalNet/<folder>/<file>.md` |
| Push to GitHub | `git push origin main` (via `gh` auth) |

---

## 11. Git & GitHub

The `gh` CLI is authenticated for user **KernicDE** (`github.com`). Git operations to `https://github.com/KernicDE/ed-lore.git` work via `gh auth setup-git` + HTTPS. Do not rely on SSH keys being present; use `gh` credential helper instead.

---

*Last updated: 2026-04-30*
