#!/usr/bin/env bash
set -euo pipefail

VERSION="${JULES_SERENA_VERSION:-1.7.0}"
ROOT="${JULES_CAP_ROOT:-$HOME/.local/jules-cap}"
INSTALL_DIR="$ROOT/serena-$VERSION"
SERENA="$INSTALL_DIR/venv/bin/serena"
REPO="${JULES_REPO:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
LAB_DIR="${JULES_LAB_DIR:-/tmp/jules-lab}"
SERENA_HOME="${JULES_SERENA_HOME:-$LAB_DIR/serena-home}"
PROJECT_DATA="${JULES_SERENA_PROJECT_DATA:-$LAB_DIR/serena-projects}"

if [[ ! -x "$SERENA" ]]; then
  JULES_REPO="$REPO" bash "${JULES_CAP_RUNTIME_DIR:?}/bootstrap-serena.sh" >&2
fi

mkdir -p "$SERENA_HOME" "$PROJECT_DATA"

cat >"$SERENA_HOME/serena_config.yml" <<EOF
language_backend: LSP
agent_interface: tools
gui_log_window: false
web_dashboard: false
web_dashboard_open_on_launch: false
log_level: 30
trace_lsp_communication: false
project_serena_folder_location: "$PROJECT_DATA/\$projectFolderName/.serena"
trusted_project_path_patterns:
  - "**"
projects: []
EOF

export SERENA_HOME

exec "$SERENA" start-mcp-server \
  --project-from-cwd \
  --context agent \
  --enable-web-dashboard false \
  --open-web-dashboard false \
  --enable-gui-log-window false \
  --log-level WARNING \
  --tool-timeout "${JULES_SERENA_TOOL_TIMEOUT:-120}"
