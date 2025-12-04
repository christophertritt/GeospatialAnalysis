"""
Spatial clustering analysis module (Phase 5)
Implements Moran's I, LISA, and Getis-Ord Gi* analysis
"""
import numpy as np
import pandas as pd
import geopandas as gpd


def calculate_morans_i(segments, variable_col):
    """
    Calculate Global Moran's I for spatial autocorrelation
    
    Args:
        segments: GeoDataFrame with analysis segments
        variable_col: Column name to analyze
    
    Returns:
        Dictionary with Moran's I statistics
    """
    try:
        from libpysal.weights import Queen
        from esda.moran import Moran
        
        # Create spatial weights matrix
        w = Queen.from_dataframe(segments)
        w.transform = 'r'
        
        # Extract variable
        data = segments[variable_col].values
        
        # Calculate Moran's I
        moran = Moran(data, w)
        
        results = {
            'I': moran.I,
            'expected_I': moran.EI,
            'z_score': moran.z_norm,
            'p_value': moran.p_norm,
            'interpretation': interpret_morans_i(moran.I, moran.p_norm)
        }
        
        return results
        
    except ImportError:
        print("Warning: libpysal/esda not installed. Skipping Moran's I analysis.")
        return None
    except Exception as e:
        print(f"Error calculating Moran's I: {e}")
        return None


def interpret_morans_i(I, p_value):
    """Interpret Moran's I results"""
    if p_value >= 0.05:
        return "No significant spatial autocorrelation"
    elif I > 0:
        return "Significant positive spatial autocorrelation (clustering)"
    else:
        return "Significant negative spatial autocorrelation (dispersion)"


def calculate_local_morans(segments, variable_col):
    """
    Calculate Local Moran's I (LISA) for identifying clusters
    
    Args:
        segments: GeoDataFrame with analysis segments
        variable_col: Column name to analyze
    
    Returns:
        GeoDataFrame with LISA results added
    """
    try:
        from libpysal.weights import Queen
        from esda.moran import Moran_Local
        
        # Create spatial weights matrix
        w = Queen.from_dataframe(segments)
        w.transform = 'r'
        
        # Extract variable
        data = segments[variable_col].values
        
        # Calculate Local Moran's I
        lisa = Moran_Local(data, w, permutations=999)
        
        # Add results to segments
        segments = segments.copy()
        segments['lisa_I'] = lisa.Is
        segments['lisa_pvalue'] = lisa.p_sim
        segments['lisa_qvalue'] = lisa.q
        
        # Classify significance
        segments['lisa_sig'] = segments['lisa_pvalue'] < 0.05
        
        # Classify cluster types
        cluster_labels = {
            1: 'HH (High-High)',
            2: 'LH (Low-High)',
            3: 'LL (Low-Low)',
            4: 'HL (High-Low)'
        }
        
        def classify_cluster(row):
            if not row['lisa_sig']:
                return 'Not Significant'
            return cluster_labels.get(row['lisa_qvalue'], 'Unknown')
        
        segments['lisa_cluster'] = segments.apply(classify_cluster, axis=1)
        
        print("\nLISA Cluster Summary:")
        print(segments['lisa_cluster'].value_counts())
        
        return segments
        
    except ImportError:
        print("Warning: libpysal/esda not installed. Skipping LISA analysis.")
        return segments
    except Exception as e:
        print(f"Error calculating LISA: {e}")
        return segments


def calculate_hot_spots(segments, variable_col, distance_threshold=15840):
    """
    Calculate Getis-Ord Gi* hot spot analysis
    
    Args:
        segments: GeoDataFrame with analysis segments
        variable_col: Column name to analyze
        distance_threshold: Distance band in feet (default 3 miles = 15,840 ft)
    
    Returns:
        GeoDataFrame with hot spot results added
    """
    try:
        from libpysal.weights import DistanceBand
        from esda.getisord import G_Local
        
        # Create distance-based weights
        w_dist = DistanceBand.from_dataframe(
            segments, 
            threshold=distance_threshold, 
            binary=False
        )
        w_dist.transform = 'r'
        
        # Extract variable
        data = segments[variable_col].values
        
        # Calculate Getis-Ord Gi*
        gi_star = G_Local(data, w_dist, transform='r', permutations=999, star=True)
        
        # Add results to segments
        segments = segments.copy()
        segments['gi_star'] = gi_star.Zs
        segments['gi_pvalue'] = gi_star.p_sim
        
        # Classify hot spots and cold spots
        def classify_hotspot(row):
            if row['gi_pvalue'] >= 0.10:
                return 'Not Significant'
            elif row['gi_star'] > 2.58:  # 99% confidence
                return 'Hot Spot (99%)'
            elif row['gi_star'] > 1.96:  # 95% confidence
                return 'Hot Spot (95%)'
            elif row['gi_star'] > 1.65:  # 90% confidence
                return 'Hot Spot (90%)'
            elif row['gi_star'] < -2.58:
                return 'Cold Spot (99%)'
            elif row['gi_star'] < -1.96:
                return 'Cold Spot (95%)'
            elif row['gi_star'] < -1.65:
                return 'Cold Spot (90%)'
            else:
                return 'Not Significant'
        
        segments['hotspot_class'] = segments.apply(classify_hotspot, axis=1)
        
        print("\nHot Spot Analysis Summary:")
        print(segments['hotspot_class'].value_counts())
        
        return segments
        
    except ImportError:
        print("Warning: libpysal/esda not installed. Skipping hot spot analysis.")
        return segments
    except Exception as e:
        print(f"Error calculating hot spots: {e}")
        return segments


def perform_spatial_clustering_analysis(segments, variable_col='gap_index'):
    """
    Perform complete spatial clustering analysis
    
    Args:
        segments: GeoDataFrame with analysis segments
        variable_col: Column name to analyze (default: 'gap_index')
    
    Returns:
        Dictionary with results and updated segments GeoDataFrame
    """
    print("\n" + "="*70)
    print(f"PHASE 5: SPATIAL CLUSTERING ANALYSIS ({variable_col})")
    print("="*70)
    
    if variable_col not in segments.columns:
        print(f"Error: Column '{variable_col}' not found in segments")
        return None, segments
    
    results = {}
    
    # Global Moran's I
    print("\nCalculating Global Moran's I...")
    morans_result = calculate_morans_i(segments, variable_col)
    if morans_result:
        results['morans_i'] = morans_result
        print(f"  Moran's I: {morans_result['I']:.3f}")
        print(f"  Z-score: {morans_result['z_score']:.3f}")
        print(f"  P-value: {morans_result['p_value']:.4f}")
        print(f"  {morans_result['interpretation']}")
    
    # Local Moran's I (LISA)
    print("\nCalculating Local Moran's I (LISA)...")
    segments = calculate_local_morans(segments, variable_col)
    
    # Hot Spot Analysis (Getis-Ord Gi*)
    print("\nCalculating Hot Spots (Getis-Ord Gi*)...")
    segments = calculate_hot_spots(segments, variable_col)
    
    return results, segments
