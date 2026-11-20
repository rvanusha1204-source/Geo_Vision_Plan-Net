"""
analysis_pipeline.py
Reusable Earth Engine analysis pipeline for the Green Cover Detection &
Deforestation Analysis System.

This is your NDVI_ChangeDetection_ViolationEngine.ipynb notebook's Stage 4-5
logic, turned into importable functions instead of manual notebook cells,
so it can be called automatically by build_cache.py for every district.

Nothing in here talks to Streamlit. app.py never imports this module directly
— it only reads the cache/<district>/ files that build_cache.py produces
using this module. This keeps the live dashboard fast (reads cached files,
no per-click Earth Engine wait) while removing all manual download/drag-drop
work from your workflow.
"""

import os
import json
import time
import math
from concurrent.futures import ThreadPoolExecutor, as_completed
import ee
import geemap
import pandas as pd
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Tunable parameters — same defaults as your notebook. Adjust these to match
# your project's ground truth or a specific state's environmental rules.
# ---------------------------------------------------------------------------
CLOUD_COVER_MAX = 20            # percent, filters very cloudy Sentinel-2 scenes
LOSS_THRESHOLD = -0.15          # NDVI diff below this = vegetation loss
GAIN_THRESHOLD = 0.15           # NDVI diff above this = vegetation gain
SEVERE_LOSS_THRESHOLD = -0.30   # NDVI diff below this = severe loss (Rule C)
BUFFER_METERS = 500             # no-encroachment buffer around protected areas
EXPORT_SCALE = 10               # meters/pixel for the GeoTIFF/vector exports (visual quality)
STATS_SCALE = 60                 # meters/pixel for area calculations — coarser to reduce
                                  # server-side compute load, since these are the calls that
                                  # have been hitting memory-limit/timeout errors under
                                  # quota-restricted mode. ~9x fewer pixels than scale=10,
                                  # negligible accuracy loss for hectare-level reporting.

MAX_WORKERS = 6                 # cells computed in parallel; lower to 3 if you get quota errors
CELL_AREA_KM2 = 500              # grid cell size for stats; lower to 250 if cells still time out

WDPA_COLLECTION = 'WCMC/WDPA/current/polygons'


def mask_s2_clouds(image):
    qa = image.select('QA60')
    cloud_bit = 1 << 10
    cirrus_bit = 1 << 11
    mask = qa.bitwiseAnd(cloud_bit).eq(0).And(qa.bitwiseAnd(cirrus_bit).eq(0))
    return image.updateMask(mask).divide(10000)


def get_ndvi_composite(aoi, start_date, end_date, cloud_max=CLOUD_COVER_MAX):
    """Cloud-free median NDVI composite for a date range over an AOI."""
    collection = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                  .filterBounds(aoi)
                  .filterDate(start_date, end_date)
                  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', cloud_max))
                  .map(mask_s2_clouds))
    composite = collection.median().clip(aoi)
    ndvi = composite.normalizedDifference(['B8', 'B4']).rename('NDVI')
    return ndvi, collection.size()


def area_hectares(mask_image, region, scale=EXPORT_SCALE, tile_scale=4):
    area_img = mask_image.selfMask().multiply(ee.Image.pixelArea())
    stats = area_img.reduceRegion(
        reducer=ee.Reducer.sum(), geometry=region, scale=scale, maxPixels=1e13,
        tileScale=tile_scale, bestEffort=True
    )
    band_name = mask_image.bandNames().get(0)
    sq_meters = stats.get(band_name)
    return ee.Number(sq_meters).divide(10000)


