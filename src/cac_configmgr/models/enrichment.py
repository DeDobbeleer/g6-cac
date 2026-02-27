"""Enrichment Policy models for adding context to logs.

Based on 20-TEMPLATE-HIERARCHY.md specification.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict


class EnrichmentPolicy(BaseModel):
    """Enrichment Policy - defines what context is added to logs.
    
    Example:
        enrichmentPolicies:
          - name: ep-geoip
            _id: ep-geoip
            description: "GeoIP enrichment"
            sources:
              - source: geoip-db
              - source: threat-intel
    """
    model_config = ConfigDict(populate_by_name=True)
    
    name: str = Field(..., min_length=1, pattern=r"^[a-zA-Z0-9_-]+$")
    id: str = Field(..., alias="_id", description="Template ID for inheritance")
    
    # Policy details
    sources: list[dict] = Field(default_factory=list, description="Enrichment sources")
    description: str | None = Field(default=None)
    
    # Template internal fields
    action: str | None = Field(default=None, alias="_action", description="Action: delete, etc.")
