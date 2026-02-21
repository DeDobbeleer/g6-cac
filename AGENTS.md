# g6-cac - Logpoint Configuration as Code

## Project Overview

**g6-cac** is a Configuration as Code (CaC) tool designed for centralized management of Logpoint Director configurations across multiple pools and SIEM instances.

**Project Status:** Design and specification phase - implementation has not started yet.

**Language:** French (all documentation is in French)

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

### Key Libraries (Planned)
| Library | Purpose |
|---------|---------|
| Typer | CLI framework |
| Rich | Terminal formatting and UI |
| Pydantic | YAML schema validation |
| httpx | HTTP client for API calls |
| textual | TUI (Text User Interface) - future |

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
├── SPECS.md              # Project specifications and requirements
├── ARCHITECTURE.md       # Technical architecture documentation
├── API_ENDPOINTS.md      # Complete Director API endpoint reference
├── ADRS.md              # Architecture Decision Records
├── USER_STORIES.md      # User stories by actor
├── CONTRAINTES.md       # Technical constraints
├── schemas.xml          # Draw.io architecture diagrams (XML format)
├── diagrams/
│   └── architecture.drawio
└── AGENTS.md            # This file
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

### Phase 1: MVP (Repos + Device Groups)
- Basic Director connector
- CRUD for Repos and Device Groups
- plan/apply commands
- Unit tests

### Phase 2: Policies Pipeline
- Routing Policies
- Normalization Policies + Packages
- Enrichment Policies + Sources
- Processing Policies
- DAG management

### Phase 3: Devices + Collectors
- CRUD for Devices
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
