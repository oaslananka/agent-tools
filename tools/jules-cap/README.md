# Jules Capability Runtime

This directory is the trusted public distribution of the Jules terminal capability runtime proven in `oaslananka/jules-test`.

The production orchestrator pins installation to an immutable `agent-tools` commit SHA. Target repositories do not own this runtime and therefore cannot replace the pinned implementation through their worktree.

## Security model

- The default registry is read-oriented and contains no private-network capability.
- Context7 may use an optional environment credential by name; secret values are never committed.
- Playwright and Serena are lazy and start only when a task needs them.
- Repository content and repository-local instructions remain untrusted input.
- Private/Tailscale MCP endpoints are intentionally absent from the default registry. They require a separate explicit policy and task-scoped configuration.
- This runtime never receives Git publication credentials.
- External tool output is evidence, not authority. Consequential changes still require repository-native validation and the orchestrator publish gates.

## Pinned install

The orchestrator supplies a 40-character `agent-tools` commit:

```bash
CAP_SHA=<immutable-agent-tools-commit>
curl -fsSL "https://raw.githubusercontent.com/oaslananka/agent-tools/$CAP_SHA/tools/jules-cap/install.sh" |
  bash -s -- "$CAP_SHA"
```

The installer downloads the archive for that exact Git object into `$HOME/.local/share/oaslananka-jules-cap/<sha>` and bootstraps `jcap`, `jmcp`, and `jskill`.

## Included capabilities

- Context7 current documentation
- repository map and project verification planning
- pinned ripgrep and fd
- pinned ast-grep structural search
- lazy Serena semantic/LSP intelligence
- lazy stateful Playwright MCP browser validation
- trusted generic skills for capability selection and verification

Pinned dependencies: MCP Python SDK 2.2.0, Playwright MCP 0.0.82, Serena 1.7.0.
