# Processing Policies Specification

**Version**: 1.0  
**Status**: 🚧 Draft - Basé sur modèle existant lpcac  
**Date**: 2026-02-26  
**Author**: CaC-ConfigMgr Product Team  

---

## 1. Executive Summary

Les **Processing Policies (PP)** définissent l'**orchestration du pipeline complet** de traitement des logs :

```
Log Source → [Processing Policy orchestrates:] → Storage
                │
                ├── Step 1: Routing → repo X
                ├── Step 2: Normalization → parser Y  
                ├── Step 3: Enrichment → source Z
                ├── Step 4: Processing → filter W
                └── Step 5: Storage → repo final
```

**Rôle**: Ordonnancer les étapes et définir les dépendances entre elles.
**Ne fait pas**: Transformer les logs (c'est le rôle des Normalization Policies).

---

## 2. Concept Clé : Pipeline Orchestration

### 2.1 Différence avec autres Policies

| Policy Type | Rôle | Contient |
|-------------|------|----------|
| **Routing Policy** | Choisir le repo | Critères de routage |
| **Normalization Policy** | Parser/normaliser | Packages de normalisation |
| **Enrichment Policy** | Ajouter contexte | Sources d'enrichissement |
| **Processing Policy** | **Ordonnancer tout ça** | **Liste ordonnée d'étapes** |

### 2.2 Étapes du Pipeline (Steps)

| Step | Description | Référence |
|------|-------------|-----------|
| `routing` | Router vers repo | `policy_ref` → RoutingPolicy |
| `normalization` | Parser le log | `policy_ref` → NormalizationPolicy |
| `enrichment` | Enrichir | `policy_ref` → EnrichmentPolicy |
| `processing` | Filtres additionnels | `policy_ref` → ProcessingPolicy (récursif) |
| `storage` | Destination finale | `repo_ref` → Repo |
| `alerting` | Déclencher alerte | `policy_ref` → AlertRule (futur) |

---

## 3. Structure YAML

### 3.1 Définition Complète

```yaml
apiVersion: cac-configmgr.io/v1
kind: ConfigTemplate
metadata:
  name: acme-base
  extends: logpoint/golden-base
  
spec:
  processingPolicies:
    - name: standard-security-pipeline
      _id: pp-standard-sec
      description: "Pipeline standard pour logs de sécurité"
      enabled: true
      
      # Le pipeline ordonné
      pipeline:
        # Étape 1: Routing
        - step: routing
          policy_ref: rp-security-events
        
        # Étape 2: Normalization (avec condition)
        - step: normalization
          policy_ref: np-windows-security
          condition: "device_product == 'Windows'"
        
        # Étape 3: Enrichment GeoIP (optionnel)
        - step: enrichment
          policy_ref: ep-geoip
          optional: true
        
        # Étape 4: Enrichment Threat Intel (optionnel)
        - step: enrichment  
          policy_ref: ep-threat-intel
          optional: true
        
        # Étape 5: Filtre additionnel (ex: drop internal traffic)
        - step: processing
          policy_ref: pp-filter-internal
          optional: true
          condition: "not is_internal_traffic"
        
        # Étape 6: Stockage final
        - step: storage
          repo_ref: repo-secu
      
      # Gestion des erreurs
      on_error: quarantine  # drop | quarantine | continue | alert
      
      # Limites
      max_events_per_second: 10000
```

### 3.2 Champs par Step

```yaml
pipeline:
  - step: <string>           # Obligatoire: routing|normalization|enrichment|processing|storage|alerting
    policy_ref: <string>     # Pour routing/normalization/enrichment/processing/alerting
    repo_ref: <string>       # Pour storage uniquement
    optional: <bool>         # Défaut: false. Si true, l'étape peut échouer sans bloquer
    condition: <string>      # Expression conditionnelle (optionnel)
```

---

## 4. Héritage et Template IDs

### 4.1 Héritage Standard

Même mécanisme que les autres ressources : `_id` pour matcher.

```yaml
# Parent: logpoint/golden-base/processing-policies.yaml
spec:
  processingPolicies:
    - name: standard-pipeline
      _id: pp-standard
      pipeline:
        - step: routing
          policy_ref: rp-default
        - step: storage
          repo_ref: repo-default

# Enfant: mssp/acme-corp/base/processing-policies.yaml
spec:
  processingPolicies:
    - name: standard-pipeline
      _id: pp-standard          # Même _id = merge
      pipeline:
        - _id: step-1           # Référence étape parent (keep)
        - _id: step-2
        - step: enrichment      # Nouvelle étape = append
          policy_ref: ep-geoip
          optional: true
        - _id: step-3           # Référence étape parent (keep)
```

### 4.2 Step IDs pour Matching

Les étapes du pipeline peuvent avoir des `_id` pour être référencées :

```yaml
pipeline:
  - _id: route-step
    step: routing
    policy_ref: rp-default
    
  - _id: normalize-step
    step: normalization
    policy_ref: np-auto
    
  - _id: enrich-step
    step: enrichment
    policy_ref: ep-geoip
```

**Règles de merge**:
- Même `_id` = merge (override champs spécifiés)
- Nouvel `_id` = append à la fin du pipeline
- `_action: delete` = supprimer l'étape
- `_action: reorder` avec `_after`/`_before` = changer position

### 4.3 Exemple: Ajouter une étape au milieu

```yaml
# Parent pipeline: [route] → [normalize] → [storage]

# Enfant: ajoute enrichment entre normalize et storage
pipeline:
  - _id: route-step
  - _id: normalize-step
  
  - step: enrichment          # Nouvelle étape
    _after: normalize-step    # Position: après normalize
    policy_ref: ep-custom
    optional: true
    
  - _id: storage-step
```

Résultat: `[route] → [normalize] → [enrichment] → [storage]`

---

## 5. Conditions et Optional

### 5.1 Conditions par Step

Une étape ne s'exécute que si la condition est vraie :

```yaml
pipeline:
  - step: normalization
    policy_ref: np-windows
    condition: "device_product == 'Windows'"  # Skip si Linux
    
  - step: normalization
    policy_ref: np-linux
    condition: "device_product == 'Linux'"    # Skip si Windows
```

### 5.2 Optional Steps

```yaml
pipeline:
  - step: enrichment
    policy_ref: ep-geoip
    optional: true  # Si GeoIP indisponible, continue sans erreur
    
  - step: enrichment
    policy_ref: ep-threat-intel
    optional: true  # Si MISP down, on continue quand même
```

**Comportement on_error par step**:
- `optional: false` + erreur = erreur pipeline (selon `on_error` de la PP)
- `optional: true` + erreur = warning, continue pipeline

---

## 6. Gestion des Erreurs

### 6.1 on_error Policy-Level

```yaml
on_error: quarantine  # Comportement si une étape échoue
```

| Valeur | Comportement |
|--------|--------------|
| `drop` | Dropper l'événement |
| `quarantine` | Envoyer dans repo quarantaine |
| `continue` | Continuer avec étape suivante (risqué) |
| `alert` | Déclencher alerte + quarantaine |

### 6.2 max_events_per_second

Protection contre surcharge :

```yaml
max_events_per_second: 10000  # Drop events au-delà
```

---

## 7. Exemples Complets

### 7.1 LogPoint Golden Template

```yaml
# templates/logpoint/golden-base/processing-policies.yaml
spec:
  processingPolicies:
    - name: default-pipeline
      _id: pp-default
      description: "Pipeline par défaut pour tous les logs"
      enabled: true
      pipeline:
        - step: routing
          policy_ref: rp-default
        - step: normalization
          policy_ref: np-auto-detect
        - step: storage
          repo_ref: repo-default
      on_error: quarantine
```

### 7.2 MSSP Pipeline Sécurité

```yaml
# templates/mssp/acme-corp/base/processing-policies.yaml
spec:
  processingPolicies:
    # Hérite et étend default-pipeline
    - name: default-pipeline
      _id: pp-default
      pipeline:
        - _id: step-route
        - _id: step-normalize
        
        - step: enrichment          # Ajoute GeoIP
          _after: step-normalize
          policy_ref: ep-geoip
          optional: true
          
        - step: enrichment          # Ajoute Threat Intel
          _after: step-normalize
          policy_ref: ep-threat-intel
          optional: true
          
        - _id: step-storage
      
      max_events_per_second: 50000
    
    # Pipeline spécifique haute sécurité
    - name: high-security-pipeline
      _id: pp-high-sec
      description: "Pipeline pour logs critiques (DC, firewalls)"
      extends: pp-default           # Hérite et modifie
      pipeline:
        - step: routing
          policy_ref: rp-critical-security
        - step: storage
          repo_ref: repo-secu
      on_error: alert
      max_events_per_second: 10000
```

### 7.3 Profile Entreprise

```yaml
# templates/mssp/acme-corp/profiles/enterprise/processing-policies.yaml
spec:
  processingPolicies:
    - name: high-security-pipeline
      _id: pp-high-sec
      pipeline:
        - step: routing
          policy_ref: rp-critical-security
        - step: normalization
          policy_ref: np-auto-detect
        - step: enrichment
          policy_ref: ep-geoip
          optional: true
        - step: enrichment
          policy_ref: ep-threat-intel
          optional: true
        - step: enrichment          # Ajoute AD lookup pour entreprise
          policy_ref: ep-active-directory
          optional: true
        - step: storage
          repo_ref: repo-secu-critical
      max_events_per_second: 50000
```

---

## 8. Validation

### 8.1 Règles de Validation

| Règle | Sévérité | Description |
|-------|----------|-------------|
| Step valide | ERROR | Step doit être dans liste autorisée |
| Référence existe | ERROR | `policy_ref` doit exister dans templates |
| Repo existe | ERROR | `repo_ref` doit exister dans repos |
| Pas de boucle | ERROR | PP ne peut pas référencer elle-même (direct/indirect) |
| Pipeline non vide | ERROR | Minimum une étape routing + une étape storage |
| Storage unique | WARN | Un seul `storage` step recommandé |
| Ordre logique | WARN | `normalization` avant `enrichment` recommandé |

### 8.2 Exemple Erreurs

```yaml
# INVALIDE: policy_ref inexistant
pipeline:
  - step: routing
    policy_ref: rp-inexistant  # ERROR: Cette routing policy n'existe pas

# INVALIDE: Boucle
pipeline:
  - step: processing
    policy_ref: pp-courante     # ERROR: Self-reference

# INVALIDE: Pas de storage
pipeline:
  - step: routing
    policy_ref: rp-default
  # ERROR: Missing storage step
```

---

## 9. Intégration avec Devices/Log Sources

### 9.1 Association Device → Processing Policy

Les devices référencent la PP à utiliser :

```yaml
# Dans devices.yaml ou log-collection-policy.yaml
devices:
  - name: windows-dc-01
    device_type: windows
    processing_policy: pp-high-sec  # ← Référence la PP
    
  - name: firewall-perimeter
    device_type: checkpoint
    processing_policy: pp-firewall-pipeline
```

---

## 10. Différences avec DirSync

| Aspect | DirSync | CaC-ConfigMgr Processing Policies |
|--------|---------|-----------------------------------|
| **Structure** | Implicite/monolithique | Explicite/pipeline ordonné |
| **Flexibilité** | Limitée | Étapes conditionnelles, optionnelles |
| **Héritage** | Non | Oui (template IDs) |
| **Réutilisation** | Copie | Référence par `policy_ref` |

---

## Appendix A: Référence Rapide

```yaml
processingPolicies:
  - name: <string>              # Obligatoire
    _id: <string>               # Pour héritage
    description: <string>
    enabled: <bool>
    
    pipeline:                   # Liste ordonnée d'étapes
      - step: routing|normalization|enrichment|processing|storage|alerting
        policy_ref: <string>    # Référence policy (sauf storage)
        repo_ref: <string>      # Référence repo (storage uniquement)
        optional: <bool>        # Défaut: false
        condition: <string>     # Expression optionnelle
        _id: <string>           # Pour reorder/merge
        _after: <id>            # Positionnement
        
    on_error: drop|quarantine|continue|alert
    max_events_per_second: <int>
```

---

## Open Questions

1. **Alerting step**: Comment référencer les Alert Rules quand ils seront définis ?
2. **Step répétable**: Peut-on avoir plusieurs `enrichment` steps ? (Oui selon cette spec)
3. **Sub-pipelines**: Une PP peut-elle inclure une autre PP comme "macro" ?
4. **Conditions**: Syntaxe exacte des expressions (`device_product == 'Windows'`)
