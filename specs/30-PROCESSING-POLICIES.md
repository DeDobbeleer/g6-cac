# Processing Policies Specification

**Version**: 1.0  
**Status**: 🚧 Draft  
**Date**: 2026-02-26  
**Author**: CaC-ConfigMgr Product Team  

---

## 1. Executive Summary

Ce document spécifie les **Processing Policies** (PP) et leur place dans le pipeline de traitement LogPoint :

```
Log Sources → Routing → Repos → Normalization → Enrichment → Processing → Storage/Alerts
                ↓                                              ↓
          (Routing Policies)                          (Processing Policies)
```

Les Processing Policies permettent de définir des règles métier appliquées **après** enrichment :
- **Field Extraction**: Extraire des champs calculés
- **Event Filtering**: Filtrer certains événements avant stockage
- **Aggregation**: Agréger des événements (windowing)
- **Alert Triggering**: Déclencher des alertes internes (non-correlation)

---

## 2. Pipeline LogPoint Overview

### 2.1 Stages du Pipeline

| Stage | Input | Output | Configurable via CaC |
|-------|-------|--------|---------------------|
| **Routing** | Logs bruts | Destination repo | ✅ Oui (Routing Policies) |
| **Normalization** | Logs bruts | Logs parsés (champs normalisés) | ❌ Non (packages read-only) |
| **Enrichment** | Logs parsés | Logs enrichis (contexte ajouté) | ⚠️ Référence uniquement |
| **Processing** | Logs enrichis | Logs traités / Actions | ✅ Oui (Processing Policies) |
| **Storage** | Logs traités | Stockage persistant | (Défini par Repo) |

### 2.2 Read-Only vs Configurable

| Élément | Type | Contrôle CaC |
|---------|------|--------------|
| Normalization Packages | Système | Référence (`name` uniquement) |
| Compiled Normalizers | Système | Référence (`name` uniquement) |
| Enrichment Sources | Système/UI | Référence (`name` uniquement) |
| **Processing Policies** | **Configurable** | **Création/Modification complète** |

---

## 3. Processing Policy Structure

### 3.1 Définition YAML

```yaml
# templates/mssp/acme-corp/base/processing-policies.yaml
apiVersion: cac-configmgr.io/v1
kind: ConfigTemplate
metadata:
  name: acme-base
  extends: logpoint/golden-base
  
spec:
  processingPolicies:
    - policy_name: pp-windows-security
      _id: pp-windows-sec
      
      # Conditions d'application
      matchCriteria:
        - type: KeyPresentValueMatches
          key: device_product
          value: Windows
        - type: KeyPresentValueMatches
          key: category
          value: Security
      
      # Actions à exécuter
      actions:
        # Action 1: Extraire le niveau de risque
        - type: ExtractField
          targetField: risk_score
          expression: "severity * 10 + if(is_admin, 50, 0)"
          
        # Action 2: Taguer les événements haute criticité
        - type: AddTag
          condition: "risk_score >= 80"
          tags: ["critical", "immediate-review"]
          
        # Action 3: Dropper les events de basse valeur
        - type: Filter
          condition: "event_id in [4624, 4625] and source_ip == '127.0.0.1'"
          action: discard
```

### 3.2 Champs Principaux

| Champ | Type | Description | Requis |
|-------|------|-------------|--------|
| `policy_name` | string | Nom unique de la policy | ✅ Oui |
| `_id` | string | ID template pour héritage | ✅ Oui |
| `matchCriteria` | array | Conditions pour matcher les logs | ❌ Non (défaut: all) |
| `actions` | array | Actions à exécuter | ✅ Oui (min: 1) |
| `enabled` | boolean | Actif/inactif | ❌ Non (défaut: true) |
| `priority` | integer | Ordre d'évaluation | ❌ Non (défaut: 100) |

---

## 4. Match Criteria

### 4.1 Types de Critères

| Type | Description | Paramètres |
|------|-------------|------------|
| `KeyPresent` | Clé existe | `key` |
| `KeyPresentValueMatches` | Clé = valeur | `key`, `value` |
| `KeyPresentValueContains` | Clé contient valeur | `key`, `value` |
| `KeyPresentValueRegex` | Clé match regex | `key`, `pattern` |
| `LogicalAnd` | Tous les critères | `criteria: []` |
| `LogicalOr` | Au moins un | `criteria: []` |
| `LogicalNot` | Négation | `criteria` |

