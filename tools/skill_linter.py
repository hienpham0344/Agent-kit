"""
Skill Quality and Frontmatter Linter.
Verifies all skills against formatting, naming, reference integrity, and security standards:
- Valid YAML frontmatter bounded by --- (works with or without PyYAML installed)
- Proper lowercase kebab/snake naming without path characters
- Concise description present (<= 350 chars recommended)
- No duplicate top-level skill names
- No broken internal relative links (references/, scripts/, docs/references/)
- No dangerous unescaped shell commands, remote shell pipes, or hardcoded secrets
"""

import re
import sys
from pathlib import Path
from typing import Dict, Any, Set

KIT_DIR = Path(__file__).resolve().parent.parent
if str(KIT_DIR) not in sys.path:
    sys.path.insert(0, str(KIT_DIR))

from core.registry import parse_frontmatter

DANGEROUS_PATTERNS = [
    (re.compile(r"\brm\s+-rf\s+/(?!\w)"), "Dangerous root deletion: rm -rf /"),
    (re.compile(r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:"), "Fork bomb detected"),
    (re.compile(r"\b(AKIA[0-9A-Z]{16})\b"), "Hardcoded AWS Access Key detected"),
    (re.compile(r"\b(?:curl|wget)\b[^\n`|]*\|\s*(?:ba)?sh\b"), "Suspicious remote pipe execution (curl/wget | sh)"),
]

BACKTICK_REF_RE = re.compile(
    r"`((?:references|reference|scripts|docs/references)/[^`\s]+\.(?:md|py|sh|json|toml|yaml|yml|ts|js))`"
)
MD_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)#\s]+)\)")


def _resolve_ref_target(rel_ref: str, skill_md: Path, kit_dir: Path) -> Path:
    if rel_ref.startswith("docs/references/"):
        return kit_dir / rel_ref.removeprefix("docs/")
    return skill_md.parent / rel_ref


def lint_all_skills(kit_dir: Path = KIT_DIR) -> Dict[str, Any]:
    skills_dir = kit_dir / "skills"
    results: Dict[str, Any] = {
        "total_scanned": 0,
        "valid": 0,
        "errors": [],
        "warnings": [],
    }

    if not skills_dir.exists():
        results["errors"].append("skills directory does not exist.")
        return results

    seen_top_level_names: Dict[str, str] = {}
    top_level_files: Set[Path] = set(skills_dir.glob("*/*/SKILL.md"))

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
            meta = parse_frontmatter(fm_text)
            if not isinstance(meta, dict):
                results["errors"].append(f"{rel_path}: Frontmatter is not a valid YAML dictionary.")
                continue

            name = str(meta.get("name") or "").strip()
            desc = str(meta.get("description") or "").strip()

            if not name:
                results["errors"].append(f"{rel_path}: Missing 'name' in frontmatter.")
            else:
                if not re.match(r"^[a-z0-9_-]+$", name):
                    results["warnings"].append(
                        f"{rel_path}: Name '{name}' contains non-lowercase or special characters."
                    )
                if sm in top_level_files:
                    if name in seen_top_level_names:
                        results["errors"].append(
                            f"{rel_path}: Duplicate top-level skill name '{name}' (already defined in {seen_top_level_names[name]})."
                        )
                    else:
                        seen_top_level_names[name] = rel_path

            if not desc:
                results["errors"].append(f"{rel_path}: Missing 'description' in frontmatter.")
            elif len(desc) > 350:
                results["warnings"].append(
                    f"{rel_path}: Description is very long ({len(desc)} chars). Consider shortening for token efficiency."
                )

        except Exception as e:
            results["errors"].append(f"{rel_path}: Frontmatter parsing error: {e}")
            continue

        # 2. Check for dangerous patterns
        for pattern, msg in DANGEROUS_PATTERNS:
            if pattern.search(content):
                results["errors"].append(f"{rel_path}: {msg}")

        # 3. Check broken internal relative file references
        for ref in BACKTICK_REF_RE.findall(content):
            if any(ch in ref for ch in ("*", "{", "<", "$")):
                continue
            target = _resolve_ref_target(ref, sm, kit_dir)
            if not target.exists():
                results["errors"].append(f"{rel_path}: Broken internal file reference `{ref}`.")

        for link in MD_LINK_RE.findall(content):
            if link.startswith(("http://", "https://", "mailto:")):
                continue
            if any(link.startswith(p) for p in ("references/", "reference/", "scripts/", "docs/references/")):
                if any(ch in link for ch in ("*", "{", "<", "$")):
                    continue
                target = _resolve_ref_target(link, sm, kit_dir)
                if not target.exists():
                    results["errors"].append(f"{rel_path}: Broken markdown link `{link}`.")

        results["valid"] += 1

    return results


def main() -> None:
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
        for w in r["warnings"][:10]:
            print(f"  • {w}")

    if r["errors"]:
        sys.exit(1)

    print("\n🎉 ALL SKILLS PASSED QUALITY & SECURITY LINTING!\n")


if __name__ == "__main__":
    main()
