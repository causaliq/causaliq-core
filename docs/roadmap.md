# CausalIQ Core - Development Roadmap

**Last updated**: May 24, 2026  

This project roadmap fits into the [overall ecosystem roadmap](https://causaliq.org/projects/ecosystem_roadmap/)

## 🚧 Under Development

### Release v0.8.0.dev1 — Language Integration

Provides the shared rpy2 foundation used by all CausalIQ repositories that
interact with R packages (initially bnlearn; the same pattern will be
extended to Java/Tetrad in a later release). This is a bona fide part of
`causaliq-core` — not confined to tests — because it provides session
management and data conversion used by `causaliq-discovery`'s
`BnlearnAdapter` and by integration tests in other repos.

#### R availability detection

- `is_r_available() -> bool`: detects whether R is installed and rpy2 can
  connect to it
- `is_r_package_available(package: str) -> bool`: checks whether a specific
  R package (e.g. `"bnlearn"`) is installed and loadable
- Both functions are safe to call unconditionally; they return `False`
  rather than raising when R is absent

#### R session management (`src/causaliq_core/r/`)

- Shared rpy2 session initialisation and `robjects` / `rpackages` access
  helpers used by downstream adapters
- Converts rpy2 `RRuntimeError` and related exceptions into typed Python
  exceptions so callers never depend on rpy2 directly

#### Data conversion utilities

- `data_to_r_dataframe(data: Data) -> rpy2 DataFrame`: converts a CausalIQ
  `Data` object to an R `data.frame` using `Data.sample` (NumPy array) and
  `Data.nodes` / `Data.node_types`; categorical columns become R factors,
  continuous columns become numeric vectors
- `r_arcs_to_edges(r_arcs) -> List[Tuple]`: converts bnlearn arc lists
  (flat endpoint lists) to CausalIQ `(tail, type, head)` edge tuples

#### bnlearn graph utilities (ported from legacy `call/bnlearn.py`)

- `bnlearn_cpdag(pdag: PDAG) -> PDAG`: PDAG → CPDAG conversion via bnlearn;
  used for equivalence testing against the native CausalIQ implementation
- `bnlearn_compare(graph: SDG, ref: SDG) -> dict`: structural comparison
  metrics (SHD, TP, FP, FN) via bnlearn
- `bnlearn_import(rda_path: str) -> BN`: import a BN from an `.rda` file

#### pytest `r_integration` marker

- `conftest.py` provides a `pytest.mark.r_integration` marker that
  auto-skips any test when `is_r_available()` or the required package check
  returns `False`
- The same pattern will be used for `pytest.mark.java_integration` (Tetrad)
  and any other external-tool integrations in future
- `r_integration` tests are **excluded from GitHub Actions CI** and from the
  100% coverage requirement
- All non-R code paths (session management, data conversion logic, error
  wrapping) are covered by unit tests using mocked rpy2

#### Tests

- Unit tests for data conversion and availability detection using mocked rpy2
- `r_integration` tests comparing `bnlearn_cpdag()` output against the
  native CausalIQ PDAG → CPDAG conversion
- `r_integration` tests comparing `bnlearn_compare()` structural metrics
  against native CausalIQ equivalents
- `r_integration` tests for `bnlearn_import()` round-trip fidelity

---

## ✅ Previous Releases

  - **0.1.0 Foundation** [November 2025]: Initial package creation and support for shared utility capabilities (mathematical, random numbers and enums etc.)

  - **0.2.0 Graphs** [November 2025]: Graph classes representing SDG (general graph), PDAGs and DAGs, and support for Tetrad and Bayesys graph file formats.

  - **0.3.0 Bayesian Networks** [December 2025]: BN class and classes for local probability distributions, and support for DSC and XDSL BN file formats.

  - **0.4.0 Caching Infrastructure** [February 2026]: Token-based caching and (de)compression of JSON and GraphML.

  - **0.5.0 Aggregation Workflows** [March 2026]: PDG class, filter expressions and metadata-driven weighting.

  - **0.6.0 Optimal DAG** [March 2026]: Greedy optimal DAG extraction from PDG, ActionPattern enum, and template method pattern for action providers.

  - **0.7.0 Randomised Filters** [April 2026]: `random()` function support in filter expressions.


*See Git commit history for detailed implementation progress*


## 🛣️ Upcoming Implementation

- none planned beyond v0.8.0.dev1

---

**Dependencies**: None (this is the base layer)

