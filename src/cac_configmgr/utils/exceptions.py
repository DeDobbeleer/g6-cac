"""Custom exceptions for CaC-ConfigMgr."""


class ConfigError(Exception):
    """Base exception for configuration errors."""
    pass


class ValidationError(ConfigError):
    """Exception for validation errors."""
    pass


class ResolutionError(ConfigError):
    """Exception for template resolution errors."""
    pass
