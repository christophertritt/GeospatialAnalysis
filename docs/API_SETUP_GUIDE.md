# API Setup Guide

Complete guide for configuring all API integrations in the GeospatialAnalysis repository.

## Overview

The SeattleTacoma corridor analysis integrates data from **5 external sources**:

| Source | Authentication | Update Frequency | Status |
|--------|---------------|------------------|---------|
| NOAA Climate Data Online | **Token Required** | Monthly | ✅ Active |
| USGS Water Services | None | Weekly | ✅ Active |
| Seattle Open Data Portal | None | Weekly | ✅ Active |
| National Weather Service | None | Monthly | ✅ Active |
| Multi-Jurisdiction Data | Varies | Quarterly | ⚠️ Requires Setup |

---

## 1. NOAA Climate Data Online (CDO) API

### Purpose
Historical precipitation data for Sea-Tac Airport, extreme event identification, Pacific Northwest wet season analysis.

### Authentication Required: ✅ YES

### How to Obtain Token

1. Visit: https://www.ncdc.noaa.gov/cdo-web/token
2. Enter your email address
3. Check email for token (arrives within minutes)
4. Token format: 32-character alphanumeric string

### Configuration

Add token to `config.yaml`:

```yaml
noaa_cdo_token: "your_32_character_token_here"
```

Or set environment variable:

```bash
export NOAA_CDO_TOKEN="your_token_here"
```

### Testing

```python
from scripts.integrations.noaa_cdo import NOAACDOClient
from datetime import date

client = NOAACDOClient(token="YOUR_TOKEN")

# Test: Fetch last 30 days of precipitation
precip = client.get_daily_precip(
    start_date=date(2024, 11, 1),
    end_date=date(2024, 11, 30)
)

print(f"Retrieved {len(precip)} days of precipitation data")
```

### API Limits
- 5 requests per second
- 10,000 requests per day
- Citation: Menne et al. (2012) "An Overview of the Global Historical Climatology Network-Daily Database"

### Common Issues

**Issue**: `HTTP 400 - Invalid token`
**Solution**: Check token is correctly copied (no spaces), verify not expired

**Issue**: `HTTP 429 - Rate limit exceeded`
**Solution**: Add delays between requests, use caching

---

## 2. USGS Water Services API

### Purpose
Real-time streamgage data for Duwamish, Green, and Puyallup Rivers; flood stage validation.

### Authentication Required: ❌ NO

No registration or API key needed. Public data access.

### Configuration

No configuration needed. API endpoints are hardcoded:
- Instantaneous values: `https://waterservices.usgs.gov/nwis/iv/`
- Site information: `https://waterservices.usgs.gov/nwis/site/`

### Testing

```python
from scripts.integrations.usgs_water import USGSWaterServicesClient

client = USGSWaterServicesClient()

# Test: Get current conditions for Green River
readings = client.get_current_conditions(["12113000"])  # Green River near Auburn

for reading in readings:
    print(f"Gage height: {reading.gage_height_ft:.2f} ft")
    print(f"Flood status: {reading.flood_status}")
```

### Key Streamgages

| Site Number | River | Location | Flood Stage |
|-------------|-------|----------|-------------|
| 12113000 | Green River | Auburn, WA | 24.0 ft |
| 12108500 | Duwamish River | Tukwila, WA | 18.0 ft |
| 12101500 | Puyallup River | Puyallup, WA | 31.0 ft |
| 12095000 | Carbon River | Near Sumner | 10.0 ft |

### API Limits
- No official rate limits
- Recommend <50 requests/minute to avoid throttling
- Citation: De Cicco et al. (2018) "dataRetrieval: R packages for discovering and retrieving water data"

---

## 3. Seattle Open Data Portal

### Purpose
Seattle Public Utilities green stormwater infrastructure installations (permeable pavement, rain gardens, bioswales).

### Authentication Required: ❌ NO

Public ArcGIS REST services, no authentication needed.

### Configuration

