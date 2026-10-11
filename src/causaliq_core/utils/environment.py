"""Environment and system information utilities."""

import json
from json import dump, load
from pathlib import Path
from platform import uname
from time import time
from typing import Any, Dict, Optional

from cpuinfo import get_cpu_info  # type: ignore[import-untyped]
from platformdirs import user_cache_dir
from psutil import virtual_memory


def _query_environment() -> Dict[str, Any]:
    """Query the operating system for fresh environment information.

    Returns:
        Environment information including os, cpu, python, ram.
    """
    return {
        "os": uname().system + " v" + uname().version,
        "cpu": get_cpu_info()["brand_raw"],
        "python": get_cpu_info()["python_version"],
        "ram": round(virtual_memory().total / (1024 * 1024 * 1024)),
    }


def _is_env_cache_stale(envfile_path: Path) -> bool:
    """Return whether the environment cache is missing or out of date.

    Args:
        envfile_path: Path of the cached environment JSON file.

    Returns:
        True when the cache must be rebuilt, False when it can be reused.
    """
    if not envfile_path.exists():
        return True
    return time() - envfile_path.stat().st_mtime > 24 * 3600


def _write_environment_cache(envfile_path: Path, env: Dict[str, Any]) -> None:
    """Write environment information to the cache file.

    Args:
        envfile_path: Path of the cached environment JSON file.
        env: Environment information to cache.
    """
    with open(envfile_path, "w") as file:
        dump(env, file)


def _refresh_environment_cache(envfile_path: Path) -> Dict[str, Any]:
    """Query fresh environment data and try to cache it.

    Args:
        envfile_path: Path of the cached environment JSON file.

    Returns:
        Freshly queried environment information.
    """
    env = _query_environment()
    try:
        _write_environment_cache(envfile_path, env)
    except (PermissionError, OSError):
        # If we can't write cache, just return the data
        pass
    return env


def _read_environment_cache(envfile_path: Path) -> Dict[str, Any]:
    """Read cached environment information, refreshing it if unusable.

    Args:
        envfile_path: Path of the cached environment JSON file.

    Returns:
        Environment information from the cache, or freshly queried data if
        the cache is corrupted or inaccessible.
    """
    try:
        with open(envfile_path, "r") as file:
            env: Dict[str, Any] = load(file)
        return env
    except (FileNotFoundError, PermissionError, json.JSONDecodeError):
        # If cache is corrupted or inaccessible, query fresh data
        return _refresh_environment_cache(envfile_path)


def environment(cache_dir: Optional[str] = None) -> Dict[str, Any]:
    """Obtain details of the hardware and software environment.

    For efficiency, this is obtained from a cached file "environment.json"
    if one modified in the last 24 hours is available, otherwise the OS
    is queried and a new cache file created.

    Args:
        cache_dir: Optional cache directory. If None, uses standard
            user cache directory for the platform.

    Returns:
        Environment information including os, cpu, python, ram.
    """
    if cache_dir is None:
        cache_dir = user_cache_dir("causaliq-core", "causaliq")

    cache_path = Path(cache_dir)
    cache_path.mkdir(parents=True, exist_ok=True)

    envfile_path = cache_path / "environment.json"

    # Check if cache exists and is fresh (< 24 hours old)
    if _is_env_cache_stale(envfile_path):
        # Query OS for fresh environment data and cache the results
        env = _query_environment()
        _write_environment_cache(envfile_path, env)
    else:
        # Load from cache
        env = _read_environment_cache(envfile_path)

    return env
