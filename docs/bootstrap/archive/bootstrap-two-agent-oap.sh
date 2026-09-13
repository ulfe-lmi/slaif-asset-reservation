#!/usr/bin/env bash
# bootstrap-two-agent-oap.sh — plan/apply/refresh the manifest-owned two-workspace
# materialization. DEFAULT IS DRY RUN: no writes, no temp files, no FIFO creation,
# no Git mutation, no model invocation. No activation or publication ever happens here.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$DIR/oap_materialize.py" "$@"
