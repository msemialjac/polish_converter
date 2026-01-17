"""GUI for Odoo domain converter using FreeSimpleGUI.

This module provides a graphical interface for converting Odoo domains
to human-readable formats and validating them against Odoo instances.
"""

import FreeSimpleGUI as sg

from .parser import parse_domain
from .converter import convert_odoo_domain_to_python, convert_odoo_domain_to_pseudocode
from .odoo_connection import OdooConnection
from .validation import validate_domain_fields


# Default font for the GUI
FONT = ("Helvetica", 20)

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
        font=FONT,
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


def run_gui():
    """Run the main Odoo domain converter GUI."""
    layout = [
        [
            sg.Text(
                "Polish Notation to Python Expression Converter",
                size=(50, 1),
                key="-text-",
                font=FONT,
            )
        ],
        [sg.Text("Model (for validation):", size=(20, 1)),
         sg.Input(key="-MODEL-", size=(30, 1), tooltip="Technical name (res.partner) or display name (Contact)")],
        [sg.Multiline(size=(100, 10), key="-INPUT-")],
        [sg.Radio('Pseudocode', 'RADIO1', default=True, key='-RADIO_PSEUDO-'),
         sg.Radio('Python Code', 'RADIO1', key='-RADIO_PY-')],
        [sg.Button("Convert"), sg.Button("Validate"), sg.Button("Settings")],
        [sg.Multiline(size=(100, 10), key="-OUTPUT-")],
        [sg.Multiline(size=(100, 3), key="-VALIDATION-", text_color='orange', disabled=True)],
    ]
    window = sg.Window("Odoo Domain to Python Expression Converter", layout, font=FONT)

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
                results = validate_domain_fields(model, domain, odoo_settings)

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


# Alias for backwards compatibility
convert_odoo_domain_to_python_gui = run_gui
