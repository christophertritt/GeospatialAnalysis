"""
Multi-jurisdiction data consolidation for Seattle-Tacoma corridor.

This module fetches and harmonizes green stormwater infrastructure data from
all 9 jurisdictions along the rail corridor: Seattle, Tukwila, Kent, Auburn,
Sumner, Puyallup, Fife, Tacoma, and King County unincorporated areas.

Citation: Craglia & Campagna (2010) "Advanced Regional SDI in Europe: Comparative
Cost-Benefit Evaluation" for cross-boundary geospatial data integration.

CRITICAL: Per DATA_GAP_ANALYSIS.md, infrastructure data currently exists ONLY
for Seattle. This module is essential to answer the research question for the
full corridor.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import geopandas as gpd
import pandas as pd
import requests
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

# Data sources for each jurisdiction
# Per DATA_GAP_ANALYSIS.md Section 2: Infrastructure Data Review
JURISDICTION_SOURCES = {
    "Seattle": {
        "primary": "arcgis",
        "url": "https://data-seattlecitygis.opendata.arcgis.com/",
        "contact": "Seattle Public Utilities",
        "notes": "Complete - 169 facilities via SPU DWW services"
    },
    "Tukwila": {
        "primary": "direct_request",
        "contact": "Tukwila Public Works",
        "phone": "(206) 433-1800",
        "notes": "MISSING - requires data request"
    },
    "Renton": {
        "primary": "king_county",
        "contact": "Renton Utility Systems",
        "phone": "(425) 430-7400",
        "notes": "MISSING - may be in King County database or city records"
    },
    "Kent": {
        "primary": "king_county",
        "contact": "Kent Public Works",
        "phone": "(253) 856-5500",
        "notes": "MISSING - requires data request"
    },
    "Auburn": {
        "primary": "king_county",
        "contact": "Auburn Environmental Services",
        "phone": "(253) 931-3010",
        "notes": "MISSING - requires data request"
    },
    "Sumner": {
        "primary": "pierce_county",
        "contact": "Sumner Public Works",
        "phone": "(253) 299-5678",
        "notes": "MISSING - requires data request"
    },
    "Puyallup": {
        "primary": "pierce_county",
        "contact": "Puyallup Public Works",
        "phone": "(253) 864-4165",
        "notes": "MISSING - requires data request"
    },
    "Fife": {
        "primary": "pierce_county",
        "contact": "Fife Public Works",
        "phone": "(253) 896-8560",
        "notes": "MISSING - requires data request"
    },
    "Tacoma": {
        "primary": "arcgis",
        "url": "https://data.cityoftacoma.org/",
        "contact": "Tacoma Environmental Services",
        "phone": "(253) 502-2100",
        "notes": "MISSING - check Tacoma Open Data Portal"
    },
    "King County (Unincorporated)": {
        "primary": "king_county",
        "url": "https://gis-kingcounty.opendata.arcgis.com/",
        "contact": "WLRD-GIS@kingcounty.gov",
        "notes": "MISSING - contact King County WLRD"
    }
}

# County-level data sources
COUNTY_SOURCES = {
    "King County": {
        "url": "https://gis-kingcounty.opendata.arcgis.com/",
        "contact_email": "WLRD-GIS@kingcounty.gov",
        "datasets": [
            "King County GSI Facilities",
            "Surface Water Management Projects",
            "NPDES Stormwater Facilities"
        ]
    },
    "Pierce County": {
        "url": "https://gisdata-piercecowa.opendata.arcgis.com/",
        "contact_phone": "(253) 798-7470",
        "datasets": [
            "Stormwater Facilities",
            "Low Impact Development (LID) Projects",
            "Green Infrastructure Inventory"
        ]
    }
}

# Standardized schema for unified dataset
STANDARD_SCHEMA = {
    "facility_id": "string",  # Unique identifier
    "jurisdiction": "string",  # City/county name
    "facility_type": "string",  # permeable_pavement, rain_garden, bioswale, etc.
    "pavement_type": "string",  # pervious_concrete, porous_asphalt, PICP, other
    "area_sqft": "float",  # Facility area in square feet
    "installation_date": "datetime",  # Installation date
    "installation_year": "int",  # Year installed
    "status": "string",  # Active, Proposed, Under Construction, Decommissioned
    "maintenance_freq": "string",  # Annual, Semi-Annual, Quarterly, As-Needed
    "maintenance_records": "string",  # JSON or text field with maintenance history
    "design_infiltration_rate": "float",  # Design infiltration rate (in/hr)
    "storage_capacity_cf": "float",  # Storage capacity in cubic feet
    "longitude": "float",
    "latitude": "float",
    "data_source": "string",  # Source of data for provenance
    "fetch_date": "datetime",  # When data was acquired
    "geometry": "geometry"  # Point or Polygon
}


@dataclass(frozen=True)
class DataAcquisitionStatus:
    """Status of data acquisition for a jurisdiction."""

    jurisdiction: str
    status: str  # 'complete', 'partial', 'missing', 'in_progress'
    facility_count: int
    data_source: str
    last_updated: datetime
    notes: str


class MultiJurisdictionConsolidator:
    """
    Consolidate GSI data from all jurisdictions in Seattle-Tacoma corridor.

    Citation: Schema harmonization follows Craglia & Campagna (2010) for
    cross-boundary geospatial data integration standards.
    """

    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        session: Optional[requests.Session] = None
    ) -> None:
        """Initialize multi-jurisdiction consolidator."""

        self.cache_dir = cache_dir or Path("data/processed/infrastructure")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.session = session or requests.Session()
        self.session.headers.update({
            "User-Agent": "GeospatialAnalysis/1.0 (Rail Corridor Research)"
        })

        self.acquisition_log: List[DataAcquisitionStatus] = []

    def fetch_king_county_gsi(
        self,
        bbox: Optional[tuple] = None
    ) -> gpd.GeoDataFrame:
        """
        Fetch GSI data from King County open data portal.

        Covers: Tukwila, Renton (partial), Kent, Auburn, unincorporated areas

        Args:
            bbox: Optional bounding box filter

        Returns:
            GeoDataFrame of King County GSI facilities
        """

        # King County ArcGIS REST endpoint (example - actual URL may differ)
        base_url = "https://gis-kingcounty.opendata.arcgis.com/api/v3"

        print("Attempting to fetch King County GSI data...")
        print("⚠️  IMPLEMENTATION NOTE: Actual King County GSI layer ID required")
        print("   Contact: WLRD-GIS@kingcounty.gov")
        print("   Search for: 'green stormwater infrastructure', 'permeable pavement', 'LID'")

        # Placeholder - actual implementation requires correct layer ID
        # This demonstrates the approach
        try:
            # Example query structure for ArcGIS REST
            # Actual implementation would use correct service URL and layer ID
            params = {
                "where": "1=1",
                "outFields": "*",
                "f": "geojson",
                "returnGeometry": "true"
            }

            # NOTE: Replace with actual King County GSI service URL
            # url = f"{base_url}/datasets/KING_COUNTY_GSI_LAYER_ID/FeatureServer/0/query"
            # response = self.session.get(url, params=params, timeout=60)
            # response.raise_for_status()
            # data = response.json()
            # gdf = gpd.GeoDataFrame.from_features(data["features"], crs="EPSG:4326")

            # For now, return empty GeoDataFrame with correct schema
            gdf = self._create_empty_standard_gdf()
            gdf["jurisdiction"] = "King County"

            self._log_acquisition("King County", "missing", 0,
                                 "Requires data request to WLRD-GIS@kingcounty.gov")

            return gdf

        except Exception as e:
            print(f"Warning: Could not fetch King County data: {e}")
            return self._create_empty_standard_gdf()

    def fetch_pierce_county_gsi(
        self,
        bbox: Optional[tuple] = None
    ) -> gpd.GeoDataFrame:
        """
        Fetch GSI data from Pierce County open data portal.

        Covers: Sumner, Puyallup, Fife, unincorporated areas

        Args:
            bbox: Optional bounding box filter

        Returns:
            GeoDataFrame of Pierce County GSI facilities
        """

        base_url = "https://gisdata-piercecowa.opendata.arcgis.com"

        print("Attempting to fetch Pierce County GSI data...")
        print("⚠️  IMPLEMENTATION NOTE: Actual Pierce County stormwater layer ID required")
        print("   Contact: Pierce County Public Works (253) 798-7470")
        print("   Search for: 'stormwater facilities', 'LID', 'green infrastructure'")

        # Placeholder - actual implementation requires correct layer ID
        try:
            gdf = self._create_empty_standard_gdf()
            gdf["jurisdiction"] = "Pierce County"

            self._log_acquisition("Pierce County", "missing", 0,
                                 "Requires data request to Pierce County Public Works")

            return gdf

        except Exception as e:
            print(f"Warning: Could not fetch Pierce County data: {e}")
            return self._create_empty_standard_gdf()

    def fetch_tacoma_gsi(
        self,
        bbox: Optional[tuple] = None
    ) -> gpd.GeoDataFrame:
        """
        Fetch GSI data from City of Tacoma open data portal.

        Args:
            bbox: Optional bounding box filter

        Returns:
            GeoDataFrame of Tacoma GSI facilities
        """

        base_url = "https://data.cityoftacoma.org"

        print("Attempting to fetch Tacoma GSI data...")
        print("⚠️  IMPLEMENTATION NOTE: Actual Tacoma stormwater layer required")
        print("   Contact: Tacoma Environmental Services (253) 502-2100")
        print("   Check: https://data.cityoftacoma.org/ for 'Stormwater Facilities'")

        # Placeholder
        try:
            gdf = self._create_empty_standard_gdf()
            gdf["jurisdiction"] = "Tacoma"

            self._log_acquisition("Tacoma", "missing", 0,
                                 "Check Tacoma Open Data Portal for GSI inventory")

            return gdf

        except Exception as e:
            print(f"Warning: Could not fetch Tacoma data: {e}")
            return self._create_empty_standard_gdf()

    def fetch_all_jurisdictions(
        self,
        corridor_gdf: Optional[gpd.GeoDataFrame] = None,
        buffer_meters: int = 500
    ) -> gpd.GeoDataFrame:
        """
        Fetch GSI data from all 9 jurisdictions and consolidate.

        This is the primary method for complete corridor analysis.

        Args:
            corridor_gdf: Optional corridor geometry for spatial filtering
            buffer_meters: Buffer distance for corridor filtering

        Returns:
            Unified GeoDataFrame with standardized schema
        """

        print("\n" + "="*70)
        print("MULTI-JURISDICTION GSI DATA CONSOLIDATION")
        print("="*70)
        print("\nFetching data from all jurisdictions along Seattle-Tacoma corridor...")

        datasets = []

        # 1. Seattle (COMPLETE via existing integration)
        from scripts.integrations.seattle_opendata import SeattleOpenDataClient

        seattle_client = SeattleOpenDataClient()
        seattle_gsi = seattle_client.fetch_all_seattle_gsi()

        if not seattle_gsi.empty:
            seattle_std = self._standardize_schema(seattle_gsi, "Seattle")
            datasets.append(seattle_std)
            self._log_acquisition("Seattle", "complete", len(seattle_std),
                                 "Seattle Open Data Portal - SPU DWW services")
            print(f"✓ Seattle: {len(seattle_std)} facilities")
        else:
            print("✗ Seattle: No data retrieved")

        # 2. King County (covers Tukwila, Kent, Auburn, Renton)
        king_county_gsi = self.fetch_king_county_gsi()
        if not king_county_gsi.empty:
            datasets.append(king_county_gsi)
            print(f"✓ King County: {len(king_county_gsi)} facilities")
        else:
            print("✗ King County: No data available - REQUIRES DATA REQUEST")

        # 3. Pierce County (covers Sumner, Puyallup, Fife)
        pierce_county_gsi = self.fetch_pierce_county_gsi()
        if not pierce_county_gsi.empty:
            datasets.append(pierce_county_gsi)
            print(f"✓ Pierce County: {len(pierce_county_gsi)} facilities")
        else:
            print("✗ Pierce County: No data available - REQUIRES DATA REQUEST")

        # 4. Tacoma
        tacoma_gsi = self.fetch_tacoma_gsi()
        if not tacoma_gsi.empty:
            datasets.append(tacoma_gsi)
            print(f"✓ Tacoma: {len(tacoma_gsi)} facilities")
        else:
            print("✗ Tacoma: No data available - CHECK TACOMA OPEN DATA PORTAL")

        # Consolidate all datasets
        if not datasets:
            print("\n❌ ERROR: No GSI data available from any jurisdiction")
            print("   Cannot answer research question without infrastructure data")
            return self._create_empty_standard_gdf()

        consolidated = pd.concat(datasets, ignore_index=True)

        print(f"\n{'='*70}")
        print(f"CONSOLIDATION SUMMARY")
        print(f"{'='*70}")
        print(f"Total facilities: {len(consolidated)}")
        print(f"\nBy Jurisdiction:")
        print(consolidated["jurisdiction"].value_counts())

        # Filter to corridor if provided
        if corridor_gdf is not None and not consolidated.empty:
            print(f"\nFiltering to {buffer_meters}m corridor buffer...")
            consolidated = self._filter_to_corridor(consolidated, corridor_gdf, buffer_meters)
            print(f"Facilities within corridor: {len(consolidated)}")

        return consolidated

    def _standardize_schema(
        self,
        gdf: gpd.GeoDataFrame,
        jurisdiction: str
    ) -> gpd.GeoDataFrame:
        """
        Standardize GeoDataFrame to unified schema.

        Args:
            gdf: Input GeoDataFrame
            jurisdiction: Jurisdiction name

        Returns:
            Standardized GeoDataFrame
        """

        std_gdf = gdf.copy()

        # Ensure all required columns exist
        for col, dtype in STANDARD_SCHEMA.items():
            if col == "geometry":
                continue

            if col not in std_gdf.columns:
                if dtype == "string":
                    std_gdf[col] = ""
                elif dtype == "float":
                    std_gdf[col] = 0.0
                elif dtype == "int":
                    std_gdf[col] = 0
                elif dtype == "datetime":
                    std_gdf[col] = pd.NaT

        # Set jurisdiction
        std_gdf["jurisdiction"] = jurisdiction

        # Extract coordinates from geometry
        if "longitude" not in std_gdf.columns or "latitude" not in std_gdf.columns:
            centroids = std_gdf.geometry.centroid
            std_gdf["longitude"] = centroids.x
            std_gdf["latitude"] = centroids.y

        # Add provenance
        std_gdf["fetch_date"] = datetime.now()

        # Select only standard schema columns (in order)
        schema_cols = [c for c in STANDARD_SCHEMA.keys() if c != "geometry"]
        schema_cols.append("geometry")

        return std_gdf[[c for c in schema_cols if c in std_gdf.columns]]

    def _filter_to_corridor(
        self,
        gdf: gpd.GeoDataFrame,
        corridor_gdf: gpd.GeoDataFrame,
        buffer_meters: int
    ) -> gpd.GeoDataFrame:
        """Filter facilities to corridor buffer."""

        # Project to WA State Plane South for accurate distances
        gdf_proj = gdf.to_crs(2927)
        corridor_proj = corridor_gdf.to_crs(2927)

        # Buffer corridor
        corridor_buffered = corridor_proj.buffer(buffer_meters * 3.28084)  # m to ft

        # Spatial filter
        within = gpd.sjoin(
            gdf_proj,
            gpd.GeoDataFrame(geometry=corridor_buffered, crs=2927),
            how="inner",
            predicate="within"
        )

        return within.to_crs(4326)

    def _create_empty_standard_gdf(self) -> gpd.GeoDataFrame:
        """Create empty GeoDataFrame with standard schema."""

        return gpd.GeoDataFrame(
            columns=list(STANDARD_SCHEMA.keys()),
            crs="EPSG:4326"
        )

    def _log_acquisition(
        self,
        jurisdiction: str,
        status: str,
        count: int,
        notes: str
    ) -> None:
        """Log data acquisition status."""

        log_entry = DataAcquisitionStatus(
            jurisdiction=jurisdiction,
            status=status,
            facility_count=count,
            data_source=JURISDICTION_SOURCES.get(jurisdiction, {}).get("primary", "unknown"),
            last_updated=datetime.now(),
            notes=notes
        )

        self.acquisition_log.append(log_entry)

    def generate_acquisition_report(self) -> pd.DataFrame:
        """
        Generate report on data acquisition status.

        This report identifies which jurisdictions lack data.

        Returns:
            DataFrame with acquisition status for all jurisdictions
        """

        report_data = []

        for jurisdiction, source_info in JURISDICTION_SOURCES.items():
            # Find acquisition log entry if exists
            log_entry = next(
                (log for log in self.acquisition_log if log.jurisdiction == jurisdiction),
                None
            )

            if log_entry:
                report_data.append({
                    "jurisdiction": jurisdiction,
                    "status": log_entry.status,
                    "facility_count": log_entry.facility_count,
                    "data_source": log_entry.data_source,
                    "contact": source_info.get("contact", ""),
                    "phone": source_info.get("phone", ""),
                    "notes": log_entry.notes
                })
            else:
                report_data.append({
                    "jurisdiction": jurisdiction,
                    "status": "not_attempted",
                    "facility_count": 0,
                    "data_source": source_info.get("primary", ""),
                    "contact": source_info.get("contact", ""),
                    "phone": source_info.get("phone", ""),
                    "notes": source_info.get("notes", "")
                })

        return pd.DataFrame(report_data)

    def save_consolidated_data(
        self,
        gdf: gpd.GeoDataFrame,
        filename: str = "infrastructure_consolidated"
    ) -> Path:
        """
        Save consolidated dataset to GeoPackage.

        Args:
            gdf: Consolidated GeoDataFrame
            filename: Output filename (without extension)

        Returns:
            Path to saved file
        """

        output_path = self.cache_dir / f"{filename}.gpkg"
        gdf.to_file(output_path, driver="GPKG", layer="infrastructure")

        print(f"\nConsolidated data saved: {output_path}")

        return output_path

    def persist_to_postgres(
        self,
        gdf: gpd.GeoDataFrame,
        table_name: str,
        engine_url: str
    ) -> None:
        """
        Persist consolidated data to PostgreSQL/PostGIS.

        Args:
            gdf: Consolidated GeoDataFrame
            table_name: Target table name
            engine_url: SQLAlchemy connection string
        """

        if gdf.empty:
            print("Warning: No data to persist")
            return

        engine: Engine = create_engine(engine_url, future=True)

        try:
            # Convert geometry to WKT for PostGIS
            gdf_copy = gdf.copy()
            gdf_copy["geometry"] = gdf_copy["geometry"].apply(lambda x: x.wkt)

            gdf_copy.to_sql(table_name, engine, if_exists="replace", index=False)

            print(f"Data persisted to {table_name} table")

        except SQLAlchemyError as exc:
            raise RuntimeError(f"Failed to persist to {table_name}: {exc}") from exc

    def ingest_quarterly_update(
        self,
        corridor_gdf: gpd.GeoDataFrame,
        engine_url: str
    ) -> None:
        """
        Quarterly full refresh of all jurisdiction data.

        This method is designed to be called by automated scheduler.

        Args:
            corridor_gdf: Rail corridor geometry
            engine_url: PostgreSQL connection string
        """

        print("Executing quarterly multi-jurisdiction data refresh...")

        # Fetch all data
        consolidated = self.fetch_all_jurisdictions(corridor_gdf)

        # Persist to database
        if not consolidated.empty:
            self.persist_to_postgres(consolidated, "infrastructure_consolidated", engine_url)

            # Also save local copy
            self.save_consolidated_data(
                consolidated,
                f"infrastructure_{datetime.now().strftime('%Y%m%d')}"
            )

        # Generate and save acquisition report
        report = self.generate_acquisition_report()
        report_path = self.cache_dir / f"acquisition_report_{datetime.now().strftime('%Y%m%d')}.csv"
        report.to_csv(report_path, index=False)

        print(f"Acquisition report saved: {report_path}")
