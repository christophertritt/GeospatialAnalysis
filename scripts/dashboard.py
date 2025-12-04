#!/usr/bin/env python3
"""
Streamlit Dashboard for Seattle-Tacoma Rail Corridor Analysis
Displays interactive and static maps from the geospatial analysis.
"""

import json
from pathlib import Path

import geopandas as gpd
import pandas as pd
import streamlit as st

# Optional imports with graceful fallback
try:
    import folium
    from streamlit_folium import st_folium
    FOLIUM_AVAILABLE = True
except ImportError:
    FOLIUM_AVAILABLE = False

try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"

# Data file paths
SEGMENTS_PATH = DATA_DIR / "outputs" / "analysis_segments.gpkg"
SEGMENTS_PATH_ALT = DATA_DIR / "outputs_final" / "analysis_segments.gpkg"
INFRASTRUCTURE_PATH = DATA_DIR / "outputs" / "infrastructure_processed.gpkg"

# Static image paths
STATIC_MAPS = {
    "Flood Vulnerability": DATA_DIR / "figures" / "maps" / "vulnerability_map.png",
    "Infrastructure Gap Index": DATA_DIR / "figures" / "maps" / "gap_index_map.png",
}

STATIC_CHARTS = {
    "Vulnerability vs Density Correlation": DATA_DIR / "figures" / "charts" / "correlation_plot.png",
    "Quadrant Distribution": DATA_DIR / "figures" / "charts" / "quadrant_distribution.png",
}

# Map column options
MAP_COLUMNS = {
    "Flood Vulnerability Score": "vuln_mean",
    "Infrastructure Density (sq ft/acre)": "density_sqft_per_acre",
    "Gap Index (Priority Areas)": "gap_index",
    "Imperviousness (%)": "imperv_mean",
    "Slope": "slope_mean",
    "Hot Spot Classification": "hotspot_class",
    "LISA Cluster": "lisa_cluster",
    "Curve Number (Current)": "cn_current",
    "Runoff Volume 25-yr (ac-ft)": "volume_current_25-year_acft",
    "Optimized Density": "optimized_density",
    "Facility Count": "facility_count",
}

COLOR_SCALES = {
    "vuln_mean": "RdYlBu_r",
    "density_sqft_per_acre": "YlGn",
    "gap_index": "Reds",
    "imperv_mean": "Greys",
    "slope_mean": "BrBG_r",
    "hotspot_class": "RdYlBu_r",
    "lisa_cluster": "Set1",
    "cn_current": "YlOrRd",
    "volume_current_25-year_acft": "Blues",
    "optimized_density": "Greens",
    "facility_count": "Purples",
}

# -----------------------------------------------------------------------------
# Page Config
# -----------------------------------------------------------------------------

