#!/usr/bin/env bash
set -euo pipefail

RG_VERSION="${JULES_RIPGREP_VERSION:-15.2.0}"
FD_VERSION="${JULES_FD_VERSION:-10.5.0}"
ROOT="${JULES_CAP_ROOT:-$HOME/.local/jules-cap}"
INSTALL_DIR="$ROOT/search-tools/rg-$RG_VERSION-fd-$FD_VERSION"
BIN_DIR="$HOME/.local/bin"

mkdir -p "$INSTALL_DIR" "$BIN_DIR"

case "$(uname -m)" in
  x86_64|amd64)
    RG_TARGET="x86_64-unknown-linux-musl"
    RG_SHA256="33e15bcf1624b25cdd2a55813a47a2f95dbe126268203e76aa6a585d1e7b149c"
    FD_TARGET="x86_64-unknown-linux-musl"
    FD_SHA256="761c72dc8e120d85b22292063be8a796e2eeb20eb3e4f38b8fa2343ccf3514a7"
    ;;
  aarch64|arm64)
    RG_TARGET="aarch64-unknown-linux-musl"
    RG_SHA256="800b1e7206afe799dfb5a6901f23147cfaabe0e52210538100f61e86e1740915"
    FD_TARGET="aarch64-unknown-linux-musl"
    FD_SHA256="d76c4317f7d5dba69f8a2a15856c90c777e7f0dd4e85f0de8c76de6992c374d4"
    ;;
  *)
    echo "Unsupported architecture for pinned search tools: $(uname -m)" >&2
    exit 1
    ;;
esac

RG_BIN="$INSTALL_DIR/rg"
FD_BIN="$INSTALL_DIR/fd"

install_rg() (
  set -euo pipefail
  local tmpdir archive url src
  tmpdir="$(mktemp -d)"
  trap 'rm -rf "$tmpdir"' EXIT
  archive="ripgrep-$RG_VERSION-$RG_TARGET.tar.gz"
  url="https://github.com/BurntSushi/ripgrep/releases/download/$RG_VERSION/$archive"

  echo "Downloading ripgrep $RG_VERSION for $RG_TARGET..."
  curl --fail --silent --show-error --location "$url" -o "$tmpdir/$archive"
  printf '%s  %s\n' "$RG_SHA256" "$tmpdir/$archive" | sha256sum --check --status

  tar -xzf "$tmpdir/$archive" -C "$tmpdir"
  src="$tmpdir/ripgrep-$RG_VERSION-$RG_TARGET/rg"
  install -m 0755 "$src" "$RG_BIN"
)

install_fd() (
  set -euo pipefail
  local tmpdir archive url src
  tmpdir="$(mktemp -d)"
  trap 'rm -rf "$tmpdir"' EXIT
  archive="fd-v$FD_VERSION-$FD_TARGET.tar.gz"
  url="https://github.com/sharkdp/fd/releases/download/v$FD_VERSION/$archive"

  echo "Downloading fd $FD_VERSION for $FD_TARGET..."
  curl --fail --silent --show-error --location "$url" -o "$tmpdir/$archive"
  printf '%s  %s\n' "$FD_SHA256" "$tmpdir/$archive" | sha256sum --check --status

  tar -xzf "$tmpdir/$archive" -C "$tmpdir"
  src="$tmpdir/fd-v$FD_VERSION-$FD_TARGET/fd"
  install -m 0755 "$src" "$FD_BIN"
)

if [[ ! -x "$RG_BIN" ]] || [[ "$("$RG_BIN" --version 2>/dev/null | head -1)" != "ripgrep $RG_VERSION" ]]; then
  install_rg
fi

if [[ ! -x "$FD_BIN" ]] || [[ "$("$FD_BIN" --version 2>/dev/null | head -1)" != "fd $FD_VERSION" ]]; then
  install_fd
fi

ln -sfn "$RG_BIN" "$BIN_DIR/rg"
ln -sfn "$FD_BIN" "$BIN_DIR/fd"

echo "Core search tools ready:"
"$BIN_DIR/rg" --version | head -1
"$BIN_DIR/fd" --version | head -1
