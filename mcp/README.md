# Model Context Protocol (MCP) Ecosystem for Agents-kit

## Overview
Agents-kit provides pre-configured production manifests for 10 industry-standard MCP servers, enabling autonomous coding agents (Antigravity, Claude Code, Cursor) to interface with external execution environments, databases, browsers, and tracing services.

## Registered MCP Servers

| Server Name | Protocol Command | Category | Purpose |
| :--- | :--- | :--- | :--- |
| **`context-mode`** | `context-mode` | Core Guardrails | Token-saving FTS5 search & isolated bash piping |
| **`filesystem`** | `npx @modelcontextprotocol/server-filesystem` | Core I/O | Scoped secure file inspection |
| **`postgres`** | `npx @modelcontextprotocol/server-postgres` | Database | PostgreSQL schema and query profiling |
| **`sqlite`** | `uvx mcp-server-sqlite` | Database | Local SQLite inspection |
| **`github`** | `npx @modelcontextprotocol/server-github` | DevOps | GitHub PRs, issues, and commit inspection |
| **`puppeteer`** | `npx @modelcontextprotocol/server-puppeteer` | Testing | Headless browser rendering and screenshot diffs |
| **`memory`** | `npx @modelcontextprotocol/server-memory` | AI Memory | Graph-based persistent agent memory |
| **`brave-search`** | `npx @modelcontextprotocol/server-brave-search` | Search | Real-time web retrieval |
| **`docker`** | `uvx mcp-server-docker` | DevOps | Docker container management & logs |
| **`sentry`** | `uvx mcp-server-sentry` | Observability | Production exception & breadcrumb querying |

## Management via CLI
```bash
# List all registered servers and their status
agents-kit mcp

# Verify specific server binary
agents-kit mcp verify context-mode
```