st.set_page_config(
    page_title="Rail Corridor Analysis Dashboard",
    page_icon="🚄",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🚄 Seattle-Tacoma Rail Corridor Analysis")
st.markdown("Interactive exploration of flood vulnerability and green infrastructure alignment")

# -----------------------------------------------------------------------------
# Data Loading
# -----------------------------------------------------------------------------

@st.cache_data(ttl=3600)
def load_segments():
    """Load analysis segments from GeoPackage."""
    path = SEGMENTS_PATH if SEGMENTS_PATH.exists() else SEGMENTS_PATH_ALT
    if not path.exists():
        return None
    
    try:
        gdf = gpd.read_file(path, layer="segments")
    except Exception:
        gdf = gpd.read_file(path)
    
    # Ensure WGS84 for web mapping
    if gdf.crs is not None and gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(4326)
    
    # Simplify geometry for faster rendering
    gdf["geometry"] = gdf.geometry.simplify(0.0001, preserve_topology=True)
    
    return gdf


@st.cache_data(ttl=3600)
def load_infrastructure():
    """Load infrastructure features."""
    if not INFRASTRUCTURE_PATH.exists():
        return None
    
    gdf = gpd.read_file(INFRASTRUCTURE_PATH)
    if gdf.crs is not None and gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(4326)
    
    return gdf


@st.cache_data(ttl=3600)
def load_summary_stats():
    """Load pre-computed summary statistics."""
    stats_path = DATA_DIR / "dashboard_ready" / "summary_statistics.json"
    if stats_path.exists():
        with open(stats_path, "r") as f:
            return json.load(f)
    return None


# Load data
segments = load_segments()
infrastructure = load_infrastructure()
stats = load_summary_stats()

if segments is None:
    st.error("No analysis data found. Please run the analysis pipeline first:")
    st.code("""
python scripts/geospatial_analysis.py \\
    --rail data/raw/rail/corridor.shp \\
    --infrastructure data/raw/infrastructure/permeable_pavement.shp \\
    --imperviousness data/raw/landcover/nlcd_2021_impervious.tif \\
    --output-dir data/outputs
    """)
    st.stop()

# -----------------------------------------------------------------------------
# Sidebar
# -----------------------------------------------------------------------------

st.sidebar.header("🎛️ Map Controls")

# Map type selection
map_display = st.sidebar.selectbox(
    "Select Variable to Map",
    options=list(MAP_COLUMNS.keys()),
    index=0,
)
selected_column = MAP_COLUMNS[map_display]

# Filter options
st.sidebar.markdown("---")
st.sidebar.subheader("Filters")

# Vulnerability filter
vuln_range = st.sidebar.slider(
    "Vulnerability Score Range",
    min_value=0.0,
    max_value=10.0,
    value=(0.0, 10.0),
    step=0.5,
)

# Quadrant filter
if "quadrant" in segments.columns:
    quadrants = segments["quadrant"].dropna().unique().tolist()
    selected_quadrants = st.sidebar.multiselect(
        "Filter by Quadrant",
        options=quadrants,
        default=quadrants,
    )
else:
    selected_quadrants = None

# Hot spot filter
if "hotspot_class" in segments.columns:
    show_hotspots_only = st.sidebar.checkbox("Show Hot Spots Only", value=False)
else:
    show_hotspots_only = False

# Apply filters
filtered = segments.copy()
filtered = filtered[
    (filtered["vuln_mean"] >= vuln_range[0]) & 
    (filtered["vuln_mean"] <= vuln_range[1])
]

if selected_quadrants is not None and "quadrant" in filtered.columns:
    filtered = filtered[filtered["quadrant"].isin(selected_quadrants)]

if show_hotspots_only and "hotspot_class" in filtered.columns:
    filtered = filtered[filtered["hotspot_class"].str.contains("Hot Spot", na=False)]

# -----------------------------------------------------------------------------
# Key Metrics
# -----------------------------------------------------------------------------

st.markdown("---")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Total Segments", f"{len(filtered):,}")

with col2:
    mean_vuln = filtered["vuln_mean"].mean()
    st.metric("Mean Vulnerability", f"{mean_vuln:.2f}")

with col3:
    high_vuln = (filtered["vuln_mean"] >= 7.0).sum()
    st.metric("High Vulnerability", f"{high_vuln:,}")

with col4:
    if "facility_count" in filtered.columns:
        total_facilities = int(filtered["facility_count"].sum())
        st.metric("GSI Facilities", f"{total_facilities:,}")
    else:
        st.metric("GSI Facilities", "N/A")

with col5:
    if "gap_index" in filtered.columns:
        mean_gap = filtered["gap_index"].mean()
        st.metric("Mean Gap Index", f"{mean_gap:.2f}")
    else:
        st.metric("Mean Gap Index", "N/A")

# -----------------------------------------------------------------------------
# Main Content Tabs
# -----------------------------------------------------------------------------

tab_interactive, tab_static, tab_charts, tab_data = st.tabs([
    "🗺️ Interactive Map",
    "📸 Static Maps",
    "📊 Charts & Analysis",
    "📋 Data Table",
])

# -----------------------------------------------------------------------------
# Tab 1: Interactive Map
# -----------------------------------------------------------------------------

with tab_interactive:
    st.subheader(f"Interactive Map: {map_display}")
    
    if FOLIUM_AVAILABLE and len(filtered) > 0:
        bounds = filtered.total_bounds
        center_lat = (bounds[1] + bounds[3]) / 2
        center_lon = (bounds[0] + bounds[2]) / 2
        
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=10,
            tiles="CartoDB positron",
        )
        
        if selected_column in filtered.columns:
            filtered["_map_id"] = filtered.index.astype(str)
            is_categorical = filtered[selected_column].dtype == "object"
            
            if is_categorical:
                folium.GeoJson(
                    filtered,
                    name=map_display,
                    style_function=lambda x: {
                        "fillColor": "#ff7800" if "Hot" in str(x["properties"].get(selected_column, "")) else "#3388ff",
                        "color": "black",
                        "weight": 0.5,
                        "fillOpacity": 0.6,
                    },
                    tooltip=folium.GeoJsonTooltip(
                        fields=["segment_id", selected_column, "vuln_mean", "gap_index"],
                        aliases=["Segment ID", map_display, "Vulnerability", "Gap Index"],
                    ),
                ).add_to(m)
            else:
                folium.Choropleth(
                    geo_data=filtered.__geo_interface__,
                    data=filtered,
                    columns=["_map_id", selected_column],
                    key_on="feature.id",
                    fill_color=COLOR_SCALES.get(selected_column, "YlOrRd"),
                    fill_opacity=0.7,
                    line_opacity=0.3,
                    legend_name=map_display,
                    nan_fill_color="gray",
                ).add_to(m)
                
                folium.GeoJson(
                    filtered,
                    name="Tooltips",
                    style_function=lambda x: {"fillColor": "transparent", "color": "transparent", "weight": 0},
                    tooltip=folium.GeoJsonTooltip(
                        fields=["segment_id", "vuln_mean", "density_sqft_per_acre", "gap_index"],
                        aliases=["Segment ID", "Vulnerability", "Density (sq ft/ac)", "Gap Index"],
                        localize=True,
                    ),
                ).add_to(m)
        
        folium.LayerControl().add_to(m)
        st_folium(m, width=None, height=600)
        
    elif not FOLIUM_AVAILABLE:
        st.warning("Folium not installed. Install with: pip install folium streamlit-folium")
    else:
        st.info("No data matches the current filters.")

