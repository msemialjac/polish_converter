import FreeSimpleGUI as sg
import ast
import black
from enum import Enum, auto
from typing import Any


class DynamicRef:
    """Represents a dynamic reference in an Odoo domain (e.g., user.id, company_ids).

    This wrapper class distinguishes parsed variable references from regular strings,
    allowing the converter to handle domains containing dynamic references that
    ast.literal_eval() cannot parse.
    """

    def __init__(self, name: str):
        """Initialize with the variable reference name.

        Args:
            name: The full reference path (e.g., 'user.id', 'user.partner_id.id', 'company_ids')
        """
        self.name = name

    def __repr__(self) -> str:
        """Return the name for repr (used in output display)."""
        return self.name

    def __str__(self) -> str:
        """Return the name for string conversion."""
        return self.name

    def __eq__(self, other: object) -> bool:
        """Check equality with another DynamicRef."""
        return isinstance(other, DynamicRef) and self.name == other.name

    def __hash__(self) -> int:
        """Make DynamicRef hashable for use in sets/dicts."""
        return hash(self.name)


class TokenType(Enum):
    """Token types for the domain parser."""
    STRING = auto()
    NUMBER = auto()
    BOOL_TRUE = auto()
    BOOL_FALSE = auto()
    NONE = auto()
    IDENTIFIER = auto()
    LPAREN = auto()
    RPAREN = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    COMMA = auto()
    OPERATOR = auto()
    EOF = auto()


class Token:
    """A token from the domain string."""

    def __init__(self, type_: TokenType, value: Any, pos: int):
        self.type = type_
        self.value = value
        self.pos = pos

    def __repr__(self) -> str:
        return f"Token({self.type.name}, {self.value!r}, pos={self.pos})"


class DomainTokenizer:
    """Tokenizes Odoo domain strings."""

    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.length = len(text)

    def _skip_whitespace(self):
        """Skip whitespace characters."""
        while self.pos < self.length and self.text[self.pos] in ' \t\n\r':
            self.pos += 1

    def _read_string(self, quote_char: str) -> str:
        """Read a quoted string."""
        start = self.pos
        self.pos += 1  # skip opening quote
        result = []

        while self.pos < self.length:
            char = self.text[self.pos]
            if char == '\\' and self.pos + 1 < self.length:
                # Handle escape sequences
                next_char = self.text[self.pos + 1]
                if next_char in (quote_char, '\\', 'n', 't', 'r'):
                    if next_char == 'n':
                        result.append('\n')
                    elif next_char == 't':
                        result.append('\t')
                    elif next_char == 'r':
                        result.append('\r')
                    else:
                        result.append(next_char)
                    self.pos += 2
                else:
                    result.append(char)
                    self.pos += 1
            elif char == quote_char:
                self.pos += 1  # skip closing quote
                return ''.join(result)
            else:
                result.append(char)
                self.pos += 1

        raise ValueError(f"Unterminated string starting at position {start}")

    def _read_number(self) -> int | float:
        """Read a number (integer or float)."""
        start = self.pos
        has_dot = False
        is_negative = False

        if self.text[self.pos] == '-':
            is_negative = True
            self.pos += 1

        while self.pos < self.length:
            char = self.text[self.pos]
            if char.isdigit():
                self.pos += 1
            elif char == '.' and not has_dot:
                # Check if this is a float or start of an identifier
                if self.pos + 1 < self.length and self.text[self.pos + 1].isdigit():
                    has_dot = True
                    self.pos += 1
                else:
                    break
            else:
                break

        num_str = self.text[start:self.pos]
        if has_dot:
            return float(num_str)
        return int(num_str)

    def _read_identifier(self) -> str:
        """Read an identifier (may include dots for dotted paths)."""
        start = self.pos

        while self.pos < self.length:
            char = self.text[self.pos]
            if char.isalnum() or char == '_' or char == '.':
                self.pos += 1
            else:
                break

        return self.text[start:self.pos]

    def get_next_token(self) -> Token:
        """Get the next token from the input."""
        self._skip_whitespace()

        if self.pos >= self.length:
            return Token(TokenType.EOF, None, self.pos)

        char = self.text[self.pos]
        start_pos = self.pos

        # Single-character tokens
        if char == '(':
            self.pos += 1
            return Token(TokenType.LPAREN, '(', start_pos)
        if char == ')':
            self.pos += 1
            return Token(TokenType.RPAREN, ')', start_pos)
        if char == '[':
            self.pos += 1
            return Token(TokenType.LBRACKET, '[', start_pos)
        if char == ']':
            self.pos += 1
            return Token(TokenType.RBRACKET, ']', start_pos)
        if char == ',':
            self.pos += 1
            return Token(TokenType.COMMA, ',', start_pos)

        # Strings
        if char in ('"', "'"):
            value = self._read_string(char)
            return Token(TokenType.STRING, value, start_pos)

        # Numbers (including negative)
        if char.isdigit() or (char == '-' and self.pos + 1 < self.length and self.text[self.pos + 1].isdigit()):
            value = self._read_number()
            return Token(TokenType.NUMBER, value, start_pos)

        # Identifiers and keywords
        if char.isalpha() or char == '_':
            ident = self._read_identifier()
            if ident == 'True':
                return Token(TokenType.BOOL_TRUE, True, start_pos)
            if ident == 'False':
                return Token(TokenType.BOOL_FALSE, False, start_pos)
            if ident == 'None':
                return Token(TokenType.NONE, None, start_pos)
            return Token(TokenType.IDENTIFIER, ident, start_pos)

        raise ValueError(f"Unexpected character '{char}' at position {self.pos}")

    def tokenize(self) -> list[Token]:
        """Tokenize the entire input and return list of tokens."""
        tokens = []
        while True:
            token = self.get_next_token()
            tokens.append(token)
            if token.type == TokenType.EOF:
                break
        return tokens


