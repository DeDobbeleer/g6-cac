# Architecture du PoC

## Vue d'ensemble

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Fichiers  │────▶│   Modèles   │────▶│  Connecteur │
│    YAML     │     │   Pydantic  │     │   Director  │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                                        HTTP + polling
                                               │
                                          Director
```

## Flux de données

### 1. Validation (`cac validate`)
```
YAML → Pydantic → Validation stricte → Rapport d'erreurs coloré
```

### 2. Plan (`cac plan`)
```
YAML local → Modèles Pydantic → 
    ↓
Director API → État réel → 
    ↓
Comparaison → Tableau des actions (create/update/delete)
```

### 3. Apply (`cac apply`) - TODO
```
Plan → Exécution séquentielle → 
    ↓
Polling async (Director) → 
    ↓
Rapport de succès/échec
```

## Composants

### Modèles (`lpcac/models/`)

| Fichier | Rôle |
|---------|------|
| `repos.py` | Stockage physique des logs |
| `routing.py` | Routage conditionnel vers repos |
| `normalization.py` | Parsing et normalisation |
| `processing.py` | Orchestration du pipeline |

### Connecteur (`lpcac/connectors/director.py`)

Gère :
- Authentification Bearer Token
- URLs formatées `/configapi/{pool}/{logpoint}/{resource}`
- Opérations async (polling des `request_id`)

## Découpage YAML recommandé

```
configs/
├── 01-repos.yaml           # D'abord les repos
├── 02-routing.yaml         # Puis le routing
├── 03-normalization.yaml   # Puis normalization
└── 04-processing.yaml      # Enfin le pipeline
```

L'ordre des fichiers importe peu, l'ordre des déploiements sera géré par les dépendances.
