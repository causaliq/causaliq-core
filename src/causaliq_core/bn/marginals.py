#
#   Cache for marginal distributions computed for a Bayesian Network
#

from typing import Any, Dict, List, Optional, Tuple, Union

from pandas import DataFrame, MultiIndex

from causaliq_core.graph import DAG
from causaliq_core.utils import ln

from .dist import NodeValueCombinations


class MarginalsCache:
    """Cache for marginal distributions to improve performance.

    This cache stores computed marginal distributions to avoid recomputation
    of expensive probability calculations. It limits cached entries to a
    maximum number of nodes to control memory usage.

    Attributes:
        MAX_NODES: Maximum number of nodes allowed in cached marginals.
        cache: Dictionary storing cached marginal distributions.
        stats: Dictionary tracking cache performance statistics.
    """

    MAX_NODES = 3  # limit on number of nodes for cached marginals

    def __init__(self) -> None:
        """Initialize the marginals cache with empty cache and statistics."""
        self.cache: Dict[Any, Any] = {}
        self.stats = {
            "get.ok": 0,
            "get.miss": 0,
            "get.big": 0,
            "put.ok": 0,
            "put.dupl": 0,
            "put.big": 0,
        }

    def get(self, nodes: List[str]) -> Optional[Any]:
        """Retrieve cached marginal distribution for specified nodes.

        Args:
            nodes: List of node names to get marginal distribution for.

        Returns:
            Cached marginal distribution if found, None otherwise.
        """
        if len(nodes) > self.MAX_NODES:
            self.stats["get.big"] += 1
            return None
        key = frozenset(nodes)
        if key in self.cache:
            self.stats["get.ok"] += 1
            # print('Cache hit for {}'.format(nodes))
            return self.cache[key]
        else:
            self.stats["get.miss"] += 1
            return None

    def put(self, dist: Any) -> None:
        """Store marginal distribution in cache if within size limits.

        Args:
            dist: Marginal distribution to cache. Expected format is a list
                of tuples containing node value dictionaries and probabilities.

        Returns:
            None. Updates cache statistics based on operation result.
        """
        nodes = set(dist[0][0].keys())
        if len(nodes) > self.MAX_NODES:
            self.stats["put.big"] += 1
            return None
        key = frozenset(nodes)
        if key in self.cache:
            self.stats["put.dupl"] += 1
            return None
        else:
            self.stats["put.ok"] += 1
            self.cache.update({key: dist})
            # print('Cache put for {}'.format(nodes))
            return None

    def __str__(self) -> str:
        return "{}".format(self.stats)


def _check_marginal_distribution_args(
    dag_nodes: List[str], node: str, parents: Optional[List[str]]
) -> None:
    """Validate the arguments of BN.marginal_distribution().

    Args:
        dag_nodes: Nodes of the network's DAG.
        node: Node for which the distribution is required.
        parents: Parents of the node, if any.

    Raises:
        TypeError: If arguments have bad types.
        ValueError: If arguments have bad values.
    """
    if (
        not isinstance(node, str)
        or (not isinstance(parents, list) and parents is not None)
        or (
            parents is not None
            and any([not isinstance(p, str) for p in parents])
        )
    ):
        raise TypeError("marginal_distribution bad arg types")

    if node not in dag_nodes or (
        parents is not None
        and (
            node in parents
            or any([p not in dag_nodes for p in parents])
            or len(parents) != len(set(parents))
        )
    ):
        raise ValueError("marginal_distribution bad node value")


def _accumulate_marginals(
    bn: Any,
    node: str,
    parents: Optional[List[str]],
    node_values: Dict[str, List[str]],
) -> Dict[Any, Dict[str, float]]:
    """Accumulate marginal probabilities for a node and its parents.

    Args:
        bn: Bayesian Network whose marginals are required.
        node: Node for which the distribution is required.
        parents: Parents of the node, if any.
        node_values: Possible values of every node {node: [values]}.

    Returns:
        Marginal probabilities keyed by parental value combination, or by
        the node itself for a parentless node.
    """
    marginals: Dict[Any, Dict[str, float]] = {}
    for case in NodeValueCombinations(node_values):
        lnprob = bn.lnprob_case(case)
        if lnprob is None:
            continue  # ignore cases with zero possibility
        node_value = case[node]
        pvs = frozenset([(p, case[p]) for p in parents]) if parents else node
        if pvs not in marginals:
            marginals[pvs] = {v: 0.0 for v in node_values[node]}
        marginals[pvs][node_value] += 10**lnprob
    return marginals


