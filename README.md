# Polish Converter

**Version:** 1.0.0
**Category:** Developer Tools
**License:** MIT
**Python:** 3.10+

## Overview

Polish Converter is a developer tool that converts Odoo domain expressions from Polish (prefix) notation to human-readable formats. It helps developers and business analysts understand complex domain filters without decoding nested logical operators manually.

**Key Features:**
1. **Pseudocode Output** - Human-readable business logic format
2. **Python Expression Output** - Readable Python-style boolean expressions
3. **Dynamic Reference Support** - Handles `user.id`, `company_ids`, and other runtime references
4. **Odoo Validation** - Validate domains against live Odoo instances
5. **GUI & CLI** - Both graphical and command-line interfaces

---

## Features

### Domain Conversion

- **Polish notation parsing** - Correctly interprets Odoo's prefix notation (`&`, `|`, `!` operators)
- **Implicit AND handling** - Domains without explicit operators are joined with AND
- **Nested structures** - Handles deeply nested conditions
- **All Odoo operators** - `=`, `!=`, `>`, `<`, `>=`, `<=`, `in`, `not in`, `like`, `ilike`, `=like`, `=ilike`, `child_of`, `parent_of`

### Human-Readable Output

- **Field humanization** - `privacy_visibility` → "Privacy Visibility"
- **ID suffix stripping** - `company_id` → "Company", `user_ids` → "Users"
- **Dotted path support** - `project_id.name` → "Project's Name"
- **System field labels** - `create_uid` → "Created By", `write_date` → "Last Updated On"
- **User reference humanization** - `user.id` → "current user", `user.company_ids` → "current user's Companies"

### Value Formatting

- **Boolean humanization** - `False` → "Not set" (pseudocode), `False` (Python)
- **Tautology recognition** - `(1, '=', 1)` → "Always True (all records)"
- **False tautology** - `(0, '=', 1)` → "Always False (no records)"

### Odoo Validation (Optional)

- **Model resolution** - Accepts technical names (`res.partner`) or display names ("Contact")
- **Field existence** - Validates fields exist on the model
- **Operator compatibility** - Warns about incompatible operators (e.g., `>` on boolean fields)
- **Value type checking** - Warns about type mismatches
- **Path traversal** - Validates dotted paths through relational fields

---

## Architecture

### Package Structure

```
polish_converter/
├── __init__.py          # Public API exports
├── __main__.py          # CLI entry point
├── parser.py            # Domain tokenizer and parser
├── converter.py         # Domain to pseudocode/Python conversion
├── humanizer.py         # Field name humanization
├── odoo_connection.py   # Odoo XML-RPC client
├── validation.py        # Domain validation utilities
├── gui.py               # FreeSimpleGUI interface
└── cli.py               # Click-based CLI

main.py                  # Backward-compatible entry point
tests/                   # Test suite (127 tests)
```

### Dependencies

**Runtime:**
- `FreeSimpleGUI>=5.0.0` - GUI framework
- `click>=8.1.7` - CLI framework

**Development:**
- `pytest>=8.0.0` - Test framework

### Key Classes

| Class | Module | Description |
|-------|--------|-------------|
| `DynamicRef` | parser | Represents runtime references (e.g., `user.id`) |
| `DomainTokenizer` | parser | Lexical analysis of domain strings |
| `DomainParser` | parser | Recursive descent parser |
| `OdooConnection` | odoo_connection | XML-RPC client for validation |

### Key Functions

| Function | Module | Description |
|----------|--------|-------------|
| `parse_domain()` | parser | Parse domain string to Python structure |
| `convert_odoo_domain_to_pseudocode()` | converter | Convert to human-readable pseudocode |
| `convert_odoo_domain_to_python()` | converter | Convert to Python expression |
| `humanize_field()` | humanizer | Convert field names to labels |
| `validate_domain_fields()` | validation | Validate against Odoo model |

---

## Installation

### From Source

```bash
# Clone or download the repository
cd polish_converter

# Create virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or: .venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### Verify Installation

```bash
# Run tests
python -m pytest tests/ -v

# Test CLI
python -m polish_converter --help

# Launch GUI
python main.py
```

---

## Usage

### Command Line Interface

**Convert to pseudocode (default):**
```bash
python -m polish_converter convert "[('state', '=', 'draft')]"
```

Output:
```
(State equals "draft")
```

**Convert to Python expression:**
```bash
python -m polish_converter convert --python "[('state', '=', 'draft'), ('user_id', '=', user.id)]"
```

Output:
```
((State equals 'draft') and (User equals current user))
```

**Read from file:**
```bash
python -m polish_converter convert -f domain.txt
```

**Read from stdin:**
```bash
echo "[('active', '=', True)]" | python -m polish_converter convert
```

**Validate against Odoo:**
```bash
python -m polish_converter validate \
  --db mydb \
  --model res.partner \
  "[('name', 'ilike', 'test')]"
```

**Launch GUI:**
```bash
python -m polish_converter gui
# or simply:
python main.py
```

### Graphical User Interface

1. Launch the GUI with `python main.py`
2. Paste your domain in the input field
3. Select output format (Pseudocode or Python Code)
4. Click **Convert**
5. Optionally, enter a model name and click **Validate** to check against Odoo

### Programmatic Use

```python
from polish_converter import (
    parse_domain,
    convert_odoo_domain_to_pseudocode,
    convert_odoo_domain_to_python,
    DynamicRef,
)

