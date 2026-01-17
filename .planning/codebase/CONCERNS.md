# Codebase Concerns

**Analysis Date:** 2026-01-17
**Last Updated:** 2026-01-17

## Tech Debt

**~~Significant Code Duplication:~~ RESOLVED**
- Issue: Two nearly identical converter functions (97 lines each)
- Resolution: Refactored into `polish_converter/converter.py` with shared `_convert_domain()` function
  that accepts an `OutputFormat` enum parameter. Eliminated ~90 lines of duplicate code.
- Fixed in: Refactoring commit (package structure)

**~~Unused Import:~~ RESOLVED**
- Issue: `black` module imported but never used
- Resolution: Removed from new package structure. `main.py` is now a thin compatibility wrapper.
- Fixed in: Refactoring commit (package structure)

## Known Bugs

**~~Silent Failure on Malformed Domains:~~ RESOLVED**
- Symptoms: Produces incorrect results without warning for domains with missing operands
- Resolution: Added warning collection in `_convert_domain()`. When binary operators have
  insufficient operands, warnings are appended to output. Added `MalformedDomainError` exception
  class for explicit error handling.
- Fixed in: `polish_converter/converter.py`

## Security Considerations

**Input Parsing (Low Risk):**
- Risk: Potential for malicious input
- Current mitigation: Uses `ast.literal_eval()` which is safe against code injection
- Files: `main.py` line 235
- Recommendations: Input is reasonably secure; consider depth limits for nested structures

**No Hardcoded Secrets:**
- Risk: None detected
- Current mitigation: Not applicable - no secrets in codebase

## Performance Bottlenecks

**Deeply Nested Domains:**
- Problem: Recursive processing of nested domains
- File: `main.py` lines 65-70, 166-171
- Measurement: Not profiled
- Cause: Recursive calls without depth limit
- Improvement path: Add recursion depth limit or convert to iterative processing

## Fragile Areas

**GUI Event Handler:**
- File: `polish_converter/gui.py`
- Why fragile: Broad exception handling masks specific errors
- Common failures: Silent failure, unhelpful error messages
- Safe modification: Add specific exception handlers with meaningful messages
- Test coverage: No direct GUI tests (stable simple UI - low priority)

**Operator Stack Processing:** (Improved)
- File: `polish_converter/converter.py` - `_convert_domain()` function
- Why fragile: Complex state management with stack operations
- Improvement: Now produces warnings for malformed domains instead of silent failures
- Test coverage: Good - 127 tests including edge cases

## Scaling Limits

**Not Applicable:**
- This is a desktop utility application
- No concurrent users or scaling concerns

## Dependencies at Risk

**PySimpleGUI 4.60.5:**
- Risk: License changed to commercial in 2022, version 4.x may be last LGPL version
- Impact: Future updates may require paid license
- Migration plan: Consider PySimpleGUIQt, tkinter, or dearpygui as alternatives

**Outdated Dependencies:**
- Risk: Dependencies from mid-2023 (18+ months old)
- Files: `requirements.txt`
- Versions: black==23.7.0, aiohttp==3.8.5
- Impact: Missing security patches and bug fixes
- Migration plan: Run `pip list --outdated` and update pinned versions

## Missing Critical Features

**~~No CLI Interface:~~ RESOLVED**
- Problem: Conversion functions only accessible via GUI
- Resolution: Added comprehensive CLI using click in `polish_converter/cli.py`:
  - `python -m polish_converter convert` - Convert domains (supports --python, -f file)
  - `python -m polish_converter validate` - Validate against Odoo instance
  - `python -m polish_converter gui` - Launch GUI
  - Supports reading from stdin, files, or arguments
- Fixed in: `polish_converter/cli.py`

**~~No Test Suite:~~ RESOLVED**
- Problem: Zero test coverage for critical conversion logic
- Resolution: Tests already exist in `tests/` with 127 passing tests covering:
  - Parser tests (`test_parser.py`)
  - Humanization tests (`test_humanization.py`)
  - Odoo-aware output tests (`test_odoo_aware.py`)
  - Python output tests (`test_python_output.py`)
- Current status: 127 tests, all passing

## Test Coverage Gaps

**~~Conversion Functions:~~ RESOLVED**
- Now tested: `convert_odoo_domain_to_python()`, `convert_odoo_domain_to_pseudocode()`
- Coverage: Good - 127 tests in `tests/` directory
- Tested in: `test_python_output.py`, `test_humanization.py`, `test_odoo_aware.py`

**~~Edge Cases:~~ RESOLVED**
- Now tested: Empty domains, nested structures, special values, tautology patterns
- Coverage: Good - comprehensive edge case tests in `test_parser.py`

**GUI Functionality:**
- What's not tested: Event handling, user interaction
- Risk: UI regressions
- Priority: Low (stable simple UI)
- Difficulty to test: Medium - requires GUI testing framework

**CLI Functionality:**
- What's not tested: CLI argument parsing, file input, stdin handling
- Risk: CLI regressions
- Priority: Medium
- Difficulty to test: Low - use click's testing utilities

---

*Concerns audit: 2026-01-17*
*Last updated: 2026-01-17 (after package refactoring)*
*Update as issues are fixed or new ones discovered*
