"""
Logging utilities for A3DShell A3Dshell.

Provides consistent logging configuration across the application.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


def setup_logging(
    level: str = "INFO",
    log_file: Optional[Path] = None,
    log_to_console: bool = True
) -> logging.Logger:
    """
    Setup logging configuration for A3DShell.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file
        log_to_console: Whether to log to console

    Returns:
        Configured root logger
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # File handler
    if log_file:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    return root_logger


def log_section(logger: logging.Logger, section_name: str, start_time: datetime) -> None:
    """
    Log a section progress with elapsed time.

    Args:
        logger: Logger instance
        section_name: Name of the section
        start_time: Start time of the overall process
    """
    elapsed = datetime.now() - start_time
    logger.info(f"[{elapsed}] {section_name}")


class ProgressLogger:
    """Simple progress logger for long-running operations."""

    def __init__(self, logger: logging.Logger, total: int, operation: str):
        """
        Initialize progress logger.

        Args:
            logger: Logger instance
            total: Total number of items
            operation: Description of operation
        """
        self.logger = logger
        self.total = total
        self.operation = operation
        self.current = 0
        self.start_time = datetime.now()

    def update(self, count: int = 1) -> None:
        """Update progress counter."""
        self.current += count
        if self.current % max(1, self.total // 10) == 0 or self.current == self.total:
            progress_pct = (self.current / self.total) * 100
            elapsed = datetime.now() - self.start_time
            self.logger.info(
                f"{self.operation}: {self.current}/{self.total} ({progress_pct:.0f}%) "
                f"[Elapsed: {elapsed}]"
            )

    def finish(self) -> None:
        """Log completion."""
        elapsed = datetime.now() - self.start_time
        self.logger.info(f"{self.operation} completed in {elapsed}")
