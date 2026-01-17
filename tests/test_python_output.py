"""Tests for Python output in Odoo domain converter.

These tests verify that convert_odoo_domain_to_python() correctly:
- Keeps field names in snake_case (Python style)
- Uses Python comparison operators (==, !=, >, <, in, not in, etc.)
- Keeps dynamic references as Python variables (e.g., user.id)
"""

import pytest

from polish_converter import (
    convert_odoo_domain_to_python,
    parse_domain,
    DynamicRef,
)
from polish_converter.humanizer import to_readable_text


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


class TestPythonOutputFieldNames:
    """Tests for field names in Python output - kept as snake_case."""

    def test_create_uid_field(self):
        """create_uid stays as create_uid in Python output."""
        domain = parse_domain("[('create_uid', '=', 1)]")
        result = convert_odoo_domain_to_python(domain)
        assert "create_uid" in result
        assert "Created By" not in result

    def test_write_date_field(self):
        """write_date stays as write_date in Python output."""
        domain = parse_domain("[('write_date', '>', '2024-01-01')]")
        result = convert_odoo_domain_to_python(domain)
        assert "write_date" in result
        assert "Last Updated On" not in result

    def test_active_field(self):
        """active field stays as active in Python output."""
        domain = parse_domain("[('active', '=', True)]")
        result = convert_odoo_domain_to_python(domain)
        assert "active" in result
        assert "(active ==" in result

    def test_company_id_field(self):
        """company_id stays as company_id in Python output."""
        domain = parse_domain("[('company_id', '=', 1)]")
        result = convert_odoo_domain_to_python(domain)
        assert "company_id" in result
        assert "Company" not in result

    def test_user_ids_field(self):
        """user_ids stays as user_ids in Python output."""
        domain = parse_domain("[('user_ids', 'in', [1, 2])]")
        result = convert_odoo_domain_to_python(domain)
        assert "user_ids" in result
        assert "Users" not in result

    def test_dotted_path_field(self):
        """Dotted path stays as-is with underscores."""
        domain = parse_domain("[('project_id.name', '=', 'Test')]")
        result = convert_odoo_domain_to_python(domain)
        assert "project_id.name" in result
        assert "Project's Name" not in result


class TestPythonOutputDynamicRef:
    """Tests for DynamicRef in Python output - kept as Python variables."""

    def test_user_id_ref(self):
        """user.id stays as user.id in Python output."""
        domain = parse_domain("[('user_id', '=', user.id)]")
        result = convert_odoo_domain_to_python(domain)
        assert "user.id" in result
        assert "current user" not in result

    def test_user_company_ids_ref(self):
        """user.company_ids stays as Python variable."""
        domain = parse_domain("[('company_id', 'in', user.company_ids)]")
        result = convert_odoo_domain_to_python(domain)
        assert "user.company_ids" in result
        assert "current user's Companies" not in result

    def test_user_partner_id_ref(self):
        """user.partner_id.id stays as Python variable."""
        domain = parse_domain("[('partner_id', '=', user.partner_id.id)]")
        result = convert_odoo_domain_to_python(domain)
        assert "user.partner_id.id" in result
        assert "current user's Partner" not in result


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
    """Integration tests for complete Python output."""

    def test_create_uid_with_user_id(self):
        """Complete conversion: create_uid = user.id."""
        domain = parse_domain("[('create_uid', '=', user.id)]")
        result = convert_odoo_domain_to_python(domain)
        assert result == "(create_uid == user.id)"

    def test_or_condition_with_refs(self):
        """OR condition with user references."""
        domain = parse_domain("['|', ('user_id', '=', user.id), ('company_id', 'in', user.company_ids)]")
        result = convert_odoo_domain_to_python(domain)
        assert "user_id ==" in result
        assert "user.id" in result
        assert "company_id in" in result
        assert "user.company_ids" in result
        assert " or " in result

    def test_complex_dotted_path(self):
        """Dotted path with privacy_visibility."""
        domain = parse_domain("[('project_id.privacy_visibility', '=', 'followers')]")
        result = convert_odoo_domain_to_python(domain)
        assert "project_id.privacy_visibility" in result
        assert "'followers'" in result

    def test_active_false(self):
        """Active = False with Python output."""
        domain = parse_domain("[('active', '=', False)]")
        result = convert_odoo_domain_to_python(domain)
        assert result == "(active == False)"


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
        """'in' operator used for Python output."""
        domain = parse_domain("[('company_id', 'in', [1, 2, 3])]")
        result = convert_odoo_domain_to_python(domain)
        assert " in " in result
        assert "[1, 2, 3]" in result


