# Audit de Validation - CaC-ConfigMgr

> **Date**: 2026-03-02  
> **Statut**: Phase 2 - Correction des gaps Phase 1  
> **Objectif**: Documenter exhaustivement ce qui est validé et ce qui ne l'est pas

---

## 🎯 Résumé Exécutif

| Métrique | Valeur |
|----------|--------|
| Ressources LogPoint supportées | 10+ |
| Ressources avec validation complète | 5 |
| Ressources avec validation partielle | 0 |
| Ressources sans validation | 5+ |
| Champs critiques non validés | ❌ Oui (corrigé) |

**Problème identifié**: La validation Phase 1 était incomplète. Des champs requis comme `path` dans `hiddenrepopath` n'étaient pas validés, et les références croisées n'étaient pas exhaustivement vérifiées.

---

## 📊 Matrice de Validation par Ressource

### Légende

| Symbole | Signification |
|---------|---------------|
| ✅ | Validation complète (champs + types + références) |
| ⚠️ | Validation partielle (certains champs manquants) |
| ❌ | Pas de validation |
| 🔄 | Modèle existe, validation à implémenter |
| ⏳ | Pas de modèle Pydantic |

### Repos (Stockage)

| Élément | Modèle | Validation API | Cross-refs | Statut |
|---------|--------|----------------|------------|--------|
| `Repo` | ✅ | ✅ (name, pattern) | - | ✅ |
| `Repo.name` | ✅ | ✅ (pattern) | - | ✅ |
| `Repo.hiddenrepopath` | ✅ | ✅ (path, retention requis) | - | ✅ |
| `HiddenRepoPath._id` | ✅ | ✅ (requis) | - | ✅ |
| `HiddenRepoPath.path` | ✅ | ✅ (requis, string) | - | ✅ |
| `HiddenRepoPath.retention` | ✅ | ✅ (requis, int) | - | ✅ |

**Bug corrigé**: Avant le 2026-03-02, `path` n'était pas validé comme champ requis, permettant des valeurs `None` ou `"None"`.

### Routing Policies

| Élément | Modèle | Validation API | Cross-refs | Statut |
|---------|--------|----------------|------------|--------|
| `RoutingPolicy` | ✅ | ✅ | - | ✅ |
| `policy_name` | ✅ | ✅ (pattern) | - | ✅ |
| `catch_all` | ✅ | ✅ (requis, string) | → Repo | ✅ |
| `routing_criteria` | ✅ | ✅ (liste) | - | ✅ |
| `routing_criteria[].repo` | ✅ | ✅ | → Repo | ✅ |

### Processing Policies

| Élément | Modèle | Validation API | Cross-refs | Statut |
|---------|--------|----------------|------------|--------|
| `ProcessingPolicy` | ✅ | ✅ | - | ✅ |
| `policy_name` | ✅ | ✅ (pattern) | - | ✅ |
| `routing_policy` | ✅ | ✅ (requis) | → RoutingPolicy | ✅ |
| `normalization_policy` | ✅ | ✅ (optionnel) | → NormalizationPolicy | ✅ |
| `enrichment_policy` | ✅ | ✅ (optionnel) | → EnrichmentPolicy | ✅ |

**Bug corrigé**: Les aliases camelCase (`routingPolicy`, `normalizationPolicy`, `enrichmentPolicy`) n'étaient pas supportés.

### Normalization Policies

| Élément | Modèle | Validation API | Cross-refs | Statut |
|---------|--------|----------------|------------|--------|
| `NormalizationPolicy` | ✅ | ✅ | - | ✅ |
| `name` | ✅ | ✅ (pattern) | - | ✅ |
| `normalization_packages` | ✅ | ✅ (liste) | - | ✅ |
| `compiled_normalizer` | ✅ | ✅ (optionnel) | - | ✅ |

### Enrichment Policies

| Élément | Modèle | Validation API | Cross-refs | Statut |
|---------|--------|----------------|------------|--------|
| `EnrichmentPolicy` | ✅ | ✅ | - | ✅ |
| `name` | ✅ | ✅ (pattern) | - | ✅ |
| `specifications` | ✅ | ✅ (liste requise) | - | ✅ |
| `specifications[].source` | ✅ | ✅ (requis) | - | ✅ |
| `specifications[].criteria` | ✅ | ✅ (liste requise) | - | ✅ |
| `specifications[].rules` | ✅ | ✅ (optionnel) | - | ✅ |

