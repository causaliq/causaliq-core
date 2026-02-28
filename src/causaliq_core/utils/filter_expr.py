"""Filter expression evaluation utilities.

Provides safe evaluation of Python-like filter expressions against metadata
dictionaries using the simpleeval library. This enables filtering cache
entries by metadata values without the security risks of eval().

Example:
    >>> from causaliq_core.utils.filter_expr import evaluate_filter
    >>> metadata = {"network": "asia", "sample_size": 1000}
    >>> evaluate_filter("network == 'asia'", metadata)
    True
    >>> evaluate_filter("sample_size > 500", metadata)
    True
    >>> evaluate_filter("network in ['asia', 'alarm']", metadata)
    True
"""

from typing import Any, Dict, List, Set

from simpleeval import (  # type: ignore[import-untyped]
    EvalWithCompoundTypes,
    InvalidExpression,
    NameNotDefined,
)


class FilterExpressionError(Exception):
    """Raised when filter expression evaluation fails."""

    pass


class FilterSyntaxError(FilterExpressionError):
    """Raised when filter expression has invalid syntax."""

    pass


# Allowed names in filter expressions (empty - all names come from metadata)
_ALLOWED_NAMES: Dict[str, Any] = {}

# Allowed functions in filter expressions
_ALLOWED_FUNCTIONS: Dict[str, Any] = {
    "len": len,
    "str": str,
    "int": int,
    "float": float,
    "bool": bool,
    "abs": abs,
    "min": min,
    "max": max,
}


def _create_evaluator(metadata: Dict[str, Any]) -> EvalWithCompoundTypes:
    """Create a simpleeval evaluator with metadata as names.

    Args:
        metadata: Metadata dictionary to use as variable names.

    Returns:
        Configured evaluator instance.
    """
    evaluator = EvalWithCompoundTypes()
    evaluator.names = dict(metadata)
    evaluator.functions = _ALLOWED_FUNCTIONS.copy()
    return evaluator


def validate_filter(expression: str) -> None:
    """Validate filter expression syntax without evaluating.

    Checks that the expression can be parsed. Does not verify that variable
    names exist - that is checked during evaluation.

    Args:
        expression: Filter expression string.

    Raises:
        FilterSyntaxError: If expression has invalid syntax.
        TypeError: If expression is not a string.

    Example:
        >>> validate_filter("network == 'asia'")  # OK
        >>> validate_filter("network ==")  # Raises FilterSyntaxError
    """
    if not isinstance(expression, str):
        raise TypeError(
            f"Filter expression must be a string, "
            f"got {type(expression).__name__}"
        )

    if not expression.strip():
        raise FilterSyntaxError("Filter expression cannot be empty")

    # Create evaluator with dummy metadata to test parsing
    evaluator = _create_evaluator({"_dummy": True})

    try:
        # Parse expression to check syntax (will fail on undefined names,
        # but that's OK - we just want to check syntax)
        evaluator.parse(expression)
    except SyntaxError as e:
        raise FilterSyntaxError(f"Invalid filter syntax: {e}") from e
    except InvalidExpression as e:
        raise FilterSyntaxError(f"Invalid filter expression: {e}") from e


