# Odoo Domain Converter

## What This Is

A desktop GUI tool that converts Odoo domain expressions (Polish notation) into human-readable pseudocode and Python expressions. Designed for mid-level Odoo users who understand Odoo concepts but aren't developers — making Record Rules, Filters, and other domain-based configurations easier to understand.

## Core Value

Domains with dynamic references (`user.id`, `company_ids`, field paths) must parse successfully and produce genuinely readable output that a non-developer Odoo user can understand.

## Requirements

### Validated

<!-- Shipped and confirmed valuable. -->

- ✓ Converts Odoo domains to Python expressions — existing
- ✓ Converts Odoo domains to pseudocode — existing
- ✓ GUI interface with input/output fields and format toggle — existing
- ✓ Handles standard Odoo operators (=, !=, >, <, >=, <=, in, not in, like, ilike, etc.) — existing
- ✓ Handles logical operators (&, |, !) with correct arity — existing
- ✓ Handles implicit AND between adjacent conditions — existing
- ✓ Stack-based reverse Polish notation algorithm — existing

### Active

<!-- Current scope. Building toward these. -->

**Parsing (critical):**
- [ ] Parse domains containing dynamic references (`user.id`, `user.partner_id.id`, `company_ids`)
- [ ] Parse domains containing dotted field paths (`account_online_link_id.company_id`)
- [ ] Handle multi-line domain strings gracefully

**Field humanization:**
- [ ] Convert snake_case field names to Title Case (`privacy_visibility` → "Privacy Visibility")
- [ ] Strip `_id` suffix from field names (`company_id` → "Company")
- [ ] Strip `_ids` suffix from field names (`group_ids` → "Groups")
- [ ] Humanize dotted paths (`project_id.privacy_visibility` → "Project's Privacy Visibility")

**Odoo-aware mappings:**
- [ ] Map common system fields to UI labels (`create_uid` → "Created By", `write_uid` → "Last Updated By", `create_date` → "Created On", `write_date` → "Last Updated On", `active` → "Active")
- [ ] Render `user.id` as "current user"
- [ ] Render `user.partner_id.id` as "current user's Partner"
- [ ] Render `user.groups_id.ids` as "current user's Groups"

**Value humanization:**
- [ ] Render `False` as "Not set" in pseudocode
- [ ] Render `None` as "Not set" in pseudocode
- [ ] Recognize `(1, '=', 1)` pattern as "Always True (all records)"
- [ ] Recognize `(0, '=', 1)` pattern as "Always False (no records)"

**Python output (lower priority):**
- [ ] Apply field humanization to Python output
- [ ] Maintain valid Python-like syntax while improving readability

### Out of Scope

- Web interface — desktop GUI is sufficient for this use case
- Domain validation against Odoo models — no connection to Odoo instance
- Reverse conversion (pseudocode → domain) — one-way conversion only
- Support for computed domains or Python code evaluation — static parsing only

## Context

**Problem origin:** Using the converter in an Odoo 18 custom module to make Record Rules readable. Many valid Odoo 18 domains fail to parse because they contain dynamic references that `ast.literal_eval()` cannot handle.

**Current limitation:** The parser uses `ast.literal_eval()` which only handles Python literals. Variable references like `user.id` or `company_ids` cause parse failures.

**Solution approach:** Replace `ast.literal_eval()` with a custom tokenizer/parser that treats variable references as tokens rather than attempting to evaluate them.

**Target audience:** Mid-level Odoo users — good Odoo knowledge but not technical expertise. Output should read like natural language, not code.

## Constraints

- **Tech stack**: Python with FreeSimpleGUI — maintain existing stack
- **Compatibility**: Must handle all valid Odoo 18 domain syntax
- **Single file**: Keep as single `main.py` unless complexity warrants splitting

## Key Decisions

<!-- Decisions that constrain future work. Add throughout project lifecycle. -->

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Custom parser over ast.literal_eval | Need to handle variable references as tokens | — Pending |
| Strip _id/_ids suffixes | More readable for non-technical users | — Pending |
| Map system fields to UI labels | Matches what users see in Odoo interface | — Pending |

---
*Last updated: 2026-01-17 after initialization*
