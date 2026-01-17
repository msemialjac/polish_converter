import FreeSimpleGUI as sg
import ast
import black
import xmlrpc.client
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


class OdooConnection:
    """Client for connecting to Odoo via XML-RPC API.

    Provides methods to test connectivity, authenticate, and retrieve
    database information from an Odoo instance.

    Attributes:
        url: Base URL of the Odoo instance (e.g., 'http://localhost:8069')
        database: Database name to connect to
        username: Login username
        password: Login password
        uid: User ID after successful authentication (None until authenticated)
    """

    # Mapping of field types to compatible operators (VALID-04)
    FIELD_TYPE_OPERATORS = {
        'char': {'=', '!=', 'like', 'ilike', '=like', '=ilike', 'in', 'not in'},
        'text': {'=', '!=', 'like', 'ilike', '=like', '=ilike', 'in', 'not in'},
        'integer': {'=', '!=', '>', '<', '>=', '<=', 'in', 'not in'},
        'float': {'=', '!=', '>', '<', '>=', '<=', 'in', 'not in'},
        'monetary': {'=', '!=', '>', '<', '>=', '<=', 'in', 'not in'},
        'boolean': {'=', '!='},
        'date': {'=', '!=', '>', '<', '>=', '<='},
        'datetime': {'=', '!=', '>', '<', '>=', '<='},
        'many2one': {'=', '!=', 'in', 'not in', 'child_of', 'parent_of'},
        'one2many': {'in', 'not in', 'child_of', 'parent_of'},
        'many2many': {'in', 'not in', 'child_of', 'parent_of'},
        'selection': {'=', '!=', 'in', 'not in'},
    }

    # Mapping of field types to expected Python value types (VALID-06)
    FIELD_TYPE_VALUES = {
        'char': (str,),
        'text': (str,),
        'integer': (int,),
        'float': (int, float),
        'monetary': (int, float),
        'boolean': (bool,),
        'date': (str,),  # Format validated separately
        'datetime': (str,),  # Format validated separately
        'many2one': (int, bool, type(None)),  # ID or False/None
        'one2many': (list,),
        'many2many': (list,),
        'selection': (str,),
    }

    def __init__(self, url: str, database: str, username: str, password: str):
        """Initialize OdooConnection with connection parameters.

        Args:
            url: Base URL of the Odoo instance (e.g., 'http://localhost:8069')
            database: Database name to connect to
            username: Login username
            password: Login password
        """
        self.url = url.rstrip('/')  # Remove trailing slash if present
        self.database = database
        self.username = username
        self.password = password
        self.uid: int | None = None

    def test_connection(self) -> tuple[bool, str]:
        """Test if the Odoo server is reachable.

        Attempts to connect to the XML-RPC common endpoint and call version().

        Returns:
            Tuple of (success, message):
            - (True, version_info) if connection successful
            - (False, error_message) if connection failed
        """
        try:
            common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')
            version_info = common.version()
            server_version = version_info.get('server_version', 'unknown')
            return True, f"Connected to Odoo {server_version}"
        except ConnectionRefusedError:
            return False, f"Cannot connect to {self.url}"
        except OSError as e:
            return False, f"Connection error: {e}"
        except xmlrpc.client.Fault as e:
            return False, f"XML-RPC error: {e.faultString}"
        except Exception as e:
            return False, f"Unexpected error: {e}"

    def authenticate(self) -> int | None:
        """Authenticate with the Odoo instance.

        Attempts to authenticate using the stored credentials. On success,
        stores the user ID (uid) for later API calls.

        Returns:
            User ID (uid) on success, None on failure
        """
        try:
            common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')
            uid = common.authenticate(self.database, self.username, self.password, {})
            if uid:
                self.uid = uid
                return uid
            return None
        except ConnectionRefusedError:
            return None
        except xmlrpc.client.Fault:
            return None
        except Exception:
            return None

    @classmethod
    def get_databases(cls, url: str) -> tuple[bool, list[str] | str]:
        """Get list of available databases from an Odoo instance.

        This is a class method since it doesn't require authentication.

        Args:
            url: Base URL of the Odoo instance

        Returns:
            Tuple of (success, result):
            - (True, [database_names]) if successful
            - (False, error_message) if failed
        """
        url = url.rstrip('/')
        try:
            db = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/db')
            databases = db.list()
            return True, databases
        except ConnectionRefusedError:
            return False, f"Cannot connect to {url}"
        except xmlrpc.client.Fault as e:
            # Some Odoo instances disable database listing for security
            if 'Access Denied' in str(e.faultString):
                return False, "Database listing disabled on this server"
            return False, f"XML-RPC error: {e.faultString}"
        except Exception as e:
            return False, f"Error retrieving databases: {e}"

    def resolve_model_name(self, model_input: str) -> tuple[bool, str, str | None]:
        """Resolve a model input to its technical name.

        Accepts either:
        - Technical name: 'helpdesk.ticket.report.analysis'
        - Display name: 'Ticket Analysis'

        First tries the input as a technical name. If that fails,
        searches ir.model by name (display name) to find the technical model.

        Args:
            model_input: Technical name or display name of the model

        Returns:
            Tuple of (success, technical_name, error):
            - (True, 'model.name', None) if resolved
            - (False, '', error_message) if not found
        """
        if not self.uid:
            return False, '', "Not authenticated. Call authenticate() first."

        model_input = model_input.strip()

        # First, try as technical name by attempting to get fields
        try:
            models = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')
            # Try calling fields_get - if model exists, it will work
            models.execute_kw(
                self.database, self.uid, self.password,
                model_input, 'fields_get',
                [],
                {'attributes': ['type'], 'limit': 1}
            )
            # If we get here, the model exists as a technical name
            return True, model_input, None
        except xmlrpc.client.Fault:
            # Model not found as technical name, try display name lookup
            pass
        except Exception as e:
            return False, '', f"Error checking model: {e}"

        # Search ir.model by display name
        try:
            models = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')
            # Search for models with matching name (case-insensitive)
            model_ids = models.execute_kw(
                self.database, self.uid, self.password,
                'ir.model', 'search',
                [[['name', 'ilike', model_input]]],
                {'limit': 10}
            )

            if not model_ids:
                return False, '', f"Model '{model_input}' not found (tried as technical name and display name)"

            # Get model info
            model_records = models.execute_kw(
                self.database, self.uid, self.password,
                'ir.model', 'read',
                [model_ids],
                {'fields': ['model', 'name']}
            )

            # Try exact match first
            for record in model_records:
                if record['name'].lower() == model_input.lower():
                    return True, record['model'], None

            # If no exact match, return first result with a note
            if len(model_records) == 1:
                return True, model_records[0]['model'], None
            else:
                # Multiple matches - list them
                options = [f"  - {r['name']} ({r['model']})" for r in model_records[:5]]
                options_str = '\n'.join(options)
                return False, '', f"Multiple models match '{model_input}':\n{options_str}\nPlease use the technical name."

        except xmlrpc.client.Fault as e:
            return False, '', f"Error searching models: {e.faultString}"
        except Exception as e:
            return False, '', f"Error searching models: {e}"

    def get_fields(self, model_name: str) -> dict:
        """Get field definitions for a model from Odoo.

        Uses the fields_get() method on the model to retrieve field metadata.
        Results are cached to avoid repeated API calls.

        Args:
            model_name: Technical name of the model (e.g., 'res.partner')

        Returns:
            Dict of field_name -> field_info, where field_info contains:
            - type: Field type (char, many2one, etc.)
            - relation: Target model for relational fields
            - string: Human-readable field label

        Raises:
            RuntimeError: If not authenticated or API call fails
        """
        if not self.uid:
            raise RuntimeError("Not authenticated. Call authenticate() first.")

        # Check cache
        if not hasattr(self, '_fields_cache'):
            self._fields_cache = {}

        if model_name in self._fields_cache:
            return self._fields_cache[model_name]

        try:
            models = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')
            fields = models.execute_kw(
                self.database, self.uid, self.password,
                model_name, 'fields_get',
                [],
                {'attributes': ['type', 'relation', 'string']}
            )
            self._fields_cache[model_name] = fields
            return fields
        except xmlrpc.client.Fault as e:
            if 'does not exist' in str(e.faultString).lower() or 'access' in str(e.faultString).lower():
                raise RuntimeError(f"Model '{model_name}' not found or access denied")
            raise RuntimeError(f"XML-RPC error: {e.faultString}")
        except Exception as e:
            raise RuntimeError(f"Error retrieving fields: {e}")

    def validate_field(self, model_name: str, field_name: str) -> tuple[bool, dict | None, str | None]:
        """Validate that a field exists on a model.

        Args:
            model_name: Technical name of the model (e.g., 'res.partner')
            field_name: Name of the field to validate (e.g., 'name')

        Returns:
            Tuple of (valid, field_info, error):
            - (True, field_info_dict, None) if field exists
            - (False, None, error_message) if field doesn't exist or error
        """
        try:
            fields = self.get_fields(model_name)
            if field_name in fields:
                return True, fields[field_name], None
            return False, None, f"Field '{field_name}' does not exist on {model_name}"
        except RuntimeError as e:
            return False, None, str(e)

    def validate_path(self, model_name: str, field_path: str) -> tuple[bool, dict | None, str | None]:
        """Validate a dotted field path traversal.

        Checks that each segment of the path exists and that intermediate
        segments are relational fields that can be traversed.

        Args:
            model_name: Starting model name (e.g., 'res.partner')
            field_path: Dotted path (e.g., 'company_id.name' or 'user_ids.partner_id.name')

        Returns:
            Tuple of (valid, field_info, error):
            - (True, final_field_info, None) if path is valid
            - (False, None, error_message) if any segment is invalid
        """
        segments = field_path.split('.')
        current_model = model_name
        relational_types = {'many2one', 'one2many', 'many2many'}

        for i, segment in enumerate(segments):
            is_last = (i == len(segments) - 1)

            # Validate current segment exists
            valid, field_info, error = self.validate_field(current_model, segment)
            if not valid:
                return False, None, error

            if is_last:
                # Final segment - just return its info
                return True, field_info, None

            # Not last segment - must be relational to traverse
            field_type = field_info.get('type', '')
            if field_type not in relational_types:
                return False, None, f"Cannot traverse '{segment}' on {current_model} - not a relational field (type: {field_type})"

            # Get the related model for next iteration
            relation = field_info.get('relation')
            if not relation:
                return False, None, f"Field '{segment}' on {current_model} has no relation defined"

            current_model = relation

        # Should not reach here, but handle empty path
        return False, None, "Empty field path"

    @classmethod
    def validate_operator(cls, field_type: str, operator: str) -> tuple[bool, str | None]:
        """Validate if an operator is compatible with a field type.

        Args:
            field_type: The Odoo field type (e.g., 'char', 'integer', 'many2one')
            operator: The comparison operator (e.g., '=', 'like', '>')

        Returns:
            Tuple of (valid, warning):
            - (True, None) if operator is compatible with field type
            - (False, warning_message) if operator may not work correctly
        """
        allowed_operators = cls.FIELD_TYPE_OPERATORS.get(field_type)

        # Unknown field type - can't validate, assume ok
        if allowed_operators is None:
            return True, None

        if operator in allowed_operators:
            return True, None

        return False, f"Operator '{operator}' may not work correctly with {field_type} fields"

    @classmethod
    def validate_value_type(cls, field_type: str, value: Any) -> tuple[bool, str | None]:
        """Validate if a value type matches the expected types for a field type.

        Args:
            field_type: The Odoo field type (e.g., 'char', 'integer', 'many2one')
            value: The value to validate

        Returns:
            Tuple of (valid, warning):
            - (True, None) if value type matches expected types
            - (False, warning_message) if value type may not match field type
        """
        # Skip validation for DynamicRef (can't validate at parse time)
        if isinstance(value, DynamicRef):
            return True, None

        # For 'in' / 'not in' operators, value should be a list - validate list contents
        if isinstance(value, list):
            # Validate each item in the list
            for item in value:
                if isinstance(item, DynamicRef):
                    continue  # Skip dynamic refs
                valid, warning = cls.validate_value_type(field_type, item)
                if not valid:
                    return False, f"List contains value with incompatible type: {warning}"
            return True, None

        expected_types = cls.FIELD_TYPE_VALUES.get(field_type)

        # Unknown field type - can't validate, assume ok
        if expected_types is None:
            return True, None

        if isinstance(value, expected_types):
            return True, None

        value_type_name = type(value).__name__
        expected_names = ', '.join(t.__name__ for t in expected_types)
        return False, f"Value type '{value_type_name}' may not match {field_type} field (expected: {expected_names})"

    def validate_domain_condition(self, model_name: str, condition: tuple) -> list[tuple[str, str]]:
        """Validate a single domain condition (field, operator, value).

        Args:
            model_name: The Odoo model to validate against
            condition: A tuple of (field, operator, value)

        Returns:
            List of (level, message) tuples where level is 'error', 'warning', or 'info'
        """
        warnings = []

        if not isinstance(condition, tuple) or len(condition) < 3:
            return [('error', f"Invalid condition format: {condition}")]

        field, operator, value = condition[:3]

        # Skip non-string fields (e.g., tautology patterns like (1, '=', 1))
        if not isinstance(field, str):
            return []

        # 1. Validate field exists and get field info
        if '.' in field:
            valid, field_info, error = self.validate_path(model_name, field)
        else:
            valid, field_info, error = self.validate_field(model_name, field)

        if not valid:
            warnings.append(('error', error))
            return warnings  # Can't validate further without field info

        # 2. Validate operator compatibility with field type
        field_type = field_info.get('type', '')
        if field_type:
            op_valid, op_warning = self.validate_operator(field_type, operator)
            if not op_valid:
                warnings.append(('warning', f"Field '{field}': {op_warning}"))

        # 3. Validate value type matches field type
        if field_type:
            val_valid, val_warning = self.validate_value_type(field_type, value)
            if not val_valid:
                warnings.append(('warning', f"Field '{field}': {val_warning}"))

        return warnings

    def validate_domain(self, model_name: str, domain: list) -> list[tuple[str, str]]:
        """Validate an entire domain against an Odoo model.

        Validates:
        - Field existence
        - Operator compatibility with field types
        - Value type compatibility with field types
        - Dotted path traversal

        Args:
            model_name: The Odoo model to validate against
            domain: Parsed domain (list of tuples and operators)

        Returns:
            List of (level, message) tuples where level is 'error', 'warning', or 'info'
        """
        warnings = []

        for item in domain:
            if isinstance(item, tuple):
                # Validate condition tuple
                condition_warnings = self.validate_domain_condition(model_name, item)
                warnings.extend(condition_warnings)
            elif isinstance(item, list):
                # Nested domain - recurse
                nested_warnings = self.validate_domain(model_name, item)
                warnings.extend(nested_warnings)
            # Skip string operators ('&', '|', '!')

        return warnings


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


