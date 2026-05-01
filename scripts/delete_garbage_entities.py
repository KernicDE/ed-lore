#!/usr/bin/env python3
"""Delete obvious garbage entities created by bad automated extraction."""

import yaml
from pathlib import Path

ENTITIES_DIR = Path("Entities")

GARBAGE_SUFFIXES = [
    'gave', 'told', 'made', 'held', 'said', 'claimed', 'confirmed',
    'argued', 'ordered', 'demanded', 'announced', 'revealed',
    'provided', 'explained', 'added', 'continued', 'insisted',
    'proposed', 'agreed', 'declared', 'stated', 'commented',
    'warned', 'advised', 'noted', 'remarked', 'concluded',
    'responded', 'replied', 'asked', 'questioned', 'suggested',
    'emphasised', 'acknowledged', 'dismissed', 'criticised',
    'praised', 'condemned', 'welcomed', 'rejected', 'accepted',
    'promised', 'threatened', 'offered', 'invited', 'urged',
    'called', 'described', 'referred', 'considered', 'believed',
    'expected', 'hoped', 'feared', 'reported',
    'asserted', 'maintained', 'contended',
    'observed', 'recalled', 'remembered', 'admitted',
    'denied', 'recognised', 'understood',
    'knew', 'learned', 'discovered', 'found', 'showed',
    'demonstrated', 'proved', 'indicated',
    'implied', 'summarised', 'outlined', 'detailed', 'listed',
]

GARBAGE_EXACT = {
    'the', 'with', 'but', 'and', 'for', 'from', 'that', 'this', 'these', 'those',
    'when', 'where', 'what', 'who', 'why', 'how', 'which', 'whose', 'whom',
    'its', 'it', 'he', 'she', 'they', 'them', 'their', 'his', 'her', 'him',
    'we', 'us', 'our', 'you', 'your', 'i', 'me', 'my', 'mine',
    'a', 'an', 'all', 'any', 'both', 'each', 'either', 'neither', 'none',
    'some', 'many', 'much', 'more', 'most', 'other', 'another', 'such',
    'no', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very',
    'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten',
    'can', 'will', 'shall', 'may', 'might', 'must', 'should', 'would', 'could',
    'do', 'does', 'did', 'done', 'doing', 'have', 'has', 'had', 'having',
    'be', 'been', 'being', 'am', 'is', 'are', 'was', 'were',
    'go', 'goes', 'going', 'went', 'gone',
    'get', 'gets', 'getting', 'got', 'gotten',
    'take', 'takes', 'taking', 'took', 'taken',
    'come', 'comes', 'coming', 'came',
    'see', 'sees', 'seeing', 'saw', 'seen',
    'know', 'knows', 'knowing', 'knew', 'known',
    'think', 'thinks', 'thinking', 'thought',
    'use', 'uses', 'using', 'used',
    'find', 'finds', 'finding', 'found',
    'give', 'gives', 'giving', 'given',
    'tell', 'tells', 'telling', 'told',
    'become', 'becomes', 'becoming', 'became',
    'leave', 'leaves', 'leaving', 'left',
    'feel', 'feels', 'feeling', 'felt',
    'put', 'puts', 'putting',
    'bring', 'brings', 'bringing', 'brought',
    'begin', 'begins', 'beginning', 'began', 'begun',
    'keep', 'keeps', 'keeping', 'kept',
    'hold', 'holds', 'holding',
    'write', 'writes', 'writing', 'wrote', 'written',
    'stand', 'stands', 'standing', 'stood',
    'hear', 'hears', 'hearing', 'heard',
    'let', 'lets', 'letting',
    'mean', 'means', 'meaning', 'meant',
    'set', 'sets', 'setting',
    'meet', 'meets', 'meeting', 'met',
    'run', 'runs', 'running', 'ran',
    'pay', 'pays', 'paying', 'paid',
    'sit', 'sits', 'sitting', 'sat',
    'speak', 'speaks', 'speaking', 'spoke', 'spoken',
    'lie', 'lies', 'lying', 'lay', 'lain',
    'lead', 'leads', 'leading', 'led',
    'read', 'reads', 'reading',
    'grow', 'grows', 'growing', 'grew', 'grown',
    'lose', 'loses', 'losing', 'lost',
    'fall', 'falls', 'falling', 'fell', 'fallen',
    'send', 'sends', 'sending', 'sent',
    'build', 'builds', 'building', 'built',
    'understand', 'understands', 'understanding', 'understood',
    'draw', 'draws', 'drawing', 'drew', 'drawn',
    'break', 'breaks', 'breaking', 'broke', 'broken',
    'spend', 'spends', 'spending', 'spent',
    'cut', 'cuts', 'cutting',
    'rise', 'rises', 'rising', 'rose', 'risen',
    'drive', 'drives', 'driving', 'drove', 'driven',
    'buy', 'buys', 'buying', 'bought',
    'wear', 'wears', 'wearing', 'wore', 'worn',
    'choose', 'chooses', 'choosing', 'chose', 'chosen',
    'seek', 'seeks', 'seeking', 'sought',
}


def is_garbage(entity_id):
    eid = entity_id.lower().strip()
    if eid in GARBAGE_EXACT:
        return True
    for suffix in GARBAGE_SUFFIXES:
        if eid.endswith('-' + suffix) or eid == suffix:
            return True
    for prefix in ['with-', 'but-', 'and-', 'for-', 'from-', 'that-', 'this-', 'these-', 'those-', 'when-', 'where-', 'what-', 'who-', 'why-', 'how-', 'which-', 'whose-', 'whom-', 'the-', 'a-', 'an-', 'as-', 'by-', 'on-', 'in-', 'at-', 'to-', 'of-', 'off-', 'up-', 'out-', 'down-', 'over-', 'under-', 'through-', 'during-', 'before-', 'after-', 'above-', 'below-', 'between-', 'among-', 'within-', 'without-', 'against-', 'toward-', 'towards-', 'across-', 'around-', 'behind-', 'beyond-', 'except-', 'inside-', 'into-', 'near-', 'onto-', 'outside-', 'upon-', 'via-', 'worth-']:
        if eid.startswith(prefix):
            return True
    for frag in ['the-following', 'following-the', 'news-is', 'is-coming', 'reports-from', 'sources-close', 'close-to', 'according-to', 'spokesperson-for', 'representative-of', 'officials-in', 'authorities-in', 'forces-in', 'fleet-in', 'station-in', 'system-in']:
        if frag in eid:
            return True
    return False


def main():
    deleted = 0
    kept = 0
    for subdir in ENTITIES_DIR.iterdir():
        if not subdir.is_dir():
            continue
        for md_file in subdir.glob("*.md"):
            entity_id = md_file.stem
            if is_garbage(entity_id):
                md_file.unlink()
                deleted += 1
            else:
                kept += 1
    print(f"Deleted {deleted} garbage entities")
    print(f"Kept {kept} entities")


if __name__ == "__main__":
    main()
