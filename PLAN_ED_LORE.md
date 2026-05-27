# Plan: Von GalNet Chronicle zu Elite Dangerous Lore (ED Lore)

## Ziel
Erweiterung der bestehenden GalNet Chronicle-Seite zu einer umfassenden Elite Dangerous Lore-Plattform, die neben offiziellen GalNet-Artikeln auch Community-Inhalte (CMDR Logs und Chronicles) integriert.

---

## 1. Zentrale Design-Entscheidung: Integration der Content-Kategorien

### Option A: Einheitliche Timeline mit visueller Trennung (Empfohlen)
Alle Artikel (GalNet, CMDR Logs, Chronicles) erscheinen in einer einzigen chronologischen Timeline. Die Kategorie wird durch visuelle Marker (Badges, Farben, Icons) unterschieden. Der Nutzer kann per Filter ein- oder ausblenden.

**Vorteile:**
- Lore bleibt zeitlich kohärent – ein Event aus GalNet und die dazugehörige CMDR-Perspektive liegen direkt beieinander
- Keine fragmentierte Nutzererfahrung
- Die Timeline als Herzstück behält ihre Bedeutung
- Einfacher für Audio-Feed (alles in einem Stream)

**Nachteile:**
- CMDR Logs könnten die offizielle Timeline "verwässern" wenn es viele gibt
- Erfordert klare visuelle Differenzierung

### Option B: Getrennte Bereiche mit gemeinsamer Entity-Verknüpfung
GalNet bleibt auf der Hauptseite. CMDR Logs und Chronicles bekommen eigene Unterseiten (`/logs/`, `/chronicles/`). Entities verlinken auf alle drei Bereiche.

**Vorteile:**
- Klare Trennung zwischen Canon und Community
- Nutzer, die nur offizielle Inhalte wollen, werden nicht gestört
- Einfacher zu navigieren bei hohem Community-Volumen

**Nachteile:**
- Bricht die chronologische Kohärenz
- Erfordert mehr Klicks für Kontext
- Schwieriger auf Mobile

### Option C: Hybrider Ansatz – Timeline + dedizierte Arc-Seiten
GalNet und Chronicles erscheinen in der Timeline (da beide datiert und arc-basiert sind). CMDR Logs bekommen eine eigene `/logs/` Seite, da sie lose Blogposts sind. Chronicles-Arcs sind wie bisherige Arcs, aber mit Community-Badge.

**Vorteile:**
- Chronicles als zeitlich verankerte Story-Arcs passen natürlich in die Timeline
- CMDR Logs als lose Gedanken/Stimmen separat
- Balanciert Kohärenz und Übersichtlichkeit

**Nachteile:**
- Zwei verschiedene Paradigmen für Community-Inhalte
- Etwas komplexer zu kommunizieren

---

## 2. Datenmodell-Erweiterungen

### Neue Felder für Artikel-Frontmatter

```yaml
---
# Bestehende Felder bleiben erhalten
uuid: ...
title: ...
slug: ...
date: '3307-03-15'
source_url: ...

# NEU: Content-Kategorie
category: galnet        # galnet | cmdr-log | chronicle
source_type: official   # official | community

# NEU: Arc-Zuordnung (Arcs sind quellen-unabhängig!)
# Ein Arc wie "distant-worlds-3" kann sowohl offizielle GalNet-Artikel
# als auch Community-Chronicles und CMDR Logs enthalten.
arc_id: distant-worlds-3
arc_chapter: 5

# NEU: Quellen-Verwaltung (mehrere Quellen möglich)
sources:
  - name: "Frontier Forums"
    url: "https://forums.frontier.co.uk/threads/distant-worlds-3-the-narrative.646004/page-3#post-12345678"
    type: forum_post
    author: "CMDR Erimus Kamzel"
    date: "3307-03-15"
  - name: "Reddit"
    url: "https://reddit.com/r/EliteDangerous/..."
    type: reddit_post
    author: "u/Explorer42"

curated_by: "CMDR KernicDE"  # Wer hat diesen Eintrag erstellt/bearbeitet
curated_date: "2026-05-27"

# NEU: Für Community-Inhalte
author: CMDR StarGazer  # Primärer Autor (für Anzeige)
author_url: https...

# Bestehende Enrichment-Felder
summary: ...
player_impact: ...
modern_impact: ...
topics: ...
entities: ...
locations: ...
---
```

