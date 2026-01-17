"""Odoo domain to human-readable expression converters.

This module provides functions to convert Odoo domain expressions to either
human-readable pseudocode or Python-style expressions.

The converters follow Odoo domain conventions (compatible with Odoo 16+):
- '&' and '|' are BINARY operators (take exactly 2 operands)
- '!' is a UNARY operator (takes exactly 1 operand)
- Implicit '&' between adjacent conditions without explicit operators
"""

from enum import Enum, auto
from typing import Any

from .parser import DynamicRef
from .humanizer import (
    humanize_field,
    humanize_dynamic_ref,
    get_system_field_label,
    to_readable_text,
)


class OutputFormat(Enum):
    """Output format for domain conversion."""
    PSEUDOCODE = auto()
    PYTHON = auto()


class MalformedDomainError(Exception):
    """Raised when a domain is structurally invalid."""
    pass


# Comparison operators for pseudocode (human-readable words)
PSEUDOCODE_COMPARISON_OPERATORS = {
    '=': 'equals',
    '!=': "doesn't equal",
    '>': 'is greater than',
    '<': 'is less than',
    '>=': 'is at least',
    '<=': 'is at most',
    'in': 'is in',
    'not in': 'is not in',
    'like': 'is like',
    'ilike': 'is like (case-insensitive)',
    '=like': 'matches pattern',
    '=ilike': 'matches pattern (case-insensitive)',
    'child_of': 'is child of',
    'parent_of': 'is parent of',
}

# Comparison operators for Python (Python syntax)
PYTHON_COMPARISON_OPERATORS = {
    '=': '==',
    '!=': '!=',
    '>': '>',
    '<': '<',
    '>=': '>=',
    '<=': '<=',
    'in': 'in',
    'not in': 'not in',
    'like': 'like',  # Odoo-specific, keep as-is
    'ilike': 'ilike',  # Odoo-specific, keep as-is
    '=like': '=like',  # Odoo-specific, keep as-is
    '=ilike': '=ilike',  # Odoo-specific, keep as-is
    'child_of': 'child_of',  # Odoo-specific, keep as-is
    'parent_of': 'parent_of',  # Odoo-specific, keep as-is
}

# Logical operators for pseudocode (uppercase)
PSEUDOCODE_LOGICAL_OPERATORS = {
    '&': 'AND',
    '|': 'OR',
    '!': 'NOT',
}

# Logical operators for Python (lowercase)
PYTHON_LOGICAL_OPERATORS = {
    '&': 'and',
    '|': 'or',
    '!': 'not',
}

LOGICAL_OPERATOR_SET = {'&', '|', '!'}


def _is_tautology(condition: tuple) -> str | None:
    """Check if condition is a tautology pattern.

    Returns:
        - "always_true" for (1, '=', 1) patterns
        - "always_false" for (0, '=', 1) patterns
        - None for regular conditions
    """
    if len(condition) < 3:
        return None

    field, operator, value = condition[:3]
    if operator != '=':
        return None

    # Normalize to comparable values (handle both int and str)
    def normalize(v):
        if isinstance(v, str) and v in ('0', '1'):
            return int(v)
        return v

    norm_field = normalize(field)
    norm_value = normalize(value)

    # (1, '=', 1) or ('1', '=', '1') -> always true
    if norm_field == 1 and norm_value == 1:
        return "always_true"

    # (0, '=', 1) or ('0', '=', '1') -> always false
    if norm_field == 0 and norm_value == 1:
        return "always_false"

    return None


