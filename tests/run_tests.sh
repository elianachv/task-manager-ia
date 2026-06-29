#!/usr/bin/env bash
# Ejecuta la suite completa con logs, informe final y E2E en navegador visible.
set -euo pipefail
cd "$(dirname "$0")"
source ../backend/venv/bin/activate
pytest "$@"
