# Dashboard User Guide

## Quick Start

The Seattle-Tacoma Rail Resilience Dashboard is now easier to use with automatic data loading and helpful visualizations displayed by default.

### Launch Dashboard

```bash
streamlit run scripts/dashboard.py
```

The dashboard will open at `http://localhost:8501`

## What's New

### ✨ Welcome Screen with Key Metrics

When you open the dashboard, you'll immediately see:

- **Analysis Segments**: Total number of corridor segments analyzed
- **Corridor Length**: Total miles of rail corridor covered
- **Mean Vulnerability**: Average flood vulnerability score (0-10 scale)
- **GSI Facilities**: Number of green stormwater infrastructure facilities

### 📊 Quick Insights Panel

Click the "📊 Quick Insights" expander to see:

- **Flood Vulnerability Summary**
  - Percentage of high-vulnerability segments
  - Maximum vulnerability score

- **Green Infrastructure Coverage**
  - Percentage of segments with GSI
  - Total GSI area in acres

- **Spatial Analysis** (if available)
  - Hot spot identification (99% and 95% confidence levels)
  - Clusters requiring priority attention

- **Priority Gaps**
  - Percentage of segments with high vulnerability but low infrastructure
  - Areas for targeted investment

### 🔧 Better Error Messages

If data is missing, the dashboard now provides:

- Clear explanation of what's needed
- Step-by-step instructions to generate data
- Links to documentation
- Status of each data file (✓ found or ✗ missing)

## Data Preparation

### Option 1: Generate Dashboard Data (Recommended)

This prepares optimized data for visualization:

```bash
python scripts/generate_dashboard_data.py
```

**What it does:**
- Loads analysis segments and infrastructure data
- Computes comprehensive summary statistics
- Creates pre-computed chart data
- Exports simplified GeoJSON for fast web mapping
- Generates data manifest and statistics files

**Output location:** `data/dashboard_ready/`

**Time required:** ~30 seconds

### Option 2: Verify Existing Data

Check if your data is ready for the dashboard:

```bash
python scripts/load_demo_data.py
```

**What it shows:**
- Feature availability (basic analysis, infrastructure, spatial stats, etc.)
- Data columns present
- Summary statistics
- Whether data needs preparation

### Option 3: Full Analysis Pipeline

If you need to process raw data:

```bash
python scripts/geospatial_analysis.py
```

**Time required:** Several minutes depending on data size

## Dashboard Features

### Tab 1: Infrastructure Distribution

**Purpose**: Visualize where GSI is located along the corridor

**Features:**
- Multi-layer interactive map
- Installation timeline (1995-2024)
- Coverage statistics by jurisdiction
- Density calculations

**Key Metrics:**
- Total infrastructure count
- Coverage area (sq ft and acres)
- Density per buffer segment

### Tab 2: Flood Vulnerability

**Purpose**: Identify areas with highest flood risk

**Features:**
- Vulnerability component analysis (5 factors)
- Summary tables by jurisdiction
- Vulnerability classification (Low/Moderate/High)

**Analysis Components:**
1. Elevation (proximity to water bodies)
2. Slope (drainage capacity)
3. Soil drainage (infiltration)
4. Impervious surface (runoff generation)
5. Flood zone classification

### Tab 3: Correlation & Jurisdictions

**Purpose**: Analyze spatial patterns and cross-jurisdiction comparisons

**Features:**
- Scatter plots (vulnerability vs. infrastructure)
- Jurisdiction comparison tables
- **NEW: Spatial autocorrelation analysis**
  - Moran's I statistic
  - Hot spot analysis (Getis-Ord Gi*)
  - Interpretation guidance

**Key Insights:**
- Where infrastructure aligns with vulnerability
- Jurisdictions with highest need
- Clustered areas of concern

### Tab 4: Priority Gap Targeting

**Purpose**: Identify high-need, low-infrastructure areas

**Features:**
- Priority gap map highlighting critical areas
- Gap index calculations
- Downloadable segment lists

**Criteria for Priority Gaps:**
- Vulnerability score > 7.0
- Infrastructure density < 100 sq ft/acre

### Tab 5: Runoff & Temporal Dynamics

**Purpose**: Model runoff scenarios and temporal trends

**Features:**
- **SCS Curve Number runoff modeling**
  - 4 scenarios (Baseline, Redistribute, Gap Investments, Combined)
  - 3 design storms (25-year, 50-year, 100-year)
  - Volume comparisons (acre-feet)
- **Temporal analysis**
  - Installation cohorts (1995-2010, 2011-2014, 2015-2024)
  - Vulnerability trends over time

## Sidebar Controls

### Buffer Distance

Choose analysis scale:
- **Station influence (100 m)**: Immediate station area
- **Core corridor (250 m)**: Default analysis buffer
- **Watershed context (500 m)**: Broader hydrologic context

### Vulnerability Weight Overrides

Customize the 5-component vulnerability index:
- Elevation weight (default: 0.25)
- Slope weight (default: 0.15)
- Soil weight (default: 0.20)
- Impervious surface weight (default: 0.25)
- Drainage/flood zone weight (default: 0.15)

**Note:** Weights must sum to 1.0

### Jurisdictions Filter

