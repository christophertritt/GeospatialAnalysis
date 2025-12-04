#!/usr/bin/env python3
"""
Main geospatial analysis tool for rail corridor flood vulnerability and infrastructure assessment

This tool implements the comprehensive methodology from the COMPLETE_METHODOLOGY_GUIDE.txt
for analyzing spatial alignment of permeable pavement and flood vulnerability.
"""
import os
import sys
import argparse
import geopandas as gpd
import pandas as pd
import numpy as np
from pathlib import Path
import json
import logging

try:
    import yaml
except ImportError:
    yaml = None

# Support both direct execution and package import
try:
    from .utils import (
        validate_spatial_data,
        reproject_to_standard,
        create_buffers,
        calculate_infrastructure_density,
        correlation_analysis,
        classify_vulnerability,
        assign_quadrant,
        calculate_gap_index
    )
    from .spatial_clustering import perform_spatial_clustering_analysis
    from .runoff_modeling import perform_runoff_modeling
    SPATIAL_CLUSTERING_AVAILABLE = True
    RUNOFF_MODELING_AVAILABLE = True
except ImportError:
    # Fallback for direct script execution
    sys.path.insert(0, os.path.dirname(__file__))
    from utils import (
        validate_spatial_data,
        reproject_to_standard,
        create_buffers,
        calculate_infrastructure_density,
        correlation_analysis,
        classify_vulnerability,
        assign_quadrant,
        calculate_gap_index
    )
    try:
        from spatial_clustering import perform_spatial_clustering_analysis
        SPATIAL_CLUSTERING_AVAILABLE = True
    except ImportError:
        SPATIAL_CLUSTERING_AVAILABLE = False
    
    try:
        from runoff_modeling import perform_runoff_modeling
        RUNOFF_MODELING_AVAILABLE = True
    except ImportError:
        RUNOFF_MODELING_AVAILABLE = False


# Standard coordinate reference system for Washington State
# EPSG:2927 - NAD83(2011) / Washington State Plane South
# Units: US Survey Feet
TARGET_CRS = 2927


