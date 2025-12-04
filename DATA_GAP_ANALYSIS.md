# Data Gap Analysis & Scope Expansion Plan

**Date:** December 3, 2025  
**Project:** Rail Corridor Flood Vulnerability & Green Infrastructure Analysis  
**Region:** Seattle-Tacoma Corridor (King & Pierce Counties)

---

## Executive Summary

### Current Research Question
> **To what extent does current permeable pavement distribution align with stormwater flood vulnerability in the urban rail corridors between Seattle and Tacoma?**

### Current Data Status
- ✅ **Rail Coverage:** Complete for Seattle-Tacoma corridor
- ❌ **Infrastructure Coverage:** SEATTLE ONLY (major gap)
- ⚠️ **Context Data:** Partial coverage for contextual layers

### Critical Findings
1. **Infrastructure data gap:** No permeable pavement data for 8 of 9 cities
2. **Geographic bias:** 100% of green infrastructure data is in Seattle
3. **Analysis limitation:** Current analysis cannot answer the research question for the full corridor

---

## 1. RAIL CORRIDOR DATA REVIEW

### Current Coverage ✅

```
Total Rail Features: 1,746 line segments
Geographic Extent: 47.19°N to 47.66°N (Seattle to Tacoma)
```

#### Coverage by City
| City | Latitude | Within Bounds | Rail Data |
|------|----------|--------------|-----------|
| Seattle | 47.6062 | ✓ | ✓ Complete |
| Tukwila | 47.4740 | ✓ | ✓ Complete |
| Renton | 47.4829 | ✗ | ⚠️ Partial |
| Kent | 47.3809 | ✓ | ✓ Complete |
| Auburn | 47.3073 | ✓ | ✓ Complete |
| Sumner | 47.2034 | ✓ | ✓ Complete |
| Puyallup | 47.1854 | ✗ | ⚠️ Partial |
| Fife | 47.2396 | ✓ | ✓ Complete |
| Tacoma | 47.2529 | ✓ | ✓ Complete |

#### Rail Lines Included
- **BNSF Seattle Subdivision** (151 segments)
- **Sound Transit 1 Line** (70 segments)
- **Federal Way Link Extension** (37 segments)
- **Tacoma Rail** (32 segments)
- **Sounder Lakewood Subdivision** (29 segments)
- **Sound Transit 2 Line** (27 segments)
- **Union Pacific** (26 segments)

### Recommendation: Expand East to Renton ✓
**Action:** Extend bounding box eastward to fully capture Renton rail yards
- Current eastern limit: -122.2191°
- Renton longitude: -122.2171°
- Required extension: ~200 meters east

---

## 2. INFRASTRUCTURE DATA REVIEW

### Current Coverage ❌ CRITICAL GAP

```
Total Facilities: 169 permeable pavement installations
Geographic Extent: 47.52°N to 47.72°N (SEATTLE ONLY)
Latitude Range: ~22 km (13.7 miles)
```

#### Coverage by City
| City | Population | Rail Miles | Infrastructure Data | Status |
|------|-----------|------------|---------------------|---------|
| Seattle | 749,256 | ~25 mi | ✅ 169 facilities | Complete |
| Tukwila | 21,798 | ~3 mi | ❌ 0 facilities | **MISSING** |
| Renton | 106,785 | ~2 mi | ❌ 0 facilities | **MISSING** |
| Kent | 136,588 | ~8 mi | ❌ 0 facilities | **MISSING** |
| Auburn | 82,970 | ~5 mi | ❌ 0 facilities | **MISSING** |
| Sumner | 10,621 | ~2 mi | ❌ 0 facilities | **MISSING** |
| Puyallup | 42,973 | ~4 mi | ❌ 0 facilities | **MISSING** |
| Fife | 10,699 | ~2 mi | ❌ 0 facilities | **MISSING** |
| Tacoma | 219,346 | ~10 mi | ❌ 0 facilities | **MISSING** |

### Impact on Analysis
- **Current analysis is INVALID** for research question
- Only 1 of 9 cities has data
- ~75% of corridor population has no infrastructure data
- Cannot assess alignment south of Seattle city limits

### Data Sources to Acquire

#### 1. King County (Tukwila, Renton, Kent, Auburn)
**Primary Source:** King County Water and Land Resources Division
- URL: https://gis-kingcounty.opendata.arcgis.com/
- Contact: WLRD-GIS@kingcounty.gov
- Search Terms: "green stormwater infrastructure", "permeable pavement", "low impact development"
- Expected Datasets:
  - King County GSI Facilities
  - Surface Water Management Projects
  - NPDES Stormwater Facilities

