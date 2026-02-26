# CLI Workflow Specification

**Version**: 1.0  
**Status**: 🚧 Draft  
**Date**: 2026-02-26  
**Author**: CaC-ConfigMgr Product Team  

---

## 1. Executive Summary

Spécification des commandes CLI et du workflow CaC-ConfigMgr :

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Validate  │───→│    Plan     │───→│    Apply    │───→│    Drift    │
│  (syntaxe)  │    │   (diff)    │    │  (deploy)   │    │  (monitor)  │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │                  │                  │                  │
       └──────────────────┴──────────────────┴──────────────────┘
                          Workflow itératif
```

---

## 2. Command Overview

### 2.1 Command Structure

```bash
cac-configmgr <command> [subcommand] [flags] [args]
```

### 2.2 Command Summary

| Command | Description | Idempotent | Safe |
|---------|-------------|------------|------|
| `validate` | Vérifie syntaxe et cohérence | ✅ Oui | ✅ Read-only |
| `plan` | Calcule et affiche le diff | ✅ Oui | ✅ Read-only |
| `apply` | Applique les changements | ✅ Oui | ⚠️ Modifie SIEM |
| `drift` | Détecte divergences | ✅ Oui | ✅ Read-only |
| `backup` | Exporte configuration actuelle | ✅ Oui | ✅ Read-only |
| `version` | Affiche version | ✅ Oui | ✅ Read-only |

---

## 3. Validate Command

### 3.1 Usage

```bash
# Valider un fichier fleet
cac-configmgr validate fleet.yaml

# Valider un template
cac-configmgr validate --template templates/mssp/acme-corp/base/

# Valider une instance complète (fleet + topology)
cac-configmgr validate --fleet instances/client-dupont/prod/fleet.yaml \
                       --topology instances/client-dupont/prod/instance.yaml

# Valider sans connexion API (offline)
cac-configmgr validate --offline fleet.yaml
```

### 3.2 Validation Levels

| Level | Description | Sortie |
|-------|-------------|--------|
| **Syntax** | YAML valide, schéma respecté | Errors/Warnings |
| **References** | Tous les refs résolvables | Errors (unresolved refs) |
| **API Check** | Ressources externes existent | Errors (missing packages/sources) |
| **Dry-run** | Test contre API réelle | Success/Errors |

### 3.3 Exit Codes

| Code | Signification |
|------|---------------|
| 0 | Validation réussie, aucun warning |
| 1 | Validation réussie, warnings présents |
| 2 | Erreurs de validation |
| 3 | Erreur système/connexion |

### 3.4 Output Format

```bash
# Format text (défaut)
cac-configmgr validate fleet.yaml
✓ fleet.yaml: Valid
✓ 12 nodes defined
✓ 3 clusters resolved
✓ All references valid
⚠ Warning: DN 'dn-legacy-site' has no cluster tag

# Format JSON
cac-configmgr validate --output json fleet.yaml
```

```json
{
  "valid": true,
  "warnings": [
    {
      "file": "fleet.yaml",
      "line": 45,
      "message": "DN 'dn-legacy-site' has no cluster tag",
      "severity": "warning"
    }
  ],
  "errors": [],
  "summary": {
    "nodes": 12,
    "clusters": 3,
    "references_resolved": 8
  }
}
```

---

## 4. Plan Command

### 4.1 Usage

```bash
# Plan sur une instance complète
cac-configmgr plan --fleet instances/client-dupont/prod/fleet.yaml \
                   --topology instances/client-dupont/prod/instance.yaml

# Plan avec détails complets
cac-configmgr plan --detailed ...

# Plan format JSON (pour CI/CD)
cac-configmgr plan --output json ...

# Comparer deux topologies
cac-configmgr plan --base topology-staging.yaml \
                   --target topology-prod.yaml
```

### 4.2 Output: Resource Changes

```
$ cac-configmgr plan --fleet fleet.yaml --topology instance.yaml

Planning changes for client: banque-dupont-prod

Repos (3 changes):
  + CREATE repo-trading (new in instance)
  ~ UPDATE repo-secu (retention: 90 → 7)
  - DELETE repo-temp (not in target)

Routing Policies (2 changes):
  ~ UPDATE rp-windows (3 criteria modified)
    + ADD crit-powershell
    ~ MODIFY crit-verbose (repo changed)
  + CREATE rp-paloalto

