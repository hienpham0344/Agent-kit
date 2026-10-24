"""
Managed Installation Manifest Manager.
Tracks files and skills installed by agents-kit so sync and uninstall do not destroy user modifications.
"""

import json
import hashlib
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import List, Dict, Optional, Any

MANIFEST_FILENAME = "agents-kit.manifest.json"

@dataclass
class InstallationManifest:
    version: str = "4.3.0"
    preset: str = "auto"
    mode: str = "symlink"
    categories: List[str] = field(default_factory=list)
    installed_skills: List[str] = field(default_factory=list)
    managed_files: Dict[str, str] = field(default_factory=dict) # rel_path -> sha256 hash
    timestamp: str = ""

def calculate_file_hash(path: Path) -> str:
    """Calculate sha256 checksum of a file."""
    if not path.exists() or path.is_dir() or path.is_symlink():
        return ""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

class ManifestManager:
    def __init__(self, target_dir: Path):
        self.target_dir = target_dir.resolve()
        self.manifest_path = self.target_dir / ".agents" / MANIFEST_FILENAME

    def exists(self) -> bool:
        return self.manifest_path.exists()

    def load_manifest(self) -> Optional[InstallationManifest]:
        if not self.exists():
            return None
        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return InstallationManifest(
                version=data.get("version", "4.3.0"),
                preset=data.get("preset", "auto"),
                mode=data.get("mode", "symlink"),
                categories=data.get("categories", []),
                installed_skills=data.get("installed_skills", []),
                managed_files=data.get("managed_files", {})
            )
        except Exception:
            return None

    def save_manifest(
        self,
        preset: str,
        mode: str,
        categories: List[str],
        installed_skills: List[str],
        managed_files: Any,
        version: str = "4.3.0"
    ):
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_hashes: Dict[str, str] = {}
        if isinstance(managed_files, list):
            for rel in managed_files:
                p = self.target_dir / rel
                file_hashes[rel] = calculate_file_hash(p)
        elif isinstance(managed_files, dict):
            file_hashes = managed_files

        import datetime
        now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
        manifest = InstallationManifest(
            version=version,
            preset=preset,
            mode=mode,
            categories=categories,
            installed_skills=installed_skills,
            managed_files=file_hashes,
            timestamp=now_utc
        )

        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(asdict(manifest), f, indent=2, ensure_ascii=False)
