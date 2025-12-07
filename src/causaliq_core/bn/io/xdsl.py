#   Read and write XDSL format BN definition files produced by GenIe

from math import prod
from re import compile, findall, sub
from typing import Any, Dict, Optional, Tuple
from xml.dom import minidom

from causaliq_core.bn import CPT, LinGauss, NodeValueCombinations
from causaliq_core.utils import FileFormatError, is_valid_path

XDSL_HDR = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    + "<!-- This network was created in BNBENCH -->\n"
    + '<smile version="1.0" id="bnbench" numsamples="100000" '
    + 'discsamples="100000">\n    <nodes>\n'
)
NODES_END = "    </nodes>\n"
XDSL_END = "</smile>\n"

STARTS_WITH_LETTER = compile(r"^[a-zA-Z].*$")

GENIE_HDR = (
    "    <extensions>\n"
    + '        <genie version="1.0" app="GeNIe 4.0.1922.0 ACADEMIC" '
    + 'name="Network1">\n'
)
GENIE_NODE = (
    '            <node id="{0:}">\n'
    + "                <name>{0:}</name>\n"
    + '                <interior color="e5f6f7" />\n'
    + '                <outline color="000080" />\n'
    + '                <font color="000000" name="Arial"'
    + ' size="{1:}" />\n'
    + "                <position>{2:} {3:} {4:} {5:}</position>\n"
    + "            </node>\n"
)
GENIE_END = "        </genie>\n    </extensions>\n"

# Patterns relating to equation definition

EQN_VALID_CHARS = compile(r"^[a-zA-Z0-9\=\(\)\_\.\,\*\+\-]+$")
EQN_NORMAL = r"[\+\-]?Normal\(.+?\,.+?\)"
EQN_SPLIT_TERMS = compile(r"[\+|\-]")


def _to_float(string: str) -> Optional[float]:
    """Convert string to float.

    Args:
        string: String to convert to a float.

    Returns:
        Float value or None if conversion impossible.
    """
    try:
        x = float(string)
    except ValueError:
        x = None
    return x


def _parse_equation_normal(string: str) -> Tuple[float, float]:
    """Parse the string defining normal function.

    Args:
        string: Normal definition as textual string.

    Returns:
        Tuple of floats: (mean, sd).
    """

    # Determine whether negative or postive, remove leading sign

    if string[0] in {"-", "+"}:
        positive = True if string[0] == "+" else False
        string = string[1:]
    else:
        positive = True

    # Extract & check mean and SD, converting to floats

    mean, sd = tuple(string.replace("Normal(", "").replace(")", "").split(","))
    mean = _to_float(mean)  # type: ignore[assignment]
    sd = _to_float(sd)  # type: ignore[assignment]
    if mean is None or sd is None or sd < 0.0:  # type: ignore[operator]
        raise FileFormatError("xdsl.read() invalid Normal args")
    mean = mean if positive is True else -1.0 * mean  # type: ignore[operator]

    return (mean, sd)  # type: ignore[return-value]


def _parse_equation_coeffs(string: Any, parents: Any) -> Any:
    """Parse and validate the parent coefficients in the equation.

    Args:
        string: Text containing coefficients.
        parents: Parent variables (defined in parents elem).

    Returns:
        Dict of parent coefficients, {p1: coeff1, ...}.

    Raises:
        FileFormatError: If definition is invalid.
    """
    coeffs: Dict[Any, Any] = {}
    if len(string) == 0 and len(parents) == 0:
        pass  # coeffs already empty

    if len(string) > 0 and len(parents) > 0:

        # split string at "+" and "-" symbols

        terms = EQN_SPLIT_TERMS.split(string)
        terms = terms[1:] if terms[0] == "" else terms

        for term in terms:
            pos = string.find(term)
            sign = 1.0 if pos == 0 or string[pos - 1] == "+" else -1.0
            term = term.split("*")
            if len(term) == 1:
                parent = term[0]
                coeff = 1.0
            elif len(term) == 2:
                coeff = _to_float(term[0])  # type: ignore[assignment]
                if coeff is None:
                    parent = term[0]  # type: ignore[unreachable]
                    coeff = _to_float(term[1])
                else:
                    parent = term[1]
            else:
                coeff = None
            if coeff is None or parent in coeffs:
                raise FileFormatError("xdsl.read() bad coeffs")
            coeffs.update({parent: coeff * sign})

    elif len(string) > 0 or len(parents) > 0:
        coeffs = None  # type: ignore[assignment]

    if set(coeffs) != set(parents):
        raise FileFormatError("xdsl.read() bad coeffs")

    return coeffs


