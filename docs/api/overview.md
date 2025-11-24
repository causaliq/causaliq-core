# CausalIQ Core API Reference

This is the entry point for the API documentation. It is organised by module,
with each module briefly described here to ease navigation of the API and
avoid overlong pages.

## [Main Package](main.md)

The main `causaliq_core` package exports:
- `SOFTWARE_VERSION`: Legacy software version constant for compatibility
- Package metadata (`__version__`, `VERSION`, etc.)

## Modules

### [CLI](cli.md)

Command-line interface functionality for CausalIQ Core.

### [Graph](graph.md)

Graph-related enumerations and utilities for edge types and marks used in
causal discovery.

### [Utils](utils.md)

Comprehensive utility module with specialized functional areas:
- [Mathematical Functions](utils_math.md): Number formatting and logarithm calculations
- [Environment Detection](utils_environment.md): System information with caching  
- [Random Numbers](utils_random.md): Reproducible random number generation
- [Timing Utilities](utils_timing.md): Performance measurement and timeouts
- Enhanced enumeration functionality
