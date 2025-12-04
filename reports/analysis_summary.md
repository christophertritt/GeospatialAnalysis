# Alignment of Permeable Pavement with Flood Vulnerability (Seattle–Tacoma Rail Corridor)

_Last generated: 2025-12-03_

## Headline Answer

> **Poor alignment.** Only **5.8%** of corridor segments pair high stormwater flood vulnerability with high permeable pavement coverage, while **44.2%** of segments represent critical gaps (high vulnerability, low infrastructure).

## Snapshot Statistics

- **Study extent:** 2,319 buffered rail segments covering 112,277 acres.
- **Vulnerability:** Mean index **8.42 / 10**; 90.5% of segments classified as high vulnerability.
- **Infrastructure presence:** 13,208 GSI facilities mapped; only 20.7% of segments contain any permeable pavement.
- **Correlation:** Pearson **r = 0.000 (p = 0.998)** → infrastructure deployment shows no statistical association with vulnerability scores.

### Quadrant Breakdown

| Quadrant | Interpretation | Segments | Acreage |
| --- | --- | ---:| ---:|
| Q1 | High vulnerability + High infrastructure (well aligned) | 135 | 6,536 |
| Q2 | High vulnerability + Low infrastructure (critical gap) | 1,025 | 49,627 |
| Q3 | Low vulnerability + High infrastructure (overserved) | 106 | — |
| Q4 | Low vulnerability + Low infrastructure (appropriate) | 1,053 | — |

## Implications

1. **Targeted investment required:** The 49,627 acres in Q2 should be prioritized for new GSI deployment to mitigate elevated flood risk.
2. **Seattle-centric installations:** Current permeable pavement inventory is concentrated within Seattle city limits, leaving the broader corridor underserved.
3. **Recalibrate planning:** Adopt vulnerability-driven siting criteria; current deployments appear opportunistic or jurisdictionally constrained.

## Provenance

- Narrative report: `data/outputs/analysis_summary.txt`
- GIS outputs: `data/outputs/analysis_segments.gpkg`
- Tabular metrics: `data/outputs/analysis_segments.csv`
- Workflow entry point: `scripts/geospatial_analysis.py`

Consult `docs/research_question_alignment.md` for data requirements and reproduction instructions.
