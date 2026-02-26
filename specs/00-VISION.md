# Product Vision

## Name
**Status**: ✅ **VALIDATED** - **GuardSix CaC** (guardsix cac)

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

- [ ] **Pseudo-Cluster**: Config replication across N identical SIEMs
- [ ] **Inventory (Fleet)**: Client fleet representation
- [ ] **Configuration (Topology)**: Desired state definition
- [ ] **Workflow**: Plan → Validate → Apply → Drift

## Decisions to Make

- [x] Final product name
- [ ] Validate pseudo-cluster concept
- [ ] Validate inventory structure
- [ ] Validate configuration format
