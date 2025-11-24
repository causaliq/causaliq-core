# CausalIQ Repo Template - Development Roadmap

**Last updated**: November 21, 2025  

This project roadmap fits into the [overall ecosystem roadmap](https:/https://causaliq.org/projects/ecosystem_roadmap/)

## 🎯 Current Release

  - **✅ 0.1 Foundation**: Initial package creation and support for shared utility capabilities (mathematical, random numbers and enums etc.)

Commits:

- `current` docs: provide the initial document set
- `bac248f` Refactor: moved math functions into utils, and legacy constant into top level __init__.py
- `b6f6369` Refactor: migrate timing capabilities into utils.timing
- `16851c8` Refactor: migrate random number capabilities into utils.random
- `38cf6e8` Refactor: migrate environment into utils
- `05549d7` Refactor: migrate adjmat and BAYESYS_VERSIONS into graph
- `42a3f9f` Refactor: migrate ln and rndsf math function, and simplify package structure
- `a626001` Refactor: migrate SOFTWARE_VERSION, EdgeMark, EdgeType and EnumWithAttrs
- `a469829` Fix: restrict CI testing to Python 3.11 on Ubuntu
- `c00bdb2` Refactor: change package name to causaliq-core
- `66cb058` Initial commit

---

## ✅ Previous Releases

*See Git commit history for detailed implementation progress*

- None


## 🛣️ Upcoming Implementation

### Release 0.2: Graphs [November 2025]
**Key Deliverables**: Graph classes representing SDG (general graph), PDAGs and DAGs 

### Release 0.3: Bayesian Networks [December 2025]
**Key Deliverables**: BN class and classes for local probability distributions

### Release 0.4: Input/Output [December 2025]
**Key Deliverables**: Input and output of graph, BN and data in different formats
