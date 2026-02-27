"""Demo configuration generator for presentation.

Generates a complete multi-client, multi-template structure demonstrating:
- Horizontal inheritance (intra-level): base → PCI, base → ISO
- Vertical inheritance (cross-level): LogPoint → MSSP → Profile → Instance
- Multiple client types (banks, enterprises)
- Multiple clients per type (bank-a, bank-b)
"""

from __future__ import annotations

from pathlib import Path

from .models import (
    ConfigTemplate, TemplateMetadata, TemplateSpec,
    TopologyInstance, InstanceMetadata,
    Repo, HiddenRepoPath,
    RoutingPolicy, RoutingCriterion,
    ProcessingPolicy,
    Fleet, FleetMetadata, FleetSpec, DirectorConfig, Nodes,
    DataNode, SearchHead, AIO,
)
from .utils import save_multi_file_template, save_instance, save_fleet


def generate_all_configs(output_dir: Path) -> None:
    """Generate complete demo configuration structure."""
    output_dir = Path(output_dir)
    
    # Level 1: LogPoint Golden Templates (with horizontal addons)
    _generate_logpoint_templates(output_dir / "templates" / "logpoint")
    
    # Level 2-3: MSSP Templates (with horizontal and vertical inheritance)
    _generate_mssp_templates(output_dir / "templates" / "mssp" / "acme-corp")
    
    # Level 4: Client Instances
    _generate_client_instances(output_dir / "instances")


def _generate_logpoint_templates(base_dir: Path) -> None:
    """Generate LogPoint Golden Templates (Level 1)."""
    
    # 1. Golden Base (root template)
    golden_base = ConfigTemplate(
        metadata=TemplateMetadata(
            name="golden-base",
            version="2.0.0",
            provider="logpoint"
        ),
        spec=TemplateSpec(
            vars={
                "mount_point": "/opt/immune/storage",
                "retention_default": 90,
                "retention_sec": 365,
            },
            repos=[
                Repo(name="repo-default", hiddenrepopath=[
                    HiddenRepoPath(_id="primary", path="{{mount_point}}", retention="{{retention_default}}")
                ]),
                Repo(name="repo-secu", hiddenrepopath=[
                    HiddenRepoPath(_id="primary", path="{{mount_point}}", retention="{{retention_sec}}")
                ]),
                Repo(name="repo-secu-verbose", hiddenrepopath=[
                    HiddenRepoPath(_id="primary", path="{{mount_point}}", retention=30)
                ]),
                Repo(name="repo-system", hiddenrepopath=[
                    HiddenRepoPath(_id="primary", path="{{mount_point}}", retention=180)
                ]),
                Repo(name="repo-system-verbose", hiddenrepopath=[
                    HiddenRepoPath(_id="primary", path="{{mount_point}}", retention=30)
                ]),
                Repo(name="repo-cloud", hiddenrepopath=[
                    HiddenRepoPath(_id="primary", path="{{mount_point}}", retention=180)
                ]),
            ],
            routing_policies=[
                RoutingPolicy(
                    policy_name="rp-default",
                    _id="rp-default",
                    catch_all="repo-system",
                    routing_criteria=[]
                ),
                RoutingPolicy(
                    policy_name="rp-windows",
                    _id="rp-windows",
                    catch_all="repo-system",
                    routing_criteria=[
                        RoutingCriterion(_id="crit-verbose", type="KeyPresentValueMatches", 
                                        key="EventType", value="Verbose", repo="repo-system-verbose"),
                    ]
                ),
                RoutingPolicy(
                    policy_name="rp-linux",
                    _id="rp-linux",
                    catch_all="repo-system",
                    routing_criteria=[
                        RoutingCriterion(_id="crit-debug", type="KeyPresentValueMatches",
                                        key="severity", value="debug", repo="repo-system-verbose"),
                    ]
                ),
            ],
        )
    )
    save_multi_file_template(base_dir / "golden-base", golden_base)
    
    # 2. Golden PCI-DSS (horizontal addon - extends base at same level)
    golden_pci = ConfigTemplate(
        metadata=TemplateMetadata(
            name="golden-pci-dss",
            extends="logpoint/golden-base",  # Intra-level inheritance
            version="1.0.0",
            provider="logpoint"
        ),
        spec=TemplateSpec(
            vars={
                "retention_pci": 2555,  # 7 years PCI requirement
            },
            repos=[
                # Add compliance repo with long retention
                Repo(name="repo-pci-audit", hiddenrepopath=[
                    HiddenRepoPath(_id="primary", path="/opt/immune/storage-nfs", retention="{{retention_pci}}")
                ]),
            ],
            processing_policies=[
                ProcessingPolicy(
                    name="pp-pci-audit",
                    _id="pp-pci-audit",
                    routing_policy="rp-pci-audit",
                    normalization_policy="np-auto",
                    enrichment_policy="ep-pci-fields",
                ),
            ],
        )
    )
    save_multi_file_template(base_dir / "golden-pci-dss", golden_pci)
    
    # 3. Golden ISO27001 (another horizontal addon)
    golden_iso = ConfigTemplate(
        metadata=TemplateMetadata(
            name="golden-iso27001",
            extends="logpoint/golden-base",
            version="1.0.0",
            provider="logpoint"
        ),
        spec=TemplateSpec(
            vars={
                "retention_iso": 3650,  # 10 years ISO requirement
            },
            repos=[
                Repo(name="repo-iso-audit", hiddenrepopath=[
                    HiddenRepoPath(_id="primary", path="/opt/immune/storage-nfs", retention="{{retention_iso}}")
                ]),
            ],
        )
    )
    save_multi_file_template(base_dir / "golden-iso27001", golden_iso)


