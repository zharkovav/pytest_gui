# Pytest GUI

A modern GUI application for running pytest tests with advanced features like test tree visualization, marker filtering, environment configuration, and real-time progress monitoring.

## Features

- **Test Tree Visualization**: Hierarchical display of tests organized by directory structure
- **Smart Selection**: Checkbox system with parent-child relationships for easy test selection
- **Marker Filtering**: Filter tests by pytest markers (built-in and custom)
- **Environment Configuration**: Built-in .env file editor and management
- **Pytest Options**: Comprehensive options panel with descriptions
- **Real-Time Progress**: Live progress bar and status updates during test execution
- **File Watching**: Automatic test discovery when files change
- **Configuration Persistence**: Save and restore user preferences

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Install from Source

1. Clone the repository:
```bash
git clone https://github.com/pytest-gui/pytest-gui.git
cd pytest-gui
```

2. Create and activate a virtual environment:
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows (Command Prompt):
venv\Scripts\activate
# On Windows (PowerShell):
venv\Scripts\Activate.ps1
# On macOS/Linux:
source venv/bin/activate
```

**Quick Start Scripts (Windows):**
- Run `activate.bat` for Command Prompt
- Run `activate.ps1` for PowerShell

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install the package in development mode:
```bash
pip install -e .
```

### Install from PyPI (when available)

```bash
pip install pytest-gui
```

## Usage

### Command Line

Run the application from the command line:

```bash
# Run in current directory
pytest-gui

# Run in specific directory
pytest-gui /path/to/your/tests

# Or using Python module
python -m pytest_gui
python -m pytest_gui /path/to/your/tests
```

### GUI Interface

1. **Test Discovery**: The application automatically discovers tests in the specified directory
2. **Test Selection**: Use checkboxes to select which tests to run
3. **Configuration**: Configure markers, environment variables, and pytest options in the right panel
4. **Execution**: Click "Run Selected Tests" to start test execution
5. **Monitoring**: Watch real-time progress and view detailed logs

## Project Structure

```
pytest_gui/
├── main.py                     # Application entry point
├── requirements.txt            # Dependencies
├── setup.py                   # Package setup
├── pytest.ini                # Pytest configuration
├── .env.example              # Environment variables template
├── core/                     # Business logic
│   ├── test_discovery.py     # Test file scanning
│   ├── test_runner.py        # Test execution
│   ├── config_manager.py     # Configuration handling
│   └── logger.py            # Logging setup
├── ui/                       # User interface
│   ├── main_window.py        # Main application window
│   ├── test_tree.py          # Test tree widget
│   ├── marker_filter.py      # Marker filtering
│   ├── env_config.py         # Environment editor
│   ├── pytest_options.py     # Options configuration
│   └── progress_panel.py     # Progress display
├── test/                    # Sample tests
│   ├── conftest.py         # Pytest fixtures
│   └── test_sample.py      # Example tests
└── docs/                   # Documentation
```

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and modify as needed:

```bash
# Test execution settings
PYTEST_TIMEOUT=300
PYTEST_WORKERS=auto
PYTEST_VERBOSITY=1

# Application settings
LOG_LEVEL=INFO
THEME=default
AUTO_DISCOVER=true
```

### Pytest Configuration

The application respects your existing `pytest.ini` configuration:

```ini
[tool:pytest]
testpaths = test
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
    unit: marks tests as unit tests
```

## Development

### Setting up Development Environment

1. Clone the repository
2. Create and activate a virtual environment:
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows (Command Prompt):
venv\Scripts\activate
# On Windows (PowerShell):
venv\Scripts\Activate.ps1
# On macOS/Linux:
source venv/bin/activate
```

**Quick Start Scripts (Windows):**
- Run `activate.bat` for Command Prompt
- Run `activate.ps1` for PowerShell

3. Install development dependencies:
```bash
pip install -r requirements.txt
pip install -e .
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=pytest_gui

# Run specific test file
pytest test/test_sample.py

# Run with specific markers
pytest -m "unit"
```

### Code Quality

```bash
# Format code
black pytest_gui/

# Lint code
flake8 pytest_gui/

# Type checking
mypy pytest_gui/
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for your changes
5. Ensure all tests pass
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [PySide6](https://doc.qt.io/qtforpython/) for the GUI framework
- Powered by [pytest](https://pytest.org/) for test execution
- Uses [watchdog](https://python-watchdog.readthedocs.io/) for file monitoring

## Support

- Create an issue on GitHub for bug reports or feature requests
- Check the [documentation](docs/) for detailed usage instructions
- Join our community discussions

## Roadmap

- [ ] Plugin system for custom extensions
- [ ] Test report generation (HTML/PDF)
- [ ] Remote test execution
- [ ] CI/CD integration
- [ ] Team collaboration features
- [ ] Custom themes and styling
- [ ] Test templates and generators

## Screenshots

*Screenshots will be added once the GUI is fully implemented*

## System Requirements

- **Operating System**: Windows 10+, macOS 10.15+, Linux (Ubuntu 20.04+)
- **Python**: 3.8 or higher
- **Memory**: 512MB RAM minimum, 1GB recommended
- **Storage**: 100MB for application, additional space for test outputs