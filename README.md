# causaliq-repo-template

[![Python Support](https://img.shields.io/pypi/pyversions/zenodo-sync.svg)](https://pypi.org/project/zenodo-sync/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

This is a template for **creating new CausalIQ repos** which provides a new **capability** and follows CausalIQ development practices.

## Status

🚧 **Active Development** - This repository is currently in active development. It will be updated periodically to align with the latest approaches used in CausalIQ repos. New repos within the CausalIQ project should follow the naming convention causaliq-[capability], e.g. "causaliq-discovery" or "causaliq-analysis".


## Features

- 📁 **Standardised project structure**: following current best practices
- ⌨️ **CLI Interface**: An initial dummy command-line interface.
- 📖 **Documentation framework**: using mkdocs with shared CausalIQ branding.
- 🐍 **Python setup**: providing virtual environments for Python 3.9, 3.10, 3.11 and 3.12.
- 🔬 **pytest test framework**: for unit, functional and integration testing including code coverage.
- 🔄 **Continuous Integration testing**: across Python versions and operating systems using GitHub actions 


## New CausalIQ repo creation

This section provides instructions for **creating a completely new CausalIQ repo** which offers a **new capability**. This capability will be referred to as "newcapability" in the following instructions below, but should in practice be a word which meaningfully summarises the capability e.g. "pipeline" or "score".

### Prerequisites

- Git 
- Latest stable versions of Python 3.9, 3.10. 3.11 and 3.12

### Create the new repo on GitHub

- Create the new repo with name causaliq-newcapability specifying **this repository (i.e. causaliq-repo-template) as the template** with an initial commit message "feat: initial project setup from causaliq-repo-template"

### Clone the new repo locally and check that it works

Clone the causaliq-newcapability repo locally as normal

```bash
git clone https://github.com/causaliq/causaliq-newcapability.git
```

Set up the Python virtual environments and activate the default Python virtual environment. You may see
messages from VSCode (if you are using it as your IDE) that new Python environments are being created
as the scripts/setup-env runs - these messages can be safely ignored at this stage.

```text
scripts/setup-env -Install
scripts/activate
```

Check that the causaliq-repo-template CLI is working, check that all CI tests pass, and start up the local mkdocs webserver. There should be no errors  reported in any of these.

```text
causaliq-repo-template --help
scripts/check_ci
mkdocs serve
```

Enter **http://127.0.0.1:8000/** in a browser and check that the 
causaliq-repo-template skeleton documentation is visible.

If all of the above works, this confirms that the code from the template repo is working successfully on your system.

### Change all references in package to new package name

In the IDE (e.g. VSCode) editor make the following GLOBAL changes to all files and folder names

- replace **causaliq-repo-template** with **causaliq-newcapability** in all files (57 changes across 16 files)
- replace **causaliq_repo_template** with **causaliq_newcapability** in all files (13 changes across 5 files)
- rename folder **src/causaliq_repo_template** to **src/causaliq_newcapability**
- manually delete the **src/causaliq-repo-template.egg-info** package file
- manually delete all folders under venv (which will contain references to the causaliq-repo-template)

⚠️ **Important**: Make sure to use underscores for Python package names (`causaliq_newcapability`) and hyphens for repo names (`causaliq-newcapability`)

### Check newly named package works OK and commit to GitHub

- Remove and re-setup the virtual environments again (which will then contain the package causaliq-newcapability), and activate the default Pyhton virtual environment

```text
scripts/setup-env -Install
scripts/activate
```

Check the causaliq-newcapability command runs, that all CI checks pass with the new
package name, and that mkdocs for the renamed package can be served.

```text
causaliq-newcapability --help
scripts/check_ci
mkdocs serve
```
This should all work without any errors and the mkdocs should refer to causaliq-newcapability
rather than causaliq-repo-template.

This confirms that the package name has been successfully changed to "causaliq-newcapability". These changes can be commited to the new repo with message "refactor: package name changed to causaliq-newcapability"

### Start work on new package

The real work of implementing the functionality of this new CausalIQ package can now begin!

### Checklist
- [ ] GitHub repo created from template
- [ ] Repo cloned locally
- [ ] Initial tests pass
- [ ] All references renamed
- [ ] Folder renamed
- [ ] venv folders deleted
- [ ] Final tests pass
- [ ] Commit changes implementing new package name to GitHub
- [ ] Start work on the new package functionality!


---

**Supported Python Versions**: 3.9, 3.10, 3.11, 3.12  
**Default Python Version**: 3.11
