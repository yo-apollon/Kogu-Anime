import json
import os
import urllib.request
import urllib.parse
from scripts.fetch_all_era_photos import WIKI_HEADERS, SAFEBOORU_HEADERS, fetch_image_bytes

def get_commons_fixed(query):
    url = f"https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrsearch={urllib.parse.quote(query)}&gsrnamespace=6&gsrlimit=10&prop=imageinfo&iiprop=url|size&format=json"
    req = urllib.request.Request(url, headers=WIKI_HEADERS)
    try:
        data = json.loads(urllib.request.urlopen(req, timeout=5).read().decode('utf-8'))
        pages = data.get("query", {}).get("pages", {})
        imgs = []
        for p in pages.values():
            infos = p.get("imageinfo", [])
            if infos:
                u = infos[0].get("url")
                size = infos[0].get("size", 0)
                clean_u = u.lower().split('?')[0]
                if clean_u.endswith(('.jpg', '.jpeg', '.png')) and size > 20000:
                    imgs.append(u)
        return imgs
    except Exception:
        return []

def get_safebooru_direct(tag):
    url = f"https://safebooru.org/index.php?page=dapi&s=post&q=index&json=1&tags={urllib.parse.quote(tag)}&limit=8"
    req = urllib.request.Request(url, headers=SAFEBOORU_HEADERS)
    try:
        data = json.loads(urllib.request.urlopen(req, timeout=5).read().decode('utf-8'))
        imgs = []
        for d in data:
            d_dir = d.get("directory")
            d_img = d.get("image")
            if d_dir is not None and d_img and not d_img.endswith('.mp4'):
                imgs.append(f"https://safebooru.org/images/{d_dir}/{d_img}")
        return imgs
    except Exception:
        return []

def get_pt_wiki(title):
    url = f"https://pt.wikipedia.org/api/rest_v1/page/media-list/{urllib.parse.quote(title)}"
    req = urllib.request.Request(url, headers=WIKI_HEADERS)
    try:
        data = json.loads(urllib.request.urlopen(req, timeout=5).read().decode('utf-8'))
        imgs = []
        for item in data.get("items", []):
            if item.get("type") == "image":
                src = item.get("srcset", [{}])[-1].get("src")
                if src and not src.endswith('.svg') and not 'icon' in src.lower():
                    full_src = "https:" + src if src.startswith("//") else src
                    imgs.append(full_src)
        return imgs
    except Exception:
        return []

LAST_24_MAP = {
    # Anime
    "sukuna": ("safebooru", "sukuna_(jujutsu_kaisen)"),
    "emilia": ("safebooru", "emilia_(re:zero)"),
    "takumi-usui": ("safebooru", "usui_takumi"),
    "hak-son": ("safebooru", "son_hak"),
    "hirotaka-nifuji": ("safebooru", "nifuji_hirotaka"),
    "qifrey": ("safebooru", "qifrey"),
    "yorha-2-gou-b-gata": ("safebooru", "yorha_no._2_type_b"),
    "shirayuki": ("safebooru", "shirayuki_(akagami_no_shirayukihime)"),

    # Cinema / TV
    "neo-matrix": ("commons", "Keanu Reeves"),
    "john-wick-cinema": ("commons", "Keanu Reeves John Wick"),
    "black-widow-marvel": ("commons", "Scarlett Johansson"),

    # Music
    "bk": ("pt_wiki", "BK'"),

    # MMA
    "amanda-nunes": ("commons", "Amanda Nunes"),
    "israel-adesanya": ("commons", "Israel Adesanya"),
    "alex-volkanovski": ("commons", "Alexander Volkanovski"),
    "tom-aspinall": ("commons", "Tom Aspinall"),
    "paddy-pimblett": ("commons", "Paddy Pimblett"),
    "kamaru-usman": ("commons", "Kamaru Usman"),
    "zhang-weili": ("commons", "Zhang Weili"),
    "wanderlei-silva": ("commons", "Wanderlei Silva"),
    "vitor-belfort": ("commons", "Vitor Belfort"),
    "robert-whittaker": ("commons", "Robert Whittaker"),
    "dricus-du-plessis": ("commons", "Dricus du Plessis"),
    "belal-muhammad": ("commons", "Belal Muhammad"),
}

for slug, (source, query) in LAST_24_MAP.items():
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
        print(f"ALREADY OK: {slug}")
        continue

    urls = []
    if source == "safebooru":
        urls = get_safebooru_direct(query)
    elif source == "commons":
        urls = get_commons_fixed(query)
    elif source == "pt_wiki":
        urls = get_pt_wiki(query)

    saved_epic = has_epic
    saved_mythic = has_mythic

    for u in urls:
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
            if os.path.exists(epic_path):
                with open(epic_path, "rb") as f_ep:
                    if f_ep.read() == data:
                        continue
            with open(mythic_path, "wb") as out:
                out.write(data)
            saved_mythic = True

    status = "OK" if (saved_epic and saved_mythic) else f"PARTIAL(ep={saved_epic}, my={saved_mythic})"
    print(f"[{status}] {slug} -> found {len(urls)} urls")
