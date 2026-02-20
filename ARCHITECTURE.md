# Logpoint CaC - Architecture Technique

## 🎯 Vue d'ensemble

Cette architecture implémente la Configuration as Code pour Logpoint avec support de deux modes :
- **Mode Director** : Gestion via API Director (MSSP, multi-tenants)
- **Mode Direct** : Gestion via API SIEM locale (all-in-one ou distribué)

## 🏗️ Architecture des couches

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           COUCHE PRÉSENTATION                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   CLI       │  │   TUI       │  │   CI/CD     │  │   GitOps Operator   │ │
│  │  (Typer)    │  │  (Textual)  │  │  (Docker)   │  │   (Kubernetes)      │ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘ │
└─────────┼────────────────┼────────────────┼────────────────────┼────────────┘
          │                │                │                    │
          └────────────────┴────────────────┴────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         COUCHE ORCHESTRATION                                │
│                                                                             │
│   ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────────────┐ │
│   │  Plan Engine    │    │  Apply Engine   │    │    Drift Detector       │ │
│   │  (dry-run)      │    │  (execution)    │    │    (state comparison)   │ │
│   └────────┬────────┘    └────────┬────────┘    └────────────┬────────────┘ │
│            │                      │                          │              │
│   ┌────────▼──────────────────────▼──────────────────────────▼────────┐     │
│   │                    Dependency Resolver                            │     │
│   │         (DAG - Directed Acyclic Graph des ressources)             │     │
│   └───────────────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          COUCHE ABSTRACTION                                 │
│                                                                             │
│   ┌─────────────────────────────┐    ┌─────────────────────────────────┐    │
│   │    Cluster Type Detector    │    │      Node Type Router           │    │
│   │  (all-in-one vs distribué)  │    │  (Search Head vs Data Node)     │    │
│   └─────────────┬───────────────┘    └────────────────┬────────────────┘    │
│                 │                                     │                     │
│   ┌─────────────▼─────────────────────────────────────▼───────────────┐     │
│   │                    Resource Abstraction Layer                     │     │
│   │    (même interface pour Repos, Policies, Devices...)              │     │
│   └───────────────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          COUCHE CONNECTEURS                                 │
│                                                                             │
│   ┌─────────────────────────┐        ┌─────────────────────────────────┐    │
│   │   Director Connector    │        │      Direct SIEM Connector      │    │
│   │   (API Director)        │        │   (API SIEM locale)             │    │
│   │                         │        │                                 │    │
│   │   - Multi-pool          │        │   - All-in-one                  │    │
│   │   - Tenant isolation    │        │   - Search Head                 │    │
│   │   - Async operations    │        │   - Data Node                   │    │
│   └─────────────────────────┘        └─────────────────────────────────┘    │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │              Async Operation Manager (polling, retry)               │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📦 Modèle de données

### Hiérarchie des configurations

```yaml
# Structure du repository CaC
.
├── environments/
│   ├── production/
│   │   ├── director.yaml           # Config connexion Director
│   │   ├── clusters/
│   │   │   ├── cluster-a/          # Cluster distribué
│   │   │   │   ├── search-head.yaml
│   │   │   │   └── data-nodes/
│   │   │   │       ├── dn-01.yaml
│   │   │   │       └── dn-02.yaml
│   │   │   └── cluster-b/          # All-in-one
│   │   │       └── all-in-one.yaml
│   │   └── kustomization.yaml      # Inclusion configs communes
│   │
│   └── staging/
│       └── ...
│
├── shared/
│   ├── packages/                   # Normalization Packages
│   │   └── windows-security/
│   ├── sources/                    # Enrichment Sources
│   │   └── threat-intel/
│   └── policies/
│       ├── normalization/
│       ├── enrichment/
│       └── processing/
│
└── schemas/                        # Schémas de validation
    └── v1/
```

### Format de configuration par nœud

