import os
import geopandas as gpd
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def convert_gpkg_to_shp(root_dir):
    """
    Recursively find all .gpkg files and convert them to .shp
    """
    root_path = Path(root_dir)
    gpkg_files = list(root_path.rglob('*.gpkg'))
    
    if not gpkg_files:
        logging.info("No .gpkg files found.")
        return

    logging.info(f"Found {len(gpkg_files)} GeoPackage files to convert.")

    for gpkg_path in gpkg_files:
        try:
            # Define output shapefile path (same name, .shp extension)
            shp_path = gpkg_path.with_suffix('.shp')
            
            # Skip if shapefile already exists and is newer
            if shp_path.exists():
                if shp_path.stat().st_mtime > gpkg_path.stat().st_mtime:
                    logging.info(f"Skipping {gpkg_path.name} (Shapefile exists and is newer)")
                    continue
            
            logging.info(f"Converting {gpkg_path.name} to Shapefile...")
            
            # Read GeoPackage
            # Note: GPKG can have multiple layers. We'll try to read the default or first one.
            try:
                gdf = gpd.read_file(gpkg_path)
            except Exception as e:
                # Try listing layers if default fails
                import fiona
                layers = fiona.listlayers(gpkg_path)
                if layers:
                    logging.info(f"  - Multiple layers found: {layers}. Converting first layer '{layers[0]}'.")
                    gdf = gpd.read_file(gpkg_path, layer=layers[0])
                else:
                    raise e

            # Write Shapefile
            # Shapefiles have column name limits (10 chars). GeoPandas handles this but might truncate.
            gdf.to_file(shp_path)
            logging.info(f"  ✅ Created {shp_path.name}")
            
        except Exception as e:
            logging.error(f"  ❌ Failed to convert {gpkg_path.name}: {e}")

if __name__ == "__main__":
    convert_gpkg_to_shp("data")
