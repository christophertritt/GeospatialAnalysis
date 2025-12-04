#!/usr/bin/env python3
"""
Test script to verify project structure and basic imports
"""
import os
import sys

def test_structure():
    """Test that all required files and directories exist"""
    print("="*70)
    print("TESTING PROJECT STRUCTURE")
    print("="*70)
    
    required_files = [
        'README.md',
        'LICENSE',
        'requirements.txt',
        'setup.py',
        'COMPLETE_METHODOLOGY_GUIDE.txt',
        'scripts/geospatial_analysis.py',
        'scripts/utils/__init__.py',
        'scripts/utils/gis_functions.py',
        'scripts/utils/statistics.py',
        'scripts/spatial_clustering.py',
        'scripts/runoff_modeling.py',
        'example_usage.py',
        'test_tool.py',
        'docs/DATA_ACQUISITION_GUIDE.md'
    ]
    
    required_dirs = [
        'data/raw',
        'data/processed',
        'data/outputs',
        'figures/maps',
        'figures/charts',
        'scripts/utils',
        'analysis',
        'docs'
    ]
    
    print("\nChecking required files...")
    all_files_exist = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path} - MISSING")
            all_files_exist = False
    
    print("\nChecking required directories...")
    all_dirs_exist = True
    for dir_path in required_dirs:
        if os.path.isdir(dir_path):
            print(f"✓ {dir_path}/")
        else:
            print(f"✗ {dir_path}/ - MISSING")
            all_dirs_exist = False
    
    print("\nChecking Python syntax...")
    python_files = [
        'scripts/geospatial_analysis.py',
        'scripts/utils/__init__.py',
        'scripts/utils/gis_functions.py',
        'scripts/utils/statistics.py',
        'scripts/spatial_clustering.py',
        'scripts/runoff_modeling.py',
        'example_usage.py',
        'test_tool.py',
        'setup.py'
    ]
    
    syntax_ok = True
    for py_file in python_files:
        try:
            with open(py_file, 'r') as f:
                code = f.read()
            compile(code, py_file, 'exec')
            print(f"✓ {py_file} - syntax OK")
        except SyntaxError as e:
            print(f"✗ {py_file} - SYNTAX ERROR: {e}")
            syntax_ok = False
        except FileNotFoundError:
            print(f"✗ {py_file} - FILE NOT FOUND")
            syntax_ok = False
    
    print("\n" + "="*70)
    if all_files_exist and all_dirs_exist and syntax_ok:
        print("✓ ALL STRUCTURE TESTS PASSED")
        print("="*70)
        print("\nProject structure is complete and valid!")
        print("\nTo install dependencies and run the tool:")
        print("  1. pip install -r requirements.txt")
        print("  2. python test_tool.py  # Full test with dependencies")
        print("  3. python scripts/geospatial_analysis.py  # Run analysis")
        return 0
    else:
        print("✗ SOME TESTS FAILED")
        print("="*70)
        return 1


if __name__ == '__main__':
    sys.exit(test_structure())
