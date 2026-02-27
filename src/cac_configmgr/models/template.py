"""Template models for hierarchical configuration.

Based on 20-TEMPLATE-HIERARCHY.md specification.
"""

from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field, field_validator

from .repos import Repo
from .routing import RoutingPolicy
from .processing import ProcessingPolicy


class TemplateMetadata(BaseModel):
    """Template metadata.
    
    Example:
        metadata:
          name: acme-base
          extends: logpoint/golden-base
          version: "1.0.0"
          provider: acme-mssp
    """
    name: str = Field(..., min_length=1, pattern=r"^[a-zA-Z0-9_-]+$")
    extends: str | None = Field(default=None, description="Parent template reference")
    version: str = Field(default="1.0.0", pattern=r"^\d+\.\d+\.\d+$")
    provider: str | None = Field(default=None, description="Template provider/organization")
    
    @field_validator("extends")
    @classmethod
    def validate_extends(cls, v):
        """Validate extends format: path/to/template or path/to/template@version."""
        if v is None:
            return v
        # Remove version suffix if present for validation
        base = v.split("@")[0]
        if "/" not in base:
            raise ValueError("extends must contain '/' (e.g., 'logpoint/golden-base')")
        return v
    
    def get_parent_ref(self) -> tuple[str, str | None]:
        """Parse extends into (template_ref, version).
        
        Returns:
            (template_ref, version_or_none)
            
        Example:
            "logpoint/golden-base@v2.1.0" -> ("logpoint/golden-base", "v2.1.0")
            "mssp/acme/base" -> ("mssp/acme/base", None)
        """
        if not self.extends:
            return (None, None)
        
        if "@" in self.extends:
            ref, version = self.extends.rsplit("@", 1)
            return (ref, version)
        return (self.extends, None)


class TemplateSpec(BaseModel):
    """Template specification containing all resource types.
    
    A template can define multiple resource types:
    - repos: List of Repo configurations
    - routing_policies: List of RoutingPolicy configurations
    - processing_policies: List of ProcessingPolicy configurations
    - vars: Variables for interpolation
    
    Example:
        spec:
          vars:
            retention_default: 90
          repos:
            - name: repo-secu
              hiddenrepopath:
                - _id: fast-tier
                  path: /opt/immune/storage
                  retention: 365
          routingPolicies:
            - policy_name: rp-windows
              _id: rp-windows
              catch_all: repo-system
    """
    vars: dict[str, Any] = Field(default_factory=dict, description="Variables for interpolation")
    repos: list[Repo] = Field(default_factory=list, alias="repos")
    routing_policies: list[RoutingPolicy] = Field(default_factory=list, alias="routingPolicies")
    processing_policies: list[ProcessingPolicy] = Field(default_factory=list, alias="processingPolicies")
    # Future resource types can be added here:
    # normalization_policies: list[NormalizationPolicy] = Field(default_factory=list, alias="normalizationPolicies")
    # enrichment_policies: list[EnrichmentPolicy] = Field(default_factory=list, alias="enrichmentPolicies")
    
    def get_all_resources(self) -> dict[str, list]:
        """Get all resources grouped by type.
        
        Returns:
            Dict mapping resource type name to list of resources.
        """
        return {
            "repos": self.repos,
            "routing_policies": self.routing_policies,
            "processing_policies": self.processing_policies,
        }
    
    def get_resource_by_name(self, resource_type: str, name: str) -> Any | None:
        """Get a specific resource by type and name.
        
        Args:
            resource_type: Type of resource (repos, routingPolicies, etc.)
            name: Resource name to find
            
        Returns:
            Resource object or None if not found.
        """
        resources = getattr(self, resource_type, [])
        for resource in resources:
            # Different resources have different name fields
            resource_name = getattr(resource, "name", None) or \
                          getattr(resource, "policy_name", None) or \
                          getattr(resource, "_id", None)
            if resource_name == name:
                return resource
        return None


