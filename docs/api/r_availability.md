# Availability Detection

`causaliq_core.r.availability` provides functions for checking whether R and
specific R packages are available on the current system. These functions
never raise; they return `False` when R is absent.

## Functions

### `is_r_available`

```python
def is_r_available() -> bool:
```

Return `True` if `Rscript` is available on this system.

The check uses `_find_rscript()` to locate Rscript, then runs a minimal
version-print command to confirm the installation is functional.

**Returns:** `True` if R is available and executes successfully, `False`
otherwise.

**Example:**

```python
from causaliq_core.r.availability import is_r_available

if is_r_available():
    print("R is available")
else:
    print("R not found — skipping R-dependent steps")
```

This function is safe to call unconditionally. It is used as the guard in
`pytest.mark.r_integration` to skip integration tests when R is absent.

### `is_r_package_available`

```python
def is_r_package_available(package: str) -> bool:
```

Return `True` if the named R package is installed and loadable.

Runs `requireNamespace("<package>", quietly=TRUE)` via `run_r_script` and
returns whether it succeeds.

**Parameters:**

- `package` — the R package name to check (e.g. `"bnlearn"`).

**Returns:** `True` if the package can be loaded, `False` otherwise.

**Example:**

```python
from causaliq_core.r.availability import is_r_package_available

if is_r_package_available("bnlearn"):
    print("bnlearn is ready")
```

## Usage Pattern

The recommended pattern for code that depends on R is to guard with these
functions rather than catching exceptions:

```python
from causaliq_core.r.availability import (
    is_r_available,
    is_r_package_available,
)

if not is_r_available():
    raise RuntimeError("R is required but not available")

if not is_r_package_available("bnlearn"):
    raise RuntimeError("bnlearn is required but not installed")
```

In tests, use `pytest.mark.r_integration` which applies these checks
automatically via `conftest.py`.