def _combined_area_stats_with_retry(veg_loss_mask, veg_gain_mask, rule_a, rule_b, rule_c,
                                     any_violation, region, scale=STATS_SCALE):
    """
    Stacks all 6 masks into one image, then splits the district into small grid
    cells (~500 sq km each) and runs reduceRegion once per cell, summing results.
    Large districts (e.g. Coimbatore) time out when computed in a single call;
    small cells each finish well within the interactive compute limit.
    """
    combined = ee.Image.cat([
        veg_loss_mask.selfMask().multiply(ee.Image.pixelArea()).rename('veg_loss'),
        veg_gain_mask.selfMask().multiply(ee.Image.pixelArea()).rename('veg_gain'),
        rule_a.selfMask().multiply(ee.Image.pixelArea()).rename('protected_encroach'),
        rule_b.selfMask().multiply(ee.Image.pixelArea()).rename('buffer_violation'),
        rule_c.selfMask().multiply(ee.Image.pixelArea()).rename('severe_loss'),
        any_violation.selfMask().multiply(ee.Image.pixelArea()).rename('total_flagged'),
    ])

    # Cut the district into small squares (about CELL_AREA_KM2 each)
    area_km2 = region.area(1).getInfo() / 1e6
    n = max(1, math.ceil(math.sqrt(area_km2 / CELL_AREA_KM2)))
    ring = region.bounds().getInfo()['coordinates'][0]
    xs = [p[0] for p in ring]
    ys = [p[1] for p in ring]
    xmin, xmax, ymin, ymax = min(xs), max(xs), min(ys), max(ys)
    dx, dy = (xmax - xmin) / n, (ymax - ymin) / n
    print(f"    Splitting {area_km2:,.0f} sq km into {n}x{n} cells...")

    totals = {k: 0.0 for k in ['veg_loss', 'veg_gain', 'protected_encroach',
                               'buffer_violation', 'severe_loss', 'total_flagged']}

    def run_cell(i, j):
        cell = ee.Geometry.Rectangle([xmin + i * dx, ymin + j * dy,
                                      xmin + (i + 1) * dx, ymin + (j + 1) * dy])
        for attempt in range(3):
            try:
                return combined.reduceRegion(
                    reducer=ee.Reducer.sum(), geometry=cell, scale=scale,
                    maxPixels=1e13, tileScale=4
                ).getInfo()
            except Exception as e:
                msg = str(e).lower()
                if attempt < 2 and any(t in msg for t in ('timed out', 'memory limit', 'timeout',
                                                          'too many concurrent', 'quota', 'rate')):
                    time.sleep(10)
                    continue
                raise

    done = 0
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = [pool.submit(run_cell, i, j) for i in range(n) for j in range(n)]
        for fut in as_completed(futures):
            stats = fut.result()
            for k in totals:
                totals[k] += (stats.get(k) or 0.0) / 10000.0
            done += 1
            print(f"    cell {done}/{n * n} done")
    return totals


def compute_period_analysis(aoi, year1_start, year1_end, year2_start, year2_end):
    """
    Runs the notebook's Stage 4-5 analysis for one AOI between two dates.
    Returns (summary_dict, ee_objects) — ee_objects carries the images/vectors
    needed for export (ndvi_diff, any_violation).
    """
    ndvi_t1, _ = get_ndvi_composite(aoi, year1_start, year1_end)
    ndvi_t2, _ = get_ndvi_composite(aoi, year2_start, year2_end)
    ndvi_diff = ndvi_t2.subtract(ndvi_t1).rename('NDVI_diff')

    veg_loss_mask = ndvi_diff.lt(LOSS_THRESHOLD)
    veg_gain_mask = ndvi_diff.gt(GAIN_THRESHOLD)

    wdpa = ee.FeatureCollection(WDPA_COLLECTION).filterBounds(aoi)
    protected_area_count = wdpa.size().getInfo()
    protected_mask = ee.Image(0).byte().paint(wdpa, 1).rename('protected')
    protected_buffered = wdpa.map(lambda f: f.simplify(100).buffer(BUFFER_METERS, 100))
    buffer_mask = ee.Image(0).byte().paint(protected_buffered, 1).rename('buffer_zone')

    rule_a = veg_loss_mask.And(protected_mask.eq(1)).rename('rule_a_protected_encroachment')
    rule_b = veg_loss_mask.And(buffer_mask.eq(1)).And(protected_mask.eq(0)).rename('rule_b_buffer_violation')
    rule_c = ndvi_diff.lt(SEVERE_LOSS_THRESHOLD).rename('rule_c_severe_loss')
    any_violation = rule_a.Or(rule_b).Or(rule_c).rename('any_violation')

    stats = _combined_area_stats_with_retry(
        veg_loss_mask, veg_gain_mask, rule_a, rule_b, rule_c, any_violation, aoi
    )

    summary = {
        'total_veg_loss_ha': stats['veg_loss'],
        'total_veg_gain_ha': stats['veg_gain'],
        'protected_area_encroachment_ha': stats['protected_encroach'],
        'buffer_zone_violation_ha': stats['buffer_violation'],
        'severe_loss_ha': stats['severe_loss'],
        'total_flagged_violation_ha': stats['total_flagged'],
        'protected_areas_in_aoi': protected_area_count,
    }
    ee_objects = {'ndvi_diff': ndvi_diff, 'any_violation': any_violation, 'wdpa': wdpa}
    return summary, ee_objects


