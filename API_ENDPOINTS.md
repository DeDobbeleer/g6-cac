# Logpoint Director Console API - Endpoints Complets

## Base URL

```
https://{api-server-host-name}/configapi/{pool_UUID}/{logpoint_identifier}
```

## Authentification

```
Authorization: Bearer {token}
Content-Type: application/json
```

Le token est valable 8 heures. Utiliser l'API Refresh Token pour le renouvellement.

---

## 📁 AlertRules

Gestion des règles d'alerte.

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/AlertRules` | Liste toutes les règles d'alerte |
| GET | `/AlertRules/{id}` | Récupère une règle par ID |
| POST | `/AlertRules` | Crée une nouvelle règle d'alerte |
| PUT | `/AlertRules/{id}` | Modifie une règle existante |
| DELETE | `/AlertRules/{id}` | Supprime une règle |
| POST | `/AlertRules/{id}/activate` | Active une règle |
| POST | `/AlertRules/{id}/deactivate` | Désactive une règle |

---

## 📁 BackupAndRestore

Gestion des sauvegardes.

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/BackupAndRestore` | Liste toutes les sauvegardes |
| GET | `/BackupAndRestore/{id}` | Récupère une sauvegarde par ID |
| GET | `/BackupAndRestore/settings` | Liste les paramètres de sauvegarde |
| POST | `/BackupAndRestore/backupnow` | Crée une sauvegarde immédiate |
| POST | `/BackupAndRestore/logchecksumbackupnow` | Sauvegarde logs + checksums |
| POST | `/BackupAndRestore` | Configure la sauvegarde (config + logs) |
| POST | `/BackupAndRestore/{id}/restore` | Restaure une sauvegarde |
| DELETE | `/BackupAndRestore/{id}` | Supprime une sauvegarde |
| POST | `/BackupAndRestore/refreshlist` | Rafraîchit la liste |

---

## 📁 Certificates

Gestion des certificats.

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/Certificates` | Liste tous les certificats |
| GET | `/Certificates/{id}` | Récupère un certificat par ID |
| POST | `/Certificates` | Importe un certificat |
| PUT | `/Certificates/{id}` | Met à jour un certificat |
| DELETE | `/Certificates/{id}` | Supprime un certificat |

---

## 📁 Charsets

Charsets disponibles (lecture seule).

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/Charsets` | Liste les charsets disponibles |

---

## 📁 DeviceGroups

Gestion des groupes de devices.

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/DeviceGroups` | Liste tous les groupes |
| GET | `/DeviceGroups/{id}` | Récupère un groupe par ID |
| POST | `/DeviceGroups` | Crée un nouveau groupe |
| PUT | `/DeviceGroups/{id}` | Modifie un groupe |
| DELETE | `/DeviceGroups/{id}` | Supprime un groupe |

---

## 📁 Devices

Gestion des devices.

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/Devices` | Liste tous les devices |
| GET | `/Devices/{id}` | Récupère un device par ID |
| GET | `/Devices/{id}/plugins` | Récupère les plugins d'un device |
| POST | `/Devices` | Crée un nouveau device |
| PUT | `/Devices/{id}` | Modifie un device |
| DELETE | `/Devices/{id}` | Supprime un device |
| POST | `/Devices/{id}/attach` | Attache un collector distribué |
| POST | `/Devices/{id}/detach` | Détache un collector (deprecated) |
| POST | `/Devices/ignoredips` | Ajoute une IP ignorée |
| POST | `/Devices/install` | Importe des devices depuis CSV |

---

## 📁 DistributedCollectors

