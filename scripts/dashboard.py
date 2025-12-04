"""Streamlit dashboard for the Seattle-Tacoma corridor alignment study."""

from __future__ import annotations

import io
import math
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import geopandas as gpd
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import folium
from folium import Choropleth, FeatureGroup, LayerControl, Map
from folium.features import GeoJson, GeoJsonTooltip
from streamlit_folium import st_folium

try:
	from utils.statistics import (
		assign_quadrant,
		calculate_cn_from_imperviousness,
		calculate_gap_index,
		calculate_runoff_depth,
		classify_vulnerability,
	)
except ImportError:  # Streamlit executes this file directly
	sys.path.append(str(Path(__file__).resolve().parent))
	from utils.statistics import (  # type: ignore  # pylint: disable=import-error
		assign_quadrant,
		calculate_cn_from_imperviousness,
		calculate_gap_index,
		calculate_runoff_depth,
		classify_vulnerability,
	)


# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
DATA_DIR = ROOT_DIR / "data"

SEGMENT_CANDIDATES = [
	Path("data/outputs/analysis_segments.gpkg"),
	Path("data/outputs_final/analysis_segments.gpkg"),
	Path("data/outputs/analysis_segments.shp"),
]
RAIL_LINE_CANDIDATES = [
	Path("data/raw/rail/corridor.shp"),
	Path("data/raw/rail/corridor.gpkg"),
	Path("data/raw/rail/osm_rail.gpkg"),
	Path("data/raw/rail/osm_rail.shp"),
]
INFRASTRUCTURE_CANDIDATES = [
	Path("data/processed/infrastructure_combined.gpkg"),
	Path("data/processed/infrastructure_combined.shp"),
	Path("data/raw/infrastructure/permeable_pavement.gpkg"),
]
STATION_CANDIDATES = [
	Path("data/raw/rail/sounder_stations.geojson"),
	Path("data/raw/rail/sounder_stations.gpkg"),
	Path("data/processed/rail/stations.gpkg"),
]
FREIGHT_CANDIDATES = [Path("data/raw/rail/freight_nodes.geojson"), Path("data/processed/rail/freight_nodes.gpkg")]
PRIORITY_THRESHOLD_VULN = 7.0
PRIORITY_THRESHOLD_DENSITY = 100.0  # sq ft / acre

BUFFER_OPTIONS = {
	"Station influence (100 m)": 100,
	"Core corridor (250 m)": 250,
	"Watershed context (500 m)": 500,
}
JURISDICTIONS = [
	"Seattle",
	"Tukwila",
	"Kent",
	"Auburn",
	"Sumner",
	"Puyallup",
	"Fife",
	"Tacoma",
	"King County (Unincorporated)",
]

WEIGHT_DEFAULTS = {
	"elevation": 0.25,
	"slope": 0.15,
	"soil": 0.20,
	"impervious": 0.25,
	"drainage": 0.15,
}

COMPONENT_COLUMNS = {
	"elevation": ["elevation_position_index", "elevation_position", "elevation_rank", "elevation_mean"],
	"slope": ["slope_mean", "slope_pct", "slope"],
	"soil": ["soil_drainage_score", "soil_hsg_score", "soil_infiltration", "soil_hydgrp_score"],
	"impervious": ["imperv_mean", "impervious_pct"],
	"drainage": ["drainage_distance_m", "distance_to_drainage", "drainage_proximity_m"],
}

COMPONENT_DIRECTION = {
	"elevation": "inverse",
	"slope": "inverse",
	"soil": "inverse",
	"impervious": "positive",
	"drainage": "positive",
}

RUNOFF_EVENTS = ["25-year", "50-year", "100-year"]
DESIGN_STORMS = {
	"2-year": 2.2,
	"5-year": 2.6,
	"10-year": 2.9,
	"25-year": 3.4,
	"50-year": 3.8,
	"100-year": 4.3,
}


# -----------------------------------------------------------------------------
# Streamlit setup
# -----------------------------------------------------------------------------

st.set_page_config(
	page_title="Seattle-Tacoma Corridor Resilience",
	layout="wide",
	initial_sidebar_state="expanded",
)

st.markdown(
	"""
	<style>
	:root {
		color-scheme: dark;
	}
	.metric-card {
		background-color: rgba(20, 20, 20, 0.7);
		padding: 0.75rem 1rem;
		border-radius: 0.75rem;
		border: 1px solid rgba(255, 255, 255, 0.08);
		margin-bottom: 0.5rem;
	}
	section.main > div {
		padding-top: 0.5rem;
	}
	.stTabs [role="tab"] {
		padding: 0.5rem 1.5rem;
		font-weight: 600;
	}
	</style>
	""",
	unsafe_allow_html=True,
)

st.title("🚄 Seattle–Tacoma Rail Resilience Dashboard")
st.caption(
	"Five analytical lenses to evaluate permeable pavement alignment with flood vulnerability "
	"along the 38.7-mile Seattle–Tacoma rail corridor."
)

