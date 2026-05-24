# Data Conversion

`causaliq_core.r.convert` provides utilities for converting data between
Python and R representations. All conversion is text-based — data is
serialised to R code strings (Python → R) or parsed from tab-separated text
(R → Python).

## Functions

### `data_to_r_dataframe`

```python
def data_to_r_dataframe(
    sample: Any,
    columns: List[str],
    node_types: Dict[str, str],
    varname: str,
) -> str:
```

Generate R code that creates a `data.frame` from a Python sample.

**Parameters:**

- `sample` — array-like with shape `(n_rows, n_cols)`.
- `columns` — list of column names, one per column in `sample`.
- `node_types` — mapping from column name to node type. Columns with type
  `"categorical"` (case-insensitive) become R factors; all others become
  numeric vectors.
- `varname` — the R variable name to assign the data.frame to.

**Returns:** A string of R code, e.g.:

```r
df <- data.frame(
  A = c(1.2, 3.4, 5.6),
  B = factor(c("x", "y", "x"))
)
```

**Example:**

```python
from causaliq_core.r.convert import data_to_r_dataframe

code = data_to_r_dataframe(
    sample=[[1.0, "a"], [2.0, "b"]],
    columns=["X", "Y"],
    node_types={"X": "continuous", "Y": "categorical"},
    varname="df",
)
# code can be prepended to an R script and passed to run_r_script()
```

### `r_arcs_to_edges`

```python
def r_arcs_to_edges(
    arcs: List[Tuple[str, str]],
) -> List[Tuple[str, str, str]]:
```

Convert bnlearn arc pairs to CausalIQ edge tuples.

bnlearn represents a directed arc as `(from, to)`. A bidirectional pair
`(A, B)` and `(B, A)` is treated as an undirected edge.

**Parameters:**

- `arcs` — list of `(from_node, to_node)` tuples as returned by bnlearn.

**Returns:** List of `(tail, edge_type, head)` tuples:

- Directed arc `(A, B)` (without a reverse) → `("A", "-->", "B")`
- Bidirectional pair `(A, B)` + `(B, A)` → `("A", "---", "B")` (one entry)

**Example:**

```python
from causaliq_core.r.convert import r_arcs_to_edges

arcs = [("A", "B"), ("B", "C"), ("C", "B")]  # A->B, B<->C
edges = r_arcs_to_edges(arcs)
# [("A", "-->", "B"), ("B", "---", "C")]
```
