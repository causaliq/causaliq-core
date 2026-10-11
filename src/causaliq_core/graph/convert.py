#
#   Graph conversion operations
#

from typing import Dict, List, Optional, Set, Tuple, Union

from pandas import DataFrame

from .dag import DAG
from .enums import EdgeType
from .pdag import PDAG


def _process_incoming_to_x(
    x: str,
    y: str,
    edges: List[Tuple[str, str, str]],
    parents: Dict[str, List[str]],
) -> Tuple[List[Tuple[str, str, str]], bool]:
    """
    Compel the edges required by steps 5 to 7 of Chickering (1995).

    :param str x: first node of the unknown edge under consideration
    :param str y: second node of the unknown edge under consideration
    :param edges: ordered edge triples, unknown edges marked "?"
    :param parents: parents of each node {node: [parents]}

    :returns: updated edges and whether the algorithm should restart
    """
    if not len(parents[x]):  # nothing to do if no parents of x
        return (edges, False)

    for w in parents[x]:  # Step 5 - Loop over inbound edges to x ...
        if (w, "->", x) in edges:  # ... that are compelled
            if w not in parents[y]:
                # Step 6 - if w is not a parent of y then label all
                #          inbound to y as compelled and exit
                return (
                    [(e[0], "->", e[2]) if e[2] == y else e for e in edges],
                    True,
                )
            # Step 7 - if w is parent of y then compel w -> y
            edges = [
                (e[0], "->", e[2]) if e[0] == w and e[2] == y else e
                for e in edges
            ]
    return (edges, False)


def _process_incoming_to_y(
    x: str,
    y: str,
    edges: List[Tuple[str, str, str]],
    parents: Dict[str, List[str]],
) -> List[Tuple[str, str, str]]:
    """
    Compel the edges required by steps 8 and 9 of Chickering (1995).

    :param str x: first node of the unknown edge under consideration
    :param str y: second node of the unknown edge under consideration
    :param edges: ordered edge triples, unknown edges marked "?"
    :param parents: parents of each node {node: [parents]}

    :returns: updated edge triples
    """
    # Step 8 - if there is an edge z -> y where z is not x or a parent
    #          of x, label x -> y all unknown inbound to y as compelled

    for z in parents[y]:
        if z != x and z not in parents[x]:
            return [
                (
                    (e[0], "->", e[2])
                    if (e[0] == x or e[1] == "?") and e[2] == y
                    else e
                )
                for e in edges
            ]

    # Step 9 - set x -> y and unknown inbound arcs to y to reversible

    return [
        ((e[0], "-", e[2]) if (e[0] == x or e[1] == "?") and e[2] == y else e)
        for e in edges
    ]


def _orient_unknown_edges(
    edges: List[Tuple[str, str, str]], parents: Dict[str, List[str]]
) -> List[Tuple[str, str, str]]:
    """
    Orientate every unknown edge, following Chickering (1995).

    :param edges: ordered edge triples, unknown edges marked "?"
    :param parents: parents of each node {node: [parents]}

    :returns: edge triples with no unknown edges remaining
    """
    while any([t == "?" for (_, t, _) in edges]):  # 3 some edges unknown
        for i, (x, _, y) in enumerate(edges):
            if edges[i][1] != "?":  # 4 dynamic lowest unknown edge
                continue

            edges, restart = _process_incoming_to_x(x, y, edges, parents)
            if restart:  # 5-7 incoming to x
                break

            edges = _process_incoming_to_y(  # 8&9, edges incoming to y
                x, y, edges, parents
            )

    return edges


def dag_to_pdag(dag: DAG) -> PDAG:
    """
    Generates PDAG representing equivalence class DAG belongs to.

    Uses the algorithm in "A Transformational Characterization of
    Equivalent Bayesian Network Structures", Chickering, 1995. Step
    numbers in comments refer to algorithm step numbers in paper.

    Args:
        dag: DAG whose PDAG is required.

    Raises:
        TypeError: if dag is not of type DAG

    Returns:
        PDAG for equivalence class that dag belongs to
    """

    if not isinstance(dag, DAG):
        raise TypeError("dag arg in dag_to_pdag not a DAG")

    nodes = [n for n in dag.ordered_nodes()]  # nodes in topological order
    parents = {
        n: [
            p
            for p in nodes
            if p  # node parents in topo order
            in (dag.parents[n] if n in dag.parents else [])
        ]
        for n in nodes
    }
    edges = [(p, "?", n) for n in reversed(nodes) for p in parents[n]]
    edges = [e for e in reversed(edges)]
    # print('dag_to_pdag: reversed ordered edges are: {}'.format(edges))

    edges = _orient_unknown_edges(edges, parents)  # 3-9 unknown edges

    return PDAG(dag.nodes, edges)


