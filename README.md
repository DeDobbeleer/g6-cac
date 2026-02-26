# CaC-ConfigMgr

**Configuration as Code Manager for LogPoint**

Standardize, deploy and maintain LogPoint configuration at scale — without errors, without thousands of clicks, for 1 or 100 SIEMs.

## Vision

- **Time**: 2 days of clicks → 5 minutes
- **Quality**: Zero configuration errors (pre-validation)
- **Scalability**: Manage N SIEMs as one (pseudo-cluster)
- **Traceability**: Complete change history (who, what, when)

## Specifications

| Document | Purpose |
|----------|---------|
| [00-VISION](specs/00-VISION.md) | Product vision and target audiences |
| [01-ARCHITECTURE-LOGPOINT](specs/01-ARCHITECTURE-LOGPOINT.md) | LogPoint node types and config mapping |
| [10-INVENTORY-FLEET](specs/10-INVENTORY-FLEET.md) | Tag-based fleet inventory system |
| [20-TEMPLATE-HIERARCHY](specs/20-TEMPLATE-HIERARCHY.md) | 4-level hierarchical template system |
| [30-PROCESSING-POLICIES](specs/30-PROCESSING-POLICIES.md) | Processing policy specification |
| [40-CLI-WORKFLOW](specs/40-CLI-WORKFLOW.md) | CLI commands and workflow |
| [99-ROADMAP](specs/99-ROADMAP.md) | Decisions and next steps |

## Architecture Decisions

See [ADRS.md](ADRS.md) for all architecture decision records.

## Status

🚧 **Design Phase Complete** - Specifications validated, ready for implementation.

## Quick Start (Future)

```bash
# Install
pip install cac-configmgr

# Validate configurations
cac-configmgr validate ./configs/

# Preview changes
cac-configmgr plan --fleet fleet.yaml --topology topology.yaml

# Apply changes
cac-configmgr apply --fleet fleet.yaml --topology topology.yaml
```

## License

TBD
