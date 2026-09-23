#!/usr/bin/env bash
set -euo pipefail

PORT="${JULES_PLAYWRIGHT_MCP_PORT:-8931}"
HOST="${JULES_PLAYWRIGHT_MCP_HOST:-127.0.0.1}"
LAB_DIR="${JULES_LAB_DIR:-/tmp/jules-lab}"
PID_FILE="$LAB_DIR/playwright-mcp.pid"
LOG_FILE="$LAB_DIR/playwright-mcp.log"
REPO="${JULES_REPO:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
PROFILE_DIR="$LAB_DIR/playwright-profile"

mkdir -p "$LAB_DIR" "$PROFILE_DIR"

port_open() {
  timeout 1 bash -c "exec 3<>/dev/tcp/$HOST/$PORT" >/dev/null 2>&1
}

if port_open; then
  exit 0
fi

if [[ -f "$PID_FILE" ]]; then
  old_pid="$(cat "$PID_FILE" 2>/dev/null || true)"
  if [[ -n "$old_pid" ]] && kill -0 "$old_pid" 2>/dev/null; then
    kill "$old_pid" 2>/dev/null || true
    for _ in $(seq 1 30); do
      kill -0 "$old_pid" 2>/dev/null || break
      sleep 0.1
    done
  fi
  rm -f "$PID_FILE"
fi

nohup bash "${JULES_CAP_RUNTIME_DIR:?}/playwright-mcp.sh" \
  --port "$PORT" \
  --host "$HOST" \
  --shared-browser-context \
  --user-data-dir "$PROFILE_DIR" \
  >"$LOG_FILE" 2>&1 < /dev/null &
pid=$!
echo "$pid" > "$PID_FILE"

for _ in $(seq 1 300); do
  if port_open; then
    exit 0
  fi
  if ! kill -0 "$pid" 2>/dev/null; then
    echo "Playwright MCP server exited before listening." >&2
    tail -n 80 "$LOG_FILE" >&2 2>/dev/null || true
    exit 5
  fi
  sleep 0.1
done

echo "Playwright MCP did not listen on $HOST:$PORT within 30 seconds." >&2
tail -n 80 "$LOG_FILE" >&2 2>/dev/null || true
exit 6