def _format_value(value: Any, output_format: OutputFormat) -> str:
    """Format a value for output.

    Args:
        value: The value to format
        output_format: The output format (PSEUDOCODE or PYTHON)

    Returns:
        Formatted string representation of the value
    """
    if isinstance(value, DynamicRef):
        if output_format == OutputFormat.PYTHON:
            # Keep as Python variable reference
            return value.name
        else:
            # Humanize for pseudocode
            humanized = humanize_dynamic_ref(value)
            return to_readable_text(humanized)
    elif isinstance(value, str):
        if output_format == OutputFormat.PSEUDOCODE:
            return f'"{value}"'
        else:
            return repr(value)
    elif isinstance(value, list):
        formatted_items = ', '.join(_format_value(v, output_format) for v in value)
        return f"[{formatted_items}]"
    elif value is None:
        if output_format == OutputFormat.PSEUDOCODE:
            return 'Not set'
        else:
            return 'None'
    elif value is True:
        return 'True'
    elif value is False:
        if output_format == OutputFormat.PSEUDOCODE:
            return 'Not set'
        else:
            return 'False'
    else:
        return str(value)


def _format_field_name(field: Any, output_format: OutputFormat) -> str:
    """Format a field name based on output format.

    Args:
        field: The field name (usually a string)
        output_format: The output format (PSEUDOCODE or PYTHON)

    Returns:
        Formatted field name
    """
    if output_format == OutputFormat.PYTHON:
        # Keep field name as-is with underscores for Python
        return str(field)
    else:
        # Humanize for pseudocode
        if isinstance(field, str):
            system_label = get_system_field_label(field)
            if system_label:
                return to_readable_text(system_label)
            return to_readable_text(humanize_field(field))
        return str(field)


def _process_condition(condition: tuple, output_format: OutputFormat) -> str:
    """Convert a condition tuple to a formatted string.

    Args:
        condition: A tuple of (field, operator, value)
        output_format: The output format (PSEUDOCODE or PYTHON)

    Returns:
        Formatted condition string
    """
    if len(condition) < 3:
        raise MalformedDomainError(f"Invalid condition: expected 3 elements, got {len(condition)}")

    field, operator, value = condition[:3]

    # Check for tautology patterns (pseudocode only shows special messages)
    if output_format == OutputFormat.PSEUDOCODE:
        tautology = _is_tautology(condition)
        if tautology == "always_true":
            return "Always True (all records)"
        elif tautology == "always_false":
            return "Always False (no records)"

    # Handle =? operator
    if operator == '=?':
        if value in (None, False):
            if output_format == OutputFormat.PSEUDOCODE:
                return 'Always True (ignored condition)'
            else:
                return 'True'
        else:
            operator = '='

    formatted_field = _format_field_name(field, output_format)
    formatted_value = _format_value(value, output_format)

    # Select comparison operators based on output format
    comparison_ops = (
        PSEUDOCODE_COMPARISON_OPERATORS
        if output_format == OutputFormat.PSEUDOCODE
        else PYTHON_COMPARISON_OPERATORS
    )
    op_str = comparison_ops.get(operator, operator)

    return f"({formatted_field} {op_str} {formatted_value})"


