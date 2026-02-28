# Audit Plan: Documentation vs Code Verification

**Created:** 2026-02-27  
**Branch:** `testing/audit`  
**Status:** 🚧 In Progress

---

## Objective

Verify consistency between:
- Technical specifications (`specs/*.md`)
- Implemented code (`src/`)
- Project status (`PROJECT-STATUS.md`)
- Architecture decisions (`ADRS.md`)

---

## Audit Progress Status

| Step | Description | Status | Result |
|------|-------------|--------|--------|
| 0 | Create audit plan | ✅ Completed | This file |
| 1 | Verify technical specs | ⏳ Pending | - |
| 2 | Verify project status | ⏳ Pending | - |
| 3 | Verify ADRs | ⏳ Pending | - |
| 4 | Verify other MD files | ⏳ Pending | - |
| 5 | Code ↔ Specs sync | ⏳ Pending | - |
| 6 | Final report & actions | ⏳ Pending | - |

---

## Step 1: Technical Specifications (`specs/*.md`)

### 1.1 20-TEMPLATE-HIERARCHY.md
**To verify:**
- [ ] Model structures (NP/EP/PP) match code
- [ ] **ALL YAML examples in spec match current hierarchy structure**
- [ ] Documented fields exist in Pydantic models
- [ ] Aliases (`routingPolicy`, `normalizationPackages`) consistent
- [ ] Inheritance and merging logic matches implementation

**Potential red flags:**
- Spec describes fields that don't exist
- Different structure between spec and code
- YAML examples in spec don't work or use outdated structure
- Examples use old field names that have evolved

### 1.2 30-PROCESSING-POLICIES.md
**To verify:**
- [ ] `normalization_packages` structure documented
- [ ] `specifications` (EP) structure documented
- [ ] Optional fields (`enrichmentPolicy`) marked as such
- [ ] References PP → RP → NP/EP documented

### 1.3 40-CLI-WORKFLOW.md
**To verify:**
- [ ] Commands `validate`, `plan`, `generate-demo` documented
- [ ] Command options match code
- [ ] Exit codes and errors documented

### 1.4 10-INVENTORY-FLEET.md
**To verify:**
- [ ] Fleet model with tags
- [ ] Node structure (DataNode, SearchHead, AIO)
- [ ] Tags and clusters documented

---

## Step 2: Project Status (`PROJECT-STATUS.md`)

### 2.1 Phase 1 (MVP)
**To verify:**
- [ ] Items marked "✅ Done" are actually done
- [ ] "🚧 In Progress" features are in progress
- [ ] P0/P1/P2 resources match code

### 2.2 Implemented Resources
**Code vs Status mapping:**
| Resource | Code | Status.md | Consistent? |
|----------|------|-----------|-------------|
| Repos | ✅ | ? | - |
| Routing Policies | ✅ | ? | - |
| Processing Policies | ✅ | ? | - |
| Normalization Policies | ✅ | ? | - |
| Enrichment Policies | ✅ | ? | - |
| Devices | ✅ | ? | - |
| Alert Rules | ❌ | ? | - |

---

## Step 3: Architecture Decision Records (`ADRS.md`)

### 3.1 ADR-001: Python
**To verify:**
- [ ] Still current
- [ ] Correct Python version

### 3.2 ADR-002: Template ID with `_id`
**To verify:**
- [ ] Implemented in all models
- [ ] `_id` matching logic works

### 3.3 ADR-003: Multi-level Inheritance
**To verify:**
- [ ] 4 documented levels = implemented
- [ ] Intra-level and Cross-level work

### 3.4 Missing ADRs
**Potentially to add:**
- [ ] NP/EP structure (packages vs single ref)
- [ ] Dependency validation
- [ ] `None` → `"None"` handling

---

## Step 4: Other Markdown Files

### 4.1 README.md
**To verify:**
- [ ] Accurate for current project
- [ ] Installation commands work
- [ ] Badges and links valid

### 4.2 AGENTS.md
**To verify:**
- [ ] Developer info correct
- [ ] Project structure up to date
- [ ] Build commands valid

### 4.3 DEMO-SCRIPT.md
**To verify:**
- [ ] Matches actual demo
- [ ] Commands copy-pasteable
- [ ] Realistic timing

### 4.4 CLEANUP-MIGRATION.md
**To verify:**
- [ ] Still relevant or obsolete
- [ ] Cleanup actions done

---

## Step 5: Code ↔ Specs Synchronization

### 5.1 Pydantic Models vs Specs
| Model | File | Code Fields | Spec Fields | Consistent? |
|-------|------|-------------|-------------|-------------|
| Repo | repos.py | ? | ? | - |
| RoutingPolicy | routing.py | ? | ? | - |
| ProcessingPolicy | processing.py | ? | ? | - |
| NormalizationPolicy | normalization.py | ? | ? | - |
| EnrichmentPolicy | enrichment.py | ? | ? | - |
| Fleet | fleet.py | ? | ? | - |

### 5.2 Aliases and Serialization
**To verify:**
- [ ] `by_alias=True/False` consistent with specs
- [ ] Internal fields (`_id`, `_action`) filtered correctly
- [ ] API payload = expected DirSync format

---

## Step 6: Final Report

### 6.1 Inconsistencies Found
*To fill after steps 1-5*

### 6.2 Corrective Actions
*To fill after steps 1-5*

### 6.3 Files to Update
*To fill after steps 1-5*

---

## Final Checklist

- [ ] All specs up to date with code
- [ ] PROJECT-STATUS.md reflects real state
- [ ] ADRs cover all major decisions
- [ ] README.md is accurate
- [ ] DEMO-SCRIPT.md matches reality

---

## Notes

*Add notes here during audit*
