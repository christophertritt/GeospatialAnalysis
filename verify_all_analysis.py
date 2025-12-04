#!/usr/bin/env python3
"""
Comprehensive verification of all geospatial analysis components.

This script checks that all analysis modules have been run and data is complete.
"""

from __future__ import annotations

from pathlib import Path
import sys

import geopandas as gpd
import pandas as pd
import numpy as np

ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data"

def check_analysis_segments():
    """Verify analysis segments exist and have all required data."""
    print("\n" + "="*70)
    print("1. ANALYSIS SEGMENTS")
    print("="*70)

    paths = [
        DATA_DIR / "outputs_final" / "analysis_segments.gpkg",
        DATA_DIR / "outputs" / "analysis_segments.gpkg",
    ]

    for path in paths:
        if path.exists():
            print(f"✓ Found: {path}")
            segments = gpd.read_file(path)

            print(f"  - Segments: {len(segments):,}")
            print(f"  - CRS: {segments.crs}")
            print(f"  - Columns: {len(segments.columns)}")

            # Check key analysis columns
            key_cols = {
                "Vulnerability": ["vuln_mean", "vuln_class"],
                "Infrastructure": ["facility_count", "density_sqft_per_acre", "total_area_sqft"],
                "Spatial Stats": ["lisa_cluster", "hotspot_class", "gi_star"],
                "Runoff": ["cn_current", "runoff_current_25-year"],
                "Gap Analysis": ["gap_index", "quadrant"],
            }

            print("\n  Analysis Components:")
            for category, cols in key_cols.items():
                present = [col for col in cols if col in segments.columns]
                if present:
                    print(f"    ✓ {category}: {len(present)}/{len(cols)} columns")
                else:
                    print(f"    ✗ {category}: MISSING")

            return segments

    print("✗ No analysis segments found")
    return None


def check_infrastructure():
    """Verify infrastructure data exists."""
    print("\n" + "="*70)
    print("2. INFRASTRUCTURE DATA")
    print("="*70)

    paths = [
        DATA_DIR / "outputs_final" / "infrastructure_processed.gpkg",
        DATA_DIR / "processed" / "infrastructure_combined.gpkg",
    ]

    for path in paths:
        if path.exists():
            print(f"✓ Found: {path}")
            infra = gpd.read_file(path)

            print(f"  - Facilities: {len(infra):,}")
            print(f"  - CRS: {infra.crs}")

            # Calculate total area
            if infra.crs != "EPSG:2927":
                infra_proj = infra.to_crs(2927)
            else:
                infra_proj = infra

            total_area = infra_proj.geometry.area.sum()
            print(f"  - Total area: {total_area:,.0f} sq ft ({total_area/43560:.1f} acres)")

            return infra

    print("✗ No infrastructure data found")
    return None


def check_spatial_statistics(segments):
    """Verify spatial statistics have been computed."""
    print("\n" + "="*70)
    print("3. SPATIAL STATISTICS")
    print("="*70)

    if segments is None:
        print("✗ Cannot check - no segments loaded")
        return False

    # Check for spatial stats columns
    spatial_cols = {
        "Moran's I (LISA)": ["lisa_I", "lisa_pvalue", "lisa_cluster"],
        "Getis-Ord Gi*": ["gi_star", "gi_pvalue", "hotspot_class"],
    }

    all_present = True
    for analysis, cols in spatial_cols.items():
        present = all(col in segments.columns for col in cols)
        if present:
            print(f"✓ {analysis}")

            # Show statistics
            if "hotspot_class" in segments.columns:
                hotspot_counts = segments["hotspot_class"].value_counts()
                print(f"  Hot spots:")
                for cls, count in hotspot_counts.items():
                    print(f"    - {cls}: {count}")
        else:
            print(f"✗ {analysis}: Missing columns {[c for c in cols if c not in segments.columns]}")
            all_present = False

    return all_present


def check_runoff_modeling(segments):
    """Verify runoff modeling has been computed."""
    print("\n" + "="*70)
    print("4. RUNOFF MODELING (SCS CURVE NUMBER)")
    print("="*70)

    if segments is None:
        print("✗ Cannot check - no segments loaded")
        return False

    # Check for curve number and runoff columns
    required = {
        "Curve Numbers": ["cn_current", "cn_with_gsi", "cn_optimized"],
        "Runoff Depths": ["runoff_current_25-year", "runoff_no_gsi_25-year"],
        "Runoff Volumes": ["volume_current_25-year_acft", "volume_no_gsi_25-year_acft"],
    }

    all_present = True
    for category, cols in required.items():
        present = [col for col in cols if col in segments.columns]
        if len(present) == len(cols):
            print(f"✓ {category}: All present")

            # Show sample stats
            if "runoff_current_25-year" in segments.columns:
                mean_runoff = segments["runoff_current_25-year"].mean()
                print(f"  Mean 25-yr runoff: {mean_runoff:.2f} inches")
            if "volume_current_25-year_acft" in segments.columns:
                total_volume = segments["volume_current_25-year_acft"].sum()
                print(f"  Total 25-yr volume: {total_volume:,.0f} acre-feet")
        elif present:
            print(f"⚠ {category}: Partial ({len(present)}/{len(cols)})")
            all_present = False
        else:
            print(f"✗ {category}: Missing")
            all_present = False

    return all_present


