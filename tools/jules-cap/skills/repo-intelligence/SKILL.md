---
name: repo-intelligence
description: Build a compact repository architecture map before broad exploration in an unfamiliar or large project.
tags: repository, architecture, context, discovery, tests, build, ci
---

Use this skill when the task starts in an unfamiliar repository or when broad shell exploration would otherwise require many terminal actions.

## First pass

Run the compact read-only repository map:

```bash
jcap plugin run repo-map
```

Use JSON only when another script needs structured output:

```bash
jcap plugin run repo-map -- --json
```

The map reports tracked-file counts, dominant languages, top directories, manifests, build/lint/test configs, test examples, CI files, package scripts, and current git state.

## Then narrow the search

Use the map to choose the smallest relevant directory/configuration surface. Prefer one batched read-only terminal action for the targeted files rather than scanning the whole repository again.

## Rules

- Do not rerun the map after every edit. It is a discovery primitive, not a heartbeat.
- Treat detected test/config files as hints; inspect the actual project files before assuming commands or conventions.
- For version-sensitive external APIs, combine this skill with `current-library-docs`.
- Before reporting completion, use the project's existing targeted checks and inspect the final diff.
