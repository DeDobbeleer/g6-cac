# Logpoint CaC - PoC Pipeline de données

Outil CLI pour gérer les configurations de pipeline de données Logpoint via YAML et l'API Director.

## Scope du PoC

**Ressources gérées** :
- ✅ **Repos** - Configuration du stockage
- ✅ **Routing Policies** - Où router les logs
- ✅ **Normalization Policies** - Parser et normaliser
- ✅ **Processing Policies** - Orchestrer le pipeline complet

## Quick Start

```bash
# Installation
pip install -e .

# Valider des configs
python -m lpcac.main validate examples/simple/

# Voir les changements (nécessite accès Director)
export DIRECTOR_URL="https://director.example.com"
export DIRECTOR_TOKEN="..."

python -m lpcac.main plan examples/simple/ \
    --pool="uuid-du-pool" \
    --logpoint="id-logpoint"
```

## Structure

```
lpcac/
├── models/         # Pydantic models (validation)
├── connectors/     # API Director
└── main.py        # CLI

examples/
└── simple/        # Configs d'exemple
    ├── 01-repos.yaml
    ├── 02-routing.yaml
    ├── 03-normalization.yaml
    └── 04-processing.yaml
```

## Documentation

| Fichier | Contenu |
|---------|---------|
| [README_POC.md](./README_POC.md) | Guide démarrage rapide |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | Architecture technique |
| [ADRS.md](./ADRS.md) | Décisions d'architecture |
| [CONSTRAINTS.md](./CONSTRAINTS.md) | Contraintes API |

## Roadmap PoC

- [x] Modèles Pydantic pour les 4 ressources
- [x] Connecteur Director basique
- [x] Commande `validate`
- [x] Commande `plan` (structure)
- [ ] Polling des opérations async
- [ ] Commande `apply` complète
- [ ] Commande `sync` (export YAML)

---

*PoC interne Logpoint - Pipeline de données*
