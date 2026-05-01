#!/usr/bin/env python3
"""Generate biographical descriptions for entities by analyzing their articles."""
import json
import re
from pathlib import Path
import yaml

BASE_DIR = Path(__file__).parent.parent
with open(BASE_DIR / 'lore_graph.json') as f:
    graph = json.load(f)

def make_eid(name: str) -> str:
    return ''.join(c for c in name.lower().replace(' ', '-').replace('/', '-').replace("'", '').replace('.', '') if c.isalnum() or c == '-')

entity_articles = {}
for art in graph['articles']:
    all_ents = set(art.get('entities', []) + art.get('groups', []) + art.get('locations', []) + 
                   art.get('persons', []) + art.get('technologies', []))
    for name in all_ents:
        eid = make_eid(name)
        entity_articles.setdefault(eid, []).append(art)

cooccurrence = {}
for art in graph['articles']:
    eids = [make_eid(n) for n in set(art.get('entities', []) + art.get('groups', []) + art.get('locations', []) + 
                                     art.get('persons', []) + art.get('technologies', []))]
    for i, a in enumerate(eids):
        for b in eids[i+1:]:
            if a == b: continue
            cooccurrence.setdefault(a, {}).setdefault(b, 0)
            cooccurrence.setdefault(b, {}).setdefault(a, 0)
            cooccurrence[a][b] += 1
            cooccurrence[b][a] += 1

def get_top_coentities(eid, exclude=None, n=5):
    exclude = set(exclude or [])
    rel = cooccurrence.get(eid, {})
    sorted_rel = sorted(rel.items(), key=lambda x: -x[1])
    result = []
    for rid, count in sorted_rel:
        if rid in exclude: continue
        rec = graph['entities'].get(rid)
        if rec:
            result.append((rec['name'], rec['type'], count))
        if len(result) >= n:
            break
    return result

def pick_best_sentences(arts, entity_name, max_sentences=2):
    """Pick sentences from article summaries that actually mention the entity."""
    name_lower = entity_name.lower()
    # Also check common variations
    name_parts = name_lower.split()
    sentences = []
    seen = set()
    
    for art in sorted(arts, key=lambda a: -(a.get('legacy_weight', 2) * 10 + 
                                             (3 if a.get('significance') == 'high' else 
                                              2 if a.get('significance') == 'medium' else 1))):
        summary = art.get('summary', '')
        if not summary or len(summary) < 20:
            continue
        # Split into sentences
        for sent in re.split(r'(?<=[.!?])\s+', summary):
            sent = sent.strip()
            if len(sent) < 30 or len(sent) > 200:
                continue
            # Check if sentence mentions entity
            sent_lower = sent.lower()
            if name_lower in sent_lower:
                key = sent_lower[:60]
                if key not in seen:
                    sentences.append(sent)
                    seen.add(key)
            elif any(part in sent_lower for part in name_parts if len(part) > 3):
                key = sent_lower[:60]
                if key not in seen:
                    sentences.append(sent)
                    seen.add(key)
        if len(sentences) >= max_sentences + 3:
            break
    
    return sentences[:max_sentences]

def detect_role(arts, entity_name):
    name_lower = entity_name.lower()
    role_hints = {
        'emperor': ['emperor', 'empress'],
        'president': ['president'],
        'senator': ['senator'],
        'admiral': ['admiral'],
        'commander': ['commander'],
        'ceo': ['ceo', 'chief executive'],
        'engineer': ['engineer'],
        'scientist': ['scientist', 'researcher', 'professor'],
        'pirate': ['pirate', 'piracy', 'pirate king'],
        'terrorist': ['terrorist', 'terrorism'],
        'diplomat': ['ambassador', 'diplomat'],
        'journalist': ['journalist', 'reporter'],
        'pilot': ['pilot', 'commander'],
    }
    scores = {}
    for art in arts:
        title = art.get('title', '').lower()
        summary = art.get('summary', '').lower()
        text = title + ' ' + summary
        for role, keywords in role_hints.items():
            for kw in keywords:
                if kw in text:
                    scores[role] = scores.get(role, 0) + 1
    if scores:
        best = max(scores.items(), key=lambda x: x[1])
        if best[1] > 0:
            return best[0]
    return None

