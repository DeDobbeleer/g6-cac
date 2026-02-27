"""Routing Policy models for log routing configuration.

Based on 20-TEMPLATE-HIERARCHY.md specification (Appendix D).
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class RoutingCriterion(BaseModel):
    """Single routing criterion for matching log events.
    
    Each criterion matches based on field presence and/or value.
    The _id is used for inheritance and ordering.
    
    Example:
        routing_criteria:
          - _id: crit-verbose
            repo: repo-system-verbose
            type: KeyPresentValueMatches
            key: EventType
            value: Verbose
            drop: store
    """
    _id: str = Field(..., description="Template ID for matching and ordering")
    
    # Matching fields
    type: str = Field(..., description="Match type: KeyPresent, KeyPresentValueMatches, etc.")
    key: str = Field(..., description="Field/key to match on")
    value: str | None = Field(default=None, description="Value to match (if applicable)")
    
    # Action fields
    repo: str | None = Field(default=None, description="Destination repo (if not dropping)")
    drop: str = Field(default="store", description="Action: store, discard_raw, discard_entirely")
    
    # Ordering fields
    _after: str | None = Field(default=None, description="Insert after this criterion")
    _before: str | None = Field(default=None, description="Insert before this criterion")
    _position: int | None = Field(default=None, description="Absolute position")
    _first: bool = Field(default=False, description="Force first position")
    _last: bool = Field(default=False, description="Force last position")
    
    # Action for inheritance
    _action: str | None = Field(default=None, description="Action: delete, merge, etc.")


class RoutingPolicy(BaseModel):
    """Routing Policy for a specific log source type.
    
    Each source type (Windows, Linux, Checkpoint, etc.) has its own
    routing policy with vendor-specific fields.
    
    Example:
        routingPolicies:
          - policy_name: rp-windows
            _id: rp-windows
            catch_all: repo-system
            routing_criteria:
              - _id: crit-verbose
                repo: repo-system-verbose
                type: KeyPresentValueMatches
                key: EventType
                value: Verbose
              - _id: crit-debug
                repo: repo-system-verbose
                type: KeyPresent
                key: DebugMode
    """
    policy_name: str = Field(..., min_length=1, pattern=r"^[a-zA-Z0-9_-]+$")
    _id: str = Field(..., description="Template ID for policy matching")
    catch_all: str = Field(..., description="Default repo if no criteria match")
    routing_criteria: list[RoutingCriterion] = Field(default_factory=list)
    
    # Template internal fields
    _action: str | None = Field(default=None, description="Action: delete, etc.")
    
    def get_criterion(self, criterion_id: str) -> RoutingCriterion | None:
        """Get a specific criterion by _id."""
        for crit in self.routing_criteria:
            if crit._id == criterion_id:
                return crit
        return None
    
    def is_redundant(self, criterion: RoutingCriterion) -> bool:
        """Check if a criterion is redundant (routes to same repo as catch_all)."""
        return criterion.repo == self.catch_all and criterion.drop == "store"
