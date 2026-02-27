"""Pydantic models for configuration resources.

Based on specifications:
- 20-TEMPLATE-HIERARCHY: Template inheritance, Repos, Routing
- 10-INVENTORY-FLEET: Fleet inventory
- 30-PROCESSING-POLICIES: Processing policies
"""

from .fleet import (
    Fleet,
    FleetMetadata,
    FleetSpec,
    DirectorConfig,
    Nodes,
    Node,
    AIO,
    DataNode,
    SearchHead,
    Tag,
)

from .template import (
    ConfigTemplate,
    TemplateMetadata,
    TemplateSpec,
    TopologyInstance,
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
)

from .enrichment import (
    EnrichmentPolicy,
)

__all__ = [
    # Fleet
    "Fleet",
    "FleetMetadata",
    "FleetSpec",
    "DirectorConfig",
    "Nodes",
    "Node",
    "AIO",
    "DataNode",
    "SearchHead",
    "Tag",
    # Template
    "ConfigTemplate",
    "TemplateMetadata",
    "TemplateSpec",
    "TopologyInstance",
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
    # Enrichment
    "EnrichmentPolicy",
]
