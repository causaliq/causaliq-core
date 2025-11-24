# CausalIQ Core

<!-- add in coverage and CI badges when repo is public -->

![Python Versions](https://img.shields.io/badge/python-3.9%2C%203.10%2C%203.11%2C%203.12-blue)

## Welcome

Welcome to the documentation for the CausalIQ Core — part of the [CausalIQ ecosystem](https://causaliq.org) for intelligent causal discovery. 

CausalIQ Core provides functionality required by several CausalIQ projects. It is not envisaged that it will be used or called directly itself, nor can it be directly used in [CausalIQ Workflows](https://causaliq.org/projects/workflow/).

---

## Overview

CausalIQ Core provides the following common functionality required by several user-facing CausalIQ packages in the following areas:

- **graph**: support for general graphs, PDAGs and CPDAGs used in causal discovery;
- **bn**: support for Bayesian Networks (BNs);
- **io**: filesystem io and format conversion, particularly relating to standard formats for graphs (.graphml, .dsc etc) and BNs (.xdsl)
- **utils**: utility enums, functions and classes, relating to random numbers, mathematical functions, path handling etc.

This site provides detailed documentation, including: development roadmap, architectural vision, design notes, and API reference for contributors. Since this is not a "user-facing" capability a user guide is not provided.


---

## Quickstart & Installation

For a quickstart guide and installation instructions, see the [README on GitHub](https://github.com/causaliq/causaliq-core#readme).

---

## Documentation Contents

- [Development Roadmap](roadmap.md): roadmap of upcoming features
- [Architecture](architecture/overview.md): overall architecture and design notes
- [API Reference](api/overview.md): complete reference for Python code
- [Development Guidelines](https://github.com/causaliq/causaliq-core/blob/main/CONTRIBUTING.md): CausalIQ guidelines for developers
- [Changelog](https://github.com/causaliq/causaliq-core/blob/main/CHANGELOG.md)
- [License](https://github.com/causaliq/causaliq-core/blob/main/LICENSE)

---

## Support & Community

- [GitHub Issues](https://github.com/causaliq/causaliq-core/issues): Report bugs or request features.
- [GitHub Discussions](https://github.com/causaliq/causaliq-core/discussions): Ask questions and join the community.

---

**Tip:**  
Use the navigation sidebar to explore the documentation.  
For the latest code and releases, visit the [causaliq-core GitHub repository](https://github.com/causaliq/causaliq-core).

---

**Supported Python Versions**: 3.9, 3.10, 3.11, 3.12  
**Default Python Version**: 3.11