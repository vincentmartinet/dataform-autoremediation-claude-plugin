#!/usr/bin/env bash
set -euo pipefail

PID_FILE="/tmp/dataform-scout.pid"

if [ -f "$PID_FILE" ]; then
  pid=$(cat "$PID_FILE")
  if kill -0 "$pid" 2>/dev/null; then
    exit 0
  fi
fi

nohup python3 "${CLAUDE_PLUGIN_ROOT}/src/scout_daemon.py" \
  > /tmp/dataform-scout.log 2>&1 &
echo $! > "$PID_FILE"
