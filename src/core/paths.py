"""
Path management for A3DShell A3Dshell.

Manages all input, output, and cache directory paths in a centralized way.
"""

from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class PathManager:
    """Manages all directory paths for A3DShell simulation."""

    def __init__(self, base_dir: Optional[Path] = None, simu_name: Optional[str] = None):
        """
        Initialize path manager.

        Args:
            base_dir: Base directory for A3Dshell (defaults to auto-detect)
            simu_name: Simulation name (required for output paths)
        """
        if base_dir is None:
            # Auto-detect base directory (assume we're in src/)
            self.base_dir = Path(__file__).parent.parent.parent
        else:
            self.base_dir = Path(base_dir)

        self.simu_name = simu_name

        # Main directories
        self.input_dir = self.base_dir / "input"
        self.output_dir = self.base_dir / "output"
        self.cache_dir = self.base_dir / "cache"

        # Input subdirectories
        self.input_brdf = self.input_dir / "brdf-files"
        self.input_templates = self.input_dir / "templates"
        self.input_imis = self.input_dir / "imis"

        # Cache subdirectories
        self.cache_dem = self.cache_dir / "dem_tiles"
        self.cache_tlm = self.cache_dir / "tlm"
        self.cache_maps = self.cache_dir / "maps"
        self.cache_metadata = self.cache_dir / "metadata.json"

    def get_simulation_dir(self, create: bool = True) -> Path:
        """
        Get simulation-specific output directory.

        Args:
            create: Whether to create the directory if it doesn't exist

        Returns:
            Path to simulation directory

        Raises:
            ValueError: If simu_name is not set
        """
        if not self.simu_name:
            raise ValueError("Simulation name not set")

        simu_dir = self.output_dir / self.simu_name
        if create:
            simu_dir.mkdir(parents=True, exist_ok=True)
        return simu_dir

    def get_simu_input_dir(self, create: bool = True) -> Path:
        """Get simulation input directory."""
        simu_dir = self.get_simulation_dir(create=create)
        input_dir = simu_dir / "input"
        if create:
            input_dir.mkdir(parents=True, exist_ok=True)
        return input_dir

    def get_simu_output_dir(self, create: bool = True) -> Path:
        """Get simulation output directory."""
        simu_dir = self.get_simulation_dir(create=create)
        output_dir = simu_dir / "output"
        if create:
            output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir

    def get_simu_grids_dir(self, create: bool = True) -> Path:
        """Get simulation surface grids directory."""
        input_dir = self.get_simu_input_dir(create=create)
        grids_dir = input_dir / "surface-grids"
        if create:
            grids_dir.mkdir(parents=True, exist_ok=True)
        return grids_dir

    def get_simu_meteo_dir(self, create: bool = True) -> Path:
        """Get simulation meteo directory."""
        input_dir = self.get_simu_input_dir(create=create)
        meteo_dir = input_dir / "meteo"
        if create:
            meteo_dir.mkdir(parents=True, exist_ok=True)
        return meteo_dir

    def get_simu_snowfiles_dir(self, create: bool = True) -> Path:
        """Get simulation snowfiles directory."""
        input_dir = self.get_simu_input_dir(create=create)
        snow_dir = input_dir / "snowfiles"
        if create:
            snow_dir.mkdir(parents=True, exist_ok=True)
        return snow_dir

    def get_simu_brdf_dir(self, create: bool = True) -> Path:
        """Get simulation BRDF directory."""
        input_dir = self.get_simu_input_dir(create=create)
        brdf_dir = input_dir / "brdf-files"
        if create:
            brdf_dir.mkdir(parents=True, exist_ok=True)
        return brdf_dir

    def get_simu_mapping_dir(self, create: bool = True) -> Path:
        """Get simulation mapping/visualization directory."""
        simu_dir = self.get_simulation_dir(create=create)
        mapping_dir = simu_dir / "mapping"
        if create:
            mapping_dir.mkdir(parents=True, exist_ok=True)
        return mapping_dir

    def get_dem_file(self, gsd: float) -> Path:
        """Get DEM file path for simulation."""
        grids_dir = self.get_simu_grids_dir()
        return grids_dir / f"{int(gsd)}m_dem_{self.simu_name}.asc"

    def get_lus_file(self, gsd: float) -> Path:
        """Get LUS file path for simulation."""
        grids_dir = self.get_simu_grids_dir()
        return grids_dir / f"{int(gsd)}m_lus_{self.simu_name}.lus"

    def get_mesh_file(self, gsd: float, fmt: str = "vtu") -> Path:
        """Get mesh file path for simulation."""
        grids_dir = self.get_simu_grids_dir()
        return grids_dir / f"{int(gsd)}m_mesh_{self.simu_name}.{fmt}"

    def create_all_directories(self) -> None:
        """Create all necessary directories."""
        directories = [
            self.input_dir,
            self.input_brdf,
            self.input_templates,
            self.input_imis,
            self.output_dir,
            self.cache_dir,
            self.cache_dem,
            self.cache_tlm,
            self.cache_maps,
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {directory}")

        logger.info("All base directories created/verified")

    def __str__(self) -> str:
        """String representation of paths."""
        return (
            f"PathManager(\n"
            f"  base_dir={self.base_dir}\n"
            f"  simulation={self.simu_name}\n"
            f"  input_dir={self.input_dir}\n"
            f"  output_dir={self.output_dir}\n"
            f"  cache_dir={self.cache_dir}\n"
            f")"
        )
