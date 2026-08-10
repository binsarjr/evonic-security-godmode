#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
EVONIC_BIN="${EVONIC_BIN:-evonic}"

"${EVONIC_BIN}" plugin install "${REPO_DIR}/plugin"
"${EVONIC_BIN}" plugin enable security_godmode
printf '%s\n' 'Security Godmode installed and enabled globally.'
printf '%s\n' 'Assign its tools to an agent, then call godmode_profile(action="enable").'

