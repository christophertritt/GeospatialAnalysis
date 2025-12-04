"""
Runoff reduction modeling module (Phase 6)
Implements SCS Curve Number method for stormwater runoff estimation
"""
import numpy as np
import pandas as pd

# Support both direct execution and package import
try:
    from .utils.statistics import calculate_runoff_depth, calculate_cn_from_imperviousness
except ImportError:
    from utils.statistics import calculate_runoff_depth, calculate_cn_from_imperviousness


# NOAA Atlas 14 design storm depths for Seattle-Tacoma region
# 24-hour precipitation depths in inches
# Location: 47.45°N, 122.31°W (Sea-Tac Airport)
# Source: https://hdsc.nws.noaa.gov/pfds/
DESIGN_STORMS = {
    '2-year': 2.2,
    '5-year': 2.6,
    '10-year': 2.9,
    '25-year': 3.4,
    '50-year': 3.8,
    '100-year': 4.3
}


def prepare_curve_numbers(segments, soil_type='C'):
    """
    Prepare SCS Curve Numbers for each segment
    
    Args:
        segments: GeoDataFrame with segments
        soil_type: Dominant hydrologic soil group
    
    Returns:
        GeoDataFrame with curve numbers added
    """
    print("\nPreparing Curve Numbers...")
    
    segments = segments.copy()
    
    # Calculate CN from imperviousness
    if 'imperv_mean' in segments.columns:
        segments['cn_current'] = segments['imperv_mean'].apply(
            lambda x: calculate_cn_from_imperviousness(x, soil_type)
        )
    else:
        # Use default CN if imperviousness not available
        print("Warning: No imperviousness data. Using default CN=75")
        segments['cn_current'] = 75
    
    # Adjust CN for existing permeable pavement infrastructure
    if 'density_sqft_per_acre' in segments.columns:
        segments['cn_with_gsi'] = segments.apply(
            lambda row: adjust_cn_for_gsi(row['cn_current'], row['density_sqft_per_acre']),
            axis=1
        )
    else:
        segments['cn_with_gsi'] = segments['cn_current']
    
    print(f"  Mean CN (current): {segments['cn_current'].mean():.1f}")
    print(f"  Mean CN (with GSI): {segments['cn_with_gsi'].mean():.1f}")
    print(f"  Range: {segments['cn_current'].min():.1f} - {segments['cn_current'].max():.1f}")
    
    return segments


def adjust_cn_for_gsi(cn_current, density_sqft_per_acre):
    """
    Reduce Curve Number based on existing green stormwater infrastructure
    
    Args:
        cn_current: Current curve number without GSI
        density_sqft_per_acre: Infrastructure density
    
    Returns:
        Adjusted curve number
    """
    # Assume each 1,000 sq ft/acre reduces CN by 2 points
    reduction_factor = density_sqft_per_acre / 1000 * 2
    cn_adjusted = cn_current - reduction_factor
    
    # Minimum CN cannot be below pervious grass (CN ~35)
    return max(cn_adjusted, 35)


def calculate_runoff_volumes(segments, storm_events=None):
    """
    Calculate runoff volumes for design storms
    
    Args:
        segments: GeoDataFrame with curve numbers
        storm_events: List of storm events to analyze (default: ['2-year', '10-year', '25-year'])
    
    Returns:
        GeoDataFrame with runoff volumes added
    """
    if storm_events is None:
        storm_events = ['2-year', '10-year', '25-year']
    
    print("\nCalculating runoff volumes...")
    segments = segments.copy()
    
    for storm in storm_events:
        if storm not in DESIGN_STORMS:
            print(f"Warning: Storm '{storm}' not in design storms. Skipping.")
            continue
        
        precip = DESIGN_STORMS[storm]
        
        # Current conditions (with existing GSI)
        segments[f'runoff_current_{storm}'] = segments['cn_with_gsi'].apply(
            lambda cn: calculate_runoff_depth(precip, cn)
        )
        
        # No GSI baseline (for comparison)
        segments[f'runoff_no_gsi_{storm}'] = segments['cn_current'].apply(
            lambda cn: calculate_runoff_depth(precip, cn)
        )
        
        # Calculate volumes (depth × area)
        # Convert inches to feet, multiply by area in acres, gives acre-feet
        if 'buffer_area_acres' in segments.columns:
            segments[f'volume_current_{storm}_acft'] = (
                segments[f'runoff_current_{storm}'] / 12 * 
                segments['buffer_area_acres']
            )
            
            segments[f'volume_no_gsi_{storm}_acft'] = (
                segments[f'runoff_no_gsi_{storm}'] / 12 * 
                segments['buffer_area_acres']
            )
    
    # Print summary
    print("\nRunoff Volume Summary (acre-feet):")
    for storm in storm_events:
        if f'volume_current_{storm}_acft' in segments.columns:
            total_current = segments[f'volume_current_{storm}_acft'].sum()
            total_no_gsi = segments[f'volume_no_gsi_{storm}_acft'].sum()
            reduction = total_no_gsi - total_current
            pct_reduction = (reduction / total_no_gsi * 100) if total_no_gsi > 0 else 0
            
            print(f"  {storm}:")
            print(f"    Current: {total_current:.1f} ac-ft")
            print(f"    Without GSI: {total_no_gsi:.1f} ac-ft")
            print(f"    Reduction: {reduction:.1f} ac-ft ({pct_reduction:.1f}%)")
    
    return segments


