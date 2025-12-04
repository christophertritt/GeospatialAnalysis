# GeospatialAnalysis

A comprehensive geospatial analysis tool for assessing flood vulnerability and green infrastructure alignment in rail corridors. This tool implements the methodology described in `COMPLETE_METHODOLOGY_GUIDE.txt` for analyzing spatial relationships between permeable pavement infrastructure and flood vulnerability indicators.

## Core Research Question

> **To what extent does current permeable pavement distribution align with stormwater flood vulnerability in the urban rail corridors between Seattle and Tacoma?**

All workflows, data requirements, and reporting in this repository are organized to answer that question as directly as possible. See `docs/research_question_alignment.md` for a guided walkthrough of the analysis and interpretation.

## Overview

This tool provides automated geospatial analysis capabilities for:
- **Vulnerability Assessment**: Computing multi-factor flood vulnerability indices based on topography, slope, soil type, imperviousness, and drainage proximity
- **Infrastructure Density Analysis**: Calculating permeable pavement density within corridor buffers
- **Alignment Assessment**: Evaluating spatial correlation between vulnerability and infrastructure placement
- **Gap Analysis**: Identifying priority areas with high vulnerability but low infrastructure coverage
- **Spatial Clustering**: Detecting hot spots and cold spots using Local Moran's I and Getis-Ord Gi* statistics
- **Runoff Modeling**: Estimating stormwater runoff using SCS Curve Number method

## Features

### Core Capabilities
- Multi-buffer analysis (100m, 250m, 500m)
- Coordinate system standardization (WA State Plane South EPSG:2927)
- Spatial data validation and cleaning
- Corridor segmentation at station locations
- Composite vulnerability index calculation
- Infrastructure density metrics
- Correlation and regression analysis
- Quadrant classification for priority setting
- Gap index computation

### Spatial Statistics
- Global Moran's I for spatial autocorrelation
- Local Indicators of Spatial Association (LISA)
- Getis-Ord Gi* hot spot analysis
- Distance decay pattern analysis

### Hydrological Modeling
- SCS Curve Number runoff estimation
- Design storm scenario analysis (2-year, 10-year, 25-year)
- Infrastructure optimization scenarios
- Runoff reduction benefit quantification

## Complete Function Reference

### Core Analysis Module (`scripts/geospatial_analysis.py`)

**Main Class: `GeospatialAnalysisTool`**
- `__init__(data_dir, output_dir, config_path)`: Initialize analysis tool with configuration
- `load_data(rail_path, infrastructure_path)`: Load and validate spatial data, create buffers
- `calculate_vulnerability(imperviousness_raster, dem_path, soils_path)`: Compute multi-factor vulnerability index
- `analyze_infrastructure_density()`: Calculate infrastructure density metrics per segment
- `assess_alignment()`: Evaluate correlation between vulnerability and infrastructure placement
- `perform_spatial_clustering(variable_col)`: Execute spatial autocorrelation analysis
- `perform_runoff_modeling(storm_events, soil_type)`: Model stormwater runoff scenarios
- `generate_report()`: Create comprehensive analysis summary
- `save_results(formats)`: Export results to multiple formats (Shapefile, GeoPackage, CSV, GeoJSON)

### Spatial Clustering (`scripts/spatial_clustering.py`)

- `calculate_morans_i(segments, variable_col)`: Compute Global Moran's I for spatial autocorrelation
- `interpret_morans_i(I, p_value)`: Interpret Moran's I significance and clustering pattern
- `calculate_local_morans(segments, variable_col)`: Perform Local Indicators of Spatial Association (LISA)
- `calculate_hot_spots(segments, variable_col, distance_threshold)`: Getis-Ord Gi* hot spot analysis
- `perform_spatial_clustering_analysis(segments, variable_col)`: Complete spatial clustering workflow

### Runoff Modeling (`scripts/runoff_modeling.py`)

- `prepare_curve_numbers(segments, soil_type)`: Prepare SCS Curve Numbers based on land cover
- `adjust_cn_for_gsi(cn_current, density_sqft_per_acre)`: Adjust CN for green infrastructure impact
- `calculate_runoff_volumes(segments, storm_events)`: Estimate runoff for design storm scenarios
- `optimize_infrastructure_allocation(segments, total_infrastructure_sqft)`: Optimize GSI placement
- `calculate_optimization_benefit(segments, storm_event)`: Quantify runoff reduction benefits
- `perform_runoff_modeling(segments, storm_events, soil_type)`: Complete runoff modeling workflow

