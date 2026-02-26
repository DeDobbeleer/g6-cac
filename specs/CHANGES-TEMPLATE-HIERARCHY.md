# Changes in Template Hierarchy Specification

**Document**: 20-TEMPLATE-HIERARCHY.md  
**Version**: Teams (old) → Current (2026-02-26)  
**Comparison**: PDF "20-TEMPLATE-HIERARCHY-old.pdf" vs Current Markdown

---

## Executive Summary of Changes

The specification evolved from a basic hierarchical template concept to a comprehensive system with:
- Clear inheritance mechanisms (Cross-Level vs Intra-Level)
- List ordering specification moved to main sections
- Simplified Processing Policy definition (glue resource, not orchestrator)
- Complete CLI workflow specification

---

## Major Changes by Section

### 1. Structure & Organization

| Aspect | Old (Teams) | Current | Impact |
|--------|-------------|---------|--------|
| **Section 3** | Basic inheritance only | Added Intra-Level inheritance (3.2) | Allows templates at same level to extend each other |
| **Section 3.5** | Minimal (Template IDs only) | Complete List Merging & Ordering | Critical for list element positioning |
| **Section 7** | Basic directory structure | Detailed file structure rules (7.1-7.4) | Clear separation: multi-file (templates) vs single-file (instances) |
| **Appendices** | Complete specs in appendices | Concepts moved to main sections | Better flow: concepts first, examples after |

### 2. Key Concepts Added

#### 2.1 Intra-Level Inheritance (NEW - Section 3.2)

**What**: Templates at the same hierarchy level can extend each other.

**Use cases**:
- `golden-base` → `golden-pci-dss` (Level 1 → Level 1)
- `enterprise` → `banking-addon` (Level 3 → Level 3)

**Example**:
```yaml
# templates/logpoint/golden-pci-dss/repos.yaml
metadata:
  name: golden-pci-dss
  extends: logpoint/golden-base  # Level 1 → Level 1 (intra-level)
```

**Resolution order**:
```
logpoint/golden-base
└── (intra) logpoint/golden-pci-dss
    └── (cross) mssp/acme-corp/base
        └── (intra) mssp/acme-corp/profiles/enterprise
            └── (cross) instances/client-bank/prod
```

#### 2.2 List Ordering Specification (MOVED to Section 3.5)

**Before**: Appendix F (80+ lines, complete specification)
**After**: Section 3.5 (integrated in main concepts)

**Mechanisms preserved**:
| Attribute | Purpose |
|-----------|---------|
| `_after: _id` | Insert after element |
| `_before: _id` | Insert before element |
| `_position: N` | Absolute position (1-based) |
| `_first: true` | Force first position |
| `_last: true` | Force last position |

**Precedence rules**: Moved to Section 3.5.4

### 3. Simplifications

#### 3.1 Processing Policies (DRASTICALLY SIMPLIFIED)

**Old understanding**: Complex pipeline orchestration with steps, conditions, optional flags
```yaml
# OLD (over-engineered)
pipeline:
  - step: routing
    policy_ref: rp-windows
  - step: normalization  
    policy_ref: np-windows
    condition: "device_product == 'Windows'"
    optional: true
  - step: enrichment
    policy_ref: ep-geoip
```

**Current**: Simple glue resource
```yaml
# CURRENT (simplified)
processingPolicies:
  - name: windows-security
    _id: pp-windows-sec
    routingPolicy: rp-windows-security        # ← Reference only
    normalizationPolicy: np-windows           # ← Reference only
    enrichmentPolicy: ep-geoip-threatintel    # ← Reference only
```

**Rationale**: Processing Policy is just a convenience resource linking 3 other policies. No complex orchestration needed.

### 4. File Structure Clarifications

#### 4.1 Multi-file vs Single-file Rule (NEW in Section 7.1)

