"""Command-line interface for Odoo domain converter.

This module provides a CLI for converting Odoo domains to human-readable
formats without launching the GUI.

Usage:
    # Convert domain to pseudocode (default)
    python -m polish_converter convert "[('state', '=', 'draft')]"

    # Convert domain to Python expression
    python -m polish_converter convert --python "[('state', '=', 'draft')]"

    # Read domain from file
    python -m polish_converter convert -f domain.txt

    # Launch GUI
    python -m polish_converter gui
"""

import sys
import click

from .parser import parse_domain
from .converter import convert_odoo_domain_to_python, convert_odoo_domain_to_pseudocode


@click.group()
@click.version_option(version="1.0.0", prog_name="polish-converter")
def main():
    """Odoo Domain Converter - Convert Polish notation domains to human-readable format."""
    pass


@main.command()
@click.argument('domain', required=False)
@click.option('-f', '--file', 'file_path', type=click.Path(exists=True),
              help='Read domain from file instead of argument')
@click.option('--python', 'output_python', is_flag=True,
              help='Output Python expression instead of pseudocode')
@click.option('--pseudocode', 'output_pseudocode', is_flag=True, default=True,
              help='Output pseudocode (default)')
def convert(domain: str | None, file_path: str | None, output_python: bool, output_pseudocode: bool):
    """Convert an Odoo domain to human-readable format.

    DOMAIN is the Odoo domain string in Polish notation, e.g.:
    "[('state', '=', 'draft'), ('user_id', '=', user.id)]"

    Examples:
        polish-converter convert "[('state', '=', 'draft')]"
        polish-converter convert --python "[('active', '=', True)]"
        polish-converter convert -f domain.txt
    """
    # Get domain from file or argument
    if file_path:
        with open(file_path, 'r') as f:
            domain_str = f.read().strip()
    elif domain:
        domain_str = domain
    else:
        # Read from stdin if no argument or file
        if not sys.stdin.isatty():
            domain_str = sys.stdin.read().strip()
        else:
            click.echo("Error: Provide a domain string, use -f to read from file, or pipe input", err=True)
            sys.exit(1)

    if not domain_str:
        click.echo("Error: Empty domain", err=True)
        sys.exit(1)

    try:
        parsed = parse_domain(domain_str)

        if output_python:
            result = convert_odoo_domain_to_python(parsed)
        else:
            result = convert_odoo_domain_to_pseudocode(parsed)

        click.echo(result)
    except ValueError as e:
        click.echo(f"Parse error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command()
def gui():
    """Launch the graphical user interface."""
    from .gui import run_gui
    run_gui()


@main.command()
@click.argument('domain', required=False)
@click.option('-f', '--file', 'file_path', type=click.Path(exists=True),
              help='Read domain from file instead of argument')
@click.option('--url', default='http://localhost:8069',
              help='Odoo server URL')
@click.option('--db', 'database', required=True,
              help='Database name')
@click.option('--user', 'username', default='admin',
              help='Username (default: admin)')
@click.option('--password', default='admin',
              help='Password (default: admin)')
@click.option('--model', required=True,
              help='Model to validate against (e.g., res.partner)')
def validate(domain: str | None, file_path: str | None, url: str, database: str,
             username: str, password: str, model: str):
    """Validate a domain against an Odoo model.

    Connects to the specified Odoo instance and validates field existence,
    operator compatibility, and value types.

    Examples:
        polish-converter validate --db mydb --model res.partner "[('name', 'ilike', 'test')]"
        polish-converter validate --url http://odoo.example.com:8069 --db prod --model sale.order -f domain.txt
    """
    from .validation import validate_domain_fields

    # Get domain from file or argument
    if file_path:
        with open(file_path, 'r') as f:
            domain_str = f.read().strip()
    elif domain:
        domain_str = domain
    else:
        # Read from stdin if no argument or file
        if not sys.stdin.isatty():
            domain_str = sys.stdin.read().strip()
        else:
            click.echo("Error: Provide a domain string, use -f to read from file, or pipe input", err=True)
            sys.exit(1)

    if not domain_str:
        click.echo("Error: Empty domain", err=True)
        sys.exit(1)

    try:
        parsed = parse_domain(domain_str)

        odoo_settings = {
            'url': url,
            'database': database,
            'username': username,
            'password': password,
        }

        results = validate_domain_fields(model, parsed, odoo_settings)

        if not results:
            click.echo("All validations passed!")
            sys.exit(0)

        # Group by level
        errors = [(msg, level) for level, msg in results if level == 'error']
        warnings = [(msg, level) for level, msg in results if level == 'warning']
        infos = [(msg, level) for level, msg in results if level == 'info']

        has_errors = bool(errors)

        if errors:
            click.echo("ERRORS:", err=True)
            for msg, _ in errors:
                click.echo(f"  {msg}", err=True)

        if warnings:
            if errors:
                click.echo("", err=True)
            click.echo("WARNINGS:")
            for msg, _ in warnings:
                click.echo(f"  {msg}")

        if infos:
            if errors or warnings:
                click.echo("")
            click.echo("INFO:")
            for msg, _ in infos:
                click.echo(f"  {msg}")

        sys.exit(1 if has_errors else 0)

    except ValueError as e:
        click.echo(f"Parse error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
