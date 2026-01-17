"""Odoo XML-RPC connection client for domain validation.

This module provides an OdooConnection class for connecting to Odoo instances
via the XML-RPC API to validate domain fields, operators, and values against
actual model definitions.
"""

import xmlrpc.client
from typing import Any

from .parser import DynamicRef


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
        self._fields_cache: dict[str, dict] = {}

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
