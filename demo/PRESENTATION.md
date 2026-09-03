# Templating System — Concept Demo

**Audience:** Engineering · **Support:** design draft (`docs/reflexion/TEMPLATING-DESIGN-DRAFT.md`) · **Spec (implementation bible):** `specs/20-TEMPLATE-HIERARCHY.md`

---

## 1. Scope

**V1 — legacy onboarding, Fleet (Director) API:**

Repos → Routing Policies → Normalization Policies → Enrichment Policies → Processing Policies → Devices → Fetchers

**Explicitly out:** Log Sources (not templatable — e.g. routing policies), Direct SIEM API (log-sources only), alerting/dashboards/reports, tenant **topology** (separate PR-FAQ, Q4 — the code must just be ready for it).

## 2. Source selection — three sources of truth confronted

1. **Confluence tiering** — [Tier 1 Integrations](https://logpoint.atlassian.net/wiki/pages/viewpage.action?pageId=5343510701), [Premium/Standard classification](https://logpoint.atlassian.net/wiki/pages/viewpage.action?pageId=5922947094)
2. **Field experience** — 12 years of SIEM/MSSP integrations
3. **Industry consensus** — [SIEM prioritization guide](https://www.decryptiondigest.com/blog/log-source-onboarding-siem-prioritization), [US DoD practitioner guidance](https://media.defense.gov/2025/May/27/2003722069/-1/-1/0/Priority-logs-for-SIEM-ingestion-Practitioner-guidance.PDF)

**Finding:** field priorities match the industry consensus — **authentication > DNS > endpoint > firewall** — and converge with the official tiering on the same source set.

V1 set: Windows (Security/ADFS/DNS/DHCP + Sysmon), Linux, firewalls (FortiGate, Palo Alto, Check Point, …), Guardsix NDR, **EDR** (CrowdStrike, SentinelOne, Defender XDR — log ingestion; alert *rules* come later). V2: cloud control plane.

## 3. Configuration element policies

- **Repos** — max 8 custom per tenant, **aggregation by category** (never one repo per source): `repo-system(-verbose)`, `repo-secu(-verbose)`, `repo-expert-system`, `repo-cloud`. Verbose = shorter retention. Compliance floor: ≥ 1 year if the SIEM is the legal log store.
- **Routing** — **one policy per source** (`rp-windows`, `rp-fortigate`…), self-contained; verbose split on event type, not device; `drop` field for filtering (`store` / `discard_raw` / `discard_entirely`); `sourceMappings` link vendor/product → policy.
- **Normalization** — `np-<source>` per source, **derived from Guardsix official packages** (curated, not reinvented); real packages verified on a live 7.10 export.
- **Enrichment** — policies templated (`ep-threat-intel`, `ep-geoip`, `ep-active-directory`); **sources are UI-created prerequisites** (read-only API).

## 4. How templates are built (spec: `specs/20-TEMPLATE-HIERARCHY.md`)

- **4 levels:** Guardsix Golden → MSSP Base → Profile → Instance (practical limit 4–5; cross-level + intra-level inheritance).
- **Inheritance is optional and granular:** no `extends` = standalone; merge per resource by `name`, per list element by `_id`; child always wins.
- **Mechanisms:** inherit · override · append · patch · (delete: future release) + ordering (`_before`, `_after`, `_position`, `_first`, `_last`).
- `_id` / `_action` are internal — stripped before the API payload.
- **Version pinning:** `extends: golden-base@v2`.

## 5. Documented vs remaining

**Done:** hierarchy & inheritance model · V1 scope · source prioritization · repo aggregation policy + golden retentions · routing matrix · normalization mapping · enrichment scope decision · spec v1.1 aligned with the draft.

**Open:** distribution channel for gold templates (GitHub repo / Terraform provider / CLI-embedded) · governance fields per element (owner, change rights) · normalization gaps (SonicWall, FortiOS main package, Windows/Sysmon core, NDR) from marketplace · enrichment source workflow · template signing & audit trail · topology hooks.

---

## 6. Demo — repos, live

**Story:** one Guardsix gold template, specialized by an MSSP, producing two different artifacts for two customer types. Zero duplication.

```
guardsix/golden-base        6 repos · /opt/immune/storage · 30d (15d verbose)
└── mssp/demo/default       retention 30→90 / 15→30 · append cold tier (90d)
    ├── client-standard     pure inheritance
    └── mssp/demo/legal-retention   warm tier inserted before cold · cold→185d · total = 365d
        └── client-regulated
```

### Commands

```bash
# Show the three template levels
cat demo/templates/guardsix/golden-base/repos.yaml
cat demo/templates/mssp/demo/default/repos.yaml
cat demo/templates/mssp/demo/legal-retention/repos.yaml

# Resolve both clients — watch chain, order, retentions
cac-configmgr resolve -i demo/instances/client-standard/instance.yaml --templates-dir demo
cac-configmgr resolve -i demo/instances/client-regulated/instance.yaml --templates-dir demo

# JSON payload only (same shape as a real live-system payload)
cac-configmgr resolve -i demo/instances/client-regulated/instance.yaml --templates-dir demo --json
```

### Live tweaks (verified — cause → effect)

```bash
# A. Gold owns the path: edit golden-base /opt/immune/storage -> /opt/immune/storage_fast
#    Re-run resolve on both clients -> path updated EVERYWHERE (no one overrode it).
cac-configmgr resolve -i demo/instances/client-regulated/instance.yaml --templates-dir demo --json

# B. MSSP owns primary retention: edit mssp/demo/default 90 -> 60
#    Re-run -> BOTH clients move to 60. Note: legal template still shows cold=185,
#    total is now 335 — the "sum = 365" rule is an authoring convention,
#    NOT engine-enforced (validation candidate).

# C. Gold retention change is invisible: edit golden-base 30 -> 45
#    Re-run -> nothing changes: MSSP overrode primary retention (child wins).
```

Reference artifacts (pre-generated): `demo/expected/client-standard.json`, `demo/expected/client-regulated.json`.

### Known limitation (found by negative testing)

A `_before`/`_after` pointing to a non-existent `_id` is silently ignored (element appended at end) — must become a validation error. Extends-not-found and circular dependencies are correctly rejected.

### Out of scope (say it)

Topology (PR-FAQ Q4, code archived in `topology/`) · plan/apply (Phase 2 — payload validation on a live system comes next) · delete (future release).
