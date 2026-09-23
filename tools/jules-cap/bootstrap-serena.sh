#!/usr/bin/env bash
set -euo pipefail

VERSION="${JULES_SERENA_VERSION:-1.7.0}"
ROOT="${JULES_CAP_ROOT:-$HOME/.local/jules-cap}"
INSTALL_DIR="$ROOT/serena-$VERSION"
VENV="$INSTALL_DIR/venv"
MARKER="$INSTALL_DIR/.installed-version"

mkdir -p "$ROOT"

needs_install=0
if [[ ! -x "$VENV/bin/serena" ]]; then
  needs_install=1
elif [[ ! -f "$MARKER" ]] || [[ "$(cat "$MARKER" 2>/dev/null || true)" != "$VERSION" ]]; then
  needs_install=1
fi

if (( needs_install )); then
  echo "Installing Serena MCP $VERSION..." >&2
  rm -rf "$INSTALL_DIR"
  mkdir -p "$INSTALL_DIR"
  python3 -m venv "$VENV"
  "$VENV/bin/python" -m pip install \
    --disable-pip-version-check \
    --no-input \
    --quiet \
    "serena-agent==$VERSION"
  printf '%s\n' "$VERSION" > "$MARKER"
fi

echo "Serena MCP ready: $VERSION" >&2