Gestion des collectors distribués.

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/DistributedCollectors` | Liste tous les collectors |
| GET | `/DistributedCollectors/{id}` | Récupère un collector par ID |
| POST | `/DistributedCollectors/{id}/activate` | Active un collector |
| POST | `/DistributedCollectors/{id}/deactivate` | Désactive un collector |
| DELETE | `/DistributedCollectors/{id}` | Supprime un collector |
| POST | `/DistributedCollectors/refreshlist` | Rafraîchit la liste |

---

## 📁 EnrichmentPolicies

Gestion des politiques d'enrichissement.

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/EnrichmentPolicies` | Liste toutes les politiques |
| GET | `/EnrichmentPolicies/{id}` | Récupère une politique par ID |
| POST | `/EnrichmentPolicies` | Crée une politique |
| PUT | `/EnrichmentPolicies/{id}` | Modifie une politique |
| DELETE | `/EnrichmentPolicies/{id}` | Supprime une politique |

---

## 📁 IncidentUserGroups

Gestion des groupes d'utilisateurs d'incidents.

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/IncidentUserGroups` | Liste tous les groupes |
| GET | `/IncidentUserGroups/{id}` | Récupère un groupe par ID |
| POST | `/IncidentUserGroups` | Crée un groupe |
| POST | `/IncidentUserGroups/fetch` | Récupère la liste (async) |
| DELETE | `/IncidentUserGroups/{id}` | Supprime un groupe |

---

## 📁 LDAP

Configuration LDAP (lecture seule via API).

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/LDAP` | Liste les configurations LDAP |
| GET | `/LDAP/{id}` | Récupère une config LDAP |
| POST | `/LDAP/refreshlist` | Rafraîchit la liste LDAP |

---

## 📁 License

Gestion des licences.

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/License` | Récupère les infos de licence |
| POST | `/License` | Importe une licence |
| POST | `/License/refreshlist` | Rafraîchit les infos de licence |

---

## 📁 LogCollectionPolicies

Gestion des politiques de collecte de logs.

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/LogCollectionPolicies` | Liste toutes les politiques |
| GET | `/LogCollectionPolicies/{id}` | Récupère une politique |
| GET | `/LogCollectionPolicies/{id}/plugins` | Récupère les plugins |
| POST | `/LogCollectionPolicies` | Crée une politique |
| PUT | `/LogCollectionPolicies/{id}` | Modifie une politique |
| DELETE | `/LogCollectionPolicies/{id}` | Supprime une politique |

---

## 📁 MitreAttacks

Tags MITRE ATT&CK.

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/MitreAttacks/fetch` | Liste tous les tags MITRE (async) |

---

## 📁 NormalizationPolicies

Gestion des politiques de normalisation.

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/NormalizationPolicies` | Liste toutes les politiques |
| GET | `/NormalizationPolicies/{id}` | Récupère une politique |
| POST | `/NormalizationPolicies` | Crée une politique |
| PUT | `/NormalizationPolicies/{id}` | Modifie une politique |
| DELETE | `/NormalizationPolicies/{id}` | Supprime une politique |

---

## 📁 Policies

Gestion générale des politiques.

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/Policies` | Liste toutes les politiques |
| GET | `/Policies/{id}` | Récupère une politique par ID |
| POST | `/Policies` | Crée une politique |
| PUT | `/Policies/{id}` | Modifie une politique |
| DELETE | `/Policies/{id}` | Supprime une politique |

---

## 📁 ProcessPolicies

Gestion des politiques de traitement.

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/ProcessPolicies` | Liste toutes les politiques |
| GET | `/ProcessPolicies/{id}` | Récupère une politique |
| POST | `/ProcessPolicies` | Crée une politique |
| PUT | `/ProcessPolicies/{id}` | Modifie une politique |
| DELETE | `/ProcessPolicies/{id}` | Supprime une politique |

---

## 📁 Repos

