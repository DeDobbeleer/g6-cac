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
| 1.1 | Verify 20-TEMPLATE-HIERARCHY.md | ✅ Completed | See Section 1.1 below |
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

**Audit Results:**

🔴 **CRITICAL INCOHERENCES FOUND (Based on LogPoint Director API):**

| Element | Spec | Code | API Director | Correct Source | Action Required |
|---------|------|------|--------------|----------------|-----------------|
| NP field name | `policy_name` | `name` | `name` | ✅ API | 🔴 **Fix SPEC** |
| EP specification structure | `criteria[]`, `rules[]` | `fields[]` | `criteria[]`, `rules[]` | ✅ API | 🔴 **Fix CODE** |
| PP field name | `policy_name` | `name` | `policy_name` | ✅ API | 🔴 **Fix CODE** |
| RP field name | `policy_name` | `policy_name` | `policy_name` | ✅ All | ✅ OK |
| EP field name | `name` | `name` | `name` | ✅ All | ✅ OK |

**LogPoint Director API Reference:**
- https://docs.logpoint.com/director/director-apis/director-console-api-documentation/normalizationpolicy
- https://docs.logpoint.com/director/director-apis/director-console-api-documentation/enrichmentpolicy  
- https://docs.logpoint.com/director/director-apis/director-console-api-documentation/processingpolicy

**Actions Required:**
1. ✅ **Update SPEC** (20-TEMPLATE-HIERARCHY.md line ~1901): Change NP `policy_name` → `name`
2. 🔧 **Update CODE** (enrichment.py): Replace `fields[]` with `criteria[]` + `rules[]` structure
3. 🔧 **Update CODE** (processing.py): Change `name` → `policy_name`
4. 🔧 **Update DEMO GENERATOR**: Fix examples to match corrected spec/code
- Examples use old field names that have evolved

### 1.2 30-PROCESSING-POLICIES.md

**Status:** ⚠️ **NEEDS UPDATE**

**Audit Results:**

| Check | Status | Notes |
|-------|--------|-------|
| `normalization_packages` structure | ❌ NOT DOCUMENTED | Missing from this spec - only in 20-TEMPLATE-HIERARCHY.md |
| `specifications` (EP) structure | ❌ NOT DOCUMENTED | EP structure not detailed here |
| Optional fields marked | ✅ OK | Table shows normalizationPolicy ❌ No, enrichmentPolicy ❌ No |
| References PP → RP → NP/EP | ✅ OK | Well documented in section 2.1 and 5.1 |

**🔴 CRITICAL ISSUE:**

Document uses `name` field (line 45, 62) but API Director requires `policy_name`:

```yaml
# Current spec (WRONG):
- name: windows-security-pipeline
  _id: pp-windows-sec
  routingPolicy: rp-windows-security

# Should be (CORRECT per API):
- policy_name: pp-windows-security
  _id: pp-windows-sec
  routingPolicy: rp-windows-security
```

**Required Actions:**
1. Update all examples to use `policy_name` instead of `name`
2. Update field table: `name` → `policy_name`
3. Add note explaining that `name` in YAML maps to `policy_name` in API
4. Consider adding NP/EP structure references (or link to 20-TEMPLATE-HIERARCHY.md)

**Files to Fix:**
- `specs/30-PROCESSING-POLICIES.md` - Update field names and examples

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