# -----------------------------------------------------------------------------
# Tab 2: Static Maps
# -----------------------------------------------------------------------------

with tab_static:
    st.subheader("Pre-generated Analysis Maps")
    
    available_maps = {k: v for k, v in STATIC_MAPS.items() if v.exists()}
    
    if available_maps:
        map_choice = st.selectbox("Select Map", list(available_maps.keys()))
        st.image(str(available_maps[map_choice]), use_container_width=True)
        
        st.markdown("---")
        st.markdown("### All Available Maps")
        cols = st.columns(len(available_maps))
        for i, (name, path) in enumerate(available_maps.items()):
            with cols[i]:
                st.markdown(f"**{name}**")
                st.image(str(path), use_container_width=True)
    else:
        st.warning("No static maps found. Generate them with:")
        st.code("python scripts/visualize_results.py --output-dir data/outputs")

# -----------------------------------------------------------------------------
# Tab 3: Charts & Analysis
# -----------------------------------------------------------------------------

with tab_charts:
    st.subheader("Analysis Charts")
    
    available_charts = {k: v for k, v in STATIC_CHARTS.items() if v.exists()}
    
    if available_charts:
        st.markdown("### Pre-generated Charts")
        cols = st.columns(len(available_charts))
        for i, (name, path) in enumerate(available_charts.items()):
            with cols[i]:
                st.markdown(f"**{name}**")
                st.image(str(path), use_container_width=True)
    
    st.markdown("---")
    
    if PLOTLY_AVAILABLE:
        st.markdown("### Interactive Charts")
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig_vuln = px.histogram(
                filtered,
                x="vuln_mean",
                nbins=30,
                title="Vulnerability Score Distribution",
                labels={"vuln_mean": "Vulnerability Score"},
                color_discrete_sequence=["#e76f51"],
            )
            fig_vuln.update_layout(showlegend=False)
            st.plotly_chart(fig_vuln, use_container_width=True)
        
        with col2:
            if "density_sqft_per_acre" in filtered.columns:
                density_data = filtered[filtered["density_sqft_per_acre"] < 1000]
                fig_density = px.histogram(
                    density_data,
                    x="density_sqft_per_acre",
                    nbins=30,
                    title="Infrastructure Density Distribution",
                    labels={"density_sqft_per_acre": "Density (sq ft/acre)"},
                    color_discrete_sequence=["#2a9d8f"],
                )
                fig_density.update_layout(showlegend=False)
                st.plotly_chart(fig_density, use_container_width=True)
        
        st.markdown("### Vulnerability vs Infrastructure Density")
        if "density_sqft_per_acre" in filtered.columns:
            fig_scatter = px.scatter(
                filtered,
                x="vuln_mean",
                y="density_sqft_per_acre",
                color="quadrant" if "quadrant" in filtered.columns else None,
                hover_data=["segment_id", "gap_index"],
                title="Correlation: Vulnerability vs Density",
                labels={
                    "vuln_mean": "Vulnerability Score",
                    "density_sqft_per_acre": "Density (sq ft/acre)",
                },
                opacity=0.6,
            )
            fig_scatter.update_layout(height=500)
            st.plotly_chart(fig_scatter, use_container_width=True)
        
        if "hotspot_class" in filtered.columns:
            st.markdown("### Hot Spot Classification")
            hotspot_counts = filtered["hotspot_class"].value_counts()
            fig_hotspot = px.bar(
                x=hotspot_counts.index,
                y=hotspot_counts.values,
                title="Segments by Hot Spot Classification",
                labels={"x": "Classification", "y": "Count"},
                color=hotspot_counts.values,
                color_continuous_scale="RdYlBu_r",
            )
            st.plotly_chart(fig_hotspot, use_container_width=True)
        
        runoff_cols = [c for c in filtered.columns if "volume_" in c and "_acft" in c]
        if runoff_cols:
            st.markdown("### Runoff Volume Comparison")
            runoff_data = []
            for col in runoff_cols:
                scenario = col.replace("volume_", "").replace("_acft", "").replace("_", " ")
                runoff_data.append({
                    "Scenario": scenario,
                    "Total Volume (ac-ft)": filtered[col].sum(),
                })
            
            runoff_df = pd.DataFrame(runoff_data)
            fig_runoff = px.bar(
                runoff_df,
                x="Scenario",
                y="Total Volume (ac-ft)",
                title="Total Runoff Volume by Scenario",
                color="Total Volume (ac-ft)",
                color_continuous_scale="Blues",
            )
            st.plotly_chart(fig_runoff, use_container_width=True)
    
    else:
        st.warning("Install Plotly for interactive charts: pip install plotly")

