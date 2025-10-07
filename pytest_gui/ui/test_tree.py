"""
Test tree widget for displaying and selecting tests.
"""

import logging
from typing import List, Optional, Dict, Set
from enum import Enum

from PySide6.QtWidgets import (
    QTreeWidget, QTreeWidgetItem, QHeaderView, QMenu, QMessageBox,
    QAbstractItemView
)
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QIcon, QFont, QBrush, QColor

from ..core.test_discovery import TestNode, TestNodeType, TestStatus


class TestTreeItemType(Enum):
    """Types of items in the test tree."""
    DIRECTORY = "directory"
    FILE = "file"
    CLASS = "class"
    FUNCTION = "function"


class TestTreeItem(QTreeWidgetItem):
    """Custom tree widget item for test nodes."""
    
    def __init__(self, test_node: TestNode, parent=None):
        super().__init__(parent)
        
        self.test_node = test_node
        self.setup_item()
        
    def setup_item(self) -> None:
        """Set up the item display."""
        # Set text for columns
        self.setText(0, self.test_node.name)
        self.setText(1, self.test_node.status.value.title())
        self.setText(2, ', '.join(sorted(self.test_node.markers)) if self.test_node.markers else '')
        
        # Set checkbox
        self.setFlags(self.flags() | Qt.ItemIsUserCheckable)
        self.setCheckState(0, Qt.Checked if self.test_node.selected else Qt.Unchecked)
        
        # Set icon based on node type
        self.set_icon()
        
        # Set tooltip
        self.set_tooltip()
        
        # Update appearance based on status
        self.update_appearance()
        
    def set_icon(self) -> None:
        """Set icon based on node type."""
        # For now, use text-based indicators
        # In a real implementation, you would use actual icons
        icon_map = {
            TestNodeType.DIRECTORY: "📁",
            TestNodeType.FILE: "📄",
            TestNodeType.CLASS: "🏛️",
            TestNodeType.FUNCTION: "⚙️"
        }
        
        icon_text = icon_map.get(self.test_node.type, "❓")
        self.setText(0, f"{icon_text} {self.test_node.name}")
        
    def set_tooltip(self) -> None:
        """Set tooltip with detailed information."""
        tooltip_parts = [
            f"Path: {self.test_node.path}",
            f"Type: {self.test_node.type.value.title()}",
            f"Status: {self.test_node.status.value.title()}"
        ]
        
        if self.test_node.markers:
            tooltip_parts.append(f"Markers: {', '.join(sorted(self.test_node.markers))}")
            
        if self.test_node.docstring:
            tooltip_parts.append(f"Description: {self.test_node.docstring}")
            
        self.setToolTip(0, '\n'.join(tooltip_parts))
        
    def update_appearance(self) -> None:
        """Update item appearance based on status."""
        # Color coding based on test status
        color_map = {
            TestStatus.PENDING: QColor(100, 100, 100),  # Gray
            TestStatus.RUNNING: QColor(255, 165, 0),    # Orange
            TestStatus.PASSED: QColor(0, 128, 0),       # Green
            TestStatus.FAILED: QColor(255, 0, 0),       # Red
            TestStatus.SKIPPED: QColor(255, 255, 0),    # Yellow
            TestStatus.ERROR: QColor(128, 0, 128)       # Purple
        }
        
        color = color_map.get(self.test_node.status, QColor(0, 0, 0))
        
        # Set text color for status column
        self.setForeground(1, QBrush(color))
        
        # Make failed/error tests bold
        if self.test_node.status in (TestStatus.FAILED, TestStatus.ERROR):
            font = self.font(0)
            font.setBold(True)
            self.setFont(0, font)
            
    def update_from_node(self) -> None:
        """Update item display from the test node."""
        self.setup_item()


