# CLI Workflow Specification

**Version**: 1.0  
**Status**: 🚧 Draft  
**Date**: 2026-02-26  
**Author**: CaC-ConfigMgr Product Team  

---

## 1. Executive Summary

CLI commands and workflow specification for CaC-ConfigMgr:

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Validate  │───→│    Plan     │───→│    Apply    │───→│    Drift    │
│  (syntax)   │    │   (diff)    │    │  (deploy)   │    │  (monitor)  │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │                  │                  │                  │
       └──────────────────┴──────────────────┴──────────────────┘
                          Iterative workflow
```

---

## 2. Command Overview

### 2.1 Command Structure

```bash
cac-configmgr <command> [subcommand] [flags] [args]
```

### 2.2 Command Summary

| Command | Description | Idempotent | Safe |
|---------|-------------|------------|------|
| `validate` | Validates syntax and consistency | ✅ Yes | ✅ Read-only |
| `plan` | Calculates and displays diff | ✅ Yes | ✅ Read-only |
| `apply` | Applies changes | ✅ Yes | ⚠️ Modifies SIEM |
| `drift` | Detects divergences | ✅ Yes | ✅ Read-only |
| `backup` | Exports current configuration | ✅ Yes | ✅ Read-only |
| `version` | Displays version | ✅ Yes | ✅ Read-only |

---

## 3. Validate Command

### 3.1 Usage

```bash
# Validate a fleet file
cac-configmgr validate fleet.yaml

# Validate a template
cac-configmgr validate --template templates/mssp/acme-corp/base/

# Validate a complete instance (fleet + topology)
cac-configmgr validate --fleet instances/client-bank/prod/fleet.yaml \
                       --topology instances/client-bank/prod/instance.yaml

# Validate without API connection (offline)
cac-configmgr validate --offline fleet.yaml
```

### 3.2 Validation Levels

| Level | Description | Output |
|-------|-------------|--------|
| **Syntax** | Valid YAML, schema respected | Errors/Warnings |
| **References** | All refs resolvable | Errors (unresolved refs) |
| **API Check** | External resources exist | Errors (missing packages/sources) |
| **Dry-run** | Test against real API | Success/Errors |

### 3.3 Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Validation successful, no warnings |
| 1 | Validation successful, warnings present |
| 2 | Validation errors |
| 3 | System/connection error |

### 3.4 Output Format

```bash
# Text format (default)
cac-configmgr validate fleet.yaml
✓ fleet.yaml: Valid
✓ 12 nodes defined
✓ 3 clusters resolved
✓ All references valid
⚠ Warning: DN 'dn-legacy-site' has no cluster tag

# JSON format
cac-configmgr validate --output json fleet.yaml
```

```json
{
  "valid": true,
  "warnings": [
    {
      "file": "fleet.yaml",
      "line": 45,
      "message": "DN 'dn-legacy-site' has no cluster tag",
      "severity": "warning"
    }
  ],
  "errors": [],
  "summary": {
    "nodes": 12,
    "clusters": 3,
    "references_resolved": 8
  }
}
```

---

## 4. Plan Command

### 4.1 Usage

```bash
# Plan on a complete instance
cac-configmgr plan --fleet instances/client-bank/prod/fleet.yaml \
                   --topology instances/client-bank/prod/instance.yaml

# Plan with full details
cac-configmgr plan --detailed ...

# Plan JSON format (for CI/CD)
cac-configmgr plan --output json ...

# Compare two topologies
cac-configmgr plan --base topology-staging.yaml \
                   --target topology-prod.yaml
```

### 4.2 Output: Resource Changes

```
$ cac-configmgr plan --fleet fleet.yaml --topology instance.yaml

Planning changes for client: client-bank-prod

Repos (3 changes):
  + CREATE repo-trading (new in instance)
  ~ UPDATE repo-secu (retention: 90 → 7)
  - DELETE repo-temp (not in target)

Routing Policies (2 changes):
  ~ UPDATE rp-windows (3 criteria modified)
    + ADD crit-powershell
    ~ MODIFY crit-verbose (repo changed)
  + CREATE rp-paloalto