```yaml
# apiVersion: logpoint-cac/v1
# kind: DataNodeConfig | SearchHeadConfig | AllInOneConfig

apiVersion: logpoint-cac/v1
kind: DataNodeConfig

metadata:
  name: "dn-prod-01"
  cluster: "cluster-a"
  environment: "production"
  
  # Identification selon le mode
  director:
    pool_uuid: "uuid-pool-a"
    logpoint_identifier: "id-lp-01"
  # OU mode direct:
  # direct:
  #   endpoint: "https://siem-01.internal:443"
  #   auth_ref: "${vault:...}"

spec:
  # =====================================================
  # 1. REPOS (Data Nodes) - Premier élément, fondamental
  # =====================================================
  repos:
    - name: "default"
      paths:
        - path: "/opt/immune/storage/default"
          retention_days: 365
          compression: true
      
    - name: "alerts"
      paths:
        - path: "/opt/immune/storage/alerts"
          retention_days: 1095  # 3 ans
      
    - name: "cold-storage"
      paths:
        - path: "/mnt/cold/storage"
          retention_days: 2555  # 7 ans
      high_availability:
        - target_node: "dn-prod-02"
          retention_days: 30

  # =====================================================
  # 2. ROUTING POLICIES (Data Nodes)
  # Dépend des Repos
  # =====================================================
  routing_policies:
    - name: "critical-logs"
      priority: 1
      conditions:
        - field: "severity"
          operator: "in"
          values: ["high", "critical"]
      actions:
        target_repo: "alerts"
        
    - name: "default-route"
      priority: 100
      conditions:
        - field: "*"
          operator: "always"
      actions:
        target_repo: "default"

  # =====================================================
  # 3. NORMALIZATION POLICIES (Data Nodes)
  # Dépend des Normalization Packages
  # =====================================================
  normalization_policies:
    - name: "windows-security-norm"
      package_ref: "shared/packages/windows-security"  # Référence externe
      priority: 10
      conditions:
        log_source: "Microsoft-Windows-Security-Auditing"
      
    - name: "syslog-rfc5424"
      package_ref: "shared/packages/rfc5424"
      priority: 50
      conditions:
        format: "syslog"

  # =====================================================
  # 4. ENRICHMENT POLICIES (Data Nodes)
  # Dépend des Enrichment Sources
  # =====================================================
  enrichment_policies:
    - name: "geoip-enrichment"
      source_ref: "shared/sources/maxmind-geoip"
      fields:
        - source_field: "source_ip"
          target_fields: ["country", "city", "asn"]
      
    - name: "threat-intel"
      source_ref: "shared/sources/misp-threat-intel"
      fields:
        - source_field: "source_ip"
          target_fields: ["threat_score", "malware_family"]

  # =====================================================
  # 5. PROCESSING POLICIES (Data Nodes)
  # Dépend de Routing, Normalization, Enrichment
  # =====================================================
  processing_policies:
    - name: "standard-processing"
      pipeline:
        - step: "routing"
          policy_ref: "critical-logs"
        - step: "normalization"
          policy_ref: "windows-security-norm"
        - step: "enrichment"
          policy_ref: "geoip-enrichment"
          optional: true
        - step: "storage"
          repo_ref: "default"

  # =====================================================
  # 6. DEVICE GROUPS (Indépendant)
  # =====================================================
  device_groups:
    - name: "perimeter-firewalls"
      description: "Firewalls de périmètre"
      risk_profile:
        confidentiality: "high"
        integrity: "high"
        availability: "critical"
      
    - name: "internal-servers"
      description: "Serveurs internes"
      risk_profile:
        confidentiality: "medium"
        integrity: "high"
        availability: "high"

  # =====================================================
  # 7. DEVICES (Dépend des Device Groups)
  # =====================================================
  devices:
    - name: "fw-prod-01"
      ip_addresses: ["10.0.1.1", "10.0.2.1"]
      device_groups:
        - ref: "perimeter-firewalls"
      log_collection_policy: "standard-processing"
      timezone: "Europe/Paris"
      
    - name: "srv-dc-01"
      ip_addresses: ["10.1.0.10"]
      hostnames: ["dc-01.corp.local"]
      device_groups:
        - ref: "internal-servers"
      log_collection_policy: "standard-processing"

  # =====================================================
  # 8. SYSLOG COLLECTOR (Data Nodes)
  # Dépend des Devices et Processing Policies
  # =====================================================
  syslog_collector:
    enabled: true
    listeners:
      - protocol: "tcp"
        port: 514
        tls:
          enabled: true
          certificate_ref: "${vault:certificates/syslog-tls}"
      
      - protocol: "udp"
        port: 514
        
    mapping:
      - device_ref: "fw-prod-01"
        source_cidr: "10.0.0.0/8"
        processing_policy: "standard-processing"
```

---

## 🔀 Gestion des dépendances (DAG)

### Ordre de déploiement

