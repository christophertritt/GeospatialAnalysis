"""
Automated data pipeline scheduler for Seattle-Tacoma corridor analysis.

This module orchestrates scheduled data updates from all API sources:
- Monthly: NOAA precipitation updates, NWS climate scenarios
- Weekly: USGS streamgage data, Seattle open data portal
- Quarterly: Full jurisdiction data refresh

Citation: Boettiger (2015) "An introduction to Docker for reproducible research"
and National Academies (2019) "Reproducibility and Replicability in Science"
for data pipeline automation principles.

Usage:
    python scripts/data_pipeline_scheduler.py --config config.yaml --daemon

Requirements:
    - APScheduler>=3.10.4
    - PostgreSQL/PostGIS database for data storage
    - API tokens (NOAA CDO only)
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import geopandas as gpd
import yaml
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

# Import integration clients
from integrations.noaa_cdo import NOAACDOClient
from integrations.usgs_water import USGSWaterServicesClient
from integrations.seattle_opendata import SeattleOpenDataClient
from integrations.nws_forecast import NWSForecastClient
from integrations.multi_jurisdiction import MultiJurisdictionConsolidator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_pipeline.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class DataPipelineScheduler:
    """
    Orchestrates automated data updates for all API integrations.

    Citation: Automation methodology follows National Academies (2019)
    "Reproducibility and Replicability in Science" for reproducible
    data pipeline design.
    """

    def __init__(self, config_path: str) -> None:
        """
        Initialize scheduler with configuration.

        Args:
            config_path: Path to YAML configuration file
        """

        self.config = self._load_config(config_path)
        self.scheduler = BlockingScheduler()

        # Initialize API clients
        self._init_clients()

        # Load corridor geometry (cached)
        self.corridor_gdf = self._load_corridor_geometry()

        logger.info("Data pipeline scheduler initialized")

    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file."""

        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        logger.info(f"Configuration loaded from {config_path}")

        return config

    def _init_clients(self) -> None:
        """Initialize all API clients."""

        # NOAA CDO (requires token)
        noaa_token = self.config.get('noaa_cdo_token')
        if noaa_token:
            self.noaa_client = NOAACDOClient(token=noaa_token)
            logger.info("NOAA CDO client initialized")
        else:
            self.noaa_client = None
            logger.warning("NOAA CDO token not configured - skipping NOAA updates")

        # USGS (no auth required)
        self.usgs_client = USGSWaterServicesClient()
        logger.info("USGS Water Services client initialized")

        # Seattle Open Data (no auth required)
        self.seattle_client = SeattleOpenDataClient()
        logger.info("Seattle Open Data client initialized")

        # NWS (no auth required)
        self.nws_client = NWSForecastClient()
        logger.info("NWS Forecast client initialized")

        # Multi-jurisdiction consolidator
        self.multi_juris = MultiJurisdictionConsolidator()
        logger.info("Multi-jurisdiction consolidator initialized")

    def _load_corridor_geometry(self) -> Optional[gpd.GeoDataFrame]:
        """Load rail corridor geometry from outputs."""

        corridor_paths = [
            Path("data/outputs/rail_corridor.gpkg"),
            Path("data/outputs_final/rail_corridor.gpkg"),
            Path("data/raw/rail/corridor.gpkg"),
            Path("data/raw/rail/osm_rail.gpkg")
        ]

        for path in corridor_paths:
            if path.exists():
                try:
                    gdf = gpd.read_file(path)
                    logger.info(f"Corridor geometry loaded from {path}")
                    return gdf
                except Exception as e:
                    logger.warning(f"Could not load {path}: {e}")

        logger.warning("Could not load corridor geometry - some filters unavailable")
        return None

    # -------------------------------------------------------------------------
    # Monthly Jobs
    # -------------------------------------------------------------------------

    def monthly_noaa_precipitation_update(self) -> None:
        """
        Fetch previous month's precipitation data from NOAA CDO.

        Schedule: 1st of each month at 2:00 AM
        """

        if not self.noaa_client:
            logger.warning("NOAA client not configured - skipping")
            return

        try:
            logger.info("Starting monthly NOAA precipitation update...")

            engine_url = self.config['database_url']

            # Calculate reference month (previous month)
            now = datetime.now()
            ref_month = now.replace(day=1) - pd.Timedelta(days=1)

            # Ingest data
            self.noaa_client.ingest_monthly_update(ref_month.date(), engine_url)

            logger.info(f"Monthly NOAA update completed for {ref_month.strftime('%Y-%m')}")

        except Exception as e:
            logger.error(f"Monthly NOAA update failed: {e}", exc_info=True)

    def monthly_nws_climate_scenarios(self) -> None:
        """
        Generate climate change scenario projections.

        Schedule: 1st of each month at 3:00 AM
        """

        try:
            logger.info("Generating monthly climate scenarios...")

            # Load latest segment analysis
            segments_path = Path("data/outputs_final/analysis_segments.gpkg")
            if not segments_path.exists():
                logger.warning("Analysis segments not found - skipping climate scenarios")
                return

            segments = gpd.read_file(segments_path)

            engine_url = self.config['database_url']

            # Generate and store scenarios
            self.nws_client.ingest_monthly_climate_scenarios(segments, engine_url)

            logger.info("Monthly climate scenarios completed")

        except Exception as e:
            logger.error(f"Monthly climate scenarios failed: {e}", exc_info=True)

    # -------------------------------------------------------------------------
    # Weekly Jobs
    # -------------------------------------------------------------------------

    def weekly_usgs_streamgage_update(self) -> None:
        """
        Fetch latest week of USGS streamgage data.

        Schedule: Every Monday at 1:00 AM
        """

        try:
            logger.info("Starting weekly USGS streamgage update...")

            engine_url = self.config['database_url']

            # Ingest data
            self.usgs_client.ingest_weekly_update(engine_url)

            logger.info("Weekly USGS update completed")

        except Exception as e:
            logger.error(f"Weekly USGS update failed: {e}", exc_info=True)

    def weekly_seattle_opendata_update(self) -> None:
        """
        Fetch latest Seattle GSI installations.

        Schedule: Every Monday at 2:00 AM
        """

        if not self.corridor_gdf:
            logger.warning("Corridor geometry not available - skipping Seattle update")
            return

        try:
            logger.info("Starting weekly Seattle Open Data update...")

            buffer_meters = self.config.get('buffer_distance_m', 250)
            engine_url = self.config['database_url']

            # Ingest data
            self.seattle_client.ingest_weekly_update(
                self.corridor_gdf,
                buffer_meters,
                engine_url
            )

            logger.info("Weekly Seattle update completed")

        except Exception as e:
            logger.error(f"Weekly Seattle update failed: {e}", exc_info=True)

    # -------------------------------------------------------------------------
    # Quarterly Jobs
    # -------------------------------------------------------------------------

    def quarterly_full_jurisdiction_refresh(self) -> None:
        """
        Full refresh of all jurisdiction GSI data.

        Schedule: 1st of Jan, Apr, Jul, Oct at 4:00 AM
        """

        if not self.corridor_gdf:
            logger.warning("Corridor geometry not available - skipping quarterly refresh")
            return

        try:
            logger.info("Starting quarterly full jurisdiction refresh...")

            engine_url = self.config['database_url']

            # Full refresh
            self.multi_juris.ingest_quarterly_update(self.corridor_gdf, engine_url)

            logger.info("Quarterly jurisdiction refresh completed")

        except Exception as e:
            logger.error(f"Quarterly refresh failed: {e}", exc_info=True)

    # -------------------------------------------------------------------------
    # Scheduler Configuration
    # -------------------------------------------------------------------------

    def configure_schedules(self) -> None:
        """
        Configure all scheduled jobs.

        Citation: Schedule intervals follow data provider recommendations
        and research reproducibility best practices per National Academies (2019).
        """

        # Monthly jobs - 1st of month
        self.scheduler.add_job(
            self.monthly_noaa_precipitation_update,
            CronTrigger(day=1, hour=2, minute=0),
            id='monthly_noaa',
            name='Monthly NOAA Precipitation Update',
            replace_existing=True
        )

        self.scheduler.add_job(
            self.monthly_nws_climate_scenarios,
            CronTrigger(day=1, hour=3, minute=0),
            id='monthly_nws',
            name='Monthly NWS Climate Scenarios',
            replace_existing=True
        )

        # Weekly jobs - Every Monday
        self.scheduler.add_job(
            self.weekly_usgs_streamgage_update,
            CronTrigger(day_of_week='mon', hour=1, minute=0),
            id='weekly_usgs',
            name='Weekly USGS Streamgage Update',
            replace_existing=True
        )

        self.scheduler.add_job(
            self.weekly_seattle_opendata_update,
            CronTrigger(day_of_week='mon', hour=2, minute=0),
            id='weekly_seattle',
            name='Weekly Seattle Open Data Update',
            replace_existing=True
        )

        # Quarterly jobs - 1st of Jan, Apr, Jul, Oct
        self.scheduler.add_job(
            self.quarterly_full_jurisdiction_refresh,
            CronTrigger(month='1,4,7,10', day=1, hour=4, minute=0),
            id='quarterly_refresh',
            name='Quarterly Full Jurisdiction Refresh',
            replace_existing=True
        )

        logger.info("All schedules configured")
        self.print_schedule()

    def print_schedule(self) -> None:
        """Print configured schedule."""

        print("\n" + "="*70)
        print("CONFIGURED DATA PIPELINE SCHEDULE")
        print("="*70)

        print("\n📅 MONTHLY JOBS (1st of month)")
        print("  - 2:00 AM: NOAA precipitation update")
        print("  - 3:00 AM: NWS climate scenarios")

        print("\n📅 WEEKLY JOBS (Every Monday)")
        print("  - 1:00 AM: USGS streamgage data")
        print("  - 2:00 AM: Seattle open data portal")

        print("\n📅 QUARTERLY JOBS (Jan/Apr/Jul/Oct 1st)")
        print("  - 4:00 AM: Full jurisdiction data refresh")

        print("\n" + "="*70)

        # Print next run times
        print("\n⏰ NEXT SCHEDULED RUNS:")
        for job in self.scheduler.get_jobs():
            print(f"  - {job.name}: {job.next_run_time}")

        print("\n" + "="*70 + "\n")

    def run_job_now(self, job_name: str) -> None:
        """
        Manually run a specific job immediately.

        Args:
            job_name: Job identifier (monthly_noaa, weekly_usgs, etc.)
        """

        job_map = {
            'monthly_noaa': self.monthly_noaa_precipitation_update,
            'monthly_nws': self.monthly_nws_climate_scenarios,
            'weekly_usgs': self.weekly_usgs_streamgage_update,
            'weekly_seattle': self.weekly_seattle_opendata_update,
            'quarterly_refresh': self.quarterly_full_jurisdiction_refresh
        }

        job_func = job_map.get(job_name)

        if not job_func:
            logger.error(f"Unknown job: {job_name}")
            print(f"Available jobs: {', '.join(job_map.keys())}")
            return

        logger.info(f"Manually executing job: {job_name}")
        job_func()
        logger.info(f"Job {job_name} completed")

    def start(self) -> None:
        """Start the scheduler (blocking)."""

        logger.info("Starting data pipeline scheduler...")
        print("\n🚀 Data pipeline scheduler started")
        print("   Press Ctrl+C to stop\n")

        try:
            self.scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("Scheduler stopped by user")
            print("\n✓ Scheduler stopped gracefully\n")


