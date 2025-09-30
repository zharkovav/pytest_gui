"""
Test discovery and parsing functionality.
"""

import ast
import re
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict, Set
import logging

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class TestNodeType(Enum):
    """Types of nodes in the test tree."""
    DIRECTORY = "directory"
    FILE = "file"
    CLASS = "class"
    FUNCTION = "function"


class TestStatus(Enum):
    """Status of test execution."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class TestNode:
    """Represents a node in the test tree."""
    
    def __init__(
        self,
        path: str,
        name: str,
        node_type: TestNodeType,
        parent: Optional['TestNode'] = None
    ):
        self.path = path
        self.name = name
        self.type = node_type
        self.parent = parent
        self.children: List['TestNode'] = []
        self.markers: Set[str] = set()
        self.selected = False
        self.status = TestStatus.PENDING
        self.docstring: Optional[str] = None
        
    def add_child(self, child: 'TestNode') -> None:
        """Add a child node."""
        child.parent = self
        self.children.append(child)
        
    def remove_child(self, child: 'TestNode') -> None:
        """Remove a child node."""
        if child in self.children:
            self.children.remove(child)
            child.parent = None
            
    def get_full_path(self) -> str:
        """Get the full path including parent hierarchy."""
        if self.parent and self.parent.type != TestNodeType.DIRECTORY:
            return f"{self.parent.get_full_path()}::{self.name}"

        # For file paths, convert to relative path with forward slashes for pytest
        if self.type == TestNodeType.FILE:
            path = Path(self.path)
            # Try to make it relative to current working directory
            try:
                rel_path = path.relative_to(Path.cwd())
                return str(rel_path).replace('\\', '/')
            except ValueError:
                # If can't make relative, use as-is but fix slashes
                return str(path).replace('\\', '/')
        
        return self.path
        
    def is_test_node(self) -> bool:
        """Check if this node represents an actual test."""
        return self.type in (TestNodeType.FUNCTION, TestNodeType.CLASS)
        
    def get_all_test_children(self) -> List['TestNode']:
        """Get all test nodes in the subtree."""
        tests = []
        if self.is_test_node():
            tests.append(self)
        for child in self.children:
            tests.extend(child.get_all_test_children())
        return tests


class TestFileWatcher(FileSystemEventHandler):
    """Watches for changes in test files."""
    
    def __init__(self, discovery: 'TestDiscovery'):
        self.discovery = discovery
        self.logger = logging.getLogger("pytest_gui.discovery.watcher")
        
    def on_modified(self, event):
        """Handle file modification events."""
        if not event.is_directory and event.src_path.endswith('.py'):
            self.logger.info(f"Test file modified: {event.src_path}")
            self.discovery.refresh_file(event.src_path)
            
    def on_created(self, event):
        """Handle file creation events."""
        if not event.is_directory and event.src_path.endswith('.py'):
            self.logger.info(f"Test file created: {event.src_path}")
            self.discovery.refresh_file(event.src_path)
            
    def on_deleted(self, event):
        """Handle file deletion events."""
        if not event.is_directory and event.src_path.endswith('.py'):
            self.logger.info(f"Test file deleted: {event.src_path}")
            self.discovery.remove_file(event.src_path)


class TestDiscovery:
    """Discovers and parses test files."""
    
    def __init__(self, root_path: str):
        self.root_path = Path(root_path).resolve()
        self.logger = logging.getLogger("pytest_gui.discovery")
        self.observer: Optional[Observer] = None
        self.file_watcher = TestFileWatcher(self)
        self._cached_nodes: Dict[str, TestNode] = {}
        
    def start_watching(self) -> None:
        """Start watching for file system changes."""
        if self.observer is None:
            self.observer = Observer()
            self.observer.schedule(
                self.file_watcher,
                str(self.root_path),
                recursive=True
            )
            self.observer.start()
            self.logger.info(f"Started watching directory: {self.root_path}")
            
    def stop_watching(self) -> None:
        """Stop watching for file system changes."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
            self.logger.info("Stopped watching for file changes")
            
    def discover_tests(self) -> TestNode:
        """
        Discover all tests in the root directory.
        
        Returns:
            Root node of the test tree
        """
        self.logger.info(f"Starting test discovery in: {self.root_path}")
        
        root_node = TestNode(
            path=str(self.root_path),
            name=self.root_path.name,
            node_type=TestNodeType.DIRECTORY
        )
        
        self._discover_directory(self.root_path, root_node)
        
        total_tests = len(root_node.get_all_test_children())
        self.logger.info(f"Discovered {total_tests} tests")
        
        return root_node
        
    def _discover_directory(self, dir_path: Path, parent_node: TestNode) -> None:
        """Recursively discover tests in a directory."""
        try:
            for item in sorted(dir_path.iterdir()):
                if item.name.startswith('.'):
                    continue
                    
                if item.is_dir():
                    # Skip common non-test directories
                    if item.name in (
                        '__pycache__',
                        '.pytest_cache',
                        'node_modules',
                        'venv',
                        'pytest_gui.egg-info',
                        'pytest_gui',
                        'docs',
                    ):
                        continue
                        
                    dir_node = TestNode(
                        path=str(item),
                        name=item.name,
                        node_type=TestNodeType.DIRECTORY,
                        parent=parent_node
                    )
                    parent_node.add_child(dir_node)
                    self._discover_directory(item, dir_node)
                    
                elif item.suffix == '.py' and self._is_test_file(item):
                    file_node = self._parse_test_file(item, parent_node)
                    if file_node and file_node.children:
                        parent_node.add_child(file_node)
                        
        except PermissionError:
            self.logger.warning(f"Permission denied accessing: {dir_path}")
        except Exception as e:
            self.logger.error(f"Error discovering directory {dir_path}: {e}")
            
    def _is_test_file(self, file_path: Path) -> bool:
        """Check if a file is a test file based on naming conventions."""
        name = file_path.name
        return (
            name.startswith('test_') or
            name.endswith('_test.py') or
            name == 'test.py'
        )
        
    def _parse_test_file(self, file_path: Path, parent_node: TestNode) -> Optional[TestNode]:
        """Parse a test file and extract test functions and classes."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            tree = ast.parse(content, filename=str(file_path))
            
            file_node = TestNode(
                path=str(file_path),
                name=file_path.name,
                node_type=TestNodeType.FILE,
                parent=parent_node
            )
            
            # Extract file-level markers
            file_markers = self._extract_file_markers(content)
            file_node.markers.update(file_markers)
            
            # Parse AST for test functions and classes
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and self._is_test_function(node.name):
                    if node.col_offset == 0:
                        test_node = self._create_function_node(node, file_node, content)
                        file_node.add_child(test_node)
                    
                elif isinstance(node, ast.ClassDef) and self._is_test_class(node.name):
                    class_node = self._create_class_node(node, file_node, content)
                    if class_node.children:  # Only add if it has test methods
                        file_node.add_child(class_node)
                        
            return file_node if file_node.children else None
            
        except Exception as e:
            self.logger.error(f"Error parsing test file {file_path}: {e}")
            return None
            
    def _is_test_function(self, name: str) -> bool:
        """Check if a function name indicates a test function."""
        return name.startswith('test_') or name.endswith('_test')
        
    def _is_test_class(self, name: str) -> bool:
        """Check if a class name indicates a test class."""
        return name.startswith('Test') or name.endswith('Test')
        
    def _create_function_node(
        self,
        func_node: ast.FunctionDef,
        parent: TestNode,
        file_content: str
    ) -> TestNode:
        """Create a test node for a function."""
        # Create relative path for the function
        file_path = Path(parent.path)
        try:
            rel_file_path = file_path.relative_to(Path.cwd())
            rel_file_str = str(rel_file_path).replace('\\', '/')
        except ValueError:
            rel_file_str = str(file_path).replace('\\', '/')
            
        test_node = TestNode(
            path=f"{rel_file_str}::{func_node.name}",
            name=func_node.name,
            node_type=TestNodeType.FUNCTION,
            parent=parent
        )
        
        # Extract docstring
        if (func_node.body and 
            isinstance(func_node.body[0], ast.Expr) and
            isinstance(func_node.body[0].value, ast.Constant)):
            test_node.docstring = func_node.body[0].value.value
            
        # Extract markers from decorators
        markers = self._extract_function_markers(func_node, file_content)
        test_node.markers.update(markers)
        
        return test_node
        
    def _create_class_node(
        self,
        class_node: ast.ClassDef,
        parent: TestNode,
        file_content: str
    ) -> TestNode:
        """Create a test node for a class."""
        # Create relative path for the class
        file_path = Path(parent.path)
        try:
            rel_file_path = file_path.relative_to(Path.cwd())
            rel_file_str = str(rel_file_path).replace('\\', '/')
        except ValueError:
            rel_file_str = str(file_path).replace('\\', '/')
            
        class_test_node = TestNode(
            path=f"{rel_file_str}::{class_node.name}",
            name=class_node.name,
            node_type=TestNodeType.CLASS,
            parent=parent
        )
        
        # Extract class-level markers
        markers = self._extract_class_markers(class_node, file_content)
        class_test_node.markers.update(markers)
        
        # Find test methods in the class
        for node in class_node.body:
            if isinstance(node, ast.FunctionDef) and self._is_test_function(node.name):
                method_node = TestNode(
                    path=f"{class_test_node.path}::{node.name}",
                    name=node.name,
                    node_type=TestNodeType.FUNCTION,
                    parent=class_test_node
                )
                
                # Extract method docstring
                if (node.body and 
                    isinstance(node.body[0], ast.Expr) and
                    isinstance(node.body[0].value, ast.Constant)):
                    method_node.docstring = node.body[0].value.value
                    
                # Extract method markers
                method_markers = self._extract_function_markers(node, file_content)
                method_node.markers.update(method_markers)
                method_node.markers.update(markers)  # Inherit class markers
                
                class_test_node.add_child(method_node)
                
        return class_test_node
        
    def _extract_file_markers(self, content: str) -> Set[str]:
        """Extract pytest markers from file-level comments or module docstring."""
        markers = set()
        
        # Look for pytestmark variable
        pytestmark_pattern = r'pytestmark\s*=\s*pytest\.mark\.(\w+)'
        matches = re.findall(pytestmark_pattern, content)
        markers.update(matches)
        
        return markers
        
    def _extract_function_markers(self, func_node: ast.FunctionDef, content: str) -> Set[str]:
        """Extract pytest markers from function decorators."""
        markers = set()
        
        for decorator in func_node.decorator_list:
            marker = self._parse_marker_decorator(decorator)
            if marker:
                markers.add(marker)
                
        return markers
        
    def _extract_class_markers(self, class_node: ast.ClassDef, content: str) -> Set[str]:
        """Extract pytest markers from class decorators."""
        markers = set()
        
        for decorator in class_node.decorator_list:
            marker = self._parse_marker_decorator(decorator)
            if marker:
                markers.add(marker)
                
        return markers
        
    def _parse_marker_decorator(self, decorator: ast.expr) -> Optional[str]:
        """Parse a decorator to extract pytest marker name."""
        try:
            if isinstance(decorator, ast.Attribute):
                # Handle @pytest.mark.marker_name
                if (isinstance(decorator.value, ast.Attribute) and
                    isinstance(decorator.value.value, ast.Name) and
                    decorator.value.value.id == 'pytest' and
                    decorator.value.attr == 'mark'):
                    return decorator.attr
                    
            elif isinstance(decorator, ast.Call):
                # Handle @pytest.mark.marker_name(args)
                if isinstance(decorator.func, ast.Attribute):
                    return self._parse_marker_decorator(decorator.func)
                    
        except Exception:
            pass
            
        return None
        
    def refresh_file(self, file_path: str) -> None:
        """Refresh a specific file in the test tree."""
        # This would trigger a re-parse of the specific file
        # and update the tree accordingly
        self.logger.info(f"Refreshing file: {file_path}")
        
    def remove_file(self, file_path: str) -> None:
        """Remove a file from the test tree."""
        # This would remove the file node from the tree
        self.logger.info(f"Removing file: {file_path}")