Processing Policies (1 change):
  + CREATE pp-lateral-movement

Summary:
  Create: 3  Update: 2  Delete: 1  Unchanged: 12
```

### 4.3 Change Types

| Symbol | Type | Description |
|--------|------|-------------|
| `+` | CREATE | New resource |
| `~` | UPDATE | Existing resource modified |
| `-` | DELETE | Resource deletion |
| `=` | UNCHANGED | No change |
| `?` | UNKNOWN | Cannot determine (API error) |

### 4.4 Detailed Diff

```bash
$ cac-configmgr plan --detailed ...

~ UPDATE repo-secu
    hiddenrepopath[0] (fast-tier):
      retention: 90 → 7
      path: /opt/immune/storage (unchanged)
    
    hiddenrepopath[2] (nfs-tier):
      + ADD new tier
        path: /opt/immune/storage-nfs
        retention: 3650
```

---

## 5. Apply Command

### 5.1 Usage

```bash
# Interactive apply (asks for confirmation)
cac-configmgr apply --fleet fleet.yaml --topology instance.yaml

# Auto-approved apply (CI/CD)
cac-configmgr apply --auto-approve fleet.yaml topology.yaml

# Apply with batch size (limit API calls)
cac-configmgr apply --batch-size 10 ...

# Apply only certain resources
cac-configmgr apply --only repos,routing-policies ...

# Dry-run apply (test without modifying)
cac-configmgr apply --dry-run ...
```

### 5.2 Interactive Mode

```
$ cac-configmgr apply ...

Planning complete. 6 resources will be changed:
  Create: 3  Update: 2  Delete: 1

Do you want to apply these changes? [y/N/d(details)/q(quit)]: y

Applying changes...
[1/6] Creating repo-trading......................... ✓ Done (2.3s)
[2/6] Updating repo-secu............................ ✓ Done (1.1s)
[3/6] Deleting repo-temp............................ ✓ Done (0.8s)
[4/6] Creating rp-paloalto.......................... ⏳ Pending (async)
        Request ID: req-abc-123
        Polling status... Done (5.2s)
[5/6] Updating rp-windows........................... ✓ Done (1.5s)
[6/6] Creating pp-lateral-movement.................. ✓ Done (2.0s)

Apply complete! Resources: 6 changed, 12 unchanged
Duration: 13.1s

Run 'cac-configmgr drift' to verify configuration matches target.
```

### 5.3 Rollback

```bash
# Create backup before apply
cac-configmgr backup --output backup-$(date +%Y%m%d).yaml ...

# In case of partial error
$ cac-configmgr apply ...
[1/6] Creating repo-trading......................... ✓ Done
[2/6] Updating repo-secu............................ ✗ FAILED
        Error: API returned 400 - Invalid retention value
        
Applied: 1, Failed: 1, Remaining: 4

Options:
  [c]ontinue - Continue with remaining changes
  [r]ollback - Undo successful changes (repo-trading)
  [a]bort    - Stop, partial state remains

# Manual rollback
$ cac-configmgr apply --rollback backup-20260226.yaml
```

### 5.4 Progress Tracking

| State | Indicator | Description |
|-------|-----------|-------------|
| Pending | ⏳ | Waiting to execute |
| In Progress | 🔄 | API request sent |
| Async Wait | ⏱️ | Async operation, polling |
| Success | ✓ | Completed successfully |
| Failed | ✗ | Error, not applied |
| Skipped | ⊘ | Skipped (dependency failed) |

### 5.5 Exit Codes Apply

| Code | Meaning |
|------|---------|
| 0 | All changes applied |
| 1 | Partially applied (some failed) |
| 2 | Error before application (validation failed) |
| 3 | System error |

---

## 6. Drift Command

### 6.1 Usage

```bash
# Detect drift on an instance
cac-configmgr drift detect --fleet fleet.yaml --topology instance.yaml

# Drift on entire pool
cac-configmgr drift detect --pool acme-corp

# Drift with JSON format
cac-configmgr drift detect --output json ...

# Continuous drift (watch mode)
cac-configmgr drift watch --interval 5m ...

