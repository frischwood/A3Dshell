"""
Common helper utilities for A3DShell A3Dshell.
"""

import logging
from pathlib import Path
import zipfile
import shutil
from typing import List, Optional

logger = logging.getLogger(__name__)


def unzip_file(zip_path: Path, extract_dir: Optional[Path] = None) -> Path:
    """
    Extract zip file.

    Args:
        zip_path: Path to zip file
        extract_dir: Directory to extract to (defaults to same directory as zip)

    Returns:
        Path to extraction directory
    """
    zip_path = Path(zip_path)

    if extract_dir is None:
        extract_dir = zip_path.parent

    extract_dir = Path(extract_dir)
    extract_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Extracting {zip_path.name} to {extract_dir}")

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)

    return extract_dir


def zip_directory(
    dir_path: Path,
    output_path: Optional[Path] = None,
    exclude_dirs: Optional[List[str]] = None
) -> Path:
    """
    Create zip archive of directory.

    Args:
        dir_path: Directory to zip
        output_path: Output zip path (defaults to dir_path.zip)
        exclude_dirs: List of subdirectory names to exclude

    Returns:
        Path to created zip file
    """
    dir_path = Path(dir_path)
    exclude_dirs = exclude_dirs or []

    if output_path is None:
        output_path = dir_path.parent / f"{dir_path.name}.zip"
    else:
        output_path = Path(output_path)

    logger.info(f"Zipping {dir_path} to {output_path}")

    # Temporarily move excluded directories
    temp_moved = {}
    for exclude_dir in exclude_dirs:
        exclude_path = dir_path / exclude_dir
        if exclude_path.exists() and exclude_path.is_dir():
            temp_path = dir_path.parent / f"_temp_{exclude_dir}"
            shutil.move(str(exclude_path), str(temp_path))
            temp_moved[exclude_dir] = temp_path
            logger.debug(f"Temporarily moved {exclude_dir}")

    try:
        # Create zip archive
        shutil.make_archive(
            str(output_path.with_suffix('')),
            'zip',
            dir_path
        )

    finally:
        # Move back excluded directories
        for exclude_dir, temp_path in temp_moved.items():
            shutil.move(str(temp_path), str(dir_path / exclude_dir))
            logger.debug(f"Restored {exclude_dir}")

    logger.info(f"Created zip archive: {output_path}")
    return output_path


def copy_tree(src_dir: Path, dst_dir: Path) -> None:
    """
    Copy directory tree from src to dst.

    Args:
        src_dir: Source directory
        dst_dir: Destination directory
    """
    src_dir = Path(src_dir)
    dst_dir = Path(dst_dir)

    if not src_dir.exists():
        raise FileNotFoundError(f"Source directory not found: {src_dir}")

    dst_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Copying {src_dir} to {dst_dir}")

    shutil.copytree(src_dir, dst_dir, dirs_exist_ok=True)


def ensure_directory(path: Path) -> Path:
    """
    Ensure directory exists, create if necessary.

    Args:
        path: Directory path

    Returns:
        Path object
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_file_size_mb(file_path: Path) -> float:
    """
    Get file size in MB.

    Args:
        file_path: Path to file

    Returns:
        File size in MB
    """
    file_path = Path(file_path)
    if not file_path.exists():
        return 0.0

    return file_path.stat().st_size / (1024 * 1024)