class DomainParser:
    """Parser for Odoo domain strings using recursive descent."""

    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

    def _current(self) -> Token:
        """Get current token."""
        return self.tokens[self.pos] if self.pos < len(self.tokens) else Token(TokenType.EOF, None, -1)

    def _advance(self) -> Token:
        """Advance to next token and return the previous one."""
        token = self._current()
        self.pos += 1
        return token

    def _expect(self, type_: TokenType) -> Token:
        """Expect a specific token type, raise error if not found."""
        token = self._current()
        if token.type != type_:
            raise ValueError(f"Expected {type_.name} at position {token.pos}, got {token.type.name}")
        return self._advance()

    def parse(self) -> list:
        """Parse the token stream into a Python list structure."""
        return self._parse_list()

    def _parse_list(self) -> list:
        """Parse a list: [ elements ]"""
        self._expect(TokenType.LBRACKET)
        elements = []

        while self._current().type != TokenType.RBRACKET:
            if self._current().type == TokenType.EOF:
                raise ValueError("Unexpected end of input, expected ']'")

            element = self._parse_element()
            elements.append(element)

            # Handle comma between elements
            if self._current().type == TokenType.COMMA:
                self._advance()

        self._expect(TokenType.RBRACKET)
        return elements

    def _parse_element(self) -> Any:
        """Parse a single element (could be tuple, list, or value)."""
        token = self._current()

        if token.type == TokenType.LPAREN:
            return self._parse_tuple()
        if token.type == TokenType.LBRACKET:
            return self._parse_list()
        return self._parse_value()

    def _parse_tuple(self) -> tuple:
        """Parse a tuple: ( elements )"""
        self._expect(TokenType.LPAREN)
        elements = []

        while self._current().type != TokenType.RPAREN:
            if self._current().type == TokenType.EOF:
                raise ValueError("Unexpected end of input, expected ')'")

            element = self._parse_value()
            elements.append(element)

            if self._current().type == TokenType.COMMA:
                self._advance()

        self._expect(TokenType.RPAREN)
        return tuple(elements)

    def _parse_value(self) -> Any:
        """Parse a single value."""
        token = self._current()

        if token.type == TokenType.STRING:
            self._advance()
            return token.value

        if token.type == TokenType.NUMBER:
            self._advance()
            return token.value

        if token.type == TokenType.BOOL_TRUE:
            self._advance()
            return True

        if token.type == TokenType.BOOL_FALSE:
            self._advance()
            return False

        if token.type == TokenType.NONE:
            self._advance()
            return None

        if token.type == TokenType.IDENTIFIER:
            self._advance()
            # Check if this is an operator (&, |, !)
            if token.value in ('&', '|', '!'):
                return token.value
            # Otherwise it's a dynamic reference
            return DynamicRef(token.value)

        if token.type == TokenType.LBRACKET:
            return self._parse_list()

        raise ValueError(f"Unexpected token {token.type.name} at position {token.pos}")


