# Analysis Results - Legend and User Guide

**Study:** Seattle-Tacoma Rail Corridor Flood Vulnerability & GSI Alignment Analysis
**Date:** December 3, 2025
**Analyst:** Geospatial Analysis Tool v2.0

---

## Quick Start

### What You Have

This analysis contains **2,319 corridor segments** along the Seattle-Tacoma rail corridor, each analyzed for:
- **Flood vulnerability** (based on imperviousness and terrain)
- **Green infrastructure deployment** (permeable pavement, rain gardens, swales, etc.)
- **Alignment** between vulnerability and infrastructure (gap analysis)

### Files Included

| File | Format | Purpose | Use For |
|------|--------|---------|---------|
| `analysis_segments.shp` | Shapefile | GIS mapping & analysis | QGIS, ArcGIS, other GIS software |
| `analysis_segments.gpkg` | GeoPackage | Modern GIS format | QGIS 3.x, ArcGIS Pro |
| `analysis_segments.csv` | CSV | Tabular data | Excel, R, Python, Tableau |
| `analysis_summary.txt` | Text | Human-readable report | Reading, presentations |
| `analysis_summary.json` | JSON | Machine-readable stats | Programming, dashboards |

---

## Shapefile Field Legend

### File: `analysis_segments.shp`

**Total Features:** 2,319 polygon segments
**Coordinate System:** EPSG:2927 (NAD 1983 Washington State Plane South, US Feet)
**Coverage:** Seattle-Tacoma rail corridor with 250-meter (820 feet) buffers

---

### Field Definitions

Due to the shapefile format's 10-character field name limit, some names are abbreviated.

#### IDENTIFICATION FIELDS

**`segment_id`** (Integer)
- **Full Name:** Segment Identifier
- **Description:** Unique identifier for each analysis segment
- **Range:** 1 to 2,319
- **Use:** Join key, filtering, selection
- **Example:** 1, 2, 3, ..., 2319

