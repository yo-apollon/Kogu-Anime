import os
import json
import subprocess
import urllib.request
import urllib.parse
import re
import html as htmllib

CARDS_DIR = "docs/assets/cards"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

with open("docs/catalog.json") as f:
    catalog = json.load(f)
by_slug = {c["slug"]: c for c in catalog}

def get_dimensions(filepath):
    try:
        res = subprocess.run(["identify", "-format", "%w %h", filepath], capture_output=True, text=True, check=True)
        w, h = map(int, res.stdout.strip().split())
        return w, h
    except Exception:
        return 0, 0

def fetch_hd_bing(query, min_bytes=15000):
    url = f"https://www.bing.com/images/search?q={urllib.parse.quote(query)}&form=HDRSC2&first=1"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        html = urllib.request.urlopen(req, timeout=5).read().decode('utf-8', errors='ignore')
        matches = re.findall(r'class="iusc"[^>]*m="([^"]+)"', html)
        for m in matches[:4]:
            meta = json.loads(htmllib.unescape(m))
            turl = meta.get("turl")
            if turl:
                hi_url = turl + "&w=480&h=750&c=7&rs=1"
                req2 = urllib.request.Request(hi_url, headers=HEADERS)
                d = urllib.request.urlopen(req2, timeout=5).read()
                if len(d) >= min_bytes:
                    return d
    except Exception:
        pass
    return None

def upscale_imagemagick(src_path, dst_path):
    cmd = [
        "magick", src_path,
        "-filter", "Lanczos",
        "-resize", "480x750^",
        "-gravity", "center",
        "-extent", "480x750",
        "-unsharp", "0x0.75+0.75+0.008",
        "-quality", "92",
        dst_path
    ]
    subprocess.run(cmd, check=True)

files = [f for f in os.listdir(CARDS_DIR) if f.endswith(('.jpg', '.png'))]
low_res_files = []

for f in files:
    p = os.path.join(CARDS_DIR, f)
    w, h = get_dimensions(p)
    if w < 480 or h < 750:
        low_res_files.append((f, w, h))

print(f"Total low-res files to process: {len(low_res_files)}")

hd_fetched = 0
lanczos_upscaled = 0

for i, (f, w, h) in enumerate(low_res_files, 1):
    src_path = os.path.join(CARDS_DIR, f)
    slug = f.rsplit(".", 1)[0]
    card = by_slug.get(slug)
    name = card.get("name", slug) if card else slug
    clean_name = re.sub(r'\s*\(.*?\)\s*', ' ', name).strip()
    series = card.get("seriesTitle", "") if card else ""

    # Tenta fetch HD do Bing para retratos muito pequenos (<330 ou banner estreito)
    d = None
    if w <= 330 or h <= 440 or (w / h > 1.0):
        query = f"{clean_name} {series} portrait photoshoot".strip()
        d = fetch_hd_bing(query)

    if d:
        with open(src_path, "wb") as out:
            out.write(d)
        hd_fetched += 1
        print(f"[{i}/{len(low_res_files)}] HD FETCHED: {f} (orig: {w}x{h}) -> new: 480x750 ({len(d)}B)")
    else:
        upscale_imagemagick(src_path, src_path)
        lanczos_upscaled += 1
        print(f"[{i}/{len(low_res_files)}] LANCZOS UPSCALED: {f} (orig: {w}x{h}) -> 480x750")

print(f"\nProcessing complete!")
print(f"  HD Fetched: {hd_fetched}")
print(f"  Lanczos Upscaled: {lanczos_upscaled}")
