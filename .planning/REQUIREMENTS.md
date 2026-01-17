# Requirements: Odoo Domain Converter

**Defined:** 2026-01-17
**Core Value:** Domains with dynamic references must parse successfully and produce genuinely readable output that a non-developer Odoo user can understand.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Parsing

- [ ] **PARSE-01**: Parser handles domains containing dynamic references (`user.id`, `user.partner_id.id`, `company_ids`)
- [ ] **PARSE-02**: Parser handles domains containing dotted field paths (`account_online_link_id.company_id`)
- [ ] **PARSE-03**: Parser handles multi-line domain strings gracefully

### Field Humanization

- [ ] **FIELD-01**: Field names convert from snake_case to Title Case (`privacy_visibility` → "Privacy Visibility")
- [ ] **FIELD-02**: Field names strip `_id` suffix (`company_id` → "Company")
- [ ] **FIELD-03**: Field names strip `_ids` suffix (`group_ids` → "Groups")
- [ ] **FIELD-04**: Dotted paths humanize with possessive form (`project_id.privacy_visibility` → "Project's Privacy Visibility")

### Odoo-Aware Mappings

- [ ] **ODOO-01**: Common system fields map to UI labels (`create_uid` → "Created By", `write_uid` → "Last Updated By", `create_date` → "Created On", `write_date` → "Last Updated On", `active` → "Active")
- [ ] **ODOO-02**: User references render as human-readable (`user.id` → "current user", `user.partner_id.id` → "current user's Partner", `user.groups_id.ids` → "current user's Groups")

### Value Humanization

- [ ] **VALUE-01**: `False` and `None` render as "Not set" in pseudocode
- [ ] **VALUE-02**: `(1, '=', 1)` pattern renders as "Always True (all records)"
- [ ] **VALUE-03**: `(0, '=', 1)` pattern renders as "Always False (no records)"

### Domain Validation

- [ ] **VALID-01**: Connect to Odoo instance via XML-RPC API
- [ ] **VALID-02**: GUI settings panel for Odoo connection (URL, database, username, password)
- [ ] **VALID-03**: Validate field existence on specified model
- [ ] **VALID-04**: Validate operator compatibility for field type
- [ ] **VALID-05**: Validate dotted path traversal (relations exist along the path)
- [ ] **VALID-06**: Warn if value type doesn't match field type

### Python Output

- [ ] **PYOUT-01**: Python output applies field humanization
- [ ] **PYOUT-02**: Python output maintains readable syntax while being Python-like

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

(None — all discussed features included in v1)

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Web interface | Desktop GUI sufficient for this use case |
| Reverse conversion (pseudocode → domain) | One-way conversion only |
| Computed domains / Python code evaluation | Static parsing only |
| Domain editing/fixing | Read-only analysis, not an editor |

## Traceability

Which phases cover which requirements. Updated by create-roadmap.

| Requirement | Phase | Status |
|-------------|-------|--------|
| PARSE-01 | — | Pending |
| PARSE-02 | — | Pending |
| PARSE-03 | — | Pending |
| FIELD-01 | — | Pending |
| FIELD-02 | — | Pending |
| FIELD-03 | — | Pending |
| FIELD-04 | — | Pending |
| ODOO-01 | — | Pending |
| ODOO-02 | — | Pending |
| VALUE-01 | — | Pending |
| VALUE-02 | — | Pending |
| VALUE-03 | — | Pending |
| VALID-01 | — | Pending |
| VALID-02 | — | Pending |
| VALID-03 | — | Pending |
| VALID-04 | — | Pending |
| VALID-05 | — | Pending |
| VALID-06 | — | Pending |
| PYOUT-01 | — | Pending |
| PYOUT-02 | — | Pending |

**Coverage:**
- v1 requirements: 20 total
- Mapped to phases: 0
- Unmapped: 20 ⚠️ (awaiting roadmap)

---
*Requirements defined: 2026-01-17*
*Last updated: 2026-01-17 after initial definition*
