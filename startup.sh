#!/bin/bash
# DiscountDora monolithic-container entrypoint.
#
# Starts the Python services in the background and finishes with nginx
# in the foreground so the container's lifecycle matches nginx's (when
# nginx dies, the container exits — Docker's expected behaviour). The
# emailer is gated behind DORA_EMAIL_ENABLED so containers without
# SMTP configured don't crash on boot.
#
# Env vars consumed (all optional, sensible defaults baked in):
#   DORA_EMAIL_ENABLED  — "true" to spin up the emailer service
#   DORA_DATA_DIR       — sqlite + uploads dir (default /app/data)
#   DORA_CACHE_DIR      — image / scraped-json cache (default /app/cache)
#   DORA_LOG_DIR        — log directory (default /app/data/logs)
#   DORA_DB_PATH        — explicit db file location (overrides DATA_DIR)
# See `.env.example` at the repo root for the full env catalogue.

set -e

echo "[startup] DiscountDora — booting monolithic container"
echo "[startup] DATA_DIR=${DORA_DATA_DIR:-/app/data} CACHE_DIR=${DORA_CACHE_DIR:-/app/cache} LOG_DIR=${DORA_LOG_DIR:-/app/data/logs}"
echo "[startup] EMAIL_ENABLED=${DORA_EMAIL_ENABLED:-false}"

# Pre-create the standard data directories so the Python processes
# don't race each other on first boot.
mkdir -p \
    "${DORA_DATA_DIR:-/app/data}" \
    "${DORA_CACHE_DIR:-/app/cache}" \
    "${DORA_LOG_DIR:-/app/data/logs}"

# ── Python services (background) ─────────────────────────────────────
python -m dora_api.startup &
DAPI_PID=$!
echo "[startup] dora_api pid=$DAPI_PID"

python -m merchant_api.startup &
MAPI_PID=$!
echo "[startup] merchant_api pid=$MAPI_PID"

if [ "${DORA_EMAIL_ENABLED:-false}" = "true" ]; then
    python -m emailer.startup &
    EMAILER_PID=$!
    echo "[startup] emailer pid=$EMAILER_PID"
else
    echo "[startup] emailer disabled (set DORA_EMAIL_ENABLED=true to enable)"
fi

# ── nginx in foreground ──────────────────────────────────────────────
# `daemon off;` keeps nginx attached to PID 1's stdout/stderr so
# `docker logs` works without extra plumbing.
echo "[startup] nginx (foreground) serving SPA on :5174"
exec nginx -g "daemon off;"
