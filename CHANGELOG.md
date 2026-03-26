# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Nothing yet

### Changed
- Nothing yet

### Deprecated
- Nothing yet

### Removed
- Nothing yet

### Fixed
- Nothing yet

### Security
- Nothing yet

## [0.6.0 Optimal DAG] - 2026-03-26

### Added
- `GreedyDAGResult` and `PDG.to_dag_greedy()` for greedy optimal DAG extraction from PDG
- `ActionPattern` enum for workflow action execution patterns (CREATE, UPDATE, AGGREGATE)
- Template method pattern for `CausalIQActionProvider` with `validate_parameters()` hook

### Fixed
- Precision errors when checking probabilities sum to 1 in PDGs (1e-6 tolerance)
- Improved error message when action parameter is missing
- Corrected variable name in sports test data file

## [0.5.0 Aggregation Workflows] - 2026-03-01

### Added
- Probabilistic Dependency Graph (`PDG`) class for representing uncertainty over graph structures
- `EdgeProbabilities` dataclass for edge state probability distributions
- Compact binary `PDG.compress()` / `PDG.decompress()` serialisation
- GraphML I/O support for PDG (`read_pdg`, `write_pdg`)
- Filter expression evaluation (`evaluate_filter`, `validate_filter`, `filter_entries`)
- Metadata-driven weight computation (`compute_weight`, `validate_weight_spec`)
- Safe expression evaluation using `simpleeval` library

## [0.4.0 Caching Infrastructure] - 2026-02-18

### Added
- Token-based caching infrastructure
- Compression and decompression support for JSON format
- Compression and decompression support for GraphML format

## [0.3.0 Bayesian Networks] - 2025-12-15

### Added
- Bayesian Network (`BN`) class
- Local probability distribution classes
- DSC file format support (read and write)
- XDSL file format support (read and write)

## [0.2.0 Graph classes] - 2025-11-30

### Added
- Simple Dependency Graphs (`SDG`)
- Partially Directed Acyclic Graphs (`PDAG` and `CPDAG`)
- Directed Acyclic Graphs (`DAG`)
- conversion between the different graph types
- read and write Tetrad and Bayesys format graph definition files


## [0.1.0 Foundation and utilities] - 2025-11-24

### Added
- Mathematical utilities for significant figures and logarithms
- Environment detection with intelligent caching
- Enhanced enumeration classes with metadata
- Timing and performance measurement tools
- Stable cross-platform random number generation
- Command-line interface and graph utilities
- Comprehensive API documentation
