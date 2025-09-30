"""
Test execution engine for running pytest tests.
"""

import subprocess
import threading
import queue
import logging
import signal
import os
import re
from typing import List, Dict, Any, Optional, Callable
from enum import Enum
from pathlib import Path

import psutil

from .test_discovery import TestStatus


class TestRunnerState(Enum):
    """States of the test runner."""
    IDLE = "idle"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class TestResult:
    """Represents the result of a single test."""
    
    def __init__(self, test_path: str, status: TestStatus, duration: float = 0.0):
        self.test_path = test_path
        self.status = status
        self.duration = duration
        self.output: List[str] = []
        self.error_message: Optional[str] = None
        self.traceback: Optional[str] = None


class TestRunnerProgress:
    """Progress information for test execution."""
    
    def __init__(self):
        self.total_tests = 0
        self.completed_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.skipped_tests = 0
        self.error_tests = 0
        self.current_test: Optional[str] = None
        self.elapsed_time = 0.0
        
    @property
    def progress_percentage(self) -> float:
        """Get progress as percentage."""
        if self.total_tests == 0:
            return 0.0
        return (self.completed_tests / self.total_tests) * 100
        
    @property
    def remaining_tests(self) -> int:
        """Get number of remaining tests."""
        return self.total_tests - self.completed_tests


