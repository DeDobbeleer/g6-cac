# Logpoint CaC - Spécifications et Attentes

## 📋 Vue d'ensemble du projet

Outil de **Configuration as Code (CaC)** pour la gestion centralisée des configurations Logpoint Director à travers multiples pools et instances SIEM.

---

## 🎯 Objectifs métier

### Pourquoi ce projet ?
- [ ] Standardiser les configurations SIEM entre environnements (dev/staging/prod)
- [ ] Réduire les erreurs de configuration manuelle
- [ ] Faciliter le déploiement de nouveaux pools/clients
- [ ] Permettre la revue de code sur les changements SIEM
- [ ] Audit trail complet des modifications
- [ ] Recovery rapide en cas d'incident

### Cas d'usage prioritaires
1. **Onboarding client MSSP** : Déployer une config standard sur un nouveau pool
2. **Update massif** : Modifier une règle d'alerte sur tous les pools
3. **Drift detection** : Détecter les écarts entre config déclarée et réelle
4. **Backup/Restore** : Sauvegarder et restaurer des configurations

---

## 🏗️ Scope fonctionnel

### Ressources gérées (priorisé)

| Priorité | Ressource | Justification |
|----------|-----------|---------------|
| P0 | AlertRules | Cœur métier, changements fréquents |
| P0 | DeviceGroups | Structure fondamentale |
| P0 | Repos | Stockage des logs |
| P1 | Policies | Règles de traitement |
| P1 | SystemSettingsSNMP | Monitoring |
| P2 | Dashboards | Visibilité opérationnelle |
| P2 | Reports | Reporting client |
| P3 | Users/Permissions | Gouvernance |

### Opérations supportées

| Opération | Description |
|-----------|-------------|
| `plan` | Voir les changements avant application |
| `apply` | Appliquer les changements |
| `sync` | Synchroniser depuis l'état réel |
| `validate` | Valider la syntaxe YAML |
| `diff` | Comparer deux environnements |
| `backup` | Exporter la config actuelle |
| `drift` | Détecter les écarts |

---

## 🔒 Contraintes et exigences

### Contraintes techniques

| Catégorie | Contrainte | Impact |
|-----------|------------|--------|
| API Director | Toutes les modifications sont async (request_id) | Gestion de polling nécessaire |
| API Director | Rate limiting inconnu | Implémenter backoff/retry |
| API Director | Pas de bulk operations | Requêtes séquentielles |
| Logpoint | Mode Normal vs Co-Managed | Certaines APIs indisponibles en Co-Managed |
| Réseau | VPN tunnels entre pools | Latence variable |

### Exigences non-fonctionnelles

| Exigence | Critère | Commentaire |
|----------|---------|-------------|
| Disponibilité | 99.9% pour l'outil CaC | Pas de SPOF sur le déploiement |
| Performance | < 5 min pour apply sur 10 pools | Parallélisation nécessaire |
| Sécurité | Pas de secrets en clair dans les YAML | Intégration vault (HashiCorp, AWS SM...) |
| Audit | Log de toutes les actions | Qui, quoi, quand, résultat |
| Rollback | Possibilité de revenir en arrière | Versioning des configs |

---

## 🗂️ Structure des configurations

### Hiérarchie proposée

```
configs/
├── _common/                    # Configurations partagées
│   ├── alert-rules/
│   │   └── critical-security.yaml
│   ├── device-groups/
│   │   └── standard-groups.yaml
│   └── policies/
│       └── default-policy.yaml
│
├── _templates/                 # Templates pour nouveaux pools
│   └── mssp-client-template/
│       ├── pool.yaml
│       └── logpoints/
│
├── production/
│   ├── pool-a/
│   │   ├── pool.yaml           # Métadonnées du pool
│   │   ├── logpoints/
│   │   │   ├── lp-01.yaml
│   │   │   └── lp-02.yaml
│   │   └── kustomization.yaml  # Inclusion des configs communes
│   │
│   └── pool-b/
│       └── ...
│
└── staging/
    └── ...
```

