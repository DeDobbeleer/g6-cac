"""Device Group models for organizing log sources.

Based on LogPoint Director API specification.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict


class Criterion(BaseModel):
    """Criterion for dynamic device group membership.
    
    Example:
        criteria:
          - key: "os_type"
            operator: "equals"
            value: "windows"
    """
    model_config = ConfigDict(populate_by_name=True)
    
    key: str = Field(..., description="Field to match (e.g., os_type, hostname)")
    operator: str = Field(default="equals", description="Operator: equals, contains, regex")
    value: str = Field(..., description="Value to match")


class DeviceGroup(BaseModel):
    """Device group for organizing log sources.
    
    Device groups can be static (manual member list) or dynamic (criteria-based).
    
    Example:
        device_groups:
          - name: "windows-servers"
            description: "All Windows servers"
            criteria:
              - key: "os_type"
                operator: "equals"
                value: "windows"
    """
    model_config = ConfigDict(populate_by_name=True)
    
    name: str = Field(
        ..., 
        min_length=1, 
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="Device group name"
    )
    description: str | None = Field(
        default=None,
        description="Optional description"
    )
    criteria: list[Criterion] = Field(
        default_factory=list,
        description="Dynamic membership criteria"
    )
    
    # Template internal fields
    id: str | None = Field(default=None, alias="_id", description="Template ID")
    action: str | None = Field(default=None, alias="_action", description="Action: delete")
