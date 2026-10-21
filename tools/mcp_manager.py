#!/usr/bin/env python3
"""
MCP Ecosystem Manager for Agents-kit
Manages, tests, and configures Model Context Protocol (MCP) servers.
"""

import json
import sys
import shutil
import subprocess
from pathlib import Path

KIT_DIR = Path(__file__).resolve().parent.parent
MCP_DIR = KIT_DIR / "mcp"
SERVERS_FILE = MCP_DIR / "servers.json"

def load_servers():
    if not SERVERS_FILE.exists():
        return {}
    with open(SERVERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def cmd_list():
    servers = load_servers()
    print("\n🔌 REGISTERED MCP SERVERS IN AGENTS-KIT")
    print("=" * 65)
    for name, cfg in servers.items():
        cmd_bin = cfg.get("command", "")
        installed = shutil.which(cmd_bin) is not None
        status = "✅ AVAILABLE" if installed else "⚠️ NOT INSTALLED"
        print(f"  • {name:<18} : {status:<15} ({cmd_bin})")
        print(f"    Description: {cfg.get('description', 'No description')}")
    print()

def cmd_verify(name: str):
    servers = load_servers()
    if name not in servers:
        print(f"❌ Unknown server: {name}")
        return
    cfg = servers[name]
    cmd_bin = cfg.get("command", "")
    if shutil.which(cmd_bin):
        print(f"✅ Executable for '{name}' found at: {shutil.which(cmd_bin)}")
    else:
        print(f"❌ Executable '{cmd_bin}' not found in PATH.")

def main():
    if len(sys.argv) < 2 or sys.argv[1] == "list":
        cmd_list()
    elif sys.argv[1] == "verify" and len(sys.argv) > 2:
        cmd_verify(sys.argv[2])
    else:
        print("Usage: python3 mcp_manager.py [list|verify <server_name>]")

if __name__ == "__main__":
    main()
