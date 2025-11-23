"""
Unit tests for environment function in causaliq_core.utils.

These tests use mocking to avoid system resource access, making them fast
and suitable for frequent execution during development.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from causaliq_core.utils import environment


@pytest.mark.unit
def test_environment_fresh_cache_mocked(monkeypatch):
    """Test environment function when cache doesn't exist (mocked calls)."""

    # Mock the expensive system calls
    def mock_uname():
        return type(
            "obj",
            (object,),
            {"system": "Linux", "version": "5.4.0-42-generic"},
        )()

    mock_cpu_info = {
        "brand_raw": "Intel(R) Core(TM) i7-8565U CPU @ 1.80GHz",
        "python_version": "3.11.9",
    }

    def mock_memory():
        return type("obj", (object,), {"total": 16 * 1024**3})()

    # Mock platformdirs to use temp directory
    with tempfile.TemporaryDirectory() as temp_dir:

        def mock_cache_dir(*args):
            return temp_dir

        def mock_get_cpu_info():
            return mock_cpu_info

        monkeypatch.setattr(
            "causaliq_core.utils.user_cache_dir", mock_cache_dir
        )
        monkeypatch.setattr("causaliq_core.utils.uname", mock_uname)
        monkeypatch.setattr(
            "causaliq_core.utils.get_cpu_info", mock_get_cpu_info
        )
        monkeypatch.setattr("causaliq_core.utils.virtual_memory", mock_memory)

        result = environment()

        # Verify expected structure and values
        expected = {
            "os": "Linux v5.4.0-42-generic",
            "cpu": "Intel(R) Core(TM) i7-8565U CPU @ 1.80GHz",
            "python": "3.11.9",
            "ram": 16,
        }

        assert result == expected

        # Verify cache file was created
        cache_path = Path(temp_dir) / "environment.json"
        assert cache_path.exists()

        # Verify cache contents
        with open(cache_path) as f:
            cached_data = json.load(f)
        assert cached_data == expected


@pytest.mark.unit
def test_environment_use_existing_cache_mocked(monkeypatch):
    """Test environment function uses existing fresh cache (mocked)."""
    expected_data = {
        "os": "Windows v10.0.19041",
        "cpu": "AMD Ryzen 7 3700X",
        "python": "3.11.9",
        "ram": 32,
    }

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a fresh cache file
        cache_path = Path(temp_dir) / "environment.json"
        with open(cache_path, "w") as f:
            json.dump(expected_data, f)

        monkeypatch.setattr(
            "causaliq_core.utils.user_cache_dir", lambda *args: temp_dir
        )

        # Mock time to ensure cache appears fresh (current time)
        with patch(
            "causaliq_core.utils.time",
            return_value=cache_path.stat().st_mtime + 1000,
        ):
            result = environment()

        # Should return cached data without calling system functions
        assert result == expected_data


@pytest.mark.unit
def test_environment_stale_cache_refresh_mocked(monkeypatch):
    """Test environment function refreshes stale cache (mocked)."""
    old_data = {
        "os": "Old System",
        "cpu": "Old CPU",
        "python": "3.9.0",
        "ram": 8,
    }

    new_data = {
        "os": "macOS v12.6.0",
        "cpu": "Apple M1",
        "python": "3.11.9",
        "ram": 16,
    }

    # Mock system calls to return new data
    def mock_uname():
        return type(
            "obj", (object,), {"system": "macOS", "version": "12.6.0"}
        )()

    mock_cpu_info = {"brand_raw": "Apple M1", "python_version": "3.11.9"}

    def mock_memory():
        return type("obj", (object,), {"total": 16 * 1024**3})()

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create stale cache file
        cache_path = Path(temp_dir) / "environment.json"
        with open(cache_path, "w") as f:
            json.dump(old_data, f)

        monkeypatch.setattr(
            "causaliq_core.utils.user_cache_dir", lambda *args: temp_dir
        )
        monkeypatch.setattr("causaliq_core.utils.uname", mock_uname)
        monkeypatch.setattr(
            "causaliq_core.utils.get_cpu_info", lambda: mock_cpu_info
        )
        monkeypatch.setattr("causaliq_core.utils.virtual_memory", mock_memory)

        # Mock time to make cache appear stale (25 hours old)
        current_time = cache_path.stat().st_mtime + (25 * 3600)
        with patch("causaliq_core.utils.time", return_value=current_time):
            result = environment()

        # Should return refreshed data
        assert result == new_data

        # Verify cache was updated
        with open(cache_path) as f:
            cached_data = json.load(f)
        assert cached_data == new_data


@pytest.mark.unit
def test_environment_custom_cache_dir_mocked(monkeypatch):
    """Test environment function with custom cache directory (mocked)."""

    def mock_uname():
        return type(
            "obj", (object,), {"system": "FreeBSD", "version": "13.1-RELEASE"}
        )()

    mock_cpu_info = {
        "brand_raw": "Intel Xeon E5-2680",
        "python_version": "3.11.9",
    }

    def mock_memory():
        return type("obj", (object,), {"total": 64 * 1024**3})()

    with tempfile.TemporaryDirectory() as temp_dir:
        custom_cache_dir = str(Path(temp_dir) / "custom_cache")

        monkeypatch.setattr("causaliq_core.utils.uname", mock_uname)
        monkeypatch.setattr(
            "causaliq_core.utils.get_cpu_info", lambda: mock_cpu_info
        )
        monkeypatch.setattr("causaliq_core.utils.virtual_memory", mock_memory)

        result = environment(cache_dir=custom_cache_dir)

        expected = {
            "os": "FreeBSD v13.1-RELEASE",
            "cpu": "Intel Xeon E5-2680",
            "python": "3.11.9",
            "ram": 64,
        }

        assert result == expected

        # Verify custom cache directory was created and used
        cache_path = Path(custom_cache_dir) / "environment.json"
        assert cache_path.exists()