def pdag_to_cpdag(pdag: PDAG) -> Union[PDAG, None]:
    """
    Generates a completed PDAG (CPDAG) from supplied PDAG

    :param PDAG pdag: PDAG to be completed

    :raises TypeError: if pdag is not of type PDAG
    :raises ValueError: if pdag is non-extendable

    :returns PDAG/None: CPDAG corresponding to pdag
    """
    dag = extend_pdag(pdag)
    return dag_to_pdag(dag) if dag is not None else None


def is_cpdag(pdag: PDAG) -> bool:
    """
    Whether the PDAG is a Completed PDAG (CPDAG)

    :param PDAG pdag: PDAG to check

    :raises ValueError: if PDAG is not extendable

    :returns bool: True if CPDAG, otherwise False
    """
    result = pdag_to_cpdag(pdag)
    return result == pdag if result is not None else False


def _adjacency_set(n: str, s: PDAG, pc: bool = True) -> Set[str]:
    """
    Return the nodes adjacent to a node through directed or undirected edges.

    :param str n: node whose adjacency set is required
    :param PDAG s: graph in which adjacency is tested
    :param bool pc: if True, include directed as well as undirected edges

    :returns set: nodes adjacent to n through the requested edge types
    """
    et = (
        [EdgeType.UNDIRECTED, EdgeType.DIRECTED]
        if pc
        else [EdgeType.UNDIRECTED]
    )
    return {
        e[0] if e[1] == n else e[1]
        for e, t in s.edges.items()
        if (e[0] == n or e[1] == n) and t in et
    }


def _is_sink_node(x: str, s: PDAG) -> bool:
    """
    Whether a node is a sink, i.e. has no outbound directed edges.

    :param str x: node to test
    :param PDAG s: graph containing the node

    :returns bool: True if x has no outbound directed edges
    """
    return not any(
        [e[0] == x and t == EdgeType.DIRECTED for e, t in s.edges.items()]
    )


def _is_valid_x_candidate(x: str, s: PDAG) -> bool:
    """
    Whether a node satisfies condition b of the Dor-Tarsi algorithm.

    All nodes, y, attached to x by an undirected edge must be adjacent to
    all neighbours of x.

    :param str x: node to test
    :param PDAG s: graph containing the node

    :returns bool: True if condition b holds for x
    """
    adj_x = _adjacency_set(x, s)
    for y in _adjacency_set(x, s, False):
        if not (adj_x - {y}).issubset(_adjacency_set(y, s) - {x}):
            return False
    return True


def _valid_x(s: PDAG) -> Union[str, None]:
    """
    Return a node of s satisfying conditions a and b, or None.

    Condition a is that the node is a sink, condition b that all nodes
    attached to it by an undirected edge are adjacent to all of its
    neighbours.

    :param PDAG s: graph in which to search for an eligible node

    :returns str/None: eligible node or None if there is none
    """
    for x in s.nodes:
        if not _is_sink_node(x, s):
            continue
        if _is_valid_x_candidate(x, s):
            return x
    return None


def _orient_edges_into_node(
    dag_edges: Dict[Tuple[str, str], EdgeType],
    pdag_edges: Dict[Tuple[str, str], EdgeType],
    x: str,
) -> List[Tuple[str, str, str]]:
    """
    Return edge triples with every edge incident to x oriented into x.

    Edges that are not in the PDAG are left with their existing
    orientation.

    :param dag_edges: edges of the DAG being constructed
    :param pdag_edges: edges remaining in the PDAG
    :param str x: node into which incident edges are oriented

    :returns: updated edge triples
    """
    return [
        (
            (e[0] if e[1] == x else e[1], "->", x)
            if (e[0] == x or e[1] == x) and e in pdag_edges
            else (e[0], "->" if t == EdgeType.DIRECTED else "-", e[1])
        )
        for e, t in dag_edges.items()
    ]


