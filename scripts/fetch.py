import os
import re
import asyncio
import uuid
import yaml
import httpx
from datetime import datetime
from tqdm.asyncio import tqdm

# --- KONFIGURATION ---
BASE_DIR = "GalNet"
ED_YEAR_OFFSET = 1286
MAX_PARALLEL_TASKS = 15 
RETRIES = 3

JSON_API_URL = "https://cms.zaonce.net/en-GB/jsonapi/node/galnet_article?&sort=-published_at&page[limit]=50"
REPO_API_URL = "https://api.github.com/repos/elitedangereuse/LoreExplorer/contents/references/Galnet"
RAW_BASE_URL = "https://raw.githubusercontent.com/elitedangereuse/LoreExplorer/refs/heads/main/references/Galnet"

# --- HELPER ---
def slugify(text):
    """Erzeugt einen sauberen URL-konformen Namen."""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    return re.sub(r'[-\s]+', '_', text).strip('_')

def clean_github_title(filename, content):
    """
    Sucht den Titel im Dateiinhalt (#+TITLE:). 
    Falls nicht vorhanden, wird der Dateiname als Fallback gesäubert.
    """
    # Suche nach #+TITLE im Text (Case-insensitive, Multi-line)
    t_m = re.search(r'^\s*#\+TITLE:\s*(.*)$', content, re.MULTILINE | re.IGNORECASE)
    if t_m and t_m.group(1).strip():
        return t_m.group(1).strip().strip('"').strip("'")
    
    # Fallback: Dateiname säubern (z.B. 33010101-Underground_Racers.org)
    name = re.sub(r'^\d{8}-', '', filename) # Entfernt Datum am Anfang
    name = re.sub(r'\.org$', '', name, flags=re.IGNORECASE) # Entfernt Endung
    clean_name = name.replace('_', ' ').replace('-', ' ').strip()
    
    return clean_name if clean_name else "Untitled Article"

def generate_article_uuid(date_obj, title_en):
    """Erzeugt eine stabile, reproduzierbare UUID."""
    namespace = uuid.UUID('12345678-1234-5678-1234-567812345678')
    identifier = f"{date_obj.strftime('%Y%m%d')}-{title_en.lower().strip()}"
    return str(uuid.uuid5(namespace, identifier))

def _write_file(path, content):
    """Synchrone Schreiboperation für den Thread-Pool."""
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

# --- CORE PROCESSING ---
async def save_article(semaphore, date_obj, title, body, source):
    async with semaphore:
        year_real = date_obj.year
        year_ed = year_real + ED_YEAR_OFFSET
        date_ed_str = f"{year_ed}-{date_obj.strftime('%m-%d')}"
        master_slug = slugify(title)

        folder_name = f"{year_real}-{year_ed}"
        filename = f"{date_ed_str}-{master_slug}.md"
        full_dir = os.path.join(BASE_DIR, folder_name)
        full_path = os.path.join(full_dir, filename)

        # Ordner asynchron erstellen
        await asyncio.to_thread(os.makedirs, full_dir, exist_ok=True)

        uid = generate_article_uuid(date_obj, title)

        frontmatter = {
            "uuid": uid,
            "title": title,
            "slug": master_slug,
            "ed_date": date_ed_str,
            "lang": "en",
            "source": source
        }

        try:
            fm_text = yaml.safe_dump(frontmatter, allow_unicode=True, sort_keys=False)
            content = f"---\n{fm_text}---\n\n{body}"
            await asyncio.to_thread(_write_file, full_path, content)
            return full_path
        except Exception as e:
            print(f"Fehler beim Schreiben von {filename}: {e}")
            return None

# --- FETCHING ---
async def fetch_github_file(semaphore, client, file_info, year_ed):
    raw_name = file_info['name']
    # Extrahiert Datum (YYYYMMDD) aus dem Dateinamen
    d_str = raw_name.split('-')[0]
    try:
        date_obj = datetime(int(d_str[:4]) - ED_YEAR_OFFSET, int(d_str[4:6]), int(d_str[6:8]))
    except:
        return None

    for attempt in range(1, RETRIES + 1):
        try:
            res = await client.get(f"{RAW_BASE_URL}/{year_ed}/{raw_name}")
            if res.status_code == 200:
                content = res.text
                title = clean_github_title(raw_name, content)
                # Entfernt alle Zeilen mit Metadaten (#+TITLE, #+DATE, etc.)
                body = re.sub(r'^\s*#\+.*$', '', content, flags=re.MULTILINE | re.IGNORECASE).strip()
                
                path = await save_article(semaphore, date_obj, title, body, "GitHub")
                if path: return path

        except Exception as e:
            if attempt == RETRIES:
                print(f"Fehler bei {raw_name}: {e}")

        if attempt < RETRIES:
            await asyncio.sleep(1 * attempt) 

    return None

async def main():
    semaphore = asyncio.Semaphore(MAX_PARALLEL_TASKS)

    if not os.path.exists(BASE_DIR):
        os.makedirs(BASE_DIR)

    limits = httpx.Limits(max_keepalive_connections=10, max_connections=30)
    async with httpx.AsyncClient(timeout=30.0, limits=limits, follow_redirects=True) as client:

        # --- PHASE 1: GITHUB ---
        print("\n[1/2] Lade GitHub-Archiv (Historie)...")
        gh_tasks = []
        for year_ed in range(3300, 3307):
            try:
                r = await client.get(f"{REPO_API_URL}/{year_ed}")
                if r.status_code == 200:
                    files = [f for f in r.json() if f['name'].endswith('.org')]
                    for f_info in files:
                        gh_tasks.append(fetch_github_file(semaphore, client, f_info, year_ed))
                elif r.status_code == 403:
                    print(f"GitHub Rate Limit bei Jahr {year_ed} erreicht.")
                    break
            except Exception as e:
                print(f"Verbindung zu GitHub Jahr {year_ed} fehlgeschlagen: {e}")

        if gh_tasks:
            results = await tqdm.gather(*gh_tasks, desc="GitHub Archiv")
            print(f"-> GitHub: {len([r for r in results if r])} Dateien verarbeitet.")

        # --- PHASE 2: API ---
        print("\n[2/2] Lade Frontier API (Aktuell & Veredelung)...")
        api_tasks = []
        url = JSON_API_URL
        while url:
            try:
                r = await client.get(url)
                if r.status_code != 200: break
                data = r.json()
                for art in data.get('data', []):
                    attr = art['attributes']
                    date_obj = datetime.fromisoformat(attr['published_at'].replace('Z', '+00:00'))
                    body = re.sub('<[^<]+?>', '', attr['body']['value']).strip()
                    api_tasks.append(save_article(semaphore, date_obj, attr['title'], body, "API"))

                next_link = data.get('links', {}).get('next')
                url = next_link.get('href') if isinstance(next_link, dict) else next_link
                if not data.get('data'): break
            except: 
                break
        
        if api_tasks:
            results = await tqdm.gather(*api_tasks, desc="API Sync")
            print(f"-> API: {len([r for r in results if r])} Dateien verarbeitet/aktualisiert.")

    total_files = sum([len(files) for r, d, files in os.walk(BASE_DIR)])
    print(f"\n[FERTIG] Archiv enthält {total_files} Artikel.")

if __name__ == "__main__":
    asyncio.run(main())
