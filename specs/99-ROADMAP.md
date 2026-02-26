# Roadmap & Status

**Last Updated**: 2026-02-26  
**Language**: All deliverables in **English** (specifications, code, documentation)  
**Status**: Routing Policies - ✅ COMPLETE  
**Last Commit**: f1781b1 - tmp/ directory setup  
**Next Step**: Define Processing Policies or Workflow CLI

---

## Project Assets Created

### Specifications (specs/)
- ✅ `00-VISION.md` - Product vision (EN)
- ✅ `01-ARCHITECTURE-LOGPOINT.md` - LogPoint architecture reference (EN)
- ✅ `10-INVENTORY-FLEET.md` - Fleet inventory specification (EN)
- ✅ `20-TEMPLATE-HIERARCHY.md` - Template system with Routing Policies (EN)

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
- [ ] **Processing Policies**: To be defined (normalization → enrichment → processing)
- [ ] **Alert Rules**: To be defined
- [ ] **Workflow CLI**: Commands and state transitions to be defined

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
3. **Define Processing Policies** (normalization → enrichment → processing pipeline)
4. **Define Alert Rules** (detection rules)
5. **Define CLI Workflow** (commands: validate, plan, apply, drift)
6. **Create Pydantic models** from validated specs
7. **Implement Provider interface** for Director API
