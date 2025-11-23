"""
Functional tests for environment function in causaliq_core.utils.

These tests interact with the filesystem and OS, so they are functional
rather than unit tests.
"""

import os
import tempfile
from pathlib import Path
from time import time

import pytest

from causaliq_core.utils import environment

# Mark all tests in this module as slow since they access system resources
pytestmark = pytest.mark.slow


def test_environment_fresh_cache():
    """Test environment() when no cache file exists - should query OS."""
    with tempfile.TemporaryDirectory() as temp_dir:
        env = environment(cache_dir=temp_dir)

        # Verify expected keys are present
        assert set(env.keys()) == {"cpu", "os", "python", "ram"}

        # Verify cache file was created
        cache_file = Path(temp_dir) / "environment.json"
        assert cache_file.exists()

        # Verify data types are correct
        assert isinstance(env["cpu"], str)
        assert isinstance(env["os"], str)
        assert isinstance(env["python"], str)
        assert isinstance(env["ram"], int)
        assert env["ram"] > 0  # RAM should be positive


def test_environment_use_cache():
    """Test environment() using cached data - should be fast."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # First call creates cache
        environment(cache_dir=temp_dir)
        cache_file = Path(temp_dir) / "environment.json"
        first_mtime = cache_file.stat().st_mtime

        # Second call should use cache (same results)
        env2 = environment(cache_dir=temp_dir)
        second_mtime = cache_file.stat().st_mtime

        # Cache file should not have been modified
        assert first_mtime == second_mtime

        # Results should be valid
        assert set(env2.keys()) == {"cpu", "os", "python", "ram"}


def test_environment_stale_cache():
    """Test environment() with stale cache - should refresh."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create initial cache
        environment(cache_dir=temp_dir)
        cache_file = Path(temp_dir) / "environment.json"

        # Make cache file appear old (> 24 hours)
        old_time = time() - 2 * 24 * 3600  # 2 days ago
        os.utime(cache_file, times=(old_time, old_time))

        # Call again - should refresh cache
        env2 = environment(cache_dir=temp_dir)
        new_mtime = cache_file.stat().st_mtime

        # Cache should have been refreshed (newer timestamp)
        assert new_mtime > old_time

        # Results should still be valid
        assert set(env2.keys()) == {"cpu", "os", "python", "ram"}


def test_environment_default_cache_dir():
    """Test environment() with default cache directory."""
    # This test uses the actual user cache directory
    env = environment()

    # Should still return valid environment data
    assert set(env.keys()) == {"cpu", "os", "python", "ram"}
    assert isinstance(env["ram"], int)
    assert env["ram"] > 0


def test_environment_cache_directory_creation():
    """Test that environment() creates cache directory if it doesn't exist."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Use a subdirectory that doesn't exist yet
        cache_dir = Path(temp_dir) / "nested" / "cache" / "dir"
        assert not cache_dir.exists()

        # Function should create the directory
        env = environment(cache_dir=str(cache_dir))

        # Directory and cache file should now exist
        assert cache_dir.exists()
        assert (cache_dir / "environment.json").exists()
        assert set(env.keys()) == {"cpu", "os", "python", "ram"}


def test_environment_error_handling():
    """Test environment() handles filesystem errors gracefully."""
    # Test with invalid cache directory (should fall back to temp or raise)
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a file where we want a directory
        bad_cache_path = Path(temp_dir) / "not_a_directory"
        bad_cache_path.write_text("I'm a file, not a directory")

        # This should raise an exception when trying to create cache dir
        with pytest.raises((OSError, FileExistsError, PermissionError)):
            environment(cache_dir=str(bad_cache_path))