### 4.2 Exemple Complexe

```yaml
matchCriteria:
  - type: LogicalAnd
    criteria:
      - type: KeyPresentValueMatches
        key: device_product
        value: Windows
      - type: KeyPresentValueRegex
        key: event_id
        pattern: "^(4624|4625|4648|4672)$"
      - type: LogicalNot
        criteria:
          - type: KeyPresentValueMatches
            key: source_ip
            value: "127.0.0.1"
```

---

## 5. Actions

### 5.1 Types d'Actions

#### ExtractField

Extrait un champ calculé à partir d'expressions.

```yaml
- type: ExtractField
  targetField: risk_score
  expression: "severity * 10"
  dataType: integer        # integer, string, boolean, float
  overwrite: false         # true = écraser si existe
```

**Fonctions disponibles:**
- `if(condition, true_val, false_val)` - Conditionnel
- `coalesce(field1, field2, default)` - Premier non-null
- `length(field)` - Longueur chaîne/array
- `contains(field, value)` - Contient valeur
- `regex_extract(field, pattern, group)` - Extraction regex

#### AddTag

Ajoute des tags métadonnés aux événements.

```yaml
- type: AddTag
  condition: "severity >= 7"    # Optionnel
  tags: ["high-risk", "escalated"]
```

#### RemoveTag

Retire des tags.

```yaml
- type: RemoveTag
  tags: ["temp-flag", "debug"]
```

#### Filter

Filtre (drop) des événements.

```yaml
- type: Filter
  condition: "event_id == 4688 and command_line contains 'powershell.exe -enc'"
  action: discard           # discard | mark_only
  reason: "suspicious_powershell"
```

**Note**: `mark_only` garde l'event mais ajoute `_dropped: true` pour traçabilité.

#### SetField

Modifie un champ existant.

```yaml
- type: SetField
  field: normalized_user
  value: "{{domain}}\\{{username}}"
  condition: "username != null"
```

#### RouteTo

Redirige vers un repo différent (rare, pour cas spéciaux).

```yaml
- type: RouteTo
  repo: repo-secu-critical
  condition: "risk_score >= 90"
```

#### Aggregate

Agrégation window-based (alertes de seuil).

```yaml
- type: Aggregate
  window: 5m              # 5 minutes
  groupBy: [source_ip, username]
  having: "count >= 10"
  then:
    - type: AddTag
      tags: ["brute-force-detected"]
    - type: SetField
      field: aggregate_count
      value: "{{count}}"
```

---

## 6. Héritage et Template IDs

### 6.1 Même Mécanisme que Routing Policies

```yaml
# Parent: logpoint/golden-base/processing-policies.yaml
spec:
  processingPolicies:
    - policy_name: pp-windows-base
      _id: pp-windows
      matchCriteria: [...]
      actions: [...]

# Enfant: mssp/acme-corp/base/processing-policies.yaml  
spec:
  processingPolicies:
    - policy_name: pp-windows-base
      _id: pp-windows           # Même _id = merge
      actions:
        - _id: action-1         # Référence action parent
        - _id: action-2
        - _id: action-custom    # Nouvelle action = append
          type: AddTag
          tags: ["acme-specific"]
```

### 6.2 Ordering des Policies

```yaml
spec:
  processingPolicies:
    - _id: pp-critical-security
      priority: 10              # Évalué en premier
      
    - _id: pp-standard
      priority: 100             # Défaut
      
    - _id: pp-cleanup
      priority: 999             # Évalué en dernier
```

---

## 7. Intégration avec Alert Rules

### 7.1 Processing vs Alert Rules

| Aspect | Processing Policies | Alert Rules (futur) |
|--------|--------------------|---------------------|
| **Scope** | Event-level | Correlation/multi-event |
| **Latence** | Real-time | Batch/windowed |
| **Output** | Event modifié/taggué | Notification/Case |
| **Exemple** | "Taguer si risk_score > 80" | "Alerte si 5 failed logins en 5min" |

### 7.2 Interaction

Les Processing Policies peuvent préparer les données pour les Alert Rules :

```yaml
# Processing Policy: enrichit pour faciliter alerting
- policy_name: pp-prepare-bruteforce
  actions:
    - type: ExtractField
      targetField: failed_auth_key
      expression: "concat(source_ip, ':', username)"

# Alert Rule (futur) utilisera failed_auth_key pour corréler
```

