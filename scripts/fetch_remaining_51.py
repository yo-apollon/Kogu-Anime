import json
import os
import re
import urllib.request
import urllib.parse
from scripts.fetch_all_era_photos import (
    WIKI_HEADERS, SAFEBOORU_HEADERS,
    fetch_image_bytes, get_safebooru_images, get_wiki_images, get_commons_images
)

with open("docs/catalog.json") as f:
    cards = json.load(f)

# Direct queries / tags for the remaining 51
TARGETED = {
    # Anime
    "sukuna": ("safebooru", ["ryomen_sukuna", "sukuna_(jujutsu_kaisen)"]),
    "emilia": ("safebooru", ["emilia_(re:zero)", "emilia"]),
    "takumi-usui": ("safebooru", ["usui_takumi"]),
    "hak-son": ("safebooru", ["son_hak"]),
    "hirotaka-nifuji": ("safebooru", ["nifuji_hirotaka"]),
    "alisa-kujou": ("safebooru", ["alisa_mikhailovna_kujou"]),
    "qifrey": ("safebooru", ["qifrey"]),
    "yorha-2-gou-b-gata": ("safebooru", ["2b_(nier:automata)"]),
    "satan-jacob": ("safebooru", ["maou_sadao"]),
    "shirayuki": ("safebooru", ["shirayuki_(akagami_no_shirayukihime)"]),
    "aguero-agnis-khun": ("safebooru", ["khun_aguero_agnis"]),

    # Cinema / TV
    "batman-dc": ("wiki", "Batman"),
    "batman-hellbat": ("wiki", "Batman in film"),
    "iron-man-marvel": ("wiki", "Iron Man"),
    "joker-dc": ("wiki", "Joker (character)"),
    "neo-matrix": ("wiki", "Neo (The Matrix)"),
    "princess-leia-star-wars": ("wiki", "Princess Leia"),
    "scarlet-witch-marvel": ("wiki", "Wanda Maximoff (Marvel Cinematic Universe)"),
    "john-wick-cinema": ("wiki", "John Wick (character)"),
    "black-widow-marvel": ("wiki", "Natasha Romanoff (Marvel Cinematic Universe)"),

    # Idols
    "jungkook-era-golden": ("wiki", "Jungkook"),
    "v-kim-taehyung-layover": ("wiki", "V (singer)"),
    "ado-uta-rainha-do-j-pop": ("wiki", "Ado (singer)"),

    # Music
    "travis-scott": ("wiki", "Travis Scott"),
    "matue": ("wiki", "Matuê"),
    "drake": ("wiki", "Drake (musician)"),
    "asap-rocky": ("wiki", "ASAP Rocky"),
    "juice-wrld": ("wiki", "Juice Wrld"),
    "kayblack": ("wiki", "Kayblack"),
    "bk": ("wiki", "BK'"),
    "lady-gaga": ("wiki", "Lady Gaga"),
    "kurt-cobain": ("wiki", "Kurt Cobain"),
    "chester-bennington": ("wiki", "Chester Bennington"),

    # Football
    "luka-modric": ("wiki", "Luka Modrić"),
    "andres-iniesta": ("wiki", "Andrés Iniesta"),

    # MMA
    "anderson-silva": ("wiki", "Anderson Silva"),
    "amanda-nunes": ("wiki", "Amanda Nunes"),
    "khabib-nurmagomedov": ("wiki", "Khabib Nurmagomedov"),
    "israel-adesanya": ("wiki", "Israel Adesanya"),
    "charles-do-bronx": ("wiki", "Charles Oliveira"),
    "alex-volkanovski": ("wiki", "Alexander Volkanovski"),
    "tom-aspinall": ("wiki", "Tom Aspinall"),
    "paddy-pimblett": ("wiki", "Paddy Pimblett"),
    "kamaru-usman": ("wiki", "Kamaru Usman"),
    "ronda-rousey": ("wiki", "Ronda Rousey"),
    "zhang-weili": ("wiki", "Zhang Weili"),
    "wanderlei-silva": ("wiki", "Wanderlei Silva"),
    "vitor-belfort": ("wiki", "Vitor Belfort"),
    "robert-whittaker": ("wiki", "Robert Whittaker (fighter)"),
    "dricus-du-plessis": ("wiki", "Dricus du Plessis"),
    "belal-muhammad": ("wiki", "Belal Muhammad"),
}

by_slug = {c['slug']: c for c in cards}

for slug, (kind, target) in TARGETED.items():
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

    candidate_urls = []
    if kind == "safebooru":
        for tag in target:
            urls = get_safebooru_images(tag)
            candidate_urls.extend(urls)
            if len(candidate_urls) >= 4:
                break
    else:
        candidate_urls = get_wiki_images(target)
        if len(candidate_urls) < 2:
            candidate_urls.extend(get_commons_images(target))

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

    status = "OK" if (saved_epic and saved_mythic) else f"PARTIAL(ep={saved_epic}, my={saved_mythic})"
    print(f"[{status}] {slug} -> found {len(candidate_urls)} urls")