def _parse_equation_definition(
    definition: Any, node: Any, parents: Any
) -> Any:
    """Parse and validate the textual equation definition.

    Only supports Linear Gaussian equations.

    Args:
        definition: Textual equation definition.
        node: DAG node name.
        parents: Parents as defined in parents element.

    Returns:
        Parsed equation, {'mean': mean, 'sd': sd, 'coeffs': {p1: c1, ...}}.

    Raises:
        FileFormatError: If definition is invalid.
    """
    if not EQN_VALID_CHARS.match(definition):
        raise FileFormatError("xdsl.read() equation invalid chars")

    # remove spaces, check just one equals sign with something either side

    definition = definition.replace(" ", "").split("=")
    if (
        len(definition) != 2
        or len(definition[0]) == 0
        or len(definition[1]) == 0
    ):
        raise FileFormatError("xdsl.read() - missing/misplaced/repeated =")

    # LHS should match node name

    if node != definition[0]:
        raise FileFormatError(
            "xdsl.read() - node / LHS mismatch {}/{}".format(
                node, definition[0]
            )
        )

    # rhs shouldn't start with +, or end with + or -

    rhs = definition[1]
    if rhs[0] == "+" or rhs[-1] in {"-", "+"}:
        raise FileFormatError("xdsl.read() - illegal leading/trailing +/-")

    # Look for, and extract single Normal(...) term in rhs

    normal = findall(EQN_NORMAL, rhs)
    if len(normal) != 1:
        raise FileFormatError("xdsl.read() - no/multiple Normals")
    rhs = rhs.replace(normal[0], "")
    mean, sd = _parse_equation_normal(normal[0])
    coeffs = _parse_equation_coeffs(rhs, parents)

    return {"mean": mean, "sd": sd, "coeffs": coeffs}


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

    #   Process <parents>

    if len(parents):
        try:
            parents = parents[0].firstChild.nodeValue.split()
        except AttributeError:
            raise FileFormatError("xdsl.read() <parents> has no values")

    #   Process <definition>

    try:
        definition = definition[0].firstChild.nodeValue
    except AttributeError:
        raise FileFormatError("xdsl.read() <definition> is empty")

    # parse the equation definition and return it

    return {node: _parse_equation_definition(definition, node, parents)}


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

    children = [n for n in elem.childNodes if n.nodeType == 1]
    states = [n for n in elem.childNodes if n.nodeName == "state"]
    parents = [n for n in elem.childNodes if n.nodeName == "parents"]
    probs = [n for n in elem.childNodes if n.nodeName == "probabilities"]
    if (
        len(states) < 2
        or len(parents) > 1
        or len(probs) != 1
        or len(states) + len(parents) + len(probs) != len(children)
    ):
        raise FileFormatError("xdsl.read() <cpt> has missing/invalid children")

    #   Process <state>s (i.e. values) node can take

    values = []
    for state in states:
        id = state.attributes.getNamedItem("id")
        if id is None:
            raise FileFormatError("xdsl.read() <state> has no id")
        values.append(id.nodeValue)

    #   Process <parents>

    if len(parents):
        try:
            parents = parents[0].firstChild.nodeValue.split()
        except AttributeError:
            raise FileFormatError("xdsl.read() <parents> has no values")

    #   Process <probabilities>

    if len(probs):
        try:
            probs = [float(v) for v in probs[0].firstChild.nodeValue.split()]
        except AttributeError:
            raise FileFormatError("xdsl.read() <probabilities> has no values")

    return {node: {"values": values, "parents": parents, "probs": probs}}


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

    def _pmf(node: Any, pmf: Any) -> Any:  # check & optionally adjust pmf
        total = sum(pmf.values())
        if total < 0.999999 or total > 1.000001:
            if correct:
                print("\n*** Correcting probabilities for " + node)
                pmf = {v: pr / total for v, pr in pmf.items()}
            else:
                raise ValueError("xdsl.read() sum " + node + " probs not 1")
        return pmf

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

        elif len(parents[node]):  # categorical non-orphan node
            num_pvs = prod([len(values[p]) for p in parents[node]])
            if num_pvs * len(values[node]) != len(probs[node]):
                raise FileFormatError("xdsl.read() wrong # of probabilities")
            pvs = {p: values[p] for p in parents[node]}
            num_values = len(values[node])
            offset = 0
            cpt = []
            for pv in NodeValueCombinations(pvs, False):
                pr = probs[node][offset:offset + num_values]  # fmt: skip
                pmf = {v: pr for v, pr in zip(values[node], pr)}
                cpt.append((pv, _pmf(node, pmf)))
                offset += num_values
            cnds.update({node: (CPT, cpt)})

        else:  # categorical orphan node
            if len(probs[node]) != len(values[node]):
                raise FileFormatError("xdsl.read() wrong # of probabilities")
            pmf = {v: pr for v, pr in zip(values[node], probs[node])}
            cpt = _pmf(node, pmf)
            cnds.update({node: (CPT, cpt)})

    edges = [(p, "->", n) for n in parents.keys() for p in parents[n]]
    return (list(xdsl_data), edges, cnds)


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

    with open(path) as xml_file:
        try:
            xdsl = minidom.parse(xml_file)
        except Exception:
            raise FileFormatError("xdsl.read() invalid XML")

    # Check root element is <smile>

    root = xdsl.documentElement
    if root.tagName != "smile":  # type: ignore[union-attr]
        raise FileFormatError("xdsl.read() invalid root")

    # Check top levels under root are <nodes> and, optionally, <extensions>

    child_nodes = root.childNodes  # type: ignore[union-attr]
    topLevel = [n for n in child_nodes if n.nodeType == 1]
    if (
        len(topLevel) < 1
        or len(topLevel) > 2
        or topLevel[0].nodeName != "nodes"
        or (len(topLevel) == 2 and topLevel[1].nodeName != "extensions")
    ):
        raise FileFormatError("xdsl.read() invalid top level")

    # Process all the child elements of <nodes> to get node info

    xdsl_data = {}
    for child in topLevel[0].childNodes:
        if child.nodeType != 1:
            continue

        if child.nodeName == "cpt":
            xdsl_data.update(_process_cpt_element(child))

        elif child.nodeName == "equation":
            xdsl_data.update(_process_equation_element(child))

        else:
            raise FileFormatError("xdsl.read() bad elem under <nodes>")

    #   Return BN data in format required by BN constructor

    return _bn_data(xdsl_data, correct)