---

## ✅ Ressources Validées (2026-03-02)

### Device Groups

| Élément | Modèle | Validation | Cross-refs | Statut |
|---------|--------|------------|------------|--------|
| `DeviceGroup` | ✅ | ✅ | - | ✅ |
| `name` | ✅ | ✅ (pattern) | - | ✅ |
| `description` | ✅ | ✅ (optionnel) | - | ✅ |
| `criteria` | ✅ | ✅ (optionnel) | - | ✅ |

### Devices

| Élément | Modèle | Validation | Cross-refs | Statut |
|---------|--------|------------|------------|--------|
| `Device` | ✅ | ✅ | - | ✅ |
| `name` | ✅ | ✅ | - | ✅ |
| `ip_address` | ✅ | ✅ (format IP) | - | ✅ |
| `device_group` | ✅ | ✅ | → DeviceGroup | ✅ |
| `processing_policy` | ✅ | ✅ | → ProcessingPolicy | ✅ |
| `collectors` | ✅ | ✅ (liste) | - | ✅ |
| `enabled` | ✅ | ✅ (bool) | - | ✅ |

### Syslog Collectors

| Élément | Modèle | Validation | Priorité | Blocker démo? |
|---------|--------|------------|----------|---------------|
| `SyslogCollector` | ⏳ | ❌ | P2 | Non |
| `name` | ⏳ | ❌ | P2 | Non |
| `port` | ⏳ | ❌ | P2 | Non |
| `protocol` | ⏳ | ❌ | P2 | Non |

### Alert Rules

| Élément | Modèle | Validation | Priorité | Blocker démo? |
|---------|--------|------------|----------|---------------|
| `AlertRule` | ⏳ | ❌ | P2 | Non |
| `name` | ⏳ | ❌ | P2 | Non |
| `query` | ⏳ | ❌ | P2 | Non |
| `threshold` | ⏳ | ❌ | P2 | Non |
| `notification` | ⏳ | ❌ | P3 | Non |

### Users & User Groups

| Élément | Modèle | Validation | Priorité | Blocker démo? |
|---------|--------|------------|----------|---------------|
| `User` | ⏳ | ❌ | P3 | Non |
| `UserGroup` | ⏳ | ❌ | P3 | Non |
| `permissions` | ⏳ | ❌ | P3 | Non |

### Dashboards & Reports

| Élément | Modèle | Validation | Priorité | Blocker démo? |
|---------|--------|------------|----------|---------------|
| `Dashboard` | ⏳ | ❌ | P3 | Non |
| `Report` | ⏳ | ❌ | P3 | Non |

---

## 🔍 Détail des Validations Manquantes

### 1. Device Groups (CRITIQUE - P1)

**Pourquoi c'est important**: Les Device Groups sont fondamentaux pour organiser les log sources. Sans validation:
- Devices peuvent référencer des groupes inexistants
- Critères de regroupement invalides
- Déploiement qui échoue silencieusement

**Champs à valider**:
```yaml
device_groups:
  - name: "windows-servers"           # requis, pattern
    description: "All Windows servers" # optionnel
    criteria:                          # optionnel
      - key: "os_type"
        operator: "equals"
        value: "windows"
```

**Références croisées**:
- Device.device_group → DeviceGroup.name

### 2. Devices (CRITIQUE - P1)

**Pourquoi c'est important**: Les devices sont les sources de logs. Erreurs = pas de collecte.

**Champs à valider**:
```yaml
devices:
  - name: "srv-web-01"               # requis, unique, pattern
    ip_address: "10.0.1.10"          # requis, format IP
    device_group: "web-servers"      # optionnel, → DeviceGroup
    processing_policy: "pp-web"      # optionnel, → ProcessingPolicy
    collectors:                       # optionnel
      - "syslog-collector-1"
```

**Références croisées**:
- Device.device_group → DeviceGroup.name
- Device.processing_policy → ProcessingPolicy.name
- Device.collectors[] → SyslogCollector.name

