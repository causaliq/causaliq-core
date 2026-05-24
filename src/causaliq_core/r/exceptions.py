"""Typed Python exceptions for the R integration layer."""


class RNotAvailableError(RuntimeError):
    """Raised when R or rpy2 is not available."""


class RPackageNotAvailableError(RuntimeError):
    """Raised when a required R package is not installed."""


class RRuntimeError(RuntimeError):
    """Raised when an R function call fails at runtime."""