def parse_domain(domain_str: str) -> list:
    """Parse an Odoo domain string into a Python list structure.

    This parser handles:
    - Standard Python literals (strings, numbers, booleans, None, lists, tuples)
    - Dynamic references (user.id, company_ids, user.partner_id.id)
    - Odoo logical operators (&, |, !)
    - Multi-line strings

    Args:
        domain_str: The domain string to parse (e.g., "[('user_id', '=', user.id)]")

    Returns:
        A list structure identical to what ast.literal_eval() would produce for
        valid Python literals, but with DynamicRef objects for variable references.

    Example:
        >>> parse_domain("[('user_id', '=', user.id)]")
        [('user_id', '=', DynamicRef('user.id'))]
    """
    # Try ast.literal_eval first for simple cases (faster and more robust for literals)
    try:
        return ast.literal_eval(domain_str)
    except (ValueError, SyntaxError):
        # Fall back to custom parser for domains with dynamic references
        pass

    tokenizer = DomainTokenizer(domain_str)
    tokens = tokenizer.tokenize()
    parser = DomainParser(tokens)
    return parser.parse()


# System field labels for Odoo-aware output (ODOO-01)
SYSTEM_FIELD_LABELS = {
    'create_uid': 'Created By',
    'write_uid': 'Last Updated By',
    'create_date': 'Created On',
    'write_date': 'Last Updated On',
    'active': 'Active',
    'id': 'ID',
    'display_name': 'Display Name',
}


def get_system_field_label(field_name: str) -> str | None:
    """Get UI label for a system field.

    Args:
        field_name: The field name to check

    Returns:
        UI label if it's a system field, None otherwise
    """
    if not field_name:
        return None
    return SYSTEM_FIELD_LABELS.get(field_name)


def humanize_dynamic_ref(ref: 'DynamicRef') -> str:
    """Humanize a DynamicRef for pseudocode output (ODOO-02).

    Converts user references to human-readable form:
    - user.id -> "current user"
    - user.partner_id.id -> "current user's Partner"
    - user.groups_id.ids -> "current user's Groups"
    - user.company_ids -> "current user's Companies"

    Non-user references are returned unchanged.

    Args:
        ref: A DynamicRef object

    Returns:
        Human-readable string for the reference
    """
    name = ref.name

    # Only handle user.* references
    if not name.startswith('user.'):
        return str(ref)

    # Handle user.id specially
    if name == 'user.id':
        return "current user"

    # Extract the path after "user."
    rest = name[5:]  # Skip "user."

    # Split by dots
    parts = rest.split('.')

    # Handle various patterns
    if len(parts) >= 1:
        # Get the first segment (e.g., partner_id, company_ids, groups_id)
        first_segment = parts[0]

        # If ends with .id or .ids, we're accessing a relation's ID
        if len(parts) >= 2 and parts[-1] in ('id', 'ids'):
            # Use the segment before the final .id/.ids
            # e.g., user.partner_id.id -> Partner
            # e.g., user.groups_id.ids -> Groups
            base_segment = parts[-2] if len(parts) >= 2 else parts[0]
            humanized = _humanize_segment(base_segment)
            return f"current user's {humanized}"
        else:
            # Direct access like user.partner_id, user.company_ids
            humanized = _humanize_segment(first_segment)
            return f"current user's {humanized}"

    return str(ref)


def _humanize_segment(segment: str) -> str:
    """Humanize a single path segment.

    Handles:
    - Strip _id suffix (singularize)
    - Strip _ids suffix (pluralize)
    - Replace underscores with spaces
    - Apply title case

    Args:
        segment: A single field name segment (no dots)

    Returns:
        Humanized segment string
    """
    if not segment:
        return ""

    # Handle _ids suffix (strip and pluralize)
    if segment.endswith('_ids'):
        base = segment[:-4]  # Remove _ids
        # Humanize the base
        humanized = base.replace('_', ' ').title()
        # Simple pluralization: handle 'y' -> 'ies' for company
        if humanized.lower().endswith('y') and len(humanized) > 1:
            # Check if it's a consonant + y pattern (company -> companies)
            if len(humanized) >= 2 and humanized[-2].lower() not in 'aeiou':
                return humanized[:-1] + 'ies'
        return humanized + 's'

    # Handle _id suffix (strip, singular)
    if segment.endswith('_id') and len(segment) > 3:
        base = segment[:-3]  # Remove _id
        return base.replace('_', ' ').title()

    # Regular field: replace underscores and title case
    # Filter out empty parts from multiple underscores
    parts = [p for p in segment.split('_') if p]
    return ' '.join(p.title() for p in parts)


