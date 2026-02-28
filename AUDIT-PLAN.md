# Plan d'Audit : Documentation vs Code

**Date de création :** 2026-02-27  
**Branche :** `testing/audit`  
**Statut :** 🚧 En cours

---

## Objectif

Vérifier la cohérence entre :
- Les spécifications techniques (`specs/*.md`)
- Le code implémenté (`src/`)
- L'état d'avancement documenté (`PROJECT-STATUS.md`)
- Les décisions d'architecture (`ADRS.md`)

---

## État d'Avancement de l'Audit

| Étape | Description | Statut | Résultat |
|-------|-------------|--------|----------|
| 0 | Création du plan d'audit | ✅ Complété | Ce fichier |
| 1 | Vérification specs techniques | ⏳ En attente | - |
| 2 | Vérification état d'avancement | ⏳ En attente | - |
| 3 | Vérification ADRs | ⏳ En attente | - |
| 4 | Vérification autres MD | ⏳ En attente | - |
| 5 | Synchronisation Code ↔ Specs | ⏳ En attente | - |
| 6 | Rapport final et actions | ⏳ En attente | - |

---

## Étape 1 : Spécifications Techniques (`specs/*.md`)

### 1.1 20-TEMPLATE-HIERARCHY.md
**À vérifier :**
- [ ] Structure des modèles (NP/EP/PP) correspond au code
- [ ] Champs documentés existent dans les modèles Pydantic
- [ ] Alias (`routingPolicy`, `normalizationPackages`) cohérents
- [ ] Héritage et merging documentés = implémentation

**Red flags potentiels :**
- Spéc décrit des champs qui n'existent pas
- Structure différente entre spec et code
- Exemples YAML dans spec ne fonctionnent pas

### 1.2 30-PROCESSING-POLICIES.md
**À vérifier :**
- [ ] Structure `normalization_packages` documentée
- [ ] Structure `specifications` (EP) documentée
- [ ] Champs optionnels (`enrichmentPolicy`) marqués comme tel
- [ ] Références entre PP → RP → NP/EP documentées

### 1.3 40-CLI-WORKFLOW.md
**À vérifier :**
- [ ] Commandes `validate`, `plan`, `generate-demo` documentées
- [ ] Options des commandes correspondent au code
- [ ] Exit codes et erreurs documentés

### 1.4 10-INVENTORY-FLEET.md
**À vérifier :**
- [ ] Modèle Fleet avec tags
- [ ] Structure des nœuds (DataNode, SearchHead, AIO)
- [ ] Tags et clusters documentés

---

## Étape 2 : État d'Avancement (`PROJECT-STATUS.md`)

### 2.1 Phase 1 (MVP)
**À vérifier :**
- [ ] Ce qui est marqué "✅ Done" l'est vraiment
- [ ] Features "🚧 In Progress" sont en cours
- [ ] Ressources P0/P1/P2 correspondent au code

### 2.2 Ressources Implémentées
**Mapping code vs status :**
| Ressource | Code | Status.md | Cohérent ? |
|-----------|------|-----------|------------|
| Repos | ✅ | ? | - |
| Routing Policies | ✅ | ? | - |
| Processing Policies | ✅ | ? | - |
| Normalization Policies | ✅ | ? | - |
| Enrichment Policies | ✅ | ? | - |
| Devices | ✅ | ? | - |
| Alert Rules | ❌ | ? | - |

---

## Étape 3 : Architecture Decision Records (`ADRS.md`)

### 3.1 ADR-001 : Python
**À vérifier :**
- [ ] Toujours d'actualité
- [ ] Version Python correcte

### 3.2 ADR-002 : Template ID avec `_id`
**À vérifier :**
- [ ] Implémenté dans tous les modèles
- [ ] Logique de matching par `_id` fonctionne

### 3.3 ADR-003 : Héritage Multi-niveaux
**À vérifier :**
- [ ] 4 niveaux documentés = implémentés
- [ ] Intra-level et Cross-level fonctionnent

### 3.4 ADRs Manquants
**Potentiellement à ajouter :**
- [ ] Structure NP/EP (packages vs single ref)
- [ ] Validation des dépendances
- [ ] Gestion des champs `None` → `"None"`

---

## Étape 4 : Autres Fichiers Markdown

### 4.1 README.md
**À vérifier :**
- [ ] Accurate par rapport au projet
- [ ] Commandes d'installation fonctionnent
- [ ] Badges et liens valides

### 4.2 AGENTS.md
**À vérifier :**
- [ ] Informations pour devs correctes
- [ ] Structure projet à jour
- [ ] Commandes de build valides

### 4.3 DEMO-SCRIPT.md
**À vérifier :**
- [ ] Correspond à la démo réelle
- [ ] Commandes copiables/coller
- [ ] Timing réaliste

### 4.4 CLEANUP-MIGRATION.md
**À vérifier :**
- [ ] Encore pertinent ou obsolète
- [ ] Actions de cleanup réalisées

---

## Étape 5 : Synchronisation Code ↔ Specs

### 5.1 Modèles Pydantic vs Specs
| Modèle | Fichier | Champs Code | Champs Spec | Cohérent ? |
|--------|---------|-------------|-------------|------------|
| Repo | repos.py | ? | ? | - |
| RoutingPolicy | routing.py | ? | ? | - |
| ProcessingPolicy | processing.py | ? | ? | - |
| NormalizationPolicy | normalization.py | ? | ? | - |
| EnrichmentPolicy | enrichment.py | ? | ? | - |
| Fleet | fleet.py | ? | ? | - |

### 5.2 Alias et Sérialisation
**À vérifier :**
- [ ] `by_alias=True/False` cohérent avec specs
- [ ] Champs internes (`_id`, `_action`) filtrés correctement
- [ ] Payload API = format attendu par DirSync

---

## Étape 6 : Rapport Final

### 6.1 Incohérences Trouvées
*À remplir après les étapes 1-5*

### 6.2 Actions Correctives
*À remplir après les étapes 1-5*

### 6.3 Fichiers à Mettre à Jour
*À remplir après les étapes 1-5*

---

## Checklist Finale

- [ ] Tous les specs sont à jour avec le code
- [ ] PROJECT-STATUS.md reflète l'état réel
- [ ] ADRs couvrent toutes les décisions importantes
- [ ] README.md est accurate
- [ ] DémOSCRIPT.md correspond à la réalité

---

## Notes

*Ajouter ici les notes pendant l'audit*
