"""YAML serialization and deserialization utilities.

Handles loading and saving of CaC-ConfigMgr configuration files.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, TypeVar
from collections import OrderedDict

import yaml
from pydantic import BaseModel

from ..models import ConfigTemplate, TopologyInstance, Fleet

T = TypeVar("T", bound=BaseModel)


class YamlError(Exception):
    """Error during YAML parsing or serialization."""
    pass


def _represent_ordereddict(dumper, data):
    """Custom YAML representer for OrderedDict to maintain key order."""
    return dumper.represent_mapping("tag:yaml.org,2002:map", data.items())


def _setup_yaml():
    """Setup YAML parser with custom configuration."""
    # Use SafeLoader for security
    yaml.SafeLoader.add_constructor(
        "tag:yaml.org,2002:timestamp",
        yaml.SafeLoader.construct_yaml_str  # Parse timestamps as strings
    )
    
    # Custom representer for cleaner output
    yaml.add_representer(OrderedDict, _represent_ordereddict)


_setup_yaml()


def load_yaml(path: Path) -> dict[str, Any]:
    """Load YAML file as dictionary.
    
    Args:
        path: Path to YAML file
        
    Returns:
        Dictionary representation of YAML content
        
    Raises:
        YamlError: If file not found or invalid YAML
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = yaml.safe_load(f)
            if content is None:
                return {}
            return content
    except FileNotFoundError:
        raise YamlError(f"File not found: {path}")
    except yaml.YAMLError as e:
        raise YamlError(f"Invalid YAML in {path}: {e}")


def save_yaml(path: Path, data: dict[str, Any], comment: str | None = None) -> None:
    """Save dictionary to YAML file.
    
    Args:
        path: Path to output YAML file
        data: Dictionary to save
        comment: Optional header comment
        
    Raises:
        YamlError: If unable to write file
    """
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, "w", encoding="utf-8") as f:
            if comment:
                f.write(f"# {comment}\n")
                f.write("#\n")
            
            # Custom YAML representer for clean output
            yaml.dump(
                data,
                f,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,  # Preserve key order
                width=120,
                indent=2,
            )
    except OSError as e:
        raise YamlError(f"Cannot write to {path}: {e}")


def load_template(path: Path) -> ConfigTemplate:
    """Load ConfigTemplate from YAML file.
    
    Args:
        path: Path to template YAML file (e.g., repos.yaml)
        
    Returns:
        ConfigTemplate instance
        
    Raises:
        YamlError: If file invalid or missing required fields
    """
    data = load_yaml(path)
    
    try:
        return ConfigTemplate(**data)
    except Exception as e:
        raise YamlError(f"Invalid ConfigTemplate in {path}: {e}")


def load_instance(path: Path) -> TopologyInstance:
    """Load TopologyInstance from YAML file.
    
    Args:
        path: Path to instance.yaml
        
    Returns:
        TopologyInstance instance
        
    Raises:
        YamlError: If file invalid or missing required fields
    """
    data = load_yaml(path)
    
    try:
        return TopologyInstance(**data)
    except Exception as e:
        raise YamlError(f"Invalid TopologyInstance in {path}: {e}")


def load_fleet(path: Path) -> Fleet:
    """Load Fleet from YAML file.
    
    Args:
        path: Path to fleet.yaml
        
    Returns:
        Fleet instance
        
    Raises:
        YamlError: If file invalid or missing required fields
    """
    data = load_yaml(path)
    
    try:
        return Fleet(**data)
    except Exception as e:
        raise YamlError(f"Invalid Fleet in {path}: {e}")


def save_template(path: Path, template: ConfigTemplate, comment: str | None = None) -> None:
    """Save ConfigTemplate to YAML file.
    
    Args:
        path: Path to output YAML file
        template: ConfigTemplate to save
        comment: Optional header comment
    """
    # Convert to dict with aliases (camelCase for YAML)
    data = template.model_dump(by_alias=True, exclude_none=True)
    save_yaml(path, data, comment)


def save_instance(path: Path, instance: TopologyInstance, comment: str | None = None) -> None:
    """Save TopologyInstance to YAML file.
    
    Args:
        path: Path to output YAML file
        instance: TopologyInstance to save
        comment: Optional header comment
    """
    data = instance.model_dump(by_alias=True, exclude_none=True)
    save_yaml(path, data, comment)