def _generate_mssp_templates(base_dir: Path) -> None:
    """Generate MSSP Templates (Level 2-3)."""
    
    # Level 2: MSSP Base (vertical inheritance from LogPoint)
    mssp_base = ConfigTemplate(
        metadata=TemplateMetadata(
            name="acme-base",
            extends="logpoint/golden-pci-dss",  # Cross-level: LogPoint → MSSP
            version="1.0.0",
            provider="acme-mssp"
        ),
        spec=TemplateSpec(
            vars={
                "retention_default": 180,  # Override: 90→180
                "mount_warm": "/opt/immune/storage-warm",
                "mount_cold": "/opt/immune/storage-cold",
            },
            repos=[
                # Merge: Override retention for repo-secu
                Repo(name="repo-secu", hiddenrepopath=[
                    HiddenRepoPath(_id="primary", retention=90),  # 365→90
                    HiddenRepoPath(_id="warm-tier", path="{{mount_warm}}", retention=365),
                ]),
                # Add archive repo with multi-tier
                Repo(name="repo-archive", hiddenrepopath=[
                    HiddenRepoPath(_id="warm-tier", path="{{mount_warm}}", retention=90),
                    HiddenRepoPath(_id="cold-tier", path="{{mount_cold}}", retention=1095),
                ]),
            ],
        )
    )
    save_multi_file_template(base_dir / "base", mssp_base)
    
    # Level 3: Horizontal Addons (extend MSSP base)
    
    # Banking Addon (horizontal - specific to banking sector)
    banking_addon = ConfigTemplate(
        metadata=TemplateMetadata(
            name="acme-banking-addon",
            extends="mssp/acme-corp/base",  # Intra-level: MSSP base → addon
            version="1.0.0",
            provider="acme-mssp"
        ),
        spec=TemplateSpec(
            vars={
                "retention_banking": 3650,  # 10 years for banking law
            },
            repos=[
                Repo(name="repo-trading", hiddenrepopath=[
                    HiddenRepoPath(_id="primary", path="{{mount_point}}", retention=1),  # Very short
                    HiddenRepoPath(_id="warm-tier", path="{{mount_warm}}", retention=7),
                    HiddenRepoPath(_id="nfs-tier", path="/opt/immune/storage-nfs", retention=2555),
                ]),
            ],
            routing_policies=[
                RoutingPolicy(
                    policy_name="rp-trading",
                    _id="rp-trading",
                    catch_all="repo-trading",
                    routing_criteria=[
                        RoutingCriterion(_id="crit-high-freq", type="KeyPresent",
                                        key="high_frequency", repo="repo-trading"),
                    ]
                ),
            ],
        )
    )
    save_multi_file_template(base_dir / "addons" / "banking", banking_addon)
    
    # Healthcare Addon (another horizontal addon)
    healthcare_addon = ConfigTemplate(
        metadata=TemplateMetadata(
            name="acme-healthcare-addon",
            extends="mssp/acme-corp/base",
            version="1.0.0",
            provider="acme-mssp"
        ),
        spec=TemplateSpec(
            vars={
                "retention_hipaa": 2555,  # 7 years HIPAA
            },
            repos=[
                Repo(name="repo-phi", hiddenrepopath=[  # PHI = Protected Health Info
                    HiddenRepoPath(_id="primary", path="/opt/immune/storage-encrypted", retention="{{retention_hipaa}}")
                ]),
            ],
        )
    )
    save_multi_file_template(base_dir / "addons" / "healthcare", healthcare_addon)
    
    # Level 3: Profiles (vertical inheritance from base/addons)
    
    # Simple Profile
    simple_profile = ConfigTemplate(
        metadata=TemplateMetadata(
            name="acme-simple",
            extends="mssp/acme-corp/base",
            version="1.0.0",
            provider="acme-mssp"
        ),
        spec=TemplateSpec(
            vars={
                "retention_simple": 30,
            },
        )
    )
    save_multi_file_template(base_dir / "profiles" / "simple", simple_profile)
    
    # Enterprise Profile
    enterprise_profile = ConfigTemplate(
        metadata=TemplateMetadata(
            name="acme-enterprise",
            extends="mssp/acme-corp/base",
            version="1.0.0",
            provider="acme-mssp"
        ),
        spec=TemplateSpec(
            vars={
                "retention_enterprise": 365,
            },
            repos=[
                Repo(name="repo-secu", hiddenrepopath=[
                    HiddenRepoPath(_id="primary", retention=7),  # Even shorter on fast
                    HiddenRepoPath(_id="warm-tier", retention=90),
                    HiddenRepoPath(_id="cold-tier", retention=730),
                    HiddenRepoPath(_id="nfs-tier", path="/opt/immune/storage-nfs", retention=3650),
                ]),
            ],
        )
    )
    save_multi_file_template(base_dir / "profiles" / "enterprise", enterprise_profile)
    
    # Banking Premium Profile (extends enterprise + banking addon)
    # This demonstrates BOTH horizontal AND vertical inheritance
    banking_premium = ConfigTemplate(
        metadata=TemplateMetadata(
            name="acme-banking-premium",
            extends="mssp/acme-corp/profiles/enterprise",  # Could also extend addon
            version="1.0.0",
            provider="acme-mssp"
        ),
        spec=TemplateSpec(
            vars={
                "compliance": "mifid-banking",
            },
            processing_policies=[
                ProcessingPolicy(
                    name="pp-banking-audit",
                    _id="pp-banking-audit",
                    routing_policy="rp-banking-audit",
                    normalization_policy="np-banking",
                    enrichment_policy="ep-mifid",
                ),
            ],
        )
    )
    save_multi_file_template(base_dir / "profiles" / "banking-premium", banking_premium)


