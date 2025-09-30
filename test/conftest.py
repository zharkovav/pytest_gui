"""
Pytest configuration and fixtures for the test suite.
"""

import pytest
import tempfile
import os
from pathlib import Path


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def sample_data():
    """Provide sample data for tests."""
    return {
        'users': [
            {'id': 1, 'name': 'Alice', 'email': 'alice@example.com'},
            {'id': 2, 'name': 'Bob', 'email': 'bob@example.com'},
            {'id': 3, 'name': 'Charlie', 'email': 'charlie@example.com'}
        ],
        'products': [
            {'id': 1, 'name': 'Widget A', 'price': 10.99},
            {'id': 2, 'name': 'Widget B', 'price': 15.99},
            {'id': 3, 'name': 'Widget C', 'price': 20.99}
        ]
    }


@pytest.fixture
def mock_database():
    """Mock database connection for tests."""
    class MockDatabase:
        def __init__(self):
            self.data = {}
            
        def get(self, key):
            return self.data.get(key)
            
        def set(self, key, value):
            self.data[key] = value
            
        def delete(self, key):
            if key in self.data:
                del self.data[key]
                
        def clear(self):
            self.data.clear()
            
    return MockDatabase()


@pytest.fixture(scope="session")
def test_config():
    """Test configuration settings."""
    return {
        'api_url': 'http://localhost:8000',
        'timeout': 30,
        'retry_count': 3,
        'debug': True
    }