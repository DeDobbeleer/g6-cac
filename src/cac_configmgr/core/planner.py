"""Plan engine - calculates diff between declared and actual state.

The planner compares desired state (from YAML resolution) with actual state
(from API queries) and produces a plan of changes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any


class ChangeType(Enum):
    """Type of change required."""
    CREATE = auto()    # Resource exists in declared but not in actual
    UPDATE = auto()    # Resource exists in both but differs
    DELETE = auto()    # Resource exists in actual but not in declared
    UNCHANGED = auto()  # Resource identical in both


@dataclass
class FieldDiff:
    """Difference in a single field.
    
    Attributes:
        field: Field name (dot notation for nested)
        old: Current value in actual state
        new: Desired value from declared state
        change_type: Type of change
    """
    field: str
    old: Any
    new: Any
    change_type: ChangeType = ChangeType.UPDATE


@dataclass
class ResourceChange:
    """Change required for a single resource.
    
    Attributes:
        resource_type: Type of resource (repos, routing_policies, etc.)
        name: Resource name (identifier)
        change_type: CREATE, UPDATE, DELETE, or UNCHANGED
        declared: Declared state (None for DELETE)
        actual: Actual state (None for CREATE)
        diffs: List of field-level differences (for UPDATE)
    """
    resource_type: str
    name: str
    change_type: ChangeType
    declared: dict | None = None
    actual: dict | None = None
    diffs: list[FieldDiff] = field(default_factory=list)
    
    @property
    def has_changes(self) -> bool:
        """Check if this resource has actual changes."""
        return self.change_type != ChangeType.UNCHANGED


@dataclass
class PlanSummary:
    """Summary of all planned changes."""
    create: int = 0
    update: int = 0
    delete: int = 0
    unchanged: int = 0
    
    @property
    def total(self) -> int:
        """Total number of resources."""
        return self.create + self.update + self.delete + self.unchanged
    
    @property
    def has_changes(self) -> bool:
        """Check if any changes are required."""
        return self.create > 0 or self.update > 0 or self.delete > 0
    
    def __str__(self) -> str:
        parts = []
        if self.create:
            parts.append(f"Create: {self.create}")
        if self.update:
            parts.append(f"Update: {self.update}")
        if self.delete:
            parts.append(f"Delete: {self.delete}")
        if self.unchanged:
            parts.append(f"Unchanged: {self.unchanged}")
        return " | ".join(parts) if parts else "No changes"


@dataclass
class Plan:
    """Complete plan for a set of resources.
    
    Attributes:
        changes: List of all resource changes
        summary: Aggregated statistics
    """
    changes: list[ResourceChange] = field(default_factory=list)
    summary: PlanSummary = field(default_factory=PlanSummary)
    
    def is_empty(self) -> bool:
        """Check if plan has no changes."""
        return not any(c.has_changes for c in self.changes)
    
    def changes_by_type(self) -> dict[str, list[ResourceChange]]:
        """Group changes by resource type.
        
        Returns:
            Dict mapping resource_type to list of changes
        """
        result: dict[str, list[ResourceChange]] = {}
        for change in self.changes:
            if change.resource_type not in result:
                result[change.resource_type] = []
            result[change.resource_type].append(change)
        return result
    
    def to_dict(self) -> dict:
        """Convert plan to dictionary for JSON serialization."""
        return {
            "summary": {
                "create": self.summary.create,
                "update": self.summary.update,
                "delete": self.summary.delete,
                "unchanged": self.summary.unchanged,
                "total": self.summary.total,
            },
            "changes": [
                {
                    "resource_type": c.resource_type,
                    "name": c.name,
                    "change_type": c.change_type.name,
                    "diffs": [
                        {
                            "field": d.field,
                            "old": d.old,
                            "new": d.new,
                        }
                        for d in c.diffs
                    ] if c.diffs else None,
                }
                for c in self.changes if c.has_changes
            ],
        }


class DiffCalculator:
    """Calculates differences between declared and actual state.
    
    Uses APIConvention to properly identify resources and fields
    according to provider-specific rules.
    
    Example:
        calculator = DiffCalculator(convention)
        plan = calculator.compare(declared_resources, actual_resources)
        
        if plan.is_empty():
            print("No changes needed")
        else:
            print(f"Changes: {plan.summary}")
    """
    
    def __init__(self, convention):
        """Initialize with API convention.
        
        Args:
            convention: APIConvention implementation
        """
        self.convention = convention
    
    def compare(
        self,
        declared: dict[str, list[dict]],
        actual: dict[str, list[dict]],
    ) -> Plan:
        """Compare declared vs actual state.
        
        Args:
            declared: Desired state from YAML resolution
            actual: Current state from API
            
        Returns:
            Plan with all changes
        """
        changes = []
        summary = PlanSummary()
        
        # Compare each resource type
        all_types = set(declared.keys()) | set(actual.keys())
        
        for resource_type in all_types:
            declared_list = declared.get(resource_type, [])
            actual_list = actual.get(resource_type, [])
            
            type_changes = self._compare_resource_type(
                resource_type, declared_list, actual_list
            )
            
            for change in type_changes:
                changes.append(change)
                
                # Update summary
                if change.change_type == ChangeType.CREATE:
                    summary.create += 1
                elif change.change_type == ChangeType.UPDATE:
                    summary.update += 1
                elif change.change_type == ChangeType.DELETE:
                    summary.delete += 1
                else:
                    summary.unchanged += 1
        
        return Plan(changes=changes, summary=summary)
    
    def _compare_resource_type(
        self,
        resource_type: str,
        declared: list[dict],
        actual: list[dict],
    ) -> list[ResourceChange]:
        """Compare resources of a single type.
        
        Args:
            resource_type: Type of resource
            declared: List of declared resources
            actual: List of actual resources
            
        Returns:
            List of changes
        """
        changes = []
        
        # Get name field for this resource type
        name_field = self.convention.get_name_field(resource_type)
        
        # Build name-indexed maps
        declared_by_name = {r.get(name_field): r for r in declared if r.get(name_field)}
        actual_by_name = {r.get(name_field): r for r in actual if r.get(name_field)}
        
        # Find creates and updates
        for name, declared_resource in declared_by_name.items():
            if name not in actual_by_name:
                # CREATE
                changes.append(ResourceChange(
                    resource_type=resource_type,
                    name=name,
                    change_type=ChangeType.CREATE,
                    declared=declared_resource,
                    actual=None,
                ))
            else:
                # Compare for UPDATE or UNCHANGED
                actual_resource = actual_by_name[name]
                diffs = self._calculate_diffs(declared_resource, actual_resource)
                
                if diffs:
                    changes.append(ResourceChange(
                        resource_type=resource_type,
                        name=name,
                        change_type=ChangeType.UPDATE,
                        declared=declared_resource,
                        actual=actual_resource,
                        diffs=diffs,
                    ))
                else:
                    changes.append(ResourceChange(
                        resource_type=resource_type,
                        name=name,
                        change_type=ChangeType.UNCHANGED,
                        declared=declared_resource,
                        actual=actual_resource,
                    ))
        
        # Find deletes
        for name, actual_resource in actual_by_name.items():
            if name not in declared_by_name:
                changes.append(ResourceChange(
                    resource_type=resource_type,
                    name=name,
                    change_type=ChangeType.DELETE,
                    declared=None,
                    actual=actual_resource,
                ))
        
        return changes
    
    def _calculate_diffs(self, declared: dict, actual: dict) -> list[FieldDiff]:
        """Calculate field-level differences.
        
        Args:
            declared: Declared resource state
            actual: Actual resource state
            
        Returns:
            List of field differences
        """
        diffs = []
        
        # Compare all fields from both dicts
        all_fields = set(declared.keys()) | set(actual.keys())
        
        # Skip internal fields
        all_fields = {f for f in all_fields if not f.startswith("_")}
        
        for field in all_fields:
            declared_val = declared.get(field)
            actual_val = actual.get(field)
            
            # Normalize None vs empty
            if declared_val is None and actual_val in (None, "", []):
                continue
            if actual_val is None and declared_val in (None, "", []):
                continue
            
            # Compare values
            if declared_val != actual_val:
                diffs.append(FieldDiff(
                    field=field,
                    old=actual_val,
                    new=declared_val,
                ))
        
        return diffs
