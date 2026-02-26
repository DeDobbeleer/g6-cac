# Product Vision

## Name
**Status**: ✅ **VALIDATED** - **CaC-ConfigMgr** (cac-configmgr cac)

## Elevator Pitch
Standardize, deploy and maintain LogPoint configuration at scale — without errors, without thousands of clicks, for 1 or 100 SIEMs.

## Target Audiences

### Phase 1 (MVP)
- **Audience**: MSSP (Build & Run teams)
- **Mode**: Director API only
- **Pain point**: Slow client onboarding, manual configuration errors

### Phase 2
- **Audience**: Enterprise (large organizations)
- **Mode**: Direct SIEM API (when available)
- **Pain point**: Heterogeneous fleet management

### Phase 3
- **Audience**: All LogPoint customers
- **Mode**: Hybrid Director + Direct

## Promised Values

1. **Time**: 2 days of clicks → 5 minutes
2. **Quality**: Zero configuration errors (pre-validation)
3. **Scalability**: Manage N SIEMs as one (pseudo-cluster)
4. **Traceability**: Complete change history (who, what, when)

## Key Concepts Identified

- [x] **Pseudo-Cluster**: Config replication across N identical SIEMs
- [x] **Inventory (Fleet)**: Client fleet representation (tag-based)
- [x] **Configuration (Topology)**: Desired state definition (hierarchical templates with _id)
- [x] **Workflow**: ✅ Plan → Validate → Apply → Drift (defined in 40-CLI-WORKFLOW.md)

## Decisions to Make

- [x] Final product name: CaC-ConfigMgr
- [x] Validate pseudo-cluster concept: ✅ AIOs can be clustered via tags
- [x] Validate inventory structure: ✅ Tag-based approach with _id
- [x] Validate configuration format: ✅ Hierarchical templates
- [ ] Validate workflow CLI commands
