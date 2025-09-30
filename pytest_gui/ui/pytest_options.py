"""
Pytest options configuration widget for pytest GUI.
"""

import logging
from typing import List, Dict, Any
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QSpinBox,
    QComboBox, QLineEdit, QLabel, QGroupBox, QFormLayout,
    QScrollArea, QPushButton, QTextEdit
)
from PySide6.QtCore import Qt, Signal


class PytestOptionsWidget(QWidget):
    """Widget for configuring pytest command-line options."""
    
    # Signals
    options_changed = Signal(list)  # List of pytest arguments
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.logger = logging.getLogger("pytest_gui.ui.pytest_options")
        self.options: Dict[str, Any] = {}
        
        self.setup_ui()
        self.load_default_options()
        
    def setup_ui(self) -> None:
        """Set up the pytest options UI."""
        layout = QVBoxLayout(self)
        
        # Header
        header_label = QLabel("Pytest Options")
        header_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(header_label)
        
        # Scrollable area for options
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        options_widget = QWidget()
        options_layout = QVBoxLayout(options_widget)
        
        # Output options
        output_group = self.create_output_options()
        options_layout.addWidget(output_group)
        
        # Execution options
        execution_group = self.create_execution_options()
        options_layout.addWidget(execution_group)
        
        # Collection options
        collection_group = self.create_collection_options()
        options_layout.addWidget(collection_group)
        
        # Reporting options
        reporting_group = self.create_reporting_options()
        options_layout.addWidget(reporting_group)
        
        # Custom arguments
        custom_group = self.create_custom_arguments()
        options_layout.addWidget(custom_group)
        
        scroll_area.setWidget(options_widget)
        layout.addWidget(scroll_area)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.clicked.connect(self.reset_to_defaults)
        button_layout.addWidget(reset_btn)
        
        button_layout.addStretch()
        
        apply_btn = QPushButton("Apply Options")
        apply_btn.clicked.connect(self.apply_options)
        button_layout.addWidget(apply_btn)
        
        layout.addLayout(button_layout)
        
    def create_output_options(self) -> QGroupBox:
        """Create output-related options."""
        group = QGroupBox("Output Options")
        layout = QFormLayout(group)
        
        # Verbosity
        self.verbosity_combo = QComboBox()
        self.verbosity_combo.addItems([
            "Quiet (-q)", "Normal", "Verbose (-v)", "Very Verbose (-vv)"
        ])
        self.verbosity_combo.setCurrentIndex(1)  # Normal
        self.verbosity_combo.currentIndexChanged.connect(self.on_option_changed)
        layout.addRow("Verbosity:", self.verbosity_combo)
        
        # Traceback style
        self.traceback_combo = QComboBox()
        self.traceback_combo.addItems([
            "auto", "long", "short", "line", "native", "no"
        ])
        self.traceback_combo.setCurrentText("short")
        self.traceback_combo.currentTextChanged.connect(self.on_option_changed)
        layout.addRow("Traceback Style:", self.traceback_combo)
        
        # Show locals
        self.show_locals_cb = QCheckBox("Show local variables in tracebacks")
        self.show_locals_cb.stateChanged.connect(self.on_option_changed)
        layout.addRow(self.show_locals_cb)
        
        # Capture output
        self.capture_combo = QComboBox()
        self.capture_combo.addItems(["sys", "fd", "no"])
        self.capture_combo.setCurrentText("sys")
        self.capture_combo.currentTextChanged.connect(self.on_option_changed)
        layout.addRow("Capture Output:", self.capture_combo)
        
        return group
        
    def create_execution_options(self) -> QGroupBox:
        """Create execution-related options."""
        group = QGroupBox("Execution Options")
        layout = QFormLayout(group)
        
        # Stop on first failure
        self.stop_on_first_cb = QCheckBox("Stop on first failure (-x)")
        self.stop_on_first_cb.stateChanged.connect(self.on_option_changed)
        layout.addRow(self.stop_on_first_cb)
        
        # Max failures
        self.max_failures_spin = QSpinBox()
        self.max_failures_spin.setRange(1, 1000)
        self.max_failures_spin.setValue(1)
        self.max_failures_spin.setEnabled(False)
        self.max_failures_spin.valueChanged.connect(self.on_option_changed)
        
        self.max_failures_cb = QCheckBox("Stop after N failures (--maxfail)")
        self.max_failures_cb.stateChanged.connect(self.on_max_failures_toggled)
        
        max_fail_layout = QHBoxLayout()
        max_fail_layout.addWidget(self.max_failures_cb)
        max_fail_layout.addWidget(self.max_failures_spin)
        max_fail_layout.addStretch()
        
        layout.addRow(max_fail_layout)
        
        # Parallel execution
        self.parallel_cb = QCheckBox("Run tests in parallel (-n)")
        self.parallel_cb.stateChanged.connect(self.on_parallel_toggled)
        
        self.parallel_workers = QComboBox()
        self.parallel_workers.addItems(["auto", "2", "4", "8", "16"])
        self.parallel_workers.setEnabled(False)
        self.parallel_workers.currentTextChanged.connect(self.on_option_changed)
        
        parallel_layout = QHBoxLayout()
        parallel_layout.addWidget(self.parallel_cb)
        parallel_layout.addWidget(self.parallel_workers)
        parallel_layout.addStretch()
        
        layout.addRow(parallel_layout)
        
        return group
        
    def create_collection_options(self) -> QGroupBox:
        """Create test collection options."""
        group = QGroupBox("Collection Options")
        layout = QFormLayout(group)
        
        # Collect only
        self.collect_only_cb = QCheckBox("Collect tests only (--collect-only)")
        self.collect_only_cb.stateChanged.connect(self.on_option_changed)
        layout.addRow(self.collect_only_cb)
        
        # Ignore paths
        self.ignore_paths_edit = QLineEdit()
        self.ignore_paths_edit.setPlaceholderText("e.g., tests/integration")
        self.ignore_paths_edit.textChanged.connect(self.on_option_changed)
        layout.addRow("Ignore Paths:", self.ignore_paths_edit)
        
        return group
        
    def create_reporting_options(self) -> QGroupBox:
        """Create reporting options."""
        group = QGroupBox("Reporting Options")
        layout = QFormLayout(group)
        
        # Show durations
        self.durations_cb = QCheckBox("Show test durations (--durations)")
        self.durations_cb.stateChanged.connect(self.on_durations_toggled)
        
        self.durations_spin = QSpinBox()
        self.durations_spin.setRange(0, 100)
        self.durations_spin.setValue(10)
        self.durations_spin.setEnabled(False)
        self.durations_spin.valueChanged.connect(self.on_option_changed)
        
        durations_layout = QHBoxLayout()
        durations_layout.addWidget(self.durations_cb)
        durations_layout.addWidget(self.durations_spin)
        durations_layout.addStretch()
        
        layout.addRow(durations_layout)
        
        # Show summary
        self.summary_combo = QComboBox()
        self.summary_combo.addItems(["auto", "short", "long", "no"])
        self.summary_combo.setCurrentText("short")
        self.summary_combo.currentTextChanged.connect(self.on_option_changed)
        layout.addRow("Summary Style:", self.summary_combo)
        
        return group
        
    def create_custom_arguments(self) -> QGroupBox:
        """Create custom arguments section."""
        group = QGroupBox("Custom Arguments")
        layout = QVBoxLayout(group)
        
        label = QLabel("Additional pytest arguments (one per line):")
        layout.addWidget(label)
        
        self.custom_args_edit = QTextEdit()
        self.custom_args_edit.setMaximumHeight(80)
        self.custom_args_edit.setPlaceholderText("--strict-markers\n--strict-config")
        self.custom_args_edit.textChanged.connect(self.on_option_changed)
        
        layout.addWidget(self.custom_args_edit)
        
        return group
        
    def on_option_changed(self) -> None:
        """Handle option changes."""
        self.build_options()
        
    def on_max_failures_toggled(self, checked: bool) -> None:
        """Handle max failures checkbox toggle."""
        self.max_failures_spin.setEnabled(checked)
        self.on_option_changed()
        
    def on_parallel_toggled(self, checked: bool) -> None:
        """Handle parallel execution toggle."""
        self.parallel_workers.setEnabled(checked)
        self.on_option_changed()
        
    def on_durations_toggled(self, checked: bool) -> None:
        """Handle durations checkbox toggle."""
        self.durations_spin.setEnabled(checked)
        self.on_option_changed()
        
    def build_options(self) -> None:
        """Build pytest arguments from current options."""
        args = []
        
        # Verbosity
        verbosity_index = self.verbosity_combo.currentIndex()
        if verbosity_index == 0:  # Quiet
            args.append("-q")
        elif verbosity_index == 2:  # Verbose
            args.append("-v")
        elif verbosity_index == 3:  # Very verbose
            args.append("-vv")
            
        # Traceback style
        tb_style = self.traceback_combo.currentText()
        if tb_style != "auto":
            args.append(f"--tb={tb_style}")
            
        # Show locals
        if self.show_locals_cb.isChecked():
            args.append("-l")
            
        # Capture output
        capture = self.capture_combo.currentText()
        if capture != "sys":
            args.append(f"--capture={capture}")
            
        # Stop on first failure
        if self.stop_on_first_cb.isChecked():
            args.append("-x")
            
        # Max failures
        if self.max_failures_cb.isChecked():
            args.append(f"--maxfail={self.max_failures_spin.value()}")
            
        # Parallel execution
        if self.parallel_cb.isChecked():
            workers = self.parallel_workers.currentText()
            args.append(f"-n={workers}")
            
        # Collect only
        if self.collect_only_cb.isChecked():
            args.append("--collect-only")
            
        # Ignore paths
        ignore_paths = self.ignore_paths_edit.text().strip()
        if ignore_paths:
            for path in ignore_paths.split(','):
                path = path.strip()
                if path:
                    args.append(f"--ignore={path}")
                    
        # Show durations
        if self.durations_cb.isChecked():
            args.append(f"--durations={self.durations_spin.value()}")
            
        # Summary style
        summary = self.summary_combo.currentText()
        if summary != "auto":
            args.append(f"--tb={summary}")
            
        # Custom arguments
        custom_text = self.custom_args_edit.toPlainText().strip()
        if custom_text:
            for line in custom_text.split('\n'):
                arg = line.strip()
                if arg and not arg.startswith('#'):
                    args.append(arg)
                    
        self.options_changed.emit(args)
        self.logger.debug(f"Built pytest arguments: {args}")
        
    def load_default_options(self) -> None:
        """Load default pytest options."""
        # Set some sensible defaults
        self.verbosity_combo.setCurrentIndex(2)  # Verbose
        self.traceback_combo.setCurrentText("short")
        self.summary_combo.setCurrentText("short")
        
        self.build_options()
        
    def reset_to_defaults(self) -> None:
        """Reset all options to defaults."""
        # Reset all controls
        self.verbosity_combo.setCurrentIndex(1)  # Normal
        self.traceback_combo.setCurrentText("auto")
        self.show_locals_cb.setChecked(False)
        self.capture_combo.setCurrentText("sys")
        self.stop_on_first_cb.setChecked(False)
        self.max_failures_cb.setChecked(False)
        self.max_failures_spin.setValue(1)
        self.parallel_cb.setChecked(False)
        self.parallel_workers.setCurrentText("auto")
        self.collect_only_cb.setChecked(False)
        self.ignore_paths_edit.clear()
        self.durations_cb.setChecked(False)
        self.durations_spin.setValue(10)
        self.summary_combo.setCurrentText("auto")
        self.custom_args_edit.clear()
        
        self.build_options()
        
    def apply_options(self) -> None:
        """Apply current options."""
        self.build_options()
        
    def get_pytest_args(self) -> List[str]:
        """Get the current pytest arguments."""
        self.build_options()
        # Return the last built options
        return getattr(self, '_last_args', [])
        
    def set_pytest_args(self, args: List[str]) -> None:
        """Set pytest arguments and update UI."""
        # This would parse the args and update the UI controls
        # For now, just store them
        self._last_args = args