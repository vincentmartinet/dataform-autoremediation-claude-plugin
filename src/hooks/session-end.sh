#!/usr/bin/env bash
set -euo pipefail

PID_FILE="/tmp/dataform-scout.pid"

if [ -f "$PID_FILE" ]; then
  pid=$(cat "$PID_FILE")
  # Check if the process is running
  if kill -0 "$pid" 2>/dev/null; then
    echo "Stopping Dataform Scout daemon (PID: $pid)..."
    kill "$pid" 2>/dev/null || true
  fi
  rm -f "$PID_FILE"
fi