### Data Acquisition (`scripts/data_acquisition.py`)

- `fetch_ssurgo_soils_by_bbox(bbox)`: Download SSURGO soils data from USDA NRCS API
- `fetch_nlcd_impervious(year)`: Instructions for NLCD imperviousness raster download
- `fetch_fema_nfhl_by_bbox(bbox)`: Download FEMA flood zones via ArcGIS REST API
- `fetch_noaa_atlas14_depths(lat, lon)`: Retrieve NOAA Atlas 14 precipitation depths
- `clip_file_to_bbox(input_path, bbox, out_subdir, out_name, target_epsg)`: Clip spatial data to study area
- `parse_bbox_arg(s)`: Parse bounding box string to coordinate dictionary

### Data Pipeline & Scheduling (`scripts/data_pipeline_scheduler.py`)

**Main Class: `DataPipelineScheduler`**
- `add_data_source(name, fetch_fn, refresh_days, dependencies)`: Register data source
- `schedule_refresh(source_name)`: Schedule automated data refresh
- `run_pipeline(force_refresh)`: Execute complete data acquisition pipeline
- `generate_status_report()`: Create data freshness and quality report
- `export_metadata()`: Export data provenance and lineage information

### Multi-Jurisdiction Integration (`scripts/integrations/multi_jurisdiction.py`)

**Main Class: `MultiJurisdictionConsolidator`**
- `register_jurisdiction(name, bbox, data_sources)`: Register jurisdiction-specific data sources
- `harmonize_schemas()`: Standardize attribute schemas across jurisdictions
- `consolidate_infrastructure()`: Merge infrastructure data from multiple jurisdictions
- `generate_acquisition_status()`: Track data completeness across jurisdictions

### Seattle Open Data Client (`scripts/integrations/seattle_opendata.py`)

**Main Class: `SeattleOpenDataClient`**
- `fetch_gsi_facilities(bbox, facility_types)`: Download green infrastructure facilities
- `fetch_stormwater_infrastructure(bbox)`: Download storm drains and catch basins
- `fetch_land_use(bbox)`: Download zoning and land use data
- `fetch_boundary(jurisdiction_name)`: Download municipal boundaries
- `cache_and_validate(data, output_path)`: Cache and validate downloaded data

### NOAA Climate Data (`scripts/integrations/noaa_cdo.py`)

**Main Class: `NOAACDOClient`**
- `__init__(api_key)`: Initialize with NOAA CDO API key
- `fetch_precipitation_history(station_id, start_date, end_date)`: Historical precipitation data
- `fetch_wet_season_totals(station_id, years)`: Aggregate October-March precipitation
- `find_stations_near(lat, lon, radius_km)`: Locate nearby weather stations

### NWS Forecast Integration (`scripts/integrations/nws_forecast.py`)

**Main Class: `NWSForecastClient`**
- `get_gridpoint_forecast(lat, lon)`: Retrieve 7-day precipitation forecast
- `get_extended_outlook(lat, lon)`: Retrieve 6-10 day outlook
- `apply_climate_scenario(baseline_precip, scenario)`: Apply RCP climate projections
- `estimate_future_vulnerability(current_vuln, scenario, horizon_year)`: Project future conditions

### USGS Water Services (`scripts/integrations/usgs_water.py`)

**Main Class: `USGSWaterServicesClient`**
- `get_streamflow_current(site_code)`: Real-time streamflow data
- `get_streamflow_history(site_code, start_date, end_date)`: Historical streamflow
- `compare_to_flood_stage(site_code, current_flow)`: Compare to NWS flood stages
- `find_nearby_gages(lat, lon, radius_km)`: Locate nearby stream gages

### Visualization (`scripts/visualize_results.py`)

