# bnlearn Utilities

`causaliq_core.r.bnlearn` provides Python wrappers around bnlearn graph
operations. All functions require R and the bnlearn package to be available.

## Functions

### `bnlearn_cpdag`

```python
def bnlearn_cpdag(pdag: PDAG) -> PDAG:
```

Convert a PDAG to a CPDAG using bnlearn's `cpdag()` function.

This is used as a reference implementation for testing CausalIQ's native
`pdag_to_cpdag` against bnlearn's output.

**Parameters:**

- `pdag` — a `causaliq_core.graph.PDAG` instance to convert.

**Returns:** A new `PDAG` representing the CPDAG (completed partially directed
acyclic graph) produced by bnlearn.

**Raises:**

- `RNotAvailableError` — if R is not available.
- `RRuntimeError` — if bnlearn raises an error (e.g. the input graph is not
  a valid PDAG).

**Example:**

```python
from causaliq_core.graph import PDAG
from causaliq_core.r.bnlearn import bnlearn_cpdag

pdag = PDAG(["A", "B", "C"], [("A", "-->", "B"), ("B", "---", "C")])
cpdag = bnlearn_cpdag(pdag)
```

### `bnlearn_compare`

```python
def bnlearn_compare(pdag: PDAG, ref: PDAG) -> Dict[str, int]:
```

Compare a learned graph against a reference using bnlearn's `compare()` and
`shd()` functions.

**Parameters:**

- `pdag` — the learned graph to evaluate.
- `ref` — the reference (ground-truth) graph.

**Returns:** A dictionary with four integer metrics:

| Key | Meaning |
|---|---|
| `tp` | True positives — edges in both `pdag` and `ref` |
| `fp` | False positives — edges in `pdag` but not `ref` |
| `fn` | False negatives — edges in `ref` but not `pdag` |
| `shd` | Structural Hamming Distance |

**Example:**

```python
from causaliq_core.graph import PDAG
from causaliq_core.r.bnlearn import bnlearn_compare

learned = PDAG(["A", "B", "C"], [("A", "-->", "B")])
ref    = PDAG(["A", "B", "C"], [("A", "-->", "B"), ("B", "-->", "C")])

metrics = bnlearn_compare(learned, ref)
# {"tp": 1, "fp": 0, "fn": 1, "shd": 1}
```

### `bnlearn_import`

```python
def bnlearn_import(rda_path: str) -> BN:
```

Load a fitted bnlearn Gaussian BN from an `.rda` file.

The `.rda` file must contain a single object named `bn` of class
`bn.fit` with Gaussian (`GaussianNode`) conditional distributions.

**Parameters:**

- `rda_path` — path to the `.rda` file.

**Returns:** A `causaliq_core.bn.BN` instance with a `DAG` structure and
`LinGauss` conditional node distributions.

**Raises:**

- `RNotAvailableError` — if R is not available.
- `RRuntimeError` — if the `.rda` file cannot be loaded or is not a
  Gaussian `bn.fit` object.

**Example:**

```python
from causaliq_core.r.bnlearn import bnlearn_import

bn = bnlearn_import("/path/to/model.rda")
print(bn.dag.nodes)   # ['A', 'B', 'C']
print(bn.dag.edges)   # [('A', 'B'), ('B', 'C')]
```

## Data Exchange Format

bnlearn functions communicate with R via tab-separated stdout. The R scripts
write results to stdout; Python parses them line by line.

**Arcs** (for `bnlearn_cpdag`):
```
A\tB
B\tC
C\tB
```

**Metrics** (for `bnlearn_compare`):
```
tp\tfp\tfn\tshd
1\t0\t1\t1
```

**BN parameters** (for `bnlearn_import`):
```
NODE\tA
PARENTS\t
COEF\t(Intercept)\t0.5
SD\t1.2
NODE\tB
PARENTS\tA
COEF\t(Intercept)\t0.1\tA\t1.5
SD\t0.8
```
