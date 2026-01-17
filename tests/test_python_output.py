"""Tests for Python output humanization in Odoo domain converter.

These tests verify that convert_odoo_domain_to_python() correctly:
- Applies field humanization with readable text (PYOUT-01)
- Maintains readable Python-like syntax with humanized operators (PYOUT-02)
"""

import pytest
import sys
import os

# Add parent directory to path to import main
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import (
    convert_odoo_domain_to_python,
    parse_domain,
    DynamicRef,
    to_readable_text,
)


class TestToReadableText:
    """Tests for to_readable_text helper function."""

    def test_spaces_preserved(self):
        """Spaces should be preserved (not converted to underscores)."""
        assert to_readable_text("Created By") == "Created By"

    def test_current_user(self):
        """'current user' stays as 'current user'."""
        assert to_readable_text("current user") == "current user"

    def test_possessive_preserved(self):
        """Apostrophes in possessive form preserved."""
        assert to_readable_text("current user's Partner") == "current user's Partner"

    def test_already_simple(self):
        """Simple strings unchanged."""
        assert to_readable_text("Active") == "Active"

    def test_multiple_spaces(self):
        """Multiple spaces preserved."""
        assert to_readable_text("Last Updated On") == "Last Updated On"


class TestPythonOutputSystemFields:
    """Tests for system field humanization in Python output (PYOUT-01)."""

    def test_create_uid_field(self):
        """create_uid becomes Created By in Python output."""
        domain = parse_domain("[('create_uid', '=', 1)]")
        result = convert_odoo_domain_to_python(domain)
        assert "Created By" in result
        assert "create_uid" not in result

    def test_write_date_field(self):
        """write_date becomes Last Updated On in Python output."""
        domain = parse_domain("[('write_date', '>', '2024-01-01')]")
        result = convert_odoo_domain_to_python(domain)
        assert "Last Updated On" in result
        assert "write_date" not in result

    def test_active_field(self):
        """active field becomes Active in Python output."""
        domain = parse_domain("[('active', '=', True)]")
        result = convert_odoo_domain_to_python(domain)
        assert "Active" in result
        assert "(Active equals" in result


class TestPythonOutputFieldHumanization:
    """Tests for regular field humanization in Python output (PYOUT-01)."""

    def test_company_id_field(self):
        """company_id becomes Company in Python output."""
        domain = parse_domain("[('company_id', '=', 1)]")
        result = convert_odoo_domain_to_python(domain)
        assert "Company" in result
        assert "company_id" not in result

    def test_user_ids_field(self):
        """user_ids becomes Users in Python output."""
        domain = parse_domain("[('user_ids', 'in', [1, 2])]")
        result = convert_odoo_domain_to_python(domain)
        assert "Users" in result
        assert "user_ids" not in result

    def test_dotted_path_field(self):
        """Dotted path becomes possessive form with spaces."""
        domain = parse_domain("[('project_id.name', '=', 'Test')]")
        result = convert_odoo_domain_to_python(domain)
        assert "Project's Name" in result
        assert "project_id.name" not in result


class TestPythonOutputDynamicRef:
    """Tests for DynamicRef humanization in Python output (PYOUT-02)."""

    def test_user_id_ref(self):
        """user.id becomes current user in Python output."""
        domain = parse_domain("[('user_id', '=', user.id)]")
        result = convert_odoo_domain_to_python(domain)
        assert "current user" in result
        assert "user.id" not in result

    def test_user_company_ids_ref(self):
        """user.company_ids becomes current user's Companies."""
        domain = parse_domain("[('company_id', 'in', user.company_ids)]")
        result = convert_odoo_domain_to_python(domain)
        assert "current user's Companies" in result
        assert "user.company_ids" not in result

    def test_user_partner_id_ref(self):
        """user.partner_id.id becomes current user's Partner."""
        domain = parse_domain("[('partner_id', '=', user.partner_id.id)]")
        result = convert_odoo_domain_to_python(domain)
        assert "current user's Partner" in result


class TestPythonOutputValues:
    """Tests for value handling in Python output - values stay Python-valid."""

    def test_false_stays_false(self):
        """False remains as False (valid Python) - differs from pseudocode."""
        domain = parse_domain("[('active', '=', False)]")
        result = convert_odoo_domain_to_python(domain)
        assert "False" in result
        assert "Not Set" not in result

    def test_none_stays_none(self):
        """None remains as None (valid Python) - differs from pseudocode."""
        domain = parse_domain("[('partner_id', '=', None)]")
        result = convert_odoo_domain_to_python(domain)
        assert "None" in result
        assert "Not Set" not in result

    def test_true_stays_true(self):
        """True remains as True (valid Python)."""
        domain = parse_domain("[('active', '=', True)]")
        result = convert_odoo_domain_to_python(domain)
        assert "True" in result