**Wichtige Design-Entscheidung: Arcs sind Arcs — unabhängig von der Quelle.**

Ein Arc wie *Distant Worlds 3* existiert als Konzept und kann Artikel aus **allen drei Kategorien** enthalten:
- **GalNet (official):** Frontier berichtet über den Start der Expedition
- **Chronicle (community):** CMDR Erimus Kamzels Narrative aus dem Forum
- **CMDR Log (community):** Persönliche Reiseberichte teilnehmender Piloten

`arc_id` verbindet sie alle. Auf der Arc-Seite werden die Artikel gruppiert:
```
┌─ Distant Worlds 3 ──────────────────────┐
│ [◈ Official] [📖 Chronicles] [✎ Logs]   │
│                                         │
│ 3307-01-15  ◈ Expedition Announced     │  ← GalNet (official)
│ 3307-01-20  📖 Chapter 1 — The Call    │  ← Chronicle (community)
│ 3307-02-01  ✎ My DW3 Experience        │  ← CMDR Log (community)
│ 3307-02-05  ◈ Fleet Reaches Waypoint 1 │  ← GalNet (official)
└─────────────────────────────────────────┘
```

`sources` ist ein Array, da ein Community-Artikel aus mehreren Fragmenten zusammengesetzt sein kann. Der `curated_by`-Eintrag zeigt, wer den Markdown-Eintrag im Repository erstellt hat.

### Entity-Seiten: Separater Community-Mentions-Block

Auf Entity-Seiten (z.B. `Jaques Station`) erscheinen Community-Verweise in einem **eigenen Panel über den GalNet-Erwähnungen** — Community-Lore wird als lebendige, aktuelle Stimme priorisiert:

```
┌─ Community Lore (3 mentions) ────────────┐
│ • Distant Worlds 3: Chapter 5 — The Jump │
│ • CMDR Log: Meine Ankunft bei Jaques     │
│ • Chronicle: The Longest Haul            │
├─ Official Mentions (45 GalNet articles) ─┤
│ • GalNet: Jaques Station Relocated       │
│ • GalNet: Colonia Initiative Complete    │
└──────────────────────────────────────────┘
```

**Regeln:**
- Community-Inhalte fließen **nicht** in Entity-Beschreibungen ein (kein Einfluss auf Bio/Description)
- Chronicles-Arcs werden verlinkt, aber nicht in die automatische Zusammenfassung übernommen
- `mention_count`, `first_seen_date`, `last_seen_date` bleiben auf **offizielle** GalNet-Artikel beschränkt

### Neue Verzeichnisstruktur für Content

```
ed-lore/
├── Archive/                    # GalNet (bleibt)
│   └── 3307/03/15_slug.md
├── Community/                  # NEU
│   ├── sources/               # NEU: Quellen-Registry
│   │   ├── frontier-forums.md
│   │   ├── reddit-elite-dangerous.md
│   │   └── discord-dw3.md
│   ├── cmdr-logs/             # Blogposts
│   │   └── 3307/03/cmdr-stargazer_my-trip-to-jaques.md
│   └── chronicles/            # Story-Arcs wie Distant Worlds
│       └── distant-worlds-3/
│           ├── 3307/03/15_chapter-05-the-jump.md
│           └── 3307/04/02_chapter-06-the-departure.md
└── Entities/
    ├── Arcs/
    │   └── distant-worlds-3.md   # NEU: Community-Arc
```

**Quellen-Registry (`Community/sources/`):**
- Jede Quelle bekommt eine kurze Markdown-Datei mit URL-Muster, Beschreibung, Vertrauens-Level
- Artikel verlinken via `source_id` statt harter URLs
- Ermöglicht spätere Massen-Updates wenn sich URLs ändern
- Beispiel: `frontier-forums.md` → `base_url: https://forums.frontier.co.uk/threads/...`

---

## 3. Website-Anpassungen

### Rebranding
- Titel: "ED Lore — Elite Dangerous Lore Explorer" (statt GalNet Chronicle)
- URLs bleiben unter `kernicde.github.io/ed-lore/` (Redirects nicht nötig)
- Meta-Tags, OG-Tags, RSS-Feeds anpassen

