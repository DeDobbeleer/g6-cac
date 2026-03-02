"""Device models for log sources.

Based on LogPoint Director API specification.
"""

from __future__ import annotations

import re
from pydantic import BaseModel, Field, ConfigDict, field_validator


class Device(BaseModel):
    """Log source device.
    
    A device represents a log source that sends logs to LogPoint.
    It can be associated with device groups and processing policies.
    
    Example:
        devices:
          - name: "srv-web-01"
            ip_address: "10.0.1.10"
            device_group: "web-servers"
            processing_policy: "pp-web"
            collectors:
              - "syslog-collector-1"
    """
    model_config = ConfigDict(populate_by_name=True)
    
    name: str = Field(
        ..., 
        min_length=1,
        max_length=255,
        description="Device hostname or identifier"
    )
    ip_address: str = Field(
        ...,
        alias="ipAddress",
        description="Device IP address (IPv4 or IPv6)"
    )
    device_group: str | None = Field(
        default=None,
        alias="deviceGroup",
        description="Device group name this device belongs to"
    )
    processing_policy: str | None = Field(
        default=None,
        alias="processingPolicy",
        description="Processing policy to apply to this device's logs"
    )
    collectors: list[str] = Field(
        default_factory=list,
        description="List of syslog collector names for this device"
    )
    description: str | None = Field(
        default=None,
        description="Optional description"
    )
    enabled: bool = Field(
        default=True,
        description="Whether log collection is enabled"
    )
    
    # Template internal fields
    id: str | None = Field(default=None, alias="_id", description="Template ID")
    action: str | None = Field(default=None, alias="_action", description="Action: delete")
    
    @field_validator('ip_address')
    @classmethod
    def validate_ip_address(cls, v: str) -> str:
        """Validate IP address format (IPv4 or IPv6)."""
        # IPv4 pattern
        ipv4_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        # IPv6 pattern (simplified)
        ipv6_pattern = r'^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$|^::$|^::1$|^([0-9a-fA-F]{1,4}:)*::([0-9a-fA-F]{1,4}:)*[0-9a-fA-F]{1,4}$'
        
        if not (re.match(ipv4_pattern, v) or re.match(ipv6_pattern, v)):
            raise ValueError(f"Invalid IP address format: {v}")
        
        # Additional IPv4 validation
        if '.' in v and not ':' in v:
            parts = v.split('.')
            for part in parts:
                if not 0 <= int(part) <= 255:
                    raise ValueError(f"Invalid IPv4 address: octet {part} out of range")
        
        return v
