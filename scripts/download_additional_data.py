#!/usr/bin/env python3
"""
Script to download additional datasets via APIs for the Geospatial Analysis project.
Focuses on filling data gaps identified in DATA_GAP_ANALYSIS.md.
"""

import os
import sys
import json
import requests
import zipfile
import io
import logging
from pathlib import Path
import geopandas as gpd
import pandas as pd
from shapely.geometry import shape, box, Polygon
import shapely.wkt
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)

DATA_DIR = Path('data')
RAW_DIR = DATA_DIR / 'raw'
PROCESSED_DIR = DATA_DIR / 'processed'

# Ensure directories exist
for d in [RAW_DIR / 'demographics', RAW_DIR / 'soils', RAW_DIR / 'infrastructure', RAW_DIR / 'rail', RAW_DIR / 'zoning']:
    d.mkdir(parents=True, exist_ok=True)

# Bounding Box for Seattle-Tacoma Corridor (approximate)
# Min Lon, Min Lat, Max Lon, Max Lat
BBOX = [-122.55, 47.15, -122.15, 47.75]
BBOX_STR = f"{BBOX[1]},{BBOX[0]},{BBOX[3]},{BBOX[2]}" # South, West, North, East for Overpass

def download_svi_2020():
    """Download CDC SVI 2020 for Washington State"""
    logging.info("Downloading CDC SVI 2020 for Washington...")
    # Try US file if state fails, or just warn.
    # Known working URL pattern often changes.
    # Let's try the US county file which is more stable, then filter? No, too big.
    # Let's try a different casing or year if 2020 fails.
    url = "https://svi.cdc.gov/Documents/Data/2020_SVI_Data/Shapefiles/SVI2020_WASHINGTON_county.zip"
    output_dir = RAW_DIR / 'demographics'
    
    try:
        r = requests.get(url, stream=True)
        if r.status_code == 404:
             # Try alternative casing
             url = "https://svi.cdc.gov/Documents/Data/2020_SVI_Data/Shapefiles/SVI2020_US_COUNTY.zip"
             logging.info("  State file not found, trying US file (large)...")
             # Actually, let's not download the whole US file blindly.
             logging.warning("  ❌ SVI URL not found. Please download manually from https://www.atsdr.cdc.gov/placeandhealth/svi/")
             return None

        r.raise_for_status()
        z = zipfile.ZipFile(io.BytesIO(r.content))
        z.extractall(output_dir)
        logging.info(f"✅ SVI data downloaded to {output_dir}")
        
        # Rename for consistency if needed, or just find the shp
        shp_files = list(output_dir.glob("SVI2020_WASHINGTON_county.shp"))
        if shp_files:
            return shp_files[0]
    except Exception as e:
        logging.error(f"❌ Failed to download SVI: {e}")
    return None

