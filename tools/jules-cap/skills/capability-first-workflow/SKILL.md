---
name: capability-first-workflow
description: Select the smallest useful capability before coding, then verify the result deterministically.
tags: workflow, verification, tools, speed, accuracy
---

Before implementing a non-trivial task:

1. Run `jskill resolve "<short task description>"`.
2. If external or current information is needed, inspect available MCP servers with `jcap servers`.
3. Prefer one relevant capability over broad exploratory shell work.
4. Batch independent read-only repository discovery into one terminal action.
5. Keep state-changing actions separate when later work depends on their result.
6. Use deterministic project verification before reporting completion.

Do not invoke every tool just because it exists. A capability should reduce uncertainty, execution time, or verification risk.
