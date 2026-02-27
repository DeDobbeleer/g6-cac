"""Example: Generate YAML configuration files for Director.

This script demonstrates how to:
1. Create configuration objects in Python
2. Save them to YAML files
3. Load them back for validation
"""

from pathlib import Path
from cac_configmgr.models import (
    ConfigTemplate,
    TemplateMetadata,
    TemplateSpec,
    TopologyInstance,
    InstanceMetadata,
    Repo,
    HiddenRepoPath,
    RoutingPolicy,
    RoutingCriterion,
    ProcessingPolicy,
    Fleet,
    FleetMetadata,
    FleetSpec,
    DirectorConfig,
    Nodes,
    DataNode,
    SearchHead,
)
from cac_configmgr.utils import (
    save_template,
    save_instance,
    save_fleet,
    load_template,
    load_instance,
    save_multi_file_template,
)


def create_golden_template() -> ConfigTemplate:
    """Create LogPoint Golden Template (Level 1)."""
    return ConfigTemplate(
        metadata=TemplateMetadata(
            name="golden-base",
            version="1.0.0",
            provider="logpoint"
        ),
        spec=TemplateSpec(
            vars={
                "default_retention": 90,
                "mount_point": "/opt/immune/storage"
            },
            repos=[
                Repo(
                    name="repo-default",
                    hiddenrepopath=[
                        HiddenRepoPath(
                            _id="primary",
                            path="{{mount_point}}",
                            retention="{{default_retention}}"
                        )
                    ]
                ),
                Repo(
                    name="repo-secu",
                    hiddenrepopath=[
                        HiddenRepoPath(
                            _id="primary",
                            path="{{mount_point}}",
                            retention=365
                        )
                    ]
                ),
            ],
            routing_policies=[
                RoutingPolicy(
                    policy_name="rp-default",
                    _id="rp-default",
                    catch_all="repo-default",
                    routing_criteria=[]
                )
            ]
        )
    )


def create_mssp_template() -> ConfigTemplate:
    """Create MSSP Base Template (Level 2)."""
    return ConfigTemplate(
        metadata=TemplateMetadata(
            name="acme-base",
            extends="logpoint/golden-base",
            version="1.0.0",
            provider="acme-mssp"
        ),
        spec=TemplateSpec(
            vars={
                "default_retention": 180,  # Override parent
                "mount_warm": "/opt/immune/storage-warm"
            },
            repos=[
                # Merge: Override retention for repo-default
                Repo(
                    name="repo-default",
                    hiddenrepopath=[
                        HiddenRepoPath(
                            _id="primary",
                            retention="{{default_retention}}"  # Now 180 instead of 90
                        )
                    ]
                ),
                # Add new repo
                Repo(
                    name="repo-archive",
                    hiddenrepopath=[
                        HiddenRepoPath(
                            _id="warm-tier",
                            path="{{mount_warm}}",
                            retention=1095
                        )
                    ]
                ),
            ]
        )
    )


def create_instance() -> TopologyInstance:
    """Create Client Instance (Level 4)."""
    return TopologyInstance(
        metadata=InstanceMetadata(
            name="client-bank-prod",
            extends="mssp/acme-corp/base",
            fleet_ref="./fleet.yaml"
        ),
        spec=TemplateSpec(
            vars={
                "client_code": "BANK",
                "compliance": "pci-dss"
            },
            repos=[
                # Override for banking compliance
                Repo(
                    name="repo-secu",
                    hiddenrepopath=[
                        HiddenRepoPath(
                            _id="primary",
                            retention=7  # Short on fast storage
                        ),
                        HiddenRepoPath(  # Add NFS tier for compliance
                            _id="nfs-tier",
                            path="/opt/immune/storage-nfs",
                            retention=2555  # 7 years
                        )
                    ]
                )
            ],
            processing_policies=[
                ProcessingPolicy(
                    name="pp-windows-sec",
                    _id="pp-windows-sec",
                    routing_policy="rp-windows-security",
                    normalization_policy="np-windows",
                    enrichment_policy="ep-geoip",
                    description="Windows security pipeline"
                )
            ]
        )
    )


def create_fleet() -> Fleet:
    """Create Fleet configuration."""
    return Fleet(
        metadata=FleetMetadata(name="client-bank"),
        spec=FleetSpec(
            management_mode="director",
            director=DirectorConfig(
                pool_uuid="pool-abc-123",
                api_host="https://director.logpoint.com",
                credentials_ref="env://DIRECTOR_TOKEN"
            ),
            nodes=Nodes(
                data_nodes=[
                    DataNode(
                        name="dn-prod-01",
                        logpoint_id="lp-dn-p1",
                        tags=[
                            {"cluster": "production"},
                            {"env": "prod"},
                            {"site": "frankfurt"}
                        ]
                    ),
                    DataNode(
                        name="dn-prod-02",
                        logpoint_id="lp-dn-p2",
                        tags=[
                            {"cluster": "production"},
                            {"env": "prod"},
                            {"site": "munich"}
                        ]
                    ),
                ],
                search_heads=[
                    SearchHead(
                        name="sh-prod-01",
                        logpoint_id="lp-sh-p1",
                        tags=[
                            {"cluster": "frontend"},
                            {"env": "prod"},
                            {"sh-for": "production"}
                        ]
                    )
                ]
            )
        )
    )


def main():
    """Generate example configuration files."""
    output_dir = Path(__file__).parent / "generated"
    output_dir.mkdir(exist_ok=True)
    
    print("Generating CaC-ConfigMgr configuration files...\n")
    
    # 1. Generate Golden Template
    golden = create_golden_template()
    golden_dir = output_dir / "logpoint" / "golden-base"
    save_multi_file_template(golden_dir, golden)
    print(f"✅ Golden Template: {golden_dir}")
    
    # 2. Generate MSSP Template
    mssp = create_mssp_template()
    mssp_dir = output_dir / "mssp" / "acme-corp" / "base"
    save_multi_file_template(mssp_dir, mssp)
    print(f"✅ MSSP Template: {mssp_dir}")
    
    # 3. Generate Instance (single file)
    instance = create_instance()
    instance_file = output_dir / "instances" / "client-bank" / "prod" / "instance.yaml"
    save_instance(instance_file, instance, comment="Client Bank - Production Instance")
    print(f"✅ Instance: {instance_file}")
    
    # 4. Generate Fleet
    fleet = create_fleet()
    fleet_file = output_dir / "instances" / "client-bank" / "prod" / "fleet.yaml"
    save_fleet(fleet_file, fleet, comment="Client Bank - Fleet Inventory")
    print(f"✅ Fleet: {fleet_file}")
    
    print("\n" + "=" * 60)
    print("Files generated successfully!")
    print("=" * 60)
    print(f"\nOutput directory: {output_dir}")
    print("\nYou can now:")
    print("1. Review the generated YAML files")
    print("2. Load them back: load_instance(instance_file)")
    print("3. Resolve the chain: engine.resolve(instance)")
    print("4. Push to Director: provider.apply(resolved)")


if __name__ == "__main__":
    main()
