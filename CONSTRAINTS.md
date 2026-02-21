# Contraintes techniques

## API Director

### Opérations asynchrones
Toutes les modifications (POST/PUT/DELETE) retournent immédiatement avec un `request_id`:

```json
{
    "status": "Success",
    "message": "/monitorapi/{pool}/{logpoint}/orders/{request_id}"
}
```

Le client doit poller :
```
GET /monitorapi/{pool}/{logpoint}/orders/{request_id}
```

**Impact**: Temps d'apply = nombre de ressources × temps de polling (~1-5s par ressource).

### Pas de bulk API
Une requête par ressource. Pour créer 10 repos = 10 appels + 10 pollings.

### Pas de transactions
Si étape 3/5 échoue, les étapes 1-2 restent appliquées. Pas de rollback automatique.

**Mitigation**: Validation exhaustive en `plan` avant `apply`.

### Mode Co-Managed
Certaines APIs sont restreintes en mode Co-Managed (géré par Logpoint).

## Dépendances des ressources

```
Repos ───────────────────────────────────────┐
     │                                        │
     ▼                                        ▼
RoutingPolicies ───────┐              ProcessingPolicies
                       │                       ▲
                       ▼                       │
NormalizationPolicies ─┘───────────────────────┘
```

**Ordre de déploiement obligatoire**:
1. Repos (base)
2. Routing Policies (besoin des noms de repos)
3. Normalization Policies (indépendant)
4. Processing Policies (besoin des noms des autres)

## IDs Logpoint

Les APIs utilisent des IDs internes opaques (MongoDB ObjectId: `5a466fc9d8aaa4748d3977c9`).

**Mapping requis** dans le CaC:
- YAML utilise des noms lisibles (`default`, `alerts`, `firewall-logs`)
- Connecteur maintient mapping nom → ID pour les updates
