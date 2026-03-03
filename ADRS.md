# Architecture Decision Records (ADRs)

**Project**: CaC-ConfigMgr  
**Language**: English  
**Last Updated**: 2026-03-03  
**Total ADRs**: 11

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
| ADR-010 | DirSync Relationship | ✅ Accepted | Architecture |
| ADR-011 | API Convention Pattern | ✅ Accepted | Extensibility |

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

**Decision**: Directed Acyclic Graph (DAG) with explicit ordering

```yaml
# Dependencies declared, not hardcoded
spec:
  processing_policy:
    - routing_policy: "rp-default"  # Dependency by name
```

**Rationale**:
- Clear dependency visualization
- Enables parallelization where safe
- Detects circular dependencies early
- Self-documenting

---

## ADR-005: State Management

**Status**: ✅ Proposed

**Decision**: Stateless (API-only), no local state file

**Context**:
Terraform uses state files to track resource IDs. This causes issues with team collaboration and drift detection.

**Rationale**:
- Director is the source of truth
- IDs fetched at runtime via name lookup
- No state file = no conflicts, no secrets in state
- Simpler mental model

**Implementation**:
```python
# No: terraform.tfstate with IDs
# Yes: Query Director by name
resources = await provider.get_resources("routing_policies")
lookup = {r["policy_name"]: r["_id"] for r in resources}
```

---

## ADR-006: Direct vs Director Mode

**Status**: ⏳ Deferred

**Decision**: Implement Director mode first, Direct mode later

**Context**:
LogPoint can be managed via:
1. **Director API**: MSSP multi-tenant mode
2. **Direct API**: Local SIEM API (all-in-one or distributed)

**Rationale**:
- Director mode is primary use case (MSSP)
- Direct API documentation less mature
- Can add Direct mode later with same abstraction

**Future**:
```yaml
metadata:
  provider: logpoint
  deploymentMode: director  # or "direct"
```

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
```python
# Abstract provider interface
class Provider(ABC):
    @abstractmethod
    async def get_resources(self, resource_type: str) -> list[dict]: ...

# Director implementation
class DirectorProvider(Provider): ...

# Future: Direct implementation  
class DirectProvider(Provider): ...
```

**Benefits**:
- One CLI tool for all deployment modes
- Same YAML configs work everywhere
- Easy testing with MockProvider

---

### 2. API Versioning

**Principle**: Forward-compatible API evolution.

**Implementation**:
```yaml
metadata:
  apiVersion: logpoint-cac/v1  # Schema version
  directorVersion: "1.3"       # Target API version
```

**Version Compatibility**:
| CaC Version | Director API | Status |
|-------------|--------------|--------|
| v1 | 1.3+ | ✅ Supported |
| v1 | 2.0 | ⏳ Future |

---

### 3. Multi-Product

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
- Provider auto-detection from metadata

---

## ADR-008: Name-Based Validation

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

---

## ADR-010: DirSync Relationship - Knowledge vs Code

**Status**: ✅ Accepted (Architecture Principle)

**Decision**: Use DirSync as **technical reference** for domain knowledge, but implement with **clean CaC-ConfigMgr architecture**.

**Context**:
DirSync is an existing internal tool for LogPoint configuration synchronization. It has valuable domain knowledge about Director APIs but uses a legacy architecture unsuitable for Configuration as Code.

---

### What We Learn FROM DirSync (Knowledge Transfer)

DirSync provides valuable **domain expertise** about LogPoint Director:

| Knowledge Area | DirSync Experience | CaC-ConfigMgr Implementation |
|----------------|-------------------|------------------------------|
| **API Contracts** | REST endpoints, request/response formats | Documented in `API-REFERENCE.md` |
| **Authentication** | Token-based auth, pool UUID management | `DirectorProvider` with `httpx` |
| **Async Operations** | Polling strategies, timeout handling | `anyio` with exponential backoff |
| **Field Semantics** | Required vs optional fields, defaults | Pydantic validators |
| **Error Patterns** | Common failures, retry scenarios | Structured error handling |
| **Payload Structure** | JSON schemas for each resource type | Pydantic models with aliases |

