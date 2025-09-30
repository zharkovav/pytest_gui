"""
Logging configuration for the Pytest GUI application.
"""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    console_output: bool = True
) -> None:
    """
    Set up logging configuration for the application.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file
        console_output: Whether to output logs to console
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Add console handler if requested
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # Add file handler if log file specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Set up specific loggers
    setup_application_loggers(numeric_level)


def setup_application_loggers(level: int) -> None:
    """Set up specific loggers for different application components."""
    
    # Main application logger
    app_logger = logging.getLogger("pytest_gui")
    app_logger.setLevel(level)
    
    # Test discovery logger
    discovery_logger = logging.getLogger("pytest_gui.discovery")
    discovery_logger.setLevel(level)
    
    # Test execution logger
    execution_logger = logging.getLogger("pytest_gui.execution")
    execution_logger.setLevel(level)
    
    # UI logger
    ui_logger = logging.getLogger("pytest_gui.ui")
    ui_logger.setLevel(level)
    
    # Configuration logger
    config_logger = logging.getLogger("pytest_gui.config")
    config_logger.setLevel(level)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.
    
    Args:
        name: Logger name
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(f"pytest_gui.{name}")