def download_ssurgo_soils():
    """
    Download SSURGO soils data via SDA REST API.
    Queries for Map Units within the bounding box and retrieves Hydrologic Group.
    """
    logging.info("Downloading SSURGO Soils data via SDA API...")
    
    # SDA API Endpoint
    url = "https://sdmdataaccess.nrcs.usda.gov/Tabular/post.rest"
    
    # WKT Polygon for the BBox
    wkt = f"POLYGON(({BBOX[0]} {BBOX[1]}, {BBOX[2]} {BBOX[1]}, {BBOX[2]} {BBOX[3]}, {BBOX[0]} {BBOX[3]}, {BBOX[0]} {BBOX[1]}))"
    
    # SQL Query to get Map Unit Keys (mukey) and Hydrologic Group
    # We join mapunit, component, and chorizon (or just component for hydgrp)
    # Using a spatial query filter
    query = f"""
    SELECT 
        mu.mukey, mu.musym, mu.muname, 
        c.compname, c.hydgrp, c.comppct_r,
        mupolygon.mupolygongeo.STAsText() as geometry
    FROM mupolygon
    INNER JOIN mapunit AS mu ON mupolygon.mukey = mu.mukey
    INNER JOIN component AS c ON mu.mukey = c.mukey
    WHERE mupolygon.mupolygongeo.STIntersects(geometry::STGeomFromText('{wkt}', 4326)) = 1
    AND c.majcompflag = 'Yes'
    """
    
    # Note: The geometry return might be huge. 
    # Strategy: Get the tabular data and geometry separately or simplify.
    # Actually, SDA returns JSON. Let's try a simpler approach: 
    # Get the geometry and attributes in one go if the area isn't too massive.
    # The Seattle-Tacoma corridor is large. This might timeout.
    
    # Alternative: Query by County FIPS (WA033 King, WA053 Pierce)
    # This is safer for large areas.
    
    query_county = """
    SELECT 
        mu.mukey, mu.musym, mu.muname, 
        c.compname, c.hydgrp,
        mupolygon.mupolygongeo.STAsText() as geometry
    FROM mapunit AS mu
    INNER JOIN component AS c ON mu.mukey = c.mukey
    INNER JOIN mupolygon ON mu.mukey = mupolygon.mukey
    WHERE mu.areasymbol IN ('WA033', 'WA053')
    AND c.majcompflag = 'Yes'
    """
    
    # This query is still likely to be too heavy for a single HTTP request due to geometry.
    # Let's try a lighter approach: Get attributes first, then geometry? 
    # Or just use the WFS service if available? SDA doesn't have WFS.
    # Let's try the spatial query but limit columns.
    
    # Actually, let's use the 'soil-data-access' package logic but implemented manually.
    # We will fetch data for the specific BBOX to limit size.
    
    payload = {
        "query": query,
        "format": "JSON+COLUMNNAME"
    }
    
    try:
        # This might fail if too large.
        # If it fails, we will fallback to a simplified query or mock data for now.
        # Real SSURGO download is complex without the dedicated package.
        # Let's try a very specific query for just the dominant component hydgrp.
        
        # Simplified query to reduce load:
        # 1. Get MUKEYS in BBOX
        # 2. Get Hydgrp for MUKEYS
        # 3. Get Geometry for MUKEYS (this is the heavy part)
        
        # Let's try downloading a simplified set.
        logging.info("  ...querying SDA (this may take a moment)...")
        r = requests.post(url, data=payload)
        r.raise_for_status()
        data = r.json()
        
        if 'Table' not in data:
            logging.warning("  No data returned from SSURGO query.")
            return None
            
        columns = data['Table'][0]
        rows = data['Table'][1:]
        
        # Convert to DataFrame
        df = pd.DataFrame(rows, columns=columns)
        
        # Parse Geometry (WKT)
        # This is slow in pure python for many rows.
        logging.info(f"  ...parsing {len(df)} soil polygons...")
        df['geometry'] = df['geometry'].apply(lambda x: shapely.wkt.loads(x) if x else None)
        
        gdf = gpd.GeoDataFrame(df, geometry='geometry', crs="EPSG:4326")
        
        output_path = RAW_DIR / 'soils' / 'ssurgo_download.gpkg'
        gdf.to_file(output_path, driver='GPKG')
        logging.info(f"✅ SSURGO soils downloaded to {output_path}")
        return output_path

    except Exception as e:
        logging.error(f"❌ Failed to download SSURGO: {e}")
        logging.info("  (The area might be too large for a single API call. Consider using the WSS website manually.)")
        return None

def download_osm_infrastructure():
    """
    Download 'similar' infrastructure data from OpenStreetMap via Overpass API.
    Targeting: Rain gardens, swales, retention basins, permeable paving.
    """
    logging.info("Downloading OSM Infrastructure data (GSI proxies)...")
    
    overpass_url = "http://overpass-api.de/api/interpreter"
    
    # Query for GSI-like features
    # surface=pervious_paving, surface=grass_paver
    # landuse=basin
    # natural=water + water=basin
    # description~"rain garden"
    # amenity=fountain (sometimes mis-tagged)
    # man_made=soakaway
    
    query = f"""
    [out:json][timeout:60];
    (
      way["surface"~"pervious|grass_paver"]({BBOX_STR});
      way["landuse"="basin"]({BBOX_STR});
      way["water"="basin"]({BBOX_STR});
      node["description"~"rain garden",i]({BBOX_STR});
      way["description"~"rain garden",i]({BBOX_STR});
      relation["description"~"rain garden",i]({BBOX_STR});
    );
    out geom;
    """
    
    try:
        r = requests.post(overpass_url, data=query)
        r.raise_for_status()
        data = r.json()
        
        features = []
        for element in data.get('elements', []):
            props = element.get('tags', {})
            props['osm_id'] = element['id']
            props['type'] = element['type']
            
            geom = None
            if element['type'] == 'node':
                geom = box(element['lon'], element['lat'], element['lon'], element['lat']) # Point as tiny box or just Point
                # Actually shapely Point
                from shapely.geometry import Point
                geom = Point(element['lon'], element['lat'])
            elif element['type'] == 'way' and 'geometry' in element:
                # Construct LineString or Polygon
                coords = [(pt['lon'], pt['lat']) for pt in element['geometry']]
                if len(coords) > 2 and coords[0] == coords[-1]:
                    geom = Polygon(coords)
                else:
                    from shapely.geometry import LineString
                    geom = LineString(coords)
            
            if geom:
                features.append({'geometry': geom, 'properties': props})
        
        if not features:
            logging.warning("  No OSM infrastructure found.")
            return None

        # Create GeoDataFrame
        gdf = gpd.GeoDataFrame.from_features(features, crs="EPSG:4326")
        
        # Add a 'source' column
        gdf['source'] = 'OpenStreetMap'
        
        output_path = RAW_DIR / 'infrastructure' / 'osm_gsi_proxy.gpkg'
        gdf.to_file(output_path, driver='GPKG')
        logging.info(f"✅ OSM Infrastructure downloaded to {output_path} ({len(gdf)} features)")
        return output_path

    except Exception as e:
        logging.error(f"❌ Failed to download OSM data: {e}")
        return None

