"""
Statistical utility functions for geospatial analysis
"""
import numpy as np
from scipy import stats


# SCS Curve Number method constants
# From USDA NRCS Technical Release 55 (TR-55)
SCS_CN_CONSTANT = 1000  # Used in S = (1000/CN - 10) formula
SCS_RETENTION_OFFSET = 10  # Offset in potential retention formula
SCS_INITIAL_ABSTRACTION_RATIO = 0.2  # Ia = 0.2 * S


def calculate_runoff_depth(precip_inches, curve_number):
    """
    Calculate runoff depth using SCS Curve Number method
    
    Q = (P - Ia)^2 / (P - Ia + S)
    where:
    Q = runoff depth (inches)
    P = precipitation depth (inches)
    Ia = initial abstraction = 0.2 * S (inches)
    S = potential maximum retention = (1000/CN - 10) (inches)
    
    Args:
        precip_inches: Precipitation depth in inches
        curve_number: SCS Curve Number (30-100)
    
    Returns:
        Runoff depth in inches
    """
    # Calculate potential maximum retention
    S = (SCS_CN_CONSTANT / curve_number) - SCS_RETENTION_OFFSET
    
    # Calculate initial abstraction
    Ia = SCS_INITIAL_ABSTRACTION_RATIO * S
    
    # Calculate runoff (only if P > Ia)
    if precip_inches > Ia:
        Q = (precip_inches - Ia)**2 / (precip_inches - Ia + S)
    else:
        Q = 0
    
    return Q


def calculate_cn_from_imperviousness(imperv_pct, hsg='C'):
    """
    Estimate Curve Number from imperviousness percentage and Hydrologic Soil Group
    
    Args:
        imperv_pct: Imperviousness percentage (0-100)
        hsg: Hydrologic Soil Group ('A', 'B', 'C', or 'D')
    
    Returns:
        Estimated Curve Number
    """
    # Base CN by HSG (for pervious areas)
    base_cn = {'A': 25, 'B': 45, 'C': 60, 'D': 70}
    
    # Adjust for imperviousness
    cn = base_cn.get(hsg, 60) + (0.7 * imperv_pct)
    
    # Cap at 98 (fully impervious)
    return min(cn, 98)


def correlation_analysis(x, y, method='pearson'):
    """
    Perform correlation analysis between two variables
    
    Args:
        x: First variable (array-like)
        y: Second variable (array-like)
        method: 'pearson' or 'spearman'
    
    Returns:
        Dictionary with correlation coefficient and p-value
    """
    # Remove any NaN values
    mask = ~(np.isnan(x) | np.isnan(y))
    x_clean = np.array(x)[mask]
    y_clean = np.array(y)[mask]
    
    if len(x_clean) < 3:
        return {'r': np.nan, 'p_value': np.nan, 'n': len(x_clean)}
    
    if method == 'pearson':
        r, p = stats.pearsonr(x_clean, y_clean)
    elif method == 'spearman':
        r, p = stats.spearmanr(x_clean, y_clean)
    else:
        raise ValueError(f"Unknown method: {method}")
    
    return {'r': r, 'p_value': p, 'n': len(x_clean)}


def classify_vulnerability(score, low_threshold=3.34, high_threshold=6.67):
    """
    Classify vulnerability score into categories
    
    Args:
        score: Vulnerability score (0-10 scale)
        low_threshold: Upper bound for 'Low' category
        high_threshold: Upper bound for 'Moderate' category
    
    Returns:
        Category string: 'Low', 'Moderate', or 'High'
    """
    if np.isnan(score):
        return 'Unknown'
    elif score < low_threshold:
        return 'Low'
    elif score < high_threshold:
        return 'Moderate'
    else:
        return 'High'


def assign_quadrant(vuln_score, density, vuln_median, density_median):
    """
    Assign segment to quadrant based on vulnerability and infrastructure density
    
    Args:
        vuln_score: Vulnerability score
        density: Infrastructure density
        vuln_median: Median vulnerability for classification
        density_median: Median density for classification
    
    Returns:
        Quadrant label string
    """
    if vuln_score < vuln_median and density < density_median:
        return 'Q1_LowVuln_LowDensity'
    elif vuln_score < vuln_median and density >= density_median:
        return 'Q2_LowVuln_HighDensity'
    elif vuln_score >= vuln_median and density < density_median:
        return 'Q3_HighVuln_LowDensity'  # PRIORITY GAP
    else:
        return 'Q4_HighVuln_HighDensity'


def calculate_gap_index(vuln_score, density, adequacy_threshold=1500):
    """
    Calculate gap index between vulnerability and infrastructure adequacy
    
    Args:
        vuln_score: Vulnerability score (0-10 scale)
        density: Infrastructure density (sq ft/acre)
        adequacy_threshold: Threshold density for adequacy (sq ft/acre)
    
    Returns:
        Gap index value (higher = larger gap)
    """
    # Scale adequacy: 0 = meets threshold, negative values = below threshold
    adequacy_scaled = (density / adequacy_threshold * 10)
    adequacy_scaled = min(adequacy_scaled, 10)
    
    # Gap index: Vulnerability - Adequacy
    gap = vuln_score - adequacy_scaled
    
    return gap
