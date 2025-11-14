"""
Configuration management for A3DShell A3Dshell.

Supports both .ini file configuration and CLI argument overrides.
"""

import configparser
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class SimulationConfig:
    """Configuration for A3D simulation."""

    # General
    simu_name: str
    start_date: datetime
    end_date: datetime

    # Point of Interest
    poi_x: float  # Easting EPSG:2056
    poi_y: float  # Northing EPSG:2056
    poi_z: float  # Altitude LV95

    # ROI
    use_shp_roi: bool = False
    roi_shapefile: Optional[str] = None  # Path to shapefile (if use_shp_roi=True)
    roi_size: int = 1000  # ROI size in meters (if use_shp_roi=False)
    buffer_size: int = 50000  # Buffer for IMIS station selection

    # Output
    out_coord_sys: str = "CH1903+"
    gsd: float = 10.0  # Grid spacing
    gsd_ref: float = 2.0  # Reference DEM resolution
    dem_add_fmt_list: List[str] = field(default_factory=lambda: [""])
    mesh_fmt: str = "vtu"

    # Maps
    plot_horizon: bool = True

    # A3D Parameters
    use_groundeye: bool = False
    use_lus_tlm: bool = True
    lus_prevah_cst: int = 11500
    do_pvp_3d: bool = False
    pvp_3d_fmt: str = ""

    # Preprocessing
    run_snowpack: bool = True  # Generate SMET files
    sp_bin: str = "snowpack"  # Snowpack binary path

    def __post_init__(self):
        """Validate configuration after initialization."""
        # Ensure dates are datetime objects
        if isinstance(self.start_date, str):
            self.start_date = datetime.strptime(self.start_date, '%Y-%m-%dT%H:%M:%S')
        if isinstance(self.end_date, str):
            self.end_date = datetime.strptime(self.end_date, '%Y-%m-%dT%H:%M:%S')

        # Validate simulation name
        if " " in self.simu_name:
            raise ValueError("Simulation name cannot contain whitespaces")

        # Validate date range
        if self.start_date >= self.end_date:
            raise ValueError("Start date must be before end date")

        # Check shapefile path if using shapefile ROI
        if self.use_shp_roi and not self.roi_shapefile:
            raise ValueError("ROI_SHAPEFILE must be specified when USE_SHP_ROI=true")

        if self.use_shp_roi and self.roi_shapefile:
            shp_path = Path(self.roi_shapefile)
            if not shp_path.exists():
                raise FileNotFoundError(f"Shapefile not found: {self.roi_shapefile}")


