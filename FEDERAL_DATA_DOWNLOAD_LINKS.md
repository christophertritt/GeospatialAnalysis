# Federal Dataset Direct Download Links for Washington State Analysis

**Generated:** December 3, 2025  
**Target Region:** King County (FIPS 53033) and Pierce County (FIPS 53053), Washington State

---

## 1. SSURGO Soils Data - King and Pierce Counties

### **Direct Download Options**

#### Option A: Web Soil Survey (Interactive - Most Reliable)
- **URL:** https://websoilsurvey.nrcs.usda.gov/app/WebSoilSurvey.aspx
- **Steps:**
  1. Navigate to Area of Interest tab
  2. Select Washington State → King County or Pierce County
  3. Under Soil Data Explorer → Soil Properties and Qualities → Hydrologic Soil Group
  4. Add to Shopping Cart → Download
- **Format:** Shapefile, Geodatabase, or GeoJSON
- **Includes:** Hydrologic soil groups (A, B, C, D), soil map units, component data
- **Last Updated:** Varies by county (typically updated quarterly)

#### Option B: Geospatial Data Gateway (Batch Download)
- **URL:** https://gdg.sc.egov.usda.gov/
- **Direct Link:** https://gdg.sc.egov.usda.gov/GDGOrder.aspx
- **Steps:**
  1. Order by County/Counties
  2. Select Washington → King County (53033) and Pierce County (53053)
  3. Select "Soils - SSURGO"
  4. Choose format: Shapefile or File Geodatabase
  5. Submit order (requires free account)
- **Format:** Shapefile (.shp) or File Geodatabase (.gdb)
- **Size:** ~50-200 MB per county (compressed)
- **Delivery:** Email notification when ready (usually within 1 hour)

#### Option C: Soil Data Access API (Programmatic)
- **API Endpoint:** https://sdmdataaccess.nrcs.usda.gov/
- **Query Interface:** https://sdmdataaccess.nrcs.usda.gov/Query.aspx
- **Web Service:** REST/SOAP endpoints for SQL queries
- **Documentation:** https://sdmdataaccess.nrcs.usda.gov/WebServiceHelp.aspx
- **Example Query for Hydrologic Soil Groups:**
```sql
SELECT 
  mu.mukey, mu.musym, mu.muname,
  c.cokey, c.compname, c.comppct_r,
  ch.hydgrp
FROM legend l
INNER JOIN mapunit mu ON l.lkey = mu.lkey
INNER JOIN component c ON mu.mukey = c.mukey
INNER JOIN chorizon ch ON c.cokey = ch.cokey
WHERE l.areasymbol IN ('WA633', 'WA653')  -- King and Pierce counties
AND ch.hzdept_r = 0  -- Surface horizon
ORDER BY mu.mukey, c.cokey
```
- **Note:** Returns tabular data; spatial data requires separate spatial query

#### Option D: gSSURGO (State-Level Raster/Vector)
- **URL:** https://www.nrcs.usda.gov/resources/data-and-reports/gridded-soil-survey-geographic-gssurgo-database
- **Direct Download:** Available through Geospatial Data Gateway
- **Format:** File Geodatabase (.gdb) - state-level
- **Washington State File:** ~2-3 GB
- **Advantages:** Pre-processed, includes raster format (10m resolution)
- **Includes:** All SSURGO attributes including hydrologic soil groups

### **Key Attributes to Extract**
- `hydgrp` - Hydrologic Soil Group (A, B, C, D, A/D, B/D, C/D)
- `mukey` - Map Unit Key (unique identifier)
- `musym` - Map Unit Symbol
- `muname` - Map Unit Name
- `drclassdcd` - Drainage Class

---

## 2. CDC Social Vulnerability Index (SVI) 2020

### **Direct Download Links**

#### Washington State 2020 SVI
- **Primary Source:** CDC/ATSDR GRASP
- **Documentation Page:** https://www.atsdr.cdc.gov/place-health/php/svi/svi-data-documentation-download.html
- **Note:** The CDC SVI data portal has recently been reorganized. Direct download links are provided via interactive map or data request.

#### Download Methods:

##### Method A: CDC Interactive Map (Recommended)
- **Interactive Map:** https://www.atsdr.cdc.gov/placeandhealth/svi/interactive_map.html
- **Steps:**
  1. Navigate to the interactive map
  2. Select "2020 SVI"
  3. Select "Washington State"
  4. Download option appears in map interface
- **Format:** Shapefile, CSV, or Geodatabase
- **Includes:** All census tracts with RPL_THEMES (overall SVI score)

##### Method B: Direct File Access (if available)
- **Expected Filename Pattern:** `SVI2020_Washington.zip` or `Washington_SVI_2020.gdb.zip`
- **Alternative Search:** Search data.gov or gis.data.gov for "CDC SVI 2020 Washington"
- **data.gov Portal:** https://catalog.data.gov/dataset?q=social+vulnerability+index+2020+washington

##### Method C: National Database Download
- **Census Tract Level:** Download entire U.S. database and filter for Washington (FIPS 53)
- **Search Terms:** "CDC SVI 2020 Database Census Tract"
- **Format:** CSV or Geodatabase
- **Filter:** STATE = 'Washington' OR FIPS starts with '53'

### **Key Variables in 2020 SVI**
- **RPL_THEMES** - Overall SVI ranking (0-1, higher = more vulnerable)
- **RPL_THEME1** - Socioeconomic status theme
- **RPL_THEME2** - Household composition & disability theme
- **RPL_THEME3** - Racial & ethnic minority status theme
- **RPL_THEME4** - Housing type & transportation theme
- **FIPS** - Census tract FIPS code
- **LOCATION** - Census tract name

### **2020 SVI Specifics**
- **Year:** 2020 ACS 5-year estimates (2016-2020)
- **Release Date:** October 2022 (corrected December 2022)
- **Geographic Level:** Census tract
- **Format:** Shapefile or File Geodatabase
- **Size:** ~5-15 MB for Washington State
- **Coordinate System:** NAD83 / WGS84

### **Alternative: Download via ArcGIS Hub**
- **ATSDR ArcGIS Hub:** https://atsdr.maps.arcgis.com/
- **Search:** "Social Vulnerability Index 2020"
- **Direct Layer Access:** May provide REST service endpoint for direct query

### **Citation Format**
Centers for Disease Control and Prevention/ Agency for Toxic Substances and Disease Registry/ Geospatial Research, Analysis, and Services Program. CDC/ATSDR Social Vulnerability Index 2020 Database Washington. https://www.atsdr.cdc.gov/placeandhealth/svi/data_documentation_download.html. Accessed on December 3, 2025.

---

## 3. NLCD Tree Canopy Cover 2021

### **Direct Download Links**

#### Option A: USDA Forest Service (Science Product - Recommended for Analysis)
- **Data Portal:** https://data.fs.usda.gov/geodata/rastergateway/treecanopycover/
- **Direct Download Page:** https://data.fs.usda.gov/geodata/rastergateway/treecanopycover/index.php

##### CONUS 2021 Tree Canopy Cover Downloads:
**Forest Service Science TCC (with Standard Error):**
- **2021 TCC Raster:** https://data.fs.usda.gov/geodata/rastergateway/treecanopycover/docs/v2023-5/treecanopy_CONUS_2021_v2023-5.zip
- **2021 TCC Standard Error:** https://data.fs.usda.gov/geodata/rastergateway/treecanopycover/docs/v2023-5/treecanopy_SE_CONUS_2021_v2023-5.zip

**NLCD TCC (Post-processed, Cartographic):**
- **2021 NLCD TCC:** Available through MRLC portal (see Option B below)

- **Format:** GeoTIFF
- **Resolution:** 30 meters
- **Coordinate System:** Albers Equal Area Conic (CONUS)
- **Size:** ~5-8 GB (full CONUS)
- **Values:** 0-100 (percent tree canopy cover)

#### Option B: MRLC (Multi-Resolution Land Characteristics Consortium)
- **MRLC Data Portal:** https://www.mrlc.gov/data
- **Tree Canopy Filter:** https://www.mrlc.gov/data?f%5B0%5D=category%3ATree%20Canopy
- **Direct Download:** https://www.mrlc.gov/data/nlcd-tree-canopy-cover-conus

##### Download Options:
1. **Full CONUS Download:**
   - URL: Select year 2021 from dropdown on MRLC data page
   - Format: GeoTIFF
   - Size: ~6 GB