No configuration needed. Services accessed via:
- Base URL: `https://data-seattlecitygis.opendata.arcgis.com/`
- SPU DWW services: Auto-discovered

### Testing

```python
from scripts.integrations.seattle_opendata import SeattleOpenDataClient

client = SeattleOpenDataClient()

# Test: Fetch all Seattle GSI installations
gsi = client.fetch_all_seattle_gsi(include_proposed=False)

print(f"Retrieved {len(gsi)} Seattle GSI facilities")
print(gsi["facility_type"].value_counts())
```

### Available Datasets
1. **Permeable Pavement**: Active installations with area and installation dates
2. **Rain Gardens**: Point locations with design specifications
3. **Proposed Projects**: Planned future installations

### Data Update Frequency
Seattle updates their open data portal irregularly. Weekly automated checks recommended.

### Citation
Janssen et al. (2012) "Benefits, Adoption Barriers and Myths of Open Data and Open Government"

---

## 4. National Weather Service API

### Purpose
Gridded weather forecasts for climate change scenario modeling, future precipitation projections.

### Authentication Required: ❌ NO

Public API, no authentication needed.

### Configuration

Recommended: Set User-Agent header (already configured in code):

```python
headers = {
    "User-Agent": "(Your App Name, contact@example.com)"
}
```

### Testing

```python
from scripts.integrations.nws_forecast import NWSForecastClient

client = NWSForecastClient()

# Test: Get 7-day precipitation outlook for Sea-Tac
outlook = client.get_precipitation_outlook(
    latitude=47.4502,
    longitude=-122.3088,
    days_ahead=7
)

print(outlook)
```

### Climate Scenarios

Built-in climate change scenarios per Mote et al. (2019):

| Scenario | Time Period | Precip Increase | Extreme Event Increase |
|----------|-------------|-----------------|------------------------|
| Current | 2020s | 0% | 0% |
| Mid-Century RCP4.5 | 2050s | +8% | +15% |
| End-Century RCP4.5 | 2080s | +12% | +25% |
| End-Century RCP8.5 | 2080s | +20% | +40% |

### API Limits
- No official rate limits
- Recommend <10 requests/minute
- Forecasts update every 1-6 hours

### Citation
Vose et al. (2017) "Fourth National Climate Assessment"

---

## 5. Multi-Jurisdiction Data Consolidation

### Purpose
Consolidate GSI data from all 9 corridor jurisdictions (Seattle, Tukwila, Kent, Auburn, Sumner, Puyallup, Fife, Tacoma, King County).

### Authentication Required: ⚠️ VARIES BY JURISDICTION

### Current Status (per DATA_GAP_ANALYSIS.md)

| Jurisdiction | Status | Data Source | Action Required |
|-------------|--------|-------------|-----------------|
| **Seattle** | ✅ Complete | Seattle Open Data | None |
| **Tukwila** | ❌ Missing | Direct Request | Contact Public Works |
| **Renton** | ❌ Missing | King County/City | Data request needed |
| **Kent** | ❌ Missing | Direct Request | Contact Public Works |
| **Auburn** | ❌ Missing | Direct Request | Contact Environmental Services |
| **Sumner** | ❌ Missing | Pierce County | Data request needed |
| **Puyallup** | ❌ Missing | Pierce County | Data request needed |
| **Fife** | ❌ Missing | Pierce County | Data request needed |
| **Tacoma** | ❌ Missing | Tacoma Open Data | Check data portal |
| **King County** | ❌ Missing | County GIS | Email WLRD-GIS |

### Required Actions

#### King County Data Request

**Contact**: WLRD-GIS@kingcounty.gov
**URL**: https://gis-kingcounty.opendata.arcgis.com/
**Search Terms**: "green stormwater infrastructure", "permeable pavement", "low impact development"

**Email Template**:

