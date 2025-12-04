# Data Acquisition Workflow

Complete guide for downloading and preparing all required data for geospatial analysis.

---

## Quick Start

```bash
# 1. Download external data
python download_data.py --bbox "-122.36,47.58,-122.30,47.62"

# 2. Complete manual downloads (see below)

# 3. Run analysis
python scripts/geospatial_analysis.py \
  --rail data/raw/rail/corridor.shp \
  --infrastructure data/raw/infrastructure/permeable_pavement.shp \
  --imperviousness data/raw/landcover/nlcd_2019_impervious_aoi.tif \
  --dem data/raw/elevation/dem_aoi.tif \
  --soils data/processed/soils/ssurgo_aoi.gpkg \
  --verbose
```

---

## Step-by-Step Instructions

### Step 1: Define Area of Interest (AOI)

Determine your bounding box in WGS84 (EPSG:4326):

```
Format: minx,miny,maxx,maxy
Example (Seattle): -122.36,47.58,-122.30,47.62
Example (Tacoma): -122.5,47.1,-122.3,47.3
```

You can use:
- [bboxfinder.com](http://bboxfinder.com/)
- QGIS: Layer → Export → Save Features As... → View extent

### Step 2: Run Automated Download Script

```bash
python download_data.py --bbox "YOUR_BBOX_HERE" --verbose
```

This will automatically download:
- ✅ **FEMA NFHL Flood Zones** → `data/processed/flood/nfhl_aoi.gpkg`
- ⚠️ **SSURGO Soils** → `data/raw/soils/` (may need manual processing)

And provide instructions for manual downloads.

---

## Required Manual Downloads

### 1. NLCD Imperviousness Raster ⚠️

**Why manual:** Files are very large (multi-GB) and hosted on S3 with dynamic URLs.

**Steps:**
1. Visit: https://www.mrlc.gov/viewer/
2. Click "Draw AOI" or "Upload AOI"
3. Select:
   - Product: "NLCD 2019 Impervious Surface"
   - Format: "GeoTIFF"
4. Click "Download"
5. Save to: `data/raw/landcover/nlcd_2019_impervious_aoi.tif`

**Alternative:** Use Google Earth Engine:
```python
import ee
ee.Initialize()
nlcd = ee.ImageCollection('USGS/NLCD_RELEASES/2019_REL/NLCD')
impervious = nlcd.select('impervious')
```

---

### 2. Elevation/DEM Data ⚠️

**Why manual:** Large raster files, need to select appropriate resolution.

**Steps:**
1. Visit: https://apps.nationalmap.gov/downloader/
2. Click "Find Products"
3. Select "Elevation Products (3DEP)"
4. Draw your AOI on the map or enter bbox coordinates
5. Filter by:
   - Product: "1/3 arc-second DEM" (best for urban areas)
   - Format: "GeoTIFF"
6. Download all tiles covering your AOI
7. If multiple tiles, mosaic them:
   ```bash
   gdal_merge.py -o data/raw/elevation/dem_aoi.tif tile1.tif tile2.tif
   ```
8. Save to: `data/raw/elevation/dem_aoi.tif`

**Alternative Sources:**
- USGS Earth Explorer: https://earthexplorer.usgs.gov/
- OpenTopography: https://opentopography.org/ (for LiDAR)

---

### 3. Rail Corridor Data ⚠️

**Why manual:** Varies by region and requires local knowledge.

**Option 1: WSDOT GeoData Portal** (Washington State)
1. Visit: https://gisdata-wsdot.opendata.arcgis.com/
2. Search: "rail" or "railroad"
3. Download shapefile
4. Save to: `data/raw/rail/corridor.shp`

**Option 2: Local Transit Agency**
- Sound Transit: https://www.soundtransit.org/
- King County Metro
- Contact GIS/planning department

**Option 3: OpenStreetMap**
1. Visit: https://overpass-turbo.eu/
2. Query:
   ```
   [bbox:47.58,-122.36,47.62,-122.30];
   way[railway=rail];
   out geom;
   ```
3. Export as GeoJSON
4. Convert to shapefile if needed:
   ```bash
   ogr2ogr -f "ESRI Shapefile" data/raw/rail/corridor.shp railway.geojson
   ```

---

### 4. Green Infrastructure / Permeable Pavement Data ⚠️

**Why manual:** Highly specific to location and jurisdiction.

**Option 1: Seattle Open Data**
1. Visit: https://data.seattle.gov/
2. Search: "stormwater", "green infrastructure", "permeable pavement"
3. Potential datasets:
   - GSI Facilities
   - Green Stormwater Infrastructure
   - Right-of-Way Features
4. Download as Shapefile
5. Save to: `data/raw/infrastructure/permeable_pavement.shp`

**Option 2: Local Jurisdiction**
- Contact city/county stormwater department
- Request GI facility inventory
- Public works GIS department

**Option 3: Manual Mapping**
1. Create new shapefile in QGIS
2. Add points/polygons for known facilities
3. Required attributes:
   - `FacilityID` (unique identifier)
   - `AreaSqFt` (facility area in square feet)
   - `InstallYear` (optional, for temporal analysis)
   - `Type` (optional: bioretention, permeable pavement, etc.)
4. Save to: `data/raw/infrastructure/permeable_pavement.shp`

---

### 5. SSURGO Soils Processing (Optional)

If the automated download from `download_data.py` failed:

**Manual Download:**
1. Visit: https://websoilsurvey.nrcs.usda.gov/
2. Click "Start WSS"
3. Define AOI by drawing on map
4. Go to "Soil Data Explorer" → "Download"
5. Download spatial data (shapefile)
6. Extract and save to: `data/raw/soils/`

**Processing:**
```bash
# Reproject to WA State Plane South
ogr2ogr -t_srs EPSG:2927 \
  data/processed/soils/ssurgo_aoi.gpkg \
  data/raw/soils/soilmu_a_*.shp
```

---

### 6. NOAA Atlas 14 Precipitation Data (Optional)

**Manual Entry Required:**

1. Visit: https://hdsc.nws.noaa.gov/pfds/
2. Select state (e.g., Washington)
3. Click map at your site location
4. Note 24-hour precipitation depths for:
   - 2-year storm
   - 10-year storm
   - 25-year storm
5. Update JSON file created by `download_data.py`:
   ```json
   {
     "location": {"lat": 47.6, "lon": -122.33},
     "depths_in": {
       "2yr": 2.2,
       "10yr": 2.9,
       "25yr": 3.4
     },
     "source": "NOAA Atlas 14"
   }
   ```

**Note:** Seattle-area defaults are hardcoded in `scripts/runoff_modeling.py`

---

## Data Directory Structure

After downloading all data, your directory should look like:

```
data/
├── raw/
│   ├── rail/
│   │   └── corridor.shp (+ .dbf, .shx, .prj)
│   ├── infrastructure/
│   │   └── permeable_pavement.shp (+ .dbf, .shx, .prj)
│   ├── landcover/
│   │   └── nlcd_2019_impervious_aoi.tif
│   ├── elevation/
│   │   └── dem_aoi.tif
│   ├── soils/
│   │   └── soilmu_a_*.shp
│   ├── flood/
│   │   └── nfhl_*.geojson (auto-downloaded)
│   └── precip/
│       └── atlas14_*.json (auto-created)
├── processed/
│   ├── flood/
│   │   └── nfhl_aoi.gpkg (auto-created)
│   └── soils/
│       └── ssurgo_aoi.gpkg (if processed)
└── outputs/
    └── (analysis results will be saved here)
```

---

## Verification

Check that all required files exist:

```bash
# Check rail data
ls -lh data/raw/rail/corridor.shp

# Check infrastructure
ls -lh data/raw/infrastructure/permeable_pavement.shp

# Check imperviousness
ls -lh data/raw/landcover/nlcd_2019_impervious_aoi.tif

# Check DEM (optional)
ls -lh data/raw/elevation/dem_aoi.tif

# Check processed flood zones
ls -lh data/processed/flood/nfhl_aoi.gpkg
```

---

## Running the Analysis

### Minimal Run (Required Files Only)

```bash
python scripts/geospatial_analysis.py \
  --rail data/raw/rail/corridor.shp \
  --infrastructure data/raw/infrastructure/permeable_pavement.shp \
  --imperviousness data/raw/landcover/nlcd_2019_impervious_aoi.tif
```

### Full Run (All Optional Data)

```bash
python scripts/geospatial_analysis.py \
  --rail data/raw/rail/corridor.shp \
  --infrastructure data/raw/infrastructure/permeable_pavement.shp \
  --imperviousness data/raw/landcover/nlcd_2019_impervious_aoi.tif \
  --dem data/raw/elevation/dem_aoi.tif \
  --soils data/processed/soils/ssurgo_aoi.gpkg \
  --config config.yaml \
  --output-dir data/outputs \
  --verbose
```

---

## Troubleshooting

### "File not found" errors
- Verify file paths are correct
- Check file extensions (.shp vs .gpkg)
- Ensure files are not in zip archives

### "CRS mismatch" errors
- All data will be reprojected to EPSG:2927 (WA State Plane South)
- Original CRS should be WGS84 (EPSG:4326) for best results

### "No data in raster" errors
- Verify raster covers your AOI
- Check raster CRS matches AOI
- Use `gdalinfo` to inspect raster:
  ```bash
  gdalinfo data/raw/landcover/nlcd_2019_impervious_aoi.tif
  ```

### Large raster files slow
- Clip rasters to AOI before analysis:
  ```bash
  gdalwarp -cutline aoi.shp -crop_to_cutline \
    input.tif output_clipped.tif
  ```

---

## Next Steps

After running the analysis:

1. **Review Outputs:**
   - `data/outputs/analysis_summary.txt` - Text summary
   - `data/outputs/analysis_summary.json` - JSON metrics
   - `data/outputs/analysis_segments.gpkg` - Full spatial results
   - `data/outputs/analysis_segments.csv` - Tabular data

2. **Visualize in QGIS:**
   ```bash
   qgis data/outputs/analysis_segments.gpkg
   ```

3. **Further Analysis:**
   - Import CSV into R/Python for statistical analysis
   - Create maps and visualizations
   - Run sensitivity analyses

---

## Data Update Frequency

- **NLCD Imperviousness:** Every 2-3 years (latest: 2021)
- **FEMA Flood Zones:** Updated as new flood studies complete
- **SSURGO Soils:** Periodic updates, check Web Soil Survey
- **Elevation/DEM:** 3DEP updated periodically with new LiDAR
- **Infrastructure:** Update as facilities are built/decommissioned

---

## Support

For issues with data downloads or analysis:

1. Check [DATA_SOURCES_STATUS.md](DATA_SOURCES_STATUS.md) for known issues
2. Review [FIXES_APPLIED.md](FIXES_APPLIED.md) for recent changes
3. Run `python test_data_sources.py` to verify API connectivity
4. Open an issue on GitHub

---

## References

- MRLC NLCD: https://www.mrlc.gov/
- FEMA NFHL: https://www.fema.gov/flood-maps
- USDA SSURGO: https://www.nrcs.usda.gov/resources/data-and-reports/soil-survey-geographic-database-ssurgo
- USGS 3DEP: https://www.usgs.gov/3d-elevation-program
- NOAA Atlas 14: https://hdsc.nws.noaa.gov/pfds/
