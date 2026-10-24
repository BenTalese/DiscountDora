# Chunk 13 — Settings shell

**Session:** 2026-10-23 overnight (solo, no subagents) · **Stage:** 1 (analysis only — no code changed)
**Surface:** `/settings` shell (`SettingsShell`, side nav + mobile tab strip, Settings/Admin mode toggle, sign-out), the personal pages Account / Appearance / Notifications / Voice / About, the Kitchen-setup taxonomy pages (Stock locations, Stock groups, Stores, Cuisines/Categories/Tools/Meal slots/Dietary tags, QR labels, Unlinked ingredients), Admin → Users + Audit log, the twelve Admin → System pages, and the backend behind them (`features/app_settings/*`, `features/users/*`, `auth/{get_me,update_me}`, `health/health_check`, entities `AppSetting` + `User`).
**Boundaries:** Assistant page → chunk 11; Budget page → chunk 12; Nutrition system page + Nutrition matching → chunk 6/20; Import + Backup & restore → chunk 18; API access + Ingestion page body → chunk 16; the login/register/bootstrap shell → chunk 15; Onboarding → 14; MainLayout chrome (menu hover ring, header border, 404 page) → chunk 20.

---

## 0. Reading list + files walked

**Governing docs read:** `IMPL_PLAN_SETTINGS_REBUILD` (§2.1 IA, §2.5 primitives, §2.6/§6.1 segmented control, §2.9 profile picture, §2.11 dietary-tag dialog, §6.3 mobile nav, §6.5 nesting — all landed), `DESIGN_STYLE_GUIDE` D-002/003/004/015/018/019, `ENGINEERING_STANDARDS` R-001/002/003/005/019/026/029/034/045/057; feedback `# SETTINGS` (2 bullets) and `# NO AREA / MISC` (the Settings-adjacent bullets — see §F). Open FUs on this surface consulted: FU-871, 867, 865, 848, 674, 672, 656, 655, 633, 632, 779, 648; plus cross-cutting FU-654 (session user-id helper), FU-668 (unpaged first page), FU-671 (`text-color="white"`), FU-759 (`get_or_create_app_setting`).

**Backend walked in full (3,168 lines):** `app_settings/{get_app_settings,update_app_settings,access,clock,operational_config,probe_llm}.py`, `users/{get_users,create_user_as_admin,update_user_as_admin,delete_user_as_admin,reset_user_password,get_user_image}.py`, `auth/{update_me,get_me}.py`, `health/health_check.py`, `domain/entities/{app_setting,user}.py`.

**SPA walked in full (~11,700 lines):** `pages/SettingsShell.vue`; `components/settings/{SettingsNavGroup,SettingsMobileNav,SettingsSection,SettingsRow,SettingsPageHeader,SettingsNotice,DoraSegmented,TaxonomyManagerPage,VocabListEditor,PasswordSetter,EncryptionKeyBanner,ChannelSetupNote,VoicePicker,DietaryTagFormDialog,LocationZoneCard,LocationAreaRow,LocationSectionChip,LocationAddChip}.vue`; `composables/{useSettingsSave,useFeatureFlags,useMoneyEnabled,useMoney,useMeasurementSystem,useProductSearchUrl}.ts`; `services/api/{appSettingsApiService,healthApiService,authApiService,userAdminApiService}.ts`; `components/UserAvatar.vue`; pages `settings/{Account,Preferences,Notifications,Voice,About,UsersAdmin,AuditLog}Settings.vue`, `AdminSystem{Region,Money,Alerts,Stock,Stocktake,MealReconcile,Cooking,Image,Push,Email,Voice,Ingestion}Settings.vue`, `{StockLocations,StockGroups,Stores,RecipeCuisines,RecipeCategories,RecipeTools,RecipeMealSlots,RecipeDietaryTags}Settings.vue`, `QrLabels.vue`, `UnlinkedIngredientsSettings.vue`; `layouts/MainLayout.vue:60–110` (settings entry).

**Verification greps run:** `/settings` in `layouts/` (one entry — the avatar button; no main-menu "Settings" item remains); `DoraSegmented|BaseSegmented` (22 files: 9 Dora, 13 Base — FU-848); `useSettingsSave` (9 consumers) vs pages with inline `$q.notify` save toasts (14 settings pages); `.settings-divider {` (14 scoped copies); "You don't have admin permissions" banner (12 pages) vs `router/index.ts:154` admin guard; `return None, f"Invalid nutrition mode` (1 hit, `update_app_settings.py:174`) and `nutrition_mode` in `test_app_settings_router.py` (only a read assertion — no invalid-mode test); `MIN_PASSWORD_LENGTH` (TS `models/password.ts:11` = 8; Python `auth_helpers.py:69` = 8; `AccountSettings.vue:131–133,280` hardcodes `8` ×4); `probeAsync` (`appSettingsApiService.ts:129` — zero callers; the Assistant page uses `assistantApiService.probeAsync`); `_require_admin` import origin (9 files via `users.update_user_as_admin` re-export, 8 via `auth.admin_gate`); RFC-4918 `ProblemDetails` literal (6 copies across auth/users); `--focus-ring` (27 uses) vs `--ring-focus` (8 uses) — both defined, `tokens.scss:153–154`, different values; `useProductSearchUrl` reads admin-only `/app-settings` (non-admins swallow the 403 → URL empty); `nutrition_mode` on `UpdateMeCommand` (`authApiService.ts:63` — field dropped server-side 2026-08-14, `extra="forbid"`); `backup_retention_count|backup_storage_path` absent from the TS `AppSettings` type yet read/written by `AdminDataBackupRestore.vue:906–934`; `schema_version_db` absent from `HealthInfo`; `user_id` columns without FK in `table_mappings.py` (lines 648, 666, 681 = AlertInteraction/AlertPreference/PushSubscription — matches `_USER_SCOPED_UNCONSTRAINED_TABLES`); `DEFAULT_LIMIT = 50` (`query_options.py:22`) and `userAdminApiService.getAllAsync` → `/users` with no limit; `CURRENT_VERSION = "0.7.0"` (`version_info.py:12`) vs About's "Versioning isn't tagged in this fork yet"; existing tests (app_settings 17, users_admin 7, user_router 17, health 2, operational_config 7; vitest `voicePicker.spec.ts`, `settingsFileDrop.spec.ts`, `designTokensDeclared.spec.ts`).

