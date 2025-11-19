"""
Land Use (LUS) processing for A3DShell A3Dshell.

Generates land use grids from SwissTLMRegio data or constant values.
"""

import logging
import numpy as np
from pathlib import Path
from typing import List, Optional, Dict

logger = logging.getLogger(__name__)

# Optional imports
try:
    import rasterio
    from rasterio import features
    from rasterio.mask import mask as rasterio_mask
    RASTERIO_AVAILABLE = True
except ImportError:
    RASTERIO_AVAILABLE = False
    logger.warning("rasterio not available")

try:
    import geopandas as gpd
    GEOPANDAS_AVAILABLE = True
except ImportError:
    GEOPANDAS_AVAILABLE = False
    logger.warning("geopandas not available")


class LUSProcessor:
    """Processes Land Use data for A3D simulations."""

    # Mapping from SwissTLMRegio to PREVAH land use codes
    # A3D format: 1LLCD where LL is PREVAH code, CD is not used
    TLM_TO_PREVAH = {
        "Wald": 3,
        "Fels": 15,
        "Geroell": 21,
        "Gletscher": 14,
        "See": 1,
        "Stausee": 1,
        "Siedl": 2,
        "Stadtzentr": 2,
        "Sumpf": 22,
        "Obstanlage": 18,
        "Reben": 29
    }

    def __init__(self, path_manager):
        """
        Initialize LUS processor.

        Args:
            path_manager: Path manager instance
        """
        if not RASTERIO_AVAILABLE or not GEOPANDAS_AVAILABLE:
            raise ImportError("rasterio and geopandas required for LUS processing")

        self.paths = path_manager

    def create_lus(
        self,
        dem_file: Path,
        roi,
        target_crs: str,
        use_tlm: bool = True,
        tlm_shp_path: Optional[Path] = None,
        lus_constant: Optional[int] = None
    ) -> Path:
        """
        Create land use grid.

        Args:
            dem_file: Path to DEM file (used for grid structure)
            roi: ROI object
            target_crs: Target coordinate system
            use_tlm: Whether to use SwissTLMRegio data
            tlm_shp_path: Path to TLM landcover shapefile
            lus_constant: Constant LUS value (if not using TLM)

        Returns:
            Path to LUS file
        """
        logger.info("="*60)
        logger.info("LUS Processing")
        logger.info("="*60)

        lus_file = self.paths.get_lus_file(
            gsd=self._get_dem_gsd(dem_file)
        )

        # Skip if already exists
        if lus_file.exists():
            logger.info(f"LUS already exists: {lus_file}")
            return lus_file

        if use_tlm:
            if not tlm_shp_path or not tlm_shp_path.exists():
                raise FileNotFoundError(
                    f"TLM shapefile required but not found: {tlm_shp_path}"
                )
            logger.info("Creating LUS from SwissTLMRegio")
            self._create_from_tlm(dem_file, tlm_shp_path, roi, target_crs, lus_file)
        else:
            if lus_constant is None:
                raise ValueError("lus_constant required when not using TLM")
            logger.info(f"Creating LUS from constant value: {lus_constant}")
            self._create_from_constant(dem_file, roi, target_crs, lus_constant, lus_file)

        logger.info(f"LUS created: {lus_file}")
        return lus_file

    def _create_from_tlm(
        self,
        dem_file: Path,
        tlm_shp_path: Path,
        roi,
        target_crs: str,
        output_file: Path,
        nodata: int = -9999
    ) -> None:
        """
        Create LUS from SwissTLMRegio landcover data.

        Args:
            dem_file: DEM file path
            tlm_shp_path: TLM landcover shapefile path
            roi: ROI object
            target_crs: Target CRS
            output_file: Output LUS file path
            nodata: No data value
        """
        # Read DEM metadata
        with rasterio.open(dem_file) as dem:
            meta = dem.meta.copy()

        # Read TLM shapefile
        logger.info(f"   Loading TLM data from {tlm_shp_path.name}")
        tlm_data = gpd.read_file(tlm_shp_path)

        # Convert to target CRS
        if tlm_data.crs.to_string() != target_crs:
            tlm_data = tlm_data.to_crs(target_crs)

        # Convert TLM categories to PREVAH codes
        logger.info("   Converting TLM categories to PREVAH codes")

        # Get unique TLM categories before conversion
        unique_tlm_categories = tlm_data["OBJVAL"].unique()
        logger.info(f"   Found {len(unique_tlm_categories)} unique TLM categories")

        tlm_data["prevah_lus"] = tlm_data.apply(
            lambda row: self._tlm_to_a3d_code(row.get("OBJVAL", "")),
            axis=1
        )

        # Identify unmapped categories
        unmapped_mask = tlm_data["prevah_lus"] == 0
        if unmapped_mask.any():
            unmapped_categories = tlm_data[unmapped_mask]["OBJVAL"].unique()
            unmapped_count = unmapped_mask.sum()
            logger.warning(
                f"   Found {unmapped_count} features with unmapped TLM categories: {', '.join(unmapped_categories)}"
            )
            logger.warning("   These areas will be set to nodata in the LUS grid")

        # Filter out unmapped categories
        tlm_data = tlm_data[tlm_data["prevah_lus"] > 0]

        logger.info(f"   Mapped {len(tlm_data)} TLM features to PREVAH codes")
        logger.info(f"   Unique PREVAH codes: {sorted(tlm_data['prevah_lus'].unique())}")

        # Create temporary raster for burning
        temp_file = output_file.with_suffix('.tmp.lus')

        with rasterio.open(temp_file, "w", **meta) as dst:
            # Initialize with nodata
            lus_grid = np.full((meta["height"], meta["width"]), nodata, dtype=np.int32)

            # Burn TLM features into grid
            if len(tlm_data) > 0:
                shapes = (
                    (geom, value)
                    for geom, value in zip(tlm_data.geometry, tlm_data.prevah_lus)
                )

                burned = features.rasterize(
                    shapes=shapes,
                    fill=nodata,
                    out=lus_grid,
                    transform=dst.transform
                )
                lus_grid = burned

            # Write to temporary file
            dst.write(lus_grid, 1)

        # Mask to ROI
        roi_geom = roi.geometry_2056.to_crs(target_crs)

        with rasterio.open(temp_file) as src:
            masked, out_transform = rasterio_mask(
                dataset=src,
                shapes=roi_geom.geometry,
                nodata=nodata,
                filled=True,
                all_touched=True
            )

            # Write final LUS file
            with rasterio.open(output_file, "w", **meta) as dst:
                dst.write(masked[0], 1)

        # Remove temporary file
        temp_file.unlink()

        # Log statistics
        unique_values = np.unique(masked[masked != nodata])
        logger.info(f"   LUS grid created: {len(unique_values)} unique land use types")

    def _create_from_constant(
        self,
        dem_file: Path,
        roi,
        target_crs: str,
        lus_value: int,
        output_file: Path,
        nodata: int = -9999
    ) -> None:
        """
        Create LUS from constant value.

        Args:
            dem_file: DEM file path
            roi: ROI object
            target_crs: Target CRS
            lus_value: Constant LUS value
            output_file: Output file path
            nodata: No data value
        """
        # Read DEM metadata
        with rasterio.open(dem_file) as dem:
            meta = dem.meta.copy()
            dem_data = dem.read(1)

        # Create LUS grid with constant value where DEM has data
        lus_grid = np.where(
            dem_data != meta.get("nodata", -9999),
            lus_value,
            nodata
        )

        # Write LUS file
        meta_copy = meta.copy()
        meta_copy["dtype"] = "int32"

        with rasterio.open(output_file, "w", **meta_copy) as dst:
            dst.write(lus_grid.astype(np.int32), 1)

        logger.info(f"   LUS grid created with constant value: {lus_value}")

    def _tlm_to_a3d_code(self, tlm_category: str) -> int:
        """
        Convert TLM category to A3D land use code.

        Args:
            tlm_category: TLM category name

        Returns:
            A3D LUS code (1LLCD format) or 0 if not mapped
        """
        prevah_code = self.TLM_TO_PREVAH.get(tlm_category, 0)
        if prevah_code == 0:
            return 0

        # A3D format: 1LLCD where LL is PREVAH code, CD is not used (set to 00)
        a3d_code = int(f"1{prevah_code:02d}00")
        return a3d_code

    def get_unique_lus_values(self, lus_file: Path) -> List[int]:
        """
        Get unique LUS values from LUS file.

        Args:
            lus_file: Path to LUS file

        Returns:
            List of unique LUS values (excluding nodata)
        """
        with rasterio.open(lus_file) as lus:
            data = lus.read(1)
            nodata = lus.meta.get("nodata", -9999)

        unique_values = np.unique(data[data != nodata])
        return unique_values.tolist()

    def _get_dem_gsd(self, dem_file: Path) -> float:
        """
        Get grid spacing from DEM file.

        Args:
            dem_file: Path to DEM file

        Returns:
            Grid spacing in meters
        """
        with rasterio.open(dem_file) as dem:
            # Get cell size from transform
            gsd = abs(dem.transform.a)
            return round(gsd, 1)