def to_readable_text(text: str) -> str:
    """Return humanized text as-is for readable output.

    Previously converted spaces to underscores, but now we keep
    the human-readable format with spaces for better readability.
    Example: "current user's Partner" -> "current user's Partner"

    Args:
        text: Human-readable text with spaces

    Returns:
        The same text, preserving spaces for readability
    """
    return text


def convert_odoo_domain_to_python(domain):
    """Convert an Odoo domain expression to a Python expression.

    Follows Odoo domain conventions (compatible with Odoo 16+):
    - '&' and '|' are BINARY operators (take exactly 2 operands)
    - '!' is a UNARY operator (takes exactly 1 operand)
    - Implicit '&' between adjacent conditions without explicit operators
    - Supports all standard Odoo comparison operators
    """
    operator_dict = {
        '=': 'equals',
        '!=': "doesn't equal",
        '>': 'is greater than',
        '<': 'is less than',
        '>=': 'is at least',
        '<=': 'is at most',
        'in': 'is in',
        'not in': 'is not in',
        'like': 'is like',
        'ilike': 'is like (case-insensitive)',
        '=like': 'matches pattern',
        '=ilike': 'matches pattern (case-insensitive)',
        'child_of': 'is child of',
        'parent_of': 'is parent of',
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
            return to_readable_text(humanized)
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
            humanized_field = to_readable_text(humanized_field)
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

# Global settings for Odoo connection (persists during session)
odoo_settings = {
    'url': 'http://localhost:8069',
    'database': '',
    'username': 'admin',
    'password': 'admin',
}


def show_settings_window():
    """Show a modal window for configuring Odoo connection settings.

    Provides fields for URL, database, username, and password. Includes
    a Test Connection button to verify the configuration works.

    The settings are stored in the global odoo_settings dict.
    """
    # Try to get databases from the server
    databases = []
    success, result = OdooConnection.get_databases(odoo_settings['url'])
    if success:
        databases = result

    # Use dropdown if databases available, otherwise text input
    if databases:
        db_element = sg.Combo(
            databases,
            default_value=odoo_settings['database'] if odoo_settings['database'] in databases else (databases[0] if databases else ''),
            key='-DB-',
            size=(40, 1),
            readonly=True
        )
    else:
        db_element = sg.Input(
            default_text=odoo_settings['database'],
            key='-DB-',
            size=(42, 1)
        )

    layout = [
        [sg.Text("Odoo Connection Settings", font=("Helvetica", 24))],
        [sg.Text("")],  # Spacer
        [sg.Text("URL:", size=(10, 1)), sg.Input(default_text=odoo_settings['url'], key='-URL-', size=(42, 1))],
        [sg.Text("Database:", size=(10, 1)), db_element],
        [sg.Text("Username:", size=(10, 1)), sg.Input(default_text=odoo_settings['username'], key='-USER-', size=(42, 1))],
        [sg.Text("Password:", size=(10, 1)), sg.Input(default_text=odoo_settings['password'], key='-PASS-', size=(42, 1), password_char='*')],
        [sg.Text("")],  # Spacer
        [sg.Button("Refresh Databases"), sg.Button("Test Connection")],
        [sg.Text("", key='-STATUS-', size=(50, 2), text_color='gray')],
        [sg.Text("")],  # Spacer
        [sg.Button("Save"), sg.Button("Cancel")],
    ]

    window = sg.Window(
        "Settings",
        layout,
        font=font,
        modal=True,
        finalize=True
    )

    while True:
        event, values = window.read()

        if event in (sg.WINDOW_CLOSED, "Cancel"):
            break

        if event == "Refresh Databases":
            url = values['-URL-']
            window['-STATUS-'].update("Fetching databases...", text_color='gray')
            window.refresh()

            success, result = OdooConnection.get_databases(url)
            if success:
                databases = result
                # Update the database dropdown/input
                if databases:
                    window['-STATUS-'].update(f"Found {len(databases)} database(s)", text_color='green')
                    # Replace database element with combo
                    # Note: FreeSimpleGUI doesn't support dynamic element replacement,
                    # so we update the combo values if it's already a combo
                    if isinstance(window['-DB-'], sg.Combo):
                        window['-DB-'].update(values=databases, value=databases[0])
                else:
                    window['-STATUS-'].update("No databases found", text_color='orange')
            else:
                window['-STATUS-'].update(f"Error: {result}", text_color='red')

        if event == "Test Connection":
            url = values['-URL-']
            db = values['-DB-']
            username = values['-USER-']
            password = values['-PASS-']

            window['-STATUS-'].update("Testing connection...", text_color='gray')
            window.refresh()

            conn = OdooConnection(url, db, username, password)

            # Test basic connectivity
            success, msg = conn.test_connection()
            if not success:
                window['-STATUS-'].update(f"Connection failed: {msg}", text_color='red')
                continue

            # Test authentication
            uid = conn.authenticate()
            if uid:
                window['-STATUS-'].update(f"Connected! (User ID: {uid})\n{msg}", text_color='green')
            else:
                window['-STATUS-'].update(f"Server reachable but authentication failed.\n{msg}", text_color='orange')

        if event == "Save":
            odoo_settings['url'] = values['-URL-']
            odoo_settings['database'] = values['-DB-']
            odoo_settings['username'] = values['-USER-']
            odoo_settings['password'] = values['-PASS-']
            break

    window.close()


def extract_fields_from_domain(domain: list) -> list[str]:
    """Extract all field names/paths from a parsed domain.

    Args:
        domain: Parsed domain (list of tuples and operators)

    Returns:
        List of unique field names/paths referenced in the domain
    """
    fields = set()

    for item in domain:
        if isinstance(item, tuple) and len(item) >= 3:
            field = item[0]
            if isinstance(field, str):
                fields.add(field)
        elif isinstance(item, list):
            # Nested domain
            fields.update(extract_fields_from_domain(item))

    return list(fields)


def validate_domain_fields(model_input: str, domain: list) -> list[tuple[str, str]]:
    """Validate all fields, operators, and values in a domain against an Odoo model.

    Performs comprehensive validation including:
    - Model name resolution (accepts technical name or display name)
    - Field existence on the model
    - Operator compatibility with field types
    - Value type matching with field types
    - Dotted path traversal

    Args:
        model_input: The Odoo model to validate against (technical name like
                    'helpdesk.ticket' or display name like 'Helpdesk Ticket')
        domain: Parsed domain list

    Returns:
        List of (level, message) tuples where level is 'error', 'warning', or 'info'
        Empty list if all validations pass.
    """
    # Check if connection settings are configured
    if not odoo_settings.get('url') or not odoo_settings.get('database'):
        return [('error', "Connection not configured. Use Settings to configure Odoo connection.")]

    # Create connection and authenticate
    conn = OdooConnection(
        odoo_settings['url'],
        odoo_settings['database'],
        odoo_settings['username'],
        odoo_settings['password']
    )

    uid = conn.authenticate()
    if not uid:
        return [('error', "Authentication failed. Check credentials in Settings.")]

    # Resolve model name (accepts technical name or display name)
    success, model_name, error = conn.resolve_model_name(model_input)
    if not success:
        return [('error', error)]

    # Add info if model was resolved from display name
    results = []
    if model_name != model_input.strip():
        results.append(('info', f"Resolved '{model_input}' → {model_name}"))

    # Use comprehensive domain validation
    results.extend(conn.validate_domain(model_name, domain))
    return results


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
        [sg.Text("Model (for validation):", size=(20, 1)),
         sg.Input(key="-MODEL-", size=(30, 1), tooltip="Technical name (res.partner) or display name (Contact)")],
        [sg.Multiline(size=(100, 10), key="-INPUT-")],
        [sg.Radio('Python Code', 'RADIO1', default=True, key='-RADIO_PY-'),
         sg.Radio('Pseudocode', 'RADIO1', key='-RADIO_PSEUDO-')],
        [sg.Button("Convert"), sg.Button("Validate"), sg.Button("Settings")],
        [sg.Multiline(size=(100, 10), key="-OUTPUT-")],
        [sg.Multiline(size=(100, 3), key="-VALIDATION-", text_color='orange', disabled=True)],
    ]
    window = sg.Window("Odoo Domain to Python Expression Converter", layout, font=font)

    while True:
        event, values = window.read()
        if event == sg.WINDOW_CLOSED:
            break
        if event == "Settings":
            show_settings_window()
        if event == "Convert":
            try:
                domain_str = values["-INPUT-"].strip()
                domain = parse_domain(domain_str)
                if values['-RADIO_PY-']:
                    output = convert_odoo_domain_to_python(domain)
                else:
                    output = convert_odoo_domain_to_pseudocode(domain)
                window['-OUTPUT-'].update(output)
                window['-VALIDATION-'].update('')  # Clear validation on convert
            except Exception as e:
                window["-OUTPUT-"].update(str(e))
                window['-VALIDATION-'].update('')
        if event == "Validate":
            model = values["-MODEL-"].strip()
            domain_str = values["-INPUT-"].strip()

            if not model:
                window['-VALIDATION-'].update("Enter a model name to validate (e.g., res.partner)")
                continue

            if not domain_str:
                window['-VALIDATION-'].update("Enter a domain to validate")
                continue

            try:
                domain = parse_domain(domain_str)
                results = validate_domain_fields(model, domain)

                if results:
                    # Group by level and format output
                    errors = [msg for level, msg in results if level == 'error']
                    warnings = [msg for level, msg in results if level == 'warning']
                    infos = [msg for level, msg in results if level == 'info']

                    output_lines = []
                    if errors:
                        output_lines.append("ERRORS:")
                        output_lines.extend(f"  {msg}" for msg in errors)
                    if warnings:
                        if output_lines:
                            output_lines.append("")
                        output_lines.append("WARNINGS:")
                        output_lines.extend(f"  {msg}" for msg in warnings)
                    if infos:
                        if output_lines:
                            output_lines.append("")
                        output_lines.append("INFO:")
                        output_lines.extend(f"  {msg}" for msg in infos)

                    window['-VALIDATION-'].update('\n'.join(output_lines))
                else:
                    window['-VALIDATION-'].update("All validations passed!")
            except Exception as e:
                window['-VALIDATION-'].update(f"Parse error: {e}")
    window.close()


# Run the GUI
if __name__ == "__main__":
    convert_odoo_domain_to_python_gui()


# Test the function
# [("field1", "=", "value1"), "&", ("field2", "!=", "value2"),("field3", "in", ["value3", "value4"]),]
