"""CaC-ConfigMgr: Configuration as Code Manager for LogPoint."""

__version__ = "0.1.0"
__author__ = "CaC-ConfigMgr Team"

# Providers for Director API integration
from .providers import (
    Provider,
    DirectorProvider,
    DirectorConfig,
    NameToIDResolver,
)
