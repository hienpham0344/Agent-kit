"""
MCP Health, Ecosystem Verification and Doctor Diagnostics.
Distinguishes 4 verification levels:
  1. Declared (Present in servers.json)
  2. Binary Available (Executable found in PATH)
  3. Configured (Client configuration / environment variables present)
  4. Verified (Handshake protocol / connectivity test)
"""

import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, List

KIT_DIR = Path(__file__).resolve().parent.parent
MCP_DIR = KIT_DIR / "mcp"
SERVERS_FILE = MCP_DIR / "servers.json"

def load_servers() -> Dict[str, Any]:
    if not SERVERS_FILE.exists():
        return {}
    with open(SERVERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def check_server_health(name: str, cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Inspect health across 4 levels."""
    cmd_bin = cfg.get("command", "")
    is_declared = True
    is_binary_available = shutil.which(cmd_bin) is not None
    is_configured = True
    missing_env = []

    # Check required environment variables
    env_vars = cfg.get("env", {})
    for env_name, env_val in env_vars.items():
        # check if environment variable is set in os.environ
        var_key = env_name
        if not os.environ.get(var_key):
            is_configured = False
            missing_env.append(var_key)

    # Handshake verification (level 4)
    # Only verify safely without risking external destructive queries
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
        "verified": verified,
        "message": verification_msg,
        "description": cfg.get("description", "")
    }

def cmd_list():
    servers = load_servers()
    print("\n🔌 REGISTERED MCP SERVERS IN AGENTS-KIT")
    print("=" * 70)
    for name, cfg in servers.items():
        h = check_server_health(name, cfg)
        status = "✅ AVAILABLE" if h["binary_available"] else "⚠️ MISSING BINARY"
        config_status = "CONFIGURED" if h["configured"] else f"MISSING {', '.join(h['missing_env'])}"
        print(f"  • {name:<18} : {status:<18} [{config_status}] ({h['command']})")
        print(f"    Description: {h['description']}")
    print()

def cmd_doctor():
    servers = load_servers()
    print("\n🩺 MCP ECOSYSTEM DOCTOR & PROTOCOL READINESS CHECK")
    print("=" * 70)
    for name, cfg in servers.items():
        h = check_server_health(name, cfg)
        print(f"Server: {name}")
        print(f"  • Level 1 - Declared in catalog    : ✅ YES")
        print(f"  • Level 2 - Executable in PATH     : {'✅' if h['binary_available'] else '❌'} {h['command']}")
        print(f"  • Level 3 - Environment Configured : {'✅' if h['configured'] else '⚠️ MISSING ENV'} {h['missing_env']}")
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
    print(f"  Status     : {h['message']}\n")
    if not h["binary_available"]:
        sys.exit(1)

def main():
    if len(sys.argv) < 2 or sys.argv[1] == "list":
        cmd_list()
    elif sys.argv[1] == "doctor":
        cmd_doctor()
    elif sys.argv[1] == "verify" and len(sys.argv) > 2:
        cmd_verify(sys.argv[2])
    else:
        print("Usage: python3 mcp_manager.py [list|doctor|verify <server_name>]")

if __name__ == "__main__":
    main()
