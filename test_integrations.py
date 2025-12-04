#!/usr/bin/env python3
"""
Integration Test Suite for GeospatialAnalysis Repository

Tests all API integrations, data pipeline, and dashboard dependencies.
Run this script to verify the repository is properly configured.

Usage:
    python test_integrations.py
"""

import sys
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

def test_api_integrations():
    """Test all API integration modules can be imported."""
    print("\n" + "="*70)
    print("Testing API Integrations")
    print("="*70)

    tests = []

    # Test NOAA CDO
    try:
        from integrations.noaa_cdo import NOAACDOClient
        print("✓ NOAA CDO integration available")
        tests.append(("NOAA CDO", True, None))
    except Exception as e:
        print(f"✗ NOAA CDO integration failed: {e}")
        tests.append(("NOAA CDO", False, str(e)))

    # Test USGS Water Services
    try:
        from integrations.usgs_water import USGSWaterServicesClient
        print("✓ USGS Water Services integration available")
        tests.append(("USGS Water", True, None))
    except Exception as e:
        print(f"✗ USGS Water Services integration failed: {e}")
        tests.append(("USGS Water", False, str(e)))

    # Test Seattle Open Data
    try:
        from integrations.seattle_opendata import SeattleOpenDataClient
        print("✓ Seattle Open Data integration available")
        tests.append(("Seattle Open Data", True, None))
    except Exception as e:
        print(f"✗ Seattle Open Data integration failed: {e}")
        tests.append(("Seattle Open Data", False, str(e)))

    # Test NWS Forecast
    try:
        from integrations.nws_forecast import NWSForecastClient
        print("✓ NWS Forecast integration available")
        tests.append(("NWS Forecast", True, None))
    except Exception as e:
        print(f"✗ NWS Forecast integration failed: {e}")
        tests.append(("NWS Forecast", False, str(e)))

    # Test Multi-Jurisdiction
    try:
        from integrations.multi_jurisdiction import MultiJurisdictionConsolidator
        print("✓ Multi-Jurisdiction consolidation available")
        tests.append(("Multi-Jurisdiction", True, None))
    except Exception as e:
        print(f"✗ Multi-Jurisdiction consolidation failed: {e}")
        tests.append(("Multi-Jurisdiction", False, str(e)))

    return tests


def test_analysis_modules():
    """Test analysis module imports."""
    print("\n" + "="*70)
    print("Testing Analysis Modules")
    print("="*70)

    tests = []

    # Test spatial statistics
    try:
        from spatial_clustering import calculate_morans_i, calculate_hot_spots, calculate_local_morans
        print("✓ Spatial statistics module available")
        tests.append(("Spatial Statistics", True, None))
    except Exception as e:
        print(f"✗ Spatial statistics module failed: {e}")
        tests.append(("Spatial Statistics", False, str(e)))

    # Test runoff modeling
    try:
        from runoff_modeling import perform_runoff_modeling, prepare_curve_numbers
        print("✓ Runoff modeling module available")
        tests.append(("Runoff Modeling", True, None))
    except Exception as e:
        print(f"✗ Runoff modeling module failed: {e}")
        tests.append(("Runoff Modeling", False, str(e)))

    # Test utility statistics
    try:
        from utils.statistics import calculate_runoff_depth, calculate_cn_from_imperviousness
        print("✓ Statistics utilities available")
        tests.append(("Statistics Utilities", True, None))
    except Exception as e:
        print(f"✗ Statistics utilities failed: {e}")
        tests.append(("Statistics Utilities", False, str(e)))

    return tests


def test_dashboard_dependencies():
    """Test dashboard dependencies."""
    print("\n" + "="*70)
    print("Testing Dashboard Dependencies")
    print("="*70)

    tests = []

    dependencies = [
        ("geopandas", "geopandas"),
        ("pandas", "pandas"),
        ("numpy", "numpy"),
        ("plotly.express", "plotly"),
        ("plotly.graph_objects", "plotly"),
        ("streamlit", "streamlit"),
        ("folium", "folium"),
        ("streamlit_folium", "streamlit-folium"),
    ]

    for module_name, package_name in dependencies:
        try:
            __import__(module_name)
            print(f"✓ {package_name}")
            tests.append((package_name, True, None))
        except Exception as e:
            print(f"✗ {package_name}: {e}")
            tests.append((package_name, False, str(e)))

    return tests


def test_data_pipeline_scheduler():
    """Test data pipeline scheduler."""
    print("\n" + "="*70)
    print("Testing Data Pipeline Scheduler")
    print("="*70)

    try:
        from data_pipeline_scheduler import DataPipelineScheduler
        print("✓ Scheduler module available")
        return [("Scheduler", True, None)]
    except Exception as e:
        print(f"✗ Scheduler failed: {e}")
        return [("Scheduler", False, str(e))]


def generate_report(all_tests):
    """Generate summary report."""
    print("\n" + "="*70)
    print("TEST SUMMARY REPORT")
    print("="*70)

    total = len(all_tests)
    passed = sum(1 for _, success, _ in all_tests if success)
    failed = total - passed

    print(f"\nTotal Tests: {total}")
    print(f"Passed: {passed} ✓")
    print(f"Failed: {failed} ✗")
    print(f"Success Rate: {passed/total*100:.1f}%")

    if failed > 0:
        print("\n" + "="*70)
        print("FAILED TESTS")
        print("="*70)

        for name, success, error in all_tests:
            if not success:
                print(f"\n✗ {name}")
                print(f"  Error: {error}")

        print("\n" + "="*70)
        print("REMEDIATION STEPS")
        print("="*70)
        print("\n1. Install missing dependencies:")
        print("   pip install -r requirements.txt")
        print("\n2. If SQLAlchemy missing:")
        print("   pip install SQLAlchemy>=2.0.0 APScheduler>=3.10.4")
        print("\n3. If spatial stats fail:")
        print("   pip install libpysal esda")
        print("\n4. Verify virtual environment activated:")
        print("   source .venv/bin/activate  # macOS/Linux")
        print("   .venv\\Scripts\\activate  # Windows")

    else:
        print("\n" + "="*70)
        print("✓✓✓ ALL TESTS PASSED! ✓✓✓")
        print("="*70)
        print("\nRepository is ready for use!")
        print("\nNext steps:")
        print("  1. Configure API tokens (see docs/API_SETUP_GUIDE.md)")
        print("  2. Run dashboard: streamlit run scripts/dashboard.py")
        print("  3. Start scheduler: python scripts/data_pipeline_scheduler.py --daemon")

    return failed == 0


def main():
    """Run all tests."""
    print("="*70)
    print("GeospatialAnalysis Integration Test Suite")
    print("="*70)

    all_tests = []

    # Run all test suites
    all_tests.extend(test_api_integrations())
    all_tests.extend(test_analysis_modules())
    all_tests.extend(test_dashboard_dependencies())
    all_tests.extend(test_data_pipeline_scheduler())

    # Generate report
    success = generate_report(all_tests)

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