- `load_results(output_dir)`: Load analysis results from output directory
- `plot_correlation(gdf, output_dir)`: Create vulnerability vs. density scatter plot
- `plot_quadrant_counts(gdf, output_dir)`: Visualize quadrant distribution bar chart
- `plot_map(gdf, column, title, filename, output_dir, cmap)`: Generate thematic map
- `main()`: Generate complete visualization suite

### Dashboard (`scripts/dashboard.py`)

**Streamlit Interactive Dashboard Functions:**
- `load_segment_frame()`: Load analysis segments for interactive exploration
- `load_infrastructure_raw()`: Load raw infrastructure point data
- `apply_weighted_vulnerability(buffer_distance, weight_tuple)`: Recalculate vulnerability with custom weights
- `compute_runoff_scenarios(serialized_segments, events)`: Interactive runoff modeling
- `build_multilayer_map(data)`: Create interactive Folium map
- `build_correlation_scatter(data)`: Create interactive Plotly scatter plot
- `filter_segments(gdf, vuln_range, density_range, jurisdictions, quadrants)`: Dynamic segment filtering

### Dashboard Data Preparation (`scripts/generate_dashboard_data.py`)

- `load_analysis_segments()`: Load segments with all metrics
- `load_infrastructure()`: Load infrastructure facilities
- `compute_summary_statistics(segments, infrastructure)`: Calculate summary metrics
- `create_sample_charts_data(segments)`: Prepare chart-ready datasets
- `export_lightweight_geojson(segments)`: Export simplified geometry for web display
- `generate_data_manifest(stats, charts)`: Create metadata manifest

### Format Conversion (`scripts/convert_formats.py`)

- `convert_gpkg_to_shp(root_dir)`: Batch convert GeoPackage to Shapefile format

### Data Merging (`scripts/merge_data.py`)

- `merge_infrastructure()`: Consolidate infrastructure data from multiple sources

### Additional Data Download (`scripts/download_additional_data.py`)

- `download_svi_2020()`: Download CDC Social Vulnerability Index
- `download_ssurgo_soils()`: Download SSURGO soils via Web Soil Survey
- `download_osm_infrastructure()`: Extract green infrastructure from OpenStreetMap
- `download_osm_rail()`: Extract rail corridors from OpenStreetMap
- `download_sound_transit_boundary()`: Download Sound Transit service area

### GIS Utility Functions (`scripts/utils/gis_functions.py`)

- `validate_spatial_data(gdf, dataset_name)`: Validate geometry and CRS
- `reproject_to_standard(gdf, target_epsg)`: Reproject to standard coordinate system
- `create_buffers(gdf, distances_meters)`: Generate multiple buffer distances
- `split_line_at_points(line, points)`: Segment corridor at station locations
- `calculate_infrastructure_density(segments, infrastructure, buffer_gdf)`: Spatial join and density calculation

### Statistical Functions (`scripts/utils/statistics.py`)

- `calculate_runoff_depth(precip_inches, curve_number)`: SCS Curve Number runoff equation
- `calculate_cn_from_imperviousness(imperv_pct, hsg)`: Derive CN from imperviousness
- `correlation_analysis(x, y, method)`: Pearson and Spearman correlation
- `classify_vulnerability(score, low_threshold, high_threshold)`: Classify vulnerability level
- `assign_quadrant(vuln_score, density, vuln_median, density_median)`: Quadrant classification
- `calculate_gap_index(vuln_score, density, adequacy_threshold)`: Compute protection gap metric

## Installation

### Prerequisites
- Python 3.9 or higher
- pip package manager
- GDAL/OGR (for spatial operations)

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Required Packages
- **Geospatial**: geopandas, rasterio, fiona, shapely, rtree, pyproj
- **Analysis**: numpy, pandas, scipy, scikit-learn, statsmodels
- **Spatial Statistics**: pysal, esda, libpysal, splot
- **Visualization**: matplotlib, seaborn, contextily
- **Utilities**: click, rasterstats

## Usage

### Quick Start: Alignment Assessment

1. Ensure required datasets listed in [docs/research_question_alignment.md](docs/research_question_alignment.md) are present.
2. Run the alignment workflow:

```bash
python scripts/geospatial_analysis.py \
  --rail data/raw/rail/corridor.shp \
  --infrastructure data/raw/infrastructure/permeable_pavement.shp \
  --imperviousness data/raw/landcover/nlcd_2019_impervious_aoi.tif \
  --dem data/raw/elevation/dem_aoi.tif \
  --soils data/processed/soils/ssurgo_aoi.gpkg \
  --config config.yaml \
  --verbose
```

3. Review the synthesized findings in `data/outputs/analysis_summary.txt` (mirrored in `reports/`), which provides the direct answer to the research question along with actionable statistics.

### Available Scripts & Tools

#### 1. **Core Analysis** (`geospatial_analysis.py`)
Complete 6-phase vulnerability and alignment assessment:
```bash
python scripts/geospatial_analysis.py \
    --rail data/raw/rail/corridor.shp \
    --infrastructure data/raw/infrastructure/permeable_pavement.shp \
    --imperviousness data/raw/landcover/nlcd_2019_impervious_aoi.tif \
    --dem data/raw/elevation/dem_aoi.tif \
    --soils data/processed/soils/ssurgo_aoi.gpkg \
    --config config.yaml \
    --verbose
```

#### 2. **Data Acquisition** (`download_data.py`)
Download external datasets for your study area:
```bash
python download_data.py --bbox "-122.36,47.58,-122.30,47.62" --verbose
```

#### 3. **Additional Data Sources** (`download_additional_data.py`)
Download supplementary datasets (CDC SVI, OSM data, etc.):
```bash
python scripts/download_additional_data.py
```

#### 4. **Static Visualization** (`visualize_results.py`)
Generate publication-ready maps and charts:
```bash
python scripts/visualize_results.py --output-dir data/outputs_final
```

#### 5. **Interactive Dashboard** (`dashboard.py`)
Launch web-based Streamlit dashboard for dynamic exploration:
```bash
streamlit run scripts/dashboard.py
```
Features:
- Interactive vulnerability weight adjustment
- Real-time runoff scenario modeling
- Multi-layer mapping with Folium
- Correlation analysis and quadrant filtering
- Data export and download capabilities

#### 6. **Dashboard Data Preparation** (`generate_dashboard_data.py`)
Prepare lightweight datasets for web dashboard:
```bash
python scripts/generate_dashboard_data.py
```

#### 7. **Spatial Clustering Analysis** (`spatial_clustering.py`)
Standalone spatial statistics module:
```python
from scripts.spatial_clustering import perform_spatial_clustering_analysis
results = perform_spatial_clustering_analysis(segments, variable_col='gap_index')
```

#### 8. **Runoff Modeling** (`runoff_modeling.py`)
Standalone hydrological modeling:
```python
from scripts.runoff_modeling import perform_runoff_modeling
results = perform_runoff_modeling(segments, storm_events=['2-year', '10-year', '25-year'])
```

#### 9. **Data Pipeline Scheduler** (`data_pipeline_scheduler.py`)
Automate data refresh and quality monitoring:
```bash
python scripts/data_pipeline_scheduler.py --schedule daily --report
```

#### 10. **Format Conversion** (`convert_formats.py`)
Batch convert GeoPackage to Shapefile:
```bash
python scripts/convert_formats.py
```

#### 11. **Data Merging** (`merge_data.py`)
Consolidate infrastructure data from multiple sources:
```bash
python scripts/merge_data.py
```

#### 12. **Jupyter Notebook**
Interactive step-by-step analysis:
```bash
jupyter notebook notebooks/interactive_exploration.ipynb
```

### Integration Scripts

#### **Seattle Open Data** (`integrations/seattle_opendata.py`)
```python
from scripts.integrations.seattle_opendata import SeattleOpenDataClient
client = SeattleOpenDataClient()
facilities = client.fetch_gsi_facilities(bbox, facility_types=['rain_garden', 'bioswale'])
```

#### **NOAA Climate Data** (`integrations/noaa_cdo.py`)
```python
from scripts.integrations.noaa_cdo import NOAACDOClient
client = NOAACDOClient(api_key='YOUR_KEY')
precip = client.fetch_precipitation_history('GHCND:USW00024233', '2020-01-01', '2024-12-31')
```

#### **NWS Forecast** (`integrations/nws_forecast.py`)
```python
from scripts.integrations.nws_forecast import NWSForecastClient
client = NWSForecastClient()
forecast = client.get_gridpoint_forecast(47.6062, -122.3321)
```