**Alternative Source:** Cities' Public Works Departments
- Tukwila Public Works: (206) 433-1800
- Renton Utility Systems: (425) 430-7400
- Kent Public Works: (253) 856-5500
- Auburn Environmental Services: (253) 931-3010

#### 2. Pierce County (Sumner, Puyallup, Fife, Tacoma)
**Primary Source:** Pierce County Surface Water Management
- URL: https://gisdata-piercecowa.opendata.arcgis.com/
- Contact: Pierce County Public Works & Utilities (253) 798-7470
- Search Terms: "stormwater facilities", "LID", "green infrastructure"

**City of Tacoma:** Environmental Services Department
- URL: https://data.cityoftacoma.org/
- Contact: Tacoma Environmental Services (253) 502-2100
- Dataset: "Stormwater Facilities" or "GSI Inventory"

**Other Cities:**
- Sumner Public Works: (253) 299-5678
- Puyallup Public Works: (253) 864-4165
- Fife Public Works: (253) 896-8560

---

## 3. CONTEXTUAL DATA REVIEW

### Current Status

| Data Layer | Coverage | Status | Priority |
|------------|----------|--------|----------|
| **Flood Zones (FEMA NFHL)** | Seattle-Tacoma | ✅ Complete | High |
| **Imperviousness (NLCD)** | Regional | ✅ Complete | High |
| **Elevation (DEM)** | Seattle-Tacoma | ✅ Complete | High |
| **Soils (SSURGO)** | Not acquired | ❌ Missing | Medium |
| **Social Vulnerability (SVI)** | Not acquired | ❌ Missing | Medium |
| **Tree Canopy** | Not acquired | ❌ Missing | Low |
| **Zoning (WAZA)** | Not acquired | ❌ Missing | Low |

### Data Gaps to Fill

#### Priority 1: SSURGO Soils
- **Current Status:** Default 'C' soil type used
- **Impact:** Reduces vulnerability index accuracy
- **Source:** https://websoilsurvey.nrcs.usda.gov/
- **Action:** Download SSURGO for King & Pierce Counties
- **Expected Improvement:** 30% more accurate vulnerability scores

#### Priority 2: CDC Social Vulnerability Index (SVI)
- **Current Status:** Not included in analysis
- **Impact:** Cannot assess environmental justice dimensions
- **Source:** https://www.atsdr.cdc.gov/placeandhealth/svi/
- **Action:** Download SVI 2020 for Washington State
- **Expected Benefit:** Identify vulnerable communities near flood-prone rail

#### Priority 3: Tree Canopy Cover
- **Current Status:** Not included
- **Impact:** Missing key green infrastructure indicator
- **Source:** NLCD 2021 Tree Canopy Layer
- **Action:** Download from https://www.mrlc.gov/viewer/
- **Expected Benefit:** Assess natural vs built GSI distribution

#### Priority 4: Zoning Data (WAZA)
- **Current Status:** Not included
- **Impact:** Cannot assess land use patterns
- **Source:** Washington State Zoning Atlas
- **Action:** Download from https://geo.wa.gov/
- **Expected Benefit:** Link infrastructure gaps to zoning/development patterns

---

## 4. SCOPE EXPANSION RECOMMENDATIONS

### Option 1: Complete Seattle-Tacoma Corridor (RECOMMENDED)
**Goal:** Answer original research question with full geographic scope

**Required Actions:**
1. Acquire infrastructure data for 8 missing cities
2. Download SSURGO soils for King & Pierce Counties
3. Acquire SVI data for Washington State
4. Extend Renton coverage slightly eastward

**Timeline:** 2-4 weeks  
**Expected Outcomes:**
- Valid analysis for entire 60+ mile corridor
- Comparative analysis between cities
- Identification of regional infrastructure gaps
- Environmental justice assessment

**Deliverables:**
- Updated analysis covering all 9 cities
- City-by-city comparison tables
- Regional heat maps of vulnerability vs infrastructure
- Priority investment recommendations by jurisdiction

### Option 2: Add Pierce County Sound Transit Service Area
**Goal:** Expand to include all rail in Pierce County ST service area

**Additional Coverage:**
- Lakewood (Sounder terminus)
- DuPont
- University Place
- East Tacoma neighborhoods

**Additional Actions:**
- Extend flood zone data to Lakewood
- Acquire Pierce Transit infrastructure data
- Update rail data to include all ST service area

