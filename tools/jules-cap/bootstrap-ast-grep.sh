#!/usr/bin/env bash
set -euo pipefail

VERSION="${JULES_AST_GREP_VERSION:-0.45.3}"
ROOT="${JULES_CAP_ROOT:-$HOME/.local/jules-cap}"
INSTALL_DIR="$ROOT/ast-grep-$VERSION"
BIN_DIR="$HOME/.local/bin"
MARKER="$INSTALL_DIR/.installed-version"
AST_GREP="$INSTALL_DIR/node_modules/.bin/ast-grep"

mkdir -p "$ROOT" "$BIN_DIR"

needs_install=0
if [[ ! -x "$AST_GREP" ]]; then
  needs_install=1
elif [[ ! -f "$MARKER" ]] || [[ "$(cat "$MARKER" 2>/dev/null || true)" != "$VERSION" ]]; then
  needs_install=1
fi

if (( needs_install )); then
  echo "Installing ast-grep $VERSION..."
  rm -rf "$INSTALL_DIR"
  mkdir -p "$INSTALL_DIR"
  npm install --prefix "$INSTALL_DIR" --no-audit --no-fund --omit=dev "@ast-grep/cli@$VERSION"
  printf '%s\n' "$VERSION" > "$MARKER"
fi

ln -sfn "$AST_GREP" "$BIN_DIR/ast-grep"

echo "ast-grep ready:"
"$BIN_DIR/ast-grep" --version
