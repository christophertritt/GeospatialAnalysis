import streamlit as st
import geopandas as gpd
import pandas as pd
import folium
from streamlit_folium import st_folium
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Set page config
st.set_page_config(page_title="Rail Resilience Dashboard", layout="wide")

st.title("🚄 Rail Corridor Resilience Dashboard")
st.markdown("""
This dashboard visualizes the results of the flood vulnerability and green infrastructure alignment analysis.
Use the sidebar to filter data and explore different metrics.
""")

# Load data
@st.cache_data
def load_data():
    path = 'data/outputs_final/analysis_segments.gpkg'
    if not os.path.exists(path):
        return None
    return gpd.read_file(path)

gdf = load_data()

if gdf is None:
    st.error("Data not found! Please run the analysis script first.")
    st.stop()

# Sidebar Controls
st.sidebar.header("Filters & Settings")

# Metric Selection
metric = st.sidebar.selectbox(
    "Select Metric to Visualize",
    options=['vuln_mean', 'gap_index', 'density_sqft_per_acre', 'imperv_mean', 'slope_mean'],
    format_func=lambda x: {
        'vuln_mean': 'Flood Vulnerability Score',
        'gap_index': 'Infrastructure Gap Index',
        'density_sqft_per_acre': 'Permeable Pavement Density',
        'imperv_mean': 'Imperviousness (%)',
        'slope_mean': 'Slope (%)'
    }.get(x, x)
)

# Filter by Vulnerability Class
if 'vuln_class' in gdf.columns:
    classes = ['All'] + sorted(gdf['vuln_class'].unique().tolist())
    selected_class = st.sidebar.selectbox("Filter by Vulnerability Class", classes)
    
    if selected_class != 'All':
        filtered_gdf = gdf[gdf['vuln_class'] == selected_class]
    else:
        filtered_gdf = gdf
else:
    filtered_gdf = gdf

# Main Content Layout
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Interactive Map")
    
    # Create Map
    m = folium.Map(location=[47.6062, -122.3321], zoom_start=11, tiles='CartoDB positron')
    
    # Determine colors
    if metric == 'vuln_mean':
        cmap = 'RdYlBu_r'
    elif metric == 'gap_index':
        cmap = 'Reds'
    elif metric == 'density_sqft_per_acre':
        cmap = 'Greens'
    else:
        cmap = 'viridis'
        
    # Add Choropleth
    folium.Choropleth(
        geo_data=filtered_gdf,
        name='choropleth',
        data=filtered_gdf,
        columns=['segment_id', metric],
        key_on='feature.properties.segment_id',
        fill_color=cmap,
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name=metric
    ).add_to(m)
    
    # Add tooltips
    folium.GeoJson(
        filtered_gdf,
        style_function=lambda x: {'fillColor': '#00000000', 'color': '#00000000'},
        tooltip=folium.GeoJsonTooltip(
            fields=['segment_id', 'vuln_mean', 'vuln_class', 'density_sqft_per_acre'],
            aliases=['Segment ID', 'Vulnerability', 'Class', 'Density'],
            localize=True
        )
    ).add_to(m)

    st_folium(m, width=None, height=600)

with col2:
    st.subheader("Statistics")
    
    # Key Metrics
    st.metric("Total Segments", len(filtered_gdf))
    st.metric(f"Mean {metric}", f"{filtered_gdf[metric].mean():.2f}")
    st.metric(f"Max {metric}", f"{filtered_gdf[metric].max():.2f}")
    
    st.markdown("---")
    
    # Distribution Plot
    st.subheader("Distribution")
    fig, ax = plt.subplots()
    sns.histplot(filtered_gdf[metric], kde=True, ax=ax)
    st.pyplot(fig)
    
    # Correlation Plot (if applicable)
    if metric != 'density_sqft_per_acre':
        st.subheader("Correlation with Density")
        fig2, ax2 = plt.subplots()
        sns.scatterplot(data=filtered_gdf, x=metric, y='density_sqft_per_acre', alpha=0.5, ax=ax2)
        st.pyplot(fig2)

# Data Table
st.subheader("Raw Data")
st.dataframe(filtered_gdf.drop(columns='geometry').head(100))
