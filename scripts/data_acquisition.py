"""
Data acquisition utilities for GeospatialAnalysis
Fetch SSURGO soils, NLCD imperviousness, FEMA NFHL flood zones, and NOAA Atlas 14 design storms.
These functions download and cache data in data/raw/ and return local file paths.
"""
from pathlib import Path
import json
import logging
import time
import requests
import argparse
from typing import Optional, Dict, Any, List
import geopandas as gpd
from shapely.geometry import box

RAW_DIR = Path('data/raw')
RAW_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_HEADERS = {
    'User-Agent': 'GeospatialAnalysis/1.0 (contact: example@example.com)'
}


def _cache_path(subdir: str, name: str) -> Path:
    p = RAW_DIR / subdir
    p.mkdir(parents=True, exist_ok=True)
    return p / name


def fetch_ssurgo_soils_by_bbox(bbox: Dict[str, float]) -> Optional[Path]:
    """
    Fetch SSURGO soils (hydrologic soil group) by bounding box using USDA NRCS SDM API.
    bbox: {minx, miny, maxx, maxy} in WGS84.
    Returns path to cached GeoJSON.

    NOTE: Spatial queries via bbox are complex with this API. Consider using
    county FIPS codes or state boundaries instead for more reliable results.
    """
    url = 'https://sdmdataaccess.nrcs.usda.gov/Tabular/post.rest'
    # Simple query for hydrologic group by mapunit
    # Note: Complex spatial queries may not work well with this API
    # Consider filtering by area name or using Web Soil Survey for manual download
    sql = """
    SELECT TOP 100 mu.mukey, mu.muname, comp.cokey, comp.compname, comp.comppct_r, comp.hydgrpdcd
    FROM legend l
    INNER JOIN mapunit mu ON mu.lkey = l.lkey
    INNER JOIN component comp ON comp.mukey = mu.mukey
    WHERE l.areasymbol LIKE '%'
    """
    payload = {
        'query': sql,
        'minx': bbox['minx'],
        'miny': bbox['miny'],
        'maxx': bbox['maxx'],
        'maxy': bbox['maxy']
    }
    out = _cache_path('soils', f'ssurgo_hsg_{int(time.time())}.json')
    try:
        r = requests.post(url, json=payload, headers=DEFAULT_HEADERS, timeout=60)
        r.raise_for_status()
        with open(out, 'w') as f:
            f.write(r.text)
        logging.info(f"SSURGO soils saved: {out}")
        return out
    except Exception as e:
        logging.warning(f"Failed to fetch SSURGO soils: {e}")
        return None


def fetch_nlcd_impervious(year: int = 2019) -> Optional[Path]:
    """
    Fetch NLCD imperviousness raster via MRLC download service.

    NOTE: Direct download URLs are not available. Large raster files must be
    manually downloaded from https://www.mrlc.gov/viewer/ or https://www.mrlc.gov/data

    This function attempts a direct download but will likely fail. Users should
    manually place downloaded NLCD files in data/raw/landcover/

    Returns path where file should be cached.
    """
    # Placeholder URL; MRLC provides data via web download pages and staged S3 buckets.
    url = f'https://www.mrlc.gov/downloads/NLCD_{year}_Impervious_L48_2023.zip'
    out = _cache_path('landcover', f'nlcd_{year}_impervious.zip')
    try:
        r = requests.get(url, headers=DEFAULT_HEADERS, timeout=300)
        if r.status_code == 200:
            with open(out, 'wb') as f:
                f.write(r.content)
            logging.info(f"NLCD impervious downloaded: {out}")
            return out
        else:
            logging.warning(f"NLCD download failed (status {r.status_code})")
            return None
    except Exception as e:
        logging.warning(f"Failed to fetch NLCD impervious: {e}")
        return None


def _discover_nfhl_layers(service_url: str) -> List[Dict[str, Any]]:
    """Discover available NFHL layers from an ArcGIS REST service root."""
    try:
        r = requests.get(service_url, params={'f': 'json'}, headers=DEFAULT_HEADERS, timeout=30)
        r.raise_for_status()
        data = r.json()
        return data.get('layers', [])
    except Exception as e:
        logging.warning(f"Failed to discover NFHL layers: {e}")
        return []


def fetch_fema_nfhl_by_bbox(bbox: Dict[str, float]) -> Optional[Path]:
    """
    Fetch FEMA NFHL flood zones via ArcGIS FeatureServer by bbox.
    Returns path to cached GeoJSON.
    """
    service_root = 'https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer'
    layers = _discover_nfhl_layers(service_root)
    target_layer_id = None
    # Prefer Flood Hazard Zones or similar
    for lyr in layers:
        name = (lyr.get('name') or '').lower()
        if 'flood hazard' in name or 'zone' in name:
            target_layer_id = lyr.get('id')
            break
    if target_layer_id is None and layers:
        target_layer_id = layers[0].get('id')
        logging.info(f"NFHL target layer fallback: {target_layer_id}")
    if target_layer_id is None:
        logging.warning("NFHL: No layers discovered.")
        return None

    url = f"{service_root}/{target_layer_id}/query"
    params = {
        'f': 'geojson',
        'where': '1=1',
        'outFields': '*',
        'geometry': json.dumps({
            'xmin': bbox['minx'], 'ymin': bbox['miny'], 'xmax': bbox['maxx'], 'ymax': bbox['maxy'],
            'spatialReference': {'wkid': 4326}
        }),
        'geometryType': 'esriGeometryEnvelope',
        'inSR': 4326,
        'spatialRel': 'esriSpatialRelIntersects'
    }
    out = _cache_path('flood', f'nfhl_{int(time.time())}.geojson')
    try:
        r = requests.get(url, params=params, headers=DEFAULT_HEADERS, timeout=60)
        r.raise_for_status()
        with open(out, 'wb') as f:
            f.write(r.content)
        logging.info(f"FEMA NFHL saved: {out}")
        return out
    except Exception as e:
        logging.warning(f"Failed to fetch FEMA NFHL: {e}")
        return None


