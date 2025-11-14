"""
Coordinate transformation utilities for A3DShell A3Dshell.
"""

import logging
from typing import Tuple

logger = logging.getLogger(__name__)

# Optional import
try:
    from pyproj import Transformer
    PYPROJ_AVAILABLE = True
except ImportError:
    PYPROJ_AVAILABLE = False
    Transformer = None
    logger.warning("pyproj not available, coordinate transformations will use approximations")


def transform_coordinates(
    x: float,
    y: float,
    src_epsg: int,
    dst_epsg: int
) -> Tuple[float, float]:
    """
    Transform coordinates between coordinate systems.

    Args:
        x: X coordinate (easting or longitude)
        y: Y coordinate (northing or latitude)
        src_epsg: Source EPSG code
        dst_epsg: Destination EPSG code

    Returns:
        Tuple of (x, y) in destination CRS
    """
    if not PYPROJ_AVAILABLE:
        logger.warning("Using approximate coordinate transformation (pyproj not available)")
        return _approximate_transform(x, y, src_epsg, dst_epsg)

    transformer = Transformer.from_crs(
        crs_from=f'epsg:{src_epsg}',
        crs_to=f'epsg:{dst_epsg}'
    )

    # Transform
    y_out, x_out = transformer.transform(x, y)

    return x_out, y_out


def transform_2056_to_4326(x: float, y: float, z: float = 0) -> Tuple[float, float, float]:
    """
    Transform CH1903+ (EPSG:2056) to WGS84 (EPSG:4326).

    Args:
        x: Easting (EPSG:2056)
        y: Northing (EPSG:2056)
        z: Altitude

    Returns:
        Tuple of (longitude, latitude, altitude)
    """
    if not PYPROJ_AVAILABLE:
        logger.warning("Using approximate coordinate transformation (pyproj not available)")
        # Very rough approximation for Switzerland
        lon = (x - 2600000) / 111000 + 7.5
        lat = (y - 1200000) / 111000 + 46.5
        return lon, lat, z

    transformer = Transformer.from_crs(crs_from='epsg:2056', crs_to='epsg:4326')
    lat, lon, alt = transformer.transform(xx=x, yy=y, zz=z)

    return lon, lat, alt


def transform_4326_to_2056(lon: float, lat: float, alt: float = 0) -> Tuple[float, float, float]:
    """
    Transform WGS84 (EPSG:4326) to CH1903+ (EPSG:2056).

    Args:
        lon: Longitude (EPSG:4326)
        lat: Latitude (EPSG:4326)
        alt: Altitude

    Returns:
        Tuple of (easting, northing, altitude)
    """
    if not PYPROJ_AVAILABLE:
        logger.warning("Using approximate coordinate transformation (pyproj not available)")
        # Very rough approximation for Switzerland
        x = (lon - 7.5) * 111000 + 2600000
        y = (lat - 46.5) * 111000 + 1200000
        return x, y, alt

    transformer = Transformer.from_crs(crs_from='epsg:4326', crs_to='epsg:2056')
    y_out, x_out, alt_out = transformer.transform(xx=lon, yy=lat, zz=alt)

    return x_out, y_out, alt_out


def _approximate_transform(
    x: float,
    y: float,
    src_epsg: int,
    dst_epsg: int
) -> Tuple[float, float]:
    """
    Approximate coordinate transformation (fallback when pyproj not available).

    Args:
        x: X coordinate
        y: Y coordinate
        src_epsg: Source EPSG code
        dst_epsg: Destination EPSG code

    Returns:
        Tuple of (x, y) in destination CRS
    """
    # Handle common Swiss transformations
    if src_epsg == 2056 and dst_epsg == 4326:
        lon = (x - 2600000) / 111000 + 7.5
        lat = (y - 1200000) / 111000 + 46.5
        return lon, lat

    elif src_epsg == 4326 and dst_epsg == 2056:
        easting = (x - 7.5) * 111000 + 2600000
        northing = (y - 46.5) * 111000 + 1200000
        return easting, northing

    else:
        logger.warning(f"Approximate transformation not supported for {src_epsg} -> {dst_epsg}")
        return x, y


def get_epsg_from_coordsys(coord_sys: str) -> int:
    """
    Get EPSG code from coordinate system name.

    Args:
        coord_sys: Coordinate system name (CH1903+, CH1903, WGS84, CHTRS95)

    Returns:
        EPSG code

    Raises:
        ValueError: If coordinate system is not recognized
    """
    mapping = {
        "CH1903+": 2056,
        "CH1903": 21781,
        "WGS84": 4326,
        "CHTRS95": 4932
    }

    if coord_sys not in mapping:
        raise ValueError(
            f"Unknown coordinate system: {coord_sys}. "
            f"Supported: {', '.join(mapping.keys())}"
        )

    return mapping[coord_sys]
