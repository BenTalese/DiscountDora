<h3 align="center">🚨 Dora is under active development 🚨</h3>

<p align="center">
    <img alt="logo" src=".github/publication_assets/Banner.png" />
</p>
<br/>

<p align="center">
    <img alt="MIT Licence" src="https://img.shields.io/github/license/BenTalese/DiscountDora?style=flat"/>
    <img alt="Awesomeness" src="https://img.shields.io/badge/Awesomeness-100%25-brightgreen" />
    <img alt="Tests" src="https://img.shields.io/github/actions/workflow/status/BenTalese/DiscountDora/build-and-test.yml" />
    <img alt="Current Release" src="https://img.shields.io/github/v/release/BenTalese/DiscountDora"/>
    <img alt="GitHub commits since latest release" src="https://img.shields.io/github/commits-since/bentalese/discountdora/latest">
    <img alt="GitHub commit activity" src="https://img.shields.io/github/commit-activity/m/bentalese/discountdora">
</p>

<br/>

Dora is powered by [Clapy](https://github.com/BenTalese/clapy/) 🐍, a Python clean architecture toolkit.

_Disclaimer: Dora is a hobby project of Ben Talese!_
<hr style="background-color: cyan;border:2px solid blue;border-radius:5px;">

<br/>

## 🍔 Where it all started...

Discount Dora started out as an idea to efficiently keep track of all the edible items in the house without getting into too much detail. Why be overburdened by exactly how many tea bags you have? What people need is something that will be faster than going to the freezer and searching all the baskests for the salmon. After searching for a solution that fit this description, it soon became obvious a lot of pre-existing solutions were overcomplicated for what needed to be extremely fast and to the point. That's the core principle of Dora and the basis for all its features - your pantry at your fingertips.

And from there, the ideas continued to grow...

<br/>

## 🗺️ The Feature Roadmap (It's a Long Road...)

The **vision** for Discount Dora is to have every single interaction with your groceries handled in the one place. No need to go to any external tools - it's all seamlessly managed with Dora!

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
git clone https://github.com/BenTalese/DiscountDora.git
cd DiscountDora
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
- **AI assistant (optional, bring-your-own-LLM):** Dora's chat can be backed by a language model you host yourself. It's off by default and falls back to a rule-based helper. Dora does **not** bundle, download, or dictate a model. To turn it on: (1) run an OpenAI-compatible LLM server that supports tool-calling — [Ollama](https://ollama.com) is the easy option: `ollama pull qwen2.5:7b` then `ollama serve`; (2) sign in as an admin and go to **Settings → System → AI assistant**; (3) enable it and enter your server's base URL (e.g. `http://localhost:11434`) and model name (e.g. `qwen2.5:7b`), then save. The model must be tool-capable (qwen2.5, llama3.1, etc.). The LLM runs wherever you host it (a desktop/home server); other devices reach Dora over the network as usual.

### Desktop bundle (Linux AppImage)

Builds a single-file `Dora-vX.Y.Z-x86_64.AppImage`. System deps (apt-installed, not in `requirements.txt`):

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

The build script preflights the apt deps and tells you what's missing rather than failing deep inside PyInstaller. Data persists to `~/.local/share/Dora/`.

### Releasing (manual, push-the-button)

CI runs automatically on every push and PR ([.github/workflows/ci.yml](.github/workflows/ci.yml)) — frontend lint + typecheck + build, dora_api pytest, merchant + emailer compile-check. **CI never publishes anything.** Releases are explicit:

1. Land your changes on `main` and confirm CI is green for that SHA.
2. Update the `## [Unreleased]` block in `CHANGELOG.md` — whatever sits there becomes the GitHub Release body.
3. Go to **Actions → Release → Run workflow**, type a version like `v0.3.0`, and run it.
4. The workflow validates the version, refuses if the tag already exists, builds the Docker image, pushes to `ghcr.io/bentalese/discountdora:vX.Y.Z` **and** `:latest`, then cuts the GitHub Release. Tick **dry_run** to preview build + tags without publishing.
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
