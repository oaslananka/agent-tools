---
name: current-library-docs
description: Fetch current library and framework documentation through the VM-level Context7 MCP bridge before relying on model memory.
tags: docs, context7, framework, library, api, versions, current
---

Use this skill when implementation depends on a library/framework API that may have changed or when the repository pins a version whose details matter.

## Workflow

1. Inspect the Context7 MCP tool schemas once if needed:

```bash
jmcp tools context7
```

2. Resolve the library ID with the task-specific question as context:

```bash
jmcp call context7 resolve-library-id --args '{"libraryName":"<library>","query":"<specific implementation question>"}'
```

3. Choose the best matching library/version from the result.

4. Query only the documentation needed for the task:

```bash
jmcp call context7 query-docs --args '{"libraryId":"<resolved id>","query":"<specific implementation question>"}'
```

5. Reconcile the returned documentation with the version actually pinned in the repository before editing code.

## Rules

- Prefer a specific question over broad documentation dumps.
- Do not call Context7 when the task is fully answerable from repository code/tests.
- Do not treat documentation output as proof that the local project uses that version or configuration; verify package manifests and existing code.
- `CONTEXT7_API_KEY` is optional. If it exists, the runtime adds it as an Authorization bearer header without printing it. If it is absent, the header is omitted.