def _convert_domain(domain: list, output_format: OutputFormat) -> str:
    """Convert an Odoo domain expression to a human-readable format.

    This is the core conversion function used by both pseudocode and Python converters.

    Args:
        domain: The parsed Odoo domain (list of tuples and operators)
        output_format: The output format (PSEUDOCODE or PYTHON)

    Returns:
        Converted domain string

    Raises:
        MalformedDomainError: If the domain structure is invalid
    """
    logical_ops = (
        PSEUDOCODE_LOGICAL_OPERATORS
        if output_format == OutputFormat.PSEUDOCODE
        else PYTHON_LOGICAL_OPERATORS
    )

    # Separator between conditions for pseudocode (newline) vs Python (space)
    separator = '\n' if output_format == OutputFormat.PSEUDOCODE else ' '

    stack = []
    warnings = []

    # Process elements in reverse order (right to left) for prefix notation
    for i in reversed(range(len(domain))):
        element = domain[i]

        if isinstance(element, tuple):
            stack.append(_process_condition(element, output_format))
        elif isinstance(element, list):
            # Nested domain - recursive call
            stack.append(_convert_domain(element, output_format))
        elif element in LOGICAL_OPERATOR_SET:
            if element == '!':
                # Unary operator: takes exactly 1 operand
                if stack:
                    operand = stack.pop()
                    not_keyword = logical_ops['!']
                    stack.append(f"{not_keyword} ({operand})")
                else:
                    warnings.append(f"NOT operator at position {i} has no operand")
            else:
                # Binary operators '&' and '|': take exactly 2 operands (Odoo standard)
                if len(stack) >= 2:
                    operand1 = stack.pop()
                    operand2 = stack.pop()
                    op_word = logical_ops[element]
                    if output_format == OutputFormat.PSEUDOCODE:
                        stack.append(f"{operand1}{separator}{op_word}{separator}{operand2}")
                    else:
                        stack.append(f"({operand1} {op_word} {operand2})")
                elif len(stack) == 1:
                    # Only one operand available - this is a malformed domain
                    warnings.append(
                        f"Binary operator '{element}' at position {i} has only 1 operand (expected 2)"
                    )
                    # Keep the operand as-is to avoid losing data
                else:
                    warnings.append(
                        f"Binary operator '{element}' at position {i} has no operands"
                    )

    # Handle implicit AND: if multiple items remain on stack, AND them together
    # This handles cases like [('a', '=', 1), ('b', '=', 2)] without explicit '&'
    and_word = logical_ops['&']
    while len(stack) > 1:
        operand1 = stack.pop(0)
        operand2 = stack.pop(0)
        if output_format == OutputFormat.PSEUDOCODE:
            stack.insert(0, f"{operand1}{separator}{and_word}{separator}{operand2}")
        else:
            stack.insert(0, f"({operand1} {and_word} {operand2})")

    if not stack:
        if output_format == OutputFormat.PSEUDOCODE:
            return 'Always True (empty domain)'
        else:
            return 'True'

    result = stack[0]

    # If there were warnings about malformed domain, append them
    if warnings:
        warning_msg = "; ".join(warnings)
        if output_format == OutputFormat.PSEUDOCODE:
            result += f"\n\n[Warning: {warning_msg}]"
        else:
            result += f"  # Warning: {warning_msg}"

    return result


def convert_odoo_domain_to_pseudocode(domain: list) -> str:
    """Convert an Odoo domain expression to human-readable pseudocode.

    Follows Odoo domain conventions (compatible with Odoo 16+):
    - '&' and '|' are BINARY operators (take exactly 2 operands)
    - '!' is a UNARY operator (takes exactly 1 operand)
    - Implicit '&' between adjacent conditions without explicit operators
    - Supports all standard Odoo comparison operators

    Args:
        domain: The parsed Odoo domain (list of tuples and operators)

    Returns:
        Human-readable pseudocode string

    Examples:
        >>> convert_odoo_domain_to_pseudocode([('state', '=', 'active')])
        '(State equals "active")'

        >>> convert_odoo_domain_to_pseudocode([('user_id', '=', DynamicRef('user.id'))])
        '(User equals current user)'
    """
    return _convert_domain(domain, OutputFormat.PSEUDOCODE)


def convert_odoo_domain_to_python(domain: list) -> str:
    """Convert an Odoo domain expression to a Python-like expression.

    Follows Odoo domain conventions (compatible with Odoo 16+):
    - '&' and '|' are BINARY operators (take exactly 2 operands)
    - '!' is a UNARY operator (takes exactly 1 operand)
    - Implicit '&' between adjacent conditions without explicit operators
    - Uses Python comparison operators (==, !=, >, <, in, not in, etc.)
    - Field names retain underscore format (snake_case)
    - Dynamic references shown as Python variables (e.g., user.id)

    Args:
        domain: The parsed Odoo domain (list of tuples and operators)

    Returns:
        Python-style expression string

    Examples:
        >>> convert_odoo_domain_to_python([('state', '=', 'active')])
        "(state == 'active')"

        >>> convert_odoo_domain_to_python([('active', '=', True)])
        "(active == True)"

        >>> convert_odoo_domain_to_python([('user_id', '=', DynamicRef('user.id'))])
        "(user_id == user.id)"
    """
    return _convert_domain(domain, OutputFormat.PYTHON)
