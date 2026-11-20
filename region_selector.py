"""
region_selector.py
Reusable region-selection utility for the Green Cover Detection & Deforestation
Analysis System — makes the pipeline work for ANY region in India, not just a
hardcoded AOI.

Supports 3 selection modes:
  1. Search by name   -> get_region_by_name(district_name="Coimbatore")
  2. Dropdown list     -> list_states() / list_districts() to populate a UI dropdown,
                          then get_region_by_name(...) with the selected value
  3. Custom boundary   -> get_region_from_geojson(...) for an uploaded file,
                          or get_region_from_bbox(...) for manual testing

Usage in any notebook (Colab):
    Upload this file via the Colab file-upload button (left sidebar > Files),
    or recreate it in a cell with:
        %%writefile region_selector.py
        <paste this file's contents>
    Then:
        import region_selector as rs
        rs.init_gee('your-project-id')
        aoi = rs.get_region_by_name(state_name="Tamil Nadu", district_name="Coimbatore")
"""

import ee

STATE_FC = 'FAO/GAUL/2015/level1'
DISTRICT_FC = 'FAO/GAUL/2015/level2'
COUNTRY_NAME = 'India'


def init_gee(project_id):
    """Authenticate and initialize Earth Engine. Call once per notebook session."""
    try:
        ee.Initialize(project=project_id)
    except Exception:
        ee.Authenticate()
        ee.Initialize(project=project_id)
    print("Earth Engine initialized.")


def list_states():
    """Return a sorted list of Indian state names — use to populate a state dropdown."""
    states = (ee.FeatureCollection(STATE_FC)
              .filter(ee.Filter.eq('ADM0_NAME', COUNTRY_NAME))
              .aggregate_array('ADM1_NAME')
              .getInfo())
    return sorted(set(states))


def list_districts(state_name=None):
    """
    Return a sorted list of district names — use to populate a district dropdown.
    Pass state_name to narrow the list to districts within that state.
    """
    fc = ee.FeatureCollection(DISTRICT_FC).filter(ee.Filter.eq('ADM0_NAME', COUNTRY_NAME))
    if state_name:
        fc = fc.filter(ee.Filter.eq('ADM1_NAME', state_name))
    districts = fc.aggregate_array('ADM2_NAME').getInfo()
    return sorted(set(districts))


def get_region_by_name(state_name=None, district_name=None):
    """
    Mode 1 & 2: Search-by-name / dropdown-selected lookup.

    - Provide district_name (optionally with state_name to disambiguate duplicate
      district names across states) for a district-level AOI.
    - Provide only state_name for a state-level AOI.

    Returns an ee.Geometry.
    """
    if district_name:
        fc = (ee.FeatureCollection(DISTRICT_FC)
              .filter(ee.Filter.eq('ADM0_NAME', COUNTRY_NAME))
              .filter(ee.Filter.eq('ADM2_NAME', district_name)))
        if state_name:
            fc = fc.filter(ee.Filter.eq('ADM1_NAME', state_name))

        count = fc.size().getInfo()
        if count == 0:
            raise ValueError(
                f"No district found matching '{district_name}'"
                + (f" in state '{state_name}'" if state_name else "")
                + ". Check spelling against list_districts(), or try just the state."
            )
        if count > 1 and not state_name:
            names = fc.aggregate_array('ADM1_NAME').getInfo()
            raise ValueError(
                f"Multiple districts named '{district_name}' found in states: {names}. "
                f"Pass state_name to disambiguate."
            )
        return fc.geometry()

    elif state_name:
        fc = (ee.FeatureCollection(STATE_FC)
              .filter(ee.Filter.eq('ADM0_NAME', COUNTRY_NAME))
              .filter(ee.Filter.eq('ADM1_NAME', state_name)))
        count = fc.size().getInfo()
        if count == 0:
            raise ValueError(f"No state found matching '{state_name}'. Check list_states().")
        return fc.geometry()

    else:
        raise ValueError("Provide at least a state_name or district_name.")


def get_region_from_geojson(geojson_dict):
    """
    Mode 3: Custom boundary upload.
    Pass a parsed GeoJSON dict — either a bare geometry, or a Feature
    (in which case its 'geometry' key is used). Returns an ee.Geometry.

    Example (Colab):
        from google.colab import files
        import json
        uploaded = files.upload()  # user selects their_boundary.geojson
        with open(list(uploaded.keys())[0]) as f:
            geojson_dict = json.load(f)
        aoi = get_region_from_geojson(geojson_dict)
    """
    geom_dict = geojson_dict.get('geometry', geojson_dict)
    return ee.Geometry(geom_dict)


def get_region_from_bbox(min_lon, min_lat, max_lon, max_lat):
    """
    Fallback for quick manual testing without a real boundary file
    (e.g. while a user is still deciding on their exact study area).
    """
    return ee.Geometry.Rectangle([min_lon, min_lat, max_lon, max_lat])


def region_info(geometry):
    """Quick sanity check after selecting a region — prints area and centroid."""
    area_sqkm = geometry.area().divide(1e6).getInfo()
    centroid = geometry.centroid().coordinates().getInfo()
    print(f"Region area: {area_sqkm:,.1f} sq km")
    print(f"Centroid (lon, lat): {centroid}")
    return {'area_sqkm': area_sqkm, 'centroid': centroid}
