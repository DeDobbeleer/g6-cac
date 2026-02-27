"""Core business logic.

- Template resolution (inheritance chain)
- Resource merging (deep merge with _id matching)
- Variable interpolation
- Validation engine
"""

from .resolver import (
    TemplateResolver,
    TemplateResolutionError,
    CircularDependencyError,
    TemplateNotFoundError,
)

from .merger import (
    merge_resources,
    deep_merge,
    merge_list_by_id,
    apply_ordering_directives,
    MergeError,
)

from .interpolator import (
    Interpolator,
    InterpolationError,
    VariableNotFoundError,
    merge_variables,
    collect_variables_from_chain,
)

from .engine import (
    ResolutionEngine,
    ResolvedConfiguration,
    filter_internal_ids,
)

from .validator import (
    ConsistencyValidator,
    ValidationError,
    validate_resources,
)

from .logpoint_dependencies import (
    LogPointDependencyValidator,
    DependencyError,
    validate_dependencies,
    ResourceType,
)

__all__ = [
    # Resolver
    "TemplateResolver",
    "TemplateResolutionError",
    "CircularDependencyError",
    "TemplateNotFoundError",
    # Merger
    "merge_resources",
    "deep_merge",
    "merge_list_by_id",
    "apply_ordering_directives",
    "MergeError",
    # Interpolator
    "Interpolator",
    "InterpolationError",
    "VariableNotFoundError",
    "merge_variables",
    "collect_variables_from_chain",
    # Engine
    "ResolutionEngine",
    "ResolvedConfiguration",
    "filter_internal_ids",
    # Cross-resource Validator
    "ConsistencyValidator",
    "ValidationError",
    "validate_resources",
    # LogPoint Dependency Validator
    "LogPointDependencyValidator",
    "DependencyError",
    "validate_dependencies",
    "ResourceType",
]