class GeospatialAnalysisTool:
    """Main analysis tool for rail corridor geospatial analysis"""
    
    def __init__(self, data_dir='data', output_dir='data/outputs', config_path=None):
        """
        Initialize the analysis tool
        
        Args:
            data_dir: Base directory for data files
            output_dir: Directory for output files
        """
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load config if provided
        self.config = {}
        if config_path and Path(config_path).exists() and yaml:
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f) or {}
        elif config_path and not yaml:
            print("Warning: pyyaml not installed; ignoring config file.")

        # Standard CRS
        self.target_crs = int(self.config.get('crs', TARGET_CRS))
        
        # Buffer distances
        self.buffer_distances = list(self.config.get('buffers_m', [100, 250, 500]))
        
        # Analysis results storage
        self.segments = None
        self.infrastructure = None
        self.results = {}
    
    def load_data(self, rail_path=None, infrastructure_path=None):
        """
        Load and validate spatial data

        Args:
            rail_path: Path to rail corridor shapefile (REQUIRED)
            infrastructure_path: Path to infrastructure shapefile (REQUIRED)

        Raises:
            ValueError: If required data files are not provided
        """
        print("\n" + "="*70)
        print("PHASE 1: DATA LOADING AND VALIDATION")
        print("="*70)

        # Load rail data - REQUIRED
        if not rail_path or not os.path.exists(rail_path):
            raise ValueError(
                f"Rail corridor data is required. Provided path: {rail_path}\n"
                "Please provide a valid rail corridor shapefile.\n"
                "You can obtain this from:\n"
                "  - WSDOT GeoData Portal: https://gisdata-wsdot.opendata.arcgis.com/\n"
                "  - Local transit agencies\n"
                "  - OpenStreetMap (railway=rail)"
            )

        print(f"\nLoading rail data from: {rail_path}")
        rail = gpd.read_file(rail_path)
        rail = validate_spatial_data(rail, "Rail Corridor")
        rail = reproject_to_standard(rail, self.target_crs)

        # Create buffers
        print("\nCreating corridor buffers...")
        buffers = create_buffers(rail, self.buffer_distances)

        # Use 250m buffer as default analysis unit
        self.segments = buffers['250m'].copy()
        self.segments['segment_id'] = range(1, len(self.segments) + 1)

        print(f"Created analysis segments: {len(self.segments)}")

        # Load infrastructure data - REQUIRED
        if not infrastructure_path or not os.path.exists(infrastructure_path):
            raise ValueError(
                f"Infrastructure data is required. Provided path: {infrastructure_path}\n"
                "Please provide a valid infrastructure shapefile.\n"
                "You can obtain this from:\n"
                "  - Seattle Open Data: https://data.seattle.gov/\n"
                "  - Local stormwater/public works departments\n"
                "  - Manual mapping of green infrastructure facilities"
            )

        print(f"\nLoading infrastructure data from: {infrastructure_path}")
        infra = gpd.read_file(infrastructure_path)
        infra = validate_spatial_data(infra, "Infrastructure")
        self.infrastructure = reproject_to_standard(infra, self.target_crs)
    
    
    def calculate_vulnerability(self, imperviousness_raster=None, dem_path=None, soils_path=None):
        """
        Calculate vulnerability index for segments from real data sources

        Args:
            imperviousness_raster: Path to NLCD imperviousness raster
            dem_path: Path to DEM/elevation raster for slope calculation
            soils_path: Path to SSURGO soils shapefile

        Note: If raster data is not provided, vulnerability cannot be calculated.
              Use data_acquisition.py to fetch required datasets.
        """
        print("\n" + "="*70)
        print("PHASE 2: VULNERABILITY INDEX CALCULATION")
        print("="*70)

        if self.segments is None:
            raise ValueError("No segments loaded. Run load_data() first.")

        n_segments = len(self.segments)

        # Extract imperviousness from NLCD raster
        if imperviousness_raster and os.path.exists(imperviousness_raster):
            print(f"\nExtracting imperviousness from: {imperviousness_raster}")
            try:
                import rasterio
                from rasterstats import zonal_stats
                
                # Check raster CRS and reproject segments if needed
                with rasterio.open(imperviousness_raster) as src:
                    raster_crs = src.crs
                    print(f"  Raster CRS: {raster_crs}")
                
                # Reproject segments to match raster CRS for zonal stats
                segments_proj = self.segments.to_crs(raster_crs)
                
                stats = zonal_stats(
                    segments_proj,
                    imperviousness_raster,
                    stats=['mean', 'median'],
                    nodata=-9999
                )
                imperviousness = np.array([s['mean'] if s['mean'] is not None else 0 for s in stats])
                print(f"  Extracted imperviousness for {n_segments} segments")
            except Exception as e:
                raise ValueError(f"Failed to extract imperviousness: {e}\n"
                               "Install rasterstats: pip install rasterstats")
        else:
            raise ValueError(
                "Imperviousness raster is required for vulnerability calculation.\n"
                f"Provided path: {imperviousness_raster}\n"
                "Download NLCD imperviousness from: https://www.mrlc.gov/viewer/\n"
                "Place file in: data/raw/landcover/"
            )

        # Extract slope from DEM
        if dem_path and os.path.exists(dem_path):
            print(f"\nExtracting slope from DEM: {dem_path}")
            try:
                import rasterio
                from rasterstats import zonal_stats

                # Check raster CRS and reproject segments if needed
                with rasterio.open(dem_path) as src:
                    dem_crs = src.crs
                    print(f"  DEM CRS: {dem_crs}")
                
                # Reproject segments to match DEM CRS for zonal stats
                segments_dem = self.segments.to_crs(dem_crs)

                # Read DEM into memory to avoid VRT/IO segfaults with rasterstats
                dem_array = src.read(1)
                dem_transform = src.transform
                dem_nodata = src.nodata

                # Calculate slope from DEM (would need richdem or gdal)
                # For now, extract elevation and approximate slope
                stats = zonal_stats(
                    segments_dem,
                    dem_array,
                    affine=dem_transform,
                    nodata=dem_nodata,
                    stats=['mean', 'std']
                )
                # Approximate slope from elevation std dev
                slope = np.array([s['std']/10 if s['std'] is not None else 2.0 for s in stats])
                print(f"  Extracted slope approximation for {n_segments} segments")
            except Exception as e:
                print(f"  Warning: Failed to extract slope: {e}")
                print("  Using default slope values")
                slope = np.full(n_segments, 2.0)  # Default moderate slope
        else:
            print("\nWarning: No DEM provided. Using default slope values.")
            print("Download elevation data from: https://apps.nationalmap.gov/")
            slope = np.full(n_segments, 2.0)  # Default moderate slope
        
        # Calculate component scores (0-2 scale)
        # Imperviousness: >75% = 2, 60-75% = 1.5, 45-60% = 1, <45% = 0
        imperv_vuln = np.where(imperviousness > 75, 2.0,
                              np.where(imperviousness > 60, 1.5,
                                      np.where(imperviousness > 45, 1.0, 0.0)))
        
        # Slope: <2% = 2, 2-5% = 1.5, 5-10% = 1, >10% = 0
        slope_vuln = np.where(slope < 2, 2.0,
                             np.where(slope < 5, 1.5,
                                     np.where(slope < 10, 1.0, 0.0)))
        
        # Process soils data
        if soils_path and os.path.exists(soils_path):
            print(f"\nProcessing soils data from: {soils_path}")
            try:
                soils = gpd.read_file(soils_path)
                if soils.crs != self.segments.crs:
                    print(f"  Reprojecting soils from {soils.crs} to {self.segments.crs}")
                    soils = soils.to_crs(self.segments.crs)
                
                # Spatial join to get dominant soil type per segment
                joined = gpd.sjoin(self.segments, soils, how='left', predicate='intersects')
                # Extract hydrologic group (assuming column name 'hydgrpdcd' or 'HYDGRP')
                hydgrp_col = 'hydgrpdcd' if 'hydgrpdcd' in joined.columns else 'HYDGRP' if 'HYDGRP' in joined.columns else None
                if hydgrp_col:
                    # Get most common soil type per segment
                    soil_by_segment = joined.groupby('segment_id')[hydgrp_col].agg(lambda x: x.mode()[0] if len(x) > 0 else 'C')
                    print(f"  Processed soil data for {len(soil_by_segment)} segments")
                else:
                    print("  Warning: Could not find soil hydrologic group column. Using default 'C'")
                    soil_by_segment = pd.Series(['C'] * n_segments, index=range(1, n_segments+1))
            except Exception as e:
                print(f"  Warning: Failed to process soils: {e}")
                print("  Using default soil type 'C'")
                soil_by_segment = pd.Series(['C'] * n_segments, index=range(1, n_segments+1))
        else:
            print("\nWarning: No soils data provided. Using default soil type 'C'")
            print("Download soils data using: python scripts/data_acquisition.py")
            soil_by_segment = pd.Series(['C'] * n_segments, index=range(1, n_segments+1))

        # Soil vulnerability scores: D=2, C=1.5, B=1, A=0
        soil_scores = {'D': 2.0, 'C': 1.5, 'B': 1.0, 'A': 0.0}
        soil_vuln = np.array([soil_scores.get(str(s).upper()[0] if str(s) else 'C', 1.5)
                             for s in soil_by_segment])

        # Composite vulnerability (weighted average of components)
        weights = {
            'imperv': 0.40,
            'slope': 0.30,
            'soil': 0.30
        }

        # No random/synthetic data - use actual extracted values
        
        vuln_composite = (
            weights['imperv'] * imperv_vuln +
            weights['slope'] * slope_vuln +
            weights['soil'] * soil_vuln
        )
        
        # Normalize to 0-10 scale
        self.segments['imperv_mean'] = imperviousness
        self.segments['slope_mean'] = slope
        self.segments['vuln_mean'] = vuln_composite * 5  # Scale 0-2 range to 0-10
        self.segments['vuln_class'] = self.segments['vuln_mean'].apply(classify_vulnerability)
        
        print(f"\nVulnerability Statistics:")
        print(f"  Mean: {self.segments['vuln_mean'].mean():.2f}")
        print(f"  Std Dev: {self.segments['vuln_mean'].std():.2f}")
        print(f"  Range: {self.segments['vuln_mean'].min():.2f} - {self.segments['vuln_mean'].max():.2f}")
        print(f"\nVulnerability Classification:")
        print(self.segments['vuln_class'].value_counts())
    
    def analyze_context(self, flood_zones_path=None, svi_path=None, canopy_raster=None, zoning_path=None):
        """
        Analyze additional context layers (Flood Zones, SVI, Canopy, Zoning)
        
        Args:
            flood_zones_path: Path to FEMA NFHL shapefile
            svi_path: Path to CDC SVI shapefile
            canopy_raster: Path to NLCD Tree Canopy raster
            zoning_path: Path to Zoning shapefile
        """
        print("\n" + "="*70)
        print("PHASE 2.5: CONTEXTUAL ANALYSIS")
        print("="*70)
        
        if self.segments is None:
            print("Error: No segments loaded.")
            return

        # 1. FEMA Flood Zones
        if flood_zones_path and os.path.exists(flood_zones_path):
            print(f"\nProcessing Flood Zones: {flood_zones_path}")
            try:
                flood = gpd.read_file(flood_zones_path)
                if flood.crs != self.segments.crs:
                    flood = flood.to_crs(self.segments.crs)
                
                # Filter for high risk zones (A, AE, V, VE)
                high_risk = flood[flood['FLD_ZONE'].isin(['A', 'AE', 'V', 'VE'])]
                
                # Spatial join to flag segments
                # Using 'intersects' to see if any part of segment touches flood zone
                joined = gpd.sjoin(self.segments, high_risk, how='left', predicate='intersects')
                
                # Create binary flag
                self.segments['in_flood_zone'] = self.segments.index.isin(joined.index).astype(int)
                print(f"  Segments in high-risk flood zones: {self.segments['in_flood_zone'].sum()}")
                
            except Exception as e:
                print(f"  Warning: Failed to process flood zones: {e}")
        
        # 2. Social Vulnerability Index (SVI)
        if svi_path and os.path.exists(svi_path):
            print(f"\nProcessing SVI Data: {svi_path}")
            try:
                svi = gpd.read_file(svi_path)
                if svi.crs != self.segments.crs:
                    svi = svi.to_crs(self.segments.crs)
                
                # Spatial join (centroid of segment to SVI polygon)
                # Use centroids to avoid one segment matching multiple tracts
                centroids = self.segments.copy()
                centroids.geometry = centroids.geometry.centroid
                
                joined = gpd.sjoin(centroids, svi, how='left', predicate='within')
                
                # Extract RPL_THEMES (Overall SVI)
                # Map back to segments using index
                if 'RPL_THEMES' in joined.columns:
                    self.segments['svi_score'] = joined['RPL_THEMES']
                    print(f"  SVI scores assigned. Mean: {self.segments['svi_score'].mean():.2f}")
                else:
                    print("  Warning: 'RPL_THEMES' column not found in SVI data")
                    
            except Exception as e:
                print(f"  Warning: Failed to process SVI: {e}")

        # 3. Tree Canopy
        if canopy_raster and os.path.exists(canopy_raster):
            print(f"\nExtracting Tree Canopy: {canopy_raster}")
            try:
                import rasterio
                from rasterstats import zonal_stats
                
                with rasterio.open(canopy_raster) as src:
                    raster_crs = src.crs
                
                segments_proj = self.segments.to_crs(raster_crs)
                
                stats = zonal_stats(
                    segments_proj,
                    canopy_raster,
                    stats=['mean'],
                    nodata=255  # NLCD nodata is often 255
                )
                self.segments['canopy_mean'] = [s['mean'] if s['mean'] is not None else 0 for s in stats]
                print(f"  Mean canopy cover: {self.segments['canopy_mean'].mean():.1f}%")
                
            except Exception as e:
                print(f"  Warning: Failed to extract canopy: {e}")

        # 4. Zoning
        if zoning_path and os.path.exists(zoning_path):
            print(f"\nProcessing Zoning: {zoning_path}")
            try:
                zoning = gpd.read_file(zoning_path)
                if zoning.crs != self.segments.crs:
                    zoning = zoning.to_crs(self.segments.crs)
                
                # Spatial join (largest overlap)
                # For simplicity, use centroid
                centroids = self.segments.copy()
                centroids.geometry = centroids.geometry.centroid
                
                joined = gpd.sjoin(centroids, zoning, how='left', predicate='within')
                
                # Extract zoning code (adjust column name as needed, e.g., 'ZONE_CODE', 'CLASS')
                # Looking for common names
                zone_col = next((col for col in ['ZONE_CODE', 'CLASS', 'ZONING', 'ZONE'] if col in joined.columns), None)
                
                if zone_col:
                    self.segments['zoning_code'] = joined[zone_col]
                    print(f"  Zoning assigned. Categories: {self.segments['zoning_code'].nunique()}")
                else:
                    print("  Warning: Could not identify zoning code column")
                    
            except Exception as e:
                print(f"  Warning: Failed to process zoning: {e}")

    def analyze_infrastructure_density(self):
        """Analyze infrastructure density per segment"""
        print("\n" + "="*70)
        print("PHASE 3: INFRASTRUCTURE DENSITY ANALYSIS")
        print("="*70)

        if self.segments is None:
            raise ValueError("No segments loaded. Run load_data() first.")

        if self.infrastructure is None:
            raise ValueError(
                "Infrastructure data is required for density analysis.\n"
                "Infrastructure data should have been loaded in load_data()."
            )
        
        # Calculate density
        self.segments = calculate_infrastructure_density(
            self.segments, 
            self.infrastructure
        )
        
        print(f"\nInfrastructure Density Statistics:")
        print(f"  Mean: {self.segments['density_sqft_per_acre'].mean():.1f} sq ft/acre")
        print(f"  Median: {self.segments['density_sqft_per_acre'].median():.1f} sq ft/acre")
        print(f"  Range: {self.segments['density_sqft_per_acre'].min():.1f} - "
              f"{self.segments['density_sqft_per_acre'].max():.1f} sq ft/acre")
        print(f"  Segments with zero infrastructure: "
              f"{(self.segments['facility_count'] == 0).sum()}")
    
    def assess_alignment(self):
        """Assess alignment between vulnerability and infrastructure"""
        print("\n" + "="*70)
        print("PHASE 4: ALIGNMENT ASSESSMENT")
        print("="*70)
        
        if self.segments is None or 'vuln_mean' not in self.segments.columns:
            print("Error: Run vulnerability calculation first.")
            return
        
        if 'density_sqft_per_acre' not in self.segments.columns:
            print("Error: Run infrastructure density analysis first.")
            return
        
        # Correlation analysis
        result = correlation_analysis(
            self.segments['vuln_mean'],
            self.segments['density_sqft_per_acre'],
            method='pearson'
        )
        
        print(f"\nPearson Correlation Analysis:")
        print(f"  r = {result['r']:.3f}")
        print(f"  p-value = {result['p_value']:.4f}")
        print(f"  n = {result['n']}")
        
        if result['p_value'] < 0.05:
            if result['r'] < 0:
                print("  ⚠ Significant INVERSE correlation: High vulnerability areas have LOWER infrastructure density")
            else:
                print("  ✓ Significant POSITIVE correlation: High vulnerability areas have HIGHER infrastructure density")
        else:
            print("  No significant correlation detected")
        
        # Quadrant classification
        vuln_median = self.segments['vuln_mean'].median()
        density_median = self.segments['density_sqft_per_acre'].median()
        
        self.segments['quadrant'] = self.segments.apply(
            lambda row: assign_quadrant(
                row['vuln_mean'],
                row['density_sqft_per_acre'],
                vuln_median,
                density_median
            ),
            axis=1
        )
        
        print(f"\nQuadrant Classification:")
        quadrant_counts = self.segments['quadrant'].value_counts()
        for quadrant, count in quadrant_counts.items():
            print(f"  {quadrant}: {count}")
        
        # Gap index
        self.segments['gap_index'] = self.segments.apply(
            lambda row: calculate_gap_index(
                row['vuln_mean'],
                row['density_sqft_per_acre']
            ),
            axis=1
        )
        
        print(f"\nGap Index Statistics:")
        print(f"  Mean: {self.segments['gap_index'].mean():.2f}")
        print(f"  Std Dev: {self.segments['gap_index'].std():.2f}")
        print(f"  Segments with gap > 5: {(self.segments['gap_index'] > 5).sum()}")
        
        # Store results
        self.results['alignment'] = {
            'correlation_r': result['r'],
            'correlation_p': result['p_value'],
            'vuln_median': vuln_median,
            'density_median': density_median
        }
    
    def generate_report(self, output_file=None):
        """Generate summary report"""
        print("\n" + "="*70)
        print("GENERATING SUMMARY REPORT")
        print("="*70)
        
        if output_file is None:
            output_file = self.output_dir / 'analysis_summary.txt'
        
        with open(output_file, 'w') as f:
            f.write("="*70 + "\n")
            f.write("GEOSPATIAL ANALYSIS SUMMARY REPORT\n")
            f.write("Rail Corridor Flood Vulnerability and Infrastructure Assessment\n")
            f.write("="*70 + "\n\n")
            
            if self.segments is not None:
                f.write("STUDY AREA\n")
                f.write("-"*70 + "\n")
                f.write(f"Number of segments: {len(self.segments)}\n")
                f.write(f"Total area: {self.segments['buffer_area_acres'].sum():.0f} acres\n")
                f.write(f"CRS: EPSG:{self.target_crs}\n\n")
                
                if 'vuln_mean' in self.segments.columns:
                    f.write("VULNERABILITY ASSESSMENT\n")
                    f.write("-"*70 + "\n")
                    f.write(f"Mean vulnerability: {self.segments['vuln_mean'].mean():.2f}\n")
                    f.write(f"Std dev: {self.segments['vuln_mean'].std():.2f}\n")
                    f.write(f"Range: {self.segments['vuln_mean'].min():.2f} - {self.segments['vuln_mean'].max():.2f}\n")
                    f.write("\nClassification:\n")
                    for cls, count in self.segments['vuln_class'].value_counts().items():
                        f.write(f"  {cls}: {count}\n")
                    f.write("\n")
                
                if 'density_sqft_per_acre' in self.segments.columns:
                    f.write("INFRASTRUCTURE DENSITY\n")
                    f.write("-"*70 + "\n")
                    f.write(f"Mean density: {self.segments['density_sqft_per_acre'].mean():.1f} sq ft/acre\n")
                    f.write(f"Median density: {self.segments['density_sqft_per_acre'].median():.1f} sq ft/acre\n")
                    f.write(f"Range: {self.segments['density_sqft_per_acre'].min():.1f} - "
                           f"{self.segments['density_sqft_per_acre'].max():.1f} sq ft/acre\n")
                    f.write(f"Segments with zero infrastructure: {(self.segments['facility_count'] == 0).sum()}\n\n")
                
                if 'alignment' in self.results:
                    f.write("ALIGNMENT ANALYSIS\n")
                    f.write("-"*70 + "\n")
                    align = self.results['alignment']
                    f.write(f"Correlation (r): {align['correlation_r']:.3f}\n")
                    f.write(f"P-value: {align['correlation_p']:.4f}\n")
                    
                    if 'quadrant' in self.segments.columns:
                        f.write("\nQuadrant Distribution:\n")
                        for quad, count in self.segments['quadrant'].value_counts().items():
                            f.write(f"  {quad}: {count}\n")
                    
                    if 'gap_index' in self.segments.columns:
                        f.write(f"\nMean gap index: {self.segments['gap_index'].mean():.2f}\n")
                        f.write(f"High gap segments (>5): {(self.segments['gap_index'] > 5).sum()}\n")
        
        print(f"\nReport saved to: {output_file}")
        # Also emit a JSON summary
        summary_json = self.output_dir / 'analysis_summary.json'
        try:
            summary = {
                'n_segments': int(len(self.segments)) if self.segments is not None else 0,
                'crs': f"EPSG:{self.target_crs}",
                'results': self.results,
            }
            with open(summary_json, 'w') as jf:
                json.dump(summary, jf, indent=2)
            print(f"JSON summary saved to: {summary_json}")
        except Exception as e:
            print(f"Warning: Failed to write JSON summary ({e}).")
    
    def save_results(self):
        """Save analysis results to files"""
        print("\n" + "="*70)
        print("SAVING RESULTS")
        print("="*70)
        
        if self.segments is not None:
            # Save segments to GeoPackage (preferred)
            fmt = (self.config.get('output', {}) or {}).get('format', 'gpkg')
            gpkg_path = self.output_dir / 'analysis_segments.gpkg'
            try:
                if fmt == 'gpkg':
                    layer = (self.config.get('output', {}) or {}).get('segments_layer', 'segments')
                    self.segments.to_file(gpkg_path, driver='GPKG', layer=layer)
                else:
                    raise Exception('Non-GPKG requested')
                print(f"Segments saved to: {gpkg_path}")
            except Exception as e:
                print(f"Warning: Failed to write GeoPackage ({e}). Writing Shapefile instead.")
                shp_path = self.output_dir / 'analysis_segments.shp'
                self.segments.to_file(shp_path)
                print(f"Segments saved to: {shp_path}")
            
            # Save CSV summary
            csv_path = self.output_dir / 'analysis_segments.csv'
            # Drop geometry for CSV
            df = pd.DataFrame(self.segments.drop(columns='geometry'))
            df.to_csv(csv_path, index=False)
            print(f"CSV summary saved to: {csv_path}")
        
        # Save infrastructure if available
        if self.infrastructure is not None:
            infra_gpkg = self.output_dir / 'infrastructure_processed.gpkg'
            try:
                if fmt == 'gpkg':
                    layer = (self.config.get('output', {}) or {}).get('infrastructure_layer', 'infrastructure')
                    self.infrastructure.to_file(infra_gpkg, driver='GPKG', layer=layer)
                else:
                    raise Exception('Non-GPKG requested')
                print(f"Infrastructure saved to: {infra_gpkg}")
            except Exception as e:
                print(f"Warning: Failed to write GeoPackage ({e}). Writing Shapefile instead.")
                infra_shp = self.output_dir / 'infrastructure_processed.shp'
                self.infrastructure.to_file(infra_shp)
                print(f"Infrastructure saved to: {infra_shp}")


