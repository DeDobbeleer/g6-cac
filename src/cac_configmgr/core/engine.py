"""Resolution Engine - Orchestrates the complete template resolution process.

This is the high-level API that combines:
1. Template resolution (build inheritance chain)
2. Resource merging (deep merge with _id matching)
3. Variable interpolation (substitute {{variables}})
4. ID filtering (remove internal _id and _action fields)

Based on Section 5 of 20-TEMPLATE-HIERARCHY.md specification.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from dataclasses import dataclass

from ..models.template import TopologyInstance, ConfigTemplate, TemplateChain, TemplateSpec
from .resolver import TemplateResolver
from .merger import merge_resources, deep_merge
from .interpolator import Interpolator, collect_variables_from_chain


@dataclass
class ResolvedConfiguration:
    """Result of template resolution.
    
    Contains the fully resolved and interpolated configuration
    ready for deployment or comparison.
    
    Attributes:
        resources: Dict of resource type to list of resources
        variables: Final merged variables
        source_chain: The template chain used for resolution
    """
    resources: dict[str, list]
    variables: dict[str, Any]
    source_chain: TemplateChain
    
    def get_resource(self, resource_type: str, name: str) -> Any | None:
        """Get a specific resource by type and name."""
        resources = self.resources.get(resource_type, [])
        for resource in resources:
            resource_name = resource.get("name") or resource.get("policy_name") or resource.get("_id")
            if resource_name == name:
                return resource
        return None
    
    def to_api_payload(self) -> dict[str, Any]:
        """Convert to API payload (with _id fields filtered out)."""
        return {
            resource_type: filter_internal_ids(resources)
            for resource_type, resources in self.resources.items()
            if resources  # Only include non-empty resource types
        }


class ResolutionEngine:
    """High-level engine for template resolution.
    
    Usage:
        engine = ResolutionEngine(templates_dir=Path("./templates"))
        instance = load_instance(Path("./instances/client/prod/instance.yaml"))
        resolved = engine.resolve(instance)
        
        # Deploy
        api_payload = resolved.to_api_payload()
    """
    
    def __init__(self, templates_dir: Path):
        """Initialize resolution engine.
        
        Args:
            templates_dir: Root directory containing all templates
        """
        self.templates_dir = templates_dir
        self.resolver = TemplateResolver(templates_dir)
    
    def resolve(self, instance: TopologyInstance) -> ResolvedConfiguration:
        """Resolve complete configuration for an instance.
        
        Process:
        1. Build inheritance chain (resolver)
        2. Collect variables from all templates
        3. Merge resources by type
        4. Interpolate variables
        5. Filter internal IDs for API
        
        Args:
            instance: Topology instance to resolve
            
        Returns:
            Resolved configuration ready for deployment
        """
        # Step 1: Build inheritance chain
        chain = self.resolver.resolve(instance)
        
        # Step 2: Collect variables from root to leaf
        variables = collect_variables_from_chain(chain.templates)
        
        # Step 3: Merge resources by type
        merged_resources = self._merge_chain_resources(chain)
        
        # Step 4: Interpolate variables
        interpolator = Interpolator(variables)
        interpolated_resources = {
            resource_type: interpolator.interpolate(resources)
            for resource_type, resources in merged_resources.items()
        }
        
        return ResolvedConfiguration(
            resources=interpolated_resources,
            variables=variables,
            source_chain=chain
        )
    
    def _merge_chain_resources(self, chain: TemplateChain) -> dict[str, list]:
        """Merge resources from all templates in chain.
        
        Resources are merged from root to leaf, with leaf values taking precedence.
        
        Args:
            chain: Template chain from root to leaf
            
        Returns:
            Dict of resource type to merged resource list
        """
        merged: dict[str, list] = {}
        
        for template in chain:
            if not hasattr(template, "spec"):
                continue
                
            spec = template.spec
            if not isinstance(spec, TemplateSpec):
                continue
            
            # Get all resources from this template
            resources = spec.get_all_resources()
            
            # Merge each resource type
            for resource_type, resource_list in resources.items():
                if not resource_list:
                    continue
                
                # Convert Pydantic models to dicts for merging
                # Use by_alias=False to keep Python field names (snake_case)
                resource_dicts = [
                    r.model_dump(by_alias=False, exclude_none=True) if hasattr(r, "model_dump") else r
                    for r in resource_list
                ]
                
                if resource_type not in merged:
                    merged[resource_type] = resource_dicts
                else:
                    merged[resource_type] = merge_resources(
                        merged[resource_type],
                        resource_dicts
                    )
        
        return merged


def filter_internal_ids(obj: Any) -> Any:
    """Remove all internal fields (starting with _) from object.
    
    This is the final step before sending to API.
    
    Args:
        obj: Object to filter (dict, list, or primitive)
        
    Returns:
        Object with _fields removed
    """
    if isinstance(obj, dict):
        return {
            k: filter_internal_ids(v)
            for k, v in obj.items()
            if not k.startswith("_")
        }
    elif isinstance(obj, list):
        return [filter_internal_ids(item) for item in obj]
    else:
        return obj
