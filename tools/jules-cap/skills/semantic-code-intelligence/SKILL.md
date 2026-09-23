---
name: semantic-code-intelligence
description: Use Serena's LSP-backed semantic symbol and reference tools when code understanding requires more than text or AST shape.
tags: semantic, symbols, references, lsp, serena, types, definitions, code-intelligence
---

Use this skill when a task depends on **semantic code relationships** rather than literal text or syntax shape.

The optional `serena` MCP capability is LSP-backed and can answer questions such as symbol lookup, definitions, references, and symbol-aware edits depending on the active language/project.

## Choose the cheapest useful tool

- Literal string/name search → use `rg`.
- Repeated syntax-shaped pattern/refactor → use `structural-code-intelligence` / ast-grep.
- Symbol ownership, definitions, references, cross-file semantic relationships, or type-aware code navigation → use Serena.

Do not start Serena for a trivial one-file edit if repository search already answers the question.

## Discovery

The first use may lazily install the pinned Serena package into the VM capability area. Inspect its live MCP schema:

```bash
jmcp tools serena
```

Then call only the semantic tool needed for the current question. Serena's tool names may evolve, so do not hard-code guessed arguments when the live schema is available.

## Runtime behavior

Serena is configured as a persistent MCP client. Its process and LSP state survive separate `jmcp` invocations during the current Jules VM task.

Serena's own config and per-project metadata are redirected under `/tmp/jules-lab`; semantic exploration should not create a repository `.serena` directory.

The web dashboard and GUI log window are disabled for the headless Jules VM.

## Rules

- Treat the first LSP/index warm-up as setup cost; reuse the persistent session instead of restarting it.
- Scope semantic queries to the smallest relevant symbol/path when the tool supports it.
- Do not use broad semantic indexing merely because the capability exists.
- If Serena cannot initialize a language server for the project, report that concrete limitation and fall back to `rg` / ast-grep / project-native compiler tooling instead of modifying the environment blindly.
- Semantic output is evidence for navigation and refactoring, not a replacement for targeted tests, type checks, or final diff inspection.
