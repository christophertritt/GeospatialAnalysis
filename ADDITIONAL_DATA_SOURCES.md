# Additional Publicly Available Datasets for Seattle-Tacoma Rail Corridor Analysis

**Document Date:** December 3, 2025  
**Purpose:** Supplement current geospatial analysis with additional public data sources

---

## 1. OpenStreetMap Data Extracts

### Geofabrik Extracts
**URL:** https://download.geofabrik.de/north-america/us/washington.html

**Available Data:**
- Complete Washington State extract updated daily
- Includes railways, roads, waterways, land use, buildings
- Available formats: .osm.pbf, .shp.zip (shapefiles)
- Last updated: Daily

**Direct Download Link:**
```
https://download.geofabrik.de/north-america/us/washington-latest.osm.pbf
https://download.geofabrik.de/north-america/us/washington-latest-free.shp.zip
```

**Relevant Layers in Shapefile:**
- `gis_osm_railways_free_1.shp` - Railway lines
- `gis_osm_water_a_free_1.shp` - Water bodies and polygons
- `gis_osm_landuse_a_free_1.shp` - Land use classifications
- `gis_osm_natural_free_1.shp` - Natural features including green spaces

**How to Use:**
1. Download the shapefile package (~150 MB for Washington)
2. Extract and filter to King and Pierce Counties using county boundaries
3. Select railways using `fclass IN ('rail', 'light_rail', 'subway')`

---

### Overpass API Queries

#### Query 1: Railways in King and Pierce Counties
```
[out:json][timeout:300];
(
  way["railway"="rail"](47.0,-122.7,47.8,-121.5);
  way["railway"="light_rail"](47.0,-122.7,47.8,-121.5);
  way["railway"="subway"](47.0,-122.7,47.8,-121.5);
);
out body;
>;
out skel qt;
```

**Overpass Turbo Link:**
https://overpass-turbo.eu/ (paste query above)

**Export:** GeoJSON, GPX, KML formats available

---

#### Query 2: Green Infrastructure Features
```
[out:json][timeout:300];
(
  // Rain gardens and bioswales
  way["landuse"="grass"]["name"~"rain garden|bioswale",i](47.0,-122.7,47.8,-121.5);
  node["natural"="wetland"]["wetland"="swamp"](47.0,-122.7,47.8,-121.5);
  
  // Green roofs
  way["roof:material"="green"](47.0,-122.7,47.8,-121.5);
  
  // Parks and green spaces
  way["leisure"="park"](47.0,-122.7,47.8,-121.5);
  way["landuse"="meadow"](47.0,-122.7,47.8,-121.5);
  
  // Permeable surfaces
  way["surface"="grass_paver"](47.0,-122.7,47.8,-121.5);
  way["surface"="gravel"](47.0,-122.7,47.8,-121.5);
);
out body;
>;
out skel qt;
```

**Note:** OSM coverage of stormwater infrastructure is limited. This query will return some features but is not comprehensive.

---

#### Query 3: Stormwater Infrastructure (Limited Coverage)
```
[out:json][timeout:300];
(
  // Drainage features
  way["waterway"="drain"](47.0,-122.7,47.8,-121.5);
  way["waterway"="ditch"](47.0,-122.7,47.8,-121.5);
  node["man_made"="drainage"](47.0,-122.7,47.8,-121.5);
  
  // Retention ponds
  way["landuse"="basin"]["basin"="detention"](47.0,-122.7,47.8,-121.5);
  way["natural"="water"]["water"="pond"]["usage"="detention"](47.0,-122.7,47.8,-121.5);
);
out body;
>;
out skel qt;
```

**Limitations:**
- OSM stormwater data is volunteer-contributed and incomplete
- Best used to supplement, not replace, official municipal data
- Quality varies significantly by area

---

## 2. Regional Planning Data - Puget Sound Regional Council (PSRC)

### Main GIS Portal
**URL:** https://www.psrc.org/our-work/data-hub
**Alternative:** https://psrcgis.maps.arcgis.com/

**Available Datasets:**

#### Land Use Data
- **2018 Urban Land Use** - Detailed parcel-level land use
- **Regional Growth Centers** - High-density development areas
- **Manufacturing/Industrial Centers**
- Format: Shapefiles, File Geodatabase
- Coverage: 4-county region (King, Pierce, Snohomish, Kitsap)

**Direct Access:**
1. Visit: https://www.psrc.org/our-work/data-hub
2. Navigate to "Land Use" section
3. Download "Land Use 2018" dataset