def evaluate_filter(expression: str, metadata: Dict[str, Any]) -> bool:
    """Evaluate filter expression against metadata dictionary.

    The expression uses Python syntax with metadata field names as variables.
    Supports comparison operators (==, !=, >, <, >=, <=), boolean operators
    (and, or, not), membership testing (in), and parentheses for grouping.

    Args:
        expression: Filter expression string.
        metadata: Metadata dictionary with field values.

    Returns:
        True if metadata matches the filter expression, False otherwise.

    Raises:
        FilterSyntaxError: If expression has invalid syntax.
        FilterExpressionError: If evaluation fails (e.g., undefined variable).
        TypeError: If expression is not a string or metadata is not a dict.

    Examples:
        >>> metadata = {"network": "asia", "sample_size": 1000, "status": "ok"}
        >>> evaluate_filter("network == 'asia'", metadata)
        True
        >>> evaluate_filter("sample_size > 500 and status == 'ok'", metadata)
        True
        >>> evaluate_filter("network in ['asia', 'alarm']", metadata)
        True
        >>> evaluate_filter("not network == 'sports'", metadata)
        True
    """
    if not isinstance(expression, str):
        raise TypeError(
            f"Filter expression must be a string, "
            f"got {type(expression).__name__}"
        )
    if not isinstance(metadata, dict):
        raise TypeError(
            f"Metadata must be a dictionary, " f"got {type(metadata).__name__}"
        )

    if not expression.strip():
        raise FilterSyntaxError("Filter expression cannot be empty")

    evaluator = _create_evaluator(metadata)

    try:
        result = evaluator.eval(expression)
    except SyntaxError as e:
        raise FilterSyntaxError(f"Invalid filter syntax: {e}") from e
    except NameNotDefined as e:
        # Must be caught before InvalidExpression (NameNotDefined is subclass)
        raise FilterExpressionError(
            f"Undefined variable in filter: {e}"
        ) from e
    except InvalidExpression as e:
        raise FilterSyntaxError(f"Invalid filter expression: {e}") from e
    except NameError as e:
        raise FilterExpressionError(
            f"Undefined variable in filter: {e}"
        ) from e
    except Exception as e:
        raise FilterExpressionError(f"Filter evaluation failed: {e}") from e

    # Coerce result to boolean
    return bool(result)


def get_filter_variables(expression: str) -> Set[str]:
    """Extract variable names used in a filter expression.

    Parses the expression and returns the set of variable names referenced.
    Useful for validating that required metadata fields are present.

    Args:
        expression: Filter expression string.

    Returns:
        Set of variable names used in the expression.

    Raises:
        FilterSyntaxError: If expression has invalid syntax.
        TypeError: If expression is not a string.

    Example:
        >>> get_filter_variables("network == 'asia' and sample_size > 500")
        {'network', 'sample_size'}
    """
    if not isinstance(expression, str):
        raise TypeError(
            f"Filter expression must be a string, "
            f"got {type(expression).__name__}"
        )

    if not expression.strip():
        raise FilterSyntaxError("Filter expression cannot be empty")

    import ast

    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as e:
        raise FilterSyntaxError(f"Invalid filter syntax: {e}") from e

    variables: Set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            # Exclude built-in constants and allowed functions
            if (
                node.id not in ("True", "False", "None")
                and node.id not in _ALLOWED_FUNCTIONS
            ):
                variables.add(node.id)

    return variables


def filter_entries(
    entries: List[Dict[str, Any]],
    expression: str,
    metadata_key: str = "metadata",
) -> List[Dict[str, Any]]:
    """Filter a list of entries by metadata expression.

    Convenience function to filter a list of cache entry dictionaries
    by a filter expression applied to each entry's metadata.

    Args:
        entries: List of entry dictionaries.
        expression: Filter expression string.
        metadata_key: Key in entry dict containing metadata.

    Returns:
        List of entries where metadata matches the filter.

    Raises:
        FilterSyntaxError: If expression has invalid syntax.
        FilterExpressionError: If evaluation fails.
        TypeError: If arguments have invalid types.

    Example:
        >>> entries = [
        ...     {"metadata": {"network": "asia", "size": 100}},
        ...     {"metadata": {"network": "alarm", "size": 200}},
        ... ]
        >>> filter_entries(entries, "network == 'asia'")
        [{'metadata': {'network': 'asia', 'size': 100}}]
    """
    if not isinstance(entries, list):
        raise TypeError(
            f"Entries must be a list, got {type(entries).__name__}"
        )

    # Validate expression once before filtering
    validate_filter(expression)

    result = []
    for entry in entries:
        metadata = entry.get(metadata_key, {})
        if isinstance(metadata, dict):
            try:
                if evaluate_filter(expression, metadata):
                    result.append(entry)
            except FilterExpressionError:
                # Entry missing required fields - skip it
                pass

    return result
