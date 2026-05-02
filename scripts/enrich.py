import yaml
import re
import os
from collections import Counter

# --- YAML custom representer for : safety ---
def str_representer(dumper, data):
    if isinstance(data, str) and ': ' in data:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='"')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)

yaml.add_representer(str, str_representer, Dumper=yaml.SafeDumper)

# --- Paths ---
DIRECTORIES = [
    '/home/kernic/Development/ed-lore/Archive/3308/10',
    '/home/kernic/Development/ed-lore/Archive/3308/11',
    '/home/kernic/Development/ed-lore/Archive/3308/12',
]

VALID_ARCS = {
    'thargoid-titan-war',
    'salvation-azimuth',
    'salome-conspiracy',
    'nmla-terrorism',
    'guardian-thargoid-war',
    'nova-imperium',
    'federal-politics',
}

# --- Variant to canonical person mapping ---
VARIANT_TO_CANONICAL = {
    "Alba Tesreau": "Alba Tesreau", "Professor Alba Tesreau": "Alba Tesreau",
    "Professor Tesreau": "Alba Tesreau", "Tesreau": "Alba Tesreau",
    "Angela Corcoran": "Angela Corcoran", "Deputy Prime Minister Angela Corcoran": "Angela Corcoran",
    "Corcoran": "Angela Corcoran",
    "Mia Valencourt": "Mia Valencourt", "Dr Mia Valencourt": "Mia Valencourt", "Valencourt": "Mia Valencourt",
    "Carter Armstrong": "Carter Armstrong", "Dr Carter Armstrong": "Carter Armstrong", "Armstrong": "Carter Armstrong",
    "Yazhu Xing": "Yazhu Xing", "Dr Yazhu Xing": "Yazhu Xing", "Xing": "Yazhu Xing",
    "Allan Mantle": "Allan Mantle", "Dr Allan Mantle": "Allan Mantle", "Mantle": "Allan Mantle",
    "Seo Jin-ae": "Seo Jin-ae", "Ms Seo": "Seo Jin-ae", "Ms Seo Jin-ae": "Seo Jin-ae", "Subject D-2": "Seo Jin-ae",
    "Caleb Wycherley": "Caleb Wycherley", "Dr Caleb Wycherley": "Caleb Wycherley", "Wycherley": "Caleb Wycherley",
    "Torben Rademaker": "Torben Rademaker", "Rademaker": "Torben Rademaker",
    "Ishmael Palin": "Ishmael Palin", "Professor Ishmael Palin": "Ishmael Palin",
    "Professor Palin": "Ishmael Palin", "Dr Palin": "Ishmael Palin", "Dr Ishmael Palin": "Ishmael Palin", "Palin": "Ishmael Palin",
    "Ram Tah": "Ram Tah", "Professor Ram Tah": "Ram Tah", "Dr Ram Tah": "Ram Tah", "Tah": "Ram Tah",
    "Jasmina Halsey": "Jasmina Halsey", "Ambassador Jasmina Halsey": "Jasmina Halsey", "Halsey": "Jasmina Halsey",
    "Arissa Lavigny-Duval": "Arissa Lavigny-Duval", "Emperor Arissa Lavigny-Duval": "Arissa Lavigny-Duval",
    "Hadrian Duval": "Hadrian Duval", "Hadrian Augustus Duval": "Hadrian Duval",
    "Hengist": "Hengist",
    "Zemina Torval": "Zemina Torval", "Senator Zemina Torval": "Zemina Torval", "Senator Torval": "Zemina Torval", "Torval": "Zemina Torval",
    "Aisling Duval": "Aisling Duval", "Princess Aisling Duval": "Aisling Duval",
    "Caspian Leopold": "Caspian Leopold", "Senator Caspian Leopold": "Caspian Leopold", "Leopold": "Caspian Leopold",
    "Denton Patreus": "Denton Patreus", "Senator Patreus": "Denton Patreus", "Admiral Patreus": "Denton Patreus", "Patreus": "Denton Patreus",
    "Anders Blaine": "Anders Blaine", "Chancellor Anders Blaine": "Anders Blaine", "Chancellor Blaine": "Anders Blaine", "Blaine": "Anders Blaine",
    "Felicia Winters": "Felicia Winters", "Shadow President Felicia Winters": "Felicia Winters", "Winters": "Felicia Winters",
    "Lana Berkovich": "Lana Berkovich", "Secretary of State Lana Berkovich": "Lana Berkovich", "Secretary Berkovich": "Lana Berkovich", "Berkovich": "Lana Berkovich",
    "Dalton Chase": "Dalton Chase", "Governor Dalton Chase": "Dalton Chase", "Congressman Dalton Chase": "Dalton Chase", "Chase": "Dalton Chase",
    "Joy Senne": "Joy Senne", "Senne": "Joy Senne",
    "Heimar Borichev": "Heimar Borichev", "Borichev": "Heimar Borichev",
    "Polly French": "Polly French", "French": "Polly French",
    "Elias Pope": "Elias Pope", "Dr Elias Pope": "Elias Pope", "Pope": "Elias Pope",
    "Luria": "Luria",
    "Bernadette Wells": "Bernadette Wells", "Wells": "Bernadette Wells",
    "Jaya Chaudhary": "Jaya Chaudhary", "Chaudhary": "Jaya Chaudhary",
    "Shamus Madigan": "Shamus Madigan", "Professor Shamus Madigan": "Shamus Madigan", "Madigan": "Shamus Madigan",
    "Klaus-Peter Sonnek": "Klaus-Peter Sonnek", "Dr Klaus-Peter Sonnek": "Klaus-Peter Sonnek", "Sonnek": "Klaus-Peter Sonnek",
    "Remy Leroux": "Remy Leroux", "Dr Remy Leroux": "Remy Leroux", "Leroux": "Remy Leroux",
    "Nadia Machado": "Nadia Machado", "Governor Nadia Machado": "Nadia Machado", "Machado": "Nadia Machado",
    "Nikolas Glass": "Nikolas Glass", "Admiral Nikolas Glass": "Nikolas Glass", "Glass": "Nikolas Glass",
    "Rachel Ziegler": "Rachel Ziegler", "Admiral Rachel Ziegler": "Rachel Ziegler", "Ziegler": "Rachel Ziegler",
    "Maxton Price": "Maxton Price", "Admiral Maxton Price": "Maxton Price", "Price": "Maxton Price",
    "Juno Rochester": "Juno Rochester",
    "Isolde Rochester": "Isolde Rochester", "Shadow Vice President Isolde Rochester": "Isolde Rochester",
    "Liam Flanagan": "Liam Flanagan", "Admiral Liam Flanagan": "Liam Flanagan", "Flanagan": "Liam Flanagan",
    "George Varma": "George Varma", "Admiral George Varma": "George Varma", "Varma": "George Varma",
    "Maristela Silva": "Maristela Silva", "Admiral Maristela Silva": "Maristela Silva", "Silva": "Maristela Silva",
    "Tahir West": "Tahir West", "Admiral Tahir West": "Tahir West", "West": "Tahir West",
    "Hayley Sorokin": "Hayley Sorokin", "Fleet Admiral Hayley Sorokin": "Hayley Sorokin", "Sorokin": "Hayley Sorokin",
    "Edmund Mahon": "Edmund Mahon", "Prime Minister Edmund Mahon": "Edmund Mahon", "Mahon": "Edmund Mahon",
    "Nakato Kaine": "Nakato Kaine", "Councillor Nakato Kaine": "Nakato Kaine", "Kaine": "Nakato Kaine",
    "Alfred Ulyanov": "Alfred Ulyanov", "Dr Alfred Ulyanov": "Alfred Ulyanov", "Ulyanov": "Alfred Ulyanov",
    "Rani Zaman": "Rani Zaman", "Zaman": "Rani Zaman",
    "Ernesto Rios": "Ernesto Rios", "Rios": "Ernesto Rios",
    "Justine Kemp": "Justine Kemp", "Captain Justine Kemp": "Justine Kemp", "Kemp": "Justine Kemp",
    "Casey Kilpatrick": "Casey Kilpatrick", "Kilpatrick": "Casey Kilpatrick",
    "Bris Dekker": "Bris Dekker", "Colonel Bris Dekker": "Bris Dekker", "Dekker": "Bris Dekker",
    "Liz Ryder": "Liz Ryder", "Ryder": "Liz Ryder",
    "Zacariah Nemo": "Zacariah Nemo", "Nemo": "Zacariah Nemo",
    "Sandra Corrs": "Sandra Corrs", "Corrs": "Sandra Corrs",
    "Timothy Culver": "Timothy Culver", "Culver": "Timothy Culver",
    "Sima Kalhana": "Sima Kalhana", "Kalhana": "Sima Kalhana",
    "Archon Delaine": "Archon Delaine", "Delaine": "Archon Delaine",
    "Zachary Rackham": "Zachary Rackham", "Rackham": "Zachary Rackham",
    "Yaro Kenyatta": "Yaro Kenyatta", "Professor Yaro Kenyatta": "Yaro Kenyatta", "Kenyatta": "Yaro Kenyatta",
    "Lori Jameson": "Lori Jameson", "Jameson": "Lori Jameson",
    "Conrad Sterling": "Conrad Sterling", "Sterling": "Conrad Sterling",
    "Cassia Carvalho": "Cassia Carvalho", "Carvalho": "Cassia Carvalho",
    "Sofia Trevino": "Sofia Trevino", "Trevino": "Sofia Trevino",
    "Harrison Gladstone": "Harrison Gladstone", "Gladstone": "Harrison Gladstone",
    "Lewis Laychurch": "Lewis Laychurch", "Laychurch": "Lewis Laychurch",
    "First Apostle": "First Apostle",
    "President Hudson": "President Hudson", "Hudson": "President Hudson",
    "General Falkenrath": "General Falkenrath", "Falkenrath": "General Falkenrath",
}