def _generate_client_instances(base_dir: Path) -> None:
    """Generate Client Instances (Level 4)."""
    
    # ===== BANKS =====
    banks_dir = base_dir / "banks"
    
    # Bank A (uses banking-premium profile)
    bank_a_prod = TopologyInstance(
        metadata=InstanceMetadata(
            name="bank-a-prod",
            extends="mssp/acme-corp/profiles/banking-premium",
            fleet_ref="./fleet.yaml"
        ),
        spec=TemplateSpec(
            vars={
                "client_code": "BANKA",
                "region": "EU-WEST",
            },
            repos=[
                Repo(name="repo-secu", hiddenrepopath=[
                    HiddenRepoPath(_id="nfs-tier", retention=3650),  # 10 years
                ]),
            ],
        )
    )
    bank_a_dir = banks_dir / "bank-a" / "prod"
    save_instance(bank_a_dir / "instance.yaml", bank_a_prod)
    save_fleet(bank_a_dir / "fleet.yaml", _create_bank_fleet("bank-a", "eu-west-1"))
    
    # Bank A Staging
    bank_a_staging = TopologyInstance(
        metadata=InstanceMetadata(
            name="bank-a-staging",
            extends="mssp/acme-corp/profiles/banking-premium",
            fleet_ref="./fleet.yaml"
        ),
        spec=TemplateSpec(
            vars={
                "client_code": "BANKA",
                "region": "EU-WEST",
                "retention_banking": 365,  # Shorter for staging
            },
        )
    )
    bank_a_stage_dir = banks_dir / "bank-a" / "staging"
    save_instance(bank_a_stage_dir / "instance.yaml", bank_a_staging)
    save_fleet(bank_a_stage_dir / "fleet.yaml", _create_small_fleet("bank-a-staging"))
    
    # Bank B (uses banking addon directly, different region)
    bank_b_prod = TopologyInstance(
        metadata=InstanceMetadata(
            name="bank-b-prod",
            extends="mssp/acme-corp/addons/banking",  # Uses addon directly
            fleet_ref="./fleet.yaml"
        ),
        spec=TemplateSpec(
            vars={
                "client_code": "BANKB",
                "region": "US-EAST",
            },
        )
    )
    bank_b_dir = banks_dir / "bank-b" / "prod"
    save_instance(bank_b_dir / "instance.yaml", bank_b_prod)
    save_fleet(bank_b_dir / "fleet.yaml", _create_bank_fleet("bank-b", "us-east-1"))
    
    # ===== ENTERPRISES =====
    enterprises_dir = base_dir / "enterprises"
    
    # Corp X (uses enterprise profile)
    corp_x_prod = TopologyInstance(
        metadata=InstanceMetadata(
            name="corp-x-prod",
            extends="mssp/acme-corp/profiles/enterprise",
            fleet_ref="./fleet.yaml"
        ),
        spec=TemplateSpec(
            vars={
                "client_code": "CORPX",
                "industry": "manufacturing",
            },
        )
    )
    corp_x_dir = enterprises_dir / "corp-x" / "prod"
    save_instance(corp_x_dir / "instance.yaml", corp_x_prod)
    save_fleet(corp_x_dir / "fleet.yaml", _create_enterprise_fleet("corp-x"))
    
    # Corp Y (uses simple profile)
    corp_y_prod = TopologyInstance(
        metadata=InstanceMetadata(
            name="corp-y-prod",
            extends="mssp/acme-corp/profiles/simple",
            fleet_ref="./fleet.yaml"
        ),
        spec=TemplateSpec(
            vars={
                "client_code": "CORPY",
            },
        )
    )
    corp_y_dir = enterprises_dir / "corp-y" / "prod"
    save_instance(corp_y_dir / "instance.yaml", corp_y_prod)
    save_fleet(corp_y_dir / "fleet.yaml", _create_small_fleet("corp-y"))