**Timeline:** 4-6 weeks  
**Expected Outcomes:**
- Full Sound Transit Sounder corridor analysis
- Assessment of future Link extension areas
- Pierce County-wide vulnerability mapping

### Option 3: Add Comparative Analysis Dimensions
**Goal:** Enable cross-jurisdiction and temporal comparisons

**New Analysis Dimensions:**
1. **Jurisdictional Comparison**
   - Infrastructure density by city
   - Vulnerability by city
   - Investment patterns by jurisdiction
   - Policy effectiveness assessment

2. **Temporal Analysis**
   - Infrastructure installation dates (if available)
   - Changes in imperviousness over time
   - Flood event correlation with infrastructure deployment

3. **Land Use & Zoning**
   - Industrial vs residential corridors
   - Zoning restrictions on GSI
   - Opportunity zones for future investment

4. **Environmental Justice**
   - SVI scores by segment
   - Correlation between vulnerability and disadvantaged communities
   - Equitable distribution assessment

**Timeline:** 2-3 weeks (after data acquisition)  
**Expected Outcomes:**
- Actionable policy recommendations
- Identification of systemic gaps
- Evidence base for funding priorities
- Equity-focused investment framework

---

## 5. ENHANCED RESEARCH QUESTIONS

### Original Question
> To what extent does current permeable pavement distribution align with stormwater flood vulnerability in the urban rail corridors between Seattle and Tacoma?

### Expanded Questions (with complete data)

#### Geographic Scope
1. **By City:** How does infrastructure alignment vary across the 9 cities in the corridor?
2. **By County:** Are there systematic differences between King County and Pierce County approaches?
3. **Regional:** Where are the highest-priority gaps in the Seattle-Tacoma corridor?

#### Comparative Dimensions
4. **Jurisdictional:** Which cities have the best alignment between vulnerability and infrastructure?
5. **Land Use:** Does alignment differ between industrial, commercial, and mixed-use corridors?
6. **Temporal:** Has infrastructure deployment improved alignment over time?

#### Equity & Justice
7. **Environmental Justice:** Are high-vulnerability, low-infrastructure areas disproportionately in disadvantaged communities?
8. **Investment Equity:** Is infrastructure investment equitably distributed across the corridor?
9. **Access:** Do all communities have equal access to green infrastructure benefits?

#### Policy & Planning
10. **Zoning Impact:** How do zoning patterns affect GSI deployment opportunities?
11. **Effectiveness:** What is the quantified runoff reduction benefit of existing infrastructure?
12. **ROI:** Which segments offer the highest return on investment for new infrastructure?

---

## 6. IMMEDIATE ACTION PLAN

### Phase 1: Critical Data Acquisition (Week 1-2)
**Priority: CRITICAL**

1. **Contact King County WLRD** (Day 1)
   - Email: WLRD-GIS@kingcounty.gov
   - Request: GSI facilities for Tukwila, Renton, Kent, Auburn
   - Format: Shapefile or GeoJSON with AreaSqFt attribute

2. **Contact Pierce County Public Works** (Day 1)
   - Phone: (253) 798-7470
   - Request: Stormwater facilities for Sumner, Puyallup, Fife, Tacoma
   - Format: Shapefile or GeoJSON with facility size

3. **Contact City of Tacoma** (Day 2)
   - Phone: (253) 502-2100
   - Request: GSI/stormwater facility inventory
   - URL: Check https://data.cityoftacoma.org/

4. **Download SSURGO Soils** (Day 3)
   - Visit: https://websoilsurvey.nrcs.usda.gov/
   - AOI: King County (WA633) + Pierce County (WA053)
   - Format: Shapefile with hydrologic soil groups

### Phase 2: Contextual Data Enhancement (Week 2-3)
**Priority: HIGH**

1. **Download CDC SVI** (Day 5)
   - Visit: https://www.atsdr.cdc.gov/placeandhealth/svi/
   - Year: 2020
   - State: Washington
   - Format: Shapefile

2. **Download NLCD Tree Canopy** (Day 6)
   - Visit: https://www.mrlc.gov/viewer/
   - Layer: NLCD 2021 Tree Canopy
   - Region: King & Pierce Counties
   - Format: GeoTIFF

3. **Download WAZA Zoning** (Day 7)
   - Visit: https://geo.wa.gov/
   - Dataset: WAZA Zoning Atlas Public
   - Region: King & Pierce Counties
   - Format: Shapefile or GeoJSON