def humanize_field(field_name: str) -> str:
    """Convert a technical field name to a human-readable label.

    Handles:
    - Snake_case to Title Case (FIELD-01)
    - Strip _id suffix (FIELD-02)
    - Strip _ids suffix (FIELD-03)
    - Dotted paths with possessive form (FIELD-04)

    Args:
        field_name: Technical field name (e.g., 'privacy_visibility', 'project_id.name')

    Returns:
        Human-readable label (e.g., 'Privacy Visibility', "Project's Name")

    Examples:
        >>> humanize_field('privacy_visibility')
        'Privacy Visibility'
        >>> humanize_field('company_id')
        'Company'
        >>> humanize_field('group_ids')
        'Groups'
        >>> humanize_field('project_id.name')
        "Project's Name"
    """
    if not field_name:
        return ""

    # Split on dots for path handling
    segments = field_name.split('.')

    if len(segments) == 1:
        # Single segment - just humanize it
        return _humanize_segment(segments[0])

    # Multiple segments - use possessive form
    # All segments except last get 's appended
    humanized_parts = []
    for i, segment in enumerate(segments):
        humanized = _humanize_segment(segment)
        if i < len(segments) - 1:
            # Add possessive for all but last segment
            humanized_parts.append(humanized + "'s")
        else:
            humanized_parts.append(humanized)

    return ' '.join(humanized_parts)


def to_python_identifier(text: str) -> str:
    """Convert humanized text to Python-safe identifier.

    Replaces spaces with underscores while preserving apostrophes.
    Example: "current user's Partner" -> "current_user's_Partner"

    Args:
        text: Human-readable text with spaces

    Returns:
        Python-safe identifier with underscores instead of spaces
    """
    return text.replace(' ', '_')


def convert_odoo_domain_to_python(domain):
    """Convert an Odoo domain expression to a Python expression.

    Follows Odoo domain conventions (compatible with Odoo 16+):
    - '&' and '|' are BINARY operators (take exactly 2 operands)
    - '!' is a UNARY operator (takes exactly 1 operand)
    - Implicit '&' between adjacent conditions without explicit operators
    - Supports all standard Odoo comparison operators
    """
    operator_dict = {
        '=': '==',
        '!=': '!=',
        '>': '>',
        '<': '<',
        '>=': '>=',
        '<=': '<=',
        'in': 'in',
        'not in': 'not in',
        'like': 'like',
        'ilike': 'ilike',
        '=like': '=like',
        '=ilike': '=ilike',
        'child_of': 'child_of',
        'parent_of': 'parent_of',
        '&': 'and',
        '|': 'or',
        '!': 'not'
    }

    logical_operators = {'&', '|', '!'}

    def format_value(value):
        """Format a value for Python expression output with humanization."""
        if isinstance(value, DynamicRef):
            # Humanize and convert to Python-safe identifier
            humanized = humanize_dynamic_ref(value)
            return to_python_identifier(humanized)
        elif isinstance(value, str):
            return repr(value)
        elif isinstance(value, list):
            formatted_items = ', '.join(format_value(v) for v in value)
            return f"[{formatted_items}]"
        elif value is None:
            return 'None'
        elif value is True:
            return 'True'
        elif value is False:
            return 'False'
        else:
            return str(value)

    def process_condition(condition):
        """Convert a condition tuple to a Python expression string with humanization."""
        field, operator, value = condition
        if operator == '=?':
            if value in (None, False):
                return 'True'
            else:
                operator = '='

        # Humanize field: check system field labels first, fall back to humanize_field
        if isinstance(field, str):
            system_label = get_system_field_label(field)
            humanized_field = system_label if system_label else humanize_field(field)
            # Convert to Python-safe identifier (spaces to underscores)
            humanized_field = to_python_identifier(humanized_field)
        else:
            humanized_field = str(field)

        formatted_value = format_value(value)
        op_str = operator_dict.get(operator, operator)
        return f"({humanized_field} {op_str} {formatted_value})"

    def process_subexpression(subexpression):
        """Convert a subexpression list to a Python expression string."""
        if isinstance(subexpression, tuple):
            return process_condition(subexpression)
        elif isinstance(subexpression, list):
            return convert_odoo_domain_to_python(subexpression)

    stack = []
    # Process elements in reverse order (right to left) for prefix notation
    for i in reversed(range(len(domain))):
        element = domain[i]
        if isinstance(element, tuple):
            stack.append(process_condition(element))
        elif isinstance(element, list):
            stack.append(process_subexpression(element))
        elif element in logical_operators:
            if element == '!':
                # Unary operator: takes exactly 1 operand
                if stack:
                    operand = stack.pop()
                    stack.append(f"not ({operand})")
            else:
                # Binary operators '&' and '|': take exactly 2 operands (Odoo standard)
                if len(stack) >= 2:
                    operand1 = stack.pop()
                    operand2 = stack.pop()
                    stack.append(f"({operand1} {operator_dict[element]} {operand2})")
                elif len(stack) == 1:
                    # Only one operand available - this is a malformed domain
                    # Keep the operand as-is to avoid losing data
                    pass

    # Handle implicit AND: if multiple items remain on stack, AND them together
    # This handles cases like [('a', '=', 1), ('b', '=', 2)] without explicit '&'
    while len(stack) > 1:
        operand1 = stack.pop(0)
        operand2 = stack.pop(0)
        stack.insert(0, f"({operand1} and {operand2})")

    return stack[0] if stack else 'True'


