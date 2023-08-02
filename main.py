import PySimpleGUI as sg
import ast
import black


def convert_odoo_domain_to_python(domain):
    """Convert an Odoo domain expression to a Python expression."""
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
        '&': 'and',
        '|': 'or',
        '!': 'not'
    }

    def process_condition(condition):
        """Convert a condition tuple to a Python expression string."""
        field, operator, value = condition
        if operator == '=?':
            if value in (None, False):
                return 'True'
            else:
                operator = '='
        if isinstance(value, list):
            value = ', '.join(map(str, value))
        return f"({field} {operator_dict[operator]} {value})"

    def process_subexpression(subexpression):
        """Convert a subexpression list to a Python expression string."""
        if isinstance(subexpression, tuple):
            return process_condition(subexpression)
        elif isinstance(subexpression, list):
            return convert_odoo_domain_to_python(subexpression)

    stack = []
    for i in reversed(range(len(domain))):
        element = domain[i]
        if isinstance(element, tuple):
            stack.append(process_condition(element))
        elif isinstance(element, list):
            stack.append(process_subexpression(element))
        elif element in operator_dict:
            if element == '!':
                operand = stack.pop()
                stack.append(f"{operator_dict[element]} {operand}")
            else:
                operands = []
                while len(stack) > 0 and isinstance(stack[-1], str):
                    operands.append(stack.pop())
                operands.reverse()
                stack.append(f"({f' {operator_dict[element]} '.join(operands)})")
    return stack[0]
    # return stack[0]


def convert_odoo_domain_to_pseudocode(domain):
    """Convert an Odoo domain expression to a Python-flavored pseudocode."""
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
        '&': 'and',
        '|': 'or',
        '!': 'not'
    }

    def process_condition(condition):
        """Convert a condition tuple to a Python pseudocode string."""
        field, operator, value = condition
        if operator == '=?':
            if value in (None, False):
                return 'True'
            else:
                operator = '='
        if isinstance(value, list):
            value = ', '.join(map(str, value))
        return f"({field} {operator_dict[operator]} {value})"

    def process_subexpression(subexpression):
        """Convert a subexpression list to a Python pseudocode string."""
        if isinstance(subexpression, tuple):
            return process_condition(subexpression)
        elif isinstance(subexpression, list):
            return convert_odoo_domain_to_pseudocode(subexpression)

    stack = []
    for i in reversed(range(len(domain))):
        element = domain[i]
        if isinstance(element, tuple):
            stack.append(process_condition(element))
        elif isinstance(element, list):
            stack.append(process_subexpression(element))
        elif element in operator_dict:
            if element == '!':
                operand = stack.pop()
                stack.append(f"{operator_dict[element]} {operand}")
            else:
                operands = []
                while len(stack) > 0 and isinstance(stack[-1], str):
                    operands.append(stack.pop())
                operands.reverse()
                stack.append(f"\n{operator_dict[element]}\n".join(operands))
    return stack[0]

font = ("Helvetica", 20)


def convert_odoo_domain_to_python_gui():
    """A GUI for the convert_odoo_domain_to_python function."""
    layout = [
        [
            sg.Text(
                "Polish Notation to Python Expression Converter",
                size=(20, 1),
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
