# Architecture Decision Records (ADRs)

**Project**: CaC-ConfigMgr  
**Language**: English  
**Last Updated**: 2026-02-27  
**Total ADRs**: 9

---

## Summary

| # | Title | Status | Category |
|---|-------|--------|----------|
| ADR-001 | Language and Stack | ✅ Accepted | Technology |
| ADR-002 | PoC Scope | ✅ Accepted | Scope |
| ADR-003 | Configuration Format | ✅ Accepted | Format |
| ADR-004 | Dependency Management | ✅ Accepted | Deployment |
| ADR-005 | State Management | ✅ Proposed | Architecture |
| ADR-006 | Direct vs Director Mode | ⏳ Deferred | Deployment |
| ADR-007 | Multi-API Architecture | ✅ Accepted | Extensibility |
| ADR-008 | Name-Based Validation | ✅ Accepted | Validation |
| ADR-009 | API Field Name Mapping | ✅ Accepted | API Compliance |

---

## Legend

- **✅ Accepted**: Decision approved and implemented
- **⏳ Deferred**: Decision postponed to later phase
- **🚧 Proposed**: Decision under discussion
- **❌ Rejected**: Decision not adopted

---

## ADR-001: Language and Technical Stack

**Status**: ✅ Accepted (PoC)

**Decision**: Python with Pydantic + Typer + Rich

**Rationale**:
- Rapid prototyping for PoC
- Pydantic excellent for YAML validation
- Typer/Rich = Professional CLI without effort
- Easily portable to Go later if performance needed

**Alternatives Considered**: Go (better performance, static binary) but longer learning curve for rapid iterations.

---

## ADR-002: PoC Scope

**Status**: ✅ Accepted

**Decision**: Focus on data pipeline only
- Repos
- Routing Policies  
- Normalization Policies
- Processing Policies

**Rationale**:
- Core business logic common to all clients
- Concrete demonstration of value (huge time savings)
- Director APIs stable and well documented for these resources
- Easily testable (create/delete repos = safe)

**Out of PoC Scope**:
- AlertRules (more complex, risky to test)
- DeviceGroups (requires existing devices)
- Users/Permissions (sensitive)

---

## ADR-003: Configuration Format

**Status**: ✅ Accepted (PoC)

**Decision**: YAML with Pydantic schemas, Kubernetes style

```yaml
apiVersion: logpoint-cac/v1
kind: Repo
metadata:
  name: default
spec:
  ...
```

**Rationale**:
- DevOps/GitOps standard
- Comments possible (vs JSON)
- Pydantic generates validation + clear errors

---

## ADR-004: Dependency Management

**Status**: ✅ Accepted (PoC)

**Decision**: Implicit deployment order via Processing pipeline

**Order**:
1. Repos (no dependencies)
2. Routing Policies (depends on repos)
3. Normalization Policies (independent)
4. Processing Policies (depends on 2 and 3)

**Rationale**:
- Simple graph for PoC (linear DAG)
- No complex resolver needed to demonstrate value
- Manual processing in correct order acceptable for v1

---

## ADR-005: State Management

**Status**: 🚧 Proposed

**Decision**: No separate persistent state. State = Director reality + YAML files.

**Rationale**:
- Maximum simplicity for PoC
- No SPOF, no database to manage
- `cac sync` allows exporting real state when needed

**Known Limitations**:
- `plan` requires API calls to resolve IDs
- No cache = slower (acceptable for PoC)

---

## ADR-006: Direct vs Director Mode

**Status**: ⏳ Deferred

**Decision**: PoC in Director mode only.

**Rationale**:
- Director APIs stable and tested
- Existing MSSP customer base = immediate market
- Direct SIEM APIs = to be validated, not blocking to demonstrate concept

**Future Evolution**:
- Add Direct connector when SIEM APIs available
- Common abstraction so configs work in both modes

---

## ADR-007: Multi-API, Versioning and Product Extensibility

**Status**: ✅ Accepted (Founding Principle)

**Decision**: Open architecture supporting:
1. **Multi-API**: Director API (today) + Direct SIEM API (future)
2. **API Versioning**: API version management and evolution
3. **Multi-product**: Extensible to other products in LogPoint catalog

---

### 1. Multi-API

**Principle**: Same business logic must work with different target APIs.

**Implementation**:
```yaml
# Fleet specifies mode
spec:
  managementMode: director  # or 'direct'
  director:
    apiHost: "https://director.logpoint.com"
  # direct:  # Future
  #   apiHost: "https://siem.local"
```

**Connectors**:
- `DirectorConnector`: Director API (MSSP, multi-pool)
- `DirectConnector`: Local SIEM API (Enterprise, all-in-one)
- Common `Provider` interface for abstraction

---

### 2. API Versioning

**Principle**: Configurations must remain compatible despite API evolution.

**Implementation**:
```yaml
apiVersion: cac-configmgr.io/v1   # CaC schema version
kind: ConfigTemplate
metadata:
  name: golden-base
  version: "2.1.0"                # Template semantic version (SemVer)
```

**Rules**:
- `apiVersion`: Incremented on schema breaking changes
- `metadata.version`: Template semantic version (SemVer)
- `extends: template@v2`: Reference specific version
- Adapter pattern: Same YAML config → different API versions

**Adaptation Example**:
```python
# Internal: stable CaC v1 schema
# Director API v1.3 → direct mapping
# Director API v2.0 → adapt field 'repo' → 'repository'
# Direct API v1.0 → adapt endpoints
```