---

## 8. Validation

### 8.1 Règles de Validation

| Règle | Sévérité | Description |
|-------|----------|-------------|
| Expression valide | ERROR | Syntaxe expression doit être valide |
| Champ cible existe | WARN | TargetField déjà utilisé par normalizer |
| Repo cible existe | ERROR | RouteTo.repo doit exister |
| Pas de boucle | ERROR | PP ne peut pas s'appeler elle-même |
| Priority unique | WARN | Même priority = ordre non déterministe |

### 8.2 Exemple Erreur

```yaml
# INVALIDE: Expression syntax error
- type: ExtractField
  targetField: bad_field
  expression: "severity *"     # ← Erreur: opérande manquant
  
# INVALIDE: Référence repo inexistant  
- type: RouteTo
  repo: repo-inexistant        # ← Ce repo n'existe pas
```

---

## 9. Exemples Complets

### 9.1 LogPoint Golden Template

```yaml
# templates/logpoint/golden-base/processing-policies.yaml
spec:
  processingPolicies:
    # Standardiser le champ severity
    - policy_name: pp-normalize-severity
      _id: pp-severity
      actions:
        - type: ExtractField
          targetField: normalized_severity
          expression: |
            case(
              severity <= 3, "low",
              severity <= 6, "medium", 
              severity <= 8, "high",
              "critical"
            )
    
    # Taguer les logs de sécurité
    - policy_name: pp-tag-security
      _id: pp-tag-sec
      matchCriteria:
        - type: KeyPresentValueMatches
          key: category
          value: Security
      actions:
        - type: AddTag
          tags: ["security-event"]
```

### 9.2 MSSP Extension

```yaml
# templates/mssp/acme-corp/base/processing-policies.yaml
spec:
  processingPolicies:
    - policy_name: pp-normalize-severity
      _id: pp-severity
      actions:
        - _id: extract-severity    # Hérité du parent
        - _id: acme-custom
          type: AddTag
          condition: 'normalized_severity == "critical"'
          tags: ["acme-critical", "page-oncall"]
    
    # Nouvelle policy: Détection lateral movement
    - policy_name: pp-lateral-movement
      _id: pp-lateral
      priority: 50              # Évalué avant policies standard
      matchCriteria:
        - type: KeyPresentValueMatches
          key: event_id
          value: "4624"         # Successful logon
        - type: KeyPresent
          key: target_server
      actions:
        - type: ExtractField
          targetField: is_lateral
          expression: 'source_workstation != target_server'
        - type: AddTag
          condition: "is_lateral == true"
          tags: ["lateral-movement", "tier-1-review"]
```

---

## 10. Open Questions

1. **Langage d'expression**: DSL maison ou existing (CEL, jq-like) ?
2. **Performance**: Limites nombre de policies/actions par event ?
3. **Debug**: Comment tracer quelle policy a modifié un event ?
4. **Rollback**: Comment gérer changement de policy sur events déjà stockés ?

---

## Appendix A: Expression Language Reference (Draft)

### Opérateurs

| Opérateur | Description | Exemple |
|-----------|-------------|---------|
| `+ - * / %` | Arithmétique | `severity * 10 + 5` |
| `== != < > <= >=` | Comparaison | `severity >= 7` |
| `and or not` | Logique | `is_admin and severity > 5` |
| `in` | Appartenance | `event_id in [4624, 4625]` |
| `contains` | Sous-chaîne | `command contains "powershell"` |
| `matches` | Regex | `user matches "^[A-Z]{3}\\."` |

### Fonctions

| Fonction | Description | Exemple |
|----------|-------------|---------|
| `if(c, t, f)` | Conditionnel | `if(is_admin, 100, 10)` |
| `coalesce(a, b, ...)` | Premier non-null | `coalesce(username, user, "unknown")` |
| `length(x)` | Longueur | `length(command_line)` |
| `lower/upper(s)` | Casse | `lower(email)` |
| `regex_extract(s, p, g)` | Extraction | `regex_extract(path, "\\\\([^\\\\]+)$", 1)` |
| `now()` | Timestamp courant | `now() - timestamp < 3600` |
| `hash(s)` | Hash string | `hash(concat(ip, user))` |
