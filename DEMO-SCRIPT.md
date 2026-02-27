# CaC-ConfigMgr Demo Script - Monday Presentation

**Date**: Monday Demo  
**Audience**: Adriana and Team  
**Duration**: ~20 minutes

---

## Demo Overview

Demonstrate the Configuration as Code system for LogPoint with:
- ✅ CLI commands (validate, plan)
- ✅ Multi-level template inheritance (horizontal + vertical)
- ✅ Multiple client types (banks, enterprises)
- ✅ Multiple clients per type

---

## Pre-Demo Setup (Run Before)

```bash
# 1. Install the tool
cd /path/to/g6-cac
pip install -e .

# 2. Generate demo configurations
cac-configmgr generate-demo --output ./demo-configs

# 3. Verify structure
ls -la demo-configs/
```

---

## Demo Structure Generated

```
demo-configs/
├── templates/
│   ├── logpoint/                    # Level 1: Golden Templates
│   │   ├── golden-base/             # Root template
│   │   ├── golden-pci-dss/          # PCI addon (horizontal)
│   │   └── golden-iso27001/         # ISO addon (horizontal)
│   │
│   └── mssp/
│       └── acme-corp/               # Level 2-3: MSSP
│           ├── base/                # MSSP base (vertical)
│           ├── addons/
│           │   ├── banking/         # Banking addon (horizontal)
│           │   └── healthcare/      # Healthcare addon (horizontal)
│           └── profiles/
│               ├── simple/
│               ├── enterprise/
│               └── banking-premium/ # Extends enterprise
│
└── instances/                       # Level 4: Concrete Clients
    ├── banks/
    │   ├── bank-a/                  # 2 environments
    │   │   ├── prod/
    │   │   └── staging/
    │   └── bank-b/                  # 1 environment
    │       └── prod/
    │
    └── enterprises/
        ├── corp-x/                  # Manufacturing
        │   └── prod/
        └── corp-y/                  # Simple profile
            └── prod/
```

---

## Demo Script (Step by Step)

### 1. Introduction (2 min)

**Speaker**: "Today we're demonstrating CaC-ConfigMgr, our Configuration as Code solution for LogPoint."

Key points:
- Goal: Manage 1 or 100 SIEMs with same effort
- Concept: Desired state configuration (like Kubernetes, Terraform)
- Benefits: Version control, code review, automated deployment

---

### 2. Show Generated Structure (3 min)

```bash
# Show the generated tree
tree demo-configs/ -L 4
```

**Speaker**: "We have 4 levels of hierarchy:"

**Level 1 - LogPoint Golden Templates:**
```
templates/logpoint/
├── golden-base/          # Standard MSSP baseline
├── golden-pci-dss/       # PCI compliance addon
└── golden-iso27001/      # ISO compliance addon
```

Explain:
- `golden-base` is the root, no parent
- `golden-pci-dss` **extends** `golden-base` (horizontal inheritance)
- Both PCI and ISO inherit from base, then diverge

**Level 2-3 - MSSP Templates:**
```
templates/mssp/acme-corp/
├── base/                 # Extends logpoint/golden-pci-dss
├── addons/
│   ├── banking/          # Extends base (horizontal)
│   └── healthcare/       # Extends base (horizontal)
└── profiles/
    ├── simple/
    ├── enterprise/       # Extends base
    └── banking-premium/  # Extends enterprise
```

Explain:
- **Vertical**: MSSP base extends LogPoint Golden
- **Horizontal**: Banking/Healthcare addons extend MSSP base
- **Vertical**: Profiles extend base or addons

**Level 4 - Client Instances:**
```
instances/
├── banks/
│   ├── bank-a/prod       # Extends banking-premium
│   ├── bank-a/staging    # Extends banking-premium
│   └── bank-b/prod       # Extends banking addon
└── enterprises/
    ├── corp-x/prod       # Extends enterprise
    └── corp-y/prod       # Extends simple
```

Explain:
- Each client is an instance with specific values
- Can override any inherited setting
- Fleet defines where to deploy

---

### 3. CLI: Validate Command (4 min)

```bash
# Validate all configurations
cac-configmgr validate demo-configs/
```

Expected output:
```
Validating demo-configs/...

Validation Results
┌──────────────────────────────────────┬───────────┬─────────┬─────────┐
│ File                                 │ Type      │ Status  │ Details │
├──────────────────────────────────────┼───────────┼─────────┼─────────┤
│ templates/logpoint/golden-base/...   │ Template  │ ✓ OK    │ -       │
│ templates/logpoint/golden-pci-dss/...│ Template  │ ✓ OK    │ -       │
│ templates/mssp/acme-corp/base/...    │ Template  │ ✓ OK    │ -       │
│ instances/banks/bank-a/prod/...      │ Instance  │ ✓ OK    │ -       │
│ ...                                  │ ...       │ ...     │ ...     │
└──────────────────────────────────────┴───────────┴─────────┴─────────┘

Summary: 15 OK, 0 warnings, 0 errors
✓ All configurations valid!
```

**Speaker**: "The validate command checks syntax, schema compliance, and references."

Show a specific file:
```bash
cat demo-configs/instances/banks/bank-a/prod/instance.yaml
```

---

### 4. CLI: Plan Command (5 min)

```bash
# Plan deployment for Bank A Production
cac-configmgr plan \
  --fleet demo-configs/instances/banks/bank-a/prod/fleet.yaml \
  --topology demo-configs/instances/banks/bank-a/prod/instance.yaml \
  --templates-dir demo-configs/templates
```

