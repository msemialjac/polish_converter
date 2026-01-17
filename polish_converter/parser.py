"""Odoo domain parser with support for dynamic references.

This module provides a custom parser for Odoo domain strings that handles:
- Standard Python literals (strings, numbers, booleans, None, lists, tuples)
- Dynamic references (user.id, company_ids, user.partner_id.id)
- Odoo logical operators (&, |, !)
- Multi-line strings
"""

import ast
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

        if self.text[self.pos] == '-':
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
