# R Exceptions

`causaliq_core.r.exceptions` defines exception types raised by the R
integration module.

## Exception Types

### `RNotAvailableError`

Raised when `Rscript` cannot be found on the system.

```python
from causaliq_core.r.exceptions import RNotAvailableError
```

This exception is raised by `run_r_script()` when `_find_rscript()` returns
`None`. It indicates that R is not installed or not on PATH, and that
`R_HOME` does not point to a valid R installation.

**Example:**

```python
from causaliq_core.r.session import run_r_script
from causaliq_core.r.exceptions import RNotAvailableError

try:
    run_r_script("cat('hello')")
except RNotAvailableError:
    print("R is not installed on this system")
```

### `RPackageNotAvailableError`

Raised when a required R package is not installed.

```python
from causaliq_core.r.exceptions import RPackageNotAvailableError
```

This exception can be raised by callers that require a specific R package.
It is not raised automatically by `run_r_script` — use
`is_r_package_available()` to check before calling R, or catch
`RRuntimeError` from bnlearn if the package is absent.

### `RRuntimeError`

Raised when an R process exits with a non-zero exit code.

```python
from causaliq_core.r.exceptions import RRuntimeError
```

The exception message includes the stderr output from the R process, which
typically contains the R error message and traceback.

**Example:**

```python
from causaliq_core.r.session import run_r_script
from causaliq_core.r.exceptions import RRuntimeError

try:
    run_r_script("stop('something went wrong')")
except RRuntimeError as e:
    print(f"R error: {e}")
```

## Usage Notes

- Prefer `is_r_available()` and `is_r_package_available()` as guards over
  catching `RNotAvailableError` and `RPackageNotAvailableError`.
- Catch `RRuntimeError` when you want to handle R script failures gracefully
  rather than propagating them.
- All three exceptions inherit from Python's built-in `Exception`.
