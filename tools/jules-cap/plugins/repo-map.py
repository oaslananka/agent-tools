#!/usr/bin/env python3
"""Emit a compact, read-only architecture inventory for the current repository."""

from __future__ import annotations

import argparse
import collections
import json
import os
import subprocess
from pathlib import Path
from typing import Any


MANIFEST_NAMES = {
    "package.json",
    "pyproject.toml",
    "requirements.txt",
    "requirements-dev.txt",
    "Pipfile",
    "poetry.lock",
    "uv.lock",
    "go.mod",
    "Cargo.toml",
    "composer.json",
    "Gemfile",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
    "settings.gradle",
    "settings.gradle.kts",
    "Makefile",
    "justfile",
    "Taskfile.yml",
    "Taskfile.yaml",
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
}

CONFIG_NAMES = {
    "tsconfig.json",
    "vite.config.ts",
    "vite.config.js",
    "next.config.js",
    "next.config.mjs",
    "next.config.ts",
    "eslint.config.js",
    "eslint.config.mjs",
    ".eslintrc",
    ".prettierrc",
    "pytest.ini",
    "tox.ini",
    "mypy.ini",
    "ruff.toml",
    "biome.json",
    "biome.jsonc",
    "playwright.config.ts",
    "playwright.config.js",
    "vitest.config.ts",
    "jest.config.js",
    "jest.config.ts",
}

LANGUAGE_BY_SUFFIX = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java",
    ".kt": "Kotlin",
    ".kts": "Kotlin",
    ".cs": "C#",
    ".cpp": "C++",
    ".cc": "C++",
    ".cxx": "C++",
    ".c": "C",
    ".h": "C/C++",
    ".hpp": "C++",
    ".rb": "Ruby",
    ".php": "PHP",
    ".swift": "Swift",
    ".scala": "Scala",
    ".sh": "Shell",
    ".bash": "Shell",
    ".ps1": "PowerShell",
    ".sql": "SQL",
    ".vue": "Vue",
    ".svelte": "Svelte",
}


def run_git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=root,
        check=False,
        text=True,
        capture_output=True,
    )
    if completed.returncode != 0:
        return ""
    return completed.stdout


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


def tracked_files(root: Path) -> list[Path]:
    completed = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=root,
        check=False,
        capture_output=True,
    )
    if completed.returncode != 0:
        return []
    return [
        Path(item.decode("utf-8", errors="replace"))
        for item in completed.stdout.split(b"\0")
        if item
    ]


def is_test_path(path: Path) -> bool:
    parts = {part.lower() for part in path.parts}
    name = path.name.lower()
    if parts & {"test", "tests", "__tests__", "spec", "specs", "e2e"}:
        return True
    return (
        name.startswith("test_")
        or name.endswith("_test.py")
        or ".test." in name
        or ".spec." in name
    )


def package_scripts(root: Path) -> dict[str, str]:
    path = root / "package.json"
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    scripts = data.get("scripts", {})
    if not isinstance(scripts, dict):
        return {}
    return {str(k): str(v) for k, v in scripts.items()}


def python_metadata(root: Path) -> dict[str, Any]:
    path = root / "pyproject.toml"
    if not path.is_file():
        return {}
    try:
        import tomllib

        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}

    result: dict[str, Any] = {}
    project = data.get("project")
    if isinstance(project, dict):
        if project.get("name"):
            result["projectName"] = project["name"]
        if project.get("requires-python"):
            result["requiresPython"] = project["requires-python"]

    tool = data.get("tool")
    if isinstance(tool, dict):
        detected = [
            name
            for name in ("pytest", "ruff", "mypy", "poetry", "uv", "hatch")
            if name in tool
        ]
        if detected:
            result["tools"] = detected
    return result


