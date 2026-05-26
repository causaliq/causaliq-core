"""Typed Python exceptions for the Java integration layer."""


class JavaNotAvailableError(RuntimeError):
    """Raised when Java is not available."""


class JavaRuntimeError(RuntimeError):
    """Raised when a Java command fails at runtime."""