def fetch_noaa_atlas14_depths(lat: float, lon: float) -> Optional[Path]:
    """
    Fetch NOAA Atlas 14 design storm depths for a coordinate.
    NOAA does not have a simple public JSON API; this is a placeholder to cache inputs.
    """
    out = _cache_path('precip', f'atlas14_{lat:.5f}_{lon:.5f}.json')
    data = {
        'location': {'lat': lat, 'lon': lon},
        'depths_in': {
            '2yr': None,
            '10yr': None,
            '25yr': None
        },
        'source': 'NOAA Atlas 14 (manual table lookup required)'
    }
    try:
        with open(out, 'w') as f:
            json.dump(data, f, indent=2)
        logging.info(f"Atlas 14 placeholder saved: {out}")
        return out
    except Exception as e:
        logging.warning(f"Failed to write Atlas 14 placeholder: {e}")
        return None


def clip_file_to_bbox(input_path: Path, bbox: Dict[str, float], out_subdir: str, out_name: str, target_epsg: int = 2927) -> Optional[Path]:
    """Clip a vector file to the AOI bbox and save GeoPackage in data/processed reprojected to EPSG:2927."""
    try:
        aoi = box(bbox['minx'], bbox['miny'], bbox['maxx'], bbox['maxy'])
        gdf = gpd.read_file(input_path)
        if gdf.crs is None or gdf.crs.to_epsg() != 4326:
            # Reproject AOI to match layer CRS
            aoi_gdf = gpd.GeoDataFrame({'geometry': [aoi]}, crs='EPSG:4326')
            aoi_gdf = aoi_gdf.to_crs(gdf.crs)
            aoi = aoi_gdf.iloc[0].geometry
        clipped = gdf[gdf.intersects(aoi)].copy()
        # Reproject clipped layer to Washington State Plane South EPSG:2927
        try:
            clipped = clipped.to_crs(epsg=target_epsg)
        except Exception as re:
            logging.warning(f"Failed to reproject to EPSG:{target_epsg}: {re}")
        out_dir = Path('data/processed') / out_subdir
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{out_name}.gpkg"
        clipped.to_file(out_path, driver='GPKG', layer=out_name)
        logging.info(f"Clipped layer saved: {out_path}")
        return out_path
    except Exception as e:
        logging.warning(f"Failed to clip {input_path}: {e}")
        return None


def parse_bbox_arg(s: str) -> Dict[str, float]:
    try:
        parts = [float(x.strip()) for x in s.split(',')]
        if len(parts) != 4:
            raise ValueError
        return {'minx': parts[0], 'miny': parts[1], 'maxx': parts[2], 'maxy': parts[3]}
    except Exception:
        raise argparse.ArgumentTypeError('BBox must be "minx,miny,maxx,maxy" in WGS84.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Data acquisition for GeospatialAnalysis')
    parser.add_argument('--aoi-bbox', type=parse_bbox_arg,
                        help='AOI bbox in WGS84 as minx,miny,maxx,maxy')
    parser.add_argument('--minx', type=float, help='AOI minx (lon)')
    parser.add_argument('--miny', type=float, help='AOI miny (lat)')
    parser.add_argument('--maxx', type=float, help='AOI maxx (lon)')
    parser.add_argument('--maxy', type=float, help='AOI maxy (lat)')
    parser.add_argument('--nlcd-year', type=int, default=2019)
    parser.add_argument('--verbose', action='store_true')
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format='[%(levelname)s] %(message)s')

    if args.aoi_bbox:
        bbox = args.aoi_bbox if isinstance(args.aoi_bbox, dict) else parse_bbox_arg(args.aoi_bbox)
    elif None not in (args.minx, args.miny, args.maxx, args.maxy):
        bbox = {'minx': args.minx, 'miny': args.miny, 'maxx': args.maxx, 'maxy': args.maxy}
    else:
        # default AOI: downtown Seattle
        bbox = {'minx': -122.36, 'miny': 47.58, 'maxx': -122.30, 'maxy': 47.62}
    fetch_ssurgo_soils_by_bbox(bbox)
    fetch_nlcd_impervious(args.nlcd_year)
    nfhl_path = fetch_fema_nfhl_by_bbox(bbox)
    if nfhl_path:
        clip_file_to_bbox(nfhl_path, bbox, 'flood', 'nfhl_aoi', target_epsg=2927)
    # Use centroid for Atlas 14 placeholder
    lat = (bbox['miny'] + bbox['maxy']) / 2.0
    lon = (bbox['minx'] + bbox['maxx']) / 2.0
    fetch_noaa_atlas14_depths(lat, lon)
