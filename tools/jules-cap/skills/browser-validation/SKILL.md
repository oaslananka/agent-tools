---
name: browser-validation
description: Use Playwright MCP from the Jules VM for deterministic browser interaction, UI verification, console inspection, screenshots, and network-aware debugging.
tags: browser, playwright, ui, frontend, e2e, console, network, screenshot
---

Use this skill when a task changes or diagnoses behavior that is only observable in a browser.

## Discovery

Inspect the Playwright tool surface once when needed:

```bash
jmcp tools playwright
```

The capability uses a persistent `jcap` MCP client daemon plus a localhost-only Streamable HTTP Playwright server. The daemon keeps one MCP client session open across separate `jmcp call` processes, and Playwright uses a shared browser context. Together these preserve tabs/page state during the Jules VM task.

## Typical workflow

1. Start or identify the application under test using the repository's normal commands.
2. Navigate with the Playwright MCP capability.
3. Inspect the accessibility snapshot and browser console.
4. Interact with the exact element references returned by the MCP server.
5. Verify the changed user-visible behavior.
6. Use screenshots only when visual evidence is useful; prefer structured page snapshots for routine interaction.
7. Browser state should remain available across separate calls while the VM task is alive; close/reset it when isolation between scenarios matters.

## Tool selection

Common Playwright MCP tools include navigation, snapshots, clicks, form filling, console messages, network requests, screenshots, and tab management. Always inspect the live tool schemas if an argument is uncertain.

## Rules

- Prefer local application URLs for project verification.
- Do not log in to unrelated external services.
- Do not put credentials in browser instructions, URLs, screenshots, or output.
- Treat browser output as verification evidence, not as a replacement for project tests.
- If the repository already has Playwright/Cypress tests for the changed surface, run those in addition to or instead of ad-hoc browser interaction where appropriate.


## Runtime behavior

- Do not manually run Playwright browser installers. The registered bootstrap installs the exact Chrome for Testing build required by Playwright MCP, including on an older snapshot via lazy first-use bootstrap.
- If browser state unexpectedly resets between separate `jmcp call playwright ...` commands, report the failure instead of masking it with an extra navigation. The persistent-client runtime is specifically intended to preserve that state.
