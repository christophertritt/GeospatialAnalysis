"""NOAA Climate Data Online (CDO) integration utilities."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Dict, Iterable, List, Optional, Tuple

import pandas as pd
import requests
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

CDO_BASE_URL = "https://www.ncdc.noaa.gov/cdo-web/api/v2"
SEA_TAC_STATION = "GHCND:USW00024233"


@dataclass(frozen=True)
class WetSeasonTotals:
	"""Dataclass summarizing wet-season precipitation totals."""

	year: int
	total_precip_in: float
	storm_days: int
	season_start: date
	season_end: date


class NOAACDOClient:
	"""Simple NOAA CDO REST client focused on precipitation analysis."""

	def __init__(
		self,
		token: str,
		station_id: str = SEA_TAC_STATION,
		base_url: str = CDO_BASE_URL,
		session: Optional[requests.Session] = None,
	) -> None:
		"""Initialize the NOAA CDO client."""

		self.station_id = station_id
		self.base_url = base_url.rstrip("/")
		self.session = session or requests.Session()
		self.session.headers.update({"token": token})

	def _request(self, endpoint: str, params: Dict[str, str]) -> Dict:
		"""Execute a GET request against the CDO API."""

		url = f"{self.base_url}/{endpoint.lstrip('/')}"
		response = self.session.get(url, params=params, timeout=60)
		response.raise_for_status()
		return response.json()

	def get_daily_precip(self, start_date: date, end_date: date) -> pd.DataFrame:
		"""Fetch daily precipitation totals (PRCP) for Sea-Tac."""

		payload = {
			"datasetid": "GHCND",
			"datatypeid": "PRCP",
			"stationid": self.station_id,
			"startdate": start_date.isoformat(),
			"enddate": end_date.isoformat(),
			"units": "standard",
			"limit": 1000,
		}
		results: List[Dict] = []
		offset = 1
		while True:
			payload["offset"] = offset
			data = self._request("data", payload)
			events = data.get("results", [])
			results.extend(events)
			if len(events) < payload["limit"]:
				break
			offset += payload["limit"]

		if not results:
			return pd.DataFrame(columns=["date", "precip_in"])

		df = pd.DataFrame(results)
		df["date"] = pd.to_datetime(df["date"]).dt.date
		df["precip_in"] = df["value"].astype(float) / 10.0 / 2.54  # tenths of mm -> inches
		return df[["date", "precip_in"]]

	def identify_extreme_events(self, precip_df: pd.DataFrame, threshold_in: float = 2.0) -> pd.DataFrame:
		"""Return days exceeding the extreme precipitation threshold."""

		extremes = precip_df[precip_df["precip_in"] >= threshold_in].copy()
		extremes["event_label"] = ">=2 inch day"
		return extremes

	def calculate_wet_season_totals(self, water_year: int) -> WetSeasonTotals:
		"""Aggregate October–April precipitation for a given water year."""

		start = date(water_year - 1, 10, 1)
		end = date(water_year, 4, 30)
		season = self.get_daily_precip(start, end)
		return WetSeasonTotals(
			year=water_year,
			total_precip_in=float(season["precip_in"].sum()),
			storm_days=int((season["precip_in"] >= 0.5).sum()),
			season_start=start,
			season_end=end,
		)

	def extreme_event_frequency_by_decade(self, decades: Iterable[Tuple[int, int]]) -> pd.DataFrame:
		"""Summarize extreme precipitation frequency for each decade window."""

		records: List[Dict[str, float]] = []
		for start_year, end_year in decades:
			precip = self.get_daily_precip(date(start_year, 1, 1), date(end_year, 12, 31))
			extremes = self.identify_extreme_events(precip)
			records.append(
				{
					"decade": f"{start_year}s",
					"extreme_events": len(extremes),
					"total_inches": precip["precip_in"].sum(),
				}
			)
		return pd.DataFrame(records)

	def persist_to_postgres(self, df: pd.DataFrame, table_name: str, engine_url: str) -> None:
		"""Persist precipitation metrics to PostgreSQL/PostGIS."""

		if df.empty:
			return
		engine: Engine = create_engine(engine_url, future=True)
		try:
			df.to_sql(table_name, engine, if_exists="append", index=False)
		except SQLAlchemyError as exc:
			raise RuntimeError(f"Failed to insert records into {table_name}: {exc}") from exc

	def ingest_monthly_update(self, reference_month: date, engine_url: str) -> None:
		"""Fetch the previous month's precipitation and store it."""

		month_start = date(reference_month.year, reference_month.month, 1)
		if reference_month.month == 12:
			month_end = date(reference_month.year, 12, 31)
		else:
			month_end = date(reference_month.year, reference_month.month + 1, 1) - pd.Timedelta(days=1)
		precip = self.get_daily_precip(month_start, month_end)
		precip["month"] = reference_month.strftime("%Y-%m")
		self.persist_to_postgres(precip, "noaa_precip_daily", engine_url)