# Repair drift (restore to target)
cac-configmgr drift reconcile --fleet fleet.yaml --topology instance.yaml
```

### 6.2 Drift Types

| Type | Description | Example |
|------|-------------|---------|
| **Definition Drift** | YAML config different from expected | Retention changed manually in UI |
| **External Change** | External modification not reflected | Admin adds repo via Director |
| **Orphan Resource** | Resource exists in prod but not in YAML | Old test repo forgotten |
| **Missing Resource** | Resource in YAML but not in prod | Apply partially failed |

### 6.3 Drift Detection Output

```
$ cac-configmgr drift detect ...

Drift detected for client: client-bank-prod

DEFINITION DRIFT (2):
  ! repo-secu
    Actual:   retention=180
    Expected: retention=7 (from instance.yaml)
    Source:   Manual UI change by admin@acme.com (2026-02-25 14:32)

  ! rp-windows.crit-verbose
    Actual:   repo=repo-system
    Expected: repo=repo-system-verbose

EXTERNAL CHANGES (1):
  + repo-manual-test (not in YAML)
    Created: 2026-02-24 09:15 by john.doe@acme.com
    Action: Review and add to YAML or delete

ORPHAN RESOURCES (1):
  ? repo-old-legacy
    Last log: 2024-12-01 (2+ months ago)
    Recommendation: Safe to delete

Summary: 4 drifts detected (2 critical, 2 warnings)
```

### 6.4 Drift Configuration

```yaml
# .cac-configmgr.yaml (project config)
drift:
  ignore:
    - type: repo
      name: temp-*           # Ignore temp repos
    - type: routing-policy
      name: test-*
  
  threshold:
    critical: 5              # Alert if >5 critical drifts
    warning: 10              # Warn if >10 drifts
  
  auto-reconcile: false      # Never auto (safety)
  # auto-reconcile: warning  # Only warnings
  # auto-reconcile: all      # All (dangerous)
```

---

## 7. Backup Command

### 7.1 Usage

```bash
# Full backup of an instance
cac-configmgr backup --fleet fleet.yaml --output backup.yaml

# Specific backup
cac-configmgr backup --only repos,routing-policies ...

# Backup with auto timestamp
cac-configmgr backup --fleet fleet.yaml --output-dir ./backups/
# Creates: backups/backup-2026-02-26T143052.yaml

# Backup JSON format (machine-readable)
cac-configmgr backup --output json ...
```

### 7.2 Backup Output Format

```yaml
# backup-20260226.yaml
apiVersion: cac-configmgr.io/v1
kind: Backup
metadata:
  timestamp: "2026-02-26T14:30:52Z"
  source: "client-bank-prod"
  toolVersion: "1.0.0"
  
spec:
  repos:
    - name: repo-secu
      hiddenrepopath: [...]
      
  routingPolicies:
    - policy_name: rp-windows
      routing_criteria: [...]
      
  # ... other resources
```

---

## 8. Global Flags

### 8.1 Universal Flags

| Flag | Description | Default |
|------|-------------|---------|
| `--config` | CLI config file | `~/.config/cac-configmgr/config.yaml` |
| `--log-level` | Log level (debug, info, warn, error) | `info` |
| `--output` | Output format (text, json, yaml) | `text` |
| `--no-color` | Disable colors | `false` |
| `--timeout` | API timeout (seconds) | `300` |
| `--retry` | Number of retries | `3` |

### 8.2 Configuration File

```yaml
# ~/.config/cac-configmgr/config.yaml
defaults:
  log_level: info
  output: text
  timeout: 300
  
director:
  api_host: https://director.logpoint.com
  credentials_source: env  # env, file, keyring
  
features:
  auto_approve: false
  drift_watch_interval: 5m
  
aliases:
  prod: instances/client-bank/prod/
  staging: instances/client-bank/staging/
```

---

## 9. Workflow Examples

### 9.1 Development Workflow

```bash
# 1. Edit templates
vim templates/mssp/acme-corp/base/repos.yaml

# 2. Validate locally
cac-configmgr validate --template templates/mssp/acme-corp/base/

# 3. Plan on staging
cac-configmgr plan --fleet instances/client-bank/staging/fleet.yaml \
                   --topology instances/client-bank/staging/instance.yaml

