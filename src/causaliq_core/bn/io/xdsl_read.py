#
#   Reads Bayesian Networks from XDSL format BN definition files
#

from math import prod
from typing import Any, Dict, List, Tuple
from xml.dom import minidom

from causaliq_core.utils import FileFormatError, is_valid_path

from ..dist import CPT, LinGauss, NodeValueCombinations
from .xdsl_common import _parse_equation_definition


def _process_equation_element(elem: Any) -> Any:
    """Process a <equation> element from the XDSL file.

    Args:
        elem: XDSL element (<equation>) describing a node.

    Returns:
        Tuple: (node, coeffs, mean, sd) of node information.

    Raises:
        FileFormatError: If not a correctly formed <equation> element.
    """

    #   Check <cpt> elem has id attribute which is BN node name

    id = elem.attributes.getNamedItem("id")
    if id is None:
        raise FileFormatError("xdsl.read() <equation> has no id attribute")
    node = id.nodeValue

    # <equation> should have one <definition>, and optionally one parents node

    parents = [n for n in elem.childNodes if n.nodeName == "parents"]
    definition = [n for n in elem.childNodes if n.nodeName == "definition"]
    if len(definition) != 1 or len(parents) > 1:
        raise FileFormatError("xdsl.read() <equation> bad children")

    #   Process <parents> and <definition>

    parent_names = _element_parents(parents)
    text = _element_definition(definition)

    # parse the equation definition and return it

    return {node: _parse_equation_definition(text, node, parent_names)}


def _element_parents(parents: Any) -> List[Any]:
    """Return the parent names held in a <parents> element.

    Args:
        parents: List of <parents> elements (empty if no element).

    Returns:
        List of parent node names.

    Raises:
        FileFormatError: If the element holds no values.
    """
    if not len(parents):
        return []
    try:
        return parents[0].firstChild.nodeValue.split()  # type: ignore
    except AttributeError:
        raise FileFormatError("xdsl.read() <parents> has no values")


def _element_definition(definition: Any) -> Any:
    """Return the text held in a <definition> element.

    Args:
        definition: List holding the <definition> element.

    Returns:
        Textual equation definition.

    Raises:
        FileFormatError: If the element holds no values.
    """
    try:
        return definition[0].firstChild.nodeValue
    except AttributeError:
        raise FileFormatError("xdsl.read() <definition> is empty")


def _process_cpt_element(elem: Any) -> Any:
    """Process a <cpt> element from the XDSL file.

    Args:
        elem: XDSL element (<cpt>) describing a node.

    Returns:
        Tuple: (node, values, parents, probs) of node information.

    Raises:
        FileFormatError: If not a correctly formed <cpt> element.
    """

    #   Check <cpt> elem has id attribute which is BN node name

    id = elem.attributes.getNamedItem("id")
    if id is None:
        raise FileFormatError("xdsl.read() <cpt> has no id attribute")
    node = id.nodeValue

    # <cpt> must have 2 or more <state> children, optionally a <parents> child,
    # and finally a <probabilities> child

    children, states, parents, probs = _cpt_element_children(elem)
    _check_cpt_element_children(states, parents, probs, children)

    #   Process <state>s (i.e. values) node can take, <parents> and
    #   <probabilities>

    values = _cpt_element_states(states)
    parent_names = _element_parents(parents)
    probabilities = _cpt_element_probs(probs)

    return {
        node: {
            "values": values,
            "parents": parent_names,
            "probs": probabilities,
        }
    }


def _cpt_element_children(elem: Any) -> Tuple[Any, Any, Any, Any]:
    """Return the children of a <cpt> element grouped by element name.

    Args:
        elem: XDSL element (<cpt>) describing a node.

    Returns:
        Tuple of (all element children, <state> children, <parents>
        children, <probabilities> children).
    """
    children = [n for n in elem.childNodes if n.nodeType == 1]
    states = [n for n in elem.childNodes if n.nodeName == "state"]
    parents = [n for n in elem.childNodes if n.nodeName == "parents"]
    probs = [n for n in elem.childNodes if n.nodeName == "probabilities"]
    return children, states, parents, probs


def _check_cpt_element_children(
    states: Any, parents: Any, probs: Any, children: Any
) -> None:
    """Check a <cpt> element has a valid set of children.

    Args:
        states: <state> children of the element.
        parents: <parents> children of the element.
        probs: <probabilities> children of the element.
        children: All element children.

    Raises:
        FileFormatError: If children are missing or invalid.
    """
    if (
        len(states) < 2
        or len(parents) > 1
        or len(probs) != 1
        or len(states) + len(parents) + len(probs) != len(children)
    ):
        raise FileFormatError("xdsl.read() <cpt> has missing/invalid children")


