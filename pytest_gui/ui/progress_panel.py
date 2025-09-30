"""
Progress panel widget for pytest GUI.
"""

import logging
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QProgressBar, QLabel,
    QPushButton, QFrame, QGridLayout
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont

from ..core.test_runner import TestRunnerProgress, TestRunnerState


class ProgressPanelWidget(QWidget):
    """Widget for displaying test execution progress."""
    
    # Signals
    run_tests_requested = Signal()
    stop_tests_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.logger = logging.getLogger("pytest_gui.ui.progress_panel")
        self.current_progress: Optional[TestRunnerProgress] = None
        self.start_time: Optional[float] = None
        
        self.setup_ui()
        self.setup_timer()
        
    def setup_ui(self) -> None:
        """Set up the progress panel UI."""
        layout = QVBoxLayout(self)
        
        # Header
        header_label = QLabel("Test Execution Progress")
        header_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(header_label)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.run_button = QPushButton("Run Selected Tests")
        self.run_button.clicked.connect(self.run_tests_requested.emit)
        button_layout.addWidget(self.run_button)
        
        self.stop_button = QPushButton("Stop Tests")
        self.stop_button.clicked.connect(self.stop_tests_requested.emit)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Progress statistics
        stats_frame = QFrame()
        stats_frame.setFrameStyle(QFrame.StyledPanel)
        stats_layout = QGridLayout(stats_frame)
        
        # Create stat labels
        self.total_label = QLabel("Total: 0")
        self.completed_label = QLabel("Completed: 0")
        self.passed_label = QLabel("Passed: 0")
        self.failed_label = QLabel("Failed: 0")
        self.skipped_label = QLabel("Skipped: 0")
        self.error_label = QLabel("Errors: 0")
        self.elapsed_label = QLabel("Elapsed: 00:00")
        self.remaining_label = QLabel("Remaining: 0")
        
        # Style the labels
        self.passed_label.setStyleSheet("color: green; font-weight: bold;")
        self.failed_label.setStyleSheet("color: red; font-weight: bold;")
        self.skipped_label.setStyleSheet("color: orange; font-weight: bold;")
        self.error_label.setStyleSheet("color: purple; font-weight: bold;")
        
        # Arrange in grid
        stats_layout.addWidget(self.total_label, 0, 0)
        stats_layout.addWidget(self.completed_label, 0, 1)
        stats_layout.addWidget(self.passed_label, 1, 0)
        stats_layout.addWidget(self.failed_label, 1, 1)
        stats_layout.addWidget(self.skipped_label, 2, 0)
        stats_layout.addWidget(self.error_label, 2, 1)
        stats_layout.addWidget(self.elapsed_label, 3, 0)
        stats_layout.addWidget(self.remaining_label, 3, 1)
        
        layout.addWidget(stats_frame)
        
        # Current test label
        self.current_test_label = QLabel("No test running")
        self.current_test_label.setStyleSheet("font-style: italic; color: gray;")
        self.current_test_label.setWordWrap(True)
        layout.addWidget(self.current_test_label)
        
        # Status message
        self.status_message = QLabel("Select tests and click 'Run Selected Tests' to begin")
        self.status_message.setWordWrap(True)
        layout.addWidget(self.status_message)
        
    def setup_timer(self) -> None:
        """Set up timer for elapsed time updates."""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_elapsed_time)
        self.timer.setInterval(1000)  # Update every second
        
    def on_test_runner_state_changed(self, state: TestRunnerState) -> None:
        """Handle test runner state changes."""
        if state == TestRunnerState.RUNNING:
            self.run_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.progress_bar.setVisible(True)
            self.status_message.setText("Tests are running...")
            
            # Start timer
            import time
            self.start_time = time.time()
            self.timer.start()
            
        elif state == TestRunnerState.STOPPING:
            self.stop_button.setEnabled(False)
            self.status_message.setText("Stopping tests...")
            
        elif state in (TestRunnerState.IDLE, TestRunnerState.STOPPED):
            self.run_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.progress_bar.setVisible(False)
            self.timer.stop()
            
            if state == TestRunnerState.STOPPED:
                self.status_message.setText("Tests stopped by user")
            else:
                self.status_message.setText("Test execution completed")
                
        elif state == TestRunnerState.ERROR:
            self.run_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.progress_bar.setVisible(False)
            self.timer.stop()
            self.status_message.setText("Test execution error occurred")
            
    def on_progress_update(self, progress: TestRunnerProgress) -> None:
        """Handle progress updates."""
        self.current_progress = progress
        self.update_progress_display()
        
    def update_progress_display(self) -> None:
        """Update the progress display."""
        if not self.current_progress:
            return
            
        progress = self.current_progress
        
        # Update progress bar
        if progress.total_tests > 0:
            self.progress_bar.setRange(0, progress.total_tests)
            self.progress_bar.setValue(progress.completed_tests)
            percentage = progress.progress_percentage
            self.progress_bar.setFormat(f"{percentage:.1f}% ({progress.completed_tests}/{progress.total_tests})")
        else:
            self.progress_bar.setRange(0, 0)  # Indeterminate
            
        # Update statistics
        self.total_label.setText(f"Total: {progress.total_tests}")
        self.completed_label.setText(f"Completed: {progress.completed_tests}")
        self.passed_label.setText(f"Passed: {progress.passed_tests}")
        self.failed_label.setText(f"Failed: {progress.failed_tests}")
        self.skipped_label.setText(f"Skipped: {progress.skipped_tests}")
        self.error_label.setText(f"Errors: {progress.error_tests}")
        self.remaining_label.setText(f"Remaining: {progress.remaining_tests}")
        
        # Update current test
        if progress.current_test:
            # Truncate long test names
            test_name = progress.current_test
            if len(test_name) > 60:
                test_name = "..." + test_name[-57:]
            self.current_test_label.setText(f"Running: {test_name}")
        else:
            self.current_test_label.setText("No test running")
            
    def update_elapsed_time(self) -> None:
        """Update the elapsed time display."""
        if self.start_time:
            import time
            elapsed = time.time() - self.start_time
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)
            self.elapsed_label.setText(f"Elapsed: {minutes:02d}:{seconds:02d}")
            
    def reset_progress(self) -> None:
        """Reset progress display."""
        self.current_progress = None
        self.start_time = None
        
        # Reset all displays
        self.progress_bar.setVisible(False)
        self.total_label.setText("Total: 0")
        self.completed_label.setText("Completed: 0")
        self.passed_label.setText("Passed: 0")
        self.failed_label.setText("Failed: 0")
        self.skipped_label.setText("Skipped: 0")
        self.error_label.setText("Errors: 0")
        self.elapsed_label.setText("Elapsed: 00:00")
        self.remaining_label.setText("Remaining: 0")
        self.current_test_label.setText("No test running")
        self.status_message.setText("Select tests and click 'Run Selected Tests' to begin")
        
    def set_test_count(self, count: int) -> None:
        """Set the total number of available tests."""
        if count > 0:
            self.status_message.setText(f"{count} tests available. Select tests to run.")
        else:
            self.status_message.setText("No tests found in the current directory.")