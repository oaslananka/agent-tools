# Publish Readiness Matrix

This matrix tracks publish and agent-runtime readiness for active MCP products in the `agent-tools` catalog.

| Product | Source repo | Agent plugin | Runtime configs | npm/PyPI | GHCR | MCP Registry | Repo-specific policy | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `kicad-pro` | `oaslananka/kicad-mcp` | Yes | Claude, Codex, VS Code/Copilot, OpenCode | npm + PyPI | Yes | Yes | KiCad CI/release gates | Active |
| `easyeda-pro` | `oaslananka/easyeda-mcp-pro` | Yes | Claude, Codex, VS Code/Copilot, OpenCode | npm | Yes | Yes | EasyEDA metadata gates | Active |
| `ssh-mcp-pro` | `oaslananka/ssh-mcp-pro` | Yes | Claude, Codex, VS Code/Copilot, OpenCode | npm | Yes | Yes | SSH safety policy in PR #15 | Active, safety PR pending |
| `infra-lens-mcp` | `oaslananka/infra-lens-mcp` | Yes | Claude, Codex, VS Code/Copilot, OpenCode | npm | PR #76 | Yes | Schema export policy in PR #76 | Active, GHCR/policy PR pending |
| `debug-recorder-mcp` | `oaslananka/debug-recorder-mcp` | Yes | Claude, Codex, VS Code/Copilot, OpenCode | npm | PR #57 | PR #57 | Privacy fixture scan in PR #57 | Active, review required |
| `health-monitor-mcp` | `oaslananka/health-monitor-mcp` | Yes | Claude, Codex, VS Code/Copilot, OpenCode | npm | PR #70 | Yes | Monitoring contract policy in PR #70 | Active, GHCR/policy PR pending |

## Standard publish chain

1. Pull request quality gates pass.
2. Runtime config validation passes.
3. Release Please creates the release PR and GitHub Release.
4. npm or PyPI package is published and verified.
5. GHCR image is published when the repo contains a Dockerfile.
6. MCP Registry publish runs after package visibility checks.
7. `agent-tools` catalog remains the discovery/readiness layer.

## Required checks for new MCP products

- `.claude-plugin/plugin.json`
- `skills/<name>/SKILL.md`
- `.opencode/skills/<name>/SKILL.md`
- `.mcp.json`
- `.codex/config.example.toml`
- `.vscode/mcp.example.json`
- `opencode.example.jsonc`
- `docs/agent-runtime-config.md`
- `server.json`
- `publish-mcp-registry.yml`
- `publish-ghcr.yml` when a Dockerfile exists
- repo-specific safety or contract workflow
