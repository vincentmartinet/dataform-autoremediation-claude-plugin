#!/usr/bin/env bash
set -euo pipefail

PID_FILE="/tmp/dataform-scout.pid"
CONFIG_FILE="${HOME}/.config/dataform-scout/config"

# Already running — nothing to do
if [ -f "$PID_FILE" ]; then
  pid=$(cat "$PID_FILE")
  if kill -0 "$pid" 2>/dev/null; then
    exit 0
  fi
fi

# No config yet — ask Claude to run /scout-configure before starting
if [ ! -f "$CONFIG_FILE" ]; then
  printf '{"systemMessage": "Dataform Scout is not configured yet. Please run /scout-configure to choose which GCP project, folder, or organization to watch. The daemon will start automatically once configured."}\n'
  exit 0
fi

# Load scope flags from config
scope_type=""
scope_id=""
while IFS='=' read -r key value; do
  case "$key" in
    scope_type) scope_type="$value" ;;
    scope_id)   scope_id="$value" ;;
  esac
done < "$CONFIG_FILE"

SCOPE_FLAG=""
case "$scope_type" in
  project)      SCOPE_FLAG="--project=${scope_id}" ;;
  folder)       SCOPE_FLAG="--folder=${scope_id}" ;;
  organization) SCOPE_FLAG="--organization=${scope_id}" ;;
  *)
    printf '{"systemMessage": "Dataform Scout config is invalid (unknown scope_type). Please run /scout-configure to fix it."}\n'
    exit 0
    ;;
esac

nohup python3 "${CLAUDE_PLUGIN_ROOT}/src/scout_daemon.py" \
  > /tmp/dataform-scout.log 2>&1 &
echo $! > "$PID_FILE"

printf '{"systemMessage": "Dataform Scout started — listening to %s logs (%s)."}\n' "$scope_type" "$scope_id"
