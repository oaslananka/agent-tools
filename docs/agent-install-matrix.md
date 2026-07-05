# Agent Install Matrix

This matrix documents how the active oaslananka agent-tool plugins should be connected from popular MCP-capable agent runtimes.

## Active products

| Product plugin | Source repo | Claude Code | Codex CLI | VS Code / GitHub Copilot | Generic MCP clients |
| --- | --- | --- | --- | --- | --- |
| `kicad-pro` | `oaslananka/kicad-mcp` | `.claude-plugin/plugin.json` + `.mcp.json` | `.codex/config.example.toml` | `.vscode/mcp.example.json` | `uvx kicad-mcp-pro --transport stdio` |
| `easyeda-pro` | `oaslananka/easyeda-mcp-pro` | `.claude-plugin/plugin.json` + `.mcp.json` | `.codex/config.example.toml` | `.vscode/mcp.example.json` | `npx easyeda-mcp-pro` |

## Claude Code

Each active product repository owns its Claude Code plugin manifest and project-local MCP configuration:

```text
.claude-plugin/plugin.json
.mcp.json
skills/<skill-name>/SKILL.md
```

Validation command from the product repository root:

```bash
claude plugin validate .
```

One-session local test:

```bash
claude --plugin-dir .
```

## Codex CLI

Each active product repository includes a Codex MCP example:

```text
.codex/config.example.toml
```

Copy the product's `[[mcp_servers]]` block into your local Codex config and adjust environment variables as needed.

## VS Code / GitHub Copilot

Each active product repository includes a VS Code workspace MCP example:

```text
.vscode/mcp.example.json
```

Copy the relevant `servers` entry into your workspace or user MCP configuration. Keep write-capable tools behind the product's own approval, profile, or scope boundaries.

## Cursor, Gemini CLI, and other MCP clients

Most MCP-capable runtimes can use the product server's stdio command directly:

```bash
uvx kicad-mcp-pro --transport stdio
npx easyeda-mcp-pro
```

Clients that support HTTP or remote MCP should use the product documentation for transport-specific security, auth, and deployment requirements.

## ChatGPT / OpenAI Apps readiness

The active repositories are MCP-oriented, but ChatGPT/OpenAI Apps distribution requires additional remote-server work:

- Public or controlled remote MCP endpoint.
- Authentication and authorization model.
- Hosted deployment target.
- Tool safety policy and write-operation approval model.
- App metadata and UI/resource strategy where applicable.
- Operational logging, rate limiting, and privacy review.

Track this separately from Claude Code and local MCP packaging. Do not mark a product as ChatGPT Apps-ready until the hosted endpoint and auth flow are tested.

## Release checklist

Before marking a product as active in this catalog:

1. Product repo has `.claude-plugin/plugin.json`.
2. Product repo passes `claude plugin validate .`.
3. Product repo has `.mcp.json` for Claude Code project-local MCP discovery.
4. Product repo has `.codex/config.example.toml`.
5. Product repo has `.vscode/mcp.example.json`.
6. Product repo documents runtime-specific setup and validation.
7. Product repo exposes only real MCP tools and valid skill paths.
8. This catalog points to the product repo as the source of truth.
