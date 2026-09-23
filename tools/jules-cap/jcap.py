#!/usr/bin/env python3
"""Jules Capability Runtime.

A small, repo-controlled extension layer for Jules. It lets the VM use arbitrary
MCP servers (stdio or Streamable HTTP), repo-local skills, and deterministic
local plugins through a single CLI.
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import hashlib
import importlib.metadata
import json
import os
import re
import signal
import subprocess
import sys
from pathlib import Path
from typing import Any, AsyncIterator

try:
    import httpx2
    from mcp import Client, StdioServerParameters
    from mcp.client.streamable_http import streamable_http_client
except ImportError as exc:  # pragma: no cover - user-facing bootstrap failure
    print(
        "Jules Capability Runtime dependencies are missing. "
        "Run: bash tools/jules-cap/bootstrap.sh",
        file=sys.stderr,
    )
    raise SystemExit(78) from exc


class CapabilityError(RuntimeError):
    pass


def repo_root() -> Path:
    env_root = os.environ.get("JULES_REPO")
    if env_root:
        candidate = Path(env_root).expanduser().resolve()
        if candidate.exists():
            return candidate

    current = Path.cwd().resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists() or (candidate / ".jules").exists():
            return candidate

    app = Path("/app")
    if app.exists():
        return app.resolve()
    return current


def find_config(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit).expanduser().resolve()

    env_path = os.environ.get("JULES_CAP_CONFIG")
    if env_path:
        return Path(env_path).expanduser().resolve()

    root = repo_root()
    return root / ".jules" / "capabilities.json"


def read_config_file(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CapabilityError(f"Invalid JSON in {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise CapabilityError(f"Capability config root must be an object: {path}")
    if int(data.get("version", 1)) != 1:
        raise CapabilityError(
            f"Unsupported capability config version in {path}: {data.get('version')}"
        )
    return data


def merge_config(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in overlay.items():
        if key in {"mcpServers", "plugins"}:
            current = dict(merged.get(key, {}))
            if not isinstance(value, dict):
                raise CapabilityError(f"{key} in local overlay must be an object.")
            current.update(value)
            merged[key] = current
        elif key == "skillRoots":
            base_roots = list(merged.get("skillRoots", []))
            if not isinstance(value, list):
                raise CapabilityError("skillRoots in local overlay must be an array.")
            merged[key] = [*base_roots, *value]
        else:
            merged[key] = value
    return merged


def load_config(path: Path) -> tuple[dict[str, Any], list[Path]]:
    if not path.is_file():
        raise CapabilityError(f"Capability config not found: {path}")

    config = read_config_file(path)
    loaded = [path]

    local_env = os.environ.get("JULES_CAP_LOCAL_CONFIG")
    local_path = (
        Path(local_env).expanduser().resolve()
        if local_env
        else path.with_name("capabilities.local.json")
    )
    if local_path.is_file() and local_path != path:
        config = merge_config(config, read_config_file(local_path))
        loaded.append(local_path)

    return config, loaded


def expand_text(value: str, root: Path) -> str:
    value = value.replace("{repo}", str(root))
    value = os.path.expandvars(value)
    return os.path.expanduser(value)


def resolve_value(value: Any, *, root: Path, label: str) -> str:
    if isinstance(value, str):
        return expand_text(value, root)

    if not isinstance(value, dict) or "env" not in value:
        raise CapabilityError(
            f"{label} must be a string or an object containing an 'env' key."
        )

    env_name = str(value["env"])
    env_value = os.environ.get(env_name)
    optional = bool(value.get("optional", False))
    if env_value is None:
        if optional:
            env_value = str(value.get("default", ""))
        else:
            raise CapabilityError(
                f"Required environment variable is missing for {label}: {env_name}"
            )

    prefix = str(value.get("prefix", ""))
    suffix = str(value.get("suffix", ""))
    return prefix + env_value + suffix


def resolve_mapping(
    mapping: Any,
    *,
    root: Path,
    label: str,
) -> dict[str, str]:
    if mapping is None:
        return {}
    if not isinstance(mapping, dict):
        raise CapabilityError(f"{label} must be an object.")

    resolved: dict[str, str] = {}
    for key, value in mapping.items():
        if (
            isinstance(value, dict)
            and isinstance(value.get("env"), str)
            and bool(value.get("optional", False))
            and value["env"] not in os.environ
            and "default" not in value
        ):
            continue

        resolved[str(key)] = resolve_value(
            value,
            root=root,
            label=f"{label}.{key}",
        )
    return resolved


def collect_env_refs(value: Any) -> set[str]:
    refs: set[str] = set()
    if isinstance(value, dict):
        if (
            "env" in value
            and isinstance(value["env"], str)
            and not bool(value.get("optional", False))
        ):
            refs.add(value["env"])
        for key, child in value.items():
            if key == "env":
                continue
            refs.update(collect_env_refs(child))
    elif isinstance(value, list):
        for child in value:
            refs.update(collect_env_refs(child))
    return refs


def mcp_specs(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    value = config.get("mcpServers", {})
    if not isinstance(value, dict):
        raise CapabilityError("mcpServers must be an object.")
    result: dict[str, dict[str, Any]] = {}
    for name, spec in value.items():
        if not isinstance(spec, dict):
            raise CapabilityError(f"MCP server {name!r} must be an object.")
        result[str(name)] = spec
    return result


def plugin_specs(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    value = config.get("plugins", {})
    if not isinstance(value, dict):
        raise CapabilityError("plugins must be an object.")
    result: dict[str, dict[str, Any]] = {}
    for name, spec in value.items():
        if not isinstance(spec, dict):
            raise CapabilityError(f"Plugin {name!r} must be an object.")
        result[str(name)] = spec
    return result


def ensure_mcp_server(
    name: str,
    spec: dict[str, Any],
    root: Path,
) -> None:
    ensure = spec.get("ensure")
    if ensure is None:
        return
    if not isinstance(ensure, dict):
        raise CapabilityError(f"MCP server {name!r} ensure must be an object.")

    command = ensure.get("command")
    if not command:
        raise CapabilityError(f"MCP server {name!r} ensure is missing command.")

    args = ensure.get("args", [])
    if not isinstance(args, list):
        raise CapabilityError(f"MCP server {name!r} ensure args must be an array.")

    cwd_value = ensure.get("cwd", "{repo}")
    cwd = expand_text(str(cwd_value), root) if cwd_value else None

    env = os.environ.copy()
    env.update(
        resolve_mapping(
            ensure.get("env"),
            root=root,
            label=f"mcpServers.{name}.ensure.env",
        )
    )

    argv = [
        expand_text(str(command), root),
        *[expand_text(str(arg), root) for arg in args],
    ]
    completed = subprocess.run(
        argv,
        cwd=cwd,
        env=env,
        check=False,
        text=True,
        capture_output=True,
    )
    if completed.returncode != 0:
        stderr = (completed.stderr or "").strip()
        stdout = (completed.stdout or "").strip()
        detail = stderr or stdout or f"exit code {completed.returncode}"
        if len(detail) > 1200:
            detail = detail[-1200:]
        raise CapabilityError(
            f"MCP server {name!r} ensure command failed: {detail}"
        )


@contextlib.asynccontextmanager
async def open_mcp_client(
    name: str,
    spec: dict[str, Any],
    root: Path,
) -> AsyncIterator[Client]:
    transport = str(spec.get("transport") or ("http" if spec.get("url") else "stdio"))

    ensure_mcp_server(name, spec, root)

    if transport == "stdio":
        command = spec.get("command")
        if not command:
            raise CapabilityError(f"MCP server {name!r} is missing command.")

        args = spec.get("args", [])
        if not isinstance(args, list):
            raise CapabilityError(f"MCP server {name!r} args must be an array.")

        cwd_value = spec.get("cwd", "{repo}")
        cwd = expand_text(str(cwd_value), root) if cwd_value else None
        configured_env = resolve_mapping(
            spec.get("env"),
            root=root,
            label=f"mcpServers.{name}.env",
        )
        env = None
        if configured_env:
            env = os.environ.copy()
            env.update(configured_env)

        params = StdioServerParameters(
            command=expand_text(str(command), root),
            args=[expand_text(str(arg), root) for arg in args],
            env=env,
            cwd=cwd,
        )
        async with Client(params) as client:
            yield client
        return

    if transport in {"http", "streamable-http", "streamable_http"}:
        url = spec.get("url")
        if not url:
            raise CapabilityError(f"MCP server {name!r} is missing url.")


        resolved_url = resolve_value(
            url,
            root=root,
            label=f"mcpServers.{name}.url",
        )
        headers = resolve_mapping(
            spec.get("headers"),
            root=root,
            label=f"mcpServers.{name}.headers",
        )
        timeout = float(spec.get("timeoutSeconds", 30))

        client_kwargs: dict[str, Any] = {
            "headers": headers,
            "timeout": timeout,
        }
        proxy_value = spec.get("proxy")
        if proxy_value is not None:
            client_kwargs["proxy"] = resolve_value(
                proxy_value,
                root=root,
                label=f"mcpServers.{name}.proxy",
            )

        async with httpx2.AsyncClient(**client_kwargs) as http_client:
            mcp_transport = streamable_http_client(
                resolved_url,
                http_client=http_client,
            )
            async with Client(mcp_transport) as client:
                yield client
        return

    raise CapabilityError(
        f"MCP server {name!r} has unsupported transport {transport!r}."
    )


async def list_all(client: Client, method: str) -> list[Any]:
    items: list[Any] = []
    cursor: str | None = None
    while True:
        result = await getattr(client, method)(cursor=cursor)
        field = {
            "list_tools": "tools",
            "list_resources": "resources",
            "list_resource_templates": "resource_templates",
            "list_prompts": "prompts",
        }[method]
        items.extend(getattr(result, field))
        cursor = getattr(result, "next_cursor", None)
        if not cursor:
            break
    return items


def jsonable(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json", by_alias=True, exclude_none=True)
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    return value


def print_json(value: Any) -> None:
    print(json.dumps(jsonable(value), indent=2, ensure_ascii=False, sort_keys=True))


def persistent_state_paths(name: str, root: Path) -> dict[str, Path]:
    state_dir = Path(
        os.environ.get("JULES_CAP_STATE_DIR", "/tmp/jules-cap")
    ).expanduser()
    safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "-", name).strip("-") or "server"
    repo_key = hashlib.sha256(str(root).encode("utf-8")).hexdigest()[:10]
    stem = f"{repo_key}-{safe_name}"
    return {
        "dir": state_dir,
        "socket": state_dir / f"{stem}.sock",
        "pid": state_dir / f"{stem}.pid",
        "log": state_dir / f"{stem}.log",
    }


async def daemon_socket_request(
    socket_path: Path,
    request: dict[str, Any],
    *,
    timeout: float = 30.0,
) -> Any:
    reader, writer = await asyncio.wait_for(
        asyncio.open_unix_connection(str(socket_path), limit=16 * 1024 * 1024),
        timeout=timeout,
    )
    try:
        payload = json.dumps(request, ensure_ascii=False, separators=(",", ":"))
        writer.write(payload.encode("utf-8") + b"\n")
        await writer.drain()
        line = await asyncio.wait_for(reader.readline(), timeout=timeout)
        if not line:
            raise CapabilityError("Persistent MCP daemon closed the socket without a response.")
        response = json.loads(line.decode("utf-8"))
        if not isinstance(response, dict):
            raise CapabilityError("Persistent MCP daemon returned an invalid response.")
        if not response.get("ok", False):
            raise CapabilityError(str(response.get("error") or "Persistent MCP daemon request failed."))
        return response.get("result")
    finally:
        writer.close()
        with contextlib.suppress(Exception):
            await writer.wait_closed()


def _read_pid(path: Path) -> int | None:
    try:
        return int(path.read_text(encoding="ascii").strip())
    except (OSError, ValueError):
        return None


def _pid_alive(pid: int | None) -> bool:
    if not pid:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


async def ensure_persistent_daemon(
    name: str,
    root: Path,
    config_path: Path,
) -> Path:
    paths = persistent_state_paths(name, root)
    paths["dir"].mkdir(parents=True, exist_ok=True)

    if paths["socket"].exists():
        try:
            await daemon_socket_request(paths["socket"], {"op": "ping"}, timeout=1.5)
            return paths["socket"]
        except Exception:
            with contextlib.suppress(OSError):
                paths["socket"].unlink()

    existing_pid = _read_pid(paths["pid"])
    if _pid_alive(existing_pid):
        for _ in range(40):
            if paths["socket"].exists():
                try:
                    await daemon_socket_request(paths["socket"], {"op": "ping"}, timeout=1.0)
                    return paths["socket"]
                except Exception:
                    pass
            await asyncio.sleep(0.1)

        with contextlib.suppress(OSError):
            os.kill(existing_pid, signal.SIGTERM)

    log_handle = paths["log"].open("ab", buffering=0)
    try:
        proc = subprocess.Popen(
            [
                sys.executable,
                str(Path(__file__).resolve()),
                "--config",
                str(config_path),
                "mcp-daemon",
                name,
            ],
            cwd=str(root),
            env=os.environ.copy(),
            stdin=subprocess.DEVNULL,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    finally:
        log_handle.close()

    startup_seconds = max(
        5.0,
        float(os.environ.get("JULES_CAP_DAEMON_START_TIMEOUT_SECONDS", "300")),
    )
    attempts = max(1, int(startup_seconds * 10))
    for _ in range(attempts):
        if paths["socket"].exists():
            try:
                await daemon_socket_request(paths["socket"], {"op": "ping"}, timeout=1.0)
                return paths["socket"]
            except Exception:
                pass
        if proc.poll() is not None:
            detail = ""
            try:
                detail = paths["log"].read_text(encoding="utf-8", errors="replace")[-2000:]
            except OSError:
                pass
            raise CapabilityError(
                f"Persistent MCP daemon for {name!r} exited early. {detail}".strip()
            )
        await asyncio.sleep(0.1)

    with contextlib.suppress(OSError):
        proc.terminate()
    raise CapabilityError(f"Persistent MCP daemon for {name!r} did not become ready.")


async def daemon_operation(client: Client, request: dict[str, Any]) -> Any:
    op = str(request.get("op") or "")
    if op == "ping":
        return {"pong": True}
    if op == "tools":
        return jsonable(await list_all(client, "list_tools"))
    if op == "call":
        return jsonable(
            await client.call_tool(
                str(request.get("tool") or ""),
                request.get("arguments") or {},
            )
        )
    if op == "resources":
        return {
            "resources": jsonable(await list_all(client, "list_resources")),
            "templates": jsonable(await list_all(client, "list_resource_templates")),
        }
    if op == "read":
        return jsonable(await client.read_resource(str(request.get("uri") or "")))
    if op == "prompts":
        return jsonable(await list_all(client, "list_prompts"))
    if op == "prompt":
        prompt_args = {
            str(k): str(v)
            for k, v in (request.get("arguments") or {}).items()
        }
        return jsonable(
            await client.get_prompt(
                str(request.get("name") or ""),
                prompt_args,
            )
        )
    raise CapabilityError(f"Unsupported persistent MCP operation: {op}")


async def run_persistent_daemon(
    name: str,
    spec: dict[str, Any],
    root: Path,
) -> int:
    paths = persistent_state_paths(name, root)
    paths["dir"].mkdir(parents=True, exist_ok=True)
    with contextlib.suppress(OSError):
        paths["socket"].unlink()
    paths["pid"].write_text(str(os.getpid()), encoding="ascii")

    async with open_mcp_client(name, spec, root) as client:
        async def handler(
            reader: asyncio.StreamReader,
            writer: asyncio.StreamWriter,
        ) -> None:
            try:
                line = await reader.readline()
                if not line:
                    return
                request = json.loads(line.decode("utf-8"))
                if not isinstance(request, dict):
                    raise CapabilityError("Daemon request must be a JSON object.")
                result = await daemon_operation(client, request)
                response = {"ok": True, "result": result}
            except Exception as exc:
                response = {
                    "ok": False,
                    "error": f"{type(exc).__name__}: {exc}",
                }

            writer.write(
                json.dumps(response, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
                + b"\n"
            )
            await writer.drain()
            writer.close()
            with contextlib.suppress(Exception):
                await writer.wait_closed()

        server = await asyncio.start_unix_server(
            handler,
            path=str(paths["socket"]),
            limit=16 * 1024 * 1024,
        )
        try:
            async with server:
                await server.serve_forever()
        finally:
            server.close()
            await server.wait_closed()

    return 0


def render_persistent_tool_result(result: dict[str, Any], *, json_output: bool) -> int:
    if json_output:
        print_json(result)
    else:
        structured = result.get("structuredContent")
        if structured is not None:
            print(json.dumps(structured, indent=2, ensure_ascii=False))
        content = result.get("content") or []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                print(block.get("text", ""))
            elif structured is None:
                print(json.dumps(block, ensure_ascii=False))
    return 5 if bool(result.get("isError", False)) else 0


async def command_mcp_persistent(
    args: argparse.Namespace,
    name: str,
    root: Path,
    config_path: Path,
) -> int:
    socket_path = await ensure_persistent_daemon(name, root, config_path)

    if args.mcp_command == "tools":
        value = await daemon_socket_request(socket_path, {"op": "tools"})
        if args.json_output:
            print_json(value)
        else:
            for tool in value or []:
                title = tool.get("title")
                desc = tool.get("description") or ""
                heading = str(tool.get("name") or "")
                if title:
                    heading += f" — {title}"
                print(heading)
                if desc:
                    print(f"  {desc}")
                print(
                    "  input:",
                    json.dumps(
                        tool.get("inputSchema") or {},
                        ensure_ascii=False,
                        sort_keys=True,
                    ),
                )
        return 0

    if args.mcp_command == "call":
        payload = parse_json_object(args.args, args.args_file)
        value = await daemon_socket_request(
            socket_path,
            {"op": "call", "tool": args.tool, "arguments": payload},
            timeout=120.0,
        )
        if not isinstance(value, dict):
            raise CapabilityError("Persistent MCP tool call returned an invalid result.")
        return render_persistent_tool_result(value, json_output=args.json_output)

    if args.mcp_command == "resources":
        value = await daemon_socket_request(socket_path, {"op": "resources"})
        if args.json_output:
            print_json(value)
        else:
            for item in (value or {}).get("resources", []):
                print(f"{item.get('uri', '')}  {item.get('name', '')}")
            for item in (value or {}).get("templates", []):
                print(f"{item.get('uriTemplate', '')}  {item.get('name', '')} [template]")
        return 0

    if args.mcp_command == "read":
        value = await daemon_socket_request(
            socket_path,
            {"op": "read", "uri": args.uri},
        )
        if args.json_output:
            print_json(value)
        else:
            for item in (value or {}).get("contents", []):
                if isinstance(item, dict) and "text" in item:
                    print(item["text"])
                else:
                    print(json.dumps(item, ensure_ascii=False))
        return 0

    if args.mcp_command == "prompts":
        value = await daemon_socket_request(socket_path, {"op": "prompts"})
        if args.json_output:
            print_json(value)
        else:
            for prompt in value or []:
                print(f"{prompt.get('name', '')}  {prompt.get('description', '') or ''}")
        return 0

    if args.mcp_command == "prompt":
        payload = parse_json_object(args.args, args.args_file)
        value = await daemon_socket_request(
            socket_path,
            {"op": "prompt", "name": args.name, "arguments": payload},
        )
        if args.json_output:
            print_json(value)
        else:
            for message in (value or {}).get("messages", []):
                print(f"[{message.get('role', '')}]")
                print(json.dumps(message.get("content"), indent=2, ensure_ascii=False))
        return 0

    raise CapabilityError(f"Unhandled persistent MCP command: {args.mcp_command}")


def parse_json_object(raw: str | None, file_path: str | None) -> dict[str, Any]:
    if raw and file_path:
        raise CapabilityError("Use either --args or --args-file, not both.")

    if file_path:
        text = Path(file_path).read_text(encoding="utf-8")
    else:
        text = raw or "{}"

    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise CapabilityError(f"Invalid JSON arguments: {exc}") from exc
    if not isinstance(value, dict):
        raise CapabilityError("Tool/prompt arguments must be a JSON object.")
    return value


def render_tool_result(result: Any, *, json_output: bool) -> int:
    if json_output:
        print_json(result)
    else:
        structured = getattr(result, "structured_content", None)
        if structured is not None:
            print(json.dumps(jsonable(structured), indent=2, ensure_ascii=False))

        content = getattr(result, "content", None) or []
        for block in content:
            data = jsonable(block)
            if isinstance(data, dict) and data.get("type") == "text":
                print(data.get("text", ""))
            elif structured is None:
                print(json.dumps(data, ensure_ascii=False))

    return 5 if bool(getattr(result, "is_error", False)) else 0


def skill_roots(config: dict[str, Any], root: Path) -> list[Path]:
    raw = config.get("skillRoots", [".jules/skills"])
    if not isinstance(raw, list):
        raise CapabilityError("skillRoots must be an array.")
    return [Path(expand_text(str(item), root)).resolve() for item in raw]


def parse_skill(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    metadata: dict[str, str] = {}
    body = text

    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            frontmatter = text[4:end]
            body = text[end + 5 :]
            for line in frontmatter.splitlines():
                if ":" not in line:
                    continue
                key, value = line.split(":", 1)
                metadata[key.strip()] = value.strip().strip('"').strip("'")

    name = metadata.get("name") or path.parent.name
    description = metadata.get("description", "")
    tags = [
        item.strip()
        for item in metadata.get("tags", "").split(",")
        if item.strip()
    ]
    return {
        "name": name,
        "description": description,
        "tags": tags,
        "path": str(path),
        "content": body.strip(),
    }


def load_skills(config: dict[str, Any], root: Path) -> list[dict[str, Any]]:
    skills: list[dict[str, Any]] = []
    seen: set[str] = set()
    for skill_root in skill_roots(config, root):
        if not skill_root.is_dir():
            continue
        for path in sorted(skill_root.rglob("SKILL.md")):
            skill = parse_skill(path)
            name = str(skill["name"])
            if name in seen:
                continue
            seen.add(name)
            skills.append(skill)
    return skills


WORD_RE = re.compile(r"[A-Za-z0-9_.+-]+")


def skill_score(skill: dict[str, Any], query: str) -> int:
    query_lower = query.lower().strip()
    tokens = {token.lower() for token in WORD_RE.findall(query)}
    if not tokens:
        return 0

    name = str(skill["name"]).lower()
    description = str(skill["description"]).lower()
    tags = " ".join(skill["tags"]).lower()
    content = str(skill["content"])[:6000].lower()

    score = 0
    if query_lower == name:
        score += 100
    elif query_lower in name:
        score += 50
    if query_lower and query_lower in description:
        score += 25

    for token in tokens:
        if token in name:
            score += 12
        if token in tags:
            score += 8
        if token in description:
            score += 5
        if token in content:
            score += 1
    return score


def find_skill(skills: list[dict[str, Any]], name: str) -> dict[str, Any]:
    for skill in skills:
        if skill["name"] == name or Path(str(skill["path"])).parent.name == name:
            return skill
    raise CapabilityError(f"Skill not found: {name}")


def run_plugin(
    name: str,
    spec: dict[str, Any],
    root: Path,
    extra_args: list[str],
) -> int:
    command = spec.get("command")
    if not command:
        raise CapabilityError(f"Plugin {name!r} is missing command.")

    configured_args = spec.get("args", [])
    if not isinstance(configured_args, list):
        raise CapabilityError(f"Plugin {name!r} args must be an array.")

    cwd = expand_text(str(spec.get("cwd", "{repo}")), root)
    env = os.environ.copy()
    env.update(
        resolve_mapping(
            spec.get("env"),
            root=root,
            label=f"plugins.{name}.env",
        )
    )

    argv = [
        expand_text(str(command), root),
        *[expand_text(str(arg), root) for arg in configured_args],
        *extra_args,
    ]
    completed = subprocess.run(argv, cwd=cwd, env=env, check=False)
    return completed.returncode


async def command_mcp(
    args: argparse.Namespace,
    config: dict[str, Any],
    root: Path,
    config_path: Path | None = None,
) -> int:
    specs = mcp_specs(config)
    if args.server not in specs:
        raise CapabilityError(
            f"Unknown MCP server {args.server!r}. Available: {', '.join(sorted(specs)) or '(none)'}"
        )

    spec = specs[args.server]
    if bool(spec.get("persistentClient", False)):
        resolved_config = config_path or find_config(getattr(args, "config", None))
        return await command_mcp_persistent(
            args,
            args.server,
            root,
            resolved_config,
        )

    async with open_mcp_client(args.server, spec, root) as client:
        if args.mcp_command == "tools":
            tools = await list_all(client, "list_tools")
            if args.json_output:
                print_json(tools)
            else:
                for tool in tools:
                    title = getattr(tool, "title", None)
                    desc = getattr(tool, "description", None) or ""
                    heading = f"{tool.name}" + (f" — {title}" if title else "")
                    print(heading)
                    if desc:
                        print(f"  {desc}")
                    print(
                        "  input:",
                        json.dumps(
                            jsonable(getattr(tool, "input_schema", {})),
                            ensure_ascii=False,
                            sort_keys=True,
                        ),
                    )
            return 0

        if args.mcp_command == "call":
            payload = parse_json_object(args.args, args.args_file)
            result = await client.call_tool(args.tool, payload)
            return render_tool_result(result, json_output=args.json_output)

        if args.mcp_command == "resources":
            resources = await list_all(client, "list_resources")
            templates = await list_all(client, "list_resource_templates")
            value = {"resources": resources, "templates": templates}
            if args.json_output:
                print_json(value)
            else:
                for item in resources:
                    print(f"{item.uri}  {getattr(item, 'name', '')}")
                for item in templates:
                    print(f"{item.uri_template}  {getattr(item, 'name', '')} [template]")
            return 0

        if args.mcp_command == "read":
            result = await client.read_resource(args.uri)
            if args.json_output:
                print_json(result)
            else:
                for item in result.contents:
                    data = jsonable(item)
                    if isinstance(data, dict) and "text" in data:
                        print(data["text"])
                    else:
                        print(json.dumps(data, ensure_ascii=False))
            return 0

        if args.mcp_command == "prompts":
            prompts = await list_all(client, "list_prompts")
            if args.json_output:
                print_json(prompts)
            else:
                for prompt in prompts:
                    print(f"{prompt.name}  {getattr(prompt, 'description', '') or ''}")
            return 0

        if args.mcp_command == "prompt":
            payload = parse_json_object(args.args, args.args_file)
            prompt_args = {str(k): str(v) for k, v in payload.items()}
            result = await client.get_prompt(args.name, prompt_args)
            if args.json_output:
                print_json(result)
            else:
                for message in result.messages:
                    print(f"[{message.role}]")
                    print(json.dumps(jsonable(message.content), indent=2, ensure_ascii=False))
            return 0

    raise CapabilityError(f"Unhandled MCP command: {args.mcp_command}")


async def doctor_connect(
    specs: dict[str, dict[str, Any]],
    root: Path,
    *,
    include_lazy: bool = False,
) -> dict[str, Any]:
    results: dict[str, Any] = {}
    for name, spec in specs.items():
        if bool(spec.get("lazy", False)) and not include_lazy:
            results[name] = {
                "ok": True,
                "skipped": True,
                "reason": "lazy capability; use --include-lazy to initialize it",
            }
            continue
        try:
            async with open_mcp_client(name, spec, root) as client:
                tools = await list_all(client, "list_tools")
                results[name] = {
                    "ok": True,
                    "protocolVersion": getattr(client, "protocol_version", None),
                    "toolCount": len(tools),
                }
        except Exception as exc:  # diagnostic path
            results[name] = {
                "ok": False,
                "error": f"{type(exc).__name__}: {exc}",
            }
    return results


def add_common_output_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help="Emit machine-readable JSON when supported.",
    )


def add_config_override(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--config",
        default=argparse.SUPPRESS,
        help="Capability config JSON path. May be supplied after this command.",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="jcap", description=__doc__)
    parser.add_argument("--config", help="Capability config JSON path.")
    add_common_output_flags(parser)
    sub = parser.add_subparsers(dest="command", required=True)

    servers = sub.add_parser("servers", help="List configured MCP servers and local plugins.")
    add_config_override(servers)
    add_common_output_flags(servers)

    doctor = sub.add_parser("doctor", help="Validate the local capability runtime.")
    add_config_override(doctor)
    doctor.add_argument("--connect", action="store_true", help="Connect to configured MCP servers.")
    doctor.add_argument(
        "--include-lazy",
        action="store_true",
        help="Initialize lazy MCP capabilities during --connect diagnostics.",
    )
    add_common_output_flags(doctor)

    mcp = sub.add_parser("mcp", help="Use an arbitrary MCP server.")
    add_config_override(mcp)
    add_common_output_flags(mcp)
    mcp_sub = mcp.add_subparsers(dest="mcp_command", required=True)

    mcp_daemon = sub.add_parser("mcp-daemon", help=argparse.SUPPRESS)
    mcp_daemon.add_argument("server")

    tools = mcp_sub.add_parser("tools", help="List server tools.")
    tools.add_argument("server")
    add_common_output_flags(tools)

    call = mcp_sub.add_parser("call", help="Call a server tool.")
    call.add_argument("server")
    call.add_argument("tool")
    call.add_argument("--args", help="Tool arguments as a JSON object.")
    call.add_argument("--args-file", help="Read tool arguments from a JSON file.")
    add_common_output_flags(call)

    resources = mcp_sub.add_parser("resources", help="List resources and resource templates.")
    resources.add_argument("server")
    add_common_output_flags(resources)

    read = mcp_sub.add_parser("read", help="Read a resource URI.")
    read.add_argument("server")
    read.add_argument("uri")
    add_common_output_flags(read)

    prompts = mcp_sub.add_parser("prompts", help="List server prompts.")
    prompts.add_argument("server")
    add_common_output_flags(prompts)

    prompt = mcp_sub.add_parser("prompt", help="Render a server prompt.")
    prompt.add_argument("server")
    prompt.add_argument("name")
    prompt.add_argument("--args", help="Prompt arguments as a JSON object.")
    prompt.add_argument("--args-file", help="Read prompt arguments from a JSON file.")
    add_common_output_flags(prompt)

    skill = sub.add_parser("skill", help="Discover and load repo-local skills.")
    add_config_override(skill)
    add_common_output_flags(skill)
    skill_sub = skill.add_subparsers(dest="skill_command", required=True)

    skill_list = skill_sub.add_parser("list", help="List skills.")
    add_common_output_flags(skill_list)

    skill_show = skill_sub.add_parser("show", help="Print one skill.")
    skill_show.add_argument("name")
    add_common_output_flags(skill_show)

    skill_search = skill_sub.add_parser("search", help="Search skills by task text.")
    skill_search.add_argument("query")
    skill_search.add_argument("--limit", type=int, default=5)
    add_common_output_flags(skill_search)

    skill_resolve = skill_sub.add_parser("resolve", help="Load the best matching skills.")
    skill_resolve.add_argument("query")
    skill_resolve.add_argument("--limit", type=int, default=2)
    add_common_output_flags(skill_resolve)

    plugin = sub.add_parser("plugin", help="Run deterministic repo-local plugins.")
    add_config_override(plugin)
    add_common_output_flags(plugin)
    plugin_sub = plugin.add_subparsers(dest="plugin_command", required=True)

    plugin_list = plugin_sub.add_parser("list", help="List plugins.")
    add_common_output_flags(plugin_list)

    plugin_run = plugin_sub.add_parser("run", help="Run a plugin.")
    plugin_run.add_argument("name")
    plugin_run.add_argument("plugin_args", nargs=argparse.REMAINDER)
    add_common_output_flags(plugin_run)

    return parser


async def async_main(args: argparse.Namespace, config: dict[str, Any], root: Path) -> int:
    if args.command == "mcp":
        return await command_mcp(args, config, root)

    if args.command == "doctor" and args.connect:
        specs = mcp_specs(config)
        connected = await doctor_connect(specs, root)
        setattr(args, "_doctor_connected", connected)
    return -999


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        root = repo_root()
        config_path = find_config(args.config)
        config, loaded_configs = load_config(config_path)

        if args.command == "servers":
            value = {
                "config": str(config_path),
                "loadedConfigs": [str(path) for path in loaded_configs],
                "mcpServers": {
                    name: {
                        "transport": spec.get("transport") or ("http" if spec.get("url") else "stdio"),
                        "persistentClient": bool(spec.get("persistentClient", False)),
                        "lazy": bool(spec.get("lazy", False)),
                        "description": spec.get("description", ""),
                    }
                    for name, spec in mcp_specs(config).items()
                },
                "plugins": {
                    name: {
                        "description": spec.get("description", ""),
                        "readOnly": bool(spec.get("readOnly", False)),
                    }
                    for name, spec in plugin_specs(config).items()
                },
            }
            if args.json_output:
                print_json(value)
            else:
                print(f"config: {config_path}")
                print("MCP servers:")
                for name, info in value["mcpServers"].items():
                    print(f"  {name} [{info['transport']}] {info['description']}")
                print("Plugins:")
                for name, info in value["plugins"].items():
                    print(f"  {name} readOnly={str(info['readOnly']).lower()} {info['description']}")
            return 0

        if args.command == "doctor":
            specs = mcp_specs(config)
            plugins = plugin_specs(config)
            refs = collect_env_refs({"mcpServers": specs, "plugins": plugins})
            result: dict[str, Any] = {
                "ok": True,
                "repo": str(root),
                "config": str(config_path),
                "loadedConfigs": [str(path) for path in loaded_configs],
                "python": sys.version.split()[0],
                "mcpSdk": importlib.metadata.version("mcp"),
                "mcpServers": len(specs),
                "plugins": len(plugins),
                "skills": len(load_skills(config, root)),
                "missingEnvironmentVariables": sorted(
                    name for name in refs if name not in os.environ
                ),
            }
            if args.connect:
                result["connections"] = asyncio.run(
                    doctor_connect(
                        specs,
                        root,
                        include_lazy=bool(args.include_lazy),
                    )
                )
                result["ok"] = all(
                    item.get("ok", False)
                    for item in result["connections"].values()
                )
            if args.json_output:
                print_json(result)
            else:
                for key, value in result.items():
                    if key == "connections":
                        print("connections:")
                        for name, status in value.items():
                            print(f"  {name}: {status}")
                    else:
                        print(f"{key}: {value}")
            return 0 if result["ok"] else 4

        if args.command == "mcp-daemon":
            specs = mcp_specs(config)
            if args.server not in specs:
                raise CapabilityError(f"Unknown MCP server: {args.server}")
            try:
                return asyncio.run(
                    run_persistent_daemon(args.server, specs[args.server], root)
                )
            finally:
                paths = persistent_state_paths(args.server, root)
                with contextlib.suppress(OSError):
                    paths["socket"].unlink()
                with contextlib.suppress(OSError):
                    paths["pid"].unlink()

        if args.command == "mcp":
            return asyncio.run(command_mcp(args, config, root, config_path))

        if args.command == "skill":
            skills = load_skills(config, root)

            if args.skill_command == "list":
                summaries = [
                    {
                        "name": skill["name"],
                        "description": skill["description"],
                        "tags": skill["tags"],
                        "path": skill["path"],
                    }
                    for skill in skills
                ]
                if args.json_output:
                    print_json(summaries)
                else:
                    for skill in summaries:
                        print(f"{skill['name']} — {skill['description']}")
                        if skill["tags"]:
                            print(f"  tags: {', '.join(skill['tags'])}")
                        print(f"  {skill['path']}")
                return 0

            if args.skill_command == "show":
                skill = find_skill(skills, args.name)
                if args.json_output:
                    print_json(skill)
                else:
                    print(f"# {skill['name']}")
                    if skill["description"]:
                        print(f"\n{skill['description']}")
                    print(f"\n{skill['content']}")
                return 0

            ranked = [
                (skill_score(skill, args.query), skill)
                for skill in skills
            ]
            ranked = [
                item for item in sorted(ranked, key=lambda item: (-item[0], item[1]["name"]))
                if item[0] > 0
            ][: max(1, args.limit)]

            if args.skill_command == "search":
                value = [
                    {
                        "score": score,
                        "name": skill["name"],
                        "description": skill["description"],
                        "tags": skill["tags"],
                        "path": skill["path"],
                    }
                    for score, skill in ranked
                ]
                if args.json_output:
                    print_json(value)
                else:
                    for item in value:
                        print(f"{item['score']:>3}  {item['name']} — {item['description']}")
                return 0 if value else 3

            if args.skill_command == "resolve":
                value = [
                    {
                        "score": score,
                        **skill,
                    }
                    for score, skill in ranked
                ]
                if args.json_output:
                    print_json(value)
                else:
                    for index, item in enumerate(value, 1):
                        if index > 1:
                            print("\n---\n")
                        print(f"# Skill: {item['name']} (score={item['score']})")
                        if item["description"]:
                            print(f"\n{item['description']}")
                        print(f"\n{item['content']}")
                return 0 if value else 3

        if args.command == "plugin":
            plugins = plugin_specs(config)
            if args.plugin_command == "list":
                value = [
                    {
                        "name": name,
                        "description": spec.get("description", ""),
                        "readOnly": bool(spec.get("readOnly", False)),
                    }
                    for name, spec in sorted(plugins.items())
                ]
                if args.json_output:
                    print_json(value)
                else:
                    for item in value:
                        print(
                            f"{item['name']} readOnly={str(item['readOnly']).lower()} "
                            f"— {item['description']}"
                        )
                return 0

            if args.plugin_command == "run":
                if args.name not in plugins:
                    raise CapabilityError(
                        f"Unknown plugin {args.name!r}. "
                        f"Available: {', '.join(sorted(plugins)) or '(none)'}"
                    )
                extra = list(args.plugin_args)
                if extra and extra[0] == "--":
                    extra = extra[1:]
                return run_plugin(args.name, plugins[args.name], root, extra)

        raise CapabilityError(f"Unhandled command: {args.command}")

    except CapabilityError as exc:
        print(f"jcap: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        return 130
    except Exception as exc:
        print(f"jcap: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