def _create_bank_fleet(name: str, region: str) -> Fleet:
    """Create fleet configuration for a bank."""
    return Fleet(
        metadata=FleetMetadata(name=name),
        spec=FleetSpec(
            management_mode="director",
            director=DirectorConfig(
                pool_uuid=f"pool-{name}",
                api_host="https://director.logpoint.com",
                credentials_ref="env://DIRECTOR_TOKEN"
            ),
            nodes=Nodes(
                data_nodes=[
                    DataNode(name=f"dn-{name}-01", logpoint_id=f"lp-{name}-p1",
                            tags=[{"cluster": "production"}, {"env": "prod"}, {"region": region}]),
                    DataNode(name=f"dn-{name}-02", logpoint_id=f"lp-{name}-p2",
                            tags=[{"cluster": "production"}, {"env": "prod"}, {"region": region}]),
                ],
                search_heads=[
                    SearchHead(name=f"sh-{name}-01", logpoint_id=f"lp-{name}-s1",
                              tags=[{"cluster": "frontend"}, {"env": "prod"}, {"sh-for": "production"}]),
                ]
            )
        )
    )


def _create_enterprise_fleet(name: str) -> Fleet:
    """Create fleet configuration for an enterprise."""
    return Fleet(
        metadata=FleetMetadata(name=name),
        spec=FleetSpec(
            management_mode="director",
            director=DirectorConfig(
                pool_uuid=f"pool-{name}",
                api_host="https://director.logpoint.com",
                credentials_ref="env://DIRECTOR_TOKEN"
            ),
            nodes=Nodes(
                data_nodes=[
                    DataNode(name=f"dn-{name}-01", logpoint_id=f"lp-{name}-p1",
                            tags=[{"cluster": "production"}, {"env": "prod"}]),
                ],
                search_heads=[
                    SearchHead(name=f"sh-{name}-01", logpoint_id=f"lp-{name}-s1",
                              tags=[{"cluster": "frontend"}, {"env": "prod"}, {"sh-for": "production"}]),
                ]
            )
        )
    )


def _create_small_fleet(name: str) -> Fleet:
    """Create small fleet (for staging/simple clients)."""
    return Fleet(
        metadata=FleetMetadata(name=name),
        spec=FleetSpec(
            management_mode="director",
            director=DirectorConfig(
                pool_uuid=f"pool-{name}",
                api_host="https://director.logpoint.com",
                credentials_ref="env://DIRECTOR_TOKEN"
            ),
            nodes=Nodes(
                aios=[
                    AIO(name=f"aio-{name}", logpoint_id=f"lp-{name}-a1",
                        tags=[{"env": "staging"}]),
                ]
            )
        )
    )
