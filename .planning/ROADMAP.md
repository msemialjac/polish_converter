# Roadmap: Odoo Domain Converter

## Overview

Transform the domain converter from a basic tool using `ast.literal_eval()` into a fully-featured Odoo domain analyzer. Start with a custom parser that handles dynamic references, layer on humanization features for readable output, then add Odoo instance validation for real-time field checking.

## Domain Expertise

None

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

- [x] **Phase 1: Custom Parser** - Replace ast.literal_eval() with tokenizer handling dynamic references
- [x] **Phase 2: Field Humanization** - Convert technical field names to readable labels
- [x] **Phase 3: Odoo-Aware Output** - System field mappings and value humanization
- [x] **Phase 4: Python Output Enhancement** - Apply humanization to Python output format
- [ ] **Phase 5: Odoo Validation** - XML-RPC connection and field validation

## Phase Details

### Phase 1: Custom Parser
**Goal**: Replace `ast.literal_eval()` with a custom tokenizer/parser that treats variable references (`user.id`, `company_ids`) as tokens rather than attempting to evaluate them
**Depends on**: Nothing (first phase)
**Requirements**: PARSE-01, PARSE-02, PARSE-03
**Research**: Unlikely (internal tokenizer/parser, no external APIs)
**Plans**: TBD

Plans:
- [x] 01-01: Custom domain parser with DynamicRef (TDD)

### Phase 2: Field Humanization
**Goal**: Convert snake_case field names to Title Case, strip _id/_ids suffixes, humanize dotted paths with possessive form
**Depends on**: Phase 1
**Requirements**: FIELD-01, FIELD-02, FIELD-03, FIELD-04
**Research**: Unlikely (string manipulation, established patterns)
**Plans**: TBD

Plans:
- [x] 02-01: Field humanization with TDD (humanize_field, _id/_ids suffix stripping, possessive paths)

### Phase 3: Odoo-Aware Output
**Goal**: Map system fields to UI labels, render user references as human-readable, humanize special values (False/None as "Not set", tautology patterns)
**Depends on**: Phase 2
**Requirements**: ODOO-01, ODOO-02, VALUE-01, VALUE-02, VALUE-03
**Research**: Unlikely (mapping dictionaries, internal logic)
**Plans**: TBD

Plans:
- [x] 03-01: Odoo-aware output with TDD (system fields, user refs, value humanization, tautologies)

### Phase 4: Python Output Enhancement
**Goal**: Apply field humanization to Python output while maintaining readable Python-like syntax
**Depends on**: Phase 2, Phase 3
**Requirements**: PYOUT-01, PYOUT-02
**Research**: Unlikely (extends existing patterns from Phase 2/3)
**Plans**: TBD

Plans:
- [x] 04-01: Python output humanization with TDD (to_python_identifier, field humanization, DynamicRef)

### Phase 5: Odoo Validation
**Goal**: Connect to Odoo via XML-RPC, add settings panel, validate fields exist on model, check operator compatibility, validate dotted path traversal, warn on type mismatches
**Depends on**: Phase 1
**Requirements**: VALID-01, VALID-02, VALID-03, VALID-04, VALID-05, VALID-06
**Research**: Likely (external API integration)
**Research topics**: Odoo XML-RPC API patterns, field introspection methods (fields_get), model metadata access, ir.model queries
**Plans**: TBD

Plans:
- [x] 05-01: Odoo connection client + GUI settings panel (VALID-01, VALID-02)
- [x] 05-02: Field existence and path traversal validation (VALID-03, VALID-05)
- [ ] 05-03: Operator compatibility and value type validation (VALID-04, VALID-06)

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Custom Parser | 1/1 | Complete | 2026-01-17 |
| 2. Field Humanization | 1/1 | Complete | 2026-01-17 |
| 3. Odoo-Aware Output | 1/1 | Complete | 2026-01-17 |
| 4. Python Output Enhancement | 1/1 | Complete | 2026-01-17 |
| 5. Odoo Validation | 2/3 | In progress | - |
