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
