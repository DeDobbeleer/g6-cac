"""Factory for creating providers based on configuration.

Centralizes provider creation logic for CLI commands.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from cac_configmgr.providers.base import Provider
from cac_configmgr.providers.config import (
    load_provider_config,
    ProviderConfiguration,
    DirectorPoolConfig,
    DirectModeConfig,
)


class ProviderFactory:
    """Factory for creating configured provider instances.
    
    Examples:
        # From config file
        factory = ProviderFactory.from_file("~/.config/cac/production.yaml")
        async with factory.create() as provider:
            resources = await provider.get_resources("repos")
        
        # From environment
        factory = ProviderFactory.from_env()
        
        # Explicit config
        factory = ProviderFactory(config)
        provider = factory.create_director()
    """
    
    def __init__(self, config: ProviderConfiguration):
        """Initialize with configuration.
        
        Args:
            config: Provider configuration
        """
        self.config = config
        self.config.validate()
    
    @classmethod
    def from_file(cls, path: str | Path) -> ProviderFactory:
        """Create factory from configuration file.
        
        Args:
            path: Path to YAML config file
            
        Returns:
            Configured ProviderFactory
        """
        config = load_provider_config(source=str(path))
        return cls(config)
    
    @classmethod
    def from_env(
        cls,
        mode: Literal["director", "direct"] | None = None
    ) -> ProviderFactory:
        """Create factory from environment variables.
        
        Args:
            mode: Force specific mode (optional)
            
        Returns:
            Configured ProviderFactory
        """
        config = load_provider_config(mode=mode)
        return cls(config)
    
    def create(self) -> Provider:
        """Create appropriate provider based on configuration mode.
        
        Returns:
            Provider instance (DirectorProvider or DirectProvider)
            
        Raises:
            ValueError: If configuration is invalid
        """
        if self.config.mode == "director":
            return self.create_director()
        else:
            return self.create_direct()
    
    def create_director(self) -> Provider:
        """Create Director provider.
        
        Returns:
            DirectorProvider instance
            
        Raises:
            ValueError: If not in Director mode
        """
        if self.config.mode != "director":
            raise ValueError(f"Cannot create Director provider in {self.config.mode} mode")
        
        from cac_configmgr.providers.director import (
            DirectorProvider,
            DirectorConfig,
        )
        
        director_cfg = self.config.director_config
        assert director_cfg is not None
        
        return DirectorProvider(DirectorConfig(
            api_host=director_cfg.base_url,
            credentials=director_cfg.token,
            pool_uuid=director_cfg.pool_uuid,
            timeout=director_cfg.timeout,
        ))
    
    def create_direct(self) -> Provider:
        """Create Direct provider for single node.
        
        Returns:
            DirectProvider instance
            
        Raises:
            ValueError: If not in Direct mode or multiple nodes
        """
        if self.config.mode != "direct":
            raise ValueError(f"Cannot create Direct provider in {self.config.mode} mode")
        
        from cac_configmgr.providers.direct import (
            DirectProvider,
            DirectProviderConfig,
        )
        
        direct_cfg = self.config.direct_config
        assert direct_cfg is not None
        
        if len(direct_cfg.nodes) != 1:
            raise ValueError(
                f"Use create_multi_node() for {len(direct_cfg.nodes)} nodes, "
                "or select a single node"
            )
        
        node = direct_cfg.nodes[0]
        return DirectProvider(DirectProviderConfig(
            api_host=node.base_url,
            node_id=node.node_id,
            credentials=node.credentials or direct_cfg.global_credentials,
            timeout=direct_cfg.timeout,
        ))
    
    def create_multi_node(self):
        """Create multi-node provider for Direct mode.
        
        Returns:
            MultiNodeProvider instance
            
        Raises:
            ValueError: If not in Direct mode
        """
        if self.config.mode != "direct":
            raise ValueError(f"Cannot create MultiNode provider in {self.config.mode} mode")
        
        from cac_configmgr.providers.direct import MultiNodeProvider
        
        direct_cfg = self.config.direct_config
        assert direct_cfg is not None
        
        return MultiNodeProvider(direct_cfg)
    
    def get_mode(self) -> str:
        """Get configured mode."""
        return self.config.mode
    
    def get_node_ids(self) -> list[str]:
        """Get list of configured node IDs.
        
        Returns:
            List of node identifiers
        """
        if self.config.mode == "director":
            return ["director"]  # Single logical endpoint
        else:
            direct_cfg = self.config.direct_config
            if direct_cfg:
                return [n.node_id for n in direct_cfg.nodes]
            return []


def create_provider(
    config_path: str | Path | None = None,
    mode: Literal["director", "direct"] | None = None
) -> Provider:
    """Convenience function to create a provider.
    
    Args:
        config_path: Path to config file, or None for env-based
        mode: Force specific mode
        
    Returns:
        Configured Provider instance
        
    Examples:
        # From file
        provider = create_provider("~/.config/cac/prod.yaml")
        
        # From env
        provider = create_provider()
        
        # Force mode
        provider = create_provider(mode="director")
    """
    if config_path:
        factory = ProviderFactory.from_file(config_path)
    else:
        factory = ProviderFactory.from_env(mode)
    
    return factory.create()
