"""
Region of Interest (ROI) handling for A3DShell A3Dshell.

Supports both bounding box (from point + size) and shapefile-based ROI.
"""

import logging
from pathlib import Path
from typing import Union, Tuple, Optional, TYPE_CHECKING
import zipfile
import tempfile
import shutil

if TYPE_CHECKING:
    import geopandas as gpd

logger = logging.getLogger(__name__)

# Optional imports with fallbacks
try:
    import geopandas as gpd
    import shapely.geometry
    from shapely.geometry import box
    GEOPANDAS_AVAILABLE = True
except ImportError:
    GEOPANDAS_AVAILABLE = False
    gpd = None
    shapely = None
    box = None
    logger.warning("geopandas not available, shapefile support will be limited")


class ROI:
    """Region of Interest handler."""

    def __init__(
        self,
        poi_x: float,
        poi_y: float,
        poi_crs: str = "EPSG:2056",
        roi_size: Optional[int] = None,
        shapefile_path: Optional[Path] = None
    ):
        """
        Initialize ROI.

        Args:
            poi_x: Point of interest X coordinate
            poi_y: Point of interest Y coordinate
            poi_crs: CRS of the POI (default: EPSG:2056)
            roi_size: Size of ROI in meters (for bbox mode)
            shapefile_path: Path to shapefile (for shapefile mode)

        Raises:
            ValueError: If neither roi_size nor shapefile_path is provided
        """
        if not GEOPANDAS_AVAILABLE:
            raise ImportError(
                "geopandas is required for ROI handling. "
                "Install with: pip install geopandas"
            )

        self.poi_x = poi_x
        self.poi_y = poi_y
        self.poi_crs = poi_crs
        self.roi_size = roi_size
        self.shapefile_path = Path(shapefile_path) if shapefile_path else None

        # Validate inputs
        if roi_size is None and shapefile_path is None:
            raise ValueError("Either roi_size or shapefile_path must be provided")

        if shapefile_path and not self.shapefile_path.exists():
            # Check if it's a zip file
            if str(shapefile_path).endswith('.zip'):
                self.shapefile_path = self._extract_shapefile_from_zip(shapefile_path)
            else:
                raise FileNotFoundError(f"Shapefile not found: {shapefile_path}")

        # Load geometry
        self.geometry_2056 = self._load_geometry()
        self.geometry_4326 = self._convert_to_4326()

    def _load_geometry(self) -> "gpd.GeoDataFrame":
        """
        Load ROI geometry.

        Returns:
            GeoDataFrame with ROI geometry in EPSG:2056
        """
        if self.shapefile_path:
            # Load from shapefile
            logger.info(f"Loading ROI from shapefile: {self.shapefile_path}")
            gdf = gpd.read_file(self.shapefile_path)

            # Clean non-geometric attributes
            gdf = gdf[~gdf.geometry.isna()]

            # Convert to EPSG:2056 if needed
            if gdf.crs.to_string() != "EPSG:2056":
                logger.info(f"Converting shapefile CRS from {gdf.crs} to EPSG:2056")
                gdf = gdf.to_crs("EPSG:2056")

            return gdf

        else:
            # Create bounding box from POI and size
            logger.info(f"Creating {self.roi_size}m bounding box around POI")

            # Create point geometry
            point = shapely.geometry.Point(self.poi_x, self.poi_y)
            gdf = gpd.GeoDataFrame(geometry=[point], crs=self.poi_crs)

            # Buffer to create ROI (cap_style=3 for square)
            buffered = gdf.buffer(distance=self.roi_size / 2, cap_style=3)

            return gpd.GeoDataFrame(geometry=buffered, crs="EPSG:2056")

    def _convert_to_4326(self) -> "gpd.GeoDataFrame":
        """
        Convert geometry to EPSG:4326 (WGS84).

        Returns:
            GeoDataFrame with ROI geometry in EPSG:4326
        """
        return self.geometry_2056.to_crs("EPSG:4326")

    def _extract_shapefile_from_zip(self, zip_path: Path) -> Path:
        """
        Extract shapefile from zip archive.

        Args:
            zip_path: Path to zip file

        Returns:
            Path to extracted .shp file

        Raises:
            ValueError: If no .shp file found in archive
        """
        logger.info(f"Extracting shapefile from {zip_path}")

        # Create temporary directory
        temp_dir = Path(tempfile.mkdtemp(prefix="a3dshell_roi_"))

        # Extract zip
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)

        # Find .shp file
        shp_files = list(temp_dir.rglob("*.shp"))

        if not shp_files:
            shutil.rmtree(temp_dir)
            raise ValueError(f"No .shp file found in {zip_path}")

        if len(shp_files) > 1:
            logger.warning(f"Multiple .shp files found, using first: {shp_files[0]}")

        return shp_files[0]

    def get_bbox_4326(self) -> Tuple[float, float, float, float]:
        """
        Get bounding box in EPSG:4326.

        Returns:
            Tuple of (minx, miny, maxx, maxy) in EPSG:4326
        """
        bounds = self.geometry_4326.total_bounds
        return tuple(bounds)

    def get_bbox_2056(self) -> Tuple[float, float, float, float]:
        """
        Get bounding box in EPSG:2056.

        Returns:
            Tuple of (minx, miny, maxx, maxy) in EPSG:2056
        """
        bounds = self.geometry_2056.total_bounds
        return tuple(bounds)

    def get_bbox_string_4326(self) -> str:
        """
        Get bounding box as comma-separated string for API requests.

        Returns:
            String in format "minx,miny,maxx,maxy"
        """
        bounds = self.get_bbox_4326()
        return ",".join(f"{coord:.6f}" for coord in bounds)

    def buffer(self, distance: float) -> "gpd.GeoDataFrame":
        """
        Create buffered ROI.

        Args:
            distance: Buffer distance in meters

        Returns:
            Buffered GeoDataFrame in EPSG:2056
        """
        buffered = self.geometry_2056.buffer(distance=distance)
        return gpd.GeoDataFrame(geometry=buffered, crs="EPSG:2056")

    def save_to_shapefile(self, output_path: Path) -> None:
        """
        Save ROI geometry to shapefile.

        Args:
            output_path: Path where to save shapefile
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        self.geometry_2056.to_file(output_path)
        logger.info(f"Saved ROI to {output_path}")

    def __str__(self) -> str:
        """String representation."""
        bbox = self.get_bbox_2056()
        area_km2 = self.geometry_2056.geometry.area.sum() / 1_000_000

        return (
            f"ROI(\n"
            f"  Source: {'shapefile' if self.shapefile_path else 'bbox'}\n"
            f"  BBox (2056): {bbox}\n"
            f"  Area: {area_km2:.2f} km²\n"
            f")"
        )
