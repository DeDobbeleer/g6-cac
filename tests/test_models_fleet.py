"""Tests for Fleet models."""

import pytest
from cac_configmgr.models.fleet import Fleet, Tag, DataNode


class TestTag:
    def test_tag_creation(self):
        tag = Tag(key="cluster", value="production")
        assert tag.key == "cluster"
        assert tag.value == "production"
    
    def test_tag_from_dict(self):
        tag = Tag.from_dict({"cluster": "production"})
        assert tag.key == "cluster"
        assert tag.value == "production"


class TestFleet:
    def test_fleet_from_yaml_dict(self):
        """Test loading fleet from YAML-like dict."""
        data = {
            "apiVersion": "cac-configmgr.io/v1",
            "kind": "Fleet",
            "metadata": {"name": "client-alpha"},
            "spec": {
                "managementMode": "director",
                "director": {
                    "poolUuid": "aaa-111",
                    "apiHost": "https://director.logpoint.com",
                    "credentialsRef": "env://TOKEN"
                },
                "nodes": {
                    "dataNodes": [
                        {
                            "name": "dn-prod-01",
                            "logpointId": "lp-dn-p1",
                            "tags": [
                                {"cluster": "production"},
                                {"env": "prod"}
                            ]
                        }
                    ]
                }
            }
        }
        
        fleet = Fleet(**data)
        assert fleet.metadata.name == "client-alpha"
        assert len(fleet.spec.nodes.data_nodes) == 1
