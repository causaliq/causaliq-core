# Main Package

The main `causaliq_core` package provides core constants and metadata for the CausalIQ ecosystem.

## Constants

### `SOFTWARE_VERSION`

Legacy software version constant for backward compatibility.

**Type:** `int`  
**Value:** `229`

**Usage:**

```python
from causaliq_core import SOFTWARE_VERSION

print(f"Software version: {SOFTWARE_VERSION}")
```

This constant was migrated from the legacy module and is maintained for compatibility with existing code.

## Package Metadata

The package also exports standard metadata:

- `__version__`: Package version string (e.g., "0.1.0")
- `VERSION`: Version as tuple for programmatic comparison
- `__author__`, `__email__`: Author information
- `__title__`, `__description__`: Package title and description
- `__url__`, `__license__`: Repository URL and license

**Usage:**

```python
import causaliq_core

print(f"Package version: {causaliq_core.__version__}")
print(f"Version tuple: {causaliq_core.VERSION}")
```