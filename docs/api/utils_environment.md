# Environment Functions

System environment detection with intelligent caching for performance optimization.

::: causaliq_core.utils.environment
    options:
      show_source: false

## Usage Examples

### Basic Environment Detection

```python
from causaliq_core.utils import environment

# Use default cache location
env = environment()
print(f"Running on {env['os']} with {env['ram']}GB RAM")
print(f"CPU: {env['cpu']}")
print(f"Python: {env['python']}")
```

### Custom Cache Directory

```python
from causaliq_core.utils import environment

# Use custom cache directory
env = environment(cache_dir="/tmp/my_cache")
print(f"OS: {env['os']}")
```

## Returned Information

The environment function returns a dictionary with the following keys:

- **`'os'`**: Operating system name and version
- **`'cpu'`**: CPU brand/model information  
- **`'python'`**: Python version string
- **`'ram'`**: Total system RAM in GB (rounded to nearest GB)

## Caching Behavior

- Cache files are stored as `environment.json` in the cache directory
- Cache is refreshed if older than 24 hours
- Uses platform-appropriate cache locations (e.g., `~/.cache` on Linux, `~/Library/Caches` on macOS)
- Gracefully handles cache corruption or permission errors