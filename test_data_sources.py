#!/usr/bin/env python3
"""
Test script to verify accessibility of external data sources
"""
import requests
import json
from datetime import datetime

def check_endpoint(name, url, method='GET', **kwargs):
    """Test if an endpoint is accessible"""
    print(f"\n{'='*70}")
    print(f"Testing: {name}")
    print(f"URL: {url}")
    print(f"{'='*70}")

    try:
        if method == 'GET':
            r = requests.get(url, timeout=15, **kwargs)
        elif method == 'POST':
            r = requests.post(url, timeout=15, **kwargs)
        elif method == 'HEAD':
            r = requests.head(url, timeout=15, **kwargs)

        print(f"Status Code: {r.status_code}")

        if r.status_code == 200:
            print("✅ ACCESSIBLE")

            # Try to parse JSON if applicable
            if 'application/json' in r.headers.get('Content-Type', ''):
                try:
                    data = r.json()
                    if 'layers' in data:
                        print(f"   Found {len(data['layers'])} layers")
                    if 'name' in data:
                        print(f"   Service Name: {data['name']}")
                except:
                    pass

            return True
        else:
            print(f"⚠️  NOT ACCESSIBLE (Status: {r.status_code})")
            return False

    except requests.exceptions.Timeout:
        print("❌ TIMEOUT - Service did not respond")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ CONNECTION ERROR - Cannot reach service")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def main():
    print("\n" + "="*70)
    print("EXTERNAL DATA SOURCE ACCESSIBILITY TEST")
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)

    results = {}

    # 1. FEMA NFHL (National Flood Hazard Layer)
    results['FEMA NFHL'] = check_endpoint(
        "FEMA NFHL - National Flood Hazard Layer",
        "https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer",
        params={'f': 'json'}
    )

    # 2. USDA SSURGO Soils
    results['USDA SSURGO'] = check_endpoint(
        "USDA SSURGO - Soil Data Access API",
        "https://sdmdataaccess.nrcs.usda.gov/Tabular/post.rest",
        method='POST',
        json={'query': 'SELECT 1 FROM mapunit FETCH FIRST 1 ROWS ONLY'},
        headers={'Content-Type': 'application/json'}
    )

    # 3. NLCD Data Portal (main page)
    results['MRLC NLCD Portal'] = check_endpoint(
        "MRLC NLCD Data Portal",
        "https://www.mrlc.gov/data"
    )

    # 4. NOAA Atlas 14 (info page)
    results['NOAA Atlas 14'] = check_endpoint(
        "NOAA Atlas 14 Precipitation Data",
        "https://hdsc.nws.noaa.gov/pfds/"
    )

    # 5. USGS National Map (elevation data portal)
    results['USGS National Map'] = check_endpoint(
        "USGS National Map - Elevation Products",
        "https://apps.nationalmap.gov/services"
    )

    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)

    total = len(results)
    accessible = sum(1 for v in results.values() if v)

    for service, status in results.items():
        icon = "✅" if status else "❌"
        print(f"{icon} {service}")

    print(f"\nTotal: {accessible}/{total} services accessible")

    if accessible == total:
        print("\n🎉 All data sources are accessible!")
    elif accessible > 0:
        print(f"\n⚠️  {total - accessible} service(s) need attention")
    else:
        print("\n❌ No services are accessible - check network connection")

    # Specific notes
    print("\n" + "="*70)
    print("NOTES")
    print("="*70)
    print("""
1. FEMA NFHL: Use the corrected URL with '/arcgis' path
   - Correct: hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer
   - Old (404): hazards.fema.gov/gis/rest/services/NFHL/MapServer

2. NLCD Imperviousness: Direct file downloads not available via simple URL
   - Must use MRLC viewer tool: https://www.mrlc.gov/viewer/
   - Or download from: https://www.mrlc.gov/data
   - Files are hosted on S3 with dynamic URLs

3. NOAA Atlas 14: No public JSON API available
   - Requires manual lookup: https://hdsc.nws.noaa.gov/pfds/
   - Must enter coordinates and manually extract values

4. USDA SSURGO: Fully accessible via REST API ✅

5. USGS National Map: Elevation data available via multiple services
   - 3DEP Elevation products
   - The National Map viewer
    """)


if __name__ == '__main__':
    main()
