"""
Configuration management for the Pytest GUI application.
"""

import json
import configparser
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging
import os

from dotenv import load_dotenv, set_key, unset_key


class ConfigManager:
    """Manages application and pytest configuration."""
    
    def __init__(self, config_dir: Optional[str] = None):
        self.logger = logging.getLogger("pytest_gui.config")
        
        # Set up configuration directory
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            self.config_dir = Path.home() / '.pytest_gui'
            
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Configuration file paths
        self.app_config_file = self.config_dir / 'app_config.json'
        self.pytest_config_file = self.config_dir / 'pytest_config.ini'
        
        # Default configurations
        self.app_config = self._get_default_app_config()
        self.pytest_config = configparser.ConfigParser()
        self.env_vars: Dict[str, str] = {}
        
        # Load existing configurations
        self.load_config()
        
    def _get_default_app_config(self) -> Dict[str, Any]:
        """Get default application configuration."""
        return {
            'window': {
                'width': 1200,
                'height': 800,
                'maximized': False,
                'position': {'x': 100, 'y': 100}
            },
            'ui': {
                'theme': 'default',
                'font_size': 10,
                'show_tooltips': True,
                'auto_expand_tree': True
            },
            'test_discovery': {
                'auto_discover': True,
                'watch_files': True,
                'include_patterns': ['test_*.py', '*_test.py'],
                'exclude_patterns': ['__pycache__', '.pytest_cache']
            },
            'test_execution': {
                'max_workers': 'auto',
                'timeout': 300,
                'capture_output': True,
                'verbose': True
            },
            'recent_projects': []
        }
        
    def load_config(self) -> None:
        """Load configuration from files."""
        self._load_app_config()
        self._load_pytest_config()
        
    def _load_app_config(self) -> None:
        """Load application configuration from JSON file."""
        try:
            if self.app_config_file.exists():
                with open(self.app_config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    
                # Merge with defaults (preserving new default keys)
                self._merge_config(self.app_config, loaded_config)
                self.logger.info("Loaded application configuration")
            else:
                self.logger.info("Using default application configuration")
                
        except Exception as e:
            self.logger.error(f"Error loading app config: {e}")
            
    def _load_pytest_config(self) -> None:
        """Load pytest configuration from INI file."""
        try:
            if self.pytest_config_file.exists():
                self.pytest_config.read(self.pytest_config_file)
                self.logger.info("Loaded pytest configuration")
            else:
                # Create default pytest configuration
                self._create_default_pytest_config()
                
        except Exception as e:
            self.logger.error(f"Error loading pytest config: {e}")
            
    def _create_default_pytest_config(self) -> None:
        """Create default pytest configuration."""
        self.pytest_config['pytest'] = {
            'testpaths': 'test',
            'python_files': 'test_*.py',
            'python_classes': 'Test*',
            'python_functions': 'test_*',
            'addopts': '-v --tb=short'
        }
        
    def _merge_config(self, default: Dict[str, Any], loaded: Dict[str, Any]) -> None:
        """Recursively merge loaded config with defaults."""
        for key, value in loaded.items():
            if key in default and isinstance(default[key], dict) and isinstance(value, dict):
                self._merge_config(default[key], value)
            else:
                default[key] = value
                
    def save_config(self) -> None:
        """Save current configuration to files."""
        self._save_app_config()
        self._save_pytest_config()
        
    def _save_app_config(self) -> None:
        """Save application configuration to JSON file."""
        try:
            with open(self.app_config_file, 'w', encoding='utf-8') as f:
                json.dump(self.app_config, f, indent=2)
            self.logger.info("Saved application configuration")
            
        except Exception as e:
            self.logger.error(f"Error saving app config: {e}")
            
    def _save_pytest_config(self) -> None:
        """Save pytest configuration to INI file."""
        try:
            with open(self.pytest_config_file, 'w', encoding='utf-8') as f:
                self.pytest_config.write(f)
            self.logger.info("Saved pytest configuration")
            
        except Exception as e:
            self.logger.error(f"Error saving pytest config: {e}")
            
    def get_app_setting(self, key_path: str, default: Any = None) -> Any:
        """
        Get application setting using dot notation.
        
        Args:
            key_path: Dot-separated path to setting (e.g., 'window.width')
            default: Default value if setting not found
            
        Returns:
            Setting value or default
        """
        keys = key_path.split('.')
        value = self.app_config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
            
    def set_app_setting(self, key_path: str, value: Any) -> None:
        """
        Set application setting using dot notation.
        
        Args:
            key_path: Dot-separated path to setting
            value: Value to set
        """
        keys = key_path.split('.')
        config = self.app_config
        
        # Navigate to parent of target key
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
            
        # Set the value
        config[keys[-1]] = value
        
    def get_pytest_option(self, option: str, default: str = '') -> str:
        """Get pytest configuration option."""
        return self.pytest_config.get('pytest', option, fallback=default)
        
    def set_pytest_option(self, option: str, value: str) -> None:
        """Set pytest configuration option."""
        if 'pytest' not in self.pytest_config:
            self.pytest_config['pytest'] = {}
        self.pytest_config['pytest'][option] = value
        
    def load_env_file(self, env_file_path: str) -> Dict[str, str]:
        """
        Load environment variables from .env file.
        
        Args:
            env_file_path: Path to .env file
            
        Returns:
            Dictionary of environment variables
        """
        try:
            env_path = Path(env_file_path)
            if env_path.exists():
                load_dotenv(env_path)
                
                # Read the file to get all variables
                env_vars = {}
                with open(env_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            env_vars[key.strip()] = value.strip().strip('"\'')
                            
                self.env_vars = env_vars
                self.logger.info(f"Loaded {len(env_vars)} environment variables")
                return env_vars
            else:
                self.logger.warning(f"Environment file not found: {env_file_path}")
                return {}
                
        except Exception as e:
            self.logger.error(f"Error loading environment file: {e}")
            return {}
            
    def save_env_file(self, env_file_path: str, env_vars: Dict[str, str]) -> None:
        """
        Save environment variables to .env file.
        
        Args:
            env_file_path: Path to .env file
            env_vars: Dictionary of environment variables
        """
        try:
            env_path = Path(env_file_path)
            env_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(env_path, 'w', encoding='utf-8') as f:
                f.write("# Pytest GUI Environment Variables\n")
                f.write("# Generated automatically - modify as needed\n\n")
                
                for key, value in sorted(env_vars.items()):
                    # Quote values that contain spaces or special characters
                    if ' ' in value or any(c in value for c in '"\'\\'):
                        value = f'"{value}"'
                    f.write(f"{key}={value}\n")
                    
            self.env_vars = env_vars.copy()
            self.logger.info(f"Saved {len(env_vars)} environment variables")
            
        except Exception as e:
            self.logger.error(f"Error saving environment file: {e}")
            
    def get_pytest_command(
        self,
        test_paths: List[str],
        markers: Optional[List[str]] = None,
        options: Optional[Dict[str, Any]] = None,
        env_vars: Optional[Dict[str, str]] = None
    ) -> List[str]:
        """
        Build pytest command with all options.
        
        Args:
            test_paths: List of test paths to run
            markers: List of markers to filter by
            options: Additional pytest options
            env_vars: Environment variables to set
            
        Returns:
            Complete pytest command as list of strings
        """
        cmd = ['python', '-m', 'pytest']
        
        # Add test paths
        cmd.extend(test_paths)
        
        # Add marker filters
        if markers:
            marker_expr = ' or '.join(markers)
            cmd.extend(['-m', marker_expr])
            
        # Add configured options
        addopts = self.get_pytest_option('addopts')
        if addopts:
            cmd.extend(addopts.split())
            
        # Add additional options
        if options:
            for key, value in options.items():
                if value is True:
                    cmd.append(f'--{key}')
                elif value is not False and value is not None:
                    cmd.extend([f'--{key}', str(value)])
                    
        self.logger.info(f"Built pytest command: {' '.join(cmd)}")
        return cmd
        
    def add_recent_project(self, project_path: str) -> None:
        """Add project to recent projects list."""
        recent = self.app_config.get('recent_projects', [])
        
        # Remove if already exists
        if project_path in recent:
            recent.remove(project_path)
            
        # Add to beginning
        recent.insert(0, project_path)
        
        # Keep only last 10
        self.app_config['recent_projects'] = recent[:10]
        
    def get_recent_projects(self) -> List[str]:
        """Get list of recent projects."""
        return self.app_config.get('recent_projects', [])
        
    def clear_recent_projects(self) -> None:
        """Clear recent projects list."""
        self.app_config['recent_projects'] = []