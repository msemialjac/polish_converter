# Requirements: Odoo Domain Converter

**Defined:** 2026-01-17
**Core Value:** Domains with dynamic references must parse successfully and produce genuinely readable output that a non-developer Odoo user can understand.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Parsing

- [x] **PARSE-01**: Parser handles domains containing dynamic references (`user.id`, `user.partner_id.id`, `company_ids`)
- [x] **PARSE-02**: Parser handles domains containing dotted field paths (`account_online_link_id.company_id`)
- [x] **PARSE-03**: Parser handles multi-line domain strings gracefully

### Field Humanization

- [x] **FIELD-01**: Field names convert from snake_case to Title Case (`privacy_visibility` → "Privacy Visibility")
- [x] **FIELD-02**: Field names strip `_id` suffix (`company_id` → "Company")
- [x] **FIELD-03**: Field names strip `_ids` suffix (`group_ids` → "Groups")
- [x] **FIELD-04**: Dotted paths humanize with possessive form (`project_id.privacy_visibility` → "Project's Privacy Visibility")

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
| PARSE-01 | Phase 1 | Complete |
| PARSE-02 | Phase 1 | Complete |
| PARSE-03 | Phase 1 | Complete |
| FIELD-01 | Phase 2 | Complete |
| FIELD-02 | Phase 2 | Complete |
| FIELD-03 | Phase 2 | Complete |
| FIELD-04 | Phase 2 | Complete |
| ODOO-01 | Phase 3 | Pending |
| ODOO-02 | Phase 3 | Pending |
| VALUE-01 | Phase 3 | Pending |
| VALUE-02 | Phase 3 | Pending |
| VALUE-03 | Phase 3 | Pending |
| VALID-01 | Phase 5 | Pending |
| VALID-02 | Phase 5 | Pending |
| VALID-03 | Phase 5 | Pending |
| VALID-04 | Phase 5 | Pending |
| VALID-05 | Phase 5 | Pending |
| VALID-06 | Phase 5 | Pending |
| PYOUT-01 | Phase 4 | Pending |
| PYOUT-02 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 20 total
- Mapped to phases: 20
- Unmapped: 0 ✓

---
*Requirements defined: 2026-01-17*
*Last updated: 2026-01-17 after roadmap creation*
