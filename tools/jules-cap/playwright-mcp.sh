#!/usr/bin/env bash
set -euo pipefail

VERSION="${JULES_PLAYWRIGHT_MCP_VERSION:-0.0.82}"
ROOT="${JULES_CAP_ROOT:-$HOME/.local/jules-cap}"
INSTALL_DIR="$ROOT/playwright-mcp-$VERSION"
BROWSERS_DIR="$ROOT/playwright-browsers-$VERSION"
SERVER="$INSTALL_DIR/node_modules/.bin/playwright-mcp"
REPO="${JULES_REPO:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
OUT_DIR="${JULES_PLAYWRIGHT_OUTPUT_DIR:-/tmp/jules-lab/playwright}"

# Always verify package + exact browser readiness before launching. The bootstrap
# is marker-based and becomes a fast no-op after a correct environment snapshot.
JULES_REPO="$REPO" bash "${JULES_CAP_RUNTIME_DIR:?}/bootstrap-browser.sh" >&2

if [[ ! -x "$SERVER" ]]; then
  echo "Playwright MCP server is unavailable after bootstrap: $SERVER" >&2
  exit 3
fi

mkdir -p "$OUT_DIR"

export PLAYWRIGHT_BROWSERS_PATH="$BROWSERS_DIR"

exec "$SERVER" \
  --headless \
  --browser chromium \
  --no-sandbox \
  --image-responses omit \
  --output-dir "$OUT_DIR" \
  "$@"
