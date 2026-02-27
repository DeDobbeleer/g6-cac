"""Cross-resource validation - Verify references between resources.

Validates that all resource references are consistent:
- ProcessingPolicy.routing_policy → exists in routing_policies
- RoutingPolicy.catch_all → exists in repos
- RoutingCriterion.repo → exists in repos
"""

from __future__ import annotations

from typing import Any
from dataclasses import dataclass


@dataclass
class ValidationError:
    """Single validation error."""
    resource_type: str
    resource_name: str
    field: str
    reference: str
    message: str


class ConsistencyValidator:
    """Validates consistency between resource references.
    
    Example:
        validator = ConsistencyValidator(resolved.resources)
        errors = validator.validate()
        if errors:
            for e in errors:
                print(f"{e.resource_type}.{e.resource_name}: {e.message}")
    """
    
    def __init__(self, resources: dict[str, list[dict]]):
        """Initialize validator with resolved resources.
        
        Args:
            resources: Dict of resource type to list of resource dicts
                      (e.g., {"repos": [...], "routing_policies": [...]})
        """
        self.resources = resources
        self.errors: list[ValidationError] = []
    
    def validate(self) -> list[ValidationError]:
        """Run all validation checks.
        
        Returns:
            List of validation errors (empty if all valid)
        """
        self.errors = []
        
        # Build indexes for fast lookup
        self.repo_names = self._get_resource_names("repos", "name")
        self.routing_policy_names = self._get_resource_names("routing_policies", "policy_name")
        
        # Validate routing policies
        self._validate_routing_policies()
        
        # Validate processing policies
        self._validate_processing_policies()
        
        return self.errors
    
    def _get_resource_names(self, resource_type: str, name_field: str) -> set[str]:
        """Get set of resource names for fast lookup."""
        return {
            r.get(name_field, r.get("name"))
            for r in self.resources.get(resource_type, [])
            if r.get(name_field) or r.get("name")
        }
    
    def _validate_routing_policies(self) -> None:
        """Validate routing policy references."""
        for rp in self.resources.get("routing_policies", []):
            rp_name = rp.get("policy_name", "unknown")
            
            # Validate catch_all repo exists
            catch_all = rp.get("catch_all")
            if catch_all and catch_all not in self.repo_names:
                self.errors.append(ValidationError(
                    resource_type="routing_policies",
                    resource_name=rp_name,
                    field="catch_all",
                    reference=catch_all,
                    message=f"catch_all references non-existent repo: {catch_all}"
                ))
            
            # Validate each criterion's repo exists
            for criterion in rp.get("routing_criteria", []):
                repo = criterion.get("repo")
                if repo and repo not in self.repo_names:
                    self.errors.append(ValidationError(
                        resource_type="routing_policies",
                        resource_name=rp_name,
                        field="routing_criteria.repo",
                        reference=repo,
                        message=f"criterion references non-existent repo: {repo}"
                    ))
    
    def _validate_processing_policies(self) -> None:
        """Validate processing policy references."""
        for pp in self.resources.get("processing_policies", []):
            pp_name = pp.get("name", "unknown")
            
            # Validate routing_policy exists
            rp_ref = pp.get("routingPolicy")
            if rp_ref and rp_ref not in self.routing_policy_names:
                self.errors.append(ValidationError(
                    resource_type="processing_policies",
                    resource_name=pp_name,
                    field="routingPolicy",
                    reference=rp_ref,
                    message=f"references non-existent routing policy: {rp_ref}"
                ))
    
    def is_valid(self) -> bool:
        """Check if all resources are consistent."""
        return len(self.validate()) == 0
    
    def print_report(self) -> None:
        """Print validation report."""
        errors = self.validate()
        
        if not errors:
            print("✅ All resource references are consistent")
            return
        
        print(f"❌ Found {len(errors)} consistency error(s):\n")
        
        # Group by resource type
        by_type: dict[str, list[ValidationError]] = {}
        for e in errors:
            by_type.setdefault(e.resource_type, []).append(e)
        
        for resource_type, type_errors in by_type.items():
            print(f"  {resource_type}:")
            for e in type_errors:
                print(f"    • {e.resource_name}.{e.field}: {e.message}")
            print()


def validate_resources(resources: dict[str, list[dict]]) -> list[ValidationError]:
    """Quick validation function.
    
    Args:
        resources: Resolved resources from ResolutionEngine
        
    Returns:
        List of validation errors
        
    Example:
        errors = validate_resources(resolved.resources)
        if errors:
            print(f"Found {len(errors)} errors")
    """
    validator = ConsistencyValidator(resources)
    return validator.validate()