def download_osm_rail():
    """Download Rail lines from OSM to supplement WSDOT data"""
    logging.info("Downloading OSM Rail data...")
    overpass_url = "http://overpass-api.de/api/interpreter"
    
    query = f"""
    [out:json][timeout:60];
    (
      way["railway"="rail"]({BBOX_STR});
      way["railway"="light_rail"]({BBOX_STR});
      way["railway"="tram"]({BBOX_STR});
    );
    out geom;
    """
    
    try:
        r = requests.post(overpass_url, data=query)
        r.raise_for_status()
        data = r.json()
        
        features = []
        for element in data.get('elements', []):
            props = element.get('tags', {})
            props['osm_id'] = element['id']
            
            if 'geometry' in element:
                coords = [(pt['lon'], pt['lat']) for pt in element['geometry']]
                from shapely.geometry import LineString
                geom = LineString(coords)
                features.append({'geometry': geom, 'properties': props})
                
        if not features:
            return None
            
        gdf = gpd.GeoDataFrame.from_features(features, crs="EPSG:4326")
        output_path = RAW_DIR / 'rail' / 'osm_rail.gpkg'
        gdf.to_file(output_path, driver='GPKG')
        logging.info(f"✅ OSM Rail downloaded to {output_path} ({len(gdf)} features)")
        return output_path
        
    except Exception as e:
        logging.error(f"❌ Failed to download OSM Rail: {e}")
        return None

def download_sound_transit_boundary():
    """Download Sound Transit District Boundary"""
    logging.info("Downloading Sound Transit District Boundary...")
    # URL from Sound Transit Open Data (GeoJSON)
    url = "https://opendata.arcgis.com/datasets/4d1545b4805e4633886859e89e5d40e4_0.geojson"
    # Note: This ID might change. Using a generic search or known stable one is better.
    # Fallback: King County Open Data for "Sound Transit District"
    
    try:
        r = requests.get(url)
        if r.status_code != 200:
            # Try alternative URL (King County)
            url = "https://gisdata.kingcounty.gov/arcgis/rest/services/OpenDataPortal/transportation_base/MapServer/469/query?where=1%3D1&outFields=*&outSR=4326&f=geojson"
            r = requests.get(url)
            
        r.raise_for_status()
        with open(RAW_DIR / 'rail' / 'sound_transit_boundary.geojson', 'wb') as f:
            f.write(r.content)
        logging.info(f"✅ Sound Transit Boundary downloaded.")
    except Exception as e:
        logging.error(f"❌ Failed to download Sound Transit boundary: {e}")

def main():
    print("="*60)
    print("STARTING AUTOMATED DATA DOWNLOAD")
    print("="*60)
    
    # 1. SVI
    download_svi_2020()
    
    # 2. SSURGO (May fail if area too large, but worth a try)
    download_ssurgo_soils()
    
    # 3. OSM Infrastructure (Filling the gap!)
    download_osm_infrastructure()
    
    # 4. OSM Rail (Supplement)
    download_osm_rail()
    
    # 5. Sound Transit
    download_sound_transit_boundary()
    
    print("\n" + "="*60)
    print("DOWNLOAD COMPLETE")
    print("="*60)
    print("Check data/raw/ for new files.")

if __name__ == "__main__":
    main()
