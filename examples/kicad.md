# KiCad Agent Workflow Example

This is a catalog-level example. The final KiCad-specific workflow should live in `oaslananka/kicad-mcp` after the product plugin and skills are added there.

## Goal

Use an AI agent with KiCad MCP support to help review and improve a PCB project.

## Expected flow

1. Open or inspect the KiCad project.
2. Identify schematic, PCB, and rule-check files.
3. Review project structure and constraints.
4. Run design checks where the MCP server supports them.
5. Summarize violations, warnings, and missing information.
6. Suggest corrections with clear engineering rationale.
7. Generate fabrication outputs only after validation passes.

## Human review requirement

PCB and fabrication outputs must be reviewed by a qualified human before manufacturing.

## Future product location

The production-ready version of this workflow should live in:

```text
oaslananka/kicad-mcp/skills/pcb-design/SKILL.md
```
