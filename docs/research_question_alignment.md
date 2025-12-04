# Permeable Pavement vs. Flood Vulnerability Alignment

## Research Question

**To what extent does current permeable pavement distribution align with stormwater flood vulnerability in the urban rail corridors between Seattle and Tacoma?**

This repository is organized so that answering the question above is the central objective. The sections below document the evidence, reproduction steps, and data dependencies for the latest assessment.

## Executive Answer (2025-12-03)

| Metric | Finding |
| --- | --- |
| Overall alignment | **Poor** – only 5.8% of segments show high vulnerability with high infrastructure coverage |
| Critical gaps | **44.2%** of segments have high vulnerability but low infrastructure density |
| Correlation | Pearson **r = 0.000 (p = 0.998)** → no detectable targeting of infrastructure to risk |
| Coverage | GSI present in **20.7%** of corridor segments; mean density 65.6 sq ft/acre |
| Vulnerability | Mean score **8.42 / 10** (90.5% of corridor flagged as high vulnerability) |

All summary statistics are sourced from `data/outputs/analysis_summary.txt` (also mirrored in `reports/analysis_summary.md`).

## Evidence Map

- **Quadrant classification** partitions segments into alignment categories (High/Low vulnerability vs. High/Low infrastructure). Gap segments reside in Quadrant Q2.
- **Gap index** and density metrics are stored in `data/outputs/analysis_segments.gpkg` for spatial inspection with GIS tools.
- **Raw infrastructure records** originate from Seattle Public Utilities (permeable pavement facilities) and are standardized to EPSG:2927 before analysis.
- **Vulnerability index** blends imperviousness (NLCD), slope (USGS 3DEP DEM), and soils (USDA SSURGO) into a 0–10 scale.

## How to Reproduce the Answer

1. Prepare the data environment by downloading all required datasets (see below) and storing them in the default `data/` hierarchy.
2. Execute the alignment workflow:

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

3. Review the generated outputs in `data/outputs/`:
   - `analysis_summary.txt` for the human-readable narrative answer.
   - `analysis_segments.gpkg` for GIS-ready segment metrics.
   - `analysis_summary.json` for machine-readable key indicators.

4. Optionally, run `pytest` to confirm automated checks succeed before reporting results.

## Data Dependencies

| Dataset | Purpose | Source | Expected Location |
| --- | --- | --- | --- |
| Rail corridor geometry | Defines rail segments/buffers | WSDOT GeoData Portal / OpenStreetMap | `data/raw/rail/corridor.shp` |
| Permeable pavement (GSI) | Infrastructure density | Seattle Public Utilities (open data) | `data/raw/infrastructure/permeable_pavement.shp` |
| NLCD imperviousness raster | Imperviousness component of vulnerability | MRLC NLCD 2021 | `data/raw/landcover/nlcd_2019_impervious_aoi.tif` |
| DEM raster | Slope proxy | USGS 3DEP | `data/raw/elevation/dem_aoi.tif` |
| SSURGO soils | Hydrologic soil groups | USDA Web Soil Survey | `data/processed/soils/ssurgo_aoi.gpkg` |
| FEMA NFHL flood zones (optional) | Contextual mapping layers | FEMA National Flood Hazard Layer | `data/raw/flood/nfhl_aoi.gpkg` |
| NOAA Atlas 14 (optional) | Precipitation scenarios | NOAA Atlas 14 | `data/raw/precip/*.json` |

Refer to `docs/DATA_ACQUISITION_GUIDE.md` for scripted download instructions.

## Output Inventory

| Artifact | Location | Description |
| --- | --- | --- |
| Narrative summary | `data/outputs/analysis_summary.txt` | Detailed written answer and recommendations |
| Alignment snapshot | `reports/analysis_summary.md` | Markdown-friendly recap derived from the narrative summary |
| Segment metrics | `data/outputs/analysis_segments.gpkg` | Spatial layer with vulnerability, density, quadrant, and gap index fields |
| Tabular export | `data/outputs/analysis_segments.csv` | Non-spatial CSV of segment metrics |
| Machine summary | `data/outputs/analysis_summary.json` | Key indicators for dashboards/automation |

## Interpretation Guidance

- **Alignment is presently insufficient.** Planning teams should prioritize Quadrant Q2 segments (high vulnerability, low infrastructure) for near-term investment.
- **Spatial clustering results** (if enabled) can be used to phase interventions by hotspot intensity.
- **Runoff modeling outputs** supplement the alignment metrics when evaluating mitigation benefits of new GSI installations.

## Next Steps for Analysts

1. Validate that current infrastructure inventories outside Seattle are complete; observed gaps may partially reflect missing data.
2. Develop jurisdiction-specific deployment targets by intersecting Q2 segments with municipal boundaries.
3. Re-run the workflow after each major data refresh to maintain an up-to-date alignment assessment.
4. Synchronize findings with capital planning documents to ensure vulnerability-driven prioritization.
