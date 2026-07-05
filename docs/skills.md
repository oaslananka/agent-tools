# Skill Strategy

Skills are reusable instructions that help an AI agent perform a specific workflow with less ambiguity.

## Placement rule

A skill should live where its assumptions are true.

```text
Generic engineering skill      -> agent-tools
KiCad-specific skill           -> kicad-mcp
EasyEDA-specific skill         -> easyeda-mcp-pro
Zaptrace-specific skill        -> zaptrace
A2A mesh-specific skill        -> a2amesh
```

## Why this matters

A product-specific skill may depend on:

- Exact MCP tool names
- Tool parameters
- File formats
- Project structure
- Runtime behavior
- Known limitations
- Validation commands
- Release-specific workflows

If the product changes but the skill lives elsewhere, the agent may follow stale instructions. Keeping product skills next to product code reduces this risk.

## Generic skills allowed in this repository

Generic skills can live here when they are broadly useful and do not depend on one MCP server implementation.

Good examples:

- PCB design principles
- Engineering review checklists
- Documentation quality checks
- Release-readiness checklists
- Agent workflow planning

Bad examples for this repository:

- A skill that calls a specific `kicad-mcp` tool
- A skill that assumes an EasyEDA API endpoint
- A skill that relies on a private VPS path
- A skill that mirrors a product README and will drift over time

## Recommended SKILL.md structure

```text
# Skill Name

## Purpose
## When to use
## Inputs
## Workflow
## Quality checks
## Failure modes
## Output format
```

## Minimum quality standard

Every skill should:

- State when it should be used
- State when it should not be used
- Define required inputs
- Provide a deterministic workflow
- Include validation checks
- Describe common failure modes
- Avoid pretending uncertain results are verified
- Prefer safe, auditable operations

## Current generic skills

- `skills/generic/pcb-design-principles/SKILL.md`
