# Roadmap & Status

**Dernière mise à jour**: 2026-02-26
**En cours**: Validation spec Inventory Parc
**Prochaine étape**: Répondre aux questions en suspens du Parc

---

## Checklist des Concepts

### 1. Vision & Nom
- [x] Audience définie (MSSP → Enterprise)
- [x] Valeurs promises identifiées
- [x] **NOM FINAL VALIDÉ**: GuardSix CaC

### 2. Concepts Techniques
- [x] **Pseudo-Cluster**: Défini (DataNodeCluster, SearchHeadCluster)
- [ ] **Inventory Parc**: Spec écrite, validation en cours
- [ ] **Inventaire (Parc)**: Structure du fichier décrivant les SIEMs
- [ ] **Configuration**: Format du fichier décrivant la config à appliquer
- [ ] **Workflow**: Commandes et transitions d'état

### 3. Spécifications DirSync (Référence)
- [x] API Director documentée (via DirSync)
- [x] Dépendances objets connues
- [ ] Mapping concepts CAC ↔ DirSync (à faire)

---

## Journal des Décisions

### 2026-02-26
- **Décision**: On ne part PAS de DirSync comme base code, mais comme référence technique
- **Décision**: Double mode cible (Director MSSP d'abord, Direct Enterprise ensuite)
- **Décision**: Focus sur "pseudo-cluster" (problème pas résolu par LogPoint aujourd'hui)

---

## Questions en Suspens

1. Le nom du produit ?
2. Comment appelle-t-on un groupe de SIEMs identiques ? (Cluster ? Pool ? Fleet ?)
3. Un client a plusieurs environnements (prod/staging) → comment modélise-t-on ça ?
4. Variables par cluster → où les définir ?
5. Références SH → DN individuels (hors cluster) ?
6. Peut-on clusteriser des AIO ?
