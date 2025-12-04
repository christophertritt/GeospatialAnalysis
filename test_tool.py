#!/usr/bin/env python3
"""
Integration tests for the geospatial analysis tool
"""
import os
import sys
import pytest
import geopandas as gpd
import numpy as np
import pandas as pd
from scripts.geospatial_analysis import GeospatialAnalysisTool

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

def test_imports():
    """Test that all required modules can be imported"""
    import geopandas as gpd
    import numpy as np
    import pandas as pd
    from scipy import stats
    from shapely.geometry import Point, LineString
    assert True

def test_utils_imports():
    """Test utility functions imports"""
    from scripts.utils import (
        validate_spatial_data,
        reproject_to_standard,
        calculate_runoff_depth,
        correlation_analysis,
        classify_vulnerability,
        calculate_gap_index
    )
    assert True

def test_utils_functionality():
    """Test utility functions logic"""
    from scripts.utils import (
        calculate_runoff_depth,
        classify_vulnerability,
        calculate_gap_index
    )
    
    # Test runoff
    runoff = calculate_runoff_depth(2.5, 75)
    assert runoff > 0
    
    # Test vulnerability classification
    vuln_class = classify_vulnerability(5.5)
    assert isinstance(vuln_class, str)
    assert vuln_class in ['Low', 'Moderate', 'High', 'Critical']
    
    # Test gap index
    gap = calculate_gap_index(7.0, 800)
    assert isinstance(gap, float)

class TestGeospatialAnalysisTool:
    @pytest.fixture
    def tool(self):
        return GeospatialAnalysisTool(data_dir='data', output_dir='data/outputs')

    def test_initialization(self, tool):
        assert tool.data_dir.name == 'data'
        assert tool.output_dir.name == 'outputs'
        assert tool.target_crs == 2927

    @pytest.mark.skipif(not os.path.exists('data/raw/rail/corridor.shp'), reason="Rail data missing")
    @pytest.mark.skipif(not os.path.exists('data/raw/infrastructure/permeable_pavement.shp'), reason="Infra data missing")
    def test_load_data(self, tool):
        rail_path = 'data/raw/rail/corridor.shp'
        infra_path = 'data/raw/infrastructure/permeable_pavement.shp'
        
        tool.load_data(rail_path=rail_path, infrastructure_path=infra_path)
        
        assert tool.segments is not None
        assert len(tool.segments) > 0
        assert tool.infrastructure is not None
        assert len(tool.infrastructure) > 0

if __name__ == '__main__':
    sys.exit(pytest.main([__file__]))
