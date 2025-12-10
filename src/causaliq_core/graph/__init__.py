"""
Graph-related enums and utilities for CausalIQ Core.
"""

# Import io module and common functions
from . import io

# Import conversion functions
from .convert import dag_to_pdag, extend_pdag, is_cpdag, pdag_to_cpdag
from .dag import DAG, NotDAGError

# Import enums
from .enums import EdgeMark, EdgeType
from .pdag import PDAG, NotPDAGError

# Import graph classes - moved to top to fix E402
from .sdg import SDG

# Supported BayeSys versions for graph comparison semantics
BAYESYS_VERSIONS = ["v1.3", "v1.5+"]


# Export public interface
__all__ = [
    "EdgeType",
    "EdgeMark",
    "SDG",
    "PDAG",
    "NotPDAGError",
    "DAG",
    "NotDAGError",
    "dag_to_pdag",
    "pdag_to_cpdag",
    "extend_pdag",
    "is_cpdag",
    "BAYESYS_VERSIONS",
    "io",
]
