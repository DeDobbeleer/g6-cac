# g6-cac - Logpoint Configuration as Code

## Project Overview

**g6-cac** is a Configuration as Code (CaC) tool designed for centralized management of Logpoint Director configurations across multiple pools and SIEM instances.

**Project Status:** Phase 1 Complete (Foundation) - Phase 2 (Director Integration) ready to start

**Language:** English (all documentation, specifications, and code are in English)

### Purpose

This tool enables:
- Standardizing SIEM configurations across environments (dev/staging/prod)
- Reducing manual configuration errors
- Facilitating deployment of new pools/clients
- Enabling code review for SIEM changes
- Providing complete audit trail of modifications
- Enabling fast recovery in case of incidents

### Key Use Cases

1. **MSSP Client Onboarding:** Deploy standard configuration on a new pool
2. **Mass Update:** Modify an alert rule across all pools
3. **Drift Detection:** Detect discrepancies between declared and actual configuration
4. **Backup/Restore:** Backup and restore configurations

## Technology Stack

### Primary Language
**Python** (decision confirmed in ADR-001)

### Key Libraries (Implemented)
| Library | Purpose | Status |
|---------|---------|--------|
| Typer | CLI framework | ✅ Implemented |
| Rich | Terminal formatting and UI | ✅ Implemented |
| Pydantic v2 | YAML schema validation | ✅ Implemented |
| httpx | HTTP client for API calls | 🚧 Phase 2 |
| textual | TUI (Text User Interface) | ⏳ Future |

### Configuration Format
**YAML with Pydantic schemas** - Kubernetes-inspired format:
```yaml
apiVersion: logpoint-cac/v1
kind: DataNodeConfig
metadata:
  name: "dn-prod-01"
spec:
  # Resource definitions
```

## Project Structure

```
g6-cac/
├── specs/                    # Specifications (source of truth)
│   ├── 00-VISION.md
│   ├── 01-ARCHITECTURE-LOGPOINT.md
│   ├── 10-INVENTORY-FLEET.md
│   ├── 20-TEMPLATE-HIERARCHY.md
│   ├── 30-PROCESSING-POLICIES.md
│   ├── 40-CLI-WORKFLOW.md
│   ├── 50-VALIDATION-SPEC.md
│   ├── 99-ROADMAP.md
│   └── *.pdf
├── docs/
│   └── CODING-STANDARDS.md
├── src/
│   └── cac_configmgr/        # Implementation
│       ├── models/           # Pydantic models
│       ├── core/             # Resolution & validation
│       ├── cli/              # CLI commands
│       └── providers/        # API connectors (Phase 2)
├── tests/                    # Unit tests (40 passing)
├── examples/                 # Example configurations
├── ADRS.md                   # Architecture Decision Records
├── PROJECT-STATUS.md         # Current status & next steps
├── AUDIT-PLAN.md            # Documentation audit
└── AGENTS.md                # This file
```

## Architecture Overview

### Four-Layer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                        │
│  CLI (Typer) │ TUI (Textual) │ CI/CD (Docker) │ GitOps     │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                   ORCHESTRATION LAYER                        │
│  Plan Engine │ Apply Engine │ Drift Detector │ DAG Resolver │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                   ABSTRACTION LAYER                          │
│  Cluster Detector │ Node Router │ Resource Abstraction      │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                   CONNECTORS LAYER                           │
│  Director Connector │ Direct SIEM Connector │ Async Manager  │
└─────────────────────────────────────────────────────────────┘
```

### Supported Operation Modes

1. **Director Mode:** Management via Director API (MSSP, multi-tenant)
2. **Direct Mode:** Management via local SIEM API (all-in-one or distributed)

### Resource Types (Priority)

| Priority | Resource | Description |
|----------|----------|-------------|
| P0 | AlertRules | Core business, frequent changes |
| P0 | DeviceGroups | Fundamental structure |
| P0 | Repos | Log storage |
| P1 | Policies | Processing rules |
| P1 | SystemSettingsSNMP | Monitoring |
| P2 | Dashboards | Operational visibility |
| P2 | Reports | Client reporting |
| P3 | Users/Permissions | Governance |

## Operations

The tool will support these commands:

| Command | Description |
|---------|-------------|
| `plan` | Preview changes before application |
| `apply` | Apply changes |
| `sync` | Synchronize from actual state |
| `validate` | Validate YAML syntax |
| `diff` | Compare two environments |
| `backup` | Export current configuration |
| `drift` | Detect configuration drift |

## Development Phases

### Phase 1: Foundation ✅ COMPLETE
- ✅ Pydantic models for all resources
- ✅ Template resolution (6-level inheritance)
- ✅ 4-level validation system
- ✅ Validate command with CLI
- ✅ 40 unit tests passing

### Phase 2: Director Integration (Current)
- 🚧 Director Provider with httpx
- 🚧 Plan command (diff calculation)
- 🚧 Apply command (deployment)
- 🚧 Name-to-ID resolution

### Phase 3: Devices + Collectors
- Devices CRUD
- Syslog Collector
- Log Collection Policies
- Full validation

### Phase 4: Extensions
- Users + UserGroups
- AlertRules
- Direct Mode (without Director)
- Drift detection

### Phase 5: DevOps/GitOps
- Docker image
- GitHub Actions
- Kubernetes Operator
- Full observability

## API Integration

### Director API Base URL
```
https://{api-server-host-name}/configapi/{pool_UUID}/{logpoint_identifier}
```

### Authentication
```
Authorization: Bearer {token}
```

### Async Operations Pattern
All POST/PUT/DELETE operations return a `request_id`:
```json
{
    "status": "Success",
    "message": "/monitorapi/{pool_UUID}/{logpoint_identifier}/orders/{request_id}"
}
```

The client must poll the monitor endpoint for operation status.

### Key Constraints
- No bulk operations (sequential requests required)
- Rate limiting unknown (implement backoff/retry)
- Operations are async (polling required)
- No atomic transactions
- Mode Normal vs Co-Managed (some APIs restricted in Co-Managed mode)

## Configuration Structure

```
configs/
├── _common/                    # Shared configurations
│   ├── alert-rules/
│   ├── device-groups/
│   └── policies/
├── _templates/                 # Templates for new pools
├── production/
│   ├── pool-a/
│   │   ├── pool.yaml
│   │   ├── logpoints/
│   │   └── kustomization.yaml
│   └── pool-b/
└── staging/
    └── ...
