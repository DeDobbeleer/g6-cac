"""API Conventions abstraction for multi-provider validation.

This module defines the APIConvention interface that abstracts the differences
between various LogPoint API implementations (Director, Direct, SOAR, NDR, etc.).

The convention pattern allows the same validation logic to work with different
API specifications by delegating provider-specific decisions to the convention
implementation.

Example:
    # Director API uses camelCase for some fields
    convention = DirectorAPIConvention()
    api_field = convention.get_field_alias("processing_policy", "routing_policy")
    # Returns: "routingPolicy"
    
    # Direct API might use different conventions
    convention = DirectAPIConvention()  # Future
    api_field = convention.get_field_alias("processing_policy", "routing_policy")
    # Returns: "routing_policy"  # snake_case
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class FieldSpec:
    """Specification for an API field.
    
    Attributes:
        name: Internal field name (in CaC templates)
        type: Expected Python type
        required: Whether the field is required
        alias: API field name if different from internal name
        pattern: Regex pattern for validation (strings only)
        default: Default value if not provided
        api_doc: Link to API documentation
    """
    name: str
    type: type
    required: bool = True
    alias: str | None = None
    pattern: str | None = None
    default: Any = None
    api_doc: str = ""


@dataclass
class ResourceSpec:
    """Specification for a resource type.
    
    Attributes:
        resource_type: Internal resource type name
        endpoint: API endpoint path (e.g., "/routingpolicies")
        name_field: Field used as the resource identifier/name
        fields: Mapping of field names to their specifications
    """
    resource_type: str
    endpoint: str
    name_field: str
    fields: dict[str, FieldSpec]


class APIConvention(ABC):
    """Abstract base class for API conventions.
    
    An APIConvention defines:
    - Field naming conventions (snake_case vs camelCase)
    - Required fields and their types
    - Resource-specific naming fields
    - API endpoint mappings
    - Validation patterns
    
    Implementations:
    - DirectorAPIConvention: LogPoint Director API (MSSP, multi-tenant)
    - DirectAPIConvention: Direct SIEM API (future)
    - MockAPIConvention: For testing
    """
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider identifier.
        
        Returns:
            Provider name (e.g., "director", "direct", "soar")
        """
        pass
    
    @property
    @abstractmethod
    def api_version(self) -> str:
        """Return the API version.
        
        Returns:
            API version string (e.g., "v1.3", "v2")
        """
        pass
    
    @abstractmethod
    def get_resource_spec(self, resource_type: str) -> ResourceSpec | None:
        """Get specification for a resource type.
        
        Args:
            resource_type: Resource type (e.g., "routing_policies")
            
        Returns:
            ResourceSpec or None if resource type unknown
        """
        pass
    
    @abstractmethod
    def get_field_alias(self, resource_type: str, field_name: str) -> str:
        """Get the API field name for a given internal field.
        
        Args:
            resource_type: Type of resource
            field_name: Internal field name (from CaC templates)
            
        Returns:
            API field name (may differ by convention)
            
        Example:
            # Director convention (camelCase)
            get_field_alias("processing_policy", "routing_policy")
            # Returns: "routingPolicy"
            
            # Direct convention (snake_case)
            get_field_alias("processing_policy", "routing_policy")
            # Returns: "routing_policy"
        """
        pass
    
    @abstractmethod
    def get_name_field(self, resource_type: str) -> str:
        """Get the name field for a resource type.
        
        Different resource types use different name fields:
        - RoutingPolicy: "policy_name"
        - NormalizationPolicy: "name" (exception!)
        
        Args:
            resource_type: Resource type
            
        Returns:
            Name field key
        """
        pass
    
    @abstractmethod
    def get_endpoint(self, resource_type: str) -> str | None:
        """Get API endpoint for a resource type.
        
        Args:
            resource_type: Resource type
            
        Returns:
            Endpoint path or None if not supported
        """
        pass
    
    @abstractmethod
    def get_supported_resources(self) -> list[str]:
        """Get list of supported resource types.
        
        Returns:
            List of resource type identifiers
        """
        pass
    
    @abstractmethod
    def get_cross_reference_validations(self) -> list[CrossReferenceRule]:
        """Get cross-reference validation rules.
        
        Returns:
            List of rules defining which fields reference which resources
        """
        pass
    
    def get_field_spec(self, resource_type: str, field_name: str) -> FieldSpec | None:
        """Get specification for a specific field.
        
        Args:
            resource_type: Resource type
            field_name: Field name
            
        Returns:
            FieldSpec or None if not found
        """
        resource_spec = self.get_resource_spec(resource_type)
        if not resource_spec:
            return None
        return resource_spec.fields.get(field_name)