### Filter/Selektor in der Timeline
Neue Filter-Bar oberhalb oder in der Context-Panel:
- **Toggle-Gruppe:** `[GalNet ■] [Chronicles ■] [CMDR Logs □]`
- Default: GalNet + Chronicles aktiv, CMDR Logs optional
- Speicherung in localStorage

### Visuelle Differenzierung in der Timeline
- **GalNet:** Elite-Orange Akzent, kleines "◈ Official"-Badge
- **Chronicles:** Elite-Blau Akzent, "📖 Chronicle"-Badge mit Arc-Namen
- **CMDR Logs:** Grüner Akzent, "✎ CMDR Log"-Badge mit Autor

### Feinerer Datumsslider
Statt nur Jahres-Sprüngen:
- **Desktop:** Monat-Jahr-Slider (z.B. "Mar 3307") mit Zoom-In auf Arc-Bereiche
- **Mobile:** Kompakter Slider mit Halbjahres-Schritten, tippen öffnet Datums-Picker
- Schnell-Sprung zu Arc-Anfang/Ende über Arc-Liste im Context-Panel

### Entity-Seiten
- "Mentions Timeline" → umbenennen in "Official Mentions"
- Neues Panel "Community Lore" mit separater Liste
- Bei Chronicles: Link zur Arc-Seite statt Einzelartikel

### Arc-Seiten
- Arcs sind **quellen-neutral** — ein Arc wie *Distant Worlds 3* zeigt alle seine Artikel gruppiert nach Kategorie
- **Chronologie-Ansicht:** Alle Artikel zeitlich sortiert, mit Kategorie-Badge (◈ Official / 📖 Chronicle / ✎ CMDR Log)
- **Filter-Tabs:** `[All] [◈ Official] [📖 Chronicles] [✎ CMDR Logs]` — ermöglicht Fokus auf einen Typ
- **"Community Chronicle"-Banner** erscheint nur, wenn der Arc Community-Inhalte enthält
- Quellen-Panel am Ende: Alle `sources[]` aus allen Artikeln des Arcs, dedupliziert

**Beispiel Distant Worlds 3 Arc-Seite:**
```
┌─ Distant Worlds 3 ───────────────────────────┐
│ [All] [◈ Official] [📖 Chronicles] [✎ Logs] │
│                                              │
│ 3307-01-15  ◈ GalNet: Expedition Announced   │
│ 3307-01-20  📖 Chapter 1 — The Call          │
│ 3307-01-22  ✎ CMDR Log: Mein erstes DW3      │
│ 3307-02-05  ◈ GalNet: Fleet Reaches WP1      │
│ 3307-02-10  📖 Chapter 2 — Into the Deep     │
│ ...                                          │
│                                              │
│ Sources:                                     │
│ • Frontier Forums — Distant Worlds 3 Thread  │
│ • Reddit — DW3 Megathread                    │
└──────────────────────────────────────────────┘
```

### Suche (Command Console)
- Suchergebnisse zeigen Kategorie-Badge
- Filter-Shortcuts: `official:`, `community:`, `chronicle:`, `cmdr:`

---

## 3b. Quellen-Management & User-Einreichungen

### Viele Quellen, stückweise Erfassung

Community-Lore entsteht nicht linear. Ein Chronicle wie Distant Worlds 3 hat:
- Einen Haupt-Thread im Frontier-Forum (mehrere Seiten, hunderte Posts)
- Begleit-Posts auf Reddit
- Eventuell Discord-Zusammenfassungen
- Nachträgliche Retrospektiven

**Lösung: Fragment-basierte Erfassung**
- Jedes Chronicle-Kapitel ist eine **Zusammenstellung** mehrerer Original-Posts
- `sources[]` erfasst jeden Post als eigenen Eintrag mit Direktlink
- Wenn später ein weiterer Post gefunden wird, wird er an `sources[]` angehängt
- Keine Angst vor Inkrementalität – das System ist darauf ausgelegt

### User-Einreichungs-Workflow

**Option 1: GitHub Issues (Empfohlen)**
- Template: "Community Content Submission"
- Felder: URL, Typ (Chronicle/CMDR Log), Zugehöriger Arc, Zusammenfassung
- Maintainer prüft, erstellt Markdown, merged
- Vorteil: Transparent, versioniert, diskutierbar

