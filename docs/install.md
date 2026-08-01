# Installation Guide

This document describes the intended installation model for the oaslananka agent-tool ecosystem.

## Current catalog state

The repository is a catalog and documentation hub with active marketplace entries for products that publish validated product-level manifests, runtime configuration, and tested install paths. Products that have not met that bar remain under `planned_plugins`.

## Marketplace installation

Supported agent runtimes can add this repository as a marketplace source:

```bash
/plugin marketplace add oaslananka/agent-tools
```

After that, users can install individual plugins from the marketplace according to the command syntax supported by their agent runtime.

A2A Mesh also exposes a standalone stdio MCP command through its published npm package:

```bash
npx -y -p @a2amesh/mcp@alpha a2amesh-mcp --transport stdio
```

Use the product repository's `.mcp.json`, Codex, VS Code/Copilot, or OpenCode examples for the required fail-closed environment configuration.

## Product-level installation model

Each product should publish its own plugin and skills inside the product repository:

```text
kicad-mcp/
├── .claude-plugin/
│   └── plugin.json
└── skills/
    ├── pcb-design/
    │   └── SKILL.md
    ├── drc-check/
    │   └── SKILL.md
    ├── fabrication-output/
    │   └── SKILL.md
    └── schematic-review/
        └── SKILL.md
```

```text
easyeda-mcp-pro/
├── .claude-plugin/
│   └── plugin.json
└── skills/
    ├── easyeda-workflow/
    │   └── SKILL.md
    ├── component-search/
    │   └── SKILL.md
    └── design-validation/
        └── SKILL.md
```

## Why product-level manifests matter

Agent instructions often depend on exact MCP tool names, parameters, side effects, constraints, and release behavior. If those instructions are stored in a separate catalog repository, they can drift away from the real implementation.

For that reason, the source repository should own:

- The MCP server code
- The plugin manifest
- Product-specific skills
- Tool-specific examples
- Version-sensitive instructions
- Product-level release notes

This repository should own:

- Discovery
- Shared templates
- Publishing rules
- General examples
- Generic engineering skills
- Compatibility notes

## Activation checklist

Before moving a planned plugin into the active `plugins` list in `.claude-plugin/marketplace.json`, verify:

- The product repository has `.claude-plugin/plugin.json`.
- The plugin name, description, version, and entry points are correct.
- Required MCP server installation steps are documented.
- Skills exist in the product repository when the plugin depends on skills.
- The plugin can be installed by at least one supported agent runtime.
- The README clearly explains the supported workflow.
- There is no broken link from the marketplace entry.