2. **Regional Download (via MRLC Viewer):**
   - Interactive Map: https://www.mrlc.gov/viewer/
   - Steps: Define AOI → Select Tree Canopy 2021 → Download clip
   - Format: GeoTIFF (clipped to AOI)

3. **Bulk Download (All Years):**
   - Available at MRLC FTP or Box storage (check MRLC data page for current links)

#### Option C: Google Earth Engine (Cloud Processing)
- **Dataset ID:** `USFS/GTAC/NLCD/v2021/CONUS/TCC`
- **Earth Engine Catalog:** https://developers.google.com/earth-engine/datasets/catalog/USFS_GTAC_NLCD_v2021_CONUS_TCC
- **Requires:** Google Earth Engine account (free for research)
- **Advantages:** Cloud-based clipping, no large download needed
- **Export:** Can export clipped raster for King/Pierce Counties

### **Specifications**
- **Product Version:** v2023-5 (released 2025)
- **Years Available:** 1985-2023 (2021 included)
- **Resolution:** 30m × 30m
- **Projection:** Albers Conical Equal Area (EPSG:5070 for CONUS)
- **Data Type:** UInt8 (0-100% canopy cover)
- **NoData Value:** 255
- **Last Updated:** 2025

### **Processing Notes**
- NLCD version includes masking for water and agricultural areas
- Science version includes per-pixel standard error
- For King/Pierce Counties only, consider clipping to reduce file size
- Recommended: Use GDAL to clip to county boundaries before analysis

### **Documentation**
- **Methods PDF:** https://data.fs.usda.gov/geodata/rastergateway/treecanopycover/docs/TCC_v2023-5_Methods.pdf
- **Fact Sheet:** https://data.fs.usda.gov/geodata/rastergateway/treecanopycover/docs/TCC_Fact_Sheet_2024.pdf

---

## 4. Sound Transit Service Area Boundary

### **Download Sources**

#### Option A: Sound Transit Open Transit Data (Official)
- **Portal:** https://www.soundtransit.org/help-contacts/business-information/open-transit-data-otd/otd-downloads
- **Direct GIS Link:** https://www.soundtransit.org/help-contacts/business-information/gis-data
- **Expected Files:**
  - Service area boundary shapefile
  - District boundaries
  - Station locations
  - Rail alignments
- **Format:** Shapefile, GeoJSON, or KML
- **Updates:** Quarterly
- **Coordinate System:** WGS84 or Washington State Plane

#### Option B: King County GIS Open Data
- **Portal:** https://gis-kingcounty.opendata.arcgis.com/
- **Search Terms:** "Sound Transit service area" OR "regional transit"
- **Direct Dataset Search:** 
  - URL: https://gis-kingcounty.opendata.arcgis.com/search?tags=transit
  - Filter by "boundaries" category
- **Format:** Shapefile, GeoJSON, CSV, KML
- **REST Service:** Available for direct API access

#### Option C: Washington State Geospatial Open Data Portal
- **Portal:** https://geo.wa.gov/
- **Search:** "Sound Transit" OR "regional transit service area"
- **Alternative:** https://data.wa.gov/
- **Format:** Multiple formats available

#### Option D: WSDOT GIS Data
- **Portal:** https://www.wsdot.wa.gov/mapsdata/geodatacatalog/
- **Search:** "transit service areas"
- **May Include:** Regional transit authority boundaries

### **Expected Attributes**
- Service area polygon(s)
- District boundaries (North, South, East)
- Subarea designations
- Taxing district information

### **Alternative: Derive from Station Service Areas**
If official service area boundary not available:
- Download Sound Transit station locations
- Create buffer zones (typically 0.5-mile walking distance)
- Merge buffers to create effective service area
- Refine with municipal boundaries

---

## 5. Pierce County Rail Infrastructure

### **Download Sources**

#### Option A: Pierce County GIS Open Data (Primary)
- **Portal:** https://data-piercecowa.opendata.arcgis.com/
- **Search Terms:** "rail" OR "railroad" OR "railway"
- **Direct Search:** https://data-piercecowa.opendata.arcgis.com/search?tags=transportation
- **Expected Datasets:**
  - Active rail lines
  - Abandoned rail corridors
  - Rail crossings
