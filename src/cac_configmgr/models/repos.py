"""Repository models for log storage configuration.

Based on 20-TEMPLATE-HIERARCHY.md specification.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict


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
    model_config = ConfigDict(populate_by_name=True)
    
    id: str = Field(..., alias="_id", description="Template ID for inheritance matching")
    path: str | None = Field(default=None, description="Mount point path (e.g., /opt/immune/storage)")
    retention: int | str = Field(..., description="Retention period in days (or template variable)")
    
    # Optional fields for ordering
    after: str | None = Field(default=None, alias="_after", description="Insert after this _id")
    before: str | None = Field(default=None, alias="_before", description="Insert before this _id")
    position: int | None = Field(default=None, alias="_position", description="Absolute position (1-based)")
    first: bool = Field(default=False, alias="_first", description="Force first position")
    last: bool = Field(default=False, alias="_last", description="Force last position")


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
    model_config = ConfigDict(populate_by_name=True)
    
    name: str = Field(..., min_length=1, pattern=r"^[a-zA-Z0-9_-]+$")
    hiddenrepopath: list[HiddenRepoPath] = Field(default_factory=list)
    
    # Template internal fields
    id: str | None = Field(default=None, alias="_id", description="Template ID for repo matching")
    action: str | None = Field(default=None, alias="_action", description="Action: delete, etc.")
    
    def get_tier(self, tier_id: str) -> HiddenRepoPath | None:
        """Get a specific tier by _id."""
        for tier in self.hiddenrepopath:
            if tier.id == tier_id:
                return tier
        return None
    
    def get_retention_for_tier(self, tier_id: str) -> int | None:
        """Get retention days for a specific tier."""
        tier = self.get_tier(tier_id)
        return tier.retention if tier else None
