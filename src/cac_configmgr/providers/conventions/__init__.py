"""API Conventions for different LogPoint providers.

This package contains convention implementations for various LogPoint APIs:
- DirectorAPIConvention: LogPoint Director API (MSSP, multi-tenant)
- Future: DirectAPIConvention for direct SIEM API
- Future: SOARAPIConvention for LogPoint SOAR
"""

from .director import DirectorAPIConvention

__all__ = ["DirectorAPIConvention"]
