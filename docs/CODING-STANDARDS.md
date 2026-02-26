# CaC-ConfigMgr CaC - Coding Standards

**Status**: 🚧 Draft - To be completed as project progresses  
**Language**: Python 3.10+  
**Applies to**: All source code, tests, documentation

---

## 1. Code Organization

### Directory Structure
```
cac-configmgr/
├── core/                   # Core business logic
│   ├── models/            # Pydantic models
│   ├── engine/            # Plan/Apply/Drift logic
│   ├── fleet/             # Fleet inventory management
│   └── topology/          # Configuration management
├── providers/             # API connectors
│   ├── base.py           # Abstract provider interface
│   ├── director/         # Director API implementation
│   └── direct/           # Direct SIEM API (future)
├── cli/                   # Command line interface
├── gitops/               # GitOps integration (future)
└── utils/                # Shared utilities

tests/
├── unit/                 # Unit tests
├── integration/          # Integration tests
└── fixtures/             # Test data

docs/
├── specs/               # Technical specifications
└── api/                 # API documentation
```

### Module Naming
- **Lowercase** with underscores: `fleet_loader.py`, `plan_engine.py`
- **Singular** for modules: `model.py` not `models.py` (except top-level packages)
- **Action verbs** for scripts: `validate.py`, `apply.py`

---

## 2. Naming Conventions

### Python Code
| Element | Convention | Example |
|---------|-----------|---------|
| Classes | PascalCase | `FleetInventory`, `DataNodeCluster` |
| Functions | snake_case | `load_fleet()`, `validate_topology()` |
| Variables | snake_case | `cluster_ref`, `node_count` |
| Constants | UPPER_SNAKE_CASE | `DEFAULT_TIMEOUT`, `MAX_RETRIES` |
| Private | _leading_underscore | `_internal_helper()` |
| Abstract | Leading `A` or `Abstract` | `AProvider`, `AbstractConnector` |

### File Naming
| Type | Pattern | Example |
|------|---------|---------|
| Source | `snake_case.py` | `fleet_loader.py` |
| Tests | `test_*.py` | `test_fleet_loader.py` |
| Fixtures | `*.yaml` | `sample_fleet.yaml` |

### YAML/JSON Keys
- **camelCase** for API-facing data (LogPoint convention)
- **snake_case** for internal configuration
- **kebab-case** for CLI flags: `--cluster-ref`, `--dry-run`

---

## 3. Type Hints

### Mandatory
- **All function parameters**: `def load_fleet(path: Path) -> Fleet:`
- **All return types**: `def validate() -> ValidationResult:`
- **All class attributes**: `name: str`, `nodes: list[DataNode]`

### Imports
```python
from __future__ import annotations  # First line in every file

from typing import Optional, Union  # Avoid, use | instead
from pathlib import Path

# Prefer modern syntax
name: str | None  # Instead of Optional[str]
value: int | str  # Instead of Union[int, str]
```

### Pydantic Models
```python
from pydantic import BaseModel, Field

class DataNode(BaseModel):
    name: str = Field(..., description="Unique node identifier")
    logpoint_id: str = Field(..., pattern=r"^lp-[a-z0-9-]+$")
    cluster_ref: str | None = Field(None, description="Optional cluster membership")
    
    class Config:
        frozen = True  # Immutable by default
```

---

## 4. Documentation

### Docstrings
**Google Style** for all public APIs.

### Comments
- **Why**, not **what**: `# Retry needed because Director API is async`
- **TODO format**: `# TODO(username): description [ISSUE-123]`
- **No commented code**: Delete it, Git remembers

### README & Specs
- **English only** (as per project requirements)
- **Markdown format**

---

## 5. Error Handling

### Exception Hierarchy
```python
class CaC-ConfigMgrError(Exception):
    """Base exception for all CaC-ConfigMgr errors."""
    pass

class ValidationError(CaC-ConfigMgrError):
    """Configuration validation failed."""
    pass
```

### Patterns
- **Fail fast**: Validate inputs at function entry
- **Context managers**: Use `with` for resources
- **No bare except**: Always catch specific exceptions

---

## 6. Testing

### Framework
- **pytest** for all tests
- **pytest-asyncio** for async tests
- **pytest-cov** for coverage (target: 80%+)

---

## 7. Logging

### Configuration
```python
import logging
logger = logging.getLogger(__name__)
```

### Levels
- **DEBUG**: Detailed diagnostic
- **INFO**: Normal operations
- **WARNING**: Recoverable issues
- **ERROR**: Failures
- **CRITICAL**: System-wide failures

---

## 8. CLI Design

### Framework
- **Typer** for all CLI commands
- **Rich** for output formatting

### Principles
- Verb-noun structure: `cac-configmgr validate fleet.yaml`
- Consistent flags: `--fleet`, `--topology`, `--dry-run`
- Clear error messages with suggestions
