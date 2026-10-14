// UI chrome dictionary — English (canonical) + German.
// Content translations (articles, entities, arcs) are a later phase; this file
// only covers user-visible interface strings.

export type Lang = 'en' | 'de';

export const languages: { code: Lang; label: string }[] = [
  { code: 'en', label: 'English' },
  { code: 'de', label: 'Deutsch' },
];

const en = {
  // Meta / layout
  metaTitleDefault: 'ED Lore — Elite Dangerous Lore Explorer',
  metaDescriptionDefault:
    'Explore the complete Elite Dangerous lore archive: GalNet articles, community chronicles, CMDR logs, entity profiles, story arcs, and interactive timeline.',
  skipLink: 'Skip to main content',
  langToggleLabel: 'Switch language',

  // HUD header
  mapButton: 'Map',
  search: 'Search',
  searchTitle: 'Search (Cmd+K)',
  entriesCount: '{count} entries · 3301–3312',

  // Toggles
  toggleTheme: 'Toggle theme',
  toggleAi: 'Toggle AI content',
  toggleAiOn: 'AI enhanced (click for raw)',
  toggleAiOff: 'Raw only (click for AI enhanced)',

  // App-wide states
  loadingArchive: 'Loading ED Lore archive…',
  loading: 'Loading…',
  loadingAudio: 'Loading audio…',
  audioNotAvailable: 'Audio not available',
  play: 'Play',
  pause: 'Pause',

  // Categories (filter buttons)
  categoryGalnet: 'GalNet',
  categoryChronicles: 'Chronicles',
  categoryCmdrLogs: 'CMDR Logs',
  badgeOfficial: '◈ Official',
  badgeChronicle: '📖 Chronicle',
  badgeCmdrLog: '✎ CMDR Log',
  communityBadge: 'Community',

  // Timeline
  copyLinkTitle: 'Copy link to article',
  link: '🔗 Link',
  copied: 'Copied!',
  playAudioTitle: 'Play audio',
  audio: 'Audio',
  selectYear: 'Select year',
  sourceLink: 'Source ↗',
  sourceFallback: 'Source',
  aiSummary: 'AI Summary',
  aiAnalysis: 'AI Analysis',
  playerImpact: 'Player Impact',
  futureImpact: 'Future Impact',
  authorLabel: 'Author:',
  sourcesLabel: 'Sources:',
  curatedBy: 'Curated by',
  curatedOn: 'on',

  // Context panel
  jumpToDate: 'Jump to Date',
  jumpToYear: 'Jump to year',
  jumpToMonth: 'Jump to month',
  relatedArcs: 'Related Arcs',
  activeConnections: 'Active Connections',
  contextTitle: 'Context',
  noDataForPeriod: 'No data for this period',
  arcArticleRange: '{from} → {to} · {count} articles',
  dateMentions: '{date} · {count} mentions',

  // Search console
  searchPlaceholderAi: 'Search articles, entities, arcs... (official: / chronicle: / cmdr:)',
  searchPlaceholderRaw: 'Search raw article text... (official: / chronicle: / cmdr:)',
  esc: 'ESC',
  rawModeHint: 'Raw mode — searching article titles and full body text',
  noResults: 'No results found',
  typePrefix: 'Type:',
  typeArticle: 'Article',
  typeEntity: 'Entity',
  typeArc: 'Arc',
  typeLocation: 'Location',

  // Graph
  nodesLabel: 'Nodes:',
  loadingGraphData: 'Loading graph data…',
  initialisingGraph: 'Initialising graph…',
  typePerson: 'Person',
  typeFaction: 'Faction',
  typeTechnology: 'Technology',

  // Entity page
  firstSeen: 'First seen {date}',
  mentionsCount: '{count} mentions',
  activeRange: 'Active: {from} → {to}',
  unknown: 'Unknown',
  entityTypePerson: 'Person',
  entityTypeFaction: 'Faction / Organisation',
  entityTypeSystem: 'Star System',
  entityTypeStation: 'Station / Port',
  entityTypeBody: 'Planet / Moon',
  entityTypeRegion: 'Nebula / Sector',
  entityTypeTechnology: 'Technology / Ship',
  entityTypeLocation: 'System / Location',
  bioPerson: 'Biography',
  bioSystem: 'System Overview',
  bioStation: 'Station Overview',
  bioBody: 'Body Overview',
  bioRegion: 'Region Overview',
  bioTechnology: 'Technical Overview',
  bioDefault: 'Description',
  systemData: 'System Data',
  stationData: 'Station Data',
  bodyData: 'Body Data',
  regionData: 'Region Data',
  coordinates: 'Coordinates: [{x}, {y}, {z}]',
  allegiance: 'Allegiance:',
  government: 'Government:',
  security: 'Security:',
  economy: 'Economy:',
  population: 'Population:',
  reserve: 'Reserve:',
  controllingFaction: 'Controlling Faction:',
  systemLabel: 'System:',
  stationType: 'Station Type:',
  distanceToArrival: 'Distance to Arrival:',
  services: 'Services:',
  serviceMarket: 'Market',
  serviceShipyard: 'Shipyard',
  serviceOutfitting: 'Outfitting',
  typeGeneric: 'Type:',
  atmosphere: 'Atmosphere:',
  gravity: 'Gravity:',
  surfaceTemp: 'Surface Temp:',
  terraformable: 'Terraformable:',
  yes: 'Yes',
  no: 'No',
  approxLocation: 'Approx. Location:',
  sizeLabel: 'Size:',
  notableSystems: 'Notable Systems:',
  connectionMap: 'Connection Map',
  relatedEntities: 'Related Entities',
  communityLoreCount: 'Community Lore ({count} mentions)',
  officialMentionsCount: 'Official Mentions ({count} articles)',
  noOfficialArticles: 'No official articles found.',

  // Arc page
  articlesCount: '{count} articles',
  officialCount: '{count} official',
  communityCount: '{count} community',
  significanceLabel: 'Significance',
  significanceLow: 'low',
  significanceMedium: 'medium',
  significanceHigh: 'high',
  significanceCritical: 'critical',
  summaryTitle: 'Summary',
  overviewTitle: 'Overview',
  statusTitle: 'Status',
  outcomeTitle: 'Outcome',
  phasesTitle: 'Phases',
  keyFigures: 'Key Figures',
  chronologyCount: 'Chronology ({count} articles)',
  noArticlesFound: 'No articles found.',
  sourcesTitle: 'Sources',

  // Map page
  mapTitle: 'Entity Relationship Map',
  mapShortTitle: 'Relationship Map',
  mapDescription:
    'Interactive network map of all Elite Dangerous lore entities and their relationships across 3301–3312.',
  mapExplainer:
    'Network of lore entities connected by co-occurrence in GalNet articles. Use the slider to control density. Click any node to open its profile. Hover to highlight direct connections. Pinch or scroll to zoom.',
  mapUnavailableTitle: 'RELATIONSHIP MAP UNAVAILABLE',
  mapUnavailableBody:
    'The relationship map is built from AI-extracted entities and their co-occurrence patterns. Switch to AI-enhanced mode to explore the interactive network.',

  // Logs page
  logsTitle: 'CMDR Logs',
  logsSubtitle: '{count} logs · Personal stories from the black',
  noLogs: 'No CMDR logs found yet. Be the first to submit one!',
  sourceSingular: 'Source:',
  linkFallback: 'Link',

  // Chronicles page
  chroniclesTitle: 'Community Chronicles',
  chroniclesSubtitle: '{count} chapters · Player-written story arcs',
  noChronicles: 'No chronicles found yet.',
  uncategorized: 'Uncategorized',
};

