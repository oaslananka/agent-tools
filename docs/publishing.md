# Publishing Guide

Use this checklist when adding a new agent-facing product to the oaslananka agent-tool ecosystem.

## 1. Keep source ownership clear

The product repository owns the product plugin and product skills.

```text
product-repo/
├── .claude-plugin/
│   └── plugin.json
├── skills/
│   └── <workflow>/
│       └── SKILL.md
└── examples/
    └── agent-workflows/
```

The `agent-tools` repository owns discovery, templates, and catalog-level documentation.

## 2. Add the product manifest

Create `.claude-plugin/plugin.json` in the product repository using `templates/plugin.json` as the starting point.

The manifest should define:

- Stable plugin name
- Description
- Version
- Source repository
- MCP server requirements
- Skills included by the product
- Installation notes

## 3. Add product skills

Add product-specific skills beside the product code.

For example:

```text
kicad-mcp/skills/pcb-design/SKILL.md
easyeda-mcp-pro/skills/easyeda-workflow/SKILL.md
```

## 4. Document validation

Every product should explain how to confirm that the agent workflow actually worked.

For EDA tools, this may include:

- Project opens successfully
- Schematic is valid
- PCB rules are checked
- DRC passes or known issues are listed
- Fabrication outputs are generated
- Generated files are reviewable by a human engineer

## 5. Test installation

Before activation in the marketplace:

```bash
# from a clean environment
# install or register the plugin according to the target runtime
# run the smallest supported workflow
# verify outputs
```

Do not publish an active marketplace entry until the install path is tested.

## 6. Activate in marketplace

After the product repository is ready, move the entry from `planned_plugins` to `plugins` inside `.claude-plugin/marketplace.json`.

## 7. Tag releases

Use semantic versions where possible:

```text
v0.1.0  first public bootstrap
v0.2.0  first active plugin entry
v1.0.0  stable public marketplace
```

## 8. Keep docs synchronized

When product behavior changes, update the product repository first. Then update this catalog only if discovery, install instructions, or marketplace metadata changed.
