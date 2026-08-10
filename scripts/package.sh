#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
DIST_DIR="${REPO_DIR}/dist"

mkdir -p "${DIST_DIR}"
rm -f "${DIST_DIR}/security-godmode.zip" "${DIST_DIR}/security-godmode.evop"
(
  cd "${REPO_DIR}/plugin"
  zip -qrD "${DIST_DIR}/security-godmode.zip" . \
    -x '*/__pycache__/*' '*.pyc' '*.pyo'
)
cp "${DIST_DIR}/security-godmode.zip" "${DIST_DIR}/security-godmode.evop"
printf '%s\n' "Built:"
printf '  %s\n' "${DIST_DIR}/security-godmode.zip"
printf '  %s\n' "${DIST_DIR}/security-godmode.evop"
