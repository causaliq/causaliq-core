# refactor action.py according to module and method rules

Please develop a plan to refactor @src\causaliq_core\action.py to obey the
development policies


## Constraints learned from `causaliq-analysis` refactors

- **Behaviour must stay byte-identical**
- **Preserve import binding sites**
- **No behaviour-free bulk test rewrites**: add focused tests
  only where coverage gaps appear

## Quality Gates (as in `scripts/check_ci.ps1`)

- `black --check src tests`
- `isort --check-only src tests`
- `flake8 src tests`
- `mypy src/`
- `python scripts/check_code_rules.py --strict src/causaliq_core`
