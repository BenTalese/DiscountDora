# Single-stage dev image. The build/runtime split (gunicorn + nginx) is left
# commented at the bottom as a starting point for a future prod image.
FROM python:3.11-slim AS develop-stage

# Node is needed for the frontend build (Quasar/Vite). The Debian Bookworm
# `nodejs` package is Node 18, which is the minimum Quasar 2 supports — it
# works but ages quickly; bump to NodeSource Node 20+ when you next touch this.
RUN apt-get update \
    && apt-get install -y --no-install-recommends nodejs npm \
    && npm install -g @quasar/cli \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# ── Python deps (kept in their own layer so source changes don't bust them) ──
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

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

# ── Runtime ────────────────────────────────────────────────────────────────
WORKDIR /app
EXPOSE 5170 5172 5174

COPY startup.sh /usr/local/bin/startup.sh
RUN chmod +x /usr/local/bin/startup.sh
CMD ["bash", "/usr/local/bin/startup.sh"]

# ── Production image notes (switch to multi-stage when ready) ───────────────
# FROM nginx:stable-alpine AS production-stage
# COPY nginx.conf /etc/nginx/conf.d/default.conf
# COPY --from=develop-stage /app/web_app/dist/spa /usr/share/nginx/html
# Use gunicorn for the API processes and `nginx -g "daemon off;"` for the
# reverse proxy. Update startup.sh's PROD section in tandem.
