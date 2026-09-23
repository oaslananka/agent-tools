---
name: mcp-bridge
description: Use arbitrary stdio or Streamable HTTP MCP servers through the Jules VM capability runtime.
tags: mcp, tools, integrations, api, external
---

Use this skill when a task needs an external capability that Jules does not expose as a native tool.

## Discovery

Start by listing configured servers:

```bash
jcap servers
```

Inspect one server's tools before calling it:

```bash
jmcp tools <server>
```

## Tool calls

Pass arguments as JSON:

```bash
jmcp call <server> <tool> --args '{"key":"value"}'
```

For large or shell-sensitive payloads, write JSON to a temporary file under `/tmp/jules-lab` and use `--args-file`.

## Resources and prompts

```bash
jmcp resources <server>
jmcp read <server> <uri>
jmcp prompts <server>
jmcp prompt <server> <prompt-name> --args '{"name":"value"}'
```

## Secrets

Capability config must refer to secret environment variables by name. Never place secret values in the repository, command line, logs, or task report.

Example HTTP header configuration:

```json
{
  "Authorization": {
    "env": "MY_MCP_TOKEN",
    "prefix": "Bearer "
  }
}
```

The runtime resolves the value only at execution time.
