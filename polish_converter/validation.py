"""Domain validation utilities for Odoo connection.

This module provides helper functions for validating Odoo domains against
live Odoo instances.
"""

from .odoo_connection import OdooConnection
from .parser import parse_domain


def extract_fields_from_domain(domain: list) -> list[str]:
    """Extract all field names/paths from a parsed domain.

    Args:
        domain: Parsed domain (list of tuples and operators)

    Returns:
        List of unique field names/paths referenced in the domain
    """
    fields = set()

    for item in domain:
        if isinstance(item, tuple) and len(item) >= 3:
            field = item[0]
            if isinstance(field, str):
                fields.add(field)
        elif isinstance(item, list):
            # Nested domain
            fields.update(extract_fields_from_domain(item))

    return list(fields)


def validate_domain_fields(
    model_input: str,
    domain: list,
    odoo_settings: dict
) -> list[tuple[str, str]]:
    """Validate all fields, operators, and values in a domain against an Odoo model.

    Performs comprehensive validation including:
    - Model name resolution (accepts technical name or display name)
    - Field existence on the model
    - Operator compatibility with field types
    - Value type matching with field types
    - Dotted path traversal

    Args:
        model_input: The Odoo model to validate against (technical name like
                    'helpdesk.ticket' or display name like 'Helpdesk Ticket')
        domain: Parsed domain list
        odoo_settings: Dict containing url, database, username, password

    Returns:
        List of (level, message) tuples where level is 'error', 'warning', or 'info'
        Empty list if all validations pass.
    """
    # Check if connection settings are configured
    if not odoo_settings.get('url') or not odoo_settings.get('database'):
        return [('error', "Connection not configured. Use Settings to configure Odoo connection.")]

    # Create connection and authenticate
    conn = OdooConnection(
        odoo_settings['url'],
        odoo_settings['database'],
        odoo_settings['username'],
        odoo_settings['password']
    )

    uid = conn.authenticate()
    if not uid:
        return [('error', "Authentication failed. Check credentials in Settings.")]

    # Resolve model name (accepts technical name or display name)
    success, model_name, error = conn.resolve_model_name(model_input)
    if not success:
        return [('error', error)]

    # Add info if model was resolved from display name
    results = []
    if model_name != model_input.strip():
        results.append(('info', f"Resolved '{model_input}' → {model_name}"))

    # Use comprehensive domain validation
    results.extend(conn.validate_domain(model_name, domain))
    return results
