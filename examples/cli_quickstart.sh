#!/usr/bin/env bash
set -euo pipefail

export COGNOS_BASE_URL="http://127.0.0.1:8788"
export COGNOS_API_KEY=""
export COGNOS_UPSTREAM_AUTH="Bearer YOUR_UPSTREAM_KEY"

cognos chat "Explain the EU AI Act risk levels in one paragraph" --mode monitor

# If you got a trace id from output, fetch it:
# cognos trace tr_xxxxxxxxxxxx
