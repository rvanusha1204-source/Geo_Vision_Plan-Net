"""
build_cache.py
Automatically (re)builds cache/<district>/ for all 10 curated districts by
running the Earth Engine analysis pipeline (analysis_pipeline.py) end to end.
This replaces the manual "run notebook in Colab -> download 3 files -> drag
into cache/" workflow from POPULATING_THE_CACHE.md.

Setup (one-time, on the machine that will run this):
    pip install earthengine-api geemap geopandas pandas
    earthengine authenticate     # or let ee.Authenticate() below open a browser

Usage:
    python build_cache.py                              # builds all 10 districts
    python build_cache.py bengaluru_urban_karnataka     # builds just one (fast re-run/testing)

IMPORTANT: after this finishes, fully STOP and RESTART the Streamlit app
(not just refresh the browser) so it reads the fresh cache files —
a running app won't notice files changed on disk otherwise.
"""

import os
import sys
import json
import traceback
from datetime import date, timedelta, datetime, timezone

import region_selector as rs
import analysis_pipeline as ap

# Your Google Cloud project ID linked to Earth Engine.
GEE_PROJECT_ID = "green-cover-project-502404"  # <-- CHANGE THIS

CACHE_DIR = "cache"

# Baseline year stays fixed — this is your long-term reference point.
YEAR1_START, YEAR1_END = "2017-01-01", "2017-12-31"

# "Recent" period is a ROLLING 365-day window ending today, instead of a
# hardcoded year. This is what makes results "live" — every time you re-run
# this script (see the scheduling note below), YEAR2 automatically shifts
# forward to include the latest available imagery, instead of staying stuck
# at whatever date was hardcoded when this file was written.
_today = date.today()
_recent_start = _today - timedelta(days=365)
YEAR2_START, YEAR2_END = _recent_start.isoformat(), _today.isoformat()

# Multi-year trend checkpoints — same 2-year spacing as before, but the final
# checkpoint is always the current year instead of a hardcoded 2025.
TREND_YEARS = (2017, 2019, 2021, 2023, _today.year)

# Your 10 curated districts: (folder slug, state_name, district_name, display_name)
# state_name/district_name must match the FAO/GAUL spelling — see
# POPULATING_THE_CACHE.md's note about running rs.list_districts(state_name=...)
# if get_region_by_name() ever raises a "no district found" error.
DISTRICTS = [
    ("coimbatore_tamil_nadu",     "Tamil Nadu",     "Coimbatore",          "Coimbatore, Tamil Nadu"),
    ("dehradun_uttarakhand",      "Uttarakhand",    "Dehra Dun",           "Dehradun, Uttarakhand"),
    ("nagpur_maharashtra",        "Maharashtra",    "Nagpur",              "Nagpur, Maharashtra"),
    ("ernakulam_kerala",          "Kerala",         "Ernakulam",           "Ernakulam, Kerala"),
    ("jaipur_rajasthan",          "Rajasthan",      "Jaipur",              "Jaipur, Rajasthan"),
    ("bengaluru_urban_karnataka", "Karnataka",      "Bangalore Urban",     "Bengaluru Urban, Karnataka"),
    ("kamrup_assam",              "Assam",          "Kamrup",              "Kamrup, Assam"),
    ("nashik_maharashtra",        "Maharashtra",    "Nashik",              "Nashik, Maharashtra"),
    ("ludhiana_punjab",           "Punjab",         "Ludhiana",            "Ludhiana, Punjab"),
    ("visakhapatnam_ap",          "Andhra Pradesh", "Vishakhapatnam",      "Visakhapatnam, Andhra Pradesh") ,
]


def build_one(slug, state_name, district_name, display_name):
    print(f"\n{'='*60}\n{display_name}  ({slug})\n{'='*60}")
    out_dir = os.path.join(CACHE_DIR, slug)

    aoi = rs.get_region_by_name(state_name=state_name, district_name=district_name)
    rs.region_info(aoi)

    print(f"Running overall-period analysis ({YEAR1_START[:4]} - {YEAR2_END[:4]}, recent window {YEAR2_START} to {YEAR2_END})...")
    ap.export_region_outputs(aoi, out_dir, YEAR1_START, YEAR1_END, YEAR2_START, YEAR2_END)
    print("  -> violation_summary.csv, violation_zones.geojson, ndvi_change_map.tif written.")

    print(f"Running multi-year trend ({'/'.join(str(y) for y in TREND_YEARS)})...")
    ap.compute_multi_year_trend(aoi, out_dir, years=TREND_YEARS)
    print("  -> violation_trend.csv written.")

    ap.write_metadata(aoi, out_dir, display_name, state_name)
    print("  -> metadata.json written.")


def main():
    run_started = datetime.now(timezone.utc)
    rs.init_gee(GEE_PROJECT_ID)

    # Optional: pass one or more slugs as args to rebuild just those districts
    # (much faster than a full 10-district run while testing).
    only = set(sys.argv[1:]) if len(sys.argv) > 1 else None
    failures = []
    built = []

    for slug, state_name, district_name, display_name in DISTRICTS:
        if only and slug not in only:
            continue
        try:
            build_one(slug, state_name, district_name, display_name)
            built.append(slug)
        except Exception as e:
            print(f"FAILED: {display_name} ({slug}) -> {e}")
            traceback.print_exc()
            failures.append(slug)

    run_finished = datetime.now(timezone.utc)

    # Written regardless of a partial-only run, so refresh_scheduler.py and the
    # dashboard can both know exactly when data was last touched, how long it
    # took, and which satellite date range was actually used this time.
    status = {
        'run_started_utc': run_started.isoformat(timespec='seconds').replace('+00:00', 'Z'),
        'run_finished_utc': run_finished.isoformat(timespec='seconds').replace('+00:00', 'Z'),
        'duration_seconds': round((run_finished - run_started).total_seconds(), 1),
        'baseline_period': f"{YEAR1_START} to {YEAR1_END}",
        'recent_period': f"{YEAR2_START} to {YEAR2_END}",
        'districts_built': built,
        'districts_failed': failures,
        'status': 'success' if not failures else ('partial_failure' if built else 'failed'),
    }
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(os.path.join(CACHE_DIR, 'last_refresh.json'), 'w') as f:
        json.dump(status, f, indent=2)

    print(f"\n{'='*60}")
    if failures:
        print(f"Done, with {len(failures)} failure(s): {failures}")
    else:
        print("All districts built successfully.")
    print(f"Wrote {os.path.join(CACHE_DIR, 'last_refresh.json')}")
    print("Now fully restart the server so it picks up the fresh cache:")
    print("  python server.py")


if __name__ == "__main__":
    main()