class ConfigManager:
    """Manages configuration loading from .ini files with CLI overrides."""

    def __init__(self, ini_file: Optional[Path] = None, cli_overrides: Optional[Dict[str, Any]] = None):
        """
        Initialize configuration manager.

        Args:
            ini_file: Path to .ini configuration file
            cli_overrides: Dictionary of CLI argument overrides
        """
        self.ini_file = Path(ini_file) if ini_file else None
        self.cli_overrides = cli_overrides or {}

        if self.ini_file and not self.ini_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {ini_file}")

    def load_config(self) -> SimulationConfig:
        """
        Load configuration from .ini file and apply CLI overrides.

        Returns:
            SimulationConfig object

        Raises:
            ValueError: If configuration is invalid
        """
        if self.ini_file:
            logger.info(f"Loading configuration from {self.ini_file}")
            config_dict = self._load_from_ini()
        else:
            logger.info("No .ini file provided, using CLI arguments only")
            config_dict = {}

        # Apply CLI overrides
        if self.cli_overrides:
            logger.info(f"Applying {len(self.cli_overrides)} CLI overrides")
            config_dict.update(self.cli_overrides)

        # Ensure required fields are present
        self._validate_required_fields(config_dict)

        # Create and return config object
        return SimulationConfig(**config_dict)

    def _load_from_ini(self) -> Dict[str, Any]:
        """Load configuration from .ini file."""
        config = configparser.ConfigParser(
            delimiters="=",
            inline_comment_prefixes=("#",)
        )
        config.read(self.ini_file)

        config_dict = {}

        # GENERAL section
        if "GENERAL" in config:
            section = config["GENERAL"]
            config_dict["simu_name"] = section["SIMULATION_NAME"]
            config_dict["start_date"] = datetime.strptime(
                section["START_DATE"], '%Y-%m-%dT%H:%M:%S'
            )
            config_dict["end_date"] = datetime.strptime(
                section["END_DATE"], '%Y-%m-%dT%H:%M:%S'
            )

        # INPUT section
        if "INPUT" in config:
            section = config["INPUT"]
            poi_x = float(section["EAST_epsg2056"])
            poi_y = float(section["NORTH_epsg2056"])

            # Auto-detect and convert old CH1903 coordinates to CH1903+ (EPSG:2056)
            # CH1903 coordinates are typically 5-6 digits (e.g., 645000, 115000)
            # CH1903+ coordinates are 7 digits (e.g., 2645000, 1115000)
            if poi_x < 1000000:
                logger.warning(f"Detected old CH1903 coordinates ({poi_x}, {poi_y})")
                logger.warning(f"Converting to CH1903+ (EPSG:2056): ({poi_x + 2000000}, {poi_y + 1000000})")
                poi_x += 2000000
                poi_y += 1000000

            config_dict["poi_x"] = poi_x
            config_dict["poi_y"] = poi_y
            config_dict["poi_z"] = float(section["altLV95"])
            config_dict["use_shp_roi"] = config.getboolean("INPUT", "USE_SHP_ROI")
            config_dict["roi_size"] = int(section.get("ROI", "1000"))
            config_dict["buffer_size"] = int(section.get("BUFFERSIZE", "50000"))

            # Check for ROI_SHAPEFILE
            if "ROI_SHAPEFILE" in section:
                config_dict["roi_shapefile"] = section["ROI_SHAPEFILE"]

        # OUTPUT section
        if "OUTPUT" in config:
            section = config["OUTPUT"]
            config_dict["out_coord_sys"] = section["OUT_COORDSYS"]
            config_dict["gsd"] = float(section["GSD"])
            config_dict["gsd_ref"] = float(section["GSD_ref"])
            config_dict["dem_add_fmt_list"] = [section.get("DEM_ADDFMTLIST", "")]
            config_dict["mesh_fmt"] = section.get("MESH_FMT", "vtu")

        # MAPS section
        if "MAPS" in config:
            config_dict["plot_horizon"] = config.getboolean("MAPS", "PLOT_HORIZON")

        # A3D section
        if "A3D" in config:
            section = config["A3D"]
            config_dict["use_groundeye"] = config.getboolean("A3D", "USE_GROUNDEYE")
            config_dict["use_lus_tlm"] = config.getboolean("A3D", "USE_LUS_TLM")
            config_dict["lus_prevah_cst"] = int(section.get("LUS_PREVAH_CST", "11500"))
            config_dict["do_pvp_3d"] = config.getboolean("A3D", "DO_PVP_3D")
            config_dict["pvp_3d_fmt"] = section.get("PVP_3D_FMT", "")

            # Snowpack binary
            if "SP_BIN_PATH" in section:
                config_dict["sp_bin"] = section["SP_BIN_PATH"]

        return config_dict

    def _validate_required_fields(self, config_dict: Dict[str, Any]) -> None:
        """
        Validate that all required fields are present.

        Args:
            config_dict: Configuration dictionary

        Raises:
            ValueError: If required fields are missing
        """
        required_fields = [
            "simu_name",
            "start_date",
            "end_date",
            "poi_x",
            "poi_y",
            "poi_z"
        ]

        missing_fields = [field for field in required_fields if field not in config_dict]

        if missing_fields:
            raise ValueError(
                f"Missing required configuration fields: {', '.join(missing_fields)}"
            )

    @staticmethod
    def create_default_ini(output_path: Path) -> None:
        """
        Create a default .ini configuration file.

        Args:
            output_path: Path where to save the .ini file
        """
        config = configparser.ConfigParser(delimiters="=")

        config["GENERAL"] = {
            "SIMULATION_NAME": "example_10m",
            "START_DATE": "2023-10-01T00:00:00",
            "END_DATE": "2023-10-31T23:59:59"
        }

        config["INPUT"] = {
            "EAST_epsg2056": "645000",
            "NORTH_epsg2056": "115000",
            "altLV95": "1500",
            "USE_SHP_ROI": "false",
            "ROI": "1000",
            "BUFFERSIZE": "50000",
            "# ROI_SHAPEFILE": "/path/to/roi.shp  # Uncomment and set path if USE_SHP_ROI=true"
        }

        config["OUTPUT"] = {
            "OUT_COORDSYS": "CH1903+",
            "GSD": "10.0",
            "GSD_ref": "2.0",
            "DEM_ADDFMTLIST": "tif",
            "MESH_FMT": "vtu"
        }

        config["MAPS"] = {
            "PLOT_HORIZON": "true"
        }

        config["A3D"] = {
            "USE_GROUNDEYE": "false",
            "USE_LUS_TLM": "true",
            "LUS_PREVAH_CST": "11500",
            "DO_PVP_3D": "false",
            "PVP_3D_FMT": "vtu",
            "SP_BIN_PATH": "snowpack"
        }

        with open(output_path, 'w') as f:
            config.write(f)

        logger.info(f"Created default configuration file: {output_path}")