# 4. Apply on staging
cac-configmgr apply --fleet instances/client-bank/staging/fleet.yaml \
                    --topology instances/client-bank/staging/instance.yaml

# 5. Verify drift
cac-configmgr drift detect --fleet ... --topology ...

# 6. Same process on prod
cac-configmgr plan --fleet instances/client-bank/prod/...
cac-configmgr apply --auto-approve ...  # If CI/CD validated
```

### 9.2 CI/CD Workflow

```yaml
# .github/workflows/deploy.yml
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Validate configurations
        run: cac-configmgr validate --recursive ./instances/
      
  plan:
    needs: validate
    steps:
      - name: Generate plan
        run: cac-configmgr plan --output json ... > plan.json
      - name: Upload plan
        uses: actions/upload-artifact@v4
        with:
          name: deployment-plan
          path: plan.json
          
  apply:
    needs: plan
    environment: production  # Require manual approval
    steps:
      - name: Apply changes
        run: cac-configmgr apply --auto-approve ...
      - name: Verify no drift
        run: cac-configmgr drift detect ...
```

### 9.3 Emergency Response

```bash
# Incident: Need to change retention immediately

# 1. Edit instance
vim instances/client-bank/prod/instance.yaml
# Change: retention: 7 → retention: 1

# 2. Validate quickly
cac-configmgr validate --offline instance.yaml

# 3. Apply with explicit confirmation
cac-configmgr apply --only repos ...
# Confirm: y

# 4. Verify
cac-configmgr drift detect ...
```

---

## 10. Error Handling & Messages

### 10.1 Error Categories

| Category | Example | User Action |
|----------|---------|-------------|
| **Validation** | "Invalid YAML syntax" | Fix file |
| **Reference** | "Repo 'repo-x' not found" | Add definition |
| **API** | "Director API returned 503" | Retry later |
| **Permission** | "Insufficient permissions" | Check token |
| **Conflict** | "Resource modified by another" | Refresh and retry |

### 10.2 Error Format

```
ERROR: Failed to apply routing policy 'rp-windows'

Details:
  File: templates/mssp/acme-corp/base/routing-policies.yaml:45
  API Error: 400 Bad Request
  Message: "Invalid criterion: key 'EventTypeX' not recognized"
  
Suggestion:
  Valid keys for Windows events: EventType, EventID, Level, ProviderName
  
Documentation:
  https://docs.cac-configmgr.io/errors/INVALID_CRITERION_KEY
```

---

## 11. Open Questions

1. **State Management**: Need a state file (terraform.tfstate-like) or purely stateless?
2. **Concurrency**: How to handle simultaneous applies on same instance?
3. **Partial Apply**: How to resume a partially failed apply?
4. **Locking**: Should we lock an instance during apply?
5. **Audit**: Where to store apply history?

---

## Appendix A: Quick Reference Card

```
CAC-CONFIGMGR - QUICK REFERENCE
═══════════════════════════════════════════════════════════════

VALIDATE
  validate fleet.yaml                    Validate file
  validate --template dir/               Validate template
  validate --fleet f.yaml --topology t   Validate instance

PLAN
  plan --fleet f.yaml --topology t       Show changes
  plan --detailed                        With full details
  plan --output json                     Machine output

APPLY
  apply --fleet f.yaml --topology t      Apply (interactive)
  apply --auto-approve                   No confirmation
  apply --dry-run                        Test without modifying
  apply --only repos                     Only repos

DRIFT
  drift detect --fleet f --topology t    Detect divergences
  drift reconcile                        Repair drift
  drift watch --interval 5m              Continuous monitoring

BACKUP
  backup --fleet f.yaml                  Backup config
  backup --output-dir ./backups/         With timestamp

GLOBAL FLAGS
  --output json/yaml/text                Output format
  --log-level debug/info/warn/error      Verbosity
  --no-color                             No colors
  --config ~/.config/cac-configmgr/      Custom config

USEFUL ALIASES
  cac-configmgr plan ... | less          View all
  cac-configmgr apply --auto-approve ... CI/CD
  cac-configmgr drift watch &            Background monitoring
```
