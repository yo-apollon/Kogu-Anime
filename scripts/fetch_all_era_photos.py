import json
import os
import re
import sys
import time
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

os.makedirs(".cache/era_photos", exist_ok=True)

with open("docs/catalog.json") as f:
    cards = json.load(f)

anchors = [c for c in cards if c.get("edition") == "BASIC"]
print(f"Total BASIC anchors: {len(anchors)}")

WIKI_HEADERS = {"User-Agent": "KoguBot/1.0 (kogu@example.com)"}
SAFEBOORU_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def clean_name_for_search(name):
    # Remove subtitles in parentheses e.g. "Darth Vader (Lorde Sith)" -> "Darth Vader"
    c = re.sub(r'\s*\(.*?\)\s*', ' ', name).strip()
    return c

def fetch_image_bytes(url, min_size=4000):
    try:
        if url.startswith("//"):
            url = "https:" + url
        req = urllib.request.Request(url, headers=SAFEBOORU_HEADERS)
        data = urllib.request.urlopen(req, timeout=8).read()
        if len(data) >= min_size:
            return data
    except Exception:
        pass
    return None

def get_safebooru_images(char_name, series=""):
    clean = clean_name_for_search(char_name).lower()
    # Tag heuristics
    tag_candidates = [
        clean.replace(" ", "_"),
    ]
    parts = clean.split()
    if len(parts) == 2:
        tag_candidates.append(f"{parts[1]}_{parts[0]}") # Japanese surname order
    
    for tag in tag_candidates:
        url = f"https://safebooru.org/index.php?page=dapi&s=post&q=index&json=1&tags={urllib.parse.quote(tag)}+solo&limit=8"
        try:
            req = urllib.request.Request(url, headers=SAFEBOORU_HEADERS)
            data = json.loads(urllib.request.urlopen(req, timeout=5).read().decode('utf-8'))
            imgs = []
            for d in data:
                d_dir = d.get("directory")
                d_img = d.get("image")
                if d_dir is not None and d_img and not d_img.endswith('.mp4'):
                    imgs.append(f"https://safebooru.org/images/{d_dir}/{d_img}")
            if len(imgs) >= 2:
                return imgs
        except Exception:
            continue
    return []

def get_wiki_images(query):
    try:
        # Search Wikipedia
        s_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(query)}&srlimit=1&format=json"
        req = urllib.request.Request(s_url, headers=WIKI_HEADERS)
        s_data = json.loads(urllib.request.urlopen(req, timeout=5).read().decode('utf-8'))
        results = s_data.get("query", {}).get("search", [])
        if not results:
            return []
        page_title = results[0]["title"].replace(" ", "_")

        # Media list
        m_url = f"https://en.wikipedia.org/api/rest_v1/page/media-list/{urllib.parse.quote(page_title)}"
        req2 = urllib.request.Request(m_url, headers=WIKI_HEADERS)
        m_data = json.loads(urllib.request.urlopen(req2, timeout=5).read().decode('utf-8'))
        imgs = []
        for item in m_data.get("items", []):
            if item.get("type") == "image":
                src = item.get("srcset", [{}])[-1].get("src")
                if src and not src.endswith('.svg') and not 'icon' in src.lower() and not 'map' in src.lower():
                    full_src = "https:" + src if src.startswith("//") else src
                    imgs.append(full_src)
        return imgs
    except Exception:
        return []

def get_commons_images(query):
    try:
        url = f"https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrsearch={urllib.parse.quote(query)}&gsrnamespace=6&gsrlimit=10&prop=imageinfo&iiprop=url|size&format=json"
        req = urllib.request.Request(url, headers=WIKI_HEADERS)
        data = json.loads(urllib.request.urlopen(req, timeout=5).read().decode('utf-8'))
        pages = data.get("query", {}).get("pages", {})
        imgs = []
        for p in pages.values():
            infos = p.get("imageinfo", [])
            if infos:
                u = infos[0].get("url")
                size = infos[0].get("size", 0)
                if u and (u.endswith('.jpg') or u.endswith('.png') or u.endswith('.jpeg')) and size > 20000:
                    imgs.append(u)
        return imgs
    except Exception:
        return []

def process_anchor(c):
    slug = c['slug']
    epic_path = f".cache/era_photos/{slug}-epic.jpg"
    mythic_path = f".cache/era_photos/{slug}-mythic.jpg"
    base_asset = f"docs/assets/cards/{slug}.jpg"
    base_data = None
    if os.path.exists(base_asset):
        try:
            with open(base_asset, "rb") as bf:
                base_data = bf.read()
        except Exception:
            pass

    has_epic = os.path.exists(epic_path) and os.path.getsize(epic_path) > 3000
    has_mythic = os.path.exists(mythic_path) and os.path.getsize(mythic_path) > 3000
    if has_epic and has_mythic:
        return True

    niche = c.get('niche') or ''
    name = c.get('name') or ''
    clean_name = clean_name_for_search(name)
    series = c.get('seriesTitle') or ''

    candidate_urls = []
    if niche == 'anime':
        candidate_urls = get_safebooru_images(name, series)

    if len(candidate_urls) < 2:
        # Tenta Wikipedia
        wiki_imgs = get_wiki_images(f"{clean_name} {series}".strip())
        if not wiki_imgs:
            wiki_imgs = get_wiki_images(clean_name)
        candidate_urls.extend(wiki_imgs)

    if len(candidate_urls) < 2:
        # Tenta Wikimedia Commons
        commons_imgs = get_commons_images(clean_name)
        candidate_urls.extend(commons_imgs)

    saved_epic = has_epic
    saved_mythic = has_mythic

    for u in candidate_urls:
        if saved_epic and saved_mythic:
            break
        data = fetch_image_bytes(u)
        if not data:
            continue
        if base_data and data == base_data:
            continue
        if not saved_epic:
            with open(epic_path, "wb") as out:
                out.write(data)
            saved_epic = True
        elif not saved_mythic:
            with open(epic_path, "rb") as f_ep:
                if f_ep.read() == data:
                    continue
            with open(mythic_path, "wb") as out:
                out.write(data)
            saved_mythic = True

    return saved_epic and saved_mythic

if __name__ == "__main__":
    count = 0
    with ThreadPoolExecutor(max_workers=8) as ex:
        results = list(ex.map(process_anchor, anchors))
    
    ready = sum(1 for r in results if r)
    print(f"Era photos download complete: {ready}/{len(anchors)} anchors ready.")
