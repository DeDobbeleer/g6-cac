# Roadmap & Status

**Last Updated**: 2026-02-27  
**Language**: All deliverables in **English** (specifications, code, documentation)  
**Status**: Phase 1 Implementation - ✅ COMPLETE  
**Last Commit**: 55c4a45 - Validation system with name-based cross-references  
**Next Step**: Phase 2 - Director API integration (plan/apply commands)

---

## Project Assets Created

### Specifications (specs/)
- ✅ `00-VISION.md` - Product vision (EN)
- ✅ `01-ARCHITECTURE-LOGPOINT.md` - LogPoint architecture reference (EN)
- ✅ `10-INVENTORY-FLEET.md` - Fleet inventory specification (EN)
- ✅ `20-TEMPLATE-HIERARCHY.md` - Template system with Routing Policies (EN)
- ✅ `30-PROCESSING-POLICIES.md` - Processing Policies specification (EN)
- ✅ `40-CLI-WORKFLOW.md` - CLI commands and workflow (EN)
- ✅ `50-VALIDATION-SPEC.md` - Validation specification (EN)

### Standards (docs/)
- ✅ `CODING-STANDARDS.md` - Python coding standards (EN)

---

## Concept Checklist

### 1. Vision & Name
- [x] Target audience defined (MSSP → Enterprise)
- [x] Promised values identified
- [x] **PRODUCT NAME VALIDATED**: CaC-ConfigMgr CaC
- [x] **LANGUAGE DECISION**: All deliverables in English

### 2. Technical Concepts
- [x] **Pseudo-Cluster**: Defined (DataNodeCluster, SearchHeadCluster) - Q3=A
- [x] **Fleet Inventory**: ✅ COMPLETE (tag-based approach) - Q5=Permissive
- [x] **Template Hierarchy**: ✅ COMPLETE with Template ID mechanism
- [x] **Routing Policies**: ✅ COMPLETE (vendor-specific, with drop/filter support)
- [x] **Processing Policies**: ✅ COMPLETE (glue resource: RP+NP+EP)
- [x] **Workflow CLI**: ✅ COMPLETE (validate/plan/apply/drift/backup)
- [x] **Validation Spec**: ✅ COMPLETE (4-level validation, name-based cross-refs)
- [ ] **Alert Rules**: To be defined (post-MVP)

### 3. DirSync Reference
- [x] Director API documented (via DirSync)
- [x] Object dependencies known
- [ ] CaC-ConfigMgr CaC ↔ DirSync mapping (to be done)

---

## Decision Log

### 2026-02-26
- **Decision**: Do NOT start from DirSync as code base, but as technical reference
- **Decision**: Dual target mode (Director MSSP first, Direct Enterprise later)
- **Decision**: Focus on "pseudo-cluster" (problem not solved by LogPoint today)
- **Decision**: All deliverables (specs, code, docs) in **English**
- **Decision**: Python 3.10+, Pydantic v2, Typer, Rich

---

## Open Questions (Answer these to proceed)

### ✅ Q1: Cluster-scoped variables - RESOLVED
**Answer**: **B** - Variables in configuration/topology, not in Fleet
- Fleet defines structure (nodes, clusters, tags)
- Topology defines config values (retention, paths, etc.)

### ✅ Q2: SH connected to individual DNs - RESOLVED
**Answer**: **A** - Use tags for relationships
- Tags define cluster membership: `cluster: production`
- Tags define SH visibility: `sh-for: production`
- Flexible, no hardcoded references

### ✅ Q3: AIO clustering? - RESOLVED
**Answer**: **A** - Yes, AIOs can be clustered via tags
- Use case: DRP (Disaster Recovery Plan)
- Tag `cluster: drp-ha` on multiple AIOs

### ✅ Q4: Prod/Staging/Tests - RESOLVED
**Answer**: **A** - Single `fleet.yaml` with `env: prod`, `env: staging` tags
- Environment filtering via tags
- No separate files needed

---

## Next Milestones

1. ~~**Validate Fleet spec**~~ ✅ COMPLETE
2. ~~**Define Configuration (Topology)**~~ ✅ COMPLETE (Template Hierarchy)
3. ~~**Define Processing Policies**~~ ✅ COMPLETE
4. ~~**Define CLI Workflow**~~ ✅ COMPLETE
5. ~~**Create Pydantic models**~~ ✅ COMPLETE (40 tests passing)
6. ~~**Implement Validation**~~ ✅ COMPLETE (4-level validation)
7. **Implement Director Provider** for plan/apply commands
6. **Implement Provider interface** for Director API
7. **Define Alert Rules** (detection rules - post-MVP)
