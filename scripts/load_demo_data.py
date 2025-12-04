#!/usr/bin/env python3
"""
Load and prepare demo data for dashboard display.

This script ensures the dashboard can display valuable analysis even if
complete data isn't available, by preparing a subset of data optimized
for visualization.

Usage:
    python load_demo_data.py
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional
import warnings

import geopandas as gpd
import pandas as pd
import numpy as np

warnings.filterwarnings('ignore')

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"


def load_and_prepare_segments() -> Optional[gpd.GeoDataFrame]:
    """Load analysis segments and prepare for dashboard display."""

    candidates = [
        DATA_DIR / "outputs_final" / "analysis_segments.gpkg",
        DATA_DIR / "outputs" / "analysis_segments.gpkg",
        DATA_DIR / "outputs_final" / "analysis_segments.shp",
    ]

    for path in candidates:
        if path.exists():
            print(f"Loading segments from: {path}")
            try:
                gdf = gpd.read_file(path)
                print(f"✓ Loaded {len(gdf)} segments")

                # Ensure required columns exist
                required_cols = [
                    'segment_id', 'vuln_mean', 'facility_count',
                    'density_sqft_per_acre', 'geometry'
                ]

                missing_cols = [col for col in required_cols if col not in gdf.columns]
                if missing_cols:
                    print(f"⚠ Missing columns: {missing_cols}")
                    # Add default values for missing columns
                    for col in missing_cols:
                        if col == 'segment_id':
                            gdf['segment_id'] = range(1, len(gdf) + 1)
                        elif col in ['facility_count', 'density_sqft_per_acre']:
                            gdf[col] = 0
                        elif col == 'vuln_mean':
                            gdf[col] = 5.0

                # Ensure geometry is in WGS84 for web mapping
                if gdf.crs != "EPSG:4326":
                    print("Converting to WGS84...")
                    gdf = gdf.to_crs(4326)

                # Calculate buffer areas if missing
                if 'buffer_area_acres' not in gdf.columns:
                    print("Calculating buffer areas...")
                    proj = gdf.to_crs(2927)
                    gdf['buffer_area_acres'] = proj.geometry.area / 43560.0
                    gdf['buffer_area_sqft'] = proj.geometry.area
                    gdf['length_miles'] = proj.geometry.length / 5280.0

                # Ensure jurisdiction column exists
                if 'jurisdiction' not in gdf.columns:
                    gdf['jurisdiction'] = 'Unknown'

                # Calculate vulnerability classification if missing
                if 'vuln_class' not in gdf.columns and 'vuln_mean' in gdf.columns:
                    gdf['vuln_class'] = pd.cut(
                        gdf['vuln_mean'],
                        bins=[0, 4, 7, 10],
                        labels=['Low', 'Moderate', 'High']
                    )

                # Calculate gap index if missing
                if 'gap_index' not in gdf.columns:
                    if 'vuln_mean' in gdf.columns and 'density_sqft_per_acre' in gdf.columns:
                        # High vulnerability, low infrastructure = high gap
                        vuln_norm = (gdf['vuln_mean'] - gdf['vuln_mean'].min()) / (
                            gdf['vuln_mean'].max() - gdf['vuln_mean'].min()
                        )
                        density_norm = (gdf['density_sqft_per_acre'] - gdf['density_sqft_per_acre'].min()) / (
                            gdf['density_sqft_per_acre'].max() - gdf['density_sqft_per_acre'].min()
                        )
                        gdf['gap_index'] = vuln_norm * (1 - density_norm)

                # Calculate priority gap flag
                if 'priority_gap' not in gdf.columns:
                    gdf['priority_gap'] = (
                        (gdf.get('vuln_mean', 0) > 7.0) &
                        (gdf.get('density_sqft_per_acre', 0) < 100.0)
                    )

                # Ensure weighted vulnerability exists
                if 'vuln_weighted' not in gdf.columns and 'vuln_mean' in gdf.columns:
                    gdf['vuln_weighted'] = gdf['vuln_mean']

                print("✓ Data preparation complete")
                return gdf

            except Exception as e:
                print(f"✗ Error loading {path}: {e}")

    print("✗ No analysis segments found")
    return None


def verify_data_completeness(gdf: gpd.GeoDataFrame) -> dict:
    """Check which analysis features are available."""

    features = {
        "basic_analysis": False,
        "infrastructure_density": False,
        "spatial_statistics": False,
        "runoff_modeling": False,
        "temporal_analysis": False,
    }

    # Basic analysis
    if all(col in gdf.columns for col in ['vuln_mean', 'segment_id']):
        features["basic_analysis"] = True

    # Infrastructure density
    if 'density_sqft_per_acre' in gdf.columns and 'facility_count' in gdf.columns:
        features["infrastructure_density"] = True

    # Spatial statistics
    if any(col in gdf.columns for col in ['lisa_cluster', 'hotspot_class', 'gi_star']):
        features["spatial_statistics"] = True

    # Runoff modeling
    runoff_cols = [col for col in gdf.columns if 'runoff' in col.lower() or 'cn_' in col.lower()]
    if runoff_cols:
        features["runoff_modeling"] = True

    # Temporal analysis
    if 'installation_date' in gdf.columns or 'temporal_period' in gdf.columns:
        features["temporal_analysis"] = True

    return features


def main():
    """Load and verify demo data."""

    print("="*70)
    print("Demo Data Loader")
    print("="*70)
    print()

    segments = load_and_prepare_segments()

    if segments is None:
        print("\n✗ ERROR: No data files found!")
        print("\nAvailable data locations checked:")
        candidates = [
            DATA_DIR / "outputs_final" / "analysis_segments.gpkg",
            DATA_DIR / "outputs" / "analysis_segments.gpkg",
            DATA_DIR / "outputs_final" / "analysis_segments.shp",
        ]
        for path in candidates:
            exists = "✓" if path.exists() else "✗"
            print(f"  {exists} {path}")

        print("\nTo generate analysis segments, run:")
        print("  python scripts/geospatial_analysis.py")
        return 1

    # Verify features
    print("\n" + "="*70)
    print("Feature Availability")
    print("="*70)

    features = verify_data_completeness(segments)

    for feature, available in features.items():
        status = "✓" if available else "✗"
        print(f"{status} {feature.replace('_', ' ').title()}")

    # Print column summary
    print("\n" + "="*70)
    print("Data Columns")
    print("="*70)

    key_columns = {
        "Vulnerability": ['vuln_mean', 'vuln_class', 'vuln_weighted'],
        "Infrastructure": ['facility_count', 'density_sqft_per_acre', 'total_area_sqft'],
        "Spatial Stats": ['lisa_cluster', 'hotspot_class', 'gi_star'],
        "Runoff": ['cn_current', 'runoff_current_25-year', 'volume_current_25-year_acft'],
        "Temporal": ['installation_date', 'temporal_period', 'installation_year'],
    }

    for category, cols in key_columns.items():
        available = [col for col in cols if col in segments.columns]
        if available:
            print(f"\n{category}:")
            for col in available:
                print(f"  ✓ {col}")

    # Print summary statistics
    print("\n" + "="*70)
    print("Summary Statistics")
    print("="*70)

    print(f"\nSegments: {len(segments):,}")

    if 'vuln_mean' in segments.columns:
        print(f"Mean Vulnerability: {segments['vuln_mean'].mean():.2f}")
        print(f"High Vulnerability (>7.0): {(segments['vuln_mean'] > 7.0).sum():,} ({(segments['vuln_mean'] > 7.0).sum() / len(segments) * 100:.1f}%)")

    if 'facility_count' in segments.columns:
        print(f"Segments with Infrastructure: {(segments['facility_count'] > 0).sum():,} ({(segments['facility_count'] > 0).sum() / len(segments) * 100:.1f}%)")

    if 'density_sqft_per_acre' in segments.columns:
        print(f"Mean Infrastructure Density: {segments['density_sqft_per_acre'].mean():.1f} sq ft/acre")

    if 'buffer_area_acres' in segments.columns:
        print(f"Total Corridor Area: {segments['buffer_area_acres'].sum():.1f} acres")

    if 'length_miles' in segments.columns:
        print(f"Total Corridor Length: {segments['length_miles'].sum():.1f} miles")

    print("\n✓ Data is ready for dashboard display!")
    print("\nLaunch dashboard with:")
    print("  streamlit run scripts/dashboard.py")

    return 0


if __name__ == "__main__":
    exit(main())
