"""Variable interpolation - Substitute {{variables}} in resolved config.

Based on Section 5.3 of 20-TEMPLATE-HIERARCHY.md specification.
"""

from __future__ import annotations

import re
from typing import Any


class InterpolationError(Exception):
    """Error during variable interpolation."""
    pass


class VariableNotFoundError(InterpolationError):
    """Referenced variable not found in vars."""
    pass


class Interpolator:
    """Interpolator for template variables.
    
    Variables are defined in template spec.vars and can be referenced
    anywhere in the configuration using {{variable_name}} syntax.
    
    Example:
        spec:
          vars:
            retention: 90
            mount_path: /opt/immune/storage
          repos:
            - name: repo-default
              hiddenrepopath:
                - path: "{{mount_path}}"
                  retention: "{{retention}}"
    """
    
    # Pattern to match {{variable_name}}
    VARIABLE_PATTERN = re.compile(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}")
    
    def __init__(self, variables: dict[str, Any]):
        """Initialize interpolator with variables.
        
        Args:
            variables: Dictionary of variable names to values
        """
        self.variables = variables
    
    def interpolate(self, obj: Any) -> Any:
        """Recursively interpolate variables in an object.
        
        Args:
            obj: Object to interpolate (dict, list, str, or primitive)
            
        Returns:
            Object with all variables substituted
            
        Raises:
            VariableNotFoundError: If a referenced variable doesn't exist
        """
        if isinstance(obj, dict):
            return self._interpolate_dict(obj)
        elif isinstance(obj, list):
            return self._interpolate_list(obj)
        elif isinstance(obj, str):
            return self._interpolate_string(obj)
        else:
            # Primitive (int, float, bool, None) - no interpolation
            return obj
    
    def _interpolate_dict(self, obj: dict) -> dict:
        """Interpolate all values in a dictionary."""
        result = {}
        for key, value in obj.items():
            # Don't interpolate _id fields or other internal fields
            if key.startswith("_") and key != "_action":
                result[key] = value
            else:
                result[key] = self.interpolate(value)
        return result
    
    def _interpolate_list(self, obj: list) -> list:
        """Interpolate all items in a list."""
        return [self.interpolate(item) for item in obj]
    
    def _interpolate_string(self, obj: str) -> str | int | float | bool:
        """Interpolate variables in a string.
        
        If the entire string is a single variable reference,
        return the typed value directly (preserving int, bool, etc.)
        
        Otherwise, substitute within the string and return string.
        
        Examples:
            "{{retention}}" -> 90 (int)
            "{{enabled}}" -> True (bool)
            "Path: {{mount_path}}" -> "Path: /opt/immune/storage" (str)
        """
        # Check if entire string is a single variable
        match = self.VARIABLE_PATTERN.fullmatch(obj)
        if match:
            var_name = match.group(1)
            return self._get_variable(var_name)
        
        # Multiple variables or mixed content - substitute in string
        def replace_var(match: re.Match) -> str:
            var_name = match.group(1)
            value = self._get_variable(var_name)
            # Convert to string for substitution
            return str(value)
        
        return self.VARIABLE_PATTERN.sub(replace_var, obj)
    
    def _get_variable(self, name: str) -> Any:
        """Get variable value by name.
        
        Args:
            name: Variable name
            
        Returns:
            Variable value
            
        Raises:
            VariableNotFoundError: If variable not defined
        """
        if name not in self.variables:
            raise VariableNotFoundError(
                f"Variable '{{{name}}}' not found. "
                f"Available variables: {list(self.variables.keys())}"
            )
        return self.variables[name]
    
    @staticmethod
    def extract_variables(obj: Any) -> set[str]:
        """Extract all variable names referenced in an object.
        
        Useful for validating that all referenced variables are defined.
        
        Args:
            obj: Object to scan for variables
            
        Returns:
            Set of variable names
        """
        variables = set()
        
        if isinstance(obj, dict):
            for value in obj.values():
                variables.update(Interpolator.extract_variables(value))
        elif isinstance(obj, list):
            for item in obj:
                variables.update(Interpolator.extract_variables(item))
        elif isinstance(obj, str):
            for match in Interpolator.VARIABLE_PATTERN.finditer(obj):
                variables.add(match.group(1))
        
        return variables


def merge_variables(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Merge two variable dictionaries.
    
    Override variables take precedence. Shallow merge (not recursive).
    
    Args:
        base: Base variables from parent template
        override: Override variables from child template
        
    Returns:
        Merged variables dictionary
    """
    result = dict(base)
    result.update(override)
    return result


def collect_variables_from_chain(chain: list) -> dict[str, Any]:
    """Collect all variables from a template chain.
    
    Variables are merged from root to leaf, with leaf values taking precedence.
    
    Args:
        chain: List of templates from root to leaf
        
    Returns:
        Merged variables dictionary
    """
    result = {}
    for template in chain:
        if hasattr(template, "spec") and hasattr(template.spec, "vars"):
            result = merge_variables(result, template.spec.vars)
    return result