def generate_bio(eid, rec):
    name = rec['name']
    etype = rec.get('type', 'person')
    first = rec.get('first_seen_date', '')
    last = rec.get('last_seen_date', '')
    arts = entity_articles.get(eid, [])
    if not arts:
        return None
    
    coents = get_top_coentities(eid, n=5)
    sentences = pick_best_sentences(arts, name, max_sentences=2)
    
    if etype == 'person':
        role = detect_role(arts, name)
        role_text = role.replace('_', ' ') if role else "prominent figure"
        factions = [n for n, t, c in coents if t == 'faction'][:3]
        
        bio = f"{name} is a {role_text} in the Elite Dangerous universe"
        if first and last:
            bio += f", active from {first} to {last}"
        bio += ". "
        if factions:
            bio += f"Closely associated with {', '.join(factions)}. "
        if sentences:
            bio += ' '.join(sentences)
        return bio
    
    elif etype == 'faction':
        faction_type = "organization"
        type_hints = {
            'naval': ['navy', 'naval', 'military', 'fleet', 'marine'],
            'corporate': ['corporation', 'corp', 'company', 'enterprise', 'incorporated'],
            'government': ['government', 'council', 'assembly', 'senate', 'congress', 'parliament'],
            'criminal': ['pirate', 'syndicate', 'gang', 'crew', 'cartel', 'mafia'],
            'research': ['research', 'scientific', 'institute', 'university', 'laboratory'],
            'media': ['times', 'herald', 'press', 'network', 'news', 'galnet'],
            'religious': ['cult', 'church', 'order', 'faith', 'temple'],
            'medical': ['medical', 'hospital', 'clinic'],
        }
        name_lower = name.lower()
        for ft, hints in type_hints.items():
            if any(h in name_lower for h in hints):
                faction_type = ft
                break
        
        allies = [n for n, t, c in coents if t in ('faction', 'location')][:3]
        
        bio = f"{name} is a {faction_type} in the Elite Dangerous universe"
        if first and last:
            bio += f", active from {first} to {last}"
        bio += ". "
        if allies:
            bio += f"Frequently linked with {', '.join(allies)}. "
        if sentences:
            bio += ' '.join(sentences)
        return bio
    
    elif etype == 'location':
        loc_type = "star system"
        if any(w in name.lower() for w in ['station', 'orbital', 'dock', 'port']):
            loc_type = "starport"
        elif any(w in name.lower() for w in ['nebula', 'cluster']):
            loc_type = "region"
        elif any(w in name.lower() for w in ['base', 'outpost', 'settlement']):
            loc_type = "outpost"
        
        factions_here = [n for n, t, c in coents if t == 'faction'][:3]
        
        bio = f"{name} is a {loc_type} in the Elite Dangerous universe"
        if first and last:
            bio += f", significant from {first} to {last}"
        bio += ". "
        if factions_here:
            bio += f"Associated with {', '.join(factions_here)}. "
        if sentences:
            bio += ' '.join(sentences)
        return bio
    
    elif etype == 'technology':
        users = [n for n, t, c in coents if t in ('faction', 'person')][:3]
        
        bio = f"{name} is a technology in the Elite Dangerous universe"
        if first and last:
            bio += f", mentioned from {first} to {last}"
        bio += ". "
        if users:
            bio += f"Developed or used by {', '.join(users)}. "
        if sentences:
            bio += ' '.join(sentences)
        return bio
    
    return None


ENTITIES_DIR = BASE_DIR / "Entities"
updated = 0
skipped = 0

# Process all entities, but focus on top 1000
top_entities = sorted(graph['entities'].items(), key=lambda x: -x[1].get('mention_count', 0))[:1000]

for eid, rec in top_entities:
    subdir = ENTITIES_DIR / rec.get('type', 'person')
    path = subdir / f"{eid}.md"
    if not path.exists():
        continue
    
    text = path.read_text(encoding='utf-8')
    if not text.startswith('---'):
        continue
    parts = text.split('---', 2)
    if len(parts) < 3:
        continue
    
    try:
        fm = yaml.safe_load(parts[1].strip()) or {}
    except Exception:
        continue
    
    body = parts[2]
    
    # Skip if already has substantial bio
    bio_content = body.split('## Biography')[1] if '## Biography' in body else ''
    if '*[To be enriched]*' not in bio_content and len(bio_content.strip()) > 100:
        skipped += 1
        continue
    
    bio = generate_bio(eid, rec)
    if not bio:
        continue
    
    # Replace in body
    if '*[To be enriched]*' in body:
        new_body = body.replace('*[To be enriched]*', bio)
    elif '## Biography' in body:
        # Insert after Biography heading
        new_body = re.sub(r'(## Biography\n\n)(\S|$)', f'\\1{bio}\n\n\\2', body)
    else:
        new_body = body + f"\n\n## Biography\n\n{bio}\n"
    
    yaml_text = yaml.dump(fm, default_flow_style=False, sort_keys=False, allow_unicode=True)
    new_text = f"---\n{yaml_text}---{new_body}"
    path.write_text(new_text, encoding='utf-8')
    updated += 1

print(f"Updated: {updated}, Skipped (already enriched): {skipped}")
