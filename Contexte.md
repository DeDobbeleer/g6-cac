

# Cadre d'exposition
## 1. BESOINS
Le but de cet outil est de simplifier la configuration du parc Siem des clients.
le produit sera configuration as code 
les types de client sont:
- MSSP qui gère les parcs SIEM de leurs différents client via Logpoint Director
- Clients finaux qui gèrent leur parc SIEM
La gestion automatidéé de ces parcs se fera à l'aide de l'API qui est disponible pour les Director, les siem logpoint n'ont pas encore le support API mes les prochaines releases l'auront
Le produit devra prendre de compte de differents type API et aussi des versions API
### 1.1 Quels sont les vrais problèmes que tu as vécus chez les clients MSSP ?
### 1.2 Et chez les clients Director (non-MSSP) ?
### 1.3 Qu'est-ce qui fait perdre du temps, créé des erreurs, empêche de scaler ?
## 2. CONTRAINTES
### 2.1 Contraintes techniques réelles (réseau, APIs, modes Director...)
### 2.2 Contraintes organisationnelles (équipes, processus, compétences)
### 2.3 Contraintes métier (SLA, compliance, sécurité)
## 3. VISION
### 3.1 Comment tu imagines l'outil idéal ?
### 3.2 Qui l'utilise, dans quel contexte, pour faire quoi ?
### 3.3 Qu'est-ce qui le différencie d'un simple "Terraform pour Logpoint" ?
## 4. SPECS (fonctionnelles)
### 4.1 Fonctionnalités must-have / nice-to-have / hors-scope
### Flux de travail (workflow) attendus
### Ce qui est critique vs ce qui peut attendre
## 3 Docs et Coding
- Langue : On parle en français. Toute la doc et code future sera en anglais comme demandé.
- Standards : Tu me diras quand on y sera (testing, architecture, style...).