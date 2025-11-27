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
    if (
        not envfile_path.exists()
        or time() - envfile_path.stat().st_mtime > 24 * 3600
    ):
        # Query OS for fresh environment data
        env = {
            "os": uname().system + " v" + uname().version,
            "cpu": get_cpu_info()["brand_raw"],
            "python": get_cpu_info()["python_version"],
            "ram": round(virtual_memory().total / (1024 * 1024 * 1024)),
        }

        # Cache the results
        with open(envfile_path, "w") as file:
            dump(env, file)
    else:
        # Load from cache
        try:
            with open(envfile_path, "r") as file:
                env = load(file)
        except (FileNotFoundError, PermissionError, json.JSONDecodeError):
            # If cache is corrupted or inaccessible, query fresh data
            env = {
                "os": uname().system + " v" + uname().version,
                "cpu": get_cpu_info()["brand_raw"],
                "python": get_cpu_info()["python_version"],
                "ram": round(virtual_memory().total / (1024 * 1024 * 1024)),
            }

            # Try to cache the results
            try:
                with open(envfile_path, "w") as file:
                    dump(env, file)
            except (PermissionError, OSError):
                # If we can't write cache, just return the data
                pass

    return env
