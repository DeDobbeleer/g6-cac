"""Base provider interface for CaC-ConfigMgr.

This module defines the abstract Provider interface that all concrete
providers (Director, Direct, etc.) must implement.

The Provider pattern allows CaC-ConfigMgr to work with different backends:
- DirectorProvider: LogPoint Director API (MSSP, multi-tenant)
- DirectProvider: Local SIEM API (future)
- MockProvider: For testing
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class ProviderConfig:
    """Base configuration for providers.
    
    Attributes:
        api_host: Base URL for the API
        credentials: Authentication credentials (token, etc.)
        timeout: Request timeout in seconds
    """
    api_host: str
    credentials: str
    timeout: float = 30.0


class Provider(ABC):
    """Abstract base class for all CaC-ConfigMgr providers.
    
    The Provider interface abstracts the communication with LogPoint
    configuration APIs. Implementations handle:
    - Authentication
    - HTTP requests
    - Async operation polling
    - Error handling and retries
    
    Example:
        provider = DirectorProvider(config)
        resources = await provider.get_resources("routing_policies")
    """
    
    def __init__(self, config: ProviderConfig):
        """Initialize provider with configuration.
        
        Args:
            config: Provider-specific configuration
        """
        self.config = config
    
    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to the API.
        
        Validates authentication and connection parameters.
        Raises ConnectionError if connection fails.
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection and cleanup resources."""
        pass
    
    @abstractmethod
    async def get_resources(self, resource_type: str) -> list[dict[str, Any]]:
        """Fetch all resources of a given type.
        
        Used by 'plan' command to get actual state from Director.
        
        Args:
            resource_type: Type of resource (e.g., "routing_policies")
            
        Returns:
            List of resource dictionaries with at least "_id" and name fields
            
        Example:
            resources = await provider.get_resources("routing_policies")
            # Returns: [{"_id": "586cc3ed...", "policy_name": "rp-default", ...}, ...]
        """
        pass
    
    @abstractmethod
    async def get_resource_by_id(self, resource_type: str, resource_id: str) -> dict[str, Any] | None:
        """Fetch a specific resource by ID.
        
        Args:
            resource_type: Type of resource
            resource_id: Resource ID (from "_id" field)
            
        Returns:
            Resource dictionary or None if not found
        """
        pass
    
    @abstractmethod
    async def create_resource(self, resource_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Create a new resource.
        
        Args:
            resource_type: Type of resource to create
            payload: Resource data (with IDs resolved for references)
            
        Returns:
            Created resource with assigned "_id"
            
        Raises:
            ProviderError: If creation fails
            
        Note:
            Director API may return 202 Accepted with async operation.
            Implementation should handle polling and return final result.
        """
        pass
    
    @abstractmethod
    async def update_resource(
        self, 
        resource_type: str, 
        resource_id: str, 
        payload: dict[str, Any]
    ) -> dict[str, Any]:
        """Update an existing resource.
        
        Args:
            resource_type: Type of resource
            resource_id: Resource ID to update
            payload: Updated resource data
            
        Returns:
            Updated resource
            
        Raises:
            ProviderError: If update fails or resource not found
        """
        pass
    
    @abstractmethod
    async def delete_resource(self, resource_type: str, resource_id: str) -> None:
        """Delete a resource.
        
        Args:
            resource_type: Type of resource
            resource_id: Resource ID to delete
            
        Raises:
            ProviderError: If deletion fails
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if provider is healthy and reachable.
        
        Returns:
            True if provider is operational
        """
        pass


class ProviderError(Exception):
    """Base exception for provider errors."""
    
    def __init__(self, message: str, status_code: int | None = None, details: dict | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.details = details or {}


class AuthenticationError(ProviderError):
    """Raised when authentication fails."""
    pass


class ResourceNotFoundError(ProviderError):
    """Raised when a resource is not found."""
    pass


class ResourceAlreadyExistsError(ProviderError):
    """Raised when trying to create a resource that already exists."""
    pass


class AsyncOperationError(ProviderError):
    """Raised when an async operation fails."""
    pass
