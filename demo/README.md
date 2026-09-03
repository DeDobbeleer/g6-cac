# Demo — Hierarchical Templating (Concept)

> Concept demo for engineering, with the design draft (`docs/reflexion/TEMPLATING-DESIGN-DRAFT.md`) as support.
> Scope: **repos only**. No topology (archived in `topology/`, returns via the SIM-topology PR-FAQ). No apply — we show the template and the generated artifact.

## The story in one sentence

One Guardsix gold template, inherited and specialized by an MSSP, produces **two different ready-to-apply configurations** for two different customer types — without duplicating anything.

## The chain

```
guardsix/golden-base          6 repos, OOB mount /opt/immune/storage, 30d (15d verbose)
└── mssp/demo/default         override retention 30→90 / 15→30, append cold tier (storage_cold, 90d)
    ├── client-standard       pure inheritance, zero override
    └── mssp/demo/legal-retention   insert warm tier (storage_warm, 90d) BEFORE cold,
        │                           override cold to 185d → total = 365d
        └── client-regulated  inherits the legal-retention template
```

## Demo script

```bash
# 1. Show the gold template (the 6 repos, golden retentions)
cat demo/templates/guardsix/golden-base/repos.yaml

# 2. Show the MSSP override (merge by _id: retention changed, cold tier appended)
cat demo/templates/mssp/demo/default/repos.yaml

# 3. Show the legal-retention specialization (_before insertion + sum = 365)
cat demo/templates/mssp/demo/legal-retention/repos.yaml

# 4. Resolve the standard client (3 levels)
cac-configmgr resolve -i demo/instances/client-standard/instance.yaml --templates-dir demo

# 5. Resolve the regulated client (4 levels) — the same gold, a different artifact
cac-configmgr resolve -i demo/instances/client-regulated/instance.yaml --templates-dir demo

# 6. (optional) JSON payload only — same shape as a real API payload
cac-configmgr resolve -i demo/instances/client-regulated/instance.yaml --templates-dir demo --json
```

## Concepts demonstrated

| Concept | Where it shows |
|---|---|
| Hierarchy (4 levels) | chain printed by `resolve` |
| Inheritance without duplication | `client-standard` has an empty spec |
| Field-level merge by `_id` | retention 30→90, path inherited |
| Append | `cold` tier added by the MSSP |
| Ordered insertion | `warm` tier inserted `_before: cold` |
| Business rule in a template | total retention = 365d for regulated customers |
| Immutable artifact | payload = template output, `_id`/`_before` stripped |
| Realism | payload shape identical to a captured live-system payload (`examples/dumps/`) |

## Out of scope (say it explicitly)

- **Topology** — separate PR-FAQ (Q4); code archived in `topology/`
- **plan/apply** — Phase 2; validation against a live system comes next (PoC tools)
- **Delete** — not in V1 (create / update / noop only)