class TestPythonOutputOperators:
    """Tests for Python comparison operators."""

    def test_equals_operator(self):
        """= becomes '=='."""
        domain = parse_domain("[('name', '=', 'Test')]")
        result = convert_odoo_domain_to_python(domain)
        assert " == " in result
        assert "equals" not in result

    def test_not_equals_operator(self):
        """!= stays as '!='."""
        domain = parse_domain("[('name', '!=', 'Test')]")
        result = convert_odoo_domain_to_python(domain)
        assert " != " in result
        assert "doesn't equal" not in result

    def test_greater_than_operator(self):
        """> stays as '>'."""
        domain = parse_domain("[('amount', '>', 100)]")
        result = convert_odoo_domain_to_python(domain)
        assert " > " in result
        assert "is greater than" not in result

    def test_less_than_operator(self):
        """< stays as '<'."""
        domain = parse_domain("[('amount', '<', 100)]")
        result = convert_odoo_domain_to_python(domain)
        assert " < " in result
        assert "is less than" not in result

    def test_greater_equal_operator(self):
        """>= stays as '>='."""
        domain = parse_domain("[('amount', '>=', 100)]")
        result = convert_odoo_domain_to_python(domain)
        assert " >= " in result
        assert "is at least" not in result

    def test_less_equal_operator(self):
        """<= stays as '<='."""
        domain = parse_domain("[('amount', '<=', 100)]")
        result = convert_odoo_domain_to_python(domain)
        assert " <= " in result
        assert "is at most" not in result

    def test_in_operator(self):
        """'in' stays as 'in'."""
        domain = parse_domain("[('state', 'in', ['draft', 'cancel'])]")
        result = convert_odoo_domain_to_python(domain)
        assert " in " in result
        assert "is in" not in result

    def test_not_in_operator(self):
        """'not in' stays as 'not in'."""
        domain = parse_domain("[('state', 'not in', ['draft', 'cancel'])]")
        result = convert_odoo_domain_to_python(domain)
        assert " not in " in result
        assert "is not in" not in result

    def test_like_operator(self):
        """'like' stays as 'like' (Odoo-specific)."""
        domain = parse_domain("[('name', 'like', '%test%')]")
        result = convert_odoo_domain_to_python(domain)
        assert " like " in result
        assert "is like" not in result

    def test_ilike_operator(self):
        """'ilike' stays as 'ilike' (Odoo-specific)."""
        domain = parse_domain("[('name', 'ilike', '%test%')]")
        result = convert_odoo_domain_to_python(domain)
        assert " ilike " in result
        assert "is like (case-insensitive)" not in result

    def test_child_of_operator(self):
        """'child_of' stays as 'child_of' (Odoo-specific)."""
        domain = parse_domain("[('parent_id', 'child_of', 1)]")
        result = convert_odoo_domain_to_python(domain)
        assert " child_of " in result
        assert "is child of" not in result

    def test_parent_of_operator(self):
        """'parent_of' stays as 'parent_of' (Odoo-specific)."""
        domain = parse_domain("[('id', 'parent_of', [1, 2])]")
        result = convert_odoo_domain_to_python(domain)
        assert " parent_of " in result
        assert "is parent of" not in result
