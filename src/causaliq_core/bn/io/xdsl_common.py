#
#   Constants and equation helpers for XDSL format BN files
#
#   XDSL is the XML format for Bayesian networks produced by GeNIe. This
#   module holds the format constants, the equation patterns and the
#   equation parsing helpers shared by the XDSL reader and writer.
#

from re import compile, findall
from typing import Any, Dict, List, Optional, Tuple

from causaliq_core.utils import FileFormatError

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
    if len(string) == 0 and len(parents) == 0:
        return {}  # coeffs already empty

    coeffs: Any = None
    if len(string) > 0 and len(parents) > 0:
        coeffs = _parse_equation_terms(string)

    if set(coeffs) != set(parents):
        raise FileFormatError("xdsl.read() bad coeffs")

    return coeffs


def _parse_equation_terms(string: Any) -> Dict[Any, Any]:
    """Return the parent coefficients named in an equation.

    Args:
        string: Text containing the terms of the equation.

    Returns:
        Dict of parent coefficients, {p1: coeff1, ...}.

    Raises:
        FileFormatError: If a term repeats a parent or has a bad coefficient.
    """
    # split string at "+" and "-" symbols
    terms = EQN_SPLIT_TERMS.split(string)
    terms = terms[1:] if terms[0] == "" else terms

    coeffs: Dict[Any, Any] = {}
    for term in terms:
        parent, coeff = _parse_equation_term(string, term)
        if coeff is None or parent in coeffs:
            raise FileFormatError("xdsl.read() bad coeffs")
        coeffs.update({parent: coeff})
    return coeffs


def _parse_equation_term(string: Any, term: Any) -> Tuple[Any, Any]:
    """Return the parent and signed coefficient of one equation term.

    Args:
        string: Text containing the terms of the equation.
        term: Single term of the equation.

    Returns:
        Tuple of (parent name, coefficient), the coefficient being None if
        the term is malformed.
    """
    pos = string.find(term)
    sign = 1.0 if pos == 0 or string[pos - 1] == "+" else -1.0
    parts = term.split("*")
    if len(parts) == 1:
        parent, coeff = parts[0], 1.0
    elif len(parts) == 2:
        parent, coeff = _parse_equation_factor(parts)
    else:
        parent, coeff = parts[0], None
    return parent, None if coeff is None else coeff * sign


def _parse_equation_factor(parts: Any) -> Tuple[Any, Any]:
    """Return the parent and coefficient of a term with a "*" symbol.

    Args:
        parts: Term split at "*" symbols.

    Returns:
        Tuple of (parent name, coefficient), the coefficient being None if
        neither part is a number.
    """
    coeff = _to_float(parts[0])
    if coeff is None:
        return parts[0], _to_float(parts[1])
    return parts[1], coeff


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
    _check_equation_sides(definition, node)

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


def _check_equation_sides(sides: List[Any], node: Any) -> None:
    """Check an equation definition has a valid left and right hand side.

    Args:
        sides: Equation definition split at "=" symbols.
        node: DAG node name the equation defines.

    Raises:
        FileFormatError: If the "=" is missing, misplaced or repeated, or
            the left hand side is not the node name.
    """
    if len(sides) != 2 or len(sides[0]) == 0 or len(sides[1]) == 0:
        raise FileFormatError("xdsl.read() - missing/misplaced/repeated =")

    # LHS should match node name
    if node != sides[0]:
        raise FileFormatError(
            "xdsl.read() - node / LHS mismatch {}/{}".format(node, sides[0])
        )
