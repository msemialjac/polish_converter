"""Odoo Domain Converter - Main entry point.

This module provides backward-compatible entry points for the Odoo domain converter.
For new code, prefer importing directly from the polish_converter package.

Usage:
    # Launch GUI (default)
    python main.py

    # Use CLI
    python -m polish_converter convert "[('state', '=', 'draft')]"
    python -m polish_converter gui
    python -m polish_converter --help

For programmatic use, import from the polish_converter package:
    from polish_converter import (
        parse_domain,
        convert_odoo_domain_to_python,
        convert_odoo_domain_to_pseudocode,
        DynamicRef,
        OdooConnection,
    )
"""

# Re-export all public APIs for backward compatibility
from polish_converter import (
    # Parser
    DynamicRef,
    parse_domain,
    DomainTokenizer,
    DomainParser,
    Token,
    TokenType,
    # Converter
    convert_odoo_domain_to_python,
    convert_odoo_domain_to_pseudocode,
    OutputFormat,
    MalformedDomainError,
    # Humanizer
    humanize_field,
    humanize_dynamic_ref,
    get_system_field_label,
    SYSTEM_FIELD_LABELS,
    # Odoo Connection
    OdooConnection,
    # Validation
    validate_domain_fields,
    extract_fields_from_domain,
)

# Re-export to_readable_text from humanizer for backward compatibility
from polish_converter.humanizer import to_readable_text

# Re-export GUI function for backward compatibility
from polish_converter.gui import run_gui as convert_odoo_domain_to_python_gui

# Export odoo_settings for backward compatibility
from polish_converter.gui import odoo_settings


def main():
    """Main entry point - launches the GUI."""
    from polish_converter.gui import run_gui
    run_gui()


if __name__ == "__main__":
    main()