# Load and display summary statistics if available
summary_stats_path = DATA_DIR / "dashboard_ready" / "summary_statistics.json"
if summary_stats_path.exists():
	try:
		import json
		with open(summary_stats_path, 'r') as f:
			stats = json.load(f)

		# Display key metrics at the top
		col1, col2, col3, col4 = st.columns(4)

		with col1:
			segment_count = stats.get("data_availability", {}).get("segment_count", 0)
			st.metric("Analysis Segments", f"{segment_count:,}")

		with col2:
			corridor_length = stats.get("corridor_metrics", {}).get("total_length_miles", 0)
			st.metric("Corridor Length", f"{corridor_length:.1f} mi")

		with col3:
			mean_vuln = stats.get("vulnerability_summary", {}).get("mean_vulnerability", 0)
			st.metric("Mean Vulnerability", f"{mean_vuln:.2f}/10")

		with col4:
			infra_count = stats.get("data_availability", {}).get("infrastructure_count", 0)
			st.metric("GSI Facilities", f"{infra_count:,}")

		# Expandable details
		with st.expander("📊 Quick Insights", expanded=False):
			st.markdown("### Data Coverage")

			col_a, col_b = st.columns(2)

			with col_a:
				if "vulnerability_summary" in stats and stats["vulnerability_summary"]:
					high_vuln_pct = stats["vulnerability_summary"].get("high_vulnerability_percent", 0)
					st.markdown(f"""
					**Flood Vulnerability**
					- {high_vuln_pct:.1f}% of segments are high vulnerability (>7.0)
					- Maximum vulnerability: {stats["vulnerability_summary"].get("max_vulnerability", 0):.2f}
					""")

			with col_b:
				if "infrastructure_summary" in stats and stats["infrastructure_summary"]:
					coverage_pct = stats["infrastructure_summary"].get("coverage_percent", 0)
					total_area = stats["infrastructure_summary"].get("total_area_acres", 0)
					st.markdown(f"""
					**Green Infrastructure**
					- {coverage_pct:.1f}% of segments have GSI
					- Total area: {total_area:.1f} acres
					""")

			if "spatial_statistics" in stats and stats["spatial_statistics"]:
				hot_spots_99 = stats["spatial_statistics"].get("hot_spots_99", 0)
				hot_spots_95 = stats["spatial_statistics"].get("hot_spots_95", 0)
				if hot_spots_99 > 0 or hot_spots_95 > 0:
					st.markdown(f"""
					### Spatial Analysis
					- **Hot spots identified:** {hot_spots_99} (99% confidence), {hot_spots_95} (95% confidence)
					- These are clusters of high flood vulnerability requiring priority attention
					""")

			if "gap_analysis" in stats:
				high_gap_pct = stats["gap_analysis"].get("high_gap_percent", 0)
				st.markdown(f"""
				### Priority Gaps
				- **{high_gap_pct:.1f}%** of segments are high-vulnerability with low infrastructure
				- These areas should be targeted for new green infrastructure investments
				""")

		st.markdown("---")

	except Exception as e:
		# Silently fail if stats can't be loaded
		pass


# -----------------------------------------------------------------------------
# Utility functions
# -----------------------------------------------------------------------------

def find_existing_path(candidates: Sequence[Path]) -> Optional[Path]:
	"""Return the first existing path from a list of relative candidates."""

	for rel_path in candidates:
		abs_path = ROOT_DIR / rel_path
		if abs_path.exists():
			return abs_path
	return None


def normalize_series(series: pd.Series, invert: bool = False) -> pd.Series:
	"""Min-max normalize to 0-10 scale with optional inversion."""

	clean = series.astype(float).replace([np.inf, -np.inf], np.nan)
	min_val = clean.min()
	max_val = clean.max()
	if pd.isna(min_val) or pd.isna(max_val) or math.isclose(float(min_val), float(max_val)):
		norm = pd.Series(np.zeros(len(clean)), index=clean.index)
	else:
		norm = (clean - min_val) / (max_val - min_val)
	if invert:
		norm = 1 - norm
	return (norm * 10).fillna(5.0)


