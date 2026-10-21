#!/usr/bin/env python3
"""
Skill Scaffolder for Agents-kit
Generates valid, spec-compliant SKILL.md templates.
"""

import sys
import argparse
from pathlib import Path

SKILL_TEMPLATE = """---
name: {name}
description: {description}
---

# {title}

## Overview
{overview}

## When to Use
- When designing, implementing, or debugging {name}.
- In CI/CD or production verification workflows.

## Core Rules & Guidelines
1. **Rule 1**: Provide explicit constraints and deterministic behavior.
2. **Rule 2**: Enforce error handling and edge case validation.
3. **Rule 3**: Adhere to token efficiency and minimal context footprints.

## Step-by-Step Implementation Workflow
```bash
# Step 1: Initial verification
echo "Running validation for {name}"
```

## Best Practices & Anti-Patterns
- **Do**: Follow standard idiomatic practices.
- **Don't**: Skip automated testing or ignore failure modes.
"""

def scaffold_skill(name: str, domain: str, description: str, base_dir: Path) -> Path:
    domain_dir = base_dir / "skills" / domain
    skill_dir = domain_dir / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_file = skill_dir / "SKILL.md"

    title = name.replace('-', ' ').title()
    content = SKILL_TEMPLATE.format(
        name=name,
        description=description,
        title=title,
        overview=description
    )

    skill_file.write_text(content.strip() + "\n", encoding="utf-8")
    return skill_file

def main():
    parser = argparse.ArgumentParser(description="Scaffold a new skill for Agents-kit")
    parser.add_argument("name", help="Name of the skill in kebab-case (e.g. redis-sentinel-failover)")
    parser.add_argument("--domain", default="engineering-core", help="Target domain folder")
    parser.add_argument("--description", default="Production engineering guidelines and patterns.", help="Skill description")

    args = parser.parse_args()
    kit_dir = Path(__file__).resolve().parent.parent
    file_path = scaffold_skill(args.name, args.domain, args.description, kit_dir)
    print(f"✅ Successfully created skill at: {file_path}")

if __name__ == "__main__":
    main()
