"""
Environment variable configuration widget for pytest GUI.
"""

import logging
import os
from pathlib import Path
from typing import Dict, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QLabel, QMessageBox, QFileDialog,
    QTextEdit, QSplitter
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont


class EnvironmentConfigWidget(QWidget):
    """Widget for configuring environment variables."""
    
    # Signals
    env_vars_changed = Signal(dict)  # Dict of environment variables
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.logger = logging.getLogger("pytest_gui.ui.env_config")
        self.env_vars: Dict[str, str] = {}
        self.env_file_path: Optional[Path] = None
        
        self.setup_ui()
        self.load_env_file()
        
    def setup_ui(self) -> None:
        """Set up the environment configuration UI."""
        layout = QVBoxLayout(self)
        
        # Header
        header_label = QLabel("Environment Variables")
        header_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(header_label)
        
        # Splitter for table and editor
        splitter = QSplitter(Qt.Vertical)
        
        # Environment variables table
        table_widget = self.create_env_table()
        splitter.addWidget(table_widget)
        
        # .env file editor
        editor_widget = self.create_env_editor()
        splitter.addWidget(editor_widget)
        
        # Set splitter proportions
        splitter.setSizes([200, 150])
        layout.addWidget(splitter)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        add_btn = QPushButton("Add Variable")
        add_btn.clicked.connect(self.add_env_var)
        button_layout.addWidget(add_btn)
        
        remove_btn = QPushButton("Remove Selected")
        remove_btn.clicked.connect(self.remove_selected_vars)
        button_layout.addWidget(remove_btn)
        
        button_layout.addStretch()
        
        load_btn = QPushButton("Load .env File")
        load_btn.clicked.connect(self.load_env_file_dialog)
        button_layout.addWidget(load_btn)
        
        save_btn = QPushButton("Save .env File")
        save_btn.clicked.connect(self.save_env_file)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
        
    def create_env_table(self) -> QWidget:
        """Create the environment variables table."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        label = QLabel("Environment Variables:")
        layout.addWidget(label)
        
        self.env_table = QTableWidget()
        self.env_table.setColumnCount(2)
        self.env_table.setHorizontalHeaderLabels(["Variable", "Value"])
        
        # Configure table
        header = self.env_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        
        self.env_table.itemChanged.connect(self.on_table_item_changed)
        
        layout.addWidget(self.env_table)
        return widget
        
    def create_env_editor(self) -> QWidget:
        """Create the .env file editor."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        label = QLabel(".env File Content:")
        layout.addWidget(label)
        
        self.env_editor = QTextEdit()
        self.env_editor.setMaximumHeight(120)
        
        # Set monospace font
        font = QFont("Consolas", 9)
        if not font.exactMatch():
            font = QFont("Courier New", 9)
        self.env_editor.setFont(font)
        
        self.env_editor.textChanged.connect(self.on_editor_changed)
        
        layout.addWidget(self.env_editor)
        return widget
        
    def load_env_file(self) -> None:
        """Load environment variables from .env file."""
        env_path = Path(".env")
        if env_path.exists():
            self.env_file_path = env_path
        else:
            # Try .env.example
            env_example_path = Path(".env.example")
            if env_example_path.exists():
                self.env_file_path = env_example_path
            else:
                self.env_file_path = None
                
        if self.env_file_path:
            try:
                with open(self.env_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                self.env_editor.setPlainText(content)
                self.parse_env_content(content)
                
                self.logger.info(f"Loaded environment file: {self.env_file_path}")
                
            except Exception as e:
                self.logger.error(f"Failed to load env file: {e}")
                QMessageBox.warning(self, "Warning", f"Failed to load .env file:\n{e}")
        else:
            # Set default content
            default_content = """# Test execution settings
PYTEST_TIMEOUT=300
PYTEST_WORKERS=auto
PYTEST_VERBOSITY=1

# Application settings
LOG_LEVEL=INFO
THEME=default
AUTO_DISCOVER=true
"""
            self.env_editor.setPlainText(default_content)
            self.parse_env_content(default_content)
            
    def parse_env_content(self, content: str) -> None:
        """Parse .env file content into environment variables."""
        self.env_vars.clear()
        
        for line in content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                self.env_vars[key.strip()] = value.strip()
                
        self.update_env_table()
        self.env_vars_changed.emit(self.env_vars)
        
    def update_env_table(self) -> None:
        """Update the environment variables table."""
        self.env_table.setRowCount(len(self.env_vars))
        
        for row, (key, value) in enumerate(sorted(self.env_vars.items())):
            key_item = QTableWidgetItem(key)
            value_item = QTableWidgetItem(value)
            
            self.env_table.setItem(row, 0, key_item)
            self.env_table.setItem(row, 1, value_item)
            
    def on_table_item_changed(self, item: QTableWidgetItem) -> None:
        """Handle changes to table items."""
        row = item.row()
        col = item.column()
        
        if row < self.env_table.rowCount():
            key_item = self.env_table.item(row, 0)
            value_item = self.env_table.item(row, 1)
            
            if key_item and value_item:
                key = key_item.text().strip()
                value = value_item.text().strip()
                
                if key:
                    self.env_vars[key] = value
                    self.update_env_editor()
                    self.env_vars_changed.emit(self.env_vars)
                    
    def on_editor_changed(self) -> None:
        """Handle changes to the .env editor."""
        content = self.env_editor.toPlainText()
        self.parse_env_content(content)
        
    def add_env_var(self) -> None:
        """Add a new environment variable."""
        row = self.env_table.rowCount()
        self.env_table.setRowCount(row + 1)
        
        key_item = QTableWidgetItem("NEW_VAR")
        value_item = QTableWidgetItem("")
        
        self.env_table.setItem(row, 0, key_item)
        self.env_table.setItem(row, 1, value_item)
        
        # Select the new item for editing
        self.env_table.setCurrentItem(key_item)
        self.env_table.editItem(key_item)
        
    def remove_selected_vars(self) -> None:
        """Remove selected environment variables."""
        selected_rows = set()
        for item in self.env_table.selectedItems():
            selected_rows.add(item.row())
            
        if not selected_rows:
            QMessageBox.information(self, "No Selection", "Please select variables to remove.")
            return
            
        # Remove from env_vars dict
        for row in sorted(selected_rows, reverse=True):
            key_item = self.env_table.item(row, 0)
            if key_item:
                key = key_item.text()
                if key in self.env_vars:
                    del self.env_vars[key]
                    
        self.update_env_table()
        self.update_env_editor()
        self.env_vars_changed.emit(self.env_vars)
        
    def update_env_editor(self) -> None:
        """Update the .env editor content."""
        lines = []
        for key, value in sorted(self.env_vars.items()):
            lines.append(f"{key}={value}")
            
        content = '\n'.join(lines)
        
        # Block signals to prevent recursion
        self.env_editor.blockSignals(True)
        self.env_editor.setPlainText(content)
        self.env_editor.blockSignals(False)
        
    def load_env_file_dialog(self) -> None:
        """Open dialog to load a .env file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load .env File", str(Path.cwd()), "Environment Files (*.env);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                self.env_editor.setPlainText(content)
                self.env_file_path = Path(file_path)
                
                QMessageBox.information(self, "Success", f"Loaded environment file:\n{file_path}")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load file:\n{e}")
                
    def save_env_file(self) -> None:
        """Save current environment variables to .env file."""
        if not self.env_file_path:
            self.env_file_path = Path(".env")
            
        try:
            content = self.env_editor.toPlainText()
            
            with open(self.env_file_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            QMessageBox.information(self, "Success", f"Saved environment file:\n{self.env_file_path}")
            self.logger.info(f"Saved environment file: {self.env_file_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save file:\n{e}")
            
    def get_env_vars(self) -> Dict[str, str]:
        """Get the current environment variables."""
        return self.env_vars.copy()