class TestRunner:
    """Manages pytest execution."""
    
    def __init__(self):
        self.logger = logging.getLogger("pytest_gui.execution")
        self.state = TestRunnerState.IDLE
        self.process: Optional[subprocess.Popen] = None
        self.process_thread: Optional[threading.Thread] = None
        self.output_queue = queue.Queue()
        self.progress = TestRunnerProgress()
        
        # Callbacks
        self.on_progress_update: Optional[Callable[[TestRunnerProgress], None]] = None
        self.on_test_result: Optional[Callable[[TestResult], None]] = None
        self.on_test_started: Optional[Callable[[str], None]] = None  # Called when a test starts
        self.on_output_line: Optional[Callable[[str], None]] = None
        self.on_state_changed: Optional[Callable[[TestRunnerState], None]] = None
        
        # Output parsing patterns
        self.test_patterns = {
            'test_start': re.compile(r'^([^:]+::[^:]+(?:::[^:]+)*)\s+\.\.\.'),
            'test_passed': re.compile(r'^([^:]+::[^:]+(?:::[^:]+)*)\s+PASSED\s*(?:\[.*?\])?'),
            'test_failed': re.compile(r'^([^:]+::[^:]+(?:::[^:]+)*)\s+FAILED\s*(?:\[.*?\])?'),
            'test_skipped': re.compile(r'^([^:]+::[^:]+(?:::[^:]+)*)\s+SKIPPED\s*(?:\([^)]*\))?\s*(?:\[.*?\])?'),
            'test_error': re.compile(r'^([^:]+::[^:]+(?:::[^:]+)*)\s+ERROR\s*(?:\[.*?\])?'),
            'progress': re.compile(r'\[(\d+)%\]'),
            'collecting': re.compile(r'collected (\d+) item'),
        }
        
    def start_tests(
        self,
        test_paths: List[str],
        pytest_args: Optional[List[str]] = None,
        env_vars: Optional[Dict[str, str]] = None,
        working_dir: Optional[str] = None
    ) -> bool:
        """
        Start test execution.
        
        Args:
            test_paths: List of test paths to run
            pytest_args: Additional pytest arguments
            env_vars: Environment variables to set
            working_dir: Working directory for test execution
            
        Returns:
            True if tests started successfully, False otherwise
        """
        if self.state != TestRunnerState.IDLE:
            self.logger.warning("Cannot start tests: runner is not idle")
            return False
            
        try:
            # Build command
            cmd = self._build_command(test_paths, pytest_args)
            
            # Prepare environment
            env = os.environ.copy()
            if env_vars:
                env.update(env_vars)
                
            # Set working directory
            cwd = working_dir or os.getcwd()
            
            self.logger.info(f"Starting tests with command: {' '.join(cmd)}")
            self.logger.info(f"Working directory: {cwd}")
            
            # Start subprocess
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                env=env,
                cwd=cwd,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
            )
            
            # Reset progress
            self.progress = TestRunnerProgress()
            self.progress.total_tests = len(test_paths)
            
            # Start monitoring thread
            self.process_thread = threading.Thread(
                target=self._monitor_process,
                daemon=True
            )
            self.process_thread.start()
            
            # Update state
            self._set_state(TestRunnerState.RUNNING)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start tests: {e}")
            self._set_state(TestRunnerState.ERROR)
            return False
            
    def stop_tests(self) -> None:
        """Stop running tests."""
        if self.state != TestRunnerState.RUNNING:
            self.logger.warning("Cannot stop tests: no tests running")
            return
            
        self.logger.info("Stopping tests...")
        self._set_state(TestRunnerState.STOPPING)
        
        if self.process:
            try:
                # Try graceful termination first
                if os.name == 'nt':
                    # Windows
                    self.process.send_signal(signal.CTRL_BREAK_EVENT)
                else:
                    # Unix-like
                    self.process.terminate()
                    
                # Wait for process to terminate
                try:
                    self.process.wait(timeout=5.0)
                except subprocess.TimeoutExpired:
                    # Force kill if graceful termination failed
                    self.logger.warning("Graceful termination failed, force killing process")
                    self._force_kill_process()
                    
            except Exception as e:
                self.logger.error(f"Error stopping tests: {e}")
                self._force_kill_process()
                
    def _force_kill_process(self) -> None:
        """Force kill the test process and all its children."""
        if not self.process:
            return
            
        try:
            # Kill process tree
            parent = psutil.Process(self.process.pid)
            children = parent.children(recursive=True)
            
            # Kill children first
            for child in children:
                try:
                    child.kill()
                except psutil.NoSuchProcess:
                    pass
                    
            # Kill parent
            try:
                parent.kill()
            except psutil.NoSuchProcess:
                pass
                
            # Wait for process to die
            self.process.wait()
            
        except Exception as e:
            self.logger.error(f"Error force killing process: {e}")
            
    def _build_command(self, test_paths: List[str], pytest_args: Optional[List[str]]) -> List[str]:
        """Build the pytest command."""
        # Use the current Python executable to ensure we use the virtual environment
        import sys
        cmd = [sys.executable, '-m', 'pytest']
        
        # Add test paths
        cmd.extend(test_paths)
        
        # Add default arguments for better output parsing
        cmd.extend([
            '--tb=short',  # Short traceback format
            '-v',          # Verbose output
            # '--no-header', # No header
            # '--no-summary' # No summary
        ])
        
        # Add custom arguments
        if pytest_args:
            cmd.extend(pytest_args)
            
        return cmd
        
    def _monitor_process(self) -> None:
        """Monitor the test process and parse output."""
        if not self.process:
            return
            
        try:
            self.logger.info("Starting process monitoring...")
            
            # Read output line by line
            line_count = 0
            for line in iter(self.process.stdout.readline, ''):
                if not line:
                    break
                    
                line = line.rstrip()
                if line:
                    line_count += 1
                    self.logger.debug(f"Process output line {line_count}: {line}")
                    self._process_output_line(line)
                    
            # Wait for process to complete
            return_code = self.process.wait()
            self.logger.info(f"Process completed with return code: {return_code}, processed {line_count} lines")
            
            # Update final state
            if self.state == TestRunnerState.STOPPING:
                self._set_state(TestRunnerState.STOPPED)
            else:
                self._set_state(TestRunnerState.IDLE)
                
        except Exception as e:
            self.logger.error(f"Error monitoring process: {e}", exc_info=True)
            self._set_state(TestRunnerState.ERROR)
        finally:
            self.process = None
            
    def _process_output_line(self, line: str) -> None:
        """Process a single line of output."""
        # Emit raw output
        if self.on_output_line:
            self.on_output_line(line)
            
        # Log the line for debugging
        self.logger.debug(f"Processing line: '{line}'")
            
        # Parse for test results
        self._parse_test_result(line)
        
        # Parse for progress information
        self._parse_progress(line)
        
    def _parse_test_result(self, line: str) -> None:
        """Parse test result from output line."""
        test_result = None
        
        # Check for test start pattern first
        start_match = self.test_patterns['test_start'].search(line)
        if start_match:
            test_path = start_match.group(1)
            self.logger.debug(f"Test started: {test_path}")
            if self.on_test_started:
                self.on_test_started(test_path)
            return
        
        # Check for test status patterns
        for status_name, pattern in self.test_patterns.items():
            if status_name.startswith('test_') and status_name != 'test_start':
                match = pattern.search(line)
                if match:
                    test_path = match.group(1)
                    self.logger.debug(f"Test result: {test_path} -> {status_name}")
                    
                    if status_name == 'test_passed':
                        status = TestStatus.PASSED
                        self.progress.passed_tests += 1
                    elif status_name == 'test_failed':
                        status = TestStatus.FAILED
                        self.progress.failed_tests += 1
                    elif status_name == 'test_skipped':
                        status = TestStatus.SKIPPED
                        self.progress.skipped_tests += 1
                    elif status_name == 'test_error':
                        status = TestStatus.ERROR
                        self.progress.error_tests += 1
                    else:
                        continue
                        
                    # Create test result
                    test_result = TestResult(test_path, status)
                    
                    # Update progress
                    self.progress.completed_tests += 1
                    
                    break
                    
        # Emit test result
        if test_result and self.on_test_result:
            self.on_test_result(test_result)
            
        # Emit progress update
        if test_result and self.on_progress_update:
            self.on_progress_update(self.progress)
            
    def _parse_progress(self, line: str) -> None:
        """Parse progress information from output line."""
        # Check for collection info
        match = self.test_patterns['collecting'].search(line)
        if match:
            total_tests = int(match.group(1))
            self.progress.total_tests = total_tests
            self.logger.info(f"Collected {total_tests} tests")
            
            if self.on_progress_update:
                self.on_progress_update(self.progress)
                
        # Check for current test
        if '::' in line and ' PASSED' not in line and ' FAILED' not in line:
            # This might be a test that's currently running
            parts = line.split('::')
            if len(parts) >= 2:
                self.progress.current_test = line.strip()
                
    def _set_state(self, new_state: TestRunnerState) -> None:
        """Set the runner state and emit signal."""
        if self.state != new_state:
            old_state = self.state
            self.state = new_state
            self.logger.info(f"State changed: {old_state.value} -> {new_state.value}")
            
            if self.on_state_changed:
                self.on_state_changed(new_state)
                
    def is_running(self) -> bool:
        """Check if tests are currently running."""
        return self.state == TestRunnerState.RUNNING
        
    def get_progress(self) -> TestRunnerProgress:
        """Get current progress information."""
        return self.progress
        
    def get_state(self) -> TestRunnerState:
        """Get current runner state."""
        return self.state