def _cpt_element_states(states: Any) -> List[Any]:
    """Return the values (states) defined by a <cpt> element.

    Args:
        states: <state> children of the <cpt> element.

    Returns:
        List of node values.

    Raises:
        FileFormatError: If a <state> element has no id attribute.
    """
    values = []
    for state in states:
        id = state.attributes.getNamedItem("id")
        if id is None:
            raise FileFormatError("xdsl.read() <state> has no id")
        values.append(id.nodeValue)
    return values


def _cpt_element_probs(probs: Any) -> List[Any]:
    """Return the probabilities held in a <probabilities> element.

    Args:
        probs: List holding the single <probabilities> element of a <cpt>
            element.

    Returns:
        List of probability floats.

    Raises:
        FileFormatError: If the element holds no values.
    """
    try:
        text = probs[0].firstChild.nodeValue
    except AttributeError:
        raise FileFormatError("xdsl.read() <probabilities> has no values")
    return [float(v) for v in text.split()]


def _bn_data(xdsl_data: Any, correct: Any) -> Any:
    """Return BN (DAG and CNDs) data in format required by BN constructor.

    Args:
        xdsl_data: BN data in format extracted from XDSL, that is
                   {node: {parents, values, probs}} for CPTs
                   {node: {mean, sd, coeffs}} for Linear Gaussian.
        correct: Whether to correct sets of PMF probabilities that
                 don't sum to 1.

    Returns:
        Tuple of BN data in required format: ([nodes], [(n1, '->', n2)], CNDs).

    Raises:
        FileFormatError: If incorrect <probabilities> detected.
        ValueError: If PMF probabilities don't sum to 1.
    """

    # Collect parent, value and CPT data for all categorical nodes

    parents = {n: d["parents"] for n, d in xdsl_data.items() if "parents" in d}
    values = {n: d["values"] for n, d in xdsl_data.items() if "values" in d}
    probs = {n: d["probs"] for n, d in xdsl_data.items() if "probs" in d}

    # Mixed continuous / categorical networks not supported

    if len(probs) != len(xdsl_data) and len(probs) != 0:
        raise FileFormatError("xdsl.read() mixed networks unsupported")

    # Loop over XDSL data for each node extracting CPT/LinGauss info

    cnds = {}
    for node, data in xdsl_data.items():

        if "coeffs" in data:  # Linear Gaussian node
            cnds.update({node: (LinGauss, data)})
            parents.update({node: list(data["coeffs"])})

        else:  # categorical node
            cpt = _categorical_cnd(node, parents, values, probs, correct)
            cnds.update({node: (CPT, cpt)})

    edges = [(p, "->", n) for n in parents.keys() for p in parents[n]]
    return (list(xdsl_data), edges, cnds)


def _categorical_cnd(
    node: Any, parents: Any, values: Any, probs: Any, correct: Any
) -> Any:
    """Return the CPT data of a categorical node.

    Args:
        node: Node whose CPT data is required.
        parents: Parents of every node {node: [parents]}.
        values: Values of every node {node: [values]}.
        probs: Probabilities of every node {node: [probs]}.
        correct: Whether to correct PMF probabilities that don't sum to 1.

    Returns:
        CPT data: a PMF for an orphan node, otherwise a list of
        (parental values, PMF) entries.

    Raises:
        FileFormatError: If the number of probabilities is wrong.
        ValueError: If a PMF does not sum to 1.
    """
    if not len(parents[node]):  # categorical orphan node
        if len(probs[node]) != len(values[node]):
            raise FileFormatError("xdsl.read() wrong # of probabilities")
        pmf = {v: pr for v, pr in zip(values[node], probs[node])}
        return _check_pmf(node, pmf, correct)

    return _parented_cnd(node, parents[node], values, probs, correct)


def _parented_cnd(
    node: Any, node_parents: Any, values: Any, probs: Any, correct: Any
) -> List[Any]:
    """Return the CPT entries of a categorical node with parents.

    Args:
        node: Node whose CPT entries are required.
        node_parents: Parents of the node.
        values: Values of every node {node: [values]}.
        probs: Probabilities of every node {node: [probs]}.
        correct: Whether to correct PMF probabilities that don't sum to 1.

    Returns:
        List of (parental values, PMF) entries.

    Raises:
        FileFormatError: If the number of probabilities is wrong.
        ValueError: If a PMF does not sum to 1.
    """
    num_pvs = prod([len(values[p]) for p in node_parents])
    if num_pvs * len(values[node]) != len(probs[node]):
        raise FileFormatError("xdsl.read() wrong # of probabilities")

    pvs = {p: values[p] for p in node_parents}
    num_values = len(values[node])
    offset = 0
    cpt = []
    for pv in NodeValueCombinations(pvs, False):
        pr = probs[node][offset : offset + num_values]
        pmf = {v: pr for v, pr in zip(values[node], pr)}
        cpt.append((pv, _check_pmf(node, pmf, correct)))
        offset += num_values
    return cpt