class ConfigTemplate(BaseModel):
    """Configuration Template - core model for hierarchical inheritance.
    
    This is the main model for Level 1-3 templates (Golden, MSSP, Profiles).
    
    Example YAML:
        apiVersion: cac-configmgr.io/v1
        kind: ConfigTemplate
        metadata:
          name: acme-base
          extends: logpoint/golden-base
          version: "1.0.0"
          provider: acme-mssp
        spec:
          vars:
            retention: 180
          repos:
            - name: repo-secu
              hiddenrepopath:
                - _id: fast-tier
                  path: /opt/immune/storage
                  retention: 365
    """
    api_version: str = Field(default="cac-configmgr.io/v1", alias="apiVersion")
    kind: Literal["ConfigTemplate"] = Field(default="ConfigTemplate")
    metadata: TemplateMetadata
    spec: TemplateSpec
    
    def get_parent_path(self) -> str | None:
        """Get parent template path (without version)."""
        ref, _ = self.metadata.get_parent_ref()
        return ref
    
    def is_root(self) -> bool:
        """Check if this is a root template (no parent)."""
        return self.metadata.extends is None
    
    def get_template_id(self) -> str:
        """Get unique template identifier (path-like).
        
        Examples:
            logpoint/golden-base
            mssp/acme-corp/base
            mssp/acme-corp/profiles/enterprise
        """
        # This would be set by the loader based on file path
        # For now, return just the name
        return self.metadata.name


class InstanceMetadata(BaseModel):
    """Instance metadata (Level 4 - concrete deployment).
    
    Example:
        metadata:
          name: client-bank-prod
          extends: mssp/acme-corp/profiles/enterprise
          fleetRef: ./fleet.yaml
    """
    name: str = Field(..., min_length=1, pattern=r"^[a-zA-Z0-9_-]+$")
    extends: str = Field(..., description="Profile template to instantiate")
    fleet_ref: str = Field(..., alias="fleetRef", description="Path to fleet.yaml")


class TopologyInstance(BaseModel):
    """Topology Instance - concrete deployment (Level 4).
    
    Unlike ConfigTemplate which is multi-file (directory),
    TopologyInstance is single-file with only overrides.
    
    Example YAML:
        apiVersion: cac-configmgr.io/v1
        kind: TopologyInstance
        metadata:
          name: client-bank-prod
          extends: mssp/acme-corp/profiles/enterprise
          fleetRef: ./fleet.yaml
        spec:
          vars:
            clientCode: BANK
          repos:
            - name: repo-secu
              hiddenrepopath:
                - _id: nfs-tier
                  retention: 3650  # Override: 10 years for banking
    """
    api_version: str = Field(default="cac-configmgr.io/v1", alias="apiVersion")
    kind: Literal["TopologyInstance"] = Field(default="TopologyInstance")
    metadata: InstanceMetadata
    spec: TemplateSpec  # Same spec structure, but typically only overrides
    
    def get_profile_path(self) -> str:
        """Get parent profile path."""
        return self.metadata.extends


class TemplateChain(BaseModel):
    """Represents a complete inheritance chain from root to leaf.
    
    Used during template resolution to merge all templates in order.
    
    Example chain:
        logpoint/golden-base
        └── mssp/acme-corp/base
            └── mssp/acme-corp/profiles/enterprise
                └── instances/client-bank/prod
    """
    templates: list[ConfigTemplate | TopologyInstance]
    
    def get_root(self) -> ConfigTemplate | None:
        """Get the root template (first in chain)."""
        if not self.templates:
            return None
        root = self.templates[0]
        return root if isinstance(root, ConfigTemplate) else None
    
    def get_leaf(self) -> ConfigTemplate | TopologyInstance | None:
        """Get the leaf template (last in chain)."""
        if not self.templates:
            return None
        return self.templates[-1]
    
    def __iter__(self):
        """Iterate over templates from root to leaf."""
        return iter(self.templates)
    
    def __len__(self) -> int:
        return len(self.templates)
