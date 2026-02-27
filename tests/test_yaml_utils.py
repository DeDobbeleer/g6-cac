"""Tests for YAML utilities."""

import pytest
from pathlib import Path
from cac_configmgr.utils import (
    load_yaml,
    save_yaml,
    load_template,
    load_instance,
    save_template,
    save_instance,
    YamlError,
)
from cac_configmgr.models import ConfigTemplate, TopologyInstance


class TestYamlUtils:
    """Test YAML loading and saving."""
    
    def test_load_save_yaml_roundtrip(self, tmp_path):
        """Test loading and saving YAML preserves data."""
        data = {
            "name": "test-config",
            "version": "1.0.0",
            "spec": {
                "repos": [
                    {"name": "repo-1", "retention": 90}
                ]
            }
        }
        
        file_path = tmp_path / "test.yaml"
        save_yaml(file_path, data)
        loaded = load_yaml(file_path)
        
        assert loaded["name"] == "test-config"
        assert loaded["version"] == "1.0.0"
        assert loaded["spec"]["repos"][0]["name"] == "repo-1"
    
    def test_load_nonexistent_file(self, tmp_path):
        """Test loading non-existent file raises error."""
        with pytest.raises(YamlError) as exc_info:
            load_yaml(tmp_path / "nonexistent.yaml")
        
        assert "not found" in str(exc_info.value).lower()
    
    def test_save_with_comment(self, tmp_path):
        """Test saving YAML with header comment."""
        data = {"name": "test"}
        file_path = tmp_path / "test.yaml"
        
        save_yaml(file_path, data, comment="This is a test file")
        
        content = file_path.read_text()
        assert "# This is a test file" in content


class TestTemplateSerialization:
    """Test template loading and saving."""
    
    def test_save_load_template_roundtrip(self, tmp_path):
        """Test saving and loading ConfigTemplate."""
        template = ConfigTemplate(
            metadata={
                "name": "test-template",
                "version": "1.0.0",
                "provider": "test"
            },
            spec={
                "vars": {"retention": 90},
                "repos": [
                    {
                        "name": "repo-secu",
                        "hiddenrepopath": [
                            {"_id": "primary", "path": "/opt/immune/storage", "retention": 365}
                        ]
                    }
                ]
            }
        )
        
        file_path = tmp_path / "template.yaml"
        save_template(file_path, template)
        loaded = load_template(file_path)
        
        assert loaded.metadata.name == "test-template"
        assert loaded.spec.vars["retention"] == 90
        assert len(loaded.spec.repos) == 1
        assert loaded.spec.repos[0].name == "repo-secu"
    
    def test_save_load_instance_roundtrip(self, tmp_path):
        """Test saving and loading TopologyInstance."""
        instance = TopologyInstance(
            metadata={
                "name": "test-instance",
                "extends": "mssp/acme/base",
                "fleetRef": "./fleet.yaml"
            },
            spec={
                "vars": {"clientCode": "TEST"},
                "repos": [
                    {
                        "name": "repo-override",
                        "hiddenrepopath": [
                            {"_id": "primary", "retention": 7}
                        ]
                    }
                ]
            }
        )
        
        file_path = tmp_path / "instance.yaml"
        save_instance(file_path, instance)
        loaded = load_instance(file_path)
        
        assert loaded.metadata.name == "test-instance"
        assert loaded.metadata.fleet_ref == "./fleet.yaml"
        assert loaded.spec.vars["clientCode"] == "TEST"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
