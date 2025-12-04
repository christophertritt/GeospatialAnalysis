# Comprehensive Data Acquisition Plan
## Seattle-Tacoma Rail Corridor Flood Vulnerability Analysis

**Study Area:** -122.50, 47.20, -122.25, 47.65 (Seattle to Tacoma)

---

## 1. RAIL CORRIDOR DATA (REQUIRED)

### Primary Source: Sound Transit
- **URL:** https://www.soundtransit.org/help-contacts/business-information/maps-property-lines
- **Coverage:** Sounder commuter rail, Link light rail
- **Format:** Shapefile/KML
- **Action:** Contact GIS team or download from open data portal

### Alternative: WSDOT GeoData Portal
- **URL:** https://gisdata-wsdot.opendata.arcgis.com/
- **Search:** "railroad" or "rail"
- **Dataset:** Washington State Rail System
- **Format:** Shapefile
- **Status:** PUBLIC

### Alternative: OpenStreetMap
- **URL:** https://overpass-turbo.eu/
- **Query:**
```
[bbox:47.20,-122.50,47.65,-122.25];
(
  way[railway=rail];
  way[railway=light_rail];
  way[railway=subway];
);
out geom;
```
- **Export:** GeoJSON → Convert to shapefile

### Alternative: FRA National Rail Network
- **URL:** https://geodata.bts.gov/datasets/north-american-rail-network-lines
- **Coverage:** Federal Railroad Administration data
- **Format:** Shapefile/GeoJSON

---

## 2. PERMEABLE PAVEMENT / GREEN INFRASTRUCTURE (REQUIRED)

### Primary: Seattle Public Utilities
- **URL:** https://data.seattle.gov/
- **Search terms:**
  - "Green Stormwater Infrastructure"
  - "GSI Facilities"
  - "Permeable Pavement"
  - "Bioretention"
  - "Rain Gardens"
- **Likely datasets:**
  - Seattle Public Utilities Assets
  - Right-of-Way Improvements
  - Green Stormwater Infrastructure Projects

### Primary: Tacoma Public Works
- **URL:** https://data.cityoftacoma.org/
- **Search:** "stormwater" or "infrastructure"
- **Contact:** Tacoma Environmental Services at 253-591-5525

### Alternative: King County iMap
- **URL:** https://www.kingcounty.gov/services/gis/Maps/imap.aspx
- **Layers:** Check Stormwater/Drainage layers
- **Download:** Available for registered users

### Alternative: Pierce County GIS
- **URL:** https://www.piercecountywa.gov/1758/GIS-Data-Download
- **Layers:** Infrastructure, Stormwater

### Alternative: Request from jurisdictions
- Seattle Public Utilities: (206) 684-3000
- Tacoma Environmental Services: (253) 591-5525
- King County Stormwater: (206) 477-4800
- Pierce County Public Works: (253) 798-3600

### Manual Mapping Option
If no existing data:
- Use aerial imagery to identify permeable pavement
- Field surveys of rail station areas
- Create point/polygon layer with attributes:
  - FacilityID
  - AreaSqFt
  - InstallYear
  - Type (permeable pavement, bioretention, etc.)

---

## 3. NLCD IMPERVIOUSNESS RASTER (REQUIRED)

### Primary: MRLC Data Download
- **URL:** https://www.mrlc.gov/data
- **Direct download:** https://s3-us-west-2.amazonaws.com/mrlc/
- **Product:** NLCD 2021 Percent Developed Imperviousness
- **File:** nlcd_2021_impervious_l48_20230630.img
- **Size:** ~11 GB (nationwide)
- **Action:** Download full file, then clip to AOI

### Alternative: MRLC Viewer (subset download)
- **URL:** https://www.mrlc.gov/viewer/
- **Steps:**
  1. Draw AOI on map
  2. Select "NLCD 2021 Imperviousness"
  3. Download clipped GeoTIFF
