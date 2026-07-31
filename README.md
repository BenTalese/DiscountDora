<p align="center">
    <img alt="Dashy Dora" src=".github/publication_assets/Banner.png" />
</p>

<h3 align="center">Your pantry at your fingertips.</h3>

<p align="center">
    <em>A fast, private, self-hosted kitchen companion — track your stock, plan meals,<br/>
    cook from what you have, and never overpay. Free &amp; open-source.</em>
</p>

<p align="center">
    <img alt="MIT Licence" src="https://img.shields.io/github/license/BenTalese/dashy-dora?style=flat" />
    <img alt="Build" src="https://img.shields.io/github/actions/workflow/status/BenTalese/dashy-dora/ci.yml?label=build" />
    <img alt="Latest release" src="https://img.shields.io/github/v/release/BenTalese/dashy-dora" />
    <img alt="Commits since latest release" src="https://img.shields.io/github/commits-since/BenTalese/dashy-dora/latest" />
    <img alt="Made with Vue &amp; Flask" src="https://img.shields.io/badge/stack-Vue%203%20%C2%B7%20Quasar%20%C2%B7%20Flask-42b883" />
</p>

<p align="center">
    <a href="#-what-is-dora">What is it?</a> ·
    <a href="#-see-it-in-action">Screenshots</a> ·
    <a href="#-features">Features</a> ·
    <a href="#-get-started">Get started</a> ·
    <a href="#-support-dora">Support</a> ·
    <a href="#-contributing">Contributing</a>
</p>