**Example - API Error Handling:**
```python
# From DirSync experience: Director returns 202 with async operation
# CaC-ConfigMgr implementation:
async def create_resource(self, payload: dict) -> dict:
    response = await self.client.post("/routingpolicies", json=payload)
    if response.status_code == 202:
        # DirSync taught us: need to poll for completion
        operation_id = response.headers["X-Operation-Id"]
        return await self._poll_operation(operation_id)
```

---

### What We Do NOT Copy FROM DirSync (Architecture Differences)

**Why Not Reuse DirSync Code?**

| Aspect | DirSync Approach | CaC-ConfigMgr Approach | Reason |
|--------|-----------------|------------------------|--------|
| **Paradigm** | Stateful synchronization | Stateless desired state | Different use cases |
| **Architecture** | Monolithic | 4-layer clean architecture | Testability, maintainability |
| **Configuration** | Internal JSON structures | YAML with template inheritance | GitOps, human-readable |
| **Inheritance** | None | 6-level template hierarchy | Code reuse, DRY |
| **Validation** | Runtime basic checks | 4-level offline validation | Early error detection |
| **Approach** | Imperative (how) | Declarative (what) | User experience |
| **Coupling** | Tight coupling to specific use case | Loose coupling via Provider pattern | Extensibility |

**Code Comparison:**

```python
# ❌ DirSync: Stateful, synchronous, tightly coupled
class DirSync:
    def __init__(self):
        self.state = {}  # Stateful
        self.db = DatabaseConnection()  # Tight coupling
    
    def sync_config(self, config_id: str):
        # Direct database queries
        # Complex state management
        # Hard to test without real database
        pass

# ✅ CaC-ConfigMgr: Stateless, async, clean interface
class DirectorProvider(Provider):
    def __init__(self, config: DirectorConfig, client: httpx.AsyncClient):
        self.config = config
        self.client = client  # Injectable, mockable
    
    async def get_resources(self, resource_type: str) -> list[dict]:
        # Pure HTTP calls
        # No state management
        # Easily testable with mocked client
        response = await self.client.get(f"/{resource_type}")
        return response.json()
```

---

### Implementation Guidelines

**DO - Learn from DirSync:**
- ✅ API endpoint URLs and HTTP methods
- ✅ Request/response payload structures
- ✅ Authentication header formats
- ✅ Async operation polling patterns
- ✅ Error response codes and messages
- ✅ Required vs optional fields
- ✅ Default values and constraints

**DO NOT - Copy from DirSync:**
- ❌ State management patterns
- ❌ Database access patterns
- ❌ Synchronous blocking calls
- ❌ Hardcoded configuration
- ❌ Monolithic class structures
- ❌ Imperative execution logic
- ❌ Internal JSON formats

**Implementation Rule:**

> **Learn "WHAT" from DirSync:** API contracts, payloads, error scenarios  
> **Design "HOW" with CaC-ConfigMgr:** Clean architecture, async patterns, testability

---

### Benefits of Clean Implementation

1. **Testability**: Provider interface allows mocking for unit tests
2. **Extensibility**: Easy to add new providers (Direct API, future products)
3. **Maintainability**: Clean separation of concerns
4. **Modern Patterns**: Async/await, dependency injection, type hints
5. **Future-Proof**: Architecture supports evolution without rewrite

---

### DirSync Knowledge Capture

Key DirSync insights captured in CaC-ConfigMgr:

