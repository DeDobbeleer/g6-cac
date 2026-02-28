"""Resource merging - Deep merge with _id matching for lists.

Based on Section 5.1 of 20-TEMPLATE-HIERARCHY.md specification.
"""

from __future__ import annotations

from typing import Any
from copy import deepcopy


class MergeError(Exception):
    """Error during resource merging."""
    pass


def _get_resource_name(resource: dict) -> str | None:
    """Get resource identifier from various possible name fields.
    
    Different resource types use different name fields:
    - repos: 'name'
    - routing_policies: 'policy_name'
    - processing_policies: 'policy_name'
    - normalization_policies: 'name'
    - enrichment_policies: 'name'
    """
    for key in ["policy_name", "name"]:
        if key in resource:
            return resource[key]
    return None


def merge_resources(base_list: list[dict], override_list: list[dict]) -> list[dict]:
    """Merge two resource lists by name.
    
    Strategy:
    - Same 'name'/'policy_name': Deep merge (recurse into lists with _id matching)
    - New name: Append
    - Explicit _action: 'delete': Remove
    
    Args:
        base_list: Base resources from parent template
        override_list: Override resources from child template
        
    Returns:
        Merged resource list
        
    Example:
        >>> base = [{"name": "repo-secu", "retention": 365}]
        >>> override = [{"name": "repo-secu", "retention": 90}]
        >>> merge_resources(base, override)
        [{"name": "repo-secu", "retention": 90}]
    """
    # Index base resources by name for O(1) lookup
    result = {}
    for r in base_list:
        name = _get_resource_name(r)
        if name:
            result[name] = r
    
    for resource in override_list:
        name = _get_resource_name(resource)
        if name is None:
            raise MergeError(f"Resource missing 'name' or 'policy_name' field: {resource}")
        
        # Check for explicit deletion
        if resource.get("action") == "delete" or resource.get("_action") == "delete":
            result.pop(name, None)
            continue
        
        if name in result:
            # Deep merge: merge fields, with special handling for lists
            result[name] = deep_merge(result[name], resource)
        else:
            # New resource
            result[name] = deepcopy(resource)
    
    return list(result.values())


def deep_merge(base: dict, override: dict) -> dict:
    """Deep merge two dictionaries.
    
    For lists: match by _id, merge elements
    For dicts: recursive merge  
    For primitives: override wins (but None doesn't override)
    
    Internal fields (starting with _) are preserved but not merged recursively
    unless they are _id fields used for matching.
    
    Args:
        base: Base dictionary
        override: Override dictionary
        
    Returns:
        Merged dictionary
    """
    result = dict(base)  # Shallow copy
    
    for key, override_val in override.items():
        # Skip internal metadata fields (except we need to keep them)
        # We'll filter them out at the end, not during merge
        
        # Skip None values - preserve base value
        if override_val is None:
            continue
        
        if key not in result:
            # New field - deep copy to avoid shared references
            result[key] = deepcopy(override_val)
        elif isinstance(override_val, list) and isinstance(result[key], list):
            # Merge lists by _id
            result[key] = merge_list_by_id(result[key], override_val)
        elif isinstance(override_val, dict) and isinstance(result[key], dict):
            # Recursive merge for nested dicts
            result[key] = deep_merge(result[key], override_val)
        else:
            # Primitive override
            result[key] = override_val
    
    return result


