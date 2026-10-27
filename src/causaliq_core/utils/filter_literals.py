"""Relax bare literals in filter expressions.

A filter expression uses Python syntax, where a bare name is a field
reference. Workflow authors naturally write a comparison value without
quotes, for example ``status == ok``. This module rewrites bare names on
the right-hand side of comparisons, and inside membership collections,
into string literals. Names reserved for workflow parameters and names
already used as a field reference on the left-hand side are kept as
references, so ``description == 'description'`` is only needed when the
text collides with such a name.
"""

import ast
from typing import Iterable, Set

from causaliq_core.utils.filter_expr import FilterSyntaxError

_BUILTIN_NAMES = frozenset(
    {
        "True",
        "False",
        "None",
        "len",
        "str",
        "int",
        "float",
        "bool",
        "abs",
        "min",
        "max",
        "random",
    }
)


class _LiteralRelaxer(ast.NodeTransformer):
    """Replace bare comparison values with string literals."""

    def __init__(self, reserved: Set[str]) -> None:
        """Store the names that must stay field references."""
        self._reserved = reserved

    def visit_Compare(self, node: ast.Compare) -> ast.AST:
        """Rewrite the values on the right-hand side of a comparison."""
        self.generic_visit(node)
        node.comparators = [
            (
                comparator
                if isinstance(operator, (ast.Is, ast.IsNot))
                else self._as_literal(comparator)
            )
            for operator, comparator in zip(node.ops, node.comparators)
        ]
        return node

    def _as_literal(self, node: ast.expr) -> ast.expr:
        """Return a string constant for a bare value name."""
        if isinstance(node, ast.Name):
            if node.id in self._reserved or node.id in _BUILTIN_NAMES:
                return node
            return ast.Constant(value=node.id)
        if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
            node.elts = [self._as_literal(item) for item in node.elts]
        return node


def _left_hand_names(tree: ast.AST) -> Set[str]:
    """Return every bare name used as the left side of a comparison."""
    return {
        node.left.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Compare) and isinstance(node.left, ast.Name)
    }


def relax_filter_literals(
    expression: str, reserved_names: Iterable[str] = ()
) -> str:
    """Return a filter expression with bare values quoted as strings.

    Bare names on the right-hand side of a comparison, and inside a
    membership list, are converted to string literals. A name is kept as
    a reference when it appears in ``reserved_names`` or when it is used
    as the left side of a comparison anywhere in the expression. Dotted
    names, constants and function calls are never changed.

    Args:
        expression: Filter expression using Python syntax.
        reserved_names: Parameter or field names that must stay
            references.

    Returns:
        The rewritten expression. An already-quoted expression is
        returned with equivalent formatting.

    Raises:
        FilterSyntaxError: If the expression cannot be parsed.
        TypeError: If the expression is not a string.

    Example:
        >>> relax_filter_literals("status == ok")
        "status == 'ok'"
        >>> relax_filter_literals("description == description")
        "description == 'description'"
    """
    if not isinstance(expression, str):
        raise TypeError(
            f"Filter expression must be a string, "
            f"got {type(expression).__name__}"
        )
    if not expression.strip():
        return expression
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise FilterSyntaxError(f"Invalid filter syntax: {exc}") from exc
    reserved = set(reserved_names) | _left_hand_names(tree)
    relaxed = _LiteralRelaxer(reserved).visit(tree)
    ast.fix_missing_locations(relaxed)
    return ast.unparse(relaxed)