#### **USGS Water Services** (`integrations/usgs_water.py`)
```python
from scripts.integrations.usgs_water import USGSWaterServicesClient
client = USGSWaterServicesClient()
streamflow = client.get_streamflow_current('12113000')  # Duwamish River
```

#### **Multi-Jurisdiction Consolidation** (`integrations/multi_jurisdiction.py`)
```python
from scripts.integrations.multi_jurisdiction import MultiJurisdictionConsolidator
consolidator = MultiJurisdictionConsolidator()
consolidator.register_jurisdiction('Seattle', bbox, data_sources)
consolidator.register_jurisdiction('Tacoma', bbox, data_sources)
consolidated = consolidator.consolidate_infrastructure()
```

### Data Requirements

⚠️ **All analyses now require real data from external sources. No sample/synthetic data is generated.**

Before running analysis, download required datasets:

```bash
# Download external data
python download_data.py --bbox "-122.36,47.58,-122.30,47.62"
```

See [DATA_ACQUISITION_WORKFLOW.md](DATA_ACQUISITION_WORKFLOW.md) for complete instructions.

### Python API

Use the tool programmatically:

```python
from scripts.geospatial_analysis import GeospatialAnalysisTool

# Initialize
tool = GeospatialAnalysisTool(
    data_dir='data',
    output_dir='data/outputs',
    config_path='config.yaml'
)

# Load data (required)
tool.load_data(
    rail_path='data/raw/rail/corridor.shp',
    infrastructure_path='data/raw/infrastructure/permeable_pavement.shp'
)

# Run analyses with real data
tool.calculate_vulnerability(
    imperviousness_raster='data/raw/landcover/nlcd_2019_impervious_aoi.tif',
    dem_path='data/raw/elevation/dem_aoi.tif',
    soils_path='data/processed/soils/ssurgo_aoi.gpkg'
)

tool.analyze_infrastructure_density()
tool.assess_alignment()

# Generate outputs
tool.generate_report()
tool.save_results()
```

## Data Acquisition

### Automated Download Script

Use `download_data.py` to fetch external datasets for your area of interest:

```bash
python download_data.py --bbox "-122.36,47.58,-122.30,47.62" --verbose
```

This script will:
- ✅ **Automatically download:** FEMA flood zones, SSURGO soils metadata
- ⚠️ **Provide instructions for:** NLCD imperviousness, elevation/DEM, rail corridors, infrastructure

### Data Sources

**Automated (via API):**
- `fetch_fema_nfhl_by_bbox(bbox)`: FEMA NFHL flood zones (✅ working)
- `fetch_ssurgo_soils_by_bbox(bbox)`: USDA SSURGO soils (⚠️ may need manual processing)

**Manual Download Required:**
- NLCD imperviousness: https://www.mrlc.gov/viewer/
- Elevation/DEM: https://apps.nationalmap.gov/downloader/
- Rail corridors: WSDOT Portal, OSM, or local agencies
- Infrastructure: Seattle Open Data or local jurisdiction

**See [DATA_ACQUISITION_WORKFLOW.md](DATA_ACQUISITION_WORKFLOW.md) for complete instructions.**

Outputs are cached to `data/raw/` and processed data saved to `data/processed/` as GeoPackages reprojected to Washington State Plane South (EPSG:2927).

## Project Structure

```
GeospatialAnalysis/
│
├── COMPLETE_METHODOLOGY_GUIDE.txt  # Comprehensive methodology documentation
├── README.md                        # This file
├── LICENSE                          # MIT License
├── requirements.txt                 # Python dependencies
│
├── data/                           # Data directory
│   ├── raw/                        # Raw input data
│   │   ├── rail/                   # Rail corridor shapefiles
│   │   ├── infrastructure/         # Permeable pavement data
│   │   ├── elevation/              # DEM/LiDAR data
│   │   ├── soils/                  # SSURGO soil data
│   │   ├── landcover/              # NLCD imperviousness
│   │   └── drainage/               # Storm drain infrastructure
│   ├── processed/                  # Intermediate processing outputs
│   └── outputs/                    # Final analysis results
│
├── scripts/                        # Analysis scripts
│   ├── geospatial_analysis.py     # Main analysis tool
│   └── utils/                      # Utility functions
│       ├── __init__.py
│       ├── gis_functions.py       # GIS operations
│       └── statistics.py          # Statistical functions
│
├── analysis/                       # Advanced analysis scripts
│   └── (R scripts for spatial regression)
│
└── figures/                        # Output visualizations
    ├── maps/                       # Map outputs
    └── charts/                     # Chart outputs
```