def _marginal_frame(
    node: str, node_values: List[str], marginals: Dict[str, float]
) -> DataFrame:
    """Return a parentless node's marginal distribution as a frame.

    Args:
        node: Node the distribution applies to.
        node_values: Values the node can take.
        marginals: Marginal probability of each node value.

    Returns:
        Distribution in the same format returned by Pandas crosstab.
    """
    df: DataFrame = DataFrame(
        [[v, marginals[v]] for v in node_values], columns=[node, ""]
    )
    indexed: DataFrame = df.set_index(node)  # type: ignore[assignment]
    return indexed


def _parental_marginal_frame(
    node: str,
    parents: List[str],
    node_values: List[str],
    marginals: Dict[Any, Dict[str, float]],
) -> DataFrame:
    """Return a node's marginal distribution over its parents as a frame.

    Args:
        node: Node the distribution applies to.
        parents: Parents of the node.
        node_values: Values the node can take.
        marginals: Marginal probabilities keyed by parental combination.

    Returns:
        Distribution with parental combos as columns and node values as
        rows, in the same format returned by Pandas crosstab.
    """
    columns = []  # list of tuples of each parental value combo
    probs = []  # marg. probs for each pvs for each node value
    for pvs, pmf in marginals.items():
        pvs_dict = {t[0]: t[1] for t in pvs}
        columns.append(tuple([pvs_dict[p] for p in parents]))
        probs.append([pmf[v] for v in node_values])
    result: DataFrame = DataFrame(
        data=[list(i) for i in zip(*probs)],  # transpose
        columns=MultiIndex.from_tuples(columns, names=parents),
        index=node_values,
    )
    renamed: DataFrame = result.rename_axis(node)  # type: ignore[assignment]
    return renamed


def _check_marginal_nodes(dag_nodes: List[str], nodes: List[str]) -> None:
    """Validate the node list of BN.marginals().

    Args:
        dag_nodes: Nodes of the network's DAG.
        nodes: Nodes for which the marginal is required.

    Raises:
        TypeError: If nodes is not a list.
        ValueError: If nodes is empty, repeats a node or names an
            unknown node.
    """
    if not isinstance(nodes, list):
        raise TypeError("bn.marginal_distribution() bad arg types")

    if (
        not len(nodes)
        or len(nodes) != len(set(nodes))
        or not all([n in dag_nodes for n in nodes])
    ):
        raise ValueError("bn.marginal_distribution() bad arg values")


def _record_ancestors(
    parents: Dict[str, List[str]],
    children: Dict[str, set],
    ancestors: set,
    node: str,
) -> Tuple[set, Dict[str, set]]:
    """Record a node and its parents as ancestors, and its parent links.

    Args:
        parents: Parents of each node.
        children: Children of each node, updated in place.
        ancestors: Ancestors found so far.
        node: Node to add to the ancestors.

    Returns:
        Tuple of (ancestors, children) including the node.
    """
    ancestors = ancestors | {node} | set(parents[node])
    for p in parents[node]:
        children[p] = children[p] | {node}
    return ancestors, children


def _ordered_required_nodes(
    dag: DAG, nodes: List[str]
) -> Tuple[List[str], Dict[str, List[str]], Dict[str, set]]:
    """Return the nodes needed for a marginal, in topological order.

    Args:
        dag: DAG of the network.
        nodes: Nodes for which the marginal distribution is required.

    Returns:
        Tuple of (order, parents of each node, children of each node), with
        nodes that are neither required nor ancestors removed.
    """
    parents = {
        n: dag.parents[n] if n in dag.parents else [] for n in dag.nodes
    }
    partial_order = dag.partial_order(parents)
    order = [n for g in (partial_order or []) for n in g]

    ancestors: set = set()
    children: Dict[str, set] = {n: set() for n in dag.nodes}
    for i in range(len(order) - 1, -1, -1):  # work up the order
        node = order[i]
        if node in nodes or node in ancestors:
            # node is in reqd distribution, or is an ancestor of one, so
            # add it and its parents to ancestors
            ancestors, children = _record_ancestors(
                parents, children, ancestors, node
            )
            continue
        #   node is not required, nor an ancestor so disregard it
        order.pop(i)
        children.pop(node)

    return order, parents, children


def _single_node_marginals_frame(
    node: str, dist: List[Tuple[Dict[str, Any], float]]
) -> DataFrame:
    """Return the marginal distribution frame of a single node.

    Args:
        node: Node the distribution covers.
        dist: Marginal distribution as [({node: value, ...}, prob), ...].

    Returns:
        Distribution in the same format returned by Pandas crosstab.
    """
    df: DataFrame = DataFrame(
        sorted([[(e[0][node]), e[1]] for e in dist]), columns=[node, ""]
    )
    indexed: DataFrame = df.set_index(node)  # type: ignore[assignment]
    return indexed