def main():
    """Main entry point for CLI"""
    parser = argparse.ArgumentParser(
        description='Geospatial analysis tool for rail corridor flood vulnerability assessment',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Required Data Files:
  All data files must be downloaded before running analysis.
  Use download_data.py to fetch external datasets.

  Required:
    - Rail corridor shapefile (--rail)
    - Infrastructure/permeable pavement shapefile (--infrastructure)
    - NLCD imperviousness raster (--imperviousness)

  Optional but recommended:
    - Digital Elevation Model (--dem)
    - SSURGO soils shapefile (--soils)

Example Usage:
  python scripts/geospatial_analysis.py \\
    --rail data/raw/rail/corridor.shp \\
    --infrastructure data/raw/infrastructure/permeable_pavement.shp \\
    --imperviousness data/raw/landcover/nlcd_2019_impervious_aoi.tif \\
    --dem data/raw/elevation/dem_aoi.tif \\
    --soils data/processed/soils/ssurgo_aoi.gpkg \\
    --config config.yaml \\
    --verbose
        """
    )
    parser.add_argument(
        '--rail',
        required=True,
        help='Path to rail corridor shapefile (REQUIRED)'
    )
    parser.add_argument(
        '--infrastructure',
        required=True,
        help='Path to infrastructure shapefile (REQUIRED)'
    )
    parser.add_argument(
        '--imperviousness',
        required=True,
        help='Path to NLCD imperviousness raster (REQUIRED)'
    )
    parser.add_argument(
        '--dem',
        help='Path to Digital Elevation Model raster (optional)'
    )
    parser.add_argument(
        '--soils',
        help='Path to SSURGO soils shapefile (optional)'
    )
    parser.add_argument(
        '--flood-zones',
        help='Path to FEMA NFHL shapefile (optional)'
    )
    parser.add_argument(
        '--svi',
        help='Path to CDC SVI shapefile (optional)'
    )
    parser.add_argument(
        '--canopy',
        help='Path to NLCD Tree Canopy raster (optional)'
    )
    parser.add_argument(
        '--zoning',
        help='Path to Zoning shapefile (optional)'
    )
    parser.add_argument(
        '--data-dir',
        help='Base data directory',
        default='data'
    )
    parser.add_argument(
        '--output-dir',
        help='Output directory',
        default='data/outputs'
    )
    parser.add_argument(
        '--config',
        help='Path to YAML configuration file',
        default='config.yaml'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='[%(levelname)s] %(message)s'
    )

    # Validate required files exist
    required_files = {
        'Rail corridor': args.rail,
        'Infrastructure': args.infrastructure,
        'Imperviousness': args.imperviousness
    }

    print("\n" + "="*70)
    print("GEOSPATIAL ANALYSIS TOOL")
    print("Rail Corridor Flood Vulnerability and Infrastructure Assessment")
    print("="*70)

    print("\nValidating required data files...")
    missing_files = []
    for name, path in required_files.items():
        if not os.path.exists(path):
            print(f"  ❌ {name}: {path} (NOT FOUND)")
            missing_files.append(name)
        else:
            print(f"  ✅ {name}: {path}")

    if missing_files:
        print("\n❌ ERROR: Missing required data files:")
        for name in missing_files:
            print(f"  - {name}")
        print("\nPlease download required data using:")
        print("  python download_data.py --bbox \"minx,miny,maxx,maxy\"")
        print("\nOr see DATA_SOURCES_STATUS.md for manual download instructions.")
        sys.exit(1)

    # Initialize tool
    tool = GeospatialAnalysisTool(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        config_path=args.config
    )

    try:
        # Phase 1: Load data
        tool.load_data(rail_path=args.rail, infrastructure_path=args.infrastructure)

        # Phase 2: Calculate vulnerability
        tool.calculate_vulnerability(
            imperviousness_raster=args.imperviousness,
            dem_path=args.dem,
            soils_path=args.soils
        )

        # Phase 2.5: Contextual Analysis
        tool.analyze_context(
            flood_zones_path=args.flood_zones,
            svi_path=args.svi,
            canopy_raster=args.canopy,
            zoning_path=args.zoning
        )

        # Phase 3: Analyze infrastructure density
        tool.analyze_infrastructure_density()

        # Phase 4: Assess alignment
        tool.assess_alignment()

        # Phase 5: Spatial clustering (if available)
        if SPATIAL_CLUSTERING_AVAILABLE and 'gap_index' in tool.segments.columns:
            clustering_results, tool.segments = perform_spatial_clustering_analysis(
                tool.segments,
                variable_col='gap_index'
            )
            if clustering_results:
                tool.results['spatial_clustering'] = clustering_results

        # Phase 6: Runoff modeling (if available)
        if RUNOFF_MODELING_AVAILABLE:
            tool.segments = perform_runoff_modeling(tool.segments)

        # Generate report
        tool.generate_report()

        # Save results
        tool.save_results()

        print("\n" + "="*70)
        print("✅ ANALYSIS COMPLETE")
        print("="*70)
        print(f"\nResults saved to: {tool.output_dir}")
        print("\nOutput files:")
        print("  - analysis_segments.gpkg (or .shp)")
        print("  - analysis_segments.csv")
        print("  - analysis_summary.txt")
        print("  - analysis_summary.json")

    except ValueError as e:
        print(f"\n❌ ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error: {e}", exc_info=args.verbose)
        print(f"\n❌ ANALYSIS FAILED: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