# Ambiguous single names to drop
PERSON_BLOCKLIST = {"Rochester"}

# --- Group normalization ---
GROUP_NORMALIZATION = {
    "Sirius Corp": "Sirius Corporation",
    "Canonn Interstellar Research Group": "Canonn",
    "The Federal Times": "Federal Times",
    "The Imperial Herald": "Imperial Herald",
    "The Alliance Tribune": "Alliance Tribune",
    "The Old Worlds Gazette": "Old Worlds Gazette",
    "The Marlin Standard": "Marlin Standard",
    "The Sol Today": "Sol Today",
    "The Citizens' Chronicle": "Citizens' Chronicle",
    "The Federal Free Press": "Federal Free Press",
}

# --- Locations to remove ---
LOCATION_REMOVALS = {
    "Aegis", "Azimuth", "Thargoid", "Thargoids", "Titan", "Maelstrom",
    "Thargoid-tainted", "Guardian",
    "A total of 16", "Federation ALERT", "Nine", "Six populated",
    "Many", "Several", "Multiple inhabited", "A further 13",
    "Virtually everything in some of these", "Thargoid-occupied",
    "Why would they care which", "But many independent",
    "Newsfeeds across the core", "Colleagues across multiple",
    "Protests in", "Following recent attacks on",
    "Thargoids have again sought to occupy", "With access to the",
    "The aliens withdrew from the", "Thargoids have placed entire",
    "Populated", "Many more inhabited", "A total of 16 neighbouring",
    "Other inhabited", "HIP 22460 was the", "Novas and Sosong", "Full spectrum",
    "Professor Palin", "Lori Jameson", "Liz Ryder", "Zacariah Nemo", "Ram Tah",
    "Dr Palin", "Dr Ishmael Palin", "Professor Ram Tah", "Dr Ram Tah", "Ms Seo",
    "Dr Elias Pope", "Dr Remy Leroux", "Dr Caleb Wycherley", "Dr Klaus-Peter Sonnek",
    "Dr Alfred Ulyanov", "Dr Mia Valencourt", "Dr Yazhu Xing", "Dr Carter Armstrong",
    "Dr Allan Mantle",
    "Federal or independent", "Allied and independent",
}