Processing Policies (1 change):
  + CREATE pp-lateral-movement

Summary:
  Create: 3  Update: 2  Delete: 1  Unchanged: 12
```

### 4.3 Change Types

| Symbol | Type | Description |
|--------|------|-------------|
| `+` | CREATE | Nouvelle ressource |
| `~` | UPDATE | Modification ressource existante |
| `-` | DELETE | Suppression ressource |
| `=` | UNCHANGED | Aucun changement |
| `?` | UNKNOWN | Impossible à déterminer (API error) |

### 4.4 Detailed Diff

```bash
$ cac-configmgr plan --detailed ...

~ UPDATE repo-secu
    hiddenrepopath[0] (fast-tier):
      retention: 90 → 7
      path: /opt/immune/storage (unchanged)
    
    hiddenrepopath[2] (nfs-tier):
      + ADD new tier
        path: /opt/immune/storage-nfs
        retention: 3650
```

---

## 5. Apply Command

### 5.1 Usage

```bash
# Apply interactif (demande confirmation)
cac-configmgr apply --fleet fleet.yaml --topology instance.yaml

# Apply auto-apprové (CI/CD)
cac-configmgr apply --auto-approve fleet.yaml topology.yaml

# Apply avec batch size (limiter appels API)
cac-configmgr apply --batch-size 10 ...

# Apply uniquement certaines ressources
cac-configmgr apply --only repos,routing-policies ...

# Dry-run apply (test sans modifier)
cac-configmgr apply --dry-run ...
```

### 5.2 Interactive Mode

```
$ cac-configmgr apply ...

Planning complete. 6 resources will be changed:
  Create: 3  Update: 2  Delete: 1

Do you want to apply these changes? [y/N/d(details)/q(quit)]: y

Applying changes...
[1/6] Creating repo-trading......................... ✓ Done (2.3s)
[2/6] Updating repo-secu............................ ✓ Done (1.1s)
[3/6] Deleting repo-temp............................ ✓ Done (0.8s)
[4/6] Creating rp-paloalto.......................... ⏳ Pending (async)
        Request ID: req-abc-123
        Polling status... Done (5.2s)
[5/6] Updating rp-windows........................... ✓ Done (1.5s)
[6/6] Creating pp-lateral-movement.................. ✓ Done (2.0s)

Apply complete! Resources: 6 changed, 12 unchanged
Duration: 13.1s

Run 'cac-configmgr drift' to verify configuration matches target.
```

### 5.3 Rollback

```bash
# Créer un backup avant apply
cac-configmgr backup --output backup-$(date +%Y%m%d).yaml ...

# En cas d'erreur partielle
$ cac-configmgr apply ...
[1/6] Creating repo-trading......................... ✓ Done
[2/6] Updating repo-secu............................ ✗ FAILED
        Error: API returned 400 - Invalid retention value
        
Applied: 1, Failed: 1, Remaining: 4

Options:
  [c]ontinue - Continue with remaining changes
  [r]ollback - Undo successful changes (repo-trading)
  [a]bort    - Stop, partial state remains

# Rollback manuel
$ cac-configmgr apply --rollback backup-20260226.yaml
```

### 5.4 Progress Tracking

| État | Indicateur | Description |
|------|------------|-------------|
| Pending | ⏳ | En attente d'exécution |
| In Progress | 🔄 | Requête API envoyée |
| Async Wait | ⏱️ | Opération asynchrone, polling |
| Success | ✓ | Terminé avec succès |
| Failed | ✗ | Erreur, non appliqué |
| Skipped | ⊘ | Ignoré (dépendance failed) |

### 5.5 Exit Codes Apply

| Code | Signification |
|------|---------------|
| 0 | Tous les changements appliqués |
| 1 | Partiellement appliqué (certains failed) |
| 2 | Erreur avant application (validation failed) |
| 3 | Erreur système |

---

## 6. Drift Command

### 6.1 Usage

```bash
# Détecter drift sur une instance
cac-configmgr drift detect --fleet fleet.yaml --topology instance.yaml

# Drift sur tout un pool
cac-configmgr drift detect --pool acme-corp

# Drift avec format JSON
cac-configmgr drift detect --output json ...

# Drift continu (watch mode)
cac-configmgr drift watch --interval 5m ...

