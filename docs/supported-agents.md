# Supported Agents

This repository is designed to support agent runtimes that can consume MCP servers, plugins, skills, or repository-level instructions.

## Target runtimes

| Runtime | Intended support level | Notes |
|---|---:|---|
| Claude Code | Primary | Marketplace, plugin, and `SKILL.md` style distribution should be prioritized. |
| GitHub Copilot coding agents | Secondary | Repository instructions and workflow documentation should be kept clear and copyable. |
| Codex CLI-style agents | Secondary | CLI-first examples should be documented where possible. |
| Cursor-style agents | Secondary | Repo-level documentation and MCP setup notes should be useful. |
| Generic MCP clients | Primary for MCP servers | Each product repository should document its own MCP server installation and launch flow. |

## Compatibility principles

- Keep examples CLI-friendly.
- Avoid private absolute paths in public docs.
- Separate stable workflows from experimental workflows.
- Keep product-specific instructions inside the product repository.
- Use clear names for tools, skills, and plugin entries.
- Document expected inputs and outputs.
- Prefer validation steps over blind generation.

## Agent-facing documentation style

Agent-facing docs should be more explicit than human-only docs. They should include:

- Preconditions
- Exact command examples
- Expected outputs
- Validation steps
- Known failure modes
- Safe fallback behavior

## Repository-level compatibility

This hub should remain useful even for agents that do not support a plugin marketplace. For that reason, every important workflow should also be documented in Markdown.
