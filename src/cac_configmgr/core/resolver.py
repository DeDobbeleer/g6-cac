"""Template resolution - Build inheritance chain from leaf to root.

Based on Section 5.1 of 20-TEMPLATE-HIERARCHY.md specification.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..models.template import ConfigTemplate, TopologyInstance, TemplateChain


class TemplateResolutionError(Exception):
    """Error during template resolution."""
    pass


class CircularDependencyError(TemplateResolutionError):
    """Circular dependency detected in inheritance chain."""
    pass


class TemplateNotFoundError(TemplateResolutionError):
    """Referenced template not found."""
    pass


class TemplateResolver:
    """Resolver for building template inheritance chains.
    
    The resolver loads templates from the filesystem and builds
    the complete inheritance chain from leaf (instance) to root
    (golden template without parent).
    
    Example chain:
        instances/client-bank/prod  (TopologyInstance - leaf)
        └── mssp/acme-corp/profiles/enterprise  (ConfigTemplate)
            └── mssp/acme-corp/base  (ConfigTemplate)
                └── logpoint/golden-base  (ConfigTemplate - root)
    """
    
    def __init__(self, templates_dir: Path):
        """Initialize resolver with templates directory.
        
        Args:
            templates_dir: Root directory containing all templates
        """
        self.templates_dir = templates_dir
        self._cache: dict[str, ConfigTemplate | TopologyInstance] = {}
        self._max_depth = 10  # Prevent infinite recursion
    
    def resolve(self, instance: TopologyInstance) -> TemplateChain:
        """Resolve complete inheritance chain for an instance.
        
        Args:
            instance: The topology instance (Level 4 - leaf)
            
        Returns:
            TemplateChain with all templates from root to leaf
            
        Raises:
            CircularDependencyError: If circular reference detected
            TemplateNotFoundError: If parent template not found
            TemplateResolutionError: Other resolution errors
        """
        from ..models.template import TemplateChain
        
        chain = []
        seen = set()  # Track visited templates to detect cycles
        current = instance
        depth = 0
        
        while current is not None:
            # Check for circular dependency
            template_id = self._get_template_id(current)
            if template_id in seen:
                raise CircularDependencyError(
                    f"Circular dependency detected: {template_id} already in chain"
                )
            seen.add(template_id)
            
            # Check depth limit
            depth += 1
            if depth > self._max_depth:
                raise TemplateResolutionError(
                    f"Maximum inheritance depth ({self._max_depth}) exceeded"
                )
            
            # Add to chain (we'll reverse at the end)
            chain.append(current)
            
            # Get parent
            parent_ref = self._get_parent_ref(current)
            if parent_ref is None:
                break  # Root template reached
            
            # Load parent template
            current = self._load_template(parent_ref)
        
        # Reverse to get root-to-leaf order
        chain.reverse()
        
        return TemplateChain(templates=chain)
    
    def _get_template_id(self, template: ConfigTemplate | TopologyInstance) -> str:
        """Get unique identifier for a template."""
        return template.metadata.name
    
    def _get_parent_ref(self, template: ConfigTemplate | TopologyInstance) -> str | None:
        """Get parent template reference."""
        extends = template.metadata.extends
        if extends is None:
            return None
        
        # Remove version suffix if present
        return extends.split("@")[0]
    
    def _load_template(self, ref: str) -> ConfigTemplate:
        """Load template by reference.
        
        Args:
            ref: Template reference (e.g., "logpoint/golden-base")
            
        Returns:
            Loaded ConfigTemplate
            
        Raises:
            TemplateNotFoundError: If template not found
        """
        # Check cache first
        if ref in self._cache:
            return self._cache[ref]
        
        # Convert ref to path
        # "logpoint/golden-base" -> templates/logpoint/golden-base/
        template_path = self.templates_dir / ref.replace("/", "/")
        
        # Look for template files (multi-file structure)
        # In a real implementation, we'd load and merge all files
        # For now, just check existence
        if not template_path.exists():
            raise TemplateNotFoundError(f"Template not found: {ref} (looked in {template_path})")
        
        # TODO: Load actual template from YAML files
        # This would involve:
        # 1. Find all .yaml files in template_path
        # 2. Parse each file
        # 3. Merge files with same metadata.name
        # 4. Return ConfigTemplate
        
        raise NotImplementedError(
            f"Template loading not fully implemented. Would load from: {template_path}"
        )
    
    def clear_cache(self) -> None:
        """Clear template cache."""
        self._cache.clear()
