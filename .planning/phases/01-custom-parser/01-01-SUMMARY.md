---
phase: 01-custom-parser
plan: 01
subsystem: parser
tags: [tokenizer, parser, recursive-descent, ast, dynamic-references]

# Dependency graph
requires: []
provides:
  - DynamicRef class for variable references
  - parse_domain() function for domain string parsing
  - Custom tokenizer handling dynamic references
affects: [02-field-humanization, 03-odoo-aware-output]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Recursive descent parser
    - Tokenizer/Parser separation
    - Fallback to ast.literal_eval for simple cases

key-files:
  created:
    - tests/__init__.py
    - tests/test_parser.py
  modified:
    - main.py

key-decisions:
  - "Try ast.literal_eval first, fall back to custom parser only when needed"
  - "DynamicRef wrapper class to distinguish variable references from strings"
  - "Support both single and double quoted strings in tokenizer"

patterns-established:
  - "TDD workflow: RED (failing tests) -> GREEN (implementation) -> REFACTOR (cleanup)"
  - "Tokenizer yields tokens, Parser builds structure from tokens"

# Metrics
duration: 4min
completed: 2026-01-17
---

# Phase 01 Plan 01: Custom Domain Parser Summary

**Custom tokenizer/parser that handles Odoo domains with dynamic references (user.id, company_ids) that ast.literal_eval cannot parse**

## Performance

- **Duration:** 4 min
- **Started:** 2026-01-17T14:06:43Z
- **Completed:** 2026-01-17T14:10:19Z
- **Tasks:** 1 TDD feature (3 phases: RED, GREEN, REFACTOR)
- **Files modified:** 3

## Accomplishments

- DynamicRef class created to wrap variable references
- Custom tokenizer handles strings, numbers, booleans, None, identifiers, operators
- Recursive descent parser builds list/tuple structures from tokens
- parse_domain() tries ast.literal_eval first for performance, falls back to custom parser
- GUI updated to use new parser instead of ast.literal_eval()
- All 34 tests pass covering standard domains, dynamic references, multi-line strings

## Task Commits

Each TDD phase committed atomically:

1. **RED: Failing tests** - `d61cacb` (test)
   - Tests for DynamicRef class
   - Tests for standard domain parsing
   - Tests for dynamic references
   - Tests for multi-line strings
   - Tests for edge cases

2. **GREEN: Implementation** - `fc1152b` (feat)
   - DynamicRef class
   - TokenType enum, Token class
   - DomainTokenizer class
   - DomainParser class
   - parse_domain() function
   - Updated GUI and format_value functions

3. **REFACTOR: Cleanup** - `386dab5` (refactor)
   - Removed unused 're' import

## Files Created/Modified

- `tests/__init__.py` - Test package init
- `tests/test_parser.py` - 34 tests covering all parser functionality
- `main.py` - Added DynamicRef, tokenizer, parser, parse_domain()

## Decisions Made

1. **Try ast.literal_eval first** - For simple domains without dynamic references, ast.literal_eval is faster and more robust. Custom parser only used when needed.

2. **DynamicRef wrapper class** - Distinguishes variable references from regular strings, allowing downstream code to handle them specially (e.g., render "user.id" as "current user").

3. **Tokenizer/Parser separation** - Clean separation of concerns: tokenizer handles lexical analysis, parser handles structure building.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - implementation went smoothly. TDD cycle completed without issues.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Parser foundation complete, ready for Phase 2: Field Humanization
- DynamicRef objects available for special rendering in future phases
- All requirements satisfied: PARSE-01, PARSE-02, PARSE-03

---
*Phase: 01-custom-parser*
*Completed: 2026-01-17*