---

## A. Full Systems Test — Settings shell

### A1. Preconditions
- Two accounts: one admin, one member; the admin has a profile picture set.
- `DORA_SECRET_ENCRYPTION_KEY` **unset** on one run, set on another (the Email/Push banners differ).
- Money on, scanning off, nutrition `off` (so Budget shows, QR labels and Nutrition matching hide — R-029 nav honesty).

### A2. Golden path
| # | Step | Expect |
|---|---|---|
| G1 | Avatar button in the header → `/settings/account` | Shell opens on Account; sidebar groups Account · Preferences · Kitchen setup · About; admin sees the Settings/Admin pill toggle, member sees a plain "Settings" h1. |
| G2 | Upload a profile picture (tile click) | Immediate save, "Profile picture updated.", avatar updates in header + Account + Users list (version bump); "Remove photo" appears; "Or pick one of ours" presets save the same way. |
| G3 | Edit username + email, change password, Save changes | One `/auth/me` PATCH with only the changed fields, then `/auth/me/password`; "Changes saved."; Discard resets drafts; leaving mid-edit prompts (R-020 guard). |
| G4 | Appearance → Mode Dark, Theme Blueberry, Font Lexend, Size Large | Four separate saves, each toasts; swatches re-render for dark; theme key saved as `blueberry-dark`; System mode stores `system-blueberry`. |
| G5 | Notifications → discard-after 7 days, toggle a kind off, remove a price watch | Each saves + bell refreshes; Push section shows the right blocker (no VAPID → ChannelSetupNote with admin "Set up push" link; member gets "Ask an admin"); Email section hidden until product data exists. |
| G6 | Voice → enable output, pick a neural voice, preview | One save sets `voice_id` + `voice_engine='piper'`; preview plays; "Device default voice" switches engine to browser and remembers the neural pick. |
| G7 | Kitchen setup → Stock locations: New zone → + Area → + Section → rename → delete | Prompt dialogs; counts roll up server-side; delete warns "N items stored here will become unassigned"; expansion survives reload (R-026 carve-out). |
| G8 | Stock groups / Cuisines / Categories / Tools / Meal slots | Same `VocabListEditor` anatomy; meal slots reorder with ↑↓ and the planner picks up the change (store-routed). |
| G9 | Stores: New store → click logo tile → upload → rename inline → delete | Logo saves immediately; delete toast reports cleared item/line references. |
| G10 | Admin toggle → Users: Add user with a chosen password; Change password (generate); toggle Active off | Chosen password never echoed; generated one shown once with Copy; deactivation confirm → the user's next `/auth/me` 401s with the deactivated message. |
| G11 | Admin → Region: Match this device | Timezone + locale + units saved; currency untouched; HSR/Nutri-Score nudge only in matching regions and only if scheme is `none`. |
| G12 | Admin → Email: set SMTP password without the encryption key | Banner shown first; save refused with the DORA_SECRET_ENCRYPTION_KEY message. With the key: "SMTP password saved.", `smtp_password_configured=true`, Notifications' email channel unlocks. |
| G13 | Admin → Stock: scanning on | Sidebar gains "QR labels" without reload (scanning composable + flags refreshed). |
| G14 | Admin → Audit log: change retention, filter by request id, open a row, Export CSV | Retention saved on blur; detail dialog "Find related" re-filters; CSV downloads the **loaded page** only. |
| G15 | Phone (<1024) | Sidebar replaced by the tab strip; Account/About tabs navigate directly (no one-chip strip); header fits at 320 px with icon-only sign-out. |