def convert_odoo_domain_to_pseudocode(domain):
    """Convert an Odoo domain expression to human-readable pseudocode.

    Follows Odoo domain conventions (compatible with Odoo 16+):
    - '&' and '|' are BINARY operators (take exactly 2 operands)
    - '!' is a UNARY operator (takes exactly 1 operand)
    - Implicit '&' between adjacent conditions without explicit operators
    - Supports all standard Odoo comparison operators
    """
    operator_dict = {
        '=': 'is equal to',
        '!=': 'is not equal to',
        '>': 'is greater than',
        '<': 'is less than',
        '>=': 'is greater than or equal to',
        '<=': 'is less than or equal to',
        'in': 'is in',
        'not in': 'is not in',
        'like': 'matches (case sensitive, with wildcards) the pattern',
        'ilike': 'matches (case insensitive, with wildcards) the pattern',
        '=like': 'matches exactly (case sensitive) the pattern',
        '=ilike': 'matches exactly (case insensitive) the pattern',
        'child_of': 'is a child of',
        'parent_of': 'is a parent of',
        '&': 'AND',
        '|': 'OR',
        '!': 'NOT'
    }

    logical_operators = {'&', '|', '!'}

    def format_value(value):
        """Format a value for pseudocode output (VALUE-01)."""
        if isinstance(value, DynamicRef):
            return humanize_dynamic_ref(value)  # Use Odoo-aware humanization
        elif isinstance(value, str):
            return f'"{value}"'
        elif isinstance(value, list):
            formatted_items = ', '.join(format_value(v) for v in value)
            return f"[{formatted_items}]"
        elif value is None:
            return 'Not set'  # VALUE-01: Humanize None
        elif value is True:
            return 'True'
        elif value is False:
            return 'Not set'  # VALUE-01: Humanize False
        else:
            return str(value)

    def is_tautology(condition):
        """Check if condition is a tautology pattern (VALUE-02, VALUE-03).

        Returns:
            - "always_true" for (1, '=', 1) patterns
            - "always_false" for (0, '=', 1) patterns
            - None for regular conditions
        """
        field, operator, value = condition
        if operator != '=':
            return None

        # Normalize to comparable values (handle both int and str)
        def normalize(v):
            if isinstance(v, str) and v in ('0', '1'):
                return int(v)
            return v

        norm_field = normalize(field)
        norm_value = normalize(value)

        # (1, '=', 1) or ('1', '=', '1') -> always true
        if norm_field == 1 and norm_value == 1:
            return "always_true"

        # (0, '=', 1) or ('0', '=', '1') -> always false
        if norm_field == 0 and norm_value == 1:
            return "always_false"

        return None

    def process_condition(condition):
        """Convert a condition tuple to a pseudocode string."""
        field, operator, value = condition

        # Check for tautology patterns first (VALUE-02, VALUE-03)
        tautology = is_tautology(condition)
        if tautology == "always_true":
            return "Always True (all records)"
        elif tautology == "always_false":
            return "Always False (no records)"

        if operator == '=?':
            if value in (None, False):
                return 'Always True (ignored condition)'
            else:
                operator = '='

        # For regular conditions, field should be a string
        # Check system field labels first, fall back to humanize_field
        if isinstance(field, str):
            system_label = get_system_field_label(field)
            humanized_field = system_label if system_label else humanize_field(field)
        else:
            humanized_field = str(field)

        formatted_value = format_value(value)
        op_str = operator_dict.get(operator, operator)
        return f"({humanized_field} {op_str} {formatted_value})"

    def process_subexpression(subexpression):
        """Convert a subexpression list to a pseudocode string."""
        if isinstance(subexpression, tuple):
            return process_condition(subexpression)
        elif isinstance(subexpression, list):
            return convert_odoo_domain_to_pseudocode(subexpression)

    stack = []
    # Process elements in reverse order (right to left) for prefix notation
    for i in reversed(range(len(domain))):
        element = domain[i]
        if isinstance(element, tuple):
            stack.append(process_condition(element))
        elif isinstance(element, list):
            stack.append(process_subexpression(element))
        elif element in logical_operators:
            if element == '!':
                # Unary operator: takes exactly 1 operand
                if stack:
                    operand = stack.pop()
                    stack.append(f"NOT ({operand})")
            else:
                # Binary operators '&' and '|': take exactly 2 operands (Odoo standard)
                if len(stack) >= 2:
                    operand1 = stack.pop()
                    operand2 = stack.pop()
                    stack.append(f"{operand1}\n{operator_dict[element]}\n{operand2}")
                elif len(stack) == 1:
                    # Only one operand available - malformed domain
                    pass

    # Handle implicit AND: if multiple items remain on stack, AND them together
    # This handles cases like [('a', '=', 1), ('b', '=', 2)] without explicit '&'
    while len(stack) > 1:
        operand1 = stack.pop(0)
        operand2 = stack.pop(0)
        stack.insert(0, f"{operand1}\nAND\n{operand2}")

    return stack[0] if stack else 'Always True (empty domain)'

