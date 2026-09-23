---
name: project-verification
description: Detect and run the smallest project-native checks that can falsify a proposed change before reporting completion.
tags: verify, tests, lint, typecheck, build, ci, correctness
---

Use this skill after code changes or when planning how to validate a fix.

## Discover available checks

Run the read-only planner:

```bash
jcap plugin run check-plan
```

It inspects existing project manifests/configuration and suggests commands; it does not execute them.

## Choose targeted verification

Prefer checks that directly exercise the changed surface. Typical order:

1. focused unit/integration test for the changed behavior;
2. relevant linter/type checker;
3. broader test/build command when justified by the change;
4. final `git diff` inspection.

Do not mechanically run every suggested command for a tiny change if one targeted test plus static checks provides stronger evidence.

## Failure handling

When a check fails:

- distinguish failures caused by the change from pre-existing/environment failures;
- preserve the exact failing command and concise relevant output;
- fix the cause rather than weakening tests or removing checks;
- rerun the smallest failed check first, then the necessary broader checks.

## Completion rule

Do not report a code change as complete solely because files were edited successfully. Report the verification commands actually run and their outcomes.
