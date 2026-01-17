---
phase: 05-odoo-validation
plan: 02
subsystem: validation
tags: [xmlrpc, odoo, gui, field-validation, path-traversal]

# Dependency graph
requires:
  - phase: 05-01
    provides: OdooConnection class with authenticate() method
provides:
  - get_fields() method for field metadata retrieval with caching
  - validate_field() method for single field existence checks
  - validate_path() method for dotted path traversal validation
  - extract_fields_from_domain() helper for parsing domain fields
  - validate_domain_fields() for batch validation against model
  - GUI Model input field and Validate button
affects: [05-03]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Field metadata caching to avoid repeated API calls
    - Batch field validation from parsed domain

key-files:
  created: []
  modified:
    - main.py

key-decisions:
  - "Cache fields_get results per model to avoid repeated API calls"
  - "validate_path traverses each segment, checking relational types for non-final segments"
  - "Validation is informational only - does not block conversion"

# Metrics
duration: 2min
completed: 2026-01-17
---

# Phase 5 Plan 2: Field Existence and Path Traversal Validation Summary

**Field validation via Odoo XML-RPC API with GUI integration for validating domains against models**

## Performance

- **Duration:** 2 min
- **Started:** 2026-01-17T14:41:34Z
- **Completed:** 2026-01-17T14:43:34Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments

- `get_fields(model_name)` method retrieves field metadata from Odoo with caching
- `validate_field(model_name, field_name)` validates single field existence
- `validate_path(model_name, field_path)` validates dotted paths, checking:
  - Each segment exists on current model
  - Intermediate segments are relational (many2one, one2many, many2many)
  - Traverses to related model via 'relation' attribute
- `extract_fields_from_domain(domain)` extracts all field names from parsed domain
- `validate_domain_fields(model, domain)` batch validates all fields with warnings
- GUI Model input field for specifying target model (e.g., res.partner)
- GUI Validate button triggers validation against Odoo
- Validation warnings displayed in dedicated output area

## Task Commits

Each task was committed atomically:

1. **Task 1: Add field validation methods to OdooConnection** - `1df1061` (feat)
2. **Task 2: Add Model input and Validate button to GUI** - `9eda6b1` (feat)

## Files Created/Modified

- `main.py` - Added get_fields(), validate_field(), validate_path() to OdooConnection; added extract_fields_from_domain(), validate_domain_fields(); updated GUI layout with Model input and Validate button

## Decisions Made

- Field metadata is cached per model to avoid repeated XML-RPC calls during validation
- Path validation checks field type for relational traversal (many2one, one2many, many2many)
- Error messages specify which segment of a path failed validation
- Validation is informational only - conversion still works without valid connection

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## Requirements Satisfied

- **VALID-03:** Validate field existence on specified model
- **VALID-05:** Validate dotted path traversal (relations exist along the path)

## Next Phase Readiness

- Field validation infrastructure ready for operator compatibility (05-03)
- Field info includes 'type' needed for operator/value validation
- GUI validation framework extensible for additional checks

---
*Phase: 05-odoo-validation*
*Completed: 2026-01-17*