def genie_str(string: Any, prefix: Any) -> Any:
    """Cleanses string so that it conforms to Genie requirements.

    Cleanses string so that it conforms to Genie requirements for a
    node name or value.

    Args:
        string: Node name or value to cleanse.
        prefix: Prefix to use if doesn't start with letter.

    Returns:
        Cleansed string that meets Genie requirements.
    """
    cleansed = string if STARTS_WITH_LETTER.match(string) else prefix + string

    return sub("[^0-9a-zA-Z]+", "_", cleansed)


def write_genie_extension(f: Any, partial_order: Any) -> Any:
    """Writes the XDSL Genie extension XML.

    Writes the XDSL Genie extension XML which defines node placement
    on the visual drawing of the network.

    Args:
        f: Handle to write text.
        partial_order: Of (list of) nodes in each partial order
                       group of nodes.
    """
    f.write(GENIE_HDR)
    top = 0
    for group in partial_order:
        top += 100
        left = 20
        for node in group:
            f.write(
                GENIE_NODE.format(
                    genie_str(node, "N"), 8, left, top, left + 80, top + 40
                )
            )
            left += 100
    f.write(GENIE_END)


def _write_cpt(
    f: Any, node: Any, cpt: Any, node_values: Any, genie: Any
) -> Any:
    """Write a <cpt> element.

    Args:
        f: Handle for writing to file.
        node: Node that CPT relates to.
        cpt: CPT to represent in XDSL.
        node_values: Node values for categorical nodes.
        genie: Whether to be in Genie format.
    """

    # <cpt> opening element

    f.write('        <cpt id="{}">\n'.format(node))

    # node values (states)

    for value in node_values[node]:
        f.write(
            '            <state id="{}" />\n'.format(
                genie_str(value, "S") if genie is True else value
            )
        )

    # process CPT to get parents name if any, and then probabilities
    # associated with each parent value combo and node value.
    # Take care that values always processed in alphabetical order.

    probs = []
    if cpt.has_parents:
        parents = " ".join([p for p in cpt.parents()])
        f.write("            <parents>" + parents + "</parents>\n")
        pvs = {p: node_values[p] for p in cpt.parents()}
        for pvc in NodeValueCombinations(pvs):
            probs.extend([cpt.cdist(pvc)[v] for v in node_values[node]])
    else:
        probs.extend([cpt.cdist()[v] for v in node_values[node]])
    f.write(
        "            <probabilities>{}</probabilities>\n".format(
            " ".join(["{}".format(p) for p in probs])
        )
    )

    f.write("        </cpt>\n")