def ensure_jurisdiction_column(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
	"""Guarantee the presence of a jurisdiction column."""

	if "jurisdiction" not in gdf.columns:
		gdf["jurisdiction"] = "Unknown"
	gdf.loc[gdf["jurisdiction"].isin([None, "", np.nan]), "jurisdiction"] = "Unknown"
	return gdf


def assign_temporal_period(ts: Optional[pd.Timestamp]) -> str:
	"""Bucket installation dates into study cohorts."""

	if pd.isna(ts):
		return "Unknown"
	year = ts.year
	if 1995 <= year <= 2010:
		return "1995-2010 Early"
	if 2011 <= year <= 2014:
		return "2011-2014 Transition"
	if 2015 <= year <= 2024:
		return "2015-2024 Recent"
	if year > 2024:
		return "Future"
	return "Pre-1995"


def adjust_cn_for_gsi(curve_number: float, density_sqft_per_acre: float) -> float:
	"""Reduce the curve number based on infrastructure density."""

	reduction = (density_sqft_per_acre / 1000.0) * 2.0
	adjusted = max(curve_number - reduction, 35.0)
	return adjusted


def serialize_gdf(gdf: gpd.GeoDataFrame) -> str:
	"""Serialize a GeoDataFrame without geometry for caching helpers."""

	return gdf.drop(columns="geometry").to_json(orient="records")


def download_button(label: str, df: pd.DataFrame, filename: str) -> None:
	"""Render a CSV download button if data exists."""

	if df.empty:
		st.info("No data available for download.")
		return
	csv_bytes = df.to_csv(index=False).encode("utf-8")
	st.download_button(label, data=csv_bytes, file_name=filename, mime="text/csv")


# -----------------------------------------------------------------------------
# Cached data preparation
# -----------------------------------------------------------------------------


@st.cache_data(ttl=3600, show_spinner="Loading analysis segments...")
def load_segment_frame() -> Optional[gpd.GeoDataFrame]:
	"""Load the master segment GeoDataFrame from disk."""

	dataset_path = find_existing_path(SEGMENT_CANDIDATES)
	if dataset_path is None:
		return None

	try:
		gdf = gpd.read_file(dataset_path, layer="segments")
	except (ValueError, OSError):
		gdf = gpd.read_file(dataset_path)

	if gdf.crs is None:
		gdf.set_crs("EPSG:4326", inplace=True)

	gdf = gdf.to_crs(4326)
	if "segment_id" not in gdf.columns:
		gdf["segment_id"] = np.arange(1, len(gdf) + 1)

	# Geometry simplification for map rendering performance
	gdf["geometry"] = gdf.geometry.simplify(0.00008, preserve_topology=True)

	gdf = ensure_jurisdiction_column(gdf)

	proj = gdf.to_crs(2927)
	gdf["buffer_area_sqft"] = proj.geometry.area
	gdf["buffer_area_acres"] = gdf["buffer_area_sqft"] / 43560.0
	gdf["length_miles"] = proj.geometry.length / 5280.0

	if "buffer_distance_m" not in gdf.columns:
		gdf["buffer_distance_m"] = 250

	if "installation_date" in gdf.columns:
		gdf["installation_date"] = pd.to_datetime(gdf["installation_date"], errors="coerce")
	else:
		gdf["installation_date"] = pd.NaT

	gdf["installation_year"] = gdf["installation_date"].dt.year
	gdf["temporal_period"] = gdf["installation_date"].apply(assign_temporal_period)

	if "density_sqft_per_acre" not in gdf.columns:
		gdf["density_sqft_per_acre"] = 0.0

	return gdf


@st.cache_data(ttl=3600)
def load_corridor_lines() -> Optional[gpd.GeoDataFrame]:
	"""Load rail corridor centerlines for reference."""

	path = find_existing_path(RAIL_LINE_CANDIDATES)
	if not path:
		return None
	gdf = gpd.read_file(path)
	if gdf.crs is None:
		gdf.set_crs(4326, inplace=True)
	return gdf.to_crs(4326)


@st.cache_data(ttl=3600)
def load_infrastructure_raw() -> Optional[gpd.GeoDataFrame]:
	"""Load the combined infrastructure dataset for spatial joins."""

	path = find_existing_path(INFRASTRUCTURE_CANDIDATES)
	if not path:
		return None
	gdf = gpd.read_file(path)
	if gdf.crs is None:
		gdf.set_crs(4326, inplace=True)
	return gdf.to_crs(4326)


@st.cache_data(ttl=3600)
def load_station_layer() -> Optional[gpd.GeoDataFrame]:
	"""Load Sounder stations and freight nodes."""

	station_path = find_existing_path(STATION_CANDIDATES)
	freight_path = find_existing_path(FREIGHT_CANDIDATES)
	frames: List[gpd.GeoDataFrame] = []
	for option, label in [(station_path, "Sounder Station"), (freight_path, "Freight Facility")]:
		if option:
			gdf = gpd.read_file(option)
			if gdf.crs is None:
				gdf.set_crs(4326, inplace=True)
			gdf = gdf.to_crs(4326)
			gdf["marker_type"] = label
			frames.append(gdf)
	if not frames:
		return None
	return pd.concat(frames, ignore_index=True)


@st.cache_data(ttl=3600)
def load_budget_reference() -> Optional[pd.DataFrame]:
	"""Load jurisdictional capital improvement budgets if present."""

	path = ROOT_DIR / "data/reference/jurisdiction_budgets.csv"
	if path.exists():
		df = pd.read_csv(path)
		return df
	return None


@st.cache_data(ttl=3600)
def get_buffered_segments(buffer_distance: int) -> Optional[gpd.GeoDataFrame]:
	"""Return segments for the requested buffer distance."""

	base = load_segment_frame()
	if base is None:
		return None

	if "buffer_distance_m" in base.columns and buffer_distance in base["buffer_distance_m"].unique():
		return base[base["buffer_distance_m"] == buffer_distance].copy()

	reference = base["buffer_distance_m"].mode().iloc[0]
	delta_feet = (buffer_distance - reference) * 3.28084
	proj = base.to_crs(2927).copy()
	proj["geometry"] = proj.geometry.buffer(delta_feet)
	proj["buffer_distance_m"] = buffer_distance
	proj = proj[~proj.geometry.is_empty]
	return proj.to_crs(4326)


@st.cache_data(ttl=3600, show_spinner="Computing infrastructure overlays...")
def compute_infrastructure_overlay(buffer_distance: int) -> Optional[pd.DataFrame]:
	"""Spatially join infrastructure features to segments and aggregate metrics."""

	segments = get_buffered_segments(buffer_distance)
	infra = load_infrastructure_raw()
	if segments is None or infra is None:
		return None

	seg_proj = segments.to_crs(2927)
	infra_proj = infra.to_crs(2927)

	join = gpd.sjoin(
		infra_proj,
		seg_proj[["segment_id", "geometry"]],
		how="inner",
		predicate="intersects",
	)

	area_col = None
	for candidate in ["AreaSqFt", "area_sqft", "AREA_SQFT", "area", "FacilitySQFT"]:
		if candidate in join.columns:
			area_col = candidate
			break

	if area_col is None:
		join["_area_sqft"] = 0.0
		area_col = "_area_sqft"

	date_col = None
	for candidate in ["installation_date", "InstallDate", "install_dt", "InstallYear"]:
		if candidate in join.columns:
			date_col = candidate
			break

	if date_col:
		join["_install_date"] = pd.to_datetime(join[date_col], errors="coerce")

	summary = join.groupby("segment_id").agg(
		facility_count=(join.columns[0], "count"),
		total_area_sqft=(area_col, "sum"),
	)

	if "_install_date" in join.columns:
		date_stats = join.groupby("segment_id")["_install_date"].agg(["min", "max"])
		date_stats.columns = ["first_install_date", "recent_install_date"]
		summary = summary.join(date_stats, how="left")

	summary.reset_index(inplace=True)

	summary["facility_count"] = summary["facility_count"].fillna(0)
	summary["total_area_sqft"] = summary["total_area_sqft"].fillna(0)
	summary["facility_count"] = summary["facility_count"].astype(int)
	return summary


@st.cache_data(ttl=900, show_spinner="Recomputing vulnerability index...")
def apply_weighted_vulnerability(buffer_distance: int, weight_tuple: Tuple[Tuple[str, float], ...]) -> Optional[gpd.GeoDataFrame]:
	"""Apply custom vulnerability weights and merge infrastructure metrics."""

	segments = get_buffered_segments(buffer_distance)
	if segments is None:
		return None
	weights = dict(weight_tuple)

	overlay = compute_infrastructure_overlay(buffer_distance)
	if overlay is not None:
		segments = segments.merge(overlay, on="segment_id", how="left")
		# Ensure columns exist before accessing them
		if "facility_count" in segments.columns:
			segments["facility_count"] = segments["facility_count"].fillna(0)
		else:
			segments["facility_count"] = 0

		if "total_area_sqft" in segments.columns:
			segments["total_area_sqft"] = segments["total_area_sqft"].fillna(0)
		else:
			segments["total_area_sqft"] = 0

		for col in ["first_install_date", "recent_install_date"]:
			if col in segments.columns:
				segments[col] = pd.to_datetime(segments[col], errors="coerce")

		if "first_install_date" in segments.columns and "installation_date" in segments.columns:
			segments.loc[segments["installation_date"].isna(), "installation_date"] = segments["first_install_date"]
	else:
		# No overlay data - initialize columns
		if "facility_count" not in segments.columns:
			segments["facility_count"] = 0
		else:
			segments["facility_count"] = segments["facility_count"].fillna(0)

		if "total_area_sqft" not in segments.columns:
			segments["total_area_sqft"] = 0
		else:
			segments["total_area_sqft"] = segments["total_area_sqft"].fillna(0)

	segments["installation_year"] = segments["installation_date"].dt.year
	segments["temporal_period"] = segments["installation_date"].apply(assign_temporal_period)

	# Check if we can compute weighted vulnerability from components
	has_any_components = False
	for component, columns in COMPONENT_COLUMNS.items():
		col = next((c for c in columns if c in segments.columns), None)
		if col is None:
			segments[f"comp_{component}"] = pd.Series(np.full(len(segments), 5.0), index=segments.index)
		else:
			has_any_components = True
			invert = COMPONENT_DIRECTION.get(component) == "inverse"
			segments[f"comp_{component}"] = normalize_series(segments[col], invert=invert)

	# If we have component data, compute weighted vulnerability
	# Otherwise, use vuln_mean as fallback if it exists
	if has_any_components:
		composite = sum(weights[key] * segments[f"comp_{key}"] for key in weights)
		segments["vuln_weighted"] = composite
	elif "vuln_mean" in segments.columns:
		segments["vuln_weighted"] = segments["vuln_mean"]
	else:
		# Last resort: create default vulnerability scores
		segments["vuln_weighted"] = 5.0

	if "vuln_class" not in segments.columns:
		segments["vuln_class"] = segments["vuln_weighted"].apply(classify_vulnerability)

	if "density_sqft_per_acre" not in segments.columns:
		segments["density_sqft_per_acre"] = 0.0

	segments["gap_index"] = segments.apply(
		lambda row: calculate_gap_index(row["vuln_weighted"], row["density_sqft_per_acre"]),
		axis=1,
	)

	density_median = segments["density_sqft_per_acre"].median()
	vuln_median = segments["vuln_weighted"].median()
	segments["quadrant"] = segments.apply(
		lambda row: assign_quadrant(row["vuln_weighted"], row["density_sqft_per_acre"], vuln_median, density_median),
		axis=1,
	)

	total_infra_sqft = segments["total_area_sqft"].fillna(segments["density_sqft_per_acre"] * segments["buffer_area_acres"]).sum()
	allocation = segments["vuln_weighted"] * segments["buffer_area_acres"]
	if allocation.sum() > 0:
		allocation = allocation / allocation.sum()
		segments["optimized_sqft"] = allocation * total_infra_sqft
		segments["optimized_density"] = segments["optimized_sqft"] / segments["buffer_area_acres"].replace(0, np.nan)
		segments["optimized_density"].fillna(0, inplace=True)
	else:
		segments["optimized_density"] = segments["density_sqft_per_acre"]

	segments["priority_gap"] = (
		(segments["vuln_weighted"] >= PRIORITY_THRESHOLD_VULN)
		& (segments["density_sqft_per_acre"] < PRIORITY_THRESHOLD_DENSITY)
	)

	return segments


@st.cache_data(ttl=600, show_spinner="Applying filters...")
def filter_segments(
	buffer_distance: int,
	weight_tuple: Tuple[Tuple[str, float], ...],
	jurisdictions: Tuple[str, ...],
	date_range: Tuple[str, str],
) -> Optional[gpd.GeoDataFrame]:
	"""Filter the dataset by jurisdiction and installation date range."""

	segments = apply_weighted_vulnerability(buffer_distance, weight_tuple)
	if segments is None:
		return None

	if jurisdictions:
		segments = segments[segments["jurisdiction"].isin(jurisdictions)]

	start = pd.to_datetime(date_range[0])
	end = pd.to_datetime(date_range[1])
	if "installation_date" in segments.columns:
		mask = segments["installation_date"].isna() | (
			(segments["installation_date"] >= start) & (segments["installation_date"] <= end)
		)
		segments = segments[mask]

	segments = segments.copy()
	segments["installation_year"] = segments["installation_date"].dt.year
	segments["temporal_period"] = segments["installation_date"].apply(assign_temporal_period)
	return segments


@st.cache_data(ttl=600, show_spinner="Computing SCS runoff scenarios...")
def compute_runoff_scenarios(serialized_segments: str, events: Tuple[str, ...]) -> Dict[str, pd.DataFrame]:
	"""Derive runoff volumes for baseline and optimization scenarios."""

	if not serialized_segments:
		return {"segments": pd.DataFrame(), "summary": pd.DataFrame()}

	df = pd.read_json(io.StringIO(serialized_segments))
	if df.empty:
		return {"segments": pd.DataFrame(), "summary": pd.DataFrame()}

	if "buffer_area_acres" not in df.columns:
		df["buffer_area_acres"] = 0.0

	if "density_sqft_per_acre" not in df.columns:
		df["density_sqft_per_acre"] = 0.0

	if "optimized_density" not in df.columns:
		df["optimized_density"] = df["density_sqft_per_acre"]

	if "priority_gap" not in df.columns:
		df["priority_gap"] = False

	if "vuln_weighted" not in df.columns:
		df["vuln_weighted"] = 5.0

	df["cn_current"] = df.get("cn_current", np.nan)
	missing_cn = df["cn_current"].isna()
	if missing_cn.any():
		df.loc[missing_cn, "cn_current"] = df.loc[missing_cn, "imperv_mean"].apply(
			lambda x: calculate_cn_from_imperviousness(x or 0, "C")
		)

	if "cn_with_gsi" not in df.columns:
		df["cn_with_gsi"] = df.apply(
			lambda row: adjust_cn_for_gsi(row["cn_current"], row["density_sqft_per_acre"]),
			axis=1,
		)

	df["cn_optimized"] = df.apply(
		lambda row: adjust_cn_for_gsi(row["cn_current"], row["optimized_density"]),
		axis=1,
	)

	df["cn_gap_invest"] = df.apply(
		lambda row: adjust_cn_for_gsi(
			row["cn_current"], row["density_sqft_per_acre"] + (250 if row["priority_gap"] else 50)
		),
		axis=1,
	)

	df["cn_combo"] = (df["cn_optimized"] + df["cn_gap_invest"]) / 2

	summaries: List[Dict[str, float]] = []
	scenario_map = {
		"Baseline": "cn_with_gsi",
		"Scenario 1 – Redistribute": "cn_optimized",
		"Scenario 2 – Gap Investments": "cn_gap_invest",
		"Scenario 3 – Combined": "cn_combo",
	}

	for event in events:
		precipitation = DESIGN_STORMS.get(event)
		if precipitation is None:
			continue
		for scenario_name, cn_col in scenario_map.items():
			depth_col = f"runoff_{scenario_name}_{event}".replace(" ", "_")
			volume_col = f"volume_{scenario_name}_{event}".replace(" ", "_")
			df[depth_col] = df[cn_col].apply(lambda cn: calculate_runoff_depth(precipitation, cn))
			df[volume_col] = df[depth_col] / 12.0 * df["buffer_area_acres"].fillna(0)
			summaries.append(
				{
					"Scenario": scenario_name,
					"Storm": event,
					"Runoff (ac-ft)": df[volume_col].sum(),
				}
			)

	summary_df = pd.DataFrame(summaries)
	return {"segments": df, "summary": summary_df}


# -----------------------------------------------------------------------------
# Sidebar controls
# -----------------------------------------------------------------------------


st.sidebar.header("Settings & Filters")

buffer_label = st.sidebar.selectbox("Buffer Distance", list(BUFFER_OPTIONS.keys()))
buffer_value = BUFFER_OPTIONS[buffer_label]

with st.sidebar.expander("Vulnerability Weight Overrides", expanded=True):
	weight_inputs = {}
	running_total = 0.0
	for key, default in WEIGHT_DEFAULTS.items():
		weight_inputs[key] = st.slider(
			f"{key.title()} weight",
			min_value=0.0,
			max_value=1.0,
			value=float(default),
			step=0.01,
		)
		running_total += weight_inputs[key]
	if not math.isclose(running_total, 1.0, abs_tol=0.01):
		st.warning("Weights must total 1.0. Current total: {:.2f}".format(running_total))
	normalized_weights = {k: v / running_total for k, v in weight_inputs.items()} if running_total else WEIGHT_DEFAULTS

jurisdiction_selection = st.sidebar.multiselect(
	"Jurisdictions",
	options=JURISDICTIONS,
	default=JURISDICTIONS,
)

date_range_input = st.sidebar.date_input(
	"Installation Date Range",
	value=(date(1995, 1, 1), date(2024, 12, 31)),
	min_value=date(1990, 1, 1),
	max_value=date(2030, 12, 31),
)

if isinstance(date_range_input, tuple) and len(date_range_input) == 2:
	date_range_strings = (date_range_input[0].isoformat(), date_range_input[1].isoformat())
else:
	date_range_strings = ("1995-01-01", "2024-12-31")


# -----------------------------------------------------------------------------
# Data preparation
# -----------------------------------------------------------------------------


weights_tuple = tuple(sorted(normalized_weights.items()))
jurisdiction_tuple = tuple(sorted(jurisdiction_selection))

filtered_segments = filter_segments(
	buffer_value,
	weights_tuple,
	jurisdiction_tuple,
	date_range_strings,
)

if filtered_segments is None or filtered_segments.empty:
	st.error("No analysis segments available.")
	st.markdown("""
	### Getting Started

	The dashboard requires analysis segments to display data. Here's how to generate them:

	#### Option 1: Generate Dashboard Data (Recommended)
	```bash
	python scripts/generate_dashboard_data.py
	```
	This will prepare all necessary data and create summary statistics.

	#### Option 2: Run Full Geospatial Analysis
	```bash
	python scripts/geospatial_analysis.py
	```
	This will process raw data and generate complete analysis segments.

	#### Need Help?
	- See [QUICKSTART.md](QUICKSTART.md) for a 5-minute setup guide
	- See [STATUS_COMPLETE.md](STATUS_COMPLETE.md) for repository status
	- See [docs/API_SETUP_GUIDE.md](docs/API_SETUP_GUIDE.md) for API configuration

	#### Data Requirements
	The dashboard looks for analysis segments in these locations:
	""")

	for path in SEGMENT_CANDIDATES:
		exists = "✓" if path.exists() else "✗"
		st.markdown(f"- {exists} `{path}`")

	st.info("Once you've generated the data, refresh this page to see the analysis.")
	st.stop()

priority_segments = filtered_segments[filtered_segments["priority_gap"]]

rail_lines = load_corridor_lines()
station_layer = load_station_layer()
budget_reference = load_budget_reference()

total_corridor_length = (
	rail_lines.to_crs(2927).length.sum() / 5280.0 if rail_lines is not None else filtered_segments["length_miles"].sum()
)

high_vuln = filtered_segments[filtered_segments["vuln_weighted"] >= PRIORITY_THRESHOLD_VULN]
high_vuln_pct = (len(high_vuln) / len(filtered_segments)) * 100 if len(filtered_segments) else 0

coverage_by_jurisdiction = (
	filtered_segments.groupby("jurisdiction")
	.agg(
		segments=("segment_id", "count"),
		mean_density=("density_sqft_per_acre", "mean"),
		mean_vulnerability=("vuln_weighted", "mean"),
		coverage_pct=("density_sqft_per_acre", lambda s: (s > 0).mean() * 100),
	)
	.reset_index()
)

gap_share = (
	priority_segments.groupby("jurisdiction").size().div(filtered_segments.groupby("jurisdiction").size())
).fillna(0) * 100
coverage_by_jurisdiction["priority_gap_pct"] = coverage_by_jurisdiction["jurisdiction"].map(gap_share).fillna(0)


# -----------------------------------------------------------------------------
# Visualization helpers
# -----------------------------------------------------------------------------


def build_multilayer_map(data: gpd.GeoDataFrame) -> Map:
	"""Create the multi-layer Folium visualization requested in Task 2."""

	bounds = data.total_bounds
	center = [(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2]
	fmap = Map(location=center, zoom_start=10, tiles="CartoDB dark_matter", prefer_canvas=True)

	# Layer 1: Vulnerability choropleth
	Choropleth(
		geo_data=data,
		data=data,
		columns=["segment_id", "vuln_weighted"],
		key_on="feature.properties.segment_id",
		fill_color="RdYlBu_r",
		fill_opacity=0.7,
		line_opacity=0.3,
		legend_name="Flood Vulnerability (0-10)",
		bins=[0, 2, 4, 6, 8, 10],
		name="Flood Vulnerability",
	).add_to(fmap)

	tooltip_fields = [
		"segment_id",
		"jurisdiction",
		"vuln_weighted",
		"density_sqft_per_acre",
		"gap_index",
	]
	GeoJson(
		data,
		name="Segment Tooltips",
		tooltip=GeoJsonTooltip(fields=[f for f in tooltip_fields if f in data.columns], aliases=tooltip_fields),
		style_function=lambda _x: {"fillColor": "#00000000", "color": "#00000000"},
	).add_to(fmap)

	# Layer 2: Infrastructure density (hidden by default)
	density_group = FeatureGroup(name="Permeable Pavement Density", show=False)
	Choropleth(
		geo_data=data,
		data=data,
		columns=["segment_id", "density_sqft_per_acre"],
		key_on="feature.properties.segment_id",
		fill_color="YlGn",
		fill_opacity=0.55,
		line_opacity=0.1,
		name="Infrastructure Density",
	).add_to(density_group)
	density_group.add_to(fmap)

	# Layer 3: Rail corridor lines
	if rail_lines is not None:
		FeatureGroup(name="Rail Corridor", show=True).add_to(fmap)
		GeoJson(
			rail_lines,
			name="Rail Corridor",
			style_function=lambda _x: {"color": "white", "weight": 3},
			tooltip=GeoJsonTooltip(fields=["name"] if "name" in rail_lines.columns else None),
		).add_to(fmap)

	# Layer 4: Station markers
	if station_layer is not None and not station_layer.empty:
		stations = FeatureGroup(name="Stations & Freight", show=True)
		for _, row in station_layer.iterrows():
			point = row.geometry
			popup_html = f"<b>{row.get('name', 'Facility')}</b><br>Type: {row.get('marker_type', 'Station')}"
			stations.add_child(
				folium.CircleMarker(
					location=(point.y, point.x),
					radius=6,
					color="#f4d35e" if row.get("marker_type") == "Sounder Station" else "#ff0054",
					fill=True,
					fill_opacity=0.9,
					popup=popup_html,
				)
			)
		stations.add_to(fmap)

	# Layer 5: Priority gaps
	if not priority_segments.empty:
		gap_group = FeatureGroup(name="Priority Gap Areas", show=True)
		GeoJson(
			priority_segments,
			name="Priority Gaps",
			style_function=lambda _feat: {"color": "#ff2d00", "weight": 3, "fillColor": "#ff2d00", "fillOpacity": 0.3},
			tooltip=GeoJsonTooltip(fields=["segment_id", "vuln_weighted", "density_sqft_per_acre"]),
		).add_to(gap_group)
		gap_group.add_to(fmap)

	LayerControl(collapsed=False).add_to(fmap)
	return fmap


def build_correlation_scatter(data: gpd.GeoDataFrame) -> go.Figure:
	"""Create the vulnerability vs density scatter plot."""

	if data.empty:
		return go.Figure()

	fig = px.scatter(
		data,
		x="vuln_weighted",
		y="density_sqft_per_acre",
		color="jurisdiction",
		size="length_miles",
		hover_data={"segment_id": True, "imperv_mean": True, "soil_drainage_score": True},
		range_x=[0, 10],
		labels={"vuln_weighted": "Vulnerability (0-10)", "density_sqft_per_acre": "Density (sq ft/ac)"},
		template="plotly_dark",
		title="Correlation between Vulnerability and Permeable Pavement Density",
	)

	if len(data) >= 2:
		coeffs = np.polyfit(data["vuln_weighted"], data["density_sqft_per_acre"], 1)
		trend = np.poly1d(coeffs)
		x_range = np.linspace(0, 10, 50)
		fig.add_trace(
			go.Scatter(
				x=x_range,
				y=trend(x_range),
				mode="lines",
				name="Trend",
				line=dict(color="#ffb703", dash="dash"),
			)
		)

	return fig


# -----------------------------------------------------------------------------
# Tabs and content
# -----------------------------------------------------------------------------


tab_dist, tab_vuln, tab_corr, tab_gaps, tab_runoff = st.tabs(
	[
		"🧱 Infrastructure Distribution",
		"🌧️ Flood Vulnerability",
		"🔗 Correlation & Jurisdictions",
		"⚠️ Priority Gap Targeting",
		"💧 Runoff & Temporal Dynamics",
	]
)


with tab_dist:
	st.subheader("Regional Infrastructure Distribution")
	col_metrics, col_map = st.columns([1, 2])

	with col_metrics:
		st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
		st.metric("Corridor Length", f"{total_corridor_length:.1f} mi")
		st.metric("High-Vulnerability Segments", f"{len(high_vuln)} ({high_vuln_pct:.1f}%)")
		coverage_pct = (filtered_segments["density_sqft_per_acre"] > 0).mean() * 100
		st.metric("Segments with Infrastructure", f"{coverage_pct:.1f}%")
		delta_density = (
			filtered_segments["optimized_density"] - filtered_segments["density_sqft_per_acre"]
		).mean()
		st.metric(
			"Optimization Delta",
			f"{filtered_segments['optimized_density'].mean():.0f} sq ft/ac",
			delta=f"{delta_density:.0f} vs current",
			delta_color="inverse" if delta_density < 0 else "normal",
		)
		st.markdown("</div>", unsafe_allow_html=True)

	with col_map:
		multi_map = build_multilayer_map(filtered_segments)
		st_folium(multi_map, height=520, width=None)

	st.markdown("### Installation Timeline")
	timeline = (
		filtered_segments.dropna(subset=["installation_year"])
		.groupby("installation_year")
		.agg(
			segments=("segment_id", "nunique"),
			added_density=("density_sqft_per_acre", "mean"),
		)
		.reset_index()
	)
	if not timeline.empty:
		fig_timeline = px.bar(
			timeline,
			x="installation_year",
			y="segments",
			color="segments",
			template="plotly_dark",
			labels={"segments": "Segments with Installations"},
			title="Permeable Pavement Installations per Year",
		)
		st.plotly_chart(fig_timeline, use_container_width=True)
	else:
		st.info("No installation dates available for the selected filters.")

	st.markdown("### Export Segment Attributes")
	download_button("Download Filtered Segments", filtered_segments.drop(columns="geometry"), "segments_filtered.csv")


with tab_vuln:
	st.subheader("Flood Vulnerability Components")
	component_cols = [f"comp_{k}" for k in WEIGHT_DEFAULTS.keys()]
	available_components = [c for c in component_cols if c in filtered_segments.columns]
	if available_components:
		melted = filtered_segments.melt(
			id_vars=["segment_id", "jurisdiction"],
			value_vars=available_components,
			var_name="Component",
			value_name="Score",
		)
		melted["Component"] = melted["Component"].str.replace("comp_", "").str.title()
		fig_components = px.box(
			melted,
			x="Component",
			y="Score",
			color="Component",
			template="plotly_dark",
			title="Distribution of Component Scores",
		)
		st.plotly_chart(fig_components, use_container_width=True)
	else:
		st.info("Component columns not available in the dataset.")

	st.markdown("### Vulnerability Summary Table")
	vuln_summary = filtered_segments[["segment_id", "jurisdiction", "vuln_weighted", "vuln_class", "gap_index"]]
	st.dataframe(vuln_summary)
	download_button("Download Vulnerability Summary", vuln_summary, "vulnerability_summary.csv")


with tab_corr:
	st.subheader("Correlation and Jurisdiction Comparisons")
	fig_scatter = build_correlation_scatter(filtered_segments)
	st.plotly_chart(fig_scatter, use_container_width=True)

	st.markdown("### Jurisdictional Comparison")
	jur_chart_data = filtered_segments.groupby("jurisdiction").agg(
		mean_density=("density_sqft_per_acre", "mean"),
		mean_vulnerability=("vuln_weighted", "mean"),
		gap_pct=("priority_gap", "mean"),
	)
	jur_chart_data["gap_pct"] *= 100

	fig_bars = go.Figure()
	fig_bars.add_trace(
		go.Bar(
			x=jur_chart_data.index,
			y=jur_chart_data["mean_density"],
			name="Infrastructure Density",
			marker_color="#2a9d8f",
		)
	)
	fig_bars.add_trace(
		go.Bar(
			x=jur_chart_data.index,
			y=jur_chart_data["mean_vulnerability"] * 100,
			name="Vulnerability (x100)",
			marker_color="#e76f51",
		)
	)
	fig_bars.add_trace(
		go.Bar(
			x=jur_chart_data.index,
			y=jur_chart_data["gap_pct"],
			name="Gap Areas (%)",
			marker_color="#f4a261",
		)
	)
	fig_bars.update_layout(barmode="group", template="plotly_dark", yaxis_title="Value")
	st.plotly_chart(fig_bars, use_container_width=True)

	# Spatial Statistics Section
	st.markdown("### Spatial Autocorrelation Analysis")

	if len(filtered_segments) >= 3:
		try:
			from spatial_clustering import calculate_morans_i, calculate_hot_spots

			# Calculate Moran's I for vulnerability
			morans_result = calculate_morans_i(filtered_segments, "vuln_weighted")

			if morans_result:
				col1, col2, col3 = st.columns(3)

				with col1:
					st.metric(
						"Moran's I",
						f"{morans_result['I']:.3f}",
						help="Measure of spatial autocorrelation. Values > 0 indicate clustering, < 0 indicate dispersion."
					)

				with col2:
					st.metric(
						"Z-Score",
						f"{morans_result['z_score']:.2f}",
						help="Statistical significance. |Z| > 1.96 indicates p < 0.05"
					)

				with col3:
					significance = "✓ Significant" if morans_result['p_value'] < 0.05 else "Not Significant"
					st.metric(
						"P-Value",
						f"{morans_result['p_value']:.4f}",
						delta=significance
					)

				st.info(f"**Interpretation**: {morans_result['interpretation']}")

			# Hot Spot Analysis
			if "gi_star" not in filtered_segments.columns:
				segments_with_hotspots = calculate_hot_spots(filtered_segments, "vuln_weighted")
			else:
				segments_with_hotspots = filtered_segments

			if "hotspot_class" in segments_with_hotspots.columns:
				st.markdown("#### Hot Spot Analysis (Getis-Ord Gi*)")

				hotspot_counts = segments_with_hotspots["hotspot_class"].value_counts()

				fig_hotspots = px.bar(
					x=hotspot_counts.index,
					y=hotspot_counts.values,
					template="plotly_dark",
					labels={"x": "Classification", "y": "Segment Count"},
					title="Distribution of Hot Spots and Cold Spots",
					color=hotspot_counts.values,
					color_continuous_scale="RdYlBu_r"
				)

				st.plotly_chart(fig_hotspots, use_container_width=True)

				# Show hot spots on map
				hot_spots = segments_with_hotspots[segments_with_hotspots["hotspot_class"].str.contains("Hot Spot", na=False)]
				if not hot_spots.empty:
					st.markdown(f"**{len(hot_spots)} high-vulnerability hot spots identified** (clusters of elevated flood risk)")

		except ImportError:
			st.warning("Spatial statistics module not available. Install libpysal and esda packages.")
		except Exception as e:
			st.warning(f"Could not compute spatial statistics: {e}")
	else:
		st.info("Need at least 3 segments for spatial autocorrelation analysis.")

	if budget_reference is not None:
		merged_budget = budget_reference.merge(
			jur_chart_data.reset_index(), left_on="jurisdiction", right_on="jurisdiction", how="left"
		)
		st.markdown("### Capital Improvement Budgets")
		st.dataframe(merged_budget)
		download_button("Download Budget Context", merged_budget, "budget_context.csv")
	else:
		st.info("No capital improvement budget reference file found in data/reference/.")


with tab_gaps:
	st.subheader("Priority Gap Identification")
	if priority_segments.empty:
		st.success("No segments meet the high-vulnerability / low-infrastructure criteria for the current filters.")
	else:
		gap_map = build_multilayer_map(priority_segments)
		st_folium(gap_map, height=480, width=None)
		st.markdown("### Priority Gap Segments")
		st.dataframe(priority_segments[["segment_id", "jurisdiction", "vuln_weighted", "density_sqft_per_acre", "gap_index"]])
		download_button(
			"Download Priority Segments",
			priority_segments.drop(columns="geometry"),
			"priority_segments.csv",
		)


with tab_runoff:
	st.subheader("Runoff Reduction Scenarios")
	runoff_cols = [
		"segment_id",
		"buffer_area_acres",
		"imperv_mean",
		"density_sqft_per_acre",
		"optimized_density",
		"priority_gap",
		"vuln_weighted",
		"cn_current",
		"cn_with_gsi",
	]
	available_runoff_cols = [col for col in runoff_cols if col in filtered_segments.columns]
	runoff_subset = filtered_segments[available_runoff_cols].copy()
	runoff_data = compute_runoff_scenarios(serialize_gdf(runoff_subset), tuple(RUNOFF_EVENTS))

	summary_df = runoff_data.get("summary", pd.DataFrame())
	if not summary_df.empty:
		fig_runoff = px.bar(
			summary_df,
			x="Storm",
			y="Runoff (ac-ft)",
			color="Scenario",
			barmode="group",
			template="plotly_dark",
			title="Runoff Volume Comparison",
		)
		st.plotly_chart(fig_runoff, use_container_width=True)
		download_button("Download Runoff Summary", summary_df, "runoff_summary.csv")
	else:
		st.info("Runoff calculations unavailable because required columns are missing.")

	st.markdown("### Temporal Vulnerability Comparison")
	temporal_view = (
		filtered_segments.groupby("temporal_period").agg(
			segments=("segment_id", "count"),
			mean_vuln=("vuln_weighted", "mean"),
			gap_pct=("priority_gap", "mean"),
		)
	)
	if not temporal_view.empty:
		temporal_view["gap_pct"] *= 100
		fig_temporal = px.scatter(
			temporal_view.reset_index(),
			x="temporal_period",
			y="mean_vuln",
			size="segments",
			color="gap_pct",
			template="plotly_dark",
			title="Temporal Cohort Performance",
			labels={"mean_vuln": "Average Vulnerability", "gap_pct": "Gap %"},
		)
		st.plotly_chart(fig_temporal, use_container_width=True)
	else:
		st.info("Temporal cohorts not available for the selected filters.")


st.markdown("---")
st.caption(
	"Use `python scripts/geospatial_analysis.py` to regenerate the analysis segments and rerun this dashboard."
)

