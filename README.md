<h3 align="center">🚨 Dora is under active development 🚨</h3>

<p align="center">
    <img alt="logo" src=".github/publication_assets/Banner.png" />
</p>
<br/>

<p align="center">
    <img alt="MIT Licence" src="https://img.shields.io/github/license/BenTalese/DashyDora?style=flat"/>
    <img alt="Awesomeness" src="https://img.shields.io/badge/Awesomeness-100%25-brightgreen" />
    <img alt="Tests" src="https://img.shields.io/github/actions/workflow/status/BenTalese/DashyDora/build-and-test.yml" />
    <img alt="Current Release" src="https://img.shields.io/github/v/release/BenTalese/DashyDora"/>
    <img alt="GitHub commits since latest release" src="https://img.shields.io/github/commits-since/bentalese/dashydora/latest">
    <img alt="GitHub commit activity" src="https://img.shields.io/github/commit-activity/m/bentalese/dashydora">
</p>

<br/>

Dora is powered by [Clapy](https://github.com/BenTalese/clapy/) 🐍, a Python clean architecture toolkit.

_Disclaimer: Dora is a hobby project of Ben Talese!_
<hr style="background-color: cyan;border:2px solid blue;border-radius:5px;">

<br/>

## 🍔 Where it all started...

Dashy Dora started out as an idea to efficiently keep track of all the edible items in the house without getting into too much detail. Why be overburdened by exactly how many tea bags you have? What people need is something that will be faster than going to the freezer and searching all the baskests for the salmon. After searching for a solution that fit this description, it soon became obvious a lot of pre-existing solutions were overcomplicated for what needed to be extremely fast and to the point. That's the core principle of Dora and the basis for all its features - your pantry at your fingertips.

And from there, the ideas continued to grow...

<br/>

## 🗺️ The Feature Roadmap (It's a Long Road...)

The **vision** for Dashy Dora is to have every single interaction with your groceries handled in the one place. No need to go to any external tools - it's all seamlessly managed with Dora!

The following is a list of Dora's planned major features. It is **not** inclusive of all the items that have been or will be added to Dora.

-   [ ] **Stock item management** - Keep track of what you have in stock and be reminded of that 6-month old salmon in the freezer.
-   [ ] **Shopping list management** - Handle your shopping list directly where you track what's in stock.
-   [ ] **Discount tracking** - Supporting all major grocery stores in Australia, see the latest deals for your favourite ice cream!
-   [ ] **Recipe management** - Store all your favourite recipes and quickly work out if you have everything you need.
-   [ ] **Barcode scanning** - Easily open stock item entries based on the barcode.
-   [ ] **Emailing** - Be alerted immediately when things go on sale, or to receive your auto-generated shopping list.
-   [ ] **Meal planning** - Manage your weekly meals with ease, selecting recipes for the week you know you'll have stock for.
-   [ ] **Backup & restore** - Save your data so you can easily come back to it at any time.
-   [ ] **Export & print** - For those who prefer to have a physical copy of their lists.
-   [ ] **Flexible features** - Freely disable features you don't care for to declutter your user experience.
-   [ ] **Nutritional information** - Supporting integration with USDA FoodData for quickly checking how many calories that pizza is.
-   [ ] **Themes** - Pick your poison.
-   [ ] **Multi-user support** - So everyone can help grab the milk on sale.
-   [ ] **Mobile app** - No server to host Dora on? We've got you covered! A mobile app is planned to support users who don't want the fuss.

<br/>

## 🚀 Want to get started?

As Dora is 🚨 <strong><i>under active development</i></strong> 🚨, there is no packaged release yet. You can run it locally for development, or spin up the Docker container for a closer-to-production look.

---

## 🛠️ Local development setup

### Prerequisites

| Tool | Minimum version | Notes |
|------|----------------|-------|
| Python | 3.11 | [python.org](https://www.python.org/downloads/) — tick "Add to PATH" on Windows |
| Node.js | 18 LTS | [nodejs.org](https://nodejs.org) or via nvm / nvm-windows |
| Quasar CLI | latest | `npm install -g @quasar/cli` |
| Git | any | — |

---

### 1 — Clone and copy env files

```bash
git clone https://github.com/BenTalese/DashyDora.git
cd DashyDora
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

---

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

---

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

---

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

---

### Local dev quick reference

- Copy `.env.example` → `.env` and `web_app/.env.example` → `web_app/.env`. Adjust as needed.
- Set `DORA_ALLOW_DESTRUCTIVE=true` only when you intentionally want to drop & re-seed the database on startup. Debug mode no longer auto-wipes data.
- Apply schema changes: `flask db migrate -m "<description>"` (review the generated file — see [dora_api/persistence/migrations/README](dora_api/persistence/migrations/README)) then `flask db upgrade`.
- List endpoints accept standard query params: `?filter=name:ct:pasta&filter=is_favourite:eq:true&sort=name:asc&page=1&limit=50`. Responses are `{ items, total, page, limit }`.
- **Push notifications (optional, VAPID keys).** Alerts that fire while the SPA is closed are delivered via the Web Push protocol (RFC 8030), which authenticates the application server to the push service via VAPID (RFC 8292). Without keys configured, `push_sender.py` runs in **dry-run** mode — pushes are logged but never sent, and the frontend's Push toggle stays disabled (per R-014, the feature is visible-but-disabled, not absent). To turn pushes on:
  1. **Generate a key pair** with `py-vapid` (bundled with `pywebpush`):
     ```bash
     python -m py_vapid --gen --applicationServerKey
     ```
     Writes `private_key.pem` to the current directory and prints the matching base64url-encoded public key to stdout. Treat the private key like any other secret.
  2. **Configure the keys.** As of FU-333 Bucket B (2026-07-05), the primary path is **Settings → Admin → System → Push notifications** — the admin enters the public key and subject in the UI, and they persist to `AppSetting`. The private key stays in `DORA_VAPID_PRIVATE_KEY` env until Bucket C (encrypted-in-DB storage) lands. During the deprecation window, the legacy env-only path also still works:
     ```
     DORA_VAPID_PUBLIC_KEY=<base64url public key printed above>
     DORA_VAPID_PRIVATE_KEY=<PEM contents OR base64url, single line>
     DORA_VAPID_SUBJECT=mailto:admin@your-domain.example
     ```
     `DORA_VAPID_SUBJECT` is the contact URL the push service uses to reach you if delivery breaks (`mailto:` or `https://`). Omitting any of the three leaves the sender in dry-run.
  3. If configured via Settings, no restart is needed — the resolver picks up the row on the next call. Env-driven configuration still needs a restart. The frontend's **Settings → Notifications → Push** toggle becomes enabled once both halves are present; subscribing happens browser-side and is bound to the configured public key.

- **AI assistant (optional, bring-your-own-LLM, per-user):** Dora's chat can be backed by a language model — Ollama you host yourself, or OpenAI / Anthropic / Google Gemini via your own API key. AI mode is configured **per account** (two people in a household can pick different providers), and it's off by default. Setup: (1) admin confirms the master switch is on at **Settings → System → AI assistant** (defence-in-depth kill-switch — on by default on new installs); (2) each account that wants AI goes to **Settings → Assistant**, picks a provider, fills in URL/model (Ollama) or API key + model (paid), and turns the AI-mode toggle on. The page has a **Test connection** button (rate-limited, audit-logged) so you can verify before flipping the toggle. For Ollama, `ollama pull qwen2.5:7b` + `ollama serve` is the canonical setup; the model must be tool-capable (qwen2.5, llama3.1, gpt-oss, etc.).

  **Paid providers (one operator step):** the install needs the environment variable `DORA_LLM_KEY_ENCRYPTION_KEY` set so per-user API keys can be stored encrypted at rest. Ollama doesn't need this. Generate a key once with:
  ```bash
  python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
  ```
  Put the output into the API server's environment (env file, systemd `EnvironmentFile=`, k8s Secret, whatever fits the deploy). Rotating the key invalidates every saved API key — users re-enter their key on next save.

  **Network topology — important on multi-machine setups:** the Dora **backend** reaches the LLM, not your browser. On a single-laptop install (backend + LLM on the same box), the base URL is just `http://localhost:11434`. On a household setup with the backend on a NAS/Pi and an LLM on a different desktop, the backend has to be able to reach that desktop (LAN routing, Tailscale, or a port forward) — the URL you save in Settings is from the *backend's* point of view, not your phone's.

### Desktop bundle

The desktop app is [pywebview](https://pywebview.flowrl.com/) wrapping the SPA — GTK/WebKit on Linux, WebView2 on Windows, WKWebView on macOS. One PyInstaller spec (`dora.spec`); three thin platform build scripts under `packaging/`. Only the Linux path is CI-verified today — Windows and macOS scripts are checked in but browser-verify is user-driven (see `DORA_VERIFY.md`).

**Linux (AppImage):** ships as a single-file `Dora-vX.Y.Z-x86_64.AppImage`. System deps (apt-installed, not in `requirements.txt`):

```bash
sudo apt install python3.11-dev libpython3.11 \
                 python3-gi gir1.2-webkit2-4.1 \
                 libgirepository1.0-dev libcairo2-dev
```

Then from the repo root:

```bash
pip install -r requirements.txt          # adds pywebview + pyinstaller
./packaging/build-linux.sh --clean --appimage
chmod +x dist/Dora-v*-x86_64.AppImage && ./dist/Dora-v*-x86_64.AppImage
```

The Linux script preflights the apt deps and tells you what's missing rather than failing deep inside PyInstaller. Data persists to `~/.local/share/Dora/`.

**Windows** (PowerShell, from the repo root):

```powershell
pip install -r requirements.txt          # adds pywebview + pyinstaller
.\packaging\build-windows.ps1 -Clean
.\dist\Dora\Dora.exe
```

Produces `dist\Dora\Dora.exe` + its sibling DLL tree. Uses WebView2 at runtime, which ships with Windows 10/11 (older Windows 10 may need the [WebView2 Runtime](https://developer.microsoft.com/microsoft-edge/webview2/) installer). Data persists to `%LOCALAPPDATA%\Dora\`. Single-file `.exe` installer is not built yet — the bundle is a directory tree.

**macOS** (from the repo root):

```bash
pip install -r requirements.txt          # adds pywebview + pyinstaller
./packaging/build-macos.sh --clean
./dist/Dora/Dora
```

Auto-detects Apple Silicon vs Intel from `uname -m` and fetches the matching Piper binary; pass `--arch macos_x64` or `--arch macos_aarch64` to override for cross-arch builds. Requires Xcode command-line tools (`xcode-select --install`) — PyInstaller shells out to `codesign` / `lipo`. Data persists to `~/Library/Application Support/Dora/`. Notarised `.dmg` is not built yet — the bundle is a directory tree.

### Releasing (manual, push-the-button)

CI runs automatically on every push and PR ([.github/workflows/ci.yml](.github/workflows/ci.yml)) — frontend lint + typecheck + build, dora_api pytest, merchant + emailer compile-check. **CI never publishes anything.** Releases are explicit:

1. Land your changes on `main` and confirm CI is green for that SHA.
2. Update the `## [Unreleased]` block in `CHANGELOG.md` — whatever sits there becomes the GitHub Release body.
3. Go to **Actions → Release → Run workflow**, type a version like `v0.3.0`, and run it.
4. The workflow validates the version, refuses if the tag already exists, builds the Docker image, pushes to `ghcr.io/bentalese/dashydora:vX.Y.Z` **and** `:latest`, then cuts the GitHub Release. Tick **dry_run** to preview build + tags without publishing.
5. After the release lands, move the `[Unreleased]` heading down and start a fresh empty section for the next cycle.

<!-- TODO: Offer both docker and manual install options -->
<br/>

## 🐞 Bug to report? 💡 New feature suggestion?

🚧 Templates to be added. Please submit any bug reports or feature requests via our GitHub issue templates.

<br/>

## 💻 Want to contribute?

🚧 <i>Contribution guide to be added.</i>

<br/>

## ☕ Want to support us?

🚧 <i>At the moment we have not set up any form of donations but we very much appreciate the generous thought!</i>

<br/>

## 🧐 Need to see it to believe it?

🚧 <i>Screenshots to be added.</i>

<br/>

## 📜 What licence is Dora under?

Dora is under the MIT licence. See the [license](LICENSE) for more information.
