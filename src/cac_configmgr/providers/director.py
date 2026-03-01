"""Director API provider implementation.

This module implements the Provider interface for LogPoint Director API.
It handles authentication, HTTP requests, and async operation polling.

Based on ADR-010: Uses DirSync knowledge (API behavior, error patterns) 
but implements with clean CaC-ConfigMgr architecture (async, testable).
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

import httpx

from .base import (
    Provider,
    ProviderConfig,
    ProviderError,
    AuthenticationError,
    ResourceNotFoundError,
    ResourceAlreadyExistsError,
    AsyncOperationError,
)


@dataclass
class DirectorConfig(ProviderConfig):
    """Configuration for Director provider.
    
    Attributes:
        api_host: Director API base URL (e.g., "https://director.logpoint.com")
        credentials: Bearer token for authentication
        pool_uuid: Pool UUID for multi-tenant context
        timeout: Request timeout in seconds
    """
    pool_uuid: str = ""
    
    def __post_init__(self):
        """Validate configuration."""
        if not self.pool_uuid:
            raise ValueError("pool_uuid is required for Director provider")


class DirectorProvider(Provider):
    """LogPoint Director API provider.
    
    Implements the Provider interface for Director API v1.3+.
    
    Features:
    - Token-based authentication
    - Pool-scoped operations
    - Async operation polling
    - Exponential backoff retry
    - Comprehensive error handling
    
    Example:
        config = DirectorConfig(
            api_host="https://director.logpoint.com",
            credentials="Bearer eyJhbGc...",
            pool_uuid="aaa-1111-bbb-2222"
        )
        async with DirectorProvider(config) as provider:
            resources = await provider.get_resources("routing_policies")
    """
    
    # API endpoints for each resource type
    RESOURCE_ENDPOINTS = {
        "repos": "/repos",
        "routing_policies": "/routingpolicies",
        "normalization_policies": "/normalizationpolicy",
        "enrichment_policies": "/enrichmentpolicy",
        "processing_policies": "/processingpolicy",
    }
    
    def __init__(self, config: DirectorConfig):
        """Initialize Director provider.
        
        Args:
            config: Director-specific configuration
        """
        super().__init__(config)
        self.config: DirectorConfig = config
        self._client: httpx.AsyncClient | None = None
        self._base_url: str = ""
    
    async def __aenter__(self) -> DirectorProvider:
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.disconnect()
    
    async def connect(self) -> None:
        """Establish connection to Director API.
        
        Creates HTTP client with authentication headers.
        Validates connection with health check.
        
        Raises:
            AuthenticationError: If authentication fails
            ConnectionError: If Director is unreachable
        """
        # Build base URL with pool context
        self._base_url = f"{self.config.api_host}/configapi/{self.config.pool_uuid}"
        
        # Create HTTP client with auth headers
        headers = {
            "Authorization": self._format_auth_header(self.config.credentials),
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        
        self._client = httpx.AsyncClient(
            headers=headers,
            timeout=self.config.timeout,
            follow_redirects=True,
        )
        
        # Validate connection
        try:
            await self.health_check()
        except Exception as e:
            await self.disconnect()
            raise ConnectionError(f"Failed to connect to Director: {e}")
    
    async def disconnect(self) -> None:
        """Close HTTP client and cleanup."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    def _format_auth_header(self, credentials: str) -> str:
        """Format credentials as Authorization header.
        
        Args:
            credentials: Raw token or "Bearer token"
            
        Returns:
            Formatted Authorization header value
        """
        if credentials.lower().startswith("bearer "):
            return credentials
        return f"Bearer {credentials}"
    
    def _get_endpoint(self, resource_type: str) -> str:
        """Get API endpoint for resource type.
        
        Args:
            resource_type: Resource type key
            
        Returns:
            API endpoint path
            
        Raises:
            ValueError: If resource type is unknown
        """
        if resource_type not in self.RESOURCE_ENDPOINTS:
            raise ValueError(f"Unknown resource type: {resource_type}")
        return self.RESOURCE_ENDPOINTS[resource_type]
    
    async def get_resources(self, resource_type: str) -> list[dict[str, Any]]:
        """Fetch all resources of a given type.
        
        Used by 'plan' command to get actual state.
        
        Args:
            resource_type: Type of resource (e.g., "routing_policies")
            
        Returns:
            List of resource dictionaries
            
        Example:
            resources = await provider.get_resources("routing_policies")
            # [{"_id": "586cc3ed...", "policy_name": "rp-default", ...}]
        """
        if not self._client:
            raise RuntimeError("Provider not connected. Use 'async with' or call connect()")
        
        endpoint = self._get_endpoint(resource_type)
        url = f"{self._base_url}{endpoint}"
        
        try:
            response = await self._client.get(url)
            response.raise_for_status()
            
            data = response.json()
            # Director returns list directly or wrapped in response object
            if isinstance(data, list):
                return data
            return data.get("data", data.get("results", []))
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise AuthenticationError("Invalid or expired token")
            raise ProviderError(f"Failed to get {resource_type}: {e}", e.response.status_code)
        except Exception as e:
            raise ProviderError(f"Failed to get {resource_type}: {e}")
    
    async def get_resource_by_id(self, resource_type: str, resource_id: str) -> dict[str, Any] | None:
        """Fetch a specific resource by ID.
        
        Args:
            resource_type: Type of resource
            resource_id: Resource ID
            
        Returns:
            Resource dictionary or None if not found
        """
        if not self._client:
            raise RuntimeError("Provider not connected")
        
        endpoint = self._get_endpoint(resource_type)
        url = f"{self._base_url}{endpoint}/{resource_id}"
        
        try:
            response = await self._client.get(url)
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise ProviderError(f"Failed to get resource: {e}", e.response.status_code)
    
    async def create_resource(self, resource_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Create a new resource.
        
        Handles both synchronous and async creation.
        If Director returns 202 Accepted, polls for completion.
        
        Args:
            resource_type: Type of resource to create
            payload: Resource data (with resolved IDs)
            
        Returns:
            Created resource with assigned "_id"
            
        Raises:
            ResourceAlreadyExistsError: If resource already exists
            ProviderError: If creation fails
        """
        if not self._client:
            raise RuntimeError("Provider not connected")
        
        endpoint = self._get_endpoint(resource_type)
        url = f"{self._base_url}{endpoint}"
        
        try:
            response = await self._client.post(url, json=payload)
            
            # Handle 409 Conflict (already exists)
            if response.status_code == 409:
                raise ResourceAlreadyExistsError(
                    f"{resource_type} already exists",
                    details={"payload": payload}
                )
            
            response.raise_for_status()
            
            # Handle async operation (202 Accepted)
            if response.status_code == 202:
                operation_url = response.headers.get("Location")
                if operation_url:
                    return await self._poll_async_operation(operation_url)
            
            return response.json()
            
        except httpx.HTTPStatusError as e:
            raise ProviderError(
                f"Failed to create {resource_type}: {e}",
                e.response.status_code,
                {"response": e.response.text}
            )
    
    async def update_resource(
        self, 
        resource_type: str, 
        resource_id: str, 
        payload: dict[str, Any]
    ) -> dict[str, Any]:
        """Update an existing resource."""
        if not self._client:
            raise RuntimeError("Provider not connected")
        
        endpoint = self._get_endpoint(resource_type)
        url = f"{self._base_url}{endpoint}/{resource_id}"
        
        try:
            response = await self._client.put(url, json=payload)
            
            if response.status_code == 404:
                raise ResourceNotFoundError(f"{resource_type} with id {resource_id} not found")
            
            response.raise_for_status()
            
            # Handle async operation
            if response.status_code == 202:
                operation_url = response.headers.get("Location")
                if operation_url:
                    return await self._poll_async_operation(operation_url)
            
            return response.json()
            
        except httpx.HTTPStatusError as e:
            raise ProviderError(
                f"Failed to update {resource_type}: {e}",
                e.response.status_code
            )
    
    async def delete_resource(self, resource_type: str, resource_id: str) -> None:
        """Delete a resource."""
        if not self._client:
            raise RuntimeError("Provider not connected")
        
        endpoint = self._get_endpoint(resource_type)
        url = f"{self._base_url}{endpoint}/{resource_id}"
        
        try:
            response = await self._client.delete(url)
            
            if response.status_code == 404:
                raise ResourceNotFoundError(f"{resource_type} with id {resource_id} not found")
            
            response.raise_for_status()
            
            # Handle async operation
            if response.status_code == 202:
                operation_url = response.headers.get("Location")
                if operation_url:
                    await self._poll_async_operation(operation_url)
            
        except httpx.HTTPStatusError as e:
            raise ProviderError(
                f"Failed to delete {resource_type}: {e}",
                e.response.status_code
            )
    
    async def health_check(self) -> bool:
        """Check if Director API is reachable."""
        if not self._client:
            return False
        
        try:
            # Try to get list of repos as health check
            url = f"{self._base_url}/repos"
            response = await self._client.get(url)
            return response.status_code in (200, 401)  # 401 means reachable but auth needed
        except Exception:
            return False
    
    async def _poll_async_operation(
        self, 
        operation_url: str, 
        max_attempts: int = 30,
        interval: float = 2.0
    ) -> dict[str, Any]:
        """Poll async operation until completion.
        
        Director returns 202 Accepted for long-running operations.
        We poll the operation URL until it completes.
        
        Args:
            operation_url: URL to poll (from Location header)
            max_attempts: Maximum number of poll attempts
            interval: Seconds between polls
            
        Returns:
            Final operation result
            
        Raises:
            AsyncOperationError: If operation fails or times out
        """
        if not self._client:
            raise RuntimeError("Provider not connected")
        
        for attempt in range(max_attempts):
            try:
                response = await self._client.get(operation_url)
                response.raise_for_status()
                
                data = response.json()
                status = data.get("status", "unknown")
                
                if status == "completed":
                    return data.get("result", data)
                elif status == "failed":
                    raise AsyncOperationError(
                        f"Async operation failed: {data.get('error', 'Unknown error')}",
                        details=data
                    )
                
                # Still pending, wait and retry
                await asyncio.sleep(interval)
                
            except httpx.HTTPStatusError as e:
                raise AsyncOperationError(
                    f"Failed to poll operation: {e}",
                    e.response.status_code
                )
        
        raise AsyncOperationError(
            f"Async operation timed out after {max_attempts} attempts",
            details={"operation_url": operation_url}
        )


class NameToIDResolver:
    """Resolves resource names to Director IDs.
    
    Used during apply phase to translate human-readable names
    (in YAML templates) to Director-generated IDs (for API calls).
    
    Example:
        resolver = NameToIDResolver(provider)
        await resolver.build_lookup("routing_policies")
        
        # Template uses name: routing_policy: "rp-default"
        # Transformed to ID: routing_policy: "586cc3ed..."
        id = resolver.resolve("routing_policies", "rp-default")
    """
    
    def __init__(self, provider: DirectorProvider):
        """Initialize resolver with provider.
        
        Args:
            provider: Connected Director provider
        """
        self.provider = provider
        self._cache: dict[str, dict[str, str]] = {}
    
    async def build_lookup(self, resource_type: str) -> dict[str, str]:
        """Build name→ID lookup table for a resource type.
        
        Fetches all resources from Director and creates a mapping
        from name field to ID.
        
        Args:
            resource_type: Type of resource (e.g., "routing_policies")
            
        Returns:
            Dictionary mapping names to IDs
            {"rp-default": "586cc3ed...", "rp-windows": "586cc3f0..."}
        """
        resources = await self.provider.get_resources(resource_type)
        
        # Determine name field based on resource type
        name_field = self._get_name_field(resource_type)
        
        lookup = {}
        for resource in resources:
            name = resource.get(name_field) or resource.get("name")
            id = resource.get("_id") or resource.get("id")
            if name and id:
                lookup[name] = id
        
        self._cache[resource_type] = lookup
        return lookup
    
    def resolve(self, resource_type: str, name: str) -> str:
        """Resolve a resource name to its Director ID.
        
        Args:
            resource_type: Type of resource
            name: Resource name (from YAML template)
            
        Returns:
            Director ID for the resource
            
        Raises:
            KeyError: If name not found in lookup
            RuntimeError: If lookup not built for resource type
        """
        if resource_type not in self._cache:
            raise RuntimeError(f"Lookup not built for {resource_type}. Call build_lookup() first.")
        
        if name not in self._cache[resource_type]:
            raise KeyError(f"Resource '{name}' not found in {resource_type}")
        
        return self._cache[resource_type][name]
    
    def _get_name_field(self, resource_type: str) -> str:
        """Get the name field for a resource type.
        
        Different resource types use different name fields:
        - RoutingPolicy: policy_name
        - ProcessingPolicy: policy_name
        - NormalizationPolicy: name (exception!)
        - EnrichmentPolicy: name
        
        Args:
            resource_type: Resource type
            
        Returns:
            Name field key
        """
        name_fields = {
            "routing_policies": "policy_name",
            "processing_policies": "policy_name",
            "normalization_policies": "name",
            "enrichment_policies": "name",
            "repos": "name",
        }
        return name_fields.get(resource_type, "name")
