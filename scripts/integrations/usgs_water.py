"""
USGS Water Services API integration for real-time hydrological data.

This module provides access to USGS streamgage data for the Seattle-Tacoma corridor,
including real-time streamgage heights and flood stage validation.

Citation: De Cicco et al. (2018) "dataRetrieval: R packages for discovering and
retrieving water data available from U.S. federal hydrologic web services"

USGS Water Services Documentation: https://waterservices.usgs.gov/rest/
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple

import pandas as pd
import requests
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

# USGS Water Services base URLs
USGS_IV_URL = "https://waterservices.usgs.gov/nwis/iv/"  # Instantaneous values
USGS_SITE_URL = "https://waterservices.usgs.gov/nwis/site/"  # Site information
USGS_STAT_URL = "https://waterservices.usgs.gov/nwis/stat/"  # Statistics

# Key streamgages for Seattle-Tacoma rail corridor
# Source: USGS National Water Information System
CORRIDOR_GAGES = {
    "12113000": {
        "name": "Green River near Auburn, WA",
        "location": "Auburn",
        "drainage_area_sqmi": 382,
        "flood_stage_ft": 24.0,
        "major_flood_ft": 28.0
    },
    "12108500": {
        "name": "Duwamish River at Tukwila, WA",
        "location": "Tukwila",
        "drainage_area_sqmi": 439,
        "flood_stage_ft": 18.0,
        "major_flood_ft": 22.0
    },
    "12101500": {
        "name": "Puyallup River at Puyallup, WA",
        "location": "Puyallup",
        "drainage_area_sqmi": 948,
        "flood_stage_ft": 31.0,
        "major_flood_ft": 35.0
    },
    "12095000": {
        "name": "Carbon River near Fairfax, WA",
        "location": "Sumner area",
        "drainage_area_sqmi": 82.2,
        "flood_stage_ft": 10.0,
        "major_flood_ft": 12.0
    }
}


@dataclass(frozen=True)
class StreamgageReading:
    """Real-time streamgage observation."""

    site_no: str
    datetime: datetime
    gage_height_ft: float
    discharge_cfs: Optional[float]
    flood_status: str


@dataclass(frozen=True)
class FloodStageComparison:
    """Comparison of current stage to flood thresholds."""

    site_no: str
    site_name: str
    current_stage_ft: float
    flood_stage_ft: float
    major_flood_ft: float
    stage_above_flood: float
    is_flooding: bool
    severity: str  # 'Normal', 'Action', 'Flood', 'Major Flood'


class USGSWaterServicesClient:
    """
    Client for USGS Water Services API.

    No authentication required for public data access.

    Citation: Methodology follows National Weather Service (2024)
    "Advanced Hydrologic Prediction Service" for flood stage threshold classification.
    """

    def __init__(
        self,
        iv_url: str = USGS_IV_URL,
        site_url: str = USGS_SITE_URL,
        stat_url: str = USGS_STAT_URL,
        session: Optional[requests.Session] = None
    ) -> None:
        """Initialize USGS Water Services client."""

        self.iv_url = iv_url.rstrip("/")
        self.site_url = site_url.rstrip("/")
        self.stat_url = stat_url.rstrip("/")
        self.session = session or requests.Session()
        self.session.headers.update({
            "User-Agent": "GeospatialAnalysis/1.0 (Rail Corridor Flood Research)"
        })

    def _request(self, url: str, params: Dict[str, str]) -> requests.Response:
        """Execute GET request against USGS Water Services."""

        response = self.session.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response

    def get_site_info(self, site_numbers: List[str]) -> pd.DataFrame:
        """
        Fetch site metadata for given USGS gage numbers.

        Args:
            site_numbers: List of USGS site numbers (e.g., ['12113000'])

        Returns:
            DataFrame with site metadata (name, location, drainage area)
        """

        params = {
            "format": "rdb",
            "sites": ",".join(site_numbers),
            "siteOutput": "expanded"
        }

        response = self._request(self.site_url, params)

        # Parse RDB format (tab-delimited with comment lines)
        lines = response.text.split("\n")
        data_lines = [line for line in lines if not line.startswith("#")]

        if len(data_lines) < 3:
            return pd.DataFrame()

        # Skip format line (second line after header)
        header = data_lines[0].split("\t")
        data = [line.split("\t") for line in data_lines[2:] if line.strip()]

        df = pd.DataFrame(data, columns=header)
        return df

    def get_current_conditions(
        self,
        site_numbers: List[str],
        parameter_cd: str = "00065"  # Gage height in feet
    ) -> List[StreamgageReading]:
        """
        Fetch current (most recent) streamgage conditions.

        Args:
            site_numbers: List of USGS site numbers
            parameter_cd: USGS parameter code (00065=gage height, 00060=discharge)

        Returns:
            List of StreamgageReading objects
        """

        params = {
            "format": "json",
            "sites": ",".join(site_numbers),
            "parameterCd": parameter_cd,
            "siteStatus": "all"
        }

        response = self._request(self.iv_url, params)
        data = response.json()

        readings: List[StreamgageReading] = []

        try:
            time_series = data["value"]["timeSeries"]

            for series in time_series:
                site_no = series["sourceInfo"]["siteCode"][0]["value"]
                values = series.get("values", [{}])[0].get("value", [])

                if not values:
                    continue

                # Get most recent value
                latest = values[-1]
                dt = datetime.fromisoformat(latest["dateTime"].replace("Z", "+00:00"))
                gage_height = float(latest["value"])

                # Determine flood status
                flood_info = CORRIDOR_GAGES.get(site_no, {})
                flood_stage = flood_info.get("flood_stage_ft", 999)
                major_flood = flood_info.get("major_flood_ft", 999)

                if gage_height >= major_flood:
                    flood_status = "Major Flood"
                elif gage_height >= flood_stage:
                    flood_status = "Flood"
                elif gage_height >= flood_stage * 0.9:
                    flood_status = "Action"
                else:
                    flood_status = "Normal"

                readings.append(StreamgageReading(
                    site_no=site_no,
                    datetime=dt,
                    gage_height_ft=gage_height,
                    discharge_cfs=None,  # Would need separate query for discharge
                    flood_status=flood_status
                ))

        except (KeyError, IndexError, ValueError) as e:
            raise RuntimeError(f"Failed to parse USGS response: {e}") from e

        return readings

    def get_time_series(
        self,
        site_number: str,
        start_date: date,
        end_date: date,
        parameter_cd: str = "00065"
    ) -> pd.DataFrame:
        """
        Fetch historical time series data for a streamgage.

        Args:
            site_number: USGS site number
            start_date: Start date for data retrieval
            end_date: End date for data retrieval
            parameter_cd: USGS parameter code

        Returns:
            DataFrame with datetime and values
        """

        params = {
            "format": "json",
            "sites": site_number,
            "parameterCd": parameter_cd,
            "startDT": start_date.isoformat(),
            "endDT": end_date.isoformat()
        }

        response = self._request(self.iv_url, params)
        data = response.json()

        try:
            time_series = data["value"]["timeSeries"][0]
            values = time_series["values"][0]["value"]

            records = []
            for val in values:
                records.append({
                    "datetime": datetime.fromisoformat(val["dateTime"].replace("Z", "+00:00")),
                    "value": float(val["value"])
                })

            df = pd.DataFrame(records)
            return df

        except (KeyError, IndexError, ValueError) as e:
            raise RuntimeError(f"Failed to parse time series: {e}") from e

    def compare_to_flood_stages(
        self,
        readings: List[StreamgageReading]
    ) -> List[FloodStageComparison]:
        """
        Compare current stages to flood stage thresholds.

        Args:
            readings: List of StreamgageReading objects

        Returns:
            List of FloodStageComparison objects
        """

        comparisons: List[FloodStageComparison] = []

        for reading in readings:
            gage_info = CORRIDOR_GAGES.get(reading.site_no)

            if not gage_info:
                continue

            flood_stage = gage_info["flood_stage_ft"]
            major_flood = gage_info["major_flood_ft"]
            current = reading.gage_height_ft

            stage_diff = current - flood_stage
            is_flooding = current >= flood_stage

            if current >= major_flood:
                severity = "Major Flood"
            elif current >= flood_stage:
                severity = "Flood"
            elif current >= flood_stage * 0.9:
                severity = "Action"
            else:
                severity = "Normal"

            comparisons.append(FloodStageComparison(
                site_no=reading.site_no,
                site_name=gage_info["name"],
                current_stage_ft=current,
                flood_stage_ft=flood_stage,
                major_flood_ft=major_flood,
                stage_above_flood=stage_diff,
                is_flooding=is_flooding,
                severity=severity
            ))

        return comparisons

    def validate_vulnerability_index(
        self,
        segments_gdf,
        lookback_days: int = 365
    ) -> pd.DataFrame:
        """
        Validate vulnerability index against observed flooding events.

        Correlates high-vulnerability segments with historical flood occurrences
        at nearby streamgages to validate the composite index methodology.

        Citation: Validation methodology per Maantay et al. (2020)
        "Modelling, mapping and visualisation of flood inundation uncertainties"

        Args:
            segments_gdf: GeoDataFrame with vulnerability scores
            lookback_days: Days of historical data to analyze

        Returns:
            DataFrame with validation statistics
        """

        end_date = date.today()
        start_date = end_date - timedelta(days=lookback_days)

        validation_results = []

        for site_no, info in CORRIDOR_GAGES.items():
            try:
                # Get historical data
                ts = self.get_time_series(site_no, start_date, end_date)

                # Count flood events
                flood_stage = info["flood_stage_ft"]
                flood_events = (ts["value"] >= flood_stage).sum()

                # Find nearby segments (simplified - would use spatial join)
                location = info["location"]
                nearby = segments_gdf[
                    segments_gdf["jurisdiction"].str.contains(location, case=False, na=False)
                ]

                if not nearby.empty:
                    avg_vulnerability = nearby["vuln_weighted"].mean() if "vuln_weighted" in nearby.columns else None

                    validation_results.append({
                        "site_no": site_no,
                        "site_name": info["name"],
                        "flood_events": flood_events,
                        "nearby_segments": len(nearby),
                        "avg_vulnerability": avg_vulnerability,
                        "validation_score": avg_vulnerability / 10 * flood_events if avg_vulnerability else None
                    })

            except Exception as e:
                print(f"Warning: Could not validate against {site_no}: {e}")
                continue

        return pd.DataFrame(validation_results)

    def get_flood_impacts_near_rail(
        self,
        rail_corridor_gdf,
        buffer_miles: float = 5.0
    ) -> pd.DataFrame:
        """
        Identify flood impact locations near rail infrastructure.

        Uses USGS Flood Event Viewer API to find documented flood impacts
        within buffer distance of rail corridor.

        Args:
            rail_corridor_gdf: GeoDataFrame of rail corridor
            buffer_miles: Search buffer in miles

        Returns:
            DataFrame of flood impact events near corridor
        """

        # Note: USGS Flood Event Viewer API requires spatial query
        # This is a simplified implementation showing the approach

        # Buffer corridor
        corridor_buffered = rail_corridor_gdf.to_crs(2927).buffer(buffer_miles * 5280).to_crs(4326)
        bounds = corridor_buffered.total_bounds

        # Placeholder for flood impact API call
        # Actual implementation would query:
        # https://waterdata.usgs.gov/blog/api-flood-impact/

        impacts = pd.DataFrame({
            "impact_id": [],
            "date": [],
            "location": [],
            "severity": [],
            "distance_to_rail_mi": []
        })

        return impacts

    def persist_to_postgres(
        self,
        df: pd.DataFrame,
        table_name: str,
        engine_url: str
    ) -> None:
        """
        Persist streamgage data to PostgreSQL/PostGIS.

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

    def ingest_weekly_update(self, engine_url: str) -> None:
        """
        Fetch latest week of streamgage data and store to database.

        This method is designed to be called by automated scheduler
        (cron/Airflow) for weekly data updates.

        Args:
            engine_url: PostgreSQL connection string
        """

        end_date = date.today()
        start_date = end_date - timedelta(days=7)

        all_data = []

        for site_no in CORRIDOR_GAGES.keys():
            try:
                ts = self.get_time_series(site_no, start_date, end_date)
                ts["site_no"] = site_no
                ts["site_name"] = CORRIDOR_GAGES[site_no]["name"]
                all_data.append(ts)
            except Exception as e:
                print(f"Warning: Failed to fetch {site_no}: {e}")
                continue

        if all_data:
            combined = pd.concat(all_data, ignore_index=True)
            self.persist_to_postgres(combined, "usgs_streamgage_daily", engine_url)
