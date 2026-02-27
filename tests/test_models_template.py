"""Tests for Template models."""

import pytest
from cac_configmgr.models import (
    ConfigTemplate,
    TemplateMetadata,
    TemplateSpec,
    TopologyInstance,
    InstanceMetadata,
    Repo,
    RoutingPolicy,
    ProcessingPolicy,
)


class TestTemplateMetadata:
    def test_metadata_creation(self):
        meta = TemplateMetadata(name="acme-base", extends="logpoint/golden-base")
        assert meta.name == "acme-base"
        assert meta.extends == "logpoint/golden-base"
        assert meta.version == "1.0.0"
    
    def test_get_parent_ref_with_version(self):
        meta = TemplateMetadata(name="test", extends="logpoint/golden-base@v2.1.0")
        ref, version = meta.get_parent_ref()
        assert ref == "logpoint/golden-base"
        assert version == "v2.1.0"
    
    def test_get_parent_ref_without_version(self):
        meta = TemplateMetadata(name="test", extends="mssp/acme/base")
        ref, version = meta.get_parent_ref()
        assert ref == "mssp/acme/base"
        assert version is None


class TestConfigTemplate:
    def test_template_from_yaml_dict(self):
        """Test loading template from YAML-like dict."""
        data = {
            "apiVersion": "cac-configmgr.io/v1",
            "kind": "ConfigTemplate",
            "metadata": {
                "name": "acme-base",
                "extends": "logpoint/golden-base",
                "version": "1.0.0",
                "provider": "acme-mssp"
            },
            "spec": {
                "vars": {
                    "retention": 180
                },
                "repos": [
                    {
                        "name": "repo-secu",
                        "hiddenrepopath": [
                            {"_id": "fast-tier", "path": "/opt/immune/storage", "retention": 365}
                        ]
                    }
                ]
            }
        }
        
        template = ConfigTemplate(**data)
        assert template.metadata.name == "acme-base"
        assert template.metadata.provider == "acme-mssp"
        assert template.spec.vars["retention"] == 180
        assert len(template.spec.repos) == 1
        
        repo = template.spec.repos[0]
        assert repo.name == "repo-secu"
        assert len(repo.hiddenrepopath) == 1
        assert repo.hiddenrepopath[0]._id == "fast-tier"
    
    def test_is_root(self):
        root = ConfigTemplate(
            metadata={"name": "golden-base"},
            spec={}
        )
        assert root.is_root() is True
        
        child = ConfigTemplate(
            metadata={"name": "acme-base", "extends": "logpoint/golden-base"},
            spec={}
        )
        assert child.is_root() is False


class TestTopologyInstance:
    def test_instance_from_yaml_dict(self):
        """Test loading instance from YAML-like dict."""
        data = {
            "apiVersion": "cac-configmgr.io/v1",
            "kind": "TopologyInstance",
            "metadata": {
                "name": "client-bank-prod",
                "extends": "mssp/acme-corp/profiles/enterprise",
                "fleetRef": "./fleet.yaml"
            },
            "spec": {
                "vars": {
                    "clientCode": "BANK"
                },
                "repos": [
                    {
                        "name": "repo-secu",
                        "hiddenrepopath": [
                            {"_id": "nfs-tier", "path": "/opt/immune/storage-nfs", "retention": 3650}
                        ]
                    }
                ]
            }
        }
        
        instance = TopologyInstance(**data)
        assert instance.metadata.name == "client-bank-prod"
        assert instance.metadata.fleet_ref == "./fleet.yaml"
        assert instance.spec.vars["clientCode"] == "BANK"


class TestProcessingPolicy:
    def test_processing_policy_creation(self):
        pp = ProcessingPolicy(
            name="windows-security",
            _id="pp-windows-sec",
            routingPolicy="rp-windows-security",
            normalizationPolicy="np-windows",
            enrichmentPolicy="ep-geoip"
        )
        assert pp.name == "windows-security"
        assert pp.routing_policy == "rp-windows-security"
        assert pp.normalization_policy == "np-windows"
        assert pp.enrichment_policy == "ep-geoip"
        assert pp.enabled is True
    
    def test_processing_policy_optional_fields(self):
        pp = ProcessingPolicy(
            name="default-pipeline",
            _id="pp-default",
            routingPolicy="rp-default"
            # normalization and enrichment omitted
        )
        assert pp.normalization_policy is None
        assert pp.enrichment_policy is None
        assert pp.is_complete() is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
