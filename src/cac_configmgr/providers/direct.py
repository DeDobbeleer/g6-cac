"""Direct SIEM API provider implementation.

Manages LogPoint SIEMs directly without Director.
Used for all-in-one deployments or when Director is not available.

Features:
- Per-node configuration
- Token-based authentication (same as Director)
- Parallel operations across nodes
"""

from __future__ import annotations

from typing import Any

from cac_configmgr.core.conventions import APIConvention

from .base import (
    Provider,
    ProviderConfig,
    ProviderError,
    AuthenticationError,
    ResourceNotFoundError,
)


class DirectProviderConfig(ProviderConfig):
    """Configuration for Direct provider.
    
    Attributes:
        node_host: SIEM node IP or hostname
        node_id: Unique identifier for this node
        credentials: Authentication (cert path, token, or basic auth)
        verify_ssl: Whether to verify SSL certificates
    """
    node_host: str
    node_id: str
    credentials: str
    verify_ssl: bool = True


class DirectProvider(Provider):
    """Direct SIEM API provider.
    
    Manages a single SIEM node directly via its API.
    For managing multiple nodes, create multiple provider instances.
    
    Example:
        config = DirectProviderConfig(
            api_host="https://192.168.1.10",
            node_id="siem-prod-01",
            credentials="/path/to/cert.pem",
        )
        async with DirectProvider(config) as provider:
            resources = await provider.get_resources("routing_policies")
    """
    
    # API endpoints (may differ from Director)
    RESOURCE_ENDPOINTS = {
        "repos": "/api/repos",
        "routing_policies": "/api/routingpolicies",
        "normalization_policies": "/api/normalizationpolicy",
        "enrichment_policies": "/api/enrichmentpolicy",
        "processing_policies": "/api/processingpolicy",
        "device_groups": "/api/devicegroups",
        "devices": "/api/devices",
    }
    
    def __init__(self, config: DirectProviderConfig):
        """Initialize Direct provider."""
        super().__init__(config)
        self.config: DirectProviderConfig = config
        self._client = None
    
    async def __aenter__(self) -> DirectProvider:
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.disconnect()
    
    async def connect(self) -> None:
        """Establish connection to SIEM API."""
        import httpx
        
        # Setup authentication (certificates, token, etc.)
        auth = self._setup_auth()
        
        self._client = httpx.AsyncClient(
            base_url=self.config.api_host,
            auth=auth,
            timeout=self.config.timeout,
            verify=self.config.verify_ssl,
        )
        
        # Validate connection
        if not await self.health_check():
            raise ConnectionError(f"Cannot connect to SIEM at {self.config.api_host}")
    
    def _setup_auth(self):
        """Setup Bearer token authentication.
        
        Direct SIEM mode uses the same token-based auth as Director.
        Token is passed in Authorization header.
        """
        creds = self.config.credentials
        
        if not creds:
            raise ValueError(f"Token required for node {self.config.node_id}")
        
        # Bearer token (same format as Director)
        return {"Authorization": f"Bearer {creds}"}
    
    async def disconnect(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def get_resources(self, resource_type: str) -> list[dict[str, Any]]:
        """Fetch resources from SIEM."""
        if not self._client:
            raise RuntimeError("Provider not connected")
        
        endpoint = self.RESOURCE_ENDPOINTS.get(resource_type)
        if not endpoint:
            raise ValueError(f"Unknown resource type: {resource_type}")
        
        response = await self._client.get(endpoint)
        response.raise_for_status()
        return response.json()
    
    async def get_resource_by_id(self, resource_type: str, resource_id: str) -> dict[str, Any] | None:
        """Fetch single resource."""
        endpoint = f"{self.RESOURCE_ENDPOINTS[resource_type]}/{resource_id}"
        response = await self._client.get(endpoint)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()
    
    async def create_resource(self, resource_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Create resource on SIEM."""
        endpoint = self.RESOURCE_ENDPOINTS[resource_type]
        response = await self._client.post(endpoint, json=payload)
        response.raise_for_status()
        return response.json()
    
    async def update_resource(
        self, resource_type: str, resource_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        """Update resource."""
        endpoint = f"{self.RESOURCE_ENDPOINTS[resource_type]}/{resource_id}"
        response = await self._client.put(endpoint, json=payload)
        response.raise_for_status()
        return response.json()
    
    async def delete_resource(self, resource_type: str, resource_id: str) -> None:
        """Delete resource."""
        endpoint = f"{self.RESOURCE_ENDPOINTS[resource_type]}/{resource_id}"
        response = await self._client.delete(endpoint)
        response.raise_for_status()
    
    async def health_check(self) -> bool:
        """Check if SIEM is reachable."""
        if not self._client:
            return False
        try:
            response = await self._client.get("/api/health")
            return response.status_code == 200
        except Exception:
            return False
    
    def get_convention(self) -> APIConvention:
        """Get Direct API convention.
        
        Note: Direct API may have different field names than Director.
        """
        # For now, reuse Director convention with potential overrides
        from cac_configmgr.providers.conventions import DirectorAPIConvention
        return DirectorAPIConvention()


class MultiNodeProvider:
    """Provider that manages multiple SIEM nodes in parallel.
    
    Used in Direct mode when you have multiple SIEMs to manage.
    Wraps multiple DirectProvider instances.
    
    Example:
        config = load_provider_config("nodes.yaml")  # Direct mode
        async with MultiNodeProvider(config.direct_config) as multi:
            # Get resources from all nodes
            all_resources = await multi.get_resources_from_all("routing_policies")
    """
    
    def __init__(self, config: DirectModeConfig):
        """Initialize with Direct mode configuration.
        
        Args:
            config: DirectModeConfig with nodes list
        """
        self.config = config
        self.providers: list[DirectProvider] = []
    
    async def __aenter__(self) -> MultiNodeProvider:
        """Connect to all nodes."""
        for node in self.config.nodes:
            provider = DirectProvider(DirectProviderConfig(
                api_host=node.base_url,
                node_id=node.node_id,
                credentials=node.credentials or self.config.global_credentials,
                timeout=self.config.timeout,
            ))
            await provider.__aenter__()
            self.providers.append(provider)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Disconnect from all nodes."""
        for provider in self.providers:
            await provider.__aexit__(exc_type, exc_val, exc_tb)
        self.providers = []
    
    async def get_resources_from_all(
        self, resource_type: str
    ) -> dict[str, list[dict]]:
        """Get resources from all nodes.
        
        Returns:
            Dict mapping node_id to resources list
        """
        results = {}
        for provider in self.providers:
            resources = await provider.get_resources(resource_type)
            results[provider.config.node_id] = resources
        return results
    
    async def apply_to_all(self, plan: Any) -> dict[str, Any]:
        """Apply a plan to all nodes.
        
        Args:
            plan: Plan to apply
            
        Returns:
            Results per node
        """
        results = {}
        for provider in self.providers:
            # Apply plan to this node
            result = await self._apply_to_node(provider, plan)
            results[provider.config.node_id] = result
        return results
    
    async def _apply_to_node(self, provider: DirectProvider, plan: Any) -> Any:
        """Apply plan to single node."""
        # Implementation here
        pass