def _marginal_matrix(
    dist: List[Tuple[Dict[str, Any], float]],
    nodes: List[str],
    index_node: str,
    node_values: List[str],
    row_index: Dict[str, int],
) -> Dict[Tuple[Any, ...], List[Optional[float]]]:
    """Return the node value matrix of a multi-node marginal distribution.

    Args:
        dist: Marginal distribution as [({node: value, ...}, prob), ...].
        nodes: Remaining nodes the distribution covers.
        index_node: Node forming the rows of the matrix.
        node_values: Values the index node can take.
        row_index: Row of each value of the index node.

    Returns:
        Probabilities of each combination of the remaining node values.
    """
    matrix: Dict[Tuple[Any, ...], List[Optional[float]]] = {}
    for entry in dist:
        values = tuple([entry[0][n] for n in nodes])
        if values not in matrix:
            matrix[values] = [None] * len(node_values)
        matrix[values][row_index[entry[0][index_node]]] = entry[1]
    return matrix


def _multi_node_marginals_frame(
    nodes: List[str],
    dist: List[Tuple[Dict[str, Any], float]],
    cnds: Dict[str, Any],
) -> DataFrame:
    """Return the marginal distribution frame of several nodes.

    Args:
        nodes: Nodes the distribution covers.
        dist: Marginal distribution as [({node: value, ...}, prob), ...].
        cnds: Conditional distributions of each node.

    Returns:
        Distribution with a MultiIndex of columns, in the same format
        returned by Pandas crosstab.
    """
    index_node = nodes[0]
    node_values = cnds[index_node].node_values()
    row_index = {node_values[i]: i for i in range(len(node_values))}
    remaining = nodes[1:]
    matrix = _marginal_matrix(
        dist, remaining, index_node, node_values, row_index
    )
    columns = [k for k in matrix.keys()]
    probs = [matrix[k] for k in matrix.keys()]
    dist_df: DataFrame = DataFrame(
        data=[list(i) for i in zip(*probs)],  # transpose
        columns=MultiIndex.from_tuples(columns, names=remaining),
        index=node_values,
    )
    renamed: DataFrame = dist_df.rename_axis(  # type: ignore[assignment]
        index_node
    )
    return renamed


def _marginals_frame(
    nodes: List[str],
    dist: List[Tuple[Dict[str, Any], float]],
    cnds: Dict[str, Any],
) -> DataFrame:
    """Return a marginal distribution in Pandas crosstab format.

    Args:
        nodes: Nodes the distribution covers.
        dist: Marginal distribution as [({node: value, ...}, prob), ...].
        cnds: Conditional distributions of each node.

    Returns:
        Marginal distribution as a DataFrame.
    """
    if len(nodes) == 1:
        return _single_node_marginals_frame(nodes[0], dist)
    return _multi_node_marginals_frame(nodes, dist, cnds)


def _check_lnprob_args(
    dag_nodes: List[str], case_values: Dict[str, Any], base: Union[int, str]
) -> None:
    """Validate the arguments of BN.lnprob_case().

    Args:
        dag_nodes: Nodes of the network's DAG.
        case_values: Value for each node {node: value}.
        base: Logarithm base to use - 2, 10 or 'e'.

    Raises:
        TypeError: If arguments wrong type.
        ValueError: If arguments have invalid values.
    """
    if (
        not isinstance(base, int) and not isinstance(base, str)
    ) or not isinstance(case_values, dict):
        raise TypeError("bad arg type for lnprob_case")

    if sorted(list(case_values.keys())) != dag_nodes or base not in [
        2,
        10,
        "e",
    ]:
        raise ValueError("bad arg values for lnprob_case")


def _parental_values_for(
    parents: Dict[str, List[str]], node: str, case_values: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Return the parental values of a node within a case.

    Args:
        parents: Parents of each node {node: [parents]}.
        node: Node whose parental values are required.
        case_values: Value for each node {node: value}.

    Returns:
        Parental values of the node, or None for a parentless node.
    """
    if node not in parents:
        return None
    return {p: case_values[p] for p in parents[node]}


def _node_lnprob(
    cnd: Any, pvs: Optional[Dict[str, Any]], value: Any, base: Union[int, str]
) -> Optional[float]:
    """Return the log probability of one node taking a value.

    Args:
        cnd: Conditional distribution of the node.
        pvs: Parental values of the node, if any.
        value: Value the node takes.
        base: Logarithm base to use.

    Returns:
        Log of the conditional probability, or None when it is zero.

    Raises:
        ValueError: If the value is not a valid case value for the node.
    """
    try:
        prob = cnd.cdist(pvs)[value]
        if prob == 0.0:
            return None
        return float(ln(prob, base))
    except KeyError:
        raise ValueError("Bad case value in lnprob_case")
