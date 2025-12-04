# Data Acquisition Guide

This guide provides instructions for obtaining the data required for geospatial analysis of rail corridors and green infrastructure.

## Overview

The analysis requires the following core datasets:
1. Rail corridor geometry
2. Permeable pavement infrastructure
3. Digital elevation model (optional but recommended)
4. Soil data (optional but recommended)
5. Land cover/imperviousness (optional but recommended)

## Required Data

### 1. Rail Corridor Data

**Source**: Washington State Department of Transportation (WSDOT)

**URL**: https://geo.wa.gov/datasets/wsdot::wsdot-railways/

**Format**: Shapefile or GeoJSON

**Contents**: Rail line geometries, ownership, track type

**Acquisition Steps**:
1. Navigate to WSDOT GeoData portal
2. Search for "railways" or "rail lines"
3. Download as Shapefile or GeoJSON
4. Save to `data/raw/rail/`

**Alternative Source**: Sound Transit GIS Data
- URL: https://www.soundtransit.org/get-to-know-us/documents-reports
- Request GIS layers for specific corridors

### 2. Permeable Pavement Infrastructure

**Seattle Public Utilities**:
- URL: https://data-seattlecitygis.opendata.arcgis.com/
- Dataset: "SPU DWW Permeable Pavement"
- Search: "SPU permeable pavement"

**King County**:
- URL: https://gis-kingcounty.opendata.arcgis.com/
- Search: "green stormwater infrastructure" OR "permeable pavement"
- Contact: WLRD-GIS@kingcounty.gov

**Pierce County**:
- URL: https://gisdata-piercecowa.opendata.arcgis.com/
- Search: "stormwater facilities"

**Tacoma**:
- URL: https://data.cityoftacoma.org/
- Search: "green infrastructure" OR "stormwater"

**Save to**: `data/raw/infrastructure/`

## Optional Data (Recommended for Full Analysis)

### 3. Elevation Data (LiDAR)

**Source**: Washington State Lidar Portal

**URL**: https://lidarportal.dnr.wa.gov/

**Acquisition**:
1. Select area of interest (King and Pierce Counties)
2. Filter for recent acquisitions (2021 or later)
3. Download as LAS/LAZ or pre-processed DEM
4. Recommended resolution: 3-foot or better

**Alternative**: USGS National Elevation Dataset
- URL: https://apps.nationalmap.gov/downloader/
- Resolution: 10 meters (lower quality)

**Save to**: `data/raw/elevation/`

### 4. Soil Data

**Source**: USDA NRCS Web Soil Survey

**URL**: https://websoilsurvey.nrcs.usda.gov/

**Acquisition**:
1. Navigate to Web Soil Survey
2. Set Area of Interest (AOI):
   - Upload corridor buffer shapefile, OR
   - Draw polygon around study area
3. Select "Soil Data Explorer" tab
4. Choose "Hydrologic Soil Group"
5. Export: Spatial data (Shapefile) + Tabular data

**Required Attributes**:
- mukey (map unit key)
- Hydrologic Soil Group (A, B, C, D)
- Drainage class

**Save to**: `data/raw/soils/`

### 5. Land Cover / Imperviousness

**Source**: USGS National Land Cover Database (NLCD)

**URL**: https://www.mrlc.gov/data

**Dataset**: NLCD 2021 Percent Developed Imperviousness

**Acquisition**:
1. Go to Multi-Resolution Land Characteristics Consortium
2. Select "NLCD 2021"
3. Choose "Percent Developed Imperviousness" layer
4. Download for Western Washington
5. Clip to study area in GIS

**Alternative**: Seattle Open Data
- URL: https://data.seattle.gov
- Search: "impervious surfaces"
- Higher resolution for Seattle area

**Save to**: `data/raw/landcover/`

### 6. Drainage Infrastructure (Optional)

**Seattle**:
- URL: https://data.seattle.gov
- Datasets: "Storm Drain Lines", "Storm Drain Catch Basins"

**King County**:
- URL: https://gis-kingcounty.opendata.arcgis.com/
- Search: "storm" OR "drainage"

**Save to**: `data/raw/drainage/`

## Data Processing Checklist

Before running the analysis, ensure:

- [ ] All shapefiles are in the same coordinate system (or tool will reproject)
- [ ] Rail corridor has line or polygon geometry
- [ ] Infrastructure points/polygons have area attributes
- [ ] Raster data (DEM, imperviousness) covers the study area
- [ ] No corrupted or empty files

## Coordinate Systems

The tool will automatically reproject data to:
- **WA State Plane South NAD83(2011)**
- **EPSG: 2927**
- **Units**: US Survey Feet

However, data quality is best when original data is already in this projection.

## Data Privacy and Usage

When using public data sources:
1. Check data licenses and usage restrictions
2. Cite data sources appropriately
3. Respect data sharing agreements
4. Do not redistribute proprietary data

## Contact Information

For data access issues:

**WSDOT GIS**:
- Email: GISHelp@wsdot.wa.gov

**Seattle Public Utilities**:
- Phone: (206) 684-3000

**King County**:
- Email: WLRD-GIS@kingcounty.gov

**Pierce County Public Works**:
- Phone: (253) 798-7470

## Sample Data

**Note:** Sample data generation has been removed in the latest version. You must provide real data files to run the analysis. See `CHANGES_SUMMARY.md` for details.

## Additional Resources

- [COMPLETE_METHODOLOGY_GUIDE.txt](../COMPLETE_METHODOLOGY_GUIDE.txt) - Full methodology
- [WSDOT GIS Data Portal](https://geo.wa.gov/)
- [Seattle Open Data](https://data.seattle.gov/)
- [USGS Data Download](https://apps.nationalmap.gov/)

## Need Help?

If you encounter issues acquiring data:
1. Check the data source website for updates
2. Contact the data provider directly
3. Refer to the COMPLETE_METHODOLOGY_GUIDE.txt Section 1 for detailed instructions
4. Open an issue on the GitHub repository