class TestPythonOutputIntegration:
    """Integration tests for complete Python output humanization."""

    def test_create_uid_with_user_id(self):
        """Complete conversion: create_uid = user.id."""
        domain = parse_domain("[('create_uid', '=', user.id)]")
        result = convert_odoo_domain_to_python(domain)
        assert result == "(Created By equals current user)"

    def test_or_condition_with_refs(self):
        """OR condition with user references."""
        domain = parse_domain("['|', ('user_id', '=', user.id), ('company_id', 'in', user.company_ids)]")
        result = convert_odoo_domain_to_python(domain)
        assert "User equals" in result
        assert "current user" in result
        assert "Company is in" in result
        assert "current user's Companies" in result
        assert " or " in result

    def test_complex_dotted_path(self):
        """Dotted path with privacy_visibility."""
        domain = parse_domain("[('project_id.privacy_visibility', '=', 'followers')]")
        result = convert_odoo_domain_to_python(domain)
        assert "Project's Privacy Visibility" in result
        assert "'followers'" in result

    def test_active_false(self):
        """Active = False with readable output."""
        domain = parse_domain("[('active', '=', False)]")
        result = convert_odoo_domain_to_python(domain)
        assert result == "(Active equals False)"


class TestPythonOutputStructurePreserved:
    """Tests that Python output structure is preserved."""

    def test_parentheses_preserved(self):
        """Parentheses are preserved in output."""
        domain = parse_domain("[('active', '=', True)]")
        result = convert_odoo_domain_to_python(domain)
        assert result.startswith("(")
        assert result.endswith(")")

    def test_and_operator(self):
        """'and' operator preserved."""
        domain = parse_domain("[('active', '=', True), ('company_id', '=', 1)]")
        result = convert_odoo_domain_to_python(domain)
        assert " and " in result

    def test_or_operator(self):
        """'or' operator preserved."""
        domain = parse_domain("['|', ('active', '=', True), ('company_id', '=', 1)]")
        result = convert_odoo_domain_to_python(domain)
        assert " or " in result

    def test_not_operator(self):
        """'not' operator preserved."""
        domain = parse_domain("['!', ('active', '=', True)]")
        result = convert_odoo_domain_to_python(domain)
        assert "not " in result

    def test_in_operator(self):
        """'is in' operator used for readable output."""
        domain = parse_domain("[('company_id', 'in', [1, 2, 3])]")
        result = convert_odoo_domain_to_python(domain)
        assert " is in " in result
        assert "[1, 2, 3]" in result


class TestPythonOutputReadableOperators:
    """Tests for readable operator output."""

    def test_equals_operator(self):
        """= becomes 'equals'."""
        domain = parse_domain("[('name', '=', 'Test')]")
        result = convert_odoo_domain_to_python(domain)
        assert " equals " in result

    def test_not_equals_operator(self):
        """!= becomes \"doesn't equal\"."""
        domain = parse_domain("[('name', '!=', 'Test')]")
        result = convert_odoo_domain_to_python(domain)
        assert "doesn't equal" in result

    def test_greater_than_operator(self):
        """> becomes 'is greater than'."""
        domain = parse_domain("[('amount', '>', 100)]")
        result = convert_odoo_domain_to_python(domain)
        assert "is greater than" in result

    def test_less_than_operator(self):
        """< becomes 'is less than'."""
        domain = parse_domain("[('amount', '<', 100)]")
        result = convert_odoo_domain_to_python(domain)
        assert "is less than" in result

    def test_greater_equal_operator(self):
        """>= becomes 'is at least'."""
        domain = parse_domain("[('amount', '>=', 100)]")
        result = convert_odoo_domain_to_python(domain)
        assert "is at least" in result

    def test_less_equal_operator(self):
        """<= becomes 'is at most'."""
        domain = parse_domain("[('amount', '<=', 100)]")
        result = convert_odoo_domain_to_python(domain)
        assert "is at most" in result

    def test_not_in_operator(self):
        """'not in' becomes 'is not in'."""
        domain = parse_domain("[('state', 'not in', ['draft', 'cancel'])]")
        result = convert_odoo_domain_to_python(domain)
        assert "is not in" in result

    def test_like_operator(self):
        """'like' becomes 'is like'."""
        domain = parse_domain("[('name', 'like', '%test%')]")
        result = convert_odoo_domain_to_python(domain)
        assert "is like" in result

    def test_ilike_operator(self):
        """'ilike' becomes 'is like (case-insensitive)'."""
        domain = parse_domain("[('name', 'ilike', '%test%')]")
        result = convert_odoo_domain_to_python(domain)
        assert "is like (case-insensitive)" in result

    def test_child_of_operator(self):
        """'child_of' becomes 'is child of'."""
        domain = parse_domain("[('parent_id', 'child_of', 1)]")
        result = convert_odoo_domain_to_python(domain)
        assert "is child of" in result

    def test_parent_of_operator(self):
        """'parent_of' becomes 'is parent of'."""
        domain = parse_domain("[('id', 'parent_of', [1, 2])]")
        result = convert_odoo_domain_to_python(domain)
        assert "is parent of" in result