def _check_pmf(node: Any, pmf: Any, correct: Any) -> Any:
    """Check and, optionally, adjust a PMF so that it sums to 1.

    Args:
        node: Node whose PMF is being checked.
        pmf: PMF to check, {value: prob}.
        correct: Whether to correct the PMF if it does not sum to 1.

    Returns:
        The PMF, corrected if requested.

    Raises:
        ValueError: If the PMF does not sum to 1 and correction is off.
    """
    total = sum(pmf.values())
    if total < 0.999999 or total > 1.000001:
        if not correct:
            raise ValueError("xdsl.read() sum " + node + " probs not 1")
        print("\n*** Correcting probabilities for " + node)
        pmf = {v: pr / total for v, pr in pmf.items()}
    return pmf


def read(path: Any, correct: Any = False) -> Any:
    """Reads in a BN from a XDSL format BN specification file.

    Args:
        path: Full path name of file.
        correct: Whether to correct sets of PMF probabilities that
                 don't sum to 1.

    Returns:
        Tuple: nodes, edges, CND_specs.

    Raises:
        TypeError: If path is not a string.
        ValueError: If PMF probabilities don't sum to 1 (adjust=False).
        FileNotFoundError: If file does not exist.
        FileFormatError: If file contents not valid.
    """
    if not isinstance(path, str) or not isinstance(correct, bool):
        raise TypeError("xdsl.read() bad arg type")

    is_valid_path(path)

    # Check root element is <smile>

    root = _parse_xdsl_root(path)

    # Check top levels under root are <nodes> and, optionally, <extensions>

    top_level = _xdsl_top_level(root)

    # Process all the child elements of <nodes> to get node info

    xdsl_data = _xdsl_node_data(top_level[0])

    #   Return BN data in format required by BN constructor

    return _bn_data(xdsl_data, correct)


def _parse_xdsl_root(path: str) -> Any:
    """Return the root element of an XDSL format file.

    Args:
        path: Full path name of file.

    Returns:
        Root element of the document.

    Raises:
        FileFormatError: If the file is not valid XML with a <smile> root.
    """
    xdsl = _parse_xdsl_document(path)

    root = xdsl.documentElement
    if root.tagName != "smile":  # type: ignore[union-attr]
        raise FileFormatError("xdsl.read() invalid root")
    return root


def _parse_xdsl_document(path: str) -> Any:
    """Return the XML document parsed from an XDSL format file.

    Args:
        path: Full path name of file.

    Returns:
        Parsed XML document.

    Raises:
        FileFormatError: If the file is not valid XML.
    """
    with open(path) as xml_file:
        return _parse_xml_file(xml_file)


def _parse_xml_file(xml_file: Any) -> Any:
    """Return the XML document parsed from an open XDSL format file.

    Args:
        xml_file: Open XDSL format file.

    Returns:
        Parsed XML document.

    Raises:
        FileFormatError: If the file contents are not valid XML.
    """
    try:
        return minidom.parse(xml_file)
    except Exception:
        raise FileFormatError("xdsl.read() invalid XML")


def _xdsl_top_level(root: Any) -> List[Any]:
    """Return the elements directly under the <smile> root element.

    Args:
        root: Root element of the document.

    Returns:
        Top level elements of the document.

    Raises:
        FileFormatError: If the top level elements are invalid.
    """
    child_nodes = root.childNodes
    top_level = [n for n in child_nodes if n.nodeType == 1]
    if (
        len(top_level) < 1
        or len(top_level) > 2
        or top_level[0].nodeName != "nodes"
        or (len(top_level) == 2 and top_level[1].nodeName != "extensions")
    ):
        raise FileFormatError("xdsl.read() invalid top level")
    return top_level


def _xdsl_node_data(nodes_elem: Any) -> Dict[Any, Any]:
    """Return the node data described by a <nodes> element.

    Args:
        nodes_elem: <nodes> element of the XDSL file.

    Returns:
        Node data: {node: {parents, values, probs}} for CPTs or
        {node: {mean, sd, coeffs}} for Linear Gaussian equations.

    Raises:
        FileFormatError: If an unexpected element is found under <nodes>.
    """
    xdsl_data: Dict[Any, Any] = {}
    for child in nodes_elem.childNodes:
        if child.nodeType != 1:
            continue
        _add_node_data(xdsl_data, child)
    return xdsl_data


def _add_node_data(xdsl_data: Dict[Any, Any], child: Any) -> None:
    """Add the data described by one element under <nodes>.

    Args:
        xdsl_data: Node data accumulated so far, updated in place.
        child: Element under <nodes>.

    Raises:
        FileFormatError: If the element is neither <cpt> nor <equation>.
    """
    if child.nodeName == "cpt":
        xdsl_data.update(_process_cpt_element(child))
        return
    if child.nodeName == "equation":
        xdsl_data.update(_process_equation_element(child))
        return
    raise FileFormatError("xdsl.read() bad elem under <nodes>")