# -----------------------------------------------------------------------------
# Tab 4: Data Table
# -----------------------------------------------------------------------------

with tab_data:
    st.subheader("Segment Data")
    
    all_cols = [c for c in filtered.columns if c != "geometry"]
    default_cols = ["segment_id", "vuln_mean", "density_sqft_per_acre", "gap_index", "quadrant", "hotspot_class"]
    default_cols = [c for c in default_cols if c in all_cols]
    
    selected_cols = st.multiselect(
        "Select columns to display",
        options=all_cols,
        default=default_cols,
    )
    
    if selected_cols:
        display_df = filtered[selected_cols].copy()
        st.dataframe(display_df, use_container_width=True, height=500)
        
        csv = display_df.to_csv(index=False)
        st.download_button(
            label="📥 Download as CSV",
            data=csv,
            file_name="analysis_segments.csv",
            mime="text/csv",
        )
    
    st.markdown("---")
    st.markdown("### Summary Statistics")
    
    numeric_cols = filtered.select_dtypes(include=["float64", "int64"]).columns.tolist()
    numeric_cols = [c for c in numeric_cols if c in filtered.columns]
    
    if numeric_cols:
        summary = filtered[numeric_cols].describe().T
        st.dataframe(summary, use_container_width=True)

# -----------------------------------------------------------------------------
# Footer
# -----------------------------------------------------------------------------

st.markdown("---")
st.caption(
    "Dashboard for Seattle-Tacoma Rail Corridor Geospatial Analysis | "
    "Run python scripts/geospatial_analysis.py to regenerate data"
)