- **Advantage:** Smaller file size

### Alternative: Google Earth Engine
```python
import ee
ee.Initialize()
nlcd = ee.ImageCollection('USGS/NLCD_RELEASES/2021_REL/NLCD')
imperviousness = nlcd.select('impervious').first()
geometry = ee.Geometry.Rectangle([-122.50, 47.20, -122.25, 47.65])
task = ee.batch.Export.image.toDrive({
    'image': imperviousness,
    'region': geometry,
    'scale': 30,
    'fileNamePrefix': 'seattle_tacoma_imperviousness'
})
task.start()
```

### Alternative: EarthExplorer
- **URL:** https://earthexplorer.usgs.gov/
- **Search:** "NLCD Imperviousness"
- **Filter by:** Seattle-Tacoma coordinates

---

## 4. ELEVATION / DEM DATA (RECOMMENDED)

### Primary: USGS National Map Downloader
- **URL:** https://apps.nationalmap.gov/downloader/
- **Product:** 1/3 arc-second DEM (10m resolution)
- **Steps:**
  1. Enter bbox: -122.50, 47.20, -122.25, 47.65
  2. Select "Elevation Products (3DEP)"
  3. Filter: 1/3 arc-second DEM
  4. Download all tiles (likely 4-6 tiles)
  5. Mosaic with: `gdal_merge.py -o dem_aoi.tif tile*.tif`

### Alternative: OpenTopography
- **URL:** https://opentopography.org/
- **Product:** High-resolution LiDAR if available
- **Coverage:** Check for Puget Sound region
- **Advantage:** Higher resolution (1m) in urban areas

### Alternative: USGS Earth Explorer
- **URL:** https://earthexplorer.usgs.gov/
- **Dataset:** SRTM or ASTER GDEM
- **Resolution:** 30m (lower quality than 3DEP)

### Alternative: Washington State Lidar Portal
- **URL:** https://lidarportal.dnr.wa.gov/
- **Coverage:** Check for Seattle/Tacoma coverage
- **Resolution:** Sub-meter
- **Format:** LAS point clouds (need to generate DEM)

---

## 5. FEMA FLOOD ZONES (AUTOMATED)

### Primary: Automated via script
```bash
python download_data.py --bbox "-122.50,47.20,-122.25,47.65" --verbose
```
- **API:** https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer
- **Status:** ✅ Working (fixed URL)
- **Output:** data/processed/flood/nfhl_aoi.gpkg

### Alternative: FEMA Map Service Center
- **URL:** https://msc.fema.gov/portal/home
- **Steps:**
  1. Search by address or coordinates
  2. Download FIRMette or full DFIRM
  3. Extract flood zone polygons

---

## 6. SSURGO SOILS DATA (RECOMMENDED)

### Primary: Web Soil Survey
- **URL:** https://websoilsurvey.nrcs.usda.gov/
- **Steps:**
  1. Click "Start WSS"
  2. Define AOI (Seattle-Tacoma bbox)
  3. Soil Data Explorer → Download Soils Data
  4. Select "Spatial Data" (shapefile)
  5. Download and extract

### Alternative: Automated script (may need refinement)
```bash
python download_data.py --bbox "-122.50,47.20,-122.25,47.65" --verbose
```
- **Note:** API queries need refinement, may produce incomplete data

### Alternative: NRCS Data Gateway
- **URL:** https://datagateway.nrcs.usda.gov/
- **Product:** gSSURGO by State
- **Download:** Washington state gSSURGO geodatabase
- **Size:** ~500 MB
- **Action:** Extract and clip to AOI

---

## 7. NOAA ATLAS 14 PRECIPITATION (RECOMMENDED)

### Primary: Manual lookup
- **URL:** https://hdsc.nws.noaa.gov/pfds/
- **Coordinates:** 47.425, -122.375 (study area center)
- **Data needed:** 24-hour precipitation depths for:
  - 2-year storm
  - 10-year storm
  - 25-year storm

