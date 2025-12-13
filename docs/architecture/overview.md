# Architecture Overview

## CausalIQ Ecosystem

causaliq-core is a foundational component of the overall [CausalIQ ecosystem architecture](https://causaliq.org/projects/ecosystem_architecture/), providing core utilities and patterns used across CausalIQ projects.

## Design Philosophy

The architecture emphasizes **reproducibility**, **performance**, and **cross-platform compatibility** through thoughtful design patterns and data management strategies.

## Key Architectural Features

### Deterministic Random Number Generation

**Design Goal:** Ensure reproducible results across platforms and Python versions.

**Implementation:**
- Uses an embedded list of pre-generated random numbers (`STABLE_RANDOM_SEQUENCE`) 
- 10,000+ values generated from a fixed seed for cross-platform repeatability
- Avoids platform-specific random number generator differences
- Supports stable experiment randomization for scientific reproducibility

```python
# Stable across all platforms and Python versions
from causaliq_core.utils.random import stable_random
values = stable_random(seed=42, count=100)  # Always identical results
```

### Intelligent Environment Caching

**Design Goal:** Minimize expensive system queries while maintaining fresh data.

**Implementation:**
- 24-hour cache expiration for hardware/software environment detection
- Platform-appropriate cache directories (follows OS conventions)
- Graceful fallback on cache corruption or permission errors
- JSON-based cache storage for human readability and debugging

```python
# First call queries system, subsequent calls use cache
env = environment()  # May take 100ms+ on first call
env = environment()  # Returns cached data instantly
```

### Enhanced Enumeration Pattern

**Design Goal:** Extend Python enums with additional attributes while preserving enum semantics.

**Implementation:**

- `EnumWithAttrs` base class for enums with human-readable labels
- Maintains enum value integrity while adding metadata
- Supports extensible attribute patterns for domain-specific needs

### Performance-Aware Timing Infrastructure

**Design Goal:** Non-intrusive performance measurement for production use.

**Implementation:**

- Singleton pattern for centralized timing collection
- Thread-safe timeout decorators and context managers
- Optional activation to eliminate overhead in production
- Hierarchical timing with action/scale categorization

### Mathematical Precision Controls

**Design Goal:** Consistent numerical formatting across scientific applications.

**Implementation:**

- Significant figure rounding with exact legacy behavior preservation
- Configurable zero thresholds for scientific notation edge cases
- String-based output for precise display formatting control

## Module Organization

```
causaliq_core/
├── __init__.py          # Package metadata and constants
├── cli.py              # Command-line interface
├── bn/                 # Bayesian Networks
│   ├── dist/           # Conditional distributions (CPT, LinGauss)
│   └── io/             # BN file I/O (DSC, XDSL formats)
├── graph/              # Graph structures and enums
├── utils/              # Core utilities
│   ├── __init__.py     # Math functions, enums, environment
│   ├── io.py           # File and DataFrame I/O utilities
│   ├── random.py       # Stable random generation
│   └── timing.py       # Performance measurement
```

### Bayesian Networks Architecture

**Design Goal:** Modular probabilistic modeling with multiple distribution types and file format support.

**Implementation:**

 - **BN Core**: Main BN and BNFit classes for network representation
 - **Distribution Module**: Pluggable conditional distributions (CPT for discrete, LinGauss for continuous)  
 - **I/O Layer**: Format-agnostic interface with DSC and XDSL backend support
 - **Graph Integration**: Built on causaliq_core.graph DAG foundation

### Package Reorganization Rationale

The recent package structure balances functionality distribution:

- **Main package**: Constants and metadata (lightweight imports)
- **Utils package**: Mathematical functions and core utilities 
- **Specialized modules**: Domain-specific functionality (graph, timing, random)

This structure supports both convenience imports (`from causaliq_core.utils import rndsf`) and modular usage patterns while maintaining backward compatibility.