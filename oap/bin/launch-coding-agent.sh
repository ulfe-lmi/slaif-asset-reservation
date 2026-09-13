#!/usr/bin/env bash
# launch-coding-agent.sh — fresh-per-round CODING wrapper (OP-06).
# Consumes the control FIFO exactly once per wake-up, inspects durable state, then
# launches one configured Codex invocation with the private coding CODEX_HOME.
# --print-only prints the exact launch plan without any model invocation.
# Refuses: conflicting OAP_ROLE, duplicate consumer, missing/failed prerequisites.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$DIR/oap_launch.py" coding "$@"
