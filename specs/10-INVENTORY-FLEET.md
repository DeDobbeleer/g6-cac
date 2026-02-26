# Fleet Inventory Specification

**Status**: 🚧 Draft - Pending validation

Defines the **SIEM fleet** of a client (where to deploy configuration).

---

## Global Structure

```yaml
# fleet.yaml
apiVersion: guardsix.io/v1
kind: Fleet

metadata:
  name: client-alpha-production
  
spec:
  # Management type
  managementMode: director  # director | direct
  
  # Connection (if director)
  director:
    poolUuid: "aaa-1111-bbb-2222"
    apiHost: "https://director.logpoint.com"
    credentialsRef: "env://DIRECTOR_TOKEN_ALPHA"
  
  # OR connection (if direct)
  # direct:
  #   apiEndpoints: [...]
  
  # Node and cluster definitions
  nodes:
    # AIOs (unique entities)
    aios:
      - name: aio-dr-site
        logpointId: "lp-aio-dr-01"
        # An AIO = DN + SH combined
    
    # Data Nodes (individual or clustered)
    dataNodes:
      # Option A: Individual node (outside cluster)
      - name: dn-legacy
        logpointId: "lp-dn-legacy-01"
        
      # Option B: Cluster member
      - name: dn-prod-01
        logpointId: "lp-dn-prod-01"
        clusterRef: cluster-dn-production
        
      - name: dn-prod-02
        logpointId: "lp-dn-prod-02"
        clusterRef: cluster-dn-production
        
      - name: dn-archive-01
        logpointId: "lp-dn-archive-01"
        clusterRef: cluster-dn-archive
    
    # Search Heads (individual or clustered)
    searchHeads:
      # Cluster member
      - name: sh-01
        logpointId: "lp-sh-01"
        clusterRef: cluster-sh-frontend
        # A SH can see multiple DN clusters
        connectedDataNodeClusters:
          - cluster-dn-production
          - cluster-dn-archive
          
      - name: sh-02
        logpointId: "lp-sh-02"
        clusterRef: cluster-sh-frontend
        connectedDataNodeClusters:
          - cluster-dn-production
          - cluster-dn-archive
          
      # Individual Search Head (outside cluster)
      - name: sh-admin
        logpointId: "lp-sh-admin"
        # No clusterRef
        connectedDataNodeClusters:
          - cluster-dn-production
  
  # Cluster definitions (optional, for reference)
  clusters:
    dataNodeClusters:
      - name: cluster-dn-production
        description: "Production cluster 3 nodes HA"
        
      - name: cluster-dn-archive
        description: "Archive cluster cold storage"
        
    searchHeadClusters:
      - name: cluster-sh-frontend
        description: "SH cluster for analysts"
```

---

## Use Cases

### Use Case 1: Simple AIO Client
```yaml
spec:
  nodes:
    aios:
      - name: aio-main
        logpointId: "lp-aio-01"
  # No dataNodes, no searchHeads
```

### Use Case 2: Distributed without Clustering
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
        connectedDataNodeClusters: []  # Manually connected to individual DNs
```

### Use Case 3: Full Cluster Client (e.g., large bank)
```yaml
spec:
  nodes:
    dataNodes:
      # Production Cluster (3 nodes)
      - { name: dn-prod-01, logpointId: "lp-dn-p1", clusterRef: cluster-prod }
      - { name: dn-prod-02, logpointId: "lp-dn-p2", clusterRef: cluster-prod }
      - { name: dn-prod-03, logpointId: "lp-dn-p3", clusterRef: cluster-prod }
      
      # DR Cluster (2 nodes)
      - { name: dn-dr-01, logpointId: "lp-dn-d1", clusterRef: cluster-dr }
      - { name: dn-dr-02, logpointId: "lp-dn-d2", clusterRef: cluster-dr }
      
      # Archive Node (standalone)
      - { name: dn-archive, logpointId: "lp-dn-arc" }
    
    searchHeads:
      # Production SH Cluster (2 nodes)
      - { name: sh-prod-01, logpointId: "lp-sh-p1", clusterRef: cluster-sh-prod, connectedDataNodeClusters: [cluster-prod, cluster-dr] }
      - { name: sh-prod-02, logpointId: "lp-sh-p2", clusterRef: cluster-sh-prod, connectedDataNodeClusters: [cluster-prod, cluster-dr] }
      
      # Admin SH (individual)
      - { name: sh-admin, logpointId: "lp-sh-adm", connectedDataNodeClusters: [cluster-prod, cluster-dr, cluster-archive] }
      
      # External SOC SH (individual, limited access)
      - { name: sh-soc, logpointId: "lp-sh-soc", connectedDataNodeClusters: [cluster-prod] }
```

---

## Open Questions

1. **Cluster-scoped variables**: Where do we define variables (e.g., different retention between prod and archive)?
   - In the Fleet (this file)?
   - In the Configuration (topology)?
   - Both?

2. **Cross-references**: How do we model that an individual SH is connected to individual DNs (not clusters)?
   - `connectedDataNodes: [dn-01, dn-02]`?
   - Or implicit (all non-clustered DNs)?

3. **AIO clustering**: Can a client have 2 identical AIOs in HA?
   - Yes (so we need `AIOCluster`)?
   - No (AIO = always unique, no native HA)?