| DirSync Learning | CaC-ConfigMgr Location |
|-----------------|------------------------|
| API endpoint reference | `specs/API-REFERENCE.md` |
| Async operation behavior | `PHASE2-PLAN.md` polling implementation |
| Field requirements | Pydantic models with `Field(...)` |
| Authentication flow | `DirectorProvider.__init__()` |
| Error retry patterns | `providers/director.py` retry decorator |
| Payload transformations | `filter_internal_ids()` in engine |

---

**Conclusion**: DirSync is a valuable **reference implementation** for understanding LogPoint Director behavior, but CaC-ConfigMgr requires a fundamentally different architecture to achieve Configuration as Code goals.

---

## ADR-011: API Convention Pattern

**Status**: ✅ Accepted (Extensibility)

**Decision**: Abstract API validation through the **API Convention Pattern** to support multiple providers without code duplication.

**Context**:
Different LogPoint APIs (Director, Direct, SOAR, NDR) may have:
- Different field naming conventions (camelCase vs snake_case)
- Different required fields and validation rules
- Different resource types and relationships
- Different API endpoint structures

Hardcoding Director-specific validation rules in the validator would prevent supporting other APIs.

---

### Problem

Initial implementation hardcoded Director API conventions:

```python
# ❌ Before: Hardcoded for Director only
class APIFieldValidator:
    API_SPECS = {
        "processing_policy": {
            "routing_policy": {
                "type": str,
                "alias": "routingPolicy"  # Director-specific camelCase
            }
        }
    }
```

This made it impossible to validate against other APIs without duplicating code.

---

### Solution

Introduce `APIConvention` abstraction:

```python
# ✅ After: Provider-agnostic validation
class APIConvention(ABC):
    @abstractmethod
    def get_field_alias(self, resource_type: str, field_name: str) -> str:
        """Return API field name (may differ by convention)."""
        pass
    
    @abstractmethod
    def get_resource_spec(self, resource_type: str) -> ResourceSpec:
        """Return field specifications for validation."""
        pass

class DirectorAPIConvention(APIConvention):
    def get_field_alias(self, rt, field):
        # Director uses camelCase
        aliases = {
            "routing_policy": "routingPolicy",
            "device_group": "deviceGroup",
        }
        return aliases.get(field, field)

class DirectAPIConvention(APIConvention):  # Future
    def get_field_alias(self, rt, field):
        # Direct API uses snake_case
        return field  # No transformation needed
```

---

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    API Convention Pattern                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐         ┌──────────────────────────┐  │
│  │ APIConvention   │◄────────┤ DirectorAPIConvention    │  │
│  │   (abstract)    │         │ - camelCase fields       │  │
│  │                 │         │ - policy_name vs name    │  │
│  │ • get_field_alias()     │ - Pool-scoped endpoints    │  │
│  │ • get_name_field()      │                            │  │
│  │ • get_resource_spec()   │  Future:                   │  │
│  │ • get_cross_refs()      │  • DirectAPIConvention     │  │
│  │                         │  • SOARAPIConvention       │  │
│  └─────────────────┘         └──────────────────────────┘  │
│           ▲                                                 │
│           │ injects into                                    │
│  ┌────────┴──────────────────────────────────────────┐     │
│  │              APIFieldValidator                     │     │
│  │                                                    │     │
│  │  • Validates required fields & types               │     │
│  │  • Validates cross-references (by name)            │     │
│  │  • Uses convention for field name mapping          │     │
│  └────────────────────────────────────────────────────┘     │
│                            ▲                                │
│                            │ uses                           │
│  ┌─────────────────────────┴──────────────────────────┐     │
│  │                   Provider                         │     │
│  │                                                    │     │
│  │  • Provides get_convention() → APIConvention      │     │
│  │  • DirectorProvider → DirectorAPIConvention       │     │
│  │  • Future: DirectProvider → DirectAPIConvention   │     │
│  └────────────────────────────────────────────────────┘     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

### Key Components

