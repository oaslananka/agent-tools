#!/usr/bin/env bash
set -euo pipefail

VERSION="${JULES_PLAYWRIGHT_MCP_VERSION:-0.0.82}"
ROOT="${JULES_CAP_ROOT:-$HOME/.local/jules-cap}"
INSTALL_DIR="$ROOT/playwright-mcp-$VERSION"
BROWSERS_DIR="$ROOT/playwright-browsers-$VERSION"
MARKER="$INSTALL_DIR/.installed-version"
BROWSER_MARKER="$BROWSERS_DIR/.playwright-mcp-browser-version"
DEPS_MARKER="$ROOT/playwright-system-deps-$VERSION.ok"

mkdir -p "$ROOT"

needs_install=0
if [[ ! -x "$INSTALL_DIR/node_modules/.bin/playwright-mcp" ]]; then
  needs_install=1
elif [[ ! -f "$MARKER" ]] || [[ "$(cat "$MARKER" 2>/dev/null || true)" != "$VERSION" ]]; then
  needs_install=1
fi

if (( needs_install )); then
  echo "Installing Playwright MCP $VERSION..."
  rm -rf "$INSTALL_DIR"
  mkdir -p "$INSTALL_DIR"
  npm install --prefix "$INSTALL_DIR" --no-audit --no-fund --omit=dev "@playwright/mcp@$VERSION"
  printf '%s\n' "$VERSION" > "$MARKER"
fi

PW="$INSTALL_DIR/node_modules/.bin/playwright"
SERVER="$INSTALL_DIR/node_modules/.bin/playwright-mcp"
if [[ ! -x "$PW" || ! -x "$SERVER" ]]; then
  echo "Playwright binaries missing after MCP install." >&2
  exit 3
fi

mkdir -p "$BROWSERS_DIR"

# Install browser system dependencies when passwordless sudo is available. This is
# run during Jules environment setup so the result is captured in the snapshot.
if [[ "${JULES_PLAYWRIGHT_INSTALL_SYSTEM_DEPS:-0}" == "1" ]] && [[ ! -f "$DEPS_MARKER" ]]; then
  if sudo -n true >/dev/null 2>&1; then
    if sudo -n env PLAYWRIGHT_BROWSERS_PATH="$BROWSERS_DIR" "$PW" install-deps chromium >/tmp/jules-playwright-install-deps.log 2>&1; then
      touch "$DEPS_MARKER"
    else
      echo "WARNING: Playwright system dependency install failed; continuing because the Jules base image may already provide the required libraries. See /tmp/jules-playwright-install-deps.log" >&2
    fi
  else
    echo "WARNING: passwordless sudo unavailable; skipping optional Playwright system dependency installation." >&2
  fi
fi

browser_ready=0
if [[ -f "$BROWSER_MARKER" ]] && [[ "$(cat "$BROWSER_MARKER" 2>/dev/null || true)" == "$VERSION" ]]; then
  if find "$BROWSERS_DIR" -type f -path '*/chrome-linux64/chrome' -perm -111 -print -quit 2>/dev/null | grep -q .; then
    browser_ready=1
  fi
fi

if [[ "${JULES_PLAYWRIGHT_SKIP_BROWSER_INSTALL:-0}" != "1" ]] && (( ! browser_ready )); then
  # Playwright MCP expects its Chrome for Testing build. Using the generic
  # Playwright "install chromium" command is insufficient for browser_navigate.
  PLAYWRIGHT_BROWSERS_PATH="$BROWSERS_DIR" "$SERVER" install-browser chrome-for-testing
  printf '%s\n' "$VERSION" > "$BROWSER_MARKER"
fi

echo "Playwright MCP ready:"
echo "  version: $VERSION"
echo "  server: $INSTALL_DIR/node_modules/.bin/playwright-mcp"
echo "  browsers: $BROWSERS_DIR"
