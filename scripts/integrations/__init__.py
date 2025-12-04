"""
API Integration Modules for Seattle-Tacoma Corridor Analysis.

This package provides data pipeline integrations with:
- NOAA Climate Data Online (CDO): Historical precipitation data
- USGS Water Services: Real-time streamgage data and flood validation
- Seattle Open Data Portal: Seattle SPU green stormwater infrastructure
- National Weather Service: Gridded forecasts and climate scenarios
- Multi-Jurisdiction Consolidation: All 9 corridor jurisdictions

Citation: Data pipeline architecture follows Janssen et al. (2012) "Benefits,
Adoption Barriers and Myths of Open Data and Open Government" for municipal
data integration patterns.
"""

from .noaa_cdo import NOAACDOClient
from .usgs_water import USGSWaterServicesClient
from .seattle_opendata import SeattleOpenDataClient
from .nws_forecast import NWSForecastClient
from .multi_jurisdiction import MultiJurisdictionConsolidator

__all__ = [
    "NOAACDOClient",
    "USGSWaterServicesClient",
    "SeattleOpenDataClient",
    "NWSForecastClient",
    "MultiJurisdictionConsolidator",
]