**1. APIConvention (Abstract)**
```python
class APIConvention(ABC):
    @abstractmethod
    def get_field_alias(self, resource_type: str, field_name: str) -> str:
        pass
    
    @abstractmethod
    def get_name_field(self, resource_type: str) -> str:
        pass
    
    @abstractmethod
    def get_resource_spec(self, resource_type: str) -> ResourceSpec:
        pass
    
    @abstractmethod
    def get_cross_reference_validations(self) -> list[CrossReferenceRule]:
        pass
```

**2. ResourceSpec & FieldSpec**
```python
@dataclass
class FieldSpec:
    name: str
    type: type
    required: bool = True
    alias: str | None = None  # API field name if different
    pattern: str | None = None  # Regex for validation
    api_doc: str = ""

@dataclass
class ResourceSpec:
    resource_type: str
    endpoint: str
    name_field: str
    fields: dict[str, FieldSpec]
```

**3. ConventionRegistry**
```python
class ConventionRegistry:
    def register(self, name: str, convention: type[APIConvention]): ...
    def get(self, name: str) -> APIConvention: ...
    def get_for_provider(self, provider: str, mode: str, version: str) -> APIConvention: ...
```

---

### Usage Examples

**Validation with Director Convention:**
```python
from cac_configmgr.providers.conventions import DirectorAPIConvention
from cac_configmgr.core.api_validator import APIFieldValidator

convention = DirectorAPIConvention()
validator = APIFieldValidator(resources, convention)
errors = validator.validate_all()
```

**CLI with Provider Selection:**
```bash
# Default Director convention
cac-configmgr validate -f fleet.yaml

# Explicit provider selection
cac-configmgr validate -f fleet.yaml --provider director

# Future: Direct API
cac-configmgr validate -f fleet.yaml --provider direct
```

**Provider Implementation:**
```python
class DirectorProvider(Provider):
    def get_convention(self) -> APIConvention:
        from cac_configmgr.providers.conventions import DirectorAPIConvention
        return DirectorAPIConvention()
```

---

### Benefits

| Benefit | Description |
|---------|-------------|
| **Extensibility** | Add new providers without changing validation logic |
| **Testability** | Mock conventions for unit testing |
| **Consistency** | Same validation rules applied across providers |
| **Maintainability** | Provider-specific logic isolated in conventions |
| **Future-Proof** | New LogPoint products (SOAR, NDR) use same pattern |

---

### Implementation Notes

**Location of Files:**
- `src/cac_configmgr/core/conventions.py` - Abstract base classes
- `src/cac_configmgr/providers/conventions/director.py` - Director implementation
- `src/cac_configmgr/core/api_validator.py` - Provider-agnostic validator

**Registration:**
Conventions auto-register on import via:
```python
# In director.py
from cac_configmgr.core.conventions import register_convention
register_convention("director", DirectorAPIConvention)
register_convention("logpoint/director/v1.3", DirectorAPIConvention)
```

**Backward Compatibility:**
```python
# Default to Director convention for existing code
def validate_api_compliance(
    resources: dict,
    convention: APIConvention | None = None
) -> list[ValidationError]:
    if convention is None:
        from cac_configmgr.providers.conventions import DirectorAPIConvention
        convention = DirectorAPIConvention()
    ...
```

---

### Future Extensions

**1. Direct API Convention**
```python
class DirectAPIConvention(APIConvention):
    """For SIEMs without Director."""
    def get_field_alias(self, rt, field):
        return field  # snake_case, no transformation
```

**2. Product-Specific Conventions**
```python
class SOARAPIConvention(APIConvention):
    """For LogPoint SOAR."""
    # Different resource types, different fields
```

**3. Version Migration**
```python
class DirectorAPIv2Convention(APIConvention):
    """When Director API v2 is released."""
    # Handle breaking changes from v1.3
```

---

**Decision Date**: 2026-03-03  
**Implemented By**: Phase 2, Week 1  
**Related**: ADR-007 (Multi-API), ADR-009 (Field Name Mapping)