| Level | Structure | Rule |
|-------|-----------|------|
| **Level 1-3** (LogPoint, MSSP, Profiles) | **Multi-file** | One file per config type: `repos.yaml`, `routing-policies.yaml`, etc. |
| **Level 4** (Instances) | **Single-file** | One `instance.yaml` containing only overrides |

**Example**:
```
templates/
├── logpoint/
│   ├── golden-base/              # ← Directory (multi-file)
│   │   ├── repos.yaml
│   │   ├── routing-policies.yaml
│   │   └── normalization-policies.yaml
│   └── golden-pci-dss/           # ← Directory (multi-file)
│       └── repos.yaml            # Overrides for compliance
└── instances/
    └── client-bank/
        └── prod/
            └── instance.yaml     # ← Single file (not directory)
```

### 5. Appendix Changes

| Appendix | Old | Current |
|----------|-----|---------|
| **A** | Complete example (kept) | Reference to examples/ directory |
| **B** | JSON Schema placeholder | Reference to schemas/ directory |
| **C** | Complete repo example with Template IDs | Same, file paths updated |
| **D** | Routing Policies example | Same, file paths updated |
| **E** | Normalization & Enrichment | Same, simplified E.4 |
| **F** | Complete List Ordering Specification | **REMOVED** (moved to Section 3.5) |

### 6. CLI Workflow (NEW - Separate Document)

**Before**: Mentioned as "to be defined" in Vision
**After**: Complete specification in `40-CLI-WORKFLOW.md`

Commands specified:
- `validate` - Syntax and consistency checks
- `plan` - Calculate diff
- `apply` - Deploy changes
- `drift` - Detect divergences
- `backup` - Export configuration

### 7. Terminology Consistency

| Old/Unclear | Current | Notes |
|-------------|---------|-------|
| "topology.yaml" | "instance.yaml" | Clearer: topology is the concept, instance is the file |
| "banque-dupont" | "client-bank" | Generic example name |
| Template "variants" | Template "add-ons" (intra-level) | Clearer distinction |
| "process" (verb) | "processing policy" (noun) | Avoids confusion |

---

## Breaking Changes (if implemented from old spec)

None - the changes are clarifications and additions. The core mechanism (4-level hierarchy, `_id` for matching) remains unchanged.

---

## Recommendations for Reviewers

### Focus Areas

1. **Intra-Level Inheritance (Section 3.2)**
   - New concept not in Teams version
   - Critical for compliance templates (PCI, ISO)

2. **List Ordering (Section 3.5)**
   - Moved from Appendix F to main sections
   - Essential for routing criteria ordering

3. **Processing Policies (Section 3 in PP doc)**
   - Completely simplified
   - Verify this matches LogPoint API reality

4. **File Structure Rules (Section 7.1)**
   - Multi-file vs single-file decision
   - Impacts tooling and validation

### Questions to Resolve

1. **Intra-level depth**: Limit to 1 level (base → addon) or allow chains?
2. **Processing Policy**: Are NP and EP truly optional? What's the default?
3. **CLI**: State file or stateless? (Open question in 40-CLI-WORKFLOW.md)

---

## Document Statistics

| Metric | Old (Teams) | Current | Delta |
|--------|-------------|---------|-------|
| **Total lines** | ~1,800 | ~2,070 | +270 (+15%) |
| **Main sections** | 7 | 8 | +1 (intra-level inheritance) |
| **Appendices** | 6 | 5 | -1 (F moved to main) |
| **Code examples** | 45 | 52 | +7 |
| **Open questions** | 5 | 3 | -2 resolved |

---

## Next Steps

1. **Validate** the simplified Processing Policy model with LogPoint API
2. **Confirm** intra-level inheritance use cases (PCI, ISO templates)
3. **Decide** on CLI state management (state file vs stateless)
4. **Create** Pydantic models from finalized specifications

---

**Comparison Date**: 2026-02-26  
**Compared by**: CaC-ConfigMgr Product Team  
**Status**: Ready for final review
