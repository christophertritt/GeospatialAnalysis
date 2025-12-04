# GeospatialAnalysis

A comprehensive geospatial analysis tool for assessing flood vulnerability and green infrastructure alignment in rail corridors. This tool implements the methodology described in `COMPLETE_METHODOLOGY_GUIDE.txt` for analyzing spatial relationships between permeable pavement infrastructure and flood vulnerability indicators.

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

### Command Line Interface

Run the complete analysis pipeline:

```bash
python scripts/geospatial_analysis.py \
    --rail data/raw/rail/rail_corridor.shp \
    --infrastructure data/raw/infrastructure/permeable_pavement.shp \
    --data-dir data \
    --output-dir data/outputs
```

### Running with Sample Data

The tool can generate sample data for demonstration:

```bash
python scripts/geospatial_analysis.py
```

This will:
1. Create a sample corridor segment
2. Generate synthetic vulnerability scores
3. Place random infrastructure points
4. Perform complete analysis
5. Generate reports and save outputs

### Python API

Use the tool programmatically:

```python
from scripts.geospatial_analysis import GeospatialAnalysisTool

# Initialize
tool = GeospatialAnalysisTool(data_dir='data', output_dir='data/outputs')

# Load data
tool.load_data(
    rail_path='data/raw/rail/corridor.shp',
    infrastructure_path='data/raw/infrastructure/permeable.shp'
)

# Run analyses
tool.calculate_vulnerability()
tool.analyze_infrastructure_density()
tool.assess_alignment()

# Generate outputs
tool.generate_report()
tool.save_results()
```

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