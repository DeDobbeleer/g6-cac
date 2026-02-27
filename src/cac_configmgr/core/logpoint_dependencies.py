"""LogPoint resource dependencies validator.

Based on DirSync and API constraints from AGENTS.md:

    Repos → Routing Policies → Processing Policies → Devices → Syslog Collector
              ↗                    ↗
    Normalization Policies          Enrichment Policies
              ↗
    Device Groups → Devices

This module validates that all dependencies are satisfied before deployment.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any


class ResourceType(Enum):
    """LogPoint resource types in dependency order."""
    REPO = auto()
    DEVICE_GROUP = auto()
    NORMALIZATION_POLICY = auto()  # External packages
    ENRICHMENT_SOURCE = auto()     # External sources
    ROUTING_POLICY = auto()
    ENRICHMENT_POLICY = auto()
    PROCESSING_POLICY = auto()
    DEVICE = auto()
    SYSLOG_COLLECTOR = auto()
    ALERT_RULE = auto()


@dataclass
class DependencyError:
    """Dependency validation error."""
    resource_type: str
    resource_name: str
    depends_on: str
    missing_ref: str
    severity: str = "ERROR"  # ERROR or WARNING
    message: str = ""


class LogPointDependencyValidator:
    """Validates LogPoint resource dependencies.
    
    Ensures that resources are created in the correct order and that
    all references point to existing resources.
    
    Usage:
        validator = LogPointDependencyValidator(resolved_resources)
        errors = validator.validate()
        if errors:
            validator.print_report()
    """
    
    # Dependency graph: resource_type -> list of (field, required_type)
    DEPENDENCIES = {
        "routing_policies": [
            ("catch_all", "repos"),
            ("routing_criteria.*.repo", "repos"),
        ],
        "enrichment_policies": [
            ("sources.*.source", "enrichment_sources"),
        ],
        "processing_policies": [
            ("routingPolicy", "routing_policies"),
            ("normalizationPolicy", "normalization_policies"),
            ("enrichmentPolicy", "enrichment_policies"),
        ],
        "devices": [
            ("processingPolicy", "processing_policies"),
            ("deviceGroup", "device_groups"),
        ],
        "syslog_collectors": [
            ("devices.*", "devices"),
        ],
        "alert_rules": [
            ("repos.*", "repos"),
        ],
    }
    
    def __init__(self, resources: dict[str, list[dict]]):
        """Initialize validator with resolved resources.
        
        Args:
            resources: Dict mapping resource type to list of resource dicts
        """
        self.resources = resources
        self.errors: list[DependencyError] = []
        
        # Build name indexes for each resource type
        self._indexes: dict[str, set[str]] = {}
        self._build_indexes()
    
    def _build_indexes(self) -> None:
        """Build fast lookup indexes for all resource types."""
        name_fields = {
            "repos": "name",
            "routing_policies": "policy_name",
            "processing_policies": "name",
            "normalization_policies": "name",
            "enrichment_policies": "name",
            "device_groups": "name",
            "devices": "name",
            "enrichment_sources": "name",
            "syslog_collectors": "name",
            "alert_rules": "name",
        }
        
        for resource_type, items in self.resources.items():
            name_field = name_fields.get(resource_type, "name")
            self._indexes[resource_type] = {
                item.get(name_field) or item.get("name") or item.get("policy_name")
                for item in items
                if item
            }
    
    def validate(self) -> list[DependencyError]:
        """Run all dependency validations.
        
        Returns:
            List of dependency errors
        """
        self.errors = []
        
        self._validate_routing_policies()
        self._validate_processing_policies()
        self._validate_devices()
        self._validate_alert_rules()
        
        return self.errors
    
    def _validate_routing_policies(self) -> None:
        """Validate Routing Policy dependencies."""
        for rp in self.resources.get("routing_policies", []):
            rp_name = rp.get("policy_name", "unknown")
            
            # Validate catch_all repo exists
            catch_all = rp.get("catch_all")
            if catch_all and not self._exists("repos", catch_all):
                self.errors.append(DependencyError(
                    resource_type="routing_policies",
                    resource_name=rp_name,
                    depends_on="repos",
                    missing_ref=catch_all,
                    message=f"catch_all references non-existent repo: {catch_all}"
                ))
            
            # Validate each criterion's repo
            for criterion in rp.get("routing_criteria", []):
                repo = criterion.get("repo")
                if repo and not self._exists("repos", repo):
                    self.errors.append(DependencyError(
                        resource_type="routing_policies",
                        resource_name=rp_name,
                        depends_on="repos",
                        missing_ref=repo,
                        message=f"routing_criterion references non-existent repo: {repo}"
                    ))
    
    def _validate_processing_policies(self) -> None:
        """Validate Processing Policy dependencies."""
        for pp in self.resources.get("processing_policies", []):
            pp_name = pp.get("name", "unknown")
            
            # routingPolicy is REQUIRED
            rp_ref = pp.get("routingPolicy")
            if rp_ref and not self._exists("routing_policies", rp_ref):
                self.errors.append(DependencyError(
                    resource_type="processing_policies",
                    resource_name=pp_name,
                    depends_on="routing_policies",
                    missing_ref=rp_ref,
                    message=f"routingPolicy references non-existent routing policy: {rp_ref}"
                ))
            
            # normalizationPolicy is optional
            np_ref = pp.get("normalizationPolicy")
            if np_ref and not self._exists("normalization_policies", np_ref):
                self.errors.append(DependencyError(
                    resource_type="processing_policies",
                    resource_name=pp_name,
                    depends_on="normalization_policies",
                    missing_ref=np_ref,
                    severity="WARNING",
                    message=f"normalizationPolicy references non-existent policy: {np_ref} (will use Auto)"
                ))
            
            # enrichmentPolicy is optional
            ep_ref = pp.get("enrichmentPolicy")
            if ep_ref and not self._exists("enrichment_policies", ep_ref):
                self.errors.append(DependencyError(
                    resource_type="processing_policies",
                    resource_name=pp_name,
                    depends_on="enrichment_policies",
                    missing_ref=ep_ref,
                    severity="WARNING",
                    message=f"enrichmentPolicy references non-existent policy: {ep_ref}"
                ))
    
    def _validate_devices(self) -> None:
        """Validate Device dependencies."""
        for device in self.resources.get("devices", []):
            device_name = device.get("name", "unknown")
            
            # processingPolicy is optional but recommended
            pp_ref = device.get("processingPolicy")
            if pp_ref and not self._exists("processing_policies", pp_ref):
                self.errors.append(DependencyError(
                    resource_type="devices",
                    resource_name=device_name,
                    depends_on="processing_policies",
                    missing_ref=pp_ref,
                    message=f"processingPolicy references non-existent policy: {pp_ref}"
                ))
            
            # deviceGroup is optional
            dg_ref = device.get("deviceGroup")
            if dg_ref and not self._exists("device_groups", dg_ref):
                self.errors.append(DependencyError(
                    resource_type="devices",
                    resource_name=device_name,
                    depends_on="device_groups",
                    missing_ref=dg_ref,
                    message=f"deviceGroup references non-existent group: {dg_ref}"
                ))
    
    def _validate_alert_rules(self) -> None:
        """Validate Alert Rule dependencies."""
        for alert in self.resources.get("alert_rules", []):
            alert_name = alert.get("name", "unknown")
            
            # Validate repos used by alert
            repos = alert.get("repos", [])
            for repo in repos:
                if not self._exists("repos", repo):
                    self.errors.append(DependencyError(
                        resource_type="alert_rules",
                        resource_name=alert_name,
                        depends_on="repos",
                        missing_ref=repo,
                        message=f"alert references non-existent repo: {repo}"
                    ))
    
    def _exists(self, resource_type: str, name: str) -> bool:
        """Check if a resource exists."""
        return name in self._indexes.get(resource_type, set())
    
    def get_deployment_order(self) -> list[str]:
        """Get the correct deployment order for resources.
        
        Returns:
            List of resource types in deployment order
        """
        return [
            "repos",
            "device_groups",
            "normalization_policies",
            "enrichment_sources",
            "routing_policies",
            "enrichment_policies",
            "processing_policies",
            "devices",
            "syslog_collectors",
            "alert_rules",
        ]
    
    def is_valid(self) -> bool:
        """Check if all dependencies are satisfied (no errors)."""
        errors = self.validate()
        return not any(e.severity == "ERROR" for e in errors)
    
    def print_report(self) -> None:
        """Print validation report."""
        errors = self.validate()
        
        if not errors:
            print("✅ All LogPoint dependencies satisfied")
            return
        
        # Group by severity
        errors_list = [e for e in errors if e.severity == "ERROR"]
        warnings_list = [e for e in errors if e.severity == "WARNING"]
        
        if errors_list:
            print(f"❌ {len(errors_list)} dependency error(s):")
            for e in errors_list:
                print(f"  • {e.resource_type}.{e.resource_name}: {e.message}")
            print()
        
        if warnings_list:
            print(f"⚠️  {len(warnings_list)} warning(s):")
            for e in warnings_list:
                print(f"  • {e.resource_type}.{e.resource_name}: {e.message}")
            print()


def validate_dependencies(resources: dict[str, list[dict]]) -> list[DependencyError]:
    """Quick validation function.
    
    Args:
        resources: Resolved resources
        
    Returns:
        List of dependency errors
    """
    validator = LogPointDependencyValidator(resources)
    return validator.validate()
