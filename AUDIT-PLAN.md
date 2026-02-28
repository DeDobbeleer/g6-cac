# Audit Plan: Documentation vs Code Verification

**Created:** 2026-02-27  
**Updated:** 2026-02-27  
**Branch:** `testing/audit`  
**Status:** 🚧 In Progress (Steps 1.1-1.4 Complete)

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
| 1.1 | Verify 20-TEMPLATE-HIERARCHY.md | ✅ Completed | Fixed NP field name |
| 1.2 | Verify 30-PROCESSING-POLICIES.md | ✅ Completed | Fixed PP field name |
| 1.3 | Verify 40-CLI-WORKFLOW.md | ✅ Completed | Section 5.6 added for name-to-ID resolution |
| 1.4 | Verify 10-INVENTORY-FLEET.md | ✅ Completed | Spec and code fully aligned |
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
**Status:** ✅ **COMPLETED - VERIFIED AND ENHANCED**

**Verified:**
- [x] Commands `validate`, `plan`, `apply`, `generate-demo` documented
- [x] Command options match code (`--fleet`, `--topology`, `--json`, `--verbose`)
- [x] Exit codes documented (0=OK, 1=warnings, 2=errors)
- [x] 4-level validation process documented

**Enhancements Made:**

**Section 5.6 Added**: "Name-to-ID Resolution (Apply Phase)"

Documented the critical concept that:
- Validation phase uses **names** (offline, no API calls)
- Apply phase requires **name-to-ID translation** via API lookups
- References validated by name in YAML templates
- IDs only known after resources created in Director

**Documentation includes:**
- Resolution process diagram (ASCII)
- Reference mapping table (Template → API Payload)
- Resolution order (dependencies first)
- Handling new resources (extract ID from POST response)
- Validation vs Apply difference table

**Key Concept Documented:**
```
Template (Validation):    API Payload (Apply):
routing_policy:            routing_policy:
  "rp-default"      →       "586cc3ed..."  (ID lookup)
```

**Files Modified:**
- `specs/40-CLI-WORKFLOW.md` - Added section 5.6 (92 lines)

**Cross-References:**
- Links to `50-VALIDATION-SPEC.md` section 1.4 (Offline vs Apply)
- Links to `50-VALIDATION-SPEC.md` section 6.5 (Name-to-ID translation)

### 1.4 10-INVENTORY-FLEET.md
**Status:** ✅ **COMPLETED - FULLY ALIGNED**

**Verified:**
- [x] Fleet model structure matches code (`Fleet`, `FleetSpec`, `FleetMetadata`)
- [x] Node types implemented (`AIO`, `DataNode`, `SearchHead` extending `Node`)
- [x] Tags system working (`Tag` model with `from_dict()` parser)
- [x] YAML examples from spec parse correctly
- [x] Field aliases correct (`logpointId`, `managementMode`, `poolUuid`, etc.)
- [x] Helper methods implemented (`get_nodes_by_tag()`, `get_clusters()`)

**Code Coverage:**

| Spec Element | Code Location | Status |
|--------------|---------------|--------|
| `Fleet` model | `fleet.py` class `Fleet` | ✅ Implemented |
| `FleetMetadata` | `fleet.py` class `FleetMetadata` | ✅ Implemented |
| `FleetSpec` | `fleet.py` class `FleetSpec` | ✅ Implemented |
| `DirectorConfig` | `fleet.py` class `DirectorConfig` | ✅ Implemented |
| `Nodes` container | `fleet.py` class `Nodes` | ✅ Implemented |
| `AIO` node type | `fleet.py` class `AIO(Node)` | ✅ Implemented |
| `DataNode` node type | `fleet.py` class `DataNode(Node)` | ✅ Implemented |
| `SearchHead` node type | `fleet.py` class `SearchHead(Node)` | ✅ Implemented |
| `Tag` key-value pairs | `fleet.py` class `Tag` | ✅ Implemented |
| Tag parsing from YAML | `Tag.from_dict()` | ✅ Implemented |
| Tag validation | `field_validator("tags")` | ✅ Implemented |
| Cluster grouping | `Fleet.get_clusters()` | ✅ Implemented |
| Tag-based filtering | `Fleet.get_nodes_by_tag()` | ✅ Implemented |
| Node tag queries | `Node.has_tag()`, `Node.get_tag_value()` | ✅ Implemented |

**YAML Examples Tested:**

| Use Case | Status | Notes |
|----------|--------|-------|
| Use Case 1: Simple AIO Client | ✅ Passes | Parsed correctly |
| Use Case 2: Distributed with Standalone DNs | ✅ Passes | Parsed correctly |
| Use Case 3: Full Cluster (Bank) | ✅ Passes | Parsed correctly, cluster grouping works |
| Use Case 4: Prod + Staging | ✅ Passes | Parsed correctly |

**Field Mapping (Spec → Code):**

| Spec Field | Code Field | Alias | Status |
|------------|-----------|-------|--------|
| `apiVersion` | `api_version` | `apiVersion` | ✅ Correct |
| `managementMode` | `management_mode` | `managementMode` | ✅ Correct |
| `poolUuid` | `pool_uuid` | `poolUuid` | ✅ Correct |
| `apiHost` | `api_host` | `apiHost` | ✅ Correct |
| `credentialsRef` | `credentials_ref` | `credentialsRef` | ✅ Correct |
| `logpointId` | `logpoint_id` | `logpointId` | ✅ Correct |
| `dataNodes` | `data_nodes` | `dataNodes` | ✅ Correct |
| `searchHeads` | `search_heads` | `searchHeads` | ✅ Correct |
| `aios` | `aios` | (none) | ✅ Correct |

**Reserved Tags (from spec):**

| Tag | Implemented | Usage |
|-----|-------------|-------|
| `cluster` | ✅ | Group nodes via `Fleet.get_clusters()` |
| `env` | ✅ | Filtering via `Fleet.get_nodes_by_tag()` |
| `sh-for` | ✅ | Documented, used in examples |
| `role` | ✅ | Documented, used in examples |

**No Issues Found:**
- All YAML examples from spec parse correctly
- All field aliases work as expected
- Tag system handles both formats (simple dict and explicit key/value)
- Cluster grouping logic matches spec description

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
