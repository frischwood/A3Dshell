"""
IMIS (Intercantonal Measurement and Information System) station management.

Handles selection of meteorological stations for simulations.
"""

import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional, List

logger = logging.getLogger(__name__)

# Optional imports
try:
    import geopandas as gpd
    GEOPANDAS_AVAILABLE = True
except ImportError:
    GEOPANDAS_AVAILABLE = False
    logger.warning("geopandas not available")

try:
    from pyproj import Transformer
    PYPROJ_AVAILABLE = True
except ImportError:
    PYPROJ_AVAILABLE = False


class IMISManager:
    """Manages IMIS meteorological station selection."""

    def __init__(self, imis_data_dir: Path):
        """
        Initialize IMIS manager.

        Args:
            imis_data_dir: Directory containing IMIS metadata files
        """
        if not GEOPANDAS_AVAILABLE:
            raise ImportError("geopandas required for IMIS management")

        self.imis_dir = Path(imis_data_dir)

        # IMIS metadata file paths
        self.meta_10y = self.imis_dir / "imisMeta_10y.txt"
        self.meta_daily = self.imis_dir / "imisMeta_daily.txt"
        self.meta_shp = self.imis_dir / "imisMeta_merged.shp"

        # Load metadata
        self.metadata = self._load_metadata()

    def _load_metadata(self) -> pd.DataFrame:
        """
        Load IMIS station metadata.

        Returns:
            DataFrame with station metadata
        """
        logger.info("Loading IMIS metadata")

        # Try loading from text files first
        if self.meta_10y.exists() and self.meta_daily.exists():
            logger.info(f"   Loading from {self.meta_10y.name} and {self.meta_daily.name}")

            # Load both files
            df_10y = pd.read_table(
                self.meta_10y,
                sep=" ",
                skipinitialspace=True,
                comment="#",
                header=0,
                index_col="ID"
            )

            df_daily = pd.read_table(
                self.meta_daily,
                sep=" ",
                skipinitialspace=True,
                comment="#",
                header=0,
                index_col="ID"
            )

            # Combine (10y takes precedence)
            df_meta = df_10y.combine_first(df_daily)

            # Add EPSG:2056 coordinates if transformer available
            if PYPROJ_AVAILABLE:
                df_meta["E_N_2056"] = df_meta.apply(
                    lambda row: self._transform_4326_to_2056(
                        row["LATITUDE"],
                        row["LONGITUDE"]
                    ),
                    axis=1
                )
            else:
                logger.warning("pyproj not available, skipping coordinate transformation")

            logger.info(f"   Loaded {len(df_meta)} stations")
            return df_meta

        else:
            logger.warning("IMIS metadata text files not found")
            return pd.DataFrame()

    def _transform_4326_to_2056(self, lat: float, lon: float) -> tuple:
        """
        Transform WGS84 to CH1903+.

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            Tuple of (easting, northing)
        """
        if not PYPROJ_AVAILABLE:
            # Rough approximation
            e = (lon - 7.5) * 111000 + 2600000
            n = (lat - 46.5) * 111000 + 1200000
            return (e, n)

        transformer = Transformer.from_crs(crs_from='epsg:4326', crs_to='epsg:2056')
        n, e = transformer.transform(lat, lon)
        return (e, n)

    def get_stations_in_buffer(
        self,
        roi,
        buffer_size: float
    ) -> gpd.GeoDataFrame:
        """
        Get IMIS stations within buffered ROI.

        Args:
            roi: ROI object with geometry
            buffer_size: Buffer distance in meters

        Returns:
            GeoDataFrame of qualified stations
        """
        logger.info("Selecting IMIS stations in buffered ROI")
        logger.info(f"   Buffer size: {buffer_size}m")

        # Load shapefile if available
        if self.meta_shp.exists():
            logger.info(f"   Loading from {self.meta_shp.name}")
            gdf_imis = gpd.read_file(self.meta_shp)

            # Ensure CRS
            if gdf_imis.crs is None:
                gdf_imis = gdf_imis.set_crs("EPSG:4326")

            # Convert to EPSG:2056
            gdf_imis = gdf_imis.to_crs("EPSG:2056")

        else:
            logger.info("   Creating GeoDataFrame from metadata")

            # Create GeoDataFrame from metadata
            if "E_N_2056" not in self.metadata.columns:
                raise ValueError("IMIS metadata missing coordinates")

            # Extract coordinates
            coords = list(self.metadata["E_N_2056"].values)
            eastings = [c[0] for c in coords]
            northings = [c[1] for c in coords]

            # Create GeoDataFrame
            from shapely.geometry import Point
            geometry = [Point(e, n) for e, n in zip(eastings, northings)]

            gdf_imis = gpd.GeoDataFrame(
                self.metadata.reset_index(),
                geometry=geometry,
                crs="EPSG:2056"
            )

        # Buffer ROI
        buffered_roi = roi.buffer(buffer_size)

        # Select stations within buffered ROI
        mask = buffered_roi.geometry.iloc[0].contains(gdf_imis.geometry)
        selected = gdf_imis[mask]

        logger.info(f"   Selected {len(selected)} stations")

        return selected

    def get_closest_stations(
        self,
        poi_x: float,
        poi_y: float,
        n: int = 10
    ) -> gpd.GeoDataFrame:
        """
        Get n closest IMIS stations to a point.

        Args:
            poi_x: Point X coordinate (EPSG:2056)
            poi_y: Point Y coordinate (EPSG:2056)
            n: Number of stations to return

        Returns:
            GeoDataFrame of closest stations
        """
        logger.info(f"Finding {n} closest IMIS stations")

        # Calculate distances
        if "E_N_2056" in self.metadata.columns:
            self.metadata["dist_to_poi"] = self.metadata["E_N_2056"].apply(
                lambda coord: np.linalg.norm(
                    np.array([poi_x, poi_y]) - np.array(coord)
                )
            )
        else:
            raise ValueError("IMIS metadata missing coordinates")

        # Sort by distance
        closest = self.metadata.nsmallest(n, "dist_to_poi")

        # Convert to GeoDataFrame
        from shapely.geometry import Point
        coords = list(closest["E_N_2056"].values)
        geometry = [Point(c[0], c[1]) for c in coords]

        gdf_closest = gpd.GeoDataFrame(
            closest.reset_index(),
            geometry=geometry,
            crs="EPSG:2056"
        )

        logger.info(f"   Closest station: {gdf_closest.iloc[0]['ID']} "
                   f"({gdf_closest.iloc[0]['dist_to_poi']:.0f}m)")

        return gdf_closest