# --- Topics to remove ---
TOPIC_REMOVALS = {"ship", "sport", "trade", "construction", "medicine", "safety", "treasure hunt"}

# --- Helper: split frontmatter ---
def split_frontmatter(text):
    if text.startswith('---'):
        end = text.find('---', 3)
        if end != -1:
            return text[3:end].strip(), text[end+3:].strip()
    return None, text.strip()

# --- Helper: clean entity ---
def clean_entity(e):
    if not isinstance(e, str):
        return None
    words = e.split()
    kept = []
    allowed = {'of', 'the', 'and', 'for', 'in', 'de', 'van', 'der'}
    for w in words:
        w_clean = w.strip('.,;:!?')
        if not w_clean:
            continue
        if w_clean[0].isupper() or (w_clean.lower() in allowed and kept):
            kept.append(w)
        else:
            break
    if not kept:
        return None
    return ' '.join(kept)

# --- Helper: is person ---
def is_person(name):
    if name in VARIANT_TO_CANONICAL:
        return True
    if name in PERSON_BLOCKLIST:
        return False
    words = name.split()
    if len(words) >= 2 and all(w[0].isupper() for w in words):
        return True
    return False

# --- Helper: find persons in text ---
def find_persons_in_text(text):
    found = set()
    for name in sorted(VARIANT_TO_CANONICAL.keys(), key=lambda x: -len(x)):
        escaped = re.escape(name)
        if re.search(r'\b' + escaped + r'\b', text):
            found.add(name)
    return sorted(found)