# Parse a domain string
domain = parse_domain("[('user_id', '=', user.id), ('state', 'in', ['draft', 'sent'])]")

# Convert to pseudocode
pseudo = convert_odoo_domain_to_pseudocode(domain)
print(pseudo)
# Output:
# (User equals current user)
# AND
# (State is in ["draft", "sent"])

# Convert to Python expression
python_expr = convert_odoo_domain_to_python(domain)
print(python_expr)
# Output:
# ((User equals current user) and (State is in ['draft', 'sent']))

# Check for dynamic references
for item in domain:
    if isinstance(item, tuple) and isinstance(item[2], DynamicRef):
        print(f"Dynamic ref: {item[2].name}")
```

---

## User Guide

### Understanding Odoo Domains

Odoo domains use Polish (prefix) notation for logical operators:

| Domain | Meaning |
|--------|---------|
| `[('state', '=', 'draft')]` | state equals 'draft' |
| `[('a', '=', 1), ('b', '=', 2)]` | a=1 AND b=2 (implicit AND) |
| `['&', ('a', '=', 1), ('b', '=', 2)]` | a=1 AND b=2 (explicit AND) |
| `['|', ('a', '=', 1), ('b', '=', 2)]` | a=1 OR b=2 |
| `['!', ('active', '=', False)]` | NOT (active=False) |
| `['&', '|', ('a', '=', 1), ('b', '=', 2), ('c', '=', 3)]` | (a=1 OR b=2) AND c=3 |

### Dynamic References

Odoo domains often contain runtime references:

| Reference | Meaning |
|-----------|---------|
| `user.id` | Current user's ID |
| `user.partner_id.id` | Current user's partner ID |
| `user.company_ids` | Current user's allowed companies |
| `company_ids` | Active company IDs |
| `context.get('active_id')` | Context variable |

### Configuring Odoo Validation

1. Click **Settings** in the GUI
2. Enter your Odoo server URL (e.g., `http://localhost:8069`)
3. Click **Refresh Databases** to load available databases
4. Select a database and enter credentials
5. Click **Test Connection** to verify
6. Click **Save**

Now you can validate domains against real Odoo models.

---

## Technical Details

### CLI Commands

| Command | Options | Description |
|---------|---------|-------------|
| `convert` | `--python`, `-f FILE` | Convert domain to readable format |
| `validate` | `--url`, `--db`, `--user`, `--password`, `--model` | Validate against Odoo |
| `gui` | | Launch graphical interface |

### Operator Mappings

| Odoo Operator | Pseudocode | Python |
|---------------|------------|--------|
| `=` | equals | equals |
| `!=` | doesn't equal | doesn't equal |
| `>` | is greater than | is greater than |
| `<` | is less than | is less than |
| `>=` | is at least | is at least |
| `<=` | is at most | is at most |
| `in` | is in | is in |
| `not in` | is not in | is not in |
| `like` | is like | is like |
| `ilike` | is like (case-insensitive) | is like (case-insensitive) |
| `child_of` | is child of | is child of |
| `parent_of` | is parent of | is parent of |
| `&` | AND | and |
| `\|` | OR | or |
| `!` | NOT | not |

### System Field Labels

| Technical Name | Display Label |
|----------------|---------------|
| `create_uid` | Created By |
| `write_uid` | Last Updated By |
| `create_date` | Created On |
| `write_date` | Last Updated On |
| `active` | Active |
| `id` | ID |
| `display_name` | Display Name |

---

## Troubleshooting

### Parse error: Unexpected character

The domain string contains invalid syntax. Common issues:
- Missing quotes around strings
- Unbalanced parentheses or brackets
- Invalid escape sequences

### "Not set" appears for actual values

The value `False` is displayed as "Not set" in pseudocode mode. Use `--python` for literal output.

### Validation fails with "Authentication failed"

1. Check Odoo server is running
2. Verify database name is correct
3. Confirm username and password
4. Ensure user has access to the model

### Validation fails with "Model not found"

1. Try the technical name (e.g., `res.partner` not "Contact")
2. Check spelling and case
3. Verify the module providing the model is installed

### GUI doesn't launch

1. Ensure `FreeSimpleGUI` is installed: `pip install FreeSimpleGUI`
2. On Linux, you may need `tkinter`: `sudo apt install python3-tk`

---

## Changelog

### Version 1.0.0

- **Package refactoring** - Modular architecture with separate modules
- **CLI interface** - Full command-line support with `click`
- **Code deduplication** - Shared converter logic via `OutputFormat` enum
- **Malformed domain handling** - Warnings for invalid operator usage
- **Backward compatibility** - `main.py` re-exports all APIs
- **127 tests passing** - Comprehensive test coverage

### Initial Development

- Custom parser for dynamic references (`user.id`, `company_ids`)
- Pseudocode and Python output formats
- Field humanization (snake_case → Title Case)
- System field label mappings
- Tautology pattern recognition
- Odoo XML-RPC validation
- FreeSimpleGUI interface

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests for new functionality
4. Ensure all tests pass: `python -m pytest tests/ -v`
5. Submit a pull request

---

## Support

For issues and feature requests, please open an issue on the repository or contact the maintainer.
