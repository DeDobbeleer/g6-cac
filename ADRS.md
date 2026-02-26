# Architecture Decision Records

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

**Évolution future**:
- Implémenter `DirectConnector` quand APIs SIEM stables
- Ajouter `apiVersion: cac-configmgr.io/v2` si breaking changes nécessaires
- Créer providers pour autres produits du catalogue
