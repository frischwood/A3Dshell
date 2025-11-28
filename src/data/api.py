"""
Swisstopo API client for A3DShell A3Dshell.

Handles downloads of DEM tiles, national maps, and SwissTLM data with caching.
"""

import logging
import requests
from pathlib import Path
from typing import List, Dict, Optional
import zipfile
import time

from ..data.cache import CacheManager

logger = logging.getLogger(__name__)


class SwisstopoAPI:
    """Client for Swisstopo API with integrated caching."""

    def __init__(self, cache_manager: CacheManager, download_dir: Path):
        """
        Initialize Swisstopo API client.

        Args:
            cache_manager: Cache manager instance
            download_dir: Temporary directory for downloads
        """
        self.cache = cache_manager
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)

        # API endpoints
        self.dem_endpoint = "https://data.geo.admin.ch/api/stac/v0.9/collections/ch.swisstopo.swissalti3d/items"
        self.map_endpoint = "https://data.geo.admin.ch/api/stac/v0.9/collections/ch.swisstopo.landeskarte-farbe-10/items"
        self.tlm_endpoint = "https://data.geo.admin.ch/api/stac/v0.9/collections/ch.swisstopo.swisstlmregio/items"
        self.bfs_endpoint = "https://data.geo.admin.ch/api/stac/v0.9/collections/ch.bfs.arealstatistik/items"

    def get_dem_tiles(self, bbox_str: str, gsd_ref: float = 2.0) -> List[Path]:
        """
        Get DEM tiles for bounding box.

        Args:
            bbox_str: Bounding box string (minx,miny,maxx,maxy in EPSG:4326)
            gsd_ref: Reference GSD (2.0 or 0.5)

        Returns:
            List of paths to DEM tile files
        """
        logger.info(f"Fetching DEM tiles for bbox: {bbox_str}, GSD: {gsd_ref}m")

        # Query API for download links
        links = self._query_dem_api(bbox_str, gsd_ref)

        logger.info(f"Found {len(links)} DEM tiles")

        # Download or retrieve from cache
        tile_paths = []
        for link in links:
            tile_path = self._download_with_cache(link, cache_type="dem")
            tile_paths.append(tile_path)

        return tile_paths

    def get_national_maps(self, bbox_str: str) -> List[Path]:
        """
        Get Swiss national maps (1:10,000) for bounding box.

        Args:
            bbox_str: Bounding box string (minx,miny,maxx,maxy in EPSG:4326)

        Returns:
            List of paths to map files
        """
        logger.info(f"Fetching national maps for bbox: {bbox_str}")

        # Query API for download links
        links = self._query_map_api(bbox_str)

        logger.info(f"Found {len(links)} map tiles")

        # Download or retrieve from cache
        map_paths = []
        for link in links:
            map_path = self._download_with_cache(link, cache_type="map")
            map_paths.append(map_path)

        return map_paths

    def get_swisstlm_data(self) -> List[Path]:
        """
        Get SwissTLMRegio data.

        Returns:
            List of paths to TLM data files
        """
        logger.info("Fetching SwissTLMRegio data")

        # Query API
        links = self._query_tlm_api()

        logger.info(f"Found {len(links)} TLM data files")

        # Download files (TLM is cached, shared across all simulations)
        tlm_paths = []
        tlm_cache_dir = self.cache.cache_dir / "tlm"
        for link in links:
            file_path = self._download_file(link, tlm_cache_dir)

            # Extract if zip
            if file_path.suffix == ".zip":
                file_path = self._extract_zip(file_path)

            tlm_paths.append(file_path)

        return tlm_paths

    def get_bfs_arealstatistik(self) -> List[Path]:
        """
        Get BFS Arealstatistik GeoPackage.

        Returns:
            List of paths to BFS Arealstatistik data files (GeoPackage)
        """
        logger.info("Fetching BFS Arealstatistik data")

        # Direct URL for current GeoPackage (EPSG:2056)
        gpkg_url = "https://data.geo.admin.ch/ch.bfs.arealstatistik/arealstatistik/arealstatistik_2056.gpkg"

        # Cache in dedicated directory
        bfs_cache_dir = self.cache.cache_dir / "bfs_arealstatistik"
        file_path = self._download_file(gpkg_url, bfs_cache_dir)

        return [file_path]

    def _query_dem_api(self, bbox_str: str, gsd_ref: float) -> List[str]:
        """
        Query DEM API for download links.

        Args:
            bbox_str: Bounding box string
            gsd_ref: Reference GSD

        Returns:
            List of download URLs
        """
        params = {
            "limit": 100,
            "bbox": bbox_str
        }

        response = requests.get(self.dem_endpoint, params=params)

        if response.status_code != 200:
            logger.error(f"API request failed: {response.text}")
            response.raise_for_status()

        # Parse response
        links = []
        data = response.json()

        for feature in data.get("features", []):
            for asset_key, asset in feature.get("assets", {}).items():
                # Filter by GSD and format
                if asset.get("eo:gsd") == gsd_ref and "tiff" in asset.get("type", ""):
                    links.append(asset["href"])

        return links

    def _query_map_api(self, bbox_str: str) -> List[str]:
        """
        Query national map API for download links.

        Args:
            bbox_str: Bounding box string

        Returns:
            List of download URLs
        """
        params = {
            "limit": 100,
            "bbox": bbox_str
        }

        response = requests.get(self.map_endpoint, params=params)

        if response.status_code != 200:
            logger.error(f"API request failed: {response.text}")
            response.raise_for_status()

        # Parse response
        links = []
        data = response.json()

        for feature in data.get("features", []):
            for asset_key, asset in feature.get("assets", {}).items():
                # Filter for krel variant and 2022 version
                if (asset.get("geoadmin:variant") == "krel" and
                        "2022" in asset.get("href", "")):
                    links.append(asset["href"])

        return links

    def _query_tlm_api(self) -> List[str]:
        """
        Query SwissTLMRegio API for download links.

        Returns:
            List of download URLs
        """
        params = {"limit": 100}

        response = requests.get(self.tlm_endpoint, params=params)

        if response.status_code != 200:
            logger.error(f"API request failed: {response.text}")
            response.raise_for_status()

        # Parse response
        links = []
        data = response.json()

        for feature in data.get("features", []):
            for asset_key, asset in feature.get("assets", {}).items():
                # Filter for shapefile format and 2022 version
                if ("shapefile" in asset.get("type", "") and
                        "2022" in asset.get("href", "")):
                    links.append(asset["href"])

        return links

    def _download_with_cache(self, url: str, cache_type: str) -> Path:
        """
        Download file with cache check.

        Args:
            url: Download URL
            cache_type: Type of cache ("dem" or "map")

        Returns:
            Path to file (cached or newly downloaded)
        """
        # Check cache first
        if cache_type == "dem":
            cached_file = self.cache.get_dem_tile(url)
            if cached_file:
                return cached_file
        elif cache_type == "map":
            cached_file = self.cache.get_map(url)
            if cached_file:
                return cached_file

        # Download file
        file_path = self._download_file(url, self.download_dir)

        # Extract if zip
        if file_path.suffix == ".zip":
            file_path = self._extract_zip(file_path)

        # Add to cache
        if cache_type == "dem":
            cached_path = self.cache.cache_dem_tile(url, file_path)
        elif cache_type == "map":
            cached_path = self.cache.cache_map(url, file_path)
        else:
            cached_path = file_path

        return cached_path

    def _download_file(self, url: str, target_dir: Path) -> Path:
        """
        Download file from URL.

        Args:
            url: Download URL
            target_dir: Target directory

        Returns:
            Path to downloaded file
        """
        target_dir = Path(target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)

        filename = url.split("/")[-1]
        file_path = target_dir / filename

        # Skip if already exists
        if file_path.exists():
            logger.info(f"File already exists: {filename}")
            return file_path

        # Get file size
        response_head = requests.head(url, allow_redirects=True)
        file_size_mb = int(response_head.headers.get('content-length', 0)) / (1024 * 1024)

        logger.info(f"Downloading {filename} ({file_size_mb:.1f} MB)")

        # Download with progress
        start_time = time.time()
        response = requests.get(url, allow_redirects=True, stream=True)
        response.raise_for_status()

        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        elapsed = time.time() - start_time
        logger.info(f"Downloaded {filename} in {elapsed:.1f}s")

        return file_path

    def _extract_zip(self, zip_path: Path) -> Path:
        """
        Extract zip file and return path to main content.

        Args:
            zip_path: Path to zip file

        Returns:
            Path to extracted content directory or main file
        """
        extract_dir = zip_path.parent / zip_path.stem

        if extract_dir.exists():
            logger.info(f"Already extracted: {zip_path.name}")
        else:
            logger.info(f"Extracting {zip_path.name}")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)

        # Return first .tif or directory
        tif_files = list(extract_dir.glob("*.tif"))
        if tif_files:
            return tif_files[0]

        return extract_dir
