"""Normalization Policy models for log parsing.

Based on 20-TEMPLATE-HIERARCHY.md specification.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict


class NormalizationPolicy(BaseModel):
    """Normalization Policy - defines how logs are parsed.
    
    Example:
        normalizationPolicies:
          - name: np-windows
            _id: np-windows
            description: "Windows event log parsing"
            package: windows-normalization
    """
    model_config = ConfigDict(populate_by_name=True)
    
    name: str = Field(..., min_length=1, pattern=r"^[a-zA-Z0-9_-]+$")
    id: str = Field(..., alias="_id", description="Template ID for inheritance")
    
    # Policy details
    package: str = Field(..., description="Normalization package name")
    description: str | None = Field(default=None)
    
    # Template internal fields
    action: str | None = Field(default=None, alias="_action", description="Action: delete, etc.")
