import FreeSimpleGUI as sg
import ast
import black


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
        """Format a value for Python expression output."""
        if isinstance(value, str):
            return repr(value)
        elif isinstance(value, list):
            formatted_items = ', '.join(repr(v) if isinstance(v, str) else str(v) for v in value)
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
        """Convert a condition tuple to a Python expression string."""
        field, operator, value = condition
        if operator == '=?':
            if value in (None, False):
                return 'True'
            else:
                operator = '='
        formatted_value = format_value(value)
        op_str = operator_dict.get(operator, operator)
        return f"({field} {op_str} {formatted_value})"

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
        """Format a value for pseudocode output."""
        if isinstance(value, str):
            return f'"{value}"'
        elif isinstance(value, list):
            formatted_items = ', '.join(f'"{v}"' if isinstance(v, str) else str(v) for v in value)
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
        """Convert a condition tuple to a pseudocode string."""
        field, operator, value = condition
        if operator == '=?':
            if value in (None, False):
                return 'Always True (ignored condition)'
            else:
                operator = '='
        formatted_value = format_value(value)
        op_str = operator_dict.get(operator, operator)
        return f"({field} {op_str} {formatted_value})"

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
                domain = ast.literal_eval(domain_str)
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
