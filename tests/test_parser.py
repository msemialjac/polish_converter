"""Tests for the custom Odoo domain parser.

These tests verify that parse_domain() correctly handles:
- Standard Odoo domains (matching ast.literal_eval behavior)
- Dynamic references (user.id, company_ids, etc.)
- Dotted paths (user.partner_id.id)
- Multi-line strings
- All Python literal types (strings, numbers, booleans, None, lists, tuples)
"""

import pytest
import sys
import os

# Add parent directory to path to import main
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import parse_domain, DynamicRef


class TestDynamicRef:
    """Tests for the DynamicRef class."""

    def test_init_stores_name(self):
        """DynamicRef stores the variable name."""
        ref = DynamicRef("user.id")
        assert ref.name == "user.id"

    def test_repr_returns_name(self):
        """DynamicRef repr returns just the name."""
        ref = DynamicRef("user.id")
        assert repr(ref) == "user.id"

    def test_str_returns_name(self):
        """DynamicRef str returns just the name."""
        ref = DynamicRef("company_ids")
        assert str(ref) == "company_ids"

    def test_equality_with_same_name(self):
        """Two DynamicRefs with same name are equal."""
        ref1 = DynamicRef("user.id")
        ref2 = DynamicRef("user.id")
        assert ref1 == ref2

    def test_inequality_with_different_name(self):
        """Two DynamicRefs with different names are not equal."""
        ref1 = DynamicRef("user.id")
        ref2 = DynamicRef("company_ids")
        assert ref1 != ref2

    def test_inequality_with_string(self):
        """DynamicRef is not equal to a plain string."""
        ref = DynamicRef("user.id")
        assert ref != "user.id"


class TestParseStandardDomains:
    """Tests for parsing standard domains that ast.literal_eval handles."""

    def test_simple_string_condition(self):
        """Parse simple string condition."""
        result = parse_domain("[('field', '=', 'value')]")
        assert result == [("field", "=", "value")]

    def test_empty_domain(self):
        """Parse empty domain."""
        result = parse_domain("[]")
        assert result == []

    def test_boolean_true(self):
        """Parse domain with True value."""
        result = parse_domain("[('active', '=', True)]")
        assert result == [("active", "=", True)]

    def test_boolean_false(self):
        """Parse domain with False value."""
        result = parse_domain("[('parent_id', '=', False)]")
        assert result == [("parent_id", "=", False)]

    def test_none_value(self):
        """Parse domain with None value."""
        result = parse_domain("[('field', '=', None)]")
        assert result == [("field", "=", None)]

    def test_integer_value(self):
        """Parse domain with integer value."""
        result = parse_domain("[('amount', '>', 100)]")
        assert result == [("amount", ">", 100)]

    def test_negative_integer(self):
        """Parse domain with negative integer."""
        result = parse_domain("[('level', '=', -5)]")
        assert result == [("level", "=", -5)]

    def test_float_value(self):
        """Parse domain with float value."""
        result = parse_domain("[('rate', '<', 0.5)]")
        assert result == [("rate", "<", 0.5)]

    def test_nested_list_value(self):
        """Parse domain with nested list value."""
        result = parse_domain("[('state', 'in', ['draft', 'sent'])]")
        assert result == [("state", "in", ["draft", "sent"])]

    def test_multiple_conditions(self):
        """Parse domain with multiple conditions."""
        result = parse_domain("[('a', '=', 1), ('b', '=', 2)]")
        assert result == [("a", "=", 1), ("b", "=", 2)]

    def test_and_operator(self):
        """Parse domain with explicit AND operator."""
        result = parse_domain("['&', ('a', '=', 1), ('b', '=', 2)]")
        assert result == ["&", ("a", "=", 1), ("b", "=", 2)]

    def test_or_operator(self):
        """Parse domain with OR operator."""
        result = parse_domain("['|', ('a', '=', 1), ('b', '=', 2)]")
        assert result == ["|", ("a", "=", 1), ("b", "=", 2)]

    def test_not_operator(self):
        """Parse domain with NOT operator."""
        result = parse_domain("['!', ('active', '=', False)]")
        assert result == ["!", ("active", "=", False)]


