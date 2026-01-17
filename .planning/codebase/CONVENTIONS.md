# Coding Conventions

**Analysis Date:** 2026-01-17

## Naming Patterns

**Files:**
- snake_case for Python modules: `main.py`
- UPPERCASE for important docs: `README.md`
- No test file naming convention (no tests exist)

**Functions:**
- snake_case for all functions
- Descriptive, action-oriented names
- Examples: `convert_odoo_domain_to_python()`, `format_value()`, `process_condition()`

**Variables:**
- snake_case for all variables
- Examples: `operator_dict`, `logical_operators`, `formatted_value`
- Meaningful names reflecting purpose: `operand1`, `operand2`, `formatted_items`

**Types:**
- No type hints used in codebase
- No interfaces or type aliases defined

## Code Style

**Formatting:**
- 4-space indentation (Python standard)
- No enforced line length limit
- Black formatter in requirements but not configured

**Quotes:**
- Single quotes for dictionary keys and static strings
- Double quotes for f-strings and user-facing output
- Triple double-quotes for docstrings

**Semicolons:**
- Not used (Python convention)

**Linting:**
- No linting configuration files (.pylintrc, .flake8)
- Black installed but not enforced

## Import Organization

**Order:**
1. Third-party packages (PySimpleGUI, ast, black)

**Grouping:**
- All imports at top of file
- No blank lines between import groups

**Path Aliases:**
- Not used (single module application)

## Error Handling

**Patterns:**
- Broad `except Exception` at GUI event handler (`main.py` line 243)
- Error messages displayed in GUI output field
- No logging or stack traces

**Error Types:**
- Exceptions caught generically, converted to string output
- No custom exception classes
- Silent handling of malformed domain operators (pass statement)

## Logging

**Framework:**
- None implemented
- Errors displayed in GUI only

**Patterns:**
- No structured logging
- No log levels
- Commented debug code at line 254

## Comments

**When to Comment:**
- Explain algorithm logic: "Process elements in reverse order (right to left) for prefix notation"
- Document operator behavior: "Unary operator: takes exactly 1 operand"
- Note edge cases: "Handle implicit AND: if multiple items remain on stack..."

**JSDoc/Docstrings:**
- Multi-line docstrings for main functions (`main.py` lines 7-14, 108-114)
- Single-line docstrings for nested helpers
- Google-style format with Odoo compatibility notes

**TODO Comments:**
- Commented test data at line 254: `# [(\"field1\", \"=\", \"value1\")...]`
- No TODO/FIXME comments found

## Function Design

**Size:**
- Main functions: ~100 lines each
- Nested helpers: 5-15 lines each
- GUI function: ~40 lines

**Parameters:**
- Simple positional parameters (single argument)
- No keyword arguments
- No default values

**Return Values:**
- Explicit returns
- String return type for converters
- No return type hints

## Module Design

**Exports:**
- All functions at module level
- No `__all__` definition
- No barrel file pattern (single module)

**Barrel Files:**
- Not applicable (single file application)
- No package structure

---

*Convention analysis: 2026-01-17*
*Update when patterns change*
