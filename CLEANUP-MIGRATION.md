# Cleanup & Migration Plan

## Current State Analysis

### ✅ What is Ready (Specs)
- 7 specification documents (~3,500 lines)
- 7 ADRs documenting architecture decisions
- All concepts validated (inheritance, tags, CLI workflow)
- PDF versions generated for review

### 🧹 What Needs Cleanup (Code & Docs)

#### 1. Old PoC Code (`lpcac/`)
**Status**: Pre-spec implementation, needs rewrite

**Files to cleanup**:
```
lpcac/
├── models/           # Pydantic models (basic, pre-spec)
│   ├── repos.py      # Simple model, no _id support
│   ├── routing.py    # Basic, no vendor-specific fields
│   ├── normalization.py
│   └── processing.py # Old orchestrator model (wrong)
├── connectors/
│   └── director.py   # Basic connector
├── main.py           # French comments, pre-spec logic
```

**Action**: Complete rewrite based on new specs
- Implement proper Template ID (`_id`) support
- Implement inheritance resolution algorithm
- Implement list ordering (`_after`, `_position`)
- Support multi-file templates

#### 2. Documentation Cleanup

| File | Status | Action |
|------|--------|--------|
| `README.md` | Old PoC description | Rewrite with CaC-ConfigMgr branding |
| `README_POC.md` | Duplicate | Delete |
| `ARCHITECTURE.md` | Old, partial | Delete (replaced by 01-ARCHITECTURE-LOGPOINT) |
| `ARCHITECTURE_full.md` | Outdated | Delete or archive |
| `CONSTRAINTS.md` | Unknown relevance | Review and integrate or delete |
| `Contexte.md` | French duplicate | Delete (keep English version if needed) |
| `context.md` | Unclear purpose | Review and delete or integrate |
| `AGENTS.md` | Product overview | Keep but update references |

#### 3. Configuration Files

| File | Status | Action |
|------|--------|--------|
| `pyproject.toml` | Old project name "lpcac" | Update to "cac-configmgr" |
| `.code-workspace` | VS Code settings | Keep or update |
| `schemas.xml` | Draw.io schemas | Keep (architecture diagrams) |

#### 4. Examples

`examples/simple/` - Basic YAML examples
- Need update to match new spec format
- Add `_id` fields
- Add examples for all resource types

---

## DirSync → CaC Migration Plan

### Understanding DirSync

Based on references in specs, DirSync is:
- **Current tool**: Used for synchronizing configurations
- **Approach**: Imperative (scripts applying changes)
- **Structure**: 
  - `base_config.yaml` (common configuration)
  - `inventory.yaml` (deployment targets)
  - Overlay files (per-client customizations)
  - Jinja2 templating

### Mapping DirSync → CaC

| DirSync Concept | CaC Equivalent | Notes |
|-----------------|----------------|-------|
| `base_config.yaml` | Golden Template (Level 1) | Convert to ConfigTemplate |
| `inventory.yaml` | Fleet + TopologyInstance | Split: Fleet (nodes), Topology (config) |
| `vars` in inventory | `spec.vars` in instance | Variables for interpolation |
| Overlay files | Template inheritance chain | Much cleaner, no duplication |
| Jinja2 rendering | Template resolution + interpolation | Post-resolution variable substitution |

### Migration Steps

#### Phase 1: Analysis (No changes to DirSync)
1. **Audit current DirSync configurations**
   - Document all base_config.yaml variants
   - Document all inventory structures
   - Identify custom overlays

2. **Mapping exercise**
   - Map each DirSync resource to CaC resource type
   - Identify gaps (resources not yet in CaC specs)
   - Document Jinja2 variables used

#### Phase 2: Parallel Implementation
1. **Implement CaC side-by-side**
   - New CaC configs in separate directory
   - Validate CaC configs against DirSync output
   - Ensure parity (same result, different method)

2. **Test with non-production pool**
   - Use CaC `plan` to compare with DirSync
   - Verify no drift between DirSync and CaC declarations

#### Phase 3: Gradual Migration
1. **Migrate one client type**
   - Simple clients first (AIO only)
   - Keep DirSync as fallback
   - Monitor for issues

2. **Migrate remaining clients**
   - Medium complexity (distributed)
   - Complex clients (multi-cluster)

3. **Decommission DirSync**
   - Once all clients migrated
   - Archive DirSync configs for history

### Specific Migration Tasks

#### Repos Migration
```yaml
# DirSync (base_config.yaml)
repos:
  - name: repo-secu
    hiddenrepopath:
      - path: /opt/immune/storage
        retention: 365

# CaC (templates/logpoint/golden-base/repos.yaml)
spec:
  repos:
    - name: repo-secu
      hiddenrepopath:
        - _id: primary          # Added: Template ID
          path: /opt/immune/storage
          retention: 365
```

#### Inventory Migration
```yaml
# DirSync (inventory.yaml)
client: acme-corp
vars:
  retention: 180
  mount_point: /opt/immune/storage-warm

# CaC (instances/acme-corp/prod/instance.yaml)
spec:
  vars:
    retention: 180
    mount_point: /opt/immune/storage-warm
  repos:
    - name: repo-secu
      hiddenrepopath:
        - _id: primary
          retention: "{{retention}}"  # Variable interpolation
```

---

## Cleanup Checklist

### Immediate (Before Implementation)
- [ ] Delete `README_POC.md`
- [ ] Delete `ARCHITECTURE.md` (duplicate)
- [ ] Delete `ARCHITECTURE_full.md` (outdated)
- [ ] Delete `Contexte.md` (French duplicate)
- [ ] Review and delete/integrate `context.md`
- [ ] Review and delete/integrate `CONSTRAINTS.md`
- [ ] Update `README.md` with CaC-ConfigMgr branding
- [ ] Update `pyproject.toml` (project name, description)
- [ ] Move old `lpcac/` to `lpcac-old/` (archive) or delete

### During Implementation
- [ ] Create new `cacconfigmgr/` package (or `src/cac_configmgr/`)
- [ ] Implement models from specs
- [ ] Implement resolution algorithm
- [ ] Implement CLI commands

### DirSync Migration (Later)
- [ ] Document current DirSync configurations
- [ ] Create migration scripts (DirSync → CaC YAML)
- [ ] Validate migrations
- [ ] Execute phased migration
- [ ] Decommission DirSync

---

## Recommended Next Steps

1. **Cleanup documentation** (1 hour)
   - Delete obsolete files
   - Update README.md

2. **Archive old code** (30 min)
   - Move `lpcac/` to archive or delete
   - Keep Git history for reference

3. **Start fresh implementation** (Next phase)
   - Create new package structure
   - Implement from specs

4. **DirSync audit** (Parallel track)
   - Document current state
   - Plan migration

---

**Decision needed**: Do you want to keep the old PoC code for reference, or delete it completely and start fresh from specs?
