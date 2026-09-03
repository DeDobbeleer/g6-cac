"""Pydantic models for configuration resources.

Based on specifications:
- 20-TEMPLATE-HIERARCHY: Template inheritance, Repos, Routing
- 30-PROCESSING-POLICIES: Processing policies
"""

from .template import (
    ConfigTemplate,
    TemplateMetadata,
    TemplateSpec,
    Instance,
    InstanceMetadata,
    TemplateChain,
)

from .repos import (
    Repo,
    HiddenRepoPath,
)

from .routing import (
    RoutingPolicy,
    RoutingCriterion,
)

from .processing import (
    ProcessingPolicy,
)

from .normalization import (
    NormalizationPolicy,
    NormalizationPackage,
)

from .enrichment import (
    EnrichmentPolicy,
    EnrichmentSpecification,
    EnrichmentCriterion,
    EnrichmentRule,
)

from .device_groups import (
    DeviceGroup,
    Criterion,
)

from .devices import (
    Device,
)

__all__ = [
    # Template
    "ConfigTemplate",
    "TemplateMetadata",
    "TemplateSpec",
    "Instance",
    "InstanceMetadata",
    "TemplateChain",
    # Repos
    "Repo",
    "HiddenRepoPath",
    # Routing
    "RoutingPolicy",
    "RoutingCriterion",
    # Processing
    "ProcessingPolicy",
    # Normalization
    "NormalizationPolicy",
    "NormalizationPackage",
    # Enrichment
    "EnrichmentPolicy",
    "EnrichmentSpecification",
    "EnrichmentCriterion",
    "EnrichmentRule",
    # Device Groups
    "DeviceGroup",
    "Criterion",
    # Devices
    "Device",
]
