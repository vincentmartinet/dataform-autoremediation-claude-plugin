#!/usr/bin/env bash
set -euo pipefail

PID_FILE="/tmp/dataform-scout.pid"

SESSIONS_DIR="/tmp/dataform-scout-sessions"
rm -f "${SESSIONS_DIR}/${PPID}.lock"
