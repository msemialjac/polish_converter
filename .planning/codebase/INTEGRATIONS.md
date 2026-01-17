# External Integrations

**Analysis Date:** 2026-01-17

## APIs & External Services

**Payment Processing:**
- Not applicable

**Email/SMS:**
- Not applicable

**External APIs:**
- Not detected - This is a standalone desktop application with no external API calls

## Data Storage

**Databases:**
- Not applicable - No database connections

**File Storage:**
- Not applicable - No file storage operations

**Caching:**
- Not applicable - No caching layer

## Authentication & Identity

**Auth Provider:**
- Not applicable - No authentication required

**OAuth Integrations:**
- Not applicable

## Monitoring & Observability

**Error Tracking:**
- Not configured
- Errors displayed in GUI only

**Analytics:**
- Not configured

**Logs:**
- Not configured - No logging implementation

## CI/CD & Deployment

**Hosting:**
- Standalone desktop application
- Distributed as Python source code
- Run via `python main.py`

**CI Pipeline:**
- Not configured
- No GitHub Actions or other CI workflows

## Environment Configuration

**Development:**
- Required env vars: None
- Secrets location: Not applicable
- Virtual environment: `.venv/` (recommended)

**Staging:**
- Not applicable (no staging environment)

**Production:**
- Run directly with Python interpreter
- No secrets management required

## Webhooks & Callbacks

**Incoming:**
- Not applicable

**Outgoing:**
- Not applicable

## Odoo Domain Specification

**Purpose:** This application converts Odoo domain expressions but does not integrate with Odoo directly.

**Domain Format Support:**
- Compatible with Odoo 16+ domain specification
- Supports all standard operators: `=`, `!=`, `>`, `<`, `>=`, `<=`, `in`, `not in`, `like`, `ilike`, `=like`, `=ilike`, `child_of`, `parent_of`
- Logical operators: `&` (AND), `|` (OR), `!` (NOT)
- Follows Polish notation (prefix) for operator placement

**Note:** This is a parsing/conversion utility, not an Odoo API integration.

---

*Integration audit: 2026-01-17*
*Update when adding/removing external services*
