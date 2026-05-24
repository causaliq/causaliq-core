# Session Management

`causaliq_core.r.session` provides the core subprocess primitives for running
R code from Python.

## Functions

### `run_r_script`

```python
def run_r_script(script: str, timeout: int = 60) -> str:
```

Run an R script by piping it through stdin to `Rscript --vanilla -`.

**Parameters:**

- `script` — R code to execute. The entire script is passed via stdin; no
  temporary files are created.
- `timeout` — maximum wall-clock seconds to wait for the R process to finish.
  Defaults to 60.

**Returns:** The captured stdout of the R process as a string.

**Raises:**

- `RNotAvailableError` — if `Rscript` cannot be found on PATH or via
  `R_HOME`.
- `RRuntimeError` — if the R process exits with a non-zero code. The
  exception message includes the stderr output from R.

**Example:**

```python
from causaliq_core.r.session import run_r_script

result = run_r_script("cat(1 + 1, '\\n')")
print(result)  # 2
```

The `--vanilla` flag disables `.Rprofile` and `.Rhistory`, ensuring
reproducible behaviour regardless of the user's R configuration.

### `_find_rscript`

```python
def _find_rscript() -> Optional[str]:
```

Locate the `Rscript` executable.

The search proceeds in two stages:

1. `shutil.which("Rscript")` — covers the common case where R is on PATH.
2. Platform-specific candidates under `R_HOME` — handles installations where
   R is present but not on PATH.

**Returns:** The full path to `Rscript`, or `None` if it cannot be found.

This function is an implementation detail of `run_r_script` and
`is_r_available`. It is not part of the public API but is documented here
for completeness.