### Format du fichier de configuration

```yaml
# Version du schéma CaC
apiVersion: logpoint-cac/v1
kind: PoolConfig

metadata:
  pool_uuid: "uuid-here"
  pool_name: "production-pool-a"
  environment: "production"
  managed_by: "cac-tool"
  
spec:
  # Référence aux configs communes à inclure
  includes:
    - path: "_common/alert-rules/critical-security.yaml"
      override: true  # Permet de surcharger
    
  logpoints:
    - identifier: "lp-prod-01"
      
      device_groups:
        - name: "perimeter-firewalls"
          description: "Firewalls de périmètre"
          devices: 
            - ref: "device-uuid-1"  # Référence dynamique ?
            
      repos:
        - name: "default"
          paths:
            - path: "/opt/immune/storage/"
              retention_days: 365
              
      alert_rules:
        - name: "brute-force-ssh"
          query: "device_type=firewall AND (msg=\"Failed password\" OR msg=\"Authentication failure\") | chart count() by source_ip"
          risk: "high"
          condition_option: "greaterthan"
          condition_value: 5
          timerange_minute: 10
          repos: ["default"]
          # ... autres champs
```

---

## 🔐 Gestion des secrets

### Secrets nécessaires

| Secret | Usage | Stockage |
|--------|-------|----------|
| API token Director | Authentification API | Vault |
| Credentials Logpoint (si nécessaire) | Accès direct aux LP | Vault |
| Clés de chiffrement | Chiffrement des backups | Vault/KMS |

### Approche recommandée

```yaml
# Dans le YAML - références aux secrets, pas les valeurs
spec:
  alert_rules:
    - name: "webhook-alert"
      webhook_url: "${vault:secret/data/webhooks#production-url}"
      # ou
      webhook_url_ref:
        provider: "vault"
        path: "secret/data/webhooks"
        key: "production-url"
```

---

## 📊 Workflow GitOps (proposition)

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Commit    │────▶│    CI       │────▶│   Validate  │
│   sur PR    │     │   (lint)    │     │   (plan)    │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                                               ▼
                                        ┌─────────────┐
                                        │   Review    │
                                        │   humaine   │
                                        └──────┬──────┘
                                               │
                                               ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Drift     │◀────│    CD       │◀────│    Merge    │
│   detect    │     │   (apply)   │     │    PR       │
└─────────────┘     └─────────────┘     └─────────────┘
```

---

## ❓ Questions ouvertes

### À clarifier avant l'archi

- [ ] Combien de pools à gérer ? (10, 100, 1000+)
- [ ] Fréquence des changements ? (quotidien, hebdo)
- [ ] Environnements à gérer ? (dev/staging/prod)
- [ ] Équipe qui utilisera l'outil ? (SOC, DevOps, MSSP)
- [ ] Contraintes réseau ? (air-gapped, proxy)
- [ ] Outils existants à intégrer ? (Terraform, Ansible, Puppet)
- [ ] SLAs sur les déploiements ?
- [ ] Besoin de multi-tenancy ?

### Décisions d'architecture à prendre

- [ ] Langage : Python vs Go vs autre ?
- [ ] State : local vs remote (S3, DB) ?
- [ ] Distribution : CLI standalone vs container vs web UI ?
- [ ] Orchestration : GitOps natif vs CI/CD existant ?

---

## 📚 Références

- [Documentation Director API](https://docs.logpoint.com/director)
- [API AlertRules](https://docs.logpoint.com/director/director-apis/director-console-api-documentation/alertrules)
- [API DeviceGroups](https://docs.logpoint.com/director/director-apis/director-console-api-documentation/devicegroups)
- [API Repos](https://docs.logpoint.com/director/director-apis/director-console-api-documentation/repos)

---

## 📝 Changelog

| Date | Auteur | Description |
|------|--------|-------------|
| 2026-02-20 | - | Création initiale |
