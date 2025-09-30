"""
Marker filtering widget for pytest GUI.
"""

import logging
from typing import Set, List, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QLabel, 
    QScrollArea, QFrame, QPushButton, QLineEdit
)
from PySide6.QtCore import Qt, Signal


class MarkerFilterWidget(QWidget):
    """Widget for filtering tests by pytest markers."""
    
    # Signals
    markers_changed = Signal(set)  # Set of selected markers
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.logger = logging.getLogger("pytest_gui.ui.marker_filter")
        self.available_markers: Set[str] = set()
        self.selected_markers: Set[str] = set()
        self.marker_checkboxes: List[QCheckBox] = []
        
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """Set up the marker filter UI."""
        layout = QVBoxLayout(self)
        
        # Header
        header_label = QLabel("Filter by Markers")
        header_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(header_label)
        
        # Search box
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Filter markers...")
        self.search_box.textChanged.connect(self.filter_markers)
        
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_box)
        layout.addLayout(search_layout)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(self.select_all_markers)
        button_layout.addWidget(select_all_btn)
        
        clear_all_btn = QPushButton("Clear All")
        clear_all_btn.clicked.connect(self.clear_all_markers)
        button_layout.addWidget(clear_all_btn)
        
        layout.addLayout(button_layout)
        
        # Scrollable marker list
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(300)
        
        self.marker_container = QWidget()
        self.marker_layout = QVBoxLayout(self.marker_container)
        self.marker_layout.setAlignment(Qt.AlignTop)
        
        scroll_area.setWidget(self.marker_container)
        layout.addWidget(scroll_area)
        
        # Info label
        self.info_label = QLabel("No markers found")
        self.info_label.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(self.info_label)
        
    def set_available_markers(self, markers: Set[str]) -> None:
        """Set the available markers and update the UI."""
        self.available_markers = markers
        self.update_marker_list()
        
    def update_marker_list(self) -> None:
        """Update the marker checkbox list."""
        # Clear existing checkboxes
        for checkbox in self.marker_checkboxes:
            checkbox.deleteLater()
        self.marker_checkboxes.clear()
        
        # Sort markers for consistent display
        sorted_markers = sorted(self.available_markers)
        
        if not sorted_markers:
            self.info_label.setText("No markers found")
            self.info_label.setVisible(True)
            return
            
        self.info_label.setVisible(False)
        
        # Create checkboxes for each marker
        for marker in sorted_markers:
            checkbox = QCheckBox(marker)
            checkbox.setChecked(marker in self.selected_markers)
            checkbox.stateChanged.connect(self.on_marker_changed)
            
            self.marker_layout.addWidget(checkbox)
            self.marker_checkboxes.append(checkbox)
            
        self.info_label.setText(f"{len(sorted_markers)} markers available")
        
    def on_marker_changed(self) -> None:
        """Handle marker selection changes."""
        self.selected_markers.clear()
        
        for checkbox in self.marker_checkboxes:
            if checkbox.isChecked():
                self.selected_markers.add(checkbox.text())
                
        self.markers_changed.emit(self.selected_markers)
        self.logger.debug(f"Selected markers: {self.selected_markers}")
        
    def filter_markers(self, search_text: str) -> None:
        """Filter markers based on search text."""
        search_text = search_text.lower()
        
        for checkbox in self.marker_checkboxes:
            marker_text = checkbox.text().lower()
            visible = search_text in marker_text
            checkbox.setVisible(visible)
            
    def select_all_markers(self) -> None:
        """Select all visible markers."""
        for checkbox in self.marker_checkboxes:
            if checkbox.isVisible():
                checkbox.setChecked(True)
                
    def clear_all_markers(self) -> None:
        """Clear all marker selections."""
        for checkbox in self.marker_checkboxes:
            checkbox.setChecked(False)
            
    def get_selected_markers(self) -> Set[str]:
        """Get the currently selected markers."""
        return self.selected_markers.copy()
        
    def set_selected_markers(self, markers: Set[str]) -> None:
        """Set the selected markers."""
        self.selected_markers = markers.copy()
        
        # Update checkboxes
        for checkbox in self.marker_checkboxes:
            checkbox.setChecked(checkbox.text() in self.selected_markers)