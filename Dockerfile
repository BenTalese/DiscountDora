# Monolithic dev/prod image. Phase D / FU-186: dora_api runs alongside
# nginx serving the built SPA. The retailer-scraping `merchant_api` +
# the deals `emailer` live in the sibling **dora-companion** repo now.
# See compose.yml for the runtime story + nginx.conf for the SPA host
# config.
FROM python:3.11-slim AS develop-stage

# System packages:
#   nodejs + npm  — frontend build (Quasar/Vite). Debian Bookworm ships
#                   Node 18, the minimum Quasar 2 supports; bump to
#                   NodeSource Node 20+ when you next touch this.
#   nginx         — D1: replaces `quasar serve` for serving the static
#                   SPA in the runtime container.
#   curl          — used by the HEALTHCHECK directive below.
RUN apt-get update \
    && apt-get install -y --no-install-recommends nodejs npm nginx curl \
    && npm install -g @quasar/cli \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# ── Python deps (kept in their own layer so source changes don't bust them) ──
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Piper neural-TTS engine for Dora's voice. Installed here, NOT pinned in
# requirements.txt (R-018 / ADR-013): piper-tts can't install on the Windows
# desktop build, so it would break `pip install -r requirements.txt` there —
# but the Linux container ships it so the neural voice works out of the box.
# Voice models are downloaded on demand into the data volume via Settings →
# Voice (features/tts/voice_provision); if this install ever fails the app
# still runs and falls back to the browser voice.
RUN pip install --no-cache-dir piper-tts==1.2.0

# ── Frontend deps. Critical: install inside /app/web_app so `quasar build`
#    can find node_modules there. The previous Dockerfile ran npm install in
#    /app, which left /app/web_app without a node_modules directory and broke
#    the build step. ───────────────────────────────────────────────────────
WORKDIR /app/web_app
COPY web_app/package*.json ./
RUN npm install

# ── Source code (after deps so editing source doesn't bust the npm cache).
#    `.dockerignore` excludes node_modules so the COPY here doesn't wipe the
#    install above. ─────────────────────────────────────────────────────────
WORKDIR /app
COPY . .

# ── Frontend build ─────────────────────────────────────────────────────────
WORKDIR /app/web_app
RUN quasar build

# ── nginx site config + drop the stock default ─────────────────────────────
RUN rm -f /etc/nginx/sites-enabled/default \
    && rm -f /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/dora.conf

# ── Runtime ────────────────────────────────────────────────────────────────
WORKDIR /app
EXPOSE 5170 5174

# D1: container-level healthcheck. Hits nginx's lightweight /healthz
# (doesn't exercise the Python APIs, so a wedged API doesn't fail the
# whole container — the SPA still serves while you debug). Tweak with
# `compose.yml > healthcheck:` for stricter probes.
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl --fail --silent http://localhost:5174/healthz || exit 1

COPY startup.sh /usr/local/bin/startup.sh
RUN chmod +x /usr/local/bin/startup.sh
CMD ["bash", "/usr/local/bin/startup.sh"]
