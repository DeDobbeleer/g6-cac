"""Repository models for log storage configuration.

Based on 20-TEMPLATE-HIERARCHY.md specification.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class HiddenRepoPath(BaseModel):
    """Storage tier configuration within a repo.
    
    The _id field is used for template inheritance matching.
    Multiple tiers can be defined (fast, warm, cold, nfs).
    
    Example:
        hiddenrepopath:
          - _id: fast-tier
            path: /opt/immune/storage
            retention: 7
          - _id: warm-tier
            path: /opt/immune/storage-warm
            retention: 90
          - _id: nfs-tier
            path: /opt/immune/storage-nfs
            retention: 3650
    """
    _id: str = Field(..., description="Template ID for inheritance matching")
    path: str = Field(..., description="Mount point path (e.g., /opt/immune/storage)")
    retention: int = Field(..., gt=0, description="Retention period in days")
    
    # Optional fields for ordering
    _after: str | None = Field(default=None, description="Insert after this _id")
    _before: str | None = Field(default=None, description="Insert before this _id")
    _position: int | None = Field(default=None, description="Absolute position (1-based)")
    _first: bool = Field(default=False, description="Force first position")
    _last: bool = Field(default=False, description="Force last position")


class Repo(BaseModel):
    """Repository configuration for log storage.
    
    A repo can have multiple storage tiers (hiddenrepopath) for
    hot/warm/cold/NFS rotation.
    
    Example:
        repos:
          - name: repo-secu
            hiddenrepopath:
              - _id: fast-tier
                path: /opt/immune/storage
                retention: 7
              - _id: warm-tier
                path: /opt/immune/storage-warm
                retention: 90
              - _id: nfs-tier
                path: /opt/immune/storage-nfs
                retention: 3650
    """
    name: str = Field(..., min_length=1, pattern=r"^[a-zA-Z0-9_-]+$")
    hiddenrepopath: list[HiddenRepoPath] = Field(default_factory=list)
    
    # Template internal fields
    _id: str | None = Field(default=None, description="Template ID for repo matching")
    _action: str | None = Field(default=None, description="Action: delete, etc.")
    
    def get_tier(self, tier_id: str) -> HiddenRepoPath | None:
        """Get a specific tier by _id."""
        for tier in self.hiddenrepopath:
            if tier._id == tier_id:
                return tier
        return None
    
    def get_retention_for_tier(self, tier_id: str) -> int | None:
        """Get retention days for a specific tier."""
        tier = self.get_tier(tier_id)
        return tier.retention if tier else None
