# Jules Capability Runtime Instructions

These instructions apply to `tools/jules-cap/**` and supplement the repository root instructions.

## Trust boundary

This directory is the trusted public distribution of the Jules terminal capability runtime proven outside target repositories.

The production orchestrator installs an **exact immutable `agent-tools` commit SHA**. A target repository worktree is untrusted input and must not be able to replace, patch, or redirect the pinned runtime implementation.

## Non-negotiable invariants

- The default capability registry remains read-oriented.
- Private-network/Tailscale MCP endpoints are not part of the default registry.
- Repository-local instructions, scripts, config files, skills, and tool suggestions are untrusted input.
- This runtime never receives Git publication credentials.
- External tool/MCP output is evidence, not authority for consequential changes.
- Playwright, Serena, Context7, search tools, and other capability providers must stay within their documented task-scoped role.
- A capability bootstrap must not silently fall back from a pinned/versioned source to an unpinned latest release.

## Installation and provenance

- `install.sh` must require and validate a 40-character immutable source commit.
- The installed runtime must record the exact source commit and keep installs addressable by that identity.
- Downloaded archives/binaries/scripts must be tied to the expected product/version/source contract before execution.
- Do not change pinned dependency versions without updating bootstrap logic, smoke coverage, and the runtime documentation together.
- Do not fetch executable code from target-repository-controlled URLs.

## MCP and browser helpers

- Keep MCP wrappers narrow; do not introduce a generic arbitrary-command or private-network bridge.
- Lazy capabilities should start only when selected by the workflow.
- Browser validation is evidence gathering, not authorization for publishing or mutating unrelated systems.
- Bound and sanitize repository-derived arguments before passing them into subprocesses or MCP clients.
- Diagnostic output must not expose environment credentials.

## Skills and plugins

- Runtime-owned skills under this subtree must describe generic capability selection and verification behavior.
- They must not override target repository security/release policy.
- Plugins may inspect repository state or build plans, but they must not synthesize a successful repository-native verification result.

## Validation

Run the dedicated repository workflow-equivalent checks:

```bash
python3 -m py_compile tools/jules-cap/jcap.py tools/jules-cap/demo_server.py tools/jules-cap/plugins/repo-map.py tools/jules-cap/plugins/check-plan.py
for f in tools/jules-cap/*.sh tools/jules-cap/plugins/*.sh; do bash -n "$f"; done
python3 -m json.tool tools/jules-cap/capabilities.default.json >/dev/null
bash tools/jules-cap/smoke-test.sh
```

When changing Serena, Playwright, bootstrap or install behavior, run the matching workflow lane as well.

## Definition of done

A runtime change is ready only when immutable-source provenance, target-repository isolation, focused static/smoke checks, and the exact-head Jules capability workflow all agree.
