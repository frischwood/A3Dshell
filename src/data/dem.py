"""
DEM (Digital Elevation Model) processing for A3DShell A3Dshell.

Handles downloading, merging, reprojecting, cropping, and resampling of DEM data.
"""

import logging
import numpy as np
from pathlib import Path
from typing import List, Optional, Tuple
import glob

logger = logging.getLogger(__name__)

# Optional imports with fallbacks
try:
    import rasterio
    from rasterio import fill, merge
    from rasterio.warp import calculate_default_transform, reproject, Resampling
    from rasterio.mask import mask as rasterio_mask
    from rasterio.enums import Resampling as ResamplingEnum
    RASTERIO_AVAILABLE = True
except ImportError:
    RASTERIO_AVAILABLE = False
    logger.warning("rasterio not available, DEM processing will not work")

try:
    import geopandas as gpd
    GEOPANDAS_AVAILABLE = True
except ImportError:
    GEOPANDAS_AVAILABLE = False


class DEMProcessor:
    """Processes Digital Elevation Model data."""

    def __init__(self, cache_manager, api_client, path_manager):
        """
        Initialize DEM processor.

        Args:
            cache_manager: Cache manager instance
            api_client: Swisstopo API client
            path_manager: Path manager instance
        """
        if not RASTERIO_AVAILABLE:
            raise ImportError("rasterio is required for DEM processing")

        self.cache = cache_manager
        self.api = api_client
        self.paths = path_manager

    def process_dem(
        self,
        roi,
        gsd: float,
        gsd_ref: float,
        target_crs: str,
        dem_formats: List[str] = None,
        mask_to_polygon: bool = True
    ) -> Path:
        """
        Complete DEM processing pipeline.

        Args:
            roi: ROI object with geometry
            gsd: Target grid spacing
            gsd_ref: Reference DEM resolution (2.0 or 0.5)
            target_crs: Target coordinate system (e.g., "EPSG:2056")
            dem_formats: Additional output formats (e.g., ["tif"])
            mask_to_polygon: Whether to mask DEM to polygon shape (default: True)

        Returns:
            Path to processed DEM file (.asc)
        """
        logger.info("="*60)
        logger.info("DEM Processing Pipeline")
        logger.info("="*60)

        dem_formats = dem_formats or [""]
        output_file = self.paths.get_dem_file(gsd)

        # Skip if already exists
        if output_file.exists():
            logger.info(f"DEM already exists: {output_file}")
            return output_file

        # 1. Download tiles
        logger.info(f"1. Downloading DEM tiles (GSD ref: {gsd_ref}m)")
        bbox_str = roi.get_bbox_string_4326()
        tile_files = self.api.get_dem_tiles(bbox_str, gsd_ref)
        logger.info(f"   Downloaded {len(tile_files)} tiles")

        # 2. Merge tiles
        logger.info("2. Merging DEM tiles")
        merged_file = self._merge_tiles(tile_files, output_file, dem_formats)

        # 3. Reproject if needed
        logger.info(f"3. Reprojecting to {target_crs}")
        self._reproject_raster(merged_file, merged_file, gsd_ref, target_crs)

        # 4. Downsample if needed
        if gsd > gsd_ref:
            logger.info(f"4. Downsampling from {gsd_ref}m to {gsd}m")
            self._downsample_raster(merged_file, merged_file, gsd_ref, gsd)
        else:
            logger.info(f"4. No downsampling needed (GSD {gsd}m <= ref {gsd_ref}m)")

        # 5. Crop to ROI bbox (always) and optionally mask to polygon
        if mask_to_polygon:
            logger.info("5. Cropping to ROI bbox and masking to polygon")
        else:
            logger.info("5. Cropping to ROI bbox (no polygon masking)")
        self._crop_to_roi(merged_file, merged_file, roi, target_crs, mask_to_polygon=mask_to_polygon)

        logger.info(f"DEM processing complete: {output_file}")
        return output_file

    def _merge_tiles(
        self,
        tile_files: List[Path],
        output_file: Path,
        additional_formats: List[str] = None
    ) -> Path:
        """
        Merge multiple DEM tiles into single file.

        Args:
            tile_files: List of tile file paths
            output_file: Output file path (.asc)
            additional_formats: Additional formats to save (e.g., ["tif"])

        Returns:
            Path to merged file
        """
        additional_formats = additional_formats or []

        # Open all tiles
        src_files = []
        for tile_file in tile_files:
            # Handle .tif files directly, extract from zip if needed
            if tile_file.suffix == '.tif':
                src_files.append(rasterio.open(tile_file))
            else:
                # Look for .tif in directory
                tif_files = list(tile_file.glob("*.tif")) if tile_file.is_dir() else []
                if tif_files:
                    src_files.append(rasterio.open(tif_files[0]))

        if not src_files:
            raise ValueError("No valid DEM tiles found")

        # Merge
        mosaic, transform = merge.merge(src_files)

        # Get metadata from first source
        meta = src_files[0].meta.copy()
        meta.update({
            "height": mosaic.shape[1],
            "width": mosaic.shape[2],
            "transform": transform,
            "nodata": -9999
        })

        # Save in multiple formats
        formats_info = [
            ("AAIGrid", ".asc"),
        ]

        for fmt in additional_formats:
            if fmt == "tif":
                formats_info.append(("GTiff", ".tif"))

        for driver, ext in formats_info:
            output_path = output_file.with_suffix(ext)
            meta_copy = meta.copy()
            meta_copy["driver"] = driver

            with rasterio.open(output_path, "w", **meta_copy) as dst:
                dst.write(mosaic)

            logger.info(f"   Saved merged DEM: {output_path.name}")

        # Close sources
        for src in src_files:
            src.close()

        return output_file

    def _reproject_raster(
        self,
        src_file: Path,
        dst_file: Path,
        gsd: float,
        dst_crs: str
    ) -> None:
        """
        Reproject raster to target CRS.

        Args:
            src_file: Source file path
            dst_file: Destination file path
            gsd: Grid spacing
            dst_crs: Target CRS (e.g., "EPSG:2056")
        """
        with rasterio.open(src_file) as src:
            src_crs = src.crs

            # Skip if already in target CRS
            if src_crs.to_string() == dst_crs:
                logger.info("   Already in target CRS, skipping reprojection")
                return

            # Calculate transform for target CRS
            transform, width, height = calculate_default_transform(
                src_crs,
                dst_crs,
                src.width,
                src.height,
                *src.bounds,
                resolution=gsd
            )

            # Update metadata
            kwargs = src.meta.copy()
            kwargs.update({
                'crs': dst_crs,
                'transform': transform,
                'width': width,
                'height': height
            })

            # Reproject
            with rasterio.open(dst_file, "w", **kwargs) as dst:
                for i in range(1, src.count + 1):
                    reproject(
                        source=rasterio.band(src, i),
                        destination=rasterio.band(dst, i),
                        src_transform=src.transform,
                        src_crs=src_crs,
                        dst_transform=transform,
                        dst_crs=dst_crs,
                        resampling=ResamplingEnum.bilinear
                    )

            logger.info(f"   Reprojected to {dst_crs}")

    def _downsample_raster(
        self,
        src_file: Path,
        dst_file: Path,
        src_gsd: float,
        dst_gsd: float
    ) -> None:
        """
        Downsample raster to coarser resolution.

        Args:
            src_file: Source file path
            dst_file: Destination file path
            src_gsd: Source grid spacing
            dst_gsd: Target grid spacing (must be >= src_gsd)
        """
        if dst_gsd < src_gsd:
            raise ValueError(f"Cannot upsample: {src_gsd}m -> {dst_gsd}m")

        downscale_factor = src_gsd / dst_gsd

        with rasterio.open(src_file) as src:
            # Resample data
            data = src.read(
                out_shape=(
                    src.count,
                    int(src.height * downscale_factor),
                    int(src.width * downscale_factor)
                ),
                resampling=ResamplingEnum.average
            )

            # Calculate new transform
            transform = src.transform * src.transform.scale(
                round(src.width / data.shape[-1]),
                round(src.height / data.shape[-2])
            )

            # Update metadata
            kwargs = src.meta.copy()
            kwargs.update({
                "height": data.shape[1],
                "width": data.shape[2],
                "transform": transform,
                "nodata": -9999
            })

            # Write output
            with rasterio.open(dst_file, "w", **kwargs) as dst:
                dst.write(data)

            logger.info(f"   Downsampled to {dst_gsd}m")

    def _crop_to_roi(
        self,
        src_file: Path,
        dst_file: Path,
        roi,
        target_crs: str,
        mask_to_polygon: bool = True,
        nodata: float = -9999
    ) -> None:
        """
        Crop raster to ROI boundary.

        Args:
            src_file: Source file path
            dst_file: Destination file path
            roi: ROI object with geometry
            target_crs: Target CRS
            mask_to_polygon: If True, mask to polygon shape; if False, only crop to bbox
            nodata: No data value
        """
        # Get ROI geometry in target CRS
        roi_geom = roi.geometry_2056.to_crs(target_crs)

        with rasterio.open(src_file) as src:
            if mask_to_polygon:
                # Mask/crop to polygon shape
                out_image, out_transform = rasterio_mask(
                    dataset=src,
                    shapes=roi_geom.geometry,
                    nodata=nodata,
                    all_touched=True,
                    filled=False,
                    crop=True
                )
            else:
                # Only crop to bounding box (no polygon masking)
                # Use bounding box as the shape
                from shapely.geometry import box
                bounds = roi_geom.total_bounds  # minx, miny, maxx, maxy
                bbox_geom = box(*bounds)

                out_image, out_transform = rasterio_mask(
                    dataset=src,
                    shapes=[bbox_geom],
                    nodata=nodata,
                    all_touched=True,
                    filled=False,
                    crop=True
                )

            # Round transform coordinates to cm precision
            out_transform = rasterio.Affine(
                out_transform.a, out_transform.b, round(out_transform.c, 3),
                out_transform.d, out_transform.e, round(out_transform.f, 3),
                out_transform.g, out_transform.h, out_transform.i
            )

            # Update metadata
            out_meta = src.meta.copy()
            out_meta.update({
                "height": out_image.shape[1],
                "width": out_image.shape[2],
                "transform": out_transform
            })

            # Write output
            with rasterio.open(dst_file, "w", **out_meta) as dst:
                dst.write(out_image)

            # Clean up PRJ files created by GDAL (not needed for Alpine3D)
            for prj_file in dst_file.parent.glob(f"{dst_file.stem}*.prj"):
                prj_file.unlink()

            logger.info(f"   Cropped to ROI ({out_image.shape[2]}x{out_image.shape[1]} cells)")

    def fill_nodata(self, dem_file: Path, max_search_distance: int = 10000) -> None:
        """
        Fill nodata values in DEM using interpolation.

        Args:
            dem_file: Path to DEM file
            max_search_distance: Maximum search distance for interpolation
        """
        with rasterio.open(dem_file, "r+") as dem:
            meta = dem.meta.copy()
            data = dem.read(1)
            nodata_value = meta.get("nodata", -9999)

            # Check if there are nodata values
            nodata_count = (data == nodata_value).sum()

            if nodata_count > 0:
                logger.info(f"   Filling {nodata_count} nodata cells")

                # Create mask (0 where to interpolate, 1 where valid)
                nodata_mask = data != nodata_value

                # Fill using rasterio's fill
                filled = fill.fillnodata(
                    data,
                    nodata_mask,
                    max_search_distance=max_search_distance,
                    smoothing_iterations=0
                )

                # Write back
                dem.write(filled, 1)
                logger.info("   Nodata filled")
            else:
                logger.info("   No nodata values to fill")
