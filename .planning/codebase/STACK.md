# Technology Stack

**Analysis Date:** 2026-01-17

## Languages

**Primary:**
- Python - All application code (`main.py`)

**Secondary:**
- None

## Runtime

**Environment:**
- Python 3.13.11
- No browser runtime (Desktop GUI application)

**Package Manager:**
- pip (Python Package Manager)
- Lockfile: `requirements.txt` present

## Frameworks

**Core:**
- PySimpleGUI 4.60.5 - Desktop GUI library (`main.py` line 1)

**Testing:**
- None configured

**Build/Dev:**
- Black 23.7.0 - Code formatter (imported but not actively used)

## Key Dependencies

**Critical:**
- PySimpleGUI 4.60.5 - GUI framework for desktop interface
- ast (stdlib) - Safe parsing of domain expressions via `ast.literal_eval()`

**Infrastructure:**
- aiohttp 3.8.5 - Async HTTP client (listed but unused in current code)
- click 8.1.6 - CLI utility library (listed but unused)

**Supporting:**
- charset-normalizer 3.2.0
- attrs 23.1.0
- multidict 6.0.4
- yarl 1.9.2

## Configuration

**Environment:**
- No environment variables required
- Configuration via CLI flags/GUI only

**Build:**
- No build configuration files
- Direct Python execution

## Platform Requirements

**Development:**
- Any platform with Python 3.x (macOS/Linux/Windows)
- Virtual environment recommended (`.venv/`)
- No external system dependencies

**Production:**
- Runs as standalone desktop application
- Requires Python 3.x installation
- GUI requires display environment

---

*Stack analysis: 2026-01-17*
*Update after major dependency changes*
