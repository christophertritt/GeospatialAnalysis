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

# Add utils to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'utils'))

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


class GeospatialAnalysisTool:
    """Main analysis tool for rail corridor geospatial analysis"""
    
    def __init__(self, data_dir='data', output_dir='data/outputs'):
        """
        Initialize the analysis tool
        
        Args:
            data_dir: Base directory for data files
            output_dir: Directory for output files
        """
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Standard CRS: Washington State Plane South NAD83(2011) EPSG:2927
        self.target_crs = 2927
        
        # Buffer distances in meters
        self.buffer_distances = [100, 250, 500]
        
        # Analysis results storage
        self.segments = None
        self.infrastructure = None
        self.results = {}
    
    def load_data(self, rail_path=None, infrastructure_path=None):
        """
        Load and validate spatial data
        
        Args:
            rail_path: Path to rail corridor shapefile
            infrastructure_path: Path to infrastructure shapefile
        """
        print("\n" + "="*70)
        print("PHASE 1: DATA LOADING AND VALIDATION")
        print("="*70)
        
        # Load rail data
        if rail_path and os.path.exists(rail_path):
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
        else:
            print("Warning: No rail data provided. Using sample geometry.")
            # Create sample geometry for demonstration
            self.create_sample_data()
        
        # Load infrastructure data
        if infrastructure_path and os.path.exists(infrastructure_path):
            print(f"\nLoading infrastructure data from: {infrastructure_path}")
            infra = gpd.read_file(infrastructure_path)
            infra = validate_spatial_data(infra, "Infrastructure")
            self.infrastructure = reproject_to_standard(infra, self.target_crs)
        else:
            print("Warning: No infrastructure data provided.")
            self.infrastructure = None
    
    def create_sample_data(self):
        """Create sample data for demonstration"""
        print("\nCreating sample corridor segment...")
        # Create a simple line and buffer it
        from shapely.geometry import LineString
        
        # Sample line (in WA State Plane South coordinates)
        line = LineString([
            (1200000, 200000),
            (1200000, 210000),
            (1205000, 210000)
        ])
        
        gdf = gpd.GeoDataFrame({'geometry': [line]}, crs=f'EPSG:{self.target_crs}')
        buffers = create_buffers(gdf, self.buffer_distances)
        
        self.segments = buffers['250m'].copy()
        self.segments['segment_id'] = range(1, len(self.segments) + 1)
    
    def calculate_vulnerability(self, imperviousness=None, slope=None, soil_type='C'):
        """
        Calculate vulnerability index for segments
        
        Args:
            imperviousness: Array or dict of imperviousness percentages by segment
            slope: Array or dict of slope percentages by segment
            soil_type: Dominant soil type ('A', 'B', 'C', 'D')
        """
        print("\n" + "="*70)
        print("PHASE 2: VULNERABILITY INDEX CALCULATION")
        print("="*70)
        
        if self.segments is None:
            print("Error: No segments loaded. Run load_data() first.")
            return
        
        # For demonstration, create synthetic vulnerability scores
        n_segments = len(self.segments)
        
        # Sample imperviousness if not provided
        if imperviousness is None:
            imperviousness = np.random.uniform(30, 85, n_segments)
        
        # Sample slope if not provided
        if slope is None:
            slope = np.random.uniform(0.5, 8, n_segments)
        
        # Calculate component scores (0-2 scale)
        # Imperviousness: >75% = 2, 60-75% = 1.5, 45-60% = 1, <45% = 0
        imperv_vuln = np.where(imperviousness > 75, 2.0,
                              np.where(imperviousness > 60, 1.5,
                                      np.where(imperviousness > 45, 1.0, 0.0)))
        
        # Slope: <2% = 2, 2-5% = 1.5, 5-10% = 1, >10% = 0
        slope_vuln = np.where(slope < 2, 2.0,
                             np.where(slope < 5, 1.5,
                                     np.where(slope < 10, 1.0, 0.0)))
        
        # Soil: D=2, C=1.5, B=1, A=0
        soil_scores = {'D': 2.0, 'C': 1.5, 'B': 1.0, 'A': 0.0}
        soil_vuln = soil_scores.get(soil_type, 1.5)
        
        # Composite vulnerability (weighted average of components)
        # For simplicity, using equal weights here
        weights = {
            'imperv': 0.35,
            'slope': 0.25,
            'soil': 0.20,
            'topo': 0.20  # Placeholder
        }
        
        # Topographic vulnerability (placeholder - would come from DEM)
        topo_vuln = np.random.uniform(0.5, 2.0, n_segments)
        
        vuln_composite = (
            weights['imperv'] * imperv_vuln +
            weights['slope'] * slope_vuln +
            weights['soil'] * soil_vuln +
            weights['topo'] * topo_vuln
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
    
    def analyze_infrastructure_density(self):
        """Calculate infrastructure density for segments"""
        print("\n" + "="*70)
        print("PHASE 3: INFRASTRUCTURE DENSITY ANALYSIS")
        print("="*70)
        
        if self.segments is None:
            print("Error: No segments loaded.")
            return
        
        if self.infrastructure is None:
            print("Warning: No infrastructure data available. Creating sample data.")
            # Create sample infrastructure points
            n_points = 50
            bounds = self.segments.total_bounds
            
            x = np.random.uniform(bounds[0], bounds[2], n_points)
            y = np.random.uniform(bounds[1], bounds[3], n_points)
            
            from shapely.geometry import Point
            points = [Point(xi, yi) for xi, yi in zip(x, y)]
            
            self.infrastructure = gpd.GeoDataFrame(
                {
                    'FacilityID': range(1, n_points + 1),
                    'AreaSqFt': np.random.uniform(500, 5000, n_points)
                },
                geometry=points,
                crs=f'EPSG:{self.target_crs}'
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
    
    def save_results(self):
        """Save analysis results to files"""
        print("\n" + "="*70)
        print("SAVING RESULTS")
        print("="*70)
        
        if self.segments is not None:
            # Save segments shapefile
            output_path = self.output_dir / 'analysis_segments.shp'
            self.segments.to_file(output_path)
            print(f"Segments saved to: {output_path}")
            
            # Save CSV summary
            csv_path = self.output_dir / 'analysis_segments.csv'
            # Drop geometry for CSV
            df = pd.DataFrame(self.segments.drop(columns='geometry'))
            df.to_csv(csv_path, index=False)
            print(f"CSV summary saved to: {csv_path}")
        
        # Save infrastructure if available
        if self.infrastructure is not None:
            infra_path = self.output_dir / 'infrastructure_processed.shp'
            self.infrastructure.to_file(infra_path)
            print(f"Infrastructure saved to: {infra_path}")


def main():
    """Main entry point for CLI"""
    parser = argparse.ArgumentParser(
        description='Geospatial analysis tool for rail corridor flood vulnerability assessment'
    )
    parser.add_argument(
        '--rail',
        help='Path to rail corridor shapefile',
        default=None
    )
    parser.add_argument(
        '--infrastructure',
        help='Path to infrastructure shapefile',
        default=None
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
    
    args = parser.parse_args()
    
    # Initialize tool
    tool = GeospatialAnalysisTool(
        data_dir=args.data_dir,
        output_dir=args.output_dir
    )
    
    # Run analysis pipeline
    print("\n" + "="*70)
    print("GEOSPATIAL ANALYSIS TOOL")
    print("Rail Corridor Flood Vulnerability and Infrastructure Assessment")
    print("="*70)
    
    # Phase 1: Load data
    tool.load_data(rail_path=args.rail, infrastructure_path=args.infrastructure)
    
    # Phase 2: Calculate vulnerability
    tool.calculate_vulnerability()
    
    # Phase 3: Analyze infrastructure density
    tool.analyze_infrastructure_density()
    
    # Phase 4: Assess alignment
    tool.assess_alignment()
    
    # Generate report
    tool.generate_report()
    
    # Save results
    tool.save_results()
    
    print("\n" + "="*70)
    print("ANALYSIS COMPLETE")
    print("="*70)
    print(f"\nResults saved to: {tool.output_dir}")


if __name__ == '__main__':
    main()
