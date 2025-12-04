#!/usr/bin/env python3
"""
Visualization script for Geospatial Analysis Results
Generates static maps and charts from the analysis outputs.
"""
import os
import sys
import argparse
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import contextily as ctx
from pathlib import Path

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_context("paper", font_scale=1.2)

def load_results(output_dir):
    """Load analysis results from GeoPackage"""
    gpkg_path = Path(output_dir) / 'analysis_segments.gpkg'
    if not gpkg_path.exists():
        # Try shapefile fallback
        shp_path = Path(output_dir) / 'analysis_segments.shp'
        if not shp_path.exists():
            raise FileNotFoundError(f"No analysis results found in {output_dir}")
        return gpd.read_file(shp_path)
    return gpd.read_file(gpkg_path)

def plot_correlation(gdf, output_dir):
    """Generate correlation scatter plot"""
    print("Generating correlation plot...")
    
    if 'vuln_mean' not in gdf.columns or 'density_sq' not in gdf.columns:
        # Try alternative column names if truncated (shapefile limits)
        vuln_col = 'vuln_mean' if 'vuln_mean' in gdf.columns else 'vuln_score'
        dens_col = 'density_sqft_per_acre' if 'density_sqft_per_acre' in gdf.columns else 'density_sq'
    else:
        vuln_col = 'vuln_mean'
        dens_col = 'density_sq'

    plt.figure(figsize=(10, 6))
    
    # Color by quadrant if available
    if 'quadrant' in gdf.columns:
        sns.scatterplot(data=gdf, x=vuln_col, y=dens_col, hue='quadrant', alpha=0.6)
    else:
        sns.scatterplot(data=gdf, x=vuln_col, y=dens_col, alpha=0.6)
        
    plt.title('Flood Vulnerability vs. Permeable Pavement Density')
    plt.xlabel('Vulnerability Score (0-10)')
    plt.ylabel('Infrastructure Density (sq ft/acre)')
    
    # Add quadrants lines
    plt.axvline(x=gdf[vuln_col].median(), color='gray', linestyle='--', alpha=0.5)
    plt.axhline(y=gdf[dens_col].median(), color='gray', linestyle='--', alpha=0.5)
    
    plt.tight_layout()
    plt.savefig(Path(output_dir) / '../figures/charts/correlation_plot.png', dpi=300)
    plt.close()

def plot_quadrant_counts(gdf, output_dir):
    """Generate bar chart of quadrant counts"""
    print("Generating quadrant distribution chart...")
    
    if 'quadrant' not in gdf.columns:
        return

    plt.figure(figsize=(10, 6))
    sns.countplot(data=gdf, y='quadrant', order=sorted(gdf['quadrant'].unique()))
    plt.title('Distribution of Segments by Analysis Quadrant')
    plt.xlabel('Number of Segments')
    plt.ylabel('Quadrant')
    
    plt.tight_layout()
    plt.savefig(Path(output_dir) / '../figures/charts/quadrant_distribution.png', dpi=300)
    plt.close()

def plot_map(gdf, column, title, filename, output_dir, cmap='viridis'):
    """Generate static map with basemap"""
    print(f"Generating map: {title}...")
    
    # Ensure Web Mercator for Contextily
    gdf_web = gdf.to_crs(epsg=3857)
    
    fig, ax = plt.subplots(figsize=(12, 12))
    
    # Plot data
    gdf_web.plot(column=column, ax=ax, cmap=cmap, legend=True, 
                 alpha=0.7, edgecolor='none',
                 legend_kwds={'label': title, 'orientation': "horizontal"})
    
    # Add basemap
    try:
        ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron)
    except Exception as e:
        print(f"Warning: Could not fetch basemap ({e})")
    
    ax.set_axis_off()
    ax.set_title(title, fontsize=16)
    
    plt.tight_layout()
    plt.savefig(Path(output_dir) / f'../figures/maps/{filename}', dpi=300)
    plt.close()

def main():
    parser = argparse.ArgumentParser(description='Visualize analysis results')
    parser.add_argument('--output-dir', default='data/outputs_final', help='Directory containing analysis results')
    args = parser.parse_args()
    
    # Ensure figure directories exist
    (Path(args.output_dir) / '../figures/maps').mkdir(parents=True, exist_ok=True)
    (Path(args.output_dir) / '../figures/charts').mkdir(parents=True, exist_ok=True)
    
    try:
        gdf = load_results(args.output_dir)
        print(f"Loaded {len(gdf)} segments.")
        
        # Generate Charts
        plot_correlation(gdf, args.output_dir)
        plot_quadrant_counts(gdf, args.output_dir)
        
        # Generate Maps
        # 1. Vulnerability Map
        vuln_col = 'vuln_mean' if 'vuln_mean' in gdf.columns else 'vuln_score'
        plot_map(gdf, vuln_col, 'Flood Vulnerability Score', 'vulnerability_map.png', args.output_dir, cmap='RdYlBu_r')
        
        # 2. Gap Index Map (Priority Areas)
        if 'gap_index' in gdf.columns:
            plot_map(gdf, 'gap_index', 'Infrastructure Gap Index (Priority Areas)', 'gap_index_map.png', args.output_dir, cmap='Reds')
            
        print("\nVisualization complete!")
        print(f"Maps saved to: {Path(args.output_dir) / '../figures/maps'}")
        print(f"Charts saved to: {Path(args.output_dir) / '../figures/charts'}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
