#!/usr/bin/env bash
#
# Restart the local dev backend. Runnable from anywhere.
#
#   scripts/dev-restart.sh          # restart the dev backend on :5170
#   scripts/dev-restart.sh 5171     # ...or whichever port
#   scripts/dev-restart.sh --stop   # stop only
#   scripts/dev-restart.sh --fg     # run in the foreground (Ctrl-C to quit)
#
# Why this exists: `is_reloader_enabled()` returns False, so the API never
# picks up a Python change on its own — every backend edit needs a bounce, and
# doing it by hand means hunting a PID and remembering the venv path.
#
# It kills *only* the process listening on the given port, so the scratch
# instances on 5171/5172 are safe when you restart 5170 and vice versa.
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="$REPO/.venv/bin/python"
PORT=5170
MODE=bg

for arg in "$@"; do
    case "$arg" in
        --stop) MODE=stop ;;
        --fg)   MODE=fg ;;
        [0-9]*) PORT="$arg" ;;
        *) echo "usage: $(basename "$0") [PORT] [--stop|--fg]" >&2; exit 2 ;;
    esac
done

LOG="$REPO/data/logs/dev-backend-$PORT.log"

# Whoever is listening on $PORT. Three probes because boxes differ in which of
# these is installed; all three are read-only.
pid_on_port() {
    { ss -ltnpH "sport = :$PORT" 2>/dev/null | grep -oP 'pid=\K[0-9]+' \
        || lsof -tiTCP:"$PORT" -sTCP:LISTEN 2>/dev/null \
        || fuser "$PORT"/tcp 2>/dev/null; } | tr -s ' \n' '\n' | head -n1
}

stop() {
    local pid; pid="$(pid_on_port)"
    if [[ -z "$pid" ]]; then
        echo "· nothing listening on :$PORT"
        return 0
    fi
    echo "· stopping pid $pid on :$PORT"
    kill "$pid" 2>/dev/null
    # SIGTERM, then escalate. 10s is generous for a Flask dev server.
    for _ in $(seq 20); do
        sleep 0.5
        [[ -z "$(pid_on_port)" ]] && { echo "· stopped"; return 0; }
    done
    echo "· did not exit on SIGTERM — sending SIGKILL"
    kill -9 "$pid" 2>/dev/null
    sleep 1
    [[ -z "$(pid_on_port)" ]] || { echo "!! :$PORT still held by $(pid_on_port)" >&2; return 1; }
    echo "· stopped"
}

start() {
    [[ -x "$PYTHON" ]] || { echo "!! no venv python at $PYTHON" >&2; exit 1; }
    mkdir -p "$(dirname "$LOG")"
    cd "$REPO" || exit 1

    if [[ "$MODE" == fg ]]; then
        echo "· starting on :$PORT (foreground)"
        exec "$PYTHON" -m dora_api.startup
    fi

    echo "· starting on :$PORT — log: $LOG"
    nohup "$PYTHON" -m dora_api.startup >>"$LOG" 2>&1 &
    local pid=$!

    # Wait for it to actually serve, not just for the process to exist. A boot
    # that dies on a migration exits quickly and would otherwise look like a
    # successful restart.
    for _ in $(seq 60); do
        sleep 0.5
        if ! kill -0 "$pid" 2>/dev/null; then
            echo "!! backend exited during boot — last 20 log lines:" >&2
            tail -n 20 "$LOG" >&2
            exit 1
        fi
        if curl -fsS --max-time 2 "http://127.0.0.1:$PORT/api/health" >/dev/null 2>&1; then
            echo "· up on http://localhost:$PORT (pid $pid)"
            return 0
        fi
    done

    echo "!! no healthy response on :$PORT after 30s — last 20 log lines:" >&2
    tail -n 20 "$LOG" >&2
    exit 1
}

stop || exit 1
[[ "$MODE" == stop ]] && exit 0
start