#### Transportation Data
- **Regional Transit Network** - All transit routes including Sound Transit
- **High Capacity Transit Stations** - Light rail and commuter rail stations
- **Freight Significant Corridors**
- **Non-Motorized Facilities** - Bike lanes, trails

**How This Fills Gaps:**
- Provides regional context for rail corridor analysis
- Land use data useful for understanding development patterns near rail
- Transit accessibility metrics

**Data Quality:** Good - regularly updated by regional planning staff

---

## 3. Washington State Department of Ecology

### GIS Data Portal
**URL:** https://ecology.wa.gov/Research-Data/Data-resources/Geographic-Information-Systems-GIS/Data

**Key Datasets for This Analysis:**

#### Municipal Stormwater Permit Areas
- **Dataset Name:** Municipal Stormwater Permit Areas
- **Direct Link:** Search for "Municipal Stormwater" on the GIS Data page
- **Format:** File Geodatabase (.gdb)
- **Last Updated:** 2023
- **Contents:** 
  - Phase I and Phase II permit boundaries
  - Municipal Separate Storm Sewer System (MS4) jurisdictions
  - Useful for identifying which municipalities have stormwater management requirements

#### NPDES Permit Locations
**URL:** https://apps.ecology.wa.gov/paris/PermitLookup.aspx

**Description:**
- PARIS (Permit and Reporting Information System)
- Search by permit type: "Stormwater" or "Industrial Stormwater"
- Export results with coordinates
- Can be geocoded into GIS layer

**Specific Search Strategy:**
1. Select "Stormwater - Construction"
2. Select "Stormwater - Industrial"
3. Filter to King and Pierce Counties
4. Export to CSV with facility locations

**Limitations:**
- Individual facility locations, not comprehensive stormwater infrastructure
- Focuses on regulated facilities, may miss municipal GSI projects

---

#### Land Cover Data
- **Dataset:** Land Cover: Basins Potentially Meeting 40% Total Impervious Area
- **Format:** File Geodatabase
- **Relevance:** Identifies high-imperviousness areas where GSI would be most beneficial

#### Water Quality Data
- **Environmental Information Management (EIM) Database**
- **URL:** https://ecology.wa.gov/Research-Data/Data-resources/Environmental-Information-Management-database
- **Contents:** Water quality monitoring stations, sample results
- **Spatial Data:** Can be queried and exported with coordinates

---

## 4. Alternative Infrastructure Data Sources

### 4.1 iTree Data - Urban Tree Canopy

#### National iTree Landscape Tool
**URL:** https://landscape.itreetools.org/

**Features:**
- Web-based tool providing tree canopy data
- Uses NLCD (National Land Cover Database) and NAIP imagery
- Census tract level data
- Free access, no download required

**Data Available:**
- % Tree canopy cover by census tract
- Urban heat island metrics
- Air quality benefits estimates
- Potential planting areas

**For Seattle-Tacoma Analysis:**
1. Navigate to Seattle/Tacoma metropolitan area
2. Draw boundary around rail corridor (or upload shapefile)
3. Export summary statistics
4. Use census tract IDs to join with your analysis

**Alternative: City-Specific Tree Canopy Data**

**Seattle Tree Canopy (2016)**
- **Source:** Seattle Open Data Portal
- **URL:** https://data.seattle.gov/
- **Search:** "Tree Canopy"
- **Dataset:** 2016 Tree Canopy Assessment
- **Format:** Raster (GeoTIFF), Vector (Shapefile)
- **Resolution:** 1-meter for raster
- **Coverage:** City of Seattle only

**Tacoma Tree Canopy**
- Check: https://cityoftacoma.org/
- May need to contact Planning & Development Services
- Alternative: Use iTree Landscape for consistent methodology

---

### 4.2 EPA Green Infrastructure Resources

#### National Green Infrastructure Dataset
**URL:** https://www.epa.gov/green-infrastructure/epa-green-infrastructure-resources

**Available Resources:**
- **Green Infrastructure Modeling Toolkit**
  - SWMM (Storm Water Management Model) input files
  - Not a dataset, but modeling support

- **EPA Smart Location Database**
  - **URL:** https://www.epa.gov/smartgrowth/smart-location-mapping
  - Census block group level data
  - Walkability, transit access, development density
  - Can correlate with GSI effectiveness

**Direct Download:**
https://edg.epa.gov/EPADataCommons/public/OA/SLD/SmartLocationDb.gdb.zip

**Relevant Variables:**
- `D4a` - Transit access index
- `D1B` - Employment density
- `D3b` - Street network density (indicator of imperviousness)

