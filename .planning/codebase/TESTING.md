# Testing Patterns

**Analysis Date:** 2026-01-17

## Test Framework

**Runner:**
- Not configured
- No pytest, unittest, or other test framework installed

**Assertion Library:**
- Not applicable

**Run Commands:**
```bash
# No test commands available
# Recommended setup:
pip install pytest
pytest tests/
```

## Test File Organization

**Location:**
- No test files exist
- No `tests/` directory

**Naming:**
- Not established (recommend: `test_*.py` pattern)

**Structure:**
```
# Current: No test structure
# Recommended:
tests/
  test_converter.py    # Unit tests for conversion functions
  test_gui.py          # GUI integration tests (if applicable)
  conftest.py          # Shared fixtures
```

## Test Structure

**Suite Organization:**
- Not established

**Recommended Pattern:**
```python
import pytest
from main import convert_odoo_domain_to_python, convert_odoo_domain_to_pseudocode

class TestOdooDomainToPython:
    def test_simple_equality(self):
        domain = [('field', '=', 'value')]
        result = convert_odoo_domain_to_python(domain)
        assert result == '(field == "value")'

    def test_and_operator(self):
        domain = ['&', ('a', '=', 1), ('b', '=', 2)]
        result = convert_odoo_domain_to_python(domain)
        # assert expected output

    def test_or_operator(self):
        domain = ['|', ('a', '=', 1), ('b', '=', 2)]
        result = convert_odoo_domain_to_python(domain)
        # assert expected output

    def test_not_operator(self):
        domain = ['!', ('field', '=', 'value')]
        result = convert_odoo_domain_to_python(domain)
        # assert expected output

    def test_empty_domain(self):
        domain = []
        result = convert_odoo_domain_to_python(domain)
        assert result == 'True'
```

**Patterns:**
- Not established
- Recommend: arrange/act/assert pattern
- Recommend: beforeEach for shared setup

## Mocking

**Framework:**
- Not configured
- Recommend: pytest-mock or unittest.mock

**Patterns:**
- Not established

**What to Mock:**
- PySimpleGUI for GUI tests
- File system if adding file features

**What NOT to Mock:**
- Core conversion logic (pure functions)
- Operator dictionaries

## Fixtures and Factories

**Test Data:**
- Commented example in `main.py` line 254:
```python
# [("field1", "=", "value1"), "&", ("field2", "!=", "value2"), ("field3", "in", ["value3", "value4"])]
```

**Location:**
- No fixtures exist
- Recommend: `tests/fixtures/` for sample domains

**Recommended Fixtures:**
```python
@pytest.fixture
def simple_domain():
    return [('field', '=', 'value')]

@pytest.fixture
def and_domain():
    return ['&', ('a', '=', 1), ('b', '=', 2)]

@pytest.fixture
def complex_nested_domain():
    return ['|', '&', ('a', '=', 1), ('b', '=', 2), ('c', '=', 3)]
```

## Coverage

**Requirements:**
- No coverage configured
- No coverage targets

**Configuration:**
- Not applicable

**Recommended Setup:**
```bash
pip install pytest-cov
pytest --cov=main --cov-report=html tests/
```

## Test Types

**Unit Tests:**
- Not implemented
- Critical need: Test `convert_odoo_domain_to_python()` and `convert_odoo_domain_to_pseudocode()`

**Integration Tests:**
- Not implemented
- Lower priority for this simple application

**E2E Tests:**
- Not implemented
- Would require GUI testing framework (e.g., pytest-qt or similar)

## Common Patterns

**Async Testing:**
- Not applicable (no async code)

**Error Testing:**
- Not implemented
- Recommended:
```python
def test_invalid_input_handling():
    # Test that malformed input is handled gracefully
    domain = "not a list"
    # Should raise or handle appropriately
```

**Snapshot Testing:**
- Not used
- Could be useful for regression testing converter output

---

*Testing analysis: 2026-01-17*
*Update when test patterns change*
