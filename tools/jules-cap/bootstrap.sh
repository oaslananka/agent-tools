#!/usr/bin/env bash
set -euo pipefail
MCP_VERSION="${JULES_CAP_MCP_VERSION:-2.2.0}"
ROOT="${JULES_CAP_ROOT:-$HOME/.local/jules-cap}"
VENV="$ROOT/venv"
BIN_DIR="$HOME/.local/bin"
RUNTIME_DIR="${JULES_CAP_RUNTIME_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}"
MARKER="$ROOT/mcp-version.txt"
mkdir -p "$ROOT" "$BIN_DIR"
needs_install=0
if [[ ! -x "$VENV/bin/python" ]]; then needs_install=1
elif [[ ! -f "$MARKER" ]] || [[ "$(cat "$MARKER" 2>/dev/null || true)" != "$MCP_VERSION" ]]; then needs_install=1
fi
if (( needs_install )); then
  rm -rf "$VENV"
  python3 -m venv "$VENV"
  "$VENV/bin/python" -m pip install --disable-pip-version-check --no-input --quiet "mcp==$MCP_VERSION"
  printf '%s\n' "$MCP_VERSION" > "$MARKER"
fi
for name in jcap jmcp jskill; do
  case "$name" in jcap) prefix="" ;; jmcp) prefix="mcp" ;; jskill) prefix="skill" ;; esac
  cat > "$BIN_DIR/$name" <<EOF
#!/usr/bin/env bash
set -euo pipefail
export JULES_CAP_RUNTIME_DIR="$RUNTIME_DIR"
export JULES_CAP_CONFIG="${JULES_CAP_CONFIG:-$RUNTIME_DIR/capabilities.default.json}"
exec "$VENV/bin/python" "$RUNTIME_DIR/jcap.py" $prefix "\$@"
EOF
  chmod 0755 "$BIN_DIR/$name"
done
echo "Jules Capability Runtime ready: $RUNTIME_DIR"
"$VENV/bin/python" - <<'PY'
import importlib.metadata
print("mcp-sdk:", importlib.metadata.version("mcp"))
PY
