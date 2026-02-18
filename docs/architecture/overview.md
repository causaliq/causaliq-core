# Architecture Overview

## CausalIQ Ecosystem

causaliq-core is a foundational component of the overall
[CausalIQ ecosystem architecture](https://causaliq.org/projects/ecosystem_architecture/),
providing core utilities and patterns used across CausalIQ projects.

## Design Philosophy

The architecture emphasises **reproducibility**, **performance**, and
**cross-platform compatibility** through thoughtful design patterns and data
management strategies.

## Key Architectural Features

### Deterministic Random Number Generation

**Design Goal:** Ensure reproducible results across platforms and Python
versions.

**Implementation:**

- Uses an embedded list of pre-generated random numbers
  (`STABLE_RANDOM_SEQUENCE`)
- 10,000+ values generated from a fixed seed for cross-platform repeatability
- Avoids platform-specific random number generator differences
- Supports stable experiment randomisation for scientific reproducibility

```python
# Stable across all platforms and Python versions
from causaliq_core.utils.random import stable_random
values = stable_random(seed=42, count=100)  # Always identical results
```

### Intelligent Environment Caching

**Design Goal:** Minimise expensive system queries while maintaining fresh
data.

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

**Design Goal:** Extend Python enums with additional attributes while
preserving enum semantics.

**Implementation:**

- `EnumWithAttrs` base class for enums with human-readable labels
- Maintains enum value integrity while adding metadata
- Supports extensible attribute patterns for domain-specific needs

### Performance-Aware Timing Infrastructure

**Design Goal:** Non-intrusive performance measurement for production use.

**Implementation:**

- Singleton pattern for centralised timing collection
- Thread-safe timeout decorators and context managers
- Optional activation to eliminate overhead in production
- Hierarchical timing with action/scale categorisation

### Mathematical Precision Controls

**Design Goal:** Consistent numerical formatting across scientific
applications.

**Implementation:**

- Significant figure rounding with exact legacy behaviour preservation
- Configurable zero thresholds for scientific notation edge cases
- String-based output for precise display formatting control

### SQLite-Backed Token Cache

**Design Goal:** Efficient, persistent caching with compression support for
workflow data and computed results.

**Implementation:**

- SQLite-backed storage with concurrency support via database locking
- In-memory mode (`:memory:`) for fast, non-persistent caching
- Pluggable compressor architecture for data compression
- Shared token dictionary for cross-entry deduplication
- Hit counting and access tracking for cache analytics

```python
from causaliq_core.cache import TokenCache

with TokenCache(":memory:") as cache:
    cache.put("key123", b"data")
    data = cache.get("key123")
```

### Action Provider Framework

**Design Goal:** Standardised interface for workflow components that expose
multiple related actions.

**Implementation:**

- `CausalIQActionProvider` abstract base class defining the action interface
- `CoreActionProvider` with GraphML and JSON compression/decompression
- Structured input/output specifications via `ActionInput` and `ActionOutput`
- Action validation and execution error handling

## Module Organisation

```
causaliq_core/
├── __init__.py          # Package metadata and constants
├── action.py            # Action provider framework
├── cli.py               # Command-line interface
├── bn/                  # Bayesian Networks
│   ├── bn.py            # BN class (network structure)
│   ├── bnfit.py         # BNFit class (fitted parameters)
│   ├── dist/            # Conditional distributions (CPT, LinGauss)
│   └── io/              # BN file I/O (DSC, XDSL formats)
├── cache/               # Caching infrastructure
│   ├── token_cache.py   # SQLite-backed TokenCache
│   └── compressors/     # Pluggable compression backends
│       ├── base.py      # Compressor interface
│       └── json_compressor.py
├── graph/               # Graph structures and algorithms
│   ├── sdg.py           # Simple Dependency Graphs (base class)
│   ├── dag.py           # Directed Acyclic Graphs
│   ├── pdag.py          # Partially Directed Acyclic Graphs
│   ├── enums.py         # EdgeType, EdgeMark enumerations
│   ├── convert.py       # Graph type conversions
│   └── io/              # Graph I/O formats
│       ├── common.py    # Unified read_graph/write_graph
│       ├── graphml.py   # GraphML format support
│       ├── bayesys.py   # BayeSys format support
│       └── tetrad.py    # Tetrad format support
└── utils/               # Core utilities
    ├── __init__.py      # EnumWithAttrs and public exports
    ├── environment.py   # System environment detection
    ├── io.py            # File and DataFrame I/O utilities
    ├── math.py          # rndsf, ln mathematical functions
    ├── random.py        # Stable random generation
    ├── same.py          # Precision-aware value comparison
    └── timing.py        # Performance measurement
```

### Graph Module Architecture

**Design Goal:** Flexible representation of dependency graphs supporting
multiple graph types used in causal discovery.

**Implementation:**

- **SDG (Simple Dependency Graph)**: Base class supporting arbitrary endpoint
  marks (head `>`, tail `-`, circle `o`)
- **DAG**: Directed Acyclic Graph with parent/child relationships
- **PDAG**: Partially Directed Acyclic Graph (CPDAGs, equivalence classes)
- **Conversion Functions**: `dag_to_pdag`, `pdag_to_cpdag`, `extend_pdag`
- **Multi-Format I/O**: GraphML, BayeSys, and Tetrad format support

Supported graph types:

- Markov Graphs
- Directed Acyclic Graphs (DAGs)
- Partially Directed Acyclic Graphs (PDAGs)
- Maximal Ancestral Graphs (MAGs)
- Partial Ancestral Graphs (PAGs)

### Bayesian Networks Architecture

**Design Goal:** Modular probabilistic modelling with multiple distribution
types and file format support.

**Implementation:**

- **BN Core**: Main `BN` and `BNFit` classes for network representation
- **Distribution Module**: Pluggable conditional distributions (CPT for
  discrete, LinGauss for continuous)
- **I/O Layer**: Format-agnostic interface with DSC and XDSL backend support
- **Graph Integration**: Built on `causaliq_core.graph.DAG` foundation

### Value Comparison Utilities

**Design Goal:** Precision-aware comparison of numeric values, dictionaries,
and probability distributions.

**Implementation:**

- `values_same`: Compare numbers to specified significant figures
- `dicts_same`: Deep dictionary comparison with numeric precision
- `dists_same`: Probability distribution comparison

### Package Organisation Rationale

The package structure balances functionality distribution:

- **Main package**: Constants and metadata (lightweight imports)
- **Cache package**: Caching infrastructure with compressor plugins
- **Graph package**: Graph representations and I/O formats
- **BN package**: Bayesian Network modelling
- **Utils package**: Mathematical functions and core utilities
- **Action module**: Workflow integration framework

This structure supports both convenience imports
(`from causaliq_core.utils import rndsf`) and modular usage patterns while
maintaining backward compatibility.