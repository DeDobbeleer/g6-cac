# Templating System — Design Draft

> **Status:** Draft — co-written step by step. Open points are marked **[OPEN]**.
> **Source:** Templating & Topology meeting (2026-08-28) + PM draft.
> **Language:** English (project convention).

## 0. Context & Problem

**Why templating.** Onboarding a new MSSP customer today means manually configuring every SIEM element — repos, routing, normalization, processing, devices — pool by pool, instance by instance. This is slow, inconsistent between engineers, error-prone, and unreviewable. There is no standard baseline: each customer estate reflects whoever configured it.

**Who it serves.** The primary user is the **MSSP / SOC engineer** deploying and operating customer estates at fleet scale (reference point: SCALTEL operates ~70 Director-managed tenants). Secondary users: Guardsix CS/SE engineers onboarding new customers, and partners (8com, Scautel) building their own templates on top of ours.

**Target outcome.** A new customer pool is configured **from a template on day one**: standard, reviewable, repeatable. The template is the unit of change — reviewed like code, applied identically across tenants, and the reference against which drift is measured later.

**Success criteria (to be refined in PR-FAQ):** time-to-configure a new customer pool drops from days of manual work to a single template apply; every element deployed is traceable to a template version.

## 1. Principles

**Decisions already taken (meeting 2026-08-28):**

- The templating system is the **source of truth**. The artifact generated from a plan is the configuration file that gets applied — it **cannot be modified** outside the template (immutability).
- Three possible actions per configuration object: **create**, **update**, **noop** (nothing is performed when the object already exists identically — avoids wasting time on API calls and status checks). **No delete in V1.**
- Configuration objects are **validated**: required dependencies and referenced resources must exist. Name-based references imply an **ID lookup mechanism** (detail deferred to tech design).
- **Performance contract (baseline):** today one configuration object takes ~2–3 s to apply (async API + status polling). This is the documented current baseline; it will be revised after testing the new flow (bulk POST then batched status checks is a candidate optimization — *how*, tech design).

**Requirements and open points:**

- The templating system must be **hierarchical**.
- The customer may or may not **inherit from the Guardsix gold templates**.
  - **[OPEN]** Define what optional inheritance means concretely: opt-in per layer? per resource type? Can a customer inherit partially (e.g. Guardsix repos but their own normalization policies)?
- The **distribution channel** for gold templates is still to be defined: GitHub repo? Terraform provider?
  - **[OPEN]** Candidates: GitHub repo (native versioning, PR/review, customer forks — but we own maintenance and version migrations), Terraform provider (product-grade distribution — but imposes a runtime/mental model), or templates embedded in the CLI itself (`cac init --template golden-base`). This is a *how*, can stay TBD in the PR-FAQ.

## 2. V1 Scope

- Compatible with the **Fleet destination API** (Director), and must be designed to **extend to the Direct SIEM API** later.
  - **Remark 1:** The Direct SIEM API is only compatible with **Log Sources**.
  - **Remark 2:** Log Sources are **not compatible with templating** — e.g. it is impossible to template routing policies.
    - **[RISK]** If true, this directly challenges the assertion in §5 — must be verified early.

### 2.1 Legacy source onboarding (and Log Sources later)

Resources covered by templating, in dependency order:

1. Repos
2. Routing Policies
3. Normalization Policies
4. Enrichment Policies — Enrichment Sources? **[OPEN]** enrichment policies reference live sources (tables, files, threat intel). Proposal to decide: in V1 we template the policy, the source stays out of scope.
5. Processing Policies
6. Devices
7. Fetchers

### 2.2 Topology

- In V1 we do **not** manage tenant topologies. Topology management will be handled in a **separate PR-FAQ** (owned during Q4).
- However, the templating system **must be ready to integrate topology**.
  - **[OPEN]** Minimal hook to avoid retrofit pain: e.g. an optional `topology:` section or a `target_role` field (all-in-one / search-head / data-node) in the schema, ignored in V1.

## 3. Sources

### 3.1 Prioritization method — three sources of truth confronted

The gold template source list is **not** derived from a single reference. It comes from confronting three independent sources:

1. **Internal — Confluence official tiering** (product/marketplace view):
   - [Tier 1 Integrations Vendors & Products](https://logpoint.atlassian.net/wiki/pages/viewpage.action?pageId=5343510701) — priority 1–8 + wave 1, driven by compliance (NIST SP 800-53 AU-2/AU-3, CIS 8.11, ISO 27001 A.12.4) and TDIR use cases.
   - [Integration Classification Overview](https://logpoint.atlassian.net/wiki/pages/viewpage.action?pageId=5922947094) — Premium / Standard / Archived plugin classification.
   - Local exports: `tmp/tier1-integrations-vendors-products.md`, `tmp/tier-wise-integrations.md`.
2. **Field — PM integration experience** (12 years of SIEM/MSSP integrations): the real-life priority order observed on SOC/MSSP onboardings.
3. **Internet — industry consensus** (detection-value view):
   - [SIEM Log Source Onboarding: Prioritization Guide](https://www.decryptiondigest.com/blog/log-source-onboarding-siem-prioritization) — defines a 5-source "coverage floor": authentication logs → DNS resolver logs → endpoint process execution (EDR/Sysmon) → cloud control plane → firewall/proxy outbound. Based on a coverage-vs-cost matrix and MITRE ATT&CK mapping.
   - [Priority logs for SIEM ingestion — Practitioner guidance](https://media.defense.gov/2025/May/27/2003722069/-1/-1/0/Priority-logs-for-SIEM-ingestion-Practitioner-guidance.PDF) (media.defense.gov, May 2025) — US DoD practitioner guidance covering EDR, Windows/Linux OS, cloud and network devices.

**Key finding:** the PM's field prioritization **matches the industry consensus** (authentication > DNS > endpoint > firewall). The Confluence tiering is consistent but ordered by compliance/adoption drivers rather than pure detection value — both converge on the same source set.

### 3.2 Field priority order (PM decision)

Priority is set by real-life SOC/MSSP integration experience, confirmed by the industry references above:

1. **Authentication & host OS** — Windows Security Event Log (incl. Sysmon), Linux servers
2. **DNS / DHCP** — resolver and server logs (most commonly missing high-value source in the field)
3. **Endpoint & network detection telemetry** — EDR/Sysmon process execution, NDR alerts and metadata (e.g. Guardsix NDR)
4. **Firewalls / network perimeter** — outbound traffic, covers hosts without agents
5. **Cloud control plane** — out of V1 scope (requires Log Sources, see §2 Remark 2)

### 3.3 Intersection — Confluence tier-1 sources that are also field priorities

Sources present **both** in the [Confluence tier-1 list](https://logpoint.atlassian.net/wiki/pages/viewpage.action?pageId=5343510701) **and** in the field priority order (§3.2), with their collection mode:

| Field priority | Confluence source | Confluence ref | Collection mode | V1-compatible (legacy)? |
|---|---|---|---|---|
| 1. Auth & host OS | Windows Security Event Log incl. Sysmon | Priority 1, plugin Yes, content yes | Logpoint Agent / Event Log | ✅ |
| 1. Auth & host OS | Linux servers | Priority 1, plugin Yes, content yes | Syslog | ✅ |
| 1. Auth (IAM) | Microsoft ADFS Authentication | Priority 2, plugin Yes, content yes | Windows Event Log | ✅ |
| 2. DNS/DHCP | Windows DNS Server logs / debug log | Priority 4, plugin yes | Event Log / debug log file | ✅ |
| 2. DNS/DHCP | Windows DHCP Server | Priority 4, plugin Yes | Event Log / file | ✅ |
| 3. Endpoint (EDR) | CrowdStrike / SentinelOne / Defender XDR / Trellix | Priority 3 | API / alerting sources | ❌ alerting out of V1 scope |
| 3. Network detection (NDR) | Guardsix NDR; also DarkTrace, Vectra | Premium / Standard plugins | Syslog (alerts / metadata) | ✅ (legacy syslog) — **[OPEN]** validate with Benjamin |
| 4. Firewall | Fortinet FortiGate | Priority 6, Premium, SE-prioritized | Syslog | ✅ |
| 4. Firewall | Palo Alto Networks PAN-OS | Priority 6, Premium, SE-prioritized | Syslog | ✅ |
| 4. Firewall | Check Point / Cisco Firepower / Sophos / others | Priority 6 | Syslog | ✅ (candidates for V1.1) |
| 5. Cloud control plane | AWS CloudTrail / GCP Admin-Audit | Priority 7 | API fetcher / Log Sources | ❌ requires Log Sources |

Enrichment (Confluence wave 1, all Premium): Threat Intelligence, Stix/Taxii, CSV, LDAP, ODBC, IPtoHost — templated as enrichment *policies* only; the live sources themselves stay out of scope **[OPEN]**.

### 3.4 Divergences and exclusions

- **Confluence tier-1 but not a field top priority:** email security gateways (Mimecast, Proofpoint, Barracuda, O365 — Priority 5), VMware vCenter/ESXi + FortiAnalyzer (Priority 8), Ping Identity / CyberArk (Priority 2, plugin present but no content) → V1.1 candidates.
- **Field/industry top priority but blocked in V1:** cloud control plane (CloudTrail, Azure Activity, GCP Audit) — requires Log Sources; endpoint EDR alerting — alerting is a later stage. Both are explicitly called out so partners understand the gap is architectural, not an omission.
- **Disputed in Confluence comments:** the need for Sysmon vs native Event Logs is debated (see inline comments on the tier-1 page); field position: keep Sysmon — MITRE coverage, pySigma support, fills the native logging visibility gap.

**[OPEN]** Validate §3.3 with Benjamin (field reality check) before the engineering demo.
**[OPEN]** Repo retention per source must encode compliance drivers (NIST SP 800-53 AU-2/AU-3, CIS 8.11, ISO 27001 A.12.4): ≥ 1 year when the SIEM is the legal log store, shorter when raw logs are retained elsewhere.

## 4. Configuration Element Governance

> Governance is described **per configuration element**. For each element: who owns it, at which template layer it lives, who may change it, and how it evolves (create / update / noop — no delete in V1, per the 2026-08-28 meeting).

*Per-element template to fill:*

- **Owner:** who is accountable for the element definition
- **Template layer:** where it lives in the hierarchy (gold base / profile / addon / customer)
- **Change rights:** who may modify or override it
- **Inheritance:** can a lower layer override it? Under which constraints?
- **Lifecycle:** create / update / noop rules, validation requirements

### 4.1 Repos

- **Recommendation:** maximum **8 custom repos** per tenant. Aggregation is the rule: sources are **grouped into repos by category**, never one repo per source.
- **Aggregation policy** (field-proven, from MSSP architecture practice):

| Repo | Sources aggregated | Retention |
|---|---|---|
| `repo-system` | Windows/AD, Linux, macOS, … | standard |
| `repo-system-verbose` | same sources, verbose logs | **lower** than standard |
| `repo-secu` | Firewall, proxy, router, switch, … | standard |
| `repo-secu-verbose` | same sources, verbose logs | **lower** than standard |
| `repo-expert-system` | EDR, NDR, bastion, UEBA, … | standard |
| `repo-cloud` | O365, AWS, Google Workspace | standard |

- **Retention rule:** verbose repos may have a **shorter retention** than their non-verbose counterparts (volume-driven cost control). Compliance floor still applies (see §3.4 — ≥ 1 year when the SIEM is the legal log store).
- **Design implication:** this aggregation policy drives **both repos and routing policies** — routing policies must map each source category to its target repo (see §4.2). The two elements are designed together.
- **Note:** `repo-cloud` is part of the policy even though cloud sources are out of V1 scope (Log Sources, §2 Remark 2) — the repo definition can be templated ahead of the collection mode.
- **Owner / layer / change rights / inheritance:** **[OPEN]** to define (who owns the gold repo set, may a customer add repos up to the 8-custom limit, may a lower layer override retention?)

### 4.2 Routing Policies

Routing policies implement the repo aggregation policy (§4.1): **one routing policy per source**, named `rp-<source>`. Each policy routes its source's events to the target repo defined by the aggregation policy — including the verbose split.

**Routing matrix (sources from §3.3; V1 and later stages marked):**

| Routing policy | Source | Target repo (standard events) | Target repo (verbose events) |
|---|---|---|---|
| `rp-windows` | Windows: Security Event Log, ADFS, DNS Server, DHCP Server | `repo-system` | Sysmon (Windows), PowerShell/WMI operational, DNS debug log → `repo-system-verbose` |
| `rp-linux` | Linux servers | `repo-system` (auth, syslog) | Sysmon (Linux), auditd/debug → `repo-system-verbose` |
| `rp-fortigate` | FortiGate | `repo-secu` (system, VPN, auth, threat) | traffic/session → `repo-secu-verbose` |
| `rp-paloalto` | Palo Alto PAN-OS | `repo-secu` (system, VPN, auth, threat) | traffic/session → `repo-secu-verbose` |
| `rp-checkpoint` | Check Point Firewall | `repo-secu` (system, VPN, auth, threat) | traffic/session → `repo-secu-verbose` |
| `rp-cisco-firepower` | Cisco Firepower | `repo-secu` (system, VPN, auth, threat) | traffic/session → `repo-secu-verbose` |
| `rp-sophos` | Sophos Firewall | `repo-secu` (system, VPN, auth, threat) | traffic/session → `repo-secu-verbose` |
| `rp-sonicwall` | SonicWall Firewall | `repo-secu` (system, VPN, auth, threat) | traffic/session → `repo-secu-verbose` |
| `rp-watchguard` | WatchGuard Firewall | `repo-secu` (system, VPN, auth, threat) | traffic/session → `repo-secu-verbose` |
| `rp-f5` | F5 BIG-IP | `repo-secu` | traffic → `repo-secu-verbose` |
| `rp-citrix-netscaler` | Citrix Netscaler | `repo-secu` | traffic → `repo-secu-verbose` |
| `rp-bluecoat` | Blue Coat proxy | `repo-secu` | traffic → `repo-secu-verbose` |
| `rp-guardsix-ndr` | Guardsix NDR | `repo-expert-system` | — |
| `rp-crowdstrike` | CrowdStrike | `repo-expert-system` — **V2** (alerting sources out of V1 scope, §3.3) | — |
| `rp-sentinelone` | SentinelOne Singularity | `repo-expert-system` — **V2** | — |
| `rp-defender-xdr` | Microsoft Defender XDR | `repo-expert-system` — **V2** | — |
| `rp-trellix` | Trellix | `repo-expert-system` — **V2** | — |
| `rp-o365` | Microsoft Office365 | `repo-cloud` — **V2 only** (Log Sources, §2 Remark 2) | — |
| `rp-aws` | AWS CloudTrail | `repo-cloud` — **V2 only** (Log Sources, §2 Remark 2) | — |
| `rp-gworkspace` | Google Workspace (Gmail, audit) | `repo-cloud` — **V2 only** (Log Sources, §2 Remark 2) | — |
| `rp-gcp` | GCP Admin/Audit | `repo-cloud` — **V2 only** (Log Sources, §2 Remark 2) | — |

**Design rules:**

- **One policy = one source:** granularity is the source (platform family), not the repo and not the sub-service. **Windows is a single source** — Security Event Log, ADFS, DNS and DHCP all route through `rp-windows`; no per-service policies. **Sysmon follows its host OS** — Sysmon for Windows routes in `rp-windows`, Sysmon for Linux in `rp-linux`. A customer enabling a source gets exactly one routing policy, self-contained.
- **Verbose split inside the source policy:** when a source produces both standard and verbose events (firewalls, DNS, Linux), the same policy routes verbose event types to the `-verbose` repo. The split is on the event channel/type, not on the device.
- **Evaluation order:** within a source policy, verbose criteria are evaluated **before** standard criteria (most specific first). **[OPEN]** confirm ordering semantics of routing policy evaluation (Director API).
- **Catch-all:** anything unmatched goes to a default repo — governance note: unmatched logs must be **visible** (drift/monitoring), never silently dropped. **[OPEN]** keep `repo-default` as catch-all or reject unmatched?
- **Normalization dependency:** routing criteria reference normalization policies — routing policies are therefore designed **after** normalization policies in the dependency DAG (§2.1).
- **Lifecycle:** create / update / noop (no delete in V1). Idempotent re-apply: same criteria + same target = noop.

**Governance fields:** owner / layer / change rights / inheritance — **[OPEN]**, same model to define as repos (§4.1).

### 4.3 Normalization Policies

*(to be written)*

### 4.4 Enrichment Policies

*(to be written)*

### 4.5 Processing Policies

*(to be written)*

### 4.6 Devices

*(to be written)*

### 4.7 Fetchers

*(to be written)*

## 5. General Remarks

- With a **Legacy-ready template**, we could in the future have a legacy destination scope and, from the legacy data, derive **Log Sources destinations** *(assertion to be verified)*.
  - **[RISK]** Depends on Remark 2 above — needs early validation.