**Option 2: Einfaches Formular (zukünftig)**
- Static-Site-Formular → GitHub Issue API oder E-Mail
- Kein Backend nötig
- Vorteil: Niedriger Einstieg für Nicht-Techniker

**Option 3: Direkte PRs**
- Erfahrene Community-Mitglieder erstellen direkt Markdown-Dateien
- Wie bei Open-Source-Dokumentation üblich
- Vorteil: Höchste Qualität, niedrigster Pflegeaufwand

### Quellen-Registry (optional)

```yaml
# Community/sources/frontier-forums.yaml
---
id: frontier-forums
name: "Frontier Developments Forums"
base_url: "https://forums.frontier.co.uk/"
trust_level: high
description: "Offizielle Elite Dangerous Community-Foren"
---
```

Artikel verweisen dann via `source_name: "Frontier Forums"` statt harter URLs – ermöglicht Massen-Updates.

### Distant Worlds 3 — Konkretes Beispiel

**Hauptquelle:** https://forums.frontier.co.uk/threads/distant-worlds-3-the-narrative.646004/
- Thread-Start: Planung und Ankündigung
- Seite 2-3: Kapitel 1-3 der Narrative
- Seite 4-5: Kapitel 4-6
- etc.

**Erfassung heute (Mai 2026):**
1. Erstelle `Entities/Arcs/distant-worlds-3.md` (Arc-Übersicht)
2. Erstelle `Community/chronicles/distant-worlds-3/3307_01_chapter-01.md` mit Quellen aus Seite 2
3. Erstelle weitere Kapitel nach und nach
4. Jedes Kapitel verlinkt exakt auf den Forum-Post

**Nachträgliche Ergänzung (Juni 2026):**
- Jemand findet ein vergessenes Kapitel auf Seite 7
- Neues Markdown angelegt oder `sources[]` erweitert
- Keine Änderung an bestehenden Dateien nötig

---

## 4. Build-Pipeline-Anpassungen

### `scripts/build_graph.py`
1. **Neue Quellverzeichnisse einlesen:**
   - `Archive/` → `category: galnet`, `source_type: official`
   - `Community/chronicles/` → `category: chronicle`, `source_type: community`
   - `Community/cmdr-logs/` → `category: cmdr-log`, `source_type: community`

2. **Neue Felder im Article-Record:**
   ```python
   record["category"] = fm.get("category", "galnet")
   record["source_type"] = fm.get("source_type", "official")
   record["author"] = fm.get("author", "")
   record["sources"] = fm.get("sources", [])  # NEU: Array von Quellen
   record["curated_by"] = fm.get("curated_by", "")
   record["curated_date"] = fm.get("curated_date", "")
   ```

3. **Quellen-Aggregation pro Arc:**
   - Sammelt alle `sources[]` aus Chronicle-Kapiteln eines Arcs
   - Dedupliziert nach URL
   - Speichert in `arc["sources"]` für die Arc-Detailseite

4. **Entity-Mentions-Separierung:**
   - GalNet-Mentions → `entity["article_uuids"]` (wie bisher)
   - Community-Mentions → `entity["community_article_uuids"]` (neu)
   - Nur GalNet-Mentions fließen in `mention_count`, `first_seen_date`, `last_seen_date`

5. **Arc-Verarbeitung (quellen-neutral):**
   - Ein Arc wie `distant-worlds-3` sammelt **alle** Artikel mit diesem `arc_id`, egal ob `category: galnet`, `chronicle` oder `cmdr-log`
   - Arc-Record enthält:
     - `mention_count`: Gesamtanzahl aller Artikel
     - `official_count`: Nur `category: galnet`
     - `community_count`: `chronicle` + `cmdr-log`
   - `first_seen_date` / `last_seen_date` über ALLE Artikel berechnet
   - `key_entities` aus allen Artikeln aggregiert

6. **Neue Client-JSONs:**
   - `community-meta.json` (optional, falls groß)
   - Oder: Alles in `galnet-meta.json`, aber mit `category`-Filter im Client

### RSS/Atom-Feeds
- Separate Feeds pro Kategorie: `/rss.xml`, `/chronicles.xml`, `/cmdr-logs.xml`
- Oder: Ein Feed mit `<category>`-Tags
- Jeder Feed-Eintrag enthält `<source>` mit Original-URL(s)

---

