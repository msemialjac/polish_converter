"""Entry point for running polish_converter as a module.

Usage:
    python -m polish_converter convert "[('state', '=', 'draft')]"
    python -m polish_converter gui
    python -m polish_converter --help
"""

from .cli import main

if __name__ == '__main__':
    main()