```
Subject: Data Request - Green Stormwater Infrastructure for Research

Dear King County WLRD GIS Team,

I am conducting academic research on flood vulnerability and green
infrastructure alignment along the Seattle-Tacoma rail corridor.

I would like to request access to green stormwater infrastructure data
for the following jurisdictions:
- Tukwila
- Kent
- Auburn
- King County unincorporated areas

Specifically, I need:
- Permeable pavement installations (location, area, installation date)
- Rain gardens and bioswales
- Any LID/GSI facilities within 500m of rail corridor

Format: Shapefile or GeoJSON with EPSG:4326 or EPSG:2927
Time Period: 1995-present

This data will be used for academic research analyzing spatial alignment
between infrastructure and flood vulnerability. The study will be shared
with Sound Transit for capital improvement planning.

Thank you for your assistance.

[Your Name]
[Institution/Organization]
[Contact Information]
```

#### Pierce County Data Request

**Contact**: Pierce County Public Works & Utilities (253) 798-7470
**URL**: https://gisdata-piercecowa.opendata.arcgis.com/
**Search Terms**: "stormwater facilities", "LID", "green infrastructure"

Use similar email template as above, requesting data for Sumner, Puyallup, Fife, and Pierce County unincorporated areas.

#### City of Tacoma

**Contact**: Tacoma Environmental Services (253) 502-2100
**URL**: https://data.cityoftacoma.org/
**Search**: "Stormwater Facilities", "GSI Inventory"

Check open data portal first before submitting direct request.

### Testing Multi-Jurisdiction Consolidation

```python
from scripts.integrations.multi_jurisdiction import MultiJurisdictionConsolidator
import geopandas as gpd

# Load corridor geometry
corridor = gpd.read_file("data/raw/rail/corridor.gpkg")

# Initialize consolidator
consolidator = MultiJurisdictionConsolidator()

# Fetch all available data
consolidated = consolidator.fetch_all_jurisdictions(
    corridor_gdf=corridor,
    buffer_meters=250
)

# Generate acquisition report
report = consolidator.generate_acquisition_report()
print(report)

# Save consolidated data
consolidator.save_consolidated_data(consolidated)
```

### Expected Timeline
- **Immediate**: Seattle data available now
- **2-4 weeks**: County-level data requests processed
- **4-6 weeks**: Individual city data requests processed

---

## 6. Database Configuration

### PostgreSQL/PostGIS Setup

All API integrations can persist data to PostgreSQL with PostGIS extension.

### Requirements

```bash
# Install PostgreSQL with PostGIS
# macOS (Homebrew)
brew install postgresql postgis

# Ubuntu/Debian
sudo apt-get install postgresql postgis

# Windows
# Download from https://www.postgresql.org/download/windows/
```

### Database Initialization

```sql
-- Create database
CREATE DATABASE geospatial_analysis;

-- Connect to database
\c geospatial_analysis

-- Enable PostGIS extension
CREATE EXTENSION postgis;

-- Create tables
CREATE TABLE noaa_precip_daily (
    date DATE,
    precip_in FLOAT,
    month VARCHAR(7),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE usgs_streamgage_daily (
    datetime TIMESTAMP,
    site_no VARCHAR(20),
    site_name VARCHAR(255),
    value FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE seattle_gsi_weekly (
    facility_id VARCHAR(50),
    jurisdiction VARCHAR(100),
    facility_type VARCHAR(100),
    area_sqft FLOAT,
    installation_date DATE,
    geometry TEXT,
    fetch_date TIMESTAMP
);

-- Add indexes
CREATE INDEX idx_noaa_date ON noaa_precip_daily(date);
CREATE INDEX idx_usgs_site ON usgs_streamgage_daily(site_no, datetime);
CREATE INDEX idx_gsi_juris ON seattle_gsi_weekly(jurisdiction);
```

### Configuration

Add to `config.yaml`:

```yaml
database_url: "postgresql://username:password@localhost:5432/geospatial_analysis"
```

Or environment variable:

```bash
export DATABASE_URL="postgresql://username:password@localhost:5432/geospatial_analysis"
```

---

## 7. Automated Scheduler Configuration

### Setup

1. Create `config.yaml` with all settings:

