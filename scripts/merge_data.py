import geopandas as gpd
import pandas as pd
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)

def merge_infrastructure():
    """Merge Seattle Open Data and OSM Infrastructure"""
    seattle_path = Path('data/raw/infrastructure/permeable_pavement.shp')
    osm_path = Path('data/raw/infrastructure/osm_gsi_proxy.gpkg')
    output_path = Path('data/processed/infrastructure_combined.gpkg')
    
    gdfs = []
    
    if seattle_path.exists():
        logging.info(f"Loading Seattle data: {seattle_path}")
        gdf_sea = gpd.read_file(seattle_path)
        gdf_sea['source'] = 'Seattle Open Data'
        # Ensure CRS matches
        if gdf_sea.crs != 'EPSG:4326':
            gdf_sea = gdf_sea.to_crs('EPSG:4326')
        gdfs.append(gdf_sea)
        
    if osm_path.exists():
        logging.info(f"Loading OSM data: {osm_path}")
        gdf_osm = gpd.read_file(osm_path)
        gdf_osm['source'] = 'OpenStreetMap'
        if gdf_osm.crs != 'EPSG:4326':
            gdf_osm = gdf_osm.to_crs('EPSG:4326')
        gdfs.append(gdf_osm)
        
    if gdfs:
        # Concatenate
        combined = gpd.GeoDataFrame(pd.concat(gdfs, ignore_index=True), crs=gdfs[0].crs)
        
        # Standardize columns if needed (e.g. AreaSqFt)
        # OSM doesn't have AreaSqFt, so we calculate it (projected)
        combined_proj = combined.to_crs('EPSG:2927')
        combined['AreaSqFt'] = combined_proj.geometry.area
        
        output_path.parent.mkdir(exist_ok=True)
        combined.to_file(output_path, driver='GPKG')
        logging.info(f"✅ Merged infrastructure saved to {output_path} ({len(combined)} features)")
        return output_path
    else:
        logging.error("No infrastructure data found to merge.")
        return None

if __name__ == "__main__":
    merge_infrastructure()
