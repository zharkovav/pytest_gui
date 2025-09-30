"""
Entry point for running pytest_gui as a module.
"""

import sys
from .main import main, parse_arguments

if __name__ == "__main__":
    # Parse command line arguments
    args = parse_arguments()
    sys.exit(main(args.test_directory))