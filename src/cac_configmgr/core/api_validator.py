"""API-compliant validation for LogPoint Director.

Validates configurations against:
- CaC-ConfigMgr internal specs
- LogPoint Director API requirements
- Field types and required fields
- Cross-reference dependencies
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import re


@dataclass
class ValidationError:
    """Single validation error."""
    resource_type: str
    resource_name: str
    field: str
    message: str
    severity: str = "ERROR"  # ERROR or WARNING
    api_doc: str = ""  # Link to API doc


class APIFieldValidator:
    """Validates fields against LogPoint Director API specs."""
    
    # API field specifications from API-REFERENCE.md
    API_SPECS = {
        "routing_policy": {
            "policy_name": {"type": str, "required": True, "pattern": r"^[a-zA-Z0-9_-]+$"},
            "catch_all": {"type": str, "required": True},
            "routing_criteria": {"type": list, "required": True},
        },
        "processing_policy": {
            "policy_name": {"type": str, "required": True, "pattern": r"^[a-zA-Z0-9_-]+$"},
            "routing_policy": {"type": str, "required": True},  # RP ID
            "normalization_policy": {"type": str, "required": False},  # NP name or "None"
            "enrichment_policy": {"type": str, "required": False},  # EP ID or "None"
        },
        "normalization_policy": {
            "name": {"type": str, "required": True, "pattern": r"^[a-zA-Z0-9_-]+$"},
            "normalization_packages": {"type": list, "required": False},
            "compiled_normalizer": {"type": str, "required": False},
        },
        "enrichment_policy": {
            "name": {"type": str, "required": True, "pattern": r"^[a-zA-Z0-9_-]+$"},
            "specifications": {"type": list, "required": True},
        },
        "enrichment_specification": {
            "source": {"type": str, "required": True},
            "criteria": {"type": list, "required": True},
            "rules": {"type": list, "required": False},
        },
        "repo": {
            "name": {"type": str, "required": True, "pattern": r"^[a-zA-Z0-9_-]+$"},
            "hiddenrepopath": {"type": list, "required": False},  # Storage tiers
        },
        "hiddenrepopath": {
            "_id": {"type": str, "required": True},
            "path": {"type": str, "required": True},
            "retention": {"type": int, "required": True},
        },
    }
    
    def __init__(self, resources: dict[str, list[dict]]):
        """Initialize validator with resolved resources.
        
        Args:
            resources: Dict of resource type to list of resource dicts
        """
        self.resources = resources
        self.errors: list[ValidationError] = []
        
        # Build indexes for dependency checking
        self._indexes = self._build_indexes()
    
    def _build_indexes(self) -> dict[str, set[str]]:
        """Build indexes for quick lookup."""
        indexes = {}
        
        name_fields = {
            "repos": "name",
            "routing_policies": "policy_name",
            "processing_policies": "policy_name",
            "normalization_policies": "name",
            "enrichment_policies": "name",
        }
        
        for resource_type, name_field in name_fields.items():
            indexes[resource_type] = {
                item.get(name_field) 
                for item in self.resources.get(resource_type, [])
                if item.get(name_field)
            }
        
        # Also index by ID
        indexes["routing_policies_by_id"] = {
            item.get("id") 
            for item in self.resources.get("routing_policies", [])
            if item.get("id")
        }
        
        indexes["enrichment_policies_by_id"] = {
            item.get("id")
            for item in self.resources.get("enrichment_policies", [])
            if item.get("id")
        }
        
        return indexes
    
    def validate_all(self) -> list[ValidationError]:
        """Run all validations.
        
        Returns:
            List of validation errors (empty if all valid)
        """
        self.errors = []
        
        # Validate each resource type
        self._validate_routing_policies()
        self._validate_processing_policies()
        self._validate_normalization_policies()
        self._validate_enrichment_policies()
        self._validate_repos()
        
        # Validate cross-references
        self._validate_dependencies()
        
        return self.errors
    
    def _validate_routing_policies(self) -> None:
        """Validate routing policies against API spec."""
        spec = self.API_SPECS["routing_policy"]
        
        for rp in self.resources.get("routing_policies", []):
            rp_name = rp.get("policy_name", "unknown")
            
            # Check required fields
            for field, config in spec.items():
                if config["required"] and field not in rp:
                    self.errors.append(ValidationError(
                        resource_type="routing_policies",
                        resource_name=rp_name,
                        field=field,
                        message=f"Required field '{field}' is missing",
                        severity="ERROR",
                        api_doc="https://docs.logpoint.com/director/director-apis/director-console-api-documentation/routingpolicies"
                    ))
                elif field in rp:
                    # Check type (allow None for optional fields)
                    value = rp[field]
                    if value is None and not config.get("required", False):
                        continue  # None is allowed for optional fields (will be converted to "None")
                    
                    expected_type = config["type"]
                    if expected_type == str and not isinstance(value, str):
                        self.errors.append(ValidationError(
                            resource_type="routing_policies",
                            resource_name=rp_name,
                            field=field,
                            message=f"Field '{field}' should be string, got {type(value).__name__}",
                            severity="ERROR"
                        ))
                    elif expected_type == list and not isinstance(value, list):
                        self.errors.append(ValidationError(
                            resource_type="routing_policies",
                            resource_name=rp_name,
                            field=field,
                            message=f"Field '{field}' should be list, got {type(value).__name__}",
                            severity="ERROR"
                        ))
                    
                    # Check pattern
                    if "pattern" in config and isinstance(value, str):
                        if not re.match(config["pattern"], value):
                            self.errors.append(ValidationError(
                                resource_type="routing_policies",
                                resource_name=rp_name,
                                field=field,
                                message=f"Field '{field}' value '{value}' doesn't match pattern {config['pattern']}",
                                severity="ERROR"
                            ))
    
    def _validate_processing_policies(self) -> None:
        """Validate processing policies against API spec."""
        spec = self.API_SPECS["processing_policy"]
        
        for pp in self.resources.get("processing_policies", []):
            pp_name = pp.get("policy_name", "unknown")
            
            # Check required fields
            for field, config in spec.items():
                if config["required"] and field not in pp:
                    self.errors.append(ValidationError(
                        resource_type="processing_policies",
                        resource_name=pp_name,
                        field=field,
                        message=f"Required field '{field}' is missing",
                        severity="ERROR",
                        api_doc="https://docs.logpoint.com/director/director-apis/director-console-api-documentation/processingpolicy"
                    ))
                elif field in pp:
                    # Check type (allow None for optional fields)
                    value = pp[field]
                    if value is None and not config.get("required", False):
                        continue  # None is allowed for optional fields (will be converted to "None")
                    
                    expected_type = config["type"]
                    if expected_type == str and not isinstance(value, str):
                        self.errors.append(ValidationError(
                            resource_type="processing_policies",
                            resource_name=pp_name,
                            field=field,
                            message=f"Field '{field}' should be string, got {type(value).__name__}",
                            severity="ERROR"
                        ))
                    
                    # Check pattern
                    if "pattern" in config and isinstance(value, str):
                        if not re.match(config["pattern"], value):
                            self.errors.append(ValidationError(
                                resource_type="processing_policies",
                                resource_name=pp_name,
                                field=field,
                                message=f"Field '{field}' value '{value}' doesn't match pattern {config['pattern']}",
                                severity="ERROR"
                            ))
    
    def _validate_normalization_policies(self) -> None:
        """Validate normalization policies against API spec."""
        spec = self.API_SPECS["normalization_policy"]
        
        for np in self.resources.get("normalization_policies", []):
            np_name = np.get("name", "unknown")
            
            for field, config in spec.items():
                if config["required"] and field not in np:
                    self.errors.append(ValidationError(
                        resource_type="normalization_policies",
                        resource_name=np_name,
                        field=field,
                        message=f"Required field '{field}' is missing",
                        severity="ERROR",
                        api_doc="https://docs.logpoint.com/director/director-apis/director-console-api-documentation/normalizationpolicy"
                    ))
                elif field in np and "pattern" in config:
                    value = np[field]
                    if isinstance(value, str) and not re.match(config["pattern"], value):
                        self.errors.append(ValidationError(
                            resource_type="normalization_policies",
                            resource_name=np_name,
                            field=field,
                            message=f"Field '{field}' value '{value}' doesn't match pattern {config['pattern']}",
                            severity="ERROR"
                        ))
    
    def _validate_enrichment_policies(self) -> None:
        """Validate enrichment policies against API spec."""
        spec = self.API_SPECS["enrichment_policy"]
        
        for ep in self.resources.get("enrichment_policies", []):
            ep_name = ep.get("name", "unknown")
            
            for field, config in spec.items():
                if config["required"] and field not in ep:
                    self.errors.append(ValidationError(
                        resource_type="enrichment_policies",
                        resource_name=ep_name,
                        field=field,
                        message=f"Required field '{field}' is missing",
                        severity="ERROR",
                        api_doc="https://docs.logpoint.com/director/director-apis/director-console-api-documentation/enrichmentpolicy"
                    ))
            
            # Validate specifications structure
            if "specifications" in ep:
                for i, spec_item in enumerate(ep["specifications"]):
                    self._validate_enrichment_specification(spec_item, ep_name, i)
    
    def _validate_enrichment_specification(self, spec: dict, ep_name: str, index: int) -> None:
        """Validate a single enrichment specification."""
        spec_def = self.API_SPECS["enrichment_specification"]
        
        for field, config in spec_def.items():
            if config["required"] and field not in spec:
                self.errors.append(ValidationError(
                    resource_type="enrichment_policies",
                    resource_name=f"{ep_name}.specifications[{index}]",
                    field=field,
                    message=f"Required field '{field}' is missing in specification",
                    severity="ERROR"
                ))
    
    def _validate_repos(self) -> None:
        """Validate repos against API spec."""
        spec = self.API_SPECS["repo"]
        
        for repo in self.resources.get("repos", []):
            repo_name = repo.get("name", "unknown")
            
            for field, config in spec.items():
                if config["required"] and field not in repo:
                    self.errors.append(ValidationError(
                        resource_type="repos",
                        resource_name=repo_name,
                        field=field,
                        message=f"Required field '{field}' is missing",
                        severity="ERROR"
                    ))
                elif field in repo:
                    value = repo[field]
                    expected_type = config["type"]
                    if expected_type == int and not isinstance(value, int):
                        self.errors.append(ValidationError(
                            resource_type="repos",
                            resource_name=repo_name,
                            field=field,
                            message=f"Field '{field}' should be integer, got {type(value).__name__}",
                            severity="ERROR"
                        ))
                    
                    if "pattern" in config and isinstance(value, str):
                        if not re.match(config["pattern"], value):
                            self.errors.append(ValidationError(
                                resource_type="repos",
                                resource_name=repo_name,
                                field=field,
                                message=f"Field '{field}' value '{value}' doesn't match pattern {config['pattern']}",
                                severity="ERROR"
                            ))
    
    def _validate_dependencies(self) -> None:
        """Validate cross-references between resources."""
        # Validate Processing Policy references
        for pp in self.resources.get("processing_policies", []):
            pp_name = pp.get("policy_name", "unknown")
            
            # Check routing_policy reference
            rp_ref = pp.get("routing_policy")
            if rp_ref and rp_ref != "None":
                # routing_policy is an ID
                if rp_ref not in self._indexes.get("routing_policies_by_id", set()):
                    self.errors.append(ValidationError(
                        resource_type="processing_policies",
                        resource_name=pp_name,
                        field="routing_policy",
                        message=f"References non-existent Routing Policy ID: {rp_ref}",
                        severity="ERROR"
                    ))
            
            # Check norm_policy reference (by name)
            np_ref = pp.get("normalization_policy")
            if np_ref and np_ref != "None":
                if np_ref not in self._indexes.get("normalization_policies", set()):
                    self.errors.append(ValidationError(
                        resource_type="processing_policies",
                        resource_name=pp_name,
                        field="norm_policy",
                        message=f"References non-existent Normalization Policy: {np_ref}",
                        severity="ERROR"
                    ))
            
            # Check enrich_policy reference (by ID)
            ep_ref = pp.get("enrichment_policy")
            if ep_ref and ep_ref != "None":
                if ep_ref not in self._indexes.get("enrichment_policies_by_id", set()):
                    self.errors.append(ValidationError(
                        resource_type="processing_policies",
                        resource_name=pp_name,
                        field="enrich_policy",
                        message=f"References non-existent Enrichment Policy ID: {ep_ref}",
                        severity="ERROR"
                    ))
        
        # Validate Routing Policy catch_all references
        for rp in self.resources.get("routing_policies", []):
            rp_name = rp.get("policy_name", "unknown")
            
            catch_all = rp.get("catch_all")
            if catch_all:
                if catch_all not in self._indexes.get("repos", set()):
                    self.errors.append(ValidationError(
                        resource_type="routing_policies",
                        resource_name=rp_name,
                        field="catch_all",
                        message=f"References non-existent Repo: {catch_all}",
                        severity="ERROR"
                    ))
            
            # Check routing_criteria repo references
            for criterion in rp.get("routing_criteria", []):
                repo_ref = criterion.get("repo")
                if repo_ref and repo_ref not in self._indexes.get("repos", set()):
                    self.errors.append(ValidationError(
                        resource_type="routing_policies",
                        resource_name=rp_name,
                        field="routing_criteria.repo",
                        message=f"Criterion references non-existent Repo: {repo_ref}",
                        severity="ERROR"
                    ))
    
    def print_report(self) -> None:
        """Print validation report."""
        if not self.errors:
            print("✅ All API validations passed")
            return
        
        errors = [e for e in self.errors if e.severity == "ERROR"]
        warnings = [e for e in self.errors if e.severity == "WARNING"]
        
        if errors:
            print(f"\n❌ {len(errors)} API validation error(s):")
            for e in errors:
                print(f"  • [{e.resource_type}.{e.resource_name}] {e.field}: {e.message}")
                if e.api_doc:
                    print(f"    Doc: {e.api_doc}")
        
        if warnings:
            print(f"\n⚠️  {len(warnings)} warning(s):")
            for e in warnings:
                print(f"  • [{e.resource_type}.{e.resource_name}] {e.field}: {e.message}")


def validate_api_compliance(resources: dict[str, list[dict]]) -> list[ValidationError]:
    """Quick validation function.
    
    Args:
        resources: Resolved resources
        
    Returns:
        List of validation errors
    """
    validator = APIFieldValidator(resources)
    return validator.validate_all()
