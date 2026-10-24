# ed-lore — The GalNet Chronicle

Angereichertes Archiv aller Elite-Dangerous-GalNet-Artikel (3301–3312+) als statische Website: https://kernicde.github.io/ed-lore/

Stand 2026-10-10: 2.616 Einträge (GalNet-Artikel, Chronicles), 38 Story-Arcs, 3.346 Entitäten (Personen, Fraktionen, Systeme, Stationen, Technologien u. a.).

## Aufbau

```
Archive/<Jahr>/<Monat>/<Tag>_<slug>.md   Artikel (Markdown + YAML-Frontmatter)
Entities/<typ>/*.md, Entities/Arcs/*.md  Entitäts- und Arc-Profile
        │  scripts/build_graph.py
        ▼
lore_graph.json + website/public/data/*  generierte Daten
        │
        ▼
website/                                  Astro-6-Site (React-Inseln), Basis-Pfad /ed-lore
```

- `GalNet/`, `Community/`: Rohquellen (GalNet-Jahrgänge, Community-Chronicles)
- `website/`: Timeline, Chronicles, Karte, Entitäts- und Arc-Seiten, Suche, Audio-Player, RSS/Atom
- Audio: MP3s (edge-tts, `en-GB-SoniaNeural`) liegen in einem Cloudflare-R2-Bucket, nicht im Build

## Befehle

```bash
python scripts/build_graph.py          # Graph neu bauen (nach jeder Änderung an Archive/ oder Entities/)
python scripts/validate_enrichment.py  # Frontmatter prüfen
cd website && pnpm install && pnpm dev # Dev-Server
cd website && pnpm build               # lokaler Produktions-Build
```

Python ab 3.10 (`pyyaml`, `httpx`, `tqdm`), Node ab 22.12.

Weitere Skripte in `scripts/`:
- `fetch.py` lädt GalNet neu und überschreibt `Archive/` (nur bewusst ausführen)
- `enrich_{systems,stations,bodies}_edsm.py` ergänzen Daten über die EDSM-API
- `audit_*.py` vergleichen Archiv, Arcs und UUIDs
- `generate_audio.py`, `sync_audio_to_r2.py` laufen über den Workflow `audio-generation`

## Deployment

Push auf `main` löst den GitHub-Actions-Workflow `deploy.yml` aus (Build und GitHub Pages). `audio-generation.yml` läuft stündlich. R2-Zugangsdaten liegen nur in den GitHub Secrets.

Technische Details und Redaktionsregeln: `AGENTS.md`, `CLAUDE.md`. Lizenz: `LICENSE`.
