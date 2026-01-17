"""Tests for Python output humanization in Odoo domain converter.

These tests verify that convert_odoo_domain_to_python() correctly:
- Applies field humanization with Python-safe identifiers (PYOUT-01)
- Maintains readable Python-like syntax (PYOUT-02)
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
    to_python_identifier,
)


class TestToPythonIdentifier:
    """Tests for to_python_identifier helper function."""

    def test_spaces_to_underscores(self):
        """Spaces should be converted to underscores."""
        assert to_python_identifier("Created By") == "Created_By"

    def test_current_user(self):
        """'current user' becomes 'current_user'."""
        assert to_python_identifier("current user") == "current_user"

    def test_possessive_preserved(self):
        """Apostrophes in possessive form preserved."""
        assert to_python_identifier("current user's Partner") == "current_user's_Partner"

    def test_already_python_safe(self):
        """Already Python-safe strings unchanged."""
        assert to_python_identifier("Active") == "Active"

    def test_multiple_spaces(self):
        """Multiple spaces converted to multiple underscores."""
        assert to_python_identifier("Last Updated On") == "Last_Updated_On"


class TestPythonOutputSystemFields:
    """Tests for system field humanization in Python output (PYOUT-01)."""

    def test_create_uid_field(self):
        """create_uid becomes Created_By in Python output."""
        domain = parse_domain("[('create_uid', '=', 1)]")
        result = convert_odoo_domain_to_python(domain)
        assert "Created_By" in result
        assert "create_uid" not in result

    def test_write_date_field(self):
        """write_date becomes Last_Updated_On in Python output."""
        domain = parse_domain("[('write_date', '>', '2024-01-01')]")
        result = convert_odoo_domain_to_python(domain)
        assert "Last_Updated_On" in result
        assert "write_date" not in result

    def test_active_field(self):
        """active field becomes Active in Python output."""
        domain = parse_domain("[('active', '=', True)]")
        result = convert_odoo_domain_to_python(domain)
        assert "Active" in result
        # Note: 'active' can appear in 'Active' so we check the field is humanized
        assert "(Active ==" in result


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
        """Dotted path becomes possessive form with underscores."""
        domain = parse_domain("[('project_id.name', '=', 'Test')]")
        result = convert_odoo_domain_to_python(domain)
        assert "Project's_Name" in result
        assert "project_id.name" not in result


class TestPythonOutputDynamicRef:
    """Tests for DynamicRef humanization in Python output (PYOUT-02)."""

    def test_user_id_ref(self):
        """user.id becomes current_user in Python output."""
        domain = parse_domain("[('user_id', '=', user.id)]")
        result = convert_odoo_domain_to_python(domain)
        assert "current_user" in result
        assert "user.id" not in result

    def test_user_company_ids_ref(self):
        """user.company_ids becomes current_user's_Companies."""
        domain = parse_domain("[('company_id', 'in', user.company_ids)]")
        result = convert_odoo_domain_to_python(domain)
        assert "current_user's_Companies" in result
        assert "user.company_ids" not in result

    def test_user_partner_id_ref(self):
        """user.partner_id.id becomes current_user's_Partner."""
        domain = parse_domain("[('partner_id', '=', user.partner_id.id)]")
        result = convert_odoo_domain_to_python(domain)
        assert "current_user's_Partner" in result


class TestPythonOutputValues:
    """Tests for value handling in Python output - values stay Python-valid."""

    def test_false_stays_false(self):
        """False remains as False (valid Python) - differs from pseudocode."""
        domain = parse_domain("[('active', '=', False)]")
        result = convert_odoo_domain_to_python(domain)
        assert "False" in result
        assert "Not_Set" not in result

    def test_none_stays_none(self):
        """None remains as None (valid Python) - differs from pseudocode."""
        domain = parse_domain("[('partner_id', '=', None)]")
        result = convert_odoo_domain_to_python(domain)
        assert "None" in result
        assert "Not_Set" not in result

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
        assert result == "(Created_By == current_user)"

    def test_or_condition_with_refs(self):
        """OR condition with user references."""
        domain = parse_domain("['|', ('user_id', '=', user.id), ('company_id', 'in', user.company_ids)]")
        result = convert_odoo_domain_to_python(domain)
        assert "User ==" in result
        assert "current_user" in result
        assert "Company in" in result
        assert "current_user's_Companies" in result
        assert " or " in result

    def test_complex_dotted_path(self):
        """Dotted path with privacy_visibility."""
        domain = parse_domain("[('project_id.privacy_visibility', '=', 'followers')]")
        result = convert_odoo_domain_to_python(domain)
        assert "Project's_Privacy_Visibility" in result
        assert "'followers'" in result

    def test_active_false(self):
        """Active = False with Python-valid output."""
        domain = parse_domain("[('active', '=', False)]")
        result = convert_odoo_domain_to_python(domain)
        assert result == "(Active == False)"


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
        """'in' operator preserved."""
        domain = parse_domain("[('company_id', 'in', [1, 2, 3])]")
        result = convert_odoo_domain_to_python(domain)
        assert " in " in result
        assert "[1, 2, 3]" in result
