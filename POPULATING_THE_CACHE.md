# Populating the Region Cache — "Analyze a Region" Tab

The dashboard's new **🔎 Analyze a Region** tab shows instant results by reading from a local
`cache/` folder instead of running Earth Engine live. This is where you put the pre-computed
results for each district.

## Folder structure

Inside your dashboard folder, create:

```
green-cover-dashboard/
├── app.py
├── cache/
│   ├── coimbatore_tamil_nadu/
│   │   ├── violation_summary.csv
│   │   ├── violation_zones.geojson       (optional, enables the map)
│   │   ├── ndvi_change_map.tif            (optional, enables the heatmap)
│   │   └── metadata.json                  (optional, controls the display name)
│   ├── dehradun_uttarakhand/
│   │   └── ... (same 4 files)
│   └── ... one folder per district
```

**Folder naming:** use lowercase with underscores (e.g. `nagpur_maharashtra`) — this becomes the
internal ID. The dropdown label shown to users comes from `metadata.json` if present, otherwise
it's auto-generated from the folder name.

**`metadata.json` format** (optional but recommended for clean display names):
```json
{"display_name": "Coimbatore, Tamil Nadu"}
```

## Steps to prepare each district

For each of your 10 districts, repeat this process using your existing notebooks:

1. Open `NDVI_ChangeDetection_ViolationEngine.ipynb` in Colab
2. Follow the usual setup (Section 1: auth + `region_selector.py` + project ID)
3. In Section 2, set the AOI to the district:
   ```python
   aoi = rs.get_region_by_name(state_name="Uttarakhand", district_name="Dehradun")
   ```
4. Run the rest of the notebook as usual
5. Download the 3 output files: `violation_summary.csv`, `violation_zones.geojson`, `ndvi_change_map.tif`
6. On your PC, create `cache/dehradun_uttarakhand/` and move those 3 files into it
7. Optionally add a `metadata.json` with a nicely formatted display name
8. Repeat for the next district

## Suggested district list (from our discussion)

| Folder name | `state_name` | `district_name` |
|---|---|---|
| `coimbatore_tamil_nadu` | Tamil Nadu | Coimbatore |
| `dehradun_uttarakhand` | Uttarakhand | Dehradun |
| `nagpur_maharashtra` | Maharashtra | Nagpur |
| `ernakulam_kerala` | Kerala | Ernakulam |
| `jaipur_rajasthan` | Rajasthan | Jaipur |
| `bengaluru_urban_karnataka` | Karnataka | Bangalore Urban |
| `kamrup_assam` | Assam | Kamrup Metropolitan |
| `nashik_maharashtra` | Maharashtra | Nashik |
| `ludhiana_punjab` | Punjab | Ludhiana |
| `visakhapatnam_ap` | Andhra Pradesh | Visakhapatnam |

**Note:** exact district names in the FAO/GAUL dataset (which `region_selector.py` uses) can differ
slightly from common usage. If `get_region_by_name()` throws a "no district found" error, run
`rs.list_districts(state_name="...")` first to see the exact spelling available for that state.

## Time estimate

Each district takes roughly the same time your Coimbatore run took (~5-15 minutes depending on
district size and GEE load). For 10 districts, budget **1-3 hours total** — you don't have to do
them all in one sitting; the dashboard will just show however many are in the `cache/` folder at
any time, and you can keep adding more.

## Testing as you go

You don't need all 10 before testing — drop in just 1-2 districts, run:
```
streamlit run app.py
```
and check the **🔎 Analyze a Region** tab shows a dropdown with those districts and loads their
data instantly when selected. Then keep adding the rest.
