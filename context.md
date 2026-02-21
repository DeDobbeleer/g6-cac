# 1. Objectif du produit

## 1.1 Contexte

Les clients Logpoint (MSSP et clients finaux) doivent gérer des parcs SIEM de plus en plus complexes, souvent multi-tenant, distribués et évolutifs.

La configuration manuelle :

* est chronophage
* est source d’erreurs
* manque d’homogénéité
* complique la maintenance et les mises à jour

## 1.2 Objectif

Le produit a pour objectif de :

> **Simplifier, standardiser et automatiser la configuration des environnements SIEM Logpoint via une approche Configuration as Code (CaC).**

Il permettra :

* La gestion centralisée des configurations
* L’industrialisation des déploiements
* La reproductibilité des environnements
* La gestion des écarts entre versions
* L’automatisation via API

---

# 2. Typologie des clients ciblés

Le produit devra adresser deux profils principaux :

## 2.1 MSSP (Managed Security Service Providers)

Les MSSP :

* Gèrent plusieurs clients (multi-tenant)
* Utilisent Logpoint Director pour piloter leurs SIEM
* Ont besoin de :

  * Standardiser les configurations
  * Appliquer des modèles (templates)
  * Déployer massivement des changements
  * Maintenir la cohérence entre tenants

## 2.2 Clients finaux (Single organization)

Les clients finaux :

* Gèrent leur propre parc SIEM
* Peuvent disposer d’un ou plusieurs environnements (Prod, Préprod, DR)
* Ont besoin de :

  * Versionner leur configuration
  * Automatiser les déploiements
  * Simplifier les mises à jour
  * Réduire la dépendance aux actions manuelles

---

# 3. Approche : Configuration as Code (CaC)

Le produit reposera sur le principe suivant :

> Toute configuration SIEM doit être définie sous forme déclarative dans des fichiers versionnés.

Exemples d’objets potentiellement gérés :

* Pools
* Logpoints
* Tenants
* Policies
* Alerts
* Parsers
* Use cases
* Connecteurs
* Paramètres système

### Bénéfices :

* Traçabilité (Git)
* Versioning
* Rollback possible
* Auditabilité
* Déploiement reproductible

---

# 4. Mécanisme d’automatisation

## 4.1 Utilisation des API

La gestion automatisée s’appuiera sur :

* API Logpoint Director (déjà disponibles)
* API SIEM Logpoint (à venir dans les prochaines releases)

Le produit devra :

* Interagir dynamiquement avec les API
* Supporter plusieurs endpoints
* Gérer les authentifications (tokens, etc.)
* Gérer les réponses et erreurs API
* Être idempotent (ne pas recréer ce qui existe déjà)

---

# 5. Gestion des versions API

Un point critique du design :

> Le produit devra être compatible avec différentes versions d’API et anticiper les évolutions futures.

Cela implique :

* Détection automatique de la version API
* Abstraction des endpoints
* Gestion de la rétrocompatibilité
* Mapping version → endpoints disponibles
* Gestion des différences de payload selon versions

Exemple de problématiques :

* Endpoint existant en v2.6 mais modifié en v2.7
* Structure JSON différente
* Changement de nom d’objet
* Fonctionnalité non encore disponible côté SIEM

---

# 6. Contraintes actuelles

* Les SIEM Logpoint ne disposent pas encore d’un support API complet
* Le produit devra :

  * Être initialement orienté Director
  * Être évolutif pour intégrer l’API SIEM dès disponibilité
  * Prévoir une architecture modulaire

---

# 7. Exigences clés

Le produit devra être :

* Multi-tenant
* Version-aware (API aware)
* Idempotent
* Extensible
* Automatisable (CLI + pipeline CI/CD)
* Sécurisé (gestion token, logs masqués, etc.)
* Traçable (journalisation complète)