---

### 3. Multi-product

**Principle**: Architecture must support products other than LogPoint SIEM.

**Implementation**:
```yaml
metadata:
  provider: logpoint        # Target product
  productType: siem         # Product type
  # Future: provider: logpoint, productType: soar
  # Future: provider: logpoint, productType: ndr
```

**Extensibility**:
- `kind: ConfigTemplate`: Generic
- `spec.repos`: SIEM specific (ignored by other products)
- `spec.playbooks`: SOAR specific (ignored by SIEM)
- Per-product Pydantic validation (`LogPointConfig`, `SOARConfig`)

---

**Rationale**:
- **Future-proof**: No major rewrite for new APIs or products
- **Protected investment**: Time spent on YAML specs reusable
- **Strategic alignment**: LogPoint vision = security platform, not just SIEM

**Current Limitations**:
- PoC: Director only (concept validation)
- Internal → API mapping: To be completed for each new version

**Future Evolution**:
- Implement `DirectConnector` when SIEM APIs stable
- Add `apiVersion: cac-configmgr.io/v2` if breaking changes needed
- Create providers for other products in catalog

---

## ADR-008: Name-Based Cross-Reference Validation

**Status**: ✅ Accepted (Architecture Principle)

**Decision**: Cross-reference validation in offline mode uses resource **NAMES**, not IDs.

**Context**:
During the validation phase, CaC-ConfigMgr works on desired state templates without any API calls. At this stage:
- Resources do not exist yet in Director
- IDs are generated by Director **on resource creation**
- IDs are **unknown** during validation

**Example**:
```yaml
# Template uses names (human-readable)
processing_policy:
  policy_name: pp-default
  routing_policy: rp-default        # ← Name, not ID
  normalization_policy: _logpoint   # ← Name, not ID
```

**Consequences**:

1. **Validation Phase** (Offline):
   - Check: Does "rp-default" exist as a Routing Policy name?
   - Check: Does "_logpoint" exist as a Normalization Policy name?
   - No network calls required
   - Fast, local validation

2. **Apply Phase** (Online):
   - Query Director API: `GET /routingpolicies`
   - Build lookup table: `{"rp-default": "586cc3ed...", ...}`
   - Transform payload: `routing_policy: "rp-default"` → `routing_policy: "586cc3ed..."`
   - Send to API with real Director IDs

3. **Simpler Mental Model**:
   - Humans write and think in names
   - IDs are implementation details of Director
   - Name stability: "rp-default" stays constant, ID changes per environment

**Implementation**:

```python
# api_validator.py - Name-based validation
indexes = {
    "routing_policies": {"rp-default", "rp-windows", ...},  # By name
    # NOT: "routing_policies_by_id": {"586cc3ed...", ...}   # IDs unknown
}

def validate_pp_routing_policy(pp):
    if pp.routing_policy not in indexes["routing_policies"]:
        raise ValidationError(f"Unknown routing policy: {pp.routing_policy}")
```

**Trade-offs**:
- ✅ Simpler templates (names vs UUIDs)
- ✅ Portable configs (names stable across environments)
- ✅ Fast offline validation
- ⚠️ Requires name→ID translation during apply
- ⚠️ Name changes = breaking changes

---

## ADR-009: API Field Name Mapping

**Status**: ✅ Accepted (LogPoint Director API Compliance)

**Decision**: Resource types use different primary name fields to match LogPoint Director API conventions.

**Context**:
LogPoint Director API uses inconsistent field naming across resource types. CaC-ConfigMgr must match these conventions for API compliance.

**Field Mapping**:

| Resource Type | CaC Field | Director API Field | Consistency |
|---------------|-----------|-------------------|-------------|
| RoutingPolicy | `policy_name` | `policy_name` | ✅ Consistent |
| ProcessingPolicy | `policy_name` | `policy_name` | ✅ Consistent |
| EnrichmentPolicy | `policy_name` | `policy_name` | ✅ Consistent |
| **NormalizationPolicy** | **`name`** | **`name`** | ⚠️ **Exception** |
| Repo | `name` | `name` | ✅ Consistent |

**The Exception**:
NormalizationPolicy uses `name` instead of `policy_name` in both CaC and Director API.

```yaml
# routing_policies.yaml
routing_policies:
  - policy_name: rp-default          # ✅ Uses policy_name
    catch_all: repo-default

# processing_policies.yaml  
processing_policies:
  - policy_name: pp-default          # ✅ Uses policy_name
    routing_policy: rp-default

# normalization_policies.yaml
normalization_policies:
  - name: _logpoint                   # ⚠️ Uses name, not policy_name
    normalization_packages: [...]
```

**Implementation**:

```python
# Pydantic models match API conventions
class RoutingPolicy(BaseModel):
    policy_name: str = Field(..., alias="name")  # YAML uses 'name'
    
class NormalizationPolicy(BaseModel):
    name: str = Field(...)  # YAML also uses 'name'
    # No alias needed - matches API field
```

**Validation Considerations**:
- Code must check correct field for each resource type
- Indexes use correct field: `rp.policy_name` vs `np.name`
- Error messages reference correct field name
- Serialization uses `by_alias=True` for YAML compatibility

**Future-Proofing**:
If LogPoint unifies naming in future API versions:
- Adapter pattern can handle mapping
- CaC internal schema can remain stable
- Only API client layer needs updates
