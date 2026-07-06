# Plugin Strategy

## Core decision

Use a hybrid model:

```text
agent-tools       = central marketplace, catalog, documentation, templates
product repo      = MCP server code, product plugin, product skills, product examples
```

This keeps `agent-tools` clean while preserving version alignment between each MCP server and its agent-facing instructions.

## Active plugins

| Plugin | Source repository | Scope |
| --- | --- | --- |
| `kicad-pro` | `oaslananka/kicad-mcp` | Active KiCad MCP workflows for schematic, PCB, DRC/ERC, review, and fabrication automation. |
| `easyeda-pro` | `oaslananka/easyeda-mcp-pro` | Active EasyEDA MCP workflows for project automation, component search, validation, and design assistance. |
| `ssh-mcp-pro` | `oaslananka/ssh-mcp-pro` | Active SSH operations workflows. |
| `infra-lens-mcp` | `oaslananka/infra-lens-mcp` | Active infrastructure visibility workflows. |
| `debug-recorder-mcp` | `oaslananka/debug-recorder-mcp` | Active debug recording workflows. |
| `health-monitor-mcp` | `oaslananka/health-monitor-mcp` | Active health monitoring workflows. |

## Active vs planned plugins

The marketplace file uses two levels:

- `plugins`: installable entries that should work now.
- `planned_plugins`: catalog entries that are intentionally not installable yet.

A planned plugin becomes active only after the source repository contains a valid plugin manifest and tested installation instructions.

## Planned plugin catalog

| Plugin | Source repository | Intended role |
|---|---|---|
| `zaptrace` | `oaslananka/zaptrace` | AI-native EDA operating system and broader electronic design workflows. |
| `a2amesh` | `oaslananka/a2amesh` | Agent-to-agent mesh and CLI agent orchestration workflows. |

## Product repository responsibilities

Each product repository should include:

```text
.claude-plugin/plugin.json
skills/<skill-name>/SKILL.md
examples/agent-workflows/
README.md plugin section
```

The product repository should document:

- How to install the MCP server
- How the agent discovers or launches the MCP server
- Which tools are exposed
- Which workflows are stable
- Which workflows are experimental
- How to validate output
- How to report issues

## Catalog repository responsibilities

This repository should document:

- What tools exist
- What each tool is for
- Which agent runtimes are supported
- How to publish new plugins
- How to structure skills
- Shared templates
- General engineering examples

## Naming rules

Use short, stable, product-oriented names:

- `kicad-pro`
- `easyeda-pro`
- `zaptrace`
- `a2amesh`

Avoid names that encode temporary implementation details, internal branches, or unstable experiments.

## Marketplace quality bar

A plugin should not be activated until it has:

- A valid source repository
- A valid plugin manifest
- Clear installation instructions
- At least one practical example
- A defined support boundary
- A tested install path
- No dependency on private local paths
