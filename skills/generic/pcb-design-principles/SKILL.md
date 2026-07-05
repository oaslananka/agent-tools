# PCB Design Principles

## Purpose

Guide an AI agent through general PCB design review principles without depending on a specific EDA tool or MCP server.

## When to use

Use this skill when the user asks for general PCB design review, PCB quality guidance, manufacturability review, or engineering sanity checks.

Do not use this skill as proof that a board is safe, manufacturable, certified, or production-ready. Physical PCB designs require tool-based validation and human engineering review.

## Required inputs

Useful inputs include:

- Board purpose
- Schematic or netlist information
- PCB layout files or screenshots
- Stackup
- Design rules
- Component constraints
- Power requirements
- Signal-speed requirements
- Manufacturing constraints

## Review workflow

1. Identify the board objective and operating environment.
2. Separate known facts from assumptions.
3. Review power architecture and current paths.
4. Review grounding strategy and return paths.
5. Review placement of connectors, regulators, decoupling capacitors, oscillators, sensors, and high-speed parts.
6. Review trace widths, clearances, vias, thermal relief, and copper pours against expected current and voltage.
7. Review signal integrity risks such as long stubs, impedance mismatch, poor return paths, and noisy coupling.
8. Review EMI/EMC-sensitive areas such as switching regulators, clocks, antennas, and fast digital interfaces.
9. Review manufacturability: board outline, drill sizes, annular rings, silkscreen, solder mask, panelization assumptions, and test access.
10. Produce a prioritized issue list.

## Quality checks

The response should classify findings as:

- Critical: likely functional, safety, or fabrication failure
- Major: high probability of degraded performance or rework
- Minor: improvement or documentation issue
- Unknown: cannot be verified from available data

## Common risks

- Missing decoupling capacitors near IC power pins
- Undersized power traces
- Poor regulator thermal design
- Split or broken return paths
- High-speed signals crossing plane gaps
- Inadequate creepage or clearance
- No test points for important rails
- Silkscreen overlapping pads
- Missing mounting or enclosure constraints
- Fabrication outputs generated before DRC review

## Output format

Return:

- Board context
- Assumptions
- Critical issues
- Major issues
- Minor issues
- Unknowns
- Recommended next validation steps

## Safety note

Do not claim that a PCB is production-ready unless formal EDA checks, manufacturing constraints, electrical requirements, and human engineering review have all been completed.
