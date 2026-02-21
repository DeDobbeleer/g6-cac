# PoC - Pipeline de données Logpoint

**Scope** : Repos + Routing Policies + Normalization Policies + Processing Policies

## Structure

```
lpcac/
├── models/           # Modèles Pydantic
│   ├── repos.py
│   ├── routing.py
│   ├── normalization.py
│   └── processing.py
├── connectors/       # Connecteurs API
│   └── director.py
└── main.py          # CLI

examples/
└── simple/          # Exemples réalistes
    ├── 01-repos.yaml
    ├── 02-routing.yaml
    ├── 03-normalization.yaml
    └── 04-processing.yaml
```

## Démarrage rapide

```bash
# 1. Installer
pip install -e .

# 2. Valider des configs
python -m lpcac.main validate examples/simple/

# 3. Comparer avec un Director (nécessite credentials)
export DIRECTOR_URL="https://director.example.com"
export DIRECTOR_TOKEN="..."

python -m lpcac.main plan examples/simple/ \
    --pool="uuid-pool" \
    --logpoint="lp-01"
```

## Ressources gérées

| Ressource | Description | Dépendances |
|-----------|-------------|-------------|
| `Repo` | Où stocker les logs | Aucune (base) |
| `RoutingPolicy` | Choisir le repo selon le contenu | Repos |
| `NormalizationPolicy` | Parser/normaliser les logs | Aucune (mais utilisée par Processing) |
| `ProcessingPolicy` | Orchestrer le pipeline complet | Routing + Normalization |

## Prochaines étapes du PoC

1. [ ] Connecteur : Gérer le polling async des opérations
2. [ ] Plan : Afficher un vrai diff (quoi créer/modifier/supprimer)
3. [ ] Apply : Appliquer les changements sur Director
4. [ ] Sync : Exporter l'état réel vers YAML
5. [ ] Drift : Détecter les écarts automatiquement

## Exemple métier

**Use case** : Nouveau client MSSP, déploiement du pipeline standard

```bash
# 1. Valider les configs du client
cac validate ./clients/acme-corp/

# 2. Voir ce qui va changer
cac plan ./clients/acme-corp/ --pool=pool-acme --logpoint=lp-01

# 3. Appliquer
cac apply ./clients/acme-corp/ --pool=pool-acme --logpoint=lp-01 --auto-approve
```

**Temps estimé** : < 5 minutes vs 2-3 heures en manuel
