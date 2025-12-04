# Verification Checklist

Use this checklist to verify your GeospatialAnalysis setup is complete and ready to run.

---

## ✅ Pre-Analysis Checklist

### 1. External Data Source Connectivity

```bash
python test_data_sources.py
```

**Expected Result:**
- ✅ FEMA NFHL: Accessible
- ✅ MRLC NLCD Portal: Accessible
- ✅ NOAA Atlas 14: Accessible
- ✅ USGS National Map: Accessible
- ⚠️ USDA SSURGO: May vary (acceptable)

**Status:** 4-5/5 services accessible

---

### 2. Required Data Files

Check that all required data files are in place:

```bash
#!/bin/bash

echo "Checking required data files..."

# Required files
FILES=(
  "data/raw/rail/corridor.shp"
  "data/raw/infrastructure/permeable_pavement.shp"
  "data/raw/landcover/nlcd_2019_impervious_aoi.tif"
)

for file in "${FILES[@]}"; do
  if [ -f "$file" ]; then
    echo "✅ $file"
  else
    echo "❌ $file (MISSING)"
  fi
done
```

**All three files must exist to run analysis.**

---

### 3. Optional Data Files

Check optional but recommended files:

```bash
# Optional files
OPTIONAL_FILES=(
  "data/raw/elevation/dem_aoi.tif"
  "data/processed/soils/ssurgo_aoi.gpkg"
  "data/processed/flood/nfhl_aoi.gpkg"
)

for file in "${OPTIONAL_FILES[@]}"; do
  if [ -f "$file" ]; then
    echo "✅ $file"
  else
    echo "⚠️  $file (optional, but recommended)"
  fi
done
```

---

### 4. Python Dependencies

Verify all required packages are installed:

```bash
pip install -r requirements.txt --dry-run 2>&1 | grep -i "already\|installed" && echo "✅ All packages installed" || echo "❌ Some packages missing"
```

**Key packages:**
- geopandas >= 0.14.0
- rasterio >= 1.3.0
- rasterstats >= 0.19.0
- pysal >= 2.7.0
- esda >= 2.5.0

---

### 5. Configuration File

Check config file exists:

```bash
if [ -f "config.yaml" ]; then
  echo "✅ config.yaml exists"
  cat config.yaml
else
  echo "⚠️  config.yaml not found (will use defaults)"
fi
```

---

## ✅ Data Validation Checklist

### Rail Corridor Data

```python
import geopandas as gpd

# Load rail data
rail = gpd.read_file('data/raw/rail/corridor.shp')

print(f"✅ Rail corridors loaded: {len(rail)} features")
print(f"✅ CRS: {rail.crs}")
print(f"✅ Geometry type: {rail.geometry.type.unique()}")
print(f"✅ Bounds: {rail.total_bounds}")
```

**Expected:**
- Features: > 0
- Geometry type: LineString or MultiLineString
- Valid CRS (preferably EPSG:4326 or EPSG:2927)

---

### Infrastructure Data

```python
# Load infrastructure
infra = gpd.read_file('data/raw/infrastructure/permeable_pavement.shp')

print(f"✅ Infrastructure features: {len(infra)}")
print(f"✅ Columns: {infra.columns.tolist()}")
print(f"✅ Has AreaSqFt: {'AreaSqFt' in infra.columns}")
```

**Required Columns:**
- ✅ `geometry` (Point or Polygon)
- ✅ `AreaSqFt` (facility area in square feet)
- ✅ `FacilityID` (unique identifier, optional but recommended)

---

### NLCD Imperviousness Raster

```bash
gdalinfo data/raw/landcover/nlcd_2019_impervious_aoi.tif
```

**Expected:**
- Driver: GTiff/GeoTIFF
- Size: > 0 x 0
- Pixel values: 0-100 (percent impervious)
- Coordinate System: Defined
- NoData Value: Defined

---

### DEM/Elevation Raster (Optional)

```bash
gdalinfo data/raw/elevation/dem_aoi.tif
```

**Expected:**
- Driver: GTiff/GeoTIFF
- Pixel values: Elevation in meters or feet
- Covers same area as AOI

---

## ✅ Analysis Test Run

### Minimal Test (Required Files Only)

