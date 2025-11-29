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

    # BFS Arealstatistik LC_27 to PREVAH mapping
    # LC_27 codes: 11-17 (urban), 21 (grass), 31-35 (shrubs/crops), 41-47 (forest), 51-53 (rock), 61-64 (water/wet)
    # PREVAH codes: 01=water, 02=settlement, 03=coniferous forest, 04=deciduous forest,
    # 05=mixed forest, 06=cereals, 07=pasture, 08=bush, 11=road, 13=firn, 14=bare ice,
    # 15=rock, 18=fruit, 19=vegetables, 20=wheat, 21=alpine vegetation, 22=wetlands,
    # 23=rough pasture, 24=subalpine meadow, 25=alpine meadow, 26=bare soil vegetation,
    # 27=free, 28=corn, 29=grapes
    LC27_TO_PREVAH = {
        # Urban/Built-up (LC_27: 11-17)
        11: 11,  # Befestigte Flächen (sealed surfaces) -> road
        12: 2,   # Gebäude (buildings) -> settlement
        13: 2,   # Treibhäuser (greenhouses) -> settlement
        14: 19,  # Beetstrukturen (garden beds) -> vegetables
        15: 7,   # Rasen (lawn) -> pasture
        16: 8,   # Bäume auf künstlich angelegten Flächen -> bush
        17: 2,   # Gemischte Kleinstrukturen -> settlement

        # Grassland (LC_27: 21)
        21: 7,   # Gras-, Krautvegetation -> pasture

        # Shrubs/Crops (LC_27: 31-35)
        31: 8,   # Gebüsch (shrubs) -> bush
        32: 8,   # Verbuschte Flächen (overgrown) -> bush
        33: 18,  # Niederstammobst (fruit trees) -> fruit
        34: 29,  # Reben (vines) -> grapes
        35: 19,  # Gärtnerische Dauerkulturen -> vegetables

        # Forest (LC_27: 41-47)
        41: 5,   # Geschlossene Baumbestände (closed forest) -> mixed forest
        42: 5,   # Waldecken (forest corners) -> mixed forest
        43: 5,   # Waldstreifen (forest strips) -> mixed forest
        44: 5,   # Aufgelöste Baumbestände (open forest) -> mixed forest
        45: 8,   # Gebüschwaldbestände (shrub forest) -> bush
        46: 5,   # Lineare Baumbestände (linear trees) -> mixed forest
        47: 5,   # Baumgruppen (tree groups) -> mixed forest

        # Rock/Stone (LC_27: 51-53)
        51: 15,  # Anstehender Fels (exposed rock) -> rock
        52: 15,  # Lockergestein (loose rock) -> rock
        53: 15,  # Versteinte Flächen (stony areas) -> rock

        # Water/Wet (LC_27: 61-64)
        61: 1,   # Wasser (water) -> water
        62: 13,  # Gletscher, Firn -> firn
        63: 22,  # Nassstandorte (wet sites) -> wetlands
        64: 22,  # Schilfbestände (reed stands) -> wetlands
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
        lus_source: str = "tlm",
        tlm_shp_path: Optional[Path] = None,
        bfs_gpkg_path: Optional[Path] = None,
        lus_constant: Optional[int] = None,
        mask_to_polygon: bool = True
    ) -> Path:
        """
        Create land use grid.

        Args:
            dem_file: Path to DEM file (used for grid structure)
            roi: ROI object
            target_crs: Target coordinate system
            lus_source: Land use source ("tlm", "bfs", or "constant")
            tlm_shp_path: Path to TLM landcover shapefile (if lus_source="tlm")
            bfs_gpkg_path: Path to BFS Arealstatistik GeoPackage (if lus_source="bfs")
            lus_constant: Constant LUS value (if lus_source="constant")
            mask_to_polygon: Whether to mask LUS to polygon (vs full bbox)

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

        if lus_source == "tlm":
            if not tlm_shp_path or not tlm_shp_path.exists():
                raise FileNotFoundError(
                    f"TLM shapefile required but not found: {tlm_shp_path}"
                )
            logger.info("Creating LUS from SwissTLMRegio")
            self._create_from_tlm(dem_file, tlm_shp_path, roi, target_crs, lus_file, mask_to_polygon)
        elif lus_source == "bfs":
            if not bfs_gpkg_path or not bfs_gpkg_path.exists():
                raise FileNotFoundError(
                    f"BFS GeoPackage required but not found: {bfs_gpkg_path}"
                )
            logger.info("Creating LUS from BFS Arealstatistik")
            self._create_from_bfs(dem_file, bfs_gpkg_path, roi, target_crs, lus_file, mask_to_polygon)
        else:  # constant
            if lus_constant is None:
                raise ValueError("lus_constant required when using constant source")
            logger.info(f"Creating LUS from constant value: {lus_constant}")
            self._create_from_constant(dem_file, roi, target_crs, lus_constant, lus_file, mask_to_polygon)

        logger.info(f"LUS created: {lus_file}")
        return lus_file

    def _create_from_tlm(
        self,
        dem_file: Path,
        tlm_shp_path: Path,
        roi,
        target_crs: str,
        output_file: Path,
        mask_to_polygon: bool = True,
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
            mask_to_polygon: Whether to mask LUS to polygon
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

        # Crop to ROI bbox (always) and optionally mask to polygon
        roi_geom = roi.geometry_2056.to_crs(target_crs)

        with rasterio.open(temp_file) as src:
            if mask_to_polygon:
                logger.info("   Cropping to ROI bbox and masking to polygon")
                # Mask/crop to polygon shape
                masked, out_transform = rasterio_mask(
                    dataset=src,
                    shapes=roi_geom.geometry,
                    nodata=nodata,
                    filled=True,
                    all_touched=True,
                    crop=True
                )
            else:
                logger.info("   Cropping to ROI bbox (no polygon masking)")
                # Only crop to bounding box (no polygon masking)
                from shapely.geometry import box
                bounds = roi_geom.total_bounds  # minx, miny, maxx, maxy
                bbox_geom = box(*bounds)

                masked, out_transform = rasterio_mask(
                    dataset=src,
                    shapes=[bbox_geom],
                    nodata=nodata,
                    filled=True,
                    all_touched=True,
                    crop=True
                )

            # Update metadata with new transform
            meta.update({
                "height": masked.shape[1],
                "width": masked.shape[2],
                "transform": out_transform
            })

            # Write final LUS file
            with rasterio.open(output_file, "w", **meta) as dst:
                dst.write(masked[0], 1)

            # Log statistics
            unique_values = np.unique(masked[masked != nodata])
            logger.info(f"   LUS grid created: {len(unique_values)} unique land use types")

        # Remove temporary file if it still exists
        if temp_file.exists():
            temp_file.unlink()

    def _create_from_bfs(
        self,
        dem_file: Path,
        bfs_gpkg_path: Path,
        roi,
        target_crs: str,
        output_file: Path,
        mask_to_polygon: bool = True,
        nodata: int = -9999
    ) -> None:
        """
        Create LUS from BFS Arealstatistik (GeoPackage with point data).

        Args:
            dem_file: DEM file path
            bfs_gpkg_path: BFS Arealstatistik GeoPackage path
            roi: ROI object
            target_crs: Target CRS
            output_file: Output LUS file path
            mask_to_polygon: Whether to mask LUS to polygon
            nodata: No data value
        """
        from shapely.geometry import box as shapely_box

        # Read DEM metadata and bounds
        with rasterio.open(dem_file) as dem:
            meta = dem.meta.copy()
            dem_bounds = dem.bounds
            dem_crs = dem.crs

        # Read BFS GeoPackage with spatial filter (file is ~1.2GB, must filter!)
        # BFS file is in EPSG:2056 - transform bounds if needed
        logger.info(f"   Loading BFS Arealstatistik from {bfs_gpkg_path.name}")
        bbox_for_filter = dem_bounds
        if dem_crs and str(dem_crs) != "EPSG:2056":
            from pyproj import Transformer
            transformer = Transformer.from_crs(dem_crs, "EPSG:2056", always_xy=True)
            minx, miny = transformer.transform(dem_bounds.left, dem_bounds.bottom)
            maxx, maxy = transformer.transform(dem_bounds.right, dem_bounds.top)
            bbox_for_filter = (minx, miny, maxx, maxy)
        logger.info(f"   Filtering to bounds: {bbox_for_filter}")
        bfs_data = gpd.read_file(bfs_gpkg_path, bbox=bbox_for_filter)

        # Convert to target CRS
        if bfs_data.crs.to_string() != target_crs:
            bfs_data = bfs_data.to_crs(target_crs)

        # Buffer points to 100m cells (BFS uses 100m grid centers)
        logger.info("   Buffering points to 100m cells")
        bfs_data['geometry'] = bfs_data.geometry.buffer(50, cap_style=3)  # cap_style=3 = square

        # Convert LC_27 to PREVAH codes
        logger.info("   Converting LC_27 categories to PREVAH codes")
        unique_lc27 = bfs_data["LC_27"].unique()
        logger.info(f"   Found {len(unique_lc27)} unique LC_27 categories")

        bfs_data["prevah_lus"] = bfs_data.apply(
            lambda row: self._lc27_to_a3d_code(row.get("LC_27", 0)),
            axis=1
        )

        # Log unmapped categories
        unmapped_mask = bfs_data["prevah_lus"] == 0
        if unmapped_mask.any():
            unmapped = bfs_data[unmapped_mask]["LC_27"].unique()
            unmapped_count = unmapped_mask.sum()
            logger.warning(
                f"   Found {unmapped_count} features with unmapped LC_27 categories: {unmapped}"
            )
            logger.warning("   These areas will be set to nodata in the LUS grid")

        # Filter unmapped
        bfs_data = bfs_data[bfs_data["prevah_lus"] > 0]
        logger.info(f"   Mapped {len(bfs_data)} features to PREVAH codes")
        logger.info(f"   Unique PREVAH codes: {sorted(bfs_data['prevah_lus'].unique())}")

        # Rasterize (same as TLM method from here)
        temp_file = output_file.with_suffix('.tmp.lus')

        with rasterio.open(temp_file, "w", **meta) as dst:
            lus_grid = np.full((meta["height"], meta["width"]), nodata, dtype=np.int32)

            if len(bfs_data) > 0:
                shapes = (
                    (geom, value)
                    for geom, value in zip(bfs_data.geometry, bfs_data.prevah_lus)
                )
                burned = features.rasterize(
                    shapes=shapes,
                    fill=nodata,
                    out=lus_grid,
                    transform=dst.transform
                )
                lus_grid = burned

            dst.write(lus_grid, 1)

        # Crop/mask to ROI (same as TLM method)
        roi_geom = roi.geometry_2056.to_crs(target_crs)

        with rasterio.open(temp_file) as src:
            if mask_to_polygon:
                logger.info("   Cropping to ROI bbox and masking to polygon")
                masked, out_transform = rasterio_mask(
                    dataset=src,
                    shapes=roi_geom.geometry,
                    nodata=nodata,
                    filled=True,
                    all_touched=True,
                    crop=True
                )
            else:
                logger.info("   Cropping to ROI bbox (no polygon masking)")
                bounds = roi_geom.total_bounds
                bbox_geom = shapely_box(*bounds)
                masked, out_transform = rasterio_mask(
                    dataset=src,
                    shapes=[bbox_geom],
                    nodata=nodata,
                    filled=True,
                    all_touched=True,
                    crop=True
                )

            meta.update({
                "height": masked.shape[1],
                "width": masked.shape[2],
                "transform": out_transform
            })

            with rasterio.open(output_file, "w", **meta) as dst:
                dst.write(masked[0], 1)

            unique_values = np.unique(masked[masked != nodata])
            logger.info(f"   LUS grid created: {len(unique_values)} unique land use types")

        if temp_file.exists():
            temp_file.unlink()

    def _create_from_constant(
        self,
        dem_file: Path,
        roi,
        target_crs: str,
        lus_value: int,
        output_file: Path,
        mask_to_polygon: bool = True,
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
            mask_to_polygon: Whether to mask LUS to polygon
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

        # Write to temporary file first
        temp_file = output_file.with_suffix('.tmp.lus')
        meta_copy = meta.copy()
        meta_copy["dtype"] = "int32"

        with rasterio.open(temp_file, "w", **meta_copy) as dst:
            dst.write(lus_grid.astype(np.int32), 1)

        # Crop to ROI bbox (always) and optionally mask to polygon
        roi_geom = roi.geometry_2056.to_crs(target_crs)

        with rasterio.open(temp_file) as src:
            if mask_to_polygon:
                logger.info("   Cropping to ROI bbox and masking to polygon")
                # Mask/crop to polygon shape
                masked, out_transform = rasterio_mask(
                    dataset=src,
                    shapes=roi_geom.geometry,
                    nodata=nodata,
                    filled=True,
                    all_touched=True,
                    crop=True
                )
            else:
                logger.info("   Cropping to ROI bbox (no polygon masking)")
                # Only crop to bounding box (no polygon masking)
                from shapely.geometry import box
                bounds = roi_geom.total_bounds  # minx, miny, maxx, maxy
                bbox_geom = box(*bounds)

                masked, out_transform = rasterio_mask(
                    dataset=src,
                    shapes=[bbox_geom],
                    nodata=nodata,
                    filled=True,
                    all_touched=True,
                    crop=True
                )

            # Update metadata with new transform
            meta_copy.update({
                "height": masked.shape[1],
                "width": masked.shape[2],
                "transform": out_transform
            })

            # Write final LUS file
            with rasterio.open(output_file, "w", **meta_copy) as dst:
                dst.write(masked[0], 1)

        logger.info(f"   LUS grid created with constant value: {lus_value}")

        # Remove temporary file if it still exists
        if temp_file.exists():
            temp_file.unlink()

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

    def _lc27_to_a3d_code(self, lc27_category: int) -> int:
        """
        Convert LC_27 category to A3D land use code.

        Args:
            lc27_category: LC_27 category code (1-27)

        Returns:
            A3D LUS code (1LLCD format) or 0 if not mapped
        """
        try:
            cat_int = int(lc27_category)
        except (ValueError, TypeError):
            return 0

        prevah_code = self.LC27_TO_PREVAH.get(cat_int, 0)
        if prevah_code == 0:
            return 0

        # A3D format: 1LLCD where LL is PREVAH code, CD is not used (set to 00)
        return int(f"1{prevah_code:02d}00")

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