def merge_list_by_id(base_list: list, override_list: list) -> list:
    """Merge two lists by matching _id fields.
    
    Elements without _id are treated as append-only.
    Supports ordering directives: _after, _before, _position, _first, _last
    
    Algorithm:
    1. Index base elements by _id
    2. Process overrides (merge or delete)
    3. Apply ordering directives
    4. Reconstruct final list
    
    Args:
        base_list: Base list elements
        override_list: Override list elements
        
    Returns:
        Merged list with correct ordering
    """
    # Separate elements with and without _id
    base_by_id: dict[str, dict] = {}
    base_without_id: list = []
    
    for item in base_list:
        if isinstance(item, dict) and "_id" in item:
            base_by_id[item["_id"]] = item
        else:
            base_without_id.append(item)
    
    # Process overrides
    # Start with elements without _id (they keep their relative order)
    result_without_id = list(base_without_id)
    result_by_id = dict(base_by_id)
    
    # Track ordering directives
    ordering_directives: list[tuple[str, str, Any]] = []  # (_id, directive_type, value)
    
    for override_item in override_list:
        if not isinstance(override_item, dict):
            # Primitive in list, append as-is
            result_without_id.append(override_item)
            continue
        
        item_id = override_item.get("_id")
        action = override_item.get("_action")
        
        # Handle ordering directives (only if value is not None)
        if item_id:
            if override_item.get("_after"):
                ordering_directives.append((item_id, "_after", override_item["_after"]))
            if override_item.get("_before"):
                ordering_directives.append((item_id, "_before", override_item["_before"]))
            if override_item.get("_position") is not None:
                ordering_directives.append((item_id, "_position", override_item["_position"]))
            if override_item.get("_first"):
                ordering_directives.append((item_id, "_first", True))
            if override_item.get("_last"):
                ordering_directives.append((item_id, "_last", True))
        
        # Handle merge/delete
        if item_id and item_id in base_by_id:
            # Merge existing element
            if action == "delete":
                result_by_id.pop(item_id, None)
            else:
                base_elem = base_by_id[item_id]
                merged_elem = deep_merge(base_elem, override_item)
                result_by_id[item_id] = merged_elem
        else:
            # New element (no _id or new _id)
            if action != "delete":
                if item_id:
                    result_by_id[item_id] = deepcopy(override_item)
                else:
                    result_without_id.append(deepcopy(override_item))
    
    # Apply ordering directives
    final_order = apply_ordering_directives(
        list(result_by_id.keys()), 
        ordering_directives
    )
    
    # Reconstruct list
    result = []
    for item_id in final_order:
        if item_id in result_by_id:
            result.append(result_by_id[item_id])
    
    # Append elements without _id at the end (or per their own logic)
    result.extend(result_without_id)
    
    return result


def apply_ordering_directives(
    item_ids: list[str],
    directives: list[tuple[str, str, Any]]
) -> list[str]:
    """Apply ordering directives to determine final element order.
    
    Precedence (from spec Section 3.5.4):
    1. delete (already applied)
    2. _position (absolute)
    3. _first / _last
    4. _before / _after
    
    Args:
        item_ids: List of element _ids
        directives: List of (item_id, directive_type, value) tuples
        
    Returns:
        Ordered list of item_ids
    """
    # Create mutable list
    result = list(item_ids)
    
    # Sort directives by precedence
    def directive_priority(d):
        item_id, directive_type, value = d
        precedence = {
            "_position": 1,
            "_first": 2,
            "_last": 2,
            "_before": 3,
            "_after": 3,
        }
        return precedence.get(directive_type, 99)
    
    sorted_directives = sorted(directives, key=directive_priority)
    
    # Apply directives
    for item_id, directive_type, value in sorted_directives:
        if item_id not in result:
            continue  # Item was deleted or doesn't exist
        
        if directive_type == "_position":
            # Absolute position (1-based)
            result.remove(item_id)
            position = min(max(1, value), len(result) + 1) - 1  # Convert to 0-based
            result.insert(position, item_id)
            
        elif directive_type == "_first":
            result.remove(item_id)
            result.insert(0, item_id)
            
        elif directive_type == "_last":
            result.remove(item_id)
            result.append(item_id)
            
        elif directive_type == "_after":
            # Insert after specific element
            if value in result:
                result.remove(item_id)
                after_index = result.index(value)
                result.insert(after_index + 1, item_id)
                
        elif directive_type == "_before":
            # Insert before specific element
            if value in result:
                result.remove(item_id)
                before_index = result.index(value)
                result.insert(before_index, item_id)
    
    return result