# Réparer le drift (remettre à la cible)
cac-configmgr drift reconcile --fleet fleet.yaml --topology instance.yaml
```

### 6.2 Drift Types

| Type | Description | Exemple |
|------|-------------|---------|
| **Definition Drift** | Config YAML différente de l'attendu | Retention changé manuellement dans UI |
| **External Change** | Modification externe non reflétée | Admin ajoute repo via Director |
| **Orphan Resource** | Ressource existe en prod mais pas dans YAML | Old test repo oublié |
| **Missing Resource** | Ressource dans YAML mais pas en prod | Apply partiellement failed |

### 6.3 Drift Detection Output

```
$ cac-configmgr drift detect ...

Drift detected for client: banque-dupont-prod

DEFINITION DRIFT (2):
  ! repo-secu
    Actual:   retention=180
    Expected: retention=7 (from instance.yaml)
    Source:   Manual UI change by admin@acme.com (2026-02-25 14:32)

  ! rp-windows.crit-verbose
    Actual:   repo=repo-system
    Expected: repo=repo-system-verbose

EXTERNAL CHANGES (1):
  + repo-manual-test (not in YAML)
    Created: 2026-02-24 09:15 by john.doe@acme.com
    Action: Review and add to YAML or delete

ORPHAN RESOURCES (1):
  ? repo-old-legacy
    Last log: 2024-12-01 (2+ months ago)
    Recommendation: Safe to delete

Summary: 4 drifts detected (2 critical, 2 warnings)
```

### 6.4 Drift Configuration

```yaml
# .cac-configmgr.yaml (project config)
drift:
  ignore:
    - type: repo
      name: temp-*           # Ignorer les repos temporaires
    - type: routing-policy
      name: test-*
  
  threshold:
    critical: 5              # Alert si >5 drifts critiques
    warning: 10              # Warn si >10 drifts
  
  auto-reconcile: false      # Jamais auto (sécurité)
  # auto-reconcile: warning  # Uniquement warnings
  # auto-reconcile: all      # Tout (dangereux)
```

---

## 7. Backup Command

### 7.1 Usage

```bash
# Backup complet d'une instance
cac-configmgr backup --fleet fleet.yaml --output backup.yaml

# Backup spécifique
cac-configmgr backup --only repos,routing-policies ...

# Backup avec timestamp auto
cac-configmgr backup --fleet fleet.yaml --output-dir ./backups/
# Crée: backups/backup-2026-02-26T143052.yaml

# Backup format JSON (machine-readable)
cac-configmgr backup --output json ...
```

### 7.2 Backup Output Format

```yaml
# backup-20260226.yaml
apiVersion: cac-configmgr.io/v1
kind: Backup
metadata:
  timestamp: "2026-02-26T14:30:52Z"
  source: "banque-dupont-prod"
  toolVersion: "1.0.0"
  
spec:
  repos:
    - name: repo-secu
      hiddenrepopath: [...]
      
  routingPolicies:
    - policy_name: rp-windows
      routing_criteria: [...]
      
  # ... autres ressources
```

---

## 8. Global Flags

### 8.1 Flags Universels

| Flag | Description | Défaut |
|------|-------------|--------|
| `--config` | Fichier config CLI | `~/.config/cac-configmgr/config.yaml` |
| `--log-level` | Niveau log (debug, info, warn, error) | `info` |
| `--output` | Format sortie (text, json, yaml) | `text` |
| `--no-color` | Désactiver couleurs | `false` |
| `--timeout` | Timeout API (secondes) | `300` |
| `--retry` | Nombre retries | `3` |

### 8.2 Configuration File

```yaml
# ~/.config/cac-configmgr/config.yaml
defaults:
  log_level: info
  output: text
  timeout: 300
  
director:
  api_host: https://director.logpoint.com
  credentials_source: env  # env, file, keyring
  
features:
  auto_approve: false
  drift_watch_interval: 5m
  
aliases:
  prod: instances/client-dupont/prod/
  staging: instances/client-dupont/staging/
```

---

## 9. Workflow Examples

### 9.1 Development Workflow

```bash
# 1. Modifier templates
vim templates/mssp/acme-corp/base/repos.yaml

# 2. Valider localement
cac-configmgr validate --template templates/mssp/acme-corp/base/

# 3. Plan sur staging
cac-configmgr plan --fleet instances/client-dupont/staging/fleet.yaml \
                   --topology instances/client-dupont/staging/instance.yaml

