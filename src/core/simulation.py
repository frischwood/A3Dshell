"""
Main simulation orchestrator for A3DShell A3Dshell.

Coordinates the complete simulation setup pipeline.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..config import SimulationConfig
from ..core.paths import PathManager
from ..geometry.roi import ROI
from ..data.cache import CacheManager
from ..data.api import SwisstopoAPI
from ..data.dem import DEMProcessor
from ..data.lus import LUSProcessor
from ..data.imis import IMISManager
from ..preprocessing.snowpack import SnowpackPreprocessor
from ..preprocessing.a3d_config import A3DConfigurator
from ..output.packaging import OutputPackager
from ..utils.logging import log_section

logger = logging.getLogger(__name__)


class SimulationOrchestrator:
    """Orchestrates the complete A3D simulation setup pipeline."""

    def __init__(self, config: SimulationConfig, source_ini: Optional[Path] = None):
        """
        Initialize simulation orchestrator.

        Args:
            config: Simulation configuration
            source_ini: Path to source .ini file (for copying to output)
        """
        self.config = config
        self.source_ini = source_ini
        self.start_time = datetime.now()

        # Initialize managers
        self.paths = PathManager(simu_name=config.simu_name)
        self.cache = CacheManager(self.paths.cache_dir)
        self.api = SwisstopoAPI(self.cache, self.paths.cache_dir / "downloads")

        # Initialize processors
        self.dem_proc = DEMProcessor(self.cache, self.api, self.paths)
        self.lus_proc = LUSProcessor(self.paths)
        self.imis_mgr = IMISManager(self.paths.input_imis)
        self.snowpack = SnowpackPreprocessor(self.paths, config)
        self.a3d_config = A3DConfigurator(self.paths, config)
        self.packager = OutputPackager(self.paths, config)

    def run(self) -> bool:
        """
        Execute complete simulation setup pipeline.

        Returns:
            True if successful
        """
        try:
            logger.info("="*60)
            logger.info(f"A3DShell Simulation: {self.config.simu_name}")
            logger.info("="*60)
            logger.info(f"Start time: {self.start_time}")
            logger.info("")

            # Phase 1: Setup
            log_section(logger, "Phase 1: Setup", self.start_time)
            self._setup_directories()

            # Different workflows for Switzerland vs Other Locations
            if self.config.dem_mode == "swisstopo":
                # Switzerland mode - full workflow
                self._run_switzerland_mode()
            elif self.config.dem_mode == "user_provided":
                # Other Locations mode - simplified workflow
                self._run_other_locations_mode()

            # Phase 8: Output Packaging
            log_section(logger, "Phase 8: Output Packaging", self.start_time)
            self._package_output()

            # Done
            elapsed = datetime.now() - self.start_time
            logger.info("="*60)
            logger.info(f"✓ Simulation setup complete!")
            logger.info(f"Total time: {elapsed}")
            logger.info(f"Output: {self.paths.get_simulation_dir()}")
            logger.info("="*60)

            return True

        except Exception as e:
            logger.error(f"Simulation failed: {e}", exc_info=True)
            return False

    def _setup_directories(self) -> None:
        """Setup directory structure."""
        logger.info("Setting up directories")
        self.paths.create_all_directories()
        self.packager.create_output_structure()
        logger.info(f"   ✓ Directories created: {self.paths.get_simulation_dir()}")

    def _run_switzerland_mode(self) -> None:
        """Run full workflow for Switzerland mode."""
        # Phase 2: ROI & Data Download
        log_section(logger, "Phase 2: ROI & Data", self.start_time)
        roi = self._create_roi()
        target_crs = self._get_target_crs()

        # Phase 3: DEM Processing
        log_section(logger, "Phase 3: DEM Processing", self.start_time)
        dem_file = self._process_dem(roi, target_crs)

        # Phase 4: LUS Processing
        log_section(logger, "Phase 4: LUS Processing", self.start_time)
        lus_file = self._process_lus(roi, dem_file, target_crs)

        # Phase 5: IMIS Station Selection
        log_section(logger, "Phase 5: IMIS Station Selection", self.start_time)
        imis_stations = self._select_imis_stations(roi)

        # Phase 6: Snowpack Preprocessing
        log_section(logger, "Phase 6: Snowpack Preprocessing", self.start_time)
        self._run_snowpack(imis_stations)

        # Phase 7: A3D Configuration
        log_section(logger, "Phase 7: A3D Configuration", self.start_time)
        self._configure_a3d(imis_stations, lus_file)

    def _run_other_locations_mode(self) -> None:
        """Run simplified workflow for Other Locations mode."""
        logger.info("Running Other Locations mode workflow")
        logger.info("   User provides: DEM, meteorological data (SMET files)")
        logger.info("   A3DShell generates: DEM conversion (TIF→ASC), LUS, POI files, setup folder")

        # Phase 2: Convert user DEM from TIF to ASC
        log_section(logger, "Phase 2: DEM Processing", self.start_time)
        dem_file = self._convert_user_dem()

        # Phase 3: Generate constant LUS
        log_section(logger, "Phase 3: LUS Generation", self.start_time)
        lus_file = self._generate_constant_lus(dem_file)

        # Phase 4: Generate POI files
        if self.config.pois:
            log_section(logger, "Phase 4: POI File Generation", self.start_time)
            self._generate_poi_smet()
        else:
            logger.info("Skipping POI generation (no POIs defined)")

    def _convert_user_dem(self) -> Path:
        """
        Convert user-provided DEM from TIF to ASC format.

        Returns:
            Path to converted ASC file
        """
        import rasterio
        from pathlib import Path

        input_dem = Path(self.config.user_dem_path)
        output_dem = self.paths.get_simu_grids_dir() / "dem.asc"

        logger.info(f"Converting DEM: {input_dem.name}")
        logger.info(f"   Input: {input_dem}")
        logger.info(f"   Output: {output_dem}")

        # Read TIF and write as ASC
        with rasterio.open(input_dem) as src:
            data = src.read(1)
            meta = src.meta.copy()
            meta.update({
                'driver': 'AAIGrid',
                'nodata': -9999
            })

            with rasterio.open(output_dem, 'w', **meta) as dst:
                dst.write(data, 1)

        logger.info(f"   ✓ DEM converted to ASC format")
        logger.info(f"   Dimensions: {data.shape[1]} x {data.shape[0]} cells")

        return output_dem

    def _generate_constant_lus(self, dem_file: Path) -> Path:
        """
        Generate constant land use surface (LUS) grid.

        Args:
            dem_file: Path to DEM file (for getting dimensions)

        Returns:
            Path to generated LUS file
        """
        import rasterio
        import numpy as np

        lus_file = self.paths.get_simu_grids_dir() / "lus.asc"
        lus_value = self.config.lus_prevah_cst

        logger.info(f"Generating constant LUS with value: {lus_value}")

        # Read DEM to get dimensions and georeferencing
        with rasterio.open(dem_file) as dem:
            # Create constant LUS array with same shape as DEM
            lus_data = np.full(dem.shape, lus_value, dtype=np.int32)

            # Copy metadata from DEM
            meta = dem.meta.copy()
            meta.update({
                'dtype': 'int32',
                'nodata': -9999
            })

            # Write LUS file
            with rasterio.open(lus_file, 'w', **meta) as dst:
                dst.write(lus_data, 1)

        logger.info(f"   ✓ LUS file generated: {lus_file.name}")
        logger.info(f"   All cells set to: {lus_value}")

        return lus_file

    def _generate_poi_smet(self) -> None:
        """Generate POI SMET file from configuration."""
        poi_file = self.paths.get_simu_input_dir() / "poi.smet"

        logger.info(f"Generating POI SMET file: {poi_file.name}")
        logger.info(f"   POIs: {len(self.config.pois)}")

        # Read template
        template_file = Path("input/templates/poi.smet")
        with open(template_file, 'r') as f:
            template_content = f.read()

        # Generate POI data lines
        poi_lines = []
        for poi in self.config.pois:
            # Format: easting northing altitude
            poi_lines.append(f"{poi['x']:.2f} {poi['y']:.2f} {poi['z']:.2f}")

        # Update template with EPSG and POI data
        output_content = template_content.replace(
            "epsg = 21781",
            f"epsg = {self.config.target_epsg}"
        )

        # Add POI data after [DATA] section
        output_content = output_content.rstrip() + "\n" + "\n".join(poi_lines) + "\n"

        # Write output file
        with open(poi_file, 'w') as f:
            f.write(output_content)

        logger.info(f"   ✓ POI file generated with {len(self.config.pois)} points")

    def _create_roi(self) -> ROI:
        """
        Create ROI from configuration.

        Returns:
            ROI object
        """
        logger.info("Creating Region of Interest (ROI)")

        if self.config.use_shp_roi:
            logger.info(f"   Mode: Shapefile")
            logger.info(f"   Path: {self.config.roi_shapefile}")
            roi = ROI(
                poi_x=self.config.poi_x,
                poi_y=self.config.poi_y,
                poi_crs="EPSG:2056",
                shapefile_path=Path(self.config.roi_shapefile)
            )
        else:
            logger.info(f"   Mode: Bounding box")
            logger.info(f"   Size: {self.config.roi_size}m")
            roi = ROI(
                poi_x=self.config.poi_x,
                poi_y=self.config.poi_y,
                poi_crs="EPSG:2056",
                roi_size=self.config.roi_size
            )

        # Save ROI to output
        roi_path = self.paths.get_simu_mapping_dir() / "roi.shp"
        roi.save_to_shapefile(roi_path)

        logger.info(f"   ✓ ROI created")
        logger.info(f"   {roi}")

        return roi

    def _get_target_crs(self) -> str:
        """Get target CRS string."""
        from ..geometry.transforms import get_epsg_from_coordsys
        epsg = get_epsg_from_coordsys(self.config.out_coord_sys)
        return f"EPSG:{epsg}"

    def _process_dem(self, roi, target_crs: str) -> Path:
        """
        Process DEM.

        Args:
            roi: ROI object
            target_crs: Target CRS

        Returns:
            Path to processed DEM file
        """
        dem_file = self.dem_proc.process_dem(
            roi=roi,
            gsd=self.config.gsd,
            gsd_ref=self.config.gsd_ref,
            target_crs=target_crs,
            dem_formats=self.config.dem_add_fmt_list,
            mask_to_polygon=self.config.mask_dem_to_polygon
        )

        return dem_file

    def _process_lus(self, roi, dem_file: Path, target_crs: str) -> Path:
        """
        Process Land Use.

        Args:
            roi: ROI object
            dem_file: Path to DEM file
            target_crs: Target CRS

        Returns:
            Path to LUS file
        """
        # Get TLM shapefile if using TLM
        tlm_shp = None
        if self.config.use_lus_tlm:
            # Download/get TLM data
            logger.info("Fetching SwissTLMRegio data")
            tlm_files = self.api.get_swisstlm_data()

            # Find landcover shapefile
            for tlm_file in tlm_files:
                if tlm_file.is_dir():
                    landcover_shp = tlm_file / "Landcover" / "swissTLMRegio_LandCover.shp"
                    if landcover_shp.exists():
                        tlm_shp = landcover_shp
                        break

            if not tlm_shp:
                logger.warning("TLM landcover shapefile not found, using constant LUS")
                use_tlm = False
            else:
                use_tlm = True
        else:
            use_tlm = False

        lus_file = self.lus_proc.create_lus(
            dem_file=dem_file,
            roi=roi,
            target_crs=target_crs,
            use_tlm=use_tlm,
            tlm_shp_path=tlm_shp,
            lus_constant=self.config.lus_prevah_cst if not use_tlm else None
        )

        return lus_file

    def _select_imis_stations(self, roi):
        """
        Select IMIS stations.

        Args:
            roi: ROI object

        Returns:
            GeoDataFrame of selected stations
        """
        imis_stations = self.imis_mgr.get_stations_in_buffer(
            roi=roi,
            buffer_size=self.config.buffer_size
        )

        if len(imis_stations) == 0:
            logger.warning("No IMIS stations found in buffered ROI")
            logger.info("Falling back to closest stations")
            imis_stations = self.imis_mgr.get_closest_stations(
                poi_x=self.config.poi_x,
                poi_y=self.config.poi_y,
                n=4
            )

        logger.info(f"   Selected stations: {', '.join(imis_stations['ID'].values)}")

        return imis_stations

    def _run_snowpack(self, imis_stations) -> None:
        """
        Run Snowpack preprocessing.

        Args:
            imis_stations: GeoDataFrame of IMIS stations
        """
        success = self.snowpack.run_preprocessing(imis_stations)

        if not success:
            logger.warning("Snowpack preprocessing failed or was skipped")

    def _configure_a3d(self, imis_stations, lus_file: Path) -> None:
        """
        Configure Alpine3D.

        Args:
            imis_stations: GeoDataFrame of IMIS stations
            lus_file: Path to LUS file
        """
        self.a3d_config.create_configuration(imis_stations, lus_file)

    def _package_output(self) -> None:
        """Package and finalize output."""
        self.packager.copy_static_files()
        self.packager.finalize_output(
            source_ini=self.source_ini,
            create_zip=True
        )
