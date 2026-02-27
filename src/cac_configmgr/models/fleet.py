"""Fleet inventory models.

Based on 10-INVENTORY-FLEET.md specification.
"""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field, field_validator, ConfigDict


class Tag(BaseModel):
    """A tag is a key-value pair for node classification.
    
    Examples:
        - cluster: production
        - env: staging
        - sh-for: production
    """
    model_config = ConfigDict(populate_by_name=True)
    
    key: str = Field(..., min_length=1, pattern=r"^[a-z0-9-]+$")
    value: str = Field(..., min_length=1)
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Tag:
        """Create Tag from single-key dict like {'cluster': 'production'}."""
        if len(data) != 1:
            raise ValueError("Tag must have exactly one key-value pair")
        key, value = next(iter(data.items()))
        return cls(key=key, value=value)
    
    def to_dict(self) -> dict[str, str]:
        return {self.key: self.value}


class Node(BaseModel):
    """Base class for all node types (AIO, DataNode, SearchHead)."""
    model_config = ConfigDict(populate_by_name=True)
    
    name: str = Field(..., min_length=1, pattern=r"^[a-z0-9-]+$")
    logpoint_id: str = Field(..., alias="logpointId", min_length=1)
    tags: list[Tag] = Field(default_factory=list)
    
    @field_validator("tags", mode="before")
    @classmethod
    def parse_tags(cls, v):
        """Parse tags from YAML format.
        
        Supports two formats:
        - Simple: [{"cluster": "production"}, {"env": "prod"}]
        - Explicit: [{"key": "cluster", "value": "production"}]
        """
        if isinstance(v, list):
            result = []
            for item in v:
                if isinstance(item, Tag):
                    result.append(item)
                elif isinstance(item, dict):
                    # Check if explicit format (has key and value fields)
                    if "key" in item and "value" in item:
                        result.append(Tag(key=item["key"], value=item["value"]))
                    else:
                        # Simple format: single-key dict
                        result.append(Tag.from_dict(item))
                else:
                    raise ValueError(f"Invalid tag format: {item}")
            return result
        return v
    
    def get_tag_value(self, key: str) -> str | None:
        """Get tag value by key."""
        for tag in self.tags:
            if tag.key == key:
                return tag.value
        return None
    
    def has_tag(self, key: str, value: str | None = None) -> bool:
        """Check if node has tag (optionally with specific value)."""
        for tag in self.tags:
            if tag.key == key:
                if value is None or tag.value == value:
                    return True
        return False


class AIO(Node):
    """All-In-One node (DataNode + SearchHead combined)."""
    pass


class DataNode(Node):
    """Data Node (collector + storage)."""
    pass


class SearchHead(Node):
    """Search Head (queries, dashboards, alerts)."""
    pass


class DirectorConfig(BaseModel):
    """Director API configuration."""
    model_config = ConfigDict(populate_by_name=True)
    
    pool_uuid: str = Field(..., alias="poolUuid")
    api_host: str = Field(..., alias="apiHost")
    credentials_ref: str = Field(..., alias="credentialsRef")


class FleetSpec(BaseModel):
    """Fleet specification."""
    model_config = ConfigDict(populate_by_name=True)
    
    management_mode: str = Field(default="director", alias="managementMode")
    director: DirectorConfig | None = None
    nodes: Nodes


class Nodes(BaseModel):
    """Collection of all node types."""
    model_config = ConfigDict(populate_by_name=True)
    
    aios: list[AIO] = Field(default_factory=list)
    data_nodes: list[DataNode] = Field(default_factory=list, alias="dataNodes")
    search_heads: list[SearchHead] = Field(default_factory=list, alias="searchHeads")


class FleetMetadata(BaseModel):
    """Fleet metadata."""
    model_config = ConfigDict(populate_by_name=True)
    
    name: str = Field(..., min_length=1)


class Fleet(BaseModel):
    """Fleet resource - top-level container for all nodes.
    
    Example YAML:
        apiVersion: cac-configmgr.io/v1
        kind: Fleet
        metadata:
          name: client-alpha
        spec:
          managementMode: director
          director:
            poolUuid: "aaa-1111-bbb-2222"
            apiHost: "https://director.logpoint.com"
            credentialsRef: "env://DIRECTOR_TOKEN"
          nodes:
            dataNodes:
              - name: dn-prod-01
                logpointId: "lp-dn-p1"
                tags:
                  - cluster: production
                  - env: prod
    """
    model_config = ConfigDict(populate_by_name=True)
    
    api_version: str = Field(default="cac-configmgr.io/v1", alias="apiVersion")
    kind: str = Field(default="Fleet")
    metadata: FleetMetadata
    spec: FleetSpec
    
    def get_nodes_by_tag(self, key: str, value: str | None = None) -> list[Node]:
        """Get all nodes matching a tag."""
        result = []
        for node_type in [self.spec.nodes.aios, 
                         self.spec.nodes.data_nodes, 
                         self.spec.nodes.search_heads]:
            for node in node_type:
                if node.has_tag(key, value):
                    result.append(node)
        return result
    
    def get_clusters(self) -> dict[str, list[Node]]:
        """Group nodes by cluster tag."""
        clusters: dict[str, list[Node]] = {}
        for node in (self.spec.nodes.aios + 
                    self.spec.nodes.data_nodes + 
                    self.spec.nodes.search_heads):
            cluster = node.get_tag_value("cluster")
            if cluster:
                if cluster not in clusters:
                    clusters[cluster] = []
                clusters[cluster].append(node)
        return clusters