# --- Helper: extract first quote ---
def extract_first_quote(text):
    m = re.search(r'[\"“]([^\"”]+)[\"”]', text)
    if m:
        q = m.group(1).strip()
        if len(q) > 10:
            return q
    return None

# --- Helper: generate summary ---
def generate_summary(fm, body):
    body_clean = re.sub(r'\*\*', '', body)
    body_clean = re.sub(r'\*Pilots[’\'] Federation ALERT\*\s*', '', body_clean)
    sentences = re.split(r'(?<=[.!?])\s+', body_clean.strip())
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        if len(s) > 20:
            return s
    return fm.get('title', '') + '.'

# --- Helper: generate player_impact ---
def generate_player_impact(body):
    body_lower = body.lower()
    has_genetic = any(k in body_lower for k in ['genetic data', 'genetic sampler', 'exobiology data'])
    has_delivery = any(k in body_lower for k in ['deliveries', 'commodities', 'computer components', 'semiconductors', 'titanium', 'supplies', 'materials required', 'basic medicines', 'fruit and vegetables', 'shipment'])
    has_combat = any(k in body_lower for k in ['combat bonds', 'bounty', 'destroy thargoid', 'engage thargoid', 'combat vouchers', 'xeno-hunters', 'ax weapon', 'ax multi-cannon', 'ax missile', 'overcharged guardian plasma charger', 'phasing sequence'])
    has_alert = "pilots’ federation alert" in body_lower or "pilots federation alert" in body_lower

    parts = []
    if has_genetic:
        parts.append("collect and submit genetic data samples")
    if has_delivery:
        parts.append("deliver commodities")
    if has_combat:
        parts.append("engage hostile forces")

    if len(parts) == 2:
        return f"Independent pilots were asked to both {parts[0]} and {parts[1]}."
    elif len(parts) == 3:
        return f"Independent pilots were asked to {parts[0]}, {parts[1]}, and {parts[2]}."
    elif len(parts) == 1:
        actions = {
            "collect and submit genetic data samples": "Independent pilots were encouraged to collect and submit genetic data samples.",
            "deliver commodities": "Independent pilots were tasked with delivering commodities to support the operation.",
            "engage hostile forces": "Independent pilots were called upon to destroy Thargoid vessels and claim combat bonds.",
        }
        return actions.get(parts[0], f"Independent pilots were asked to {parts[0]}.")
    elif has_alert:
        return "Independent pilots were encouraged to participate in the unfolding events."
    else:
        return "This article focuses on political and strategic developments without direct pilot involvement."