class TestParseDynamicReferences:
    """Tests for parsing domains with dynamic references."""

    def test_simple_user_id(self):
        """Parse domain with user.id reference."""
        result = parse_domain("[('user_id', '=', user.id)]")
        assert len(result) == 1
        assert result[0][0] == "user_id"
        assert result[0][1] == "="
        assert isinstance(result[0][2], DynamicRef)
        assert result[0][2].name == "user.id"

    def test_dotted_path_reference(self):
        """Parse domain with dotted path reference."""
        result = parse_domain("[('partner_id', '=', user.partner_id.id)]")
        assert len(result) == 1
        assert isinstance(result[0][2], DynamicRef)
        assert result[0][2].name == "user.partner_id.id"

    def test_simple_variable_reference(self):
        """Parse domain with simple variable reference (no dots)."""
        result = parse_domain("[('company_id', 'in', company_ids)]")
        assert len(result) == 1
        assert isinstance(result[0][2], DynamicRef)
        assert result[0][2].name == "company_ids"

    def test_complex_domain_with_dynamic_refs(self):
        """Parse complex domain with operators and dynamic references."""
        result = parse_domain("['|', ('user_id', '=', user.id), ('company_id', 'in', company_ids)]")
        assert len(result) == 3
        assert result[0] == "|"
        assert isinstance(result[1][2], DynamicRef)
        assert result[1][2].name == "user.id"
        assert isinstance(result[2][2], DynamicRef)
        assert result[2][2].name == "company_ids"

    def test_mixed_static_and_dynamic(self):
        """Parse domain with both static values and dynamic references."""
        result = parse_domain("[('state', '=', 'active'), ('user_id', '=', user.id)]")
        assert len(result) == 2
        assert result[0] == ("state", "=", "active")
        assert isinstance(result[1][2], DynamicRef)


class TestParseMultilineStrings:
    """Tests for parsing multi-line domain strings."""

    def test_multiline_simple(self):
        """Parse multi-line domain string."""
        domain_str = """[
            ('field', '=', 'value'),
            ('other', '!=', False)
        ]"""
        result = parse_domain(domain_str)
        assert result == [("field", "=", "value"), ("other", "!=", False)]

    def test_multiline_with_dynamic_ref(self):
        """Parse multi-line domain with dynamic reference."""
        domain_str = """[
            ('user_id', '=', user.id),
            ('active', '=', True)
        ]"""
        result = parse_domain(domain_str)
        assert len(result) == 2
        assert isinstance(result[0][2], DynamicRef)
        assert result[1] == ("active", "=", True)


class TestParseMixedBooleanAndNone:
    """Tests for parsing domains with mixed boolean and None values."""

    def test_all_special_values(self):
        """Parse domain with True, False, and None values."""
        result = parse_domain("[('active', '=', True), ('parent_id', '=', False), ('field', '=', None)]")
        assert result == [
            ("active", "=", True),
            ("parent_id", "=", False),
            ("field", "=", None),
        ]


class TestParseNumericValues:
    """Tests for parsing domains with numeric values."""

    def test_mixed_numeric_values(self):
        """Parse domain with integer and float values."""
        result = parse_domain("[('amount', '>', 100), ('rate', '<', 0.5)]")
        assert result == [("amount", ">", 100), ("rate", "<", 0.5)]


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_deeply_nested_operators(self):
        """Parse domain with nested AND/OR operators."""
        result = parse_domain("['&', '|', ('a', '=', 1), ('b', '=', 2), ('c', '=', 3)]")
        assert result == ["&", "|", ("a", "=", 1), ("b", "=", 2), ("c", "=", 3)]

    def test_double_quoted_strings(self):
        """Parse domain with double-quoted strings."""
        result = parse_domain('[("field", "=", "value")]')
        assert result == [("field", "=", "value")]

    def test_mixed_quotes(self):
        """Parse domain with mixed single and double quotes."""
        result = parse_domain("""[('field1', '=', "value1"), ("field2", "=", 'value2')]""")
        assert result == [("field1", "=", "value1"), ("field2", "=", "value2")]

    def test_empty_string_value(self):
        """Parse domain with empty string value."""
        result = parse_domain("[('field', '=', '')]")
        assert result == [("field", "=", "")]

    def test_string_with_special_chars(self):
        """Parse domain with special characters in string."""
        result = parse_domain(r"[('field', 'like', '%test%')]")
        assert result == [("field", "like", "%test%")]

    def test_dotted_field_path(self):
        """Parse domain with dotted field in first position (static)."""
        result = parse_domain("[('partner_id.name', '=', 'Test')]")
        assert result == [("partner_id.name", "=", "Test")]
