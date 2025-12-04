#!/usr/bin/env python3
"""
Test script to verify project structure and basic imports
"""
import os
import sys
import pytest

REQUIRED_FILES = [
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

REQUIRED_DIRS = [
    'data/raw',
    'data/processed',
    'data/outputs',
    'figures/maps',
    'figures/charts',
    'scripts/utils',
    'analysis',
    'docs'
]

PYTHON_FILES = [
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

@pytest.mark.parametrize("file_path", REQUIRED_FILES)
def test_file_exists(file_path):
    """Test that required file exists"""
    assert os.path.exists(file_path), f"Missing file: {file_path}"

@pytest.mark.parametrize("dir_path", REQUIRED_DIRS)
def test_directory_exists(dir_path):
    """Test that required directory exists"""
    assert os.path.isdir(dir_path), f"Missing directory: {dir_path}"

@pytest.mark.parametrize("py_file", PYTHON_FILES)
def test_python_syntax(py_file):
    """Test that python file has valid syntax"""
    if not os.path.exists(py_file):
        pytest.skip(f"File not found: {py_file}")
    
    with open(py_file, 'r') as f:
        code = f.read()
    
    try:
        compile(code, py_file, 'exec')
    except SyntaxError as e:
        pytest.fail(f"Syntax error in {py_file}: {e}")

if __name__ == '__main__':
    sys.exit(pytest.main([__file__]))