# --- Helper: generate modern_impact ---
def generate_modern_impact(fm, body):
    quote = extract_first_quote(body)
    title = fm.get('title', '')
    if not quote:
        quote = generate_summary(fm, body)
    if len(quote) > 120:
        quote = quote[:117] + "..."

    if 'aegis' in title.lower():
        commentary = "This call for collaboration continues to resonate in discussions about superpower unity against the Thargoids."
    elif 'azimuth' in title.lower() or 'salvation' in title.lower():
        commentary = "Azimuth's legacy of ethically compromised research remains a cautionary tale in xenological studies."
    elif 'kingfisher' in title.lower() or 'xeno-peace' in title.lower():
        commentary = "The failure of civilian-led diplomacy underscores the dangers of underestimating Thargoid hostility."
    elif 'maelstrom' in title.lower():
        commentary = "The relentless expansion of Thargoid forces redefined the scale of the Second Thargoid War."
    elif 'taranis' in title.lower():
        commentary = "Taranis heralded a new phase of total war that humanity was ill-prepared to resist."
    elif 'weapon' in title.lower():
        commentary = "Upgrading AX weaponry remains a critical priority for independent pilots on the front lines."
    elif 'empire' in title.lower() or 'imperial' in title.lower():
        commentary = "Imperial policy during this period reveals the tensions between isolationism and collective security."
    elif 'federation' in title.lower() or 'federal' in title.lower():
        commentary = "Federal political maneuvering illustrates the struggle to balance civil liberties with wartime imperatives."
    elif 'retrospective' in title.lower():
        commentary = "Looking back, the events of 3308 set the stage for the protracted conflict that followed."
    else:
        commentary = "This perspective highlights the broader stakes and continues to shape contemporary debates."

    return f'"{quote}" {commentary}'

# --- Load all files ---
files = []
for d in DIRECTORIES:
    for f in sorted(os.listdir(d)):
        if f.endswith('.md'):
            path = os.path.join(d, f)
            with open(path, 'r') as fh:
                content = fh.read()
            fm_str, body = split_frontmatter(content)
            if fm_str is None:
                continue
            try:
                fm = yaml.safe_load(fm_str)
            except Exception as e:
                print(f"YAML error in {path}: {e}")
                continue
            files.append({
                'path': path,
                'content': content,
                'fm': fm,
                'body': body,
                'fm_str': fm_str,
            })

# --- Pre-calculate cleaned fields for related_uuids similarity ---
for f in files:
    fm = f['fm']
    f['arc'] = fm.get('arc_id') if fm.get('arc_id') in VALID_ARCS else None
    f['persons_set'] = set()
    f['groups_set'] = set()
    f['locs_set'] = set()
    f['topics_set'] = set()
    for e in fm.get('entities', []):
        c = clean_entity(e)
        if c and is_person(c):
            f['persons_set'].add(c)
    for g in fm.get('groups', []):
        if isinstance(g, str):
            f['groups_set'].add(g)
    for l in fm.get('locations', []):
        if isinstance(l, str):
            f['locs_set'].add(l)
    for t in fm.get('topics', []):
        if isinstance(t, str):
            f['topics_set'].add(t)

