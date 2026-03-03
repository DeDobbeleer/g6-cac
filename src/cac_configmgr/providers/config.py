"""Provider configuration management.

Handles different configuration schemes for:
- Director mode: Token + Pool UUID (MSSP)
- Direct mode: Per-node credentials (SIEM local)

Supports multiple credential sources (env vars, config files, vault).
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import yaml


@dataclass
class NodeEndpoint:
    """Endpoint configuration for a single node.
    
    Used in Direct mode to manage SIEMs individually.
    
    Attributes:
        node_id: Unique identifier (hostname, IP, or custom ID)
        host: IP address or hostname of the SIEM
        port: API port (default 443)
        credentials: Bearer token for SIEM API authentication
        metadata: Optional tags/labels (datacenter, role, etc.)
    """
    node_id: str
    host: str
    port: int = 443
    credentials: str = ""
    metadata: dict = field(default_factory=dict)
    
    @property
    def base_url(self) -> str:
        """Construct base URL for this node."""
        return f"https://{self.host}:{self.port}"


@dataclass  
class DirectorPoolConfig:
    """Configuration for Director mode (MSSP multi-tenant).
    
    Attributes:
        director_host: Director API hostname
        pool_uuid: Pool UUID for multi-tenant context
        token: Bearer token for authentication
        timeout: Request timeout
    """
    director_host: str
    pool_uuid: str
    token: str
    timeout: float = 30.0
    
    @property
    def base_url(self) -> str:
        """Construct Director base URL."""
        return f"https://{self.director_host}"
    
    def validate(self) -> None:
        """Validate configuration."""
        if not self.pool_uuid:
            raise ValueError("pool_uuid is required for Director mode")
        if not self.token:
            raise ValueError("token is required for Director mode")


@dataclass
class DirectModeConfig:
    """Configuration for Direct mode (per-node management).
    
    Attributes:
        nodes: List of node endpoints to manage
        global_credentials: Default credentials for all nodes (optional)
        timeout: Request timeout
    """
    nodes: list[NodeEndpoint] = field(default_factory=list)
    global_credentials: str = ""
    timeout: float = 30.0
    
    def get_node(self, node_id: str) -> NodeEndpoint | None:
        """Get node configuration by ID."""
        for node in self.nodes:
            if node.node_id == node_id:
                return node
        return None
    
    def validate(self) -> None:
        """Validate configuration."""
        if not self.nodes:
            raise ValueError("At least one node is required for Direct mode")


@dataclass
class ProviderConfiguration:
    """Unified provider configuration.
    
    Supports both Director and Direct modes with credential resolution
    from multiple sources (environment, files, explicit values).
    
    Examples:
        # Director mode from environment
        config = ProviderConfiguration.from_env(mode="director")
        
        # Direct mode from YAML file
        config = ProviderConfiguration.from_file("~/.config/cac/nodes.yaml")
        
        # Explicit construction
        config = ProviderConfiguration(
            mode="director",
            director_config=DirectorPoolConfig(...)
        )
    """
    mode: Literal["director", "direct"]
    director_config: DirectorPoolConfig | None = None
    direct_config: DirectModeConfig | None = None
    
    @classmethod
    def from_env(cls, mode: Literal["director", "direct"] | None = None) -> ProviderConfiguration:
        """Load configuration from environment variables.
        
        Environment variables:
        - LOGPOINT_MODE: "director" or "direct"
        - LOGPOINT_DIRECTOR_HOST: Director hostname
        - LOGPOINT_POOL_UUID: Pool UUID (Director mode)
        - LOGPOINT_API_TOKEN: Bearer token
        - LOGPOINT_NODES_FILE: Path to nodes config (Direct mode)
        
        Args:
            mode: Force a specific mode (optional)
            
        Returns:
            ProviderConfiguration
        """
        detected_mode = mode or os.getenv("LOGPOINT_MODE", "director")
        
        if detected_mode == "director":
            return cls(
                mode="director",
                director_config=DirectorPoolConfig(
                    director_host=os.getenv("LOGPOINT_DIRECTOR_HOST", ""),
                    pool_uuid=os.getenv("LOGPOINT_POOL_UUID", ""),
                    token=os.getenv("LOGPOINT_API_TOKEN", ""),
                    timeout=float(os.getenv("LOGPOINT_TIMEOUT", "30.0")),
                )
            )
        else:
            # Direct mode - load from file or env
            nodes_file = os.getenv("LOGPOINT_NODES_FILE")
            if nodes_file and Path(nodes_file).exists():
                return cls.from_file(nodes_file)
            
            # Single node from env
            return cls(
                mode="direct",
                direct_config=DirectModeConfig(
                    nodes=[NodeEndpoint(
                        node_id=os.getenv("LOGPOINT_NODE_ID", "default"),
                        host=os.getenv("LOGPOINT_NODE_HOST", ""),
                        port=int(os.getenv("LOGPOINT_NODE_PORT", "443")),
                        credentials=os.getenv("LOGPOINT_API_TOKEN", ""),
                    )],
                    timeout=float(os.getenv("LOGPOINT_TIMEOUT", "30.0")),
                )
            )
    
    @classmethod
    def from_file(cls, path: str | Path) -> ProviderConfiguration:
        """Load configuration from YAML file.
        
        File format for Director mode:
        ```yaml
        mode: director
        director:
          host: director.logpoint.com
          pool_uuid: aaa-bbb-ccc
          token: ${LOGPOINT_API_TOKEN}  # Env var reference
          timeout: 30
        ```
        
        File format for Direct mode:
        ```yaml
        mode: direct
        direct:
          timeout: 30
          credentials: ${GLOBAL_SIEM_TOKEN}  # Optional global token
          nodes:
            - node_id: siem-prod-01
              host: 192.168.1.10
              port: 443
              # Uses global credentials
              metadata:
                datacenter: dc1
                role: primary
            - node_id: siem-prod-02
              host: 192.168.1.11
              credentials: ${SIEM_02_TOKEN}  # Per-node token
              metadata:
                datacenter: dc1
                role: secondary
        ```
        
        Args:
            path: Path to YAML configuration file
            
        Returns:
            ProviderConfiguration
        """
        path = Path(path).expanduser()
        
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")
        
        with open(path) as f:
            data = yaml.safe_load(f)
        
        # Resolve environment variable references
        data = cls._resolve_env_vars(data)
        
        mode = data.get("mode", "director")
        
        if mode == "director":
            director_data = data.get("director", {})
            return cls(
                mode="director",
                director_config=DirectorPoolConfig(
                    director_host=director_data.get("host", ""),
                    pool_uuid=director_data.get("pool_uuid", ""),
                    token=director_data.get("token", ""),
                    timeout=director_data.get("timeout", 30.0),
                )
            )
        else:
            direct_data = data.get("direct", {})
            nodes_data = direct_data.get("nodes", [])
            
            nodes = [
                NodeEndpoint(
                    node_id=n.get("node_id", f"node-{i}"),
                    host=n.get("host", ""),
                    port=n.get("port", 443),
                    credentials=n.get("credentials", direct_data.get("credentials", "")),
                    metadata=n.get("metadata", {}),
                )
                for i, n in enumerate(nodes_data)
            ]
            
            return cls(
                mode="direct",
                direct_config=DirectModeConfig(
                    nodes=nodes,
                    global_credentials=direct_data.get("credentials", ""),
                    timeout=direct_data.get("timeout", 30.0),
                )
            )
    
    @classmethod
    def _resolve_env_vars(cls, obj):
        """Recursively resolve ${VAR} references in dict/list/str."""
        if isinstance(obj, dict):
            return {k: cls._resolve_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [cls._resolve_env_vars(item) for item in obj]
        elif isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
            var_name = obj[2:-1]
            return os.getenv(var_name, obj)
        return obj
    
    def validate(self) -> None:
        """Validate configuration based on mode."""
        if self.mode == "director":
            if not self.director_config:
                raise ValueError("director_config is required for Director mode")
            self.director_config.validate()
        else:
            if not self.direct_config:
                raise ValueError("direct_config is required for Direct mode")
            self.direct_config.validate()
    
    def get_default_config_dir(self) -> Path:
        """Get default configuration directory.
        
        Returns:
            Path to config directory (~/.config/cac-configmgr/)
        """
        return Path.home() / ".config" / "cac-configmgr"


# Global configuration loader with caching
_config_cache: dict[str, ProviderConfiguration] = {}


def load_provider_config(
    source: str | None = None,
    mode: Literal["director", "direct"] | None = None
) -> ProviderConfiguration:
    """Load provider configuration with caching.
    
    Args:
        source: Config file path, or None for env-based
        mode: Force specific mode
        
    Returns:
        ProviderConfiguration
        
    Examples:
        # From environment
        config = load_provider_config()
        
        # From specific file
        config = load_provider_config("~/.config/cac/production.yaml")
        
        # Force director mode from env
        config = load_provider_config(mode="director")
    """
    cache_key = f"{source}:{mode}"
    
    if cache_key not in _config_cache:
        if source:
            _config_cache[cache_key] = ProviderConfiguration.from_file(source)
        else:
            _config_cache[cache_key] = ProviderConfiguration.from_env(mode)
    
    return _config_cache[cache_key]


def clear_config_cache() -> None:
    """Clear configuration cache (useful for testing)."""
    _config_cache.clear()
