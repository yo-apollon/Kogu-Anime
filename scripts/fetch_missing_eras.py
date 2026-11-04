import json
import os
import time
from scripts.fetch_all_era_photos import anchors, process_anchor

missing = []
for c in anchors:
    s = c["slug"]
    ep = f".cache/era_photos/{s}-epic.jpg"
    my = f".cache/era_photos/{s}-mythic.jpg"
    ep_ok = os.path.exists(ep) and os.path.getsize(ep) > 3000
    my_ok = os.path.exists(my) and os.path.getsize(my) > 3000
    if not (ep_ok and my_ok):
        missing.append(c)

print(f"Total missing anchors to process: {len(missing)}")

success = 0
for i, c in enumerate(missing, 1):
    try:
        res = process_anchor(c)
        if res:
            success += 1
            print(f"[{i}/{len(missing)}] OK: {c['slug']} ({c.get('niche')})")
        else:
            print(f"[{i}/{len(missing)}] MISS: {c['slug']} ({c.get('niche')})")
    except Exception as e:
        print(f"[{i}/{len(missing)}] ERR: {c['slug']} -> {e}")
    time.sleep(0.1)

print(f"Finished batch: {success}/{len(missing)} successfully fetched.")
