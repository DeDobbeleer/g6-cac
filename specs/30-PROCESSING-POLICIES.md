# Processing Policies Specification

**Version**: 1.0  
**Status**: 🚧 Draft  
**Date**: 2026-02-26  
**Author**: CaC-ConfigMgr Product Team  

---

## 1. Executive Summary

Les **Processing Policies (PP)** sont des **ressources de configuration** qui lient ensemble :
- **1 Routing Policy** (où stocker)
- **1 Normalization Policy** (comment parser)  
- **1 Enrichment Policy** (quel contexte ajouter)

```
Processing Policy = RP + NP + EP

Log Source → [Processing Policy] → Storage
                │
                ├── RP: routing-policy-ref → choisit repo
                ├── NP: normalization-policy-ref → parse log
                └── EP: enrichment-policy-ref → ajoute contexte
```

**Rôle**: Simplifier la configuration en regroupant les 3 policies en 1 référence.

---

## 2. Structure

### 2.1 Définition YAML

```yaml
# templates/mssp/acme-corp/base/processing-policies.yaml
apiVersion: cac-configmgr.io/v1
kind: ConfigTemplate
metadata:
  name: acme-base
  extends: logpoint/golden-base
  
spec:
  processingPolicies:
    - name: windows-security-pipeline
      _id: pp-windows-sec
      
      # Références aux 3 policies
      routingPolicy: rp-windows-security
      normalizationPolicy: np-windows
      enrichmentPolicy: ep-geoip-threatintel
      
      # Métadonnées
      description: "Pipeline complet pour logs Windows sécurité"
      enabled: true
```

### 2.2 Champs

| Champ | Type | Description | Requis |
|-------|------|-------------|--------|
| `name` | string | Nom unique de la PP | ✅ Oui |
| `_id` | string | ID template pour héritage | ✅ Oui |
| `routingPolicy` | string | Référence RoutingPolicy | ✅ Oui |
| `normalizationPolicy` | string | Référence NormalizationPolicy | ❌ Non (défaut: Auto) |
| `enrichmentPolicy` | string | Référence EnrichmentPolicy | ❌ Non |
| `description` | string | Description | ❌ Non |
| `enabled` | bool | Actif/inactif | ❌ Non (défaut: true) |

---

## 3. Héritage

Même mécanisme que les autres ressources : `_id` pour matcher.

```yaml
# Parent: logpoint/golden-base/processing-policies.yaml
spec:
  processingPolicies:
    - name: default-pipeline
      _id: pp-default
      routingPolicy: rp-default
      normalizationPolicy: np-auto
      enrichmentPolicy: ep-basic

# Enfant: mssp/acme-corp/base/processing-policies.yaml
spec:
  processingPolicies:
    - name: default-pipeline
      _id: pp-default
      routingPolicy: rp-acme-default        # Override
      # normalizationPolicy: hérité (np-auto)
      enrichmentPolicy: ep-acme-geoip       # Override
```

---

## 4. Exemples

### 4.1 LogPoint Golden Template

```yaml
# templates/logpoint/golden-base/processing-policies.yaml
spec:
  processingPolicies:
    - name: default
      _id: pp-default
      routingPolicy: rp-default
      normalizationPolicy: np-auto
      
    - name: windows-security
      _id: pp-windows-sec
      routingPolicy: rp-windows
      normalizationPolicy: np-windows
      enrichmentPolicy: ep-geoip
      
    - name: linux-syslog
      _id: pp-linux
      routingPolicy: rp-linux
      normalizationPolicy: np-syslog
      
    - name: firewall-perimeter
      _id: pp-firewall
      routingPolicy: rp-security
      normalizationPolicy: np-common-firewall
      enrichmentPolicy: ep-threat-intel
```

### 4.2 MSSP Extension

```yaml
# templates/mssp/acme-corp/base/processing-policies.yaml
spec:
  processingPolicies:
    - name: default
      _id: pp-default
      routingPolicy: rp-acme-default
      normalizationPolicy: np-auto
      enrichmentPolicy: ep-acme-geoip       # Ajoute GeoIP maison
      
    - name: windows-security
      _id: pp-windows-sec
      routingPolicy: rp-acme-windows        # Override routing
      normalizationPolicy: np-windows
      enrichmentPolicy: ep-acme-full        # GeoIP + ThreatIntel + AD
      
    - name: high-value-assets
      _id: pp-high-value
      routingPolicy: rp-critical-assets
      normalizationPolicy: np-auto
      enrichmentPolicy: ep-premium          # Tous les enrichissements
```

### 4.3 Instance

```yaml
# instances/banque-dupont/prod/instance.yaml
spec:
  processingPolicies:
    - name: windows-security
      _id: pp-windows-sec
      routingPolicy: rp-bank-windows        # Override: routing spécifique banque
      # normalizationPolicy: hérité
      # enrichmentPolicy: hérité
```

---

## 5. Utilisation

### 5.1 Association avec Devices

Les devices référencent la PP à utiliser :

```yaml
# devices.yaml
devices:
  - name: windows-dc-01
    type: windows-wec
    processingPolicy: pp-windows-sec       # ← Référence la PP
    
  - name: firewall-checkpoint-01
    type: checkpoint
    processingPolicy: pp-firewall
    
  - name: linux-server-generic
    type: syslog
    processingPolicy: pp-default
```

### 5.2 Avantages

- **Simplicité**: 1 référence au lieu de 3
- **Cohérence**: Garantit RP/NP/EP compatibles
- **Héritage**: Change tout le pipeline en 1 lieu

---

## 6. Validation

### 6.1 Règles

| Règle | Sévérité | Description |
|-------|----------|-------------|
| `routingPolicy` existe | ERROR | Doit référencer une RP existante |
| `normalizationPolicy` existe | ERROR | Si spécifié, doit exister |
| `enrichmentPolicy` existe | ERROR | Si spécifié, doit exister |
| Pas de boucle | ERROR | EP ne référence pas la PP (indirect) |

### 6.2 Exemple Erreur

```yaml
# INVALIDE: Référence inexistante
processingPolicies:
  - name: bad-pipeline
    routingPolicy: rp-inexistant           # ERROR: RP pas définie
    normalizationPolicy: np-windows
```

---

## Appendix: Référence Rapide

```yaml
processingPolicies:
  - name: <string>              # Obligatoire
    _id: <string>               # Pour héritage
    routingPolicy: <string>     # Obligatoire → RoutingPolicy
    normalizationPolicy: <string> # Optionnel → NormalizationPolicy
    enrichmentPolicy: <string>    # Optionnel → EnrichmentPolicy
    description: <string>
    enabled: <bool>
```

---

## Open Questions

1. **Optionnels**: `normalizationPolicy` et `enrichmentPolicy` vraiment optionnels ?
2. **Défauts**: Valeurs par défaut si non spécifiés (`np-auto`, pas d'EP) ?
3. **Unicité**: Une PP peut-elle être utilisée par plusieurs devices ? (Oui, c'est le but)
