Voici le fichier Markdown structuré prêt à importer dans Google Slides (via Import) ou à utiliser comme script de présentation :

```markdown
---
theme: white
backgroundColor: #ffffff
color: #333333
---

# CaC-ConfigMgr
## Configuration as Code for LogPoint SIEM

**Fleet & Hierarchical Templates Demonstration**

*From 50+ manual SIEMs to 1 codebase*

---

# The Problem: Before vs After

| Before (Manual) | After (CaC-ConfigMgr) |
|----------------|---------------------|
| 50+ SIEMs managed manually | 1 codebase = 50+ deployments |
| Frequent human errors | Automatic validation before deployment |
| No change traceability | Git = complete audit history |
| Client onboarding = 2 weeks | Onboarding = 1 YAML file (5 minutes) |
| Mass updates = nightmare | 1 template change → all clients updated |

**Critical Impact:** Zero configuration drift, guaranteed compliance

---

# Three-Tier Architecture

```
┌─────────────────────────────────────┐
│     LOGPOINT (Vendor)               │
│     • Golden Templates              │
│     • Security standards            │
│     • PCI-DSS, ISO27001             │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│     ACME-CORP (MSSP)                │
│     • MSSP Base                     │
│     • Banking Addon (MiFID)         │
│     • Healthcare Addon (HIPAA)      │
│     • Profiles: simple/enterprise   │
└──────────────┬──────────────────────┘
               │
    ┌──────────┴──────────┐
    │                     │
┌───▼────┐          ┌────▼────┐
│ Bank A │          │ Bank B  │
│(Premium)│         │(Standard)│
└────────┘          └─────────┘
```

---

# Fleet Concept: Node Roles

**Role determines WHAT can be configured**
**Tags determine WHERE configs are deployed**

### 🔵 AIO (All-In-One)
- **Role:** Storage + Ingestion + Query (Combined)
- **Use Case:** Small deployments, POC, Edge sites
- **Fleet Tag:** `role: aio`

### 🟢 Data Node
- **Role:** Storage + Ingestion
- **Configs:** Repos, Routing Policies, Normalization, Enrichment
- **Fleet Tag:** `role: datanode`

### 🟡 Search Head
- **Role:** Query + Alerting
- **Configs:** Alert Rules, Dashboards, Reports
- **Fleet Tag:** `role: searchhead`

> **Critical Rule:** Node role determines *which* configurations can be deployed. Fleet tags (cluster) determine *where* they are deployed.

---

# Deployment Architectures

## Simple (AIO)
Single All-In-One Node or basic distributed mode
- `aio-main` (role: aio, env: prod)
- OR `datanode-main` + `searchhead-main`

## Medium (Distributed)
2 Backend Clusters + 1 Search Head
- Backend Cluster 1: `cluster: Prod-DN`
- Backend Cluster 2: `cluster: HR-DN`
- Search Head: `sh-for: Prod-DN, HR-DN`

## Complex (Enterprise)
Production + DR + Search Head Cluster
- Backend: Production cluster + DR cluster
- Frontend: SH Cluster (load balancing)
- Tags: `cluster: frontend`, `sh-for: prod + dr`

---

# Template Hierarchy System

## 6 Levels of Inheritance

| Level | Template | Type | What It Brings |
|-------|----------|------|----------------|
| **L1** | `golden-base` | Root | 6 standard repos, basic routing, 90d retention |
| **L2** | `golden-pci-dss` | Addon | +1 PCI repo, 7y retention (2555d), audit rules |
| **L3** | `acme-base` | MSSP | Custom mount points, archive tiering, 180d retention |
| **L4** | `acme-banking-addon` | Addon | +1 trading repo, MiFID compliance, 10y retention |
| **L5** | `acme-banking-premium` | Profile | MiFID enrichment, 4-tier storage, trading normalization |
| **L6** | `bank-a-prod` | Instance | `client_code: BANKA`, `region: EU-WEST`, specific overrides |

### Inheritance Types
- **Vertical (Cross-level):** Parent L1 → Child L2
- **Horizontal (Intra-level):** Base → PCI-DSS Addon (same level)

---

# Deep Merge Mechanisms

## Parent Template
```yaml
# golden-base/repos.yaml
repos:
  - name: repo-secu
    hiddenrepopath:
      - _id: fast-tier
        path: /opt/immune/storage
        retention: 365
      - _id: warm-tier
        path: /opt/immune/storage-warm
        retention: 90
```

## Child Template
```yaml
# acme-enterprise/repos.yaml
repos:
  - name: repo-secu
    hiddenrepopath:
      - _id: fast-tier
        retention: 7        # <-- Override
      - _id: warm-tier
        retention: 30       # <-- Override
      - _id: nfs-tier       # <-- Append (new)
        path: /opt/immune/storage-nfs
        retention: 1095