- **Format:** Shapefile, GeoJSON, KML, CSV
- **REST Service:** Available for API access

#### Option B: WSDOT Rail System Data
- **Portal:** https://www.wsdot.wa.gov/mapsdata/geodatacatalog/
- **Dataset:** "Washington State Rail System"
- **Direct Link:** Search for "Rail Network" or "Rail Lines"
- **Coverage:** Statewide (filter for Pierce County)
- **Format:** Shapefile, File Geodatabase
- **Includes:**
  - Freight rail lines
  - Passenger rail (Amtrak, Sounder)
  - Rail ownership
  - Rail class

#### Option C: U.S. Department of Transportation - National Rail Network
- **Portal:** https://data-usdot.opendata.arcgis.com/
- **Dataset:** "North American Rail Network"
- **Direct Link:** https://data-usdot.opendata.arcgis.com/datasets/usdot::north-american-rail-network-lines
- **Download:**
  - Shapefile
  - GeoJSON
  - CSV
  - KML
- **Filter:** STATE = 'WA' AND COUNTY = 'Pierce'
- **Attributes:**
  - Railroad owner/operator
  - Track type
  - Passenger/freight designation
  - Active/abandoned status

#### Option D: OpenStreetMap (Community-Maintained)
- **Overpass Turbo Query:** https://overpass-turbo.eu/
- **Query for Pierce County Rails:**
```overpass
[out:json];
area["name"="Pierce County"]["admin_level"="6"]->.a;
(
  way["railway"="rail"](area.a);
  way["railway"="light_rail"](area.a);
  way["railway"="subway"](area.a);
);
out geom;
```
- **Export Formats:** GeoJSON, GPX, KML
- **Advantages:** Frequently updated, free, no registration
- **Limitations:** May have gaps in rural/industrial areas

#### Option E: U.S. Census Bureau TIGER/Line Files
- **Portal:** https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html
- **Dataset:** "Rails Feature Class"
- **Year:** 2020 or later
- **Download:** https://www2.census.gov/geo/tiger/TIGER2020/RAILS/
- **Filter:** Select Washington State, clip to Pierce County
- **Format:** Shapefile
- **Note:** May not include all freight/industrial spurs

### **Recommended Approach: Combine Multiple Sources**
1. **Primary:** Pierce County GIS (most accurate for local detail)
2. **Supplement:** WSDOT Rail System (for regional context and ownership)
3. **Validate:** OpenStreetMap (for recent changes)
4. **Backup:** USDOT National Rail Network (comprehensive coverage)

### **Key Attributes to Verify**
- Rail line operator (BNSF, UP, Sound Transit, Amtrak, etc.)
- Track type (main line, spur, yard)
- Active vs. abandoned status
- Passenger vs. freight designation
- Track class/speed rating

---

## Data Processing Workflow

### Recommended Download Order:
1. **SSURGO Soils** (via Geospatial Data Gateway - batch download)
2. **CDC SVI 2020** (via interactive map or data portal)
3. **Tree Canopy 2021** (via MRLC or USFS - large file, download last)
4. **Sound Transit Service Area** (via Sound Transit OTD)
5. **Pierce County Rail** (via Pierce County GIS Open Data)

### File Organization:
```
data/
├── raw/
│   ├── soils/
│   │   ├── ssurgo_king_county/
│   │   └── ssurgo_pierce_county/
│   ├── demographics/
│   │   └── SVI_2020_Washington.shp
│   ├── landcover/
│   │   └── NLCD_TCC_2021_CONUS.tif (or clipped version)
│   ├── transit/
│   │   └── sound_transit_service_area.shp
│   └── rail/
│       └── pierce_county_rail_lines.shp
└── processed/
    └── [processed versions after clipping/reprojection]
```

### Post-Download Processing Steps:
1. **Clip large datasets to AOI** (especially Tree Canopy)
2. **Reproject to consistent CRS** (recommend: EPSG:2926 - NAD83(HARN) / Washington South)
3. **Validate geometry** (check for invalid polygons/lines)
4. **Attribute QC** (verify required fields are populated)
5. **Create metadata** (document source, download date, processing steps)

---

## Alternative Data Sources (If Primary Sources Unavailable)

