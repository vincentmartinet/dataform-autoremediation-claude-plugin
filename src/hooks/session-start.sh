#!/usr/bin/env bash
set -euo pipefail

PID_FILE="/tmp/dataform-scout.pid"
CONFIG_FILE="${HOME}/.config/dataform-scout/config"

if ! command -v python3 &> /dev/null; then
  printf '{"systemMessage": "Dataform Scout requires Python 3 to be installed. Please install Python 3 and try again."}\n'
  exit 0
fi

if ! python3 -c "import grpc" &> /dev/null; then
  printf '{"systemMessage": "Dataform Scout requires the python grpcio package for gcloud live tailing. Please install it (e.g., `sudo pip3 install grpcio`) and try again."}\n'
  exit 0
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

# Already running — print status and exit
if [ -f "$PID_FILE" ]; then
  pid=$(cat "$PID_FILE")
  if kill -0 "$pid" 2>/dev/null; then
    printf '{"systemMessage": "Dataform Scout daemon is already running — listening to %s logs (%s)."}\n' "$scope_type" "$scope_id"
    exit 0
  fi
fi

cd "${CLAUDE_PLUGIN_ROOT}"
nohup python3 -m src.scout_daemon \
  > /tmp/dataform-scout.log 2>&1 &
echo $! > "$PID_FILE"

printf '{"systemMessage": "Dataform Scout started — listening to %s logs (%s)."}\n' "$scope_type" "$scope_id"
