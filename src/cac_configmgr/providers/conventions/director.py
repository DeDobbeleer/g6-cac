"""LogPoint Director API conventions.

Implements APIConvention for LogPoint Director API v1.3+.

Director API characteristics:
- Uses camelCase for some field names (e.g., routingPolicy, deviceGroup)
- Uses policy_name for most policies (except NormalizationPolicy which uses 'name')
- Pool-scoped endpoints: /configapi/{pool_uuid}/{endpoint}
- Async operations return 202 with polling URL
"""

from __future__ import annotations

from cac_configmgr.core.conventions import (
    APIConvention,
    ResourceSpec,
    FieldSpec,
    CrossReferenceRule,
)


class DirectorAPIConvention(APIConvention):
    """LogPoint Director API conventions (v1.3+).
    
    Implements the APIConvention interface for Director API specifics.
    
    Example:
        convention = DirectorAPIConvention()
        
        # Field name transformation
        api_field = convention.get_field_alias("processing_policy", "routing_policy")
        assert api_field == "routingPolicy"  # camelCase in Director API
        
        # Name field lookup
        name_field = convention.get_name_field("routing_policies")
        assert name_field == "policy_name"
    """
    
    # API endpoint mappings
    RESOURCE_ENDPOINTS = {
        "repos": "/repos",
        "routing_policies": "/routingpolicies",
        "normalization_policies": "/normalizationpolicy",
        "enrichment_policies": "/enrichmentpolicy",
        "processing_policies": "/processingpolicy",
        "device_groups": "/devicegroups",
        "devices": "/devices",
        "alert_rules": "/alertrules",
        "users": "/users",
        "user_groups": "/usergroups",
    }
    
    # Name fields vary by resource type (ADR-009)
    NAME_FIELDS = {
        "repos": "name",
        "routing_policies": "policy_name",
        "processing_policies": "policy_name",
        "normalization_policies": "name",  # Exception!
        "enrichment_policies": "name",  # Actually uses policy_name in API
        "device_groups": "name",
        "devices": "name",
        "alert_rules": "name",
        "users": "username",
        "user_groups": "name",
    }
    
    # Field aliases: Director API uses camelCase for some fields
    FIELD_ALIASES = {
        "processing_policy": {
            "routing_policy": "routingPolicy",
            "normalization_policy": "normalizationPolicy",
            "enrichment_policy": "enrichmentPolicy",
        },
        "device": {
            "ip_address": "ipAddress",
            "device_group": "deviceGroup",
            "processing_policy": "processingPolicy",
        },
        "device_group": {
            "parent_group": "parentGroup",
        },
    }
    
    # API field specifications for validation
    API_SPECS = {
        "routing_policy": {
            "policy_name": FieldSpec(
                name="policy_name",
                type=str,
                required=True,
                pattern=r"^[a-zA-Z0-9_-]+$",
                api_doc="https://docs.logpoint.com/director-apis/routingpolicies",
            ),
            "catch_all": FieldSpec(
                name="catch_all",
                type=str,
                required=True,
                api_doc="https://docs.logpoint.com/director-apis/routingpolicies",
            ),
            "routing_criteria": FieldSpec(
                name="routing_criteria",
                type=list,
                required=True,
                api_doc="https://docs.logpoint.com/director-apis/routingpolicies",
            ),
        },
        "processing_policy": {
            "policy_name": FieldSpec(
                name="policy_name",
                type=str,
                required=True,
                pattern=r"^[a-zA-Z0-9_-]+$",
                alias="name",  # YAML uses 'name', API uses 'policy_name'
                api_doc="https://docs.logpoint.com/director-apis/processingpolicy",
            ),
            "routing_policy": FieldSpec(
                name="routing_policy",
                type=str,
                required=True,
                alias="routingPolicy",  # camelCase in API
                api_doc="https://docs.logpoint.com/director-apis/processingpolicy",
            ),
            "normalization_policy": FieldSpec(
                name="normalization_policy",
                type=str,
                required=False,
                alias="normalizationPolicy",  # camelCase in API
                default="None",
                api_doc="https://docs.logpoint.com/director-apis/processingpolicy",
            ),
            "enrichment_policy": FieldSpec(
                name="enrichment_policy",
                type=str,
                required=False,
                alias="enrichmentPolicy",  # camelCase in API
                default="None",
                api_doc="https://docs.logpoint.com/director-apis/processingpolicy",
            ),
        },
        "normalization_policy": {
            "name": FieldSpec(
                name="name",
                type=str,
                required=True,
                pattern=r"^[a-zA-Z0-9_-]+$",
                api_doc="https://docs.logpoint.com/director-apis/normalizationpolicy",
            ),
            "normalization_packages": FieldSpec(
                name="normalization_packages",
                type=list,
                required=False,
                api_doc="https://docs.logpoint.com/director-apis/normalizationpolicy",
            ),
            "compiled_normalizer": FieldSpec(
                name="compiled_normalizer",
                type=str,
                required=False,
                api_doc="https://docs.logpoint.com/director-apis/normalizationpolicy",
            ),
        },
        "enrichment_policy": {
            "policy_name": FieldSpec(
                name="policy_name",
                type=str,
                required=True,
                pattern=r"^[a-zA-Z0-9_-]+$",
                alias="name",  # YAML uses 'name'
                api_doc="https://docs.logpoint.com/director-apis/enrichmentpolicy",
            ),
            "specifications": FieldSpec(
                name="specifications",
                type=list,
                required=True,
                api_doc="https://docs.logpoint.com/director-apis/enrichmentpolicy",
            ),
        },
        "repo": {
            "name": FieldSpec(
                name="name",
                type=str,
                required=True,
                pattern=r"^[a-zA-Z0-9_-]+$",
                api_doc="https://docs.logpoint.com/director-apis/repos",
            ),
            "hiddenrepopath": FieldSpec(
                name="hiddenrepopath",
                type=list,
                required=False,
                api_doc="https://docs.logpoint.com/director-apis/repos",
            ),
        },
        "device_group": {
            "name": FieldSpec(
                name="name",
                type=str,
                required=True,
                pattern=r"^[a-zA-Z0-9_-]+$",
                api_doc="https://docs.logpoint.com/director-apis/devicegroups",
            ),
            "description": FieldSpec(
                name="description",
                type=str,
                required=False,
                api_doc="https://docs.logpoint.com/director-apis/devicegroups",
            ),
            "criteria": FieldSpec(
                name="criteria",
                type=list,
                required=False,
                api_doc="https://docs.logpoint.com/director-apis/devicegroups",
            ),
        },
        "device": {
            "name": FieldSpec(
                name="name",
                type=str,
                required=True,
                alias="name",  # Same in API
                api_doc="https://docs.logpoint.com/director-apis/devices",
            ),
            "ip_address": FieldSpec(
                name="ip_address",
                type=str,
                required=True,
                alias="ipAddress",  # camelCase in API
                api_doc="https://docs.logpoint.com/director-apis/devices",
            ),
            "device_group": FieldSpec(
                name="device_group",
                type=str,
                required=False,
                alias="deviceGroup",  # camelCase in API
                api_doc="https://docs.logpoint.com/director-apis/devices",
            ),
            "processing_policy": FieldSpec(
                name="processing_policy",
                type=str,
                required=False,
                alias="processingPolicy",  # camelCase in API
                api_doc="https://docs.logpoint.com/director-apis/devices",
            ),
            "collectors": FieldSpec(
                name="collectors",
                type=list,
                required=False,
                api_doc="https://docs.logpoint.com/director-apis/devices",
            ),
            "enabled": FieldSpec(
                name="enabled",
                type=bool,
                required=False,
                default=True,
                api_doc="https://docs.logpoint.com/director-apis/devices",
            ),
        },
    }
    
    # Cross-reference validation rules
    CROSS_REFERENCES = [
        CrossReferenceRule(
            source_type="processing_policies",
            source_field="routing_policy",
            target_type="routing_policies",
            allow_none=False,
            description="Processing Policy must reference existing Routing Policy",
        ),
        CrossReferenceRule(
            source_type="processing_policies",
            source_field="normalization_policy",
            target_type="normalization_policies",
            allow_none=True,
            description="Processing Policy may reference Normalization Policy",
        ),
        CrossReferenceRule(
            source_type="processing_policies",
            source_field="enrichment_policy",
            target_type="enrichment_policies",
            allow_none=True,
            description="Processing Policy may reference Enrichment Policy",
        ),
        CrossReferenceRule(
            source_type="routing_policies",
            source_field="catch_all",
            target_type="repos",
            allow_none=False,
            description="Routing Policy catch_all must reference existing Repo",
        ),
        CrossReferenceRule(
            source_type="routing_policies",
            source_field="routing_criteria.repo",
            target_type="repos",
            allow_none=False,
            description="Routing Criterion must reference existing Repo",
        ),
        CrossReferenceRule(
            source_type="devices",
            source_field="device_group",
            target_type="device_groups",
            allow_none=True,
            description="Device may reference Device Group",
        ),
        CrossReferenceRule(
            source_type="devices",
            source_field="processing_policy",
            target_type="processing_policies",
            allow_none=True,
            description="Device may reference Processing Policy",
        ),
    ]
    
    @property
    def provider_name(self) -> str:
        """Return provider identifier."""
        return "director"
    
    @property
    def api_version(self) -> str:
        """Return API version."""
        return "v1.3"
    
    def get_resource_spec(self, resource_type: str) -> ResourceSpec | None:
        """Get specification for a resource type.
        
        Args:
            resource_type: Resource type (e.g., "routing_policies")
            
        Returns:
            ResourceSpec or None if unknown
        """
        # Map plural resource types to singular spec keys
        spec_key = resource_type.rstrip("s")
        if resource_type.endswith("ies"):
            spec_key = resource_type[:-3] + "y"
        
        if spec_key not in self.API_SPECS:
            return None
        
        fields = self.API_SPECS[spec_key]
        name_field = self.get_name_field(resource_type)
        endpoint = self.get_endpoint(resource_type) or f"/{spec_key}s"
        
        return ResourceSpec(
            resource_type=resource_type,
            endpoint=endpoint,
            name_field=name_field,
            fields=fields,
        )
    
    def get_field_alias(self, resource_type: str, field_name: str) -> str:
        """Get API field name for a given internal field.
        
        Director API uses camelCase for some fields.
        
        Args:
            resource_type: Type of resource
            field_name: Internal field name
            
        Returns:
            API field name
        """
        # Get singular resource key
        singular = resource_type.rstrip("s")
        if resource_type.endswith("ies"):
            singular = resource_type[:-3] + "y"
        
        # Check for alias in FIELD_ALIASES
        if singular in self.FIELD_ALIASES:
            if field_name in self.FIELD_ALIASES[singular]:
                return self.FIELD_ALIASES[singular][field_name]
        
        # Check for alias in API_SPECS
        spec_key = singular
        if spec_key in self.API_SPECS:
            if field_name in self.API_SPECS[spec_key]:
                field_spec = self.API_SPECS[spec_key][field_name]
                if field_spec.alias:
                    return field_spec.alias
        
        # Default: return field name as-is
        return field_name
    
    def get_name_field(self, resource_type: str) -> str:
        """Get the name field for a resource type.
        
        Args:
            resource_type: Resource type
            
        Returns:
            Name field key
        """
        return self.NAME_FIELDS.get(resource_type, "name")
    
    def get_endpoint(self, resource_type: str) -> str | None:
        """Get API endpoint for a resource type.
        
        Args:
            resource_type: Resource type
            
        Returns:
            Endpoint path or None if not supported
        """
        return self.RESOURCE_ENDPOINTS.get(resource_type)
    
    def get_supported_resources(self) -> list[str]:
        """Get list of supported resource types."""
        return list(self.RESOURCE_ENDPOINTS.keys())
    
    def get_cross_reference_validations(self) -> list[CrossReferenceRule]:
        """Get cross-reference validation rules."""
        return self.CROSS_REFERENCES.copy()


# Auto-register on import
from cac_configmgr.core.conventions import register_convention

register_convention("director", DirectorAPIConvention)
register_convention("logpoint/director/v1.3", DirectorAPIConvention)
register_convention("logpoint/director", DirectorAPIConvention)