### 3. Syslog Collectors (P2)

**Champs à valider**:
```yaml
syslog_collectors:
  - name: "syslog-collector-1"       # requis
    port: 514                        # requis, int, 1-65535
    protocol: "udp"                  # requis, enum [udp, tcp]
    tls_enabled: false               # optionnel, bool
```

### 4. Alert Rules (P2)

**Champs à valider**:
```yaml
alert_rules:
  - name: "high-cpu-alert"           # requis
    query: "* | where cpu > 90"      # requis, syntaxe LPQL
    threshold: 5                     # requis, int
    timeframe: 300                   # requis, int (secondes)
    severity: "high"                 # requis, enum [low, medium, high, critical]
```

---

## 🚨 Bugs Critiques Corrigés (2026-03-02)

### Bug #1: Champs `None` dans hiddenrepopath

**Symptôme**: `path: "None"` dans les payloads JSON exportés.

**Cause**: `model_dump(exclude_none=False)` + merge qui ne skippe pas les `None`.

**Fix**: 
- `exclude_none=True` dans `engine.py`
- Validation explicite des champs requis dans `hiddenrepopath`

### Bug #2: Aliases camelCase non supportés

**Symptôme**: Validation échoue sur `routingPolicy` (attend `routing_policy`).

**Cause**: Pydantic `by_alias=True` exporte en camelCase, mais le validateur cherchait en snake_case.

**Fix**:
- Ajout du support `alias` dans `API_SPECS`
- Mapping `routing_policy` → `routingPolicy` dans la validation

### Bug #3: `policy_name` vs `name`

**Symptôme**: ProcessingPolicy avec `name` mais pas `policy_name` échoue validation.

**Cause**: Inconsistance entre Pydantic (utilise `name`) et API spec (attend `policy_name`).

**Fix**:
- Alias `policy_name` → `name` dans la spec de validation

---

## 📝 Recommandations

### Immédiat (Avant démo)

1. ✅ **DONE** - Corriger validation `hiddenrepopath`
2. ✅ **DONE** - Corriger support aliases camelCase
3. ⏳ **TODO** - Ajouter modèle DeviceGroup (basique)
4. ⏳ **TODO** - Ajouter modèle Device (basique)

### Court terme (Phase 2)

5. Validation complète DeviceGroup (critères)
6. Validation complète Device (format IP, références)
7. Validation Syslog Collectors
8. Tests d'intégration avec validation d'erreurs

### Fait (2026-03-02)

9. ✅ Validation DeviceGroup (champs + critères)
10. ✅ Validation Device (format IP, références DeviceGroup/ProcessingPolicy)

### Long terme (Phase 3+)

11. Validation Alert Rules (syntaxe LPQL)
12. Validation Users & Permissions
13. Validation Dashboards
14. Validation Reports
15. Validation Syslog Collectors

---

## 🧪 Comment Vérifier

### Tester la validation actuelle

```bash
# Valider toute la config
cac-configmgr validate \
  --fleet demo-configs/instances/banks/bank-a/prod/fleet.yaml \
  --topology demo-configs/instances/banks/bank-a/prod/instance.yaml \
  demo-configs/

# Vérifier qu'un path manquant est détecté
# ( Modifier instance.yaml pour supprimer 'path' d'un tier )
cac-configmgr validate ...
# Devrait échouer avec: "Required field 'path' is missing"
```

### Vérifier les payloads

```bash
# Exporter et vérifier qu'il n'y a pas de "None"
cac-configmgr plan ... --export-dir /tmp/test

# Vérifier
jq '.. | objects | select(.path == "None")' /tmp/test/*.json
# Devrait retourner vide
```

---

## 📚 Références

- [50-VALIDATION-SPEC.md](../specs/50-VALIDATION-SPEC.md)
- [API-REFERENCE.md](../specs/API-REFERENCE.md)
- [20-TEMPLATE-HIERARCHY.md](../specs/20-TEMPLATE-HIERARCHY.md)
- [ADRS.md](../ADRS.md)

---

**Document maintenu par**: Agent AI  
**Dernière mise à jour**: 2026-03-02  
**Prochaine revue**: Après implémentation DeviceGroup/Device
