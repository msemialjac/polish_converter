---
phase: 05-odoo-validation
plan: 03
subsystem: validation
tags: [xmlrpc, odoo, gui, type-validation, operator-validation]

# Dependency graph
requires:
  - phase: 05-01
    provides: OdooConnection class with authentication
  - phase: 05-02
    provides: Field validation methods (get_fields, validate_field, validate_path)
provides:
  - FIELD_TYPE_OPERATORS constant for operator/field compatibility
  - FIELD_TYPE_VALUES constant for value type expectations
  - validate_operator() classmethod for operator validation
  - validate_value_type() classmethod for value type validation
  - validate_domain_condition() for per-condition validation
  - validate_domain() for comprehensive domain validation
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Class-level constants for validation rules
    - Categorized validation results (error/warning/info levels)

key-files:
  created: []
  modified:
    - main.py

key-decisions:
  - "Operator validation returns warning not error (domain may still work)"
  - "Value type validation skips DynamicRef (can't validate at parse time)"
  - "List values validated recursively for 'in'/'not in' operators"
  - "Unknown field types pass validation (Odoo may have custom types)"

# Metrics
duration: 3min
completed: 2026-01-17
---

# Phase 5 Plan 3: Operator Compatibility and Value Type Validation Summary

**Type and operator validation for Odoo domains with comprehensive per-condition checking**

## Performance

- **Duration:** 3 min
- **Started:** 2026-01-17T14:45:39Z
- **Completed:** 2026-01-17T14:48:12Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments

- `FIELD_TYPE_OPERATORS` constant maps each Odoo field type to compatible operators:
  - char/text: =, !=, like, ilike, =like, =ilike, in, not in
  - integer/float/monetary: =, !=, >, <, >=, <=, in, not in
  - boolean: =, != only
  - date/datetime: =, !=, >, <, >=, <=
  - many2one: =, !=, in, not in, child_of, parent_of
  - one2many/many2many: in, not in, child_of, parent_of
  - selection: =, !=, in, not in
- `FIELD_TYPE_VALUES` constant maps field types to expected Python types
- `validate_operator()` classmethod checks operator/field type compatibility
- `validate_value_type()` classmethod checks value/field type compatibility
- Handles DynamicRef values (skips validation - runtime value unknown)
- Handles list values recursively for 'in'/'not in' operators
- `validate_domain_condition()` validates single (field, operator, value) tuples
- `validate_domain()` validates entire domains with categorized results
- GUI displays validation results grouped by level (errors, warnings, info)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add operator and type validation methods** - `77c579e` (feat)
2. **Task 2: Integrate with domain validation** - `ef662af` (feat)

## Files Created/Modified

- `main.py` - Added FIELD_TYPE_OPERATORS, FIELD_TYPE_VALUES constants; added validate_operator(), validate_value_type(), validate_domain_condition(), validate_domain() methods; updated validate_domain_fields() and GUI validation handling

## Decisions Made

- Operator validation returns (False, warning) not error - domains may still work with unusual operators
- Value type validation skips DynamicRef instances entirely - can't know runtime value
- List values (for 'in'/'not in') validated recursively - each item checked against field type
- Unknown field types (e.g., 'html', custom types) pass validation - Odoo may have types not in our list

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## Requirements Satisfied

- **VALID-04:** Validate operator compatibility for field type
- **VALID-06:** Warn if value type doesn't match field type

## Next Phase Readiness

This completes Phase 5: Odoo Validation.
All 6 VALID-* requirements are now satisfied:
- VALID-01: Connect to Odoo instance via XML-RPC API
- VALID-02: GUI settings panel for Odoo connection
- VALID-03: Validate field existence on specified model
- VALID-04: Validate operator compatibility for field type
- VALID-05: Validate dotted path traversal
- VALID-06: Warn if value type doesn't match field type

---
*Phase: 05-odoo-validation*
*Completed: 2026-01-17*