Select which cities to include:
- Seattle
- Tukwila
- Kent
- Auburn
- Sumner
- Puyallup
- Fife
- Tacoma
- King County (Unincorporated)

### Installation Date Range

Filter infrastructure by installation period (1995-2024)

## Data Export

Each tab includes CSV download buttons:
- Infrastructure metrics
- Vulnerability scores
- Runoff scenario results
- Priority gap segments

## Troubleshooting

### Dashboard shows "No analysis segments available"

**Solution:**
1. Run `python scripts/generate_dashboard_data.py`
2. Refresh the dashboard
3. Check the status indicators showing which files exist

### Spatial statistics not displaying

**Cause:** Missing spatial analysis columns in data

**Solution:**
Run full analysis pipeline:
```bash
python scripts/geospatial_analysis.py
```

This will compute:
- Moran's I (global autocorrelation)
- Local Moran's I (LISA)
- Getis-Ord Gi* (hot spots)

### Map is slow or unresponsive

**Cause:** Too many segments or complex geometry

**Solutions:**
1. Use simplified data: `python scripts/generate_dashboard_data.py`
   (creates `segments_simplified.geojson`)
2. Filter to fewer jurisdictions in sidebar
3. Use smaller buffer distance

### Installation date filter has no effect

**Cause:** Installation dates not in the infrastructure data

**Current Status:** Seattle data lacks temporal information. This feature will be available when additional jurisdiction data is acquired.

## Data Sources

### Current Coverage (as of December 2024)

- **Seattle**: 169 GSI facilities (11% of corridor by population)
- **Other 8 cities**: Data requests pending (4-6 week timeline)

See [DATA_GAP_ANALYSIS.md](DATA_GAP_ANALYSIS.md) for details.

### Required Files

| File | Purpose | Status |
|------|---------|--------|
| `data/outputs_final/analysis_segments.gpkg` | Main analysis data | ✓ Available |
| `data/outputs_final/infrastructure_processed.gpkg` | GSI facilities | ✓ Available |
| `data/dashboard_ready/summary_statistics.json` | Pre-computed stats | ✓ Generated |
| `data/dashboard_ready/segments_simplified.geojson` | Web-optimized map data | ✓ Generated |

## Performance Tips

1. **First load is slower**: Streamlit caches data after initial load
2. **Use simplified data**: Run `generate_dashboard_data.py` for faster maps
3. **Filter early**: Use sidebar controls to reduce data before analysis
4. **Close unused tabs**: Only load data for tabs you're actively viewing

## Advanced Usage

### Custom Analysis

The dashboard loads data from multiple locations (checked in order):

1. `data/outputs/analysis_segments.gpkg`
2. `data/outputs_final/analysis_segments.gpkg`
3. `data/outputs/analysis_segments.shp`

Add your custom analysis to any of these locations.

### Integration with API Data

To enable real-time data updates:

1. Configure API tokens (see [docs/API_SETUP_GUIDE.md](docs/API_SETUP_GUIDE.md))
2. Run data pipeline: `python scripts/data_pipeline_scheduler.py --run-now weekly_usgs`
3. Dashboard automatically detects updated data

### Automated Updates

Schedule automatic data refreshes:

```bash
python scripts/data_pipeline_scheduler.py --daemon
```

**Update frequency:**
- Monthly: NOAA precipitation, NWS climate scenarios
- Weekly: USGS streamgage, Seattle open data
- Quarterly: Full multi-jurisdiction refresh

## Support

### Documentation

- **Quick Start**: [QUICKSTART.md](QUICKSTART.md)
- **Complete Status**: [STATUS_COMPLETE.md](STATUS_COMPLETE.md)
- **API Setup**: [docs/API_SETUP_GUIDE.md](docs/API_SETUP_GUIDE.md)
- **Methodology**: [COMPLETE_METHODOLOGY_GUIDE.txt](COMPLETE_METHODOLOGY_GUIDE.txt)

### Testing

Verify all components:
```bash
python test_integrations.py
```

Expected: `✓✓✓ ALL TESTS PASSED!`

## Technical Details

### Stack

- **Frontend**: Streamlit 1.24+
- **Geospatial**: GeoPandas, Rasterio, Folium
- **Analysis**: NumPy, Pandas, SciPy
- **Spatial Statistics**: PySAL (libpysal, esda)
- **Visualization**: Plotly, Matplotlib

### Caching

The dashboard uses Streamlit's `@st.cache_data` decorator to cache:
- Raw data loads (TTL: 1 hour)
- Filtered segments (recomputes on filter change)
- Vulnerability calculations (recomputes on weight change)
- Map rendering (recomputes on data change)

### Memory Usage

- **Base**: ~200 MB
- **With full data**: ~400-500 MB
- **Recommended**: 4GB RAM minimum, 8GB for optimal performance

## Citation

If using this dashboard for research or publication:

```
Seattle-Tacoma Rail Resilience Dashboard (2024)
Geospatial analysis of permeable pavement alignment with flood vulnerability
along the Seattle-Tacoma rail corridor.
```

See [IMPLEMENTATION_SUMMARY_2024.md](IMPLEMENTATION_SUMMARY_2024.md) for complete citations.

---

**Last Updated**: December 3, 2024
**Version**: 2.0 (Enhanced with welcome screen and automatic data detection)
**Status**: Production ready ✅

