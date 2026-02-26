# Inventory Parc (Spécification)

**Statut**: 🚧 Draft - En attente validation

Définit le **parc de SIEMs** d'un client (quoi déployer la config).

---

## Structure globale

```yaml
# parc.yaml
apiVersion: guardsix.io/v1
kind: Parc

metadata:
  name: client-alpha-production
  
spec:
  # Type de gestion
  managementMode: director  # director | direct
  
  # Connexion (si director)
  director:
    poolUuid: "aaa-1111-bbb-2222"
    apiHost: "https://director.logpoint.com"
    credentialsRef: "env://DIRECTOR_TOKEN_ALPHA"
  
  # OU connexion (si direct)
  # direct:
  #   apiEndpoints: [...]
  
  # Définition des nœuds et clusters
  nodes:
    # AIOs (entités uniques)
    aios:
      - name: aio-dr-site
        logpointId: "lp-aio-dr-01"
        # Un AIO = DN + SH combinés
    
    # Data Nodes (individuels ou en cluster)
    dataNodes:
      # Option A: Nœud individuel (hors cluster)
      - name: dn-legacy
        logpointId: "lp-dn-legacy-01"
        
      # Option B: Membre d'un cluster
      - name: dn-prod-01
        logpointId: "lp-dn-prod-01"
        clusterRef: cluster-dn-production
        
      - name: dn-prod-02
        logpointId: "lp-dn-prod-02"
        clusterRef: cluster-dn-production
        
      - name: dn-archive-01
        logpointId: "lp-dn-archive-01"
        clusterRef: cluster-dn-archive
    
    # Search Heads (individuels ou en cluster)
    searchHeads:
      # Membre d'un cluster
      - name: sh-01
        logpointId: "lp-sh-01"
        clusterRef: cluster-sh-frontend
        # Un SH peut voir plusieurs clusters DN
        connectedDataNodeClusters:
          - cluster-dn-production
          - cluster-dn-archive
          
      - name: sh-02
        logpointId: "lp-sh-02"
        clusterRef: cluster-sh-frontend
        connectedDataNodeClusters:
          - cluster-dn-production
          - cluster-dn-archive
          
      # Search Head individuel (hors cluster)
      - name: sh-admin
        logpointId: "lp-sh-admin"
        # Pas de clusterRef
        connectedDataNodeClusters:
          - cluster-dn-production
  
  # Définition des clusters (optionnel, pour référence)
  clusters:
    dataNodeClusters:
      - name: cluster-dn-production
        description: "Cluster production 3 nœuds HA"
        
      - name: cluster-dn-archive
        description: "Cluster archive cold storage"
        
    searchHeadClusters:
      - name: cluster-sh-frontend
        description: "Cluster SH pour analysts"
```

---

## Cas d'usage

### Cas 1: Client AIO simple
```yaml
spec:
  nodes:
    aios:
      - name: aio-main
        logpointId: "lp-aio-01"
  # Pas de dataNodes, pas de searchHeads
```

### Cas 2: Client distribué sans clustering
```yaml
spec:
  nodes:
    dataNodes:
      - name: dn-site-a
        logpointId: "lp-dn-01"
      - name: dn-site-b
        logpointId: "lp-dn-02"
    
    searchHeads:
      - name: sh-main
        logpointId: "lp-sh-01"
        connectedDataNodeClusters: []  # Connecté manuellement aux DN individuels
```

### Cas 3: Client full cluster (ex: grande banque)
```yaml
spec:
  nodes:
    dataNodes:
      # Cluster Production (3 nœuds)
      - { name: dn-prod-01, logpointId: "lp-dn-p1", clusterRef: cluster-prod }
      - { name: dn-prod-02, logpointId: "lp-dn-p2", clusterRef: cluster-prod }
      - { name: dn-prod-03, logpointId: "lp-dn-p3", clusterRef: cluster-prod }
      
      # Cluster DR (2 nœuds)
      - { name: dn-dr-01, logpointId: "lp-dn-d1", clusterRef: cluster-dr }
      - { name: dn-dr-02, logpointId: "lp-dn-d2", clusterRef: cluster-dr }
      
      # Node Archive (seul)
      - { name: dn-archive, logpointId: "lp-dn-arc" }
    
    searchHeads:
      # Cluster SH Production (2 nœuds)
      - { name: sh-prod-01, logpointId: "lp-sh-p1", clusterRef: cluster-sh-prod, connectedDataNodeClusters: [cluster-prod, cluster-dr] }
      - { name: sh-prod-02, logpointId: "lp-sh-p2", clusterRef: cluster-sh-prod, connectedDataNodeClusters: [cluster-prod, cluster-dr] }
      
      # SH Admin (individuel)
      - { name: sh-admin, logpointId: "lp-sh-adm", connectedDataNodeClusters: [cluster-prod, cluster-dr, cluster-archive] }
      
      # SH SOC externe (individuel, accès limité)
      - { name: sh-soc, logpointId: "lp-sh-soc", connectedDataNodeClusters: [cluster-prod] }
```

---

## Questions en suspens

1. **Variables par cluster** : Où définit-on les variables (ex: retention différente entre prod et archive) ?
   - Dans le Parc (ce fichier) ?
   - Dans la Configuration (topo) ?
   - Les deux ?

2. **Références croisées** : Comment modélise-t-on qu'un SH individuel est connecté à des DN individuels (pas des clusters) ?
   - `connectedDataNodes: [dn-01, dn-02]` ?
   - Ou implicite (tous les DN non clusterisés) ?

3. **AIO dans un cluster** : Est-ce qu'on peut avoir un "cluster d'AIO" (2 AIOs identiques en HA) ?
   - Ou AIO = toujours entité unique ?
