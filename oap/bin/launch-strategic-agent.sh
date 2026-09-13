#!/usr/bin/env bash
# launch-strategic-agent.sh — long-lived STRATEGIC role wrapper (OP-07).
# Starts from STRATEGIC_HOME with the full installed constitution and the private
# strategy CODEX_HOME. Logical continuity persists; handoff lives in
# workorders/STRATEGIC-HANDOFF.md. --print-only prints the exact launch plan.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$DIR/oap_launch.py" strategic "$@"