```

## Dependency Management

Resources have dependencies that form a DAG (Directed Acyclic Graph):

```
Repos → Routing Policies → Processing Policies → Devices → Syslog Collector
          ↗
Normalization Policies (external packages)
          ↗
Enrichment Policies (external sources)
          ↗
Device Groups → Devices
```

## Security

### Secret Management
- No plaintext secrets in YAML files
- Vault integration (HashiCorp, AWS SM)
- Secret references: `${vault:secret/data/webhooks#production-url}`

### Authentication Hierarchy
1. Environment variables (`LOGPOINT_API_TOKEN`)
2. Config file (`~/.config/logpoint-cac/config.yaml`)
3. Vault (optional, if configured)

## GitOps Workflow

```
Commit on PR → CI (lint) → Validate (plan) → Human Review → Merge PR → CD (apply) → Drift detect
```

## Testing Strategy

| Level | Method | Dependencies |
|-------|--------|--------------|
| Unit | Mocked APIs | None |
| Integration | Real API calls | Test Director instance |
| Staging | Real deployment | Reduced production replica |
| Production | Dry-run | No modifications |

## Retry and Error Handling

```yaml
retry:
  max_attempts: 3
  backoff_base: 1    # seconds
  backoff_max: 30    # seconds

circuit_breaker:
  failure_threshold: 5
  recovery_timeout: 60  # seconds
```

## Observability

### Metrics (Planned)
- `cac_apply_duration` - Total apply time
- `cac_resources_changed` - Number of modified resources
- `cac_api_requests_total` - API requests by endpoint/status
- `cac_api_latency` - API call latency
- `cac_drift_detected` - Number of detected drifts

### Structured Logging
```json
{
  "timestamp": "2026-02-20T14:30:00Z",
  "level": "info",
  "component": "cac-engine",
  "operation": "apply",
  "pool": "production-pool-a",
  "resource": "AlertRules",
  "action": "create",
  "status": "success"
}
```

## Actors and User Stories

| Actor | Description | Key Needs |
|-------|-------------|-----------|
| SOC Analyst | SIEM Operator | Modify alerts, view state |
| MSSP Engineer | Multi-client engineer | Deploy standardized configs |
| Security Architect | Security architect | Governance, compliance |
| DevOps Engineer | CI/CD, infrastructure | Automation, integration |
| CISO | Security leadership | Reporting, audit |

## Important Files for AI Agents

| File | Purpose |
|------|---------|
| `SPECS.md` | Complete project specifications |
| `ARCHITECTURE.md` | Detailed technical architecture |
| `API_ENDPOINTS.md` | API reference (100+ endpoints) |
| `ADRS.md` | Architecture decisions and rationale |
| `USER_STORIES.md` | Feature requirements by actor |
| `CONTRAINTES.md` | Technical constraints and limitations |
| `schemas.xml` | Architecture diagrams (draw.io format) |

## Build and Development Commands

**Note:** Since this is a design-phase project, no build commands exist yet.

When implementation starts, expected commands will be:
```bash
# Setup (planned)
uv pip install -e ".[dev]"

# Testing (planned)
pytest tests/unit
pytest tests/integration

# CLI usage (planned)
cac plan --environment=production
cac apply --environment=production --auto-approve
cac drift detect --pool=pool-a
```

## Contributing Guidelines

1. All documentation is in French
2. Follow ADR process for architectural changes
3. Update relevant .md files when specifications change
4. Maintain diagrams in draw.io format (schemas.xml)

## Version Compatibility

| Component | Supported Version |
|-----------|------------------|
| Logpoint Director | 1.3.0+ |
| Logpoint | 6.6.0+ |

## License

TBD - Not specified in current documentation
