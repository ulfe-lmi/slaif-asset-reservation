#!/usr/bin/env bash
# launch-setup-tmux.sh — isolated setup tmux session (OP-08): one owned socket,
# two side-by-side shells (strategy left in STRATEGIC_HOME, coding right in REPO).
# Works with no model/auth/remote configured and activates nothing. --print-only.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$DIR/oap_launch.py" setup-tmux "$@"