## 5. Markdown-Format für manuelles Einfügen

### CMDR Log-Template
```markdown
---
uuid: "uuidv5 aus date + title"
title: "My Journey to Jaques Station"
slug: "cmdr-stargazer_my-journey-to-jaques"
date: "3307-03-15"
category: cmdr-log
source_type: community
author: "CMDR StarGazer"
author_url: "https://..."
sources:
  - name: "Frontier Forums"
    url: "https://forums.frontier.co.uk/threads/..."
    type: forum_post
    author: "CMDR StarGazer"
  - name: "Reddit"
    url: "https://reddit.com/r/EliteDangerous/..."
    type: reddit_post
curated_by: "CMDR KernicDE"
curated_date: "2026-05-27"
summary: "A personal account of the 22,000 ly trek to Jaques Station."
player_impact: "Tips for aspiring explorers on the Colonia Highway."
modern_impact: "Still relevant for new Colonia-bound pilots."
topics: ["exploration", "colonia", "anaconda"]
entities:
  - Jaques Station
  - Colonia
locations:
  - Eol Prou RS-T d3-94
---

The stars look different out here...
```

### Chronicle-Kapitel-Template (Beispiel: Distant Worlds 3)
```markdown
---
uuid: "..."
title: "Distant Worlds 3: Chapter 5 — The Jump"
slug: "distant-worlds-3_chapter-05-the-jump"
date: "3307-03-15"
category: chronicle
source_type: community
community_arc_id: distant-worlds-3
community_arc_chapter: 5
sources:
  - name: "Frontier Forums — Distant Worlds 3: The Narrative"
    url: "https://forums.frontier.co.uk/threads/distant-worlds-3-the-narrative.646004/page-3#post-12345678"
    type: forum_post
    author: "CMDR Erimus Kamzel"
    date: "3307-03-15"
  - name: "Frontier Forums — Distant Worlds 3: The Narrative"
    url: "https://forums.frontier.co.uk/threads/distant-worlds-3-the-narrative.646004/page-4#post-12345700"
    type: forum_post
    author: "CMDR Erimus Kamzel"
    date: "3307-03-16"
curated_by: "CMDR KernicDE"
curated_date: "2026-05-27"
summary: "The fleet makes the final jump into the Deep."
entities:
  - Jaques Station
  - Distant Worlds Expedition
locations:
  - Beagle Point
---

The fleet assembled at the waypoint...
```

**Hinweis:** Ein Chronicle-Kapitel kann aus mehreren Forum-Posts (verschiedene Seiten desselben Threads) zusammengesetzt sein. Die `sources`-Liste erfasst jeden Original-Post einzeln. Wenn später ein weiterer Post zum selben Kapitel hinzukommt, wird er einfach an `sources[]` angehängt.

### Arc-Entity-Template (quellen-neutral)

**Wichtig:** Arcs selbst haben kein `source_type` oder `category`. Ein Arc ist ein Arc. Erst die **Artikel innerhalb des Arcs** haben eine Kategorie.

```markdown
---
id: distant-worlds-3
name: "Distant Worlds 3"
type: arc
first_seen_date: "3307-01-15"
last_seen_date: "3307-08-22"
mention_count: 42        # Inkl. ALLER Artikel (GalNet + Community)
official_count: 8        # Nur GalNet-Artikel
community_count: 34      # Chronicles + CMDR Logs
significance: high
key_entities:
  - Jaques Station
  - Beagle Point
sources:
  - name: "Frontier Forums — Distant Worlds 3: The Narrative"
    url: "https://forums.frontier.co.uk/threads/distant-worlds-3-the-narrative.646004/"
    type: forum_thread
    author: "CMDR Erimus Kamzel"
---

# Distant Worlds 3

A player-organized expedition to the far reaches of the galaxy...

## Summary

Over 1,000 CMDRs participated in this months-long journey...

## Phases

1. Assembly at Pallaeni
2. The Colonia Crossing
3. The Core Transit
4. The Final Push to Beagle Point
5. Return Journey
```

---

## 6. Mobile/Audio/Feed-Kompatibilität

### Mobile
- Filter-Toggles als kompakte Chips unter dem Header
- CMDR Logs auf Mobile: Autoren-Avatar (Platzhalter) + kurze Vorschau
- Touch-freundliche Timeline mit Swipe-Gesten zwischen Artikeln

