"""Filter expression evaluation utilities.

Provides safe evaluation of Python-like filter expressions against metadata
dictionaries using the simpleeval library. This enables filtering cache
entries by metadata values without the security risks of eval().

The ``random(count, seed)`` function enables reproducible random
selection within filter expressions.  When used as
``VAR in random(count, seed)``, it selects *count* values from the
distinct population of VAR across all entries, using the
hardware-stable RandomIntegers sequence.

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

import re
from typing import Any, Dict, FrozenSet, List, Sequence, Set, Tuple

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


def random_set(values: Sequence[Any], count: int, seed: int) -> FrozenSet[Any]:
    """Select *count* values from a population using stable RNG.

    Uses the hardware-stable ``RandomIntegers`` sequence so that
    the same *seed* always produces the same selection regardless
    of platform.

    Args:
        values: Population of values to select from.
        count: Number of values to select.
        seed: Seed for reproducible selection (0-999).

    Returns:
        Frozen set of selected values.

    Raises:
        ValueError: If count exceeds the number of distinct
            values, or if the population is empty.

    Example:
        >>> sorted(random_set(range(10), 3, 0))
        [2, 4, 6]
    """
    from causaliq_core.utils.random import RandomIntegers

    sorted_vals = sorted(set(values), key=str)
    n = len(sorted_vals)
    if n < 1:
        raise ValueError("random() requires a non-empty population")
    if count > n:
        raise ValueError(
            f"random() requires at least {count} distinct " f"values, got {n}"
        )
    indices = list(RandomIntegers(n, subsample=seed))
    return frozenset(sorted_vals[i] for i in indices[:count])


def _random_placeholder(*args: Any) -> None:
    """Placeholder that raises a helpful error."""
    raise FilterExpressionError(
        "random() in filter expressions requires "
        "pre-resolution via resolve_random_calls(). "
        "Use filter_entries() or call "
        "resolve_random_calls() before evaluate_filter()."
    )


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
    "random": _random_placeholder,
}

# Regex to find VAR in random(count, seed) patterns
_RANDOM_PATTERN = re.compile(
    r"(\w+)\s+in\s+(random\s*\(\s*(\d+)\s*,\s*(\d+)\s*\))"
)


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


def _evaluate_expression(
    evaluator: EvalWithCompoundTypes, expression: str
) -> Any:
    """Evaluate an expression, mapping failures to filter exceptions.

    Args:
        evaluator: Configured evaluator instance.
        expression: Filter expression string.

    Returns:
        Raw result of evaluating the expression.

    Raises:
        FilterSyntaxError: If the expression has invalid syntax.
        FilterExpressionError: If evaluation fails (e.g. undefined variable).
    """
    try:
        return evaluator.eval(expression)
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

    # Coerce result to boolean
    return bool(_evaluate_expression(evaluator, expression))


def _is_user_variable(name: str) -> bool:
    """Return whether a name is a user variable rather than a builtin.

    Args:
        name: Name referenced in the expression.

    Returns:
        bool: Whether the name is a user variable.
    """
    if name in ("True", "False", "None"):
        return False
    return name not in _ALLOWED_FUNCTIONS


def _filter_variables(expression: str) -> Set[str]:
    """Return the user variable names referenced in an expression.

    Args:
        expression: Filter expression string.

    Returns:
        Set of variable names used in the expression.

    Raises:
        FilterSyntaxError: If expression has invalid syntax.
    """
    import ast

    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as e:
        raise FilterSyntaxError(f"Invalid filter syntax: {e}") from e

    variables: Set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and _is_user_variable(node.id):
            variables.add(node.id)

    return variables


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

    return _filter_variables(expression)


def _select_random_values(
    all_metadata: List[Dict[str, Any]], var_name: str, count: int, seed: int
) -> FrozenSet[Any]:
    """Select *count* distinct values of a variable using stable RNG.

    Args:
        all_metadata: Flat metadata dictionaries from all entries.
        var_name: Variable whose distinct values are sampled.
        count: Number of values to select.
        seed: Seed for reproducible selection.

    Returns:
        Frozen set of selected values.

    Raises:
        FilterExpressionError: If fewer distinct values exist than requested.
    """
    # Collect distinct non-None values of var_name.
    values = {
        meta[var_name]
        for meta in all_metadata
        if var_name in meta and meta[var_name] is not None
    }

    try:
        return random_set(list(values), count, seed)
    except ValueError as e:
        raise FilterExpressionError(
            f"random() for variable '{var_name}': {e}"
        ) from e


def _substitute_random_call(expression: str, match: Any, name: str) -> str:
    """Return expression with one ``random(...)`` call replaced by a name.

    Args:
        expression: Expression to rewrite.
        match: Match object for the ``VAR in random(...)`` pattern.
        name: Replacement variable name.

    Returns:
        Rewritten expression.
    """
    call_start = match.start(2)
    call_end = match.end(2)
    return expression[:call_start] + name + expression[call_end:]


def resolve_random_calls(
    expression: str,
    all_metadata: List[Dict[str, Any]],
) -> Tuple[str, Dict[str, Any]]:
    """Pre-resolve ``random()`` calls in a filter expression.

    Finds ``VAR in random(count, seed)`` patterns, collects the
    distinct values of *VAR* across *all_metadata*, selects
    *count* of them using the hardware-stable ``RandomIntegers``
    sequence, and returns a rewritten expression plus a dictionary
    of pre-computed sets to inject as extra names during
    evaluation.

    Args:
        expression: Filter expression, possibly containing
            ``random(count, seed)`` calls.
        all_metadata: List of flat metadata dictionaries from
            all entries in the population.

    Returns:
        Tuple of *(resolved_expression, extra_names)*.
        *extra_names* should be merged into each entry's metadata
        when calling :func:`evaluate_filter`.

    Raises:
        FilterExpressionError: If fewer distinct values exist
            than the requested count.

    Example:
        >>> metas = [{"seed": i} for i in range(25)]
        >>> expr, names = resolve_random_calls(
        ...     "seed in random(10, 0)", metas
        ... )
        >>> len(names)
        1
    """
    matches = list(_RANDOM_PATTERN.finditer(expression))
    if not matches:
        return expression, {}

    extra_names: Dict[str, Any] = {}
    new_expr = expression

    # Process in reverse order to preserve string positions.
    for i, m in enumerate(reversed(matches)):
        var_name = m.group(1)
        count = int(m.group(3))
        seed = int(m.group(4))
        selected = _select_random_values(all_metadata, var_name, count, seed)

        # Inject as extra name, replace random(...) in expression.
        name = f"_random_{i}"
        extra_names[name] = selected
        new_expr = _substitute_random_call(new_expr, m, name)

    return new_expr, extra_names


def _entry_matches(
    entry: Dict[str, Any],
    metadata_key: str,
    expression: str,
    extra_names: Dict[str, Any],
) -> bool:
    """Return whether a single entry satisfies the filter expression.

    Args:
        entry: Cache entry dictionary.
        metadata_key: Key in entry dict containing metadata.
        expression: Pre-resolved filter expression.
        extra_names: Pre-computed names merged into the metadata.

    Returns:
        bool: Whether the entry matches the filter.
    """
    metadata = entry.get(metadata_key, {})
    if not isinstance(metadata, dict):
        return False
    try:
        merged = {**metadata, **extra_names}
        return evaluate_filter(expression, merged)
    except FilterExpressionError:
        # Entry missing required fields - skip it
        return False


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

    # Pre-resolve random() calls if present
    all_meta = [
        entry.get(metadata_key, {})
        for entry in entries
        if isinstance(entry.get(metadata_key), dict)
    ]
    resolved_expr, extra_names = resolve_random_calls(expression, all_meta)

    result = []
    for entry in entries:
        if _entry_matches(entry, metadata_key, resolved_expr, extra_names):
            result.append(entry)

    return result