> **Status: pre-release.** Dora is being actively finished — it runs well and is
> feature-rich, but there's no tagged, packaged release yet. You can run it
> locally or via Docker today (see [Get started](#-get-started)).

<br/>

## 🍔 What is Dora?

Dashy Dora started as a simple idea: keep track of everything edible in the house
**without getting bogged down in detail**. Why agonise over exactly how many tea
bags you have? What people actually need is something *faster* than walking to the
freezer and rummaging through baskets for the salmon.

Most existing tools were overcomplicated for something that should be extremely
fast and to the point. That's the core principle of Dora — **your pantry at your
fingertips** — and the basis for everything it does. From there, the ideas kept
growing: shopping lists, recipes, cook mode, meal plans, personal price history,
a friendly assistant, and more — all in one place, so you never have to reach for
an external tool.

Dora is **free, open-source, and self-hosted** — it runs on your machine, your
data never leaves the box by default, and there's nothing to pay for. If you find
it useful, [donations](#-support-dora) are hugely appreciated but never required.

<br/>

## 📽️ See it in action

> _GIFs and screenshots are on the way. The placeholders below mark where each
> one lands — drop the assets into `.github/publication_assets/` and swap the
> caption for the image._

<!-- GIF: Dashboard overview — .github/publication_assets/dashboard.gif -->
| | |
|---|---|
| **🏠 Dashboard** <br/> _Coming soon_ | **📦 Stock at a glance** <br/> _Coming soon_ |
| **🍳 Cook mode** <br/> _Coming soon_ | **🛒 Shopping lists** <br/> _Coming soon_ |
| **📅 Meal plans** <br/> _Coming soon_ | **💬 Ask Dora (assistant)** <br/> _Coming soon_ |

<!--
    When adding a real asset, replace a cell with:
    ![Dashboard](.github/publication_assets/dashboard.gif)
    Keep them trimmed (< ~5 MB) so the README stays quick to load.
-->

<br/>

## ✨ Features

- **📦 Stock tracking** — know what you have and get nudged about that six-month-old
  salmon in the freezer. Locations as a simple tree, groups, expiry & low-stock alerts.
- **🛒 Shopping lists** — a DRAFT → SHOPPING → DONE flow that lives right where you
  track stock; auto-draft a shop from what's running low.
- **🍳 Cook mode** — a hands-free, step-by-step cooking view that knows what you have.
- **📖 Recipes** — store your favourites, paste-import from anywhere, and instantly
  see whether you can cook something tonight.
- **📅 Meal plans** — plan the week, see shortfalls, and turn a plan into a shop.
- **💬 Ask Dora** — a friendly assistant. Works great with **no LLM at all** (the
  default), or bring your own model (Ollama, or OpenAI / Anthropic / Gemini keys).
- **💸 Personal price intelligence** — Dora remembers what *you* paid, so it can tell
  you when something's a genuinely good buy.
- **🔔 Alerts** — expiry, low-stock, price-watch, e-mail digests, and web push.
- **📱 Runs everywhere** — installable PWA, a native mobile app, and desktop bundles
  for Windows / macOS / Linux.
- **🎨 Themes, backup/restore, export/print, multi-user** — and flexible feature
  toggles so you can hide anything you don't care about.

<br/>

## 🚀 Get started

There's no packaged release yet, so run it locally for development or spin up the
Docker stack for a closer-to-production look.

### Prerequisites

| Tool | Minimum version | Notes |
|------|----------------|-------|
| Python | 3.11 | [python.org](https://www.python.org/downloads/) — tick "Add to PATH" on Windows |
| Node.js | 18 LTS | [nodejs.org](https://nodejs.org) or via nvm / nvm-windows |
| Quasar CLI | latest | `npm install -g @quasar/cli` |
| Git | any | — |

### 1 — Clone and copy env files

```bash
git clone https://github.com/BenTalese/dashy-dora.git
cd dashy-dora
```

Copy the two env templates and leave the defaults for local dev:

**Windows (PowerShell):**
```powershell
Copy-Item .env.example .env
Copy-Item web_app\.env.example web_app\.env
```

**Linux / macOS:**
```bash
cp .env.example .env
cp web_app/.env.example web_app/.env
```

### 2 — Backend (Python / Flask)

**Start Postgres first** (the standard datastore — see Decision 5 in `docs/01_charter/RECONCILED_FINISHING_PLAN.md`):

```bash
docker compose -f compose.dev.yml up -d postgres
```

> The `-f compose.dev.yml` is deliberate — the dev Postgres lives in its own
> compose file so it doesn't collide with the production self-host stack in
> `compose.yml`.

**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1      # if blocked: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
pip install -r requirements.txt
flask --app dora_api.app db upgrade
python -m dora_api.startup
```

**Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
flask --app dora_api.app db upgrade
python -m dora_api.startup
```

The API listens on **http://localhost:5170**.

> **First run:** `flask db upgrade` creates the Dora schema in the Postgres instance from `compose.dev.yml` (`postgres://dora:dora@localhost:5432/dora`).
> If you want a fresh database on every startup (dev only), set `DORA_ALLOW_DESTRUCTIVE=true` in `.env`.
>
> **Lightweight self-host on SQLite:** set `DORA_DB_PATH=./data/dora.data.db` (any filesystem path will do — the app builds the SQLite URL for you) and skip the `docker compose` step. Postgres is the standard target but SQLite is still supported for zero-dependency installs. For non-default cases (remote Postgres, in-memory SQLite, custom driver) use `DORA_DB_URL` with a full SQLAlchemy URL — it overrides `DORA_DB_PATH`.

### 3 — Frontend (Quasar / Vue 3)

In a second terminal:

**Windows (PowerShell):**
```powershell
cd web_app
npm install
quasar dev
```

**Linux / macOS:**
```bash
cd web_app
npm install
quasar dev
```

The SPA opens on **http://localhost:5174** and hot-reloads on file changes.

> If `quasar` is not found: `npm install -g @quasar/cli` then try again.

### 4 — (Optional) Docker — full stack in one command

Requires Docker Desktop (Windows/macOS) or Docker Engine + Compose v2 (Linux).

```bash
docker compose up --build
```

Ports exposed:
- `5170` — dora_api
- `5172` — merchant_api
- `5174` — SPA (served by nginx)

Data is persisted in named Docker volumes (`dora_data`, `dora_cache`, `dora_logs`). Use `docker compose down -v` to clear them.

<details>
<summary><strong>More: quick reference, push notifications, AI assistant, desktop bundles, releasing</strong></summary>

### Local dev quick reference

- Copy `.env.example` → `.env` and `web_app/.env.example` → `web_app/.env`. Adjust as needed.
- Set `DORA_ALLOW_DESTRUCTIVE=true` only when you intentionally want to drop & re-seed the database on startup. Debug mode no longer auto-wipes data.
- Apply schema changes: `flask db migrate -m "<description>"` (review the generated file — see [dora_api/persistence/migrations/README](dora_api/persistence/migrations/README)) then `flask db upgrade`.
- List endpoints accept standard query params: `?filter=name:ct:pasta&filter=is_favourite:eq:true&sort=name:asc&page=1&limit=50`. Responses are `{ items, total, page, limit }`.

### Push notifications (optional, VAPID keys)

Alerts that fire while the SPA is closed are delivered via the Web Push protocol (RFC 8030), which authenticates the application server to the push service via VAPID (RFC 8292). Without keys configured, `push_sender.py` runs in **dry-run** mode — pushes are logged but never sent, and the frontend's Push toggle stays hidden.

1. **Generate a key pair** with `py-vapid` (bundled with `pywebpush`):
   ```bash
   python -m py_vapid --gen --applicationServerKey
   ```
   Writes `private_key.pem` to the current directory and prints the matching base64url-encoded public key to stdout. Treat the private key like any other secret.
2. **Configure the keys** at **Settings → Admin → System → Push notifications** (all three fields live on `AppSetting`; the private key is stored encrypted-at-rest, wrapped by `DORA_LLM_KEY_ENCRYPTION_KEY`). Paste the public key + private key into the admin form and set `Subject` to your contact URL. All fields flip to dry-run when either half is missing.
3. No restart needed — the resolver picks up the row on the next call. The **Settings → Notifications → Push** toggle appears once both halves are configured.

### AI assistant (optional, bring-your-own-LLM, per-user)

Dora's chat can be backed by a language model — Ollama you host yourself, or OpenAI / Anthropic / Google Gemini via your own API key. AI mode is configured **per account** and is off by default; the no-LLM **Basic** assistant is the default and stays fully useful.

Setup: (1) admin confirms the master switch is on at **Settings → System → AI assistant**; (2) each account that wants AI goes to **Settings → Assistant**, picks a provider, fills in URL/model (Ollama) or API key + model (paid), and turns AI mode on. There's a **Test connection** button. For Ollama, `ollama pull qwen2.5:7b` + `ollama serve` is the canonical setup; the model must be tool-capable (qwen2.5, llama3.1, gpt-oss, etc.).

**Paid providers (one operator step):** set `DORA_LLM_KEY_ENCRYPTION_KEY` so per-user API keys can be stored encrypted at rest (Ollama doesn't need this):
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```
Put the output into the API server's environment. Rotating the key invalidates every saved API key.

**Network topology note:** the Dora **backend** reaches the LLM, not your browser. On a single box the base URL is `http://localhost:11434`; on a split setup the backend must be able to reach wherever the LLM runs (LAN routing / Tailscale / port forward).

### Desktop bundles

The desktop app is [pywebview](https://pywebview.flowrl.com/) wrapping the SPA — GTK/WebKit on Linux, WebView2 on Windows, WKWebView on macOS. One PyInstaller spec (`dora.spec`); three thin platform build scripts under `packaging/`.

**Linux (AppImage):**
```bash
sudo apt install python3.11-dev libpython3.11 python3-gi gir1.2-webkit2-4.1 \
                 libgirepository1.0-dev libcairo2-dev
pip install -r requirements.txt
./packaging/build-linux.sh --clean --appimage
chmod +x dist/Dora-v*-x86_64.AppImage && ./dist/Dora-v*-x86_64.AppImage
```
Data persists to `~/.local/share/Dora/`.

**Windows (PowerShell):**
```powershell
pip install -r requirements.txt
.\packaging\build-windows.ps1 -Clean
.\dist\Dora\Dora.exe
```
Uses WebView2 (ships with Windows 10/11). Data persists to `%LOCALAPPDATA%\Dora\`.

**macOS:**
```bash
pip install -r requirements.txt
./packaging/build-macos.sh --clean
./dist/Dora/Dora
```
Auto-detects Apple Silicon vs Intel. Requires Xcode command-line tools. Data persists to `~/Library/Application Support/Dora/`.

### Releasing (manual, push-the-button)

CI runs on every push and PR ([.github/workflows/ci.yml](.github/workflows/ci.yml)) — frontend lint + typecheck + build, dora_api pytest, merchant + emailer compile-check. **CI never publishes anything.** Releases are explicit:

1. Land your changes on `main` and confirm CI is green for that SHA.
2. Update the `## [Unreleased]` block in `CHANGELOG.md` — whatever sits there becomes the GitHub Release body.
3. Go to **Actions → Release → Run workflow**, type a version like `v0.3.0`, and run it.
4. The workflow validates the version, builds the Docker image, pushes to `ghcr.io/bentalese/dashydora:vX.Y.Z` **and** `:latest`, then cuts the GitHub Release. Tick **dry_run** to preview without publishing.
5. After the release lands, move the `[Unreleased]` heading down and start a fresh section.

</details>

<br/>

## 💗 Support Dora

Dora is free and open-source, built by one person in their spare time. If it saves
you time or money, chipping in keeps it alive and caffeinated — but it's always
optional, and every feature is free for everyone regardless.

<!-- FU-608: replace the PLACEHOLDER links once the accounts are live. -->
- ☕ **[Buy Me a Coffee](https://example.com/PLACEHOLDER-see-FU-608)** — a one-off thank-you.
- 💖 **[GitHub Sponsors](https://example.com/PLACEHOLDER-see-FU-608)** — recurring support.
- 🅿️ **[PayPal](https://example.com/PLACEHOLDER-see-FU-608)** — if that's easier for you.

> _Links are placeholders while the accounts are being set up — see the in-app
> **Support Dora** button or the repo's **Sponsor** button once they're live._

<br/>

## 🐞 Found a bug? 💡 Have an idea?

Please open an issue — bug reports and feature requests are very welcome.

- **[Open an issue](https://github.com/BenTalese/dashy-dora/issues/new/choose)** using one of the templates.
- For **security** issues, please follow [SECURITY.md](SECURITY.md) and report privately rather than opening a public issue.

> 🚧 _Issue templates are being added — see FU-608._

<br/>

## 🤝 Contributing

Contributions are welcome! A full contributing guide is on the way. In the
meantime: fork, branch, keep changes focused, run the linters/tests, and open a PR
against `main`. If you're planning something large, open an issue first so we can
talk it through.

> 🚧 _`CONTRIBUTING.md` is being written — see FU-608._

<br/>

## 📜 Licence

Dora is released under the **MIT Licence** — do what you like with it, just keep
the notice. See [LICENSE](LICENSE) for the full text.

<br/>

<p align="center"><em>Dora is a hobby project. The mascot is doing its best. 🍔</em></p>
