# Daily GalNet Enrichment & Publishing Prompt

> Copy-paste this prompt into your AI assistant to run the full daily workflow.
> This checks for new articles, enriches them, updates entities/arcs/audio, and publishes.

---

## PROMPT (copy everything below this line)

```
You are the automated maintainer of "The GalNet Chronicle" — an Elite Dangerous lore archive.

Run the FULL daily workflow in the repository at the current working directory.

### STEP 1: Check for new GalNet articles
Run: `python fetch.py`
- This fetches new articles from the Frontier API and GitHub archive.
- WARNING: This is a destructive sync. Review the output to see how many new/modified articles were fetched.
- If no new articles were found, report that and skip to Step 4 (audio check).

### STEP 2: Enrich new articles
For every NEW article (those without `summary` and `player_impact` in frontmatter):
1. Read the article file fully
2. Add these fields to the YAML frontmatter:
   - `summary`: 1-3 sentence summary of the article content
   - `player_impact`: What pilots could do / did in this event
   - `modern_impact`: Why this still matters (if relevant)
   - `persons`: List of named individuals (full canonical names)
   - `groups`: List of factions, corporations, political bodies
   - `locations`: List of star systems or significant places
   - `technologies`: List of named ships, weapons, gadgets
   - `topics`: Tags like `terrorism`, `diplomacy`, `corporate expansion`
   - `arc_id`: Story arc identifier (only if clearly part of a known arc)
   - `related_uuids`: Related article UUIDs (find chronologically adjacent articles in same arc, or articles with shared entities)
   - `legacy_weight`: 1-5 scale of long-term importance
   - `significance`: `low` / `medium` / `high`
3. Use `StrReplaceFile` for precise edits — never guess, always read first.
4. Remove garbage auto-extractions:
   - Remove sentence-fragment entities like "With the", "Our endeavour in"
   - Never put "Thargoid" as a location
   - Deduplicate groups (e.g. "Sirius Corp" → "Sirius Corporation")
   - Do not use "ACT" as an entity
5. Run `python scripts/validate_enrichment.py` after editing to catch errors.

### STEP 3: Rebuild the knowledge graph
```bash
python scripts/build_graph.py
```
This rebuilds `lore_graph.json`, `galnet-meta.json`, and `galnet-bodies.json`.
Check the output for the article/entity/arc counts.

### STEP 4: Check for new entities and arcs
After `build_graph.py` runs, check if new entity stubs or arc stubs were created:
- New entity files appear in `Entities/{type}/{id}.md`
- New arc files appear in `Entities/Arcs/{id}.md`

For each NEW entity with `*[To be enriched]*` in its Biography:
1. Read the entity's articles (look up via the entity name in `lore_graph.json`)
2. Generate a concise bio (1-3 sentences) based on article summaries
3. Replace `*[To be enriched]*` with the generated bio

For each NEW arc with `*[To be enriched]*` in its Description:
1. Read the arc's articles
2. Write a proper arc description (2-4 sentences summarizing the story)
3. Replace `*[To be enriched]*` with the description

### STEP 5: Build the website
```bash
cp lore_graph.json website/src/data/lore_graph.json
cd website && pnpm build
```
Verify the build succeeds with no errors.

### STEP 6: Commit and push
```bash
git add -A
git commit -m "Daily enrichment: [DATE] — N new articles enriched, X entities, Y arcs"
git push origin main
```
This triggers the GitHub Actions deploy workflow.

### STEP 7: Generate audio for new articles
```bash
python scripts/generate_audio.py --sort recent --concurrency 8
```
This generates MP3 audio files for any articles that don't have them yet.

Then check: how many audio files exist vs total articles?
```bash
ls website/public/audio/*.mp3 | wc -l
```

If fewer than 90% of articles have audio (target: 2,500+ files), start a new 500-batch:
```bash
python scripts/generate_audio.py --batch-size 500 --sort recent --concurrency 8
```

If the batch completed successfully, commit the updated manifest:
```bash
git add scripts/audio_manifest.json
git commit -m "Update audio manifest — batch N completed [skip ci]"
git push origin main
```

### BANNED TOPICS (remove unless explicitly legitimate)
`ship`, `sport`, `trade`, `construction`, `medicine`, `safety`, `treasure hunt`

### REPORT BACK
After completing all steps, report:
1. How many new articles were fetched
2. How many articles were enriched
3. How many new entities/arcs were created
4. Build status (pass/fail)
5. Audio generation status (X/Y files complete, batch progress)
6. Git push status (commit hash if successful)
```

---

## Usage

1. **Daily**: Paste the prompt above into your AI assistant.
2. **Every few days**: Same prompt — it will find whatever has accumulated.
3. **After major game updates** (new GalNet seasons): Run immediately to catch the flood of new articles.

## Notes

- `fetch.py` is **destructive** — it overwrites existing articles. Only run it when you're ready to reconcile changes.
- Audio generation is slow (~5 sec/article). The `--concurrency 8` flag parallelizes requests.
- The GitHub Actions workflow `.github/workflows/audio-generation.yml` runs automatically every midnight UTC to generate 500 audio files/day. The manual prompt above is for ad-hoc runs.
- Always validate enrichment with `python scripts/validate_enrichment.py` before committing.
