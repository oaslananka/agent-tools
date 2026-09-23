#!/usr/bin/env python3
"""Suggest project-native verification commands without executing them."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any


SCRIPT_PRIORITY = (
    "check",
    "verify",
    "lint",
    "typecheck",
    "type-check",
    "test",
    "test:unit",
    "test:integration",
    "test:e2e",
    "build",
    "format:check",
    "format-check",
)


def find_root() -> Path:
    completed = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        check=False,
        text=True,
        capture_output=True,
    )
    if completed.returncode == 0 and completed.stdout.strip():
        return Path(completed.stdout.strip()).resolve()
    return Path.cwd().resolve()


def package_plan(root: Path) -> list[dict[str, Any]]:
    path = root / "package.json"
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    scripts = data.get("scripts")
    if not isinstance(scripts, dict):
        return []

    package_manager = "npm"
    if (root / "pnpm-lock.yaml").exists():
        package_manager = "pnpm"
    elif (root / "yarn.lock").exists():
        package_manager = "yarn"
    elif (root / "bun.lock").exists() or (root / "bun.lockb").exists():
        package_manager = "bun"

    def command(name: str) -> str:
        if package_manager == "npm":
            return f"npm run {name}"
        return f"{package_manager} {name}"

    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for name in SCRIPT_PRIORITY:
        if name in scripts and name not in seen:
            seen.add(name)
            result.append(
                {
                    "source": "package.json",
                    "kind": name,
                    "command": command(name),
                    "definition": str(scripts[name]),
                }
            )

    for name, definition in scripts.items():
        if name in seen:
            continue
        lower = str(name).lower()
        if any(token in lower for token in ("lint", "check", "test", "type", "build")):
            result.append(
                {
                    "source": "package.json",
                    "kind": str(name),
                    "command": command(str(name)),
                    "definition": str(definition),
                }
            )
    return result[:20]


def pyproject_plan(root: Path) -> list[dict[str, Any]]:
    path = root / "pyproject.toml"
    if not path.is_file():
        return []

    try:
        import tomllib

        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except Exception:
        data = {}

    tool = data.get("tool") if isinstance(data, dict) else {}
    if not isinstance(tool, dict):
        tool = {}

    commands: list[dict[str, Any]] = []
    if "ruff" in tool or (root / "ruff.toml").exists():
        commands.append(
            {"source": "python", "kind": "lint", "command": "ruff check ."}
        )
    if "mypy" in tool or (root / "mypy.ini").exists():
        commands.append(
            {"source": "python", "kind": "typecheck", "command": "mypy ."}
        )
    if "pytest" in tool or (root / "pytest.ini").exists() or (root / "tests").is_dir():
        commands.append(
            {"source": "python", "kind": "test", "command": "pytest"}
        )

    project = data.get("project") if isinstance(data, dict) else {}
    optional = project.get("optional-dependencies") if isinstance(project, dict) else {}
    dependency_text = json.dumps(
        [project.get("dependencies", []) if isinstance(project, dict) else [], optional],
        ensure_ascii=False,
    ).lower()
    if "pytest" in dependency_text and not any(item["kind"] == "test" for item in commands):
        commands.append(
            {"source": "python", "kind": "test", "command": "pytest"}
        )
    return commands


def make_targets(root: Path) -> list[dict[str, Any]]:
    path = root / "Makefile"
    if not path.is_file():
        return []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []

    targets: set[str] = set()
    for line in text.splitlines():
        if line.startswith(("\t", " ", ".", "#")):
            continue
        match = re.match(r"^([A-Za-z0-9_.-]+)\s*:(?![=])", line)
        if match:
            targets.add(match.group(1))

    preferred = [
        name
        for name in ("check", "verify", "lint", "typecheck", "test", "test-unit", "build")
        if name in targets
    ]
    return [
        {"source": "Makefile", "kind": target, "command": f"make {target}"}
        for target in preferred
    ]


def ecosystem_plan(root: Path) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    if (root / "go.mod").is_file():
        result.extend(
            [
                {"source": "go.mod", "kind": "test", "command": "go test ./..."},
                {"source": "go.mod", "kind": "vet", "command": "go vet ./..."},
            ]
        )
    if (root / "Cargo.toml").is_file():
        result.extend(
            [
                {"source": "Cargo.toml", "kind": "test", "command": "cargo test"},
                {
                    "source": "Cargo.toml",
                    "kind": "lint",
                    "command": "cargo clippy --all-targets --all-features",
                },
            ]
        )
    if (root / "pom.xml").is_file():
        result.append(
            {"source": "pom.xml", "kind": "test", "command": "mvn test"}
        )
    if (root / "gradlew").is_file():
        result.append(
            {"source": "gradle", "kind": "test", "command": "./gradlew test"}
        )
    return result


def build_plan(root: Path) -> dict[str, Any]:
    candidates = [
        *package_plan(root),
        *pyproject_plan(root),
        *make_targets(root),
        *ecosystem_plan(root),
    ]

    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in candidates:
        command = str(item["command"])
        if command in seen:
            continue
        seen.add(command)
        deduped.append(item)

    return {
        "root": str(root),
        "candidateCount": len(deduped),
        "candidates": deduped,
        "note": (
            "Suggestions only; inspect the defining project file and choose targeted "
            "checks appropriate to the change before execution."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    plan = build_plan(find_root())
    if args.json:
        print(json.dumps(plan, indent=2, ensure_ascii=False))
    else:
        print(plan["note"])
        if not plan["candidates"]:
            print("No common verification commands detected.")
        for item in plan["candidates"]:
            print(
                f"- [{item['kind']}] {item['command']} "
                f"(source: {item['source']})"
            )
            if item.get("definition"):
                print(f"    {item['definition']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
