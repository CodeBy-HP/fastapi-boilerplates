"""
Modular Logger Configuration for FastAPI Applications

This module provides a customizable logging setup that works alongside Uvicorn.
It can be easily copied to other projects and configured via environment variables.

Features:
- Custom log formatting with colors
- Separate log files for different log levels
- Console and file handlers
- Non-interfering with Uvicorn's logger
- Easy customization through configuration
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from logging.handlers import RotatingFileHandler
from datetime import datetime


class ColoredFormatter(logging.Formatter):
    """Custom formatter with color support for console output"""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }

    def format(self, record):
        # Add color to levelname
        if record.levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[record.levelname]}{record.levelname}"
                f"{self.COLORS['RESET']}"
            )
        return super().format(record)


class LoggerConfig:
    """Configuration class for logger setup"""
    
    def __init__(
        self,
        logger_name: str = "app",
        log_level: str = "INFO",
        log_dir: str = "logs",
        log_to_console: bool = True,
        log_to_file: bool = True,
        max_file_size: int = 10 * 1024 * 1024,  # 10 MB
        backup_count: int = 5,
        log_format: Optional[str] = None,
        date_format: Optional[str] = None,
        use_colors: bool = True,
    ):
        """
        Initialize logger configuration
        
        Args:
            logger_name: Name of the logger (default: "app")
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_dir: Directory to store log files
            log_to_console: Enable console logging
            log_to_file: Enable file logging
            max_file_size: Maximum size of log file before rotation (bytes)
            backup_count: Number of backup files to keep
            log_format: Custom log format string
            date_format: Custom date format string
            use_colors: Use colored output in console
        """
        self.logger_name = logger_name
        self.log_level = getattr(logging, log_level.upper(), logging.INFO)
        self.log_dir = Path(log_dir)
        self.log_to_console = log_to_console
        self.log_to_file = log_to_file
        self.max_file_size = max_file_size
        self.backup_count = backup_count
        self.use_colors = use_colors
        
        # Default log format
        self.log_format = log_format or (
            "%(asctime)s | %(levelname)-8s | %(name)s | %(module)s:%(funcName)s:%(lineno)d | %(message)s"
        )
        
        # Default date format
        self.date_format = date_format or "%Y-%m-%d %H:%M:%S"


def setup_logger(config: Optional[LoggerConfig] = None) -> logging.Logger:
    """
    Setup and configure the application logger
    
    Args:
        config: LoggerConfig instance. If None, uses default configuration
        
    Returns:
        Configured logger instance
    """
    if config is None:
        config = LoggerConfig()
    
    # Create logger
    logger = logging.getLogger(config.logger_name)
    logger.setLevel(config.log_level)
    
    # Prevent propagation to root logger to avoid conflicts with Uvicorn
    logger.propagate = False
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Console Handler
    if config.log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(config.log_level)
        
        if config.use_colors:
            console_formatter = ColoredFormatter(
                fmt=config.log_format,
                datefmt=config.date_format
            )
        else:
            console_formatter = logging.Formatter(
                fmt=config.log_format,
                datefmt=config.date_format
            )
        
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    # File Handlers
    if config.log_to_file:
        # Create logs directory if it doesn't exist
        config.log_dir.mkdir(parents=True, exist_ok=True)
        
        # General log file (all levels)
        general_log_file = config.log_dir / f"{config.logger_name}.log"
        file_handler = RotatingFileHandler(
            general_log_file,
            maxBytes=config.max_file_size,
            backupCount=config.backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(config.log_level)
        file_formatter = logging.Formatter(
            fmt=config.log_format,
            datefmt=config.date_format
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        # Error log file (ERROR and CRITICAL only)
        error_log_file = config.log_dir / f"{config.logger_name}_error.log"
        error_handler = RotatingFileHandler(
            error_log_file,
            maxBytes=config.max_file_size,
            backupCount=config.backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        logger.addHandler(error_handler)
    
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance
    
    Args:
        name: Name for the logger. If None, returns the main app logger.
              If provided, returns a child logger (e.g., "app.module_name")
        
    Returns:
        Logger instance
    """
    if name:
        return logging.getLogger(f"app.{name}")
    return logging.getLogger("app")


# Example usage and quick setup function
def quick_setup(
    log_level: str = "INFO",
    log_dir: str = "logs",
    use_colors: bool = True
) -> logging.Logger:
    """
    Quick logger setup with common defaults
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory to store log files
        use_colors: Use colored console output
        
    Returns:
        Configured logger instance
    """
    config = LoggerConfig(
        log_level=log_level,
        log_dir=log_dir,
        use_colors=use_colors
    )
    return setup_logger(config)
