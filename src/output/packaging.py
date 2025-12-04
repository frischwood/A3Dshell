"""
Output packaging for A3DShell A3Dshell.

Handles copying static files, organizing output, and creating zip archives.
"""

import logging
import shutil
from pathlib import Path
from typing import List, Optional

from ..utils.helpers import zip_directory, copy_tree

logger = logging.getLogger(__name__)


class OutputPackager:
    """Packages simulation output for distribution."""

    def __init__(self, path_manager, config):
        """
        Initialize output packager.

        Args:
            path_manager: Path manager instance
            config: Simulation configuration
        """
        self.paths = path_manager
        self.config = config

    def copy_static_files(self) -> None:
        """
        Copy static data files to simulation directory.

        Copies:
        - BRDF files (if using Groundeye)
        - PV template
        - POI SMET template
        """
        logger.info("Copying static files to simulation directory")

        # BRDF files (if needed)
        if self.config.use_groundeye:
            logger.info("   Copying BRDF files for Groundeye")
            src_brdf = self.paths.input_brdf
            dst_brdf = self.paths.get_simu_brdf_dir()

            if src_brdf.exists():
                copy_tree(src_brdf, dst_brdf)
                logger.info(f"   ✓ BRDF files copied to {dst_brdf.relative_to(self.paths.base_dir)}")
            else:
                logger.warning(f"   BRDF directory not found: {src_brdf}")

        # PV template - disabled for now, enable for future PV developments
        # pv_template = self.paths.input_templates / "template.pv"
        # if pv_template.exists():
        #     dst_pv = self.paths.get_simu_grids_dir() / f"{self.config.simu_name}.pv"
        #     shutil.copy2(pv_template, dst_pv)
        #     logger.info(f"   ✓ PV template copied")
        # else:
        #     logger.warning(f"   PV template not found: {pv_template}")

    def copy_ini_file(self, source_ini: Optional[Path] = None) -> None:
        """
        Copy original configuration file to simulation directory.

        Args:
            source_ini: Path to source .ini file
        """
        if source_ini and source_ini.exists():
            dst_ini = self.paths.get_simulation_dir() / "a3dShell.ini"
            shutil.copy2(source_ini, dst_ini)
            logger.info(f"   ✓ Configuration file copied: {dst_ini.name}")
        else:
            logger.info("   No source .ini file to copy")

    def create_zip_archive(self, exclude_dirs: Optional[List[str]] = None) -> Path:
        """
        Create zip archive of simulation directory.

        Args:
            exclude_dirs: List of subdirectories to exclude from zip

        Returns:
            Path to created zip file
        """
        logger.info("="*60)
        logger.info("Creating Zip Archive")
        logger.info("="*60)

        exclude_dirs = exclude_dirs or ["tmp", "temp"]

        simu_dir = self.paths.get_simulation_dir()
        zip_path = self.paths.output_dir / f"{self.config.simu_name}.zip"

        # Remove existing zip if present
        if zip_path.exists():
            zip_path.unlink()
            logger.info(f"   Removed existing zip: {zip_path.name}")

        # Create zip
        logger.info(f"   Excluding directories: {', '.join(exclude_dirs)}")
        zip_directory(simu_dir, zip_path, exclude_dirs=exclude_dirs)

        # Get zip size
        zip_size_mb = zip_path.stat().st_size / (1024 * 1024)
        logger.info(f"   ✓ Zip created: {zip_path.name} ({zip_size_mb:.1f} MB)")

        return zip_path

    def create_output_structure(self) -> None:
        """
        Create complete output directory structure.

        Creates:
        - input/surface-grids/
        - input/meteo/
        - input/snowfiles/
        - input/brdf-files/ (if needed)
        - output/
        - mapping/
        """
        logger.info("Creating output directory structure")

        # All directories are created via path_manager getters
        self.paths.get_simu_grids_dir()
        self.paths.get_simu_meteo_dir()
        self.paths.get_simu_snowfiles_dir()
        self.paths.get_simu_output_dir()
        self.paths.get_simu_mapping_dir()

        if self.config.use_groundeye:
            self.paths.get_simu_brdf_dir()

        logger.info("   ✓ Directory structure created")

    def generate_summary(self) -> str:
        """
        Generate text summary of simulation setup.

        Returns:
            Summary text
        """
        simu_dir = self.paths.get_simulation_dir()

        # Count files in key directories
        grids_files = list(self.paths.get_simu_grids_dir().glob("*"))
        meteo_files = list(self.paths.get_simu_meteo_dir().glob("*.smet"))
        sno_files = list(self.paths.get_simu_snowfiles_dir().glob("*.sno"))

        # Generate mode-specific summary
        if self.config.dem_mode == "swisstopo":
            # Switzerland mode summary
            summary = f"""
{'='*60}
Simulation Summary: {self.config.simu_name}
{'='*60}

Mode: Switzerland

Configuration:
  Period: {self.config.start_date} to {self.config.end_date}
  POI: {self.config.poi_x:.0f}E, {self.config.poi_y:.0f}N, {self.config.poi_z:.0f}m
  ROI: {'Shapefile' if self.config.use_shp_roi else f'{self.config.roi_size}m bbox'}
  GSD: {self.config.gsd}m (ref: {self.config.gsd_ref}m)
  Coordinate System: {self.config.out_coord_sys}

Output:
  Location: {simu_dir}
  Surface grids: {len(grids_files)} files
  Meteo files: {len(meteo_files)} SMET files
  Snow files: {len(sno_files)} .sno files

Status:
  ✓ Input files prepared
  ✓ Ready for Alpine3D execution

{'='*60}
"""
        else:
            # Other Locations mode summary
            poi_count = len(self.config.pois) if self.config.pois else 0
            summary = f"""
{'='*60}
Simulation Summary: {self.config.simu_name}
{'='*60}

Mode: Other Locations (User-Provided Data)

Configuration:
  DEM: {self.config.user_dem_path}
  EPSG: {self.config.target_epsg}
  Coordinate System: {self.config.out_coord_sys}
  POIs: {poi_count} {'point' if poi_count == 1 else 'points'} defined

Output:
  Location: {simu_dir}
  Surface grids: {len(grids_files)} files

Next Steps:
  1. Add your meteorological SMET files to: {self.paths.get_simu_meteo_dir()}
  2. Verify DEM conversion (TIF → ASC)
  3. Configure Alpine3D simulation parameters

{'='*60}
"""
        return summary

    def finalize_output(
        self,
        source_ini: Optional[Path] = None,
        create_zip: bool = True
    ) -> None:
        """
        Finalize output: copy ini, create summary, optionally zip.

        Args:
            source_ini: Path to source .ini file
            create_zip: Whether to create zip archive
        """
        logger.info("="*60)
        logger.info("Finalizing Output")
        logger.info("="*60)

        # Copy ini file
        self.copy_ini_file(source_ini)

        # Create summary
        summary = self.generate_summary()
        summary_file = self.paths.get_simulation_dir() / "SIMULATION_SUMMARY.txt"
        summary_file.write_text(summary)
        logger.info(f"   ✓ Summary saved: {summary_file.name}")

        # Print summary
        print(summary)

        # Create zip
        if create_zip:
            self.create_zip_archive(exclude_dirs=["tmp", "temp"])

        logger.info("="*60)
        logger.info("Output finalization complete")
        logger.info("="*60)