```
┌─────────────────────────────────────────────────────────────────┐
│                        DEPENDENCY GRAPH                         │
│                                                                 │
│  ┌─────────┐                                                    │
│  │  Repos  │◄────────────────────────────────────────────────┐  │
│  └────┬────┘                                                 │  │
│       │                                                      │  │
│       ▼                                                      │  │
│  ┌─────────┐     ┌─────────────────────┐                     │  │
│  │ Routing │◄────│ Normalization       │                     │  │
│  │Policies │     │ Packages (externe)  │                     │  │
│  └────┬────┘     └─────────────────────┘                     │  │
│       │                                                      │  │
│       │     ┌─────────────────────┐                          │  │
│       │     │ Enrichment          │                          │  │
│       │     │ Sources (externe)   │                          │  │
│       │     └─────────────────────┘                          │  │
│       │            ▲                                         │  │
│       ▼            │                                         │  │
│  ┌──────────┐      │                                         │  │
│  │Processing│◄─────┘                                         │  │
│  │Policies  │                                                │  │
│  └────┬─────┘                                                │  │
│       │                                                      │  │
│       ▼                                                      │  │
│  ┌─────────┐     ┌─────────┐                                 │  │
│  │ Devices │◄────│ Device  │                                 │  │
│  │         │     │ Groups  │                                 │  │
│  └────┬────┘     └─────────┘                                 │  │
│       │                                                      │  │
│       ▼                                                      │  │
│  ┌─────────┐                                                 │  │
│  │ Syslog  │────────────────────────────────────────────────►│  │
│  │Collector│                                                 │  │
│  └─────────┘                                                 │  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Algorithme de résolution

```python
class DependencyResolver:
    """Résout l'ordre de déploiement via topological sort"""
    
    DEPENDENCIES = {
        "repos": [],
        "routing_policies": ["repos"],
        "normalization_policies": [],  # Dépend des packages externes
        "enrichment_policies": [],     # Dépend des sources externes
        "processing_policies": ["routing_policies", "normalization_policies", "enrichment_policies"],
        "device_groups": [],
        "devices": ["device_groups", "processing_policies"],
        "syslog_collector": ["devices", "processing_policies"],
    }
    
    def resolve(self, config: Config) -> List[Resource]:
        """Retourne la liste ordonnée des ressources à déployer"""
        # Implémentation du topological sort
        pass
```

---

## 🔌 Connecteurs

### Director Connector

```python
class DirectorConnector:
    """Connecteur pour l'API Director (mode MSSP)"""
    
    def __init__(self, base_url: str, token: str, pool_uuid: str):
        self.base_url = base_url
        self.token = token
        self.pool_uuid = pool_uuid
        self.async_manager = AsyncOperationManager()
    
    async def apply_resource(
        self, 
        logpoint_id: str, 
        resource_type: str, 
        resource: dict
    ) -> OperationResult:
        """Applique une ressource via l'API Director"""
        
        endpoint = f"{self.base_url}/configapi/{self.pool_uuid}/{logpoint_id}/{resource_type}"
        
        # Envoi de la requête
        response = await self._request("POST", endpoint, json=resource)
        request_id = self._extract_request_id(response)
        
        # Polling de l'opération async
        return await self.async_manager.poll(
            pool_uuid=self.pool_uuid,
            logpoint_id=logpoint_id,
            request_id=request_id,
            timeout=300
        )
```

### Direct SIEM Connector

```python
class DirectSIEMConnector:
    """Connecteur pour l'API SIEM directe (mode all-in-one/distribué)"""
    
    def __init__(self, endpoint: str, credentials: Credentials):
        self.endpoint = endpoint
        self.credentials = credentials
        self.node_type = None  # Détecté automatiquement
    
    async def detect_node_type(self) -> NodeType:
        """Détecte si Search Head ou Data Node"""
        settings = await self.get_system_settings()
        return NodeType.from_settings(settings)
    
    async def apply_resource(
        self, 
        resource_type: str, 
        resource: dict,
        target_node: Optional[NodeType] = None
    ) -> OperationResult:
        """
        Applique une ressource sur le nœud approprié.
        En mode all-in-one, tout est appliqué localement.
        En mode distribué, route vers SH ou DN selon le type.
        """
        if self.node_type == NodeType.ALL_IN_ONE:
            return await self._apply_all_in_one(resource_type, resource)
        
        # Mode distribué : routing selon le type de ressource
        if resource_type in DATA_NODE_RESOURCES:
            return await self._apply_to_data_node(resource_type, resource)
        elif resource_type in SEARCH_HEAD_RESOURCES:
            return await self._apply_to_search_head(resource_type, resource)