```bash
python scripts/geospatial_analysis.py \
  --rail data/raw/rail/corridor.shp \
  --infrastructure data/raw/infrastructure/permeable_pavement.shp \
  --imperviousness data/raw/landcover/nlcd_2019_impervious_aoi.tif \
  --output-dir data/outputs_test \
  --verbose
```

**Expected Output:**
```
======================================================================
GEOSPATIAL ANALYSIS TOOL
======================================================================

Validating required data files...
  ✅ Rail corridor: data/raw/rail/corridor.shp
  ✅ Infrastructure: data/raw/infrastructure/permeable_pavement.shp
  ✅ Imperviousness: data/raw/landcover/nlcd_2019_impervious_aoi.tif

PHASE 1: DATA LOADING AND VALIDATION
...

PHASE 2: VULNERABILITY INDEX CALCULATION
...

PHASE 3: INFRASTRUCTURE DENSITY ANALYSIS
...

PHASE 4: ALIGNMENT ASSESSMENT
...

PHASE 5: SPATIAL CLUSTERING ANALYSIS
...

PHASE 6: RUNOFF REDUCTION MODELING
...

✅ ANALYSIS COMPLETE
```

---

### Full Test (With Optional Files)

```bash
python scripts/geospatial_analysis.py \
  --rail data/raw/rail/corridor.shp \
  --infrastructure data/raw/infrastructure/permeable_pavement.shp \
  --imperviousness data/raw/landcover/nlcd_2019_impervious_aoi.tif \
  --dem data/raw/elevation/dem_aoi.tif \
  --soils data/processed/soils/ssurgo_aoi.gpkg \
  --config config.yaml \
  --output-dir data/outputs_test \
  --verbose
```

---

## ✅ Output Validation

After running analysis, check outputs:

```bash
ls -lh data/outputs_test/

# Expected files:
# - analysis_segments.gpkg (or .shp + supporting files)
# - analysis_segments.csv
# - analysis_summary.txt
# - analysis_summary.json
# - infrastructure_processed.gpkg (or .shp)
```

### Validate GeoPackage Output

```python
import geopandas as gpd

segments = gpd.read_file('data/outputs_test/analysis_segments.gpkg')

print(f"✅ Segments: {len(segments)}")
print(f"✅ Columns: {len(segments.columns)}")

# Check for key columns
required_cols = [
    'segment_id',
    'vuln_mean',
    'vuln_class',
    'imperv_mean',
    'density_sqft_per_acre',
    'facility_count',
    'quadrant',
    'gap_index'
]

for col in required_cols:
    if col in segments.columns:
        print(f"  ✅ {col}")
    else:
        print(f"  ❌ {col} (MISSING)")
```

---

### Validate Summary Report

```bash
cat data/outputs_test/analysis_summary.txt

# Expected sections:
# - STUDY AREA
# - VULNERABILITY ASSESSMENT
# - INFRASTRUCTURE DENSITY
# - ALIGNMENT ANALYSIS
```

---

### Validate JSON Output

```bash
python -m json.tool data/outputs_test/analysis_summary.json

# Should be valid JSON with:
# - n_segments
# - crs
# - results (with alignment metrics)
```

---

## ✅ Quality Checks

### 1. No NaN/Null Values in Critical Fields

```python
import pandas as pd

segments = gpd.read_file('data/outputs_test/analysis_segments.gpkg')

critical_fields = ['vuln_mean', 'imperv_mean', 'density_sqft_per_acre']

for field in critical_fields:
    null_count = segments[field].isna().sum()
    if null_count == 0:
        print(f"✅ {field}: No null values")
    else:
        print(f"⚠️  {field}: {null_count} null values")
```

---

### 2. Reasonable Value Ranges

```python
# Check vulnerability scores (should be 0-10)
vuln_range = (segments['vuln_mean'].min(), segments['vuln_mean'].max())
if 0 <= vuln_range[0] and vuln_range[1] <= 10:
    print(f"✅ Vulnerability range: {vuln_range} (valid)")
else:
    print(f"⚠️  Vulnerability range: {vuln_range} (outside 0-10)")

# Check imperviousness (should be 0-100)
imperv_range = (segments['imperv_mean'].min(), segments['imperv_mean'].max())
if 0 <= imperv_range[0] and imperv_range[1] <= 100:
    print(f"✅ Imperviousness range: {imperv_range} (valid)")
else:
    print(f"⚠️  Imperviousness range: {imperv_range} (outside 0-100)")

# Check density (should be non-negative)
if segments['density_sqft_per_acre'].min() >= 0:
    print(f"✅ Infrastructure density: All non-negative")
else:
    print(f"⚠️  Infrastructure density: Has negative values")
```

