# CaC-ConfigMgr Validation Specification

**Version**: 1.0  
**Date**: 2026-02-27  
**Status**: Implementation Complete  
**File**: `specs/50-VALIDATION-SPEC.md`

---

## Table of Contents

1. [Overview](#1-overview)
2. [Validation Architecture](#2-validation-architecture)
3. [Level 1: Syntax Validation](#3-level-1-syntax-validation)
4. [Level 2: Template Resolution](#4-level-2-template-resolution)
5. [Level 3: API Compliance](#5-level-3-api-compliance)
6. [Level 4: Cross-Resource Dependencies](#6-level-4-cross-resource-dependencies)
7. [Exit Codes and Output](#7-exit-codes-and-output)
8. [External References](#8-external-references)
9. [Audit Checklist](#9-audit-checklist)
10. [Known Issues and Warnings](#10-known-issues-and-warnings)

---

## 1. Overview

### 1.1 Objective

This document exhaustively specifies **all validations** performed by CaC-ConfigMgr before deployment to LogPoint Director.

### 1.2 Validation Prerequisites

| Resource | Required For | Format |
|----------|--------------|--------|
| **YAML Files** | Syntax, Resolution | `.yaml`, `.yml` |
| **Topology Instance** | Full chain resolution | `instance.yaml` with `extends` |
| **Fleet** | API Compliance, Dependencies | `fleet.yaml` with resources |
| **Templates** | Inheritance chain | `templates/` directory tree |
| **Director API** | External resources | Connection (optional with `--offline`) |

### 1.3 4 Validation Levels

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  LEVEL 1: SYNTAX VALIDATION                                                │
│  ├── YAML parsing                                                           │
│  ├── Kind recognition (Fleet/Template/Instance)                            │
│  └── Pydantic model loading                                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│  LEVEL 2: TEMPLATE RESOLUTION                                              │
│  ├── Inheritance chain building                                             │
│  ├── Circular dependency detection                                         │
│  ├── Template existence check                                              │
│  ├── Deep merge with _id matching                                          │
│  └── Variable interpolation (${var}, ${tpl.field})                          │
├─────────────────────────────────────────────────────────────────────────────┤
│  LEVEL 3: API COMPLIANCE (LogPoint Director)                               │
│  ├── Required fields validation                                            │
│  ├── Type checking (str, int, list, bool)                                  │
│  ├── Pattern matching (^[a-zA-Z0-9_-]+$)                                   │
│  └── API-specific field names (name vs policy_name)                        │
├─────────────────────────────────────────────────────────────────────────────┤
│  LEVEL 4: CROSS-RESOURCE DEPENDENCIES                                      │
│  ├── ProcessingPolicy → RoutingPolicy (by ID)                              │
│  ├── ProcessingPolicy → NormalizationPolicy (by name)                      │
│  ├── ProcessingPolicy → EnrichmentPolicy (by ID)                           │
│  ├── RoutingPolicy → Repo (catch_all, criteria)                            │
│  └── Deployment order calculation                                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Validation Architecture

### 2.1 Components

```
src/cac_configmgr/
├── cli/
│   └── main.py                          # Orchestrates all 4 levels
│                                        # Exit codes: 0, 1, 2, 3
│                                        # Output: Rich table or JSON
│
├── core/
│   ├── api_validator.py                 # APIFieldValidator
│   │   ├── API_SPECS: field definitions per resource
│   │   ├── _validate_routing_policies()
│   │   ├── _validate_processing_policies()
│   │   ├── _validate_normalization_policies()
│   │   ├── _validate_enrichment_policies()
│   │   ├── _validate_repos()
│   │   └── _validate_dependencies()     # Cross-refs with indexes
│   │
│   ├── validator.py                     # ConsistencyValidator
│   │   └── Validates RP→Repo references
│   │
│   ├── logpoint_dependencies.py         # LogPointDependencyValidator
│   │   ├── DEPENDENCIES: dependency graph
│   │   ├── get_deployment_order()       # Topological order
│   │   └── Validates DirSync constraints
│   │
│   ├── engine.py                        # ResolutionEngine
│   │   ├── resolve()                    # Full resolution
│   │   ├── resolve_fleet()              # Fleet only
│   │   └── filter_internal_ids()        # Clean for API
│   │
│   ├── resolver.py                      # TemplateResolver
│   │   ├── resolve()                    # Build inheritance chain
│   │   └── CircularDependencyError
│   │
│   ├── merger.py                        # Resource merging
│   │   ├── merge_resources()
│   │   ├── merge_list_by_id()
│   │   └── apply_ordering_directives()
│   │
│   └── interpolator.py                  # Variable interpolation
│       ├── Interpolator
│       └── merge_variables()
│
└── models/                              # Pydantic models
    ├── fleet.py                         # Fleet, Node, Tags
    ├── template.py                      # ConfigTemplate, Metadata
    ├── routing.py                       # RoutingPolicy, RoutingCriteria
    ├── processing.py                    # ProcessingPolicy
    ├── normalization.py                 # NormalizationPolicy
    ├── enrichment.py                    # EnrichmentPolicy, EnrichmentSpecification
    └── repos.py                         # Repo, HiddenRepoPath
```

### 2.2 Validation Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Level 1   │────→│   Level 2   │────→│   Level 3   │────→│   Level 4   │
│   Syntax    │     │ Resolution  │     │ API Comp.   │     │  Cross-Ref  │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
      │                    │                   │                   │
      ▼                    ▼                   ▼                   ▼
 YAML parse           Template           Field check         Reference
 Kind check           chain              Type check          validation
 Pydantic             merge              Pattern             Index lookup
                      interpolate        Required            Deploy order
```

---

## 3. Level 1: Syntax Validation

### 3.1 File: `cli/main.py` (lines 50-90)

#### 3.1.1 YAML Parsing

**Test performed**:
```python
yaml.safe_load(file)
```

**Error generated**:
```
❌ Syntax Errors (N):
  • {file}: mapping values are not allowed here
    in "<string>", line X, column Y
```

**Prerequisites**:
- File exists and is readable
- Content is valid YAML

#### 3.1.2 Kind Recognition

**Recognized kinds**:
| Kind | Source File | Action |
|------|-------------|--------|
| `Fleet` | `fleet.yaml` | `load_fleet()` |
| `ConfigTemplate` | `base.yaml`, `template.yaml` | `load_multi_file_template()` |
| `TopologyInstance` | `instance.yaml` | `load_instance()` |

**Warning if Unknown**:
```
⚠ Unknown kind in {file}: {kind_detected}
```

#### 3.1.3 Pydantic Model Loading

**Models used**:
```python
from ..utils import load_yaml, load_instance, load_fleet, load_multi_file_template
```

**Pydantic validation includes**:
- Field types (str, int, list, bool)
- Required fields (Field(...))
- Constraints (min_length, pattern)
- Aliases (populate_by_name=True)

---

## 4. Level 2: Template Resolution

### 4.1 Files: `core/engine.py`, `core/resolver.py`

### 4.2 Inheritance Chain Building

**Algorithm**:
```python
def build_chain(instance):
    chain = [instance]
    current = instance
    
    while current.metadata.extends:
        parent = load_template(current.metadata.extends)
        chain.insert(0, parent)  # Parent first
        current = parent
    
    return chain
```

**Maximum tested depth**: 6 levels (Bank A demo)

### 4.3 Circular Dependency Detection

**Test performed**:
```python
visited = set()
current_path = []

def detect_circular(template):
    if template.id in current_path:
        raise CircularDependencyError(current_path + [template.id])
    if template.id in visited:
        return
    
    current_path.append(template.id)
    if template.extends:
        detect_circular(load_template(template.extends))
    current_path.pop()
    visited.add(template.id)
```

**Error generated**:
```
CircularDependencyError: Circular template dependency detected:
  template-a → template-b → template-c → template-a
```

### 4.4 Template Existence Check

**Test performed**:
```python
parent_path = templates_dir / parent_ref / "template.yaml"
if not parent_path.exists():
    raise TemplateNotFoundError(parent_ref, looked_in=parent_path)
```

**Error generated**:
```
TemplateNotFoundError: Template not found: mssp/acme-corp/profiles/enterprise
  Looked in: templates/mssp/acme-corp/profiles/enterprise/template.yaml
```

### 4.5 Deep Merge with _id Matching

**File**: `core/merger.py`

**Merge rules**:

| Scenario | Action |
|----------|--------|
| Simple dict | Recursive deep merge |
| List with `_id` | Merge by _id, new items added |
| List without `_id` | Complete replacement (child wins) |
| `_action: delete` | Element removal |

**Algorithm**:
```python
def merge_list_by_id(parent_list, child_list):
    result = []
    parent_by_id = {item['_id']: item for item in parent_list if '_id' in item}
    
    for child_item in child_list:
        if '_id' not in child_item:
            result.append(child_item)  # New element
            continue
            
        parent_item = parent_by_id.get(child_item['_id'])
        if parent_item:
            if child_item.get('_action') == 'delete':
                continue  # Deletion
            merged = deep_merge(parent_item, child_item)
            result.append(merged)
        else:
            result.append(child_item)  # New element with _id
    
    # Add unmodified parent elements
    child_ids = {item['_id'] for item in child_list if '_id' in item}
    for parent_item in parent_list:
        if '_id' in parent_item and parent_item['_id'] not in child_ids:
            result.append(parent_item)
    
    return result
```

### 4.6 Ordering Directives

**Supported directives**:

| Directive | Description | Example |
|-----------|-------------|---------|
| `_after` | Insert after an _id | `_after: base-config` |
| `_before` | Insert before an _id | `_before: last-config` |
| `_position` | Absolute position (1-based) | `_position: 1` |
| `_first` | Force first position | `_first: true` |
| `_last` | Force last position | `_last: true` |

**Application**:
```python
def apply_ordering_directives(resources):
    # Sort by _position
    # Apply _first/_after/_before/_last
    # Detect conflicts
    pass
```

### 4.7 Variable Interpolation

**File**: `core/interpolator.py`

**Supported patterns**:

| Pattern | Description | Example |
|---------|-------------|---------|
| `${var}` | Global variable | `${retention_default}` |
| `${tpl.field}` | Template variable | `${mssp-base.tier_fast}` |
| `${env.VAR}` | Environment variable | `${env.LOGPOINT_TOKEN}` |

**Algorithm**:
```python
class Interpolator:
    def __init__(self, variables):
        self.variables = variables
        self.pattern = re.compile(r'\$\{(\w+)(?:\.(\w+))?\}')
    
    def interpolate(self, obj):
        if isinstance(obj, str):
            return self._interpolate_string(obj)
        elif isinstance(obj, dict):
            return {k: self.interpolate(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self.interpolate(item) for item in obj]
        return obj
    
    def _interpolate_string(self, s):
        def replace(match):
            var_name = match.group(1)
            field = match.group(2)
            
            if var_name in self.variables:
                value = self.variables[var_name]
                if field and isinstance(value, dict):
                    return str(value.get(field, match.group(0)))
                return str(value)
            return match.group(0)  # Keep original if not found
        
        return self.pattern.sub(replace, s)
```

---

## 5. Level 3: API Compliance

### 5.1 File: `core/api_validator.py`

### 5.2 API Specifications

#### 5.2.1 Routing Policy

```python
"routing_policy": {
    "policy_name": {
        "type": str,
        "required": True,
        "pattern": r"^[a-zA-Z0-9_-]+$"
    },
    "catch_all": {
        "type": str,
        "required": True
    },
    "routing_criteria": {
        "type": list,
        "required": True
    }
}
```

**Validations performed**:

| # | Validation | Valid Example | Invalid Example |
|---|------------|---------------|-----------------|
| 1 | `policy_name` required | `rp-default` | (missing) |
| 2 | Pattern match | `rp-default` | `rp default!` |
| 3 | String type | `"rp-name"` | `123` |
| 4 | `catch_all` required | `"repo-default"` | (missing) |
| 5 | `catch_all` string | `"repo-default" | `null` |
| 6 | `routing_criteria` list | `[{...}]` | `"invalid"` |

#### 5.2.2 Processing Policy

```python
"processing_policy": {
    "policy_name": {
        "type": str,
        "required": True,
        "pattern": r"^[a-zA-Z0-9_-]+$"
    },
    "routing_policy": {
        "type": str,
        "required": True
    },
    "normalization_policy": {
        "type": str,
        "required": False  # Optional
    },
    "enrichment_policy": {
        "type": str,
        "required": False  # Optional
    }
}
```

**Validations performed**:

| # | Validation | Valid Example | Invalid Example |
|---|------------|---------------|-----------------|
| 1 | `policy_name` required | `pp-default` | (missing) |
| 2 | Pattern match | `pp-default` | `pp@invalid` |
| 3 | `routing_policy` required | `"586cc3ed..."` | (missing) |
| 4 | String type | `"586cc3ed..."` | `123` |
| 5 | `normalization_policy` null allowed | `null` → `"None"` | - |
| 6 | `enrichment_policy` null allowed | `null` → `"None"` | - |

**IMPORTANT**: `null` value is accepted for optional fields and will be converted to string `"None"` when sending to Director API.

#### 5.2.3 Normalization Policy

```python
"normalization_policy": {
    "name": {
        "type": str,
        "required": True,
        "pattern": r"^[a-zA-Z0-9_-]+$"
    },
    "normalization_packages": {
        "type": list,
        "required": False
    },
    "compiled_normalizer": {
        "type": str,
        "required": False
    }
}
```

**Special note**: Director API uses `name` for NormalizationPolicy, NOT `policy_name` (unlike PP, RP, EP).

#### 5.2.4 Enrichment Policy

```python
"enrichment_policy": {
    "name": {
        "type": str,
        "required": True,
        "pattern": r"^[a-zA-Z0-9_-]+$"
    },
    "specifications": {
        "type": list,
        "required": True
    }
}

"enrichment_specification": {
    "source": {
        "type": str,
        "required": True
    },
    "criteria": {
        "type": list,
        "required": True
    },
    "rules": {
        "type": list,
        "required": False
    }
}
```

#### 5.2.5 Repository

```python
"repo": {
    "name": {
        "type": str,
        "required": True,
        "pattern": r"^[a-zA-Z0-9_-]+$"
    },
    "hiddenrepopath": {
        "type": list,
        "required": False
    }
}

"hiddenrepopath": {
    "_id": {
        "type": str,
        "required": True
    },
    "path": {
        "type": str,
        "required": True
    },
    "retention": {
        "type": int,
        "required": True
    }
}
```

### 5.3 Validation Logic

**Source code** (`api_validator.py`):

```python
def _validate_resource_type(self, resources, spec_name, resource_type):
    spec = self.API_SPECS[spec_name]
    
    for resource in resources:
        resource_name = resource.get("name") or resource.get("policy_name", "unknown")
        
        for field, config in spec.items():
            # 1. Check required
            if config["required"] and field not in resource:
                self.errors.append(ValidationError(
                    resource_type=resource_type,
                    resource_name=resource_name,
                    field=field,
                    message=f"Required field '{field}' is missing",
                    severity="ERROR"
                ))
            
            elif field in resource:
                value = resource[field]
                
                # 2. Allow None for optional fields
                if value is None and not config.get("required", False):
                    continue  # Will be converted to "None" for API
                
                # 3. Type checking
                expected_type = config["type"]
                if expected_type == str and not isinstance(value, str):
                    self.errors.append(...)
                elif expected_type == int and not isinstance(value, int):
                    self.errors.append(...)
                elif expected_type == list and not isinstance(value, list):
                    self.errors.append(...)
                
                # 4. Pattern checking
                if "pattern" in config and isinstance(value, str):
                    if not re.match(config["pattern"], value):
                        self.errors.append(...)
```

---

## 6. Level 4: Cross-Resource Dependencies

### 6.1 Dependency Graph

```
                           Repos
                            │
                            ▼
                   ┌──────────────────┐
                   │  RoutingPolicy   │◄── catch_all: repo_name
                   │                  │◄── criteria[].repo: repo_name
                   └────────┬─────────┘
                            │
                            ▼
        ┌───────────────────────────────────────────┐
        │         ProcessingPolicy                  │
        │  ├── routing_policy: RP_id                │
        │  ├── normalization_policy: NP_name        │
        │  └── enrichment_policy: EP_id             │
        └───────────────────────────────────────────┘
                            │
                            ▼
                      Devices (future)
                            │
                            ▼
                 Syslog Collectors (future)
```

### 6.2 Indexing for Fast Validation

**Index construction** (`api_validator.py`):

```python
def _build_indexes(self) -> dict[str, set[str]]:
    indexes = {}
    
    # Index by name (for name lookup)
    name_fields = {
        "repos": "name",
        "routing_policies": "policy_name",
        "processing_policies": "policy_name",
        "normalization_policies": "name",
        "enrichment_policies": "name",
    }
    
    for resource_type, name_field in name_fields.items():
        indexes[resource_type] = {
            item.get(name_field) 
            for item in self.resources.get(resource_type, [])
            if item.get(name_field)
        }
    
    # Index by ID (for ID references)
    indexes["routing_policies_by_id"] = {
        item.get("id") or item.get("_id")
        for item in self.resources.get("routing_policies", [])
    }
    
    indexes["enrichment_policies_by_id"] = {
        item.get("id") or item.get("_id")
        for item in self.resources.get("enrichment_policies", [])
    }
    
    return indexes
```

### 6.3 Reference Validations

#### 6.3.1 ProcessingPolicy → RoutingPolicy (by ID)

```python
for pp in resources.get("processing_policies", []):
    rp_ref = pp.get("routing_policy")
    if rp_ref and rp_ref != "None":
        if rp_ref not in indexes["routing_policies_by_id"]:
            errors.append(ValidationError(
                resource_type="processing_policies",
                resource_name=pp["policy_name"],
                field="routing_policy",
                message=f"References non-existent Routing Policy ID: {rp_ref}",
                severity="ERROR"
            ))
```

#### 6.3.2 ProcessingPolicy → NormalizationPolicy (by name)

```python
np_ref = pp.get("normalization_policy")
if np_ref and np_ref != "None":
    if np_ref not in indexes["normalization_policies"]:
        errors.append(ValidationError(
            resource_type="processing_policies",
            resource_name=pp["policy_name"],
            field="normalization_policy",
            message=f"References non-existent Normalization Policy: {np_ref}",
            severity="ERROR"
        ))
```

#### 6.3.3 ProcessingPolicy → EnrichmentPolicy (by ID)

```python
ep_ref = pp.get("enrichment_policy")
if ep_ref and ep_ref != "None":
    if ep_ref not in indexes["enrichment_policies_by_id"]:
        errors.append(ValidationError(
            resource_type="processing_policies",
            resource_name=pp["policy_name"],
            field="enrichment_policy",
            message=f"References non-existent Enrichment Policy ID: {ep_ref}",
            severity="ERROR"
        ))
```

#### 6.3.4 RoutingPolicy → Repo (catch_all)

```python
for rp in resources.get("routing_policies", []):
    catch_all = rp.get("catch_all")
    if catch_all and catch_all not in indexes["repos"]:
        errors.append(ValidationError(
            resource_type="routing_policies",
            resource_name=rp["policy_name"],
            field="catch_all",
            message=f"References non-existent Repo: {catch_all}",
            severity="ERROR"
        ))
```

#### 6.3.5 RoutingPolicy → Repo (criteria)

```python
for criterion in rp.get("routing_criteria", []):
    repo_ref = criterion.get("repo")
    if repo_ref and repo_ref not in indexes["repos"]:
        errors.append(ValidationError(
            resource_type="routing_policies",
            resource_name=rp["policy_name"],
            field="routing_criteria.repo",
            message=f"Criterion references non-existent Repo: {repo_ref}",
            severity="ERROR"
        ))
```

### 6.4 Deployment Order

**File**: `core/logpoint_dependencies.py`

**Dependency graph**:

```python
DEPENDENCIES = {
    "routing_policies": [
        ("catch_all", "repos"),
        ("routing_criteria.*.repo", "repos"),
    ],
    "processing_policies": [
        ("routing_policy", "routing_policies"),
        ("normalization_policy", "normalization_policies"),
        ("enrichment_policy", "enrichment_policies"),
    ],
    # ... etc
}
```

**Calculated topological order**:

```python
def get_deployment_order(self) -> list[str]:
    """Return resources in deployment order (dependencies first)."""
    # Topological sort based on DEPENDENCIES graph
    order = [
        "repos",                    # 1. No dependencies
        "device_groups",           # 2. No dependencies  
        "normalization_policies",  # 3. External packages
        "enrichment_sources",      # 4. External sources
        "routing_policies",        # 5. Depends on repos
        "enrichment_policies",     # 6. Depends on sources
        "processing_policies",     # 7. Depends on RP+NP+EP
        "devices",                 # 8. Depends on PP+DG
        "syslog_collectors",       # 9. Depends on devices
        "alert_rules",            # 10. Depends on repos
    ]
    return order
```

---

## 7. Exit Codes and Output

### 7.1 Exit Codes (40-CLI-WORKFLOW.md)

| Code | Meaning | Condition |
|------|---------|-----------|
| 0 | Validation successful, no warnings | `errors == 0 AND warnings == 0` |
| 1 | Validation successful, warnings present | `errors == 0 AND warnings > 0` |
| 2 | Validation errors | `errors > 0` |
| 3 | System/connection error | Unhandled exception |

### 7.2 Text Format (default)

```
Validating demo-configs/instances/banks/bank-a/prod...

✓ Syntax validation passed (2 files)

Resolving template chain...
  → Resolved 27 resources

Validating API compliance...
  → API compliance OK

Validating dependencies...
  → All dependencies valid


                  Validation Summary                   
╭───────────────────┬────────┬────────────────────────╮
│ Level             │ Status │ Details                │
├───────────────────┼────────┼────────────────────────┤
│ 1. Syntax         │ ✓ OK   │ 2 files parsed         │
│ 2. API Compliance │ ✓ OK   │ 27 resources validated │
│ 3. Dependencies   │ ✓ OK   │ All references valid   │
╰───────────────────┴────────┴────────────────────────╯

✓ All validations passed!
```

### 7.3 JSON Format (`--json`)

```json
{
  "valid": true,
  "summary": {
    "syntax_files": 2,
    "resolved_resources": 27,
    "errors": 0,
    "warnings": 0
  },
  "errors": [],
  "warnings": []
}
```

### 7.4 Format with Errors

```
❌ Validation Errors (3):

processing_policies:
  • pp-default → routing_policy: References non-existent Routing Policy ID: rp-missing
  • pp-default → normalization_policy: References non-existent Normalization Policy: np-invalid

routing_policies:
  • rp-test → catch_all: References non-existent Repo: repo-deleted
```

---

## 8. External References

### 8.1 Related Documents

| Document | Description | Link |
|----------|-------------|------|
| 40-CLI-WORKFLOW.md | CLI Specification | [40-CLI-WORKFLOW.md](./40-CLI-WORKFLOW.md) |
| 30-PROCESSING-POLICIES.md | Processing Policy Spec | [30-PROCESSING-POLICIES.md](./30-PROCESSING-POLICIES.md) |
| 20-TEMPLATE-HIERARCHY.md | Template Spec | [20-TEMPLATE-HIERARCHY.md](./20-TEMPLATE-HIERARCHY.md) |
| API-REFERENCE.md | Director API Reference | [API-REFERENCE.md](./API-REFERENCE.md) |
| ADRS.md | Architecture Decisions | [ADRS.md](../ADRS.md) |

### 8.2 LogPoint Director Resources

| Resource | API Endpoint | External Doc |
|----------|--------------|--------------|
| Routing Policies | `/routingpolicies` | https://docs.logpoint.com/director/apis/routingpolicies |
| Processing Policies | `/processingpolicy` | https://docs.logpoint.com/director/apis/processingpolicy |
| Normalization Policies | `/normalizationpolicy` | https://docs.logpoint.com/director/apis/normalizationpolicy |
| Enrichment Policies | `/enrichmentpolicy` | https://docs.logpoint.com/director/apis/enrichmentpolicy |

---

## 9. Audit Checklist

### 9.1 Pre-Audit

- [ ] Are YAML files well-formed?
- [ ] Are `kind` values recognized?
- [ ] Do Pydantic models load without error?

### 9.2 Template Audit

- [ ] Does the inheritance chain resolve?
- [ ] Are there circular dependencies?
- [ ] Do all parent templates exist?
- [ ] Is resource merging correct?
- [ ] Are variables interpolated?

### 9.3 API Compliance Audit

- [ ] Are all required fields present?
- [ ] Do types match specs?
- [ ] Are patterns respected (`^[a-zA-Z0-9_-]+$`)?
- [ ] Are API field names correct?
  - [ ] NP: `name` (not `policy_name`)
  - [ ] PP/RP/EP: `policy_name`
- [ ] Are optional `null` values accepted?

### 9.4 Cross-Resource Audit

- [ ] Does each `routing_policy` (PP) exist (by ID)?
- [ ] Does each `normalization_policy` (PP) exist (by name)?
- [ ] Does each `enrichment_policy` (PP) exist (by ID)?
- [ ] Does each `catch_all` (RP) exist (by name)?
- [ ] Does each `criteria[].repo` (RP) exist (by name)?

### 9.5 Post-Audit

- [ ] Is deployment order calculable?
- [ ] Are exit codes respected?
- [ ] Is output format compliant (text/JSON)?

---

## 10. Known Issues and Warnings

### 10.1 API Naming Differences

**IMPORTANT**: Field names vary by resource:

| Resource | Name Field | Example |
|----------|------------|---------|
| RoutingPolicy | `policy_name` | `rp-default` |
| ProcessingPolicy | `policy_name` | `pp-default` |
| EnrichmentPolicy | `policy_name` | `ep-threatintel` |
| **NormalizationPolicy** | **`name`** (⚠️ not `policy_name`) | `_logpoint` |

### 10.2 References by ID vs by Name

| Reference | Type | Example |
|-----------|------|---------|
| ProcessingPolicy → RoutingPolicy | **ID** | `"586cc3ed..."` |
| ProcessingPolicy → NormalizationPolicy | **Name** | `"_logpoint"` |
| ProcessingPolicy → EnrichmentPolicy | **ID** | `"57591a2c..."` |
| RoutingPolicy → Repo | **Name** | `"repo-default"` |

### 10.3 "None" Values

For ProcessingPolicy optional fields:
- YAML: `normalization_policy: null` or absent
- Director API: converted to `"None"` (string)
- Validation: `null` is accepted for optional fields

---

## Change History

| Date | Version | Change | Author |
|------|---------|--------|--------|
| 2026-02-27 | 1.0 | Initial creation | CaC-ConfigMgr Team |

---

**END OF DOCUMENT**
