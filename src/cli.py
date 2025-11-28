"""
Command-line interface for A3DShell A3Dshell.

Provides CLI for running A3D simulation setup with support for both
.ini configuration files and command-line argument overrides.
"""

import argparse
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

from .config import ConfigManager, SimulationConfig
from .core.paths import PathManager
from .utils.logging import setup_logging

logger = logging.getLogger(__name__)


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        prog="a3dshell",
        description="A3DShell - Setup Alpine3D simulation environments",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Using .ini file
  python -m src.cli --config simulation.ini

  # Override with CLI args
  python -m src.cli --config simulation.ini --roi 2000 --gsd 5

  # Pure CLI (no .ini)
  python -m src.cli --name test_10m --poi-x 645000 --poi-y 115000 --poi-z 1500 \\
                     --roi 1000 --gsd 10 \\
                     --start 2023-10-01T00:00:00 --end 2023-10-31T23:59:59

  # Using shapefile
  python -m src.cli --config simulation.ini --use-shp-roi \\
                     --roi-shapefile /path/to/roi.shp
        """
    )

    # Configuration file
    parser.add_argument(
        "--config", "-c",
        type=Path,
        help="Path to .ini configuration file"
    )

    # General options
    parser.add_argument("--name", help="Simulation name")
    parser.add_argument("--start", help="Start date (YYYY-MM-DDTHH:MM:SS)")
    parser.add_argument("--end", help="End date (YYYY-MM-DDTHH:MM:SS)")

    # POI options
    parser.add_argument("--poi-x", type=float, help="POI Easting (EPSG:2056)")
    parser.add_argument("--poi-y", type=float, help="POI Northing (EPSG:2056)")
    parser.add_argument("--poi-z", type=float, help="POI Altitude (LV95)")

    # ROI options
    parser.add_argument("--use-shp-roi", action="store_true", help="Use shapefile for ROI")
    parser.add_argument("--roi-shapefile", type=Path, help="Path to ROI shapefile")
    parser.add_argument("--roi", type=int, help="ROI size in meters (bbox mode)")
    parser.add_argument("--buffer-size", type=int, help="Buffer size for IMIS selection (m)")

    # Output options
    parser.add_argument("--gsd", type=float, help="Grid spacing (m)")
    parser.add_argument("--gsd-ref", type=float, help="Reference DEM resolution (m)")
    parser.add_argument("--coord-sys", help="Output coordinate system")
    parser.add_argument("--mesh-fmt", help="Mesh format (vtu, vtk, stl)")

    # Processing options
    parser.add_argument("--skip-snowpack", action="store_true",
                       help="Skip Snowpack preprocessing")
    parser.add_argument("--no-horizon", action="store_true",
                       help="Skip horizon plotting")

    # Cache options
    parser.add_argument("--cache-dir", type=Path, help="Custom cache directory")
    parser.add_argument("--cache-info", action="store_true",
                       help="Show cache information and exit")
    parser.add_argument("--clear-cache", action="store_true",
                       help="Clear cache and exit")

    # Logging options
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level"
    )
    parser.add_argument("--log-file", type=Path, help="Log to file")

    # Utility options
    parser.add_argument("--create-template", type=Path,
                       help="Create template .ini file and exit")
    parser.add_argument("--version", action="version", version="A3DShell A3Dshell 0.1.0")

    return parser.parse_args()


def main() -> int:
    """
    Main entry point for CLI.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    args = parse_arguments()

    # Setup logging
    setup_logging(level=args.log_level, log_file=args.log_file)

    try:
        # Handle utility commands
        if args.create_template:
            ConfigManager.create_default_ini(args.create_template)
            print(f"Created template configuration: {args.create_template}")
            return 0

        # TODO: Implement cache info and clear cache
        if args.cache_info:
            print("Cache info not yet implemented")
            return 0

        if args.clear_cache:
            print("Clear cache not yet implemented")
            return 0

        # Prepare CLI overrides
        cli_overrides = {}
        if args.name:
            cli_overrides["simu_name"] = args.name
        if args.start:
            cli_overrides["start_date"] = datetime.strptime(args.start, '%Y-%m-%dT%H:%M:%S')
        if args.end:
            cli_overrides["end_date"] = datetime.strptime(args.end, '%Y-%m-%dT%H:%M:%S')
        if args.poi_x is not None:
            cli_overrides["poi_x"] = args.poi_x
        if args.poi_y is not None:
            cli_overrides["poi_y"] = args.poi_y
        if args.poi_z is not None:
            cli_overrides["poi_z"] = args.poi_z
        if args.use_shp_roi:
            cli_overrides["use_shp_roi"] = True
        if args.roi_shapefile:
            cli_overrides["roi_shapefile"] = str(args.roi_shapefile)
        if args.roi:
            cli_overrides["roi_size"] = args.roi
        if args.buffer_size:
            cli_overrides["buffer_size"] = args.buffer_size
        if args.gsd:
            cli_overrides["gsd"] = args.gsd
        if args.gsd_ref:
            cli_overrides["gsd_ref"] = args.gsd_ref
        if args.coord_sys:
            cli_overrides["out_coord_sys"] = args.coord_sys
        if args.mesh_fmt:
            cli_overrides["mesh_fmt"] = args.mesh_fmt
        if args.skip_snowpack:
            cli_overrides["run_snowpack"] = False
        if args.no_horizon:
            cli_overrides["plot_horizon"] = False

        # Load configuration
        logger.info("="*60)
        logger.info("A3DShell A3Dshell")
        logger.info("="*60)

        config_manager = ConfigManager(ini_file=args.config, cli_overrides=cli_overrides)
        config = config_manager.load_config()

        logger.info(f"Simulation: {config.simu_name}")
        logger.info(f"Mode: {config.dem_mode}")

        # Switzerland mode specific info
        if config.dem_mode == "swisstopo":
            logger.info(f"Period: {config.start_date} to {config.end_date}")
            logger.info(f"POI: {config.poi_x:.0f}E, {config.poi_y:.0f}N, {config.poi_z:.0f}m")
            logger.info(f"ROI: {'Shapefile' if config.use_shp_roi else f'{config.roi_size}m bbox'}")
            logger.info(f"GSD: {config.gsd}m (ref: {config.gsd_ref}m)")

        # Other Locations mode specific info
        elif config.dem_mode == "user_provided":
            logger.info(f"DEM: {config.user_dem_path}")
            logger.info(f"EPSG: {config.target_epsg}")
            if config.pois:
                logger.info(f"POIs: {len(config.pois)} defined")
            else:
                logger.info(f"POIs: None (optional)")

        # Run simulation orchestrator
        from .core.simulation import SimulationOrchestrator

        orchestrator = SimulationOrchestrator(config, source_ini=args.config)
        success = orchestrator.run()

        return 0 if success else 1

    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
        return 1

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