def main():
    """Main entry point for scheduler."""

    parser = argparse.ArgumentParser(
        description='Automated data pipeline scheduler for Seattle-Tacoma corridor analysis'
    )

    parser.add_argument(
        '--config',
        type=str,
        default='config.yaml',
        help='Path to configuration YAML file'
    )

    parser.add_argument(
        '--daemon',
        action='store_true',
        help='Run scheduler as daemon (blocking)'
    )

    parser.add_argument(
        '--run-now',
        type=str,
        choices=['monthly_noaa', 'monthly_nws', 'weekly_usgs', 'weekly_seattle', 'quarterly_refresh'],
        help='Run specific job immediately (for testing)'
    )

    parser.add_argument(
        '--list-schedule',
        action='store_true',
        help='Print schedule and exit'
    )

    args = parser.parse_args()

    # Initialize scheduler
    scheduler = DataPipelineScheduler(args.config)
    scheduler.configure_schedules()

    # Handle different modes
    if args.list_schedule:
        scheduler.print_schedule()
        return

    if args.run_now:
        scheduler.run_job_now(args.run_now)
        return

    if args.daemon:
        scheduler.start()
    else:
        print("Use --daemon to start scheduler, --run-now to test a job, or --list-schedule to view schedule")


if __name__ == '__main__':
    main()
