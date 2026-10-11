# refactor causaliq-core modules according to module and method rules

Please develop a plan to refactor all `causaliq-core` modules to obey the
development policies


## Constraints learned from `causaliq-analysis` refactors

- **Behaviour must stay byte-identical**
- **Preserve import binding sites**
- **No behaviour-free bulk test rewrites**: add focused tests
  only where coverage gaps appear

## Commits

Stage the work as **between two and four commits** which the user will do:

1. **Code and tests** — one to three commits
2. **Documentation** — one documentation commit

Do not mix documentation-only changes into the code commit.

## Gates after each slice (as in `scripts/check_ci.ps1`)

- `black --check src tests`
- `isort --check-only src tests`
- `flake8 src tests`
- `mypy src/`
- `python scripts/check_code_rules.py --strict src/causaliq_core`

Maintain **100 % coverage** on the new modules and keep the `ord_hc_f1` SVG
replication test green.

## Outcome

The refactor is complete. `python scripts/check_code_rules.py` reports zero
breaches across all 60 modules in `src/causaliq_core`, the full test suite
passes with 100 % coverage, and behaviour is unchanged.

| Stage | Modules refactored | Breaches reported |
| --- | --- | --- |
| Starting point | – | 67 |
| Slice 1 | `utils`, `cache`, `java` | 52 |
| Slice 2 | `graph` | 26 |
| Slice 3 | `bn`, `action`, `r` | 0 |

### What changed

- Long methods and functions were split into private helpers, keeping every
  method within the statement and nesting depth limits.
- Modules that exceeded the module statement limit were decomposed into
  sibling sub-modules which the original module re-exports, so public API,
  module paths and import sites are unchanged. Details of the decomposition
  are recorded in the [architecture overview](architecture/overview.md).
- Modules whose functions are substituted in tests with
  `monkeypatch.setattr` were flattened in place (`utils.environment`,
  `utils.timing`, `java.session`, `r.bnlearn` and `graph.io`) so that patches
  still intercept the calls.
- One test was added for filter expression rendering, where the refactor
  exposed a coverage gap.

### Verification

Every slice was checked with `black --check`, `isort --check-only`, `flake8`,
`mypy src/` and the strict rules report, followed by the full test suite at
100 % coverage on Python 3.9 to 3.13 in CI.