### Alternative: Use Seattle defaults (hardcoded)
Already in `scripts/runoff_modeling.py`:
- 2-year: 2.2 inches
- 10-year: 2.9 inches
- 25-year: 3.4 inches

---

## EXECUTION PLAN

### Phase 1: Automated Downloads (15 minutes)
```bash
# Download FEMA flood zones
python download_data.py --bbox "-122.50,47.20,-122.25,47.65" --verbose

# Test API connectivity
python test_data_sources.py
```

### Phase 2: Rail Corridor (1-2 hours)
**Priority order:**
1. Try WSDOT GeoData Portal (fastest)
2. If unavailable, use OpenStreetMap export
3. If quality insufficient, contact Sound Transit

### Phase 3: Permeable Pavement (2-4 hours)
**Priority order:**
1. Search Seattle Open Data Portal
2. Search Tacoma Open Data Portal
3. Request from Seattle Public Utilities
4. Request from Tacoma Environmental Services
5. If none available, create manual inventory

### Phase 4: NLCD Imperviousness (30-60 minutes)
**Priority order:**
1. MRLC Viewer (clipped download - fastest)
2. Full download from S3 + clip (if viewer fails)
3. Google Earth Engine (if have account)

### Phase 5: Elevation DEM (30-60 minutes)
**Priority order:**
1. USGS National Map Downloader (3DEP)
2. OpenTopography (if LiDAR available)
3. Washington State Lidar Portal (highest quality)

### Phase 6: Soils Data (30 minutes)
**Priority order:**
1. Web Soil Survey manual download
2. Automated script (if API works)

### Phase 7: Data Validation
```bash
# Check all files exist
ls -lh data/raw/rail/
ls -lh data/raw/infrastructure/
ls -lh data/raw/landcover/
ls -lh data/raw/elevation/
ls -lh data/processed/flood/
ls -lh data/processed/soils/

# Validate data quality
python scripts/verify_data.py
```

### Phase 8: Run Analysis
```bash
python scripts/geospatial_analysis.py \
  --rail data/raw/rail/seattle_tacoma_corridor.shp \
  --infrastructure data/raw/infrastructure/permeable_pavement.shp \
  --imperviousness data/raw/landcover/nlcd_2021_impervious_aoi.tif \
  --dem data/raw/elevation/dem_aoi.tif \
  --soils data/processed/soils/ssurgo_aoi.gpkg \
  --output-dir data/outputs \
  --verbose
```

---

## FALLBACK OPTIONS

### If permeable pavement data not available:
- Focus analysis on "gap identification" rather than "alignment assessment"
- Use analysis to identify WHERE facilities SHOULD be placed
- Document as recommendation for future facility inventory

### If DEM not available:
- Use default slope values based on USGS topographic classifications
- Note limitation in analysis report

### If soils data not available:
- Use default hydrologic soil group 'C' (moderate infiltration)
- Note assumption in report

---

## ESTIMATED TIMELINE

- **Automated downloads:** 15 minutes
- **Rail corridor:** 1-2 hours
- **Permeable pavement:** 2-4 hours (most uncertain)
- **NLCD imperviousness:** 30-60 minutes
- **Elevation DEM:** 30-60 minutes
- **Soils data:** 30 minutes
- **Data validation:** 30 minutes
- **Analysis execution:** 15-30 minutes

**Total:** 5-9 hours (depending on data availability)

---

## CONTACT INFORMATION

- **Sound Transit GIS:** gis@soundtransit.org
- **Seattle Public Utilities:** (206) 684-3000
- **Tacoma Environmental Services:** (253) 591-5525
- **WSDOT GeoData:** GeoDataDistribution@wsdot.wa.gov
- **King County GIS:** gis@kingcounty.gov
- **Pierce County GIS:** pcgis@piercecountywa.gov
