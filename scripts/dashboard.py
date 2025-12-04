import streamlit as st
import geopandas as gpd
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px
import plotly.graph_objects as go
import os
import numpy as np

# Set page config
st.set_page_config(
    page_title="Rail Resilience Dashboard", 
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🚄 Rail Corridor Resilience Dashboard")
st.markdown("""
**Comprehensive analysis of flood vulnerability and green infrastructure alignment.**
Use the tabs below to explore different dimensions of the analysis.
""")

# --- Data Loading ---
@st.cache_data
def load_data():
    # Try multiple potential paths
    paths = [
        'data/outputs/analysis_segments.gpkg',
        'data/outputs_final/analysis_segments.gpkg',
        'data/outputs/analysis_segments.shp'
    ]
    
    for path in paths:
        if os.path.exists(path):
            try:
                gdf = gpd.read_file(path)
                # Ensure CRS is WGS84 for Folium
                if gdf.crs and gdf.crs.to_string() != 'EPSG:4326':
                    gdf = gdf.to_crs(epsg=4326)
                
                # OPTIMIZATION: Simplify geometry to reduce rendering load
                # 0.0001 degrees is approx 11 meters, good for overview
                gdf['geometry'] = gdf.geometry.simplify(tolerance=0.0001)
                
                return gdf
            except Exception as e:
                st.error(f"Error loading {path}: {e}")
                continue
    return None

gdf = load_data()

if gdf is None:
    st.error("❌ Analysis data not found! Please run `scripts/geospatial_analysis.py` first.")
    st.stop()

# --- Sidebar Controls ---
st.sidebar.header("⚙️ Settings & Filters")

# Basemap Selector
basemap = st.sidebar.selectbox(
    "Basemap",
    options=["CartoDB positron", "OpenStreetMap", "CartoDB dark_matter"],
    index=0
)

# Global Filters
st.sidebar.subheader("Global Filters")

# Vulnerability Class Filter
if 'vuln_class' in gdf.columns:
    vuln_classes = ['All'] + sorted(gdf['vuln_class'].unique().tolist())
    selected_class = st.sidebar.selectbox("Vulnerability Class", vuln_classes)
else:
    selected_class = 'All'

# Priority Filter (High Vuln + Low Infra)
show_priority_only = st.sidebar.checkbox("⚠️ Show Priority Gaps Only", help="Segments with High Vulnerability and Low Infrastructure")

# Apply Filters
filtered_gdf = gdf.copy()

if selected_class != 'All':
    filtered_gdf = filtered_gdf[filtered_gdf['vuln_class'] == selected_class]

if show_priority_only:
    # Assuming 'quadrant' column exists and 'Q3' or similar represents the gap
    # Or calculate it dynamically if needed
    if 'gap_index' in filtered_gdf.columns:
        filtered_gdf = filtered_gdf[filtered_gdf['gap_index'] > 0] # Positive gap = Vuln > Infra
    elif 'quadrant' in filtered_gdf.columns:
         # Usually Q2 or Q3 depending on axis. Let's use gap_index if available as it's safer.
         pass

# Export
st.sidebar.markdown("---")
st.sidebar.subheader("📥 Export")
csv = filtered_gdf.drop(columns='geometry').to_csv(index=False).encode('utf-8')
st.sidebar.download_button(
    "Download Filtered Data (CSV)",
    csv,
    "rail_analysis_filtered.csv",
    "text/csv",
    key='download-csv'
)

# --- Helper Functions ---
def create_map(data, color_col, tooltip_cols, caption, cmap='viridis', categorical=False):
    # OPTIMIZATION: prefer_canvas=True significantly speeds up rendering of many vector features
    m = folium.Map(location=[47.6062, -122.3321], zoom_start=11, tiles=basemap, prefer_canvas=True)
    
    if categorical:
        # For categorical data (like Clusters), we need a custom color function or pre-mapped colors
        # Simple approach: Factorize or use specific colors
        pass 
    
    folium.Choropleth(
        geo_data=data,
        name='choropleth',
        data=data,
        columns=['segment_id', color_col],
        key_on='feature.properties.segment_id',
        fill_color=cmap,
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name=caption
    ).add_to(m)
    
    # Filter tooltip columns to only those present in data
    valid_tooltip_cols = [c for c in tooltip_cols if c in data.columns]
    
    style_function = lambda x: {'fillColor': '#ffffff00', 'color': '#00000000'}
    folium.GeoJson(
        data,
        style_function=style_function,
        tooltip=folium.GeoJsonTooltip(
            fields=['segment_id'] + valid_tooltip_cols,
            localize=True
        )
    ).add_to(m)
    
    return m

# --- Tabs ---
tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🗺️ Spatial Analysis", "💧 Hydrology", "🔍 Deep Dive"])

# === TAB 1: OVERVIEW ===
with tab1:
    col1, col2 = st.columns([3, 1])
    
    with col2:
        st.subheader("Key Metrics")
        st.metric("Segments", len(filtered_gdf))
        
        if 'vuln_mean' in filtered_gdf.columns:
            st.metric("Avg Vulnerability", f"{filtered_gdf['vuln_mean'].mean():.2f}/10")
        
        if 'density_sqft_per_acre' in filtered_gdf.columns:
            st.metric("Avg Infra Density", f"{filtered_gdf['density_sqft_per_acre'].mean():.0f} sq ft/ac")
            
        if 'gap_index' in filtered_gdf.columns:
            high_gap_count = (filtered_gdf['gap_index'] > 5).sum()
            st.metric("Critical Gap Segments", f"{high_gap_count}", help="Segments with Gap Index > 5")

        st.markdown("### Visualization")
        map_metric = st.selectbox(
            "Map Layer",
            options=['vuln_mean', 'density_sqft_per_acre', 'gap_index', 'imperv_mean', 'slope_mean', 'svi_score', 'canopy_mean', 'in_flood_zone'],
            format_func=lambda x: {
                'vuln_mean': 'Flood Vulnerability',
                'density_sqft_per_acre': 'Infrastructure Density',
                'gap_index': 'Infrastructure Gap',
                'imperv_mean': 'Imperviousness',
                'slope_mean': 'Slope',
                'svi_score': 'Social Vulnerability (SVI)',
                'canopy_mean': 'Tree Canopy (%)',
                'in_flood_zone': 'In Flood Zone (Binary)'
            }.get(x, x)
        )

    with col1:
        # Determine colormap
        if map_metric == 'vuln_mean': cmap = 'RdYlBu_r'
        elif map_metric == 'gap_index': cmap = 'Reds'
        elif map_metric == 'density_sqft_per_acre': cmap = 'Greens'
        elif map_metric == 'svi_score': cmap = 'Purples'
        elif map_metric == 'canopy_mean': cmap = 'YlGn'
        elif map_metric == 'in_flood_zone': cmap = 'Blues'
        else: cmap = 'YlOrRd'
        
        # Check if column exists
        if map_metric in filtered_gdf.columns:
            m_overview = create_map(
                filtered_gdf, 
                map_metric, 
                ['vuln_mean', 'density_sqft_per_acre', 'gap_index', 'svi_score', 'canopy_mean'], 
                map_metric, 
                cmap
            )
            st_folium(m_overview, width=None, height=500)
        else:
            st.warning(f"Column '{map_metric}' not found in dataset. Run analysis with context layers.")

# === TAB 2: SPATIAL ANALYSIS ===
with tab2:
    st.subheader("Spatial Statistics & Clustering")
    
    col_space1, col_space2 = st.columns(2)
    
    with col_space1:
        st.markdown("#### Local Moran's I (Clusters)")
        if 'lisa_cluster' in filtered_gdf.columns:
            # Map LISA clusters
            # We need to map categorical data manually for Folium Choropleth or use a workaround
            # For simplicity, let's map the p-value or just show the table if mapping categorical is complex
            # Actually, let's map 'lisa_qvalue' (1-4) with a discrete colormap
            
            # Create a numeric mapping for visualization
            cluster_map = {'HH (High-High)': 4, 'LL (Low-Low)': 1, 'LH (Low-High)': 2, 'HL (High-Low)': 3, 'Not Significant': 0}
            filtered_gdf['lisa_numeric'] = filtered_gdf['lisa_cluster'].map(cluster_map).fillna(0)
            
            m_lisa = create_map(filtered_gdf, 'lisa_numeric', ['lisa_cluster', 'vuln_mean'], "Cluster Type (0=NS, 1=LL, 4=HH)", 'Spectral_r')
            st_folium(m_lisa, height=400, key='lisa_map')
            st.caption("HH: High Vuln surrounded by High Vuln | LL: Low surrounded by Low")
        else:
            st.info("LISA analysis not available in dataset.")

    with col_space2:
        st.markdown("#### Getis-Ord Gi* (Hot Spots)")
        if 'hotspot_class' in filtered_gdf.columns:
            # Similar numeric mapping
            hotspot_map = {
                'Hot Spot (99%)': 3, 'Hot Spot (95%)': 2, 'Hot Spot (90%)': 1,
                'Not Significant': 0,
                'Cold Spot (90%)': -1, 'Cold Spot (95%)': -2, 'Cold Spot (99%)': -3
            }
            filtered_gdf['hotspot_numeric'] = filtered_gdf['hotspot_class'].map(hotspot_map).fillna(0)
            
            m_hotspot = create_map(filtered_gdf, 'hotspot_numeric', ['hotspot_class', 'vuln_mean'], "Hot Spot Confidence", 'RdBu_r')
            st_folium(m_hotspot, height=400, key='hotspot_map')
            st.caption("Red: Significant Hot Spots (High Values) | Blue: Significant Cold Spots")
        else:
            st.info("Hot Spot analysis not available in dataset.")

    st.markdown("---")
    st.markdown("#### Correlation Matrix")
    
    # Select numeric columns for correlation
    corr_cols = ['vuln_mean', 'density_sqft_per_acre', 'imperv_mean', 'slope_mean', 'gap_index', 'svi_score', 'canopy_mean']
    available_corr_cols = [c for c in corr_cols if c in filtered_gdf.columns]
    
    if len(available_corr_cols) > 1:
        corr = filtered_gdf[available_corr_cols].corr()
        fig_corr = px.imshow(corr, text_auto=True, aspect="auto", color_continuous_scale='RdBu_r', zmin=-1, zmax=1)
        st.plotly_chart(fig_corr, use_container_width=True)

# === TAB 3: HYDROLOGY ===
with tab3:
    st.subheader("Runoff Modeling & Scenarios")
    
    if not any(col.startswith('runoff_current') for col in filtered_gdf.columns):
        st.warning("Runoff modeling data not found. Please ensure Phase 6 of the analysis was run.")
    else:
        # Scenario Selector
        storm_events = ['2-year', '10-year', '25-year']
        selected_storm = st.selectbox("Select Design Storm Event", storm_events)
        
        col_hydro1, col_hydro2 = st.columns([1, 2])
        
        with col_hydro1:
            st.markdown(f"### {selected_storm} Storm Totals")
            
            vol_current_col = f'volume_current_{selected_storm}_acft'
            vol_nogsi_col = f'volume_no_gsi_{selected_storm}_acft'
            vol_opt_col = f'volume_optimized_{selected_storm}_acft'
            
            if vol_current_col in filtered_gdf.columns:
                total_current = filtered_gdf[vol_current_col].sum()
                total_nogsi = filtered_gdf[vol_nogsi_col].sum()
                
                st.metric("Current Runoff Volume", f"{total_current:.1f} ac-ft")
                st.metric("Baseline (No GSI)", f"{total_nogsi:.1f} ac-ft", delta=f"{total_current - total_nogsi:.1f} ac-ft", delta_color="inverse")
                
                if vol_opt_col in filtered_gdf.columns:
                    total_opt = filtered_gdf[vol_opt_col].sum()
                    st.metric("Optimized Scenario", f"{total_opt:.1f} ac-ft", delta=f"{total_opt - total_current:.1f} ac-ft", delta_color="inverse")
        
        with col_hydro2:
            # Bar chart comparison
            if vol_current_col in filtered_gdf.columns:
                data = {
                    'Scenario': ['No GSI Baseline', 'Current Conditions', 'Optimized Allocation'],
                    'Volume (ac-ft)': [total_nogsi, total_current, total_opt if vol_opt_col in filtered_gdf.columns else 0]
                }
                df_hydro = pd.DataFrame(data)
                fig_hydro = px.bar(df_hydro, x='Scenario', y='Volume (ac-ft)', color='Scenario', title=f"Runoff Volume Comparison ({selected_storm})")
                st.plotly_chart(fig_hydro, use_container_width=True)

        st.markdown("### Optimization Benefit Map")
        st.markdown("Where would additional infrastructure yield the most runoff reduction?")
        
        if 'potential_benefit' in filtered_gdf.columns:
             m_benefit = create_map(filtered_gdf, 'potential_benefit', ['potential_benefit', 'vuln_mean'], "Potential Benefit (ac-ft reduction)", 'Greens')
             st_folium(m_benefit, width=None, height=400, key='benefit_map')
        else:
            st.info("Optimization benefit data not available.")

# === TAB 4: DEEP DIVE ===
with tab4:
    st.subheader("Segment Comparison & Deep Dive")
    
    # Segment Selector
    selected_segment_ids = st.multiselect(
        "Select Segments to Compare",
        options=filtered_gdf['segment_id'].tolist(),
        default=filtered_gdf['segment_id'].tolist()[:2] if len(filtered_gdf) > 1 else []
    )
    
    if selected_segment_ids:
        comparison_df = filtered_gdf[filtered_gdf['segment_id'].isin(selected_segment_ids)]
        
        col_dd1, col_dd2 = st.columns(2)
        
        with col_dd1:
            st.markdown("#### Vulnerability Components")
            # Radar Chart
            # Normalize columns for radar chart (0-1 or similar scale)
            radar_cols = ['imperv_mean', 'slope_mean', 'vuln_mean']
            
            # We need to normalize these to be comparable on a radar chart
            # Simple min-max normalization for visualization
            radar_data = comparison_df.copy()
            for col in radar_cols:
                if col in radar_data.columns:
                    max_val = gdf[col].max()
                    if max_val > 0:
                        radar_data[col + '_norm'] = radar_data[col] / max_val
            
            categories = ['Imperviousness', 'Slope', 'Overall Vulnerability']
            
            fig_radar = go.Figure()
            
            for idx, row in radar_data.iterrows():
                values = [
                    row.get('imperv_mean_norm', 0), 
                    row.get('slope_mean_norm', 0), 
                    row.get('vuln_mean_norm', 0)
                ]
                fig_radar.add_trace(go.Scatterpolar(
                    r=values,
                    theta=categories,
                    fill='toself',
                    name=f"Segment {row['segment_id']}"
                ))
            
            fig_radar.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
                showlegend=True,
                title="Normalized Vulnerability Factors"
            )
            st.plotly_chart(fig_radar, use_container_width=True)
            
        with col_dd2:
            st.markdown("#### Detailed Metrics")
            disp_cols = ['segment_id', 'vuln_mean', 'vuln_class', 'density_sqft_per_acre', 'gap_index', 'quadrant']
            disp_cols = [c for c in disp_cols if c in comparison_df.columns]
            
            st.dataframe(comparison_df[disp_cols].set_index('segment_id').T)

    st.markdown("---")
    st.markdown("#### Full Data Table")
    st.dataframe(filtered_gdf.drop(columns='geometry'))
