#
#   Common I/O functions for Bayesian Network file formats
#

from typing import TYPE_CHECKING

from ...graph import DAG
from . import dsc, xdsl

if TYPE_CHECKING:
    from ..bn import BN


def read_bn(path: str, correct: bool = False) -> "BN":
    """Read a Bayesian Network from a file, automatically detecting format.

    Supports:
    - .dsc files (DSC format)
    - .xdsl files (XDSL format)

    Args:
        path: Path to DSC/XDSL file.
        correct: Whether to correct probabilities that do not sum to 1
            (XDSL files only).

    Returns:
        Bayesian Network specified in file.

    Raises:
        TypeError: If path is not a string.
        ValueError: If path suffix is not "dsc" or "xdsl".
        FileNotFoundError: If file does not exist.
        FileFormatError: If file contents not valid.
    """
    from ..bn import BN  # Import here to avoid circular import

    if not isinstance(path, str) or not isinstance(correct, bool):
        raise TypeError("BN.read() bad arg type")

    suffix = path.split(".")[-1]
    if suffix.lower() == "dsc":
        nodes, edges, cnd_specs = dsc.read(path)
    elif suffix.lower() == "xdsl":
        nodes, edges, cnd_specs = xdsl.read(path, correct)
    else:
        raise ValueError("BN.read() invalid file suffix")

    return BN(DAG(nodes, edges), cnd_specs)


def write_bn(bn: "BN", path: str) -> None:
    """Write BN to a DSC or XDSL format file.

    Args:
        bn: Bayesian Network to write.
        path: Path to file.

    Raises:
        ValueError: If suffix not ".dsc" or ".xdsl".
        FileNotFoundError: If file location nonexistent.
    """
    suffix = path.split(".")[-1].lower()
    if suffix == "dsc":
        dsc.write(bn, path)
    elif suffix == "xdsl":
        xdsl.write(bn, path, genie=True)
    else:
        raise ValueError("Unknown file format: {}".format(suffix))
