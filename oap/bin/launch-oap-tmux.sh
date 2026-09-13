#!/usr/bin/env bash
# launch-oap-tmux.sh — operational tmux session, gated on doctor operational
# readiness first (activation enabled, attributable authority, qualified argv/models,
# no test adapters). Setup mode remains available via launch-setup-tmux.sh.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$DIR/oap_launch.py" oap-tmux "$@"
