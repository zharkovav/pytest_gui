"""
Main entry point for the Pytest GUI application.
"""

import sys
import os
import logging
import argparse
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

try:
    # Try relative imports first (when run as module)
    from .core.logger import setup_logging
    from .ui.main_window import MainWindow
except ImportError:
    # Fall back to absolute imports (when run directly)
    from pytest_gui.core.logger import setup_logging
    from pytest_gui.ui.main_window import MainWindow


def setup_application() -> QApplication:
    """Set up the QApplication with proper configuration."""
    # Enable high DPI scaling
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    app.setApplicationName("Pytest GUI")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Pytest GUI Team")
    app.setOrganizationDomain("pytest-gui.com")
    
    # Set application icon
    icon_path = Path(__file__).parent / "resources" / "icons" / "app_icon.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    
    return app


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Pytest GUI - A modern GUI for running pytest tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  pytest-gui                    # Run in current directory
  pytest-gui /path/to/tests     # Run in specific directory
  python -m pytest_gui         # Run as module in current directory
        """
    )
    
    parser.add_argument(
        "test_directory",
        nargs="?",
        default=None,
        help="Path to the test directory (default: current directory)"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="Pytest GUI 1.0.0"
    )
    
    return parser.parse_args()


def main(test_directory: Optional[str] = None) -> int:
    """
    Main entry point for the application.
    
    Args:
        test_directory: Optional path to the test directory to open
        
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        # Set up logging
        setup_logging()
        logger = logging.getLogger(__name__)
        logger.info("Starting Pytest GUI application")
        
        # Create QApplication
        app = setup_application()
        
        # Determine test directory
        if test_directory is None:
            test_directory = os.getcwd()
        
        test_path = Path(test_directory).resolve()
        if not test_path.exists():
            logger.error(f"Test directory does not exist: {test_path}")
            return 1
            
        logger.info(f"Using test directory: {test_path}")
        
        # Create and show main window
        main_window = MainWindow(test_directory=str(test_path))
        main_window.show()
        
        # Start event loop
        return app.exec()
        
    except Exception as e:
        logging.error(f"Failed to start application: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    # Parse command line arguments
    args = parse_arguments()
    sys.exit(main(args.test_directory))