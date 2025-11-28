"""
Snowpack preprocessing for A3DShell A3Dshell.

Handles Snowpack configuration and execution to generate SMET files for A3D.
"""

import logging
import configparser
import subprocess
import shutil
import pickle
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
import glob

logger = logging.getLogger(__name__)

# Optional import
try:
    import jinja2
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False
    logger.warning("jinja2 not available")


class SnowpackPreprocessor:
    """Handles Snowpack preprocessing for A3D simulations."""

    def __init__(self, path_manager, config):
        """
        Initialize Snowpack preprocessor.

        Args:
            path_manager: Path manager instance
            config: Simulation configuration
        """
        self.paths = path_manager
        self.config = config

        # Temporary directories for Snowpack
        self.temp_dir = self.paths.get_simulation_dir() / "tmp" / "snowpack"
        self.temp_input = self.temp_dir / "input"
        self.temp_output = self.temp_dir / "output"
        self.temp_input_meteo = self.temp_input / "meteo"
        self.temp_input_sno = self.temp_input / "snowfiles"
        self.temp_output_meteo = self.temp_output / "meteo"
        self.temp_output_sno = self.temp_output / "snowfiles"

    def run_preprocessing(self, imis_stations) -> bool:
        """
        Run complete Snowpack preprocessing pipeline.

        Args:
            imis_stations: GeoDataFrame of selected IMIS stations

        Returns:
            True if successful
        """
        if not self.config.run_snowpack:
            logger.info("Snowpack preprocessing skipped (run_snowpack=False)")
            return False

        logger.info("="*60)
        logger.info("Snowpack Preprocessing")
        logger.info("="*60)

        # Create temp directories
        self._create_temp_directories()

        # Create configuration files
        self._create_ini_file(imis_stations)
        self._create_sno_files(imis_stations)

        # Run Snowpack
        success = self._run_snowpack()

        if success:
            # Copy SMET files to A3D input
            self._copy_smet_to_a3d()

        logger.info("="*60)
        return success

    def _create_temp_directories(self) -> None:
        """Create temporary Snowpack directories."""
        for directory in [
            self.temp_input_meteo,
            self.temp_input_sno,
            self.temp_output_meteo,
            self.temp_output_sno
        ]:
            directory.mkdir(parents=True, exist_ok=True)

        logger.info("   Created temporary directories")

    def _create_ini_file(self, imis_stations) -> None:
        """
        Create Snowpack .ini configuration file.

        Args:
            imis_stations: GeoDataFrame of IMIS stations
        """
        logger.info("   Creating Snowpack .ini file")

        # Load template
        template_ini = self.paths.input_templates / "spConfig.ini"

        if not template_ini.exists():
            logger.warning(f"   Template not found: {template_ini}")
            logger.info("   Creating basic .ini file")
            self._create_basic_ini(imis_stations)
            return

        # Read template
        config = configparser.ConfigParser(delimiters="=")
        config.read(template_ini)

        # Update paths and parameters
        config["Output"]["EXPERIMENT"] = self.config.simu_name
        config["Input"]["METEOPATH"] = str(self.temp_input_meteo.relative_to(self.paths.base_dir))
        config["Input"]["SNOWPATH"] = str(self.temp_input_sno.relative_to(self.paths.base_dir))
        config["Output"]["METEOPATH"] = str(self.temp_output_meteo.relative_to(self.paths.base_dir))
        config["Output"]["SNOWPATH"] = str(self.temp_output_sno.relative_to(self.paths.base_dir))
        config["Input"]["COORDSYS"] = self.config.out_coord_sys
        config["Output"]["COORDSYS"] = self.config.out_coord_sys

        # Add station IDs
        for i, (_, station) in enumerate(imis_stations.iterrows(), 1):
            config["Input"][f"station_id{i}"] = station["ID"]

        # Write ini file
        ini_path = self.temp_dir / "io.ini"
        with open(ini_path, 'w') as f:
            config.write(f)

        logger.info(f"   ✓ Snowpack .ini created: {len(imis_stations)} stations")

    def _create_basic_ini(self, imis_stations) -> None:
        """
        Create basic Snowpack .ini file without template.

        Args:
            imis_stations: GeoDataFrame of IMIS stations
        """
        config = configparser.ConfigParser(delimiters="=")

        config["General"] = {}
        config["Input"] = {
            "METEOPATH": str(self.temp_input_meteo.relative_to(self.paths.base_dir)),
            "SNOWPATH": str(self.temp_input_sno.relative_to(self.paths.base_dir)),
            "COORDSYS": self.config.out_coord_sys,
        }
        config["Output"] = {
            "EXPERIMENT": self.config.simu_name,
            "METEOPATH": str(self.temp_output_meteo.relative_to(self.paths.base_dir)),
            "SNOWPATH": str(self.temp_output_sno.relative_to(self.paths.base_dir)),
            "COORDSYS": self.config.out_coord_sys,
        }

        # Add stations
        for i, (_, station) in enumerate(imis_stations.iterrows(), 1):
            config["Input"][f"station_id{i}"] = station["ID"]

        # Write
        ini_path = self.temp_dir / "io.ini"
        with open(ini_path, 'w') as f:
            config.write(f)

    def _create_sno_files(self, imis_stations) -> None:
        """
        Create .sno files for each IMIS station.

        Args:
            imis_stations: GeoDataFrame of IMIS stations
        """
        logger.info("   Creating .sno files")

        # Check for template
        template_sno = self.paths.input_templates / "template.sno"
        dict_sno = self.paths.input_templates / "dictSno.pkl"

        if template_sno.exists() and dict_sno.exists() and JINJA2_AVAILABLE:
            self._create_sno_from_template(imis_stations, template_sno, dict_sno)
        else:
            self._create_basic_sno_files(imis_stations)

        logger.info(f"   ✓ Created {len(imis_stations)} .sno files")

    def _create_sno_from_template(self, imis_stations, template_path, dict_path) -> None:
        """Create .sno files using template and dictionary."""
        # Load settings dictionary
        with open(dict_path, "rb") as f:
            sno_dict = pickle.load(f)

        # Setup Jinja2
        template_loader = jinja2.FileSystemLoader(template_path.parent)
        template_env = jinja2.Environment(loader=template_loader)
        template = template_env.get_template(template_path.name)

        # Create .sno for each station
        for _, station in imis_stations.iterrows():
            sno_dict.update(
                experiment=self.config.simu_name,
                station_id=station["ID"],
                latitude=station["LATITUDE"],
                longitude=station["LONGITUDE"],
                altitude=station["ELEVATION"],
                nsoillayerdata=0,
                data=""
            )

            # Render
            sno_output = template.render(sno_dict)

            # Write
            sno_file = self.temp_input_sno / f"{station['ID']}.sno"
            sno_file.write_text(sno_output)

    def _create_basic_sno_files(self, imis_stations) -> None:
        """Create basic .sno files without template."""
        for _, station in imis_stations.iterrows():
            config = configparser.ConfigParser(delimiters="=")

            config["Header"] = {
                "EXPERIMENT": self.config.simu_name,
                "stationID": station["ID"],
                "latitude": station["LATITUDE"],
                "longitude": station["LONGITUDE"],
                "altitude": station["ELEVATION"],
            }

            sno_file = self.temp_input_sno / f"{station['ID']}.sno"
            with open(sno_file, 'w') as f:
                config.write(f)

    def _run_snowpack(self) -> bool:
        """
        Execute Snowpack binary.

        Returns:
            True if successful
        """
        logger.info("   Running Snowpack")

        # Build command
        snowpack_start = self.config.start_date + timedelta(hours=1)
        start_str = snowpack_start.strftime('%Y-%m-%dT%H:%M:%S')
        end_str = self.config.end_date.strftime('%Y-%m-%dT%H:%M:%S')
        ini_file = self.temp_dir / "io.ini"

        cmd = [
            self.config.sp_bin,
            "-c", str(ini_file),
            "-b", start_str,
            "-e", end_str
        ]

        logger.info(f"   Command: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                cwd=self.paths.base_dir,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )

            if result.returncode == 0:
                logger.info("   ✓ Snowpack execution successful")
                return True
            else:
                logger.error(f"   Snowpack failed with code {result.returncode}")
                logger.error(f"   STDOUT: {result.stdout}")
                logger.error(f"   STDERR: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            logger.error("   Snowpack execution timed out")
            return False
        except FileNotFoundError:
            logger.error(f"   Snowpack binary not found: {self.config.sp_bin}")
            logger.info("   Skipping Snowpack execution")
            return False
        except Exception as e:
            logger.error(f"   Snowpack execution failed: {e}")
            return False

    def _copy_smet_to_a3d(self) -> None:
        """Copy Snowpack output SMET files to A3D input directory."""
        logger.info("   Copying SMET files to A3D input")

        a3d_meteo_dir = self.paths.get_simu_meteo_dir()
        smet_files = list(self.temp_output_meteo.glob("*.smet"))

        if not smet_files:
            logger.warning("   No SMET files found in Snowpack output")
            return

        for smet_file in smet_files:
            # Extract station ID from filename (e.g., "STN123_meteo.smet" -> "STN123")
            station_id = smet_file.stem.split("_")[0]
            dst_file = a3d_meteo_dir / f"{station_id}.smet"
            shutil.copy2(smet_file, dst_file)

        logger.info(f"   ✓ Copied {len(smet_files)} SMET files")
