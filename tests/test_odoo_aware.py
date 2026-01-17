"""Tests for Odoo-aware output in domain converter.

These tests verify:
- ODOO-01: System field mappings (create_uid -> "Created By", etc.)
- ODOO-02: User reference humanization (user.id -> "current user", etc.)
- VALUE-01: False/None render as "Not set"
- VALUE-02: (1, '=', 1) renders as "Always True (all records)"
- VALUE-03: (0, '=', 1) renders as "Always False (no records)"
"""

import pytest
import sys
import os

# Add parent directory to path to import main
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import (
    get_system_field_label,
    humanize_dynamic_ref,
    DynamicRef,
    convert_odoo_domain_to_pseudocode,
    parse_domain,
)


class TestSystemFieldLabels:
    """Tests for system field label mappings (ODOO-01)."""

    def test_create_uid(self):
        """create_uid maps to 'Created By'."""
        assert get_system_field_label("create_uid") == "Created By"

    def test_write_uid(self):
        """write_uid maps to 'Last Updated By'."""
        assert get_system_field_label("write_uid") == "Last Updated By"

    def test_create_date(self):
        """create_date maps to 'Created On'."""
        assert get_system_field_label("create_date") == "Created On"

    def test_write_date(self):
        """write_date maps to 'Last Updated On'."""
        assert get_system_field_label("write_date") == "Last Updated On"

    def test_active(self):
        """active maps to 'Active'."""
        assert get_system_field_label("active") == "Active"

    def test_id(self):
        """id maps to 'ID'."""
        assert get_system_field_label("id") == "ID"

    def test_display_name(self):
        """display_name maps to 'Display Name'."""
        assert get_system_field_label("display_name") == "Display Name"

    def test_name_not_system_field(self):
        """name is not a system field, returns None."""
        assert get_system_field_label("name") is None

    def test_custom_field_not_system(self):
        """Custom fields return None."""
        assert get_system_field_label("custom_field") is None

    def test_empty_string(self):
        """Empty string returns None."""
        assert get_system_field_label("") is None


class TestHumanizeDynamicRef:
    """Tests for user reference humanization (ODOO-02)."""

    def test_user_id(self):
        """user.id becomes 'current user'."""
        ref = DynamicRef("user.id")
        assert humanize_dynamic_ref(ref) == "current user"

    def test_user_partner_id_id(self):
        """user.partner_id.id becomes 'current user's Partner'."""
        ref = DynamicRef("user.partner_id.id")
        assert humanize_dynamic_ref(ref) == "current user's Partner"

    def test_user_partner_id(self):
        """user.partner_id becomes 'current user's Partner'."""
        ref = DynamicRef("user.partner_id")
        assert humanize_dynamic_ref(ref) == "current user's Partner"

    def test_user_groups_id_ids(self):
        """user.groups_id.ids becomes 'current user's Groups'."""
        ref = DynamicRef("user.groups_id.ids")
        assert humanize_dynamic_ref(ref) == "current user's Groups"

    def test_user_company_id_id(self):
        """user.company_id.id becomes 'current user's Company'."""
        ref = DynamicRef("user.company_id.id")
        assert humanize_dynamic_ref(ref) == "current user's Company"

    def test_user_company_ids(self):
        """user.company_ids becomes 'current user's Companies'."""
        ref = DynamicRef("user.company_ids")
        assert humanize_dynamic_ref(ref) == "current user's Companies"

    def test_non_user_ref_unchanged(self):
        """Non-user references return as-is."""
        ref = DynamicRef("company_ids")
        assert humanize_dynamic_ref(ref) == "company_ids"

    def test_complex_ref_unchanged(self):
        """Complex references (with function calls) return as-is."""
        ref = DynamicRef("context.get('active_id')")
        assert humanize_dynamic_ref(ref) == "context.get('active_id')"


