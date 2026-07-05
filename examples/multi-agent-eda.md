# Multi-Agent EDA Workflow Example

This example describes a future workflow where multiple specialized agents cooperate on an electronics design task.

## Roles

| Agent role | Responsibility |
|---|---|
| Requirements agent | Extract functional, electrical, mechanical, and compliance requirements. |
| Schematic agent | Build or review schematic structure and component-level intent. |
| PCB agent | Review placement, routing, stackup, constraints, and manufacturability. |
| Validation agent | Run checks, compare outputs, and produce issue reports. |
| Documentation agent | Generate design notes, release notes, and fabrication documentation. |

## Coordination model

1. Requirements are extracted first.
2. Design agents produce or inspect artifacts.
3. Validation agent checks outputs against requirements.
4. Documentation agent summarizes the result.
5. Human engineer approves before manufacturing or release.

## Safety rule

No agent should silently approve a hardware design. The final output must separate verified facts, assumptions, warnings, and open issues.

## Future product locations

- Product-specific MCP flows should live in the relevant product repositories.
- Generic multi-agent templates can live in `agent-tools`.
- A2A orchestration logic should live in `a2amesh` when ready.
