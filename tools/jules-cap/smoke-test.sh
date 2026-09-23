#!/usr/bin/env bash
set -euo pipefail

RUNTIME_DIR="${JULES_CAP_RUNTIME_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}"
export JULES_CAP_RUNTIME_DIR="$RUNTIME_DIR"

bash "$RUNTIME_DIR/bootstrap.sh"
bash "$RUNTIME_DIR/bootstrap-search-tools.sh"
bash "$RUNTIME_DIR/bootstrap-ast-grep.sh"

tmp_repo="$(mktemp -d)"
trap 'rm -rf "$tmp_repo"' EXIT
git -C "$tmp_repo" init -q
git -C "$tmp_repo" config user.email test@example.invalid
git -C "$tmp_repo" config user.name test
printf '%s\n' '{"scripts":{"test":"echo ok","typecheck":"echo ok"}}' > "$tmp_repo/package.json"
printf '%s\n' 'const x = () => console.log("hello")' > "$tmp_repo/sample.ts"
git -C "$tmp_repo" add .
git -C "$tmp_repo" commit -qm init
export JULES_REPO="$tmp_repo"

jcap doctor --json | grep -q '"ok": true'
jcap plugin run repo-map -- --json | grep -q '"trackedFileCount"'
jcap plugin run check-plan -- --json | grep -q '"candidateCount"'
jskill resolve 'current framework docs' --limit 1 | grep -q 'current-library-docs'
ast-grep run --lang ts --pattern 'console.log($A)' "$tmp_repo/sample.ts" | grep -q 'console.log'

test_config="$tmp_repo/demo-capabilities.json"
python3 - "$RUNTIME_DIR/capabilities.default.json" "$test_config" "$RUNTIME_DIR/demo_server.py" <<'PY'
import json
import os
import sys

base, target, demo = sys.argv[1:4]
with open(base, encoding="utf-8") as handle:
    data = json.load(handle)
data["mcpServers"] = {
    "demo": {
        "transport": "stdio",
        "command": os.path.expanduser("~/.local/jules-cap/venv/bin/python"),
        "args": [demo],
        "cwd": "{repo}",
        "persistentClient": True
    }
}
with open(target, "w", encoding="utf-8") as handle:
    json.dump(data, handle)
PY

out="$(jmcp --config "$test_config" call demo add --args '{"a":20,"b":22}' --json)"
printf '%s\n' "$out" | grep -q '"result": 42'
echo CAPABILITY_RUNTIME_SMOKE_OK
