#!/usr/bin/env python3
"""
Example usage of the GeospatialAnalysis tool

This script demonstrates how to use the tool with sample data
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from scripts.geospatial_analysis import GeospatialAnalysisTool


def main():
    """Run example analysis"""
    
    print("="*70)
    print("GEOSPATIAL ANALYSIS TOOL - EXAMPLE USAGE")
    print("="*70)
    print("\nThis example demonstrates the complete analysis workflow")
    print("using synthetic sample data.\n")
    
    # Initialize the tool
    print("Step 1: Initialize the tool")
    tool = GeospatialAnalysisTool(
        data_dir='data',
        output_dir='data/outputs'
    )
    
    # Load data (will create sample data since no files provided)
    print("\nStep 2: Load sample data")
    tool.load_data()
    
    # Calculate vulnerability index
    print("\nStep 3: Calculate vulnerability index")
    # You can provide custom imperviousness and slope data here
    tool.calculate_vulnerability(
        imperviousness=None,  # Will use random values
        slope=None,           # Will use random values
        soil_type='C'         # Moderate drainage
    )
    
    # Analyze infrastructure density
    print("\nStep 4: Analyze infrastructure density")
    tool.analyze_infrastructure_density()
    
    # Assess alignment between vulnerability and infrastructure
    print("\nStep 5: Assess alignment")
    tool.assess_alignment()
    
    # Optional: Spatial clustering analysis
    print("\nStep 6: Spatial clustering (if available)")
    try:
        from scripts.spatial_clustering import perform_spatial_clustering_analysis
        
        if 'gap_index' in tool.segments.columns:
            clustering_results, tool.segments = perform_spatial_clustering_analysis(
                tool.segments,
                variable_col='gap_index'
            )
            tool.results['spatial_clustering'] = clustering_results
    except ImportError:
        print("  Spatial clustering not available (libpysal/esda not installed)")
    
    # Optional: Runoff modeling
    print("\nStep 7: Runoff modeling (if available)")
    try:
        from scripts.runoff_modeling import perform_runoff_modeling
        
        tool.segments = perform_runoff_modeling(
            tool.segments,
            storm_events=['2-year', '10-year', '25-year'],
            soil_type='C'
        )
    except ImportError:
        print("  Runoff modeling not available")
    
    # Generate report
    print("\nStep 8: Generate report")
    tool.generate_report()
    
    # Save results
    print("\nStep 9: Save results")
    tool.save_results()
    
    print("\n" + "="*70)
    print("EXAMPLE COMPLETE")
    print("="*70)
    print(f"\nResults have been saved to: {tool.output_dir}")
    print("\nKey output files:")
    print("  - analysis_summary.txt: Summary report")
    print("  - analysis_segments.shp: Spatial data with all metrics")
    print("  - analysis_segments.csv: Tabular data for spreadsheet analysis")
    
    print("\n" + "="*70)
    print("NEXT STEPS")
    print("="*70)
    print("\n1. Review the output files in data/outputs/")
    print("2. Open analysis_segments.shp in QGIS or ArcGIS for visualization")
    print("3. Use analysis_segments.csv for statistical analysis")
    print("4. Customize the analysis with your own data:")
    print("   python scripts/geospatial_analysis.py \\")
    print("       --rail data/raw/rail/your_rail.shp \\")
    print("       --infrastructure data/raw/infrastructure/your_infra.shp")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