### A3. Edge cases
| # | Case | Expect (and what the code does today) |
|---|---|---|
| E1 | Admin PATCHes `/app-settings` with `nutrition_mode: "bogus"` | **Today: 500** — handler returns a tuple, caller reads `.invalid_reason` → 13-R1. Expect 400 "Invalid settings." |
| E2 | Admin edits another user's email to `not-an-email` or to an address already on another account | **Today: accepted** — admin path has no format/uniqueness check (self-serve path has both) → 13-R2. |
| E3 | Two admins, one deactivated; delete the remaining active admin | **Today: allowed** — delete guard counts `is_admin` only, not active admins → 13-R3. Expect refusal. |
| E4 | Account page: new password of 7 chars | Inline "At least 8 characters" — correct today but from a hardcoded `8`, not `MIN_PASSWORD_LENGTH` → 13-R12 (FU-656). |
| E5 | Member (non-admin) with a Product Search URL configured | Main-nav "Product Search" entry **never appears** for members — the URL is read from the admin-only `/app-settings` → 13-R4 (FU-186 intent was "every user"). |
| E6 | Install with 51+ users opens Admin → Users | **Today: list silently capped at 50** (`DEFAULT_LIMIT`) → 13-R5 (FU-668 class; low likelihood). |
| E7 | Theme row holds a legacy key (`pesto-noir`) | `familyAndModeOf` → null → picker shows System/Pesto while the app renders pesto-dark (themeService maps legacy at apply time, the Preferences decoder doesn't) → 13-R6. |
| E8 | Appearance page unmounts | `matchMedia` change listener never removed → 13-R7 (leak, minor). |
| E9 | Admin deep-links `/settings/admin/...` as a member | Router guard (`index.ts:154`) redirects; the 12 per-page banners are unreachable → 13-R13. |
| E10 | `/health` with the DB down | Flags fall back to conservative defaults; `features` still emits strings for `nutrition_mode`/`nutrition_rating_scheme` under a `Record<string, boolean>` type → 13-R16. |
| E11 | Audit log on a page with more rows than shown | "Export CSV" exports only the loaded rows; the label promises more → 13-R20 (copy). |
| E12 | Sign out from a dirty Account page | Guard suppressed; no false "discard?" prompt ✅. |
| E13 | QR labels reached by URL with scanning off | Banner with link to Admin → Stock ✅. |

### A4. Persona coverage
- **Member:** Account/Preferences/Notifications/Voice/Kitchen setup/About; sees "Ask an admin" variants; cannot reach admin pages. (E5 bites them.)
- **Admin:** everything above + the three admin groups; self-row toggles disabled with tooltips.
- **Fresh install / self-host op:** Email + Push banners drive the encryption-key setup; Region "Match this device" is the one-click regionalisation; About carries the instance URL only on native.
- **Phone:** tab strip, inline rows keep toggles beside labels, 44 px tabs/chips.

### A5. Load-bearing conditions
- Install-wide facts reach non-admins only through `/health` (`features`, `locale_policy`, `image_policy`, `cooking_policy`, `budget_policy`, `reconcile_policy`, `stocktake_policy`) — every admin save that changes one must refresh the matching composable cache (all pages do today ✅; the pattern is hand-copied ×10 → 13-R9).
- `get_or_create_app_setting` is memoised per app context (FU-560) — admin PATCH mutates the same identity-map row ✅.
- Password policy is one Python authority (`validate_password`) used by self-serve, admin-create and admin-set ✅; the SPA mirrors the length only.
- Secrets never ride the DTO (`*_configured` bools) ✅ (tested).

### A6. Release-gate rows
- [ ] Invalid `nutrition_mode` → 400, not 500 (13-R1).
- [ ] Admin email edit validates + dedupes like self-serve (13-R2).
- [ ] Deleting the last **active** admin is refused (13-R3).
- [ ] A member sees the Product Search nav entry when a URL is set (13-R4).

---

## B. Help content — Settings shell

### B1. Current help audit
`HelpPage.vue` group "Settings & admin" holds three entries — 'Theme, font, and text size', 'Manage other users (admin)', 'Manage stores (admin)'. 'Theme, font, and text size' predates the Mode/Theme split (round-19) and the 2026-09-03 Appearance rename — it should say Mode (System/Light/Dark) × Theme family, and name `xl`. Nothing covers the profile picture, notifications channels, voice engines, stock locations' three fixed levels, taxonomy editing, the Region page, the encryption-key requirement, deactivate-vs-delete, or the audit log. `APP_OVERVIEW` (chunk 11 owns the rewrite) mentions Settings only as a destination.

### B2. Help entries (one per feature / auto-behaviour)

#### Settings and Admin are two modes
- **Group:** Settings & admin
- **What it does:** Personal settings (Account, Preferences, Kitchen setup, About) and install-wide Admin settings (Install, Kitchen features, Data & access) are separate modes; admins switch with the pill at the top.
- **When it fires / how to trigger it:** Header avatar → Settings; admins see the Settings | Admin toggle.
- **What controls it:** admin flag on the account (Admin → Users).
- **What it costs / might get wrong:** Kitchen setup is shared by the household even though it sits on the personal side — it's "what this kitchen has", not "what I prefer".
- **Related:** Who can change what · Manage other users (admin).
- **Chip:** none. **Source:** `SettingsShell.vue:17–40`, owner calls 2026-08-14/17, 2026-09-03.

#### Who can change what
- **Group:** Settings & admin
- **What it does:** Anyone can edit their own account, appearance, notifications, voice, and the shared kitchen setup (locations, groups, stores, recipe vocab, budget). Only admins change install-wide behaviour (region, money, email, push, stocktake, cooking, image quality, users).
- **What controls it:** `is_admin`; non-admins redirected from `/settings/admin/*`.
- **What it costs / might get wrong:** A member can rename or delete a store everyone uses — kitchen setup is deliberately not admin-gated.
- **Related:** Settings and Admin are two modes. **Chip:** none. **Source:** `router/index.ts:154`, shell nav groups.

#### Appearance: mode, theme, font, text size (reword of 'Theme, font, and text size')
- **Group:** Settings & admin
- **What it does:** Pick a Mode (System follows your device, Light, Dark), a Theme family (Pesto, Lemon Tart, Blueberry, Cherry Cola, Sourdough, Salt & Pepper, Dragonfruit), a font, and one of four text sizes (Small 87.5 % · Medium · Large 112.5 % · Extra large 125 %).
- **What controls it:** `/settings/preferences`; saved per account, follows you across devices.
- **What it costs / might get wrong:** System mode re-evaluates on the device's dark-mode switch without a reload; text size scales the whole UI, so very large on a small phone wraps labels.
- **Related:** Profile picture. **Chip:** none. **Source:** `PreferencesSettings.vue`, `themeService.ts`, `tokens.scss:294–298`.

#### Profile picture
- **Group:** Settings & admin
- **What it does:** Upload a photo or pick a preset; it shows in the header, Account, and the admin Users list.
- **When it fires:** Saves immediately on pick/clear — no Save button.
- **What controls it:** `/settings/account`; an admin can also clear another user's picture via the API (no UI today — 13-R15).
- **What it costs / might get wrong:** Compressed on upload to the install's image policy; stored in the database, so it rides backups.
- **Related:** Image quality (admin). **Chip:** none. **Source:** `AccountSettings.vue:9–57`, `update_me.py:76–81`.

#### Username, email and password
- **Group:** Settings & admin
- **What it does:** Edit your sign-in name and email inline; change your password with your current one; all commit on one Save.
- **What costs / might get wrong:** Changing your password signs out your other devices (this one stays in). An entered email counts as verified — Dora trusts you on your own address.
- **Related:** Notifications: email. **Chip:** none. **Source:** `update_me.py:130–148`, `AccountSettings.vue`.

#### Notifications: in-app, push, email
- **Group:** Settings & admin
- **What it does:** Choose which alert kinds reach your bell and how long alerts live (7/14/30 days/never); subscribe this device to push and the 7 pm Evening brief; opt into the weekly deals email.
- **When it fires / how to trigger it:** Push needs VAPID keys (admin → Push) and browser support; email needs SMTP (admin → Email), a verified address, and product data.
- **What it costs / might get wrong:** Push is per device — turning it off here doesn't touch your phone. Unverified addresses receive nothing; the page offers "Send verification email".
- **Related:** Alert thresholds (admin) · Email and push setup (admin). **Chip:** none. **Source:** `NotificationsSettings.vue`.

#### Voice: input, output, which voice
- **Group:** Settings & admin
- **What it does:** Speak to Dora (browser speech recognition — Chrome/Edge/Safari only) and let her speak replies with either her neural voice (Piper, on the server) or your device's voice.
- **What controls it:** `/settings/voice` per user; the Piper engine path is admin → Voice.
- **What it costs / might get wrong:** Neural voices are 60–110 MB downloads on the server; without Piper installed (source installs on Windows) replies fall back to the device voice automatically.
- **Related:** Voice engine (admin). **Chip:** none. **Source:** `VoiceSettings.vue`, `VoicePicker.vue`.

#### Stock locations: zones, areas, sections
- **Group:** Settings & admin
- **What it does:** A fixed three-level map of where things live; items can sit at any level; counts roll up.
- **What it costs / might get wrong:** Deleting a zone removes its areas/sections and leaves items **unassigned**, not deleted. Search expands every match; your collapse state is remembered on this device.
- **Related:** Stock groups. **Chip:** `StockLocationsSettings.vue:3` header. **Source:** `StockLocationsSettings.vue`, `Location*` components.

#### Stock groups and recipe vocabulary
- **Group:** Settings & admin
- **What it does:** Name-only lists (stock groups, cuisines, categories, tools, meal slots, dietary tags) used as filters and pickers across the app; each row shows how many things use it.
- **What it costs / might get wrong:** Deleting one strips it from the items/recipes using it (meal slots: entries keep the label). Meal slots are the only reorderable list and the order drives the planner.
- **Related:** Stock locations · Manage stores. **Chip:** none. **Source:** `TaxonomyManagerPage.vue`, `VocabListEditor.vue`.

#### Region & locale (admin)
- **Group:** Settings & admin
- **What it does:** Currency, language/format, units system (metric / imperial / US) and household timezone — the install's "where do we live". Preview updates as you pick; "Match this device" fills zone, locale and units (never currency) and may offer the locally recognised recipe rating.
- **What it costs / might get wrong:** Timezone decides which day is "today" for meal plans, budgets and alerts everywhere; units change every dropdown immediately.
- **Related:** Money (admin). **Chip:** none. **Source:** `AdminSystemRegionSettings.vue`, `clock.py`.

#### Email and push setup (admin) — and the encryption key
- **Group:** Settings & admin
- **What it does:** SMTP details, the email on/off switch, the public URL used in emailed links; VAPID keys for web push. Passwords and private keys are stored encrypted.
- **When it fires:** Saves on blur/toggle; secret fields have their own Save/Clear.
- **What controls it:** `DORA_SECRET_ENCRYPTION_KEY` must be set in the server environment or secret saves are refused — the page shows a banner and can generate a key for you.
- **What it costs / might get wrong:** Rotating the key makes every stored secret unreadable (re-enter them). Gmail needs an App Password.
- **Related:** Notifications. **Chip:** none. **Source:** `AdminSystemEmailSettings.vue`, `AdminSystemPushSettings.vue`, `EncryptionKeyBanner.vue`.

#### Manage other users (admin) (reword)
- **Group:** Settings & admin
- **What it does:** Add users (set a password or let Dora generate a one-time one), rename, change emails and passwords, promote to admin, **deactivate** (locks them out, keeps everything) or delete (removes their sessions, alert prefs and push subscriptions; shared recipes/lists stay).
- **What it costs / might get wrong:** You can't demote, deactivate or delete yourself, or remove the last admin who can still sign in. An admin-set password signs that person out everywhere.
- **Related:** Who can change what. **Chip:** none. **Source:** `UsersAdminSettings.vue`, `users/*.py`.

#### Audit log (admin)
- **Group:** Settings & admin
- **What it does:** Every mutating request, login attempt, client crash and service event; filter by severity/action/actor/entity/request id; "Find related" follows one request; CSV export of the current page; retention 1–3650 days pruned nightly.
- **Related:** Manage other users. **Chip:** none. **Source:** `AuditLogSettings.vue`.

#### Kitchen features (admin): stock, stocktake, cooking, meal reconciliation, money, alert thresholds, image quality
- **Group:** Settings & admin
- **What it does:** One page per feature switch, each saving on change: auto-add mode + scanning/QR; stocktake master switch, new-item default, cadence, self-tuning; household headcount + fresh/batch cooking style; auto-drain past meals; money on/off; expiring-soon window; upload quality + longest edge.
- **What it costs / might get wrong:** Each flip is install-wide and takes effect for everyone on their next page load (this session refreshes immediately). Image settings are forward-only.
- **Related:** Region & locale. **Chip:** none. **Source:** `AdminSystem{Stock,Stocktake,Cooking,MealReconcile,Money,Alerts,Image}Settings.vue`.

### B3. DoraBot corpus delta
Replace the Settings mention in `APP_OVERVIEW` with: *"Settings (header avatar) has two modes: your own — account, appearance, notifications, voice, and the shared kitchen setup (locations, groups, stores, recipe vocabulary, budget) — and, for admins, the install: users, region & units, email/push, kitchen feature switches, data & access. Install-wide switches apply to everyone."* Tool nav for settings should point at `/settings/account` and `/settings/admin/users` (chunk 11 `_TOOL_NAV` fix already covers `/settings/preferences`).

---

## C. Senior review — Settings shell

### C1. Bugs (verified or high-confidence latent)
- **13-R1** · bug · `dora_api/features/app_settings/update_app_settings.py:171–175` · on an invalid `nutrition_mode` the handler does `return None, f"Invalid nutrition mode …"` (a tuple) while every other branch returns `UpdateAppSettingsResponse(invalid_reason=…)`; the route (`:461–464`) reads `_Response.invalid_reason` → `AttributeError` → 500. **Change:** `return UpdateAppSettingsResponse(invalid_reason=f"'{_Mode}' is not a nutrition mode. Supported: {list(NUTRITION_MODE_VALUES)}.")`. Blast S. Guard: none — add `test__patch_app_settings__BogusNutritionMode__400InvalidSettings` beside the cadence-band test (`test_app_settings_router.py:170`). **execute**.
- **13-R2** · bug · `users/update_user_as_admin.py:100–101` · `if "email" in _SetFields: _Target.email = request.email` — no `normalise_email`/`is_valid_email`/uniqueness check and no `email_verified` update, unlike `update_me.py:130–148` and `create_user_as_admin.py:77–82,162`. An admin can store a malformed or duplicate address (password-reset mail would then route wrongly). **Change:** extract the email block of `update_me.py:136–148` into `auth_helpers.apply_email_change(repo, user, raw) -> str | None` and call it from both handlers; admin route maps the message to `business_rule_violation`. Blast S. Guard: `test_users_admin.py` + new `test__admin_update_user__malformed_or_taken_email__rejected`. **execute**.
- **13-R3** · bug · `users/delete_user_as_admin.py:64–67` · last-admin guard counts `is_admin == True` rows, ignoring `is_active`; `update_user_as_admin._other_usable_admins` (`:59–74`) counts active admins. Deactivate admin B, delete admin A → install has no admin who can sign in. **Change:** move `_other_usable_admins` to `auth/admin_gate.py` as `other_usable_admins(repo, user_id)` and use it in both handlers. Blast S. Guard: new pytest "deactivated admin doesn't count as cover for delete". **execute**.
- **13-R4** · bug (functional gap) · `composables/useProductSearchUrl.ts:28–41` · reads `product_search_url` from admin-only `GET /app-settings`; members get 403 → URL empty → the main-nav "Product Search" entry (and the companion CTAs' real link) never appear for non-admins, contradicting FU-186 ("every user"). **Change:** publish `product_search_url` on `/health` (new `products_policy: { search_url }` block beside `locale_policy`, R-057 "add, never remove") and read it there; keep the admin page writing via `/app-settings`. Blast S. Guard: `test_health_router.py` key assertion. **execute**.
- **13-R5** · latent · `services/api/userAdminApiService.ts:47–48` · `GET /users` with no `limit` → `DEFAULT_LIMIT=50` (`query_options.py:22`) silently caps the admin list. **Change:** request `?limit=500` (or add a `limit` param and page). Blast S. **execute** (FU-668 class — fold into that sweep).
- **13-R6** · latent · `pages/settings/PreferencesSettings.vue:148–153` · `modeAndFamilyForKey` returns System/Pesto for any key `familyAndModeOf` can't decode, including the five legacy keys the server still accepts (`user.py:49–53`) — the picker then disagrees with what themeService renders (`themeService.ts:305–306` maps legacy at apply time). **Change:** run the key through themeService's legacy normaliser before decoding (export it; one R-003 mapping). Blast S. Guard: vitest on `familyAndModeOf(normalise('pesto-noir'))`. **execute**.
- **13-R7** · latent (leak) · `PreferencesSettings.vue:160–168` · `mql.addEventListener('change', …)` with no `onBeforeUnmount` removal; `themeService.ts:427–429` already owns a system-dark watcher. **Change:** expose `osPrefersDarkRef` from themeService (one listener, R-003) and drop the page's own. Blast S. **execute**.
- **13-R8** · latent · `AuditLogSettings.vue:301` · `classes: 'text-mono'` references a *scoped* style; q-table renders cells outside the component's scope attribute so the class likely doesn't apply. **Change:** move `.text-mono` to a global utility (`css/app.scss` already has one? grep at Stage 2) or use `:deep`. Blast S. **execute** (verify in browser first).

### C2. Redundancy / DRY (R-001, R-003)
- **13-R9** · `AdminSystem{Region,Money,Alerts,Stock,Stocktake,MealReconcile,Cooking,Image,Push,Email,Voice,Ingestion}Settings.vue` + `AuditLogSettings.vue:425–448` · thirteen hand-copied "load `/app-settings` on mount → `saved`/`draft` → save one field on blur/toggle → toast → revert on error" blocks (~60 lines each). **Change:** `composables/useAppSettingField.ts` — `const { draft, save, saving } = useAppSettingField('smtp_host', { successMessage, afterSave: refreshX })` backed by one shared `appSettingsStore` (one GET per session instead of one per page mount; `refresh()` after PATCH). Pages shrink to templates. Blast M (13 files). Guard: vitest on the composable's revert-on-error; existing pytest unchanged. **execute**.
- **13-R10** · 14 settings pages inline `$q.notify({type:'positive'|'negative', position:'bottom-right', …})` while `useSettingsSave.ts:5–9` documents itself as the single source (9 pages use it). **Change:** route every page's save through `useSettingsSave.update()` (falls out of 13-R9 for the admin pages; Account/Users/Audit/Stores/Taxonomy/Locations use `notifySuccess/notifyError`). Blast M. **execute**.
- **13-R11** · `.settings-divider { … }` scoped copy in 14 pages (`AccountSettings.vue:355–360` etc., margins differ 0/2px/8px). **Change:** one global `.settings-divider` in `css/settingsCards.scss` (which already hosts `.settings-card`); delete the 14 copies, keep the two margin variants as modifiers. Blast S. **execute**.
- **13-R12** · `AccountSettings.vue:131–133,280` hardcodes `8` ×4 while `models/password.ts:11–17` owns `MIN_PASSWORD_LENGTH`/`PASSWORD_HINT`/`passwordLongEnough` and `PasswordSetter.vue` uses them. **Change:** import and use them. Blast S. **execute**. *tracked:* FU-656 (the TS↔Python duplication itself) — recommended resolution for FU-656: publish `password_min_length` on `/auth/capabilities` and derive the TS constant; execute at Stage 2 with this.
- **13-R13** · 12 admin pages render "You don't have admin permissions to view this page." and gate `onMounted` on `isAdmin`, but `router/index.ts:154` already redirects non-admins off `/settings/admin/*`. **Change:** delete the 12 banners + `isAdmin` early returns (route guard is the single authority, R-003); keep `isAdmin` only where the page branches copy (Voice/Notifications "ask an admin"). Blast S (12 files). **execute**.
- **13-R14** · `create_user_as_admin.py:69–87` and `reset_user_password.py:40–70` both define a 12-char alphanumeric one-time-password generator; `create_user_as_admin.py:125–130,133–138` + `reset_user_password.py:98–103` + 3 auth files build the same RFC-4918 `ProblemDetails` literal (6 copies). **Change:** `auth_helpers.mint_one_time_password()`; `api_response.validation_failed(errors: dict[str, list[str]])` returning the 422 ProblemDetails; replace the 6 literals. Blast S. Guard: existing 422 tests. **execute**.
- **13-R15** · `AdminUpdateUserRequest.image/clear_image` (`update_user_as_admin.py:39–43,126–131`) has no SPA caller (`AdminUpdateUserCommand` lacks both fields) — the documented "admin clears a problematic picture" is unreachable. **Change (owner-neutral):** add a "Remove picture" item to the row's overflow menu (`UsersAdminSettings.vue:104–131`) sending `{clear_image:true}`; drop `image` (set) from the admin request — setting another user's photo was "for completeness" only. Blast S. **execute** (the remove half) / **waive** (the set half, delete it).
- **13-R16** · contract drift (R-057): `healthApiService.ts:13–24` types `features` as `[key: string]: boolean` though the server emits strings for `nutrition_mode` and `nutrition_rating_scheme` (`health_check.py:141,168`); `schema_version_db` (`:378`) absent from `HealthInfo`; `appSettingsApiService.ts:8–102` lacks `backup_retention_count`/`backup_storage_path` that `AdminDataBackupRestore.vue:906–934` reads/writes (type-checks only because `Partial<…>` + `?? 5`); `authApiService.ts:61–63` still carries `nutrition_mode` on `UpdateMeCommand` (server `extra="forbid"` → any sender gets 400). **Change:** fix the three TS types, delete the dead field. Blast S. Guard: `test__get_app_settings__CoreFields__PresentAndTyped` + a TS compile. **execute**.
- **13-R17** · `TaxonomyManagerPage.vue:36` and `VocabListEditor.vue:86` each declare `type VocabItem`; `RecipeDietaryTagsSettings.vue:22–52,170–175` and `StoresSettings.vue:36–98,185–204` re-implement VocabListEditor's row (`.vocab-row`), inline rename (`editingId`/`renameDraft`/`saveRename`) and list chrome. **Change:** export `VocabItem` once from VocabListEditor; give VocabListEditor `#leading` (avatar) and `#meta` slots + a `rename-mode: 'inline' | 'dialog'` prop so Stores and Dietary tags become callers. Blast M. **execute**.
- **13-R18** · `ChannelSetupNote.vue` is `SettingsNotice` with channel copy baked in (identical banner anatomy, `dora-bg-warning-soft`). **Change:** render `<SettingsNotice :title>` inside it (or inline the two copies into Notifications via SettingsNotice slots) so there is one warning-card anatomy (D-015). Blast S. **execute**.

### C3. Dead code / unused fields / unread endpoints
- **13-R19** · `app_settings/probe_llm.py` (whole file) + `APP_SETTINGS_ROUTER /probe` + `appSettingsApiService.probeAsync` (`:114–118,129–132`) + `test_app_settings_router.py:205–230` — grep `probeAsync|/app-settings/probe` → only the definition; the Assistant page probes via `assistantApiService.probeAsync` (per-user providers). **Change:** delete route, client method, `ProbeResult` type, and the two tests. Blast S. **execute**.
- **13-R20** · `PreferencesSettings.vue:179,188–190,199–205` `themeDraft` is written on load/rollback and never read by the template (mode/family drafts drive it). **Change:** delete it; `onThemeChange` keeps `previous`. Blast S. **execute**.
- **13-R21** · `useMoneyEnabled.ts:17–19` — `installEnabled` and `moneyEnabled` are the same computed twice; `installEnabled` has no external reader (grep at Stage 2). **Change:** return `{ moneyEnabled }` only. Blast S. **execute**.
- **13-R22** · `AuditLogSettings.vue:312–313` — `if (sev === 'info') return 'info'; return 'info';` duplicate branch. **Change:** collapse. Blast S. **execute**.
- **13-R23** · `NotificationsSettings.vue:267,287` imports from `'vue'` twice (`onMounted` on its own line). **Change:** merge. Blast S. **execute**.
- **13-R24** · `update_user_as_admin.py:25–27` re-exports `_require_admin` "no big-bang rename" — 9 files still import it from there vs 8 from `auth.admin_gate`. **Change:** sweep the 9 imports, delete the re-export. Blast S. **execute**.

### C4. Componentisation opportunities (R-001)
- **13-R25** · the "not signed in" banner `<q-banner class="dora-bg-sunken" dense>Not signed in.</q-banner>` appears at the top of Account/Preferences/Notifications/Voice; the shell already requires auth. **Change:** delete the four `v-if="!currentUser"` branches (the router guard is the authority) or hoist one guard into `SettingsShell`. Blast S. **execute**.
- **13-R26** · `UsersAdminSettings.vue:638–651 confirmDialog` and the taxonomy/locations `promptForName`/`onDelete` dialogs are the fourth and fifth hand-rolled `$q.dialog` promise wrappers in the settings tree. **Change:** `composables/useConfirm.ts` (`confirm({title,message,okLabel,danger})` / `prompt({title,message,initial})`) — check `src/composables` for an existing one first (chunk 20 cross-cut). Blast M. **FU** (cross-cutting; chunk 20 decides the home).

### C5. Placement / layering (R-003, R-005)
- **13-R27** · `health_check.py:12–13` docstring "Cheap by design: never touches the DB or external services" is false (AppSetting fetch, Product count, alembic_version read) — R-019. **Change:** rewrite to "one memoised AppSetting read + a Product count; alembic head at import". **execute**.
- **13-R28** · `get_app_settings._to_dto`, `operational_config.resolved_operational_config`, `health_check._*_policy` use `getattr(setting, "field", default)` for fields the `AppSetting` dataclass always defines (defensive noise from the migration era). **Change:** direct attribute access; keep `or default` only where empty-string→default is intended. Blast S. **execute**.
- **13-R29** · `update_app_settings.py:1–5` docstring "Only the assistant (BYO-LLM) config lives here for now" — stale by ~40 fields (R-019). **Change:** rewrite. **execute**.
- **13-R30** · `useFeatureFlags.ts:83,95–96` comments say "true when DORA_SMTP_USERNAME is set" / "DORA_VAPID_* are set" — those env vars were retired 2026-07-06 (`operational_config.py:4–6`). **Change:** reword to the AppSetting fields. **execute**.
- **13-R31** · `update_me.py:296–305` / `get_me.py:20–32` open-code the session user-id parse (FU-654 helper sweep +2). **execute** under FU-654.
- **13-R32** · `get_users._stamp_has_image` and `delete_user_as_admin` reach `db.metadata.tables[...]` directly (same shape as FU-923's `StockItemProduct` readers). Portable SQL, but outside the repository port (R-005). **Change:** `repository.column_flags(User, "image", ids)` / `repository.delete_where(table, col == id)` helpers — fold into FU-923's widening. **FU** (FU-923).

### C6. Naming & idiom
- **13-R33** · `get_user_image.py:49` route `"/<uuid:user_id>/image"` vs siblings `"<uuid:user_id>"` (leading slash inconsistency; both resolve). **Change:** drop the slash. **execute**.
- **13-R34** · `get_users.py:97`, `update_user_as_admin.py:169`, `reset_user_password.py:129`, `update_me.py:316` use f-string logging; siblings use `%s` args. **Change:** `%s` form. **execute**.
- **13-R35** · `AdminSystemMoneySettings.vue:57` `featureFlags$refresh` (and Stock/Stocktake) — a `$`-suffixed local is idiosyncratic. **Change:** `refreshFeatureFlags`. **execute** (falls out of 13-R9).

### C7. Efficiency
- **13-R36** · every admin page mount issues its own `GET /app-settings`; the Audit page issues it alongside the log fetch. One `appSettingsStore` (13-R9) makes it one per session. **execute** (with 13-R9).
- **13-R37** · `health_check._resolve_db_schema_version` runs `SELECT version_num FROM alembic_version` on **every** probe, and `/health` is polled by every composable on boot (flags, money, measurement, image, cooking, budget, reconcile, stocktake, support — up to 9 callers share one inflight promise per composable but not across composables → up to 9 probes per cold load). **Change:** memoise the DB revision per process (it can't change at runtime); add one shared `healthProbe.ts` with a single inflight promise all policy composables read from. Blast M. **execute** (R-074).

### C8. Design-level findings — out of Stage-2 scope
- **13-D1** · Feedback "Settings is shown in both main menu and the user dropdown — remove from main menu": **already done** (`MainLayout.vue:290` comment; grep shows one `/settings/account` entry, no dropdown). Record as covered.
- **13-D2** · Feedback "Theme should be split into type … and theme … separately": **done** (round-19 Mode + Theme sections). Covered.
- **13-D3** · Feedback "Profile picture + menu bar avatar": **done** (Phase 4). Covered.
- **13-D4** · Feedback "Text size 75/100/150 %": shipped as 87.5/100/112.5/125 % (`tokens.scss:294–298`). Owner call: is the narrower range acceptable, or add 75 %/150 % steps (`xs`/`xxl` would need `ALLOWED_FONT_SIZES` + TS union + tokens)? Default: accept as-is (owner ≥90 % happy).
- **13-D5** · Kitchen setup is member-editable (stores, locations, vocab) while every install switch is admin-only — deliberate ("kitchen setup, not personal") but worth one line in Help (B2 "Who can change what"). No change.
- **13-D6** · About says "Versioning isn't tagged in this fork yet" while `/health.version` is `0.7.0` (`version_info.py:12`). Owner call: show `version` + `schema_version` (+ `schema_version_db` mismatch warning) in Technical details — a 10-line change but it's a copy/product decision.
- **13-D7** · Admin → Users has no search/sort and no pagination UI (fine for a household; note only if Path B managed instances grow).

### C9. Hand-rolled-vs-library verdicts
| Site | What it is | Library alternative | Verdict | Effort / risk | Note |
|---|---|---|---|---|---|
| `DoraSegmented.vue` | radiogroup segmented control | `BaseSegmented` (q-btn-toggle) | **merge** into one component (FU-848) | M / low | Dora's wraps + scrolls + has radio semantics; make Base the thin wrapper or retire Base. Decide in FU-848, execute at Stage 2 of chunk 20. |
| `SettingsMobileNav.vue` | tab strip + chips | `q-tabs`/`q-route-tab` | **keep** | – | 44 px, badge, group→first-leaf semantics; q-tabs would need the same custom chips. |
| `EncryptionKeyBanner.generateFernetKey` | 32 random bytes → url-safe b64 | none needed | **keep** | – | 6 lines, correct. |
| `AuditLogSettings.exportCsv` | CSV escape + blob download | `papaparse` / `quasar exportFile` | **wrap** — use Quasar's `exportFile` for the download half | S / low | Keep the 8-line escaper. |
| `AdminSystemRegionSettings` preview + choices | Intl-based preview, static choice lists | — | **keep** | – | Plain Intl, no round-trip. |
| `StockLocationsSettings` expansion in localStorage | persisted set | `useStorage` (VueUse — not a dep) | **keep** | – | R-026 carve-out documented. |

### C10. Standards drift (R-0NN)
- **13-R38** · R-034 bare icon names: `VoicePicker.vue:117 name="download"`, `AuditLogSettings.vue:186 icon-right="chevron_right"`. **Change:** `ICONS.download`, `ICONS.chevron_right`. **execute**.
- **13-R39** · FU-671 `text-color="white"`: `AuditLogSettings.vue:163,218` (+ `ApiAccessSettings.vue` ×4, `AdminDataBackupRestore.vue:227` — chunks 16/18). **execute** under FU-671.
- **13-R40** · R-002 token drift: two focus-ring tokens with different values — `--focus-ring` (= brand primary, 27 uses) and `--ring-focus` (35 % alpha, 8 uses: `SettingsNavGroup:110,151`, `DoraSegmented:104`, `VoicePicker:390,474`, `SettingsMobileNav:151`). Settings pages mix both. **Change:** owner-neutral — alias `--ring-focus: var(--focus-ring)` in tokens and migrate the 8 uses, or document the two tiers in the style guide. **FU** (cross-cutting; FU-010/224 theme sweep). Also `VoicePicker.vue:484–485` hex literal `#c10015` fallback — replace with `var(--semantic-danger)`. **execute**.
- **13-R41** · R-045 unauthenticated `<img :src>`: `UserAvatar.vue:16–21` → `/users/<id>/image` (same class as `StoreLogo`, 10-R35; both must move to the authed-image helper the chunk-10 finding names). **execute** with 10-R35.
- **13-R42** · R-019 comment≠code: `user.py:324 # TODO: avoid god object | separate auth credential from user profile` — a standing TODO with no FU. **FU** (design; "when a second credential type arrives").
- **13-R43** · `clock.py:6` "App-wide adoption of this boundary is FU-174" — FU-174 is resolved; the live tracker is R-021. **Change:** reword. **execute**.

### C11. Ride-along signals for FU-010 / FU-224 (theme / colour)
- Two focus-ring tokens (13-R40). · `AccountSettings.vue:391–394` falls back through `--surface-base, var(--surface, transparent)` — check which exists; `SettingsShell.vue:413,432` carry `transparent`/rgba fallbacks for `--border-default`/`--overlay-hover` which **are** defined (`tokens.scss:150,159`) — drop the fallbacks. · `VoicePicker` `--negative` hex fallback. · `UsersAdminSettings.vue:41–43` avatar `color="accent" text-color="dark"` — Quasar palette names, not tokens (D-002 ride-along).

---

## D. Test plan — Settings shell

| Test | Layer | Priority | Trigger to write it |
|---|---|---|---|
| `PATCH /app-settings {nutrition_mode:'bogus'}` → 400 with `detail` naming the options | pytest | must-write-before-ship | 13-R1 fix |
| Admin PATCH `/users/<id>` with malformed / duplicate email → 422/400; valid email sets `email_verified` | pytest | must-write-before-ship | 13-R2 |
| Deactivate admin B, delete admin A → 400 "last admin" | pytest | must-write-before-ship | 13-R3 |
| `/health` emits `products_policy.search_url` (or chosen key) and never drops existing keys | pytest | nice-to-have | 13-R4 |
| `familyAndModeOf(normaliseLegacyTheme('pesto-noir'))` → pesto/dark | vitest | nice-to-have | 13-R6 |
| `useAppSettingField` reverts the draft and toasts on a rejected save | vitest | nice-to-have | 13-R9 |
| Admin user list requests > 50 rows (`limit` param present) | vitest (service) | nice-to-have | 13-R5 |
| `HealthInfo`/`AppSettings` TS types compile against a fixture of the real DTO keys (`designTokensDeclared.spec.ts` style contract check) | vitest | nice-to-have | 13-R16 |

Existing coverage is good on the admin/auth boundary (17 app-settings, 7 users-admin, 17 user-router, 7 operational-config). No Playwright.

---

## E. Proposed follow-ups (orchestrator allocates ids)

- **urgent** · bug · `update_app_settings.py:174` returns a tuple on invalid `nutrition_mode` → 500 (13-R1). Resolve now (Stage 2).
- **urgent** · bug · admin email edit skips validation/uniqueness/`email_verified` (13-R2). Resolve now.
- **urgent** · bug · delete-last-admin guard ignores `is_active` (13-R3). Resolve now.
- bug · members never see the Product Search nav entry — URL read from admin-only `/app-settings` (13-R4). Resolve now; publish on `/health`.
- finding · settings-page save/notify/load pattern copied 13× → `useAppSettingField` + `appSettingsStore` (13-R9/R10/R36). Stage 2 of this chunk.
- finding · `/health` probed up to 9× per cold load; `alembic_version` queried per probe (13-R37). Stage 2.
- finding · two focus-ring tokens with different values (13-R40). Fold into FU-010/224.
- finding · `VocabListEditor` not reused by Stores / Dietary tags (13-R17). Stage 2.
- finding · 12 unreachable admin banners duplicate the router guard (13-R13). Stage 2.
- finding · dead `/app-settings/probe` route + client + tests (13-R19). Stage 2.
- finding · R-057 contract drift ×4 in `healthApiService.ts` / `appSettingsApiService.ts` / `authApiService.ts` (13-R16). Stage 2.
- finding · `User` god-object TODO (`user.py:324`) has no tracker (13-R42). Design; later.
- decision · 13-D4 text-size range 87.5–125 % vs feedback 75–150 %. Owner.
- decision · 13-D6 show `version`/`schema_version` on About. Owner.
- decision · 13-R15 drop admin "set another user's picture"; add "Remove picture" to the Users overflow. Owner (default: yes).
- advance · FU-656 → publish `password_min_length` on `/auth/capabilities`, derive the TS constant (13-R12). FU-654 (+2), FU-671 (+2 here, +5 in chunks 16/18), FU-668 (+1), FU-923 (+2 raw-table sites), FU-848 (merge decision), FU-672 (icon duplication nav↔page: the `icon` prop on `TaxonomyManagerPage`/`SettingsPageHeader` still has to be kept in step with `SettingsShell` by hand — resolve by exporting the nav table and looking the icon up by route in `SettingsPageHeader`; Stage 2).
- cross-ref · UserAvatar `<img>` joins 10-R35's authed-image helper (13-R41).

## F. Summary for the register

- FST rows: 15 golden + 13 edge + 4 gate · Help entries: 14 (new 12 / reworded 2 — 'Theme, font, and text size', 'Manage other users') · Review findings: 43 (execute 36 / FU 5 / waive 1 / decisions 3 in C8) · Tests: 8 (must-write 3) · Bugs: 4 verified (R1–R4) + 4 latent (R5–R8)
- Feedback coverage — `# SETTINGS`: theme type/palette split → covered (13-D2); profile picture + header avatar → covered (13-D3). `# NO AREA / MISC` Settings-adjacent bullets: "Settings in both main menu and user dropdown" → covered (13-D1); "text size 75/100/150 %" → partial, owner decision 13-D4; "rename" (product rename) → done 2026-07-01 (P8-01), out of scope; menu hover double outline / menu bar border / 404 page theme / loading skeletons / undo cross-app / pesto button brightness / QR logo centring / consistency & uniqueness / usage analytics / `.local` folder + rolling logs / dark-mode text visibility → **out of scope here → chunk 20 (cross-cutting) / chunk 19 (ops)**, each one line.
- One-liner: the settings IA is finished and clean; what's left is three real server bugs on the admin edges (invalid nutrition mode 500s, admin email edits unvalidated, last-*active*-admin not guarded on delete), one functional gap (members never get the Product Search link), and a thirteen-fold copy of the same save-a-field page pattern that one composable + one store would retire.