def check_vulnerability_analysis(segments):
    """Verify vulnerability analysis is complete."""
    print("\n" + "="*70)
    print("5. VULNERABILITY ANALYSIS")
    print("="*70)

    if segments is None:
        print("✗ Cannot check - no segments loaded")
        return False

    # Check vulnerability columns
    if "vuln_mean" not in segments.columns:
        print("✗ No vulnerability data found")
        return False

    print("✓ Vulnerability scores present")
    print(f"  - Mean: {segments['vuln_mean'].mean():.2f}")
    print(f"  - Range: {segments['vuln_mean'].min():.2f} - {segments['vuln_mean'].max():.2f}")

    if "vuln_class" in segments.columns:
        class_counts = segments["vuln_class"].value_counts()
        print("  - Classification:")
        for cls, count in class_counts.items():
            pct = count / len(segments) * 100
            print(f"    - {cls}: {count} ({pct:.1f}%)")

    # Check for component columns
    component_cols = {
        "Elevation": ["elevation_position_index", "elevation_mean"],
        "Slope": ["slope_mean"],
        "Soil": ["soil_drainage_score", "soil_hsg_score"],
        "Impervious": ["imperv_mean"],
        "Drainage": ["drainage_distance_m"],
    }

    print("\n  Component Data:")
    for component, cols in component_cols.items():
        present = any(col in segments.columns for col in cols)
        if present:
            found_col = next(col for col in cols if col in segments.columns)
            print(f"    ✓ {component}: {found_col}")
        else:
            print(f"    ✗ {component}: Missing")

    return True


def check_gap_analysis(segments):
    """Verify gap analysis is complete."""
    print("\n" + "="*70)
    print("6. GAP ANALYSIS")
    print("="*70)

    if segments is None:
        print("✗ Cannot check - no segments loaded")
        return False

    required_cols = ["gap_index", "quadrant"]

    if all(col in segments.columns for col in required_cols):
        print("✓ Gap analysis data present")

        if "gap_index" in segments.columns:
            high_gap = segments["gap_index"] > 0.7
            print(f"  - High gap segments: {high_gap.sum()} ({high_gap.sum()/len(segments)*100:.1f}%)")
            print(f"  - Mean gap index: {segments['gap_index'].mean():.3f}")

        if "quadrant" in segments.columns:
            quad_counts = segments["quadrant"].value_counts()
            print("  - Quadrant distribution:")
            for quad, count in quad_counts.items():
                print(f"    - {quad}: {count}")

        return True
    else:
        missing = [col for col in required_cols if col not in segments.columns]
        print(f"✗ Missing columns: {missing}")
        return False


def check_dashboard_ready():
    """Verify dashboard-ready data exists."""
    print("\n" + "="*70)
    print("7. DASHBOARD-READY DATA")
    print("="*70)

    dashboard_dir = DATA_DIR / "dashboard_ready"

    if not dashboard_dir.exists():
        print("✗ Dashboard data directory does not exist")
        print("  Run: python scripts/generate_dashboard_data.py")
        return False

    required_files = {
        "summary_statistics.json": "Pre-computed statistics",
        "data_manifest.json": "Data manifest",
        "segments_simplified.geojson": "Simplified geometries",
    }

    all_present = True
    for filename, description in required_files.items():
        path = dashboard_dir / filename
        if path.exists():
            size = path.stat().st_size
            print(f"✓ {description}: {filename} ({size:,} bytes)")
        else:
            print(f"✗ {description}: {filename} - MISSING")
            all_present = False

    return all_present


def main():
    """Run all verification checks."""
    print("="*70)
    print("COMPREHENSIVE GEOSPATIAL ANALYSIS VERIFICATION")
    print("="*70)

    # Run all checks
    segments = check_analysis_segments()
    infra = check_infrastructure()
    spatial_ok = check_spatial_statistics(segments)
    runoff_ok = check_runoff_modeling(segments)
    vuln_ok = check_vulnerability_analysis(segments)
    gap_ok = check_gap_analysis(segments)
    dashboard_ok = check_dashboard_ready()

    # Summary
    print("\n" + "="*70)
    print("VERIFICATION SUMMARY")
    print("="*70)

    checks = {
        "Analysis Segments": segments is not None,
        "Infrastructure Data": infra is not None,
        "Spatial Statistics": spatial_ok,
        "Runoff Modeling": runoff_ok,
        "Vulnerability Analysis": vuln_ok,
        "Gap Analysis": gap_ok,
        "Dashboard Ready Data": dashboard_ok,
    }

    passed = sum(checks.values())
    total = len(checks)

    print(f"\nChecks passed: {passed}/{total}")
    print()

    for check, status in checks.items():
        symbol = "✓" if status else "✗"
        print(f"{symbol} {check}")

    if passed == total:
        print("\n" + "="*70)
        print("✓✓✓ ALL ANALYSES COMPLETE! ✓✓✓")
        print("="*70)
        print("\nYour geospatial analysis is fully operational.")
        print("Dashboard is ready to display all data.")
        print("\nLaunch dashboard:")
        print("  streamlit run scripts/dashboard.py")
        return 0
    else:
        print("\n" + "="*70)
        print("⚠ INCOMPLETE ANALYSIS")
        print("="*70)

        if not dashboard_ok:
            print("\nGenerate dashboard data:")
            print("  python scripts/generate_dashboard_data.py")

        if not spatial_ok:
            print("\nCompute spatial statistics:")
            print("  python scripts/spatial_clustering.py")

        if not runoff_ok:
            print("\nCompute runoff scenarios:")
            print("  python scripts/runoff_modeling.py")

        print("\nOr run complete analysis pipeline:")
        print("  python scripts/geospatial_analysis.py")

        return 1


if __name__ == "__main__":
    exit(main())
