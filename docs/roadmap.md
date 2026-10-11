# CausalIQ Core - Development Roadmap

**Last updated**: October 11, 2026  

This project roadmap fits into the [overall ecosystem roadmap](https://causaliq.org/projects/ecosystem_roadmap/)

## 🚧 Under Development

### v0.8.0 Language Integration [October 2026]

1. ✅ Subprocess-based Rscript session management (`run_r_script`)
1. ✅ R availability detection and bnlearn graph utilities
1. ✅ Java integration
1. ✅ [Refactor all modules to meet development guidelines](current_task.md)
1. 📊 Support Python 3.10-14, with 3.12 as default, and badge as [![SPEC 0 — Minimum Supported Dependencies](https://img.shields.io/badge/SPEC-0-green?labelColor=%23004811&color=%235CA038)](https://scientific-python.org/specs/spec-0000/)

---

## ✅ Implemented Releases

### v0.7.0 Randomised Filters [April 2026]

- **`random()`** function support in filter expressions.

### v0.6.0 Optimal DAG [March 2026]

- **optimal DAG**: greedy extraction from PDG
- **ActionPattern enum**
- **template method pattern** for action providers.

### v0.5.0 Aggregation Workflows [March 2026]

- **PDG**: Probabilistic Dependency Graph of edge type probabilities
- **filter expressions**
- **metadata-driven weighting**

### v0.4.0 Caching Infrastructure [February 2026]

- **token-based caching**
- **object (de)compression**: of JSON and GraphML


### v0.3.0 - Bayesian Networks [December 2025]

- **BN class**
- **for local probability distributions**
- **BN i/o**: DSC and XDSL BN file formats.


### v0.2.0 - Graphs [November 2025]

- **SDG**: (general graph)
- **PDAGs and DAGs**
- **graph i/o**: Tetrad and Bayesys graph file formats

### v0.1.0 - Foundation [November 2025]: 

- **Initial package creation**
- **shared utility capabilities**: mathematical, random numbers and enums etc.


*See Git commit history for detailed implementation progress*


## 🛣️ Upcoming Implementation

- none planned

---

**Dependencies**: None (this is the base layer)