def build_inventory(root: Path, max_examples: int) -> dict[str, Any]:
    files = tracked_files(root)
    top_dirs: collections.Counter[str] = collections.Counter()
    suffixes: collections.Counter[str] = collections.Counter()
    languages: collections.Counter[str] = collections.Counter()
    tests: list[str] = []
    manifests: list[str] = []
    configs: list[str] = []
    ci: list[str] = []
    docs: list[str] = []

    for path in files:
        if len(path.parts) > 1:
            top_dirs[path.parts[0]] += 1
        else:
            top_dirs["<root>"] += 1

        suffix = path.suffix.lower()
        if suffix:
            suffixes[suffix] += 1
            language = LANGUAGE_BY_SUFFIX.get(suffix)
            if language:
                languages[language] += 1

        if path.name in MANIFEST_NAMES:
            manifests.append(path.as_posix())
        if path.name in CONFIG_NAMES:
            configs.append(path.as_posix())
        if is_test_path(path):
            tests.append(path.as_posix())
        if path.parts[:2] == (".github", "workflows") or path.as_posix().startswith(
            (".gitlab-ci", ".circleci/", ".buildkite/")
        ):
            ci.append(path.as_posix())
        if (
            path.parts
            and path.parts[0].lower() in {"docs", "doc"}
            or path.name.lower().startswith(("readme", "contributing", "architecture"))
        ):
            docs.append(path.as_posix())

    head = run_git(root, "rev-parse", "--short", "HEAD").strip()
    branch = run_git(root, "branch", "--show-current").strip()
    status_lines = [
        line
        for line in run_git(root, "status", "--short", "--branch").splitlines()
        if line
    ]

    return {
        "root": str(root),
        "head": head,
        "branch": branch,
        "trackedFileCount": len(files),
        "worktreeStatus": status_lines,
        "topDirectories": dict(top_dirs.most_common(20)),
        "languagesByTrackedFiles": dict(languages.most_common()),
        "topExtensions": dict(suffixes.most_common(20)),
        "manifests": sorted(manifests)[:max_examples],
        "configs": sorted(configs)[:max_examples],
        "testFileCount": len(tests),
        "testExamples": sorted(tests)[:max_examples],
        "ciFiles": sorted(ci)[:max_examples],
        "documentation": sorted(docs)[:max_examples],
        "packageScripts": package_scripts(root),
        "python": python_metadata(root),
    }


def render_text(data: dict[str, Any]) -> str:
    lines = [
        f"repo: {data['root']}",
        f"head: {data['head']} branch: {data['branch'] or '(detached)'}",
        f"tracked files: {data['trackedFileCount']}",
    ]

    if data["languagesByTrackedFiles"]:
        langs = ", ".join(
            f"{name}={count}"
            for name, count in data["languagesByTrackedFiles"].items()
        )
        lines.append(f"languages: {langs}")

    if data["manifests"]:
        lines.append("manifests: " + ", ".join(data["manifests"]))
    if data["configs"]:
        lines.append("configs: " + ", ".join(data["configs"]))
    if data["packageScripts"]:
        lines.append(
            "package scripts: " + ", ".join(sorted(data["packageScripts"].keys()))
        )
    if data["testFileCount"]:
        lines.append(f"tests: {data['testFileCount']} tracked test-like files")
        for path in data["testExamples"][:12]:
            lines.append(f"  - {path}")
    if data["ciFiles"]:
        lines.append("CI:")
        for path in data["ciFiles"]:
            lines.append(f"  - {path}")
    if data["topDirectories"]:
        lines.append(
            "top dirs: "
            + ", ".join(
                f"{name}={count}"
                for name, count in list(data["topDirectories"].items())[:12]
            )
        )
    if data["worktreeStatus"]:
        lines.append("git status:")
        lines.extend(f"  {line}" for line in data["worktreeStatus"][:20])

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--max-examples", type=int, default=40)
    args = parser.parse_args()

    data = build_inventory(find_root(), max(1, args.max_examples))
    if args.json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(render_text(data))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