### Audio / TTS
- **Alle Inhalte können TTS bekommen** — Enrichment und Audio-Generierung gelten für GalNet, Chronicles UND CMDR Logs gleichermaßen
- Audio-Manifest erweitert um `category`-Feld
- Im Audio-Player: Kleines Badge neben Titel ("◈ Official" / "📖 Chronicle" / "✎ CMDR Log")
- **Edge-tts** (`en-GB-SoniaNeural`) für alle Kategorien
- GitHub Actions Audio-Pipeline erweitert: Verarbeitet alle `category`-Typen
- Cache-Schlüssel: `{uuid}-{audio_hash}` (wie bisher, unabhängig von Kategorie)

### Feed
- RSS/Atom: Ein Hauptfeed mit allen Kategorien + `<category>`-Tags
- Separate Feeds für Puristen (`/rss-official.xml`, `/rss-community.xml`)
- Podcast-Feed für Audio: Alle Kategorien mit `has_audio: true`

---

## 7. Implementierungsschritte (Empfohlene Reihenfolge)

### Phase 1: Foundation (keine UI-Änderungen)
1. Datenmodell erweitern (`category`, `source_type`, `author`, etc.)
2. `build_graph.py` anpassen für neue Verzeichnisse
3. Erste Community-Markdown-Dateien anlegen (Distant Worlds 3 als Test)
4. Entities erweitern: `community_article_uuids`

### Phase 2: Rebranding & UI-Basics
1. Alle "GalNet Chronicle"-Strings zu "ED Lore"
2. Timeline-Artikel mit Kategorie-Badges
3. Filter-Toggles im Context Panel

### Phase 3: Neue Seitentypen
1. Community-Arc-Seiten (`/arc/[id].astro` erweitern)
2. CMDR Logs separat oder in Timeline
3. Entity-Seiten: Community-Mentions-Block

### Phase 4: Erweiterte Features
1. Feinerer Datumsslider (Monats-Schritte)
2. Audio-Marker für Kategorien
3. RSS-Feeds pro Kategorie
4. Search-Filter nach Kategorie

---

## Anhang: Discord-Zusammenfassung (max 2000 chars)

```markdown
🚀 **ED Lore — Expansion Plan**

GalNet Chronicle is becoming **ED Lore** — a unified platform for all Elite Dangerous lore, not just GalNet articles.

**What's new:**
• **Three content categories:** GalNet (official), Chronicles (community story arcs), CMDR Logs (community blogposts)
• **Mixed timelines:** Official and community content share the same chronological timeline — e.g. Distant Worlds 3 will show both Frontier's GalNet articles AND player-written narratives side by side
• **Source-first:** Every community entry links to its original source (forum posts, Reddit, etc.) with full transparency via `curated_by`
• **AI enrichment & TTS:** Community content gets the same AI treatment as GalNet — summaries, player impact analysis, and text-to-speech audio
• **Fragment-friendly:** Sources can be added piecemeal over time. Find a DW3 forum post from 2021 today? Add it next week. No problem.

**Content structure:**
`Archive/` → GalNet (unchanged)
`Community/chronicles/` → Story arcs like Distant Worlds 3
`Community/cmdr-logs/` → Loose blogposts
`Community/sources/` → Source registry for URL management

**User submissions:** GitHub Issue template → maintainer review → markdown merge. Simple, transparent, versioned.

**Example:** Distant Worlds 3 has official GalNet articles AND a 100+ page forum narrative. Both will live under the same `distant-worlds-3` arc, filterable by type.

Feedback welcome! 🫡
```

---

## 8. Offene Entscheidungen für den User

1. **Integration:** Option A (einheitliche Timeline), B (getrennt), oder C (hybrid)?
2. **CMDR Logs:** Sollen diese TTS-Audio bekommen oder nicht?
3. **Feed-Quellen:** Soll es einen Feed-Importer geben (z.B. Reddit, Forum-RSS) oder nur manuelles Markdown?
4. **Datumsslider:** Monatsschritte auf Desktop, Quartale auf Mobile?
5. **Entity-Beschreibungen:** Sollen Chronicles (nicht CMDR Logs) *doch* in Entity-Bios erwähnt werden können (als "Also featured in community chronicle: Distant Worlds 3")?
