"""R integration layer for CausalIQ Core.

Provides rpy2-based session management, data conversion utilities, and
bnlearn graph utilities used by downstream CausalIQ repositories.
"""

from causaliq_core.r.availability import (
    is_r_available,
    is_r_package_available,
)
from causaliq_core.r.bnlearn import (
    bnlearn_compare,
    bnlearn_cpdag,
    bnlearn_import,
)
from causaliq_core.r.convert import data_to_r_dataframe, r_arcs_to_edges
from causaliq_core.r.exceptions import (
    RNotAvailableError,
    RPackageNotAvailableError,
    RRuntimeError,
)
from causaliq_core.r.session import get_robjects, import_r_package

__all__ = [
    "is_r_available",
    "is_r_package_available",
    "get_robjects",
    "import_r_package",
    "r_arcs_to_edges",
    "data_to_r_dataframe",
    "bnlearn_cpdag",
    "bnlearn_compare",
    "bnlearn_import",
    "RNotAvailableError",
    "RPackageNotAvailableError",
    "RRuntimeError",
]