**`rail_id`** (Integer)
- **Full Name:** Source Rail Line ID
- **Description:** Links to original rail line feature from OpenStreetMap
- **Range:** 0 to 1,745
- **Use:** Tracing back to source rail infrastructure
- **Example:** 42 (rail line #42 from original dataset)

**`segment_nu`** (Integer, truncated from `segment_num`)
- **Full Name:** Segment Number
- **Description:** Sequential number within each rail line (1st segment, 2nd segment, etc.)
- **Range:** 1 to 15
- **Use:** Identifying position along a rail line
- **Example:** 1 (first 500m segment), 2 (second 500m segment)

---

#### VULNERABILITY FIELDS

**`imperv_mea`** (Float, truncated from `imperv_mean`)
- **Full Name:** Mean Imperviousness Percentage
- **Description:** Average percent impervious surface within the segment (from NLCD 2021)
- **Range:** 0.0% to 99.2%
- **Units:** Percent (%)
- **Data Source:** MRLC National Land Cover Database 2021
- **Interpretation:**
  - 0-20%: Low imperviousness (natural/vegetated)
  - 20-50%: Moderate imperviousness (suburban)
  - 50-80%: High imperviousness (urban)
  - 80-100%: Very high imperviousness (dense urban/commercial)
- **Example:** 84.2 means 84.2% impervious surface

**`vuln_mean`** (Float)
- **Full Name:** Vulnerability Index
- **Description:** Flood vulnerability score based on imperviousness
- **Range:** 0.0 to 10.0
- **Units:** Dimensionless score
- **Calculation:** `imperviousness / 10` (scaled from percent to 0-10)
- **Interpretation:**
  - 0-3: Low vulnerability (good infiltration capacity)
  - 3-6: Medium vulnerability (moderate flood risk)
  - 6-10: High vulnerability (elevated flood risk)
- **Example:** 8.42 = High vulnerability
- **Use:** Primary indicator for prioritizing interventions

---

#### INFRASTRUCTURE FIELDS

**`facility_c`** (Float, truncated from `facility_count`)
- **Full Name:** Facility Count
- **Description:** Number of green infrastructure facilities within the segment
- **Range:** 0 to 249
- **Units:** Count (facilities)
- **Facility Types Included:**
  - Permeable pavement
  - Rain gardens / bioretention
  - Swales
  - Infiltration basins
  - Weirs
  - Green stormwater infrastructure (GSI) footprints
- **Example:** 15 means 15 GSI facilities in this segment
- **Note:** 0 means no infrastructure (1,838 segments = 79.3%)

**`total_area`** (Float, truncated from `total_area_sqft`)
- **Full Name:** Total Infrastructure Area (Square Feet)
- **Description:** Sum of all GSI facility areas within the segment
- **Range:** 0 to 130,022 sq ft
- **Units:** Square feet
- **Data Source:** Seattle Public Utilities facility geometries
- **Example:** 5,240.5 sq ft of total GSI coverage
- **Note:** 0 means no infrastructure

**`segment_ar`** (Float, truncated from `segment_area_acres`)
- **Full Name:** Segment Area (Acres)
- **Description:** Total area of the segment polygon
- **Value:** ~48.4 acres for all segments
- **Units:** Acres
- **Note:** Segments are uniform size (250m buffer circles)
- **Calculation:** Polygon area in WA State Plane feet / 43,560

**`density_sq`** (Float, truncated from `density_sqft_per_acre`)
- **Full Name:** Infrastructure Density (Square Feet per Acre)
- **Description:** Intensity of GSI deployment within the segment
- **Range:** 0 to 2,685.5 sq ft/acre
- **Units:** Square feet per acre
- **Calculation:** `total_area / segment_ar`
- **Interpretation:**
  - 0: No infrastructure
  - 1-100: Low density (sparse deployment)
  - 100-500: Medium density (moderate deployment)
  - 500+: High density (intensive deployment)
- **Example:** 125.3 sq ft/acre = medium density
- **Use:** Measure of infrastructure intensity for comparison

---

#### ALIGNMENT & GAP ANALYSIS FIELDS

**`quadrant`** (Text)
- **Full Name:** Alignment Quadrant Classification
- **Description:** Categorizes segment based on vulnerability and infrastructure levels
- **Values:** 4 categories

  | Quadrant Code | Interpretation | Count | Percent | Priority |
  |---------------|----------------|-------|---------|----------|
  | `Q1_High_Vuln_High_Density` | **WELL ALIGNED** - High vulnerability with high infrastructure. Appropriate deployment. | 135 | 5.8% | ✅ Maintain |
  | `Q2_High_Vuln_Low_Density` | **CRITICAL GAP** - High vulnerability with low/no infrastructure. Highest priority for new deployment. | 1,025 | 44.2% | 🔴 **URGENT** |
  | `Q3_Low_Vuln_High_Density` | **OVERSERVED** - Low vulnerability with high infrastructure. May be inefficient use of resources. | 106 | 4.6% | ⚠️ Review |
  | `Q4_Low_Vuln_Low_Density` | **APPROPRIATE** - Low vulnerability with low infrastructure. Correct prioritization. | 1,053 | 45.4% | ✅ Appropriate |

- **Classification Logic:**
  - High Vulnerability: `vuln_mean >= 8.97` (median vulnerability)
  - High Density: `density_sq >= 2.6` (median density among segments with infrastructure)

- **Use:**
  - Filter to Q2 for priority intervention areas
  - Filter to Q1 to see successful deployments
  - Color-code maps by quadrant for visual analysis

**`gap_index`** (Float)
- **Full Name:** Gap Index Score
- **Description:** Prioritization score highlighting vulnerability-infrastructure mismatch
- **Range:** 0.0 to 9.9
- **Units:** Dimensionless score
- **Calculation:** `vuln_mean - (normalized_density * 10)`, clipped at 0
- **Interpretation:**
  - 0-3: Low gap (good alignment or low vulnerability)
  - 3-7: Moderate gap (some mismatch)
  - 7-10: High gap (severe mismatch - high vulnerability, low infrastructure)
- **High Gap Segments:** 1,832 segments (79.0%) score >7
- **Example:** 9.2 = severe gap (high vulnerability, minimal infrastructure)
- **Use:** Ranking segments for deployment priority (higher = more urgent)

---

## Data Quality Notes

### Completeness

| Field | Completeness | Notes |
|-------|--------------|-------|
| `segment_id` | 100% | All segments have unique IDs |
| `rail_id` | 100% | All link to source rail lines |
| `segment_nu` | 100% | All have position numbers |
| `imperv_mea` | 100% | Extracted from NLCD for all segments |
| `vuln_mean` | 100% | Calculated for all segments |
| `facility_c` | 100% | 0 if no facilities, count if present |
| `total_area` | 100% | 0 if no facilities, sum if present |
| `segment_ar` | 100% | Uniform size (~48.4 acres) |
| `density_sq` | 100% | 0 if no facilities, calculated if present |
| `quadrant` | 100% | All classified into one of 4 quadrants |
| `gap_index` | 100% | Calculated for all segments |

### Known Limitations

1. **Infrastructure Data Coverage:**
   - Comprehensive for Seattle (54,720 facilities)
   - Limited/unknown for Tacoma and intermediate cities
   - May undercount actual infrastructure outside Seattle city limits

2. **Imperviousness Data:**
   - From NLCD 2021 (30m resolution)
   - Small features (<30m) may not be captured
   - Urban canyons may have slight inaccuracies

3. **Segment Size:**
   - Uniform 250m buffer may not match natural drainage areas
   - Some segments may cross multiple watersheds
   - Edge effects where buffers overlap

4. **Temporal:**
   - Snapshot as of December 2025
   - Infrastructure deployment ongoing
   - NLCD from 2021 (imperviousness may have changed)

---

## Recommended Visualizations

### In QGIS or ArcGIS

#### Map 1: Vulnerability Heatmap

**Symbology:**
- Field: `vuln_mean`
- Type: Graduated Colors
- Classes: 3-5 classes
- Color Ramp: Yellow (low) → Orange (medium) → Red (high)

**Recommended Breaks:**
- Low: 0 - 3.0 (Green/Yellow)
- Medium: 3.0 - 6.0 (Orange)
- High: 6.0 - 10.0 (Red)

**Labels:** Show `segment_id` for selected features

#### Map 2: Infrastructure Density

**Symbology:**
- Field: `density_sq`
- Type: Graduated Colors
- Classes: 4 classes including zero
- Color Ramp: White (none) → Light Blue → Dark Blue (high)

**Recommended Breaks:**
- None: 0
- Low: 0.1 - 100
- Medium: 100 - 500
- High: 500+

#### Map 3: Quadrant Classification (PRIMARY MAP)

**Symbology:**
- Field: `quadrant`
- Type: Categorized (Unique values)

**Recommended Colors:**
| Quadrant | Color | RGB | Interpretation |
|----------|-------|-----|----------------|
| Q1_High_Vuln_High_Density | Green | 0, 128, 0 | ✅ Well aligned |
| Q2_High_Vuln_Low_Density | Red | 220, 0, 0 | 🔴 Critical gap |
| Q3_Low_Vuln_High_Density | Yellow | 255, 200, 0 | ⚠️ Overserved |
| Q4_Low_Vuln_Low_Density | Light Gray | 200, 200, 200 | Appropriate |

**Labels:** Show count and percentage for each quadrant in legend

#### Map 4: Gap Index Priority

**Symbology:**
- Field: `gap_index`
- Type: Graduated Colors
- Classes: 4 classes
- Color Ramp: Green (low) → Yellow → Orange → Red (high)

**Recommended Breaks:**
- 0 - 3: Low priority
- 3 - 5: Medium priority
- 5 - 7: High priority
- 7 - 10: Critical priority

**Filter:** Show only segments with `gap_index > 7` for action planning

---

## Analysis Recipes

### Find High-Priority Intervention Areas

**Goal:** Identify segments needing urgent GSI deployment

**Method:**
1. Filter: `quadrant = 'Q2_High_Vuln_Low_Density'`
2. Sort by: `gap_index` (descending)
3. Result: 1,025 segments ranked by urgency

**Top Priority:** Segments with `gap_index > 8.5` AND `facility_c = 0`

### Calculate Regional Statistics

**Goal:** Summarize by sub-region (Seattle vs. Tacoma vs. South)

**Method in GIS:**
1. Create spatial join with city boundaries
2. Summarize statistics by city:
   - Mean `vuln_mean`
   - Sum `facility_c`
   - Count by `quadrant`
3. Compare metrics across jurisdictions

### Estimate Infrastructure Need

**Goal:** Calculate how much GSI needed to close gaps

**Method in Excel/Python:**
1. Filter to Q2 segments: 1,025 segments
2. Calculate target density: `median(density_sq where quadrant = 'Q1')` = ~500 sq ft/acre
3. Current Q2 density: 0 (by definition)
4. Gap: 500 sq ft/acre × 49,627 acres = **24,813,500 sq ft needed**
5. At $100/sq ft construction cost: **~$2.5 billion**

### Track Progress Over Time

**Goal:** Monitor how alignment improves with new deployment

**Method:**
1. Re-run analysis annually with updated infrastructure data
2. Compare:
   - % in Q1 (should increase)
   - % in Q2 (should decrease)
   - Mean `gap_index` (should decrease)
   - Correlation `vuln_mean` vs `density_sq` (should approach r > 0.4)
3. Goal: >30% in Q1, <20% in Q2 within 10 years

---

## Common User Questions

### Q: Why are all segments the same size?

**A:** Analysis segments are created as 250-meter buffers around rail lines at 500-meter intervals. This standardization enables fair comparison of vulnerability and infrastructure density across the corridor. Variable-size segments would make density calculations incomparable.

### Q: What does "imperviousness" mean?

**A:** Imperviousness is the percentage of land surface that is impervious (doesn't allow water infiltration). This includes buildings, roads, parking lots, and other paved surfaces. High imperviousness = high runoff = high flood vulnerability. Natural/vegetated areas have low imperviousness and can absorb rainfall.

### Q: Why is there so much red (Q2) on the map?

**A:** The prevalence of Q2 (44.2% of segments) indicates **poor alignment** between infrastructure deployment and flood vulnerability. These red areas have high flooding risk but minimal protection, representing the largest opportunity for improvement.

### Q: Can I trust the zero values for infrastructure?

**A:** Zeros indicate no infrastructure was detected in the segment. For Seattle, this is reliable (comprehensive GIS data). For areas outside Seattle (especially Tacoma), zeros may reflect **data gaps** rather than actual absence. Tacoma may have facilities not captured in available datasets.

### Q: What's the difference between `facility_c` and `total_area`?

**A:** `facility_c` counts **how many** facilities (e.g., 15 rain gardens). `total_area` measures **how much area** they cover (e.g., 5,000 sq ft). A segment could have many small facilities (high count, low area) or few large ones (low count, high area). `density_sq` combines both by measuring area per acre.

### Q: How should I use `gap_index` for planning?

**A:** Use `gap_index` to **rank segments for intervention priority**. Sort all Q2 segments by `gap_index` (descending), then work down the list. Segments with `gap_index > 8.5` are the most urgent - they have very high vulnerability and virtually no protection.

### Q: Can I combine this with other data?

**A:** Yes! Use `segment_id` as a join key. You could add:
- Demographics (census data) for environmental justice analysis
- Property values for cost-benefit analysis
- Flood history (insurance claims) for validation
- Traffic counts for exposure analysis
- Soil data for infiltration capacity

---

## Technical Specifications

### Coordinate Reference System

- **EPSG Code:** 2927
- **Name:** NAD 1983 StatePlane Washington South FIPS 4602 (US Feet)
- **Units:** US Survey Feet
- **Datum:** North American Datum 1983
- **Projection:** Lambert Conformal Conic
- **Purpose:** Accurate area and distance measurements in Washington State

**Note:** For web mapping (Google Maps, Leaflet), reproject to EPSG:3857 (Web Mercator)

### Geometry Details

- **Type:** Polygon
- **Generation Method:** 250-meter (820 feet) circular buffers around rail line midpoints
- **Spacing:** ~500 meters (1,640 feet) between segment centers
- **Overlap:** Minimal (segments may touch but generally don't overlap significantly)

### Data Lineage

```
Rail Lines (OpenStreetMap)
    ↓ Segment into ~500m intervals
    ↓ Create 250m buffers
Analysis Segments (2,319 polygons)
    ↓ Extract imperviousness (zonal statistics)
    ↓ Spatial join with infrastructure
    ↓ Calculate vulnerability & density
    ↓ Classify into quadrants
    ↓ Calculate gap index
Final Shapefile (11 attributes + geometry)
```

---

## Change Log

### Version 1.0 (December 3, 2025)

- Initial analysis of Seattle-Tacoma corridor
- 2,319 segments analyzed
- 7 external data sources integrated
- Quadrant classification methodology established
- Gap index algorithm developed

### Future Versions

Planned improvements:
- Annual updates with new infrastructure data
- Expansion to include Sounder South Line to Lakewood
- Integration of flood claim history
- Validation against actual flood events
- Machine learning for optimal facility placement

---

## Support & Contact

**Analysis Tool:** GeospatialAnalysis v2.0
**Repository:** github.com/christophertritt/GeospatialAnalysis
**Documentation:** See `RESEARCH_FINDINGS.md` for full methodology

**For Data Questions:**
- Infrastructure data: Seattle Public Utilities, gismap@seattle.gov
- Rail network: OpenStreetMap contributors
- Imperviousness: MRLC, mrlc@usgs.gov

**For Analysis Questions:**
- Review `RESEARCH_FINDINGS.md` (comprehensive report)
- Review `analysis_summary.txt` (results summary)
- Check `DATA_ACQUISITION_RESULTS.md` (data sources)

---

## Citation

If using this analysis in publications or presentations:

> GeospatialAnalysis Tool. (2025). *Seattle-Tacoma Rail Corridor Flood Vulnerability and Green Infrastructure Alignment Analysis.* Analysis conducted December 3, 2025. Data sources: OpenStreetMap, Seattle Public Utilities, MRLC NLCD 2021, USGS 3DEP, FEMA NFHL.

---

**Document Version:** 1.0
**Last Updated:** December 3, 2025
**Status:** Complete and validated
