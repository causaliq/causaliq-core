# CausalIQ Core API Reference

This is the entry point for the API documentation. It is organised by module,
with each module briefly described here to ease navigation of the API and
avoid overlong pages.

## [Main Package](main.md)

The main `causaliq_core` package exports:

- `SOFTWARE_VERSION`: Legacy software version constant for compatibility
- Package metadata (`__version__`, `VERSION`, etc.)

## Modules

### [Bayesian Networks](bn.md)

Bayesian Networks functionality including network structures, conditional distributions, and I/O operations.

### [Cache](cache.md)

SQLite-backed caching infrastructure with shared token dictionary:

- [TokenCache](cache.md): Core cache with connection management
- [Compressors](cache_compressors.md): Pluggable compressors (Compressor, JsonCompressor)

### [CLI](cli.md)

Command-line interface functionality for CausalIQ Core.

### [Graph](graph.md)

Graph-related enumerations and utilities for edge types and marks used in
causal discovery.

### [R Integration](r.md)

Subprocess-based R session management, data conversion, and bnlearn graph
utilities:

- [Session Management](r_session.md): `run_r_script`, Rscript discovery
- [Availability](r_availability.md): `is_r_available`, `is_r_package_available`
- [Data Conversion](r_convert.md): `data_to_r_dataframe`, `r_arcs_to_edges`
- [bnlearn Utilities](r_bnlearn.md): `bnlearn_cpdag`, `bnlearn_compare`, `bnlearn_import`
- [Exceptions](r_exceptions.md): `RNotAvailableError`, `RPackageNotAvailableError`, `RRuntimeError`

### [Utils](utils.md)

Comprehensive utility module with specialized functional areas:

- [Mathematical Functions](utils_math.md): Number formatting and logarithm calculations
- [Environment Detection](utils_environment.md): System information with caching  
- [Random Numbers](utils_random.md): Reproducible random number generation
- [Timing Utilities](utils_timing.md): Performance measurement and timeouts
- Enhanced enumeration functionality
