"""Enrichment Policy models for adding context to logs.

Based on 20-TEMPLATE-HIERARCHY.md specification (Appendix E).
"""

from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict


class EnrichmentSource(BaseModel):
    """Enrichment source reference.
    
    These are read-only resources created via Director UI.
    """
    model_config = ConfigDict(populate_by_name=True)
    
    source: str = Field(..., description="Source identifier")


class EnrichmentSpecification(BaseModel):
    """Single enrichment specification.
    
    Defines what fields to enrich and from which source.
    """
    model_config = ConfigDict(populate_by_name=True)
    
    id: str = Field(..., alias="_id", description="Specification ID")
    source: str = Field(..., description="Enrichment source name")
    fields: list[str] = Field(default_factory=list, description="Fields to enrich")


class EnrichmentPolicy(BaseModel):
    """Enrichment Policy - groups enrichment specifications.
    
    Example:
        enrichmentPolicies:
          - name: ep-geoip
            _id: ep-geoip
            specifications:
              - _id: spec-geoip
                source: "GeoIP"
                fields: ["src_ip", "dst_ip"]
    """
    model_config = ConfigDict(populate_by_name=True)
    
    name: str = Field(..., min_length=1, pattern=r"^[a-zA-Z0-9_-]+$")
    id: str = Field(..., alias="_id", description="Template ID for inheritance")
    
    # Policy composition
    specifications: list[EnrichmentSpecification] = Field(
        default_factory=list,
        description="List of enrichment specifications"
    )
    
    # Template internal fields
    action: str | None = Field(default=None, alias="_action", description="Action: delete, etc.")