```

---

## 🔄 Flux de travail

### Commande `plan`

```
┌─────────┐     ┌──────────────┐     ┌──────────────┐     ┌─────────────┐
│  User   │────▶│  Load Config │────▶│  Fetch State │────▶│   Diff      │
│         │     │  + Validate  │     │  (API LP)    │     │  Engine     │
└─────────┘     └──────────────┘     └──────────────┘     └──────┬──────┘
                                                                 │
                                                                 ▼
┌─────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  User   │◀────│  Format     │◀────│  Build Plan │◀────│  Dependency │
│         │     │  Output     │     │  (actions)  │     │  Resolver   │
└─────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

### Commande `apply`

```
┌─────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  User   │────▶│  Plan       │────▶│  Confirm?   │────▶│  Execute    │
│         │     │  (dry-run)  │     │  (ou -auto) │     │  Actions    │
└─────────┘     └─────────────┘     └─────────────┘     └──────┬──────┘
                                                               │
                                                               ▼
┌─────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  User   │◀────│  Report     │◀────│  Verify     │◀────│  Async Poll │
│         │     │  Final      │     │  State      │     │  (API LP)   │
└─────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

---

## 📁 Structure du projet

```
logpoint-cac/
├── src/
│   ├── logpoint_cac/
│   │   ├── __init__.py
│   │   ├── cli/                    # Interface ligne de commande
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── commands/
│   │   │   │   ├── plan.py
│   │   │   │   ├── apply.py
│   │   │   │   ├── sync.py
│   │   │   │   └── drift.py
│   │   │   └── formatters/
│   │   │       ├── table.py
│   │   │       └── json.py
│   │   │
│   │   ├── core/                   # Logique métier
│   │   │   ├── __init__.py
│   │   │   ├── config.py           # Chargement/validation config
│   │   │   ├── plan.py             # Génération des plans
│   │   │   ├── apply.py            # Exécution des changements
│   │   │   ├── state.py            # Gestion de l'état
│   │   │   └── drift.py            # Détection des drifts
│   │   │
│   │   ├── models/                 # Modèles de données
│   │   │   ├── __init__.py
│   │   │   ├── resources/          # Ressources Logpoint
│   │   │   │   ├── __init__.py
│   │   │   │   ├── repos.py
│   │   │   │   ├── policies.py
│   │   │   │   ├── devices.py
│   │   │   │   └── alerts.py
│   │   │   └── schemas/            # Schémas de validation
│   │   │       └── v1.py
│   │   │
│   │   ├── connectors/             # Connecteurs API
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── director.py
│   │   │   └── direct.py
│   │   │
│   │   ├── resolver/               # Gestion des dépendances
│   │   │   ├── __init__.py
│   │   │   ├── dag.py
│   │   │   └── graph.py
│   │   │
│   │   └── utils/
│   │       ├── async_ops.py
│   │       ├── retry.py
│   │       └── crypto.py
│   │
│   └── tests/
│       ├── unit/
│       ├── integration/
│       └── fixtures/
│
├── configs/                        # Exemples de configurations
│   ├── examples/
│   │   ├── all-in-one/
│   │   └── distributed/
│   └── schemas/
│
├── docs/
│   ├── architecture.md
│   ├── user-guide.md
│   └── api-reference.md
│
├── docker/
│   ├── Dockerfile
│   └── entrypoint.sh
│
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── release.yml
│
├── pyproject.toml
├── README.md
└── LICENSE
```

---

## 🚀 Phases de développement

### Phase 1 : MVP (Repos + Device Groups)
- [ ] Connecteur Director de base
- [ ] CRUD Repos
- [ ] CRUD Device Groups
- [ ] Commandes plan/apply
- [ ] Tests unitaires

### Phase 2 : Policies Pipeline
- [ ] Routing Policies
- [ ] Normalization Policies + Packages
- [ ] Enrichment Policies + Sources
- [ ] Processing Policies
- [ ] Gestion du DAG

### Phase 3 : Devices + Collectors
- [ ] CRUD Devices
- [ ] Syslog Collector
- [ ] Log Collection Policies
- [ ] Validation complète

### Phase 4 : Extensions
- [ ] Users + UserGroups
- [ ] AlertRules
- [ ] Mode Direct (sans Director)
- [ ] Drift detection

### Phase 5 : DevOps/GitOps
- [ ] Image Docker
- [ ] GitHub Actions
- [ ] Kubernetes Operator
- [ ] Observabilité complète

