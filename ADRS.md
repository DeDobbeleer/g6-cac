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

## ADR-001: Langage et stack technique

**Statut**: Accepté (PoC)

**Décision**: Python avec Pydantic + Typer + Rich

**Justification**:
- Prototypage rapide pour le PoC
- Pydantic excellent pour validation YAML
- Typer/Rich = CLI professionnelle sans effort
- Facilement portable en Go plus tard si besoin performance

**Alternatives envisagées**: Go (meilleure perf, binaire statique) mais courbe d'apprentissage plus longue pour itérations rapides.

---

## ADR-002: Scope du PoC

**Statut**: Accepté

**Décision**: Se concentrer sur le pipeline de données uniquement
- Repos
- Routing Policies  
- Normalization Policies
- Processing Policies

**Justification**:
- C'est le cœur métier commun à tous les clients
- Démonstration concrète de la valeur (gain de temps énorme)
- APIs Director stables et bien documentées pour ces ressources
- Facilement testable (créer/supprimer des repos = safe)

**Hors scope PoC**:
- AlertRules (plus complexe, risqué en test)
- DeviceGroups (nécessite devices existants)
- Users/Permissions (sensible)

---

## ADR-003: Format de configuration

**Statut**: Accepté (PoC)

**Décision**: YAML avec schémas Pydantic, style Kubernetes

```yaml
apiVersion: logpoint-cac/v1
kind: Repo
metadata:
  name: default
spec:
  ...
```

**Justification**:
- Standard DevOps/GitOps
- Comments possibles (vs JSON)
- Pydantic génère validation + erreurs claires

---

## ADR-004: Gestion des dépendances

**Statut**: Accepté (PoC)

**Décision**: Ordre de déploiement implicite via le pipeline Processing

**Ordre**:
1. Repos (aucune dépendance)
2. Routing Policies (dépend des repos)
3. Normalization Policies (indépendant)
4. Processing Policies (dépend de 2 et 3)

**Justification**:
- Graphe simple pour le PoC (DAG linéaire)
- Pas besoin de resolver complexe pour démontrer la valeur
- Traitement manuel dans le bon ordre acceptable pour v1

---

## ADR-005: State management

**Statut**: Proposé

**Décision**: Pas de state persistant séparé. État = réalité Director + fichiers YAML.

**Justification**:
- Simplicité maximale pour le PoC
- Pas de SPOF, pas de base de données à gérer
- `cac sync` permet d'exporter l'état réel quand besoin

**Limitations connues**:
- `plan` nécessite des appels API pour résoudre les IDs
- Pas de cache = plus lent (acceptable pour PoC)

---

## ADR-006: Mode Direct vs Director

**Statut**: Différé

**Décision**: PoC en mode Director uniquement.

**Justification**:
- APIs Director stables et testées
- Clientèle MSSP existante = marché immédiat
- APIs SIEM direct = à valider, pas bloquant pour démontrer le concept

**Évolution future**:
- Ajouter connecteur Direct quand APIs SIEM disponibles
- Abstraction commune pour que les configs fonctionnent dans les deux modes

---

## ADR-007: Multi-API, Versioning et Extensibilité Produit

**Statut**: Accepté (Principe fondateur)

**Décision**: Architecture ouverte supportant :
1. **Multi-API** : Director API (aujourd'hui) + Direct SIEM API (futur)
2. **API Versioning** : Gestion des versions d'API et évolutions
3. **Multi-produit** : Extensible à d'autres produits du catalogue LogPoint

---

### 1. Multi-API

**Principe**: Le même code métier doit fonctionner avec différentes API cibles.

**Implémentation**:
```yaml
# Fleet spécifie le mode
spec:
  managementMode: director  # ou 'direct'
  director:
    apiHost: "https://director.logpoint.com"
  # direct:  # Futur
  #   apiHost: "https://siem.local"
```

**Connecteurs**:
- `DirectorConnector` : API Director (MSSP, multi-pool)
- `DirectConnector` : API SIEM locale (Enterprise, all-in-one)
- Interface commune `Provider` pour abstraction

---

### 2. API Versioning

**Principe**: Les configurations doivent rester compatibles malgré l'évolution des APIs.

**Implémentation**:
```yaml
apiVersion: cac-configmgr.io/v1   # Version du schéma CaC
kind: ConfigTemplate
metadata:
  name: golden-base
  version: "2.1.0"                # Version du template
```

**Règles**:
- `apiVersion` : Incrémenté sur breaking changes de schéma
- `metadata.version` : Version sémantique du template (SemVer)
- `extends: template@v2` : Référence version spécifique
- Adapter pattern : Même config YAML → différentes API versions

**Exemple d'adaptation**:
```python
# Interne : schéma CaC v1 stable
# Director API v1.3 → mapping direct
# Director API v2.0 → adaptation champ 'repo' → 'repository'
# Direct API v1.0 → adaptation endpoints
```

---

### 3. Multi-produit

**Principe**: L'architecture doit supporter d'autres produits que LogPoint SIEM.

**Implémentation**:
```yaml
metadata:
  provider: logpoint        # Produit cible
  productType: siem         # Type de produit
  # Futur: provider: logpoint, productType: soar
  # Futur: provider: logpoint, productType: ndr
```

**Extensibilité**:
- `kind: ConfigTemplate` : Générique
- `spec.repos` : Spécifique SIEM (ignoré par autres produits)
- `spec.playbooks` : Spécifique SOAR (ignoré par SIEM)
- Validation Pydantic par produit (`LogPointConfig`, `SOARConfig`)

---

**Justification**:
- **Future-proof** : Pas de réécriture majeure pour nouvelles APIs ou produits
- **Investissement protégé** : Temps passé sur les specs YAML réutilisable
- **Alignement stratégique** : Vision LogPoint = plateforme de sécurité, pas juste SIEM

**Limitations actuelles**:
- PoC : Director uniquement (validation du concept)
- Mapping interne → API : À compléter pour chaque nouvelle version

**Future Evolution**:
- Implement `DirectConnector` when SIEM APIs are stable
- Add `apiVersion: cac-configmgr.io/v2` if breaking changes needed
- Create providers for other products in catalog

---

## ADR-008: Name-Based Cross-Reference Validation

**Status**: Accepted (Architecture Principle)

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

**Status**: Accepted (LogPoint Director API Compliance)

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