### SSURGO Alternatives:
- **STATSGO2** (lower resolution, state-level)
- **gNATSGO** (harmonized soils database)

### SVI Alternatives:
- **Census ACS Data** (build custom vulnerability index)
- **EJScreen** (EPA environmental justice tool)

### Tree Canopy Alternatives:
- **NLCD Land Cover** (classification-based, not continuous canopy)
- **Sentinel-2 derived canopy** (via Google Earth Engine)
- **LiDAR-derived canopy** (if available for King/Pierce Counties)

### Transit/Rail Alternatives:
- **GTFS Data** (Sound Transit schedule data - can derive routes)
- **OpenStreetMap** (community-maintained rail network)
- **HERE Maps** (commercial, may require license)

---

## Contact Information for Data Support

### SSURGO/NRCS:
- **Soils Hotline:** soilshotline@usda.gov
- **Phone:** 402-437-5378
- **Web Soil Survey Support:** https://www.nrcs.usda.gov/conservation-basics/natural-resource-concerns/soils/state-soil-scientists

### CDC SVI:
- **SVI Coordinator:** svi_coordinator@cdc.gov
- **ATSDR GRASP:** https://www.atsdr.cdc.gov/place-health/php/svi/index.html

### Tree Canopy / MRLC:
- **Forest Service TCC Support:** SM.FS.TCC@usda.gov
- **MRLC Help:** https://www.mrlc.gov/contact-us

### Sound Transit:
- **GIS Contact:** gis@soundtransit.org
- **Open Data Support:** Use contact form at https://www.soundtransit.org/help-contacts

### Pierce County GIS:
- **GIS Division:** https://www.piercecountywa.gov/338/Geographic-Information-System-GIS
- **Data Portal Support:** Via Pierce County Open Data portal

### WSDOT:
- **GeoData Catalog Support:** https://www.wsdot.wa.gov/mapsdata/geodatacatalog/
- **Email:** GeoDataCatalog@wsdot.wa.gov

---

## Data Use and Citation

### Standard Citation Format:
```
[Agency Name]. [Dataset Name]. [Version/Year]. 
Retrieved from [URL]. Accessed [Date].
```

### Examples:

**SSURGO:**
```
USDA Natural Resources Conservation Service. Soil Survey Geographic (SSURGO) Database 
for King County and Pierce County, Washington. Retrieved from 
https://websoilsurvey.nrcs.usda.gov/. Accessed December 3, 2025.
```

**CDC SVI:**
```
Centers for Disease Control and Prevention/Agency for Toxic Substances and Disease Registry. 
CDC/ATSDR Social Vulnerability Index 2020 Database - Washington State. Retrieved from 
https://www.atsdr.cdc.gov/placeandhealth/svi/. Accessed December 3, 2025.
```

**Tree Canopy:**
```
USDA Forest Service. National Land Cover Database Tree Canopy Cover, Version 2023-5. 
Retrieved from https://data.fs.usda.gov/geodata/rastergateway/treecanopycover/. 
Accessed December 3, 2025.
```

---

## Validation Checklist

Before using downloaded data, verify:

- [ ] **Coordinate System:** Matches expected projection
- [ ] **Spatial Extent:** Covers King and Pierce Counties
- [ ] **Attribute Completeness:** Required fields are populated
- [ ] **Temporal Currency:** Data is from expected year/version
- [ ] **File Integrity:** No corruption (check file size, open in GIS)
- [ ] **Geometry Validity:** No invalid geometries or topology errors
- [ ] **Documentation:** Metadata or README included
- [ ] **License:** Understand usage restrictions

---

## Notes on Data Timeliness

| Dataset | Expected Update Frequency | Current Version Date |
|---------|--------------------------|---------------------|
| SSURGO | Quarterly | Check Web Soil Survey |
| CDC SVI | Annually (with lag) | 2020 (released 2022) |
| Tree Canopy | Annually | 2021 (v2023-5, released 2025) |
| Sound Transit Service Area | As needed (expansions) | Check OTD portal |
| Rail Infrastructure | Varies | Check data portal |

**Recommendation:** Always check dataset metadata for "last updated" date to ensure using most current version.

---

*Document compiled December 3, 2025*  
*For updates or corrections, contact your project GIS analyst*
