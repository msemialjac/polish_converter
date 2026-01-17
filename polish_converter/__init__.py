"""Odoo Domain Converter - Convert Polish notation domains to human-readable format.

This package provides tools for parsing Odoo domain expressions and converting
them to human-readable pseudocode or Python expressions.

Main components:
- parser: Parse Odoo domain strings including dynamic references
- converter: Convert parsed domains to pseudocode or Python
- humanizer: Convert technical field names to human-readable labels
- odoo_connection: Connect to Odoo for domain validation
- validation: Validate domains against Odoo models
- gui: Graphical user interface
- cli: Command-line interface
"""

from .parser import (
    DynamicRef,
    parse_domain,
    DomainTokenizer,
    DomainParser,
    Token,
    TokenType,
)

from .converter import (
    convert_odoo_domain_to_python,
    convert_odoo_domain_to_pseudocode,
    OutputFormat,
    MalformedDomainError,
)

from .humanizer import (
    humanize_field,
    humanize_dynamic_ref,
    get_system_field_label,
    SYSTEM_FIELD_LABELS,
)

from .odoo_connection import OdooConnection

from .validation import (
    validate_domain_fields,
    extract_fields_from_domain,
)

__version__ = "1.0.0"

__all__ = [
    # Parser
    "DynamicRef",
    "parse_domain",
    "DomainTokenizer",
    "DomainParser",
    "Token",
    "TokenType",
    # Converter
    "convert_odoo_domain_to_python",
    "convert_odoo_domain_to_pseudocode",
    "OutputFormat",
    "MalformedDomainError",
    # Humanizer
    "humanize_field",
    "humanize_dynamic_ref",
    "get_system_field_label",
    "SYSTEM_FIELD_LABELS",
    # Odoo Connection
    "OdooConnection",
    # Validation
    "validate_domain_fields",
    "extract_fields_from_domain",
]
