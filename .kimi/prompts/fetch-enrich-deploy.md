# Fetch, Enrich & Deploy New Articles

## Goal
Import new GalNet articles from the official API, manually enrich them with metadata (summary, entities, topics, impacts), discover/update entities, generate audio, and deploy the updated site.

## Prerequisites
- Node.js 22 + pnpm 10
- Python 3.12+ with pyyaml, requests
- Working directory: `/home/kernic/Development/ed-lore`

## Step-by-Step Process

### 1. Fetch New Articles
```bash
cd /home/kernic/Development/ed-lore
python3 scripts/fetch.py
```
This pulls new articles from the Frontier GalNet API into `GalNet/` organized by year.

### 2. Verify Fetched Articles
```bash
# See what was fetched
find GalNet/ -name "*.md" -newer Archive/ -type f 2>/dev/null | head -20
# Or check the most recent files by date
ls -lt Archive/ | head -20
```

### 3. Manually Enrich Each New Article
For every newly fetched article, open the Markdown file and add complete frontmatter:

```yaml
---
uuid: "..."
title: "..."
date: "330X-XX-XX"
source_url: "..."
authors:
  - "..."
topics:
  - "..."
entities:
  - name: "..."
    type: "person|faction|location|organization|technology"
    role: "primary|secondary|mentioned"
locations:
  - "..."
arc_id: "..."          # if part of an existing arc; omit if standalone
player_impact: "..."
modern_impact: "..."
summary: "One-paragraph summary of the article."
---
```

**Enrichment rules:**
- Use existing entity names from `Entities/` — do NOT create slightly different spellings
- If a new entity appears, create a new file in `Entities/<type>/<slug>.md`
- For locations, prefer system names; add station/outpost names only if explicitly mentioned
- `arc_id` should match an existing arc from `Arcs/` or be left blank
- `player_impact`: What did/does this mean for Commanders at the time?
- `modern_impact`: Why does this still matter in the current timeline?

### 4. Run Validation
```bash
python3 scripts/validate_enrichment.py
```
Fix any reported issues (missing fields, invalid UUIDs, etc.).

### 5. Build the Lore Graph
```bash
python3 scripts/build_graph.py
```
This generates `lore_graph.json` and all client JSON files (`galnet-meta.json`, `galnet-bodies.json`, `search-index.json`, `version.json`).

### 6. Verify Build Output
```bash
# Check counts match expectations
python3 -c "import json; d=json.load(open('website/public/data/version.json')); print(d)"
```

### 7. Local Build Test (Optional but Recommended)
```bash
cd website
pnpm install
pnpm build
```
Check that the build succeeds without errors.

### 8. Commit & Push
```bash
cd /home/kernic/Development/ed-lore
git add -A
git commit -m "Add X new GalNet articles for 330X-XX-XX"
git push origin main
```

### 9. Audio Generation (Automatic)
The `audio-generation` GitHub Actions workflow will:
1. Detect the new articles (missing from `audio_manifest.json`)
2. Generate TTS audio for them
3. Upload new MP3s to Cloudflare R2
4. Build and deploy the site

This runs automatically within the hour (scheduled), or trigger it manually:
- GitHub → Actions → Audio Generation → Run workflow

### 10. Verify Live Site
After deploy completes (~5–10 minutes):
- Check article count: https://kernicde.github.io/ed-lore/
- Test audio on a new article
- Confirm search works for new entities

## Entity Management During Enrichment

### Finding Existing Entities
```bash
# Search entities by name
grep -ri "entity name" Entities/ | head -10
# List all person entities
ls Entities/person/ | head -20
```

### Creating a New Entity
Create `Entities/<type>/<slug>.md`:
```yaml
---
name: "Full Name"
type: "person|faction|location|organization|technology"
first_appearance: "330X-XX-XX"
related_entities:
  - "other-entity-slug"
---
Biography or description here.
```

### Updating an Existing Entity
Open the entity file and add:
- New appearances (dates)
- New relationships
- Updated biography if new information revealed

## Important Notes
- **Always enrich manually** — do NOT run `scripts/enrich.py` automatically. It was used for bulk initial import and makes assumptions that don't hold for nuanced new articles.
- **Audio is fully automated** — never generate audio locally. The GitHub Actions workflow handles TTS generation, R2 upload, and deployment.
- **Cache busting is automatic** — `build_graph.py` writes a new timestamp to `version.json` on every run, forcing returning visitors to reload JSON.
- **Do NOT commit MP3s** — `website/public/audio/` is in `.gitignore`. All audio lives on Cloudflare R2.

## Emergency: If Audio is Missing After Deploy
1. Check R2 bucket: `scripts/sync_audio_to_r2.py --check`
2. If incomplete, trigger Audio Generation workflow manually on GitHub
3. The workflow is self-healing — it will fill gaps within 1–3 hourly slots