class TestTreeWidget(QTreeWidget):
    """Custom tree widget for displaying tests."""
    
    # Signals
    selection_changed = Signal(list)  # List of selected test paths
    test_double_clicked = Signal(str)  # Test path that was double-clicked
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.logger = logging.getLogger("pytest_gui.ui.test_tree")
        self.root_node: Optional[TestNode] = None
        self.item_map: Dict[str, TestTreeItem] = {}  # Map test paths to items
        
        self.setup_widget()
        self.setup_connections()
        
    def setup_widget(self) -> None:
        """Set up the tree widget."""
        # Set headers
        self.setHeaderLabels(['Test', 'Status', 'Markers'])
        
        # Configure columns
        header = self.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        
        # Enable context menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        
        # Enable sorting
        self.setSortingEnabled(True)
        self.sortByColumn(0, Qt.AscendingOrder)
        
        # Set selection behavior
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        
    def setup_connections(self) -> None:
        """Set up signal connections."""
        self.itemChanged.connect(self.on_item_changed)
        self.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.customContextMenuRequested.connect(self.show_context_menu)
        
    def set_root_node(self, root_node: TestNode) -> None:
        """Set the root test node and populate the tree."""
        self.root_node = root_node
        self.populate_tree()
        
    def populate_tree(self) -> None:
        """Populate the tree from the root node."""
        if not self.root_node:
            return
            
        self.clear()
        self.item_map.clear()
        
        # Create items for all children of root
        for child_node in self.root_node.children:
            self.create_tree_item(child_node, None)
            
        # Expand first level by default
        self.expandToDepth(0)
        
        self.logger.info(f"Populated tree with {len(self.item_map)} items")
        
    def create_tree_item(self, test_node: TestNode, parent_item: Optional[QTreeWidgetItem]) -> TestTreeItem:
        """Create a tree item for a test node."""
        if parent_item:
            item = TestTreeItem(test_node, parent_item)
        else:
            item = TestTreeItem(test_node)
            self.addTopLevelItem(item)
            
        # Store in map
        self.item_map[test_node.path] = item
        
        # Create child items
        for child_node in test_node.children:
            self.create_tree_item(child_node, item)
            
        return item
        
    def on_item_changed(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle item check state changes."""
        if column != 0 or not isinstance(item, TestTreeItem):
            return
            
        # Update the test node
        is_checked = item.checkState(0) == Qt.Checked
        item.test_node.selected = is_checked
        
        # Update child items
        self.update_children_selection(item, is_checked)
        
        # Update parent items
        self.update_parent_selection(item)
        
        # Emit selection changed signal
        self.emit_selection_changed()
        
    def update_children_selection(self, item: TestTreeItem, selected: bool) -> None:
        """Update selection state of all child items."""
        check_state = Qt.Checked if selected else Qt.Unchecked
        
        for i in range(item.childCount()):
            child_item = item.child(i)
            if isinstance(child_item, TestTreeItem):
                # Block signals to prevent recursion
                self.blockSignals(True)
                child_item.setCheckState(0, check_state)
                child_item.test_node.selected = selected
                self.blockSignals(False)
                
                # Recursively update grandchildren
                self.update_children_selection(child_item, selected)
                
    def update_parent_selection(self, item: TestTreeItem) -> None:
        """Update parent item selection based on children."""
        parent_item = item.parent()
        if not isinstance(parent_item, TestTreeItem):
            return
            
        # Count checked children
        checked_count = 0
        total_count = parent_item.childCount()
        
        for i in range(total_count):
            child_item = parent_item.child(i)
            if isinstance(child_item, TestTreeItem):
                if child_item.checkState(0) == Qt.Checked:
                    checked_count += 1
                elif child_item.checkState(0) == Qt.PartiallyChecked:
                    # If any child is partially checked, parent should be too
                    checked_count = -1
                    break
                    
        # Update parent check state
        self.blockSignals(True)
        if checked_count == 0:
            parent_item.setCheckState(0, Qt.Unchecked)
            parent_item.test_node.selected = False
        elif checked_count == total_count:
            parent_item.setCheckState(0, Qt.Checked)
            parent_item.test_node.selected = True
        else:
            parent_item.setCheckState(0, Qt.PartiallyChecked)
            parent_item.test_node.selected = False
        self.blockSignals(False)
        
        # Recursively update grandparent
        self.update_parent_selection(parent_item)
        
    def on_item_double_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle item double-click."""
        if isinstance(item, TestTreeItem):
            self.test_double_clicked.emit(item.test_node.path)
            
    def show_context_menu(self, position: QPoint) -> None:
        """Show context menu for tree items."""
        item = self.itemAt(position)
        if not isinstance(item, TestTreeItem):
            return
            
        menu = QMenu(self)
        
        # Run test action
        if item.test_node.is_test_node():
            run_action = menu.addAction("Run This Test")
            run_action.triggered.connect(lambda: self.run_single_test(item.test_node.path))
            
        # Select/deselect actions
        if item.test_node.selected:
            deselect_action = menu.addAction("Deselect")
            deselect_action.triggered.connect(lambda: self.set_item_selection(item, False))
        else:
            select_action = menu.addAction("Select")
            select_action.triggered.connect(lambda: self.set_item_selection(item, True))
            
        menu.addSeparator()
        
        # Expand/collapse actions
        if item.childCount() > 0:
            if item.isExpanded():
                collapse_action = menu.addAction("Collapse")
                collapse_action.triggered.connect(lambda: item.setExpanded(False))
            else:
                expand_action = menu.addAction("Expand")
                expand_action.triggered.connect(lambda: item.setExpanded(True))
                
        # Show menu
        menu.exec(self.mapToGlobal(position))
        
    def set_item_selection(self, item: TestTreeItem, selected: bool) -> None:
        """Set selection state of an item."""
        check_state = Qt.Checked if selected else Qt.Unchecked
        item.setCheckState(0, check_state)
        
    def run_single_test(self, test_path: str) -> None:
        """Run a single test."""
        # This would be connected to the test runner
        self.logger.info(f"Running single test: {test_path}")
        
    def get_selected_tests(self) -> List[str]:
        """Get list of selected test paths."""
        selected_tests = []
        
        if self.root_node:
            self._collect_selected_tests(self.root_node, selected_tests)
            
        return selected_tests
        
    def _collect_selected_tests(self, node: TestNode, selected_tests: List[str]) -> None:
        """Recursively collect selected test paths."""
        if node.selected and node.is_test_node():
            selected_tests.append(node.get_full_path())
            
        for child in node.children:
            self._collect_selected_tests(child, selected_tests)
            
    def select_all(self) -> None:
        """Select all tests."""
        if self.root_node:
            self._set_node_selection(self.root_node, True)
            self.populate_tree()  # Refresh display
            self.emit_selection_changed()
            
    def deselect_all(self) -> None:
        """Deselect all tests."""
        if self.root_node:
            self._set_node_selection(self.root_node, False)
            self.populate_tree()  # Refresh display
            self.emit_selection_changed()
            
    def _set_node_selection(self, node: TestNode, selected: bool) -> None:
        """Recursively set selection state of a node and its children."""
        node.selected = selected
        for child in node.children:
            self._set_node_selection(child, selected)
            
    def update_test_status(self, test_path: str, status: TestStatus) -> None:
        """Update the status of a specific test."""
        self.logger.debug(f"Updating test status: {test_path} -> {status.value}")
        
        # Try exact match first
        item = self.item_map.get(test_path)
        if item:
            self.logger.debug(f"Found exact match for: {test_path}")
            item.test_node.status = status
            item.update_from_node()
            return
            
        # If no exact match, try to find by partial matching
        # This handles cases where paths might have slight differences
        for stored_path, stored_item in self.item_map.items():
            # Try matching the test function/method name part
            if '::' in test_path and '::' in stored_path:
                test_parts = test_path.split('::')
                stored_parts = stored_path.split('::')
                
                # Match if the last part (function name) and file name match
                if (len(test_parts) >= 2 and len(stored_parts) >= 2 and
                    test_parts[-1] == stored_parts[-1] and  # Same function name
                    test_parts[0].split('/')[-1] == stored_parts[0].split('/')[-1]):  # Same file name
                    
                    self.logger.debug(f"Found partial match: {test_path} -> {stored_path}")
                    stored_item.test_node.status = status
                    stored_item.update_from_node()
                    return
                    
        # If still no match, try a more flexible approach
        test_name = test_path.split('::')[-1] if '::' in test_path else test_path
        for stored_path, stored_item in self.item_map.items():
            if stored_path.endswith(f"::{test_name}"):
                self.logger.debug(f"Found name-based match: {test_path} -> {stored_path}")
                stored_item.test_node.status = status
                stored_item.update_from_node()
                return
                
        self.logger.warning(f"Could not find test item for path: {test_path}")
        self.logger.debug(f"Available paths: {list(self.item_map.keys())}")
        
    def reset_test_statuses(self) -> None:
        """Reset all test statuses to PENDING."""
        self.logger.debug("Resetting all test statuses to PENDING")
        for item in self.item_map.values():
            if item.test_node.is_test_node():
                item.test_node.status = TestStatus.PENDING
                item.update_from_node()
                
    def set_test_running(self, test_path: str) -> None:
        """Set a test status to RUNNING."""
        self.update_test_status(test_path, TestStatus.RUNNING)

    def filter_by_markers(self, markers: Set[str]) -> None:
        """Filter tests by markers."""
        self._set_all_items_selected(False)

        # Select items that match any of the markers
        for item in self.item_map.values():
            has_marker = bool(item.test_node.markers.intersection(markers))
            if has_marker:
                self.set_item_selection(item, True)

    def _set_all_items_visible(self, visible: bool) -> None:
        """Set visibility of all items."""
        for item in self.item_map.values():
            item.setHidden(not visible)

    def _set_all_items_selected(self, selected: bool) -> None:
        """Set selection of all items."""
        for item in self.item_map.values():
            self.set_item_selection(item, selected)

    def search_tests(self, search_text: str) -> None:
        """Search for tests by name."""
        if not search_text:
            self._set_all_items_visible(True)
            return
            
        search_text = search_text.lower()
        
        for item in self.item_map.values():
            matches = (
                search_text in item.test_node.name.lower() or
                search_text in item.test_node.path.lower() or
                (item.test_node.docstring and search_text in item.test_node.docstring.lower())
            )
            item.setHidden(not matches)
            
    def emit_selection_changed(self) -> None:
        """Emit selection changed signal."""
        selected_tests = self.get_selected_tests()
        self.selection_changed.emit(selected_tests)
        self.logger.debug(f"Selection changed: {len(selected_tests)} tests selected")