class TestValueHumanization:
    """Tests for False/None humanization in pseudocode (VALUE-01)."""

    def test_false_becomes_not_set(self):
        """False renders as 'Not set' in pseudocode."""
        domain = parse_domain("[('parent_id', '=', False)]")
        result = convert_odoo_domain_to_pseudocode(domain)
        assert "Not set" in result
        assert "False" not in result

    def test_none_becomes_not_set(self):
        """None renders as 'Not set' in pseudocode."""
        domain = parse_domain("[('field', '=', None)]")
        result = convert_odoo_domain_to_pseudocode(domain)
        assert "Not set" in result
        assert "None" not in result

    def test_true_unchanged(self):
        """True remains 'True' in pseudocode."""
        domain = parse_domain("[('active', '=', True)]")
        result = convert_odoo_domain_to_pseudocode(domain)
        assert "True" in result

    def test_other_values_unchanged(self):
        """Other values remain unchanged."""
        domain = parse_domain("[('amount', '=', 100)]")
        result = convert_odoo_domain_to_pseudocode(domain)
        assert "100" in result


class TestTautologyPatterns:
    """Tests for tautology pattern recognition (VALUE-02, VALUE-03)."""

    def test_one_equals_one_always_true(self):
        """(1, '=', 1) renders as 'Always True (all records)'."""
        domain = parse_domain("[(1, '=', 1)]")
        result = convert_odoo_domain_to_pseudocode(domain)
        assert "Always True (all records)" in result

    def test_zero_equals_one_always_false(self):
        """(0, '=', 1) renders as 'Always False (no records)'."""
        domain = parse_domain("[(0, '=', 1)]")
        result = convert_odoo_domain_to_pseudocode(domain)
        assert "Always False (no records)" in result

    def test_string_one_equals_string_one(self):
        """('1', '=', '1') also renders as Always True."""
        domain = parse_domain("[('1', '=', '1')]")
        result = convert_odoo_domain_to_pseudocode(domain)
        assert "Always True (all records)" in result

    def test_string_zero_equals_string_one(self):
        """('0', '=', '1') also renders as Always False."""
        domain = parse_domain("[('0', '=', '1')]")
        result = convert_odoo_domain_to_pseudocode(domain)
        assert "Always False (no records)" in result


class TestIntegrationOdooAware:
    """Integration tests for Odoo-aware pseudocode output."""

    def test_system_field_with_user_ref(self):
        """System field with user reference fully humanized."""
        domain = parse_domain("[('create_uid', '=', user.id)]")
        result = convert_odoo_domain_to_pseudocode(domain)
        assert "Created By" in result
        assert "current user" in result
        assert "create_uid" not in result
        assert "user.id" not in result

    def test_active_false(self):
        """Active field with False value fully humanized."""
        domain = parse_domain("[('active', '=', False)]")
        result = convert_odoo_domain_to_pseudocode(domain)
        assert "Active" in result
        assert "Not set" in result

    def test_tautology_in_complex_domain(self):
        """Tautology recognized in complex domain."""
        domain = parse_domain("['|', ('user_id', '=', user.id), (1, '=', 1)]")
        result = convert_odoo_domain_to_pseudocode(domain)
        assert "Always True (all records)" in result
        assert "current user" in result

    def test_complex_domain_with_user_refs(self):
        """Complex domain with multiple user references."""
        domain = parse_domain("['|', ('user_id', '=', user.id), ('company_id', 'in', user.company_ids)]")
        result = convert_odoo_domain_to_pseudocode(domain)
        assert "current user" in result
        assert "current user's Companies" in result
        assert "user.id" not in result
        assert "user.company_ids" not in result

    def test_write_uid_with_user_partner(self):
        """Write UID compared to user's partner."""
        domain = parse_domain("[('write_uid', '=', user.partner_id.id)]")
        result = convert_odoo_domain_to_pseudocode(domain)
        assert "Last Updated By" in result
        assert "current user's Partner" in result