const de: Record<keyof typeof en, string> = {
  metaTitleDefault: 'ED Lore — Elite-Dangerous-Lore-Explorer',
  metaDescriptionDefault:
    'Erkunde das vollständige Elite-Dangerous-Lore-Archiv: GalNet-Artikel, Community-Chroniken, CMDR-Logs, Entitätsprofile, Story-Arcs und eine interaktive Zeitleiste.',
  skipLink: 'Zum Inhalt springen',
  langToggleLabel: 'Sprache wechseln',

  mapButton: 'Karte',
  search: 'Suche',
  searchTitle: 'Suche (Cmd+K)',
  entriesCount: '{count} Einträge · 3301–3312',

  toggleTheme: 'Farbschema wechseln',
  toggleAi: 'KI-Inhalte umschalten',
  toggleAiOn: 'KI-erweitert (Klick für Rohtext)',
  toggleAiOff: 'Nur Rohtext (Klick für KI-erweitert)',

  loadingArchive: 'ED-Lore-Archiv wird geladen…',
  loading: 'Laden…',
  loadingAudio: 'Audio wird geladen…',
  audioNotAvailable: 'Audio nicht verfügbar',
  play: 'Abspielen',
  pause: 'Pause',

  categoryGalnet: 'GalNet',
  categoryChronicles: 'Chroniken',
  categoryCmdrLogs: 'CMDR-Logs',
  badgeOfficial: '◈ Offiziell',
  badgeChronicle: '📖 Chronik',
  badgeCmdrLog: '✎ CMDR-Log',
  communityBadge: 'Community',

  copyLinkTitle: 'Link zum Artikel kopieren',
  link: '🔗 Link',
  copied: 'Kopiert!',
  playAudioTitle: 'Audio abspielen',
  audio: 'Audio',
  selectYear: 'Jahr wählen',
  sourceLink: 'Quelle ↗',
  sourceFallback: 'Quelle',
  aiSummary: 'KI-Zusammenfassung',
  aiAnalysis: 'KI-Analyse',
  playerImpact: 'Spieler-Relevanz',
  futureImpact: 'Zukünftige Bedeutung',
  authorLabel: 'Autor:',
  sourcesLabel: 'Quellen:',
  curatedBy: 'Kuratiert von',
  curatedOn: 'am',

  jumpToDate: 'Zum Datum springen',
  jumpToYear: 'Zum Jahr springen',
  jumpToMonth: 'Zum Monat springen',
  relatedArcs: 'Verwandte Arcs',
  activeConnections: 'Aktive Verbindungen',
  contextTitle: 'Kontext',
  noDataForPeriod: 'Keine Daten für diesen Zeitraum',
  arcArticleRange: '{from} → {to} · {count} Artikel',
  dateMentions: '{date} · {count} Erwähnungen',

  searchPlaceholderAi: 'Artikel, Entitäten, Arcs suchen... (official: / chronicle: / cmdr:)',
  searchPlaceholderRaw: 'Rohen Artikeltext durchsuchen... (official: / chronicle: / cmdr:)',
  esc: 'ESC',
  rawModeHint: 'Rohtext-Modus — durchsucht Artikeltitel und Volltext',
  noResults: 'Keine Ergebnisse gefunden',
  typePrefix: 'Typ:',
  typeArticle: 'Artikel',
  typeEntity: 'Entität',
  typeArc: 'Arc',
  typeLocation: 'Ort',

  nodesLabel: 'Knoten:',
  loadingGraphData: 'Graphendaten werden geladen…',
  initialisingGraph: 'Graph wird initialisiert…',
  typePerson: 'Person',
  typeFaction: 'Fraktion',
  typeTechnology: 'Technologie',

  firstSeen: 'Zuerst gesehen: {date}',
  mentionsCount: '{count} Erwähnungen',
  activeRange: 'Aktiv: {from} → {to}',
  unknown: 'Unbekannt',
  entityTypePerson: 'Person',
  entityTypeFaction: 'Fraktion / Organisation',
  entityTypeSystem: 'Sternensystem',
  entityTypeStation: 'Station / Raumhafen',
  entityTypeBody: 'Planet / Mond',
  entityTypeRegion: 'Nebel / Sektor',
  entityTypeTechnology: 'Technologie / Schiff',
  entityTypeLocation: 'System / Ort',
  bioPerson: 'Biografie',
  bioSystem: 'Systemübersicht',
  bioStation: 'Stationsübersicht',
  bioBody: 'Himmelskörper-Übersicht',
  bioRegion: 'Regionsübersicht',
  bioTechnology: 'Technische Übersicht',
  bioDefault: 'Beschreibung',
  systemData: 'Systemdaten',
  stationData: 'Stationsdaten',
  bodyData: 'Körperdaten',
  regionData: 'Regionsdaten',
  coordinates: 'Koordinaten: [{x}, {y}, {z}]',
  allegiance: 'Zugehörigkeit:',
  government: 'Regierung:',
  security: 'Sicherheit:',
  economy: 'Wirtschaft:',
  population: 'Bevölkerung:',
  reserve: 'Reserve:',
  controllingFaction: 'Kontrollierende Fraktion:',
  systemLabel: 'System:',
  stationType: 'Stationstyp:',
  distanceToArrival: 'Ankunftsdistanz:',
  services: 'Dienste:',
  serviceMarket: 'Markt',
  serviceShipyard: 'Werft',
  serviceOutfitting: 'Ausrüstung',
  typeGeneric: 'Typ:',
  atmosphere: 'Atmosphäre:',
  gravity: 'Gravitation:',
  surfaceTemp: 'Oberflächentemp.:',
  terraformable: 'Terraformierbar:',
  yes: 'Ja',
  no: 'Nein',
  approxLocation: 'Ungefähre Lage:',
  sizeLabel: 'Größe:',
  notableSystems: 'Bemerkenswerte Systeme:',
  connectionMap: 'Verbindungskarte',
  relatedEntities: 'Verwandte Entitäten',
  communityLoreCount: 'Community-Lore ({count} Erwähnungen)',
  officialMentionsCount: 'Offizielle Erwähnungen ({count} Artikel)',
  noOfficialArticles: 'Keine offiziellen Artikel gefunden.',

  articlesCount: '{count} Artikel',
  officialCount: '{count} offiziell',
  communityCount: '{count} Community',
  significanceLabel: 'Bedeutung',
  significanceLow: 'gering',
  significanceMedium: 'mittel',
  significanceHigh: 'hoch',
  significanceCritical: 'kritisch',
  summaryTitle: 'Zusammenfassung',
  overviewTitle: 'Übersicht',
  statusTitle: 'Status',
  outcomeTitle: 'Ergebnis',
  phasesTitle: 'Phasen',
  keyFigures: 'Schlüsselfiguren',
  chronologyCount: 'Chronologie ({count} Artikel)',
  noArticlesFound: 'Keine Artikel gefunden.',
  sourcesTitle: 'Quellen',

  mapTitle: 'Beziehungskarte der Entitäten',
  mapShortTitle: 'Beziehungskarte',
  mapDescription:
    'Interaktive Netzwerkkarte aller Elite-Dangerous-Lore-Entitäten und ihrer Beziehungen von 3301–3312.',
  mapExplainer:
    'Netzwerk von Lore-Entitäten, verbunden durch gemeinsames Auftreten in GalNet-Artikeln. Nutze den Schieberegler zur Dichtesteuerung. Klicke einen Knoten an, um sein Profil zu öffnen. Hover hebt direkte Verbindungen hervor. Zum Zoomen scrollen oder kneifen.',
  mapUnavailableTitle: 'BEZIEHUNGSKARTE NICHT VERFÜGBAR',
  mapUnavailableBody:
    'Die Beziehungskarte basiert auf KI-extrahierten Entitäten und ihren Ko-Vorkommensmustern. Wechsle in den KI-erweiterten Modus, um das interaktive Netzwerk zu erkunden.',

  logsTitle: 'CMDR-Logs',
  logsSubtitle: '{count} Logs · Persönliche Geschichten aus dem All',
  noLogs: 'Noch keine CMDR-Logs vorhanden. Reiche das erste ein!',
  sourceSingular: 'Quelle:',
  linkFallback: 'Link',

  chroniclesTitle: 'Community-Chroniken',
  chroniclesSubtitle: '{count} Kapitel · Von Spielern geschriebene Story-Arcs',
  noChronicles: 'Noch keine Chroniken vorhanden.',
  uncategorized: 'Nicht kategorisiert',
};

export const dict: Record<Lang, Record<string, string>> = { en, de };

export const months: Record<Lang, readonly string[]> = {
  en: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
  de: ['Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez'],
};

const warned = new Set<string>();

export function t(lang: Lang, key: string, vars?: Record<string, string | number>): string {
  const table = dict[lang] || dict.en;
  let str = table[key] ?? dict.en[key];
  if (str === undefined) {
    if (!warned.has(key)) {
      console.warn(`[i18n] missing key: ${key}`);
      warned.add(key);
    }
    str = key;
  }
  if (vars) {
    str = str.replace(/\{(\w+)\}/g, (m, k: string) => (vars[k] !== undefined ? String(vars[k]) : m));
  }
  return str;
}

export function getLangFromDocument(): Lang {
  if (typeof document === 'undefined') return 'en';
  const attr = document.documentElement.getAttribute('data-lang');
  if (attr === 'en' || attr === 'de') return attr;
  try {
    const stored = window.localStorage.getItem('galnet-lang');
    if (stored === 'en' || stored === 'de') return stored;
  } catch {
    // localStorage unavailable
  }
  return 'en';
}