---

### 3. Spatial Clustering Results

```python
# Check for LISA/Gi* columns (if spatial clustering ran)
spatial_cols = ['lisa_I', 'lisa_cluster', 'gi_star', 'hotspot_class']

for col in spatial_cols:
    if col in segments.columns:
        print(f"✅ {col} present")
        print(f"   Unique values: {segments[col].nunique()}")
    else:
        print(f"⚠️  {col} not found (spatial clustering may not have run)")
```

---

### 4. Runoff Modeling Results

```python
# Check for runoff columns (if runoff modeling ran)
runoff_cols = ['cn_current', 'cn_with_gsi', 'volume_current_10-year_acft']

for col in runoff_cols:
    if col in segments.columns:
        print(f"✅ {col} present")
    else:
        print(f"⚠️  {col} not found (runoff modeling may not have run)")
```

---

## ✅ Visualization Test

### Load in QGIS

```bash
qgis data/outputs_test/analysis_segments.gpkg
```

**Verify:**
- ✅ Segments display correctly
- ✅ Attribute table has all columns
- ✅ Symbology can be applied (e.g., color by vulnerability)

---

### Quick Plot in Python

```python
import matplotlib.pyplot as plt

segments = gpd.read_file('data/outputs_test/analysis_segments.gpkg')

fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Plot vulnerability
segments.plot(column='vuln_mean', cmap='YlOrRd', legend=True, ax=axes[0])
axes[0].set_title('Vulnerability Index')

# Plot infrastructure density
segments.plot(column='density_sqft_per_acre', cmap='Greens', legend=True, ax=axes[1])
axes[1].set_title('Infrastructure Density')

plt.tight_layout()
plt.savefig('test_visualization.png', dpi=150)
print("✅ Visualization saved to test_visualization.png")
```

---

## Troubleshooting

### Issue: "File not found" errors

**Solution:**
```bash
# Verify file paths
ls -lh data/raw/rail/
ls -lh data/raw/infrastructure/
ls -lh data/raw/landcover/
```

---

### Issue: "CRS mismatch" warnings

**Solution:**
- Tool automatically reprojects to EPSG:2927
- Warnings are informational, not errors
- Verify final output CRS: `gdalinfo data/outputs_test/analysis_segments.gpkg`

---

### Issue: "No data in raster" errors

**Solution:**
```bash
# Check raster covers AOI
gdalinfo data/raw/landcover/nlcd_2019_impervious_aoi.tif

# Check for overlap
python -c "
import geopandas as gpd
import rasterio
rail = gpd.read_file('data/raw/rail/corridor.shp')
with rasterio.open('data/raw/landcover/nlcd_2019_impervious_aoi.tif') as src:
    print('Rail bounds:', rail.total_bounds)
    print('Raster bounds:', src.bounds)
"
```

---

### Issue: Analysis runs but produces zeros

**Possible causes:**
1. Raster nodata not set correctly
2. CRS mismatch between vector and raster
3. Raster units misunderstood (0-1 vs 0-100 for imperviousness)

**Solution:**
```bash
# Check raster metadata
gdalinfo data/raw/landcover/nlcd_2019_impervious_aoi.tif | grep -E "NoData|Pixel"

# Verify data range
gdalinfo -stats data/raw/landcover/nlcd_2019_impervious_aoi.tif | grep -E "MINIMUM\|MAXIMUM"
```

---

## ✅ Final Checklist

Before considering setup complete:

- [ ] External data sources tested (4-5/5 accessible)
- [ ] All required files downloaded and in place
- [ ] Python dependencies installed
- [ ] Rail corridor data validated
- [ ] Infrastructure data validated (has AreaSqFt column)
- [ ] NLCD raster validated (0-100 range, correct CRS)
- [ ] Test run completed successfully
- [ ] Output files generated
- [ ] Output data quality checked (no NaNs, reasonable ranges)
- [ ] Visualizations can be created
- [ ] Documentation reviewed

---

## Success!

If all checks pass:

✅ **Your GeospatialAnalysis setup is complete and ready for production use!**

You can now run full analyses with confidence that results are based on real, validated external data sources.
