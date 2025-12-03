"""
Distribution classes for Bayesian Network nodes.

This module contains conditional node distribution (CND) implementations
including the abstract base class and concrete implementations like
Linear Gaussian distributions.
"""

from .cnd import CND
from .lingauss import LinGauss

__all__ = [
    "CND",
    "LinGauss",
]