## Data Requirements

### Minimum Required Data
1. **Rail Corridor**: Line or polygon shapefile of rail corridor
2. **Infrastructure**: Point or polygon shapefile of permeable pavement facilities

### Recommended Additional Data
- **Elevation**: LiDAR-derived DEM (3-6 foot resolution)
- **Soils**: SSURGO hydrologic soil groups
- **Land Cover**: NLCD imperviousness raster
- **Drainage**: Storm drain lines and catch basins
- **Precipitation**: NOAA Atlas 14 design storm depths
- **Jurisdictions**: Municipal boundaries for jurisdictional analysis

### Data Sources
See `COMPLETE_METHODOLOGY_GUIDE.txt` Section 1 for detailed data acquisition instructions:
- WSDOT GeoData Portal (rail infrastructure)
- Seattle Open Data (permeable pavement, drainage)
- USDA Web Soil Survey (soils)
- USGS National Map (elevation, land cover)
- NOAA Climate Data (precipitation)

## Output Files

### Spatial Data
- `analysis_segments.shp`: Segment-level analysis results with all metrics
- `infrastructure_processed.shp`: Processed infrastructure data

### Reports
- `analysis_summary.txt`: Text summary of key findings
- `analysis_segments.csv`: Tabular data for further analysis

### Metrics Included
- `vuln_mean`: Composite vulnerability index (0-10 scale)
- `vuln_class`: Vulnerability classification (Low/Moderate/High)
- `density_sqft_per_acre`: Infrastructure density
- `facility_count`: Number of facilities per segment
- `quadrant`: Alignment quadrant classification
- `gap_index`: Protection gap metric
- `imperv_mean`: Mean imperviousness percentage
- `buffer_area_acres`: Analysis area in acres

## Methodology

This tool implements a six-phase methodology:

### Phase 1: Data Preparation
- Coordinate system standardization
- Buffer generation (100m, 250m, 500m)
- Corridor segmentation
- Data validation

### Phase 2: Vulnerability Index
- Topographic position analysis
- Slope calculation
- Soil drainage classification
- Imperviousness assessment
- Drainage proximity
- Weighted composite index

### Phase 3: Infrastructure Density
- Spatial join with buffers
- Density calculation (sq ft/acre)
- Temporal cohort analysis
- Jurisdictional comparison

### Phase 4: Alignment Assessment
- Pearson and Spearman correlation
- Quadrant classification
- Gap index calculation
- Multiple regression modeling

### Phase 5: Spatial Clustering
- Global Moran's I
- Local Moran's I (LISA)
- Getis-Ord Gi* hot spots

### Phase 6: Runoff Modeling
- SCS Curve Number preparation
- Runoff volume calculation
- Optimization scenarios

## Example Analysis Results

### Typical Outputs
```
VULNERABILITY ASSESSMENT
  Mean vulnerability: 5.23
  High vulnerability segments: 8
  Moderate vulnerability segments: 12
  Low vulnerability segments: 5

INFRASTRUCTURE DENSITY
  Mean density: 847.3 sq ft/acre
  Median density: 592.1 sq ft/acre
  Segments with zero infrastructure: 3

ALIGNMENT ANALYSIS
  Correlation (r): -0.342
  P-value: 0.0156
  ⚠ Significant INVERSE correlation detected
  
  Priority gap segments (Q3): 7 segments
  Mean gap index: 3.45
```

## License

MIT License - see LICENSE file for details

Copyright (c) 2025 Christopher Tritt

## Acknowledgments

This tool implements methodologies developed for rail corridor flood resilience analysis in the Seattle-Tacoma region. The comprehensive methodology guide provides detailed step-by-step instructions for conducting spatial analysis of green infrastructure and vulnerability indicators.