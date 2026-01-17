# Architecture

**Analysis Date:** 2026-01-17

## Pattern Overview

**Overall:** Single-file Desktop GUI Application (Monolithic)

**Key Characteristics:**
- Single executable module
- GUI-driven user interaction
- Stack-based algorithm for domain conversion
- Functional programming with procedural UI binding

## Layers

**Business Logic Layer:**
- Purpose: Domain conversion algorithms
- Contains: `convert_odoo_domain_to_python()`, `convert_odoo_domain_to_pseudocode()`
- Location: `main.py` (lines 6-104, 107-204)
- Depends on: Python stdlib (ast)
- Used by: Presentation layer

**Presentation Layer:**
- Purpose: User interface and event handling
- Contains: `convert_odoo_domain_to_python_gui()`
- Location: `main.py` (lines 209-250)
- Depends on: Business logic layer, PySimpleGUI
- Used by: Entry point

## Data Flow

**Domain Conversion Flow:**

1. User enters Odoo domain string in GUI input field
2. GUI event loop detects "Convert" button click (`main.py` line 229)
3. `ast.literal_eval()` parses string to Python list structure (`main.py` line 235)
4. Branch based on radio button selection (Python vs Pseudocode)
5. Converter processes domain using stack-based reverse Polish notation algorithm
6. Output formatted and displayed in GUI output field (`main.py` line 240)

**State Management:**
- Stateless: Each conversion is independent
- No persistent state between conversions
- GUI maintains widget state only

## Key Abstractions

**Domain Converter:**
- Purpose: Transform Odoo Polish notation to readable format
- Examples: `convert_odoo_domain_to_python()`, `convert_odoo_domain_to_pseudocode()`
- Pattern: Pure function with nested helpers
- Location: `main.py` lines 6-104, 107-204

**Nested Helper Functions:**
- Purpose: Encapsulated processing logic
- Examples: `format_value()`, `process_condition()`, `process_subexpression()`
- Pattern: Closure functions defined within converter
- Location: `main.py` lines 37-70, 138-171

**Operator Dictionary:**
- Purpose: Map Odoo operators to output format
- Pattern: Dictionary lookup for operator translation
- Location: `main.py` lines 15-33, 116-134

## Entry Points

**Main Script:**
- Location: `main.py` (line 249-250)
- Triggers: `python main.py` execution
- Responsibilities: Launch GUI application

**GUI Entry:**
- Location: `convert_odoo_domain_to_python_gui()` (`main.py` line 209)
- Triggers: Called by `__main__` block
- Responsibilities: Create window, run event loop, handle user interaction

## Error Handling

**Strategy:** Try/catch at GUI level with generic error display

**Patterns:**
- Broad `except Exception` at GUI event handler (`main.py` line 243)
- Error message displayed in output field
- No logging or detailed error reporting
- Silent handling of malformed domain operators

## Cross-Cutting Concerns

**Logging:**
- None implemented
- Errors displayed in GUI only

**Validation:**
- Relies on `ast.literal_eval()` for input parsing
- No explicit validation of domain structure
- Silent handling of malformed operators

**Configuration:**
- Hardcoded font: `("Helvetica", 20)` (`main.py` line 206)
- No configuration files

---

*Architecture analysis: 2026-01-17*
*Update when major patterns change*
