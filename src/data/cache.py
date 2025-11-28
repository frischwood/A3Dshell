"""
Cache management for A3DShell A3Dshell.

Handles caching of downloaded DEM tiles and national maps to avoid redundant downloads.
"""

import json
import hashlib
import logging
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)


class CacheManager:
    """Manages caching of downloaded geospatial data."""

    def __init__(self, cache_dir: Path):
        """
        Initialize cache manager.

        Args:
            cache_dir: Base cache directory
        """
        self.cache_dir = Path(cache_dir)
        self.dem_cache = self.cache_dir / "dem_tiles"
        self.maps_cache = self.cache_dir / "maps"
        self.metadata_file = self.cache_dir / "metadata.json"

        # Ensure directories exist
        self.dem_cache.mkdir(parents=True, exist_ok=True)
        self.maps_cache.mkdir(parents=True, exist_ok=True)

        # Load or initialize metadata
        self.metadata = self._load_metadata()

    def _load_metadata(self) -> Dict[str, Any]:
        """Load cache metadata from file."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load cache metadata: {e}")
                return {"dem_tiles": {}, "maps": {}}
        else:
            return {"dem_tiles": {}, "maps": {}}

    def _save_metadata(self) -> None:
        """Save cache metadata to file."""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save cache metadata: {e}")

    def _generate_cache_key(self, url: str, bbox: Optional[Dict] = None) -> str:
        """
        Generate unique cache key for a download.

        Args:
            url: Download URL
            bbox: Optional bounding box dictionary

        Returns:
            MD5 hash of the cache key
        """
        key_data = {"url": url}
        if bbox:
            key_data["bbox"] = bbox

        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()

    def get_dem_tile(self, url: str, bbox: Optional[Dict] = None) -> Optional[Path]:
        """
        Get cached DEM tile if available.

        Args:
            url: Download URL
            bbox: Optional bounding box

        Returns:
            Path to cached file if available, None otherwise
        """
        cache_key = self._generate_cache_key(url, bbox)

        if cache_key in self.metadata["dem_tiles"]:
            cached_info = self.metadata["dem_tiles"][cache_key]
            cached_file = Path(cached_info["path"])

            if cached_file.exists():
                logger.info(f"Using cached DEM tile: {cached_file.name}")
                return cached_file
            else:
                logger.warning(f"Cached DEM tile missing: {cached_file}")
                del self.metadata["dem_tiles"][cache_key]
                self._save_metadata()

        return None

    def cache_dem_tile(self, url: str, source_file: Path, bbox: Optional[Dict] = None) -> Path:
        """
        Cache a DEM tile.

        Args:
            url: Download URL
            source_file: Path to downloaded file
            bbox: Optional bounding box

        Returns:
            Path to cached file
        """
        cache_key = self._generate_cache_key(url, bbox)
        cached_file = self.dem_cache / source_file.name

        # Copy file to cache
        if source_file != cached_file:
            shutil.copy2(source_file, cached_file)

        # Update metadata
        self.metadata["dem_tiles"][cache_key] = {
            "url": url,
            "path": str(cached_file),
            "cached_at": datetime.now().isoformat(),
            "bbox": bbox,
            "size_mb": cached_file.stat().st_size / (1024 * 1024)
        }
        self._save_metadata()

        logger.info(f"Cached DEM tile: {cached_file.name}")
        return cached_file

    def get_map(self, url: str, bbox: Optional[Dict] = None) -> Optional[Path]:
        """
        Get cached national map if available.

        Args:
            url: Download URL
            bbox: Optional bounding box

        Returns:
            Path to cached file if available, None otherwise
        """
        cache_key = self._generate_cache_key(url, bbox)

        if cache_key in self.metadata["maps"]:
            cached_info = self.metadata["maps"][cache_key]
            cached_file = Path(cached_info["path"])

            if cached_file.exists():
                logger.info(f"Using cached map: {cached_file.name}")
                return cached_file
            else:
                logger.warning(f"Cached map missing: {cached_file}")
                del self.metadata["maps"][cache_key]
                self._save_metadata()

        return None

    def cache_map(self, url: str, source_file: Path, bbox: Optional[Dict] = None) -> Path:
        """
        Cache a national map.

        Args:
            url: Download URL
            source_file: Path to downloaded file
            bbox: Optional bounding box

        Returns:
            Path to cached file
        """
        cache_key = self._generate_cache_key(url, bbox)
        cached_file = self.maps_cache / source_file.name

        # Copy file to cache
        if source_file != cached_file:
            shutil.copy2(source_file, cached_file)

        # Update metadata
        self.metadata["maps"][cache_key] = {
            "url": url,
            "path": str(cached_file),
            "cached_at": datetime.now().isoformat(),
            "bbox": bbox,
            "size_mb": cached_file.stat().st_size / (1024 * 1024)
        }
        self._save_metadata()

        logger.info(f"Cached map: {cached_file.name}")
        return cached_file

    def list_cached_items(self) -> Dict[str, List[Dict]]:
        """
        List all cached items with their metadata.

        Returns:
            Dictionary with lists of cached DEM tiles and maps
        """
        return {
            "dem_tiles": list(self.metadata["dem_tiles"].values()),
            "maps": list(self.metadata["maps"].values())
        }

    def get_cache_size(self) -> Dict[str, float]:
        """
        Get total cache size in MB.

        Returns:
            Dictionary with cache sizes
        """
        dem_size = sum(
            info.get("size_mb", 0)
            for info in self.metadata["dem_tiles"].values()
        )
        maps_size = sum(
            info.get("size_mb", 0)
            for info in self.metadata["maps"].values()
        )

        return {
            "dem_tiles_mb": round(dem_size, 2),
            "maps_mb": round(maps_size, 2),
            "total_mb": round(dem_size + maps_size, 2)
        }

    def clear_cache(self, cache_type: Optional[str] = None) -> None:
        """
        Clear cache.

        Args:
            cache_type: Type of cache to clear ("dem_tiles", "maps", or None for all)
        """
        if cache_type is None or cache_type == "dem_tiles":
            for file in self.dem_cache.glob("*"):
                file.unlink()
            self.metadata["dem_tiles"] = {}
            logger.info("Cleared DEM tiles cache")

        if cache_type is None or cache_type == "maps":
            for file in self.maps_cache.glob("*"):
                file.unlink()
            self.metadata["maps"] = {}
            logger.info("Cleared maps cache")

        self._save_metadata()