```yaml
# API Tokens
noaa_cdo_token: "your_token_here"

# Database
database_url: "postgresql://user:pass@localhost:5432/geospatial_analysis"

# Analysis Parameters
buffer_distance_m: 250
```

2. Test scheduler:

```bash
# List scheduled jobs
python scripts/data_pipeline_scheduler.py --config config.yaml --list-schedule

# Test individual job
python scripts/data_pipeline_scheduler.py --config config.yaml --run-now weekly_usgs

# Start scheduler daemon
python scripts/data_pipeline_scheduler.py --config config.yaml --daemon
```

### Production Deployment

#### Using systemd (Linux)

Create `/etc/systemd/system/geospatial-pipeline.service`:

```ini
[Unit]
Description=Geospatial Analysis Data Pipeline
After=network.target postgresql.service

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/GeospatialAnalysis
ExecStart=/path/to/.venv/bin/python scripts/data_pipeline_scheduler.py --config config.yaml --daemon
Restart=on-failure
RestartSec=30

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable geospatial-pipeline
sudo systemctl start geospatial-pipeline
sudo systemctl status geospatial-pipeline
```

#### Using Docker

Create `Dockerfile`:

```dockerfile
FROM python:3.9

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "scripts/data_pipeline_scheduler.py", "--config", "config.yaml", "--daemon"]
```

Run:

```bash
docker build -t geospatial-pipeline .
docker run -d --name pipeline -v $(pwd)/config.yaml:/app/config.yaml geospatial-pipeline
```

---

## 8. Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError: No module named 'integrations'`
**Solution**: Run from repository root, or add to PYTHONPATH:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)/scripts"
```

**Issue**: Database connection fails
**Solution**: Verify PostgreSQL running, check credentials, ensure PostGIS extension installed

**Issue**: NOAA API returns 403 Forbidden
**Solution**: Check token is valid, not rate limited, request within allowed parameters

**Issue**: Multi-jurisdiction consolidator returns empty data
**Solution**: Expected - most jurisdictions require data requests per DATA_GAP_ANALYSIS.md

### Logging

All API integrations log to:
- Console (stdout)
- `data_pipeline.log` file

View logs:

```bash
tail -f data_pipeline.log
```

Increase verbosity:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## 9. Citation Requirements

When using these API integrations in research, cite:

**NOAA CDO**:
Menne, M. J., Durre, I., Vose, R. S., Gleason, B. E., & Houston, T. G. (2012). An overview of the Global Historical Climatology Network-Daily Database. Journal of Atmospheric and Oceanic Technology, 29(7), 897-910.

**USGS Water Services**:
De Cicco, L. A., Hirsch, R. M., Lorenz, D., & Watkins, W. D. (2018). dataRetrieval: R packages for discovering and retrieving water data available from U.S. federal hydrologic web services. R package version 2.7.4.

**Open Data Integration**:
Janssen, M., Charalabidis, Y., & Zuiderwijk, A. (2012). Benefits, adoption barriers and myths of open data and open government. Information systems management, 29(4), 258-268.

**Climate Projections**:
Vose, R. S., et al. (2017). Temperature changes in the United States. In Climate Science Special Report: Fourth National Climate Assessment, Volume I (pp. 185-206). U.S. Global Change Research Program.

---

## 10. Next Steps

After API setup:

1. ✅ Test each integration individually
2. ✅ Configure database persistence
3. ✅ Submit data requests to missing jurisdictions
4. ✅ Configure automated scheduler
5. ✅ Monitor data pipeline logs
6. ✅ Run full analysis pipeline: `python scripts/geospatial_analysis.py`
7. ✅ Launch dashboard: `streamlit run scripts/dashboard.py`

For questions or issues, refer to:
- Main README: [../README.md](../README.md)
- Data Gap Analysis: [../DATA_GAP_ANALYSIS.md](../DATA_GAP_ANALYSIS.md)
- Methodology Guide: [../COMPLETE_METHODOLOGY_GUIDE.txt](../COMPLETE_METHODOLOGY_GUIDE.txt)
