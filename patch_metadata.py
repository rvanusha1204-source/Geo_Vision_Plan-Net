"""
patch_metadata.py
One-time helper: adds state/lat/lon to each cached district's metadata.json,
since the original batch notebook only saved display_name.

app.py's map picker needs lat/lon to place markers — without this, districts
still work fine in the dropdown, they just won't show up on the map.

Usage:
    python patch_metadata.py
"""

import json
import os

CACHE_DIR = "cache"

# Approximate district-centroid coordinates for the map picker markers.
COORDS = {
    "coimbatore_tamil_nadu":      {"lat": 11.0168, "lon": 76.9558, "state": "Tamil Nadu"},
    "dehradun_uttarakhand":       {"lat": 30.3165, "lon": 78.0322, "state": "Uttarakhand"},
    "nagpur_maharashtra":         {"lat": 21.1458, "lon": 79.0882, "state": "Maharashtra"},
    "ernakulam_kerala":           {"lat": 9.9816,  "lon": 76.2999, "state": "Kerala"},
    "jaipur_rajasthan":           {"lat": 26.9124, "lon": 75.7873, "state": "Rajasthan"},
    "bengaluru_urban_karnataka":  {"lat": 12.9716, "lon": 77.5946, "state": "Karnataka"},
    "kamrup_assam":               {"lat": 26.1445, "lon": 91.7362, "state": "Assam"},
    "nashik_maharashtra":         {"lat": 19.9975, "lon": 73.7898, "state": "Maharashtra"},
    "ludhiana_punjab":            {"lat": 30.9010, "lon": 75.8573, "state": "Punjab"},
    "visakhapatnam_ap":           {"lat": 17.6868, "lon": 83.2185, "state": "Andhra Pradesh"},
}


def main():
    if not os.path.isdir(CACHE_DIR):
        print(f"No '{CACHE_DIR}' folder found here. Run this from your dashboard folder.")
        return

    updated, skipped = 0, 0
    for slug in sorted(os.listdir(CACHE_DIR)):
        folder = os.path.join(CACHE_DIR, slug)
        if not os.path.isdir(folder):
            continue

        meta_path = os.path.join(folder, "metadata.json")
        info = COORDS.get(slug)

        if info is None:
            print(f"  SKIP  {slug} — no known coordinates for this slug (not in COORDS dict above)")
            skipped += 1
            continue

        # Load existing metadata.json if present, else start fresh
        meta = {}
        if os.path.exists(meta_path):
            try:
                with open(meta_path) as f:
                    meta = json.load(f)
            except Exception:
                meta = {}

        meta.setdefault("display_name", slug.replace('_', ' ').title())
        meta["state"] = info["state"]
        meta["lat"] = info["lat"]
        meta["lon"] = info["lon"]

        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2)

        print(f"  DONE  {slug} -> {meta}")
        updated += 1

    print(f"\n{updated} updated, {skipped} skipped.")
    print("Now restart Streamlit (Ctrl+C then 'streamlit run app.py' again) to see the map markers.")


if __name__ == "__main__":
    main()