---

### 4.3 FEMA Community Rating System (CRS) Documentation

**URL:** https://www.fema.gov/floodplain-management/community-rating-system

**What It Provides:**
- List of communities participating in CRS
- Some communities' CRS documentation may reference GSI inventories
- Not direct GIS data but can identify which cities to contact

**King County CRS Communities:**
- Seattle (Class 5)
- King County Unincorporated (Class 6)
- Several other municipalities

**Pierce County CRS Communities:**
- Tacoma (Class 7)
- Pierce County Unincorporated (Class 8)

**Strategy:**
Contact these communities' floodplain managers for GSI data they may have compiled for CRS credit.

---

## 5. Academic/Research Datasets

### 5.1 University of Washington Earth Lab
**URL:** https://earthlab.uw.edu/
**Data Portal:** https://data.uwelp.org/ (if available)

**Potential Datasets:**
- Urban heat island studies (thermal imagery)
- Salmon habitat restoration projects (may include GSI)
- Climate change projections for Puget Sound

**Note:** Many datasets are project-specific. Contact researchers directly.

---

### 5.2 Green Seattle Partnership
**URL:** https://greenseattle.org/

**Available Data:**
- Forest restoration project locations
- Tree planting records
- **Data Access:** May require direct contact

**Strategy:**
Email: info@greenseattle.org
Request: Spatial data on urban forest restoration projects near rail corridors

**Relevance:** Urban forests provide stormwater benefits similar to GSI

---

### 5.3 Seattle Public Utilities - RainWise Program
**URL:** https://www.seattle.gov/utilities/protecting-our-environment/community-programs/rainwise

**Data Potential:**
- Locations of private property rain gardens (program subsidies)
- Cistern installations
- Permeable pavement projects

**Access:** 
- No public GIS download apparent
- Submit public records request to Seattle Public Utilities
- Reference: RainWise participant locations (anonymized to street level)

---

### 5.4 Published Research Datasets

**Search Strategy:**
1. **Zenodo** - https://zenodo.org/
   - Search: "Seattle stormwater" OR "Tacoma green infrastructure"
   - Filter: Datasets with DOI

2. **Figshare** - https://figshare.com/
   - Similar search strategy

3. **DataONE** - https://www.dataone.org/
   - Environmental/ecological data network
   - Search by geographic area

**Example Relevant Studies:**
- "Urban green infrastructure siting for stormwater management" studies
- "Rail corridor ecological connectivity" research
- Check Google Scholar for recent publications, then look for data supplements

---

## 6. County-Level Open Data Portals

### King County Open Data
**URL:** https://gis-kingcounty.opendata.arcgis.com/

**Key Datasets:**

#### Stormwater Infrastructure
- **Search:** "Stormwater" on the portal
- **Available Datasets:**
  - Stormwater Facilities (county-maintained)
  - Drainage Basins
  - Stream Network

#### Environmental Data
- **Sensitive Areas**
  - Wetlands
  - Stream buffers
  - Steep slopes
- **Tree Canopy (County unincorporated areas)**

**Direct Download:** GeoJSON, Shapefile, KML, CSV formats

**How to Use:**
1. Visit portal
2. Search "stormwater facilities"
3. Click dataset → Download → Select format
4. Filter to rail corridor area in your GIS

---

### Pierce County Open Data
**URL:** https://gis-piercecowa.opendata.arcgis.com/

**Available Datasets:**
- Drainage infrastructure
- Land use parcels
- Wetlands inventory
- Zoning districts

**Note:** Coverage may be more limited than King County

---

### Seattle Open Data Portal
**URL:** https://data.seattle.gov/

**Key Datasets:**

#### Green Seattle Partnership Sites
- **Dataset Name:** "Green Seattle Partnership Sites"
- **Format:** Shapefile, GeoJSON, CSV
- **Content:** Forest restoration project boundaries

#### Seattle Street Trees
- **Dataset Name:** "Street Trees"
- **Format:** CSV with lat/lon
- **Records:** ~200,000+ individual street trees
- **Fields:** Species, condition, location

#### Right-of-Way Improvements
- **Dataset Name:** Search "Right of Way"
- May include green street elements

#### Seattle Public Utilities Assets
- Search for: "SPU" or "drainage"
- Some stormwater infrastructure layers available

---

### Tacoma Open Data
**URL:** https://data.cityoftacoma.org/

**Available Datasets:**
- Stormwater facilities (limited)
- Parks and open spaces
- Land use parcels
- Tree inventory (if available)

**Access Similar to Seattle:** Download directly from portal

