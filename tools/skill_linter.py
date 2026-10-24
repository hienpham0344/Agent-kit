"""
Skill Quality and Frontmatter Linter.
Verifies all 285 skills against formatting, naming, and security standards:
- Valid YAML frontmatter bounded by ---
- Proper kebab-case naming
- Concise description present (<= 300 chars recommended)
- No unquoted colons breaking YAML parsers
- No dangerous unescaped shell commands or hardcoded secrets
"""

import re
import yaml
from pathlib import Path
from typing import List, Dict, Any

KIT_DIR = Path(__file__).resolve().parent.parent

DANGEROUS_PATTERNS = [
    (re.compile(r"\brm\s+-rf\s+/(?!\w)"), "Dangerous root deletion: rm -rf /"),
    (re.compile(r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:"), "Fork bomb detected"),
    (re.compile(r"\b(AKIA[0-9A-Z]{16})\b"), "Hardcoded AWS Access Key detected")
]

def lint_all_skills(kit_dir: Path = KIT_DIR) -> Dict[str, Any]:
    skills_dir = kit_dir / "skills"
    results = {
        "total_scanned": 0,
        "valid": 0,
        "errors": [],
        "warnings": []
    }

    if not skills_dir.exists():
        results["errors"].append("skills directory does not exist.")
        return results

    for sm in sorted(skills_dir.glob("**/SKILL.md")):
        results["total_scanned"] += 1
        rel_path = str(sm.relative_to(kit_dir))
        content = sm.read_text(encoding="utf-8", errors="ignore")

        # 1. Check Frontmatter presence
        if not content.startswith("---"):
            results["errors"].append(f"{rel_path}: Missing starting '---' YAML frontmatter delimiter.")
            continue

        parts = content.split("---", 2)
        if len(parts) < 3:
            results["errors"].append(f"{rel_path}: Missing closing '---' YAML frontmatter delimiter.")
            continue

        fm_text = parts[1]
        try:
            meta = yaml.safe_load(fm_text)
            if not isinstance(meta, dict):
                results["errors"].append(f"{rel_path}: Frontmatter is not a valid YAML dictionary.")
                continue

            name = meta.get("name")
            desc = meta.get("description")

            if not name:
                results["errors"].append(f"{rel_path}: Missing 'name' in frontmatter.")
            elif not re.match(r"^[a-z0-9-]+$", name):
                results["warnings"].append(f"{rel_path}: Name '{name}' is not strict lowercase kebab-case.")

            if not desc:
                results["errors"].append(f"{rel_path}: Missing 'description' in frontmatter.")
            elif len(desc) > 350:
                results["warnings"].append(f"{rel_path}: Description is very long ({len(desc)} chars). Consider shortening for token efficiency.")

        except yaml.YAMLError as e:
            results["errors"].append(f"{rel_path}: YAML parsing error: {e}")
            continue

        # 2. Check for dangerous patterns
        for pattern, msg in DANGEROUS_PATTERNS:
            if pattern.search(content):
                results["errors"].append(f"{rel_path}: {msg}")

        results["valid"] += 1

    return results

def main():
    print("\n🔍 RUNNING SKILL LINTER & SECURITY AUDIT")
    print("=" * 65)
    r = lint_all_skills()
    print(f"Total skills scanned : {r['total_scanned']}")
    print(f"Valid skills         : {r['valid']}")
    print(f"Errors found         : {len(r['errors'])}")
    print(f"Warnings found       : {len(r['warnings'])}")

    if r["errors"]:
        print("\n❌ Errors:")
        for e in r["errors"]:
            print(f"  • {e}")
    if r["warnings"]:
        print(f"\n⚠️ Top Warnings ({len(r['warnings'])}):")
        for w in r["warnings"][:5]:
            print(f"  • {w}")

    if not r["errors"]:
        print("\n🎉 ALL SKILLS PASSED QUALITY & SECURITY LINTING!\n")

if __name__ == "__main__":
    main()
