#!/usr/bin/env bash
# On-demand dependency-vulnerability scan. Runs `pip-audit` against the
# Python requirements and `npm audit` against the SPA. Prints a short
# summary; exits non-zero if either scanner reports findings.
#
# CI stays deliberately disabled on this repo (see the
# `feedback_ci_disabled_policy` memory + FU-405) so this is *manual* —
# run it before a release / whenever you fold Dependabot alerts. When
# CI comes back on at Phase 4, promote this to a scheduled job (tracked
# on FU-405).
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

pip_status=0
npm_status=0

echo "── Python (pip-audit) ────────────────────────────────────────"
if ! command -v pip-audit >/dev/null 2>&1; then
    echo "pip-audit not found. Install with:  pip install pip-audit"
    pip_status=127
else
    pip-audit -r requirements.txt --strict
    pip_status=$?
fi

echo
echo "── Frontend (npm audit) ──────────────────────────────────────"
if ! command -v npm >/dev/null 2>&1; then
    echo "npm not found."
    npm_status=127
else
    (cd web_app && npm audit)
    npm_status=$?
fi

echo
echo "── Summary ───────────────────────────────────────────────────"
echo "pip-audit exit: $pip_status"
echo "npm audit exit: $npm_status"

# Exit non-zero if either found something, so a caller (or a future CI
# job) can gate on it.
if [ "$pip_status" -ne 0 ] || [ "$npm_status" -ne 0 ]; then
    exit 1
fi
exit 0