def _convert_tags_for_yaml(data: dict) -> dict:
    """Convert tags from model format to simple dict format.
    
    Model format: [{"key": "cluster", "value": "prod"}, ...]
    YAML format: [{"cluster": "prod"}, ...]
    """
    if isinstance(data, dict):
        result = {}
        for k, v in data.items():
            if k == "tags" and isinstance(v, list):
                # Convert tags to simple dict format
                result[k] = []
                for tag in v:
                    if isinstance(tag, dict) and "key" in tag and "value" in tag:
                        result[k].append({tag["key"]: tag["value"]})
                    else:
                        result[k].append(tag)
            else:
                result[k] = _convert_tags_for_yaml(v)
        return result
    elif isinstance(data, list):
        return [_convert_tags_for_yaml(item) for item in data]
    else:
        return data


def save_fleet(path: Path, fleet: Fleet, comment: str | None = None) -> None:
    """Save Fleet to YAML file.
    
    Args:
        path: Path to output YAML file
        fleet: Fleet to save
        comment: Optional header comment
    """
    data = fleet.model_dump(by_alias=True, exclude_none=True)
    # Convert tags to simple format for cleaner YAML
    data = _convert_tags_for_yaml(data)
    save_yaml(path, data, comment)


def load_multi_file_template(template_dir: Path) -> ConfigTemplate:
    """Load a multi-file template from directory.
    
    A multi-file template has one file per resource type:
    - repos.yaml
    - routing-policies.yaml
    - processing-policies.yaml
    - etc.
    
    All files are merged into a single ConfigTemplate.
    
    Args:
        template_dir: Directory containing template files
        
    Returns:
        Merged ConfigTemplate
        
    Raises:
        YamlError: If no valid template files found
    """
    if not template_dir.is_dir():
        raise YamlError(f"Not a directory: {template_dir}")
    
    # Find all YAML files
    yaml_files = list(template_dir.glob("*.yaml")) + list(template_dir.glob("*.yml"))
    
    if not yaml_files:
        raise YamlError(f"No YAML files found in {template_dir}")
    
    # Load and merge all files
    merged_data: dict[str, Any] = {
        "apiVersion": "cac-configmgr.io/v1",
        "kind": "ConfigTemplate",
        "metadata": {},
        "spec": {}
    }
    
    for yaml_file in sorted(yaml_files):
        data = load_yaml(yaml_file)
        
        # Skip non-template files
        if data.get("kind") != "ConfigTemplate":
            continue
        
        # Merge metadata (last file wins for simple fields)
        if "metadata" in data:
            merged_data["metadata"].update(data["metadata"])
        
        # Merge spec resources
        if "spec" in data:
            for key, value in data["spec"].items():
                if key in merged_data["spec"]:
                    # Append to existing list
                    if isinstance(value, list) and isinstance(merged_data["spec"][key], list):
                        merged_data["spec"][key].extend(value)
                    else:
                        # Override
                        merged_data["spec"][key] = value
                else:
                    merged_data["spec"][key] = value
    
    return ConfigTemplate(**merged_data)


def save_multi_file_template(template_dir: Path, template: ConfigTemplate) -> None:
    """Save ConfigTemplate to multi-file directory structure.
    
    Resources are split by type into separate files:
    - vars.yaml (template variables)
    - repos.yaml
    - routing-policies.yaml
    - etc.
    
    Args:
        template_dir: Output directory
        template: ConfigTemplate to save
    """
    template_dir.mkdir(parents=True, exist_ok=True)
    
    # Get template data
    full_data = template.model_dump(by_alias=True, exclude_none=True)
    
    # Common metadata for all files
    metadata = full_data.get("metadata", {})
    
    spec = full_data.get("spec", {})
    
    # Save vars first (if any)
    vars_data = spec.get("vars", {})
    if vars_data:
        vars_file_data = {
            "apiVersion": full_data.get("apiVersion", "cac-configmgr.io/v1"),
            "kind": "ConfigTemplate",
            "metadata": metadata,
            "spec": {"vars": vars_data}
        }
        save_yaml(
            template_dir / "vars.yaml",
            vars_file_data,
            comment="CaC-ConfigMgr Template - variables"
        )
    
    # Split by resource type
    resource_types = {
        "repos": "repos.yaml",
        "routingPolicies": "routing-policies.yaml",
        "processingPolicies": "processing-policies.yaml",
        "normalizationPolicies": "normalization-policies.yaml",
        "enrichmentPolicies": "enrichment-policies.yaml",
    }
    
    for resource_key, filename in resource_types.items():
        if resource_key in spec and spec[resource_key]:
            # Create file for this resource type
            file_data = {
                "apiVersion": full_data.get("apiVersion", "cac-configmgr.io/v1"),
                "kind": "ConfigTemplate",
                "metadata": metadata,
                "spec": {resource_key: spec[resource_key]}
            }
            
            file_path = template_dir / filename
            save_yaml(
                file_path,
                file_data,
                comment=f"CaC-ConfigMgr Template - {resource_key}"
            )
