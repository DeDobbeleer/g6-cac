# Spécification des Validations CaC-ConfigMgr

**Version**: 1.0  
**Date**: 2026-02-27  
**Statut**: Implementation Complete  
**Fichier**: `specs/50-VALIDATION-SPEC.md`

---

## Table des matières

1. [Vue d'ensemble](#1-vue-densemble)
2. [Architecture des validations](#2-architecture-des-validations)
3. [Level 1: Syntax Validation](#3-level-1-syntax-validation)
4. [Level 2: Template Resolution](#4-level-2-template-resolution)
5. [Level 3: API Compliance](#5-level-3-api-compliance)
6. [Level 4: Cross-Resource Dependencies](#6-level-4-cross-resource-dependencies)
7. [Exit Codes et Output](#7-exit-codes-et-output)
8. [Références externes](#8-références-externes)
9. [Checklist d'audit](#9-checklist-daudit)

---

## 1. Vue d'ensemble

### 1.1 Objectif

Ce document spécifie exhaustivement **toutes les validations** effectuées par CaC-ConfigMgr avant déploiement sur LogPoint Director.

### 1.2 Prérequis pour validation

| Ressource | Requis pour | Format |
|-----------|-------------|--------|
| **Fichiers YAML** | Syntax, Resolution | `.yaml`, `.yml` |
| **Topology Instance** | Full chain resolution | `instance.yaml` avec `extends` |
| **Fleet** | API Compliance, Dependencies | `fleet.yaml` avec ressources |
| **Templates** | Inheritance chain | Arborescence `templates/` |
| **API Director** | External resources | Connexion (optionnel avec `--offline`) |

### 1.3 4 niveaux de validation

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  NIVEAU 1: SYNTAX VALIDATION                                               │
│  ├── YAML parsing                                                           │
│  ├── Kind recognition (Fleet/Template/Instance)                            │
│  └── Pydantic model loading                                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│  NIVEAU 2: TEMPLATE RESOLUTION                                             │
│  ├── Inheritance chain building                                             │
│  ├── Circular dependency detection                                         │
│  ├── Template existence check                                              │
│  ├── Deep merge with _id matching                                          │
│  └── Variable interpolation (${var}, ${tpl.field})                          │
├─────────────────────────────────────────────────────────────────────────────┤
│  NIVEAU 3: API COMPLIANCE (LogPoint Director)                              │
│  ├── Required fields validation                                            │
│  ├── Type checking (str, int, list, bool)                                  │
│  ├── Pattern matching (^[a-zA-Z0-9_-]+$)                                   │
│  └── API-specific field names (name vs policy_name)                        │
├─────────────────────────────────────────────────────────────────────────────┤
│  NIVEAU 4: CROSS-RESOURCE DEPENDENCIES                                     │
│  ├── ProcessingPolicy → RoutingPolicy (by ID)                              │
│  ├── ProcessingPolicy → NormalizationPolicy (by name)                      │
│  ├── ProcessingPolicy → EnrichmentPolicy (by ID)                           │
│  ├── RoutingPolicy → Repo (catch_all, criteria)                            │
│  └── Deployment order calculation                                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Architecture des validations

### 2.1 Composants

```
src/cac_configmgr/
├── cli/
│   └── main.py                          # Orchestration des 4 niveaux
│                                        # Exit codes: 0, 1, 2, 3
│                                        # Output: Rich table ou JSON
│
├── core/
│   ├── api_validator.py                 # APIFieldValidator
│   │   ├── API_SPECS: définitions des champs par ressource
│   │   ├── _validate_routing_policies()
│   │   ├── _validate_processing_policies()
│   │   ├── _validate_normalization_policies()
│   │   ├── _validate_enrichment_policies()
│   │   ├── _validate_repos()
│   │   └── _validate_dependencies()     # Cross-refs avec index
│   │
│   ├── validator.py                     # ConsistencyValidator
│   │   └── Validation des références RP→Repo
│   │
│   ├── logpoint_dependencies.py         # LogPointDependencyValidator
│   │   ├── DEPENDENCIES: graphe des dépendances
│   │   ├── get_deployment_order()       # Ordre topologique
│   │   └── Validation des contraintes DirSync
│   │
│   ├── engine.py                        # ResolutionEngine
│   │   ├── resolve()                    # Full resolution
│   │   ├── resolve_fleet()              # Fleet only
│   │   └── filter_internal_ids()        # Clean pour API
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

### 2.2 Flux de validation

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

### 3.1 Fichier: `cli/main.py` (lignes 50-90)

#### 3.1.1 YAML Parsing

**Test effectué**:
```python
yaml.safe_load(file)
```

**Erreur générée**:
```
❌ Syntax Errors (N):
  • {file}: mapping values are not allowed here
    in "<string>", line X, column Y
```

**Prérequis**:
- Fichier existe et est lisible
- Contenu est du YAML valide

#### 3.1.2 Kind Recognition

**Kinds reconnus**:
| Kind | Fichier source | Action |
|------|----------------|--------|
| `Fleet` | `fleet.yaml` | `load_fleet()` |
| `ConfigTemplate` | `base.yaml`, `template.yaml` | `load_multi_file_template()` |
| `TopologyInstance` | `instance.yaml` | `load_instance()` |

**Warning si Unknown**:
```
⚠ Unknown kind in {file}: {kind_detected}
```

#### 3.1.3 Pydantic Model Loading

**Modèles utilisés**:
```python
from ..utils import load_yaml, load_instance, load_fleet, load_multi_file_template
```

**Validation Pydantic inclut**:
- Type des champs (str, int, list, bool)
- Champs requis (Field(...))
- Contraintes (min_length, pattern)
- Alias (populate_by_name=True)

---

## 4. Level 2: Template Resolution

### 4.1 Fichier: `core/engine.py`, `core/resolver.py`

### 4.2 Inheritance Chain Building

**Algorithme**:
```python
def build_chain(instance):
    chain = [instance]
    current = instance
    
    while current.metadata.extends:
        parent = load_template(current.metadata.extends)
        chain.insert(0, parent)  # Parent avant
        current = parent
    
    return chain
```

**Profondeur maximale testée**: 6 niveaux (Bank A demo)

### 4.3 Circular Dependency Detection

**Test effectué**:
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

**Erreur générée**:
```
CircularDependencyError: Circular template dependency detected:
  template-a → template-b → template-c → template-a
```

### 4.4 Template Existence Check

**Test effectué**:
```python
parent_path = templates_dir / parent_ref / "template.yaml"
if not parent_path.exists():
    raise TemplateNotFoundError(parent_ref, looked_in=parent_path)
```

**Erreur générée**:
```
TemplateNotFoundError: Template not found: mssp/acme-corp/profiles/enterprise
  Looked in: templates/mssp/acme-corp/profiles/enterprise/template.yaml
```

### 4.5 Deep Merge with _id Matching

**Fichier**: `core/merger.py`

**Règles de merge**:

| Scénario | Action |
|----------|--------|
| Dict simple | Deep merge récursif |
| Liste avec `_id` | Merge by _id, nouveaux ajoutés |
| Liste sans `_id` | Remplacement complet (child gagne) |
| `_action: delete` | Suppression de l'élément |

**Algorithme**:
```python
def merge_list_by_id(parent_list, child_list):
    result = []
    parent_by_id = {item['_id']: item for item in parent_list if '_id' in item}
    
    for child_item in child_list:
        if '_id' not in child_item:
            result.append(child_item)  # Nouvel élément
            continue
            
        parent_item = parent_by_id.get(child_item['_id'])
        if parent_item:
            if child_item.get('_action') == 'delete':
                continue  # Suppression
            merged = deep_merge(parent_item, child_item)
            result.append(merged)
        else:
            result.append(child_item)  # Nouvel élément avec _id
    
    # Ajouter éléments parent non modifiés
    child_ids = {item['_id'] for item in child_list if '_id' in item}
    for parent_item in parent_list:
        if '_id' in parent_item and parent_item['_id'] not in child_ids:
            result.append(parent_item)
    
    return result
```

### 4.6 Ordering Directives

**Directives supportées**:

| Directive | Description | Exemple |
|-----------|-------------|---------|
| `_after` | Insertion après un _id | `_after: base-config` |
| `_before` | Insertion avant un _id | `_before: last-config` |
| `_position` | Position absolue (1-based) | `_position: 1` |
| `_first` | Forcer en premier | `_first: true` |
| `_last` | Forcer en dernier | `_last: true` |

**Application**:
```python
def apply_ordering_directives(resources):
    # Trier par _position
    # Appliquer _first/_after/_before/_last
    # Détecter conflits
    pass
```

### 4.7 Variable Interpolation

**Fichier**: `core/interpolator.py`

**Patterns supportés**:

| Pattern | Description | Exemple |
|---------|-------------|---------|
| `${var}` | Variable globale | `${retention_default}` |
| `${tpl.field}` | Variable d'un template | `${mssp-base.tier_fast}` |
| `${env.VAR}` | Variable d'environnement | `${env.LOGPOINT_TOKEN}` |

**Algorithme**:
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

### 5.1 Fichier: `core/api_validator.py`

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

**Validations effectuées**:

| # | Validation | Exemple valide | Exemple invalide |
|---|------------|----------------|------------------|
| 1 | `policy_name` requis | `rp-default` | (absent) |
| 2 | Pattern match | `rp-default` | `rp default!` |
| 3 | Type string | `"rp-name"` | `123` |
| 4 | `catch_all` requis | `"repo-default"` | (absent) |
| 5 | `catch_all` string | `"repo-default"` | `null` |
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
        "required": False  # Optionnel
    },
    "enrichment_policy": {
        "type": str,
        "required": False  # Optionnel
    }
}
```

**Validations effectuées**:

| # | Validation | Exemple valide | Exemple invalide |
|---|------------|----------------|------------------|
| 1 | `policy_name` requis | `pp-default` | (absent) |
| 2 | Pattern match | `pp-default` | `pp@invalid` |
| 3 | `routing_policy` requis | `"586cc3ed..."` | (absent) |
| 4 | Type string | `"586cc3ed..."` | `123` |
| 5 | `normalization_policy` null autorisé | `null` → `"None"` | - |
| 6 | `enrichment_policy` null autorisé | `null` → `"None"` | - |

**IMPORTANT**: La valeur `null` est acceptée pour les champs optionnels et sera convertie en string `"None"` lors de l'envoi à l'API Director.

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

**Note spéciale**: L'API Director utilise `name` pour NormalizationPolicy, PAS `policy_name` (contrairement à PP, RP, EP).

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

### 5.3 Logique de validation

**Code source** (`api_validator.py`):

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
                    continue  # Sera converti en "None" pour l'API
                
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

### 6.1 Graphe de dépendances

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

### 6.2 Indexation pour validation rapide

**Construction des indexes** (`api_validator.py`):

```python
def _build_indexes(self) -> dict[str, set[str]]:
    indexes = {}
    
    # Index par nom (pour lookup par nom)
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
    
    # Index par ID (pour les références ID)
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

### 6.3 Validations de références

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

### 6.4 Ordre de déploiement

**Fichier**: `core/logpoint_dependencies.py`

**Graphe de dépendances**:

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

**Ordre topologique calculé**:

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

## 7. Exit Codes et Output

### 7.1 Exit Codes (40-CLI-WORKFLOW.md)

| Code | Signification | Condition |
|------|---------------|-----------|
| 0 | Validation successful, no warnings | `errors == 0 AND warnings == 0` |
| 1 | Validation successful, warnings present | `errors == 0 AND warnings > 0` |
| 2 | Validation errors | `errors > 0` |
| 3 | System/connection error | Exception non gérée |

### 7.2 Format Texte (défaut)

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

### 7.3 Format JSON (`--json`)

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

### 7.4 Format avec erreurs

```
❌ Validation Errors (3):

processing_policies:
  • pp-default → routing_policy: References non-existent Routing Policy ID: rp-missing
  • pp-default → normalization_policy: References non-existent Normalization Policy: np-invalid

routing_policies:
  • rp-test → catch_all: References non-existent Repo: repo-deleted
```

---

## 8. Références externes

### 8.1 Documents liés

| Document | Description | Lien |
|----------|-------------|------|
| 40-CLI-WORKFLOW.md | Spécification CLI | [40-CLI-WORKFLOW.md](./40-CLI-WORKFLOW.md) |
| 30-PROCESSING-POLICIES.md | Spécification Processing Policy | [30-PROCESSING-POLICIES.md](./30-PROCESSING-POLICIES.md) |
| 20-TEMPLATE-HIERARCHY.md | Spécification Templates | [20-TEMPLATE-HIERARCHY.md](./20-TEMPLATE-HIERARCHY.md) |
| API-REFERENCE.md | Référence API Director | [API-REFERENCE.md](./API-REFERENCE.md) |
| ADRS.md | Architecture Decisions | [ADRS.md](../ADRS.md) |

### 8.2 Ressources LogPoint Director

| Ressource | API Endpoint | Doc externe |
|-----------|--------------|-------------|
| Routing Policies | `/routingpolicies` | https://docs.logpoint.com/director/apis/routingpolicies |
| Processing Policies | `/processingpolicy` | https://docs.logpoint.com/director/apis/processingpolicy |
| Normalization Policies | `/normalizationpolicy` | https://docs.logpoint.com/director/apis/normalizationpolicy |
| Enrichment Policies | `/enrichmentpolicy` | https://docs.logpoint.com/director/apis/enrichmentpolicy |

---

## 9. Checklist d'audit

### 9.1 Pré-audit

- [ ] Les fichiers YAML sont-ils bien formés ?
- [ ] Les `kind` sont-ils reconnus ?
- [ ] Les modèles Pydantic chargent-ils sans erreur ?

### 9.2 Audit Template

- [ ] La chaîne d'héritage se résout-elle ?
- [ ] Y a-t-il des dépendances circulaires ?
- [ ] Tous les templates parents existent-ils ?
- [ ] Le merge des ressources est-il correct ?
- [ ] Les variables sont-elles interpolées ?

### 9.3 Audit API Compliance

- [ ] Tous les champs requis sont-ils présents ?
- [ ] Les types correspondent-ils aux specs ?
- [ ] Les patterns sont-ils respectés (`^[a-zA-Z0-9_-]+$`) ?
- [ ] Les champs API utilisent-ils les bons noms ?
  - [ ] NP: `name` (pas `policy_name`)
  - [ ] PP/RP/EP: `policy_name`
- [ ] Les valeurs `null` optionnelles sont-elles acceptées ?

### 9.4 Audit Cross-Resource

- [ ] Chaque `routing_policy` (PP) existe-t-il (par ID) ?
- [ ] Chaque `normalization_policy` (PP) existe-t-il (par nom) ?
- [ ] Chaque `enrichment_policy` (PP) existe-t-il (par ID) ?
- [ ] Chaque `catch_all` (RP) existe-t-il (par nom) ?
- [ ] Chaque `criteria[].repo` (RP) existe-t-il (par nom) ?

### 9.5 Post-audit

- [ ] L'ordre de déploiement est-il calculable ?
- [ ] Les exit codes sont-ils respectés ?
- [ ] Le output est-il conforme (texte/JSON) ?

---

## 10. Points de vigilance / Problèmes connus

### 10.1 Différences de nommage API

**IMPORTANT**: Les noms de champs varient selon les ressources :

| Ressource | Champ nom | Exemple |
|-----------|-----------|---------|
| RoutingPolicy | `policy_name` | `rp-default` |
| ProcessingPolicy | `policy_name` | `pp-default` |
| EnrichmentPolicy | `policy_name` | `ep-threatintel` |
| **NormalizationPolicy** | **`name`** (⚠️ pas `policy_name`) | `_logpoint` |

### 10.2 Références par ID vs par nom

| Référence | Type | Exemple |
|-----------|------|---------|
| ProcessingPolicy → RoutingPolicy | **ID** | `"586cc3ed..."` |
| ProcessingPolicy → NormalizationPolicy | **Nom** | `"_logpoint"` |
| ProcessingPolicy → EnrichmentPolicy | **ID** | `"57591a2c..."` |
| RoutingPolicy → Repo | **Nom** | `"repo-default"` |

### 10.3 Valeurs "None"

Pour les champs optionnels de ProcessingPolicy:
- YAML: `normalization_policy: null` ou absent
- API Director: converti en `"None"` (string)
- Validation: `null` est accepté pour champs optionnels

---

## Historique des modifications

| Date | Version | Changement | Auteur |
|------|---------|------------|--------|
| 2026-02-27 | 1.0 | Création initiale | CaC-ConfigMgr Team |

---

**FIN DU DOCUMENT**
