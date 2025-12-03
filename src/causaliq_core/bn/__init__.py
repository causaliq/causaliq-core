"""
Bayesian Networks module for CausalIQ Core.

This module provides classes and utilities for working with Bayesian Networks,
including conditional node distributions and their implementations.
"""

from .dist import LinGauss

__all__ = [
    "LinGauss",
]
