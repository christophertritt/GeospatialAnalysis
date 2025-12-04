#!/usr/bin/env python3
"""
Test script to verify the geospatial analysis tool works correctly
"""
import sys
import os

# Add scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))

def test_imports():
    """Test that all required modules can be imported"""
    print("Testing imports...")
    
    try:
        import geopandas as gpd
        print("✓ geopandas")
    except ImportError as e:
        print(f"✗ geopandas: {e}")
        return False
    
    try:
        import numpy as np
        print("✓ numpy")
    except ImportError as e:
        print(f"✗ numpy: {e}")
        return False
    
    try:
        import pandas as pd
        print("✓ pandas")
    except ImportError as e:
        print(f"✗ pandas: {e}")
        return False
    
    try:
        from scipy import stats
        print("✓ scipy")
    except ImportError as e:
        print(f"✗ scipy: {e}")
        return False
    
    try:
        from shapely.geometry import Point, LineString
        print("✓ shapely")
    except ImportError as e:
        print(f"✗ shapely: {e}")
        return False
    
    return True


def test_utils():
    """Test utility functions"""
    print("\nTesting utility functions...")
    
    try:
        from utils import (
            validate_spatial_data,
            reproject_to_standard,
            calculate_runoff_depth,
            correlation_analysis,
            classify_vulnerability,
            calculate_gap_index
        )
        print("✓ All utility functions imported successfully")
        
        # Test a simple function
        runoff = calculate_runoff_depth(2.5, 75)
        print(f"✓ calculate_runoff_depth(2.5, 75) = {runoff:.3f} inches")
        
        vuln_class = classify_vulnerability(5.5)
        print(f"✓ classify_vulnerability(5.5) = {vuln_class}")
        
        gap = calculate_gap_index(7.0, 800)
        print(f"✓ calculate_gap_index(7.0, 800) = {gap:.2f}")
        
        return True
    except Exception as e:
        print(f"✗ Error testing utilities: {e}")
        return False


def test_main_tool():
    """Test main analysis tool"""
    print("\nTesting main analysis tool...")
    
    try:
        from geospatial_analysis import GeospatialAnalysisTool
        print("✓ GeospatialAnalysisTool imported successfully")
        
        # Initialize tool
        tool = GeospatialAnalysisTool(data_dir='data', output_dir='data/outputs')
        print("✓ Tool initialized")
        
        # Test with sample data
        print("\nRunning quick analysis with sample data...")
        tool.load_data()
        print("✓ Sample data loaded")
        
        tool.calculate_vulnerability()
        print("✓ Vulnerability calculated")
        
        tool.analyze_infrastructure_density()
        print("✓ Infrastructure density analyzed")
        
        tool.assess_alignment()
        print("✓ Alignment assessed")
        
        return True
    except Exception as e:
        print(f"✗ Error testing main tool: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("="*70)
    print("GEOSPATIAL ANALYSIS TOOL - TEST SUITE")
    print("="*70)
    
    # Test imports
    if not test_imports():
        print("\n✗ Import test failed. Please install requirements:")
        print("  pip install -r requirements.txt")
        return 1
    
    # Test utilities
    if not test_utils():
        print("\n✗ Utility test failed.")
        return 1
    
    # Test main tool
    if not test_main_tool():
        print("\n✗ Main tool test failed.")
        return 1
    
    print("\n" + "="*70)
    print("✓ ALL TESTS PASSED")
    print("="*70)
    print("\nThe geospatial analysis tool is ready to use!")
    print("Run: python scripts/geospatial_analysis.py --help")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
