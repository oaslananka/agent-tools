# Skill Name

## Purpose

Describe the workflow this skill enables for an AI agent.

## When to use

Use this skill when:

- The user asks for a workflow this skill explicitly supports.
- The required inputs are available.
- The agent can validate the output.

Do not use this skill when:

- The task depends on unsupported tools.
- Required files or permissions are missing.
- The result cannot be validated safely.

## Required inputs

- Input 1
- Input 2
- Target repository or project path
- Expected output format

## Workflow

1. Confirm the project context.
2. Inspect the relevant files or tool outputs.
3. Plan the smallest safe change.
4. Execute the workflow using supported tools only.
5. Validate the result.
6. Report what changed, what was verified, and what remains uncertain.

## Quality checks

- The output is complete.
- The output is internally consistent.
- Tool outputs were checked before conclusions were made.
- Any uncertainty is clearly stated.
- The workflow avoids destructive actions unless explicitly requested.

## Failure modes

- Missing required files
- Unsupported tool version
- Ambiguous user request
- Tool output unavailable
- Validation failed

## Output format

Return:

- Summary
- Files changed or inspected
- Validation performed
- Remaining risks or next actions
