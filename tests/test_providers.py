"""Tests for CaC-ConfigMgr providers."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock

from cac_configmgr.providers import (
    ProviderConfig,
    DirectorConfig,
    DirectorProvider,
    NameToIDResolver,
    AuthenticationError,
    ResourceNotFoundError,
    ResourceAlreadyExistsError,
)


class TestDirectorConfig:
    """Test Director configuration."""
    
    def test_valid_config(self):
        """Test creating valid Director config."""
        config = DirectorConfig(
            api_host="https://director.logpoint.com",
            credentials="test-token",
            pool_uuid="test-pool-uuid"
        )
        assert config.api_host == "https://director.logpoint.com"
        assert config.credentials == "test-token"
        assert config.pool_uuid == "test-pool-uuid"
    
    def test_missing_pool_uuid(self):
        """Test that missing pool_uuid raises error."""
        with pytest.raises(ValueError, match="pool_uuid is required"):
            DirectorConfig(
                api_host="https://director.logpoint.com",
                credentials="test-token"
            )
    
    def test_bearer_token_formatting(self):
        """Test that 'Bearer' prefix is handled correctly."""
        config = DirectorConfig(
            api_host="https://director.logpoint.com",
            credentials="Bearer test-token",
            pool_uuid="pool-123"
        )
        assert config.credentials == "Bearer test-token"


class TestNameToIDResolver:
    """Test Name-to-ID resolver."""
    
    @pytest.fixture
    def mock_provider(self):
        """Create mock provider for testing."""
        provider = MagicMock(spec=DirectorProvider)
        return provider
    
    @pytest.mark.asyncio
    async def test_build_lookup_routing_policies(self, mock_provider):
        """Test building lookup for routing policies."""
        # Setup mock response
        mock_provider.get_resources = AsyncMock(return_value=[
            {"_id": "586cc3ed...", "policy_name": "rp-default"},
            {"_id": "586cc3f0...", "policy_name": "rp-windows"},
        ])
        
        resolver = NameToIDResolver(mock_provider)
        lookup = await resolver.build_lookup("routing_policies")
        
        assert lookup == {
            "rp-default": "586cc3ed...",
            "rp-windows": "586cc3f0...",
        }
        mock_provider.get_resources.assert_called_once_with("routing_policies")
    
    @pytest.mark.asyncio
    async def test_build_lookup_normalization_policies(self, mock_provider):
        """Test building lookup for normalization policies (uses 'name' field)."""
        mock_provider.get_resources = AsyncMock(return_value=[
            {"_id": "np-123", "name": "_logpoint"},
            {"_id": "np-456", "name": "custom-np"},
        ])
        
        resolver = NameToIDResolver(mock_provider)
        lookup = await resolver.build_lookup("normalization_policies")
        
        assert lookup == {
            "_logpoint": "np-123",
            "custom-np": "np-456",
        }
    
    @pytest.mark.asyncio
    async def test_resolve_existing(self, mock_provider):
        """Test resolving a name that exists."""
        mock_provider.get_resources = AsyncMock(return_value=[
            {"_id": "586cc3ed...", "policy_name": "rp-default"},
        ])
        
        resolver = NameToIDResolver(mock_provider)
        await resolver.build_lookup("routing_policies")
        
        id = resolver.resolve("routing_policies", "rp-default")
        assert id == "586cc3ed..."
    
    @pytest.mark.asyncio
    async def test_resolve_not_found(self, mock_provider):
        """Test resolving a name that doesn't exist."""
        mock_provider.get_resources = AsyncMock(return_value=[])
        
        resolver = NameToIDResolver(mock_provider)
        await resolver.build_lookup("routing_policies")
        
        with pytest.raises(KeyError, match="not found"):
            resolver.resolve("routing_policies", "unknown-rp")
    
    def test_resolve_without_build(self):
        """Test resolving without building lookup first."""
        mock_provider = MagicMock(spec=DirectorProvider)
        resolver = NameToIDResolver(mock_provider)
        
        with pytest.raises(RuntimeError, match="Lookup not built"):
            resolver.resolve("routing_policies", "rp-default")


class TestDirectorProviderInterface:
    """Test Director provider interface (with mocked HTTP)."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return DirectorConfig(
            api_host="https://director.test.com",
            credentials="test-token",
            pool_uuid="test-pool"
        )
    
    @pytest.mark.asyncio
    async def test_context_manager(self, config):
        """Test async context manager."""
        provider = DirectorProvider(config)
        
        # Mock the connect/disconnect methods
        provider.connect = AsyncMock()
        provider.disconnect = AsyncMock()
        
        async with provider as p:
            assert p is provider
            provider.connect.assert_called_once()
        
        provider.disconnect.assert_called_once()


class TestProviderExceptions:
    """Test provider exception classes."""
    
    def test_provider_error(self):
        """Test base ProviderError."""
        err = AuthenticationError("Invalid token", status_code=401)
        assert str(err) == "Invalid token"
        assert err.status_code == 401
    
    def test_resource_not_found(self):
        """Test ResourceNotFoundError."""
        err = ResourceNotFoundError("Resource not found", details={"id": "123"})
        assert "not found" in str(err)
        assert err.details == {"id": "123"}
    
    def test_resource_already_exists(self):
        """Test ResourceAlreadyExistsError."""
        err = ResourceAlreadyExistsError("Already exists")
        assert "exists" in str(err)
