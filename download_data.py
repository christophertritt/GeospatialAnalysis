#!/usr/bin/env python3
"""
Comprehensive data download script for GeospatialAnalysis project
Downloads all required external data sources for analysis
"""
import argparse
import logging
from pathlib import Path
import sys

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent / 'scripts'))

from data_acquisition import (
    fetch_fema_nfhl_by_bbox,
    fetch_ssurgo_soils_by_bbox,
    fetch_nlcd_impervious,
    fetch_noaa_atlas14_depths,
    clip_file_to_bbox
)

def setup_logging(verbose=False):
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='[%(levelname)s] %(message)s'
    )

def print_banner(text):
    """Print formatted banner"""
    print("\n" + "="*70)
    print(text)
    print("="*70)

def download_all_data(bbox, nlcd_year=2019, verbose=False):
    """
    Download all required data for the analysis

    Args:
        bbox: Dictionary with {minx, miny, maxx, maxy} in WGS84
        nlcd_year: Year for NLCD data
        verbose: Enable verbose logging
    """
    setup_logging(verbose)

    print_banner("GEOSPATIAL ANALYSIS - DATA DOWNLOAD")
    print(f"\nArea of Interest:")
    print(f"  BBox: {bbox}")
    print(f"  NLCD Year: {nlcd_year}")

    results = {}

    # 1. FEMA NFHL Flood Zones
    print_banner("1. FEMA NFHL - Flood Hazard Zones")
    try:
        nfhl_path = fetch_fema_nfhl_by_bbox(bbox)
        if nfhl_path and nfhl_path.exists():
            # Clip to AOI and reproject
            clipped = clip_file_to_bbox(
                nfhl_path,
                bbox,
                'flood',
                'nfhl_aoi',
                target_epsg=2927
            )
            results['flood_zones'] = clipped
            print(f"✅ SUCCESS: {clipped}")
        else:
            print("❌ FAILED: FEMA NFHL download failed")
            results['flood_zones'] = None
    except Exception as e:
        logging.error(f"FEMA NFHL error: {e}")
        results['flood_zones'] = None

    # 2. SSURGO Soils
    print_banner("2. USDA SSURGO - Soil Data")
    try:
        soils_path = fetch_ssurgo_soils_by_bbox(bbox)
        if soils_path and soils_path.exists():
            results['soils'] = soils_path
            print(f"✅ SUCCESS: {soils_path}")
            print("   Note: May need manual processing from Web Soil Survey")
        else:
            print("❌ FAILED: SSURGO download failed")
            print("   Alternative: Download from https://websoilsurvey.nrcs.usda.gov/")
            results['soils'] = None
    except Exception as e:
        logging.error(f"SSURGO error: {e}")
        print("❌ FAILED: SSURGO download failed")
        print("   Alternative: Download from https://websoilsurvey.nrcs.usda.gov/")
        results['soils'] = None

    # 3. NLCD Imperviousness
    print_banner("3. NLCD Imperviousness Raster")
    print("⚠️  MANUAL DOWNLOAD REQUIRED")
    print("\nNLCD files are very large and require manual download:")
    print("  1. Visit: https://www.mrlc.gov/viewer/")
    print("  2. Select your area of interest")
    print(f"  3. Download NLCD {nlcd_year} Imperviousness layer")
    print("  4. Place file in: data/raw/landcover/")
    print("  5. Recommended filename: nlcd_2019_impervious_aoi.tif")
    print("\nAttempting automatic download (may fail)...")

    try:
        nlcd_path = fetch_nlcd_impervious(nlcd_year)
        if nlcd_path and nlcd_path.exists():
            results['imperviousness'] = nlcd_path
            print(f"✅ SUCCESS: {nlcd_path}")
        else:
            print("❌ Automatic download failed (expected)")
            results['imperviousness'] = None
    except Exception as e:
        logging.debug(f"NLCD error: {e}")
        results['imperviousness'] = None

    # 4. NOAA Atlas 14 Precipitation
    print_banner("4. NOAA Atlas 14 - Design Storm Depths")
    print("⚠️  MANUAL ENTRY REQUIRED")

    lat = (bbox['miny'] + bbox['maxy']) / 2.0
    lon = (bbox['minx'] + bbox['maxx']) / 2.0

    try:
        atlas14_path = fetch_noaa_atlas14_depths(lat, lon)
        if atlas14_path:
            results['precipitation'] = atlas14_path
            print(f"✅ Placeholder created: {atlas14_path}")
            print("\nTo complete:")
            print(f"  1. Visit: https://hdsc.nws.noaa.gov/pfds/")
            print(f"  2. Enter coordinates: {lat:.5f}, {lon:.5f}")
            print("  3. Copy 24-hour precipitation depths for 2-year, 10-year, 25-year storms")
            print(f"  4. Update the JSON file: {atlas14_path}")
            print("\nAlternatively, hardcoded Seattle values are in scripts/runoff_modeling.py")
        else:
            print("❌ FAILED: Could not create placeholder")
            results['precipitation'] = None
    except Exception as e:
        logging.error(f"Atlas 14 error: {e}")
        results['precipitation'] = None

    # 5. Elevation/DEM Data
    print_banner("5. USGS Elevation/DEM Data")
    print("⚠️  MANUAL DOWNLOAD REQUIRED")
    print("\nElevation data must be downloaded manually:")
    print("  1. Visit: https://apps.nationalmap.gov/downloader/")
    print("  2. Select '3DEP Elevation Products'")
    print(f"  3. Enter bbox or draw on map:")
    print(f"     Min Lon: {bbox['minx']}, Min Lat: {bbox['miny']}")
    print(f"     Max Lon: {bbox['maxx']}, Max Lat: {bbox['maxy']}")
    print("  4. Download 1/3 arc-second DEM (or best available)")
    print("  5. Place file in: data/raw/elevation/")
    print("  6. Recommended filename: dem_aoi.tif")
    results['elevation'] = None

    # 6. Rail Corridor Data
    print_banner("6. Rail Corridor Data")
    print("⚠️  MANUAL DOWNLOAD REQUIRED")
    print("\nRail corridor data sources:")
    print("  Option 1: WSDOT GeoData Portal")
    print("    - Visit: https://gisdata-wsdot.opendata.arcgis.com/")
    print("    - Search: 'rail' or 'railroad'")
    print("    - Download and place in: data/raw/rail/")
    print("\n  Option 2: Local Transit Agency")
    print("    - Sound Transit, King County Metro, etc.")
    print("\n  Option 3: OpenStreetMap")
    print("    - Export railway=rail features")
    print("    - Use QGIS or overpass-turbo")
    results['rail'] = None

    # 7. Infrastructure Data
    print_banner("7. Permeable Pavement / Green Infrastructure")
    print("⚠️  MANUAL DOWNLOAD REQUIRED")
    print("\nGreen infrastructure data sources:")
    print("  Option 1: Seattle Open Data")
    print("    - Visit: https://data.seattle.gov/")
    print("    - Search: 'stormwater' or 'green infrastructure'")
    print("    - Download and place in: data/raw/infrastructure/")
    print("\n  Option 2: Local Stormwater/Public Works Department")
    print("    - Request GI facility inventory")
    print("\n  Option 3: Manual Mapping")
    print("    - Create point/polygon layer of known facilities")
    print("    - Include 'AreaSqFt' attribute for facility size")
    results['infrastructure'] = None

    # Summary
    print_banner("DOWNLOAD SUMMARY")

    auto_downloads = {
        'FEMA Flood Zones': results.get('flood_zones'),
        'SSURGO Soils': results.get('soils'),
    }

    manual_required = {
        'NLCD Imperviousness': 'data/raw/landcover/nlcd_2019_impervious_aoi.tif',
        'NOAA Atlas 14': str(results.get('precipitation', 'data/raw/precip/atlas14_*.json')),
        'Elevation/DEM': 'data/raw/elevation/dem_aoi.tif',
        'Rail Corridor': 'data/raw/rail/corridor.shp',
        'Infrastructure': 'data/raw/infrastructure/permeable_pavement.shp'
    }

    print("\nAutomated Downloads:")
    for name, path in auto_downloads.items():
        if path and Path(path).exists():
            print(f"  ✅ {name}: {path}")
        else:
            print(f"  ❌ {name}: Failed")

    print("\nManual Downloads Required:")
    for name, path in manual_required.items():
        print(f"  ⚠️  {name}")
        print(f"      Expected location: {path}")

    print("\nNext Steps:")
    print("  1. Complete manual downloads listed above")
    print("  2. Verify all files are in place:")
    print("     python scripts/verify_data.py")
    print("  3. Run analysis:")
    print("     python scripts/geospatial_analysis.py \\")
    print("       --rail data/raw/rail/corridor.shp \\")
    print("       --infrastructure data/raw/infrastructure/permeable_pavement.shp \\")
    print("       --config config.yaml")

    return results


