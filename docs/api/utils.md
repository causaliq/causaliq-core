# Utils Module Overview

The `causaliq_core.utils` module provides utility classes, enhanced enumeration functionality, mathematical utilities, random number utilities, and system utilities for common programming patterns used across the CausalIQ ecosystem.

## Core Components

### [Mathematical Functions](utils_math.md)
Number formatting and logarithm calculations including:

- `rndsf()` - Round to significant figures with precise formatting
- `ln()` - Logarithm with configurable base (2, 10, or 'e')

### I/O Operations
File and path handling utilities:

- `is_valid_path()` - Path validation and existence checking
- `write_dataframe()` - Enhanced DataFrame writing with compression and formatting

### [Environment Detection](utils_environment.md) 
System environment detection with intelligent caching:

- `environment()` - Hardware and software environment information
- Cross-platform compatibility with automatic caching

### [Random Number Generation](utils_random.md)
Stable, reproducible random number sequences:

- Cross-platform reproducible sequences
- Stable random number generation for experiments
- Random integer iterators
- Experiment randomization enums

### [Timing Utilities](utils_timing.md)
Performance measurement and timeout functionality:

- `Timing` class for performance measurement
- `run_with_timeout()` and `@with_timeout` for algorithm timeouts  
- Thread-safe execution with configurable timeouts

### Enhanced Enumerations

::: causaliq_core.utils.EnumWithAttrs
    options:
      show_source: false

## Usage Pattern

The utils module is designed as a consolidated toolkit for common programming patterns:

```python
# Mathematical operations
from causaliq_core.utils import rndsf, ln

# Environment detection  
from causaliq_core.utils import environment

# Enhanced enums
from causaliq_core.utils import EnumWithAttrs

# Timing and random numbers in submodules
from causaliq_core.utils.timing import Timing
from causaliq_core.utils.random import stable_random
```

## Module Structure

- **Main Module** (`causaliq_core.utils`): Core functions and enhanced enums
- **Random Submodule** (`causaliq_core.utils.random`): Random number utilities
- **Timing Submodule** (`causaliq_core.utils.timing`): Performance and timeout utilities

For detailed API documentation, see the specialized pages linked above.

