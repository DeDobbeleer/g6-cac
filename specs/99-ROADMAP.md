# Roadmap & Status

**Last Updated**: 2026-02-26  
**Language**: All deliverables in **English** (specifications, code, documentation)  
**Status**: Hierarchical Template System - ✅ COMPLETE with Template IDs  
**Next Step**: Validate Q3 (AIO clustering) and tag validation rules

---

## Project Assets Created

### Specifications (specs/)
- ✅ `00-VISION.md` - Product vision (EN)
- ✅ `01-ARCHITECTURE-LOGPOINT.md` - LogPoint architecture reference (EN)
- ✅ `10-INVENTORY-FLEET.md` - Fleet inventory specification (EN)

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
- [x] **Pseudo-Cluster**: Defined (DataNodeCluster, SearchHeadCluster)
- [x] **Fleet Inventory**: ✅ COMPLETE (tag-based approach)
- [x] **Template Hierarchy**: ✅ COMPLETE with Template ID mechanism
- [x] **Routing Policies**: ✅ COMPLETE (Appendix D with vendor-specific examples)
- [ ] **Configuration (Topology)**: To be defined
- [ ] **Workflow**: Commands and state transitions to be defined

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

### Q1: Cluster-scoped variables
The "production" cluster has 365 days retention, the "archive" cluster has 2555 days.

Where do you define this?
- **A**: In the `fleet.yaml` (with the cluster definition)
- **B**: In the configuration/topology (when applying)
- **C**: Both (default variables in fleet, override in config)

### Q2: SH connected to individual DNs
A Search Head is connected to Data Nodes that are NOT in a cluster (e.g., DN site A, DN site B isolated).

How do we model this?
- **A**: `connectedDataNodes: [dn-site-a, dn-site-b]` (explicit list)
- **B**: No need to model in CaC-ConfigMgr, handled on LogPoint side
- **C**: Force creation of a logical cluster even for single DN

### Q3: AIO clustering?
Can a client have 2 identical AIOs in HA?
- **A**: Yes (so we need `AIOCluster`)
- **B**: No (AIO = always unique, no native HA)

### Q4: Prod/Staging/Tests
A client has multiple environments. This is:
- **A**: A single `fleet.yaml` with everything inside (prod + staging)
- **B**: One `fleet.yaml` per environment (`fleet-prod.yaml`, `fleet-staging.yaml`)
- **C**: Single file with `environments: [prod, staging]` sections

---

## Next Milestones

1. **Validate Fleet spec** (answer Q1-Q4)
2. **Define Configuration (Topology)** spec
3. **Define CLI Workflow** (commands: validate, plan, apply, drift)
4. **Create Pydantic models** from validated specs
5. **Implement Provider interface** for Director API
