# R Language Integration

The `causaliq_core.r` module provides subprocess-based access to R packages
from Python. It was introduced in v0.8.0 as the shared R foundation used by
`causaliq-discovery` and other CausalIQ packages that interact with R.

## Design Rationale

### Why subprocess instead of rpy2?

The previous approach used **rpy2**, a C-extension that embeds the R runtime
in the Python process. This caused several practical problems:

| Problem | rpy2 | subprocess |
|---|---|---|
| Windows install | Requires Rtools + make | Plain CRAN R sufficient |
| CI setup | Complex linker configuration | Install R, done |
| Isolation | Shared process memory | Separate R process |
| Debugging | Opaque C-level errors | Full R stderr captured |
| Version coupling | rpy2 version tied to R version | Any R version works |

The subprocess approach runs `Rscript --vanilla -` and pipes R code through
stdin. Stdout is returned as a string and parsed in Python. This is simpler,
more portable, and easier to test.

## Architecture

### Module Structure

```
causaliq_core/r/
├── __init__.py        # Exports run_r_script
├── session.py         # _find_rscript(), run_r_script()
├── availability.py    # is_r_available(), is_r_package_available()
├── convert.py         # data_to_r_dataframe(), r_arcs_to_edges()
├── bnlearn.py         # bnlearn_cpdag(), bnlearn_compare(), bnlearn_import()
└── exceptions.py      # RNotAvailableError, RPackageNotAvailableError,
                       #   RRuntimeError
```

### Call Flow

```
Python caller
    │
    ├─ is_r_available()            # guard check — returns bool, never raises
    │
    ├─ data_to_r_dataframe(...)    # serialise Python data → R code string
    │
    └─ run_r_script(script)
           │
           ├─ _find_rscript()      # PATH → R_HOME fallback
           │
           └─ subprocess.run(
                  ["Rscript", "--vanilla", "-"],
                  input=script,    # R code piped via stdin
                  capture_output=True,
                  text=True,
                  timeout=timeout
              )
                  │
                  ├─ stdout  →  parsed by caller (arcs, metrics, BN fields)
                  └─ stderr  →  included in RRuntimeError on non-zero exit
```

## Session Management

### Rscript Discovery

`_find_rscript()` locates the Rscript executable using a two-stage search:

1. **PATH search** — `shutil.which("Rscript")` covers the common case where
   R is on the system PATH.
2. **R_HOME fallback** — if the `R_HOME` environment variable is set,
   platform-specific candidate paths under it are checked with
   `os.path.isfile`. This handles installations where R is present but not
   on PATH (common in some CI environments).

The function returns `None` if Rscript cannot be found; callers that need to
raise do so explicitly.

### Script Execution

`run_r_script(script, timeout=60)` provides the single execution primitive:

- The R script is passed via **stdin** (`--vanilla -`). This avoids creating
  temporary files and makes the call parallel-safe.
- `--vanilla` disables R's `.Rprofile` and `.Rhistory` so results are
  reproducible regardless of the user's R configuration.
- `RNotAvailableError` is raised when `_find_rscript()` returns `None`.
- `RRuntimeError` is raised on non-zero exit, with stderr included in the
  message.

## Data Exchange

All data flows between Python and R as **plain text**. There are no binary
formats, no shared memory, and no temp files.

### Python → R: code generation

`data_to_r_dataframe(sample, columns, node_types, varname)` returns a string
of R code that assigns a `data.frame`. Each column is serialised inline:

- **Continuous nodes** → `c(1.2, 3.4, ...)` numeric vectors
- **Categorical nodes** → `factor(c("a","b","a", ...))` factor vectors

The generated code is concatenated with the calling script and piped to R in
a single `run_r_script` call.

### R → Python: text parsing

R scripts write results to stdout as delimited text:

| Use case | Format | Parsed by |
|---|---|---|
| Graph arcs | `from\tto` per line | `r_arcs_to_edges()` |
| Structural metrics | `tp\tfp\tfn\tshd` single line | `bnlearn_compare()` |
| BN parameters | `NODE\t…`, `PARENTS\t…`, `COEF\t…`, `SD\t…` blocks | `_parse_bn_output()` |

## bnlearn Utilities

### CPDAG Conversion (`bnlearn_cpdag`)

Converts a `PDAG` to a CPDAG using bnlearn's `cpdag()` function. This
provides a reference implementation for testing CausalIQ's native
`pdag_to_cpdag` against bnlearn's.

The function:

1. Builds an `empty.graph` in R with the PDAG's nodes
2. Adds arcs and edges via `set.arc` and `set.edge`
3. Calls `cpdag()` and prints arcs as tab-separated pairs
4. Parses the output with `r_arcs_to_edges`

### Structural Comparison (`bnlearn_compare`)

Wraps bnlearn's `compare()` and `shd()` functions to compute four structural
metrics between a learned graph and a reference:

- **tp** — true positives (correct edges)
- **fp** — false positives (extra edges)
- **fn** — false negatives (missing edges)
- **shd** — Structural Hamming Distance

### BN Import (`bnlearn_import`)

Loads a fitted bnlearn BN from an `.rda` file and converts it to a
`causaliq_core.bn.BN` object. The R script extracts node names, parent
lists, regression coefficients, and standard deviations, then writes them to
stdout as tagged lines. Python parses these lines into `LinGauss`
conditional distributions and assembles the `BN`.

## Error Handling

Three exception types cover the error surface:

```
RNotAvailableError        # Rscript not found on this system
RPackageNotAvailableError # required R package not installed
RRuntimeError             # R process exited with non-zero code
```

All three inherit from Python's built-in `Exception`. Callers that want to
handle R absence gracefully should use `is_r_available()` or
`is_r_package_available()` as guards rather than catching exceptions.

## Testing Strategy

### Unit Tests

All r-module functions are covered by unit tests that monkeypatch
`subprocess.run`. This means:

- The full Python logic (argument building, output parsing, error wrapping)
  is covered without R being installed.
- Tests run in CI on all Python versions without any R dependency.

### Integration Tests (`r_integration` marker)

Tests marked `r_integration` call real R. They are:

- **Skipped automatically** when `is_r_available()` returns `False`
- **Excluded from the main CI pipeline** (run only in the dedicated
  `r-integration.yml` workflow)
- **Excluded from the 100% coverage requirement**

The `r_integration` marker pattern will be reused for future external-tool
integrations (e.g. `java_integration` for Tetrad).

To run integration tests locally (requires R and bnlearn):

```powershell
.\scripts\activate.ps1
python -m pytest tests/integration/r/ -v -m r_integration
```

## Prerequisites

Only a standard **CRAN R** installation is required. No additional Python
packages, no Rtools, no `make`:

```
https://cran.r-project.org/
```

Install bnlearn from within R:

```r
install.packages("bnlearn")
```

Verify that R is available:

```python
from causaliq_core.r import is_r_available, is_r_package_available

print(is_r_available())                       # True
print(is_r_package_available("bnlearn"))      # True
```
