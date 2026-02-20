# Logpoint CaC - Contraintes Techniques Détaillées

## 🔌 API Director - Spécificités techniques

### Modèle asynchrone

Toutes les opérations de modification (POST/PUT/DELETE) retournent immédiatement avec un `request_id` :

```json
{
    "status": "Success",
    "message": "/monitorapi/{pool_UUID}/{logpoint_identifier}/orders/{request_id}"
}
```

Le client doit ensuite poller :
```
GET /monitorapi/{pool_UUID}/{logpoint_identifier}/orders/{request_id}
```

**Implications CaC :**
- Chaque ressource modifiée = 1+ requêtes de polling
- Timeout à définir (suggéré : 5 min max)
- Retry avec backoff exponentiel
- Gestion des cas "pending" trop long

### Pas d'opérations atomiques

- Pas de transactions multi-ressources
- Pas de rollback automatique côté API
- Échec à l'étape N = état partiellement modifié

**Stratégie CaC :**
- Plan d'application ordonné (dépendances)
- Checkpoint après chaque ressource
- Possibilité de rollback manuel
- Mode "dry-run" exhaustif avant apply

### Limitations identifiées

| Limitation | Détail | Mitigation |
|------------|--------|------------|
| Pas de bulk API | 1 requête par ressource | Batch côté client + parallélisation |
| Pas de query complexe | GET liste sans filtre | Filtrage côté client |
| IDs opaques | IDs MongoDB (ex: `5a466fc9d8aaa4748d3977c9`) | Mapping nom ↔ ID dans le state |
| Pas de versioning API | Version implicite | Tests de compatibilité par version Director |

---

## 🌐 Contraintes réseau

### Architecture VPN

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   Client    │◀───────▶│    API      │◀───────▶│   Fabric    │
│    CaC      │  HTTPS  │   Server    │  VPN    │   Server    │
└─────────────┘         └─────────────┘         └──────┬──────┘
                                                       │
                              ┌────────────────────────┼────────────────────────┐
                              │                        │                        │
                              ▼                        ▼                        ▼
                        ┌─────────┐              ┌─────────┐              ┌─────────┐
                        │ Pool A  │              │ Pool B  │              │ Pool C  │
                        │ Logpoint│              │ Logpoint│              │ Logpoint│
                        └─────────┘              └─────────┘              └─────────┘
```

**Implications :**
- Latence variable selon le pool
- Timeouts à calibrer par environnement
- Possibilité de déconnexion VPN

### Scénarios de défaillance

| Scénario | Probabilité | Impact | Gestion |
|----------|-------------|--------|---------|
| Timeout API | Moyenne | Apply partiel | Retry idempotent |
| Déconnexion VPN | Faible | Pool inaccessible | Marquer comme unavailable |
| API Director down | Faible | Global | Queue + retry |
| Rate limiting | Inconnue | Ralentissement | Backoff adaptatif |

---

## 🔄 Mode Normal vs Co-Managed

### Matrice de disponibilité des APIs

| API | Mode Normal | Co-Managed | Impact CaC |
|-----|-------------|------------|------------|
| DeviceGroups | ✅ Full | ❌ Restricted | Détection du mode requise |
| Repos | ✅ Full | ❌ Restricted | - |
| AlertRules | ✅ Full | ⚠️ Read-only | LPSM pour modifications |
| Policies | ✅ Full | ❌ Restricted | - |
| SystemSettings | ✅ Full | ⚠️ Partial | - |

**Détection du mode :**
```
GET /configapi/{pool_UUID}/{logpoint_identifier}/SystemSettingsGeneral
→ Champ `fabric_connect_mode` dans la réponse
```

---

## 📦 Format des données

### IDs et références

Les APIs utilisent des IDs internes opaques. Pour le CaC, on veut des noms lisibles.

**Mapping nécessaire :**
```yaml
# Config utilisateur (nom lisible)
device_groups:
  - name: "firewall-perimeter"
    
# State interne (mapping)
state:
  device_groups:
    firewall-perimeter:
      id: "574fb123d8aaa4625bfe2d23"
      etag: "abc123"  # Pour le caching
```

### Champs calculés vs stockés

| Champ | Type | Gestion |
|-------|------|---------|
| `id` | Généré par LP | Ignoré en input, stocké en state |
| `owner` | Référence utilisateur | Résolution par nom/username |
| `repos` | Liste de chemins | Validation des paths disponibles |
| `devices` | Liste d'IDs | Résolution par IP/nom ? |

---

## 🔒 Sécurité

### Authentification

**Méthode :** API Token (à confirmer avec la doc)
```
Header: Authorization: Bearer {token}
# ou
Header: X-API-Key: {key}
```

**Rotation :**
- Tokens avec expiration ?
- Support du OAuth2 ?
- Possibilité de service accounts ?

### Permissions requises

Rôle Director minimal pour le service CaC :
- `configapi:read` - Pour plan/diff
- `configapi:write` - Pour apply
- `monitorapi:read` - Pour polling des opérations

---

## 📊 Observabilité

### Métriques à exposer

| Métrique | Type | Description |
|----------|------|-------------|
| `cac_apply_duration` | Histogram | Temps total d'apply |
| `cac_resources_changed` | Counter | Nombre de ressources modifiées |
| `cac_api_requests_total` | Counter | Requêtes API (par endpoint, status) |
| `cac_api_latency` | Histogram | Latence des appels API |
| `cac_drift_detected` | Gauge | Nombre de drifts détectés |

### Logs structurés

```json
{
  "timestamp": "2026-02-20T14:30:00Z",
  "level": "info",
  "component": "cac-engine",
  "operation": "apply",
  "pool": "production-pool-a",
  "logpoint": "lp-01",
  "resource": "AlertRules",
  "resource_name": "brute-force-ssh",
  "action": "create",
  "request_id": "req-abc123",
  "status": "success",
  "duration_ms": 2450
}
```

---

## 🧪 Testabilité

### Environnements de test

| Environnement | Usage | Contraintes |
|---------------|-------|-------------|
| Unit tests | Logique interne | Mock complet des APIs |
| Integration tests | Appels API réels | Instance Director de test |
| Staging | Déploiement réel | Replica réduit de la prod |
| Dry-run sur prod | Validation | Aucune modification |

### Mock des APIs

Structure suggérée pour les tests :
```python
class DirectorAPIMock:
    def __init__(self):
        self.state = {}  # État simulé
        self.latency = lambda: random.uniform(0.1, 0.5)
        self.failure_rate = 0.05  # 5% d'échecs
```

---

## 📝 Notes de compatibilité

### Versions Director supportées

| Version | Status | Notes |
|---------|--------|-------|
| < 1.3.0 | ❌ Non supporté | Pas de backward compat |
| 1.3.0+ | ✅ Supporté | Multi-version Logpoint |
| 2.x | ✅ Cible principale | Dernières features |

### Compatibilité Logpoint

- Logpoint 6.6.0+ requis pour multi-version
- Certaines features dépendent de la version LP (pas Director)