font = ("Helvetica", 20)


def convert_odoo_domain_to_python_gui():
    """A GUI for the convert_odoo_domain_to_python function."""
    layout = [
        [
            sg.Text(
                "Polish Notation to Python Expression Converter",
                size=(50, 1),
                key="-text-",
                font=font,
            )
        ],
        [sg.Multiline(size=(100, 10), key="-INPUT-")],
        [sg.Radio('Python Code', 'RADIO1', default=True, key='-RADIO_PY-'),
         sg.Radio('Pseudocode', 'RADIO1', key='-RADIO_PSEUDO-')],
        [sg.Button("Convert")],
        [sg.Multiline(size=(100, 10), key="-OUTPUT-")],
    ]
    window = sg.Window("Odoo Domain to Python Expression Converter", layout, font=font)

    while True:
        event, values = window.read()
        if event == sg.WINDOW_CLOSED:
            break
        if event == "Convert":
            try:
                domain_str = values["-INPUT-"].strip()
                domain = parse_domain(domain_str)
                if values['-RADIO_PY-']:
                    output = convert_odoo_domain_to_python(domain)
                else:
                    output = convert_odoo_domain_to_pseudocode(domain)
                window['-OUTPUT-'].update(output)
                # python_expression = convert_odoo_domain_to_python(domain)
                # window["-OUTPUT-"].update(python_expression)
            except Exception as e:
                window["-OUTPUT-"].update(str(e))
    window.close()


# Run the GUI
if __name__ == "__main__":
    convert_odoo_domain_to_python_gui()


# Test the function
# [("field1", "=", "value1"), "&", ("field2", "!=", "value2"),("field3", "in", ["value3", "value4"]),]
