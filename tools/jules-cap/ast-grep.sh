#!/usr/bin/env bash
set -euo pipefail

REPO="${JULES_REPO:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
AST_GREP="$HOME/.local/bin/ast-grep"

if [[ ! -x "$AST_GREP" ]]; then
  JULES_REPO="$REPO" bash "${JULES_CAP_RUNTIME_DIR:?}/bootstrap-ast-grep.sh" >&2
fi

exec "$AST_GREP" "$@"
