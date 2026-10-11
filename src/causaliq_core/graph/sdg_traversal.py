"""
Traversal helpers for simple dependency graphs.

The helpers operate on plain node, parent and edge data so that they do not
need to depend on the graph classes themselves.
"""

from typing import Dict, Iterable, List, Optional, Set, Tuple, Union


def _prepare_parents(
    parents: Dict[str, List[str]],
    nodes: Optional[Union[List[str], Set[str]]],
    new_arc: Optional[Tuple[str, str]],
) -> Dict[str, Set[str]]:
    """Return a mutable parents mapping with any new arc applied.

    Args:
        parents: Parents of each node {node: [parents]}.
        nodes: Optional complete list of nodes.
        new_arc: A new arc (n1, n2) to apply, reversing any opposing arc.

    Returns:
        Parents of each node as sets of parent names.
    """
    parents_copy = {n: set(p) for n, p in parents.items()}
    if nodes is not None:
        parents_copy.update({n: set() for n in nodes if n not in parents})
    if new_arc is not None:
        parents_copy[new_arc[0]] = parents_copy[new_arc[0]] - {new_arc[1]}
        parents_copy[new_arc[1]] = parents_copy[new_arc[1]] | {new_arc[0]}
    return parents_copy


def _remove_roots(parents_copy: Dict[str, Set[str]], roots: Set[str]) -> None:
    """Remove a layer of root nodes from a parents mapping.

    Args:
        parents_copy: Parents of each node as sets, updated in place.
        roots: Root nodes forming the current layer.
    """
    for root in roots:
        parents_copy.pop(root)
    for node in list(parents_copy.keys()):
        parents_copy[node].difference_update(roots)


def _order_layers(
    parents_copy: Dict[str, Set[str]],
) -> Optional[List[Set[str]]]:
    """Return the partial topological layers of a parents mapping.

    Args:
        parents_copy: Parents of each node as sets, consumed in place.

    Returns:
        List of layers of root nodes, or None when the graph is cyclic.
    """
    order: List[Set[str]] = []
    while len(parents_copy):
        roots = {n for n in parents_copy if not parents_copy[n]}
        if not len(roots):
            return None
        order.append(roots)
        _remove_roots(parents_copy, roots)
    return order


def layout_partial_order(
    parents: Dict[str, List[str]],
    nodes: Optional[Union[List[str], Set[str]]] = None,
    new_arc: Optional[Tuple[str, str]] = None,
) -> Optional[List[Set[str]]]:
    """Return partial topological ordering for the directed part of a graph.

    The graph is specified by a list of parents for each node.

    Args:
        parents: Parents of each node {node: [parents]}.
        nodes: Optional complete list of nodes including parentless ones
            for use if the parents argument doesn't include them already.
        new_arc: A new arc (n1, n2) to be added before order is evaluated.
            If the opposing arc is implied in parents then it is removed so
            that arc reversal is also supported. This argument facilitates
            seeing whether an arc addition or reversal would create a
            cycle.

    Returns:
        Nodes in a partial topological order as list of sets or None if
        there is no ordering which means the graph is cyclic.
    """
    if not isinstance(parents, dict) or (
        nodes is not None
        and not isinstance(nodes, list)
        and not isinstance(nodes, set)
    ):
        raise TypeError("DAG.partial_order bad arg type")

    parents_copy = _prepare_parents(parents, nodes, new_arc)

    return _order_layers(parents_copy)


def undirected_edge_pairs(
    edges: Iterable[Tuple[str, str]],
) -> Set[Tuple[str, str]]:
    """Return undirected node pairs with the smaller node name first.

    Args:
        edges: Keys of a graph's edge dictionary.

    Returns:
        Set of node pairs in canonical order.
    """
    return {(e[0], e[1]) if e[1] > e[0] else (e[1], e[0]) for e in edges}


def _crosses_boundary(edge: Tuple[str, str], c_nodes: Set[str]) -> bool:
    """Return whether exactly one end of an edge is inside a node set.

    Args:
        edge: Candidate edge.
        c_nodes: Nodes already in the node set.

    Returns:
        bool: Whether the edge crosses the boundary of the node set.
    """
    inside = (edge[0] in c_nodes, edge[1] in c_nodes)
    return inside[0] != inside[1]


def _extends_tree(
    edge: Tuple[str, str],
    tree: Set[Union[Tuple[str, str], Tuple[str, None]]],
    t_nodes: Set[str],
) -> bool:
    """Return whether an edge extends a tree across its boundary.

    Args:
        edge: Candidate edge.
        tree: Edges already in the tree.
        t_nodes: Nodes already in the tree.

    Returns:
        bool: Whether the edge joins the tree to a new node.
    """
    if edge in tree:
        return False
    return _crosses_boundary(edge, t_nodes)


def _extend_tree_pass(
    tree: Set[Union[Tuple[str, str], Tuple[str, None]]],
    t_nodes: Set[str],
    edges: Set[Tuple[str, str]],
) -> Tuple[Set[Union[Tuple[str, str], Tuple[str, None]]], Set[str], bool]:
    """Extend a tree by a single pass over the candidate edges.

    Args:
        tree: Edges already in the tree.
        t_nodes: Nodes already in the tree.
        edges: Candidate edges for the tree.

    Returns:
        Tuple of (edges in the tree, nodes in the tree, whether it grew).
    """
    grew = False
    for edge in sorted(edges):  # Sort for deterministic iteration
        if _extends_tree(edge, tree, t_nodes):
            t_nodes = t_nodes | {edge[0], edge[1]}
            tree = tree | {edge}
            grew = True

    return tree, t_nodes, grew


def grow_undirected_tree(
    first_edge: Tuple[str, str], edges: Set[Tuple[str, str]]
) -> Tuple[Set[Union[Tuple[str, str], Tuple[str, None]]], Set[str]]:
    """Return the tree grown from an edge through connected edges.

    Args:
        first_edge: Edge to start the tree from.
        edges: Candidate edges for the tree.

    Returns:
        Tuple of (edges in the tree, nodes in the tree).
    """
    tree: Set[Union[Tuple[str, str], Tuple[str, None]]] = {first_edge}
    t_nodes = {first_edge[0], first_edge[1]}

    # Keep adding connected edges until no more can be added
    growing = True
    while growing:
        tree, t_nodes, growing = _extend_tree_pass(tree, t_nodes, edges)

    return tree, t_nodes


def _absorb_crossing_edges(
    c_nodes: Set[str], edges: Set[Tuple[str, str]]
) -> Tuple[Set[str], bool]:
    """Absorb, in one pass, the edges that cross a component boundary.

    Args:
        c_nodes: Nodes already in the component.
        edges: Undirected edges of the graph skeleton.

    Returns:
        Tuple of (nodes in the component, whether the component grew).
    """
    grew = False
    for edge in edges:  # look for edges across component boundary
        if _crosses_boundary(edge, c_nodes):
            c_nodes = c_nodes | {edge[0], edge[1]}
            grew = True

    return c_nodes, grew


def grow_component(c_nodes: Set[str], edges: Set[Tuple[str, str]]) -> Set[str]:
    """Return every node reachable from a starting component.

    Args:
        c_nodes: Nodes already in the component.
        edges: Undirected edges of the graph skeleton.

    Returns:
        Set of nodes in the component.
    """
    growing = True
    while growing:
        c_nodes, growing = _absorb_crossing_edges(c_nodes, edges)

    return c_nodes