@pytest.mark.unit
def test_environment_cache_directory_creation_mocked(monkeypatch):
    """Test environment function creates cache directory."""

    def mock_uname():
        return type(
            "obj", (object,), {"system": "Ubuntu", "version": "20.04.5"}
        )()

    mock_cpu_info = {"brand_raw": "Intel i5-9400F", "python_version": "3.11.9"}

    def mock_memory():
        return type("obj", (object,), {"total": 8 * 1024**3})()

    with tempfile.TemporaryDirectory() as temp_dir:
        # Use a nested path that doesn't exist
        custom_cache_dir = str(Path(temp_dir) / "deep" / "nested" / "cache")
        assert not Path(custom_cache_dir).exists()

        def mock_get_cpu_info():
            return mock_cpu_info

        monkeypatch.setattr("causaliq_core.utils.uname", mock_uname)
        monkeypatch.setattr(
            "causaliq_core.utils.get_cpu_info", mock_get_cpu_info
        )
        monkeypatch.setattr("causaliq_core.utils.virtual_memory", mock_memory)

        result = environment(cache_dir=custom_cache_dir)

        expected = {
            "os": "Ubuntu v20.04.5",
            "cpu": "Intel i5-9400F",
            "python": "3.11.9",
            "ram": 8,
        }

        assert result == expected

        # Verify directory was created
        assert Path(custom_cache_dir).exists()
        assert Path(custom_cache_dir).is_dir()

        # Verify cache file was created
        cache_path = Path(custom_cache_dir) / "environment.json"
        assert cache_path.exists()


@pytest.mark.unit
def test_environment_json_error_handling_mocked(monkeypatch):
    """Test environment function handles corrupted cache file gracefully."""

    def mock_uname():
        return type(
            "obj", (object,), {"system": "CentOS", "version": "8.4.2105"}
        )()

    mock_cpu_info = {"brand_raw": "AMD EPYC 7742", "python_version": "3.11.9"}

    def mock_memory():
        return type("obj", (object,), {"total": 128 * 1024**3})()

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create corrupted cache file
        cache_path = Path(temp_dir) / "environment.json"
        with open(cache_path, "w") as f:
            f.write("invalid json content {")

        def mock_cache_dir(*args):
            return temp_dir

        def mock_get_cpu_info():
            return mock_cpu_info

        monkeypatch.setattr(
            "causaliq_core.utils.user_cache_dir", mock_cache_dir
        )
        monkeypatch.setattr("causaliq_core.utils.uname", mock_uname)
        monkeypatch.setattr(
            "causaliq_core.utils.get_cpu_info", mock_get_cpu_info
        )
        monkeypatch.setattr("causaliq_core.utils.virtual_memory", mock_memory)

        # Mock time to make corrupted cache appear fresh
        with patch(
            "causaliq_core.utils.time",
            return_value=cache_path.stat().st_mtime + 1000,
        ):
            result = environment()

        # Should handle the error and return fresh data
        expected = {
            "os": "CentOS v8.4.2105",
            "cpu": "AMD EPYC 7742",
            "python": "3.11.9",
            "ram": 128,
        }

        assert result == expected


@pytest.mark.unit
def test_environment_cache_write_error_in_error_path_mocked(monkeypatch):
    """Test environment handles cache write error in error recovery path."""

    def mock_uname():
        return type(
            "obj", (object,), {"system": "Alpine", "version": "3.16.0"}
        )()

    mock_cpu_info = {"brand_raw": "ARM Cortex-A72", "python_version": "3.11.9"}

    def mock_memory():
        return type("obj", (object,), {"total": 4 * 1024**3})()

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a corrupted cache file
        cache_path = Path(temp_dir) / "environment.json"
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_path, "w") as f:
            f.write("invalid json content")

        monkeypatch.setattr(
            "causaliq_core.utils.user_cache_dir", lambda *args: temp_dir
        )
        monkeypatch.setattr("causaliq_core.utils.uname", mock_uname)
        monkeypatch.setattr(
            "causaliq_core.utils.get_cpu_info", lambda: mock_cpu_info
        )
        monkeypatch.setattr("causaliq_core.utils.virtual_memory", mock_memory)

        # Mock time to make corrupted cache appear fresh
        with patch(
            "causaliq_core.utils.time",
            return_value=cache_path.stat().st_mtime + 1000,
        ):
            # Mock open to fail on write attempts
            original_open = open

            def mock_failing_write(*args, **kwargs):
                if len(args) > 1 and args[1] == "w":
                    raise PermissionError("Cannot write to cache")
                return original_open(*args, **kwargs)

            with patch("builtins.open", side_effect=mock_failing_write):
                result = environment()

        # Should still return correct data despite both read and write errors
        expected = {
            "os": "Alpine v3.16.0",
            "cpu": "ARM Cortex-A72",
            "python": "3.11.9",
            "ram": 4,
        }

        assert result == expected