def _write_equation(f: Any, node: Any, lingauss: Any, genie: Any) -> Any:
    """Write <equation> element representing linear gaussian.

    Args:
        f: Handle for writing to file.
        node: Node that CPT relates to.
        lingauss: Linear Gaussian to represent in XDSL.
        genie: Whether to be in Genie format.
    """
    f.write(
        '        <equation id="{}">\n'.format(
            genie_str(node, "N") if genie is True else node
        )
    )

    if lingauss.coeffs != {}:
        parents = " ".join([p for p in lingauss.coeffs])
        f.write("            <parents>" + parents + "</parents>\n")

    f.write(
        "            <definition>{}={}</definition>\n".format(node, lingauss)
    )

    f.write("        </equation>\n")


def write(bn: Any, filename: Any, genie: Any = False) -> Any:
    """Write Bayesian Network to disk file in XDSL format.

    Ensure everything written out with node name and values ordered
    alphabetically.

    Args:
        bn: Bayesian Network to dump to file.
        filename: Name of file to write.
        genie: Whether files needs to be read by Genie - if so,
               will ensure all node and state names start with
               a letter.

    Raises:
        TypeError: Bad argument types.
        FileNotFoundError: If file location nonexistent.
    """
    if bn.__class__.__name__ != "BN" or not isinstance(filename, str):
        raise TypeError("xdsl.write() bad arg type")

    # Ensure all node names are Genie-friendly if required

    if genie is True:
        name_map = {n: genie_str(n, "N") for n in bn.dag.nodes}
        bn.rename(name_map)

    # node_values has each node's allowed values ordered alphabetically.

    node_values = {
        n: bn.cnds[n].node_values()
        for n in bn.dag.nodes
        if isinstance(bn.cnds[n], CPT)
    }
    parents = {
        n: bn.dag.parents[n] if n in bn.dag.parents else []
        for n in bn.dag.nodes
    }
    partial_order = bn.dag.partial_order(parents)
    order = [n for g in partial_order for n in g]

    with open(filename, "w", encoding="utf-8") as f:

        f.write(XDSL_HDR)

        for node in order:
            if isinstance(bn.cnds[node], CPT):
                _write_cpt(f, node, bn.cnds[node], node_values, genie)
            else:
                _write_equation(f, node, bn.cnds[node], genie)

        f.write(NODES_END)

        if genie is True:
            write_genie_extension(f, partial_order)

        f.write(XDSL_END)
