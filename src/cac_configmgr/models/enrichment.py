"""Enrichment Policy models for adding context to logs.

Based on LogPoint Director API specification.
https://docs.logpoint.com/director/director-apis/director-console-api-documentation/enrichmentpolicy
"""

from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict


class EnrichmentCriterion(BaseModel):
    """Enrichment criterion for matching logs.
    
    Matches based on key presence and/or value.
    """
    model_config = ConfigDict(populate_by_name=True)
    
    type: str = Field(..., description="Match type: KeyPresents or KeyPresentsValueMatches")
    key: str = Field(..., description="Key to match in log")
    value: str = Field(default="", description="Value to match (if applicable)")


class EnrichmentRule(BaseModel):
    """Enrichment rule defining what to enrich.
    
    Defines the mapping between source and event fields.
    """
    model_config = ConfigDict(populate_by_name=True)
    
    category: str = Field(..., description="Category: simple or type_based")
    source_key: str = Field(..., alias="source_key", description="Source field key")
    operation: str = Field(default="Equals", description="Operation: Equals")
    event_key: str = Field(..., alias="event_key", description="Event field key")
    type: str | None = Field(default=None, description="Type: ip, string, or num (for type_based)")
    prefix: bool = Field(default=False, description="Prefix: true or false (for type_based)")


class EnrichmentSpecification(BaseModel):
    """Single enrichment specification.
    
    Defines source, criteria and rules for enrichment.
    """
    model_config = ConfigDict(populate_by_name=True)
    
    id: str = Field(..., alias="_id", description="Specification ID")
    source: str = Field(..., description="Enrichment source name")
    criteria: list[EnrichmentCriterion] = Field(default_factory=list, description="Matching criteria")
    rules: list[EnrichmentRule] = Field(default_factory=list, description="Enrichment rules")


class EnrichmentPolicy(BaseModel):
    """Enrichment Policy - groups enrichment specifications.
    
    API Format:
        {
            "name": "testPolicy",
            "specifications": [
                {
                    "source": "test_odbc",
                    "criteria": [{"type": "KeyPresents", "key": "id", "value": ""}],
                    "rules": [{"category": "simple", "source_key": "id", ...}]
                }
            ]
        }
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