# 4. Apply sur staging
cac-configmgr apply --fleet instances/client-dupont/staging/fleet.yaml \
                    --topology instances/client-dupont/staging/instance.yaml

# 5. Vérifier drift
cac-configmgr drift detect --fleet ... --topology ...

# 6. Même process sur prod
cac-configmgr plan --fleet instances/client-dupont/prod/...
cac-configmgr apply --auto-approve ...  # Si CI/CD validé
```

### 9.2 CI/CD Workflow

```yaml
# .github/workflows/deploy.yml
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Validate configurations
        run: cac-configmgr validate --recursive ./instances/
      
  plan:
    needs: validate
    steps:
      - name: Generate plan
        run: cac-configmgr plan --output json ... > plan.json
      - name: Upload plan
        uses: actions/upload-artifact@v4
        with:
          name: deployment-plan
          path: plan.json
          
  apply:
    needs: plan
    environment: production  # Require manual approval
    steps:
      - name: Apply changes
        run: cac-configmgr apply --auto-approve ...
      - name: Verify no drift
        run: cac-configmgr drift detect ...
```

### 9.3 Emergency Response

```bash
# Incident: Besoin de changer retention immédiatement

# 1. Modifier l'instance
vim instances/client-dupont/prod/instance.yaml
# Changer: retention: 7 → retention: 1

# 2. Valider rapidement
cac-configmgr validate --offline instance.yaml

# 3. Apply avec confirmation explicite
cac-configmgr apply --only repos ...
# Confirmer: y

# 4. Vérifier
cac-configmgr drift detect ...
```

---

## 10. Error Handling & Messages

### 10.1 Error Categories

| Category | Exemple | Action Utilisateur |
|----------|---------|-------------------|
| **Validation** | "Invalid YAML syntax" | Corriger fichier |
| **Reference** | "Repo 'repo-x' not found" | Ajouter définition |
| **API** | "Director API returned 503" | Réessayer plus tard |
| **Permission** | "Insufficient permissions" | Vérifier token |
| **Conflict** | "Resource modified by another" | Refresh et retry |

### 10.2 Error Format

```
ERROR: Failed to apply routing policy 'rp-windows'

Details:
  File: templates/mssp/acme-corp/base/routing-policies.yaml:45
  API Error: 400 Bad Request
  Message: "Invalid criterion: key 'EventTypeX' not recognized"
  
Suggestion:
  Valid keys for Windows events: EventType, EventID, Level, ProviderName
  
Documentation:
  https://docs.cac-configmgr.io/errors/INVALID_CRITERION_KEY
```

---

## 11. Open Questions

1. **State Management**: Faut-il un fichier d'état (terraform.tfstate-like) ou stateless pur ?
2. **Concurrency**: Comment gérer apply simultanés sur même instance ?
3. **Partial Apply**: Comment reprendre un apply partiellement failed ?
4. **Locking**: Faut-il locker une instance pendant apply ?
5. **Audit**: Où stocker l'historique des apply ?

---

## Appendix A: Quick Reference Card

```
CAC-CONFIGMGR - QUICK REFERENCE
═══════════════════════════════════════════════════════════════

VALIDATE
  validate fleet.yaml                    Valider fichier
  validate --template dir/               Valider template
  validate --fleet f.yaml --topology t   Valider instance

PLAN
  plan --fleet f.yaml --topology t       Voir changements
  plan --detailed                        Avec détails complets
  plan --output json                     Sortie machine

APPLY
  apply --fleet f.yaml --topology t      Appliquer (interactif)
  apply --auto-approve                   Sans confirmation
  apply --dry-run                        Test sans modifier
  apply --only repos                     Uniquement repos

DRIFT
  drift detect --fleet f --topology t    Détecter divergences
  drift reconcile                        Réparer drift
  drift watch --interval 5m              Surveillance continue

BACKUP
  backup --fleet f.yaml                  Backup config
  backup --output-dir ./backups/         Avec timestamp

FLAGS GLOBAUX
  --output json/yaml/text                Format sortie
  --log-level debug/info/warn/error      Verbosité
  --no-color                             Sans couleurs
  --config ~/.config/cac-configmgr/      Config custom

ALIAS UTILES
  cac-configmgr plan ... | less          Voir tout
  cac-configmgr apply --auto-approve ... CI/CD
  cac-configmgr drift watch &            Background monitoring
```