---

## 7. Sound Transit GIS Data

### Official GIS Data Portal
**Updated URL:** https://www.soundtransit.org/help-contacts/business-information/gis-data-downloads

**Alternative Access:**
- **ArcGIS Online:** Search "Sound Transit" on ArcGIS Online
- **Direct Portal:** https://soundtransit.maps.arcgis.com/

**Available Datasets:**
- Link Light Rail Lines (current and planned)
- Sounder Commuter Rail Lines
- Station locations
- Transit-Oriented Development areas
- Park & Ride locations

**Format:** Shapefiles, File Geodatabase, Web Services (WMS/WFS)

**Relevance:** Essential for defining the rail corridor precisely

---

## 8. Additional Federal Data Sources

### 8.1 USGS StreamStats
**URL:** https://streamstats.usgs.gov/ss/

**Features:**
- Watershed delineation tool
- Basin characteristics (slope, soil type, land use)
- Peak flow estimates

**For Your Analysis:**
Delineate watersheds intersecting rail corridor to understand drainage patterns

---

### 8.2 NRCS Web Soil Survey (SSURGO)
**Already in use, but additional access:**
**URL:** https://websoilsurvey.nrcs.usda.gov/

**Additional Tip:**
- Download "Soil Data Viewer" tool from NRCS
- Provides thematic maps of:
  - Infiltration rates
  - Drainage class
  - Hydrologic soil groups
- More detailed than standard SSURGO tables

---

### 8.3 NOAA Digital Coast
**URL:** https://coast.noaa.gov/digitalcoast/

**Relevant Data:**
- **C-CAP Land Cover** (Coastal Change Analysis Program)
  - Higher accuracy than NLCD for coastal areas
  - Includes Puget Sound region
  - 30-meter resolution
  
- **Coastal Lidar Data**
  - High-resolution elevation data
  - Useful for flood modeling near Puget Sound

**Download:** Data Access Viewer tool on the site

---

## 9. Summary Table: Data Source Priority Rankings

| Data Source | Priority | Data Quality | Completeness | Ease of Access | Update Frequency |
|-------------|----------|--------------|--------------|----------------|------------------|
| King County Open Data Portal | **HIGH** | Excellent | Good | Easy | Quarterly |
| OSM (Geofabrik) | **HIGH** | Good | Moderate | Very Easy | Daily |
| WA Ecology GIS Data | **HIGH** | Excellent | Good | Moderate | Annually |
| PSRC Data Hub | **HIGH** | Excellent | Good | Moderate | Annually |
| Sound Transit GIS | **HIGH** | Excellent | Excellent | Easy | Quarterly |
| Seattle Open Data | **MEDIUM** | Good | Good | Easy | Varies |
| iTree Landscape | **MEDIUM** | Good | Good | Easy | 5+ years |
| EPA Smart Location DB | **MEDIUM** | Good | Excellent | Easy | ~5 years |
| Pierce County Open Data | **MEDIUM** | Fair-Good | Moderate | Easy | Varies |
| Tacoma Open Data | **MEDIUM** | Fair | Fair | Easy | Varies |
| Green Seattle Partnership | **LOW** | Unknown | Unknown | Hard | Unknown |
| UW Research Data | **LOW** | Varies | Varies | Hard | One-time |

---

## 10. Recommended Overpass API Workflow

### Setup
1. Install QGIS plugin "QuickOSM" for easy Overpass queries
2. Or use command-line tool: `pip install overpass`

### Python Script for Automated OSM Download
```python
import overpass
import json

api = overpass.API()

# Define bounding box for Seattle-Tacoma corridor
bbox = (47.0, -122.7, 47.8, -121.5)  # (min_lat, min_lon, max_lat, max_lon)

# Query for railways
query = f"""
[bbox:{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}];
(
  way["railway"="rail"];
  way["railway"="light_rail"];
  way["railway"="subway"];
);
out body;
>;
out skel qt;
"""

response = api.get(query, responseformat="geojson")

# Save to file
with open('osm_railways.geojson', 'w') as f:
    json.dump(response, f)
```

---

## 11. Data Integration Strategy

### Step 1: Core Infrastructure Data
1. Sound Transit rail lines (authoritative source)
2. King County stormwater facilities
3. WA Ecology municipal stormwater permit areas

### Step 2: Environmental Context
1. Tree canopy (iTree Landscape or Seattle/County data)
2. SSURGO soils (already have)
3. Land cover (NLCD or WA Ecology impervious surface data)