def export_region_outputs(aoi, out_dir, year1_start, year1_end, year2_start, year2_end):
    """
    Runs the overall-period analysis (e.g. 2017 vs 2025) and writes
    violation_summary.csv, violation_zones.geojson, ndvi_change_map.tif into out_dir.
    Returns the summary dict.
    """
    os.makedirs(out_dir, exist_ok=True)
    summary, ee_objects = compute_period_analysis(aoi, year1_start, year1_end, year2_start, year2_end)
    summary['study_period'] = f"{year1_start[:4]} - {year2_end[:4]}"

    pd.DataFrame([summary]).to_csv(os.path.join(out_dir, 'violation_summary.csv'), index=False)
    geojson_path = os.path.join(out_dir, 'violation_zones.geojson')
    vector_scale = EXPORT_SCALE
    vector_ok = False
    for attempt in range(4):
        try:
            violation_vectors = ee_objects['any_violation'].selfMask().reduceToVectors(
                geometry=aoi, scale=vector_scale, geometryType='polygon',
                maxPixels=1e13, bestEffort=True
            )
            geemap.ee_export_vector(violation_vectors, filename=geojson_path)
        except Exception as e:
            print(f"  Violation vector export raised an exception at scale={vector_scale}m: {e}")

        if os.path.exists(geojson_path) and os.path.getsize(geojson_path) > 0:
            vector_ok = True
            break

        vector_scale *= 2
        print(f"  Violation vector export failed (file not written) at previous resolution; "
              f"retrying at {vector_scale}m/pixel (fewer, larger polygons, less memory load)...")

    if not vector_ok:
        print(f"  WARNING: violation_zones.geojson did not download successfully. ")

    # Earth Engine caps a single direct-download request at ~48MB. Larger
    # districts at 10m/pixel exceed that easily (this is separate from the
    # area stats above, which are server-side aggregations and never hit
    # this limit). IMPORTANT: geemap.ee_export_image() does NOT raise a
    # Python exception when this download fails — it catches the error
    # internally and just prints a message, then returns normally. So we
    # can't detect failure by catching an exception; we have to check
    # whether the file actually landed on disk with real content.
    tif_path = os.path.join(out_dir, 'ndvi_change_map.tif')
    # Pick a starting resolution that fits Earth Engine's ~48MB direct-download
    # cap up front (aim for ~2.5 million pixels), instead of failing at 10m,
    # 20m, 40m first. Casting to float32 also halves the file size vs float64.
    area_m2 = aoi.area(1).getInfo()
    scale = max(EXPORT_SCALE, int(math.ceil(math.sqrt(area_m2 / 2.5e6))))
    print(f"  NDVI GeoTIFF: starting at {scale}m/pixel to stay under the download limit.")
    ndvi_export = ee_objects['ndvi_diff'].toFloat()
    tif_ok = False
    for attempt in range(8):
        if os.path.exists(tif_path):
            os.remove(tif_path)
        try:
            geemap.ee_export_image(
                ndvi_export, filename=tif_path, scale=scale, region=aoi, file_per_band=False
            )
        except Exception as e:
            print(f"  NDVI GeoTIFF export raised an exception at scale={scale}m: {e}")

        if os.path.exists(tif_path) and os.path.getsize(tif_path) > 0:
            tif_ok = True
            break

        scale = int(scale * 1.5)
        print(f"  NDVI GeoTIFF export failed (file not written); "
              f"waiting 8s then retrying at {scale}m/pixel...")
        time.sleep(8)
    if not tif_ok:
        print(f"  WARNING: could not export ndvi_change_map.tif after retries. "
              f"Continuing without the heatmap for this district; the dashboard will show "
              f"'not available' for it, but all KPI numbers and the violation map are unaffected.")
    return summary


def compute_multi_year_trend(aoi, out_dir, years=(2017, 2019, 2021, 2023, 2025)):
    """
    Runs the analysis across consecutive year pairs (2017-2019, 2019-2021, ...)
    and writes violation_trend.csv into out_dir. Returns the trend DataFrame.
    """
    rows = []
    total_periods = len(years) - 1
    for i, (y1, y2) in enumerate(zip(years[:-1], years[1:]), start=1):
        print(f"  Trend period {i}/{total_periods}: {y1}-{y2} ...")
        summary, _ = compute_period_analysis(
            aoi, f"{y1}-01-01", f"{y1}-12-31", f"{y2}-01-01", f"{y2}-12-31"
        )
        print(f"  Trend period {i}/{total_periods}: {y1}-{y2} done "
              f"(total_flagged_violation_ha={summary['total_flagged_violation_ha']:.1f})")
        summary['year_start'] = y1
        summary['year_end'] = y2
        summary['period_label'] = f"{y1}-{y2}"
        rows.append(summary)

    trend_df = pd.DataFrame(rows)
    cols = ['year_start', 'year_end', 'period_label', 'total_veg_loss_ha', 'total_veg_gain_ha',
            'protected_area_encroachment_ha', 'buffer_zone_violation_ha', 'severe_loss_ha',
            'total_flagged_violation_ha', 'protected_areas_in_aoi']
    trend_df = trend_df[cols]
    trend_df.to_csv(os.path.join(out_dir, 'violation_trend.csv'), index=False)
    return trend_df


def write_metadata(aoi, out_dir, display_name, state_name):
    """
    Writes metadata.json with display name, state, and centroid lat/lon.
    app.py's map picker reads this to place the district's marker.
    """
    centroid = aoi.centroid().coordinates().getInfo()  # Earth Engine returns [lon, lat]
    meta = {
        'display_name': display_name,
        'state': state_name,
        'lat': centroid[1],
        'lon': centroid[0],
        'last_updated': datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z'),
    }
    with open(os.path.join(out_dir, 'metadata.json'), 'w') as f:
        json.dump(meta, f, indent=2)
    return meta