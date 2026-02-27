"""Utility functions for CaC-ConfigMgr.

- YAML serialization/deserialization
- File I/O helpers
- Validation utilities
"""

from .yaml_utils import (
    load_yaml,
    save_yaml,
    load_template,
    load_instance,
    save_template,
    save_instance,
    load_fleet,
    save_fleet,
    load_multi_file_template,
    save_multi_file_template,
    YamlError,
)

__all__ = [
    "load_yaml",
    "save_yaml",
    "load_template",
    "load_instance",
    "save_template",
    "save_instance",
    "load_fleet",
    "save_fleet",
    "load_multi_file_template",
    "save_multi_file_template",
    "YamlError",
]