### Step 3: Supplemental GSI Features
1. OSM green infrastructure features
2. Seattle/Tacoma parks and open spaces
3. PSRC land use for development context

### Step 4: Verification and Gap-Filling
1. Compare OSM data with official sources
2. Identify spatial gaps
3. Prioritize field verification or additional data requests

---

## 12. Contact Information for Data Requests

### King County
- **Department:** Wastewater Treatment Division / Stormwater Services
- **Email:** dnrp.wlrd@kingcounty.gov
- **Phone:** 206-477-4800
- **Request:** GSI project inventory, recent green infrastructure installations

### Seattle Public Utilities
- **Department:** Drainage and Wastewater
- **Email:** spuinfo@seattle.gov
- **Request:** RainWise participant locations, GSI facility inventory

### Tacoma Environmental Services
- **Department:** Environmental Services
- **Phone:** 253-502-2100
- **Request:** Stormwater facility inventory, GSI projects

### Pierce County
- **Department:** Planning and Public Works
- **Email:** pals@piercecountywa.gov
- **Request:** Stormwater infrastructure GIS layers

---

## 13. Notes on Data Quality and Limitations

### OpenStreetMap
**Strengths:**
- Excellent coverage of transportation infrastructure
- Good coverage of parks and natural features
- Free, open license

**Weaknesses:**
- GSI features are under-mapped
- Quality varies by contributor activity
- May be outdated in some areas
- Not suitable as sole source for infrastructure analysis

**Recommendation:** Use OSM as supplemental data and for exploratory analysis, but verify with official sources.

---

### Municipal Data
**Strengths:**
- Authoritative and accurate
- Regularly updated
- Maintained by professional GIS staff

**Weaknesses:**
- May not be publicly available for all datasets
- Different standards between jurisdictions
- Some datasets require public records requests

---

### Federal Data (USGS, EPA, NOAA)
**Strengths:**
- Consistent methodology across regions
- Well-documented
- Freely available

**Weaknesses:**
- May be coarser resolution than local data
- Update cycles can be infrequent (5+ years)
- May not capture local GSI projects

---

## 14. Next Steps for Implementation

1. **Immediate Downloads (Easy Wins):**
   - Geofabrik Washington shapefile extract
   - King County Open Data stormwater layers
   - Sound Transit GIS data
   - EPA Smart Location Database

2. **Medium-Term Acquisitions:**
   - WA Ecology geodatabases (requires navigating their data page)
   - PSRC datasets (may need to request specific layers)
   - Seattle tree canopy data

3. **Long-Term or As-Needed:**
   - Public records requests for GSI inventories
   - Contact academic researchers for specific datasets
   - Field verification of OSM data

4. **Data Processing Pipeline:**
   - Standardize all datasets to same projection (WA State Plane South, NAD83)
   - Clip to rail corridor buffer (suggest 1-mile buffer)
   - Create unified attribute schema
   - Document data provenance

---

## 15. Alternative Search Strategies

### Google Dataset Search
**URL:** https://datasetsearch.research.google.com/

**Search Terms:**
- "Seattle stormwater GIS"
- "Tacoma green infrastructure shapefile"
- "King County environmental data"
- "Puget Sound transportation GIS"

### State GIS Clearinghouse
**URL:** https://geo.wa.gov/

**Description:** Washington State Geospatial Data Archive
**Contents:** Various state agency GIS data
**Relevance:** May have datasets not on individual agency sites

---

## Document Metadata

**Author:** Research Assistant  
**Created:** December 3, 2025  
**Purpose:** Data acquisition support for GeospatialAnalysis project  
**Target Analysis:** Seattle-Tacoma rail corridor green stormwater infrastructure assessment

**Revision History:**
- v1.0 (2025-12-03): Initial compilation

---

## Appendix: Overpass Turbo Query Templates

Save these as text files and paste into https://overpass-turbo.eu/

### Template 1: All Green Spaces Near Rail
```
[out:json][timeout:300];
{{geocodeArea:King County}}->.searchArea;
(
  way["leisure"="park"](area.searchArea);
  way["landuse"="forest"](area.searchArea);
  way["landuse"="grass"](area.searchArea);
  way["natural"="wood"](area.searchArea);
);
out body;
>;
out skel qt;
```

### Template 2: Water Features
```
[out:json][timeout:300];
(
  way["waterway"](47.0,-122.7,47.8,-121.5);
  way["natural"="water"](47.0,-122.7,47.8,-121.5);
  way["natural"="wetland"](47.0,-122.7,47.8,-121.5);
);
out body;
>;
out skel qt;
```

---

**End of Document**
