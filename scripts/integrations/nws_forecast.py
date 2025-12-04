"""
National Weather Service API integration for gridded forecasts.

This module provides access to NWS weather forecasts for climate change scenario
modeling, including projected precipitation increases.

Citation: Vose et al. (2017) "Fourth National Climate Assessment" for precipitation
change projections in Pacific Northwest.

NWS API Documentation: https://www.weather.gov/documentation/services-web-api
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import geopandas as gpd
import pandas as pd
import requests
from shapely.geometry import Point
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

# NWS API base URL (no authentication required)
NWS_API_BASE = "https://api.weather.gov"

# Climate change precipitation multipliers for Pacific Northwest
# Source: Mote et al. (2019) "Fourth Oregon Climate Assessment Report"
CLIMATE_SCENARIOS = {
    "current": {
        "name": "Current Climate (2020s)",
        "precip_multiplier": 1.0,
        "extreme_frequency_multiplier": 1.0
    },
    "mid_century": {
        "name": "Mid-Century (2050s) RCP4.5",
        "precip_multiplier": 1.08,  # 8% increase in wet season precipitation
        "extreme_frequency_multiplier": 1.15  # 15% increase in extreme events
    },
    "end_century_moderate": {
        "name": "End-Century (2080s) RCP4.5",
        "precip_multiplier": 1.12,  # 12% increase
        "extreme_frequency_multiplier": 1.25  # 25% increase
    },
    "end_century_high": {
        "name": "End-Century (2080s) RCP8.5",
        "precip_multiplier": 1.20,  # 20% increase
        "extreme_frequency_multiplier": 1.40  # 40% increase in extremes
    }
}


@dataclass(frozen=True)
class GridpointForecast:
    """Weather forecast for a specific gridpoint."""

    grid_id: str
    grid_x: int
    grid_y: int
    forecast_time: datetime
    temperature_f: float
    precipitation_probability: float
    precipitation_amount_in: float
    wind_speed_mph: float
    short_forecast: str


@dataclass(frozen=True)
class ClimateScenario:
    """Climate change scenario projection."""

    scenario_name: str
    baseline_precip_in: float
    projected_precip_in: float
    percent_change: float
    extreme_event_multiplier: float
    description: str


class NWSForecastClient:
    """
    Client for National Weather Service API.

    No authentication required - public data access.

    Citation: Climate projection scenario methodology follows Vose et al. (2017)
    "Fourth National Climate Assessment" for precipitation change projections.
    """

    def __init__(
        self,
        base_url: str = NWS_API_BASE,
        session: Optional[requests.Session] = None
    ) -> None:
        """Initialize NWS API client."""

        self.base_url = base_url.rstrip("/")
        self.session = session or requests.Session()
        self.session.headers.update({
            "User-Agent": "(GeospatialAnalysis Rail Corridor Research, contact@example.com)",
            "Accept": "application/geo+json"
        })

    def _request(self, endpoint: str) -> Dict:
        """
        Execute GET request against NWS API.

        Args:
            endpoint: API endpoint path

        Returns:
            JSON response
        """

        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        response = self.session.get(url, timeout=30)
        response.raise_for_status()

        return response.json()

    def get_gridpoint_from_coords(
        self,
        latitude: float,
        longitude: float
    ) -> Tuple[str, int, int]:
        """
        Get NWS gridpoint identifiers for a lat/lon coordinate.

        Args:
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees

        Returns:
            Tuple of (grid_id, grid_x, grid_y)
        """

        endpoint = f"points/{latitude:.4f},{longitude:.4f}"
        data = self._request(endpoint)

        properties = data.get("properties", {})
        grid_id = properties.get("gridId")
        grid_x = properties.get("gridX")
        grid_y = properties.get("gridY")

        if not all([grid_id, grid_x, grid_y]):
            raise ValueError(f"Could not get gridpoint for {latitude}, {longitude}")

        return grid_id, grid_x, grid_y

    def get_gridpoint_forecast(
        self,
        grid_id: str,
        grid_x: int,
        grid_y: int
    ) -> List[GridpointForecast]:
        """
        Get detailed gridpoint forecast.

        Args:
            grid_id: NWS grid identifier (e.g., 'SEW' for Seattle)
            grid_x: Grid X coordinate
            grid_y: Grid Y coordinate

        Returns:
            List of GridpointForecast objects
        """

        endpoint = f"gridpoints/{grid_id}/{grid_x},{grid_y}/forecast"
        data = self._request(endpoint)

        forecasts: List[GridpointForecast] = []

        try:
            periods = data.get("properties", {}).get("periods", [])

            for period in periods:
                # Parse precipitation if available
                precip_amount = 0.0
                precip_prob = 0.0

                # NWS provides probabilityOfPrecipitation separately
                if "probabilityOfPrecipitation" in period:
                    precip_prob = float(period["probabilityOfPrecipitation"].get("value", 0) or 0)

                # Quantitative precipitation forecast (QPF) in detailed forecast
                detailed = period.get("detailedForecast", "")
                # Simple parsing - actual QPF requires gridpoint/forecast/quantitativePrecipitation endpoint
                if "inch" in detailed.lower():
                    # This is simplified - real implementation would parse properly
                    precip_amount = 0.5  # Placeholder

                forecast = GridpointForecast(
                    grid_id=grid_id,
                    grid_x=grid_x,
                    grid_y=grid_y,
                    forecast_time=datetime.fromisoformat(period["startTime"].replace("Z", "+00:00")),
                    temperature_f=float(period.get("temperature", 50)),
                    precipitation_probability=precip_prob,
                    precipitation_amount_in=precip_amount,
                    wind_speed_mph=self._parse_wind_speed(period.get("windSpeed", "0 mph")),
                    short_forecast=period.get("shortForecast", "")
                )

                forecasts.append(forecast)

        except (KeyError, ValueError, TypeError) as e:
            raise RuntimeError(f"Failed to parse NWS forecast: {e}") from e

        return forecasts

    def _parse_wind_speed(self, wind_str: str) -> float:
        """Parse wind speed string like '5 to 10 mph' to average value."""

        try:
            # Extract numbers from string
            numbers = [float(s) for s in wind_str.split() if s.replace(".", "").isdigit()]
            return sum(numbers) / len(numbers) if numbers else 0.0
        except Exception:
            return 0.0

    def get_forecast_for_corridor(
        self,
        corridor_gdf: gpd.GeoDataFrame,
        sample_points: int = 5
    ) -> pd.DataFrame:
        """
        Get gridded forecasts for rail corridor extent.

        Args:
            corridor_gdf: GeoDataFrame of rail corridor
            sample_points: Number of forecast points to sample along corridor

        Returns:
            DataFrame with forecasts for corridor area
        """

        # Get corridor bounds
        bounds = corridor_gdf.to_crs(4326).total_bounds
        min_lon, min_lat, max_lon, max_lat = bounds

        # Sample points evenly across corridor
        lats = [min_lat + (max_lat - min_lat) * i / (sample_points - 1) for i in range(sample_points)]
        lons = [min_lon + (max_lon - min_lon) * i / (sample_points - 1) for i in range(sample_points)]

        all_forecasts = []

        for lat, lon in zip(lats, lons):
            try:
                grid_id, grid_x, grid_y = self.get_gridpoint_from_coords(lat, lon)
                forecasts = self.get_gridpoint_forecast(grid_id, grid_x, grid_y)

                for fc in forecasts:
                    all_forecasts.append({
                        "sample_lat": lat,
                        "sample_lon": lon,
                        "grid_id": fc.grid_id,
                        "forecast_time": fc.forecast_time,
                        "temperature_f": fc.temperature_f,
                        "precip_probability": fc.precipitation_probability,
                        "precip_amount_in": fc.precipitation_amount_in,
                        "wind_speed_mph": fc.wind_speed_mph,
                        "forecast": fc.short_forecast
                    })

            except Exception as e:
                print(f"Warning: Could not get forecast for {lat:.4f}, {lon:.4f}: {e}")
                continue

        return pd.DataFrame(all_forecasts)

    def generate_climate_scenarios(
        self,
        baseline_precip_in: float,
        storm_event: str = "25-year"
    ) -> List[ClimateScenario]:
        """
        Generate climate change scenario projections for precipitation.

        Citation: Scenario projections follow Mote et al. (2019) "Fourth Oregon
        Climate Assessment Report" for Pacific Northwest extreme precipitation.

        Args:
            baseline_precip_in: Current/historical precipitation amount
            storm_event: Design storm return period

        Returns:
            List of ClimateScenario objects
        """

        scenarios: List[ClimateScenario] = []

        for scenario_id, params in CLIMATE_SCENARIOS.items():
            multiplier = params["precip_multiplier"]
            projected = baseline_precip_in * multiplier
            pct_change = (multiplier - 1.0) * 100

            scenario = ClimateScenario(
                scenario_name=params["name"],
                baseline_precip_in=baseline_precip_in,
                projected_precip_in=projected,
                percent_change=pct_change,
                extreme_event_multiplier=params["extreme_frequency_multiplier"],
                description=f"{storm_event} storm under {params['name']} climate conditions"
            )

            scenarios.append(scenario)

        return scenarios

    def model_future_runoff_scenarios(
        self,
        segments_gdf: gpd.GeoDataFrame,
        baseline_storm_in: float = 3.4,  # 25-year design storm
        cn_current: str = "cn_current"
    ) -> pd.DataFrame:
        """
        Model runoff under future climate scenarios.

        Uses SCS Curve Number method with climate-adjusted precipitation.

        Args:
            segments_gdf: GeoDataFrame with CN values
            baseline_storm_in: Current design storm precipitation
            cn_current: Column name for curve number values

        Returns:
            DataFrame with scenario modeling results
        """

        if cn_current not in segments_gdf.columns:
            raise ValueError(f"Column {cn_current} not found in segments")

        # Import runoff calculation (avoid circular import)
        from scripts.utils.statistics import calculate_runoff_depth

        scenarios = self.generate_climate_scenarios(baseline_storm_in)

        results = []

        for idx, row in segments_gdf.iterrows():
            segment_id = row.get("segment_id", idx)
            cn = row[cn_current]

            for scenario in scenarios:
                # Calculate runoff for this scenario
                runoff_in = calculate_runoff_depth(scenario.projected_precip_in, cn)

                # Convert to volume if area available
                volume_acft = 0.0
                if "buffer_area_acres" in row:
                    volume_acft = runoff_in / 12.0 * row["buffer_area_acres"]

                results.append({
                    "segment_id": segment_id,
                    "scenario": scenario.scenario_name,
                    "baseline_precip_in": scenario.baseline_precip_in,
                    "projected_precip_in": scenario.projected_precip_in,
                    "percent_change": scenario.percent_change,
                    "runoff_depth_in": runoff_in,
                    "runoff_volume_acft": volume_acft,
                    "curve_number": cn
                })

        return pd.DataFrame(results)

    def get_precipitation_outlook(
        self,
        latitude: float,
        longitude: float,
        days_ahead: int = 7
    ) -> pd.DataFrame:
        """
        Get precipitation outlook for next N days.

        Args:
            latitude: Location latitude
            longitude: Location longitude
            days_ahead: Days to forecast (max ~7)

        Returns:
            DataFrame with daily precipitation outlook
        """

        try:
            grid_id, grid_x, grid_y = self.get_gridpoint_from_coords(latitude, longitude)
            forecasts = self.get_gridpoint_forecast(grid_id, grid_x, grid_y)

            # Filter to requested timeframe
            cutoff = datetime.now() + timedelta(days=days_ahead)
            filtered = [fc for fc in forecasts if fc.forecast_time <= cutoff]

            df = pd.DataFrame([{
                "date": fc.forecast_time.date(),
                "precip_probability": fc.precipitation_probability,
                "precip_amount_in": fc.precipitation_amount_in,
                "forecast": fc.short_forecast
            } for fc in filtered])

            return df

        except Exception as e:
            print(f"Warning: Could not get precipitation outlook: {e}")
            return pd.DataFrame()

    def persist_to_postgres(
        self,
        df: pd.DataFrame,
        table_name: str,
        engine_url: str
    ) -> None:
        """
        Persist forecast data to PostgreSQL.

        Args:
            df: DataFrame to persist
            table_name: Target table name
            engine_url: SQLAlchemy connection string
        """

        if df.empty:
            return

        engine: Engine = create_engine(engine_url, future=True)

        try:
            df.to_sql(table_name, engine, if_exists="append", index=False)
        except SQLAlchemyError as exc:
            raise RuntimeError(f"Failed to insert into {table_name}: {exc}") from exc

    def ingest_monthly_climate_scenarios(
        self,
        segments_gdf: gpd.GeoDataFrame,
        engine_url: str
    ) -> None:
        """
        Generate and store climate scenario projections.

        This method is designed to be called monthly by automated scheduler.

        Args:
            segments_gdf: Analysis segments with CN values
            engine_url: PostgreSQL connection string
        """

        print("Generating climate change runoff scenarios...")

        # Model runoff under multiple climate scenarios
        scenario_results = self.model_future_runoff_scenarios(segments_gdf)

        # Add generation timestamp
        scenario_results["generated_date"] = datetime.now()

        # Persist to database
        self.persist_to_postgres(scenario_results, "nws_climate_scenarios", engine_url)

        print(f"Stored {len(scenario_results)} climate scenario projections")
