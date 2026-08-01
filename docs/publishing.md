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

## Catalog release checklist

Use this checklist for a tagged `agent-tools` catalog release. Product packages,
plugin manifests, and product-specific skills remain owned and released by their
source repositories.

### 1. Validate catalog metadata

Run the same local checks as catalog CI:

```bash
python3 -m json.tool .claude-plugin/marketplace.json >/dev/null
python3 -m json.tool templates/plugin.json >/dev/null
python3 -m json.tool templates/agent-runtime/vscode-mcp.example.json >/dev/null
```

Then run the structural validation embedded in
`.github/workflows/catalog-validation.yml`. Confirm that:

- Active plugin names are unique.
- Every active plugin has a product-owned `.claude-plugin/plugin.json` URL.
- Every active plugin records Claude Code, Codex, VS Code/Copilot, OpenCode,
  and documentation paths.
- No plugin appears in both `plugins` and `planned_plugins`.
- The install and publish-readiness matrices match the marketplace status.

Open a pull request and require Catalog Validation and Dependency Review to pass.
Do not tag directly from an unreviewed working tree.

### 2. Decide whether a planned plugin may become active

Move a product from `planned_plugins` to `plugins` only when all of these are
verified against the product repository's current default branch or release:

- A valid product-owned `.claude-plugin/plugin.json` exists.
- Referenced skills and runtime configuration files exist.
- Installation and support boundaries are documented.
- At least one clean install path and one safe diagnostic workflow pass.
- The catalog records the source pull request and merge commit for activation.
- The entry has no private paths, secrets, unpublished commands, or assumed
  runtime support.

Keep the product planned when any requirement is missing. Record untested
runtimes as untested instead of inferring support from similar products.

### 3. Verify source repository notifications

A product repository should notify this catalog through a focused pull request
when a change affects discovery or installation, including:

- Plugin name, manifest path, or skill path changes.
- Package, executable, or transport command changes.
- Runtime configuration additions or removals.
- Support-boundary, safety-policy, or lifecycle changes.
- Deprecation, archival, rename, or repository transfer.

The product change must merge first. The catalog pull request must link the
product pull request and immutable merge commit. Product implementation details
and release-sensitive instructions stay in the product repository.

### 4. Required checks before tagging

Before creating a catalog tag:

1. Confirm the release commit is on `main` and the working tree is clean.
2. Confirm all required pull request checks passed on the exact merged commit.
3. Re-run Catalog Validation from the release commit.
4. Verify every active manifest URL and documented install command.
5. Confirm planned products remain non-installable catalog entries.
6. Review the install matrix for explicit tested and untested runtime status.
7. Choose the next semantic version and prepare release notes listing active
   plugins, planned plugins, compatibility changes, and known limitations.
8. Create an annotated tag on the verified commit and publish the GitHub release.
9. Re-open the release page and verify the tag, target commit, notes, and assets.

Do not tag when a required check is missing, pending, or failing.

### 5. Roll back incorrect marketplace metadata

Marketplace metadata is corrected through Git history; do not rewrite a public
release tag.

1. Confirm the incorrect entry and its user impact.
2. Create a focused revert or correction branch from current `main`.
3. Move an unsafe or broken entry back to `planned_plugins` when necessary.
4. Update the install and readiness matrices in the same pull request.
5. Run catalog validation and merge only after required checks pass.
6. Publish a patch catalog release that identifies the corrected entry.

If the product itself is unsafe or compromised, follow the product repository's
security process first. Do not publish secrets, exploit details, or private
incident data in the catalog issue or pull request.
