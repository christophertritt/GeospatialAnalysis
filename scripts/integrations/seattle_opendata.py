"""
Seattle Open Data Portal integration for green stormwater infrastructure.

This module fetches permeable pavement and GSI installations from Seattle's
ArcGIS REST API services managed by Seattle Public Utilities (SPU).

Citation: Janssen et al. (2012) "Benefits, Adoption Barriers and Myths of Open Data
and Open Government" for municipal open data integration patterns.

Seattle GeoData Portal: https://data-seattlecitygis.opendata.arcgis.com/
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import geopandas as gpd
import pandas as pd
import requests
from shapely.geometry import Point
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

# Seattle SPU DWW (Drainage and Wastewater) GIS Services
SEATTLE_GSI_SERVICES = {
    "permeable_pavement": {
        "url": "https://services.arcgis.com/ZOyb2t4B0UYuYNYH/arcgis/rest/services/SPU_GSI/FeatureServer/0",
        "name": "SPU Green Stormwater Infrastructure",
        "layer_id": 0
    },
    "rain_gardens": {
        "url": "https://services.arcgis.com/ZOyb2t4B0UYuYNYH/arcgis/rest/services/SPU_GSI/FeatureServer/1",
        "name": "Rain Gardens and Bioswales",
        "layer_id": 1
    },
    "permeable_pavement_proposed": {
        "url": "https://services.arcgis.com/ZOyb2t4B0UYuYNYH/arcgis/rest/services/SPU_GSI_Proposed/FeatureServer/0",
        "name": "Proposed Permeable Pavement",
        "layer_id": 0
    }
}

# Alternative/backup endpoints (Seattle GeoData portal may reorganize services)
BACKUP_ENDPOINTS = {
    "gsi_facilities": "https://data.seattle.gov/resource/j8jw-gxft.json",  # Socrata API
    "drainage_system": "https://data.seattle.gov/resource/5kkf-5n2x.json"
}


@dataclass(frozen=True)
class GSIFacility:
    """Green stormwater infrastructure facility record."""

    facility_id: str
    facility_type: str
    area_sqft: float
    install_date: Optional[datetime]
    status: str  # 'Active', 'Proposed', 'Under Construction'
    longitude: float
    latitude: float
    jurisdiction: str
    maintenance_freq: Optional[str]


class SeattleOpenDataClient:
    """
    Client for Seattle Open Data Portal ArcGIS REST services.

    No authentication required for public data access.

    Citation: Municipal data harmonization follows Craglia & Campagna (2010)
    "Advanced Regional SDI in Europe: Comparative Cost-Benefit Evaluation"
    """

    def __init__(
        self,
        session: Optional[requests.Session] = None,
        cache_dir: Optional[Path] = None
    ) -> None:
        """Initialize Seattle Open Data client."""

        self.session = session or requests.Session()
        self.session.headers.update({
            "User-Agent": "GeospatialAnalysis/1.0 (Rail Corridor Research)"
        })
        self.cache_dir = cache_dir or Path("data/raw/infrastructure/seattle")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _query_arcgis_service(
        self,
        service_url: str,
        where_clause: str = "1=1",
        out_fields: str = "*",
        geometry: Optional[Dict] = None
    ) -> Dict:
        """
        Query ArcGIS FeatureServer endpoint.

        Args:
            service_url: Base URL of FeatureServer layer
            where_clause: SQL WHERE clause for filtering
            out_fields: Comma-separated field names or '*'
            geometry: Optional geometry filter dict

        Returns:
            JSON response from service
        """

        url = f"{service_url}/query"

        params = {
            "where": where_clause,
            "outFields": out_fields,
            "f": "geojson",
            "returnGeometry": "true",
            "outSR": 4326  # WGS84
        }

        if geometry:
            params["geometry"] = str(geometry)
            params["geometryType"] = "esriGeometryEnvelope"
            params["spatialRel"] = "esriSpatialRelIntersects"

        response = self.session.get(url, params=params, timeout=60)
        response.raise_for_status()

        return response.json()

    def _query_socrata_api(
        self,
        dataset_id: str,
        limit: int = 50000,
        where_filter: Optional[str] = None
    ) -> List[Dict]:
        """
        Query Seattle Open Data Socrata API (backup method).

        Args:
            dataset_id: Socrata dataset identifier
            limit: Maximum records to return
            where_filter: Optional SoQL WHERE clause

        Returns:
            List of feature records
        """

        url = f"https://data.seattle.gov/resource/{dataset_id}.json"

        params = {
            "$limit": limit,
            "$order": ":id"
        }

        if where_filter:
            params["$where"] = where_filter

        response = self.session.get(url, params=params, timeout=60)
        response.raise_for_status()

        return response.json()

    def fetch_permeable_pavement(
        self,
        bbox: Optional[tuple] = None
    ) -> gpd.GeoDataFrame:
        """
        Fetch current permeable pavement installations from Seattle SPU.

        Args:
            bbox: Optional bounding box (minx, miny, maxx, maxy) in WGS84

        Returns:
            GeoDataFrame of permeable pavement facilities
        """

        service_url = SEATTLE_GSI_SERVICES["permeable_pavement"]["url"]

        geometry = None
        if bbox:
            geometry = {
                "xmin": bbox[0],
                "ymin": bbox[1],
                "xmax": bbox[2],
                "ymax": bbox[3],
                "spatialReference": {"wkid": 4326}
            }

        try:
            data = self._query_arcgis_service(service_url, geometry=geometry)
            gdf = gpd.GeoDataFrame.from_features(data["features"], crs="EPSG:4326")

            # Standardize column names
            gdf = self._standardize_columns(gdf, "permeable_pavement")

            return gdf

        except Exception as e:
            print(f"Warning: ArcGIS service failed, trying Socrata backup: {e}")
            return self._fetch_from_socrata_backup()

    def fetch_rain_gardens(
        self,
        bbox: Optional[tuple] = None
    ) -> gpd.GeoDataFrame:
        """
        Fetch rain garden and bioswale installations.

        Args:
            bbox: Optional bounding box filter

        Returns:
            GeoDataFrame of rain gardens
        """

        service_url = SEATTLE_GSI_SERVICES["rain_gardens"]["url"]

        geometry = None
        if bbox:
            geometry = {
                "xmin": bbox[0],
                "ymin": bbox[1],
                "xmax": bbox[2],
                "ymax": bbox[3],
                "spatialReference": {"wkid": 4326}
            }

        data = self._query_arcgis_service(service_url, geometry=geometry)
        gdf = gpd.GeoDataFrame.from_features(data["features"], crs="EPSG:4326")

        gdf = self._standardize_columns(gdf, "rain_garden")

        return gdf

    def fetch_proposed_infrastructure(
        self,
        bbox: Optional[tuple] = None
    ) -> gpd.GeoDataFrame:
        """
        Fetch proposed/planned permeable pavement projects.

        Args:
            bbox: Optional bounding box filter

        Returns:
            GeoDataFrame of proposed facilities
        """

        service_url = SEATTLE_GSI_SERVICES["permeable_pavement_proposed"]["url"]

        geometry = None
        if bbox:
            geometry = {
                "xmin": bbox[0],
                "ymin": bbox[1],
                "xmax": bbox[2],
                "ymax": bbox[3],
                "spatialReference": {"wkid": 4326}
            }

        try:
            data = self._query_arcgis_service(service_url, geometry=geometry)
            gdf = gpd.GeoDataFrame.from_features(data["features"], crs="EPSG:4326")

            gdf = self._standardize_columns(gdf, "proposed")
            gdf["status"] = "Proposed"

            return gdf

        except Exception as e:
            print(f"Note: No proposed infrastructure data available: {e}")
            return gpd.GeoDataFrame()

    def _standardize_columns(
        self,
        gdf: gpd.GeoDataFrame,
        facility_type: str
    ) -> gpd.GeoDataFrame:
        """
        Standardize column names across different Seattle datasets.

        Args:
            gdf: Input GeoDataFrame
            facility_type: Type of facility for classification

        Returns:
            GeoDataFrame with standardized schema
        """

        # Common column mappings (Seattle uses various naming conventions)
        column_map = {
            "OBJECTID": "facility_id",
            "ObjectId": "facility_id",
            "FID": "facility_id",
            "AreaSqFt": "area_sqft",
            "AREA_SQFT": "area_sqft",
            "Area": "area_sqft",
            "InstallDate": "installation_date",
            "INSTALL_DATE": "installation_date",
            "InstallYear": "installation_year",
            "Status": "status",
            "STATUS": "status",
            "Type": "pavement_type",
            "TYPE": "pavement_type",
            "Maintenance": "maintenance_freq",
            "MAINT_FREQ": "maintenance_freq"
        }

        gdf = gdf.rename(columns={
            k: v for k, v in column_map.items() if k in gdf.columns
        })

        # Add facility_type classification
        if "facility_type" not in gdf.columns:
            gdf["facility_type"] = facility_type

        # Add jurisdiction
        if "jurisdiction" not in gdf.columns:
            gdf["jurisdiction"] = "Seattle"

        # Ensure required columns exist
        for col in ["facility_id", "area_sqft", "installation_date", "status"]:
            if col not in gdf.columns:
                if col == "facility_id":
                    gdf["facility_id"] = range(1, len(gdf) + 1)
                elif col == "area_sqft":
                    gdf["area_sqft"] = 0.0
                elif col == "installation_date":
                    gdf["installation_date"] = pd.NaT
                elif col == "status":
                    gdf["status"] = "Active"

        # Parse installation dates
        if "installation_date" in gdf.columns:
            gdf["installation_date"] = pd.to_datetime(gdf["installation_date"], errors="coerce")

        return gdf

    def _fetch_from_socrata_backup(self) -> gpd.GeoDataFrame:
        """Fallback method using Socrata API if ArcGIS service unavailable."""

        try:
            records = self._query_socrata_api("j8jw-gxft")  # GSI facilities dataset ID

            if not records:
                return gpd.GeoDataFrame()

            # Parse Socrata records into GeoDataFrame
            geometries = []
            data = []

            for rec in records:
                if "location" in rec and "latitude" in rec["location"]:
                    lat = float(rec["location"]["latitude"])
                    lon = float(rec["location"]["longitude"])
                    geometries.append(Point(lon, lat))
                    data.append(rec)

            if not geometries:
                return gpd.GeoDataFrame()

            gdf = gpd.GeoDataFrame(data, geometry=geometries, crs="EPSG:4326")
            gdf = self._standardize_columns(gdf, "gsi_facility")

            return gdf

        except Exception as e:
            print(f"Warning: Socrata backup also failed: {e}")
            return gpd.GeoDataFrame()

    def fetch_all_seattle_gsi(
        self,
        bbox: Optional[tuple] = None,
        include_proposed: bool = False
    ) -> gpd.GeoDataFrame:
        """
        Fetch all Seattle GSI facilities and combine into single dataset.

        Args:
            bbox: Optional bounding box filter
            include_proposed: Whether to include proposed facilities

        Returns:
            Combined GeoDataFrame of all facilities
        """

        datasets = []

        # Fetch permeable pavement
        print("Fetching Seattle permeable pavement installations...")
        pp = self.fetch_permeable_pavement(bbox)
        if not pp.empty:
            datasets.append(pp)
            print(f"  Found {len(pp)} permeable pavement installations")

        # Fetch rain gardens
        print("Fetching Seattle rain gardens and bioswales...")
        rg = self.fetch_rain_gardens(bbox)
        if not rg.empty:
            datasets.append(rg)
            print(f"  Found {len(rg)} rain gardens/bioswales")

        # Fetch proposed (optional)
        if include_proposed:
            print("Fetching proposed Seattle GSI projects...")
            prop = self.fetch_proposed_infrastructure(bbox)
            if not prop.empty:
                datasets.append(prop)
                print(f"  Found {len(prop)} proposed projects")

        if not datasets:
            print("Warning: No Seattle GSI data retrieved")
            return gpd.GeoDataFrame()

        # Combine all datasets
        combined = pd.concat(datasets, ignore_index=True)

        print(f"\nTotal Seattle GSI facilities: {len(combined)}")

        return combined

    def cross_reference_with_corridor(
        self,
        gsi_gdf: gpd.GeoDataFrame,
        corridor_gdf: gpd.GeoDataFrame,
        buffer_meters: int = 250
    ) -> gpd.GeoDataFrame:
        """
        Filter GSI facilities to those within corridor buffer.

        Citation: Buffer methodology follows Ewing & Cervero (2010)
        "Travel and the built environment: A meta-analysis"

        Args:
            gsi_gdf: GeoDataFrame of GSI facilities
            corridor_gdf: GeoDataFrame of rail corridor
            buffer_meters: Buffer distance in meters

        Returns:
            GeoDataFrame of facilities within corridor buffer
        """

        # Project to Washington State Plane South (EPSG:2927) for accurate distances
        gsi_proj = gsi_gdf.to_crs(2927)
        corridor_proj = corridor_gdf.to_crs(2927)

        # Buffer corridor
        corridor_buffered = corridor_proj.buffer(buffer_meters * 3.28084)  # meters to feet

        # Spatial join to find facilities within buffer
        within_corridor = gpd.sjoin(
            gsi_proj,
            gpd.GeoDataFrame(geometry=corridor_buffered, crs=2927),
            how="inner",
            predicate="within"
        )

        # Convert back to WGS84
        within_corridor = within_corridor.to_crs(4326)

        print(f"\nFacilities within {buffer_meters}m corridor buffer: {len(within_corridor)}")

        return within_corridor

    def save_to_cache(
        self,
        gdf: gpd.GeoDataFrame,
        filename: str
    ) -> Path:
        """
        Save GeoDataFrame to local cache.

        Args:
            gdf: GeoDataFrame to save
            filename: Output filename (without extension)

        Returns:
            Path to saved file
        """

        output_path = self.cache_dir / f"{filename}.gpkg"
        gdf.to_file(output_path, driver="GPKG", layer=filename)

        print(f"Saved to cache: {output_path}")

        return output_path

    def persist_to_postgres(
        self,
        gdf: gpd.GeoDataFrame,
        table_name: str,
        engine_url: str
    ) -> None:
        """
        Persist GSI data to PostgreSQL/PostGIS.

        Args:
            gdf: GeoDataFrame to persist
            table_name: Target table name
            engine_url: SQLAlchemy connection string
        """

        if gdf.empty:
            return

        engine: Engine = create_engine(engine_url, future=True)

        try:
            # Convert to WKT for PostGIS compatibility
            gdf_copy = gdf.copy()
            gdf_copy["geometry"] = gdf_copy["geometry"].apply(lambda x: x.wkt)

            gdf_copy.to_sql(table_name, engine, if_exists="append", index=False)

        except SQLAlchemyError as exc:
            raise RuntimeError(f"Failed to insert into {table_name}: {exc}") from exc

    def ingest_weekly_update(
        self,
        corridor_gdf: gpd.GeoDataFrame,
        buffer_meters: int,
        engine_url: str
    ) -> None:
        """
        Fetch latest Seattle GSI data and update database.

        This method is designed to be called by automated scheduler.

        Args:
            corridor_gdf: Rail corridor geometry
            buffer_meters: Buffer distance
            engine_url: PostgreSQL connection string
        """

        # Fetch all current GSI
        gsi = self.fetch_all_seattle_gsi(include_proposed=False)

        if gsi.empty:
            print("Warning: No Seattle GSI data retrieved during weekly update")
            return

        # Filter to corridor
        corridor_gsi = self.cross_reference_with_corridor(gsi, corridor_gdf, buffer_meters)

        # Add fetch timestamp
        corridor_gsi["fetch_date"] = datetime.now()

        # Persist to database
        self.persist_to_postgres(corridor_gsi, "seattle_gsi_weekly", engine_url)

        # Also save to cache
        self.save_to_cache(corridor_gsi, f"seattle_gsi_{datetime.now().strftime('%Y%m%d')}")
