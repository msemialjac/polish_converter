"""Tests for field humanization in Odoo domain converter.

These tests verify that humanize_field() correctly:
- Converts snake_case to Title Case (FIELD-01)
- Strips _id suffix (FIELD-02)
- Strips _ids suffix (FIELD-03)
- Humanizes dotted paths with possessive form (FIELD-04)
"""

import pytest

from polish_converter import humanize_field, convert_odoo_domain_to_pseudocode, parse_domain


class TestHumanizeFieldBasic:
    """Tests for basic field name humanization (FIELD-01)."""

    def test_single_word_lowercase(self):
        """Single word field converts to Title Case."""
        assert humanize_field("active") == "Active"

    def test_snake_case_multiple_words(self):
        """Snake_case field converts to Title Case with spaces."""
        assert humanize_field("privacy_visibility") == "Privacy Visibility"

    def test_already_title_case_with_underscore(self):
        """Already Title Case with underscore handles correctly."""
        assert humanize_field("Privacy_Visibility") == "Privacy Visibility"

    def test_single_char_segment(self):
        """Single character segments (like x_ custom fields) handle correctly."""
        assert humanize_field("x_field") == "X Field"

    def test_numbers_in_field_name(self):
        """Numbers in field names preserved."""
        assert humanize_field("field_2_name") == "Field 2 Name"


class TestHumanizeFieldIdSuffix:
    """Tests for _id suffix stripping (FIELD-02)."""

    def test_simple_id_suffix(self):
        """Simple _id suffix is stripped."""
        assert humanize_field("company_id") == "Company"

    def test_snake_case_ending_in_id(self):
        """Snake_case field ending in _id strips suffix."""
        assert humanize_field("partner_shipping_id") == "Partner Shipping"

    def test_id_alone(self):
        """Field named just 'id' should become 'Id' (edge case)."""
        # This is an edge case - 'id' alone shouldn't be stripped
        assert humanize_field("id") == "Id"


class TestHumanizeFieldIdsSuffix:
    """Tests for _ids suffix stripping (FIELD-03)."""

    def test_simple_ids_suffix(self):
        """Simple _ids suffix is stripped and pluralized."""
        assert humanize_field("group_ids") == "Groups"

    def test_snake_case_ending_in_ids(self):
        """Snake_case field ending in _ids strips suffix and pluralizes."""
        assert humanize_field("allowed_company_ids") == "Allowed Companies"

    def test_company_to_companies(self):
        """Company becomes Companies (special plural)."""
        assert humanize_field("company_ids") == "Companies"

    def test_user_to_users(self):
        """Regular plural just adds s."""
        assert humanize_field("user_ids") == "Users"


class TestHumanizeFieldDottedPaths:
    """Tests for dotted path humanization with possessive form (FIELD-04)."""

    def test_simple_dotted_path(self):
        """Simple dotted path with possessive form."""
        assert humanize_field("project_id.name") == "Project's Name"

    def test_dotted_path_with_suffix_stripping(self):
        """Dotted path strips _id suffix from first segment."""
        assert humanize_field("project_id.privacy_visibility") == "Project's Privacy Visibility"

    def test_multiple_dots(self):
        """Multiple dots with multiple possessives."""
        assert humanize_field("account_id.partner_id.name") == "Account's Partner's Name"

    def test_dotted_path_ending_in_id(self):
        """Dotted path where last segment ends in _id."""
        assert humanize_field("order_id.partner_id") == "Order's Partner"

    def test_three_segment_path(self):
        """Three segment path with possessives."""
        assert humanize_field("user_id.partner_id.company_id") == "User's Partner's Company"


class TestHumanizeFieldIntegration:
    """Integration tests: humanization in pseudocode output."""

    def test_pseudocode_simple_field(self):
        """Pseudocode output uses humanized field names."""
        domain = parse_domain("[('privacy_visibility', '=', 'employees')]")
        result = convert_odoo_domain_to_pseudocode(domain)
        assert "Privacy Visibility" in result
        assert "privacy_visibility" not in result.lower() or "privacy visibility" in result.lower()

    def test_pseudocode_id_field(self):
        """Pseudocode output strips _id suffix."""
        domain = parse_domain("[('company_id', '=', 1)]")
        result = convert_odoo_domain_to_pseudocode(domain)
        assert "Company equals 1" in result
        # Should not contain raw "company_id"
        assert "company_id" not in result

    def test_pseudocode_dotted_path(self):
        """Pseudocode output humanizes dotted paths."""
        domain = parse_domain("[('project_id.privacy_visibility', '=', 'portal')]")
        result = convert_odoo_domain_to_pseudocode(domain)
        assert "Project's Privacy Visibility" in result


class TestHumanizeFieldEdgeCases:
    """Edge cases for field humanization."""

    def test_empty_string(self):
        """Empty string returns empty string."""
        assert humanize_field("") == ""

    def test_underscore_only(self):
        """Single underscore handles gracefully."""
        # Edge case - should not crash
        result = humanize_field("_")
        assert isinstance(result, str)

    def test_multiple_underscores(self):
        """Multiple consecutive underscores handle correctly."""
        # Should collapse to single space
        assert humanize_field("field__name") == "Field Name"

    def test_leading_underscore(self):
        """Leading underscore (private field convention) handled."""
        assert humanize_field("_private_field") == "Private Field"

    def test_trailing_underscore(self):
        """Trailing underscore handled."""
        result = humanize_field("field_")
        assert isinstance(result, str)
