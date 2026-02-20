# Logpoint CaC - User Stories

## 👤 Acteurs

| Acteur | Description | Besoins principaux |
|--------|-------------|-------------------|
| **SOC Analyst** | Opérateur SIEM | Modifier alertes, voir l'état |
| **MSSP Engineer** | Ingénieur multi-clients | Déployer configs standardisées |
| **Security Architect** | Architecte sécurité | Gouvernance, conformité |
| **DevOps Engineer** | CI/CD, infrastructure | Automatisation, intégration |
| **CISO** | Direction sécurité | Reporting, audit |

---

## 📖 Stories par acteur

### SOC Analyst

#### US-SOC-001 : Modifier une règle d'alerte
> **En tant que** SOC Analyst  
> **Je veux** modifier une règle d'alerte via une PR Git  
> **Afin de** suivre un process de review et garder un historique

**Critères d'acceptation :**
- [ ] Je peux éditer un fichier YAML d'alerte
- [ ] La CI valide ma syntaxe
- [ ] Un `plan` montre les changements avant merge
- [ ] Après merge, la règle est déployée automatiquement
- [ ] Je reçois une notification du résultat

---

#### US-SOC-002 : Voir les alertes actives
> **En tant que** SOC Analyst  
> **Je veux** lister toutes les alertes d'un pool  
> **Afin de** comprendre la couverture de détection

**Critères d'acceptation :**
- [ ] Commande `cac list alert-rules --pool=prod-a`
- [ ] Affichage formaté (tableau ou JSON)
- [ ] Filtrage par statut (active/inactive)
- [ ] Export possible vers CSV

---

#### US-SOC-003 : Désactiver une alerte rapidement
> **En tant que** SOC Analyst  
> **Je veux** désactiver une alerte bruyante immédiatement  
> **Afin de** réduire le bruit pendant l'investigation

**Critères d'acceptation :**
- [ ] Commande `cac disable alert-rule <name> --pool=prod-a`
- [ ] Confirmation interactive
- [ ] Option `--force` pour bypass
- [ ] Création automatique d'un commit de "hotfix"
- [ ] Notification à l'équipe

---

### MSSP Engineer

#### US-MSSP-001 : Onboarding nouveau client
> **En tant que** MSSP Engineer  
> **Je veux** créer un nouveau pool avec une config standard  
> **Afin de** réduire le temps d'onboarding à < 1h

**Critères d'acceptation :**
- [ ] Template de pool prêt à l'emploi
- [ ] Commande `cac init pool --from-template=mssp-standard`
- [ ] Configuration des alertes de base
- [ ] Configuration des device groups standard
- [ ] Validation post-déploiement

---

#### US-MSSP-002 : Déployer une nouvelle règle sur tous les clients
> **En tant que** MSSP Engineer  
> **Je veux** ajouter une alerte sur tous les pools clients  
> **Afin de** réagir rapidement à une nouvelle menace

**Critères d'acceptation :**
- [ ] Définition de la règle dans `_common/`
- [ ] Commande `cac apply --all-pools`
- [ ] Progression visible (pool X/Y)
- [ ] Rapport de succès/échec par pool
- [ ] Rollback possible si > N% d'échecs

---

#### US-MSSP-003 : Comparer deux environnements clients
> **En tant que** MSSP Engineer  
> **Je veux** comparer les configs de deux pools  
> **Afin de** identifier pourquoi un client n'a pas une règle

**Critères d'acceptation :**
- [ ] Commande `cac diff pool-a pool-b`
- [ ] Diff par type de ressource
- [ ] Export du rapport
- [ ] Suggestion de synchronisation

---

### Security Architect

#### US-ARCH-001 : Audit de conformité
> **En tant que** Security Architect  
> **Je veux** vérifier que tous les pools ont les alertes critiques  
> **Afin de** démontrer la conformité aux audits

**Critères d'acceptation :**
- [ ] Définition de "policies as code" (règles de gouvernance)
- [ ] Commande `cac compliance check`
- [ ] Rapport des écarts
- [ ] Score de conformité par pool
- [ ] Export PDF/CSV pour l'audit

---

#### US-ARCH-002 : Gérer les versions de configuration
> **En tant que** Security Architect  
> **Je veux** taguer des versions de configuration  
> **Afin de** pouvoir revenir à un état connu

**Critères d'acceptation :**
- [ ] Commande `cac tag v1.2.3`
- [ ] Liste des versions `cac history`
- [ ] Rollback `cac rollback v1.2.0`
- [ ] Diff entre versions

---

### DevOps Engineer

#### US-DEVOPS-001 : Intégration CI/CD
> **En tant que** DevOps Engineer  
> **Je veux** intégrer le CaC dans notre pipeline GitLab  
> **Afin de** suivre notre workflow existant

**Critères d'acceptation :**
- [ ] Image Docker officielle
- [ ] Configuration via variables d'env
- [ ] Exit codes standard (0=succès, 1=erreur, 2=drift...)
- [ ] Output machine-readable (JSON)
- [ ] Documentation des jobs GitLab CI

---

#### US-DEVOPS-002 : Monitoring des drifts
> **En tant que** DevOps Engineer  
> **Je veux** détecter les changements manuels non trackés  
> **Afin de** maintenir la cohérence Git ↔ Réalité

**Critères d'acceptation :**
- [ ] Cron job `cac drift detect`
- [ ] Alertes sur drift détecté
- [ ] Auto-remediation optionnelle
- [ ] Dashboard des drifts

---

#### US-DEVOPS-003 : Backup automatisé
> **En tant que** DevOps Engineer  
> **Je veux** sauvegarder les configs quotidiennement  
> **Afin de** pouvoir restaurer en cas d'incident

**Critères d'acceptation :**
- [ ] Commande `cac backup --all-pools`
- [ ] Stockage S3 / object storage
- [ ] Rétention configurable
- [ ] Chiffrement des backups
- [ ] Test de restore régulier

---

### CISO

#### US-CISO-001 : Reporting global
> **En tant que** CISO  
> **Je veux** un dashboard de l'état des SIEMs  
> **Afin de** présenter la posture de sécurité au board

**Critères d'acceptation :**
- [ ] Nombre de pools gérés
- [ ] Nombre d'alertes actives
- [ ] Taux de conformité
- [ ] Derniers changements
- [ ] Export exécutif

---

## 🔗 Dépendances entre stories

```
US-DEVOPS-001 (CI/CD)
    └── US-SOC-001 (PR workflow)
        └── US-SOC-003 (Hotfix)

US-MSSP-001 (Onboarding)
    └── US-DEVOPS-002 (Drift detect)
        └── US-ARCH-001 (Compliance)

US-MSSP-002 (Multi-pool deploy)
    └── US-MSSP-003 (Diff)
```

---

## 📊 Priorisation MoSCoW

### Must have (MVP)
- US-SOC-001 : Modifier alerte via PR
- US-MSSP-001 : Onboarding pool
- US-DEVOPS-001 : CI/CD integration
- US-DEVOPS-002 : Drift detection

### Should have (V1.1)
- US-SOC-002 : List alertes
- US-MSSP-002 : Multi-pool deploy
- US-ARCH-002 : Versioning

### Could have (V1.2)
- US-SOC-003 : Hotfix rapide
- US-MSSP-003 : Diff pools
- US-ARCH-001 : Compliance

### Won't have (V2+)
- US-CISO-001 : Dashboard (peut utiliser logs)
- US-DEVOPS-003 : Backup (scriptable via existing)