def parse_bbox(s):
    """Parse bbox string into dictionary"""
    try:
        parts = [float(x.strip()) for x in s.split(',')]
        if len(parts) != 4:
            raise ValueError
        return {'minx': parts[0], 'miny': parts[1], 'maxx': parts[2], 'maxy': parts[3]}
    except Exception:
        raise argparse.ArgumentTypeError('BBox must be "minx,miny,maxx,maxy" in WGS84')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Download geospatial data for analysis',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Seattle area (default)
  python download_data.py

  # Custom area
  python download_data.py --bbox "-122.5,47.5,-122.0,48.0"

  # Tacoma area
  python download_data.py --bbox "-122.5,47.1,-122.3,47.3"
        """
    )

    parser.add_argument(
        '--bbox',
        type=parse_bbox,
        help='Bounding box as "minx,miny,maxx,maxy" in WGS84 (default: Downtown Seattle)'
    )
    parser.add_argument(
        '--nlcd-year',
        type=int,
        default=2019,
        help='NLCD year (default: 2019)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    # Default to downtown Seattle if no bbox provided
    if not args.bbox:
        args.bbox = {'minx': -122.36, 'miny': 47.58, 'maxx': -122.30, 'maxy': 47.62}
        print("Using default bbox: Downtown Seattle")

    download_all_data(args.bbox, args.nlcd_year, args.verbose)
