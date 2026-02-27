"""Normalization Policy models for log parsing.

Based on 20-TEMPLATE-HIERARCHY.md specification (Appendix E).
"""

from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict


class NormalizationPackage(BaseModel):
    """Normalization package reference.
    
    These are system-level resources (read-only in API).
    """
    model_config = ConfigDict(populate_by_name=True)
    
    id: str = Field(..., alias="_id", description="Package ID")
    name: str = Field(..., description="Package name")


class NormalizationPolicy(BaseModel):
    """Normalization Policy - groups normalization packages.
    
    Example:
        normalizationPolicies:
          - name: np-windows
            _id: np-windows
            normalization_packages:
              - _id: pkg-windows
                name: "Windows"
              - _id: pkg-winsec
                name: "WinSecurity"
            compiled_normalizer:
              - _id: cnf-windows
                name: "WindowsCompiled"
    """
    model_config = ConfigDict(populate_by_name=True)
    
    name: str = Field(..., min_length=1, pattern=r"^[a-zA-Z0-9_-]+$")
    id: str = Field(..., alias="_id", description="Template ID for inheritance")
    
    # Policy composition
    normalization_packages: list[NormalizationPackage] = Field(
        default_factory=list, 
        alias="normalizationPackages",
        description="List of normalization packages"
    )
    compiled_normalizer: list[NormalizationPackage] = Field(
        default_factory=list,
        alias="compiledNormalizer",
        description="Compiled normalizer packages"
    )
    
    # Template internal fields
    action: str | None = Field(default=None, alias="_action", description="Action: delete, etc.")
