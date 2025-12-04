"""
GIS utility functions for geospatial analysis
"""
import geopandas as gpd
import numpy as np
from shapely.geometry import Point, LineString
from shapely.ops import split, nearest_points


def validate_spatial_data(gdf, dataset_name):
    """
    Validate spatial dataset for common issues
    
    Args:
        gdf: GeoDataFrame to validate
        dataset_name: Name of dataset for reporting
    
    Returns:
        GeoDataFrame with fixes applied
    """
    print(f"\n=== Validating {dataset_name} ===")
    
    # Check CRS
    print(f"CRS: {gdf.crs}")
    if gdf.crs is None:
        print("WARNING: No CRS defined!")
    
    # Check for null geometries
    null_geoms = gdf.geometry.isna().sum()
    print(f"Null geometries: {null_geoms}")
    if null_geoms > 0:
        gdf = gdf[~gdf.geometry.isna()]
        print(f"  Removed {null_geoms} null geometries")
    
    # Check for invalid geometries
    invalid = ~gdf.geometry.is_valid
    print(f"Invalid geometries: {invalid.sum()}")
    if invalid.sum() > 0:
        print("  Attempting to fix...")
        gdf.loc[invalid, 'geometry'] = gdf.loc[invalid, 'geometry'].buffer(0)
        still_invalid = ~gdf.geometry.is_valid
        print(f"  Remaining invalid: {still_invalid.sum()}")
    
    # Check bounds
    bounds = gdf.total_bounds
    print(f"Bounds: minx={bounds[0]:.2f}, miny={bounds[1]:.2f}, maxx={bounds[2]:.2f}, maxy={bounds[3]:.2f}")
    
    # Summary statistics
    print(f"Total features: {len(gdf)}")
    print(f"Geometry types: {gdf.geometry.type.value_counts().to_dict()}")
    
    return gdf


def reproject_to_standard(gdf, target_epsg=2927):
    """
    Reproject GeoDataFrame to standard CRS
    
    Args:
        gdf: GeoDataFrame to reproject
        target_epsg: Target EPSG code (default: 2927 - WA State Plane South)
    
    Returns:
        Reprojected GeoDataFrame
    """
    if gdf.crs.to_epsg() != target_epsg:
        print(f"Reprojecting from EPSG:{gdf.crs.to_epsg()} to EPSG:{target_epsg}")
        gdf = gdf.to_crs(epsg=target_epsg)
    return gdf


def create_buffers(gdf, distances_meters):
    """
    Create multiple buffers around geometries
    
    Args:
        gdf: GeoDataFrame with geometries to buffer
        distances_meters: List of buffer distances in meters
    
    Returns:
        Dict of GeoDataFrames with buffers at different distances
    """
    # Convert meters to feet (WA State Plane is in feet)
    METERS_TO_FEET = 3.28084
    
    buffers = {}
    for distance in distances_meters:
        distance_feet = distance * METERS_TO_FEET
        buffer_gdf = gdf.copy()
        buffer_gdf['geometry'] = gdf.geometry.buffer(distance_feet)
        buffer_gdf = buffer_gdf.dissolve()
        buffer_gdf['buffer_distance_m'] = distance
        buffers[f'{distance}m'] = buffer_gdf
        
        # Calculate area
        area_acres = buffer_gdf.geometry.area.sum() / 43560  # sqft to acres
        print(f"{distance}m buffer: {area_acres:.0f} acres")
    
    return buffers


def split_line_at_points(line, points):
    """
    Split a LineString at multiple points
    
    Args:
        line: LineString geometry to split
        points: List of Point geometries to split at
    
    Returns:
        List of LineString segments
    """
    segments = []
    current_line = line
    
    # Sort points by distance along line
    point_distances = []
    for point in points:
        dist = line.project(point)
        point_distances.append((dist, point))
    
    point_distances.sort()
    
    # Split progressively
    for i, (dist, point) in enumerate(point_distances):
        # Find nearest point on line
        nearest = nearest_points(current_line, point)[0]
        
        # Split at nearest point
        try:
            split_result = split(current_line, nearest.buffer(1))  # 1-foot buffer
            if len(split_result.geoms) >= 2:
                segments.append(split_result.geoms[0])
                # Continue with remainder
                remaining = split_result.geoms[1:]
                if len(remaining) == 1:
                    current_line = remaining[0]
                else:
                    # Merge remaining parts
                    coords = [pt for geom in remaining for pt in geom.coords]
                    current_line = LineString(coords)
        except Exception as e:
            print(f"Warning: Could not split at point {i}: {e}")
            pass
    
    # Add final segment
    if current_line is not None:
        segments.append(current_line)
    
    return segments


def calculate_infrastructure_density(segments, infrastructure, buffer_gdf=None):
    """
    Calculate infrastructure density for each segment
    
    Args:
        segments: GeoDataFrame of analysis segments
        infrastructure: GeoDataFrame of infrastructure features
        buffer_gdf: Optional buffered segments (uses segments if None)
    
    Returns:
        GeoDataFrame with density metrics added
    """
    if buffer_gdf is None:
        buffer_gdf = segments
    
    # Ensure same CRS
    infrastructure = infrastructure.to_crs(buffer_gdf.crs)
    
    # Spatial join: which facilities fall within each segment?
    joined = gpd.sjoin(infrastructure, buffer_gdf, how='inner', predicate='intersects')
    
    # Aggregate by segment
    if 'segment_id' in buffer_gdf.columns:
        group_col = 'segment_id'
    else:
        group_col = buffer_gdf.index.name or 'index'
        buffer_gdf = buffer_gdf.reset_index()
    
    # Count facilities and sum area
    area_col = None
    for col in ['AreaSqFt', 'area_sqft', 'Area', 'area']:
        if col in infrastructure.columns:
            area_col = col
            break
    
    if area_col:
        density = joined.groupby(group_col).agg({
            joined.columns[0]: 'count',  # Count any column
            area_col: 'sum'
        }).reset_index()
        density.columns = [group_col, 'facility_count', 'total_area_sqft']
    else:
        density = joined.groupby(group_col).size().reset_index(name='facility_count')
        density['total_area_sqft'] = 0
    
    # Merge back to segments
    result = buffer_gdf.merge(density, on=group_col, how='left')
    
    # Fill NaN (segments with no infrastructure)
    result['facility_count'] = result['facility_count'].fillna(0)
    result['total_area_sqft'] = result['total_area_sqft'].fillna(0)
    
    # Calculate buffer area and density
    result['buffer_area_sqft'] = result.geometry.area
    result['buffer_area_acres'] = result['buffer_area_sqft'] / 43560
    result['density_sqft_per_acre'] = result['total_area_sqft'] / result['buffer_area_acres'].replace(0, 1)
    
    return result