```

## Final Resolution (API Payload)
```json
{
  "repos": [{
    "name": "repo-secu",
    "hiddenrepopath": [
      {"path": "/opt/immune/storage", "retention": 7},
      {"path": "/opt/immune/storage-warm", "retention": 30},
      {"path": "/opt/immune/storage-nfs", "retention": 1095}
    ]
  }]
}
```

> Note: `_id` fields are internal and filtered before API call

---

# Advanced Merge Features

## Ordering Directives
Control element position in lists:
- `_after: _id` — Insert after element
- `_before: _id` — Insert before element  
- `_position: N` — Absolute position (1-based)
- `_first: true` — Force first position
- `_last: true` — Force last position

## Deletion
```yaml
routing_criteria:
  - _id: crit-obsolete
    _action: delete  # Removes inherited element
```

---

# Operating Mode Workflow

```
┌─────────────┐    ┌──────────────────┐    ┌─────────────────┐    ┌────────┐
│ YAML Configs│ -> │ Template         │ -> │ Comparison      │ -> │ Apply  │
│ (Git)       │    │ Resolution       │    │ (plan/diff)     │    │        │
│             │    │ (6-level merge)  │    │                 │    │        │
└─────────────┘    └──────────────────┘    └─────────────────┘    └────────┘
```

## CLI Commands

```bash
# 1. Validate syntax and references
cac-configmgr validate demo-configs/

# 2. Preview changes (dry-run)
cac-configmgr plan \
  --fleet instances/bank-a/prod/fleet.yaml \
  --topology instances/bank-a/prod/instance.yaml

# 3. Deploy (Phase 2)
cac-configmgr apply --fleet ... --topology ... --auto-approve
```

---

# Client Comparison: Same MSSP, Different Profiles

| Feature | Bank A (Premium) | Bank B (Standard) | Corp X (Enterprise) |
|---------|-----------------|-------------------|-------------------|
| **Profile** | banking-premium | banking | enterprise |
| **Inheritance Chain** | 6 levels | 4 levels | 5 levels |
| **Repos** | 10 (incl. trading, pci-audit) | 8 (no trading) | 7 (standard) |
| **Retention Max** | 10 years | 7 years (PCI) | 7 years |
| **Enrichment** | MiFID compliance | None | GeoIP + Threat Intel |
| **Storage Tiers** | 4-tier (fast/warm/cold/nfs) | 3-tier | 3-tier |
| **Variables** | `client_code: BANKA` | `client_code: BANKB` | `client_code: CORPX` |

---

# Key Benefits

## 1. DRY Principle (Don't Repeat Yourself)
❌ **Before:** 50 clients × 100 config lines = **5,000 lines** to maintain  
✅ **After:** 6 templates + 50 instance files = **~800 lines**

## 2. Simplified Mass Updates
Modify `retention_default` in `acme-base` → **ALL ACME clients** automatically updated

## 3. Fast Onboarding
New client = 1 YAML file  
**Time:** 5 minutes vs 2 weeks before

## 4. Guaranteed Compliance
- PCI-DSS Addon → All banking clients inherit
- ISO27001 Addon → All sensitive clients inherit

## 5. Audit and Traceability
Git log = complete change history  
Who changed what when = immediately available

---

# Roadmap & Current Status

## Phase 1: Foundation ✅ COMPLETE
- Template resolution engine
- 4-level validation (Syntax → Resolution → API Compliance → Dependencies)
- Fleet inventory system
- 40+ tests passing

## Phase 2: Director Integration 🔄 IN PROGRESS
- Plan/Apply commands
- Director API provider
- Name-to-ID resolution
- Async operation handling

## Target Vision
> "One codebase to manage 1 or 100 SIEMs with the same effort"

---

# Demo Checklist

| Step | Command/Action | Objective |
|------|---------------|-----------|
| 1 | `tree demo-configs/ -L 4` | Show complete structure |
| 2 | `cac-configmgr validate demo-configs/` | Validate all configs |
| 3 | Plan Bank A | Show resolution + 6-level chain |
| 4 | Compare Bank A vs Bank B | Show profile flexibility |
| 5 | Show `fleet.yaml` | Explain node management |
| 6 | Highlight variables | `client_code`, `region`, retentions |

---

# Questions?

**Technical Documentation:**
- `specs/20-TEMPLATE-HIERARCHY.md`
- `specs/10-INVENTORY-FLEET.md`
- `specs/40-CLI-WORKFLOW.md`

**Architecture Diagrams:**
- Fleet Architecture (Node Roles & Topologies)
- Template Hierarchy (4 levels overview)
- Merge Mechanisms (Deep merge with `_id`)

*CaC-ConfigMgr — Configuration as Code for LogPoint*
```

**Utilisation :**
1. **Google Slides** : File → Import slides → Upload → Sélectionne ce fichier .md
2. **PowerPoint** : Copie-colle dans l'outil "Markdown to PowerPoint" ou utilise Pandoc : `pandoc demo-script.md -o presentation.pptx`
3. **Kimi Slides** : Copie le contenu dans l'éditeur

Le fichier est optimisé pour une présentation technique de 15-20 minutes avec des transitions logiques entre la problématique, l'architecture et la démo.