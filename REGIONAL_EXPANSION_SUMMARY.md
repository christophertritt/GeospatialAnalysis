# Regional Expansion & Data Gap Filling Summary

## Overview
This project successfully expanded the geospatial analysis from the Seattle city limits to the full Seattle-Tacoma rail corridor (including Tukwila, Renton, Kent, Auburn, Sumner, Puyallup, Fife, and Tacoma). Critical data gaps in infrastructure and soils were identified and filled using automated acquisition scripts.

## Key Achievements

### 1. Scope Expansion
- **Original Scope**: Seattle only.
- **New Scope**: Full regional corridor (~40 miles).
- **Segments Analyzed**: 1,746 rail corridor segments (250m buffer).

### 2. Data Acquisition & Integration
- **Automated Scripts**: Created `scripts/download_additional_data.py` to fetch data from federal and open APIs.
- **Soils Data**: Downloaded USDA SSURGO soil data for the entire corridor (8,242 map units) via the SDA REST API.
- **Infrastructure Data**:
  - **Problem**: Municipal GSI data was missing for 8 out of 9 cities.
  - **Solution**: Used OpenStreetMap (OSM) as a proxy, querying for `surface=pervious_paving`, `description~"rain garden"`, and `swale`.
  - **Result**: Acquired 1,015 regional infrastructure features and merged them with Seattle's 169 existing features.
- **Rail Data**: Downloaded OSM rail lines to supplement the corridor definition.

### 3. Analysis Execution
- **Vulnerability Assessment**: Calculated for all 1,746 segments using NLCD imperviousness, DEM slope, and SSURGO soils.
- **Infrastructure Density**: Analyzed using the merged regional dataset.
- **Runoff Modeling**: Modeled runoff reduction for 2-year, 10-year, and 25-year storm events.
- **Optimization**: Identified optimal GSI placement strategies.

## Results Summary

### Vulnerability
- **Mean Vulnerability Score**: 7.88 (High).
- **High Vulnerability Segments**: 1,473 (84% of corridor).
- **Drivers**: High imperviousness and poor soil drainage in the industrial rail corridor.

### Infrastructure Gaps
- **Coverage**: Only ~2.5% of segments have documented green stormwater infrastructure.
- **Median Density**: 0.0 sq ft/acre (indicating significant lack of GSI in the corridor).
- **Gap Analysis**: The "High Vulnerability, Low Density" quadrant is effectively the entire corridor due to the sparsity of infrastructure.

### Runoff Reduction Potential
- **Current Reduction**: Existing GSI reduces runoff by ~0.4-0.5% (148-161 ac-ft).
- **Optimization**: Targeted placement could increase efficiency, but the sheer volume of runoff requires significantly more infrastructure investment.

## Files Created
- `scripts/download_additional_data.py`: Tool for fetching SSURGO, OSM, and SVI data.
- `scripts/merge_data.py`: Tool for combining local and regional datasets.
- `data/processed/infrastructure_combined.gpkg`: The master infrastructure dataset.
- `data/outputs/analysis_summary.txt`: Detailed statistical report.
- `data/outputs/analysis_segments.gpkg`: Geospatial results for mapping.

## Next Steps
1. **Visual Validation**: Use QGIS or ArcGIS to inspect `data/outputs/analysis_segments.gpkg`.
2. **SVI Integration**: The CDC SVI download failed (404). Manually downloading the shapefile for Washington State would add social equity context.
3. **Municipal Outreach**: The OSM proxy data is a good start, but contacting the cities of Kent, Auburn, and Tacoma for official stormwater asset data would improve accuracy.
