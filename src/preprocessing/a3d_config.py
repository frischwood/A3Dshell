"""
Alpine3D configuration for A3DShell A3Dshell.

Generates configuration files for Alpine3D simulations.
"""

import logging
import configparser
import pickle
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)

# Optional import
try:
    import jinja2
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False


class A3DConfigurator:
    """Handles Alpine3D configuration file generation."""

    def __init__(self, path_manager, config):
        """
        Initialize A3D configurator.

        Args:
            path_manager: Path manager instance
            config: Simulation configuration
        """
        self.paths = path_manager
        self.config = config

    def create_configuration(self, imis_stations, lus_file: Path) -> None:
        """
        Create complete A3D configuration.

        Args:
            imis_stations: GeoDataFrame of IMIS stations
            lus_file: Path to LUS file
        """
        logger.info("="*60)
        logger.info("Alpine3D Configuration")
        logger.info("="*60)

        # Create io.ini
        self._create_ini_file(imis_stations)

        # Create .sno files
        self._create_sno_files(lus_file, imis_stations)

        logger.info("="*60)

    def _create_ini_file(self, imis_stations) -> None:
        """
        Create A3D io.ini file.

        Args:
            imis_stations: GeoDataFrame of IMIS stations
        """
        logger.info("   Creating A3D io.ini")

        # Choose template based on complexity
        if self.config.use_groundeye:
            template_name = "a3dConfigComplex.ini"
        else:
            template_name = "a3dConfig.ini"

        template_ini = self.paths.input_templates / template_name

        if not template_ini.exists():
            logger.warning(f"   Template not found: {template_ini}")
            self._create_basic_ini(imis_stations)
            return

        # Load template
        config = configparser.ConfigParser(delimiters="=")
        config.read(template_ini)

        # Update configuration
        dem_file = self.paths.get_dem_file(self.config.gsd)
        lus_file = self.paths.get_lus_file(self.config.gsd)

        config["Output"]["EXPERIMENT"] = self.config.simu_name
        config["Input"]["DEMFILE"] = f"input/surface-grids/{dem_file.name}"
        config["Input"]["LANDUSEFILE"] = f"input/surface-grids/{lus_file.name}"
        config["Input"]["COORDSYS"] = self.config.out_coord_sys
        config["Output"]["COORDSYS"] = self.config.out_coord_sys
        config["Output"]["TIME_ZONE"] = "0"  # UTC

        # Set PVP file if using complex mode
        if self.config.use_groundeye:
            config["EBalance"]["PVPFILE"] = f"./input/surface-grids/{self.config.simu_name}.pv"
            config["EBalance"]["TERRAIN_RADIATION_METHOD"] = "COMPLEX"

        # Add station IDs
        for i, (_, station) in enumerate(imis_stations.iterrows(), 1):
            config["Input"][f"STATION{i}"] = station["ID"]

        # Write ini file
        ini_path = self.paths.get_simulation_dir() / "io.ini"
        with open(ini_path, 'w') as f:
            config.write(f)

        logger.info(f"   ✓ A3D io.ini created with {len(imis_stations)} stations")

    def _create_basic_ini(self, imis_stations) -> None:
        """Create basic A3D ini file without template."""
        config = configparser.ConfigParser(delimiters="=")

        dem_file = self.paths.get_dem_file(self.config.gsd)
        lus_file = self.paths.get_lus_file(self.config.gsd)

        config["General"] = {}
        config["Input"] = {
            "DEMFILE": f"input/surface-grids/{dem_file.name}",
            "LANDUSEFILE": f"input/surface-grids/{lus_file.name}",
            "METEOPATH": "./input/meteo",
            "SNOWPATH": "./input/snowfiles",
            "COORDSYS": self.config.out_coord_sys,
        }
        config["Output"] = {
            "EXPERIMENT": self.config.simu_name,
            "METEOPATH": "./output/meteo",
            "SNOWPATH": "./output/snowfiles",
            "COORDSYS": self.config.out_coord_sys,
            "TIME_ZONE": "0",
        }

        # Add stations
        for i, (_, station) in enumerate(imis_stations.iterrows(), 1):
            config["Input"][f"STATION{i}"] = station["ID"]

        # Write
        ini_path = self.paths.get_simulation_dir() / "io.ini"
        with open(ini_path, 'w') as f:
            config.write(f)

    def _create_sno_files(self, lus_file: Path, imis_stations) -> None:
        """
        Create .sno files for each LUS type.

        Args:
            lus_file: Path to LUS file
            imis_stations: GeoDataFrame of IMIS stations
        """
        logger.info("   Creating A3D .sno files")

        # Get unique LUS values
        from ..data.lus import LUSProcessor
        lus_processor = LUSProcessor(self.paths)
        unique_lus = lus_processor.get_unique_lus_values(lus_file)

        logger.info(f"   Found {len(unique_lus)} unique LUS types")

        # Check for template
        template_name = "template_complex.sno" if self.config.use_groundeye else "template.sno"
        template_sno = self.paths.input_templates / template_name
        dict_sno = self.paths.input_templates / "dictSno.pkl"

        if template_sno.exists() and dict_sno.exists() and JINJA2_AVAILABLE:
            self._create_sno_from_template(unique_lus, imis_stations, template_sno, dict_sno)
        else:
            self._create_basic_sno_files(unique_lus, imis_stations)

        logger.info(f"   ✓ Created {len(unique_lus)} .sno files")

    def _create_sno_from_template(
        self,
        unique_lus: List[int],
        imis_stations,
        template_path: Path,
        dict_path: Path
    ) -> None:
        """Create .sno files using LUS-specific or fallback templates."""
        # Load settings
        with open(dict_path, "rb") as f:
            sno_dict = pickle.load(f)

        # Setup Jinja2 environment for templates
        template_loader = jinja2.FileSystemLoader(template_path.parent)
        template_env = jinja2.Environment(loader=template_loader)

        # Use first station for metadata
        first_station = imis_stations.iloc[0]

        # Update dictionary with station metadata
        sno_dict.update(
            EXPERIMENT=self.config.simu_name,
            station_id=first_station["ID"],
            latitude=first_station["LATITUDE"],
            longitude=first_station["LONGITUDE"],
            altitude=first_station["ELEVATION"],
            nodata=-999,
            tz=1,
            station_name=first_station.get("NAME", first_station["ID"]),
            nsoillayerdata=0,
            data=""
        )

        # Create .sno for each LUS
        sno_dir = self.paths.get_simu_snowfiles_dir()
        for lus_value in unique_lus:
            lus_code = int(lus_value)

            # Try LUS-specific template first
            lus_template_path = template_path.parent / f"lus_{lus_code}.sno"

            if lus_template_path.exists():
                # Use LUS-specific template
                template = template_env.get_template(f"lus_{lus_code}.sno")
                logger.debug(f"   Using LUS-specific template for {lus_code}")
            else:
                # Fall back to generic template
                template = template_env.get_template(template_path.name)
                logger.debug(f"   Using fallback template for {lus_code}")

            # Render and save
            sno_output = template.render(sno_dict)
            sno_file = sno_dir / f"{self.config.simu_name}_{lus_code}.sno"
            sno_file.write_text(sno_output)

    def _create_basic_sno_files(self, unique_lus: List[int], imis_stations) -> None:
        """Create basic .sno files without template."""
        first_station = imis_stations.iloc[0]
        sno_dir = self.paths.get_simu_snowfiles_dir()

        for lus_value in unique_lus:
            config = configparser.ConfigParser(delimiters="=")

            config["Header"] = {
                "EXPERIMENT": self.config.simu_name,
                "stationID": first_station["ID"],
                "latitude": first_station["LATITUDE"],
                "longitude": first_station["LONGITUDE"],
                "altitude": first_station["ELEVATION"],
            }

            sno_file = sno_dir / f"{self.config.simu_name}_{int(lus_value)}.sno"
            with open(sno_file, 'w') as f:
                config.write(f)
