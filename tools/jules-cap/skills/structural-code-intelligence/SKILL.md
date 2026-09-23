---
name: structural-code-intelligence
description: Use AST-aware structural search and carefully scoped rewrites when text grep is too imprecise for code-pattern discovery or repetitive refactors.
tags: ast, structural, search, refactor, codemod, ast-grep, symbols, patterns
---

Use this skill when the task depends on code **structure**, not just literal text.

The VM snapshot provides pinned `ast-grep` through the capability wrapper:

```bash
jcap plugin run ast-grep -- <ast-grep arguments>
```

or directly:

```bash
ast-grep <arguments>
```

## Discovery first

Prefer structural search before any rewrite. For example:

```bash
ast-grep run --lang ts --pattern 'console.log($A)' src
```

Use the language and the narrowest relevant directory. If the pattern syntax is uncertain, consult current ast-grep documentation through Context7/web docs rather than guessing a destructive rewrite.

## Rewrites

Only use rewrite/update modes when the task explicitly requires source changes and the match set has already been inspected.

Before applying a broad rewrite:

1. run the search without mutation;
2. inspect representative matches and count/scope;
3. apply the rewrite to the smallest relevant path;
4. inspect `git diff`;
5. run targeted project verification.

## When not to use it

- Literal names/strings: prefer `rg`.
- One obvious local edit: edit the file directly.
- Semantic type/reference questions that require compiler/LSP knowledge: use a language-aware capability when available.
- Do not turn a one-line fix into a codemod.

Structural tooling should reduce false matches and repetitive edits, not add ceremony.