@dataclass
class CrossReferenceRule:
    """Rule for cross-reference validation.
    
    Defines that a field in one resource type must reference
    an existing resource of another type.
    
    Attributes:
        source_type: Resource type containing the reference
        source_field: Field name containing the reference
        target_type: Resource type being referenced
        allow_none: Whether null/"None" values are allowed
        description: Human-readable description of the rule
    """
    source_type: str
    source_field: str
    target_type: str
    allow_none: bool = True
    description: str = ""


class ConventionRegistry:
    """Registry of available API conventions.
    
    Provides factory access to convention implementations.
    
    Example:
        registry = ConventionRegistry()
        registry.register("director", DirectorAPIConvention)
        
        convention = registry.get("director")
        # or
        convention = registry.get_for_provider("logpoint", "director", "v1.3")
    """
    
    def __init__(self):
        """Initialize empty registry."""
        self._conventions: dict[str, type[APIConvention]] = {}
    
    def register(self, name: str, convention_class: type[APIConvention]) -> None:
        """Register a convention implementation.
        
        Args:
            name: Convention identifier
            convention_class: Convention class (not instance)
        """
        self._conventions[name] = convention_class
    
    def get(self, name: str) -> APIConvention:
        """Get convention instance by name.
        
        Args:
            name: Convention identifier
            
        Returns:
            Convention instance
            
        Raises:
            KeyError: If convention not registered
        """
        if name not in self._conventions:
            raise KeyError(f"Unknown convention: {name}. "
                          f"Available: {list(self._conventions.keys())}")
        return self._conventions[name]()
    
    def get_for_provider(
        self, 
        provider: str, 
        deployment_mode: str = "director",
        api_version: str = "v1.3"
    ) -> APIConvention:
        """Get appropriate convention for provider configuration.
        
        Args:
            provider: Provider name (e.g., "logpoint")
            deployment_mode: Deployment mode ("director" or "direct")
            api_version: API version
            
        Returns:
            Appropriate convention instance
            
        Raises:
            KeyError: If no convention available for configuration
        """
        # Map configuration to convention name
        key = f"{provider}/{deployment_mode}/{api_version}"
        
        # Try exact match
        if key in self._conventions:
            return self._conventions[key]()
        
        # Try without version
        key = f"{provider}/{deployment_mode}"
        if key in self._conventions:
            return self._conventions[key]()
        
        # Fallback to deployment mode only
        if deployment_mode in self._conventions:
            return self._conventions[deployment_mode]()
        
        raise KeyError(f"No convention found for {provider}/{deployment_mode}/{api_version}")
    
    def list_conventions(self) -> list[str]:
        """List registered convention names.
        
        Returns:
            List of convention identifiers
        """
        return list(self._conventions.keys())


# Global registry instance
_registry: ConventionRegistry | None = None


def get_registry() -> ConventionRegistry:
    """Get the global convention registry.
    
    Returns:
        Global ConventionRegistry instance
    """
    global _registry
    if _registry is None:
        _registry = ConventionRegistry()
    return _registry


def register_convention(name: str, convention_class: type[APIConvention]) -> None:
    """Register a convention in the global registry.
    
    Args:
        name: Convention identifier
        convention_class: Convention class
    """
    get_registry().register(name, convention_class)


def get_convention(name: str) -> APIConvention:
    """Get convention from global registry.
    
    Args:
        name: Convention identifier
        
    Returns:
        Convention instance
    """
    return get_registry().get(name)
