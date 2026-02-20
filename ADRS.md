# Logpoint CaC - Architecture Decision Records (ADR)

## ADR-001 : Langage de programmation

### Status
> Proposé

### Contexte
Besoin d'un langage pour implémenter l'outil CLI CaC. Contraintes :
- Facilité de maintenance par l'équipe
- Bonnes librairies HTTP/API
- Facilité de packaging/distribution
- Performance acceptable pour des appels API

### Options considérées

| Langage | Pros | Cons |
|---------|------|------|
| **Python** | Équipe familière, riche écosystème, PyYAML natif, rapidité de dev | Performance, packaging complexe |
| **Go** | Binaire statique, performant, bon pour CLI, typage fort | Courbe d'apprentissage, moins d'équipe familière |
| **Rust** | Performance, sécurité, binaire statique | Complexité, overkill pour ce use case |
| **TypeScript/Node** | Équipe JS possible, bon tooling | Runtime lourd, gestion async complexe |

### Décision
**Python** avec packaging via `uv` / `pex` / `PyInstaller`

### Justification
- L'équipe SOC/DevOps est probablement plus à l'aise avec Python
- Librairies HTTP (httpx, requests) matures
- Pydantic pour la validation de schémas YAML
- Rich/Typer pour des CLI ergonomiques
- Packaging acceptable avec les outils modernes

### Conséquences
- Dépendance Python sur les machines cibles (ou binaire)
- GIL peut limiter le parallélisme (mais I/O bound ici)

---

## ADR-002 : Gestion du state

### Status
> Proposé

### Contexte
L'outil doit maintenir un mapping entre les noms lisibles (YAML) et les IDs internes de Logpoint. Où stocker cet état ?

### Options considérées

| Option | Pros | Cons |
|--------|------|------|
| **Local file** (`.cac/state.json`) | Simple, offline, pas de dépendance | Pas de partage, conflits en équipe |
| **Git** (state.json versionné) | Traçabilité, partage | Risque de conflits, secrets possibles |
| **S3/Object storage** | Partagé, durable, scalable | Dépendance cloud, latence |
| **Etat réel comme source** | Toujours à jour, pas de drift | Lent (requêtes API), pas de cache |

### Décision
**Git + cache local optionnel**

Le state est dérivé de l'état réel via `cac sync` et commité dans Git. Pas de state séparé persistant.

### Justification
- GitOps-friendly : tout est dans Git
- Pas de SPOF sur un backend de state
- Drift detection naturelle (diff Git vs réalité)
- Reproductibilité (checkout + apply)

### Conséquences
- `plan` nécessite des appels API pour résoudre les IDs
- Caching local possible pour accélérer
- Nécessite une connexion API pour la plupart des opérations

---

## ADR-003 : Format de configuration

### Status
> Proposé

### Contexte
Quel format pour définir les ressources Logpoint ?

### Options considérées

| Format | Pros | Cons |
|--------|------|------|
| **YAML** | Lisible, standard, comments | Verbose, indentation sensible |
| **JSON** | Universel, parsing simple | Pas de comments, verbeux |
| **HCL** (Terraform) | Connu des DevOps, modules | Courbe d'apprentissage, complexe |
| **CUE** | Validation forte, langage config | Nouveau, peu connu |
| **TOML** | Simple, comments | Moins standard pour ce use case |

### Décision
**YAML avec schémas Pydantic**

### Justification
- Standard dans l'écosystème K8s/GitOps
- Les équipes SOC sont familières avec YAML
- Pydantic permet validation + auto-completion
- Support natif des comments pour documentation

### Structure
```yaml
apiVersion: logpoint-cac/v1
kind: AlertRule
metadata:
  name: brute-force-ssh
  pool: production-pool-a
spec:
  # ... champs spécifiques
```

---

## ADR-004 : Stratégie de déploiement

### Status
> Proposé

### Contexte
Comment appliquer les changements sur les pools ?

### Options considérées

| Stratégie | Pros | Cons |
|-----------|------|------|
| **All-at-once** | Simple, rapide | Risque élevé, pas de rollback partiel |
| **Sequential** | Contrôle, rollback par étape | Lent |
| **Canary** (un pool) | Sécurité, validation réelle | Complexité, nécessite staging |
| **Blue/Green** | Zero-downtime | Overkill pour de la config |

### Décision
**Sequential avec checkpoint**

Par défaut, appliquer séquentiellement avec possibilité d'arrêt en cas d'erreur. Option `--parallel` pour la vitesse.

### Justification
- API Director n'est pas conçue pour des transactions
- Échec partiel = état inconnu
- Sequential permet rollback ciblé
- Option parallèle pour les cas sûrs (créations uniquement)

### Ordre de déploiement
1. DeviceGroups (dépendances pour les devices)
2. Repos (dépendances pour les alertes)
3. AlertRules
4. Policies
5. SystemSettings

---

## ADR-005 : Authentification

### Status
> Proposé

### Contexte
Comment l'outil s'authentifie-t-il à l'API Director ?

### Options considérées

| Méthode | Pros | Cons |
|---------|------|------|
| **Token en variable d'env** | Simple, standard | Pas de rotation, exposé dans env |
| **Fichier de config** | Persistant, multi-env | Risque de commit accidentel |
| **Vault integration** | Sécurisé, rotation | Complexité, dépendance |
| **OIDC/IAM** | Pas de secret, moderne | Support incertain côté Director |

### Décision
**Hiérarchie : Env var > Config file > Vault (optionnel)**

```bash
# Option 1 : Env
export LOGPOINT_API_TOKEN="..."

# Option 2 : Config file
# ~/.config/logpoint-cac/config.yaml
api_token: "..."

# Option 3 : Vault (si configuré)
vault:
  address: "https://vault.company.com"
  path: "secret/logpoint/api-token"
```

### Justification
- Flexibilité selon les contraintes de l'organisation
- Vault supporté mais pas obligatoire
- Possibilité de rotation via sidecar

---

## ADR-006 : Gestion des erreurs et retry

### Status
> Proposé

### Contexte
Les APIs peuvent échouer (timeout, rate limit, erreur temporaire). Comment gérer ?

### Décision
**Retry avec backoff exponentiel + circuit breaker**

```python
# Configuration par défaut
retry:
  max_attempts: 3
  backoff_base: 1  # secondes
  backoff_max: 30  # secondes
  
circuit_breaker:
  failure_threshold: 5
  recovery_timeout: 60  # secondes
```

### Comportement
- Retry sur 5xx, timeout, connection error
- Pas de retry sur 4xx (client error)
- Circuit breaker après N échecs consécutifs
- Mode "dry-run" pour valider avant apply

---

## ADR-007 : Interface utilisateur

### Status
> Proposé

### Contexte
Quelle forme prend l'outil ? CLI uniquement ? Web UI ?

### Options considérées

| Interface | Pros | Cons |
|-----------|------|------|
| **CLI only** | Simple, scriptable, GitOps natif | Courbe d'apprentissage, pas visuel |
| **CLI + TUI** (Text UI) | Interactif, reste dans le terminal | Complexité, dépendances |
| **Web UI** | Accessible, visuel | SPOF, sécurité, maintenance |
| **CLI + API** | Flexible, intégrations | Overkill pour MVP |

### Décision
**CLI riche (Typer + Rich) d'abord, API interne pour extensions**

### Fonctionnalités CLI
- Output coloré et formaté (tables, arbres)
- Progress bars pour les opérations longues
- Interactive mode pour le debugging
- JSON output pour piping

### Futur possible
- TUI avec `textual` si demande
- Web UI en V2 si nécessaire (lecture seule d'abord)