Expected output:
```
Planning changes...

Instance: bank-a-prod
Fleet: bank-a
Extends: mssp/acme-corp/profiles/banking-premium

Resolved Configuration
┌───────────────────┬───────┬──────────────────────────────┐
│ Resource Type     │ Count │ Names                        │
├───────────────────┼───────┼──────────────────────────────┤
│ repos             │ 7     │ repo-default, repo-secu...   │
│ routing_policies  │ 4     │ rp-default, rp-windows...    │
│ processing_policies│ 2    │ pp-pci-audit, pp-banking...  │
└───────────────────┴───────┴──────────────────────────────┘

Variables
┌──────────────────┬─────────────────┐
│ Name             │ Value           │
├──────────────────┼─────────────────┤
│ client_code      │ BANKA           │
│ region           │ EU-WEST         │
│ retention_default│ 180             │
│ retention_pci    │ 2555            │
│ ...              │ ...             │
└──────────────────┴─────────────────┘

Template Chain (Root → Leaf)
┌───────┬──────────────────────────────────────┬───────────┐
│ Level │ Template                             │ Type      │
├───────┼──────────────────────────────────────┼───────────┤
│ 1     │ golden-base                          │ Template  │
│ 2     │ golden-pci-dss                       │ Template  │
│ 3     │ acme-base                            │ Template  │
│ 4     │ acme-enterprise                      │ Template  │
│ 5     │ acme-banking-premium                 │ Template  │
│ 6     │ bank-a-prod                          │ Instance  │
└───────┴──────────────────────────────────────┴───────────┘

✓ Plan complete. No changes applied (dry-run).
Use 'apply' command to deploy these changes.
```

**Speaker**: "The plan command shows us:"
1. All resolved resources (after inheritance)
2. Final variable values (after merge)
3. Complete inheritance chain (6 levels!)

---

### 5. Show Inheritance Depth (3 min)

Show the complete chain for Bank A:

**Speaker**: "Let's trace the inheritance for Bank A:"

1. **golden-base** (LogPoint)
   - 6 standard repos
   - Basic routing policies

2. **golden-pci-dss** → extends golden-base (horizontal)
   - Adds PCI audit repo (7-year retention)
   - PCI-specific processing

3. **acme-base** (MSSP) → extends golden-pci-dss (vertical)
   - Overrides retention (90→180)
   - Adds archive repo with warm/cold tiers
   - Adds mount_warm variable

4. **acme-enterprise** → extends acme-base (vertical)
   - Overrides repo-secu (adds NFS tier)
   - 4-tier storage (fast/warm/cold/nfs)

5. **acme-banking-premium** → extends enterprise (horizontal)
   - Adds MiFID compliance processing
   - Trading repo for high-frequency logs

6. **bank-a-prod** (Instance)
   - Client code: BANKA
   - Region: EU-WEST
   - Overrides specific retentions

**Speaker**: "This demonstrates both inheritance types:"
- **Horizontal** (same level): base → pci, base → banking
- **Vertical** (parent→child): LogPoint → MSSP → Profile → Instance

---

### 6. Multiple Clients Demo (3 min)

Show different clients:

```bash
# Compare Bank A vs Bank B
# Bank A: Uses banking-premium profile
cat demo-configs/instances/banks/bank-a/prod/instance.yaml | grep extends
# Output: extends: mssp/acme-corp/profiles/banking-premium

# Bank B: Uses banking addon directly
cat demo-configs/instances/banks/bank-b/prod/instance.yaml | grep extends
# Output: extends: mssp/acme-corp/addons/banking
```

**Speaker**: "Bank A and Bank B are both banks but with different profiles."

```bash
# Enterprise client
cat demo-configs/instances/enterprises/corp-x/prod/instance.yaml | grep extends
# Output: extends: mssp/acme-corp/profiles/enterprise
```

**Speaker**: "Corp X uses enterprise profile, no banking-specific configs."

---

## Key Messages to Emphasize

1. **Single Source of Truth**
   - LogPoint maintains golden templates
   - MSSP customizes for their needs
   - Clients get exactly what they need

2. **DRY Principle (Don't Repeat Yourself)**
   - Common configs in base templates
   - Only specify differences
   - 6-level inheritance = maximum reuse

3. **Compliance Made Easy**
   - PCI addon for financial clients
   - Healthcare addon for HIPAA
   - Mix and match as needed

4. **Scalability**
   - Add new client: 1 YAML file (instance.yaml)
   - Update all clients: Change base template
   - 100 clients managed as easily as 1

---

## Q&A Preparation

**Q: "How do we handle API changes?"**
A: Provider abstraction (ADR-007). Director API today, Direct API later.

**Q: "What about existing DirSync configurations?"**
A: Migration path documented in CLEANUP-MIGRATION.md. Convert base_config.yaml → templates.

**Q: "Can clients override everything?"**
A: Yes! Instance level has final say. But they inherit sensible defaults.

**Q: "How do we prevent breaking changes?"**
A: Versioning (SemVer) + validate command catches errors before deployment.

---

## Backup Plan

If something doesn't work:
1. Show generated YAML files directly
2. Use `cat` and `less` to show structure
3. Focus on concept over working demo

---

## Post-Demo Actions

1. Collect feedback on template structure
2. Validate understanding of inheritance
3. Confirm client types and profiles needed
4. Schedule follow-up: Provider implementation

---

**Good luck with the demo! 🚀**
