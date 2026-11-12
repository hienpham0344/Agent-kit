"""
MCP Health, Ecosystem Verification and Doctor Diagnostics.
Distinguishes 4 verification levels:
  1. Declared (Present in servers.json)
  2. Binary Available (Executable found in PATH)
  3. Configured (Client configuration / environment variables present)
  4. Verified (Handshake protocol / connectivity test)
"""

import os
import re
import sys
import json
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, List

KIT_DIR = Path(__file__).resolve().parent.parent
MCP_DIR = KIT_DIR / "mcp"
SERVERS_FILE = MCP_DIR / "servers.json"

HARDCODED_PATH_RE = re.compile(r"(/home/[^/\"'\s]+|/Users/[^/\"'\s]+|[A-Za-z]:\\\\Users\\\\[^\\\\\"'\s]+)")
TEMPLATE_VAR_RE = re.compile(r"\$\{([A-Za-z0-9_]+)\}")


def load_servers() -> Dict[str, Any]:
    if not SERVERS_FILE.exists():
        return {}
    with open(SERVERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def check_server_health(name: str, cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Inspect health across 4 levels plus portability and template placeholders."""
    cmd_bin = cfg.get("command", "")
    is_declared = True
    is_binary_available = shutil.which(cmd_bin) is not None
    is_configured = True
    missing_env: List[str] = []

    env_vars = cfg.get("env", {})
    for env_name in env_vars:
        if not os.environ.get(env_name):
            is_configured = False
            missing_env.append(env_name)

    serialized = json.dumps(cfg)
    portability_warnings = [
        f"Hardcoded machine path detected: {match}"
        for match in HARDCODED_PATH_RE.findall(serialized)
    ]
    template_vars = sorted(set(TEMPLATE_VAR_RE.findall(serialized)))

    verified = False
    verification_msg = "Not attempted (requires client handshake)"
    if is_binary_available:
        if cmd_bin == "context-mode":
            try:
                res = subprocess.run(["context-mode", "--help"], capture_output=True, timeout=2)
                if res.returncode == 0:
                    verified = True
                    verification_msg = "CLI responsive (exit 0)"
            except Exception:
                verification_msg = "CLI unresponsive"
        elif is_configured:
            verification_msg = "Ready for client connection"

    return {
        "name": name,
        "declared": is_declared,
        "binary_available": is_binary_available,
        "command": cmd_bin,
        "configured": is_configured,
        "missing_env": missing_env,
        "template_vars": template_vars,
        "portability_warnings": portability_warnings,
        "verified": verified,
        "message": verification_msg,
        "description": cfg.get("description", ""),
    }


def cmd_list(as_json: bool = False):
    servers = load_servers()
    items = [check_server_health(name, cfg) for name, cfg in servers.items()]
    if as_json:
        print(json.dumps({"servers": items}, indent=2))
        return

    print("\n🔌 REGISTERED MCP SERVERS IN AGENTS-KIT")
    print("=" * 70)
    for h in items:
        status = "✅ AVAILABLE" if h["binary_available"] else "⚠️ MISSING BINARY"
        config_status = "CONFIGURED" if h["configured"] else f"MISSING {', '.join(h['missing_env'])}"
        print(f"  • {h['name']:<18} : {status:<18} [{config_status}] ({h['command']})")
        print(f"    Description: {h['description']}")
    print()


def cmd_doctor(as_json: bool = False):
    servers = load_servers()
    items = [check_server_health(name, cfg) for name, cfg in servers.items()]
    portability_issues = [w for h in items for w in h["portability_warnings"]]

    if as_json:
        print(json.dumps({"portability_ok": not portability_issues, "servers": items}, indent=2))
        return

    print("\n🩺 MCP ECOSYSTEM DOCTOR & PROTOCOL READINESS CHECK")
    print("=" * 70)
    for h in items:
        print(f"Server: {h['name']}")
        print("  • Level 1 - Declared in catalog    : ✅ YES")
        print(f"  • Level 2 - Executable in PATH     : {'✅' if h['binary_available'] else '❌'} {h['command']}")
        print(f"  • Level 3 - Environment Configured : {'✅' if h['configured'] else '⚠️ MISSING ENV'} {h['missing_env']}")
        if h["template_vars"]:
            print(f"  • Template Placeholders            : {', '.join('${' + v + '}' for v in h['template_vars'])}")
        for w in h["portability_warnings"]:
            print(f"  • ⚠️ {w}")
        print(f"  • Level 4 - Verified Connectivity  : {h['message']}")
        print()


def cmd_verify(name: str):
    servers = load_servers()
    if name not in servers:
        print(f"❌ Unknown MCP server: {name}")
        sys.exit(1)
    h = check_server_health(name, servers[name])
    print(f"\n🔍 Verifying MCP Server: {name}")
    print(f"  Command    : {h['command']}")
    print(f"  Binary     : {'✅ Found at ' + (shutil.which(h['command']) or '') if h['binary_available'] else '❌ Not in PATH'}")
    print(f"  Configured : {'✅ Valid' if h['configured'] else '⚠️ Missing: ' + str(h['missing_env'])}")
    if h["template_vars"]:
        print(f"  Variables  : {', '.join('${' + v + '}' for v in h['template_vars'])}")
    for w in h["portability_warnings"]:
        print(f"  ⚠️ {w}")
    print(f"  Status     : {h['message']}\n")
    if not h["binary_available"] or h["portability_warnings"]:
        sys.exit(1)


def main():
    args = sys.argv[1:]
    as_json = "--json" in args
    clean_args = [a for a in args if a != "--json"]

    if not clean_args or clean_args[0] == "list":
        cmd_list(as_json=as_json)
    elif clean_args[0] == "doctor":
        cmd_doctor(as_json=as_json)
    elif clean_args[0] == "verify" and len(clean_args) > 1:
        cmd_verify(clean_args[1])
    else:
        print("Usage: python3 mcp_manager.py [list|doctor|verify <server_name>] [--json]")


if __name__ == "__main__":
    main()