def optimize_infrastructure_allocation(segments, total_infrastructure_sqft=None):
    """
    Calculate optimal infrastructure allocation based on vulnerability
    
    Args:
        segments: GeoDataFrame with vulnerability and current infrastructure
        total_infrastructure_sqft: Total infrastructure to allocate (uses current if None)
    
    Returns:
        GeoDataFrame with optimized allocation metrics
    """
    print("\nCalculating optimized infrastructure allocation...")
    
    segments = segments.copy()
    
    # Get total infrastructure if not specified
    if total_infrastructure_sqft is None:
        if 'total_area_sqft' in segments.columns:
            total_infrastructure_sqft = segments['total_area_sqft'].sum()
        else:
            print("Warning: No infrastructure data available")
            return segments
    
    print(f"  Total infrastructure to allocate: {total_infrastructure_sqft:,.0f} sq ft")
    
    # Allocation strategy: proportional to vulnerability × area
    if 'vuln_mean' in segments.columns and 'buffer_area_acres' in segments.columns:
        segments['allocation_weight'] = (
            segments['vuln_mean'] * 
            segments['buffer_area_acres']
        )
        
        segments['allocation_weight'] = (
            segments['allocation_weight'] / 
            segments['allocation_weight'].sum()
        )
        
        segments['optimized_sqft'] = (
            segments['allocation_weight'] * total_infrastructure_sqft
        )
        
        segments['optimized_density'] = (
            segments['optimized_sqft'] / segments['buffer_area_acres']
        )
        
        print(f"  Optimized density range: {segments['optimized_density'].min():.0f} - "
              f"{segments['optimized_density'].max():.0f} sq ft/acre")
    
    return segments


def calculate_optimization_benefit(segments, storm_event='10-year'):
    """
    Calculate runoff reduction benefit from optimized allocation
    
    Args:
        segments: GeoDataFrame with current and optimized infrastructure
        storm_event: Storm event to analyze
    
    Returns:
        GeoDataFrame with benefit metrics added
    """
    if storm_event not in DESIGN_STORMS:
        print(f"Warning: Storm '{storm_event}' not in design storms")
        return segments
    
    print(f"\nCalculating optimization benefit for {storm_event} storm...")
    
    segments = segments.copy()
    precip = DESIGN_STORMS[storm_event]
    
    # Calculate CN with optimized allocation
    if 'optimized_density' in segments.columns:
        segments['cn_optimized'] = segments.apply(
            lambda row: adjust_cn_for_gsi(row['cn_current'], row['optimized_density']),
            axis=1
        )
        
        # Calculate runoff with optimized allocation
        segments[f'runoff_optimized_{storm_event}'] = segments['cn_optimized'].apply(
            lambda cn: calculate_runoff_depth(precip, cn)
        )
        
        if 'buffer_area_acres' in segments.columns:
            segments[f'volume_optimized_{storm_event}_acft'] = (
                segments[f'runoff_optimized_{storm_event}'] / 12 * 
                segments['buffer_area_acres']
            )
            
            # Calculate benefit
            if f'volume_current_{storm_event}_acft' in segments.columns:
                segments['potential_benefit'] = (
                    segments[f'volume_current_{storm_event}_acft'] - 
                    segments[f'volume_optimized_{storm_event}_acft']
                )
                
                # Summary
                total_current = segments[f'volume_current_{storm_event}_acft'].sum()
                total_optimized = segments[f'volume_optimized_{storm_event}_acft'].sum()
                total_benefit = segments['potential_benefit'].sum()
                pct_benefit = (total_benefit / total_current * 100) if total_current > 0 else 0
                
                print(f"  Current: {total_current:.1f} ac-ft")
                print(f"  Optimized: {total_optimized:.1f} ac-ft")
                print(f"  Additional reduction: {total_benefit:.1f} ac-ft ({pct_benefit:.1f}%)")
    
    return segments


def perform_runoff_modeling(segments, storm_events=None, soil_type='C'):
    """
    Perform complete runoff modeling analysis
    
    Args:
        segments: GeoDataFrame with analysis segments
        storm_events: List of storm events to analyze
        soil_type: Dominant hydrologic soil group
    
    Returns:
        GeoDataFrame with runoff modeling results
    """
    print("\n" + "="*70)
    print("PHASE 6: RUNOFF REDUCTION MODELING")
    print("="*70)
    
    # Prepare curve numbers
    segments = prepare_curve_numbers(segments, soil_type)
    
    # Calculate runoff volumes
    segments = calculate_runoff_volumes(segments, storm_events)
    
    # Optimize allocation
    segments = optimize_infrastructure_allocation(segments)
    
    # Calculate optimization benefit
    segments = calculate_optimization_benefit(segments)
    
    return segments
