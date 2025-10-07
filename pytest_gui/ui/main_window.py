"""
Main application window for the Pytest GUI.
"""

import logging
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QMenuBar, QStatusBar, QToolBar, QMessageBox, QFileDialog,
    QTabWidget, QLabel, QPushButton, QTextEdit, QProgressBar
)
from PySide6.QtCore import Qt, QTimer, Signal, QObject
from PySide6.QtGui import QAction, QIcon, QFont, QTextCursor

from ..core.test_discovery import TestDiscovery
from ..core.config_manager import ConfigManager
from ..core.test_runner import TestRunner, TestRunnerState
from .test_tree import TestTreeWidget
from .marker_filter import MarkerFilterWidget
from .env_config import EnvironmentConfigWidget
from .pytest_options import PytestOptionsWidget
from .progress_panel import ProgressPanelWidget


class TestRunnerSignalBridge(QObject):
    """Thread-safe signal bridge for test runner callbacks."""
    
    state_changed = Signal(object)  # TestRunnerState
    progress_updated = Signal(object)  # TestRunnerProgress
    test_result = Signal(object)  # TestResult
    test_started = Signal(str)  # Test path that started
    output_line = Signal(str)  # Output line


class MainWindow(QMainWindow):
    """Main application window."""
    
    # Signals
    test_selection_changed = Signal(list)  # List of selected test paths
    
    def __init__(self, test_directory: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self.logger = logging.getLogger("pytest_gui.ui.main_window")
        self.test_directory = Path(test_directory)
        
        # Core components
        self.config_manager = ConfigManager()
        self.test_discovery = TestDiscovery(test_directory)
        self.test_runner = TestRunner()
        
        # Thread-safe signal bridge
        self.signal_bridge = TestRunnerSignalBridge()
        
        # UI components
        self.test_tree: Optional[TestTreeWidget] = None
        self.config_tabs: Optional[QTabWidget] = None
        self.progress_panel: Optional[ProgressPanelWidget] = None
        self.status_label: Optional[QLabel] = None
        self.output_console: Optional[QTextEdit] = None
        self.progress_bar: Optional[QProgressBar] = None
        
        # Configuration widgets
        self.marker_filter: Optional[MarkerFilterWidget] = None
        self.env_config: Optional[EnvironmentConfigWidget] = None
        self.pytest_options: Optional[PytestOptionsWidget] = None
        
        # Initialize UI
        self.setup_ui()
        self.setup_connections()
        self.restore_window_state()
        
        # Start test discovery
        self.discover_tests()
        
    def setup_ui(self) -> None:
        """Set up the user interface."""
        self.setWindowTitle(f"Pytest GUI - {self.test_directory.name}")
        self.setMinimumSize(800, 600)

        my_icon = QIcon()
        my_icon.addFile('app_icon.png')
        self.setWindowIcon(my_icon)

        # Create menu bar
        self.create_menu_bar()
        
        # Create toolbar
        self.create_toolbar()
        
        # Create central widget
        self.create_central_widget()
        
        # Create status bar
        self.create_status_bar()
        
    def create_menu_bar(self) -> None:
        """Create the application menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        open_action = QAction("&Open Project...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_project)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        # Recent projects submenu
        recent_menu = file_menu.addMenu("Recent Projects")
        self.update_recent_projects_menu(recent_menu)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        refresh_action = QAction("&Refresh Tests", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self.refresh_tests)
        view_menu.addAction(refresh_action)
        
        view_menu.addSeparator()
        
        expand_all_action = QAction("&Expand All", self)
        expand_all_action.triggered.connect(self.expand_all_tests)
        view_menu.addAction(expand_all_action)
        
        collapse_all_action = QAction("&Collapse All", self)
        collapse_all_action.triggered.connect(self.collapse_all_tests)
        view_menu.addAction(collapse_all_action)
        
        # Tests menu
        tests_menu = menubar.addMenu("&Tests")
        
        select_all_action = QAction("Select &All", self)
        select_all_action.setShortcut("Ctrl+A")
        select_all_action.triggered.connect(self.select_all_tests)
        tests_menu.addAction(select_all_action)
        
        deselect_all_action = QAction("&Deselect All", self)
        deselect_all_action.setShortcut("Ctrl+D")
        deselect_all_action.triggered.connect(self.deselect_all_tests)
        tests_menu.addAction(deselect_all_action)
        
        tests_menu.addSeparator()
        
        run_selected_action = QAction("&Run Selected Tests", self)
        run_selected_action.setShortcut("Ctrl+R")
        run_selected_action.triggered.connect(self.run_selected_tests)
        tests_menu.addAction(run_selected_action)
        
        stop_tests_action = QAction("&Stop Tests", self)
        stop_tests_action.setShortcut("Ctrl+S")
        stop_tests_action.triggered.connect(self.stop_tests)
        tests_menu.addAction(stop_tests_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def create_toolbar(self) -> None:
        """Create the application toolbar."""
        toolbar = self.addToolBar("Main")
        toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        
        # Refresh button
        refresh_action = QAction("Refresh", self)
        refresh_action.setToolTip("Refresh test discovery")
        refresh_action.triggered.connect(self.refresh_tests)
        toolbar.addAction(refresh_action)
        
        toolbar.addSeparator()
        
        # Run button
        run_action = QAction("Run Tests", self)
        run_action.setToolTip("Run selected tests")
        run_action.triggered.connect(self.run_selected_tests)
        toolbar.addAction(run_action)
        
        # Stop button
        stop_action = QAction("Stop", self)
        stop_action.setToolTip("Stop running tests")
        stop_action.triggered.connect(self.stop_tests)
        toolbar.addAction(stop_action)
        
    def create_central_widget(self) -> None:
        """Create the central widget with main layout."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main vertical splitter
        main_splitter = QSplitter(Qt.Vertical)
        
        # Top horizontal splitter
        top_splitter = QSplitter(Qt.Horizontal)
        
        # Left panel: Test tree
        self.test_tree = TestTreeWidget()
        self.test_tree.setMinimumWidth(600)
        top_splitter.addWidget(self.test_tree)
        
        # Right panel: Configuration and progress
        right_panel = self.create_right_panel()
        top_splitter.addWidget(right_panel)
        
        # Set top splitter proportions
        top_splitter.setSizes([400, 800])
        
        # Add top splitter to main splitter
        main_splitter.addWidget(top_splitter)
        
        # Bottom panel: Output console
        output_panel = self.create_output_panel()
        main_splitter.addWidget(output_panel)
        
        # Set main splitter proportions (top 70%, bottom 30%)
        main_splitter.setSizes([700, 300])
        
        # Main layout
        layout = QVBoxLayout(central_widget)
        layout.addWidget(main_splitter)
        
    def create_right_panel(self) -> QWidget:
        """Create the right panel with configuration tabs and progress."""
        right_widget = QWidget()
        layout = QVBoxLayout(right_widget)
        
        # Configuration tabs
        self.config_tabs = QTabWidget()
        
        # Markers tab
        markers_tab = self.create_markers_tab()
        self.config_tabs.addTab(markers_tab, "Markers")
        
        # Environment tab
        env_tab = self.create_environment_tab()
        self.config_tabs.addTab(env_tab, "Environment")
        
        # Options tab
        options_tab = self.create_options_tab()
        self.config_tabs.addTab(options_tab, "Options")
        
        layout.addWidget(self.config_tabs)
        
        # Progress panel
        self.progress_panel = self.create_progress_panel()
        layout.addWidget(self.progress_panel)
        
        return right_widget
        
    def create_markers_tab(self) -> QWidget:
        """Create the markers configuration tab."""
        self.marker_filter = MarkerFilterWidget()
        self.marker_filter.markers_changed.connect(self.on_markers_changed)
        return self.marker_filter
        
    def create_environment_tab(self) -> QWidget:
        """Create the environment configuration tab."""
        self.env_config = EnvironmentConfigWidget()
        self.env_config.env_vars_changed.connect(self.on_env_vars_changed)
        return self.env_config
        
    def create_options_tab(self) -> QWidget:
        """Create the pytest options tab."""
        self.pytest_options = PytestOptionsWidget()
        self.pytest_options.options_changed.connect(self.on_pytest_options_changed)
        return self.pytest_options
        
    def create_progress_panel(self) -> QWidget:
        """Create the progress and logging panel."""
        self.progress_panel = ProgressPanelWidget()
        self.progress_panel.run_tests_requested.connect(self.run_selected_tests)
        self.progress_panel.stop_tests_requested.connect(self.stop_tests)
        return self.progress_panel
        
    def create_output_panel(self) -> QWidget:
        """Create the output console panel."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Header
        header_layout = QHBoxLayout()
        header_label = QLabel("Test Output")
        header_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        header_layout.addWidget(header_label)
        
        # Clear button
        clear_button = QPushButton("Clear")
        clear_button.setMaximumWidth(80)
        clear_button.clicked.connect(self.clear_output)
        header_layout.addWidget(clear_button)
        
        layout.addLayout(header_layout)
        
        # Output console
        self.output_console = QTextEdit()
        self.output_console.setReadOnly(True)
        self.output_console.setMinimumHeight(150)
        
        # Set monospace font for better output formatting
        font = QFont("Consolas", 9)
        if not font.exactMatch():
            font = QFont("Courier New", 9)
        self.output_console.setFont(font)
        
        # Set dark theme for console
        self.output_console.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3e3e3e;
            }
        """)
        
        layout.addWidget(self.output_console)
        
        return widget
        
    def create_status_bar(self) -> None:
        """Create the status bar."""
        status_bar = self.statusBar()
        
        self.status_label = QLabel("Ready")
        status_bar.addWidget(self.status_label)
        
        # Add permanent widgets
        test_count_label = QLabel("Tests: 0")
        status_bar.addPermanentWidget(test_count_label)
        
    def setup_connections(self) -> None:
        """Set up signal connections."""
        if self.test_tree:
            self.test_tree.selection_changed.connect(self.on_test_selection_changed)
            
        # Connect test runner signals through thread-safe bridge
        self.signal_bridge.state_changed.connect(self.on_test_runner_state_changed)
        self.signal_bridge.progress_updated.connect(self.on_test_progress_update)
        self.signal_bridge.test_result.connect(self.on_test_result)
        self.signal_bridge.test_started.connect(self.on_test_started)
        self.signal_bridge.output_line.connect(self.on_test_output_line)
        
        # Connect test runner callbacks to signal bridge
        self.test_runner.on_state_changed = self.signal_bridge.state_changed.emit
        self.test_runner.on_progress_update = self.signal_bridge.progress_updated.emit
        self.test_runner.on_test_result = self.signal_bridge.test_result.emit
        self.test_runner.on_test_started = self.signal_bridge.test_started.emit
        self.test_runner.on_output_line = self.signal_bridge.output_line.emit
        
        # Connect progress panel signals
        if self.progress_panel:
            self.signal_bridge.state_changed.connect(self.progress_panel.on_test_runner_state_changed)
            self.signal_bridge.progress_updated.connect(self.progress_panel.on_progress_update)
            
    def discover_tests(self) -> None:
        """Start test discovery."""
        self.status_label.setText("Discovering tests...")
        
        try:
            # Start file watching
            self.test_discovery.start_watching()
            
            # Discover tests
            root_node = self.test_discovery.discover_tests()
            
            # Update test tree
            if self.test_tree:
                self.test_tree.set_root_node(root_node)
                
            # Update status
            test_count = len(root_node.get_all_test_children())
            self.status_label.setText(f"Found {test_count} tests")
            
            # Update progress panel
            if self.progress_panel:
                self.progress_panel.set_test_count(test_count)
            
            # Extract and set available markers
            all_markers = set()
            for test in root_node.get_all_test_children():
                all_markers.update(test.markers)
            
            if self.marker_filter:
                self.marker_filter.set_available_markers(all_markers)
            
            self.logger.info(f"Test discovery completed: {test_count} tests found")
            
        except Exception as e:
            self.logger.error(f"Test discovery failed: {e}")
            self.status_label.setText("Test discovery failed")
            QMessageBox.critical(self, "Error", f"Failed to discover tests:\n{e}")
            
    def refresh_tests(self) -> None:
        """Refresh test discovery."""
        self.logger.info("Refreshing tests")
        self.discover_tests()
        
    def expand_all_tests(self) -> None:
        """Expand all items in test tree."""
        if self.test_tree:
            self.test_tree.expandAll()
            
    def collapse_all_tests(self) -> None:
        """Collapse all items in test tree."""
        if self.test_tree:
            self.test_tree.collapseAll()
            
    def select_all_tests(self) -> None:
        """Select all tests."""
        if self.test_tree:
            self.test_tree.select_all()
            
    def deselect_all_tests(self) -> None:
        """Deselect all tests."""
        if self.test_tree:
            self.test_tree.deselect_all()
            
    def run_selected_tests(self) -> None:
        """Run selected tests."""
        if self.test_tree:
            selected_tests = self.test_tree.get_selected_tests()
            if selected_tests:
                self.logger.info(f"Selected tests: {selected_tests}")
                # Filter out duplicates and invalid paths
                unique_tests = []
                seen = set()
                for test_path in selected_tests:
                    if test_path not in seen and '::' in test_path:  # Only actual test functions/methods
                        unique_tests.append(test_path)
                        seen.add(test_path)
                
                if unique_tests:
                    self.logger.info(f"Running {len(unique_tests)} selected tests")
                    self.status_label.setText(f"Running {len(unique_tests)} tests...")
                    
                    # Get configuration options
                    pytest_args = []
                    env_vars = {}
                    
                    if self.pytest_options:
                        pytest_args = self.pytest_options.get_pytest_args()
                    
                    if self.env_config:
                        env_vars = self.env_config.get_env_vars()
                    
                    # Start test execution
                    success = self.test_runner.start_tests(
                        test_paths=unique_tests,
                        pytest_args=pytest_args,
                        env_vars=env_vars,
                        working_dir=str(self.test_directory)
                    )
                    
                    if not success:
                        QMessageBox.critical(self, "Error", "Failed to start test execution.")
                        self.status_label.setText("Ready")
                else:
                    QMessageBox.information(self, "No Valid Tests",
                                          "No valid test functions selected.")
            else:
                QMessageBox.information(self, "No Tests Selected",
                                      "Please select tests to run.")
                
    def stop_tests(self) -> None:
        """Stop running tests."""
        self.logger.info("Stopping tests")
        self.status_label.setText("Stopping tests...")
        self.test_runner.stop_tests()
        
    def on_test_selection_changed(self, selected_tests: list) -> None:
        """Handle test selection changes."""
        self.test_selection_changed.emit(selected_tests)
        
    def on_test_runner_state_changed(self, state: TestRunnerState) -> None:
        """Handle test runner state changes."""
        if state == TestRunnerState.RUNNING:
            self.status_label.setText("Running tests...")
            if self.progress_bar:
                self.progress_bar.setVisible(True)
                self.progress_bar.setRange(0, 0)  # Indeterminate progress
            if self.output_console:
                self.output_console.append("=== Test execution started ===")
            # Reset all test statuses to PENDING when starting
            if self.test_tree:
                self.test_tree.reset_test_statuses()
        elif state == TestRunnerState.STOPPING:
            self.status_label.setText("Stopping tests...")
            if self.output_console:
                self.output_console.append("=== Stopping tests ===")
        elif state == TestRunnerState.STOPPED:
            self.status_label.setText("Tests stopped")
            if self.progress_bar:
                self.progress_bar.setVisible(False)
            if self.output_console:
                self.output_console.append("=== Tests stopped ===")
        elif state == TestRunnerState.IDLE:
            self.status_label.setText("Ready")
            if self.progress_bar:
                self.progress_bar.setVisible(False)
            if self.output_console:
                self.output_console.append("=== Test execution completed ===")
        elif state == TestRunnerState.ERROR:
            self.status_label.setText("Test execution error")
            if self.progress_bar:
                self.progress_bar.setVisible(False)
            if self.output_console:
                self.output_console.append("=== Test execution error ===")
            
    def on_test_progress_update(self, progress) -> None:
        """Handle test progress updates."""
        if progress.total_tests > 0:
            percentage = progress.progress_percentage
            self.status_label.setText(
                f"Running tests: {progress.completed_tests}/{progress.total_tests} "
                f"({percentage:.1f}%) - "
                f"Passed: {progress.passed_tests}, "
                f"Failed: {progress.failed_tests}, "
                f"Skipped: {progress.skipped_tests}"
            )
            
            # Update progress bar
            if self.progress_bar:
                self.progress_bar.setRange(0, progress.total_tests)
                self.progress_bar.setValue(progress.completed_tests)
            
    def on_test_started(self, test_path: str) -> None:
        """Handle test started event."""
        # Update test tree to show test is running
        if self.test_tree:
            self.test_tree.set_test_running(test_path)
            
    def on_test_result(self, result) -> None:
        """Handle individual test results."""
        # Update test tree with result
        if self.test_tree:
            self.test_tree.update_test_status(result.test_path, result.status)
            
    def on_test_output_line(self, line: str) -> None:
        """Handle test output lines."""
        # Display output in console
        if self.output_console:
            # Add timestamp for better readability
            import datetime
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            formatted_line = f"[{timestamp}] {line}"
            
            # Append to console
            self.output_console.append(formatted_line)
            
            # Auto-scroll to bottom
            cursor = self.output_console.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            self.output_console.setTextCursor(cursor)
        
        # Also log for debugging
        self.logger.debug(f"Test output: {line}")
        
    def clear_output(self) -> None:
        """Clear the output console."""
        if self.output_console:
            self.output_console.clear()
            
    def on_markers_changed(self, selected_markers: set) -> None:
        """Handle marker filter changes."""
        if self.test_tree:
            self.test_tree.filter_by_markers(selected_markers)
        self.logger.debug(f"Marker filter changed: {selected_markers}")
        
    def on_env_vars_changed(self, env_vars: dict) -> None:
        """Handle environment variable changes."""
        self.logger.debug(f"Environment variables changed: {len(env_vars)} variables")
        
    def on_pytest_options_changed(self, options: list) -> None:
        """Handle pytest options changes."""
        self.logger.debug(f"Pytest options changed: {options}")
        
    def open_project(self) -> None:
        """Open a different project directory."""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Test Directory", str(self.test_directory.parent)
        )
        
        if directory:
            self.config_manager.add_recent_project(directory)
            test_path = Path(directory).resolve()
            self.test_directory = test_path
            self.test_discovery = TestDiscovery(directory)
            self.refresh_tests()
            
    def update_recent_projects_menu(self, menu) -> None:
        """Update the recent projects menu."""
        menu.clear()
        recent_projects = self.config_manager.get_recent_projects()
        
        for project_path in recent_projects:
            action = QAction(project_path, self)
            action.triggered.connect(lambda checked, path=project_path: self.open_recent_project(path))
            menu.addAction(action)
            
        if recent_projects:
            menu.addSeparator()
            clear_action = QAction("Clear Recent Projects", self)
            clear_action.triggered.connect(self.clear_recent_projects)
            menu.addAction(clear_action)
            
    def open_recent_project(self, project_path: str) -> None:
        """Open a recent project."""
        # TODO: Implement recent project opening
        pass
        
    def clear_recent_projects(self) -> None:
        """Clear recent projects list."""
        self.config_manager.clear_recent_projects()
        
    def show_about(self) -> None:
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About Pytest GUI",
            "Pytest GUI v1.0.0\n\n"
            "A modern GUI application for running pytest tests.\n\n"
            "Built with PySide6 and Python."
        )
        
    def restore_window_state(self) -> None:
        """Restore window state from configuration."""
        width = self.config_manager.get_app_setting('window.width', 1200)
        height = self.config_manager.get_app_setting('window.height', 800)
        self.resize(width, height)
        
        if self.config_manager.get_app_setting('window.maximized', False):
            self.showMaximized()
            
    def save_window_state(self) -> None:
        """Save current window state to configuration."""
        self.config_manager.set_app_setting('window.width', self.width())
        self.config_manager.set_app_setting('window.height', self.height())
        self.config_manager.set_app_setting('window.maximized', self.isMaximized())
        self.config_manager.save_config()
        
    def closeEvent(self, event) -> None:
        """Handle window close event."""
        self.save_window_state()
        
        # Stop test runner if running
        if self.test_runner and self.test_runner.is_running():
            self.test_runner.stop_tests()
        
        # Stop file watching
        if self.test_discovery:
            self.test_discovery.stop_watching()
            
        event.accept()