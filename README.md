# Agent Tools by oaslananka

Engineering, EDA, PCB, and developer-automation tools for AI agents.

This repository is the central catalog, documentation hub, and distribution entry point for agent-facing tools built around MCP servers, plugins, skills, and repeatable engineering workflows.

## Purpose

`agent-tools` is not a monorepo for every MCP server. It is the public hub that helps agents and developers discover the right tool, understand compatibility, copy templates, and install supported plugins once their source repositories contain valid manifests.

Project-specific plugins and skills should live inside their own source repositories so their instructions stay synchronized with the actual tools, commands, schemas, and releases.

```text
agent-tools         = marketplace / catalog / templates / shared docs
kicad-mcp           = KiCad MCP server + KiCad-specific plugin + KiCad skills
easyeda-mcp-pro     = EasyEDA MCP server + EasyEDA-specific plugin + EasyEDA skills
zaptrace            = product repository + product-specific plugin and skills
a2amesh             = product repository + product-specific plugin and skills
```

## Current status

| Tool | Repository | Status | Notes |
|---|---|---:|---|
| KiCad MCP | `oaslananka/kicad-mcp` | Planned | Plugin manifest and project-specific skills should be added in the source repository. |
| EasyEDA MCP Pro | `oaslananka/easyeda-mcp-pro` | Planned | Plugin manifest and EasyEDA workflow skills should be added in the source repository. |
| Zaptrace | `oaslananka/zaptrace` | Future | Should be published as its own product-level plugin when ready. |
| A2A Mesh | `oaslananka/a2amesh` | Future | Should be published as its own multi-agent workflow plugin when ready. |

The marketplace file intentionally does **not** expose active installable plugin entries yet. This prevents broken installs before the product repositories contain their own `.claude-plugin/plugin.json` manifests.

## Recommended repository model

```text
agent-tools/
├── README.md
├── .claude-plugin/
│   └── marketplace.json
├── docs/
│   ├── install.md
│   ├── plugins.md
│   ├── skills.md
│   ├── supported-agents.md
│   └── publishing.md
├── templates/
│   ├── plugin.json
│   ├── SKILL.md
│   └── README-plugin-section.md
├── examples/
│   ├── kicad.md
│   ├── easyeda.md
│   └── multi-agent-eda.md
└── skills/
    └── generic/
        └── pcb-design-principles/
            └── SKILL.md
```

## Install concept

Once product repositories publish valid plugin manifests, this repository can act as the marketplace entry point:

```bash
/plugin marketplace add oaslananka/agent-tools
```

Then individual plugins can be installed from the marketplace according to the agent runtime being used.

Until then, use this repository as the source of truth for templates, publication rules, and shared agent workflow documentation.

## What belongs here

- Marketplace metadata and catalog entries
- Product discovery documentation
- Installation and publishing guides
- Shared plugin and skill templates
- Agent compatibility notes
- Generic, product-independent engineering skills
- Examples for multi-agent engineering workflows

## What does not belong here

- MCP server source code
- Product-specific tool schemas
- KiCad-specific or EasyEDA-specific operational skills
- Release-sensitive tool documentation
- Product-specific tests and fixtures
- Anything that must change in lockstep with a specific MCP server release

## Publication rule

A plugin should only be listed as active in `.claude-plugin/marketplace.json` when its source repository contains a valid `.claude-plugin/plugin.json` file and the plugin has at least one tested installation path.

## Commercial direction

This hub is designed to support a professional agent-tool ecosystem around engineering automation. It can grow into a public catalog for:

- MCP server distribution
- Agent skills for EDA and hardware workflows
- Paid consulting and integration work
- Sponsored workflow examples
- Enterprise-ready installation documentation
- Community contributions around agent-native engineering automation

## Next milestones

1. Add `.claude-plugin/plugin.json` to `oaslananka/kicad-mcp`.
2. Add KiCad-specific skills next to the KiCad MCP source code.
3. Add `.claude-plugin/plugin.json` to `oaslananka/easyeda-mcp-pro`.
4. Add EasyEDA-specific workflow skills next to the EasyEDA MCP source code.
5. Move `kicad-pro` and `easyeda-pro` from planned catalog entries to active marketplace entries.
6. Test plugin installation with supported agent runtimes.
7. Publish a first tagged release of this catalog.
