#!/usr/bin/env bash
set -euo pipefail
COMMIT="${1:-${JULES_CAP_COMMIT:-}}"
if [[ ! "$COMMIT" =~ ^[0-9a-fA-F]{40}$ ]]; then echo "usage: install.sh <40-char-agent-tools-commit>" >&2; exit 64; fi
COMMIT="${COMMIT,,}"
ROOT="${JULES_CAP_DISTRIBUTION_ROOT:-$HOME/.local/share/oaslananka-jules-cap}"
DEST="$ROOT/$COMMIT"
URL="https://codeload.github.com/oaslananka/agent-tools/tar.gz/$COMMIT"
if [[ ! -f "$DEST/.installed-commit" ]] || [[ "$(cat "$DEST/.installed-commit" 2>/dev/null || true)" != "$COMMIT" ]]; then
  tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
  mkdir -p "$ROOT"
  curl --fail --silent --show-error --location "$URL" -o "$tmp/runtime.tar.gz"
  tar -xzf "$tmp/runtime.tar.gz" -C "$tmp"
  src="$(find "$tmp" -mindepth 2 -maxdepth 2 -type d -path '*/tools/jules-cap' -print -quit)"
  [[ -n "$src" ]] || { echo "Pinned archive missing tools/jules-cap" >&2; exit 65; }
  stage="$ROOT/.stage-$COMMIT-$$"; rm -rf "$stage"; mkdir -p "$stage"
  cp -a "$src"/. "$stage"/
  printf '%s\n' "$COMMIT" > "$stage/.installed-commit"
  rm -rf "$DEST"; mv "$stage" "$DEST"
fi
export JULES_CAP_RUNTIME_DIR="$DEST"
bash "$DEST/bootstrap.sh"
