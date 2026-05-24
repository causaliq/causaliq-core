# R Integration

The `causaliq_core.r` module provides subprocess-based R session management,
data conversion utilities, and bnlearn graph utilities. It was introduced in
v0.8.0 as the shared R foundation for CausalIQ packages that interact with R.

## Overview

R is invoked via `Rscript --vanilla -` with scripts piped through stdin. No
rpy2, no Rtools, and no C compiler are required — a plain CRAN R installation
is sufficient.

```python
from causaliq_core.r import (
    run_r_script,
    is_r_available,
    is_r_package_available,
)

if is_r_available() and is_r_package_available("bnlearn"):
    output = run_r_script('cat("hello from R\\n")')
    print(output)  # hello from R
```

## Submodules

| Submodule | Purpose |
|---|---|
| [session](r_session.md) | Rscript discovery and script execution |
| [availability](r_availability.md) | R and R package availability detection |
| [convert](r_convert.md) | Python ↔ R data conversion utilities |
| [bnlearn](r_bnlearn.md) | bnlearn graph utilities (CPDAG, compare, import) |
| [exceptions](r_exceptions.md) | R-specific exception types |

## Prerequisites

Install R from CRAN — no additional Python packages are needed:

```
https://cran.r-project.org/
```

Install bnlearn from within R for graph utilities:

```r
install.packages("bnlearn")
```

## See Also

- [R Language Integration Architecture](../architecture/r_integration.md) —
  design rationale, call flow, and test strategy
