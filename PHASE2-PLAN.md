# Phase 2: Director Integration Plan

**Status**: 🚧 In Progress  
**Branch**: `phase2`  
**Start Date**: 2026-02-27  
**Goal**: Connect to Director API, implement plan/apply commands

---

## Overview

Phase 2 implements the core deployment functionality:
- Director API provider (HTTP client with authentication)
- Plan command (dry-run, shows diff)
- Apply command (actual deployment with name-to-ID resolution)
- Name-to-ID translation during apply

---

## Deliverables

### 1. Director Provider (`src/cac_configmgr/providers/`)

```
providers/
├── __init__.py
├── base.py              # Abstract Provider interface
└── director.py          # DirectorProvider implementation
```

**Features:**
- [ ] Authentication (token-based)
- [ ] Pool UUID management
- [ ] HTTP client (httpx)
- [ ] Resource CRUD operations
- [ ] Async operation polling
- [ ] Error handling and retries

### 2. Plan Command (`src/cac_configmgr/cli/`)

**Features:**
- [ ] Load declared state from YAML
- [ ] Fetch actual state from Director API
- [ ] Calculate diff (CREATE/UPDATE/DELETE)
- [ ] Output: Table or JSON
- [ ] Exit codes for CI/CD integration

### 3. Apply Command (`src/cac_configmgr/cli/`)

**Features:**
- [ ] Execute plan
- [ ] Name-to-ID resolution (GET resources → build lookup)
- [ ] Handle async operations (polling)
- [ ] Progress reporting
- [ ] Error handling with rollback option
- [ ] Auto-approve flag for CI/CD

### 4. Name-to-ID Resolution

**Implementation:**
```python
# During apply phase:
1. GET /routingpolicies from Director
2. Build lookup: {"rp-default": "586cc3ed...", ...}
3. Transform: routing_policy: "rp-default" → "586cc3ed..."
4. POST to Director with real IDs
```

---

## Implementation Order

### Week 1: Director Provider Foundation

Day 1-2:
- Create `providers/base.py` - Abstract interface
- Create `providers/director.py` - Initial implementation
- Implement authentication

Day 3-4:
- Implement GET operations (for plan/diff)
- Implement POST/PUT/DELETE operations
- Add error handling

Day 5:
- Implement async operation polling
- Add retry logic
- Write tests

### Week 2: Plan Command

Day 1-2:
- Load declared state (reuse resolution engine)
- Fetch actual state from Director

Day 3-4:
- Implement diff calculation
- Create output formatters (table, JSON)

Day 5:
- Integration testing
- Documentation

### Week 3: Apply Command

Day 1-2:
- Implement name-to-ID resolution
- Build lookup tables from Director

Day 3-4:
- Execute operations in dependency order
- Handle async polling
- Progress reporting

Day 5:
- Error handling and rollback
- Auto-approve flag
- Integration testing

### Week 4: Testing & Polish

- Integration tests with real Director instance
- Error scenarios
- Performance testing
- Documentation updates

---

## Technical Design

### Provider Interface

```python
class Provider(ABC):
    @abstractmethod
    async def get_resources(self, resource_type: str) -> list[dict]:
        """Fetch all resources of a type from Director."""
        pass
    
    @abstractmethod
    async def create_resource(self, resource_type: str, payload: dict) -> dict:
        """Create a resource, return response with _id."""
        pass
    
    @abstractmethod
    async def update_resource(self, resource_type: str, id: str, payload: dict) -> dict:
        """Update a resource."""
        pass
    
    @abstractmethod
    async def delete_resource(self, resource_type: str, id: str) -> None:
        """Delete a resource."""
        pass
```

### Name-to-ID Resolution

```python
class NameToIDResolver:
    def __init__(self, provider: Provider):
        self.provider = provider
        self._cache: dict[str, dict[str, str]] = {}
    
    async def build_lookup(self, resource_type: str) -> dict[str, str]:
        """Build name→ID lookup for a resource type."""
        resources = await self.provider.get_resources(resource_type)
        return {r["name"]: r["_id"] for r in resources}
    
    def resolve(self, resource_type: str, name: str) -> str:
        """Resolve a name to ID."""
        if resource_type not in self._cache:
            raise ValueError(f"Lookup not built for {resource_type}")
        return self._cache[resource_type][name]
```

### Plan Command Flow

```
1. Parse arguments (--fleet, --topology)
2. Load declared state (resolution engine)
3. Connect to Director (provider)
4. Fetch actual state (GET all resources)
5. Calculate diff:
   - In declared, not in actual → CREATE
   - In both, different → UPDATE
   - In actual, not in declared → DELETE
6. Output diff table
```

### Apply Command Flow

```
1. Parse arguments (--auto-approve?)
2. Load declared state
3. If not auto-approve, show plan and confirm
4. Connect to Director
5. Build name→ID lookups
6. Transform payloads (names → IDs)
7. Execute in dependency order:
   a. Create repos
   b. Create routing policies
   c. Create normalization policies
   d. Create enrichment policies
   e. Create processing policies (with resolved IDs)
8. Handle errors (rollback on failure)
```

---

## Dependencies

New dependencies (add to `pyproject.toml`):
```toml
[project.dependencies]
httpx = "^0.28.0"          # HTTP client
anyio = "^4.0.0"           # Async support
```

---

## Testing Strategy

### Unit Tests
- Provider with mocked HTTP responses
- Name-to-ID resolver
- Diff calculation
- Payload transformation

### Integration Tests
- Against test Director instance
- Full workflow: validate → plan → apply
- Error scenarios (network failure, API errors)

### Manual Testing
- Demo configs (Bank A, Bank B)
- Real Director instance (staging)

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Director API unavailable | High | Mock provider for testing |
| Async operation timeout | Medium | Configurable timeout + retry |
| Name collision | Medium | Validation in Phase 1 |
| Network failures | Medium | Retry with exponential backoff |

---

## Success Criteria

- [ ] Director Provider connects and authenticates
- [ ] Plan command shows accurate diff
- [ ] Apply command deploys resources
- [ ] Name-to-ID resolution works correctly
- [ ] Error handling with rollback
- [ ] Integration tests passing
- [ ] Demo configs deploy successfully

---

## Related Documentation

- `40-CLI-WORKFLOW.md` section 5.6 (name-to-ID resolution)
- `50-VALIDATION-SPEC.md` section 6.5 (apply phase)
- `ADRS.md` ADR-008 (name-based validation)
- `API-REFERENCE.md` (Director API endpoints)

---

**Next Step**: Start Week 1 - Create Provider base and Director implementation
