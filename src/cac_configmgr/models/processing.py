"""Processing Policy models.

Based on 30-PROCESSING-POLICIES.md specification.

Processing Policy is a "glue" resource that links:
- Routing Policy (where to store)
- Normalization Policy (how to parse)
- Enrichment Policy (what context to add)
"""

from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict


class ProcessingPolicy(BaseModel):
    """Processing Policy - links RP, NP, and EP together.
    
    This is a simple reference resource that groups 3 other policies
    into a single convenient reference for devices.
    
    Example:
        processingPolicies:
          - name: windows-security-pipeline
            _id: pp-windows-sec
            routingPolicy: rp-windows-security
            normalizationPolicy: np-windows
            enrichmentPolicy: ep-geoip-threatintel
            description: "Complete pipeline for Windows security logs"
            enabled: true
    """
    model_config = ConfigDict(populate_by_name=True)
    
    name: str = Field(..., min_length=1, pattern=r"^[a-zA-Z0-9_-]+$")
    id: str = Field(..., alias="_id", description="Template ID for inheritance matching")
    
    # Policy references (links to other resources)
    routing_policy: str = Field(..., alias="routingPolicy", description="Reference to RoutingPolicy")
    normalization_policy: str | None = Field(default=None, alias="normalizationPolicy", description="Reference to NormalizationPolicy (optional)")
    enrichment_policy: str | None = Field(default=None, alias="enrichmentPolicy", description="Reference to EnrichmentPolicy (optional)")
    
    # Metadata
    description: str | None = Field(default=None)
    enabled: bool = Field(default=True)
    
    # Template internal fields
    action: str | None = Field(default=None, alias="_action", description="Action: delete, etc.")
    
    def get_referenced_policies(self) -> dict[str, str | None]:
        """Get all referenced policy names.
        
        Returns:
            Dict with keys: routing, normalization, enrichment
        """
        return {
            "routing": self.routing_policy,
            "normalization": self.normalization_policy,
            "enrichment": self.enrichment_policy,
        }
    
    def is_complete(self) -> bool:
        """Check if all optional policies are specified."""
        return all([
            self.routing_policy,
            self.normalization_policy,
            self.enrichment_policy,
        ])
