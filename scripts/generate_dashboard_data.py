#!/usr/bin/env python3
"""
Generate Dashboard-Ready Data and Summary Statistics

This script prepares analysis data for the Streamlit dashboard by:
1. Loading and validating all available datasets
2. Computing summary statistics
3. Creating a data manifest for the dashboard
4. Generating sample visualizations data

Usage:
    python generate_dashboard_data.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, Optional
import warnings

import geopandas as gpd
import pandas as pd
import numpy as np

warnings.filterwarnings('ignore')

# Paths
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
OUTPUT_DIR = DATA_DIR / "dashboard_ready"
OUTPUT_DIR.mkdir(exist_ok=True)


def load_analysis_segments() -> Optional[gpd.GeoDataFrame]:
    """Load analysis segments from available files."""
    candidates = [
        DATA_DIR / "outputs_final" / "analysis_segments.gpkg",
        DATA_DIR / "outputs" / "analysis_segments.gpkg",
        DATA_DIR / "outputs_final" / "analysis_segments.shp",
    ]

    for path in candidates:
        if path.exists():
            print(f"✓ Loading segments from: {path}")
            try:
                gdf = gpd.read_file(path)
                return gdf
            except Exception as e:
                print(f"  ✗ Error loading {path}: {e}")

    print("✗ No analysis segments found")
    return None


def load_infrastructure() -> Optional[gpd.GeoDataFrame]:
    """Load infrastructure data from available files."""
    candidates = [
        DATA_DIR / "outputs_final" / "infrastructure_processed.gpkg",
        DATA_DIR / "processed" / "infrastructure_combined.gpkg",
        DATA_DIR / "raw" / "infrastructure" / "permeable_pavement.gpkg",
    ]

    for path in candidates:
        if path.exists():
            print(f"✓ Loading infrastructure from: {path}")
            try:
                gdf = gpd.read_file(path)
                return gdf
            except Exception as e:
                print(f"  ✗ Error loading {path}: {e}")

    print("✗ No infrastructure data found")
    return None


def compute_summary_statistics(segments: gpd.GeoDataFrame,
                               infrastructure: Optional[gpd.GeoDataFrame]) -> Dict[str, Any]:
    """Compute comprehensive summary statistics."""

    stats = {
        "data_availability": {
            "segments_available": True,
            "infrastructure_available": infrastructure is not None,
            "segment_count": len(segments),
            "infrastructure_count": len(infrastructure) if infrastructure is not None else 0,
        },
        "corridor_metrics": {},
        "vulnerability_summary": {},
        "infrastructure_summary": {},
        "spatial_statistics": {},
        "runoff_summary": {},
    }

    # Corridor metrics
    if "length_miles" in segments.columns:
        stats["corridor_metrics"]["total_length_miles"] = float(segments["length_miles"].sum())
    else:
        # Calculate from geometry
        proj = segments.to_crs(2927)
        stats["corridor_metrics"]["total_length_miles"] = float(proj.geometry.length.sum() / 5280.0)

    stats["corridor_metrics"]["total_buffer_area_acres"] = float(
        segments["buffer_area_acres"].sum() if "buffer_area_acres" in segments.columns
        else segments.to_crs(2927).geometry.area.sum() / 43560.0
    )

    # Vulnerability summary
    if "vuln_mean" in segments.columns:
        stats["vulnerability_summary"]["mean_vulnerability"] = float(segments["vuln_mean"].mean())
        stats["vulnerability_summary"]["max_vulnerability"] = float(segments["vuln_mean"].max())
        stats["vulnerability_summary"]["high_vulnerability_count"] = int((segments["vuln_mean"] > 7.0).sum())
        stats["vulnerability_summary"]["high_vulnerability_percent"] = float(
            (segments["vuln_mean"] > 7.0).sum() / len(segments) * 100
        )

    # Infrastructure summary
    if infrastructure is not None:
        infra_proj = infrastructure.to_crs(2927)
        total_area = infra_proj.geometry.area.sum()
        stats["infrastructure_summary"]["total_facilities"] = int(len(infrastructure))
        stats["infrastructure_summary"]["total_area_sqft"] = float(total_area)
        stats["infrastructure_summary"]["total_area_acres"] = float(total_area / 43560.0)

        if "facility_count" in segments.columns:
            stats["infrastructure_summary"]["segments_with_infrastructure"] = int(
                (segments["facility_count"] > 0).sum()
            )
            stats["infrastructure_summary"]["coverage_percent"] = float(
                (segments["facility_count"] > 0).sum() / len(segments) * 100
            )

    if "density_sqft_per_acre" in segments.columns:
        stats["infrastructure_summary"]["mean_density"] = float(segments["density_sqft_per_acre"].mean())
        stats["infrastructure_summary"]["max_density"] = float(segments["density_sqft_per_acre"].max())
        stats["infrastructure_summary"]["low_density_count"] = int((segments["density_sqft_per_acre"] < 100).sum())

    # Spatial statistics
    if "lisa_cluster" in segments.columns:
        cluster_counts = segments["lisa_cluster"].value_counts().to_dict()
        stats["spatial_statistics"]["lisa_clusters"] = {str(k): int(v) for k, v in cluster_counts.items()}

    if "hotspot_class" in segments.columns:
        hotspot_counts = segments["hotspot_class"].value_counts().to_dict()
        stats["spatial_statistics"]["hotspot_classes"] = {str(k): int(v) for k, v in hotspot_counts.items()}
        stats["spatial_statistics"]["hot_spots_99"] = int((segments["hotspot_class"] == "Hot Spot 99%").sum())
        stats["spatial_statistics"]["hot_spots_95"] = int((segments["hotspot_class"] == "Hot Spot 95%").sum())

    # Runoff summary
    runoff_cols = [col for col in segments.columns if "runoff" in col.lower()]
    if runoff_cols:
        stats["runoff_summary"]["available_scenarios"] = runoff_cols

        if "runoff_current_25-year" in segments.columns:
            stats["runoff_summary"]["mean_runoff_25yr_inches"] = float(
                segments["runoff_current_25-year"].mean()
            )

        if "volume_current_25-year_acft" in segments.columns:
            stats["runoff_summary"]["total_volume_25yr_acft"] = float(
                segments["volume_current_25-year_acft"].sum()
            )

    # Gap analysis
    if "gap_index" in segments.columns:
        stats["gap_analysis"] = {
            "high_gap_count": int((segments["gap_index"] > 0.7).sum()),
            "high_gap_percent": float((segments["gap_index"] > 0.7).sum() / len(segments) * 100),
            "mean_gap_index": float(segments["gap_index"].mean()),
        }

    return stats


def create_sample_charts_data(segments: gpd.GeoDataFrame) -> Dict[str, Any]:
    """Create pre-computed data for charts."""

    charts = {}

    # Vulnerability distribution
    if "vuln_mean" in segments.columns:
        vuln_hist = np.histogram(segments["vuln_mean"].dropna(), bins=20)
        charts["vulnerability_distribution"] = {
            "counts": vuln_hist[0].tolist(),
            "bin_edges": vuln_hist[1].tolist(),
        }

    # Infrastructure density distribution
    if "density_sqft_per_acre" in segments.columns:
        density_hist = np.histogram(
            segments["density_sqft_per_acre"].dropna().clip(0, 1000),
            bins=20
        )
        charts["density_distribution"] = {
            "counts": density_hist[0].tolist(),
            "bin_edges": density_hist[1].tolist(),
        }

    # Hotspot classification
    if "hotspot_class" in segments.columns:
        hotspot_counts = segments["hotspot_class"].value_counts().to_dict()
        charts["hotspot_classification"] = {str(k): int(v) for k, v in hotspot_counts.items()}

    # Temporal cohorts (if installation dates exist)
    if "temporal_period" in segments.columns:
        temporal_counts = segments["temporal_period"].value_counts().to_dict()
        charts["temporal_cohorts"] = {str(k): int(v) for k, v in temporal_counts.items()}

    return charts


def export_lightweight_geojson(segments: gpd.GeoDataFrame) -> None:
    """Export simplified GeoJSON for web mapping."""

    # Select essential columns only
    essential_cols = [
        "segment_id", "vuln_mean", "vuln_class",
        "facility_count", "density_sqft_per_acre",
        "hotspot_class", "gap_index", "geometry"
    ]

    available_cols = [col for col in essential_cols if col in segments.columns]

    # Convert to WGS84 and simplify geometry
    web_segments = segments[available_cols].copy()
    if web_segments.crs != "EPSG:4326":
        web_segments = web_segments.to_crs(4326)

    # Aggressive simplification for web performance
    web_segments["geometry"] = web_segments.geometry.simplify(0.0001, preserve_topology=True)

    output_path = OUTPUT_DIR / "segments_simplified.geojson"
    web_segments.to_file(output_path, driver="GeoJSON")

    print(f"✓ Exported simplified GeoJSON: {output_path}")
    print(f"  Original size: {len(segments)} features")
    print(f"  Simplified size: {len(web_segments)} features")


def generate_data_manifest(stats: Dict[str, Any], charts: Dict[str, Any]) -> None:
    """Generate a manifest file describing all available data."""

    manifest = {
        "generated_at": pd.Timestamp.now().isoformat(),
        "data_version": "1.0",
        "statistics": stats,
        "charts": charts,
        "data_files": {
            "segments_simplified": "segments_simplified.geojson",
            "statistics": "summary_statistics.json",
            "manifest": "data_manifest.json",
        },
        "status": {
            "ready_for_dashboard": stats["data_availability"]["segments_available"],
            "infrastructure_integrated": stats["data_availability"]["infrastructure_available"],
            "spatial_statistics_available": bool(stats["spatial_statistics"]),
            "runoff_analysis_available": bool(stats["runoff_summary"]),
        }
    }

    # Save manifest
    manifest_path = OUTPUT_DIR / "data_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"✓ Generated data manifest: {manifest_path}")

    # Save statistics separately
    stats_path = OUTPUT_DIR / "summary_statistics.json"
    with open(stats_path, "w") as f:
        json.dump(stats, f, indent=2)

    print(f"✓ Generated summary statistics: {stats_path}")


def main():
    """Main execution function."""

    print("="*70)
    print("Dashboard Data Generator")
    print("="*70)
    print()

    # Load data
    print("Loading datasets...")
    segments = load_analysis_segments()
    infrastructure = load_infrastructure()

    if segments is None:
        print("\n✗ ERROR: No analysis segments found!")
        print("  Please run the geospatial analysis pipeline first:")
        print("  python scripts/geospatial_analysis.py")
        return 1

    print(f"\n✓ Loaded {len(segments)} analysis segments")
    if infrastructure is not None:
        print(f"✓ Loaded {len(infrastructure)} infrastructure facilities")
    else:
        print("⚠ No infrastructure data found (dashboard will show analysis only)")

    # Compute statistics
    print("\nComputing summary statistics...")
    stats = compute_summary_statistics(segments, infrastructure)

    # Create chart data
    print("Generating chart data...")
    charts = create_sample_charts_data(segments)

    # Export simplified data
    print("Exporting simplified data for web...")
    export_lightweight_geojson(segments)

    # Generate manifest
    print("Creating data manifest...")
    generate_data_manifest(stats, charts)

    # Print summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"\n✓ Analysis segments: {stats['data_availability']['segment_count']}")
    print(f"✓ Infrastructure facilities: {stats['data_availability']['infrastructure_count']}")

    if stats["corridor_metrics"]:
        print(f"\nCorridor Coverage:")
        print(f"  - Length: {stats['corridor_metrics'].get('total_length_miles', 0):.1f} miles")
        print(f"  - Buffer area: {stats['corridor_metrics'].get('total_buffer_area_acres', 0):.1f} acres")

    if stats["vulnerability_summary"]:
        print(f"\nVulnerability Analysis:")
        print(f"  - Mean vulnerability: {stats['vulnerability_summary'].get('mean_vulnerability', 0):.2f}")
        print(f"  - High vulnerability segments: {stats['vulnerability_summary'].get('high_vulnerability_count', 0)}")

    if stats["spatial_statistics"]:
        print(f"\nSpatial Statistics:")
        if "hot_spots_99" in stats["spatial_statistics"]:
            print(f"  - Hot spots (99%): {stats['spatial_statistics']['hot_spots_99']}")
            print(f"  - Hot spots (95%): {stats['spatial_statistics']['hot_spots_95']}")

    print(f"\n✓ Dashboard-ready data exported to: {OUTPUT_DIR}")
    print("\nNext step: Launch dashboard with:")
    print("  streamlit run scripts/dashboard.py")

    return 0


if __name__ == "__main__":
    exit(main())