### Phase 3: Analysis Updates (Week 3-4)
**Priority: MEDIUM**

1. **Update Rail Corridor** (Day 10)
   - Extend bbox to include full Renton coverage
   - Verify all 9 cities fully covered
   - Re-segment corridor with updated data

2. **Integrate New Infrastructure Data** (Day 11-12)
   - Merge all city datasets
   - Standardize attributes
   - Validate facility counts and areas

3. **Re-run Full Analysis** (Day 13-14)
   - Execute with complete dataset
   - Generate city-by-city comparisons
   - Produce updated visualizations

### Phase 4: Enhanced Reporting (Week 4)
**Priority: MEDIUM**

1. **Generate Comparative Report**
   - Alignment scores by city
   - Jurisdictional comparison tables
   - Regional heat maps

2. **Create Policy Recommendations**
   - High-priority investment areas
   - Equity assessment findings
   - Jurisdiction-specific recommendations

3. **Update Documentation**
   - Revised README with expanded scope
   - Updated methodology guide
   - New visualization examples

---

## 7. DATA VALIDATION CHECKLIST

### Before Re-running Analysis

- [ ] Infrastructure data covers all 9 cities
- [ ] All datasets in same CRS (EPSG:2927)
- [ ] Facility size attribute present (AreaSqFt)
- [ ] Rail data extends to Renton eastward boundary
- [ ] SSURGO soils downloaded for King & Pierce Counties
- [ ] CDC SVI downloaded for Washington State
- [ ] Tree canopy raster covers full corridor
- [ ] Zoning data covers King & Pierce Counties
- [ ] All datasets validated for null geometries
- [ ] Attribute fields standardized across jurisdictions

### Quality Assurance

- [ ] Verify infrastructure counts match jurisdictional records
- [ ] Cross-check vulnerability scores with known flood-prone areas
- [ ] Validate alignment correlations are statistically significant
- [ ] Confirm all 1,746+ rail segments have complete attribute data
- [ ] Test spatial joins produce reasonable results
- [ ] Review hot spot analysis for spatial autocorrelation artifacts

---

## 8. EXPECTED OUTCOMES WITH COMPLETE DATA

### Quantitative Improvements
- **Coverage:** 100% of corridor (vs current 11% by population)
- **Sample Size:** 1,746 segments (same) with complete attributes
- **Infrastructure Facilities:** 500-1,000+ (vs current 169)
- **Analysis Validity:** Full corridor assessment (vs single city)

### New Analytical Capabilities
1. **Cross-jurisdictional comparison** of infrastructure deployment patterns
2. **Environmental justice analysis** using SVI scores
3. **Land use influence** assessment using zoning data
4. **Natural vs built GSI** comparison using canopy cover
5. **Soil-based vulnerability** refinement (vs default assumptions)

### Policy Impact
- **Evidence-based** infrastructure gap identification
- **Equity-focused** investment prioritization
- **Jurisdiction-specific** recommendations for each city
- **Regional coordination** opportunities identified
- **Cost-benefit** analysis for infrastructure expansion

---

## 9. CONCLUSION

### Critical Gaps Identified
1. ❌ **Infrastructure data:** Missing for 8 of 9 cities (89% gap)
2. ⚠️ **Soils data:** Using default values (reduces accuracy)
3. ⚠️ **Social vulnerability:** No equity assessment possible
4. ⚠️ **Geographic extent:** Renton partially excluded

### Recommended Path Forward
**Immediate Priority:** Acquire infrastructure data for all cities
- Without this, the current analysis **cannot answer the research question**
- Contact King County and Pierce County GIS departments
- Timeline: 2 weeks for data acquisition

**Secondary Priority:** Enhance contextual layers
- SSURGO soils, CDC SVI, tree canopy, zoning
- Enables richer analysis and policy recommendations
- Timeline: 2 weeks for data acquisition

**Final Priority:** Scope expansion analysis
- Comparative analysis across cities
- Environmental justice assessment
- Temporal patterns (if installation dates available)
- Timeline: 2 weeks for analysis and reporting

### Next Steps
1. **Initiate data requests** to King County and Pierce County (Day 1)
2. **Download contextual datasets** from federal sources (Day 3-7)
3. **Update analysis pipeline** to integrate new data (Week 2-3)
4. **Generate comprehensive report** with full corridor coverage (Week 4)

**Total Timeline:** 4 weeks to complete scope expansion with enhanced analysis capabilities