def _remove_node(
    nodes: List[str], edges: Dict[Tuple[str, str], EdgeType], x: str
) -> Tuple[List[str], List[Tuple[str, str, str]]]:
    """
    Return the nodes and edge triples left after removing a node.

    :param nodes: nodes of the graph
    :param edges: edges of the graph {pair: EdgeType}
    :param str x: node to remove

    :returns: remaining nodes and remaining edge triples
    """
    remaining = list(set(nodes) - {x})
    triples = [
        (e[0], "->" if t == EdgeType.DIRECTED else "-", e[1])
        for e, t in edges.items()
        if e[0] != x and e[1] != x
    ]
    return remaining, triples


def extend_pdag(pdag: PDAG) -> DAG:
    """
    Generates a DAG which extends a PDAG (i.e. is a member of the
    equivalence class the PDAG represents)

    Uses the algorithm in "A simple algorithm to construct a
    consistent extension of a partially oriented graph",
    Dor and Tarsi, 1992

    :param PDAG pdag: PDAG from which DAG derived

    :raises TypeError: if pdag is not of type PDAG
    :raises ValueError: if pdag is not extendable (example is
                        an undirected square PDAG)

    :returns DAG: extension of pdag
    """

    if not isinstance(pdag, PDAG):
        raise TypeError("pdag arg in extend_pdag not a PDAG")

    if pdag.is_directed:  # if already directed just return as DAG class
        return DAG(pdag.nodes, [(e[0], "->", e[1]) for e in pdag.edges.keys()])

    # Clone pdag as dag. The DAG will be created in "dag", matching G' in
    # paper, "pdag" will act as graph A in the paper

    dag = PDAG(
        pdag.nodes,
        [
            (e[0], "->" if t == EdgeType.DIRECTED else "-", e[1])
            for e, t in pdag.edges.items()
        ],
    )

    while len(pdag.edges):
        x = _valid_x(pdag)
        # print("Processing eligible node is {}".format(x))
        if x is None:  # means pdag is not extendable
            raise ValueError("pdag is not extendable")

        # orientate all edges incident to x in pdag to go into x in dag

        edges = _orient_edges_into_node(dag.edges, pdag.edges, x)
        dag = PDAG(dag.nodes, edges)
        # print('DAG is:\n{}'.format(dag))

        # remove x and its incident edges from pdag for next iteration

        nodes, edges = _remove_node(pdag.nodes, pdag.edges, x)
        pdag = PDAG(nodes, edges)
        # print('PDAG is:\n{}\n\n'.format(pdag))

    # return dag as DAG object

    return DAG(
        dag.nodes,
        [
            (e[0], "->" if t == EdgeType.DIRECTED else "?", e[1])
            for e, t in dag.edges.items()
        ],
    )


def dict_to_adjmat(
    columns: Optional[Dict[str, List[int]]] = None,
) -> DataFrame:
    """
    Create an adjacency matrix with specified entries.

    :param dict columns: data for matrix specified by column

    :raises TypeError: if arg types incorrect
    :raises ValueError: if values specified are invalid

    :returns DataFrame: the adjacency matrix
    """
    if (
        columns is None
        or not isinstance(columns, dict)
        or not all([isinstance(c, list) for c in columns.values()])
        or not all([isinstance(e, int) for c in columns.values() for e in c])
    ):
        raise TypeError("dict_to_adjmat called with bad arg type")

    if not all([len(c) == len(columns) for c in columns.values()]):
        raise ValueError("some columns wrong length for dict_to_adjmat")

    valid = [e.value[0] for e in EdgeType]  # valid edge integer codes
    if not all([e in valid for c in columns.values() for e in c]):
        raise ValueError("invalid integer values for dict_to_adjmat")

    adjmat_df: DataFrame = DataFrame(columns, dtype="int8")
    adjmat_df[""] = list(adjmat_df.columns)
    result: DataFrame = adjmat_df.set_index("")
    return result


# Export public interface
__all__ = [
    "dag_to_pdag",
    "pdag_to_cpdag",
    "extend_pdag",
    "is_cpdag",
    "dict_to_adjmat",
]
