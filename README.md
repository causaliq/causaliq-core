# causaliq-core

[![Python Support](https://img.shields.io/pypi/pyversions/causaliq-core.svg)](https://pypi.org/project/causaliq-core/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

This is the core package providing common functionality required by several CausalIQ packages.

## Installation

Install from PyPI:

```bash
pip install causaliq-core
```

## Status

🚧 **Active Development** - This repository is currently in active development, which involves:

- migrating functionality from the legacy monolithic [discovery repo](https://github.com/causaliq/discovery) 
- restructuring classes to reduce module size and improve maintainability and improve usability
- ensure CausalIQ development standards are met



## Features

Currently implemented:

- **Release v0.1.0 - Foundation and utilities**: CausalIQ compliant development environment and utility functions (timing, random numbers, environment detection, etc.)
- **Release v0.2.0 - Graph classes**: Graph types for causal discovery including Summary Dependence Graphs (SDG), Partially Directed Acyclic Graphs (PDAG), Directed Acyclic Graphs (DAG), with conversion utilities and I/O support for Tetrad/Bayesys formats
- **Release v0.3.0 - Bayesian Networks**: support for Bayesian Networks and their parameterised distributions and I/O support for DSC and XDSL formats

Upcoming releases:

- **Release v0.4.0 - Graph ML**: support for GraphML formats

## Quick Start

```python
from causaliq_core.graph import PDAG, read, write

# Create a partially directed graph
pdag = PDAG(['X', 'Y', 'Z'], [('X', '->', 'Y'), ('Y', '--', 'Z')])

# Save and load graphs
write(pdag, "my_graph.csv")  # Bayesys format
loaded_graph = read("my_graph.csv")

# Convert between graph types
from causaliq_core.graph import extend_pdag
dag = extend_pdag(pdag)  # Extend PDAG to DAG
```

## Getting started

### Prerequisites

- Git 
- Latest stable versions of Python 3.9, 3.10. 3.11 and 3.12


### Clone the new repo locally and check that it works

Clone the causaliq-core repo locally as normal

```bash
git clone https://github.com/causaliq/causaliq-core.git
```

Set up the Python virtual environments and activate the default Python virtual environment. You may see
messages from VSCode (if you are using it as your IDE) that new Python environments are being created
as the scripts/setup-env runs - these messages can be safely ignored at this stage.

```text
scripts/setup-env -Install
scripts/activate
```

Check that the causaliq-core CLI is working, check that all CI tests pass, and start up the local mkdocs webserver. There should be no errors  reported in any of these.

```text
causaliq-core --help
scripts/check_ci
mkdocs serve
```

Enter **http://127.0.0.1:8000/** in a browser and check that the 
causaliq-core documentation is visible.

If all of the above works, this confirms that the code is working successfully on your system.


### Start work on new features

The real work of implementing the functionality of this new CausalIQ package can now begin!

## Documentation

Full API documentation is available at: **http://127.0.0.1:8000/** (when running `mkdocs serve`)

## Contributing

This repository is part of the CausalIQ ecosystem. For development setup:

1. Clone the repository
2. Run `scripts/setup-env -Install` to set up environments  
3. Run `scripts/check_ci` to verify all tests pass
4. Start documentation server with `mkdocs serve`

---

**Supported Python Versions**: 3.9, 3.10, 3.11, 3.12  
**Default Python Version**: 3.11  
**License**: MIT
