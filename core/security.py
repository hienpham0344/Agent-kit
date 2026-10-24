"""
Security validation module for file operations, skill names, and symlink isolation.
Protects against path traversal (../, absolute paths) and destructive directory collisions.
"""

import os
import re
from pathlib import Path

VALID_SKILL_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")

def validate_skill_name(name: str) -> str:
    """Validate skill name format to prevent path traversal and shell injection."""
    name = name.strip()
    if not name:
        raise ValueError("Skill name cannot be empty.")
    if "/" in name or "\\" in name or ".." in name:
        raise ValueError(f"Security error: Invalid skill name containing path separators: '{name}'")
    if not VALID_SKILL_NAME_PATTERN.match(name):
        raise ValueError(f"Security error: Skill name '{name}' contains invalid characters. Use letters, numbers, hyphens, and underscores only.")
    return name

def validate_safe_destination(base_dir: Path, target_path: Path) -> Path:
    """Ensure target_path does not escape base_dir boundary."""
    resolved_base = base_dir.resolve()
    resolved_target = target_path.resolve()

    try:
        resolved_target.relative_to(resolved_base)
    except ValueError:
        raise ValueError(f"Security error: Destination path '{resolved_target}' escapes base directory '{resolved_base}'.")

    return resolved_target
