# ChatGPT / OpenAI Apps Remote MCP Plan

The local Claude Code, Codex, VS Code, Cursor, and generic MCP workflows are different from a hosted ChatGPT/OpenAI Apps deployment. This plan defines the extra work required before any product is described as ChatGPT Apps-ready.

## Scope

Applies to active and future product plugins such as:

- `kicad-pro`
- `easyeda-pro`
- `zaptrace`
- `a2amesh`

## Required decisions

- Hosted endpoint owner and domain.
- Transport mode and path layout.
- Authentication model.
- User/session isolation.
- Tool allowlist for read-only, write, export, and remote execution operations.
- Rate limits, abuse limits, and audit logs.
- Privacy and data-retention behavior.
- UI/resources strategy where the app needs visual components.

## Minimum readiness criteria

A product can be called ChatGPT/OpenAI Apps-ready only after:

1. A remote MCP endpoint is deployed.
2. Authentication is configured and documented.
3. The endpoint exposes a minimal safe read-only tool set by default.
4. Write or export operations require explicit approval and product-level safety checks.
5. A smoke test proves the endpoint can initialize, list tools, and call a safe diagnostic tool.
6. Operational logs avoid storing sensitive design contents unless explicitly configured.
7. The product README links to the hosted setup and limitations.

## Recommended phases

### Phase 1 — Remote MCP smoke

- Deploy a read-only remote MCP endpoint.
- Expose diagnostic/status tools only.
- Test initialize, list tools, and one safe read operation.

### Phase 2 — Auth and policy

- Add auth.
- Add rate limiting.
- Add audit logging.
- Define user/session isolation.

### Phase 3 — Product workflows

- Add selected product tools.
- Gate write/export tools.
- Add per-product safety disclaimers.

### Phase 4 — App packaging

- Add app metadata.
- Add UI/resource components only when the workflow benefits from visual interaction.
- Document support boundaries.

## Non-goals

- Do not expose raw execution tools by default.
- Do not expose manufacturing release or write tools without explicit gating.
- Do not claim autonomous engineering sign-off.
