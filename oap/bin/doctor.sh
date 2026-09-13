#!/usr/bin/env bash
# doctor.sh — readiness in separate dimensions (structural/setup/operational/adoption).
# Read-only; never activates, publishes or mutates. DEFAULT LEVEL: all.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$DIR/oap_doctor.py" "$@"
