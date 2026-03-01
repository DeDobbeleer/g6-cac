"""CaC-ConfigMgr providers for different LogPoint APIs.

Providers abstract the communication with LogPoint configuration APIs.
Each provider implements the base Provider interface for a specific backend.

Available providers:
- DirectorProvider: LogPoint Director API (MSSP, multi-tenant)
- MockProvider: For testing (future)
"""

from .base import (
    Provider,
    ProviderConfig,
    ProviderError,
    AuthenticationError,
    ResourceNotFoundError,
    ResourceAlreadyExistsError,
    AsyncOperationError,
)
from .director import (
    DirectorProvider,
    DirectorConfig,
    NameToIDResolver,
)

__all__ = [
    # Base classes
    "Provider",
    "ProviderConfig",
    "ProviderError",
    "AuthenticationError",
    "ResourceNotFoundError",
    "ResourceAlreadyExistsError",
    "AsyncOperationError",
    # Director implementation
    "DirectorProvider",
    "DirectorConfig",
    "NameToIDResolver",
]