# --- Process each file ---
for f in files:
    fm = f['fm']
    body = f['body']
    path = f['path']

    # arc_id
    current_arc = fm.get('arc_id')
    if current_arc in VALID_ARCS:
        new_arc = current_arc
    else:
        new_arc = None
    fm['arc_id'] = new_arc

    # persons: cleaned entities + text scan
    persons_from_entities = set()
    moved = False
    for e in fm.get('entities', []):
        c = clean_entity(e)
        if c and is_person(c):
            persons_from_entities.add(c)
            moved = True

    if moved:
        fm['entities'] = []
    elif fm.get('persons') or fm.get('entities') == []:
        fm['entities'] = []
    elif 'entities' in fm:
        del fm['entities']

    persons_from_text = set(find_persons_in_text(body))
    all_persons = sorted(persons_from_entities | persons_from_text)

    # normalize and deduplicate
    canonical = set()
    for p in all_persons:
        c = VARIANT_TO_CANONICAL.get(p, p)
        if c in PERSON_BLOCKLIST:
            continue
        canonical.add(c)
    all_persons = sorted(canonical)

    if all_persons:
        fm['persons'] = all_persons
    elif 'persons' in fm:
        del fm['persons']

    # groups: clean and normalize
    raw_groups = fm.get('groups', [])
    cleaned_groups = []
    seen_groups = set()
    removals = {'act', 'thargoid', 'thargoids', 'shadow president', 'pilots federation', 'pilots’ federation'}
    for g in raw_groups:
        if not isinstance(g, str):
            continue
        gl = g.lower().strip()
        if gl in removals:
            continue
        normalized = GROUP_NORMALIZATION.get(g, g)
        nl = normalized.lower().strip()
        if nl in seen_groups:
            continue
        seen_groups.add(nl)
        cleaned_groups.append(normalized)
    if cleaned_groups:
        fm['groups'] = cleaned_groups
    elif 'groups' in fm:
        del fm['groups']

    # locations: clean
    raw_locs = fm.get('locations', [])
    cleaned_locs = []
    seen_locs = set()
    for l in raw_locs:
        if not isinstance(l, str):
            continue
        if l in LOCATION_REMOVALS:
            continue
        ll = l.lower().strip()
        if ll in seen_locs:
            continue
        seen_locs.add(ll)
        cleaned_locs.append(l)
    if cleaned_locs:
        fm['locations'] = cleaned_locs
    elif 'locations' in fm:
        del fm['locations']

    # topics: clean
    raw_topics = fm.get('topics', [])
    cleaned_topics = []
    seen_topics = set()
    for t in raw_topics:
        if not isinstance(t, str):
            continue
        tl = t.lower().strip()
        if tl in TOPIC_REMOVALS:
            continue
        if tl in seen_topics:
            continue
        seen_topics.add(tl)
        cleaned_topics.append(t)
    if cleaned_topics:
        fm['topics'] = cleaned_topics
    elif 'topics' in fm:
        del fm['topics']

    # summary
    fm['summary'] = generate_summary(fm, body)

    # player_impact
    fm['player_impact'] = generate_player_impact(body)

    # modern_impact
    fm['modern_impact'] = generate_modern_impact(fm, body)

    # related_uuids
    similarities = []
    for other in files:
        if other['path'] == path:
            continue
        score = 0
        if f['arc'] and other['arc'] == f['arc']:
            score += 5
        score += len(f['persons_set'] & other['persons_set'])
        score += len(f['groups_set'] & other['groups_set'])
        score += len(f['locs_set'] & other['locs_set'])
        score += len(f['topics_set'] & other['topics_set'])
        if score > 0:
            similarities.append((score, other['fm']['uuid']))
    similarities.sort(reverse=True)
    related = [uuid for _, uuid in similarities[:5]]
    if related:
        fm['related_uuids'] = related
    elif 'related_uuids' in fm:
        del fm['related_uuids']

    # Reconstruct frontmatter with nice order
    field_order = [
        'uuid', 'title', 'slug', 'date', 'source',
        'arc_id', 'persons', 'groups', 'locations', 'topics',
        'player_impact', 'summary', 'modern_impact', 'related_uuids',
        'legacy_weight', 'significance'
    ]
    ordered_fm = {}
    for key in field_order:
        if key in fm:
            ordered_fm[key] = fm[key]
    for key, val in fm.items():
        if key not in ordered_fm:
            ordered_fm[key] = val

    new_fm_str = yaml.safe_dump(ordered_fm, default_flow_style=False, sort_keys=False, allow_unicode=True)
    new_fm_str = new_fm_str.strip()
    new_content = f"---\n{new_fm_str}\n---\n\n{body}\n"

    with open(path, 'w') as fh:
        fh.write(new_content)

print(f"Processed {len(files)} files.")