Gestion des référentiels (repos).

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/Repos` | Liste tous les repos |
| GET | `/Repos/{id}` | Récupère un repo par ID |
| GET | `/Repos/RepoPaths` | Liste les chemins de repo disponibles |
| POST | `/Repos` | Crée un nouveau repo |
| PUT | `/Repos/{id}` | Modifie un repo |
| DELETE | `/Repos/{id}` | Supprime un repo |
| POST | `/Repos/RemoteRepos/fetch` | Récupère les repos distants (async) |
| POST | `/Repos/RepoPaths/refreshlist` | Rafraîchit la liste des chemins |

---

## 📁 SystemSettingsGeneral

Paramètres système généraux.

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/SystemSettingsGeneral` | Liste les paramètres généraux |
| GET | `/SystemSettingsGeneral/auth` | Liste les types d'authentification |
| POST | `/SystemSettingsGeneral` | Met à jour les paramètres |
| POST | `/SystemSettingsGeneral/refreshAuthlist` | Rafraîchit la liste d'auth |

---

## 📁 SystemSettingsSMTP

Configuration SMTP.

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/SystemSettingsSMTP` | Liste les paramètres SMTP |
| POST | `/SystemSettingsSMTP` | Met à jour les paramètres SMTP |

---

## 📁 SystemSettingsSNMP

Configuration SNMP.

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/SystemSettingsSNMP` | Liste les paramètres SNMP |
| POST | `/SystemSettingsSNMP` | Met à jour les paramètres SNMP |

---

## 📁 Timezones

Fuseaux horaires (lecture seule).

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/Timezones` | Liste tous les fuseaux horaires |

---

## 📁 UserGroups

Gestion des groupes d'utilisateurs.

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/UserGroups` | Liste tous les groupes |
| GET | `/UserGroups/{id}` | Récupère un groupe par ID |
| POST | `/UserGroups` | Crée un groupe |
| PUT | `/UserGroups/{id}` | Modifie un groupe |
| DELETE | `/UserGroups/{id}` | Supprime un groupe |

---

## 📁 Users

Gestion des utilisateurs.

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/Users` | Liste tous les utilisateurs |
| GET | `/Users/{id}` | Récupère un utilisateur par ID |
| POST | `/Users` | Crée un utilisateur |
| PUT | `/Users/{id}` | Modifie un utilisateur |
| DELETE | `/Users/{id}` | Supprime un utilisateur |
| POST | `/Users/{id}/activate` | Active un utilisateur |
| POST | `/Users/{id}/deactivate` | Désactive un utilisateur |
| POST | `/Users/{id}/changePassword` | Change le mot de passe |
| POST | `/Users/{id}/unlock` | Déverrouille un utilisateur |
| POST | `/Users/fetch` | Récupère la liste (async) |
| POST | `/Users/refreshlist` | Rafraîchit la liste |

---

## 📊 Résumé par catégorie

| Catégorie | Nombre d'endpoints | Priorité CaC |
|-----------|-------------------|--------------|
| AlertRules | 7 | P0 |
| DeviceGroups | 5 | P0 |
| Devices | 9 | P0 |
| Repos | 7 | P0 |
| Policies | 5 | P1 |
| LogCollectionPolicies | 6 | P1 |
| SystemSettings* | 6 | P1 |
| Users | 9 | P2 |
| UserGroups | 5 | P2 |
| BackupAndRestore | 7 | P2 |
| IncidentUserGroups | 5 | P2 |
| DistributedCollectors | 5 | P2 |
| EnrichmentPolicies | 5 | P3 |
| NormalizationPolicies | 5 | P3 |
| ProcessPolicies | 5 | P3 |
| Certificates | 5 | P3 |
| License | 3 | P3 |
| LDAP | 3 | P3 |
| MITRE | 1 | P3 |
| Charsets | 1 | P3 |
| Timezones | 1 | P3 |

**Total : ~100+ endpoints**

---

## ⚠️ Notes importantes

### Opérations asynchrones
Toutes les opérations POST/PUT/DELETE retournent un `request_id` à poller sur :
```
/monitorapi/{pool_UUID}/{logpoint_identifier}/orders/{request_id}
```

### États du polling
- `queued` : En attente
- `in_progress` : En cours
- `completed` : Terminé (vérifier `success: true/false`)
- `failed` : Échec

### Mode Normal vs Co-Managed
Certaines APIs sont restreintes en mode Co-Managed. Vérifier `SystemSettingsGeneral` pour le mode actuel.

