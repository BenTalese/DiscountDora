# Changelog

All notable changes to Dashy Dora live here. Versions follow loose
semver — major bumps signal schema or breaking-config changes.

## [Unreleased]

### Fixed
- **Dates now show in your region's format everywhere, not US month-first (2026-08-13, design-remediation DR-14).** Dates across the app — shopping lists, meal plans, alerts, the dashboard, recipe "last made", stock-item history, price charts, admin timestamps — were rendered using *the browser's* locale instead of the household's, so on an Australian install they came out US-style ("7/17/2026", "Jul 13"). Every date now goes through a single formatter that uses the install's locale (the same one that already drives money formatting), so they read in the household's format ("17/07/2026") consistently, and changing the install's region updates them everywhere at once. *(Two related pieces remain for a follow-up: asking your region during first-time setup instead of defaulting to Australian, and a rare theme-flicker when the OS light/dark setting changes mid-session.)*
- **Page toolbars no longer overflow the screen on a phone or collide with the title on desktop (2026-08-13, design-remediation DR-9).** On a narrow phone the shopping-list toolbar (Quick add · grouping · Refresh deals · Select · More) ran ~255px wider than the screen — the last actions were unreachable without scrolling sideways, and the page title truncated to "Shoppin…". On desktop (~1280px) the same toolbar squeezed the title into a mid-word wrap ("Shopping / lists") colliding with the buttons. The shared toolbar now lets its actions **wrap onto their own line** below the title instead of forcing everything onto one row — so there's no sideways scrolling on any page that uses it, and the title always gets its own line. *(Verified: 0px horizontal overflow at 375px, title uncollided at 1280px.)* Separately, on the **stock list**, long item names now **wrap to two lines on phones** instead of truncating after ~10 characters ("Barilla Pa…"), so you can actually read them. *(Further mobile polish — collapsing the busiest toolbars and stock-row action icons into a "More"/overflow menu, and squaring up a few half-empty dashboard card rows — is tracked as a follow-up.)*
- **The startup splash can no longer get stuck over the app, and loading states show proper placeholders (2026-08-13, design-remediation DR-8).** Three loading-experience fixes. **(1)** The "Waking up Dora…" startup splash is dismissed by a reliable timer now, instead of waiting for a screen-repaint that a **backgrounded or throttled tab never delivers** — previously, opening the app in a background tab (or on a device that paused painting) could leave the splash frozen full-screen *on top of* the loaded app, silently swallowing your taps. It also drops out of the way instantly the moment the app is ready, so it can't block anything even mid-fade. **(2)** The **dashboard** now shows content-shaped **skeleton cards** while it loads (like the other pages already did), instead of a bare spinner and a literal "Loading totals…" line — so it settles into its real shape rather than flashing empty then popping in. **(3)** On the stock list, the little **"Dora thinks…" hint pill** and the **Buy/Wait/Skip badge** — which load a moment after the row — now **fade in** into space the row already reserves, instead of popping in and nudging the row's text sideways. *(Investigated a related report of the splash sitting for 2+ seconds on a warm reload: that's development-server rebuild + backend warm-up time, not the app itself — a production build doesn't have it.)*
- **A few labels/captions now render at their intended (smaller) size (2026-08-13).** Some meal-planner text — the "Build my week" dialog's field labels, hint boxes, day headers and cook-batch markers, the reconcile-nudge link on the Meal Plans page, and the dashboard "reconcile past meals" chip caption — declared their size using a design-system size token the wrong way (a bare unitless value, which browsers silently ignore), so they fell back to the surrounding body size and read slightly too large. They now use the token correctly and match their intended size. Purely visual; no behaviour change. (D-017, follow-up from the DR-2 review.)
- **Stock levels now read the right way round — green, amber, red — and the row colours have a key (2026-08-13, design-remediation DR-2).** The coloured square on each stock row (and the matching counts in the footer, the level pickers, cook mode, recipes, stocktake — everywhere) had its colours **backwards**: "Low" showed **red** while "Out of stock" showed **grey**, so the more urgent state looked calmer than the less urgent one, and a grey "out" square was indistinguishable from a disabled row. Levels now escalate properly — **Stocked = green, Low = amber, Out of stock = red** — with grey reserved for "level not set / unknown". The fix lives in the single place all those surfaces read their colour from, so they all corrected together. On top of that, the Stock overview's **filter panel now carries a legend** — "what the row colours mean" — decoding the level squares *and* the row highlights that previously had no explanation: the essential-item left stripe, the amber "needs attention soon" and red "needs attention now" outlines, the **dimmed row** (which used to look like a bug — it means "out of stock, and not marked essential"), and the pulsing box that means "due for a stocktake check". *(A cross-theme visual pass is noted for verification.)*
- **Settings pages no longer let the scrollbar sit on top of the content (2026-08-13).** On most Settings pages the vertical scrollbar was painted right over the right edge of the form (the same issue Stock Overview had). The Settings content pane now keeps a small gap between the content and the scrollbar (and reserves that gap so nothing shifts when a page grows long enough to scroll) — the same fix already applied to the stock list.
- **The Settings header no longer overflows on a phone (2026-08-13).** On mobile the top row of Settings was too crowded — the "Sign out" button got squished and the page could scroll sideways when it shouldn't. The **duplicate donate button is now hidden on mobile** (the app's main top bar already has one), **"Sign out" collapses to just its icon**, and the admin **Settings / Admin** toggle is trimmed slightly, so the row fits within the screen (down to ~320px wide) with no horizontal scroll. Desktop is unchanged — full "Sign out" label and the donate button stay.
- **Previewing a neural voice now works on phones, not just the server's own browser (2026-08-13).** On **Settings → Voice**, tapping **Preview** on a downloaded neural voice worked on a desktop browser but **errored on mobile** (Android Chrome/Firefox). Cause: mobile browsers only allow audio playback that's tied to a tap, and the preview fetched the audio from the server *first* and then tried to play — by which point the tap "permission" had expired, so the browser blocked it. The preview now claims that permission **the moment you tap** (priming a silent audio element inside the tap) and swaps in the real audio once it arrives, so it plays on mobile too. *(A phone check is still worth doing — noted for verification.)*
- **The "New version available" prompt no longer fires spuriously on the Notifications page (2026-08-13).** Visiting **Settings → Notifications** could pop a "new version available, reload" message even though nothing had been deployed — most reliably in development. Cause: that page is the only one that registers the push service worker, and on a fresh session that registration made the *first* service worker take control of the tab, which the code mistook for "a new build replaced the old one". It now distinguishes the initial service-worker claim from a genuine replacement (only prompts when a worker was already in control at page load), so the notice only shows when there's really a newer build cached. *(See the related banner change under "Changed".)*
- **The dashboard's "Set a budget" button now lands on the Money page (2026-08-13).** The budget nudge on the Dora score card linked to the Appearance settings page (the old combined "Preferences" URL) instead of **Settings → Money**, where the budget input actually lives — so tapping "Set a budget" dropped you on theme-and-font options with no budget field in sight. It now routes straight to Money.
- **Dora's helper no longer crowds the corner or covers the page (2026-08-12, design-remediation DR-7).** Three placement/tone fixes around the Dora assistant: **success and error toasts no longer stack on top of the mascot** — they popped up in the same bottom-right corner as the Dora launcher, so a "Saved" or "Added to list" toast landed right over her; the toast column now sits clear above the mascot (and respects the phone's safe area). The **first-time "Hi! I'm Dora" tip now auto-dismisses** after a few seconds instead of hovering over page content until you click it, and the launcher itself now honours the mobile safe-area inset so it doesn't tuck under a home indicator. And Dora's **greeting uses your name capitalised** ("Hi, Dora!" not "Hi, dora!") and drops a cryptic in-joke ("Burger online" → "Dora reporting for pantry duty"). *(A separate remaining item — a toast fired right before you navigate can still linger onto the next page — is tracked for a follow-up that routes all toasts through one helper.)*
- **Marking a stock item "open" can now be cancelled cleanly (2026-08-12, design-remediation DR-5).** When you mark an item as opened, Dora asks whether to update its effective expiry (opened milk goes off fast; opened jam barely moves). Previously that pop-up **only** controlled the expiry — the item was flipped to "open" the instant you clicked, so pressing Escape, clicking outside the dialog, or hitting "Skip" all left it opened with **no way to back out**. The prompt now has **three clear choices**: **Update expiry** (open it and set the new date), **Skip** (open it, leave the expiry alone), and **Cancel** — and dismissing the dialog with Escape or a backdrop click behaves like Cancel: **nothing is written, the item stays sealed.** So the "open" toggle is only ever committed when you actually confirm it. (Applies on both the stock list and the item's detail page, which now share one implementation.)
- **Interaction-detail polish across dialogs, the stock row and the bulk bar (2026-08-12, design-remediation DR-3).** A cluster of small "this looks like raw Quasar" tells, now cleared: **dialog buttons no longer SHOUT** — every confirm/prompt dialog that still rendered its buttons in ALL-CAPS ("CANCEL", "SKIP", "GOT IT", "OK") now uses sentence case, matching the rest of the app (swept across ~15 files, plus the one raw uppercase "Pause" button in cook mode). The stock row's **open / in-use toggle** dropped the **padlock** icon — which read as a security lock — for a **sealed-box → open-box** glyph that actually means "this packet is opened", and the icon-only button now carries a proper screen-reader label (it had only a hover tooltip before). And the **bulk-select bar's disabled actions** ("Add to list…", "Log waste…", etc. when nothing is selected) now visibly **grey out** instead of staying the same white as the enabled ones — they were only dimmed by opacity, which didn't show on the bar's background, so they looked clickable when they weren't. (The cart add/remove glyphs the same audit flagged were already distinct — icon + colour + tooltip per state — so no change there.)
- **Two low-contrast badges fixed (2026-08-12, design-remediation DR-1b).** The **alerts count badge** (the red number on the notifications bell) used the theme's semantic-negative red, which is *lightened* in dark themes — so the white number on it dropped to ~3:1 and was hard to read. It now uses a fixed deeper red across all themes (white number stays ≥6:1). The **Buy / Wait / Skip verdict badge** rendered its label in the full-strength semantic colour on a pale tinted chip, which failed contrast badly (the "Wait" amber was ~2:1); the label now uses the primary text colour (dark on light themes, light on dark), so it's clearly legible in every theme while the chip's coloured border and tint still signal buy/wait/skip. (Two other spots the audit flagged — the primary-button brand colour and the yellow-on-green wordmark — are left as-is: the button is a borderline brand-pairing call and a logotype is exempt from contrast rules. The dashboard/stock "Essential" count and the broader brand-secondary colour are being reworked together — see below.)
- **Muted/secondary text now meets the WCAG AA contrast floor in every theme (2026-08-12, design-remediation DR-1).** The de-emphasised "muted" text colour (used for captions, footer stats, timestamps, metadata) measured as low as **3.0:1** against its background in several light themes — below the 4.5:1 accessibility floor, so it read as faint rather than merely quiet. The `--text-muted` token was retuned across all **10 themes** (5 families × light/dark) so it clears **≥4.5:1 on every surface** while staying clearly lighter than primary/secondary text (the hierarchy is preserved). Light themes darkened the muted grey; the two dark themes that were marginally under (Lemon Tart Dark, Blueberry Dark) lifted it slightly. Verified with a contrast-ratio probe over every text/surface pair. (Secondary text already passed and was left unchanged. A few individual component badges the audit flagged — the Buy/Wait verdict badge, the alerts count badge in dark mode, the dashboard "Essential" stat, the wordmark — involve shared semantic colours or tiny type sizes and are tracked separately as DR-1b.)
- **A round of copy and wording fixes across the app (2026-08-12, design-remediation DR-4).** A cluster of small text bugs the UX review turned up, now cleared: the use-soon suggestion that read **"… expires expired 3 days ago"** now reads "… expired 3 days ago"; alert details that said **"N day(s)"** now pluralise properly ("1 day" / "3 days"), via a single shared helper so it can't drift again; the dashboard greeting shows your name **capitalised** ("Good afternoon, Dora", not "dora"); the savings stat label reads **"saved vs RRP"** (was "saves vs rrp"); recipe cards no longer render a **duplicated chip** ("Dessert · Dessert") when a recipe's cuisine and category are the same word; the image-upload buttons say **"Take a photo"** / "Add image" / "Add logo" instead of the cryptic "Add (camera)" / "Add (file)"; the essential-out-of-stock alert copy is **action-neutral** (it no longer tells you to "add it to your shopping list" next to a "Mark restocked" button); and the **Batch** cooking-style explainer is rewritten in plain words (no "cook pool" / "shortfall" jargon).
- **The grocery budget no longer switches itself off when you change the period (2026-08-12).** Turning the budget on and then changing the period (Weekly ↔ Monthly) before entering an amount used to flip the budget back off. The Money page has been reworked to be **value-driven** — there's no separate on/off toggle any more: type an amount to set a budget, clear it to turn the budget off. With no toggle whose state could get out of step, the period picker (which only appears once there's an amount) can't knock the budget off. (See the household-budget change below for the bigger picture.)
- **Blank screens when navigating between pages (2026-08-11).** After the R-036 page-height sweep (FU-609) moved every in-app page onto a `<q-page>` root, clicking from one page to another left a **blank screen** — only a full browser refresh would paint the target page. Cause: the `MainLayout` router-view's fade used `<FadeTransition mode="out-in">`, and with the new `<q-page>` page roots that wedged Vue's transition state machine — the leaving page unmounted but the entering page never mounted (and stayed wedged for every subsequent navigation). Dropping `out-in` (pages now cross-fade) makes every client-side navigation render reliably. This is the same "empty container on route change" the FU-609 session observed and mis-attributed to an in-app-browser limitation; it was the real regression.

### Added
- **Auto mode for meal reconciliation now shows a log instead of asking you to confirm each meal (2026-08-13).** When "Assume past-day meals were cooked" (auto-drain) is on, Dora already marks planned meals cooked as each day passes — but the reconcile page still treated every one as a to-do to walk through, and the dashboard chip + "reconcile overdue" reminder still nagged you about meals Dora had already handled. Now, in **auto** mode, `/meal-plans/reconcile` shows a **read-only log** — "here's what happened to your meals," newest first, grouped by day, with a status on each (Logged as cooked / Cooked / Not cooked / Skipped) — and the **chip and the overdue nudge no longer fire** (auto means hands-off). **Manual** mode is unchanged: it still shows the confirm-each runner and its reminders. The switch is automatic based on the install setting; an admin flips it under Settings → Admin → System → Meal reconciliation (which now also relabels its shortcut "View meal log" vs "Go to reconcile"). *(The log is view-only for now — a follow-up will assess whether it needs a per-row "didn't cook / adjust" correction. This also finishes the meal-reconcile "history view" that was scoped but never built.)* Dora stores several secrets encrypted at rest (your AI provider's API key, the SMTP password, the VAPID push private key), which needs the `DORA_SECRET_ENCRYPTION_KEY` environment variable set. Previously you'd only find out it was missing when a save silently failed. Now the **Settings → Assistant** page (per-account) and the admin **System → Email** and **System → Push notifications** pages show a clear warning banner **when the key isn't set**, explaining what's needed — and offer a **"Generate a key"** button that mints a valid key right in the browser for you to copy into your environment. The generated key is **never saved or transmitted** (Dora just shows it to you); it's the exact same kind of key the documented `python -c "…Fernet.generate_key()…"` command produces. Once the environment variable is set, the banner disappears.
- **The Settings sidebar now flags outstanding unlinked ingredients with a count badge (2026-08-11).** When you have recipe ingredients that still need linking to stock items, the **Unlinked ingredients** entry under Settings → Kitchen setup shows a small badge with how many there are — so you can see there's cleanup waiting without opening the page. The badge updates as you link them and disappears once everything's linked. It shows in both the desktop sidebar and the mobile settings nav.
- **Cook once, eat several days: "cook batches" in the meal planner (2026-08-11).** For households on the **Batch** cooking style (Settings → System → Cooking), you can now link the same meal across several days into a single cook — "cook the curry once on Monday, eat it Mon/Tue/Wed dinner." On any planned meal, the ⋮ menu offers **"Cook once for more days…"** → tick the days it should cover; the linked meals show a **"Cook · serves N"** marker on the cook day (the earliest) and **"Leftovers"** on the rest, with the total servings the one cook needs to produce. **"Separate this cook"** un-links them again. It's the missing middle between planning every day distinctly and repeating an identical week — and the shopping list is unaffected (cooking once vs three times needs the same ingredients). **"Build my week" also proposes cooks for you**: for a Batch household it plans one recipe across a run of days per meal slot (rather than a different recipe every day), which the Review step shows with the same Cook/Leftovers markers before you save. Fresh-style households don't see any of this; the planner stays pure scheduling and the builder plans a distinct recipe per day.
- **Recipe cards show the ingredient count (2026-08-10).** Each recipe card in the cookbook (and the "Recipes using this" tab on a stock item) now carries a small **"N ingredients"** chip alongside the existing time / serves / difficulty chips, so you can gauge a recipe's involvement at a glance. Singular "1 ingredient" is handled, and a recipe with no ingredients yet shows no chip (rather than "0 ingredients"). Display-only count of the already-loaded ingredient list — no new API field.

### Removed
- **Quick-add no longer remembers which shopping list you picked — it always asks when you have more than one draft (2026-08-13).** Settings → Appearance carried an **"Always ask which list"** toggle whose *off* (default) state made Dora remember the draft list you last picked and silently send later quick-adds there for the rest of the tab session. On reflection that was the wrong default: multiple draft lists are deliberate, so quietly reusing the last pick was more annoying than helpful. The toggle and the remembered-pick behaviour are **both gone** — when you have two or more draft lists, adding an item always shows the "Which list?" picker; with a single draft it still adds straight there (no prompt), and bulk-adding a selection still routes the whole batch to the one list you pick for the first item. **Pre-release hard change:** the stored per-user `always_ask_which_shopping_list` value + column are dropped, not migrated.
- **The install-wide "AI master switch" is gone — anyone can use AI mode if they want to (2026-08-12).** Admins used to have a master kill-switch at **Settings → System → AI assistant** that, when off, forced every account's AI mode off regardless of their personal setting. It didn't make sense for this app — there's no reason to stop a household member connecting their own LLM — so both the admin toggle and its whole settings page have been removed. **AI mode is now purely a per-account choice**: each person turns it on and configures their provider on their own **Settings → Assistant** page, exactly as before, just without an install-wide gate sitting on top. The old admin page's guidance about the encryption key (for paid-provider API keys) moved onto the per-account Assistant page as a warning banner (see Added). **Pre-release hard change:** the stored `master_llm_enabled` value + column are dropped, not migrated; the old admin page + URL are gone (no redirect — pre-release).
- **The per-account "Show money features" toggle is gone — money is one install-wide switch now (2026-08-12).** Settings → Money used to carry a personal **"Show money features"** toggle on top of the admin's install-wide money switch, so every member had to opt in individually. That per-user layer has been removed: when an admin turns money on under **System → Features**, dollar surfaces (recipe costs, list totals, the budget card) show for everyone; off hides them for everyone. Money now reads as a **kitchen-setup** concern rather than a personal-account one, so its settings page moved out of the personal **Account** group into **Kitchen setup** and only appears when the install has money enabled. **Pre-release hard change:** the stored per-user `money_features_enabled` value is dropped, not migrated.
- **The "Legacy voice override" is gone from Admin → System → Voice, and the page now explains itself (2026-08-11).** The admin Voice settings page carried a **"Legacy voice override"** field — an absolute path to a single `.onnx` file that, when set, won over the voice catalog for every request. It existed only as back-compat with an original test page and had no place in a pre-release app; it's been removed end-to-end (`AppSetting.piper_voice`, the resolver/DTO/update plumbing, the DB column, and the `DORA_PIPER_VOICE` env var). Piper still resolves voices from the bundled catalog + voices folder exactly as before. The page was also **reworked for clarity**: a new "How Dora's voice works" intro spells out that this page is install-wide engine plumbing (where the server finds Piper) while the voice each person actually hears lives on the per-user **Settings → Voice** page, and the two remaining fields (Piper program, Voice models folder) now say that shipped Docker/desktop builds fill them in automatically and blank is normal. **Pre-release hard change:** any `DORA_PIPER_VOICE` env var or stored override value is dropped, not migrated.
- **The per-user "Meals per week" preference is gone (2026-08-11).** Settings → Preferences used to carry a **"Meals per week"** number that fed the meal-plan builder's target count. The 2026-08-07 builder rework replaced that single number with the explicit day × meal-slot toggle grid ("Which days" × "Which meals"), so the setting no longer drove anything — a control that did nothing. It's been removed end-to-end: the settings row, the `meals_per_week` field on your account, and the plumbing behind it. **Pre-release hard change:** the stored per-user value is dropped (not migrated); the builder decides the meal count from the toggles you pick.

### Changed
- **Settings → Voice simplified, and picking the voice is now one choice (2026-08-13).** The Voice page was tidied to match the rest of Settings:
  - The **Microphone** and **Spoken replies** sections are now just a **heading + toggle** — "Enable microphone voice input" and "Let Dora speak her replies" — with the explanatory blurbs removed.
  - The separate **"Voice engine" (Dora's voice / Browser) switch is gone.** You now just **pick a voice**: choose one of the neural voices, or the new **"Device default voice"** card (your browser/device's built-in text-to-speech, always available, no download). Selecting a neural voice automatically uses it; selecting Device default uses the browser voice — no second toggle to keep in sync. The Device default card has its own **Preview** (spoken by the browser voice). Section copy updated to "Download a neural voice you like and select it, or use the default device text-to-speech voice."
  - *(Voice choice is per-account — your engine and chosen neural voice are yours; the downloaded voice **models** are shared on the server, but which one you hear is your own setting.)*
- **Settings → Notifications cleaned up: clearer gating, fewer blurbs, and setup links for admins (2026-08-13).** A batch of fixes to the Notifications settings page:
  - The **page subtitle is gone** — it claimed Dora reaches you "on this device", which was misleading (the email digests are per-account server settings, not per-device).
  - The **Weekly deals email** section now only appears when the install actually has **product data** (its whole information source) — with no products it's hidden entirely, both here and as the per-user column on the admin **Users** page. Its description was rewritten to explain the dependency ("if you have a tool that regularly pushes product deal data into Dora…, keep the data flowing for best results") and it now carries the **same email-must-be-set-up barrier** as the alerts digest.
  - The **email/push "not set up on this install" notices are now prominent warning cards** instead of faint grey footnotes, so it's obvious *why* a toggle is disabled. And **if you're an admin**, the card gives you a direct **"Set up email" / "Set up push"** button to the relevant System settings page, instead of telling you to "ask an admin" (you are the admin).
  - The **Alerts email digest** and **Push notifications** sections were trimmed to just their heading + toggle — the explanatory paragraphs and the redundant repeated row labels ("Email me a digest of my alerts", "Send me push notifications on this device") were removed (the toggles keep accessible labels for screen readers).
- **The "new version available" prompt is now a dismissible in-app banner, not a one-shot toast (2026-08-13).** When your browser has fetched a newer Dora build and needs a reload to apply it, the notice used to be a toast that appeared once and was easy to miss. It's now a **banner pinned under the header** (next to the offline banner) with a **Reload** button and a dismiss **✕**, shown to every signed-in user — because each browser holds its own copy of the new build and an admin can't reload it for you. *(A separate, operator-facing "a newer Dora release is available to deploy" notification for admins is tracked as a follow-up.)*
- **Password fields no longer show a standing "At least 8 characters" hint (2026-08-13).** Every new-password field (register, admin setup, password reset, and Account → change password) carried a permanent helper line ("At least 8 characters — a passphrase works well."). It's removed — the inline validation message that appears if the password is too short is enough, so the fields stay uncluttered until there's something to say.
- **Settings → Preferences is now "Appearance", trimmed to just the look-and-feel controls (2026-08-13).** The page (and its sidebar entry) is renamed **Appearance**, and the clutter is gone: the page subtitle and every section blurb were removed (the controls are self-explanatory), **"Mode" is now "Theme mode"**, and **Font family** and **Text size** were lifted out of a "Typography" sub-group to become top-level headings in their own right, sitting **left-aligned** under their labels like Theme mode and Theme (they were right-aligned in a two-column row before). A layout bug is fixed too: the Theme-mode selector's background pill **stretched edge-to-edge across the page** instead of hugging its three options — it now sizes to its content. The two settings that weren't about appearance moved off the page: the **Zero-Input Pantry** toggle went to **Settings → Assistant** (see below) and the shopping-list "Always ask which list" toggle was removed outright (see Removed).
- **The Zero-Input Pantry toggle moved to Settings → Assistant (2026-08-13).** Dora's infer-my-stock-levels switch used to sit on the Appearance/Preferences page, which was an odd home for a behaviour of the assistant. It now lives on **Settings → Assistant** — the natural place for "what Dora does on your behalf" — as its own **Zero-Input Pantry** section with a tightened description and a **Learn more** link that jumps straight to the "Dora thinks…" help guide. Nothing about the toggle's effect changed; only its location and surrounding copy.
- **Dora's inferred-stock hint is quieter, clearer, and only speaks up when it matters (2026-08-12).** The Zero-Input Pantry hint that sits beside each stock item's recorded level — Dora's own guess at whether you're Out / Low / Stocked, worked out from your purchases, rebuy cadence and cooking — was a cramped little pill packing five things at once (an icon, a coloured status dot, "Dora:", the band, and a "· low" confidence tag), and its dot sat right next to the level's own dot, so two dots competed at the same spot. It's been cut back to a single purpose: it now shows **only when Dora's guess differs from what you recorded** — a small amber **"Dora thinks low/out/stocked"** — which is the one case actually worth a glance. When Dora agrees with you (whether she's sure or not) she now says **nothing at all**, so ordinary rows stay clean. The band, confidence and the plain-English reason move into the hover tooltip, and a quick check reconciles the two. The pill uses dark, legible text on the amber tint (not amber ink on amber, which failed the contrast floor — the same D-002 fix already made for the Buy/Wait/Skip badge), and its icon changed from what was accidentally a **magic-wand** glyph to a lightbulb-with-question-mark that reads as "a hunch". A new **Help → Guides → Stock** entry explains the whole thing, and the per-account off switch (Settings → Preferences) is unchanged.
- **Settings → Assistant reworked: pick a "Mode", and connect several language models at once (2026-08-12).** The Assistant page was redesigned around the two questions that actually matter. The disabled "Enable AI mode" toggle with the easy-to-miss reason text is **gone** — in its place is a single **Mode** dropdown: **Basic (built-in)** by default, plus every language model you've **connected** (only models that have actually answered a test appear in the list, so you can never pick a half-configured one). Below it, **each provider (Ollama, OpenAI, Anthropic, Google Gemini) is its own block with a live status chip** — *Not configured · Checking… · Connected · Couldn't connect* — and you can **fill in details for several providers and flip between them freely** (previously the page only held one provider's settings, so switching wiped the last one and blocked you with "enter OpenAI details"). Details are **checked the moment you enter them**: typing an Ollama base URL pings the server and turns **Model into a picker of the models actually installed** there (the auto-discovery that had regressed), and a paid provider's key + model are verified on entry. The page copy is trimmed throughout — the title is just **"Assistant"** with a short D.O.R.A. intro linking to her help page, the "Show chat bubble" setting collapses to a single row, and the per-provider descriptions/dividers are gone. **Under the hood** each provider's config now lives in its own `UserLlmProvider` row (a provider isn't selectable until a live probe verifies it); `User` keeps only the active-provider pointer + AI-mode opt-in. **Pre-release hard change:** any previously-saved single-provider config is dropped, not migrated — reconnect your provider on the redesigned page.
- **Timezone, currency and locale are now one page: Settings → System → Region & locale (2026-08-12).** The household timezone and the currency-&-display-locale settings used to be two separate admin pages sitting next to each other in the sidebar. They're now combined onto a single **Region & locale** page — all three are the same "where is this household, moneywise and timewise" concern, so editing them together is simpler. Nothing about how each setting works changed (timezone picker with "Use this device", currency/locale inputs with the live money preview). **Pre-release:** the old separate URLs are gone (no redirects kept).
- **The grocery budget is now one shared household budget, not a per-person one (2026-08-12).** The budget amount + period used to live on each user account, but the budget tracks spend across **every finished shopping list** in the household — a shared total — so comparing it against a *personal* budget number never really made sense (and "is the week over budget?" in the meal planner could come out differently depending on who was signed in). It's now a single household budget, stored install-wide alongside the other shared kitchen settings. **Any household member can set it** from Settings → Kitchen setup → **Money** (it's shared config, like stores and stock locations — not admin-only), and the dashboard budget card + meal-planner budget defence all read the one shared value. This is the same "a household has one of these, not one per person" move already made for headcount and cooking style. **Pre-release hard change:** the old per-user budget values are dropped (not migrated) — set the household budget once on the Money page. (Internally: `budget_amount` / `budget_period` moved User → `AppSetting`, read via `/api/health.budget_policy`, written via a new any-member `PATCH /api/budget/settings`; engineering rule R-038 / ADR-034.)
- **Settings → Account is simpler and more direct (2026-08-11).** The page was streamlined end-to-end: the read-only identity block at the top (avatar + name + email + account ID) is gone; the **Profile picture** is now a circular avatar you click (or tap) to change — hovering shows a pencil overlay, and a small **Remove photo** clears it (the old rectangle + "add file" button are gone); and instead of a Save button per field there's a single **Save changes** bar at the bottom, with an unsaved-changes prompt if you navigate away mid-edit. **Changing your email is now just editing a field and saving** — the old flow that required your current password and a confirmation link to the new address was removed as overengineered for this app. The password-change fields stay (leave them blank unless you're changing it) but now save through the same global button. *(Self-hosted note: email changes now take effect immediately without an email round-trip; the address is still validated and must stay unique.)*
- **Settings → Kitchen setup is now a single flat list with distinct icons (2026-08-11).** The recipe taxonomy pages (Cuisines, Categories, Tools, Meal slots, Dietary tags) used to sit indented under a "Recipe taxonomies" sub-heading and all shared the same book icon. They're now flat entries in the Kitchen setup list like everything else, each with its own icon — a globe for Cuisines, a shape for Categories, a blender for Tools, a clock for Meal slots, and a leaf for Dietary tags — so they're easier to tell apart at a glance. Stock groups also picked up a clearer multi-tag icon (matching that it's about tagging stock items into groups).
- **"Unlinked ingredients" moved out of Admin into Settings → Kitchen setup, so any household member can reach it (2026-08-11).** The bulk-linker for recipe ingredients that didn't match a tracked stock item on import used to live under **Admin → Data**, which meant only admins could open it — even though it's ordinary recipe-data cleanup any recipe author does, and its endpoints were never admin-restricted in the first place. It now sits in **Settings → Kitchen setup** (just above the Recipe taxonomies), alongside the other shared kitchen data everyone curates. The old admin URL still works (it redirects), and nothing about how the linking itself works has changed.
- **Every in-app page now shares one page-height contract, so scrolling and full-screen layouts stay robust (2026-08-11).** Following the Cookbook fix, the remaining in-app pages were moved onto the same standard full-height page shell (engineering rule R-036) instead of hand-rolling their own layout with a hardcoded header offset that silently drifts when the app chrome changes (e.g. when the offline banner appears). Most pages look identical — this is preventive structural consistency — but the full-screen **Stocktake** and **Meal reconcile** runners and the **Settings** screen now size to the real viewport (no overshoot or double-scroll), and the Settings screen still falls back to a normal single-column scroll on mobile. No feature behaviour changed. (Internally: all remaining `MainLayout` pages now root on `<q-page>`; the two runners and Settings use the live-offset app-shell form; the stock-item detail page stays layout-agnostic so it still works both full-page and inside the Stock Overview peek.) The Cookbook's summary footer (recipe counts) is a sticky bar, but the page lacked a height contract, so on a short recipe list it floated up in the middle of the screen instead of resting at the bottom. The page now uses the standard full-height page shell (like Stock Overview), so the footer sits where it should whether the list is short or long. No change to how the list scrolls. (Internally this establishes a new engineering rule — R-036 — that in-app pages root on a proper page element with a real height contract instead of hardcoding pixel offsets.)

- **Household headcount and batch-cooking are now install-wide settings, not per-account (2026-08-10).** "How many people do you usually cook for?" and the "Batch / Fresh" cooking style used to be stored on each user account — so every person who signed up was asked their own headcount, even though a household has one. They're now a single shared setting for the whole install, edited by an admin under **Settings → System → Cooking**, and read by cook mode (recipe scaling) and the meal planner (the batch cook-pool tools) for everyone. As part of this, the two prompts were removed from the onboarding wizard (its first step is now just personal look — theme + font) and the per-user "Cooking style" toggle was removed from **Settings → Preferences**. **Pre-release hard change:** the old per-user values are dropped (not migrated) — set the household headcount + cooking style once in System → Cooking.
- **Onboarding got a slimmer top bar and a self-contained dark look (2026-08-10).** The first-run wizard's header — which showed a **Sign out** button, the mascot, and the "Dashy Dora" wordmark — is gone. In its place, a single slim row runs the width of the wizard: the **mascot**, the **Story/Setup progress rail**, and a persistent **"Skip onboarding"** button, spaced apart with room to breathe. Skip replaces the old sign-out as the escape hatch (it finishes onboarding and drops you into the app, where you can sign out normally); the duplicate skip buttons that used to sit inside the story and setup views were folded into this one. The wizard is now a **fixed dark canvas regardless of your chosen theme** (`data-theme="pesto-dark"`), so a light-theme user re-entering the tour no longer sees light cards floating on a dark background. On the welcome step: the greeting reads **"Hi, I'm Dora."** (was "Hi! I'm Dora."), the theme dropdown's **"System (follow OS)"** option is now just **"System"**, and the **"What should I call you?"** field was removed — your display name is the username you picked when you created the account, so onboarding no longer asks again.
- **"Restart onboarding" was removed from Settings → About (2026-08-10).** The re-run-the-welcome-tour button is gone. It was the path that let you land back in the wizard after already setting up — which could look broken once themes were involved — and the tour has little to re-offer an established household. (The dashboard's time-boxed "finish setting up" prompt, shown only if you *skipped* onboarding recently, is unaffected — that's for completing an unfinished setup, not restarting a finished one.)
- **The default-font option is now named "Nunito (Default)" (2026-08-10).** In both the **Settings → Preferences** font picker and the **onboarding wizard**, the font-family option that was labelled just **"Default"** now reads **"Nunito (Default)"**, so you can see what the default actually is rather than guessing. (The default removes the per-user font override and falls back to the app's base body font, which is Nunito.) The now-redundant standalone **"Nunito"** option — which rendered identically to the default — was removed to avoid two entries that look the same; any account that had explicitly picked "Nunito" simply shows "Nunito (Default)" selected (it renders the same, and `nunito` stays a valid stored value for back-compat).
- **Transactional emails now carry a branded header banner, and the password-reset copy was cleaned up (2026-08-10).** Every transactional email (password reset, verify email, email-change, password-changed, alerts digest) now opens with a **brand banner** — the Dora mascot on the left and the *Dashy Dora* wordmark in the Cute Dino brand font, centred on the brand-yellow strip — in place of the old plain "Dashy Dora" text heading. Because email clients strip web fonts (and Gmail/Outlook strip `data:` image URIs), the banner is a pre-rendered PNG embedded as an **inline CID attachment**: `send_email` wraps the message in `multipart/related` and attaches the image as `cid:brand-banner`, which the shared `_layout.html` header references (with "Dashy Dora" alt text so it degrades gracefully if images are blocked). On the **password-reset email** specifically: the button label is now **"Reset Password"** (was "Reset password"), the intro reads **"There was a request to reset the password on your Dashy Dora account."** (was "Someone asked to reset…" — it's almost always the account owner, not "someone"), and the redundant **"If you didn't ask for this, ignore the email — your password stays the same."** line was removed (the layout footer already covers the suspicious-email case).
- **Essential flag renamed `is_flagged` → `is_essential` end-to-end (2026-08-08).** The per-item "Essential" flag was stored and transported under the legacy name `is_flagged` — the DB column, the `StockItem` entity, every API request/response field, and the frontend models/stores/filters — even though every product surface (the Overview "Essentials" filter, the left-edge stripe, the auto-add "essential only" mode, the spreadsheet import mapping) already calls it *Essential*. It's now `is_essential` everywhere, so there's a single name across code and database. Delivered as a column-rename migration (`f4a2c7e9b1d3`, chained off the current head) plus a mechanical token rename across 45 files; the CSV export column and any import header now round-trip on `is_essential`. **Pre-release hard rename — no back-compat alias.** No behaviour change; verified by the full backend suite (299 targeted tests green), a real destructive-boot migration run (column confirmed renamed on all three dev DBs), and the frontend typecheck + affected unit tests.
- **Page titles in the mobile menu bar + browser tab are now Title Case (2026-08-08).** The mobile top-bar page name and the browser-tab title (both sourced from each route's `meta.title`) capitalise every principal word — "Stock Item", "Price History", "System: Alert Thresholds" — instead of sentence case, matching the main-menu labels (which were already Title Case). Interactive controls (buttons, dialogs, chips) deliberately stay sentence case; this page/tab-title exception is recorded as a carve-out on `DESIGN_STYLE_GUIDE` D-008 so it isn't "corrected" back later.
- **Stock Overview expiry dropdown is clearer (2026-08-08).** Every option now carries an icon — a **+** on the push shortcuts, an **✕** on Clear expiry, the bin on Log waste — and the push rows read **"Push expiry by 1 day / 7 days / 14 days"** (were "Push expiry +1 day / +7 days"). The toolbar **Export** button also swaps its generic "⋯" for a dedicated export glyph (tray-with-out-arrow); its menu still offers CSV + Print.
- **Stock Overview "Stocktake" attention pulse now breathes the button fill (2026-08-08).** When a stocktake is overdue the button drew a pulsing glow *ring* only; the button's fill tint now pulses in sync with the ring so the whole control breathes. Reduced-motion users get a static soft tint (no animation), as before.
- **Stock item detail — usual-store logos, stable Clear-expiry, reflowing recipe cards (2026-08-08).** Three small fixes on the detail page: (1) the **Usual store** dropdown now shows each store's logo — the uploaded image when there is one, the deterministic swatch otherwise — beside its name, matching the linked-products cards. (2) The **Clear expiry** ✕ moved to the *left* edge of the expiry button cluster, so clearing a date no longer shoves the +1d/+7d/+14d/Set buttons sideways (they stay anchored to the right; only the ✕ appears/disappears). (3) The **Recipes using this** cards now reflow by column count (a CSS auto-fill grid) instead of stretching within fixed Quasar breakpoints, so resizing the window adds/removes a whole column rather than continuously growing the cards.
- **"Build my week" now defaults to breakfast, lunch and dinner (2026-08-07).** The builder used to open with only the dinner slot ticked; it now pre-selects breakfast, lunch and dinner (whichever your install names) — the three main meals most households plan. Snack/dessert and any custom slots stay off until you tick them. Installs with none of those three named still open with a single dinner-ish slot.
- **"Build my week" is now driven by day and meal toggles instead of scope/count/slot-mode dropdowns (2026-08-07).** The builder's first step used to ask three overlapping questions — plan for *this week* or *a day*, then *how many meals* on a slider, then a *Spread / One slot / Pick slots* mode with its own follow-up picker. Which day you got, and which slots got filled, was inferred from that combination. It's now two plain rows of toggle buttons: **Which days** (Mon–Sun, each showing its date) and **Which meals** (your household's meal slots), each with a one-tap **Select all / Clear all**. Slots apply to every selected day — there's no per-day slot picking, deliberately. The meal-count slider is gone: one meal is planned per selected day × selected meal, and a live line tells you the total ("Dora will plan 6 meals."). Days already past in the current week render in place but greyed out and unselectable, so the row never reflows as the week goes on. New **Same meals every day** checkbox (shown once you've picked more than one day) builds a single day's line-up and repeats it across the days you chose — for anyone who eats the same thing all week. The dialog opens pre-set to every remaining day of the week plus your dinner slot, so one tap still gets you a week. Everything downstream — the editable review step, reshuffle, the what-you'll-need list, "I'll pick myself" — is unchanged.

- **Data-at-rest wrapping key renamed from `DORA_LLM_KEY_ENCRYPTION_KEY` → `DORA_SECRET_ENCRYPTION_KEY` (2026-08-04).** The env var that encrypts every secret Dora stores in the DB — SMTP password, VAPID private key, per-user paid-provider LLM API keys — was introduced (FU-153) for LLM keys and named accordingly, then quietly reused for the other two without renaming. Operators who didn't use LLMs reasonably assumed the gating didn't apply to them and were surprised when saving an SMTP password (or VAPID private key) failed with an "LLM key isn't configured" error. Renamed to reflect what it actually is (Dora's data-at-rest KEK); the module also moved from `dora_api/infrastructure/llm/key_encryption.py` → `dora_api/infrastructure/security/secret_encryption.py`. Error messages, help text on Admin → System → Email / Push / AI Assistant, the Help page, README, `.env.example` and the desktop-bundle key file (`.llm_key_encryption_key` → `.secret_encryption_key`) all updated. **Pre-release hard rename — no back-compat fallback:** the old env var is no longer read, so any install that still sets it must rename before boot (existing ciphertext decrypts fine, the wrapping key itself is unchanged). Bucket-C 400 message now says "DORA_SECRET_ENCRYPTION_KEY isn't configured…" so the fix is obvious.

### Fixed
- **Security actions are no longer double-logged in the audit trail (2026-08-11).** Account-security actions that record their own detailed audit event — email-change requests, registrations, password changes, admin user create/delete, admin bootstrap — were also getting a second, generic audit row from the request middleware, so one operation showed up twice under two different names (e.g. `auth.email_change.requested` *and* `request_email_change`). The middleware now recognises when a handler has already written its own (richer) audit event for a request and skips the duplicate — while still writing the generic row for every other mutating request as before. The dedup only kicks in once the explicit event has committed successfully, so a failed write still leaves the generic row as a fallback (no lost coverage).
- **The health endpoint now reports the database's actual schema version, and a stale database is called out at boot (2026-08-11).** Two operator-facing diagnostics. (1) `GET /api/health` now includes `schema_version_db` — the migration revision the *connected database* is actually on — alongside the existing `schema_version` (the revision the code expects). Previously only the code's expected version was reported, which was misleading when the database was behind. (2) At startup the backend now compares the live database against the schema the code expects and logs a loud error banner if tables or columns are missing, instead of booting silently and then failing request-by-request on the missing schema (which is exactly how a stale database slipped through before). The banner names what's missing and how to fix it; it warns rather than refusing, so a normal boot is unaffected.
- **Admin feature toggles for scanning and the "Should I buy?" oracle now take effect immediately (2026-08-11).** In Settings → System → Features, flipping **Scanning & QR labels** or the **"Should I buy?" oracle** saved and toasted success, but the UI those flags gate — the Stock Overview scan button, QR-label tools, and the buy/wait/skip badges on stock rows and shopping lists — didn't appear or disappear until you did a full page reload. The toggles now re-check the setting straight away, so the affected UI updates in place. (The other feature flags already behaved this way.)
- **The "reconcile your meals" nudge no longer gets buried on a busy pantry (2026-08-11).** Dora's suggestion feed is capped at 8 cards, sorted by urgency. On a full pantry, 8+ high-urgency "use this soon" cards could fill every slot and silently push out the lower-priority "you've got meals to reconcile" nudge — exactly when a busy kitchen most needs it. The feed now guarantees each *kind* of suggestion at least one slot before any single kind takes a second, so a distinct nudge can't be crowded out entirely by one noisy category. Most-urgent cards still lead, and still take the remaining slots.
- **A bad instance URL is now recoverable from the error screen instead of stranding the app (2026-08-11).** If you pointed the app at an unreachable Dora backend (Settings → About → Change instance URL), it would reload into the full-page "Can't reach Dora's brain" screen whose only button was **Try again** — and the Settings page that would let you fix the URL rendered that same error screen, so a browser or installed-app user was stuck until they manually cleared site data. That screen now also shows a **"Change instance URL"** button whenever a custom backend URL is set, so you can point the app back at a working instance and recover on the spot.
- **Upcoming-timeline dots are now told apart by shape, not just colour (2026-08-11).** On the dashboard's "Upcoming" fortnight grid, each day's category dots are colour-coded — expiry, shopping day, planned meal. But on the default **Pesto** theme (and near-so on Cherry Cola) the "shopping" and "meal" colours are the same green, so a shop day and a meal day looked identical, and the legend didn't help because its swatches were those same two colours. Each category now also carries a distinct **shape** — expiry = circle, shopping = square, meal = diamond — so the three stay distinguishable in every theme (and colour is no longer the only channel, which is the more accessible answer). The legend uses the same shapes, so it teaches the mapping. Cosmetic only.
- **"Build my week" now explains why some days come back empty (2026-08-11).** When you pick more day × meal cells than your cookbook can fill, Dora plans one distinct recipe per meal and simply runs out — so the last days were left blank with no explanation (e.g. 7 days × breakfast/lunch/dinner = 21 meals against an 11-recipe cookbook fills ~8 and leaves 4 days empty). The Review step now shows a short note — "Dora planned 8 of the 21 meals you picked… some days are still empty. Add more recipes, choose fewer days or meals, or tick *Same meals every day* to reuse recipes." — that clears itself once you fill the gap by hand. Purely a heads-up; the plan itself is unchanged.
- **Meal-plan template/set dialogs no longer freeze their text fields while saving (2026-08-11).** The "Save as a template", "Apply recurring", "Save set" and inline template-rename dialogs disabled their own input fields the moment you hit Save — which, if a blur kicked off the save, could yank focus out of a field mid-type. Following the D-019 rule already applied to the settings pages, the in-flight state now shows only on the Save button (its spinner + double-submit guard); the text fields, dropdowns and date pickers stay live. No behaviour change beyond smoother typing.
- **Meal-plan card and drop-target borders now actually render (2026-08-11).** Several borders across the meal-plan cards — the entry chips, the rich day cards, the mobile day-focus view, and the week day cards, including the dashed "add a meal" / drop-target outlines — were coded against a CSS colour variable (`--separator`) that doesn't exist in any theme. An undefined custom property makes the whole `border` declaration invalid, so those borders silently drew as nothing. They now use the real `--border-default` token, so the card outlines and the dashed drag/drop affordances show up as intended in every theme. Cosmetic only — no behaviour change.
- **Password-reset (and verify-email / confirm-email-change) links now open the right screen instead of dumping you on the login page (2026-08-10).** Every link Dora e-mails that points at an in-app screen was built as a plain path — `https://host/reset-password?token=…`. But the app uses hash-based routing (`/#/…`), so that path was served the app shell and then silently resolved to `/` and bounced the (logged-out) recipient to the login screen; the token, sitting in the page's query string ahead of the `#`, was never seen. The links now carry the route in the URL fragment — `https://host/#/reset-password?token=…` — so clicking a reset link lands on the **"Choose a new password"** screen with the token applied, verify-email lands on the confirmation screen, and the alerts-digest "Open alerts" link opens the alerts page. All e-mailed deep links now go through one shared, documented helper so the routing style lives in a single place. (No change needed to any link you already generated — this only affects newly sent e-mails.)
- **Stocktake button now actually animates its fill with the glow (2026-08-10).** The overdue-stocktake button's attention pulse was meant to breathe the button's fill colour in sync with its glow ring, but only the ring ever animated. The Stocktake button is an *outline* button, and Quasar forces `background: transparent !important` on outline buttons — and CSS ignores `!important` inside `@keyframes`, so a fill declared on the button element could never win. The fill now animates on the button's `::before` layer (which Quasar doesn't force-transparent and which paints behind the label), so the whole control breathes as intended. Reduced-motion users get a static fill tint instead of the pulse, as before.
- **Expiry dropdown no longer wraps "Push expiry by 14 days" onto two lines (2026-08-10).** The stock-row expiry shortcut menu had a 180px floor that was a touch too narrow for the longest option, so its label wrapped. The menu is now slightly wider and its option labels never wrap (the menu grows to fit instead), regardless of font or locale.
- **"Build my week" → Reshuffle now actually produces a different plan (2026-08-07).** On the Review step, **Reshuffle** was firing the request but coming back with the identical set of meals every time: for every emphasis except "Surprise me", Dora's recipe ranker was fully deterministic, so the same inputs always yielded the same plan. Reshuffle now applies a small per-request random tiebreak, so hitting it gives you a fresh selection — while still respecting the emphasis: a recipe that uses expiring stock, or a favourite, still outranks the shuffle and stays in, only the near-ties get reshuffled. (Where your cookbook has no more suitable recipes than there are meal slots to fill, there's only one possible plan, so reshuffle can't change it.)
- **Settings inputs no longer lose focus when a save fires, so you can edit several fields in a row (2026-08-07).** Every settings page bound its in-flight `saving` flag to `:disable` on its own inputs, selects and toggles. Combined with blur-triggered autosave, that made editing more than one field in a row impossible: you'd change field A, click into field B, A's blur would start the save, and the flag would disable field B a frame after you landed in it — a disabled control can't hold focus, so the caret was silently dropped and your next keystrokes went nowhere. (The Stock detail view never had this because it only gates *buttons* on its busy flag.) Transient save state no longer disables any focusable field on any settings page — the toast still confirms the save, and Save/Test buttons keep their `:disable` as genuine double-submit protection. Permanent reasons to disable a field (feature turned off for the install, SMTP not configured, email unchanged) are untouched. Concurrency is unaffected: each field PATCHes independently, and a rapid double-toggle is last-write-wins, which is already the intended behaviour. Promoted to a standing rule as **D-019** so it can't creep back in.
- **Signing out from Settings no longer prompts "Discard unsaved changes?" over a light-flashing screen, or strands the app logged-out on the settings page (2026-08-04).** On Settings → Account (and any settings sub-page wired to the unsaved-changes guard), clicking **Sign out** produced a false-positive "Discard unsaved changes?" dialog even when nothing had been edited — because `logoutAsync()` cleared `currentUser` *before* the router push, and the page's draft-vs-user diff (e.g. `usernameDraft` vs. an unchanged username) suddenly saw the user side as empty and reported the drafts as dirty. Hitting **Cancel** on that prompt aborted the navigation, leaving the app on the settings page while already logged-out (the "bad state") and flashing the pre-auth light theme through the modal (default theme applies as soon as `currentUser` clears). Sign-out is an intentional exit with nothing meaningful to save, so it now suppresses the unsaved-changes guard for the logout+navigate step via a new `suppressUnsavedChangesGuard()` helper on the guard composable — no more prompt, no more stranded state.
- **Stock Overview: rows lost their spacing, the counts footer wouldn't stay at the bottom, and the detail pane left a dead gap (2026-08-04).** Four related layout defects, all traced to one root cause. (1) On a large pantry the rows sat flush against each other — the list relied on a `q-gutter-y-sm` container class, which Quasar's virtual scroller ignores, so spacing silently vanished once a pantry crossed the 50-item virtualisation threshold; the row now owns its own gap, so both the small-list and virtualised paths look identical. (2) The sticky counts footer only pinned to the bottom of the screen *while the item-detail pane was open*. (3) Opening that pane left a growing empty gap between the last item row and the footer. (4) The page showed **three** scrollbars at once with the pane open. Causes 2–4 were one problem: the page was running two incompatible scroll models simultaneously — the item list capped its own height (which stopped the page from scrolling) while the footer used a sticky mode that only works when the page *does* scroll, and the detail pane grew without limit, stretching the list column to match it. Stock Overview is now a proper app shell: the toolbar and counts footer are pinned, the list and the detail pane each scroll independently in their own column, and the page itself never scrolls. Result: **two** scrollbars (one per pane, which is what a list-plus-detail view should have), the footer always sits flush with the bottom of the screen, the two panes are always the same height so no gap can appear, and the detail pane's header stays visible while you scroll it. The item list's scrollbar also now sits flush against the edge of its pane instead of floating inset over the rows with dead space beyond it, and its space is reserved so row widths don't jump when filtering makes the list start or stop scrolling. The viewport maths is now derived from the app's real layout instead of hardcoded pixel guesses, so it can't drift when the header or the offline banner changes height.

### Changed
- **Product Search config simplified — URL lives in Features, menu button shows only when it's set (2026-08-07).** Replaces a briefer-lived arrangement (a dedicated Settings → System → Products page + a "Hide menu button" toggle) that overcomplicated things: the Products page is gone, the `product_search_hidden` setting is removed, and the **Product Search URL** row is back on **Settings → System → Features** (shown when the products overlay is on). The rule is now one thing: **set a URL → the "Product Search" main-menu entry appears (opening it in a new tab); leave it blank → the entry is hidden.** This also fixes the real bug behind the change — the menu entry previously stayed visible with no URL and pointed a *normal* user at an admin-only settings page they can't open. There's no longer any not-set-up dead-end in the nav. (The non-nav "Product Search" CTAs — find-&-link, dashboard deals, Dora quick-actions — still fall back to the admin Features page when no URL is set, for an admin to configure it.)

### Added
- **Duplicate a week's meal plan to the next week (2026-08-07).** The meal planner's week header (and the mobile week nav) gains a **Duplicate to next week** button: it copies every meal in the week you're looking at to the same weekday and meal slot seven days later, keeping servings. It asks first, and tells you what it's about to do — including how many meals it will **replace** if next week already has a plan, since duplicating overwrites rather than merges. Meals that would land in the past are skipped. Once it's done you're taken to the week you just created, so you can see it straight away. The mobile day view's **Print this week** button now works too — it was wired to emit an event the page never listened for, so it did nothing.
- **"Build my week" — a real auto-planner that builds your meal plan for you (FU-596, 2026-07-31).** The meal planner's old *"Plan step-by-step"* dialog was just the recipe picker in a modal — you hand-picked every meal and it dropped them all into the first slot ("everything in Breakfast"). It's replaced by **Build my week**: you give Dora light guidance and she proposes a plan you can edit before saving. **Guidance dials:** plan *this week* or *a specific day* ("plan Wednesday, get a shopping list for it, cook, done"); how many meals; an **emphasis** — *Use up my stock* (leans on meals you can cook now + stock that's expiring), *Variety* (spreads cuisines, favours things you haven't had lately), *Favourites*, or *Surprise me*; which **slots** to fill (spread across all, one slot, or a chosen few); and — when money features are on — a **keep-under-budget** toggle. Dora generates a proposal you **review and edit**: remove, swap, or add any meal, change its day/slot/servings, or **reshuffle** for a fresh set; a live "what you'll need" list shows what you'd buy vs. have. Manual control is preserved — *"I'll pick myself"* opens the same review empty so you can build by hand. When you save, a scoped shopping list is one tap away (a single-day plan generates a list for just that day). **The selection + slot placement are server-owned** (R-003) — the ranker uses each recipe's cookability, expiring-ingredient count, cuisine/category, favourite status, how recently you made it, and cost, and honours a recipe's own *time of day* when placing it (falling back to the least-loaded slot), so meals land sensibly instead of all in Breakfast. Reachable from the planner toolbar, the empty-week banner, and (new) a **Build my week** button on the mobile day view. Backend ranker is fixture-unit-tested; the old `SequentialBuilderDialog` is retired.
- **"Support Dora" donation buttons + restored GitHub issue/support links — open-source pivot (FU-608, 2026-07-31).** Now that Dora is free, open-source, and donation-funded (all features free to everyone), a friendly **Support Dora** affordance appears in three places: a gently pulsing pink heart in the **main menu bar**, a floating pulsing button **bottom-left on the sign-in / auth screens** (rhyming with the Dora mascot bubble, which lives bottom-right), and a labelled pill **beside Sign out in Settings**. All three open the same little popover listing the donation channels (Buy Me a Coffee, GitHub Sponsors, and a third to-be-named platform). The buttons use their own dedicated pink token (not a semantic colour), carry an accessible name + tooltip, meet the 44px tap-target floor, and their pulse respects `prefers-reduced-motion`. **Donation links are placeholders** until the owner stands up the accounts (tracked in FU-608). Alongside this, the **GitHub issue / "Report an issue" links** that were stripped when the repo went private are back: the support channel now points at the public `github.com/BenTalese/dashy-dora` issue tracker, which auto-lights the Help "Report an issue" button, the full-page error "Report this" button, and DoraBot's report-issue reply; the Settings → About page regains its **Source code** and **Report a bug** links (plus a **Support Dora** row); and the `SECURITY.md` advisory link + README were corrected to the real `dashy-dora` repo slug. The README was rewritten from its under-construction state into a proper project readme (intro, feature highlights, screenshot/GIF placeholder areas, quickstart, donate/contributing/issues sections, MIT). A `.github/FUNDING.yml` scaffold is in place for the repo's native Sponsor button.
- **`DORA_LOG_LEVEL` env override — tune log verbosity independent of debug mode (FU-591, 2026-07-20).** Operators (and the e2e harness) can now set `DORA_LOG_LEVEL=WARNING` (or any standard level) to override the default log level, which was previously tied to debug mode (DEBUG when debug on, else INFO). This lets a runtime stay in debug/seed *mode* — needed by the Playwright e2e backend, which builds its schema with `create_all()` + seeds — while logging quietly: the per-request DEBUG body-dumps + INFO request lines, each hitting the rotating file handler, were dominating that backend's latency and degrading the long single-worker test run into timeouts. Unset, behaviour is unchanged. Self-host operators get the same knob for quieting a debug instance's logs without leaving debug mode.
- **Register a real barcode against one of your products — FU-373 (2026-07-15).** My Products now lets you attach an EAN/UPC to a saved product from the per-product "⋮" menu → **Register barcode…**. This is the correct home for a real-world barcode: a scanned EAN identifies a *product* (a sellable SKU), not a personal pantry slot, so scanning that code later resolves product → its linked stock item. The dialog is text-entry (type or paste the code), mirroring the existing "Add barcode" dialog on a stock item's detail page; the server enforces one barcode per product, so re-registering surfaces a friendly "already registered" message instead of a silent failure. The action only appears when the operator has enabled scanning (the install-wide `scanning_enabled` flag, off by default), consistent with the rest of the barcode/QR surface. This closes the last deferred build slice of the P6-02 barcode proposal; the scan-unknown flow is deliberately left as-is (owner scope call — the one-tap "scan an unknown code → add a new pantry item" path stays friction-free rather than forking into a link-to-product prompt), and the "Scan tab under Data" placement question was already resolved earlier (that tab was removed; scanning lives on the surfaces that need it).
- **Offline-queue composable test coverage — FU-520 (2026-07-15).** `useOfflineQueue` (the F3 offline-tolerant mutation queue that lets grocery-run actions — ticking lines, bumping stock levels, marking opened/restocked — survive a dropped connection and replay on reconnect) now has behavioural unit coverage: 13 Vitest cases pinning the swallow-network-only-else-rethrow wrapper, oldest-first drain that stops on the first network error but shunts non-network rejections to a conflict pile, the reconnect auto-drain edge, conflict discard/retry, and per-user localStorage isolation. This drains the last opportunistic component/composable surface on FU-520's item 3; the frontend Vitest suite is now 385 tests / 30 files. No product code changed.
- **Production WSGI server (gunicorn) for the self-host container — FU-397 (2026-07-14).** The API no longer runs behind Flask's development server in production — a real WSGI server (gunicorn) now fronts it, which is table-stakes for a credible self-host release (the dev server is single-threaded, unhardened, and explicitly "not for production"). The container entrypoint (`startup.sh`) picks the server from the environment: `DORA_API_SERVER=auto` (default) runs gunicorn when `DORA_ENV=production` and the Flask dev server otherwise, and you can force either with `gunicorn`/`flask`. gunicorn is configured in a new `gunicorn.conf.py` — bind mirrors `DORA_API_HOST`/`DORA_API_PORT` (nginx's `:5170` upstream is unchanged), with a **single threaded worker by default** (`gthread`, `DORA_WEB_THREADS=4`). Single-worker is deliberate: the app runs an in-process scheduler (alerts digest/push, audit-log prune, demo reset, snooze cleanup) that must fire exactly once, so concurrency comes from threads rather than processes; scaling past one worker (`DORA_WEB_CONCURRENCY>1`) logs a loud boot warning because it would duplicate those jobs, and true horizontal scale is the worker-split work parked in `OPTIONAL_SAAS_AND_MANAGED_DEPLOYMENT.md`. Internally, `startup.py` was split so the app wiring (CORS, migrations, routers, scheduler) lives in a reusable `bootstrap()` that a new `dora_api/wsgi.py` entry point (`gunicorn dora_api.wsgi:app`) calls at import — the dev path (`app.run()`), the desktop bundle (its own `make_server`), and the test suite are all unchanged. gunicorn logs to stdout/stderr so `docker logs` captures them.
- **Action-first Stock Overview scan mode — FU-378 (2026-07-14).** The Stock Overview **Scan** button (shown only when the operator has enabled scanning) opens the camera in an action-first mode. Inside the overlay a always-visible **"Action: …"** chip shows what each scan does, with a one-line caption, and tapping it switches the action — so you can see the selected action and change it *without leaving the camera*. The default action is **Open stock item**: scan a code and jump straight to that item's detail page (the scanner then closes). Switch to **Set to <level>** (one entry per configured stock level) and the camera *stays open*, setting every item you scan to that level with a per-item "<item> → <level>" confirmation banner and chime — so you can walk the pantry marking things well-stocked / low / out in one continuous pass, switching the target level on the fly. This is the unified scanner the design called for — it doubles as a fast stocktake ("scan each shelf, set its level") without a second scanning surface. A scanned code that isn't a known pantry item (an unlinked product, or an unknown barcode) is reported and skipped so the loop keeps going, rather than derailing into the add-item flow. Level changes go through the same path as the in-row level swap, so they inherit optimistic update, offline queueing, and any auto-add-to-list behaviour. Still entirely gated behind the install-wide `scanning_enabled` flag (off by default).
- **Support / "Report an issue" channel — FU-370 (2026-07-14).** Dora now has a first-class, opt-in way for users to reach whoever runs the install. When the operator configures a channel, a **Report an issue** button appears in the Help page header, the full-page error screen gains a **Report this** button (pre-filled with the screen, path, correlation id, and error message), and DoraBot's "I found a bug" reply offers a real report link — all opening the operator's chosen destination (a public issues repo, a hosted form, or a `mailto:` address), pre-filling a subject/body where the destination supports it. The Help "About" copy was also rewritten from the old "pass it to whoever runs this Dora instance" line to an honest one-person/side-project message that sets expectations up front. **Ships off by default:** with no channel configured nothing new renders, and the About copy falls back gracefully. The target is a single hardcoded switch (`support_channel.py`, with `DORA_SUPPORT_URL` / `DORA_SUPPORT_EMAIL` env overrides) rather than an admin setting — a deliberate single-maintainer simplification. *(Standing up the actual channel is a follow-up, FU-557.)*
- **Demo / sellable-showcase mode — FU-392 (2026-07-13).** Booting the API with `DORA_DEMO_MODE=true` turns any install into a self-resetting product demo for sales conversations. On boot it wipes and re-seeds a *curated* showcase dataset (`seed_showcase.py`) — a believable single-household pantry with clean product/price data, a coherent week's meal plan, and an active + finished shopping list, deliberately free of the developer test artifacts the dev seed carries (no "chatty history test" item, no real personal email, no backdated overdue-stocktake noise). Log in as `demo` / `demo`. A background job re-seeds on a fixed interval (`DORA_DEMO_RESET_MINUTES`, default 60; `0` disables the reset for a static demo) so anyone poking at the demo starts from a clean, coherent state. The SPA renders a persistent floating "Demo mode — this is sample data that resets periodically" pill (self-gated on a new pre-auth `demo_mode` capability flag) so a prospect always knows it's a sandbox. This is the *shared* demo cut — one live install, one dataset; true per-visitor isolation (each prospect gets a private sandbox) needs multi-tenancy and is deferred to Phase 4 (FU-555). All app-code; no new dependencies. The flag is env/operator-only (never an in-app admin setting) and the demo install is disposable by design, so it deliberately bypasses the normal production seed-guard.
- **Dora is now an installable PWA — FU-336 (2026-07-13).** The complete PWA config (Workbox service worker, web app manifest with app shortcuts, offline fallback, runtime caching) had been fully wired for weeks but never actually shipped, because `npm run build` ran Quasar's plain SPA mode. The build now runs in PWA mode (`quasar build -m pwa`), so the service worker (`sw.js` — NetworkFirst on `/api/`, CacheFirst on product/stock images, `index.html`/offline navigateFallback), `manifest.json`, `offline.html`, and Web-Push service worker now land in the shipped frontend. Result: install-to-home-screen on Chrome/Android + desktop browsers, an offline shell, and the already-built Web Push path is now reachable end-to-end — with zero new application code. The build still emits to `dist/spa` (the output path every consumer — nginx, the Flask SPA server, the PyInstaller desktop bundle, the packaging scripts — already uses), so nothing downstream had to change. nginx now serves the service worker with `Cache-Control: no-cache` so deployments roll over cleanly instead of pinning clients to a stale worker. *(The iOS add-to-home-screen icon + Safari pinned-tab placeholder-logo gap was closed by FU-552, 2026-07-15.)*
- **Ingestion API: `POST /api/ingest/link-status` read-side lookup — C-10.5 / FU-422 (2026-07-12).** An ingestion source (e.g. the standalone companion) can now ask Dora, in a single batched call, which of a set of products it's about to surface in *its own* search UI are already held by Dora, and which of those are already linked to a stock item. Request shape mirrors the write side — `(store external name, merchant_stockcode)` first, `(store, name)` fallback — so a caller that already builds a `/api/ingest` payload can reuse the same identifiers. Response is per-item: `{ ref, product_id, linked_stock_item_id, linked_stock_item_name, reason? }`, where `reason` is `store_not_mapped` or `product_not_found` when nothing was resolved. Bearer-auth via the existing `IngestionSource` key; source-agnostic response shape (invisibility rule). Motivated by the original-spec ask "when searching for products, mark ones already linked to a stock item" — since Dora itself has no in-app product-search UI (search moved to the companion), the rule now lives at the ingestion boundary as a decorate-your-own-results hook. Capped at 200 items per call to keep it from turning into an accidental catalogue dump. **Companion consumer landed the same day** in `dora-companion` — `companion_common.dora_ingest.check_link_status` calls this endpoint after each scrape, and `ProductSearchCard` renders a "Linked in Dora: <stock item>" / "Already in Dora (not linked)" badge per card.

### Fixed
- **"Skip for now" on a past meal no longer silently adds meals back to your pantry — FU-594 (2026-07-31).** When reconciling past-day meals ("did you cook this?"), tapping **Skip for now** — the passive "ask me again later" option — was quietly treated like **Didn't cook**: it reversed the auto-drain the nightly sweep had already applied and cleared the "consumed" stamp. So on an install with auto-drain on, skipping a meal you'd been assumed to eat *increased* the recipe's available-meals count (e.g. a planned-4 meal moved the pool from 10 back to 14) and left the pantry over-stating what you have. **Skip** is now genuinely neutral — it re-queues the entry for next time and changes nothing about the pool or the consumed stamp, matching what the button says and what the module always documented. A later **Cooked** on a skipped entry is a correct no-op (no second drain) and a later **Didn't cook** reverses the drain exactly once. Pinned by three new backend contract tests. Found during the verify campaign (Batch 7, meal-plan reconcile).
- **"Removed from N lists" toast no longer over-counts — FU-573 (2026-07-31).** The "remove from every list" action (the buy-verdict card's remove-from-list, and the multi-list popover's "remove from all") fans out over every open shopping list — but removing an item that isn't on a given list is a deliberate no-op success, and every such response was being counted as a removal. So an item on **1** list produced "Removed from **3** lists." The server endpoint now reports whether it actually removed a line, and the toast counts only real removals (and says "It was already off your lists." if nothing matched). Pinned by new backend contract tests.
- **"Log a price" Back arrow now returns to a clean picker — FU-585 (2026-07-31).** On the dashboard's "Log a price" sheet, tapping **Back** from the price-entry form dropped you back onto the item picker but left your previous search still in the box. It now clears the search too, so Back matches closing the sheet — both return you to the clean shortlist (frequently-added / low / out first).
- **Dashboard "kitchen health" freshness & stocktake links now actually filter the pantry — FU-583 (2026-07-26).** The Dora Score card's **Freshness** action ("Expiring items") linked to `/stock?expiring=1` and its **Stocktake** action ("Do a stocktake") to `/stock?stocktake=1`, but the Stock page ignored both query params — so you landed on the full, unfiltered pantry instead of the items the score was pointing you at. Both now take effect: `?expiring=1` narrows to items expiring within 7 days (or already expired) via a new **Expiring soon** filter chip on the Stock page, and `?stocktake=1` opens the existing **Needs check** (stocktake-queue) filter. The new chip is also usable directly — toggle it any time to see just what's about to go off. Found during the verify campaign (Batch 10, Dora Score).
- **"Product Search" links no longer dead-end on the 404 page, and the nav entry now shows even before it's set up — FU-581 (2026-07-26).** FU-186 removed the in-app `/product-search` route (Product Search is now an external companion opened via an admin-set URL), but several in-app entry points still pushed to that dead route and landed users on the 404: the stock-item "Find & link a product" CTA, My Products' empty-state "Open Product Search" button and its orphan-stock-item "search" action, the dashboard's "Hunt for deals →" empty-state link, and Dora's "Find cheaper alternatives" / "Hunt for fresh deals" quick-actions. All of these now route through one shared resolver (`openProductSearch`): a configured URL opens the external companion in a new tab, and when no URL is set they route to Settings → System → Features where it's configured — so the setup path is always reachable instead of a dead end. The stale `?q=` / `?stock_item_id=` seeding (which the removed in-app page used to consume for auto-linking) is dropped; products found in the companion are linked back from My Products' per-product "Link to stock item…" dialog. **Behaviour change (owner call):** the **Product Search** nav entry is now shown whenever the products overlay is on — previously it was hidden until an admin set the URL — so the surface is discoverable and signals it can be set up; when unset it links to the Features page (this supersedes the earlier R-029 hide-when-unset behaviour for this one entry). Found during the verify campaign (Batch 3, Products tab).
- **Dashboard money & deal cards now populate on a cold load without a second navigation — FU-586 (2026-07-25).** The dashboard's money cards (budget, savings, spend-by-store, pantry value, budget-defense swaps) and the price-drops deal card are gated on the install-wide feature flags, which the app reads once per document from `/api/health`. On a *cold* load — a hard browser reload or a PWA cold start — that probe usually hasn't resolved by the time the dashboard mounts, so those card loaders saw the gate as still-off, skipped their fetch, and nothing re-ran them when the flags landed a moment later. The result: on a hard reload the money/deal card bodies stayed blank until you navigated away and back. The dashboard now re-fires exactly those gated loaders when a gate flips on, so the cards fill in as soon as the flags resolve. Warm navigations (the gate is already on at mount) are unaffected — no extra requests. Found during the verify campaign (Batch 10, codifying FU-300/FU-297).
- **Cart "add to list" now targets a planning list by default, and its tooltip is accurate — FU-603 (2026-07-24).** The stock / My-Products cart button tooltip said "Add to a **draft** list", but the picker actually targets any active (non-done) list — including a shop you're mid-way through. Two fixes: (1) the tooltips now say "a list" (accurate), and (2) when the target is ambiguous, the picker defaults to a planning **draft** rather than the first active list, so a pantry cart-add no longer drops by default into an in-progress shop. An explicit preset or the remembered per-tab target still take precedence.
- **Per-user "money features off" now also hides the Alerts price-watch panel — FU-604 (2026-07-24).** Turning money features off for your own account (Settings) hid the trim-to-budget banner but left the Alerts hub's armed-price-watch panel visible — it only checked the install-wide money flag, not the per-user opt-out. It now gates on both layers via the shared `useMoneyEnabled` composable, consistent with every other money surface: opting out of money features hides all money UI for that account.
- **The Alerts page no longer shows a stale feed — FU-597 (2026-07-24).** The Alerts page only refetched on open when the shared alert store was empty; once the header bell (which refreshes on mount and polls every 60s) had populated it, navigating to Alerts rendered whatever the store last held. So if you resolved something elsewhere — planned next week's meals, restocked an item, finished a shop — and then opened Alerts, it could still show the alert you'd just cleared (and a matching stale count), until you hit Refresh. Alerts are derived live server-side from constantly-changing state, so the page now always refetches on open (matching the bell), with an in-flight guard so it doesn't duplicate a refresh already running. Found during the verify campaign (Batch 11).
- **Settings save-failure toasts are no longer grammatically broken — FU-601 (2026-07-24).** When a settings save failed (e.g. a transient network blip), the error toast reused the *success* sentence as a noun, producing strings like "Could not save dora helper shown.." or "Could not save ai mode turned on..". The error path now shows a single fixed message — "Could not save your change." — with the specific failure detail still in the toast caption. The bug was copy-pasted across all six settings pages (Assistant, Preferences, Nutrition, Money, Notifications, Voice), so the fix also extracts the shared save-toast helper into one `useSettingsSave()` composable (R-003), removing the six duplicated copies. No behavioural change on the success path. Found during the verify campaign (Batch 1).
- **A past meal you didn't cook no longer freezes the whole week's planner — FU-595 (2026-07-24).** If a week contained a past-dated entry that was never marked consumed — reachable two ordinary ways: auto-drain turned off, or answering "Didn't cook" during reconcile — then *any* subsequent add/edit to that week failed with "Meal plan entries cannot be scheduled in the past.", and the error blanked the entire planner screen ("Something went wrong on this screen."). Two defects, both fixed: (1) the server now preserves *all* past entries as immutable history when the forward plan is replaced — previously only *consumed* past entries were kept, so a past-unconsumed one was dropped by the replace, and the client's resend of it tripped the past-date guard; and the client now sends only forward-looking, unconsumed entries (past days are read-only, so they're never resent). (2) A failed plan mutation now surfaces as a toast instead of escaping to the page error boundary — so no plan write can blank the screen. The "can't schedule a *new* meal in the past" guard is unchanged. Found during the verify campaign (Batch 7, meal plans).
- **Price History: picking products from the list now updates the chart — FU-605 (2026-07-24).** On the **Price history** compare page, ticking a product in the left-hand list added it to the "Selected" chips but the chart and the per-product comparison cards never changed — the price data was never fetched for the newly-picked product. The only way to see a chart was to arrive via a deep link ("View price history" from My Products, or the Alerts-hub price-watch panel). Cause: selecting/deselecting mutated the selection list in place, which the data-fetch watcher didn't detect (it only watched for the list being *replaced*, which is what the deep-link path happens to do). Selecting now replaces the list, so the chart and comparison cards refresh immediately as you add or remove products (up to five). Found during the verify campaign (Batch 14, My Products / Price History).
- **Currency & locale preview now reflects the saved setting on page load — FU-600 (2026-07-23).** Settings → Admin → System → **Currency & locale** shows a live "$12.50 · $1,234.56"-style preview of how money will render. On a fresh load it showed the Australian default format regardless of the currency/locale you'd actually saved — it only corrected itself once you edited and re-saved on that page. Cause: the preview reads the shared money-format policy, which is loaded lazily the first time any money surface asks for it; the settings page never asked, and with money features off (the default) nothing else did either, so the preview fell back to the AUD/en-AU default. The page now refreshes the money policy when it opens, so the preview is correct on first paint. Verified live: with the install set to EUR/de-DE the preview reads "12,50 € · 1.234,56 €", and resetting to AUD/en-AU reads "$12.50 · $1,234.56". Found during the verify campaign (Batch 1).
- **Dora no longer name-drops specific supermarkets, and dead help copy for a removed page is gone (2026-07-23).** Dora's contextual page-help still carried a canned line for the retired in-app `/product-search` page ("Hunt for products across Coles, Woolies, IGA, Aldi…") — dead code (that route was removed in FU-186, so the line could never appear) that also hardcoded specific AU retailer brands. Removed. Dora's Help-page tool descriptions already describe searching "across the configured stores" generically. Found during the verify campaign (Batch 1, Currency & locale item 8).
- **Alerts history no longer shows "out of_stock" (2026-07-22).** The History list at the bottom of the Alerts page labelled each entry by munging the internal key, and it only replaced the *first* underscore — so an out-of-stock alert you'd dismissed read **"out of_stock"**, while the Manage panel a few rows up correctly said "out of stock". History now reads its label from the same shared list of alert kinds every other surface uses, so the two can't drift again; an unrecognised kind (one retired since it was stored) still reads as words rather than a raw key. Pinned by three unit tests.
- **Printing a meal plan no longer titles the page "None" (2026-07-22).** The planner deliberately creates *nameless* week-plans, so every print from it came out with the literal word **None** as both the browser tab title and the heading at the top of the sheet. Unnamed plans now title by the week they start — "Week of 2026-07-20" — while a plan you *did* name still shows its name. Pinned by a new backend test that creates a nameless plan explicitly (the seeded plans all carry names, so the existing print-view test could never have caught this).
- **Finishing a reconcile pass no longer dumps you on a "page wandered off" 404 (2026-07-22).** After walking your past-day meals on **Meal plans → Reconcile**, the recap card's **Done** button sent the app to `/dashboard` — a route that doesn't exist (the dashboard lives at `/`), so the very last tap of the flow landed on the 404 page instead of home. Every other link on that page was already correct; this was the single stale path in the SPA. Found by walking the reconcile runner end-to-end during the verify campaign (Batch 7, Meal plans).
- **Making a new version of a recipe that has ingredients no longer fails — FU-590 (2026-07-20).** "New version" (from a recipe's kebab menu) crashed with a 500 for **any recipe that had ingredients** — i.e. essentially every real recipe; only an empty stub could be versioned. Two faults compounded: (1) the copied ingredient rows were staged in the database session before the new recipe existed to own them, and reading the source recipe's image mid-build triggered a premature save that hit a "recipe is required" constraint; (2) the copy read each ingredient's linked pantry item off a relationship that isn't loaded on that query, so a **linked ingredient came out unlinked** and — with its original text also not copied — tripped the "an ingredient needs either a pantry link or a text label" rule, failing the save outright. Fixed by suppressing the premature save during the copy and by cloning each ingredient from its loaded link + original text (and carrying the "optional" flag). New `test_new_recipe_version_numbering.py` pins versioning a recipe with linked, unlinked, and optional ingredients end-to-end. Found while codifying the recipe-versions verify checks (verify-campaign Batch 5).
- **Recipe version numbering no longer skips "v2" — FU-589 (2026-07-20).** The first "New version" of a recipe was named "(v1)", then the next jumped to "(v3)" — the sequence skipped v2 because the numbering counted the group's members before the original recipe had been recorded as one of them (so the first copy counted 0 siblings, the second counted 1). It now flushes that link first, so versions read "(v2)", "(v3)", "(v4)"… consistently, and — as before — a version made off a copy still takes the next number in the group (versions are equal peers, numbered by total count, not by parentage). Pinned in `test_new_recipe_version_numbering.py`.
- **The bulk-linker page no longer says "Used in 0 recipes" for every ingredient — FU-588 (2026-07-20).** Settings → Admin → Data → **Unlinked ingredients** groups every unlinked recipe ingredient and shows how many recipes use each one. The grouping code read the recipe foreign key off the un-prefixed attribute name (`row.recipe_id`), but the ORM binds that FK to the underscore-prefixed `_recipe_id` property — so the read silently returned nothing and **every group reported a count of 0 with an empty recipe list** (the "Used in N recipes" label always said 0, and the group's recipe set was empty). The one-tap **Link** still worked (it matches by ingredient text, not by the count), so the bug was cosmetic-but-misleading rather than blocking. Fixed by reading the mapped `_recipe_id` property (the same R-032 underscore-FK discipline already applied to `_stock_item_id` in the same file). The bug had a passing unit test that masked it — the stub rows were hand-built with the wrong attribute name; the stub now mirrors the real mapping, and a new endpoint-level `test_unlinked_ingredients_bulk_link.py` pins the real count/recipe-ids, the cross-recipe bulk-link, cookability re-derive, only-matching-rows, and the not-found / empty-key error paths. Found while codifying the bulk-linker verify checks (verify-campaign Batch 4).
- **"Generate shopping list from this week" (and Draft-my-shop's meal-plan source) now actually adds your recipe ingredients — FU-587 (2026-07-19).** The recipe and meal-plan sources of the auto-generator read each ingredient's linked stock item off a relationship that isn't loaded on that query (`lazy="noload"`), so it always read as absent: **every** linked recipe ingredient was silently skipped (nothing added to the list) **and** simultaneously mis-reported as "unlinked" in the FU-505 "Add these manually" warning — so the one feature that turns a meal plan into a shop added none of its recipe items while spamming the manual-add dialog with ingredients that *were* linked. Fixed by reading the loaded foreign-key column instead (the same R-032 noload discipline used elsewhere), in both the per-recipe and meal-plan-week collectors. New `test_auto_generate_unlinked.py` pins it: a recipe's linked out-of-stock ingredient becomes a line while only its genuinely-unlinked (free-text) ingredients appear in the warning, a fully-linked recipe produces no warning, and multiple free-text ingredients are each reported against their recipe. Found while codifying the FU-505 unlinked-ingredient warning (verify-campaign Batch 7).
- **Updating a product's price no longer breaks after the first-ever price change (2026-07-19).** `PATCH /api/products/<id>` archives the outgoing offer into the product's price history, but the archived row was inserted without an id being assigned — so the *second* price update anywhere in an install's lifetime collided with the first on the primary key and returned a 500. The manual price-update path now persists the archived offer the same way the ingestion path and the seed always did. Found by the new price-drops report regression tests (verify-campaign Batch 10), which now pin ranking (biggest %-drop first, dollar amount as tie-break), the inactive-product exclusion, and the `limit` clamp (1–20, default 5) alongside the fix.
- **A dead recipe deep-link no longer strands a phantom "Ingredients of: this recipe" chip on Stock Overview (2026-07-18).** Landing on `/stock?recipe=<id>` with an id that doesn't resolve (a deleted recipe, or a mangled link) correctly left the list unfiltered, but the filter chip still rendered with its hydration-fallback label "Ingredients of: this recipe" — a chip naming no recipe, whose × did nothing observable. The chip now distinguishes "recipes still loading" (fallback label, as before) from "loaded and the id doesn't resolve" (no chip at all), via a reactive hydration flag on the recipe store. Found while codifying the FU-109 verify checks. Also fixed in passing: the "No items match the current filters" empty-state **Clear** button on Stock Overview called the raw filter reset instead of the page's clear-all wrapper, so it left `?recipe=` in the URL — a refresh would silently reinstate the filter the user had just cleared.
- **`quasar build` (and the e2e pipeline) un-broken: bulk-waste spec type errors fixed — FU-579 half (2026-07-18).** The 12 `noUncheckedIndexedAccess` errors in `web_app/e2e/bulk-waste.spec.ts` didn't just feed the dev-server overlay — they hard-fail `npx quasar build` (exit 2, no `dist/spa`), which broke `npm run test:e2e` from a clean tree. The spec's items-by-name lookup now returns a throwing accessor, so every index access is non-undefined; `vue-tsc --noEmit` is clean again. (The `src-pwa` half of FU-579 — workbox types in the dev-watch checker — remains open.)
- **Creating a stock item with an over-long or whitespace-only name is now handled cleanly, and names are trimmed — Codex review (2026-07-17).** Three related fixes to the stock-item create path: (1) a name of 256+ characters was accepted by the request model (it only enforced a *minimum* length) and would have hit the `String(255)` column — silently accepted on SQLite but a **500 on Postgres**; it now returns a clean validation error, matching the edit action which already capped at 255 (same class as the FU-520 `alert_key` truncation fix). (2) Names are **trimmed** at the request boundary, so a whitespace-only name (`"   "`) is rejected instead of stored, and `"  Milk  "` can no longer masquerade as distinct from an existing `"Milk"` (the duplicate check was already case-insensitive but wasn't trimming). Create and edit normalise identically. (3) The **Add-a-stock-item dialog** trims the name before submit and rejects a whitespace-only entry in its own rule.
- **The "Add a stock item" dialog now lets you set expiry and mark an item essential at add time — Codex review (2026-07-17).** Help and the API both said you could set location, expiry, or the "essential" flag while adding an item, but the dialog only exposed name, level, and location. It now includes an **Expiry (optional)** date field (with a calendar picker) and an **Essential** toggle — matching the API and what Help promises, so you no longer have to add the item then immediately edit it to set those.
- **Buy-verdict badges and cards now refresh immediately after you act — FU-572 (2026-07-17).** Two staleness gaps in the "Should I buy?" oracle's client cache: tapping a one-tap action (or changing the stock level) on the stock-item detail page left the verdict card showing the old answer until you navigated away and back, and adding/removing an item via the row cart button didn't refresh its verdict badge at all for up to five minutes. Cache invalidation now refetches live entries immediately, and every shared add-to-list / remove-from-list / restock seam invalidates the affected item's verdict — so the card's button flips to the fresh action in place (e.g. "Remove from list" → "Already stocked" right after the removal). The confirmation toast also now uses your actual level name ("Marked as Stocked.") instead of the retired hardcoded "Well-Stocked" wording.
- **Spreadsheet Import and Backup-restore uploads work again — FU-571 (2026-07-17).** Since the CSRF double-submit defence landed (FU-197), every chunked upload in the browser was rejected with a 403: the upload composable (and a handful of other call sites) used raw `fetch` instead of the shared axios client, so the interceptor that attaches `X-CSRF-Token` never ran — picking a file on Settings → Admin → Data → **Import** or **Backup & restore** died immediately. A new shared `csrfHeader()` helper is now spread into every raw-fetch mutating call: the chunked-upload start/chunk/finish/abort calls, import inspect/commit, backup create/inspect/restore, the two image/backup settings saves on the Backup page, client-side error-log shipping (`/client-logs`), and text-to-speech (`/tts`). Verified end-to-end: a real chunked upload + import inspect both succeed, and a request without the header is still rejected (the defence itself is untouched).
- **"A passphrase works well" password hint restored on all auth surfaces — FU-568 (2026-07-17).** The FU-442 hint copy ("At least 8 characters — a passphrase works well.") was dropped from the four password-entry surfaces during the C-19 auth-shell rebuild, leaving only the bare validator message. Restored as a proper field hint on Login (register mode), Reset password, first-run admin setup, and Account settings → change password. Server-side policy was never affected.
- **Windows console no longer prints a logging traceback on every request — FU-569 (2026-07-17).** On a Windows console using the legacy cp1252 code page, the `→ GET /api/…` request-log glyphs (and any non-ASCII user content in a log line) crashed the logging stream, printing a "--- Logging error ---" traceback to stderr on **every request** and drowning real errors on exactly the platform the desktop bundle targets. Logger setup now re-encodes the console stream to UTF-8 (with replacement, so logging can never crash on output again); the log file was already UTF-8.
- **iOS home-screen + Safari pinned-tab icons now show Dora's logo, not a placeholder — FU-552 (2026-07-15).** When the app went full-PWA (FU-336), Quasar's `injectPwaMetaTags` started emitting `<link>`/`<meta>` tags pointing at `icons/apple-icon-{120,152,167,180}.png`, `icons/ms-icon-144x144.png`, and `icons/safari-pinned-tab.svg` for the iOS add-to-home-screen icon, the Windows tile, and the Safari pinned-tab. Those files were Quasar's default blue-gear placeholder (untracked, generated on 2026-06-22) and had since been deleted — so on iOS/Safari the home-screen icon showed the wrong logo, and after the cleanup those exact paths 404'd. All six are now real Dora-branded assets: the four `apple-icon` sizes and the MS tile are high-quality downscales of the committed `apple-touch-icon.png` (the already-approved solid-background treatment iOS needs — no transparency, so no black corners), and `safari-pinned-tab.svg` is a hand-authored monochrome "D/D" vector (Safari recolours it to the theme gold via the `mask-icon` `color`). Android/Chrome/favicon were always fine and are untouched. The generated `index.html` now resolves every injected icon path to a real committed file (verified). *(Note: the Safari mask-icon is a legacy surface — Safari 15+ ignores it and uses the regular icons — so it's kept branded mainly to avoid the 404; a pixel-perfect pinned-tab spot-check is queued in DORA_VERIFY.)*
- **Foreign-key delete rules now behave as intended in production — FU-565 (2026-07-15).** Six foreign keys were meant to have an on-delete rule (the model declared them) but production had none, on tables that pre-dated the convention. The effect on a real deployment: deleting a stock level, group, or location that a stock item still referenced would error instead of quietly clearing the link; a product's offers and historic offers wouldn't be cleaned up when the product was deleted; and a store still referenced by a product wasn't protected from deletion. A migration recreates all six constraints with the correct rule (`SET NULL` for the stock-item groupings, `CASCADE` for product offers, `RESTRICT` for a product's store), on both SQLite and Postgres. The migration test now also compares foreign-key delete rules between the two schema-build paths, so this class of drift is caught automatically from here on. This completes the data-model consistency sweep (indexes, nullability, and now delete rules all reconciled).
- **Product nullability now matches between dev and production — FU-564 (2026-07-15).** Three `Product` columns disagreed on nullability between the ORM model (what dev + tests build) and the migrated production schema: `is_active` and `is_available` were meant to be required but production allowed NULLs, and `merchant_stockcode` was meant to be optional but production still required it (so an insert a dev database accepts could be rejected in production). A migration reconciles all three in production to the model's intent (backfilling any missing active/available flags to true first), and the migration test now enforces column nullability so this can't silently drift again. The one remaining intentional difference — `User.username`, which the app keeps required-and-unique while the production column stays nullable for historical migration-safety reasons — is now documented in the model and explicitly allowlisted. No user-visible behaviour change.
- **Foreign-key columns are now indexed, and the dev/test schema finally matches production — FU-563 (2026-07-15).** The ORM model (`table_mappings.py`) had drifted badly from the migrations: it declared **1** secondary index while the migration chain built **32**, so local dev and the entire test suite ran against a near-unindexed schema that didn't match a real deployment. Worse, **43 foreign-key columns had no covering index in production** — and neither SQLite nor Postgres auto-indexes FK columns, so deleting a parent row (a recipe, a shopping list, a stock item) full-scanned the child table, and every join on those keys was unindexed. This is invisible at single-household scale but degrades as pantry/price history grows. The model now declares every index the schema has (the 32 pre-existing ones, mirrored so they build identically in dev, plus a covering index on all 43 FK columns), and a single additive, forward-only migration adds the FK indexes to existing installs. A migration test now compares columns, nullability, and index/unique constraints between the two schema-build paths, so this drift can't silently return. No behaviour or data change — purely faster deletes and joins, and honest local testing.
- **Settings file-drop is now keyboard- and screen-reader-accessible — FU-545 (2026-07-15).** The drop-zone used by Settings → Admin → **Data → Import** and **Backup & restore** was a `<div role="button">` with a hidden native file input nested inside it — an interactive control inside another interactive control (`nested-interactive`, flagged `serious` by axe), which is a classic screen-reader/keyboard trap. It's rebuilt to the standard accessible pattern: a plain `<label>` wrapping a single visually-hidden (but still focusable) file input. Behaviour is unchanged for mouse users — click anywhere to open the picker, drag-and-drop still works, the Remove button still clears without re-opening the picker — but keyboard users now get a proper focus ring and can open the picker with Enter/Space via native browser behaviour, and the nesting violation is gone. The whole component's accessibility test now scans clean in its idle, filled, and disabled states (previously only disabled was asserted).
- **Two SQLite-vs-Postgres divergence bugs that only surfaced on a Postgres deployment — FU-520 (2026-07-14).** Postgres is the standard datastore target (SQLite is still supported for lightweight self-host), but part of the code base had only ever run against SQLite, which silently tolerates two things Postgres rejects. First, three hand-rolled `text(...)` SQL sites bound UUID parameters in SQLite's storage form (a 16-byte BLOB): on Postgres, where `UUIDType` is a native `uuid` column, that raised `operator does not exist: uuid = bytea` — a 500 on the affected paths (recipe-pool ranking bump in `recipes/pool.py`, and meal-plan reconciliation in `meal_plans/reconcile.py`). The binds are now dialect-aware (`bytes` on SQLite, canonical string on Postgres), so both engines match rows correctly. Second, marking/snoozing/dismissing an alert with an absurdly long alert id (250+ chars) wrote past the `alert_key` column's 255-char limit: SQLite accepts the over-length write, but Postgres raised `StringDataRightTruncation` (a 500). Since an over-length key can't name any real alert, the alert-interaction endpoints now treat it as an idempotent no-op (the same as acting on an already-gone alert) instead of erroring. All three were caught by running the full backend test suite against a real Postgres database for the first time; no schema or API-shape change.
- **Unlinked recipe ingredients now show their text instead of a blank picker (2026-07-13).** After importing a recipe (or hand-entering a free-text ingredient), any ingredient that didn't fuzzy-match an existing stock item is stored as free text (`raw_text`, no pantry link) — and the recipe editor is built to show that text (a "Free-text ingredient" label + the quoted original under the picker). But the editor's load step silently dropped `raw_text` when hydrating an existing recipe, so on the very next page load every unlinked row collapsed to an empty "Stock item" dropdown with only a quantity and unit — the user had no way to tell what "1 · tbsp" or "0.3333 · cup" was supposed to be. This was especially bad right after a paste import, where most rows start unlinked (e.g. the *Thai massaman beef curry* import showed 19 anonymous rows). `raw_text` now carries through load, so each unlinked row shows its original text (e.g. "1/3 cup (100g) massaman curry paste") and can be linked at leisure.
- **Pasting a taste.com.au recipe no longer imports video-carousel spam and price-widget junk (2026-07-13).** The paste importer's text parser (`parse_recipe_from_text`) grabbed two extra pieces of taste.com.au / Coles page chrome: the Coles price widget (`Estimate based on regular price…`, `Fulfilled by coles-logo`) leaked in as ingredients, and — worse on recipes with an embedded "how-to" video — the method block swallowed the video carousel (a `01:01` timecode, up to a dozen `Next video thumbnail` lines, the video title/description, and a `more` link) plus the `Show ingredient quantity` widget label and the per-step photo captions (`<recipe>-Step N`) as bogus steps. A user pasting the *Thai massaman beef curry* recipe got 3 real steps buried under 16 junk ones. The parser now filters the price-widget lines from ingredients, drops the widget label + photo captions from steps, and ends the method at the first video-carousel marker — so the same paste imports 19 clean ingredients and 3 clean steps. Fenced by a new corpus fixture (`taste.com.au2`).
- **Fresh installs now migrate and boot cleanly — FU-549 (2026-07-13).** A brand-new self-hosted install (empty database) would crash on first boot: the app runs the full Alembic migration chain via `flask_migrate.upgrade()`, and migration `a3e9f6c2d8b4` (Merchant→Store rename) died with `AttributeError: 'BINARY' object has no attribute 'name'` — an Alembic batch-mode quirk where a column *rename* reads `.name` on the `sqlalchemy_utils.UUIDType`'s `BINARY` impl. It went unnoticed because existing databases migrate incrementally (never from-empty in one shot) and the test/seed path builds the schema with `create_all()` rather than migrations. The UUIDType-column renames now pass the concrete `sa.BINARY(16)` type, so the full 116-migration chain applies cleanly from empty. Also pinned `alembic` in `requirements.txt` (it was only transitively present) so production resolves the verified version, and added migration tests (from-empty upgrade + schema-vs-model match) so this can't regress silently. *(A separate downgrade-only issue on SQLite — `downgrade base` dropping a named CHECK constraint — is tracked as FU-553; it doesn't affect boot, which only upgrades.)*
- **Buy-verdict "wait" hint dates now use the household timezone — FU-525 (2026-07-13).** The oracle bucketed purchase-observation timestamps into calendar days using UTC while comparing them against the household-local "today", so for a non-UTC household (e.g. AEST, UTC+10) any shop recorded before ~10am local landed on the previous day. That could shift the predicted "next low" date by a day and, at the edge, wrongly suppress or show the wait-hint (its `next_low <= today` staleness check). Observation dates are now taken in the configured household zone throughout the buy-verdict path (R-021), so the hint's dates and staleness logic line up with the rest of the app. Internal correctness fix; no API shape change.
- **Error page no longer claims "the team's been notified", and no longer leaks internal module URLs as a fake correlation id (2026-07-12).** Two problems on the shared server-error page:
  1. `PageErrorState.vue` copy for `variant='server'` said *"The team's been notified — try again, or come back in a few minutes."* That implies auto-telemetry, which the app doesn't have. Trimmed to *"Something on the server didn't respond as expected. Try again, or come back in a few minutes."* The `variant='render'` copy also carried a *"please tell us about it with the reference below"* tail that assumed a report-this surface (retired when the repo went private) — trimmed to *"Reloading the page is the fastest fix."*
  2. `router/index.ts` `ROUTER.onError` pushed `{ path: '/errors/server', query: { ref: err.message.slice(0, 80) } }`, and `ErrorServer.vue` reads `?ref=` straight through to `PageErrorState`'s `correlationId` slot. On a lazy-chunk fetch failure the `err.message` is Vite's *"The requested module 'http://localhost:5174/src/pages/onboarding/onboardingContent.ts' does not provide…"* — that dev-only module URL was ending up in front of end users as their "Reference:". Dropped the query entirely: the router logs the message to the console for debugging and the user-facing page just says "try again". The `?ref=` query slot is still honoured for legitimate correlation ids that other callers might one day pin (server `X-Request-Id`).

### Changed
- **Finishing a shopping list has no per-item level choice — the `level_overrides` API option is gone (FU-582, 2026-07-22).** The "Finish & restock" modal reviews what you ticked and restocks all of it to **Stocked**, full stop. The per-item stock-level picker that the UX-v2 M12 design called for was removed from the UI back on 2026-07-13; this change finishes the job by removing the matching server contract (`FinishShoppingListRequest.level_overrides`) and the dead client type. Reasoning: someone who has just bought an item at the shops would never intentionally mark it as anything other than Stocked, so the picker was ceremony over a foregone conclusion — and an API option no correct caller would ever set is a trap, not a feature for API users. A part-used item ("bought milk but it's still half-empty") is corrected on the stock item itself, where per-batch state belongs, not at finish time. The endpoint now takes an empty body; a caller still sending `level_overrides` gets a 400 rather than having it silently ignored. *(The 2026-07-13 UI removal shipped undocumented, which is why this was re-raised as a bug five days later — the contract-level cut and this entry close it out.)*
- **"Add a stock item" now asks for a stock group instead of an expiry date (2026-07-22).** The add dialog no longer carries an **Expiry** field; it carries a **Stock group (optional)** picker in its place. Reasoning: the create dialog should only ask for facts that are *permanent* properties of a pantry item. A stock group ("Baking", "Cleaning") is a stable classification of the item itself; an expiry date is a per-batch fact that changes every time you restock, so asking for it at add time invited a value that goes stale immediately. Expiry is unchanged everywhere it genuinely belongs — the stock item's detail page and the stocktake flow. The group picker mirrors the detail page's (same options, clearable, blank = ungrouped) and refetches its options each time the dialog opens, so a group added in Settings shows up without a reload. The create API already accepted `stock_group_id`; no backend change. Help's "Add a stock item" entry was corrected to match — it had promised "a location, expiry, or flag" at add time (the line that motivated adding expiry here in the first place), and also still named a "+ New stock item" button that is actually labelled **New item**; it now names the stock group and points expiry at the item's own page. This supersedes the 2026-07-17 change that added the expiry field to this dialog.
- **Main menu bar bottom border removed — FU-363 item 6 (2026-07-15).** Dropped the `bordered` line under the app header (`MainLayout.vue`); the toolbar's own `--surface-toolbar` background already separates it from the page, so the extra rule read as visual noise (from feedback: "would the main menu bar look better without the bottom border?"). The mobile side drawer keeps its border.
- **Sign out moved into the Settings shell header (2026-07-13).** The "Sign out" button was relocated from a card at the bottom of Settings → Account to the right-hand side of the Settings shell page header, inline with the admin Settings/Admin mode toggle (or the "Settings" title for non-admins). It uses the same `logoutAsync` → `/login` flow; the Account-page card was removed so there's a single sign-out entry point in the settings surface. (The app toolbar still carries no sign-out, per the FU-346 header design.)
- **Onboarding story polish — auto-advance removed, persona chips retired, control-scene redone (2026-07-12).** Five focused fixes to the cinematic intro (`OnboardingStory.vue`, `OnboardingLoop.vue`, `onboardingContent.ts`, `WelcomeWizard.vue`):
  1. Scenes no longer auto-progress; the user drives forward with Next. `autoAdvanceMs` + timer machinery deleted.
  2. Hero-loop's "What you're here for" persona chip bar (Mostly cooking / Watching spend / All of it) removed — flag-less since FU-210, only rewrote the Dora-centre sell. Centre now uses a single stronger description of what Dora watches ("expiry, stock, spend and habits, hinting at what you can cook now, and answering when you ask"). `PersonaPreviewKey`, `PERSONA_PREVIEWS`, `DEFAULT_PERSONA_PREVIEW`, the v-model plumbing across Story ↔ Wizard, and the `personaPreview` draft field all deleted.
  3. Scene 2's `sub` — "Tap any stage — or Dora in the middle — to see how it hands off to the next." — dropped; the loop-detail hint already says the same thing under the ring.
  4. Skip button label is now "Skip onboarding" (was "Skip"; the old label read as "skip to next part").
  5. Scene 4 ("You're in control") re-copyed + re-visualised — no more Cooking / Spend / Everything pills. Now shows a stylised control panel with four real Settings toggles (AI assistant, Spend tracking, Voice replies, Barcode scanning) as on/off switches, over "every part of Dora is a toggle — turn things on as you find you need them."

- **Settings shell gets a Settings/Admin mode toggle for admins — FU-346 (2026-07-10).** The Admin · global sidebar group no longer sits as a buried third group under Account + Kitchen setup. For admins, the "Settings" h1 at the top of the shell is now a two-pill segmented control — Settings / Admin — and the sidebar underneath is filtered to only that mode's groups. Mode is derived from the URL (`/settings/admin/**` = Admin), so refresh / back-button / deep-link all preserve it. Clicking a mode lands on that mode's first sidebar item (`/settings/account` or `/settings/admin/users`). Non-admins see the plain h1 unchanged. Mobile top-tab strip picks up the filter automatically.

- **Text-size preference now travels into every component-internal text — FU-025 (2026-07-10).** Since A6 landed the scale steps, page-level text scaled with the user's Settings → Appearance → Text size choice but component-internal text (button labels, input text, chip labels, table cells, toolbar titles, field helper text, dashboard score card, stepper captions, date/time picker text, uploader/slider/timeline captions, knob values) stayed pinned at Quasar's compile-time 14px/12px/etc. defaults. Fixed by overriding ~30 Quasar SCSS font-size vars in `src/css/quasar.variables.scss` to their rem equivalents (14px → 0.875rem, 12px → 0.75rem, …) — Quasar CLI auto-imports the file before framework SASS, so all `.q-*` emitted CSS now uses rem and tracks `--dora-base-font-size`. Three vars that participate in Quasar's `+ 10px` / `+ 8px` height derivations (`$bar-dense-font-size`, `$field-bottom-font-size`, `$field-dense-bottom-font-size`) stay in px at compile time; their visible-text selectors (`.q-bar--dense`, `.q-field__bottom`) are re-scaled to rem in `app.scss` instead. A handful of in-repo px content-text sites (`DoraScoreCard` hero number/trend/foot, `BuyVerdictCard` headline, `BuyVerdictBadge` label) also converted. Icon/graphic sizing vars, decorative Onboarding glyphs, the camera scanner UI, price-history chart labels, and the dashboard's 3/7.5 px micro-gauge stay in px — those size glyphs, not readable text.

- **Filter bars on Cookbook, Stock, and My Products reordered by usage frequency — FU-108 (2026-07-10).** Pure template moves; no state or logic changed. Cookbook: Sort moved from the tail to just after the quick chips; single-selects (Cuisine · Category · Time of day · Difficulty) precede the ingredients tri-state; numeric bounds and Dietary/Tools cluster before Collection (set-and-forget). Stock: "Needs attention" chip leads the cluster; Sort moved ahead of Location/Group. My Products: "Show inactive" moved to the tail as housekeeping.

### Fixed
- **List filters/sorts reject invalid field names cleanly — FU-546 (2026-07-12).** Filtering or sorting a list by a field name that isn't a real column (a relationship name, or an internal attribute) now returns a clean "bad request" (400) instead of a server error (500). This tightens the earlier FU-537 hardening into a strict allowlist across every list endpoint, and removes dead validation code it superseded.
- **The web app can be built again — FU-550 (2026-07-12).** The frontend production build (`quasar build`) had been failing its type-check since mid-June: a real dashboard card (`draft_shop`, "Draft this week's shop") was missing from an internal card-id list, so the build errored out — meaning the SPA couldn't be rebuilt or deployed. Added the missing entry (a one-line, no-behaviour-change fix); the build succeeds again. Surfaced while standing up the new browser E2E layer.
- **Self-hosting on Windows: the app now loads in the browser — FU-551 (2026-07-12).** When the backend serves the built web app itself (desktop bundle / Windows self-host), it served JavaScript module files with the wrong content type (`text/plain`, from the Windows registry), which browsers reject — leaving a blank page. The correct types are now forced regardless of host OS. (Linux/container deployments behind nginx were unaffected.)
- **Logging out is now recorded in the audit log — FU-548 (2026-07-12).** Session termination was the one state-changing action that left no audit trail. Logout now writes an `auth.logout` audit entry naming the user (recorded before the session is cleared), matching how login is audited — so the security log shows who signed out and when.
- **Crafted filter/sort field names no longer trigger a server error — FU-537 (2026-07-12).** List endpoints accept `?filter=field:op:value` / `?sort=field`; a field name referencing an internal Python attribute (e.g. `__class__`) slipped past the field allowlist's fallback check and hit the query builder, returning a 500 — which also let an attacker distinguish (via 400 vs 500) which internal attributes exist. The fallback now rejects any non-public field name, so these return a clean 400. (Found by the new security test suite; the query grammar was already safe against SQL-injection in the value position — this hardens the field position.)
- **Error recovery is more robust: one failing "undo" no longer blocks the others — FU-539 (2026-07-12).** When the app hits an unexpected error it rolls back any optimistic on-screen changes (e.g. a stock level shown as changed before the server confirmed). Previously, if one of those rollbacks itself threw, every remaining rollback was silently skipped, leaving other optimistic changes stuck on screen until refresh. Each rollback is now isolated, so a single failure can't strand the rest. Surfaced and pinned by the new frontend-resilience test suite.
- **Malformed record IDs in a URL now return "not found" instead of a server error — FU-532 / R-033 (2026-07-12).** Every API route that takes a record ID in its URL now validates that the ID is a well-formed UUID at the routing layer (Flask's `uuid` converter, applied to 123 params across 61 endpoints); a garbage/mistyped ID returns a clean 404 rather than a 500. This also closes the last of the string-vs-UUID bug family and, as a side effect, fixed dead cycle-detection in the locations tree (moving a location under its own descendant now correctly returns a validation error). Codified as engineering rule R-033.
- **A batch of quiet "wrong number / dead link" bugs found by the recent test passes — FU-527/528/524/522 (2026-07-12).** (1) The **"keeps running out" report silently dropped** any item that had no stock-level-change history (it fell back to the item's current level but read that off an un-loaded relationship → treated as unknown). (2) **Stock-group `item_count` always showed 0** in the groups list (it counted via an un-loaded relationship). (3) **Deleting a tool or dietary tag reported "0 recipes affected"** even when recipes used it (a str-vs-UUID key mismatch in the count lookup — the delete itself always worked, only the reported count was wrong). (4) **`normalise_unit` mis-handled degree marks** next to whitespace (e.g. `"gas °"` didn't canonicalise), so a few gas-mark/unit lookups missed. (5) The **change-email confirmation email's plain-text link pointed at the wrong route** (`/verify-email` instead of `/confirm-email-change`), dead-ending the flow for text-only mail clients (the HTML link was already correct). All five fixed and pinned by regression tests.
- **Stocktake queue and the alerts bell 500'd whenever any item was snoozed, on SQLite — FU-526 (2026-07-12).** `resolve_overdue_map` compared each item's `snoozed_until` against the current time, but SQLite hands that column back as a *tz-naive* datetime while "now" is tz-aware — Python raises `TypeError` comparing the two. So for as long as any single stocktake item was snoozed, `GET /api/stocktake/queue` returned 500, and because the alerts feed shares the same map, the alerts bell broke too (blank/error). Fixed by coercing `snoozed_until` to aware-UTC before the comparison (the same idiom already used elsewhere in that file). Postgres was unaffected (it preserves tz). Pinned by the stocktake snooze regression test plus an alerts-feed health assertion; browser walk queued in DORA_VERIFY.
- **Cook-mode / sourced stock-level drops silently recorded no depletion, and same-level "confirm" clicks logged phantom history — FU-533 (2026-07-12).** `UpdateStockItemHandler` loaded the item without eager-loading its `stock_level` (a `lazy="noload"` relationship), so the *previous* level always read as `None`. Two consequences: (1) the "did the level actually change?" guard always passed, appending a `StockLevelChange` row on every level PATCH — a same-level confirm produced `Stocked → Stocked` timeline noise; (2) worse, the depletion recorder (P8-07/FU-449 — the leg that feeds run-out prediction when you cook with or manually drop an item) bailed because it needs the previous level's sequence, so a sourced drop wrote **no `ConsumptionEvent` at all** — silent data loss in the depletion history. Fixed by `.include(STOCK_LEVEL)` on the load. Separately, PATCHing a recipe's `cuisine_id`/`category_id`/`recipe_collection_id` to `null` returned 204 but didn't clear the link (same noload trap — a relationship-side `= None` doesn't dirty the FK column); fixed by writing the underscore FK columns directly. All pinned by regression tests in `test_patch_semantics.py`. Consumption-loss browser walk queued in DORA_VERIFY.
- **Renaming anything to its own current name was rejected as a duplicate — found and fixed by the new PATCH-semantics suite (2026-07-12).** Five update handlers (stock item, recipe, stock location, store, admin-user) guarded against duplicate names with a self-exemption that compared the entity's `UUID` id against the raw `str` path param (`entity.id != stock_item_id`), which is *always* true — so re-saving any edit dialog without changing the name returned "already exists"/"already taken" (422). Same str-vs-UUID family as the product-unlink 404 and the taxonomy delete-count bugs. Fixed with `str(...)` on both sides at all five sites; pinned by five regression tests in `tests/e2e/dora_api/test_patch_semantics.py`. Browser check queued in DORA_VERIFY.
- **`GET /api/recipes/unlinked-ingredients` returned 500 on every request — found and fixed by the new API-fuzz suite (2026-07-12).** The handler filtered on `EntityField(RecipeIngredient, "stock_item_id")`, but the imperative mapping binds that FK column to the underscore-prefixed property `_stock_item_id`, so every call raised `AttributeError` → 500. The endpoint (which powers the "ingredients not linked to stock" review) was completely dead. Fixed to `_stock_item_id` at both query sites; pinned by `test__unlinked_ingredients__does_not_500`. Browser check queued in DORA_VERIFY.
- **`GET /api/meal-plans/reconcile-queue` returned 500 whenever the queue paginated — found and fixed by the new API-fuzz suite (2026-07-12).** The keyset cursor called `scheduled_for.isoformat()`, but the raw-SQL row hands `scheduled_for` back as a `str` on SQLite (a `date` on Postgres), so `.isoformat()` raised `AttributeError` → 500 the moment the queue had more than one page — any household with >50 unresolved past-day entries would hit it. Fixed by coercing str → `date` at the cursor boundary (R-005 portability, mirrors the existing `_stringify_entry_id` UUID normaliser); pinned by `test__reconcile_queue__paginates_without_500` (which also round-trips the returned cursor). Browser check queued in DORA_VERIFY.
- **Unlinking a product from a stock item always 404'd — found and fixed by the new delete-integrity e2e suite (2026-07-11).** `DELETE /api/stock-items/<id>/products/<product_id>` compared the in-memory `p.id == product_id` with the raw `str` Flask path param (no uuid converter), so the match never succeeded and every unlink returned "link never existed" — the link was impossible to remove via the API. Third incident of the FU-528 str/UUID family. Fixed by coercing the path param to `UUID` at the route boundary (malformed ids still read as 404); pinned by `test__unlink_product_from_stock_item__both_sides_read_back`. Browser check queued in DORA_VERIFY.
- **Alerts-digest dedup test no longer breaks when a seeded stocktake goes overdue mid-window (2026-07-11).** The FU-518 rewrite pinned digest passes to fixed June dates, but seed-data timestamps derive from real wall-clock — so on some real dates a seeded item's `stocktake_overdue` alert surfaces on the test's third simulated day, earning a legitimate new-key email the test misread as a dedup violation (went red 2026-07-11 having passed 2026-07-10). The test now drives passes until the key set converges — asserting the actual contract (a stamped key never re-emails while active) on every pass — then asserts silence.
- **Cookbook cookability + expiring filters were silent no-ops — found and fixed by the new recipe-router e2e suite (2026-07-10).** `GetRecipesHandler._restrict_query` loaded the plain "all recipe ids" universe *before* building the cookability / expiring maps. SQLAlchemy's identity map then handed those already-loaded (noload → empty `ingredients`) instances back to the maps' eager queries, so every recipe counted `(0 missing, 0 ingredients, 0 unlinked)`: `?cookable=true` kept **everything**, `?cookable=false` returned an **empty page**, `?max_missing=N` never excluded anything, and `?expiring_within_days=N` returned nothing. Unfiltered lists and the recipe detail were unaffected (they never ran the plain load first), which is why the DTO's cookability badge looked right while the filters lied. Fixed by building the relationship-dependent maps before the id-universe load; pinned by four filter tests in the new `tests/e2e/dora_api/test_recipe_router.py`. Browser check queued in DORA_VERIFY.
- **Buy-verdict unit tests no longer flake on UTC+n mornings (2026-07-10).** `tests/test_buy_verdict.py` derived price-sample dates from `datetime.now(timezone.utc)` but expectations from local `date.today()` — on any AEST morning the UTC calendar day is one behind, shifting every derived low-date and breaking the wait-hint prediction. Test helper now anchors samples to local-today at noon UTC. The production-side version of the same clock mix (cosmetic ±1-day drift in the wait hint) is logged as FU-525.
- **Alerts digest evaluates one run at one instant (FU-518 close, 2026-07-10).** `GetAlertsHandler.handle()` gained a `now` test seam and `send_alerts_digest` passes its tick time through; the digest dedup test was rewritten to assert per-alert-key dedup via the `AlertInteraction` ledger and now passes deterministically (the old per-item assertion conflated a fresh expired item's two legitimate alert keys).
- **Alerts bell no longer crashes the app when a `meal_reconcile_overdue` alert exists — FU-357 close-out (2026-07-10).** Regression from FU-317 Chunk 4 (2026-07-09): the backend gained a new `meal_reconcile_overdue` alert kind, but the SPA's `AlertKind` union in [alert.ts](web_app/src/models/alert.ts) never got it, so TS couldn't warn about the missing case in the five kind-switches (`iconFor`, `colorForKind`, `kindTheme`, `actionsFor`, `linkFor`) — all fell through and returned `undefined`. When the bell tried to render such an alert, `AlertRow.vue:114`'s `.slice()` on `undefined` threw and blew up the whole panel with an ErrorBoundary "something went wrong" screen. Fixed by adding `meal_reconcile_overdue` to the union + all five switches (icon `playlist_add_check`, theme "meals to reconcile", link to `/meal-plans/reconcile`, nav-only nudge like the other backward-looking kinds). Also added a defensive `?? []` in `AlertRow` so the next backend-only alert-kind rollout degrades to a nav-only row instead of crashing.
- **Dashboard alert-action now shows a success/error toast (2026-07-10).** `DashboardPage.applyAlertAction` was firing the API call and refreshing state but never calling `$q.notify` — silent success and silent failure. `AlertsBell` and `AlertsPage` both toast "Done." / "Could not apply." Fixed by adding the same toast pair to Dashboard so all three surfaces behave identically. (The state-ownership drift where three surfaces hand-roll the same action wrapper is logged as FU-521 for the finalisation-plan senior review.)
- **PageErrorState "Go to dashboard" is a live button when the error is on the dashboard (2026-07-10).** The button was a `router-link to="/"`, which no-ops when the current route already matches — so if the render-error boundary caught a crash on the dashboard itself, the dashboard button did nothing. Now, if `route.path === '/'`, clicking it reloads the page (matching the other escape hatch); otherwise it still navigates to `/`.

- **Two real reconcile bugs surfaced by the FU-169 Phase 2 pass (2026-07-09).**
  1. `bump_pool` (FU-317 Chunk 2) was binding `str(uuid)` against SQLite's
     BINARY(16) UUIDType column, so the ORM caller path (`cook_recipe`)
     blew up with `NoResultFound`. Fixed via a shared `_id_bytes` helper
     that normalises `UUID | bytes | str → bytes`; applied to
     `bump_pool`, `_read_pool`, `_load_entry`, `_latest_receipt`, and
     the receipt INSERT binds inside `reconcile.py`.
  2. `_sweep_auto_drain` (FU-317 Chunk 1) had no `NOT EXISTS` guard
     against existing receipts, so after a `Didn't cook` verb cleared
     `consumed_at`, the next sweep re-consumed the entry and wrote a
     stale `unresolved_auto` receipt over the user's `resolved_not_cooked`
     decision. Guard added — mirrors the manual branch.

### Added
- **Browser end-to-end smoke layer (Playwright) — FU-540 (2026-07-12).** A thin automated layer that drives the real built app in a headless browser — a *complement* to the manual QA/UAT walks, not a replacement. Covers the login flow and an authenticated navigation sweep over the main screens (dashboard, stock, cookbook, meal plans, shopping lists), asserting each renders and talks to the API without crashing. Run with `npm run test:e2e` (see `web_app/e2e/README.md`); wires into CI with FU-405. **First run is green (9 tests)** — and it immediately earned its keep by catching the two "can't build / can't boot" bugs above.
- **Concurrency / idempotency tests — FU-535 (2026-07-12).** New `test_concurrency.py` pins how the app behaves under double-submits and offline-queue replays: double-tapping a create is rejected as a duplicate (name uniqueness) rather than making two rows; re-applying a stock-level change records the depletion only once; edits to different fields don't clobber each other; and adding a just-deleted item to a list fails cleanly instead of orphaning. No bugs found — the behaviours are sound. (True simultaneous-writer cases are deferred to the Postgres CI matrix.)
- **Database-migration integrity tests — FU-536 (2026-07-12).** New `tests/test_migrations.py` checks the 116-file migration chain: exactly one head, linear/walkable history, every migration has a real (non-empty) downgrade, and — in an isolated throwaway database — a full up/down/up round-trip and a schema-vs-models match. **This surfaced a potentially serious issue (tracked as FU-549):** migrations were never actually run in the test suite (it builds the schema straight from the models), and running the chain from an empty database currently fails at one migration — which the production fresh-install path relies on. Flagged for confirmation on the release toolchain before advertising fresh self-hosting / the Postgres migration.
- **Audit-coverage test sweep — FU-538 (2026-07-12).** New `test_audit_completeness.py` pins that every state-changing API endpoint leaves an audit-log entry (or is on an explicit, reasoned exempt-list), and that each entry records who did it with secrets redacted. Confirmed the audit hook covers the whole mutating surface; the one endpoint with no audit trail (logout) is flagged for a product decision (FU-548).
- **Security test suite — FU-537 (2026-07-12).** New `test_security_injection.py` pins that user input can't escape its layer: SQL-injection payloads in the filter/sort query grammar are treated as literal search text (never executed; the table survives), privilege/identity fields (`is_admin`, `id`) can't be mass-assigned through update endpoints, and user content (recipe names, etc.) is HTML-escaped in rendered emails. Found and fixed a real field-name-handling bug (see Fixed); token single-use/expiry checks tracked as a follow-up.
- **Frontend resilience test suite — FU-539 (2026-07-12).** The SPA's safety-net layer (offline mutation queue, optimistic-update rollback registry, global error handler, render error boundary, unsaved-changes guard) is now covered by 33 tests — the layer where a bug means silent data loss or a white-screen crash. First run found + fixed a real robustness bug in the rollback registry (see Fixed).
- **Query-count regression guards on the hot read endpoints — FU-534 (2026-07-12).** New `test_query_budgets.py` pins that the stock list, dashboard summary, shopping-list detail, and cookable-recipe filter each issue a *constant* number of database queries regardless of how much data exists — so a future change that accidentally reintroduces a per-row query (the noload/N+1 pattern behind several of this month's bugs) fails a test instead of silently shipping. This is the automated net for engineering rule R-032.
- **Frontend accessibility (a11y) testing — FU-542 (2026-07-12).** Component specs can now assert against WCAG rules via `vitest-axe`/`axe-core` (shared `expectAccessible()` helper). Wired into the AlertRow, DoraModeSlider, and SettingsFileDrop specs to establish the pattern; the very first run caught a real defect — the file drop-zone's hidden `<input type="file">` was unlabelled — now fixed by removing it from the accessibility tree (the drop-zone itself is the exposed control). A remaining structural a11y issue on the same component is logged as FU-545.
- **Frontend test-coverage reporting — FU-541 (2026-07-12).** `npm run test:coverage` (in `web_app/`) produces a per-module coverage map (terminal summary + browsable `coverage/index.html`) via `@vitest/coverage-v8`. Deliberately report-only with **no coverage threshold/gate** — it's a map to find untested modules, not a target to hit. Plain `npm test` is unaffected (coverage is opt-in). Backend coverage was already wired (`pytest --cov=dora_api`, report-only).
- **Test-suite pass 4 — API fuzzing, PATCH semantics, Pinia store layer, e2e tail closed (2026-07-12).** Backend 1323 → **1415 passing** (~61 s); frontend 254 → **298** Vitest tests (19 files). New:
  - **API-fuzz / robustness sweep** (`test_api_fuzz.py`): "4xx, never 500" over the whole surface — malformed request bodies (empty, invalid-JSON, array-for-object) on every POST/PATCH/PUT, garbage query params on every GET, non-UUID/overlong/nonexistent path params, and wrong-type fields on the core creates. **Found three real 500 bugs** (two fixed — see Fixed; one systemic path-param bug logged as FU-532 and pinned as a strict xfail over its 82-route list).
  - **PATCH-semantics suite** (`test_patch_semantics.py`, 59): the missing-vs-explicit-null matrix, no-op PATCH, unknown-field rejection, and cross-field 4xx across 9 surfaces — pins the null-out contract per surface so a future `exclude_unset` refactor can't silently flip a field's clear-vs-ignore behaviour. **Found the 5-site rename-to-own-name bug** (fixed — see Fixed) and three noload-read PATCH bugs (FU-533, incl. silent consumption-event loss).
  - **e2e tail closed**: suggestions router (14), substitutes router (16); `deals/` confirmed to have no HTTP surface. FU-519 tail complete.
  - **Pinia store layer** (`stockItemStore` 16 / `shoppingListStore` 10 / `alertStore` 9 / `locationStore` 9): derived getters, optimistic-update + rollback-registry contract, cache/refresh dedupe, error-path consistency, and pinning that the alert badge reads the server's `actionable_count` verbatim (R-003, no client recompute).
- **Test-suite pass 3 — enforcement sweeps, delete integrity, minor-surface tail, component layer (2026-07-11).**
  Backend 1238 → **1323 passing** (85 new tests across 6 suites); frontend 203 → **254** Vitest tests (4 new component specs, 51 tests). New:
  - **Route auth/permission enforcement** (`test_route_auth_enforcement.py`, 6): anonymous sweep over all 271 `/api` rules (259 protected (method, route) pairs must 401 — none leak), `PUBLIC_ENDPOINTS` allowlist-rot guards, and a pinned 32-endpoint admin-only contract driven as a fresh non-admin (all must 403), with a reverse check that counts `require_admin` call sites in the source tree so a future ungated admin endpoint fails the suite. No vulnerabilities found.
  - **Delete / referential integrity** (`test_delete_integrity.py`, 24): cross-entity delete webs — stock item referenced by recipe/list/waste, recipe on a meal plan + in a collection, store with price history/preferred buys, location with children + items, product↔stock-item links, meal plan with receipts, list with attachments, double-deletes are 404 never 500. Found the product-unlink 404 bug (see Fixed).
  - **Minor-surface e2e** (FU-519 tail): locations tree (21 — kind nesting rules, cascades, moves), app_settings (17 — GET shape, PATCH round-trips + validation), client_logs (13 — public-endpoint contract, payload validation), help (4 — version/changelog/food-fact shapes).
  - **Component Vitest**: AddToListButton (20 — all five variants, cart-state decision tree, bulk + inline-product paths), AlertRow (13 — incl. pinning the unknown-kind degrade-not-crash regression), DoraModeSlider (6), SettingsFileDrop (12). Store-mock pattern for Pinia `storeToRefs` documented in `addToListButton.spec.ts`.
- **Test-suite Phases 3 + 4, second pass — FU-519 essentially closed (2026-07-10, later).**
  Backend 1096 → **1238 passing** (~45 s); frontend 192 → **203** Vitest tests. New:
  - **Search e2e** (`test_search_router.py`, 12): scoring order (exact > prefix >
    contains > fuzzy), per-type subtitles (location breadcrumbs, list status,
    recipe cuisine), types filter incl. the invalid-types→all fallback, and the
    per-*type* limit clamp semantics.
  - **DTO contract snapshots** (`test_dto_contracts.py`, 27 endpoints): response-key
    shapes pinned against a committed `dto_snapshots.json`; intentional contract
    changes refresh via `DORA_UPDATE_DTO_SNAPSHOTS=1` and review as a JSON diff.
  - **Long-tail e2e** (10 surfaces, 103 tests): waste rescue feed + insights,
    budget status/history windows, all 10 report endpoints, stocktake queue/
    check/snooze/review lifecycle, and the six taxonomy routers via a shared
    `_taxonomy_crud.py` helper.
  - **First component-level Vitest** (`stockLevelDot.spec.ts`, 11): both
    StockLevelDot components rendered with the real Quasar plugin — the mount
    pattern (client-bundle alias + `@vitejs/plugin-vue` + per-file jsdom) is
    now established for future component specs.
  - The pass surfaced **four more logged findings**: a stocktake-queue 500 (and
    broken alerts bell) while a snooze is active on SQLite (FU-526, strict-xfail
    pinned), two noload-relationship count bugs (FU-527), str/UUID key mismatches
    in tool/dietary-tag delete counts (FU-528), and a transient reconcile
    idempotence flake pointing at non-deterministic receipt ordering (FU-529).

- **Test-suite Phases 3 + 4 targeted sweep — FU-519 / FU-520 (2026-07-10).** Backend
  920 → 1096 passing (~41 s); frontend 53 → 192 Vitest tests (~1 s). New suites:
  - **API e2e** for three of the four ⚠️ priority surfaces: `test_recipe_router.py`
    (CRUD, filters, cookability surfacing — found the filter bug above),
    `test_meal_plan_router.py`, `test_dashboard_router.py`. `search` still open on FU-519.
  - **Repository/persistence** (`test_sqlalchemy_repository.py`): paginate math, the
    full filter-operator matrix, field_map resolution, NOCASE sort, UUID round-trips,
    on a standalone SQLite fixture. Found the Contains/StartsWith `case_sensitive`
    inversion (FU-523, pinned by strict xfails).
  - **Emailer** (`test_email_templates.py` + `test_email_sender.py`, 29 tests): all five
    content templates + layout render with call-site-shaped context; SMTP wire
    choreography, MIME assembly, dry-run degradation and error paths via a fake
    transport. Found the change-email plain-text wrong-link bug (FU-522).
  - **Hypothesis property tests** (`test_domain_properties.py`, 26 tests): invariants
    over recipe_cookability (cookable ⇒ nothing required missing), stock_status band
    coherence/monotonicity, product_offer discount bounds, units round-trips.
    Found `normalise_unit` non-idempotence (FU-524). `hypothesis` pinned in requirements.
  - **Frontend Vitest** (9 new spec files): formatQuantity, scaleQuantity,
    queryStringBuilder, relativeTime, weekDates, shoppingList, stockStatus,
    useListState, useStockFilters. `@vue/test-utils` + `jsdom` devDeps in place for the
    component layer (still open on FU-520).
  - The commented-out CI workflow now runs bare `pytest` (full suite, closing the §3.1
    e2e-only scope gap) and `npm test`, so un-commenting it (FU-405) inherits the
    right scope.

- **Test-suite Phase 1 tail + Phase 2 (per-test DB isolation) — FU-169 (2026-07-09).**
  Bare `pytest` now runs the whole tree (unit + e2e), prints a term-missing
  coverage report (report-only, no fail-under gate), and starts every test
  from the freshly seeded DB baseline.
  - **`pytest-cov==5.0.0`** pinned + `.coveragerc` scoped to `dora_api/`
    (migrations + seed omitted); pytest.ini's addopts wire `--cov` on by
    default. Opt out with `pytest --no-cov` for a fast inner-loop run.
  - **Per-test DB rollback via SQLite file snapshot.** The session-scoped
    `api` fixture snapshots the seeded DB after `startup(is_test_env=True)`;
    an autouse function-scoped teardown rolls back the ORM session, disposes
    the engine pool, and restores the snapshot. ~1-3 ms overhead per test;
    replaces the FU-166 hand-patches for case-insensitive / filter-to-known-row
    workarounds. Kills cross-test order coupling; unblocks `pytest-xdist`.
    The one `db.engine.begin()` in the codebase (the reconcile sweep) is
    included in the isolation because we're restoring the whole file, not
    fighting individual transactions.
  - **`tests/factories.py`** — hand-rolled builders (`make_stock_location`,
    `make_product`, `make_stock_item`) so tests declare only the fields they
    care about instead of spelling 13 attributes per create. Docstrings
    document the design (hand-rolled over factory_boy, HTTP-only, defaults
    on happy-path).
  - **`uuid_bind` helper in `tests/support.py`** — normalises UUID-like
    values to the `bytes` shape SQLite's BINARY(16) UUIDType needs for
    raw-`text()` binds. Documented at the callsite so future tests that
    reach under the ORM stop rediscovering the trap.
  - 3 order-coupled test files refactored to be self-contained: per-file
    autouse fixtures with opt-out markers (`no_seed_cellar`, `no_seed_product`)
    where a create-then-assert pattern was implicit; explicit setup for
    duplicate-error assertions.

- **Meal reconciliation admin setting — FU-317 Chunk 6 (2026-07-09).**
  New **Settings → Admin → System → Meal reconciliation** page exposes the
  install-wide *auto-drain past-day meals* toggle. When on (default), the
  daily sweep silently drains the recipe pool as days roll past. When off,
  the sweep writes `unresolved_manual` receipts and every past-day entry
  waits on the reconcile page. Also carries a deep-link chip that
  everyone (not just admins) can use to open the reconcile page. Closes
  the FU-317 stack — Chunks 1-5 built the backend + surfaces, Chunk 6
  puts the last visible dial in the admin's hand.
- **Reconcile past meals — the page + dashboard chip + meal-plans header nudge — FU-317 Chunk 5 (2026-07-09).**
  Dora now surfaces past-day meal-plan entries she assumed you cooked and lets
  you confirm, adjust, or dispute them one at a time. First user-visible piece
  of the FU-317 stack (Chunks 1-4 built the receipt table, sweep, pool helper,
  queue endpoints, alert, and suggestion behind the scenes). New surfaces:
  - **`/meal-plans/reconcile`** — single-runner page (same shape as
    Stocktake). Five verbs per entry: **Cooked**, **Different portions**
    (records actual servings), **Cooked later** (records the actual date),
    **Didn't cook** (undoes any drain), **Skip for now** (defers). Empty
    state is a state of the runner; five-counter recap on completion.
  - **Dashboard "Reconcile N past meals" chip** in the *Your kitchen* zone
    (hide-when-empty, R-029) — the FU-317 alert and suggestion also
    surface via the existing bell + suggestions surfaces.
  - **Meal Plans header nudge** — a small "N past-day meals need
    confirming →" link above the planner when the queue is non-empty
    (hide-when-empty).
  - New `useReconcileQueue` composable — one server-owned queue count
    powers every surface, so a verb submitted on the page invalidates
    the chip + header nudge in the same tick.
- **`meal_reconcile_overdue` alert + `reconcile_meals_pending` suggestion — FU-317 Chunk 4 (2026-07-09).**
  Backend-only. Two new backward-looking nudges fire off one shared signal
  (`features/meal_plans/reconcile.py:reconcile_overdue_signal`, R-003) when the
  reconcile queue has ≥3 unresolved past-day entries stretching ≥4 days back
  (D1 threshold, locked by impl-plan). The alert lives in `alert_kinds.py` as
  a `fyi` tier (matches `no_planned_meals` / `shopping_day` — never inflates
  the badge), keyed `meal:meal_reconcile_overdue:<head_iso>` so a user
  snooze/dismiss persists while the head-of-queue entry stays there and
  rolls to a fresh key once cleared. The suggestion generator produces a
  card that deep-links to `/meal-plans/reconcile` (Chunk 5 registers the
  page); dedup keyed on the same head-of-queue ISO date. Both surfaces
  clear the moment the last unresolved entry is resolved.
- **Meal-plan reconcile queue + verb endpoints (backend only) — FU-317 Chunk 3 (2026-07-09).**
  Backend-only; no user-visible surface yet (that's Chunk 5). Two new endpoints on the meal-plan router:
  - `GET /api/meal-plans/reconcile-queue?cursor=<opaque>&limit=<int>` — cursor-paged
    list of past-day entries whose latest `MealPlanReconcileReceipt` is unresolved
    (or `resolved_deferred` — the "Skip" verb keeps them in the queue). Includes
    a `total` count for Chunk 5's dashboard chip. `include_resolved=true` is
    accepted but returns empty in MVP (history view is Chunk 5).
  - `POST /api/meal-plans/reconcile/<entry_id>` — five verbs (`cooked` /
    `cooked_adjusted` / `cooked_later` / `not_cooked` / `skip`) each writing a
    new append-only receipt against the entry (never mutating past receipts —
    same `MealPlanSwapLedger`-style shape as FU-451). Pool math goes through
    Chunk 2's `bump_pool`; `consumed_at` is stamped or cleared to match the
    target state. Idempotent — a same-verb replay returns `idempotent: true`
    with no new receipt. A different verb writes a corrective receipt AND
    applies whatever pool / consumed_at delta lands the entry in the new
    state (e.g. `cooked` → `not_cooked` restores the drain). Rate-limited
    60/min per authenticated user via the FU-458 shared `subject` bucket.
- **`Recipe.available_meals` mutation collapsed to one authority — FU-317 Chunk 2 (2026-07-09).**
  Backend-only refactor. New shared helper `dora_api/features/recipes/pool.py`
  with `bump_pool(recipe_id, delta, connection=None) -> int` (atomic
  `UPDATE ... RETURNING`, floors at zero, works both on the ORM session and on
  a decoupled `sqlalchemy.engine.Connection`) plus a pure `preview_pool_after`
  used by preview surfaces. Rewired the three writers — the reconcile sweep,
  `cook_recipe`, and `adjust_recipe_meals` — through the helper; the assistant
  confirm-action preview through the pure projection. The floor-at-zero rule
  no longer lives in two Python handlers plus one SQL CASE WHEN — one place
  now, `grep -rE '\.available_meals\s*=[^=]' dora_api/` returns only creation /
  seed sites. Closes the R-003 drift flagged in `PROPOSAL_MEAL_RECONCILE.md`
  §5.1.
- **Meal-plan reconcile receipts (backend only) — FU-317 Chunk 1 (2026-07-09).**
  The daily past-day meal-plan sweep (`reconcile_consumed_meals`) now writes an
  append-only `MealPlanReconcileReceipt` per drained entry, so the previously
  silent "we assumed you cooked this" mutation carries an audit trail that
  Chunks 3-6 will surface via a `/meal-plans/reconcile` page. Chunk 1 is
  backend-only — **no user-visible change yet**; the receipt table is being
  populated in the background, ready for the surface work.

  A new install-wide `AppSetting.auto_drain_past_meals` (default TRUE, matches
  today's behaviour) decides the sweep's branch. TRUE keeps the historic
  auto-drain (`consumed_at` stamped, `available_meals` decremented) plus writes
  an `unresolved_auto` receipt. FALSE switches to a "receipt-only" branch — the
  sweep leaves entries and pool untouched and writes `unresolved_manual`
  receipts, so nothing consumes silently and the reconcile page (Chunk 5) will
  own the mutation. Setting is install-wide, not per-user, because `MealPlan` is
  household-shared (D5 / FU-517). Editable via `PATCH /api/app-settings`;
  admin-only.

  Migration `a1b7f3e9c2d4` (chains from `f4b2d8e6a1c3`) adds the column +
  `MealPlanReconcileReceipt` table (FK cascade to `MealPlanEntry`, composite
  index on `(state, created_at)`). Forward-only, additive, no backfill. Both
  sweep branches are idempotent across repeat invocations (auto-drain: the
  `WHERE consumed_at IS NULL` guard; manual: a `NOT EXISTS` receipt-check).

### Security
- **P5-01 security & privacy hardening sweep — FU-387 (2026-07-09).** Full
  pre-Phase-4 pass across the six P5-01 buckets (auth & sessions, authorization,
  secrets, data privacy, uploads, dependencies). The artefact is the standing
  [SECURITY_REVIEW.md](docs/security/SECURITY_REVIEW.md); a new
  [SECURITY.md](SECURITY.md) at the repo root documents how to report
  vulnerabilities; a new [scripts/security-audit.sh](scripts/security-audit.sh)
  runs `pip-audit` + `npm audit` on demand. Behaviour changes shipped in the
  same pass:
  - `SESSION_COOKIE_SECURE` **defaults to True when `DORA_ENV=production`** so a
    prod deploy that forgets `DORA_SECURE_COOKIES=1` no longer silently ships
    the session cookie over plain HTTP. `DORA_SECURE_COOKIES=false` stays as an
    opt-out for LAN-behind-VPN installs, and the boot-time warning now surfaces
    the deliberate opt-out (previously it only warned on unset).
  - New `hash_password()` helper pins the password KDF at `scrypt:32768:8:1`;
    every register / reset / change / seed call-site routes through it so an
    upstream Werkzeug version bump can't silently change the KDF. Existing
    hashes still verify (`check_password_hash` auto-detects the method).
  - Backups no longer round-trip the three Fernet-encrypted operational secrets
    — `User.llm_api_key_encrypted`, `AppSetting.smtp_password_encrypted`,
    `AppSetting.vapid_private_key_encrypted`. Ciphertext-only isn't compromise,
    but a leaked backup plus a leaked encryption key would be; defence-in-depth
    against accidentally-shared backups.
  - Python dependency bumps: `flask-cors 4.0.0 → 6.0.0` (7 CVEs),
    `flask 3.0.2 → 3.1.3`, `jinja2 3.1.2 → 3.1.6` (5 CVEs),
    `requests 2.32.4 → 2.33.0`, `pytest 8.3.4 → 9.0.3` +
    `pytest-asyncio 1.4.0` + `typing_extensions 4.16.0` for compatibility.
    `pip-audit -r requirements.txt --strict` → clean.
  - Frontend dependency bumps via `npm audit fix` (lock-file only): `form-data`
    (high, CRLF injection), `vite` (high, Windows-only), `js-yaml` (moderate)
    resolved. Two low-severity dev-only Windows-only items (`esbuild` + the
    transitive `@quasar/app-vite`) remain accepted pending an upstream Quasar
    release.

### Removed
- **Proactive "good deal" alerts cut before release (2026-07-09).** The
  `good_deal` alert type shipped in the FU-450 commit earlier the same day was
  pulled back out end-to-end: alert kind, per-user `good_deal_alert_threshold`
  User column + migration `d2f8a1c4b7e9`, Preferences → Notifications control,
  AlertsPage mapping, `--alert-kind-good-deal` token (renamed to
  `--savings-accent` — still needed by the swap-suggestions panel + dashboard
  savings signpost). Reason: proactive "this product is cheap right now"
  nudges read like the app pushing users to buy from stores, which isn't
  Dora's posture. The **fake-markdown demotion in the Buy Verdict card**
  (FU-450's other half) stays — it *stops* users being tricked by an
  inflated "special", it doesn't push them at anything. The `DealQuality`
  compute + its use by the FU-451 recipe-swap ranker are unchanged.

### Changed
- **Data pages (Import + Backup & restore) UI revamp — FU-359 (2026-07-09).**
  Both admin data screens were rebuilt onto the shared Settings design language
  (`SettingsPageHeader` + `SettingsSection` + `SettingsRow` + `.settings-divider`)
  so they match the rest of Settings instead of the old ad-hoc card stack. New
  shared `SettingsFileDrop.vue` gives a proper drag-and-drop upload zone (idle /
  filled / busy + progress) on both pages. Import: template download moved into
  the header, responsive column-mapping grid, cleaner preview table, options as
  labelled toggle rows. Backup & restore: backup library rendered as tidy rows
  with inline actions, restore preview in a self-contained panel, and the
  Library-settings / Image-compression blocks converted to `SettingsSection`s.
  Upload/inspect/restore logic is unchanged — presentation only.
- **Dora chat header: Basic/AI mode is now a toggle slider — FU-360 #3 (2026-07-09).**
  The read-only Basic/AI chip in the assistant chat header is replaced with a
  two-position slider (`DoraModeSlider.vue`) — skewed thick knob that slides
  between "Basic" and "AI" with a brand-primary glow on the active side. Tapping
  flips the user's `llm_enabled` preference via `PATCH /auth/me` and re-probes
  `/assistant/status`. Disabled state with an explanatory tooltip when the
  install-wide master flag is off or the user hasn't finished configuring a
  provider (mirrors the AssistantSettings `canEnable` guard). The "AI mode
  unavailable" banner logic is unchanged, so a "preference on but currently
  unreachable" state still surfaces the banner.
- **Substitute-swap on shopping lists only offers when there's a substitute —
  FU-407 / RD-18 (2026-07-09).** The per-line "Swap with substitute" button used
  to be a dead-end for items with no recorded substitute (tap → "No substitutes
  recorded" toast). Lines now carry a server-derived `has_substitutes` flag, so
  the action is disabled up front with a clear tooltip ("No substitutes recorded
  for this item" vs "Swap for a substitute item"). The relabel also
  disambiguates it from the "store offers" picker on the same line.

### Added
- **Personal notes on a recipe — RD-29 / FU-432 (2026-07-09).** A recipe now has
  an optional free-text **Personal notes** field (distinct from the method /
  instructions) — "I halve the chilli", "kids' favourite", "serve with rice". Edit
  it on the recipe detail page; it shows in **cook mode under the steps** where
  it's handy mid-cook. Notes carry across recipe versions. Migration
  `f4b2d8e6a1c3`. (Closes FU-432: RD-11 per-ingredient notes was dropped as creep;
  RD-3 filterable ingredient picker + RD-33 "Log cook" toolbar placement were
  already satisfied by earlier work.)
- **Budget-defense recipe swaps — FU-451 (2026-07-09).** When a meal-plan week
  is *projected* to blow your grocery budget, the planner now shows a
  **Suggestions** panel offering cheaper **recipe swaps** to bring it back under —
  a non-destructive alternative to cutting the shopping list. Each suggestion is
  the best cheaper alternative for a given meal ("Thursday dinner: Beef stroganoff
  → Chicken tray-bake, −$4.10 · uses stock you have"), ranked by saving, capped at
  five. Preview → confirm → apply, with a session Undo (a fresh reverse action,
  backed by a `MealPlanSwapLedger` audit row; migration `e3a9c7b1f2d8`). The
  Dashboard budget card gains a "Save $X this week — N swaps ready" signpost that
  deep-links to the planner. Money-features-gated; hidden entirely when off.
  Endpoints: `GET/POST /api/meal-plans/<id>/{swap-suggestions,apply-swap,undo-swap}`.
  **Product/brand swaps were cut** (not built) — they'd require per-item "usual
  product" upkeep that isn't in the product direction; recipe swaps are the whole
  lever. Recipe cost estimation was extracted to a shared `recipe_cost` module
  (R-003) so the ranker and the recipe-detail card price recipes identically.
- **Deal-quality signal + honest-markdown Buy Verdict — FU-450 (2026-07-09).**
  Dora now judges how good a product's current price really is, using the
  product's own offer history *and* your household's real paid prices as ground
  truth. The **Buy Verdict** card flags an inflated "special" — if a merchant
  claims a saving but you've paid less recently, a `buy` is demoted to `wait`
  with *"Markdown looks inflated — you've paid less than this 'special'
  recently"*. Money-features only. Fake markdowns are also filtered out of the
  FU-451 swap ranker. (The originally-shipped `good_deal` proactive alert was
  cut same day — see the Removed section above.) This is the upstream half
  (P6-03 survivors) of the budget-defense-swaps design
  (`PROPOSAL_BUDGET_DEFENSE_SWAPS.md`).
- **Dora Basic mode can now add to your shopping list by typing — FU-429 (2026-07-08).**
  Basic mode (the rule-based assistant that runs by default with no language
  model configured) was answer-only: it could tell you your list *status* but
  couldn't put anything on it. It now understands add-to-list phrasing — "add
  milk", "buy eggs and bread", "need to buy rice" — resolves each item against
  your pantry, and drops the unambiguous matches onto your primary list (the
  same path the contextual "Add to list" chip uses, so notifications match).
  Items that match more than one pantry entry, or none, are called out rather
  than guessed. AI mode's richer multi-step add flow is unchanged. This is the
  headline fix from the FU-429 assistant-architecture reconciliation: since most
  everyday users never wire up an LLM, Basic mode is the default experience and
  now has its first real action verb.
- **Hide the Dora helper entirely — FU-360.6 (2026-07-08).** A new per-user
  toggle at **Settings → Assistant → "Show Dora on every page"** removes the
  floating helper bubble for your account (Basic *and* AI). Defaults on
  (discoverable by default); flip it back any time. Backed by a `show_assistant`
  user preference (migration `c7d1a9e3f2b6`).
- **Free-text ingredient path in the recipe editor — FU-506 (2026-07-07).**
  The recipe editor's ingredient picker now offers a second no-match option
  next to "Create '<typed>'": **Use "<typed>" as free text (no pantry link)**.
  Picking it saves the row as an unlinked ingredient (server-supported since
  the paste-import Chunk 4 landed) — the recipe keeps the ingredient name for
  cook-mode and display, but doesn't demand a pantry entry. Unlinked rows show
  the raw text as an italic caption under the picker so the row isn't blank,
  and the picker label flips to "Free-text ingredient". Cookability stays
  "unknown" while any required ingredient is unlinked, per the existing tri-
  state rule.
- **Unlinked-ingredient warning after auto-generating a shopping list from a
  meal plan — FU-505 (2026-07-07).** Auto-gen only produces stock-item-
  anchored lines, so recipe / meal-plan ingredients without a linked StockItem
  used to vanish silently. The auto-generate response now carries an
  `unlinked_skipped` list (recipe + ingredient name), and the meal-plan
  generator pops a dismissible **Add these manually** dialog listing them
  after the success toast. No new line shape — the model kept its stock-item
  contract; the dialog is the honesty layer.
- **Expiry prompt when marking a stock item as opened — FU-507 (2026-07-07).**
  Toggling a stock item to "opened" (row action or detail-page toggle) now
  opens a small date-prompt dialog prefilled with the current expiry, asking
  **Update its effective expiry?** — opened milk shortens fast, opened jam
  barely moves, so no universal rule works. **Skip** leaves the expiry alone
  (default-unchanged, the previous behaviour). **Update expiry** saves the
  new date and the open flip in one PATCH. Marking back to sealed is
  unchanged (no prompt).
- **App-wide security response headers — FU-459 (2026-07-07).** Every
  response now carries `X-Content-Type-Options: nosniff`,
  `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer-when-downgrade`,
  and a permissive-but-honest `Content-Security-Policy` (default-src
  self; script-src self 'unsafe-inline' 'unsafe-eval' — Quasar's runtime
  needs both; style-src self 'unsafe-inline'; img-src self data: blob:
  https:; connect-src self https:; frame-ancestors 'none'; base-uri +
  form-action self). Hand-rolled hook in `middleware.py` — no
  Flask-Talisman dependency. `response.headers.setdefault()` yields to
  any header a reverse proxy already set. `DORA_DISABLE_SECURITY_HEADERS=1`
  opts out (escape hatch when a specific proxy/CDN conflicts — not
  intended for production use). Tightening `script-src` off
  'unsafe-inline'/'unsafe-eval' requires a nonce-per-response scheme
  (bigger job than the header itself, deferred).
- **Boot-time warning when `DORA_SECURE_COOKIES` is unset in production —
  FU-460 (2026-07-07).** Any install running `DORA_ENV=production`
  without an explicit `DORA_SECURE_COOKIES` value now sees a loud stderr
  banner at boot: HTTPS-fronted installs (SaaS or self-host behind
  Let's Encrypt / Cloudflare / LB TLS termination) that forgot the flag
  get told to set `DORA_SECURE_COOKIES=true`, and installs deliberately
  serving over plain HTTP (LAN-only, VPN-fronted, home-lab) are told to
  set `DORA_SECURE_COOKIES=false` explicitly to silence the warning.
  Warning, not a boot-block — a prod install on plain HTTP is a
  legitimate shape and shouldn't be forced through an override flag.
  Default stays off so desktop / LAN self-host / dev keep working
  unchanged. `DORA_SKIP_PROD_VALIDATION=true` also silences.
- **Put-away helper on finished shopping lists — FU-452 Surface A (2026-07-07).**
  A **Put away** button now appears in the toolbar of a `done` shopping list.
  Opens an ephemeral checklist dialog that groups the list's ticked items by
  their `stock_location_breadcrumb` — one card per kitchen location with a
  tick-per-group affordance ("Freezer · 3", "Pantry · 2", "(No location) · 1"
  pinned to the bottom). Unsorted items get a per-line **Assign** button that
  opens a small location picker (searchable walked tree, same shape as the
  create-stock-item picker); saving re-parents the item and refreshes the list
  so the item moves group in-place. All checklist state is ephemeral — closing
  the dialog resets ticks, and no new column was added. Nothing appears on
  non-`done` lists. Surface B of the original FU (grouping expiring alerts by
  location) was explicitly cut this session.

### Changed
- **Dora helper polish — FU-360 (2026-07-08).** The AI/Basic mode chip in the
  chat header no longer reads squished: dropped the `dense` sizing for a
  rem-based font (so it follows your text-size preference) with proper padding.
  The first-time "Hi! I'm Dora" hint is now remembered **per user** rather than
  per browser, so on a shared household browser each account sees it exactly
  once. The AI-mode settings copy was updated to reflect that Basic mode now
  handles simple add-to-list itself.
- **Internal: unit-of-work refactor swept across 10 more handlers — FU-512 (2026-07-08).**
  The FU-456 pattern-setter (`CreateRecipeHandler` — one flush, one commit
  at the end) has been mirrored across every other multi-commit handler
  identified in the FU-512 runbook: `CreateMealPlanTemplateHandler`,
  `CloneMealPlanTemplateHandler`, `CreateSetHandler` (meal-plan template
  sets), `NewRecipeVersionHandler`, `AutoGenerateHandler`, `SeedHandler`
  (onboarding), `CopyShoppingListHandler`, plus the three shopping-list
  template handlers (`CreateTemplateHandler`, `InstantiateTemplateHandler`,
  `SnapshotFromListHandler`). Habit-commits that existed only to
  materialise the parent's id are gone (`SqlAlchemyRepository.add()`
  assigns UUIDs client-side, so a flush at most is needed when a
  downstream Core-level insert needs the FK on the wire); `if children:`
  guards around the final commit are gone (an empty session commit is a
  no-op). `SeedHandler`'s locations loop still calls `flush()` before
  each child insert — the classic mapper has no `relationship()` between
  self-referencing StockLocation rows, so the local flush contract
  applies. New happy-path e2e tests pin each of the 10 handlers as one
  transaction. No behaviour change for successful paths; error branches
  now roll back the whole write, matching FU-456.
- **`GET /api/suggestions` no longer mutates the DB — FU-513 (2026-07-08).**
  The read path historically deleted expired snoozes and committed on every
  dashboard load, taking a write lock on the hot request path and violating
  the "GETs don't mutate" contract downstream tooling (browser back-cache,
  HTTP proxies, retry-on-failure logic) relies on. The inline
  delete-and-commit is gone; correctness is unchanged because
  `_is_suppressed_now` already filters expired snoozes out of the returned
  set. Table hygiene moved to a new daily APScheduler job
  `prune_expired_snoozes` (03:30 UTC) in
  `dora_api/features/suggestions/prune_expired_snoozes.py`. Also fixed a
  latent tz-mismatch in the read filter: SQLite returns
  `DateTime(timezone=True)` columns as naive on read, so `_is_suppressed_now`
  now treats a naive `snoozed_until` as UTC before comparing against a
  tz-aware `now` (same pattern as `get_alerts.py`). Regression-pinned by
  `tests/e2e/dora_api/test_suggestions_snooze_prune.py` (4 tests).
- **Dependency injection walk-back: constructor injection via Protocols; no DI container — R-031 / ADR-027 (2026-07-08).**
  The `dependency_injector`-based `DependencyContainer` (~215 LOC) plus
  its reflection-based `service_wiring.py` were deleted. Handlers now
  receive their repository as a constructor parameter typed against a
  `Repository` Protocol in `dora_api/infrastructure/ports.py` — 175
  handler `__init__` signatures rewritten, ~200 `get_container().inject(X)`
  callsites rewritten to `X(SqlAlchemyRepository())`. Test seams are now
  the constructor itself: three tests that previously did `patch.object(
  handler, "repository", stub)` now pass the stub through the ctor.
  `dependency_injector` dropped from requirements. Reflection-based
  handler wiring is gone → the boot-time assertion FU-457 asked for is
  dissolved by construction (no reflection surface left to protect).
  This is a Python-idiomatic pattern: structural `typing.Protocol`
  interfaces, explicit wiring at the router/app-factory edge, no
  container ceremony. The .NET-flavoured `I`-prefix nominal interfaces
  + generic-alias name mangling that the old container relied on are
  now discouraged for new code — see [[ADR-027]] for the rationale
  walk-through and when a real seam (auth, email transport, push, LLM
  client) will earn its own Protocol.
- **`POST /recipes` is now a unit of work — FU-456 (2026-07-08).**
  The recipe-create handler used to commit 5 times (recipe → sections
  → tags → steps → step-images). A validation failure on tags or steps
  left a partial recipe row + sections behind — the recipe would show
  up in the cookbook missing the sub-part the caller was trying to add.
  Now every interior commit is replaced with an explicit `flush()` (so
  downstream FK-referencing inserts still see the recipe row) and one
  `save_changes()` runs at the end of the success path. Any validation
  ValueError inside the handler returns 400 and rolls back everything;
  no partial recipe persists. Error-branch responses drop `new_recipe_id`
  — pre-refactor that id named a committed partial row; post-refactor
  no row exists to name. 3 new e2e tests in
  `tests/e2e/dora_api/test_create_recipe_unit_of_work.py` pin the
  invariant (invalid tag → rollback, invalid step-parent → rollback,
  happy path → single commit). Full test suite 828 pass, 2 pre-existing
  unrelated fails. The sweep of the other ~20 multi-commit handlers is
  tracked as FU-512.

### Changed
- **R-029 (hide, don't nag) app-wide sweep — FU-500 (2026-07-08).**
  The one live R-014-shaped offender still in the app — the
  Product Search entry in the main navigation — now **hides** when the
  admin hasn't configured a `product_search_url`, instead of rendering
  disabled with a "Not set up yet — set the URL in Settings → System →
  Features" tooltip. Admins configure the URL on the settings screen
  that owns the field; nowhere else advertises the not-set-up state.
  `MenuButtonProps` shed its now-dead `disabled` / `disabledTooltip`
  fields and both menu-button components lost the disabled render
  branch, so no future nav entry can carry a "here but disabled" shape.
  Nine `R-014` comment references across `useFeatureFlags.ts`,
  `usePushSubscription.ts`, `models/auth.ts`, `AssistantSettings`,
  `NotificationsSettings`, `VoiceSettings`, `StockItemDetailPage`
  relabelled to R-029 (still valid carve-outs — the settings screen
  that owns the config). Eight mislabelled `R-014` tags on lifecycle,
  state-hydration, swallow-error, and calm-empty-state comments were
  removed or relabelled with an explicit "distinct from R-029" note.
  `ENGINEERING_STANDARDS.md` ADR-002 gains a Presentation line
  re-affirming hide-when-off + a "See also: R-029 / ADR-025"
  cross-reference. Purely a presentation refactor — no functional
  behaviour changes beyond the Product Search nav flip.

### Changed
- **Base-component sweep: 40 raw `<q-btn>` sites migrated to
  `<BaseButton>`; `BaseButton` gains a `filled-icon` variant + optional
  `color` prop — FU-504 (2026-07-08).** The FU-424 senior-review audit
  had left ~54 raw `<q-btn>` uses across 16 files as the last
  base-component adoption residuals, plus one open design call on
  whether `BaseButton` should cover the "unelevated coloured icon
  button" shape (RecipeCard's chef-hat toggling primary/warning was
  the marquee case). Both closed in one sweep: `BaseButton` picks up
  a **`filled-icon`** variant (`unelevated round dense`, primary by
  default) and an **optional `color` prop** that overrides the
  variant's default color when set — so `variant="icon"` and
  `variant="filled-icon"` can now carry a dynamic `:color=` binding
  without callers reaching for raw q-btn. 40 sites migrated across
  `RecipeCard`, `ScanOverlay`, `DoraChat`, `MyProductsPage`, and 6
  settings pages; 10 raw sites deliberately kept as documented
  carve-outs (accent-palette CTA on Help, Quasar-secondary outline
  buttons on timezone/locale settings, `type="a"` anchors, dynamic
  positive/warning outlines on ShoppingListDetail, and StocktakeRunner's
  labeled-dynamic-color change-level button with its custom stacked
  children). Purely a componentisation refactor — no behavioural
  change, no styling delta beyond the intended visual unification of
  MyProductsPage's empty-state CTA to the standard unelevated primary.

### Changed
- **Import templates: example row is now dict-keyed + boot-fails on
  drift — FU-350 (2026-07-07).** `ImportTemplate.example` changed from
  a positional `tuple[str, ...]` (silent misalignment if `TARGET_FIELDS`
  ever reordered or grew) to a `dict[str, str]` keyed by field name.
  The CSV writer projects the dict through `headers` at emit time, so
  reordering a column reorders the emitted example automatically and
  missing keys emit as empty cells (never misaligned under the wrong
  header). New `_validate_import_templates` module-load helper crashes
  the API at boot if a template drifts — duplicate section, stale
  example key, header set out of sync with the commit handler's
  expected fields, or a section the commit path doesn't understand.
  A new `_COMMIT_KNOWN_SECTIONS` map is the one place that names what
  the commit handler processes, so registering a template for a
  new section without wiring the handler fails loudly at boot instead
  of shipping a broken CSV.

### Changed
- **List-page state (meal-plan picker search, shopping-list-detail line
  grouping) now survives navigate-away-and-back within a session —
  FU-354 rollout (2026-07-07).** R-026 (`useListState`) was previously
  applied to Stock Overview, Cookbook, and My Products; this rollout
  covers the meal planner's picker `recipeSearch` and the shopping list
  detail's line `groupBy` toggle. Navigate away to a recipe and back →
  the picker still has your search string; navigate away from a
  shopping list to another surface and back → the grouping mode is
  still what you set. Sign-out clears every persisted scope (FU-355);
  a full page reload also clears them (module-scope Map wipes with the
  bundle). The remaining pages named in FU-354 (Shopping Lists overview,
  Stocktake, Rotating Sets, Users Admin, Stores, API Access) were
  surveyed and skipped — none of them carry filter/search/sort state
  worth persisting today; R-026 is the rule going forward when any of
  them grows one.
- **Sign-out and 401-recovery both clear per-page filter/search/sort
  state — FU-355 (2026-07-07).** `useListState`'s module-scope Map
  used to persist across `logoutAsync` (which is a soft router push,
  not a full reload) and across the silent `handleSessionExpired`
  interceptor path. On a shared device the next user could inherit the
  previous session's list-page UI shape. Both handlers now call
  `clearAllListState()` (which is the escape hatch the FU-355
  originating unit shipped for exactly this hook) — the fallout was
  minor (per-page view knobs, not sensitive data) but the close is
  honest either way.
- **Meal-plan Templates drawer now owns per-template CRUD; the dedicated
  page is Rotating Sets only — FU-308 (2026-07-07).** The
  `/meal-plans/templates` page shipped before the R-Phase 5 Templates
  drawer and had been carrying redundant per-template CRUD (rename /
  clone / delete). All three actions now live in the drawer — **Clone**
  folded in as a new icon-button beside Apply / Rename / Delete on each
  row — and the drawer picked up a footer link **Manage rotating sets →**
  so the sets page stays discoverable from where users manage individual
  templates. The `/meal-plans/templates` page itself was narrowed to
  Rotating Sets only, retitled **Rotating template sets**, with a caption
  pointing users at the drawer for per-template actions. Sets stayed on a
  page (not a drawer sub-view) because a multi-template ordered list with
  reorder controls doesn't fit gracefully in a 440px drawer; that call
  matches the FU's "keep the page as the heavy management screen" branch
  for sets and its "fold into the drawer" branch for templates. The
  dead `goToManageTemplates` helper in `useMealPlanner` — a leftover
  from the retired Direction-B planner draft — was dropped in the same
  pass; the drawer's own footer button covers the nav.
- **"Show all slots" toggle on the meal planner now survives a reload —
  FU-306 (2026-07-07).** The de-sprawled meal-planner default is "used
  slots only" — the toggle that reveals every household slot per day used
  to reset back to that default on every page load. It now persists to
  `localStorage` as a per-device view preference (`mealPlanShowAllSlots`
  key, `'0'` / `'1'` values). Wrapped in `try/catch` so private-mode
  Safari / quota-exceeded environments degrade to the previous
  session-local behaviour rather than throwing. Household-scoped sync
  across devices (via a `User.Preference` column) is available as a
  future graduation path if a real user asks for it; for now, the toggle
  is a per-device view choice, not a household preference.

### Security
- **Assistant prompt-injection + input hardening — FU-515 (2026-07-08).**
  Closed the remaining medium/low findings from the auth-&-assistant security
  audit. The Dora AI assistant now (a) tells the model, in its system prompt,
  that anything returned by a tool is untrusted **data** and must never be
  followed as instructions — the defence against a scraped product name that
  says "ignore your instructions…" (matters once real merchant data flows in),
  and strips control bytes from tool output; (b) sanitises the page-path the
  client reports before putting it in the prompt (first line, path-safe
  characters, length-capped) so it can't smuggle instruction-shaped text; and
  (c) rejects absurd tool arguments at the boundary (e.g. an assistant request
  to push an item's expiry by more than ~10 years). The audit's other items
  were either already fixed (assistant rate limits + input caps; the verified
  change-email UI; client/server password rules aligned to 8+ characters) or
  accepted as reasonable for a self-hosted single instance. No user-facing
  behaviour change on normal use.

### Fixed
- **Dora Basic mode: two assistant-parsing fixes surfaced by the new eval suite — FU-390 (2026-07-08).**
  (1) Typing "put milk **on** my list" now correctly adds *milk* — the parser
  only stripped "**to** my list" before, so it treated "milk on my list" as the
  item name. (2) Asking for a recipe with any qualifier — "I need a vegetarian
  recipe", "italian recipes", "any breakfast ideas" — now routes to recipe
  search instead of the generic fallback (Basic mode had no bare "recipe"
  trigger). Both are Basic-mode (no-LLM) improvements.
- **Retired assistant tool `set_primary_list` fully removed — FU-390 (2026-07-08).**
  The tool had been retired (the primary list is inferred from draft status
  now) but was still advertised to the language model and listed on the Dora
  help page, so the model could "call" it and silently do nothing. Removed the
  dead tool schema, help-page entry, and type.
- **Onboarding "seed starter items" no longer 500s — FU-514 (2026-07-08).**
  `POST /api/onboarding/seed-items` (used by the first-run flow to create a
  batch of pre-located starter stock items) crashed with a server error on
  every call: it still passed an `image` field to `StockItem`, which was
  dropped in FU-508. Removed the stale field; the endpoint creates items
  again. (Leftover from the FU-508 stock-item-image removal that missed this
  one construction site.)
- **Recipe ingredient drag-and-drop landed one row above where the user
  dropped when dragging downwards — FU-161 partner-bug (2026-07-07).**
  The ingredient reorder in `RecipeDetailPage.vue` was computing the
  target's index **after** the source had already been spliced out of
  the array — so when the user dragged an ingredient *down* the list,
  the target's index had shifted down by one and the source landed one
  row above the drop point. Same failure mode as feedback L414 on
  shopping lists (fixed in P6-01 Chunk 6); the shopping-list fix was
  verified working in the same session and its "capture both indices
  before any mutation" pattern is now applied identically here. Recipe
  step reorder (`RecipeStepsEditor.vue`) was already on the correct
  pattern. Section-move (dropping an ingredient from Section 1 onto a
  row in Section 2 to move it) still works — the section-copy happens
  atomically with the reorder.

### Removed
- **Meal planner Direction B page + A/B toggle — FU-304 (2026-07-07).**
  After living with both layouts for ~2 weeks, **Direction A** (the
  de-sprawled vertical carousel with slot-rows-per-day) is now the sole
  meal-planner surface. Direction B (the desktop week-board grid with
  slot-as-tag rich cards + sticky consequences bar + pinnable picker
  drawer) is retired. Deleted: `MealPlansBoardPage.vue`,
  `MealPlanWeekBoard.vue`, `useMealPlannerView.ts` (localStorage
  persistence helper). Removed from `MealPlansOverview.vue`: the
  desktop `BaseSegmented` List/Grid toggle, the mount-time restore-Grid
  redirect, and the associated imports. The `/meal-plans/board` route
  now redirects to `/meal-plans` so any stale bookmark or deep-link
  lands cleanly on the surviving planner. `MealPlanRichCard.vue` is
  preserved — it's still consumed by `MealPlanMobileFocus.vue` (shared
  mobile focus) — and the server-side `MealPlanEntryDto` enrichments
  (`has_image`, `cook_time_minutes`, `cuisine_name`, `category_name`)
  are kept for the same reason. Desktop A continues to render meals as
  the flat `MealPlanEntryChip`.

### Changed
- **Import templates: inline `#` hint row explaining the illustrative
  example values — FU-349 (2026-07-07).** The downloaded stock-items
  import template now carries an inline `#`-prefixed hint row after the
  example: *"# example values are illustrative — replace them, and use
  your own level/location/group names (see Settings → Kitchen setup)."*
  Users on customised installs — anyone who renamed a StockLevel,
  StockLocation, or StockGroup in Settings → Kitchen setup — now see
  a note explaining why the placeholder names ("In stock", "Pantry",
  "Grains") may not match their install, instead of hitting a row-level
  validation failure on first re-upload. The spreadsheet parser now
  filters `#`-prefixed rows on ingest (both `.csv` and `.xlsx`), so a
  user who re-uploads the untouched template — or keeps the hint row
  alongside their real data — doesn't accidentally import a stock item
  named "# example values are illustrative…". Row 0 is always preserved
  (headers stay headers); only data rows whose first cell begins with
  `#` are dropped.

### Added
- **"Draft my shop" one-click dashboard card — FU-351 (2026-07-07).** The
  legacy P6-10 self-drafting-weekly-shop entry point that had been
  sitting on top of the existing `/auto-generate` engine as an
  unadvertised checkbox modal now has a first-class home. A new **Draft
  this week's shop** dashboard card in the `act` zone (between
  Attention and Suggestions) exposes a one-click **Draft my shop**
  button. Defaults: **meal plan for the next 7 days** (rolling from
  today; already-consumed entries are filtered), **low + out of stock**
  items, and **flagged essentials**. On success, the SPA lands the user
  in the freshly-created DRAFT list — each line already renders the
  existing `added_via` chip ("auto: meal plan", "auto: low stock",
  "auto: essential" / "auto: flagged") so provenance is visible without
  extra chrome. Empty-input case (fresh install, no meal plan, no low
  stock, no essentials) shows an honest "Nothing to draft yet" toast
  and **no phantom empty list is created** — the `/auto-generate`
  handler now defers list creation on the create-new path until after
  candidate collection, so zero-candidate calls return
  `shopping_list_id: null` + `nothing_to_add: true` instead of leaving
  a lonely empty list in the sidebar (merge-into-existing path
  unchanged; NewListDialog always passes a `merge_into_list_id`, so
  its behaviour is untouched). Card is toggleable via the Cards menu
  like every other dashboard card.

### Changed
- **Auto-add on low: per-item toggle collapsed into a single install-wide
  3-state setting — FU-511 (2026-07-07).** The pre-existing per-item
  `Auto-add when low` toggle (a boolean column, filter chip, footer count,
  and detail-page row) is retired. Auto-add is now controlled by one
  install-wide setting at **Settings → Admin → System → Stock** with three
  modes:
    - **Off** — never auto-add on low.
    - **Essential only** (default) — fire only for items with the Essential
      flag on. Matches the pre-existing "staple you never want to run out
      of" mental model without a per-item duplicate of that concept.
    - **All items** — fire on any Stocked → Low/Out transition.

  Server owns the branching in `update_stock_item._auto_add_enabled_for`,
  which reads `AppSetting.auto_add_mode` and this item's `is_flagged`.
  The auto-add response envelope + toast are unchanged behaviourally.
  Non-preserving DB migration (`b8f2c1d4e6a9`) drops
  `StockItem.auto_add_when_low` and adds `AppSetting.auto_add_mode`.
  Removed SPA surfaces: the **Will auto-add on low** filter chip, the
  **Auto-add** footer count, and the **Auto-add when low** toggle on the
  item detail page. Also removed while touching neighbouring code: a stale
  `image=None` kwarg in `seed.py`'s StockItem construction (leftover from
  FU-508's `StockItem.image` drop) and the equivalent in the spreadsheet
  importer's raw insert.
- **Essential flag: row treatment simplified — FU-365 (2026-07-07).**
  Essential is set-and-forget, so the per-row essential-flag button was
  removed from the Stock Overview row's right cluster (`StockItemRow.vue`).
  Management is now detail-page-only. The left-edge stripe becomes the sole
  row indicator — bumped 3px → 5px and re-tinted from warning to the app's
  secondary colour so it scans without an accompanying icon. Matching
  palette changes so the concept reads as one visual family: the
  **Essential** footer count and the **Essential** filter chip both switch
  from the warning tone to the secondary tone. `PageCountsFooter` gained a
  `secondary` tone. Row alert/warn outlines (essential + low = amber;
  essential + out / expired = red) unchanged — those signal *needs-
  attention*, not *essential*.
- **Comment-hygiene sweep — FU-462 (2026-07-07).** Removed 887 prompt-ID
  (`P#`, `C-#`, `B#`, `INV-#`) and FU-NNN task-ID comments from shipped
  source across 202 files (`dora_api/`, `tests/`, `web_app/src/`). Where
  the comment carried real WHY, the substance was kept; where it was pure
  breadcrumb naming the prompt/FU that produced the code, the whole
  comment was deleted. R-008 in `docs/01_charter/ENGINEERING_STANDARDS.md`
  was hardened with an explicit close-time grep so future work can't
  reintroduce the pattern. Pytest suite still 818/818, no new type
  errors introduced.

### Fixed
- **Test-suite health restored — FU-466 (2026-07-07).** Full pytest suite
  now green (818/818). Fixed a missing session fixture in
  `test_bucket_c_secrets.py` that left the wrapping key unconfigured on
  every write-a-secret test; a stale test assumption in
  `test_recipe_is_planned.py` that picked an already-planned seed recipe
  and so couldn't observe the toggle; and an order-dependent flake in
  `test_data_router.py::test__register_barcode__against_product__lookup_traverses_via_product`
  by advancing the round-robin Product picker until it finds one with a
  linked StockItem (previously landed on an unlinked Product once earlier
  tests had consumed the linked seed rows). Most of FU-466's original
  ~41-failure spread (alerts / digest / push / stock_item / household_tz)
  had already resolved via unrelated feature work between the FU raise
  date and the fix session.

### Removed
- **Per-stock-item image feature dropped entirely — FU-508 (2026-07-07).**
  The half-built `StockItem.image` surface (upload column, `has_image` DTO
  plumbing, `/stock-items/<id>/image` bytes endpoint, thumbnail slot on the
  stock row, upload field on the detail page, "show row images" toggle in
  the stock overview, and the `show_stock_images` user preference) is gone.
  Pantry-item photos never carried much information — linked Products
  already supply the visual, and the toggle button in the toolbar was
  clutter. Migration `a4c9e1f2b3d5_20260707_drop_stock_item_image` drops
  both DB columns (`StockItem.image`, `User.show_stock_images`). Recipe
  image + user avatar image surfaces are untouched; the recipe-image
  render toggle (`show_recipe_images`) is untouched.
- **Assistant tool `seasonal_picks` removed — FU-501 (2026-07-07).** The Dora
  assistant no longer exposes a "what's in season?" tool. It was only ever
  reachable via chat (no page, no dashboard tile, no shopping-list
  integration), and the underlying `_SEASONAL_AU` table was AU-only — a
  non-AU install got wrong data with no locale fallback. Cutting was cheaper
  than localising for a low-value chat capability. Removed: the tool schema,
  handler, `_SEASONAL_AU` / `_MONTH_NAMES` / `_resolve_month` in
  [tools.py](dora_api/features/assistant/tools.py); the tool-selection
  example in [ask_assistant.py](dora_api/features/assistant/ask_assistant.py);
  the `seasonal_picks` entry in [DoraHelpPage.vue](web_app/src/pages/DoraHelpPage.vue);
  the now-unused `eco: 'mdi-leaf'` icon in [icons.ts](web_app/src/style/icons.ts).

### Added
- **Budget-aware trim on auto-generated shopping lists — FU-448 (2026-07-06).**
  Closes the P2-05 optimiser half that was deferred when the user-facing
  budget shipped. On any list where projected total exceeds the user's
  period-remaining budget, a warning banner appears with three CTAs:
  **Show what would be cut** (preview per-line with reason chip),
  **Trim to fit** (apply — cuts move to a collapsible "Deferred to fit
  budget" section, not deleted, one-tap Add back), and **Dismiss**.
  Nothing mutates on load; every mutation is a user tap. Cuts follow a
  five-tier safest-first stack — habit items with no demand, low-stock
  with days-of-cover left, buy-verdict `wait` lines, out-of-stock with
  no meal booked, then recipes/meal-plan items scheduled ≥5 days out —
  and inside each tier, highest-priced line first. Never cuts:
  essentials, meals in the next 2 days, verdict=`buy` on low/out, or
  lines under $2. Fixed seven-chip reason vocabulary frozen at trim
  time on a new `ShoppingListLine.deferred_reason` column. Self-gates
  when money features are off, no budget is set, or the list is
  already under budget. Assistant intent **"trim my shopping list to
  my budget"** proposes + commits through the same endpoint. Full
  design in `docs/04_proposals/PROPOSAL_BUDGET_AWARE_LISTS.md`.
- **FU-333 closed — Buckets C + D shipped; env-var sprawl done (2026-07-06).**
  Bucket C moves the two remaining operational secrets — the SMTP password
  and the VAPID private key — onto `AppSetting` as encrypted-at-rest columns
  (Fernet ciphertext wrapped by `DORA_LLM_KEY_ENCRYPTION_KEY`, reusing the
  FU-153 helper). Admins now enter both from **Settings → Admin → System →
  Email** and **Push notifications**; the response DTO returns only a
  `<field>_configured: bool` so ciphertext never leaves the row. Bucket D
  auto-generates the two remaining bootstrap keys (`DORA_SECRET_KEY`,
  `DORA_LLM_KEY_ENCRYPTION_KEY`) into the per-user data dir on desktop
  bundles so a double-click end-user never sees an env var — server
  self-host still sets them explicitly. Same work also closed [[FU-467]]:
  the Bucket-B env-var fallbacks (14 vars across SMTP, VAPID, Piper, email,
  audit, public URL) are gone — the resolver is a straight `AppSetting`
  projection. Migration `a3e7d2c9b5f1` adds the two new columns.
- **Batch-cooking preference now asked in onboarding — FU-041 follow-up (2026-07-06).**
  New "I batch-cook" toggle sits under the "how many people do you cook for?"
  input on the welcome step. Both are "how you cook" personal prefs and belong
  together; the batch-cooking toggle used to be Settings-only, which meant
  users who batch-cook only discovered the cook-pool ± / "N free" / shortfall
  affordances by accident. Default stays off (Charter P10 Anti-creep) and the
  Settings toggle is unchanged — the wizard just gives it a first-run
  discovery point.

### Changed
- **Onboarding split into first-user vs subsequent-user tracks — FU-041 (2026-07-06).**
  A genuine first-time setup (fresh self-host, or first user in a new SaaS
  household) always runs against an empty DB, so the seed step no longer
  branches defensively on "you already have groups/locations". First user
  walks the full path (welcome → admin → seed catalogues → first stock item →
  finish); every subsequent user walks welcome → finish only (personal prefs
  and the "here's the app" tour — no household-scoped seeding, no first-item
  nudge, no admin bootstrap). The `has_locations` / `has_groups` /
  `has_stock_items` flags — and the "You already have…" copy blocks that
  read them — are gone.

### Fixed
- **Import template CSV: UTF-8 BOM prepended for Excel-on-Windows — FU-347 (2026-07-06).**
  The downloaded `dora-import-<section>.csv` now begins with the UTF-8
  byte-order mark so Excel-on-Windows opens it in UTF-8 by default
  instead of guessing ANSI/CP-1252 and rendering any accented character
  as mojibake. Round-trip is unaffected — the upload-side parser
  already strips the BOM before decoding.

### Changed
- **Recipe-picker inline-create toast copy — FU-319 (2026-07-06).** The
  "Create '<typed>'" no-option row in the recipe ingredient picker now
  toasts `Added "<name>" to your pantry.` instead of the older
  jargon-y `Created stock item "<name>".` — because the inline-created
  item persists even if the recipe save is cancelled, the copy now
  hints at where the user will see it next.

### Added
- **Targeted (?) hover-help chips on ~25 confusing controls — FU-044 (2026-07-06).**
  Non-obvious metrics and Dora-specific terminology explained in-context
  without a toggle or overlay engine: Kitchen health score, Savings
  captured range, Year-over-year card, Meals-worth metric, Alerts
  Needs-action/FYI distinction + per-kind tier override, meal-plan
  Shortfall, Available meals / Unallocated, Cookable-now filter,
  Sous Chef + hands-free mic (extended existing tooltips), Stock
  filter chips (Essential / Auto-add on low / Open / Needs check),
  Stocktake cadence + Push-3-days button, Finish-&-restock + Plan-day
  buttons, Above-usual and Your-usual price chips, Select-on-deal bulk,
  Multipack pack count disclosure, Compact deals-email format, and the
  Assistant AI-mode "tool-able requests" description. A lightweight
  sibling to the Help page and assistant, not a replacement. Some audit
  targets were already covered by nearby captions/help text or had been
  renamed since the audit (Cookable-tonight dashboard card is now
  "Next to cook"); those were skipped rather than duplicated. Overlay
  mechanism from `PROPOSAL_HELP_OVERLAY.md` remains parked.
- **Currency & locale for non-AU installs — FU-043 (2026-07-06).** Dora is now
  usable outside Australia. Two new install-wide settings on `AppSetting`:
  `currency` (ISO 4217, e.g. `USD`, `EUR`, `AUD`) and `locale` (BCP-47, e.g.
  `en-US`, `de-DE`, `en-AU`). Every money render across the app — Dashboard
  (budget, savings, spend by store, pantry value, best deals), Reports (all
  charts and totals), ShoppingListDetail (line prices, totals, offer chips),
  PriceHistory (chart axis + tooltip, "all-time low", price-alert labels),
  StockItemDetail (offer prices, price observations, purchase-event lifecycle),
  RecipeDetail (estimated cost), YourPricesWidget, PriceEntry, MoneySettings,
  ProductChip, QuickAddSheet, SubscriptionsPanel, MyProductsPage — now routes
  through one shared `Intl.NumberFormat` wrapper (`useMoney.ts`). Money-input
  prefixes read the same currency symbol so `q-input` fields flip atomically
  when an admin changes the setting. Voice input's speech-recognition locale
  derives from the same setting (fallback: browser locale, then `en-AU`), so a
  German-locale install gets German voice recognition instead of Australian
  English. New admin page at **Settings → Admin → System → Currency & locale**
  with validation, a live preview, and a "Use this device" locale detect.
  Assistant copy generalised — `APP_OVERVIEW` no longer name-drops "Coles,
  Woolworths, IGA, Aldi"; the `search_products` and `set_primary_list` tool
  descriptions read for any merchant. Household-scoped by design (one currency
  per install); if Dora ever goes multi-tenant SaaS the setting moves onto
  whatever household row lands then. Layer C (full UI translation) stays
  deferred per the proposal.
- **Operator config in Settings — FU-333 Bucket B (2026-07-05).** Twelve
  `DORA_*` env vars that were operational config (not bootstrap, not
  secrets) are now editable rows on `AppSetting`: SMTP host/port/
  username/from/use-TLS, VAPID public key + subject, Piper binary +
  bundled voice dir + legacy voice override, install-wide email
  toggle, audit retention days, and public URL. A migration backfills
  each column from the corresponding env var if set, so existing
  installs keep working without an admin touching anything on
  upgrade. Four new focused pages land under Settings → Admin →
  System: **Email**, **Push notifications**, **Voice**, **Hosting** —
  each following the established per-page pattern from the earlier
  System split. The two Bucket-C secrets (`DORA_SMTP_PASSWORD` and
  `DORA_VAPID_PRIVATE_KEY`) stay env-only and are rendered
  reveal-and-disabled in the UI with a caption pointing at the
  Bucket-C follow-up. During the deprecation window the env vars
  still work as fallbacks (resolver in
  `features/app_settings/operational_config.py` prefers the row when
  set); a follow-up tracks their eventual removal. Operator
  onboarding shrinks from "configure 19 env vars" to "set 2 bootstrap
  vars + configure the rest in Settings."
- **Per-user rate limits on the assistant surface — FU-458 (2026-07-04).**
  Defence-in-depth against a runaway loop (accidental or malicious)
  burning upstream LLM tokens on an authenticated session. Three
  endpoints gained limits, all bucketed by `session.user_id` (falling
  back to IP when unauthenticated):
  - `POST /assistant/ask` — **20/min** (LLM round-trip, most expensive)
  - `POST /assistant/act` — **60/min** (commit-add, no LLM)
  - `POST /assistant/confirm` — **60/min** (Tier-2 action dispatch)
  
  Failures return an RFC 6585 §4 shaped 429 with a `Retry-After`
  header, matching the auth surface's shape. The existing `rate_limit`
  helper in [`auth_helpers.py`](dora_api/infrastructure/auth_helpers.py)
  gained an optional `subject` argument so a shared household IP
  doesn't count multiple users against the same bucket — pre-auth
  callers (login/register/verify) keep the historical per-IP
  fallback via `subject=None`. Also fixed a doc/code drift on
  `/assistant/probe`: its comment claimed per-user bucketing but the
  code was per-IP; now that the helper supports it, the code matches
  the comment. New pytest [`test_rate_limit_subject.py`](tests/test_rate_limit_subject.py)
  locks the two-line behavioural contract (subject isolation +
  IP-fallback back-compat) so it can't silently regress. Full
  backend suite 303/303 green.

### Fixed
- **SQLite `text() + str(uuid) IN :ids` regressions — FU-463 (2026-07-04).**
  Latent bug on SQLite self-host deployments (Postgres was unaffected).
  Two hydration passes used raw `text()` with a string-uuid IN clause
  that never matched the `UUIDType` column's BINARY(16) storage on
  SQLite, silently returning zero rows:
  - [`get_stock_items.py::_hydrate_linked_product_count`](dora_api/features/stock_items/get_stock_items.py) — every stock-item DTO's `linked_product_count` was `0` regardless of the actual link-table contents.
  - [`get_recipes.py::_compute_estimated_cost`](dora_api/features/recipes/get_recipes.py) — every recipe's `estimated_cost` was `None` regardless of whether its ingredients had priced products.
  
  Rewrote both as ORM `select()` against `db.metadata.tables[…]` so
  SQLAlchemy Core adapts UUID bindings correctly on either engine —
  same idiom `_hydrate_has_image` already uses since FU-171. Verified
  by executing the rewritten queries against a real SQLite database
  under `app.app_context()`. `pytest` 298/298 green.

- **Auto-add-when-low now fires on Low transitions again — FU-464 (2026-07-04).**
  Real user-visible bug that landed silently with the 2026-07-02
  Sufficient-band collapse. The auto-add hook was gated on a raw
  sequence literal `>= 2` — under the OLD 4-band scheme that was
  Low-or-Out, but the collapse renumbered levels to 0/1/2 (Stocked /
  Low / Out), so `>= 2` meant **Out only**. An item flagged
  `auto_add_when_low` and set from Stocked → Low was NOT auto-added
  despite the whole point of the setting.
  Replaced the two sequence-literal comparisons in the auto-add hook
  with `needs_restock(level)` from `stock_status.py` (R-003 — one
  server-side authority for "restock-needing"). The predicate returns
  True for both Low and Out, False for Stocked and None, so the hook
  now fires on the intended Stocked→Low, Stocked→Out, and None→Low/Out
  transitions. Backend pytest 298/298 green; auto-add coverage is
  e2e-only, will be re-verified via the FU-315 auto-add block on the
  next browser walk.

### Changed
- **Stocktake housekeeping — R-003 alerts drift fixed, dead heatmap deleted, deprecated columns dropped — 2026-07-04.**
  Closes the stocktake redesign trilogy properly. A survey after Chunk 3
  found two lingering callers of the "deprecated" per-item cadence
  column: the `stocktake_overdue` alert kind (bell + Alerts page +
  assistant tool filter) and the location "attention" heatmap. Both
  were computing overdue from the old per-item threshold, meaning the
  bell could disagree with the runner as soon as Auto self-tuning
  promoted a fast mover — R-003 drift shipped in Chunk 1's own tail.
  - **Alerts rewired to the queue's authority.** New shared helper
    `stocktake.resolve_overdue_map` factored out; both the queue
    endpoint and the alerts feed consume the same
    band-resolved map. The bell + runner now surface identical
    sets of items by construction.
  - **Dead heatmap system deleted.** `locations/attention.py` gone
    entirely; `attention_score` + `attention_reasons` +
    `primary_reason` removed from the location tree DTOs and the
    stock-item detail DTO; matching `AttentionReasons` type +
    `summarizeReasons` / `attentionColor` / `attentionBackground`
    helpers removed from the SPA models. Zero external consumers —
    it was computed on every location fetch but never rendered.
  - **Deprecated columns dropped.** Alembic revision
    `e5c8b3a1f4d2` drops `StockItem.days_until_stocktake_alert`
    and `AppSetting.default_days_until_stocktake_alert`.
    Symmetrical downgrade rehydrates both at historical defaults
    if needed. All backend + SPA callers pruned in the same pass
    (create/update/detail stock item, onboarding, spreadsheet
    import, seed, settings get/update, entity + table mappings,
    two SPA type files).

  Backend pytest 297/298 pass (the one failure is pre-existing
  FU-455, unrelated). `vue-tsc` clean. No UX change — the two
  surfaces now agree, which they should have been all along.

- **Stocktake redesign — Settings + Stock Overview surfacing (Chunk 3) — 2026-07-04.**
  The peripheral half of PROPOSAL_STOCKTAKE_MODE §7 + §8. Closes the
  redesign trilogy — the engine (Chunk 1), the runner (Chunk 2), and
  now the surfaces the user actually finds it from:
  - **New Settings → Stocktake page.** `q-btn-toggle` cadence selector
    (Weekly / Fortnightly / Monthly, default Fortnightly) and a
    `q-toggle` for Auto self-tuning (on by default — "auto = speed").
    Eager-saves on change. Lives at
    `/settings/admin/system/stocktake` under the System nav group,
    beside Timezone / Alert thresholds / AI assistant / Features.
  - **Old "Default stocktake reminder" section removed** from Alert
    thresholds — the numeric-days input backing
    `default_days_until_stocktake_alert` is superseded by the band
    system (Chunk 1 §7). Column stays in the DB for now (deferred drop).
  - **Stock Overview "Needs check" quick-filter.** New FilterChip
    alongside Essential / Auto-add / Open / Needs-attention. Narrows
    the visible rows to items currently in the stocktake queue
    (server-owned overdue set — R-003).
  - **Stock Overview row pulse outline.** Items in the stocktake queue
    get a 2-second brand-accent pulse around their **stock-level
    button**, matching the toolbar's Stocktake attention glow. Passive
    discovery — you notice a due item without opening the runner.
    Respects `prefers-reduced-motion` (static outline instead of the
    animation).

  Server signal shape: reused the existing `GET /stocktake/queue`
  endpoint — the Overview's queue fetch bumped from `limit=1` → `500`
  (the server cap) so the count + the full ID set arrive in one
  round-trip. No new endpoint. `vue-tsc` clean.

- **Stocktake mode redesigned (Chunk 2: SPA runner rebuild) — 2026-07-04.**
  The user-visible half of the
  [stocktake redesign](docs/04_proposals/PROPOSAL_STOCKTAKE_MODE.md).
  - **No more landing page.** Tapping Stocktake drops straight into
    the focused runner. The old "N items need a check" landing is
    gone — the count lives in the runner's progress strip and adds
    no value up front. Empty state ("You're all caught up.") is a
    state of the runner. Resolves the SK-1 (Refresh) and SK-2
    (top-of-queue text) feedback by removing the screen that hosted
    them. Legacy `/stocktake/run` sub-route redirects to
    `/stocktake` so bookmarks / worklog links still work.
  - **New button layout.** Two big primaries — **Still correct**
    and **Change level** — side-by-side. The Change-level button
    is **tinted to the current level's colour** with a small
    "(change)" hint underneath, so it doubles as the level readout
    (resolves SK-8/SK-9). Three smaller secondaries below:
    **Skip** (session-only "later today, keep reminding me"),
    **Push 3 days** (fixed snooze — makes no truth claim about the
    stock, so does NOT stamp `last_checked_at`), and **Mute**
    (danger-ghost styled; confirmation dialog before firing;
    reversible only from the item's detail page).
  - **Dropped:** the standalone Out-of-stock button (Out is a level
    in the picker), all keyboard shortcuts + their `(1)/(2)/s`
    labels (SK-4, SK-10), and the per-item Add-to-list button.
  - **Level picker** renders a
    [StockLevelDot](web_app/src/components/stock/StockLevelDot.vue)
    next to each level name so the picker matches the Stock
    Overview visual language.
  - **`(?)` help affordance** in the runner topbar opens a plain-
    English "How stocktake works" dialog explaining all five verbs
    plus a note on cadence bands / Auto self-tuning.
  - **Completion screen** shows five counters (checked / changed /
    skipped / pushed / muted). If any items were flipped to Low or
    Out during the session, an inline **"Add to list…"** button
    adds the whole set to any active shopping list in one action
    (resolves SK-7 — the old per-item Add-to-list button is
    gone). Uses the same picker + bulk-add path the Stock Overview
    bulk-add flow uses.

  `vue-tsc --noEmit` clean (only pre-existing Capacitor typings
  errors from the P8-10 native scaffold on this dev box). Backend
  unchanged.

### Added
- **Stocktake queue engine rebuilt (Chunk 1 of the redesign) — 2026-07-04.**
  Backend-only chunk; the runner UX rebuild is Chunk 2. The queue's
  "who / how often / snooze" is now driven by
  [PROPOSAL_STOCKTAKE_MODE](docs/04_proposals/PROPOSAL_STOCKTAKE_MODE.md):
  - **Engagement gate — one question.** An item enters the queue only
    when it shows a *current* sign the user manages it (in stock /
    opened / adjusted-in-60d / on-a-shopping-list-in-60d). The
    per-item `is_flagged` / `auto_add_when_low` flags are **no
    longer** gate signals — a flag never forces a not-actually-kept
    item into the queue (fixes "essential + never bought doesn't
    make sense"). The two history signals gained a **60-day window**
    so an item touched a year ago no longer nags forever.
  - **Cadence bands + self-tuning.** Weekly (7d) / Fortnightly (14d)
    / Monthly (30d) resolved server-side from a global default
    (**Fortnightly**) + a new **Auto** self-tuner (**on by default**;
    reads each item's trailing-90d level-change history: ≤10-day
    avg gap → Weekly, ≥25-day → Monthly, middle → Fortnightly).
    Low/Out in the last 14 days bumps one band faster. Essential
    (`is_flagged`) bumps one more, clamped at Weekly. Replaces the
    deprecated per-item `days_until_stocktake_alert` dial.
  - **Grace period for new items.** The `9999` never-checked
    sentinel is retired. Overdue baseline =
    `COALESCE(last_checked_at, stock_level_last_updated)` — "when
    did the user last touch this?" — so a freshly-added stub gets
    exactly one band of grace before it surfaces.
  - **Push (3-day snooze).** New `POST
    /api/stock-items/{id}/snooze` sets `snoozed_until = now + 3d`;
    queue excludes anything with `snoozed_until > now`. Push
    deliberately does **not** stamp `last_checked_at` — it makes
    no truth claim about the stock, so it must not corrupt the
    verification audit. A subsequent Check / Set-level clears the
    snooze automatically.
  - **Two new install-wide settings** — `stocktake_default_cadence_
    band` and `stocktake_auto_tuning_enabled` — exposed on
    `GET`/`PATCH /api/app-settings`. The Settings UI wires them in
    Chunk 3.

  New alembic revision `d1f9c3a8b2e4` also **merges the two open
  heads** (`a3e8b1f6c2d9` + `c5a8e1f7d3b2`) so the DB tracks a single
  linear history again. Migration adds `StockItem.snoozed_until`
  (nullable, indexed) + the two `AppSetting` columns. Non-null
  columns ship with server-defaults so existing rows adopt sensible
  values on upgrade. 18/18 new pytest green
  (`tests/test_stocktake_cadence.py` covers the pure resolver end
  to end); wider suite regression-clean (one pre-existing
  `test_buy_verdict.py` failure logged as [FU-455](DORA_FOLLOWUPS.md)).

### Added
- **Bulk "Log waste…" on Stock Overview — (2026-07-04).** The Stock Overview
  bulk-select bar gains a **Log waste…** action alongside "Add to list…",
  "Remove from list…", "Move location", and "Restock". Select N items, pick a
  single reason from the existing reason-picker dialog, and every selected item
  gets its own reason-only `StockItemWasteEvent` (Charter P2). Any selected item
  that had an expiry date has it cleared, matching the single-item row action.
  One summary toast with a batch **Undo** that restores every event + expiry.
  This is the anchor for the "expiry+waste stays on Stock Overview, not
  stocktake" split from the FU-226 stocktake redesign — one surface for waste,
  now with efficient bulk. R-001 reuse of `MarkAsWastedDialog`; no new dialog
  or component. `vue-tsc` clean.

### Changed
- **StoresSettings logo upload adopts the shared image picker — FU-335
  (2026-07-04).** The store-logo file-picker in Settings → Stores was
  the last remaining Quasar `q-file` upload; every other image-upload
  site (recipes, stock items, shopping-list receipts, recipe steps)
  already routed through `ImageSourcePicker` for the "Take photo vs
  Choose image" split. Migrated the dialog to the shared picker,
  dropped the local `MAX_BYTES = 6_000_000` + `ACCEPT` constants in
  favour of the install-wide policy that `processImageFile` reads
  (R-003), and swapped the `@rejected` toast for an inline caption
  under the buttons (same shape as elsewhere). The `StoreLogo` swatch
  preview + "Remove existing logo" button are unchanged. `vue-tsc` clean.

### Fixed
- **BuyVerdictCard one-tap actions now fully wired — FU-454 (2026-07-04).**
  The card's `mark_stocked` (wastes-often + stocked → "Already stocked")
  and `remove_from_list` (already on an open list → "Remove from list")
  variants previously emitted the intent but the handler was a silent
  no-op / a "use the row controls" toast — quietly-broken UX (Charter
  P3). New shared composable
  [useBuyVerdictActions.ts](web_app/src/composables/useBuyVerdictActions.ts)
  exposes `markStocked(stockItemId)` (flips to the Well-Stocked band via
  the same `updateStockLevelAsync` seam the row dropdown uses;
  invalidates the buy-verdict + pantry-belief caches; positive toast) and
  `removeFromAllOpenLists(stockItemId)` (fans out to every non-`done`
  list via `useShoppingListActions.removeFromAllLists`). Wired in all
  three card mounts — Stock Overview row card, Stock Item Detail card,
  Shopping-list line card. `vue-tsc` clean.

### Changed
- **Password policy realigned to NIST SP 800-63B / ISO/IEC 27002:2022 §5.17
  (FU-442, 2026-07-04).** `MIN_PASSWORD_LENGTH` dropped from **10 → 8**
  (matches the standard minimum and the user's original request); the
  forced letter-and-digit composition rules were **removed** (NIST retired
  these in 2017 because they push users toward low-entropy substitutions
  like `Password1!`); a bundled breach-list of the top ~60 known-
  compromised passwords is now rejected outright (`password123`,
  `qwerty123`, `letmein1`, `dashydora`, etc., case-insensitive), with a
  friendly message directing users to pick something less common.
  **No admin toggle** — the policy is install-wide and non-overridable,
  which is what makes the ISO/NIST citation honest. Frontend copy on
  SetupAdminPage, LoginPage, ResetPasswordPage and AccountSettings
  refreshed to match ("at least 8 characters, a passphrase works well");
  AccountSettings' stale `>= 4` client rule tightened to `>= 8`.
  Rate-limiting on `auth.login` (5/min) already covered the NIST §5.2.2
  throttle requirement. Werkzeug scrypt/pbkdf2 hashing sidesteps bcrypt's
  72-byte truncation trap, so the 255-char field cap is real. Full
  policy + citations live inline in [auth_helpers.py:43-108](dora_api/infrastructure/auth_helpers.py).

### Added
- **Native mobile app scaffold — Android build + iOS Xcode project
  (P8-10, 2026-07-04).** Capacitor 8 wraps the Quasar SPA for iOS
  and Android; **one codebase, no SPA fork**. Android platform is
  fully scaffolded (`web_app/src-capacitor/android/`) with adaptive
  launcher icons regenerated from the Dora mascot, `#F5C462`
  background swatch, and `INTERNET / CAMERA / WAKE_LOCK / VIBRATE /
  POST_NOTIFICATIONS` permissions declared. iOS platform is
  scaffolded (`src-capacitor/ios/`) but never built — needs a Mac
  session. Full build instructions in
  [packaging/BUILD_NATIVE.md](packaging/BUILD_NATIVE.md); Play Store
  draft copy in [docs/04_proposals/PLAY_STORE_LISTING.md](docs/04_proposals/PLAY_STORE_LISTING.md).
  Native gets three functional additions along with the shell:
  (1) a **runtime-configurable backend URL** — new
  `services/api/backendUrl.ts` reads / writes via
  `@capacitor/preferences` on native and `localStorage` in the
  browser, the axios request interceptor prepends it per-request so
  changing instances doesn't require a rebuild, and a first-run
  `/setup/backend` gate blocks every route until the user picks a
  URL. Settings → About gains an in-place **Change instance URL**
  affordance (also usable in the browser to override the env
  default). (2) A **screen wake lock** composable
  (`composables/useWakeLock.ts`, standard `navigator.wakeLock`
  API) keeps the display on during cook mode and while a shopping
  list is in `status === 'shopping'` (shop mode). (3) A Capacitor
  boot file (`src/boot/capacitor.ts`) hides the splash screen
  cleanly and loads the persisted backend URL before router mounts.
  Push notifications intentionally still travel over VAPID web push
  today — Android WebView doesn't expose the Push API, so on native
  the toggle stays 'unsupported' until a future prompt wires
  `@capacitor/push-notifications` + FCM.

- **⭐ The Dora Score — one honest kitchen-health number
  (P8-08, 2026-07-04).** A new **Kitchen health** card at the top
  of the dashboard's Your Kitchen zone shows a single 0-100
  composite over a rolling 30-day window, plus a trend arrow
  (score vs. the same 30-day view 7 days ago). Under the number,
  five per-signal mini-bars break the composite down: **Waste**
  (from `StockItemWasteEvent`), **Budget** (reuses the
  `/budget/status` calculation), **Freshness** (% of expiry-
  tracked items not past their date), **Run-outs** (unplanned =
  `ConsumptionEvent` hit Out AND the item wasn't on any active
  shopping list), **Stocktake** (% of items checked in the last
  30 days). Signals with no data are *excluded* from the mean,
  never zeroed — a household without a budget set gets a
  four-signal score, not a fake fifth (Charter P3 Honest). Every
  weak component links to the feature that improves it — waste
  tab, preferences (budget), expiring stock filter, shopping
  lists, stocktake — no nag copy anywhere (Charter P1 Effortless).
  New endpoint `GET /api/dashboard/dora-score`. Card can be hidden
  / reordered via the dashboard's Cards menu like any other card.

### Added
- **Bulk-linker for unlinked recipe ingredients
  (IMPL_PLAN_RECIPE_IMPORTER Chunk 6, 2026-07-04).** New
  **Settings → Admin → Data → Unlinked ingredients** page lists
  every recipe ingredient that landed unlinked from the paste
  importer, grouped by normalised `raw_text` (case-insensitive
  trim + collapsed whitespace) with the affected recipe count.
  One click on a group's stock-item picker + Link runs a single
  atomic `POST /api/recipes/unlinked-ingredients/bulk-link`
  request that flips the FK on every matching row; **Create new**
  seeds a fresh stock item from the raw_text and links in the
  same click. Recipes flip back to a real cookable / not-cookable
  state on the next read (server-owned tri-state, R-003).
- **PWA share target for recipe pages
  (IMPL_PLAN_RECIPE_IMPORTER Chunk 6, 2026-07-04).** With Dora
  installed as a PWA on Android, the system Share sheet on any
  recipe page now lists "Dashy Dora". Sharing hands the page's
  title / text / URL to `/cookbook`, which auto-opens the paste
  import dialog pre-filled with the shared content — one tap to
  Import. Manifest declares
  `share_target: { action: '/cookbook', method: 'GET', … }`;
  GET-mode so the service worker doesn't need to intercept a POST
  body. No new server code — the paste endpoint from Chunk 5 owns
  the parse.
- **Freeform-instructions hint for paste flexibility (L261,
  2026-07-04).** The recipe-detail edit mode's freeform
  instructions textarea gains a hint — *"Paste the recipe text or
  type freeform — Ctrl+V works."* — matching the paste-first
  posture of the Chunk 5 importer.

### Changed
- **Recipe importer — paste-based rebuild (IMPL_PLAN_RECIPE_IMPORTER,
  Chunks 1-5, 2026-07-04).** The URL-fetching importer is retired.
  `POST /api/recipes/import-from-url` is replaced by
  `POST /api/recipes/import-from-content` — the server no longer
  makes outbound HTTP requests, the user pastes the recipe page
  (Ctrl+A / Ctrl+C on the recipe site, Ctrl+V into Dora) and
  optionally types a "Where's this from?" URL for provenance
  (stamped on `Recipe.source`; never fetched). The new text parser
  (Class A JSON-LD-free layouts like RecipeTin / AllRecipes / Half
  Baked Harvest / Sally's / Simply / Woolworths / Taste, Class B
  `<h3>`/`<h4>`-headed layouts like Smitten Kitchen) is
  fixture-green on all 20 corpus recipes. Ingredients that don't
  fuzzy-match a tracked stock item now save unlinked (`raw_text`
  only, `stock_item_id: null`) — a Chunk 4 affordance that lets the
  recipe save fast even when the pantry side isn't fully aligned,
  and lets cookability render as a neutral tri-state until the row
  is linked. Closes **FU-104** (legal posture — no companion split,
  no third-party fetch by the operator) and **FU-199** (SSRF surface
  deleted, not patched). Bulk-linker + PWA share target land in
  Chunk 6.

### Added
- **⭐ The Zero-Input Pantry — inferred inventory (P8-07 flagship,
  2026-07-03).** Dora now holds a confidence-weighted *belief* about each
  stock item's level — a coarse band (Out / Low / Stocked) + a confidence
  + a plain-English reason — inferred from the closed loop instead of
  manual upkeep: last purchase (intake), buy cadence, cooking depletion,
  and time decay. It renders as an additive "Dora: ~Low · medium" chip
  **beside** the recorded level on the stock overview + item detail (the
  recorded level stays the source of truth for shopping/cooking); the
  tooltip explains the reason. A recent manual check always wins and resets
  confidence. Dora asks a single targeted quick-check only when a decision
  hinges on an uncertain item (it's on a list you're building, or in a
  meal planned this week) — never a bulk stocktake prompt. New endpoint
  `GET /api/stock-items/beliefs`; per-user opt-out in Preferences → Pantry
  (default on). Server-env verify (migrations + pytest + endpoint) pending;
  browser checklist in `DORA_VERIFY.md`. See
  `docs/04_proposals/PROPOSAL_ZERO_INPUT_PANTRY.md` for the full
  Charter mapping.
- **Cook→consume depletion events (P6-07 / FU-449, 2026-07-03).** Closes
  the missing leg of the loop: finishing a recipe now persists a
  `ConsumptionEvent` per ingredient it draws down, so run-out prediction
  (and the Zero-Input Pantry belief) shift when you *cook* with something,
  not only when you *buy* it — previously prediction saw purchases only.
- **Dashboard "Log price" quick action (FU-300, 2026-07-03).** Third
  button in the dashboard quick-action bar (money-gated to match the
  row-level Log-a-price posture, ADR-005). Pops a global
  `LogPriceSheet` (mounted alongside `QuickAddSheet` in `MainLayout`)
  that lists stock items low/out first, then hands off to the shared
  `PriceEntry` component in shelf mode with the item's
  `price_entry_prefill` seeded. Reuses
  `stockItemApi.addPriceObservationAsync` — no new API.
- **Dashboard stock donut deep-links (FU-299, 2026-07-03).** Pantry
  donut low/out segments and legend rows now deep-link to the
  filtered stock view (`/stock?level_id=<id>`). No new query-param —
  the stock overview already reads `?level_id`. Level ids resolved
  via `findLevelBySequence` on `stockLevelStore` so a renamed level
  still routes correctly (R-003). The card-level whole-card link was
  removed; a "View →" action link keeps the unfiltered path. "In
  stock" is intentionally not clickable (no filter for the residual).
- **Dashboard "Price drops" widget (FU-296, 2026-07-03).** New
  Money-zone card (product-data-gated, opt-in) surfacing tracked
  products whose current offer is strictly below every prior
  historic price. Ranked by drop percent, sliced server-side (5 by
  default). New endpoint `GET /api/reports/price-drops?limit=N`
  (`PriceDropsHandler` in `reports.py`). Honesty (§2.4): products
  with no prior history are excluded — a first-ever price isn't a
  drop. Verify pending Python-capable machine
  (checklist in `DORA_VERIFY.md`).
- **Windows + macOS desktop build scripts (FU-327, 2026-07-03).** New
  `packaging/build-windows.ps1` (PowerShell) and
  `packaging/build-macos.sh` mirror `build-linux.sh` step-for-step:
  SPA build → fetch Piper (auto-detected platform key on Windows;
  auto-detected + `--arch` override on macOS) → fetch default voice
  → `pyinstaller --noconfirm dora.spec` → smoke-check the output
  binary. README's Desktop-bundle section updated to cover all three
  platforms. Only Linux is CI-verified — the Windows/macOS scripts
  are checked in but their first cross-platform smoke stays a
  user-driven verify (`DORA_VERIFY.md` under
  "Windows desktop build script" / "macOS desktop build script").

### Fixed
- **iOS / WKWebView audio-unlock primer for Dora voice (FU-287,
  2026-07-03).** iOS Safari and the macOS WKWebView the desktop
  bundle uses gate `HTMLAudioElement.play()` on user gestures — and
  the gesture credit can be revoked by an intervening `await`
  longer than ~a few hundred ms. The Dora chat reply flow
  (LLM round-trip → Piper synth fetch → `audio.play()`) blew past
  that window; iOS users heard silence. `useSpeechOutput` now
  registers a one-shot document listener at first
  `useSpeechOutput()` mount that primes the browser's autoplay
  policy on the first user gesture by playing a very-short silent
  muted `data:audio/wav` blob. Subsequent `audio.play()` calls in
  the same session inherit the credit — including across `await`s.
  No-op on Chrome/Firefox/Android. The cook-mode timer-narration
  edge case (timer callback isn't a user activation) is documented
  as best-effort — the visible Notify remains the load-bearing
  "timer done" signal. iOS browser-verify pending device access
  (checklist in `DORA_VERIFY.md` under "iOS / macOS-WKWebView
  audio-unlock primer").

### Security
- **`Requests` bumped 2.31.0 → 2.32.4 (FU-196 d1, 2026-07-03).** Closes
  CVE-2024-35195 (session verification bypass after first request).

### Changed
- **`fuzzywuzzy` → `rapidfuzz` (FU-196 d2, 2026-07-03).** Actively
  maintained, MIT-licensed (fuzzywuzzy is GPL), ships a C extension
  so the "using slow pure-Python SequenceMatcher" warning noise is
  gone. Drop-in swap at two call sites
  (`features/recipes/import_recipe_from_url.py`,
  `features/search/global_search.py`) — rapidfuzz's `process` +
  `fuzz` modules use the compatible surface both sites needed.
- **Global exception handler now rolls back the DB session
  (FU-196 b partial, 2026-07-03).** `startup.py`'s
  `handle_global_exception` calls `db.session.rollback()` before
  returning 500 so a handler that raises after `add()`/`flush()`
  can't leak dirty session state past the request boundary.
  Belt-and-braces for the multi-commit sites; the full unit-of-work
  refactor is tracked as FU-456.

### Removed
- **Dead `SelectComponent.vue` deleted (FU-196 f1, 2026-07-03).**
  Grep confirmed zero non-self callers.
- **`web_app/.npmrc` deleted (FU-196 f2, 2026-07-03).** Only held
  pnpm-specific keys (`shamefully-hoist`, `strict-peer-dependencies`,
  `resolution-mode=highest`) which warned on every `npm` command;
  the repo is on npm.

### Added
- **Per-user "Meals per week" preference for the sequential builder
  (FU-181, 2026-07-03).** The meal-plan sequential builder's target
  count was hardcoded to 7. Added `User.meals_per_week int | null`
  (bounds 1–21, null = use the 7 fallback) with a new **Preferences
  → Meal planning → Meals per week** input. Consumed reactively via
  a new `useMealsPerWeek` composable so both `MealPlansBoardPage`
  and `MealPlansOverview` pick up a Preferences change without a
  reload. The old export `BUILDER_TARGET_MEALS` was renamed to
  `BUILDER_TARGET_MEALS_FALLBACK` — the single source of the fallback,
  no other file re-hardcodes 7.

### Changed
- **Dashboard drops dead `recipeStore.ensureLoadedAsync()` prefetch
  (FU-455, 2026-07-03).** The dashboard's `loadAll` fan-out
  hydrated the recipe store on every visit, but grep confirmed
  nothing on the page reads `recipes.value` — leftover from a
  pre-FU-298 design where the "Cookable tonight" card walked the
  full recipe list. Removed the prefetch + the unused
  `useRecipeStore` import. Saves one `GET /recipes` round-trip per
  dashboard load.

### Fixed
- **Stale-cache guard races swept (FU-016, 2026-07-03).** Full audit of
  `authStore.currentUser` reads in router / layout / admin guards paired
  with every backend mutation that can touch user-scoped state. Two real
  gaps closed: (1) when an admin edits *themselves* through **Settings →
  Admin → Users** (self-demote, rename, email change), the admin-user
  list refresh didn't touch `authStore.currentUser`, so the router
  guard + MainLayout + SettingsShell + every admin page kept reading a
  stale `is_admin` / `username` until the next hard reload — a demoted
  admin still saw admin surfaces. Now refreshes when the target row is
  the caller. (2) After **Settings → Admin → Data → Restore**,
  `authStore.currentUser` can be invalid (users table restored ⇒
  different `is_admin`, or the caller's row is gone) — the "Reload now"
  button was the only recommended path, but hitting Close left the
  guard lying. Close now refreshes the auth cache as a belt-and-braces
  safety net. Onboarding-complete, restart-onboarding (both surfaces),
  `PATCH /auth/me`, email-change, and password-change paths were all
  verified as already-correct.

### Changed
- **Retired the grandfathered `lazy="selectin"` on `Recipe.cuisine` /
  `Recipe.category` (FU-314, 2026-07-03).** R-019 / ADR-014's "no magic"
  rule flagged these as the last two per-entity lazy overrides in the
  codebase; each read site now names the eager-load it needs. No
  behaviour change — the same cuisine + category data lands in the same
  DTOs, but the query intent is now local to each handler instead of
  hidden in the mapper. The FU-138 e2e query-count test already guards
  `GET /recipes` against N+1 regressions, so a missed include would
  fail loudly rather than silently.

### Added
- **Auto-add-when-low toast now fires + names the list (FU-315, 2026-07-03).**
  When a stocktake transitions a stock item to Low/Out and its
  `auto_add_when_low` flag is on, the server has always dropped the item
  onto the unambiguous draft list and returned an `auto_added` payload —
  but the SPA typed the PATCH response as `void` and threw the payload
  away, so no toast ever fired. The `PATCH /stock-items/<id>` response is
  now surfaced through `stockItemStore` and every level-change path
  (row +/-, detail-page level swap, cook-mode consume, quick actions)
  shows a positive **"Added *<item>* to *<list>*"** toast + refreshes the
  shopping-list store so the new line renders live. The `auto: low stock`
  chip on the line was already wired.
- **Quick-add toast names the destination list + "always ask" pref (FU-316,
  2026-07-03).** When Dora adds a stock item to a shopping list via the
  quick-add path, the confirmation toast now names the target list
  ("Added to *Sunday shop*") instead of a generic "Added to your list."
  Also adds a new **Preferences → Shopping lists → Always ask which list**
  toggle (default off, current behaviour preserved). When on, the
  "which list?" picker fires every quick-add for users with more than one
  draft — Dora won't remember the last pick for the tab session.
- **P8-06 — Dora tells you *when* to buy, not just whether (2026-07-02).**
  When the buy-verdict oracle lands on `wait`, Dora now adds a time-boxed
  hint: "Expect a dip around Nov 15" with a sub-caption explaining the
  cycle she detected ("Your usual low lands ~every 14 days"). Derived
  purely from the user's own personal price history over the last 12
  months — no crowd data (P8-04 was cut per §7 Decision 6). The endpoint
  `GET /api/stock-items/<id>/buy-verdict` gains an optional
  `wait_hint: { until, reason }` field, present only when Dora has ≥2
  detected lows, a stable cycle (coefficient of variation ≤ 0.5), and a
  predicted next low still in the future — otherwise she stays quiet
  (Charter P3 Honesty). Same endpoint, no new route — "should I buy?" and
  "when should I buy?" are the same question at different resolutions.
- **BuyVerdictCard wired into the stock-item detail page (closes FU-437,
  2026-07-02).** Opening any stock item now shows the full three-axis
  verdict card at the top of the Overview tab — price / need / waste
  reasons, one-tap action for buy verdicts, and the P8-06 wait hint when
  present. Uses the existing `useBuyVerdict()` composable + 5-minute
  cache, and invalidates after any level-change or add-to-list mutation
  so the card re-fetches a fresh answer.

### Fixed
- **Filters button alignment on Stock Overview / My Products /
  Recipes Overview (2026-07-02).** The Filters button sat 8px above
  its `BaseButton` siblings in the toolbar. Root cause: the
  `FilterToggleButton` component wrapped its two children (Clear +
  Filters) in a `<div class="row items-center q-gutter-sm no-wrap">`.
  Quasar's `q-gutter-*` is the negative-margin trick (`margin-top: -8px`
  on the container, `+8px` on each direct child); when the wrapper sat
  inside the parent toolbar's own `q-gutter-sm`, it received `+8px`
  from outside AND applied `-8px` to itself internally — net zero
  displacement. Sibling `BaseButton`s only got the outer `+8px`, so
  they sat 8px lower. Both buttons already shared the same
  `BaseButton` base; the misalignment was purely from the wrapper.
  Fix: refactored `FilterToggleButton` to a Vue 3 multi-root template
  (no wrapper `<div>`) so the two `BaseButton`s participate directly
  in the parent's flex-row + gutter. Promoted the lesson to a new
  standing rule **R-027 — Styling encapsulation** in
  [`ENGINEERING_STANDARDS.md`](docs/01_charter/ENGINEERING_STANDARDS.md)
  (ADR-023).

### Governance
- **P8-04 crowd-sourced price graph — CUT (2026-07-02).** FU-436
  resolved: the originally-spec'd opt-in community price graph is
  retired from the champion sequence. Four structural blockers ruled
  out both KEEP and SHRINK — small-cohort re-identification even under
  anonymisation, cold-start with no distribution channel to bootstrap
  contributor volume, weekly Aus catalogue rotation caps the useful
  freshness window, hosted-broker ops role reintroduces the pattern
  `RECONCILED_FINISHING_PLAN.md §7 Decision 1` retired when the
  scraper was extracted to the private companion. P8-06's own spec
  already read "design to work on personal data alone" — crowd was
  framed as optional-blend, never load-bearing. Champion sequence is
  now `P8-01 → P8-02 → P8-03 → P8-05 → P8-06 → P8-07 → P8-08 → P8-09 →
  P8-10`. Unblocks FU-438 (P8-06 wait-until). Full argument trail:
  [`docs/05_investigations/CROWD_PRICES_ASSESSMENT.md`](docs/05_investigations/CROWD_PRICES_ASSESSMENT.md)
  (INV-11); decision recorded as
  [Reconciled Plan §7 Decision 6](docs/01_charter/RECONCILED_FINISHING_PLAN.md).
  No code changes (grep for `crowd_baseline` / `community_baseline`
  returned zero).

### Changed
- **Onboarding starter-data: per-name checklists + inline paste-rows
  (FU-195, 2026-07-02).** The C-5.5 "Seed catalogues" step is no longer
  all-or-none. The two "Use Dora's defaults" cards became expansions
  with a tri-state master checkbox and a per-name tick-list — you can
  now pick just "Pantry" + "Fridge" without importing the six other
  default groups, or just "Kitchen/Freezer" without the other zones.
  Selecting a child location auto-creates its parent zone (silent FK
  prerequisite, not counted as skipped). A new inline "Paste rows to
  bulk-add items" affordance lets you queue `Name, Group?, Location?`
  lines from a spreadsheet excerpt without navigating to the full
  importer; rows flow through the existing seed-items pipeline on
  Finish (idempotent by name). API contract: `POST /onboarding/seed`
  now accepts optional `group_names: string[] | null` and
  `location_paths: string[] | null` filters (null = seed all defaults,
  same as before). Legacy pre-FU-195 wizard drafts stored in
  `localStorage` (with the old `seedGroups` / `seedLocations` booleans)
  resume gracefully — an explicit `false` legacy value maps to "no
  picks", anything else lets the catalogue-driven defaults fill in.

- **StockLevel collapsed to 3 bands: Stocked / Low / Out (2026-07-02).**
  The middle "Sufficient Stock" band was axed — it was semantically
  dead (no predicate ever discriminated it: `needs_restock`,
  `is_low_stock`, `is_missing` all treated it identically to Stocked)
  and clashed with P8-07 Zero-Input Pantry's charter-mandated
  Out/Low/Stocked inference vocabulary. **Rename:** `WELL_STOCKED` →
  `STOCKED` throughout the domain enum, Python constants
  (`WELL_STOCKED_SEQUENCE` → `STOCKED_SEQUENCE`), TS helpers, the
  shopping-list review API contract (`set_well_stocked` →
  `set_stocked`), and the buy-verdict signal string
  (`"well_stocked"` → `"stocked"`). **DB rename:** the seeded "Well-
  Stocked" row now reads "Stocked". Migration
  `a1c7d9e42be0_20260702_drop_sufficient_stock_band` collapses any
  existing StockItems from Sufficient onto Stocked, deletes the
  Sufficient row, and reseries Low (was seq=2 → seq=1) and Out (was
  seq=3 → seq=2). StockLevelChange history survives via its
  denormalised name column. UX ripple: sticky-footer counts,
  `StockLevelDot`, the `useStockFilters` short-label regex, and the
  onboarding "Restock" scene copy all updated. Assistant NLU keeps
  "sufficient" / "ok" / "fine" as user-speech synonyms that now
  resolve to Stocked. Pre-release — no data preservation shim.

- **C-19 shared auth-shell + AuthButton (2026-07-02).** All nine pre-auth
  surfaces (Login, Setup admin, Splash + cannot-connect, Onboarding
  wrapper, Verify email, Forgot password, Reset password, Confirm
  email change, plus the `index.html` pre-mount) now share a single
  `AuthShell.vue` component that owns the animated blob backdrop,
  floating mascot, frosted-glass card, and the promoted
  `--auth-shell-*` colour ladder. The private `--lp-*` / `--setup-*`
  duplication is gone (R-003 fix, closes FU-440); the
  `.auth-shell` class-name collision across four aux pages is gone
  (closes FU-441).

  The submit button treatment is extracted into a dedicated
  `AuthButton.vue` — primary (teal gradient, unchanged from today's
  Login submit), secondary (amber "dora yellow" gradient), ghost
  (flat with hit target). Login's tiny "Need an account? Register"
  toggle and "Forgot password?" link are now full-sized buttons
  (feedback §LOGIN "make them buttons in the same style, different
  colour"). Forgot Password matches Login (feedback §LOGIN "Forgot
  password screen should match styling of login screen"). Splash and
  cannot-connect share the login canvas via `backdrop="quiet"`
  (blobs motion-frozen so bootstrap doesn't burn CPU) and the
  pre-mount HTML splash is pinned to `#1f2647` so cold-load reads as
  one unified midnight moment. Net ~-200 LOC.

  Design: `docs/04_proposals/PROPOSAL_AUTH_SHELL.md`. Execution:
  `docs/04_proposals/IMPL_PLAN_AUTH_SHELL.md`.

### Added
- **P8-05 "Should I buy this?" personal buy-verdict oracle (2026-07-02).**
  Every stock item now has a personal verdict — **buy / wait / skip /
  unsure** — composed server-side from *your own* data: completed
  shopping-list line prices (per FU-227 line ladder), purchase cadence,
  and waste events over the last 12 months. **No external calls, no
  crowd baselines, no scraping** — the oracle reads only what you've
  logged.

  Two surfaces:
  * **Stock Overview row** — inline badge on each item so you can decide
    at list-building time.
  * **Shopping List detail line** — same badge while in shop mode, so
    the "wait, actually skip this" nudge lands right before checkout.

  The badge is silent on low-confidence verdicts (Charter P3 — no
  dashboarding every row). The popover shows the reasons in three axes
  (price / need / waste) plus a "why?" summary of the data used
  (Charter P7 — never a black box). One-tap `add_to_list` is wired in
  Stock Overview via the existing quick-add-target seam; other actions
  route to the row's existing controls (R-003 — no duplicate mutation
  seams).

  Gated by install-wide `AppSetting.buy_verdict_enabled` (default
  **on**). Migration `e2b9c4a7f5d1` adds the flag. Full charter +
  composition rules: `docs/04_proposals/PROPOSAL_BUY_VERDICT_ORACLE.md`.

- **P8-02 barcode-to-add via Open Food Facts (2026-07-02).** Scanning
  a barcode from Stock Overview now handles the *unknown* case: Dora
  asks Open Food Facts (open data, add-only) for a suggested name,
  brand, image, and category, and opens the "Add a stock item" dialog
  pre-filled and clearly labelled as a suggestion the user reviews. On
  save the EAN is auto-registered against the new stock item so the
  next scan of the same code jumps straight to that item.

  **Interaction with already-mapped EANs is honest by design:**
  * `stock_item` / `stock_item_via_product` (barcode already resolves
    to an item, directly or via a Product) → navigate to the existing
    item; **no OFF lookup, no duplicate created**.
  * `product_no_link` (barcode matches a Product with no linked stock
    item) → open the add dialog barcode-only, with a "matches a known
    product" note; user's own Product data wins over an open-data
    suggestion, so no OFF call.
  * `unknown` → OFF lookup; on a hit the dialog is seeded with the
    suggestion, on a miss (or a network failure) the dialog falls back
    to a barcode-only prefill so the add still works.

  The whole surface stays gated by `scanning_enabled` (off by default).
  This is **distinct from the removed real-world barcode deal-lookup**
  (P6-02); OFF is used only as a name/image seed for a *user-
  confirmed* new pantry item, never for price/deal data. See
  `docs/04_proposals/PROPOSAL_BARCODE_SCANNING.md` §P8-02 for the
  design rationale.

### Changed
- **P8-01 rename: Discount Dora → Dashy Dora (2026-07-01).** The
  full sweep. Every in-repo identifier that carried "Discount" or
  "DiscountDora" is now "Dashy" / "DashyDora" / "Dashy Dora": UI
  copy (Dashboard hero alt, Help update-available banner + About
  panel, the assistant's "who are you" / "what's new" answers),
  package name (`dashy-dora`), PWA `appId` (`dashy-dora`),
  compose service + container name (`dashy_dora`), Docker image
  ref (`ghcr.io/bentalese/dashydora`), User-Agents
  (`DashyDora-Help`, `DashyDora-RecipeImporter`), release-check
  URL (`api.github.com/repos/BenTalese/DashyDora/releases/latest`),
  README badges and clone URL, and the docstrings/comments that
  used the old name. Bare "Dora" is untouched — the mascot, the
  short-form voice, and the code namespace stay. Two external
  identifiers can't be flipped from inside the repo — the actual
  GitHub repository and the local checkout directory — tracked as
  FU-353.
- **D.O.R.A. bot rename + easter egg (2026-07-01).** The
  chat-header label "DoraBot" and the Help-page "Meet DoraBot"
  button both read **D.O.R.A.** now. The `/help/dora` landing
  reveals the acronym in a caption:
  **D**elicious **O**rganised **R**estock **A**ssistant.
  Hovering the header label surfaces the same expansion as a
  tooltip. Suggestion chip "Thanks DoraBot" → "Thanks D.O.R.A."
- **Nav-state policy: list-page filters/search/sort/scroll persist
  within a session, reset on full reload (A8 §3, 2026-07-01).**
  New composable
  [`useListState`](web_app/src/composables/useListState.ts) —
  module-level Map keyed by page scope, gone on hard reload.
  Applied to Stock Overview (via `useStockFilters`), Cookbook,
  and My Products as the canonical pattern; router now honours
  Vue Router's `savedPosition` so browser back/forward restores
  scroll. Codified as **R-026** with **ADR-022** in
  [`docs/01_charter/ENGINEERING_STANDARDS.md`](docs/01_charter/ENGINEERING_STANDARDS.md).
  Remaining list pages migrate opportunistically (FU-354);
  sign-out `clearAllListState()` hook is FU-355.
- **QR labels moved to Settings → Kitchen setup (FU-340, 2026-07-01).**
  The Print QR labels workflow (pick items, pick a sheet layout,
  open a printable sheet) moves from `/data/barcodes` to
  `/settings/kitchen-setup/qr-labels`. The old page's Scan tab is
  retired — every surface that needs scanning already has its own
  Scan button (Stock Overview toolbar, Add-to-list flows), so the
  central Scan tab was pure duplication. `/data/barcodes` redirects
  to the new settings page so existing bookmarks still work; the
  redirect will drop when FU-341 collapses the `/data` shell. The
  "Scan a barcode" PWA shortcut was retired at the same time (it
  pointed at the deleted tab).

### Added
- **Install-wide image compression settings (FU-345, 2026-07-01).**
  Settings → Admin → Data → Backup & restore has a new "Image
  compression" card with two knobs: JPEG/WebP quality (30–100,
  default 85 — visually indistinguishable from original) and
  longest-edge cap in pixels (512–8192, default 1920). Applied at
  upload time via the shared client-side pipeline, so every image
  surface (stock items, recipes, products, avatars, receipts, store
  logos) picks up the admin's choice with no per-surface work.
  Existing images are unchanged — forward-only. Backups inherit
  whatever bytes the images already have; no re-encode on the
  backup path.

### Changed
- **Import page: Options block uses SettingsRow (FU-344, 2026-07-01).**
  The Options checkbox list on Settings → Admin → Data → Import got
  a chrome pass — same label-left / toggle-right shape as every
  other Settings page. Each toggle now has a one-line hint under
  its label explaining what it does. Fixes the previous stacked-
  checkbox misalignment and lets the Import page sit flush with
  its siblings.

### Added
- **Import templates — download a blank spreadsheet (FU-343, 2026-07-01).**
  Settings → Admin → Data → Import now has a "Download template"
  button next to the file picker. Clicking it downloads a CSV with
  the right header row + one example line, so new users can fill
  in the blanks instead of guessing the schema. Only `stock_items`
  today (the one shape the importer accepts); more sections slot in
  without a UI change. Headers come from the same constant the
  inspect + commit paths read, so the template can never drift from
  what the importer accepts.

- **Backup library (FU-342, 2026-07-01).** Every backup now persists
  as a row + a file on disk. Settings → Admin → Data → Backup &
  restore shows a library list (newest first) with per-row
  Download / Restore-from-saved / Delete actions; the "New backup"
  button opens a section picker with an inline warning when
  Optional sections (users, system settings, historic offers) are
  ticked. Restore-from-saved skips the upload + inspect round-trip
  external files still go through. Retention (default 5) and
  storage path (default `<DATA_DIR>/backups`) are admin-editable at
  the bottom of the page — an external mount / NAS is validated
  for writeability on save. The old download-only
  `GET /api/data/backup` and its `User.last_backup_at` stamp
  retired in the same migration (no fast-path — every backup goes
  through the library, per user decision).

### Security
- **Admin-gate every mutating Data endpoint (FU-198 / FU-341, 2026-07-01).**
  New shared `require_admin()` dependency; backup export, backup
  inspect, backup restore, the chunked-upload chain
  (`/data/uploads/start|chunk|finish|<id>`), and spreadsheet
  import (inspect + commit) all now return 403 for non-admin
  callers. Previously required only a logged-in session — a
  logged-in non-admin could restore arbitrary rows (users,
  app_settings, historic offers) into the install. Closes the
  FU-198 HIGH-severity finding.

### Changed
- **Data area collapsed under Settings → Admin → Data (FU-341, 2026-07-01).**
  The `/data` shell and its DataManagement.vue host are retired.
  Backup & restore and Import now live under
  `Settings → Admin → Data → …` alongside the other admin-only
  surfaces, with matching chrome. The "Data" main-menu entry is
  gone (admin-only workflows don't need a top-level slot; admins
  reach it in two clicks via the header avatar). Every prior URL
  redirects to its new location — `/data/backup` and `/data` both
  land on the new Backup page, `/data/import` on the new Import
  page, `/data/barcodes` on QR labels (per FU-340), and
  `/data/export` on Backup (nearest sibling — the Export page
  itself was retired in FU-339). Non-admin bookmarks chain through
  the redirect and land on Settings → Account.

### Removed
- **`/data/export` (Export & Print) page retired (FU-339, 2026-07-01).**
  The central Data → Export & Print page has been deleted along with
  its route. Every printable surface (stock overview, recipes,
  shopping lists, meal plans) now carries its own Print/CSV action
  in-context — the central hub duplicated those callers and, per
  the user, was "a management area I never wanted; I print where I
  need to". The four export composables and the backend
  print-view/CSV endpoints are unchanged — every in-context caller
  still uses them. Paired with FU-338 (meal-plan Board Print) in
  the same day so no window existed where meal-plan print was
  unreachable.

### Changed
- **Meal-plan Board — in-context Print action added (FU-338, 2026-07-01).**
  The weekly Board (`/meal-plans/board`) now carries a Print /
  Save-as-PDF button in the desktop top strip (icon, next to
  Templates) and in the mobile week-nav header. Uses the existing
  [`useMealPlanExport`](web_app/src/composables/useMealPlanExport.ts)
  path via `planner.printFocusedWeek`. Closes the last hole where a
  printable surface was only reachable from the central
  `/data/export` page. Hidden when no plan is focused / no meals
  planned this week (nothing to print).
- **History tab honest truncation — 2026-06-30 (follow-up).** The
  per-kind server cap rose from 20 to 50 events, and the client no
  longer silently trims to the last 60 merged rows. Instead, the
  server reports `history_older_count` — the sum of events dropped
  past the 50-per-kind cap across every event kind — and the SPA
  renders a single *"N older events not shown"* footer under the
  timeline. Retention is unchanged (events live forever; only the
  detail-page projection is capped).

### Added
- **Stock Item History tab: three new event kinds — 2026-06-30.** The
  timeline on each stock item's History tab now surfaces three signals
  the old view couldn't answer:
  - **Bought** — every ticked line on a finished shopping list appears
    as *"Bought · <list name>"* with quantity, price and store when
    the Finish flow captured them. Answers *"when did I last actually
    buy this and for how much?"* — a question the prior "added to
    list" entries couldn't. Pure read-side projection; no new table.
  - **Used in <recipe>** — every recipe you cooked (POST
    `/api/recipes/<id>/cook`) that references this item as an
    ingredient. Batch cooks badge with "× N meals". Closes the
    purchase → use → waste loop that INV-7 sketched but only half-
    built. Backed by a new `CookEvent` append-only table, joined to
    the item's linked-recipe universe at projection time.
  - **Set expiry / Pushed expiry +N days / Cleared expiry** — every
    transition of `StockItem.expiry_date`. Repeat pushes reveal a
    "this is stale in your fridge" pattern the user can act on.
    Backed by a new `StockItemExpiryEvent` append-only table, written
    from both `create_stock_item` and `update_stock_item` (which is
    the single endpoint the row-menu "+N days" nudges and "Clear
    expiry" both flow through).

### Security
- **Account-takeover chain closed: CSRF defence + verified email change
  with password proof — FU-197 (2026-06-30).** Three coupled gaps fixed
  together. (1) **CSRF double-submit defence** on every mutating API
  call: the backend mints a non-HttpOnly `dora_csrf` cookie on the
  first response a client makes without one (SameSite=Lax, Secure
  mirrors `SESSION_COOKIE_SECURE`); every `POST/PATCH/PUT/DELETE` on a
  non-public endpoint must echo it as `X-CSRF-Token` or 403s, with a
  constant-time compare so timing attacks can't tease out the cookie.
  Login / register / forgot-password / reset / verify / bootstrap-admin
  stay exempt so a cold client can authenticate; the bearer-authenticated
  ingestion endpoint stays exempt because Bearer tokens aren't
  browser-ambient. The SPA's axios client reads the cookie and attaches
  the header automatically. (2) **Email change now requires the current
  password** (matching the existing change-password flow) and emails a
  heads-up notice to the **old** address **before** sending the
  confirmation link to the new one — so even if a future hole lets an
  attacker through both prior gates, the legitimate owner sees the
  notice at the address they currently control. (3) **`PATCH /api/auth/me`
  no longer accepts the `email` field** at all: the SPA was silently
  using this unverified path; it now hard-rejects with 400, and Settings
  → Account → Email is rebuilt around the verified flow with an
  in-form Current password input + "Send confirmation" button +
  explanatory copy. Codified as **R-025** (session-mutating writes need
  both proof-of-possession and CSRF) and **ADR-021** in
  `ENGINEERING_STANDARDS.md` so the asymmetry between sensitive flows
  becomes a violation rather than a judgement call.
- **Fresh-install bootstrap is now an explicit, single-use setup page —
  FU-200 (2026-06-30).** On a brand-new install the first visitor lands
  on a dedicated `/setup` "Create the first admin account" page instead
  of `/login`. The page is single-use: after one admin exists, the
  backend `POST /api/auth/bootstrap-admin` endpoint 410s on every
  subsequent call and the SPA router refuses to render `/setup` (anyone
  who saved that tab gets bounced to `/login` or the dashboard). At the
  same time, `POST /api/auth/register` no longer self-grants admin to
  the first registrant — every self-serve signup is `is_admin=false`
  and `email_verified=false` regardless of database state. The
  `ADMIN_BOOTSTRAP_EMAIL` env var (previously listed as production-
  required but never read) is now honoured: when set, only that exact
  email can bootstrap, closing the "first stranger to hit the box on a
  public IP" race.

### Added
- **Receipt photos on shopping lists — FU-334 (2026-06-30).** Once a
  list moves out of `draft` (Start shopping → Finish & restock), a new
  **Receipts** section appears on the list detail. The picker offers
  **Take photo** *and* **Choose receipt** — on mobile you can snap a
  fresh photo or pick one already on the phone; on desktop just the file
  picker. Multi-photo by design (long till rolls, two-store shops); no
  captions, no OCR, no reconciliation with line prices. Pure
  record-keeping that survives Finish — the receipts stick to the `done`
  list as evidence. Storage reuses the centralised `processImageFile`
  pipeline (R-003): 1600px long-edge JPEG q0.85, 12MB input cap, served
  raw via a dedicated bytes endpoint so detail JSON never inlines blobs.
  Deleting the list cascades the receipts.

### Changed
- **Manual product-add: no more auto-spawned stores — FU-189a
  (2026-06-30).** `POST /api/products` no longer silently creates a
  `Store` row when the named store doesn't exist; the request is
  rejected with a 422 *"Store 'X' does not exist. Create it in
  Settings → Stores first."* This matches the strict no-auto-create
  posture the ingestion API has enforced since FU-190 — stores stay
  user-curated everywhere. Existing stores match case-insensitively
  (trimmed), mirroring `CreateStoreHandler`'s duplicate-detection
  rule. No SPA UI exercises this path today, so there's no visible
  product-side change; future product-create UIs will surface a
  store picker instead of typing names.

- **Image upload UX consistency — R-024 (2026-06-30).** Image-upload
  surfaces across the SPA now share the same picker UX: **Take photo**
  (mobile only, opens the rear camera) and **Choose image** (gallery /
  files / desktop disk). The new `ImageSourcePicker` primitive is the
  single source of truth for the camera-vs-gallery question and is
  composed by `ImageUploadField` (uplifting recipe hero, stock item
  image, user avatar, recipe edit dialog) and used directly by
  `RecipeStepImagesEditor` and the new Receipts section.
  `StoresSettings` store-logo upload still uses `q-file` (tracked under
  FU-335) — that's the only carve-out.

- **AI assistant — finalised: probe banner, "Test connection" button,
  topology docs — FU-330 + FU-331 + FU-332 (2026-06-29).** Same-day
  PR2 over the per-user assistant work. **Banner**: the chat panel now
  surfaces an inline *"AI mode unavailable — using basic mode"*
  banner with a Retry button whenever a user who's turned AI mode on
  finds their LLM unreachable (wrong URL, expired key, server down,
  rotated encryption key). Plain Basic-mode users — who haven't
  configured AI — don't see it. **Test connection**: Settings →
  Assistant gains a *Test connection* button per provider that
  probes the saved config (or freshly-typed draft values) without
  forcing the user to commit. Rate-limited at 10/min per user,
  every probe is audit-logged. **Docs**: HelpPage gets four new
  "Dora itself" entries (provider matrix, unavailable-banner causes,
  network topology — backend reaches the LLM not your browser,
  admin master switch + key-encryption env var). README's
  AI-assistant section rewritten for the per-user pattern, all four
  providers, and the multi-machine topology gotcha.

- **AI assistant — per-user config + four providers — FU-153 PR1
  (2026-06-29).** The assistant's LLM config is now per-user instead
  of install-wide. A new **Settings → Assistant** page lets each
  household member pick a provider (Ollama, OpenAI, Anthropic, or
  Google Gemini), enter the URL/model or API key it needs, and turn
  AI mode on for *their own* account. The old install-wide
  AppSetting.llm_* row is gone; in its place is a single admin
  **master kill-switch** at System → AI assistant. The assistant
  handler picks the current user's provider per request, so a
  household with two desktops each running their own LLM can have
  each user pointed at their own. API keys are encrypted at rest
  with Fernet via the `DORA_LLM_KEY_ENCRYPTION_KEY` env var
  (operator sets it once; Ollama works without it). The probe +
  "AI unavailable" banner from proposal §7.2 + the broader help
  docs from §7.3 + a per-user "Test connection" button are
  deferred to FU-330/FU-331/FU-332.

### Changed (process / non-product)
- **Assistant chat-mode redesign folded into the existing proposal —
  FU-152 + FU-150 retired (2026-06-29).**
  `docs/04_proposals/DORA_ASSISTANT_ARCHITECTURE_PROPOSAL.md` gained a
  new **§2.2.1 — Rules-router mechanism (tokenise → slot-extract →
  filter)** that owns the four-layer pipeline (vocab-derived triggers
  → slot extractor → optional intent scoring → reply transparency)
  previously spec'd in FU-152, plus a status note tying step 1 to the
  already-shipped FU-150 minimal fix. §5 sequencing bullet 4 ("Rules
  router over real capabilities") now points at §2.2.1 for the
  mechanism. Both FUs flipped to `[RESOLVED]` and moved to
  `DORA_FOLLOWUPS_RESOLVED.md`. No product code change.

### Fixed
- **Spend-by-store report now honours `actual_unit_price` overrides —
  FU-229 (2026-06-29).** The Money-zone "Spend by store" widget
  previously summed only the `picked_offer_price` snapshot from each
  ticked line and ignored the user's till-receipt
  `actual_unit_price` override. A line where the user typed a
  different price at the till counted as the offer's headline price
  instead of what was actually paid. The handler now applies the
  same `actual → picked` ladder used by budget, waste, the assistant
  and suggestions (`shopping_lists._line_price.line_paid_unit_price`).
  Savings ("RRP − picked") deliberately stays snapshot-only — it
  measures the deal, not what you paid.

### Fixed
- **Products saved on product-search now show up immediately on My
  Products, Price History, and Reports — FU-154 (2026-06-29).**
  Three pages each kept their own `ref<Product[]>` populated by a
  direct `productApi.getAllAsync()` call, bypassing
  `productStore.products`. So a product saved on the search page
  (which writes through the store) was invisible until a hard
  refresh on any of those three surfaces. Each page now reads
  `products` via `storeToRefs(productStore)` and triggers refreshes
  through `productStore.getProductsAsync()`; the store
  initialises `products` to `[]` (not `undefined`) so consumers
  never see a tri-state. R-003 (state ownership) violation closed.

### Added
- **Onboarding "demo dataset" toggle — FU-194 / L38 (2026-06-29).**
  New opt-in card on the wizard's starter-data step ("Add a demo
  recipe + this-week meal plan"). Off by default. When ticked,
  Finish calls `POST /api/onboarding/seed-demo`, which creates one
  plain "Spaghetti Aglio e Olio" recipe (with the three pantry
  items it needs — reused by name if already present from a starter
  pack), and a current-week meal plan with one Dinner entry today.
  Rows aren't marked as demo — the user renames or deletes them
  like any other entry. The endpoint is idempotent: a second call
  with the recipe already present returns `seeded: false` and
  writes nothing.

### Fixed
- **Assistant honours the household-configured expiring-soon window
  — FU-187 (2026-06-29).** The four assistant tools that filter on
  "expiring soon" (`search_stock` with `expiring_soon`,
  `whats_expiring`, the pantry summary, the location urgency check)
  used to read the bare `EXPIRING_SOON_WINDOW_DAYS` default
  constant. They now resolve through `effective_expiring_soon_window`
  / `AppSetting.expiring_soon_window_days`, so an admin retune of
  the household window is reflected everywhere — assistant answers,
  alerts list, and the location heatmap all agree.

### Changed
- **Dashboard "Next to cook" card is meal-plan-driven — FU-298 (L272)
  (2026-06-29).** The old "Cookable tonight" card showed the top 3
  fully-in-stock recipes regardless of whether the user had planned
  them. The new card pulls the next 3 *planned* meals from
  `meal_plan.upcoming_entries`, deduped by recipe, and tags each with
  a server-derived ready / missing-N badge (green "Ready" / amber
  "Missing N" / grey "No ingredients"). Empty state now invites
  planning a meal (link to `/meal-plans`). Backend
  `UpcomingMealPlanEntry` DTO gained `recipe_id` (for deep-linking)
  and `missing_count` (`null` for empty recipes, `0` = ready, `>0` =
  N missing) — reuses the existing `load_recipe_cookability` map
  already computed for the recipe summary so no extra DB round-trip.
- **Dashboard budget card is money-gated — FU-297 (2026-06-29).**
  Added `gate: 'money'` to the budget CardDef, matching savings /
  spend / pantry-value. Budget surfaces are all dollar-denominated
  (even the "no target set" copy reads "$X.YZ spent so far"), so the
  Money-zone gate posture applies (ADR-005). With money features
  off, budget no longer renders and the `/api/budget/status` fetch
  is skipped.
- **Dashboard Cards menu has drag-and-drop reorder — FU-294 / D4
  (2026-06-29).** Desktop power-user extra layered on the existing
  tap-up/down (which stays — C13's mobile-mandatory alternative).
  Reuses the shared `useDragDropList` composable (R-022 / ADR-018);
  drag is constrained to within-zone, same persistence path as tap.
  Handle column hides on `$q.platform.is.mobile`.

### Fixed
- **Voice toggle appears on browsers without SpeechSynthesis when
  Piper is configured — FU-289 (2026-06-29).**
  `useSpeechOutput().available` now reflects Piper too: on a browser
  that lacks `window.speechSynthesis`, the composable does a one-time
  session-cached probe of `GET /api/tts/voices` and flips `available`
  true when the server reports `configured: true`. The Settings →
  Voice "Let Dora speak her replies" toggle and the chat mute button
  now appear in that scenario. Browsers with SpeechSynthesis are
  unaffected — they never hit the probe.

### Changed
- **VocabListEditor empty-state is customisable per taxonomy — FU-285
  (2026-06-29).** The hardcoded "No {nounPlural} yet. Create one to
  start tagging recipes." now accepts an optional `emptyAction`
  override threaded through `TaxonomyManagerPage`. Recipe cuisines /
  categories / tools / dietary tags keep the recipe-shaped default;
  the meal-slots page now reads "Create one to schedule meals
  against." (slots aren't tags — the old wording read oddly on a
  freshly-emptied slot page).

### Documentation
- **README — install docs cover VAPID key generation (FU-207,
  2026-06-29).** New "Push notifications (optional, VAPID keys)"
  section under § Local dev quick reference: command to generate a
  key pair with `py-vapid`, the three `DORA_VAPID_*` env vars, and
  the dry-run / disabled-toggle behaviour when any is missing.

### Fixed
- **`PATCH stock_location_id: null` regression test (FU-203,
  2026-06-29).** The clear path was already fixed (the FK-set mirror
  of the C-1b.1 stock_group fix); added the missing e2e regression so
  the next `lazy="noload"`-flavoured bug can't sneak back in.

### Changed (engineering / no user-visible behaviour change)
- **R-016 lazy hydration extended to 5 more stores + app-wide
  sweep (2026-06-29).** `ensureLoadedAsync()` added to
  `recipeStore` (split into `ensureLoadedAsync` for recipes +
  `ensureCollectionsLoadedAsync` for collections — independent
  fetches), `shoppingListStore`, `locationStore`,
  `recipeVocabStore`, `mealSlotStore`. Every page / composable /
  component that was calling the raw refetcher unconditionally
  in `onMounted` (or guarding with the textbook
  `if (store.items.length === 0)` smell) was migrated:
  RecipeDetailPage, RecipesOverview, StockItemDetailPage,
  StockOverview, DashboardPage, RecipeCookMode, ShoppingListDetail,
  StockLocationsSettings, useMealPlanner, RecipeEditDialog,
  DoraChat, QuickAddSheet, CreateStockItemDialog. Truly dynamic
  stores (`alertStore`, `mealPlanStore`, `suggestionStore`)
  deliberately left on their force-refresh paths — lazy caching
  is the wrong default for volatile data.
- **R-016 lazy-hydration sweep across recipe + stock pages — FU-221
  (2026-06-29).** `onMounted` Promise.all blocks on
  `RecipeDetailPage.vue`, `RecipesOverview.vue`,
  `StockItemDetailPage.vue`, and `StockOverview.vue` now call
  `stockItemStore.ensureLoadedAsync()` / `stockLevelStore.ensureLoadedAsync()`
  instead of the raw `getXAsync()` refetchers. Avoids redundant
  collection refetches when re-entering these pages without unmount.
  Stores without the helper (`recipeStore`, `shoppingListStore`,
  `locationStore`, `recipeVocabStore`, `mealSlotStore`) were left
  unchanged per R-007 — extending those is a separate sweep.
  `MealPlansOverview.vue`, also flagged in FU-221, has since shrunk
  to 507 lines and no longer fetches stores in `onMounted` (only a
  planner-view redirect).
- **FU-215 (Shopping-list preferred-buy hint) closed (2026-06-29).**
  No code change — browser-verified the flow that went in 2026-06-17.
  Picking a hint on a line persists across reload; clearing removes
  it. Dangling ids after a PreferredBuy delete still tolerated
  (render no hint).
- **FU-216 (cost consumers — observation fallback) closed
  (2026-06-29).** No code change — browser-verified the additive
  fallback that went in 2026-06-17. Stock-value report and recipe
  cost-estimate card now pick up `StockItemPriceObservation` values
  for items without a linked-product price.
- **`UpdateMeCommand` TS type carries `household_headcount` (FU-204,
  2026-06-29).** C-5.4 added the field to the backend
  `UpdateMeRequest` + `AuthenticatedUserDto` but not the TS Command,
  so any frontend call site sending `{ household_headcount: N }`
  would typecheck against `Record<string, never>`-ish. Drift audited
  across every Pydantic field on `UpdateMeRequest` vs every key on
  `UpdateMeCommand`; only this one was missing.
- **All three drag-and-drop lists now share one composable + stylesheet
  — FU-326 / R-022 / ADR-018 (2026-06-29).** Shopping-list line reorder,
  structured-step reorder, and ingredient reorder all routed onto the
  new `useDragDropList` composable + `src/css/dnd.scss`. Visual
  affordance (handle grip, source-dim, drop-target ring) is now
  identical across the three surfaces (it was three slightly-different
  treatments before). No user-facing behaviour change.

### Added
- **Drag-and-drop ingredients between sections — FU-118 (2026-06-29).**
  The recipe editor's ingredient list now has a drag handle on each row
  (mirroring the structured-steps DnD pattern). Drop an ingredient onto
  another row to both reorder it *and* move it to the target's section in
  one gesture — the per-row Section picker stays for assigning into an
  empty section. Same stock item across different sections (olive oil in
  both Sauce and Garnish, etc.) was already supported and remains
  unrestricted; see the FU-118 resolution note in
  `DORA_FOLLOWUPS_RESOLVED.md` for the full duplicate-ingredient
  assessment.

- **Jump from a recipe card to "all the stock items it uses" (2026-06-29).**
  On a stock item's "Recipes using this" tab, each recipe card now carries a
  filter icon — click it to land on Stock Overview pre-filtered to that
  recipe's ingredient set. A removable chip ("Ingredients of: &lt;recipe&gt;")
  sits in the filter bar so it's discoverable + dismissable; the deep-link
  `?recipe=&lt;id&gt;` is stripped on clear so back/refresh won't reinstate it.

### Changed
- **Recipe-card dim removed for good — FU-109 resolved (2026-06-29).** The
  "would-be-cookable" opacity treatment was already gone from both surfaces
  (cookbook overview + stock-item detail); we dropped the now-unused
  `highlightStockItemIds` prop on `RecipeCard` and its only binding on
  StockItemDetailPage. The "Missing N ingredients" copy on the card face
  remains the single signal.

### Changed (process / non-product)
- **Verify checklist split out of the followups ledger (2026-06-29).** All
  pure "browser-verify X" entries moved from `DORA_FOLLOWUPS.md` to a new
  `DORA_VERIFY.md` — grouped by app surface, verb-first checkboxes, designed
  to be walked end-to-end. 38 verify FUs drained, `DORA_FOLLOWUPS.md`
  shrinks ~42% to its actual job ("open loops with state"). No-archive
  workflow: delete items as you confirm them; the pre-release systems test
  catches anything that slips. `CLAUDE.md` updated: session-start does NOT
  pre-scan the verify file; session-end routes new verify checks to
  `DORA_VERIFY.md`, not to `DORA_FOLLOWUPS.md`.

### Changed
- **All dates now respect your household timezone (FU-107 + FU-174,
  2026-06-29).** Every "what day is it today" decision the app makes —
  expiry alerts, dashboard "next 7 days", the assistant's "what's
  expiring", waste-rescue, budget periods, recipe "last made", location
  heatmap, the assistant's "push expiry", and the timestamp on
  downloaded files — now evaluates against the household timezone you
  set in Settings, not the server's local clock. Self-hosting Dora in
  one country with a household in another no longer drifts your alerts
  ±1 day around midnight. `Recipe.last_made_on` is now stored as a
  date (it always meant "which day", never "which moment"); the
  on-the-wire format was already ISO 8601 (ADR-007). No user action
  needed; if you've changed your household timezone, every surface
  picks it up automatically.

- **API-access + Stores settings errors carry the request ref too
  (FU-323, 2026-06-29).** The 10 toast / banner sites in those two
  pages that the FU-099 sweep deliberately deferred now match the rest
  of the app — toast lead = the action that failed, caption = the
  friendly cause + `ref: <id>`. Inline banners (load failures) carry
  the ref too. No user-visible behaviour change beyond consistency.

- **Error messages now read like English (FU-099, 2026-06-29).** Form
  saves that fail server validation no longer show developer prose like
  *"Input should be a valid integer, unable to parse string as an
  integer"* or *"Extra inputs not allowed"* — those are translated to
  friendly per-field copy ("Must be a whole number.", "This field isn't
  supported here.") rendered inline next to the offending input. The
  save toast is now a short *"Couldn't save — check the highlighted
  fields."* with a `· ref: <8-char>` suffix that ties the error to the
  request line in the server log. Every API failure (4xx + 5xx +
  network) also logs to the browser console with the same correlation
  id, so pasting a toast caption into a bug report is enough for a dev
  to find the failing request.

- **Unsaved-changes guard now covers Account + Assistant settings
  (FU-098, 2026-06-29).** Editing your username, email, or the
  install-wide AI assistant config (enable / base URL / model) and
  then trying to navigate away — sidebar link, refresh, close — now
  prompts before discarding your edits, matching the existing
  behaviour on the recipe and stock-item detail pages. Settings that
  save on every change (theme, notifications, money, alert
  thresholds) are unchanged — they have no draft window to guard.

- **Quantity-spacing sweep (FU-097, 2026-06-29).** All remaining
  `qty + unit` display sites now go through the central spacing helper —
  meal-plan "This week's shopping", the sequential builder preview,
  both substitute-ratio captions (cook-mode + stock-item detail) and
  the server-side recipe print template. Added a Python mirror
  `format_quantity` in `dora_api/domain/units.py` so the print view
  and the SPA can never disagree on spacing. No user-visible change
  for units that were already spaced correctly; "250 g" → "250g" /
  "1 ml" → "1ml" on the touched surfaces.

- **Magic-behaviour audit complete (FU-092, 2026-06-28).** 18 implicit
  / automatic behaviours catalogued and given per-finding verdicts.
  Audit at `docs/05_investigations/MAGIC_BEHAVIOUR_AUDIT.md`. 13 of
  18 already in the right shape (alerts, suggestions, finish modal,
  added_via chip, etc.) — no action. 4 small UX surfacing follow-ups
  spun off (FU-315 / FU-316 / FU-318 / FU-319). 1 plan-first
  follow-up: past-day meal-plan auto-drain (FU-317) wants a
  designed manual-reconcile feature + opt-in setting before any code
  touches the reconcile path.
- **New engineering rule: R-019 — No magic: explicit, verbose,
  consistent (FU-084 promoted, 2026-06-28).** User-elevated to a
  top-line value: prefer verbose explicit code over clever / implicit /
  auto-discovered behaviour; reject AutoMapper-shaped reflection
  between layers, decorator behaviour-mutation, convention-over-
  configuration past what the framework requires, and per-entity
  SQLAlchemy `lazy="..."` overrides. Follow the codebase's established
  pattern when one exists; don't introduce parallel approaches because
  one "felt right". Documented as R-019 in
  `docs/01_charter/ENGINEERING_STANDARDS.md` with ADR-014; existing
  `Recipe.cuisine`/`.category` selectin overrides grandfathered as
  FU-314 for a focused cleanup.

### Fixed
- **Recipe step editor type leaks under `exactOptionalPropertyTypes`
  (collateral from FU-117, surfaced during the FU-140 audit,
  2026-06-28).** The import-recipe step factory in
  `RecipeDetailPage.vue` now initialises `section_client_id: null`
  on parsed steps, and `RecipeStepsEditor.vue` forwards
  `sectionOptions ?? []` so the optional prop never leaks
  `undefined` to `RecipeStepRow`. No behaviour change.

### Added
- **Query-count regression test for `GET /recipes` (FU-138,
  2026-06-28).** New `SelectCounter` e2e harness and a ratio test
  that inserts 10 throw-away recipes and asserts the SELECT count
  doesn't scale with row count. Guards the batched
  cookability/ingredients/tags/tools/sections/plan-rollups path
  on the cookbook hot endpoint from regressing into per-recipe
  lazy loads.

### Fixed
- **Backup/restore round-trip preserves product-only and nested
  product shopping-list lines (FU-131, 2026-06-28).**
  Cart Button Chunk 3 added a nullable `product_id` to
  `ShoppingListLine` and a CHECK that requires at least one anchor.
  The restore decoder wasn't aware of the new column: a partial
  restore that selected shopping lists but skipped `saved_products`
  silently nulled `product_id` on every line, dropping product-only
  rows (CHECK violation) and degrading nested children to plain
  stock-item lines. Restores now pull the referenced `Product` in
  automatically and drop a line cleanly (with a warning) when the
  Product is genuinely missing instead of mangling it.

### Added
- **Section picker on the structured steps editor (FU-117,
  2026-06-28).** When a recipe has named sections, each top-level
  step row in `RecipeStepsEditor` now surfaces a small `Section`
  select (with `(Main)` as the implicit default) so multi-part
  recipes can be grouped end-to-end without leaning on the URL
  importer. Sub-steps inherit their parent's section visually — no
  picker is rendered on depth-1 rows. Removing a section detaches
  any step that pointed at it (parity with the existing ingredient
  picker).

### Removed
- **Freeform `Recipe.nutrition` text column (FU-115, 2026-06-28).**
  Superseded by the structured `kcal` field (C-4 Chunk 9). Pre-release,
  so the column was dropped outright via migration
  `b7e2d9a4c1f5_20260628_drop_recipe_nutrition` rather than audited
  first. All API request/response models, import/export paths, seed
  factory, and SPA editors no longer carry the field.

### Added
- **Hybrid barcode model: register an EAN against a stock item, a
  product, or both (FU-056 slice 1, 2026-06-28).** Real-world barcodes
  no longer require the Products overlay — lightweight installs can
  register an EAN straight to a stock item (`barcode → stock_item`),
  and catalogued installs still get the SKU coalescing via Product. New
  **Barcodes** section on the stock-item detail page (gated on
  `features.scanning`) shows direct registrations + via-Product
  derivations with add/remove. Scanning an unknown barcode now offers
  an in-place register flow. The per-Product UNIQUE rule (*one
  Product = one EAN*) is enforced server-side. Ingestion EAN auto-
  populate stays Phase-2 deferred.

- **Substitute notes + optional structured ratio (FU-034, 2026-06-27).**
  Each stock-item substitute pair can now carry a free-text hint
  ("1:1 in soups, but not in baking") and an **optional** structured
  ratio like *1 tsp olive oil → 1 tsp butter*. The note and ratio show
  on the substitute list on the stock-item detail page, and again in the
  cook-mode swap picker so the cook has the hint front-and-centre when
  swapping. Edit dialog: pencil icon next to the unlink button → textarea
  + "Add a ratio" toggle revealing qty + unit pickers on each side
  (units autocomplete against the canonical UNIT_TABLE; aliases like
  "tablespoons" resolve to "tbsp" on save). Cook mode does not yet
  auto-compute swap quantities — it surfaces the hint and the cook
  applies it; auto-compute is a future-phase call per Anti-creep.

### Changed
- **Meal planner — calmer meal cards + keyboard / screen-reader pass
  (2026-06-26, R-Phase 6 of the rebuild).** Planned meal cards no longer
  ship as saturated blue or amber fills — both the Direction A chip and
  the Direction B rich card render as calm content-forward cards with a
  **restrained left-border accent** (brand-primary for planned, amber
  for cook-shortfall, neutral for consumed). Status now reads through
  three channels (border + icon + text alternative) so colour isn't the
  sole signal. Slot rows on the Direction A day cards, day columns on
  the Direction B board, and week rows in the calendar widget are now
  real focusable buttons with full `aria-label`s (e.g. "Add a meal to
  Thursday 25 June Lunch", "Week of 30 June, 3 days with meals"). The
  global ArrowUp/Down "change week" shortcut no longer fires while a
  button has focus, so arrowing through a day's controls doesn't jump
  the week any more. Initial page load now paints a **layout-shaped
  skeleton** (3 day cards / 7 grid columns / mobile day strip) so the
  planner shape is visible instantly while the ~10 parallel store
  loads complete.

### Added
- **Cooking style preference + batch-aware meal planner (2026-06-25,
  R-Phase 5 of the rebuild).** New **Fresh / Batch** toggle in Settings →
  Preferences (under Typography). **Fresh** (default) keeps the meal
  planner pure scheduling. **Batch** opts in to the cook-pool
  affordances — per-recipe ± / log-cook / "n free" caption in the recipe
  palette, the shortfall ⚠ amber accent on planned-meal cards and chips,
  and the "to cook by DATE" warning on the week status + shopping
  summary. Existing households default to fresh; flipping to batch
  restores the previous behaviour. Migration:
  `e4c7a2f9b5d3_20260625_user_batch_optin.py`.
- **Meal planner — unified Templates drawer (2026-06-25, R-Phase 5 of
  the rebuild).** Templates work used to span four entry points: a rail
  card, a `$q.dialog` radio list to apply, a separate "Apply recurring"
  dialog, and a navigation hop to `/meal-plans/templates` for editing.
  Browsing, applying, renaming, and deleting now happens in a single
  in-place drawer ("Browse + apply templates…") — a right-side panel on
  desktop, a bottom-sheet on mobile. Rename is inline; delete asks for
  confirmation; **Apply** runs the existing "replace planned meals?"
  guard before forking. The dedicated `/meal-plans/templates` page stays
  for now as the heavy-management screen.

### Changed
- **Plan step-by-step builder rebuilt onto the shared recipe picker
  (2026-06-25, R-Phase 5 of the rebuild).** The first step of the
  step-by-step builder used to be a flat checkbox list of every recipe
  with no search. It's now the same picker the meal-planner rail uses:
  favourites tray, "haven't had in a while", "frequently planned", and
  search across the full cookbook. The disabled "Email" placeholder is
  gone. Building a plan no longer auto-generates the shopping list —
  the done step offers an explicit **Generate shopping list** button so
  users who only wanted to plan can stop there.

### Added
- **Meal planner — shared mobile single-day focus (2026-06-25, R-Phase 4
  of the rebuild).** On phones and portrait tablets both meal-planner
  pages (`/meal-plans` and `/meal-plans/board`) now render the **same**
  single-day focused view instead of the desktop carousel/grid. The day
  strip across the top shows seven small chips (today rimmed, focused
  day filled, a dot on days with planned meals); tapping a chip switches
  focus, the long-form date label heads the day's section, and the day's
  meals stack as the same content-forward cards used on Direction B (so
  the slot is a tag on each card, not five empty rows). Empty days show
  one calm "Plan {Day}" pill; past days read "Past day — read-only."
  Adding a meal opens a **bottom-sheet slot picker**, then a **bottom-sheet
  recipe picker** (auto-closes after a pick). A collapsible "This week"
  section at the bottom holds the same week-status summary + Generate
  shopping list CTA the desktop layouts surface, so consequences are
  always reachable. The A/B toggle is desktop-only — the carousel-vs-
  grid experiment doesn't apply when only one day is on-screen.
- **Meal planner Direction B — content-forward week board (2026-06-25,
  R-Phase 3 of the rebuild).** A second meal-planner layout now lives at
  **`/meal-plans/board`** alongside the existing vertical-carousel page
  at `/meal-plans`. Both views are switchable from a small **List / Grid**
  toggle in each page's header (desktop only); the choice persists across
  reload via `localStorage` and can be pinned by a `?view=` URL param.
  - **The board.** Seven day columns; each holds **0..n meal cards that
    stack** — slot is rendered as a small tag on the card, not a
    pre-printed empty row. Today's column carries a primary border so the
    eye lands on "now" first. Empty days collapse to a single ghost
    "+ add a meal" affordance. An optional **"Group by slot"** toggle
    flips to a slot-major / day-minor grid for the F46 "time of day as
    rows" view, on demand instead of as the default.
  - **Rich meal cards.** Thumbnail (or category-tinted monogram fallback
    when the recipe has no image), name, slot tag, ×servings, and
    cook-time when known. A restrained left-border accent calls out
    pool-shortfall (amber) or consumed (neutral); planned-and-cookable
    stay on the calm brand-primary border.
  - **Sticky consequences bar.** A summary strip — *N planned · N to cook
    by DATE · N to buy* — pins to the top of the working area as the
    board scrolls, with an inline "Generate shopping list" button when
    there's anything to buy. The shopping summary is always visible, not
    a card that scrolls away.
  - **Pinnable recipe drawer.** A right-side recipe drawer hosts the same
    search + trays + pool ± + log-cook controls as the existing palette.
    A pin toggle keeps it open during drag/add sprints; otherwise it
    auto-closes after each pick. Tapping a day's `+` opens a slot picker,
    then auto-surfaces the drawer so the user can pick a recipe in one
    flow.
  - **Calendar as a popover.** The minimalist calendar widget is
    available from a button in the top strip as a month-jump popover;
    behaviour is identical to the rail-hosted widget on the List page.
  - The board is a desktop-first experiment; narrow viewports continue to
    use the List page until the shared single-day focus lands. The whole
    A/B experiment is explicitly temporary — once a winner is picked, the
    losing page and the toggle are deleted.
  - Server-side, the meal-plan entry DTO is enriched with the display
    fields the card needs (cook-time, category name, cuisine name,
    has-image flag), keeping the client free of cross-joins to the
    recipes store.

### Changed
- **Meal planner Direction A upgrade (2026-06-25, R-Phase 2 of the rebuild).**
  The vertical-carousel planner is calmer and more glanceable without changing
  its shape. Notable shifts:
  - **De-sprawled days (Q2).** Each day card now renders only the slots that
    actually have a meal planned; instead of 5 italic "tap to add" rows, there
    is **one quiet "+ add a meal" affordance per day** that opens a slot picker
    menu. Households that prefer the old behaviour can flip a **"Show all
    slots"** toggle above the carousel.
  - **Sticky context columns.** On desktop the left palette and the right
    calendar + shopping rail stay pinned in view as the week scrolls — the
    answer-bearing summary no longer scrolls away first (U2).
  - **Promoted week status.** A small summary strip at the top of the working
    column reads "N planned · N to cook (by DATE) · N to buy" at a glance,
    always above the day cards.
  - **Calm empty states (R-014).** First run (no recipes yet) replaces the
    empty 3-column layout with a single hero pointing to the Cookbook. An
    empty week (recipes exist) gets a single "Plan this week" banner instead
    of seven days of "tap to add" sprawl.
  - **Safer Clear-week button (U7).** The destructive clear-week action is no
    longer an icon-only sibling of "Print"; it's a labelled button with the
    negative colour. Confirmation dialog unchanged.
  See `docs/04_proposals/IMPL_PLAN_MEAL_PLANS_REBUILD.md` for the full rebuild
  brief; FU-304 tracks the multi-phase work.

### Added
- **Recipe "image" steps mode (2026-06-25).** Recipes gain a third step
  payload alongside structured and freeform: a **scrollable gallery of
  photos** the user uploads (cookbook spread, handwritten card, printout).
  Cook mode renders the images full-width with tap-to-zoom; ingredients,
  finish-cooking, B8 substitute swaps, and Sous Chef all work the same.
  The mode toggle on the recipe detail page is non-destructive — switching
  between modes keeps each payload intact so the user can experiment.
  Client-side resize (1600px / JPEG q=0.85; 20-image soft cap) runs through
  a new centralised `processImageFile` helper now shared by every upload
  site in the app (R-003 applied to image upload utilities). Importer never
  produces image mode (image steps are hand-entered only). See
  `docs/04_proposals/PROPOSAL_RECIPE_IMAGE_STEPS.md`.

### Removed
- **`/waste` page (C-waste, 2026-06-25).** The standalone Waste page is
  gone. Its three jobs moved to lighter, in-context surfaces (see
  *Changed* below). Bookmarks now 404 by design — pre-release, no
  redirect. Waste **as data** is preserved end-to-end so the future
  Dora Score can still read the signal; see
  `docs/04_proposals/PROPOSAL_WASTE_MINIMISATION.md` for the full
  decision set. Score-weighting reassessment deferred to **FU-302**.
- **Dashboard "Use soon" card (C-waste, 2026-06-25).** Removed; the
  Needs-your-attention card already surfaces `expired` and
  `expiring_soon` alerts.

### Changed
- **Waste capture moved onto the stock-item row (C-waste, 2026-06-25).** The
  expiry dropdown on each stock item gains a **Mark as wasted** action that
  opens a tile-grid modal (Expired / Spoiled / Didn't like / Bought too much
  / Other). Tile-tap = submit; a 5-second **Undo** toast both removes the
  logged event and restores the cleared expiry. No money field, no note
  field, no quantity field — anti-shame UX by design.
- **Stock list "Stalest first" → "Expires soonest" (C-waste, 2026-06-25).**
  The previous "Stalest first" sort was sorting by last-touched stock
  level, not by expiry — a long-standing surprise. The new "Expires
  soonest" sort puts the nearest-expiry items at the top (items without
  an expiry sink to the bottom). The "Recently updated" sort already
  covers the "what have I touched lately" question.
- **Cookbook "Uses expiring ingredients" filter (C-waste, 2026-06-25).**
  A new filter narrows the cookbook to recipes that use at least one
  in-stock ingredient expiring within 14 days, ordered by count desc, with
  a **Uses N expiring** badge on each card while the filter is active.
  Off-filter, no badge — no noise.
- **Stock-item history: waste events are reason-only (C-waste, 2026-06-25).**
  The lifecycle timeline now shows "Wasted: expired" / "Wasted: spoiled"
  etc. without the old quantity / value / note line. Existing events are
  unaffected; the dropped fields are not recoverable post-migration.
- **Dora `waste_insights` tool simplified (C-waste, 2026-06-25).** The tool
  now returns just `{most_wasted, most_recent}` — what gets wasted often
  and what was wasted most recently. Reason breakdowns and dollar sums are
  gone with the underlying fields. `expiry_rescue` is unchanged.
- **"Frequent waster" suggestion deep-link (C-waste, 2026-06-25).** The
  suggestion now opens the specific stock-item detail page (where the
  history tab shows the events) instead of the deleted `/waste` page.
  Same goes for the dashboard's "Use soon" inbox-style suggestion.

- **Dashboard internals — card shell extracted (2026-06-24).** No behaviour
  change: the dashboard's repeated card markup is now a single reusable
  `DashboardCard` component, so the cards stay visually identical but the page
  is no longer a monolith (R-001). Verify-in-browser for visual parity.
- **Dashboard rebuild — Phase 6 (fortnight calendar, 2026-06-24).** A new opt-in
  **This fortnight** card shows the next 14 days as a grid, with coloured dots
  marking days that have meals (green), expiries (red) or planned shopping
  (accent). Tap a day to expand what's on — with links straight to the recipe,
  stock item or list. Enable it from the **Cards** menu. (Reuses the existing
  upcoming-events feed — no new backend.)
- **Dashboard rebuild — Phase 7 (mobile pass, 2026-06-24).** Mobile tidy-ups on
  the rebuilt dashboard: the quick-action buttons span the row for easy tapping,
  and the savings/alert chips get comfortable touch targets. The zone layout
  already stacks to a single column on narrow screens.
- **Dashboard rebuild — Phase 5 (restock radar + quick actions, 2026-06-24).** A
  new **Restock radar** card flags the things you keep running out of, each with
  a one-tap **Add** to your shopping list. A **quick-action bar** at the top of
  the dashboard lets you **Add item** or **Add to list** without leaving the
  page — the home screen now *does*, not just links out. (A "Log price" quick
  action and a meal-plan-driven cookable upgrade are still to come.)
- **Dashboard rebuild — Phase 4 (Money zone, 2026-06-24).** The dashboard now
  surfaces the money story it was hiding. A flagship **"You've saved"** card
  shows what you've saved vs RRP with a Month / Year / All toggle; opt-in
  **Spend by store** and **Pantry value** cards round out the Money band (all
  from existing reports). These appear only when money features are enabled, and
  the **Best deals** card now appears only when you actually track products.
  (Savings/spend/pantry use endpoints that already shipped — no backend change.
  A "price drops" widget is still to come; it needs a new server signal.)
- **Dashboard rebuild — Phase 3 (alert card redesign, 2026-06-24).** The
  "Needs your attention" card now leads with a **summary** — a row of chips
  showing the shape of what's wrong at a glance ("5 · expiring soon", "3 · out
  of stock") — above a peek at the three most-urgent alerts with their inline
  quick-actions, and a clear **"See all alerts →"** into the alerts page. Alert
  rows are now proper links (keyboard-accessible, open-in-new-tab) instead of
  mouse-only handlers.
- **Dashboard rebuild — Phase 2 (zones + reorder, 2026-06-24).** Dashboard
  cards are now grouped into labelled bands — **Act now**, **Today**, **Money**,
  **Your kitchen** — so the most urgent things sit up top instead of every card
  having equal weight. From the **Cards** menu you can show/hide cards and
  **reorder them within a band** (up/down controls). Your layout now **saves to
  your account** instead of just this browser, so it survives a cache clear and
  follows you to another device. (Backend column + migration are static-only on
  this machine — verified by type-check/lint; runtime migration + e2e pending a
  Python-capable environment.)
- **Dashboard rebuild — Phase 1 (declutter + welcome, 2026-06-24).** The
  dashboard now leads with what's *actionable*, not vanity totals. Four
  counter-only cards were removed — **Products**, **Recipes**, **Meals on
  hand**, and the standalone **Shopping** card (its count is now a "+N other
  active lists" link on the Primary shopping list card). The **alerts**,
  **Use soon**, and **Dora suggests** cards no longer disappear when empty —
  they show a calm "all clear" state, so a tidy kitchen looks reassuring
  instead of blank. The bottom-right "Dora says" tip bubble is replaced by an
  inline **welcome** at the top: a day-of-the-week greeting plus a rotating
  helpful hint, keeping the warm "Dora says" look. The "skipped setup wizard"
  reminder keeps its Continue/Hide buttons **inline** instead of on their own
  row.
- **Dashboard rebuild — Phase 0 (foundations, 2026-06-24).** Groundwork ahead of
  the dashboard content/layout rebuild (`IMPL_PLAN_DASHBOARD_REBUILD.md`). The
  manual **Refresh button is gone** — the dashboard already reloads on every
  navigation, so it earned nothing. Every dashboard **card and link is now a
  real link**: cards that navigate (Pantry, the week ahead, primary shopping
  list, budget, and the soon-to-change stat cards) are keyboard-focusable and
  open-in-new-tab–able instead of mouse-only `@click` blocks, and the in-card
  links (alerts "All", "Rescue ideas", recipe names, deal items, empty-state
  CTAs) became proper router links. The "Use soon" card no longer nests links
  inside a clickable card. No visual change intended.
- **Three more voices on the catalog (2026-06-24, download-only).** Alba
  (Scottish woman, warm and lilting), Northern English (friendly northern
  English man), and Hannah (soft American woman) join the five bundled
  voices. They're not shipped in the artifact — the user picks one in
  Settings → Voice and it downloads server-side into the data dir like
  any other catalog voice, ~60 MB each. SHA-256 pinned + verified.
- **Dora's neural voice now works out of the box on shipped artifacts
  (2026-06-24).** The Docker image and desktop installer prefetch the
  default voice (Amy) at build time into a read-only bundle directory —
  no clicks, no 60 MB download on first run, no git bloat (voice files
  are still gitignored). Source installs keep the on-demand download path
  from Settings → Voice. Hardening pass on the on-demand fetch alongside:
  Content-Length pre-check, orphan `.part` cleanup on any failure (was
  only on checksum mismatch), split connect/read timeout (60/30 s) so a
  stuck stream doesn't hang the worker, and the voice picker's preview /
  download / retry chips are now real `<button disabled>` elements
  instead of the prior `pointer-events: none` trick.
- **Settings rebuild — Phase 5 (mobile pass, 2026-06-23).** On narrow screens
  (`<md`) the settings side-nav is replaced by a top tab strip: a row of group
  tabs (Account / Kitchen setup / Admin) with the selected group's destinations
  as a horizontally-scrolling chip strip beneath — the active tab follows the
  current page. Desktop keeps the sticky sidebar. (Section rows already
  collapse to label-above-control, the theme grid wraps to one column, and the
  segmented controls scroll — all from Phase 3.) This completes the settings
  rebuild (Phases 1–5).

### Added
- **Dora's neural voice (Piper TTS, 2026-06-23).** Dora can now speak with a
  natural, offline neural voice instead of only the browser's built-in one.
  When "Let Dora speak her replies" is on, the chat assistant reads her replies
  and cook-mode Sous Chef reads each step through the chosen voice; both share
  one `useSpeechOutput` path so they're wired together. Settings → Voice gains a
  **Dora's voice** section: pick the engine (Dora's neural voice vs. your
  browser voice) and choose from a curated catalogue (Amy — the warm default —
  Ryan, Jenny, Kristin, Lessac), each with a **Download** button (voices are
  free, ~60 MB, run on your server) and a **Preview**. The neural voice runs
  server-side via Piper (`POST /api/tts`, `GET /api/tts/voices`). Voice models
  are **downloaded on demand** into the data dir (checksum-verified;
  `POST /api/tts/voices/<id>/download`) — nothing large is committed to git, and
  there are no manual setup steps. The Piper engine itself ships automatically:
  the Docker image installs it and the desktop bundle includes the binary. If
  Piper isn't available the endpoint returns 503 and Dora transparently falls
  back to the browser voice, so she's never silent. New per-user `voice_engine`
  / `voice_id` preferences (migration `c2e9f4a6b8d3`). The prototype `/tts-test`
  page was removed — its preview lives in Settings now. See
  `dora_api/features/tts/voices/README.md`.
- **Profile pictures (Settings rebuild Phase 4, 2026-06-23).** Users can set a
  profile picture on Settings → Account; it appears on the menu-bar account
  button, the Account header, and the admin Users list. When none is set, the
  menu bar keeps its account icon and the larger avatars show initials (the
  existing behaviour). New `User.image` column (migration `a4f7c2e9b6d1`),
  `GET /api/users/<id>/image` bytes endpoint, `image`/`clear_image` on
  `PATCH /api/auth/me` (and the admin user update), `has_image` on the
  current-user + user-list payloads, and a shared `UserAvatar` SPA component.
  Image cap ~4.5 MB (mirrors stock-item images).

### Changed
- **Settings rebuild — Phase 3 (visual rebuild, 2026-06-23).** Every settings
  page sheds its `q-card flat bordered` chrome and adopts a shared
  page-header + `SettingsSection`/`SettingsRow` layout (left-info /
  right-control, modelled on Stripe / Linear / GitHub). The loud
  `q-btn-toggle` controls (Mode / Font / Text size / Cadence / Budget
  period) are replaced by a new `DoraSegmented` with a soft-sunken active
  fill — same family as `DoraTabs`. Theme cards compact to a swatch +
  family name; the blurb moves to a tooltip; active state is a 2px accent
  border + `check_circle` badge. Side nav drops its card wrapper and
  captions, sticks while the main pane scrolls, and gets a 3px accent
  left-edge bar on the active item; the "(admin) only visible to admins"
  banner is retired. Every page now begins with a real `<h1>`-style page
  title; page padding bumps to 28px. Collection pages (Stores / Users /
  Audit log / API access / Vocab editors) share one refresh/primary-action
  shape via the page-header's `#actions` slot. Backend untouched —
  frontend-only refactor.
- **Settings rebuild — Phase 2 (page splits, 2026-06-23).** The two monolithic
  settings pages are broken into focused ones. **Preferences** (was ~1170 lines,
  9 concerns) is now Appearance-only; its other concerns split into new
  **Notifications**, **Money** (money toggle + grocery budget combined),
  **Voice**, and **Nutrition** pages, and the misplaced username/email/password
  forms moved to **Account** (where the section header always said they were).
  **Account** also drops the theatrical "Danger zone" heading (sign-out stands
  alone) and hands "Restart onboarding" to **About**. The admin **System** page
  (was ~760 lines, 5 concerns) splits into **Timezone**, **Alert thresholds**,
  **AI assistant**, and **Features** (the latter absorbs the feature-flag list,
  the scanning/QR toggle, and the Product search URL). **Recipe tags &
  categories** splits into five pages — Cuisines, Categories, Tools, Meal slots,
  Dietary tags — under Kitchen setup, with a nested "Recipe taxonomies" sub-nav.
  Creating/renaming a dietary tag now uses one dialog instead of two sequential
  prompts. All old URLs redirect to their new homes. Still no visual repaint —
  that's Phase 3.

- **Settings rebuild — Phase 1 (IA + routing, 2026-06-23).** The settings
  side-nav reorganises from two groups ("Your settings" + "Admin · global")
  into three: **Account**, **Kitchen setup**, **Admin · global**. Stock
  locations, Stock groups, Recipe tags & categories, and Stores all live
  under the new "Kitchen setup" group; their old URLs (`/settings/stock-*`
  etc.) keep working via redirects so bookmarks survive. Settings now
  lands on **Account** instead of Preferences. Visual look unchanged
  pixel-wise — the visual rebuild is Phase 3. Nav captions dropped (label
  + icon only) per `IMPL_PLAN_SETTINGS_REBUILD.md` §2.7.

### Added
- **Ingestion contract — multipack `pack_count` (FU-232, 2026-06-23).**
  `POST /api/ingest` `products[]` now accepts an optional `pack_count`
  (integer > 0) — the producer-facing other half of the FU-227 multipack
  work. Persists to `Product.pack_count`; the existing convention that
  `size_value` is the TOTAL across the bundle is unchanged.
  `INGESTION_GUIDE.md` + `PROPOSAL_INGESTION_API.md` updated; new
  round-trip pytest in `test_ingest_batch.py`.

- **Multipack prices (FU-227 follow-up, 2026-06-23).** The PriceEntry widget
  gains an "Add pack count (multipack)" disclosure — enter `$4.20`, `125g`
  each, count `4` and the obs is stored as `total_measure=500g` with
  `pack_count=4`. The detail-page obs list now reads "$4.20 for 4 × 125g"
  instead of "500g flat". Shopping-list harvest at `/finish` inherits the
  multipack context from the linked product.
- **US unit pricing (FU-227 follow-up).** New install setting
  `unit_pricing_locale` (default `AU`, optional `US`). Same observation
  shows as `$2.00 / L` under AU and `$1.89 / qt` under US — the AU `/100ml`
  vs `/L` flip becomes the US `/fl oz` vs `/qt` flip; `/100g` vs `/kg`
  becomes `/oz` vs `/lb`. Compute math is locale-independent; only the
  rendered denominator changes. Admin toggles via `PATCH /api/app-settings`.

### Changed
- **"Your prices" feature complete (FU-227, 2026-06-22).** All 8 chunks of the
  pricing-system reassessment shipped end-to-end: shared unit-conversion helper,
  folded observation shape with store + line-provenance FK, the shared
  `PriceEntry` widget (used by the row "log a price" button + detail-page widget
  + shopping-line harvest), server-derived median baseline + "paying more than
  usual" chip, shopping-line prefill, `/finish` harvest, "Receipt" relabel,
  bottom-sheet Full History, per-product Price-History observation overlay, and
  removal of the ingestion → observation path (observations are now in-app
  input only). Adds a new standing engineering rule R-017: features land with
  seed coverage in the same unit of work.

### Added
- **"Full history" price chart for a stock item (FU-227 chunk 6, 2026-06-22).**
  The "Your prices" widget's **Full history** button now opens a bottom-sheet
  chart that overlays the prices you've logged ("your data", solid line + dots)
  with the shelf offers from any linked products ("context", a faint dashed
  line), plus a dashed "usually $X" baseline line — all on one comparable
  per-unit axis (e.g. $/L), so a 2 L offer and a 1 L log line up correctly.
- **Price History page now shows your own prices, not just store offers
  (FU-227 chunk 6).** Each product's card shows "Your usual: $X" with an
  *above usual* chip when the latest is high, and — for products with no offer
  history — the chart now plots your logged prices instead of rendering empty.
- **Prices you enter while shopping become "Your prices" (FU-227 chunk 5, 2026-06-22).**
  The closed loop is wired end-to-end: confirm what you paid on a shopping line
  at the till, then **Finish & restock**, and Dora harvests one price record per
  priced line onto the matching stock item — no separate logging step. A sized
  product (e.g. 2 × 2 L milk) is recorded as a measure (per-L) observation; a
  sizeless line as a count (per-item) one. Finishing twice is safe — the harvest
  is idempotent and never double-counts.
- **Shopping lines suggest a price (FU-227 chunk 5).** Each line now shows where
  its price would prefill from — *"from your last receipt"* when you've bought
  the item before, otherwise *"from <store> offer"* — so the common case at the
  till is confirming one number. The suggestion is resolved server-side; it's a
  starting point and persists when you edit it.

### Fixed
- **"Current shelf prices" sidecar now actually appears (FU-227 chunk 6).** The
  offers sidecar on the "Your prices" widget read the linked products' offers
  through a `noload` relationship, so it was always empty. Linked-product offers
  are now eager-loaded, so an item linked to products with current offers shows
  the "Current shelf prices: $X at Y" line as designed (LC-2).

### Changed
- **A finished list is a "Receipt" when money is on (FU-227 chunk 5).** The
  status badge on a done list reads "Receipt" instead of "Done" once money
  surfaces are enabled — a label swap only; nothing about the list changes.
- **Finishing is the only way to complete a list (FU-227 chunk 5).** A list now
  becomes *done* exclusively via **Finish & restock** (which snapshots prices,
  harvests observations and restocks). The old generic `PATCH status=done`
  back-door is gone — it returns a clear error pointing to finish. draft⇄shopping
  edits are unaffected.

### Changed
- **Preferred buys are alphabetical, no manual order (FU-225, 2026-06-18).** The round-3
  stock-item-detail polish dropped the manual reorder UI; the backend now matches. The
  `PreferredBuy.position` column was dropped (migration `b5d8a2f4c9e7`), the
  `PATCH /stock-items/<id>/preferred-buys/reorder` endpoint was removed, and the SPA's
  `reorderPreferredBuysAsync` method went with it. Server- and client-side both sort
  case-insensitively by label.

### Changed
- **API: naive datetimes serialize as UTC (2026-06-18).** `DoraJSONProvider`
  now tags timezone-naive `datetime` values with a trailing `Z` on the way
  out. SQLite strips tzinfo from `DateTime(timezone=True)` columns on
  read, so values stored as `datetime.now(UTC)` came back naive and the
  SPA's `new Date(iso)` parsed them as local time — every "X ago"
  display was shifted by the user's UTC offset (a Sydney user saw
  "10 hours ago" no matter how recently the value was written). Every
  relative-time display across the app reads honestly now.

### Changed
- **Stock pages — feedback round 3 (2026-06-18).** Design polish round
  on top of the UTC fix:
  - **Image-toggle button reads as active** when images are shown
    (`color="primary"`).
  - **Splitter divider is a clean coloured vertical bar.** The
    gripper-dot motif is gone; the bar is muted text-tinted while
    peeking and brightens to accent on hover. Cursor change carries
    the draggability signal.
  - **`RowActionButton`** — new shared component that pins the row
    cluster's `flat dense round size="md"` style. Adopters: stock-row
    expiry / essential / open + `AddToListButton` row variant. Stops
    the size/shape drift the previous round flagged.
  - **Export button now rides BaseButton** (`variant="secondary"`)
    instead of `q-btn-dropdown`, so it sits flush with the other
    toolbar buttons.
  - **Rows slightly shorter** — `min-height: 64 → 56`, image tile
    `56 → 48`, body padding tightened — without losing the breathing
    room from round 1.
  - **Notes** gets a real outlined autogrow input (placeholder reads as
    "Anything you want to remember about this item") instead of a
    bare dash.
  - **Preferred buys alphabetised**; the manual reorder buttons are
    gone (these are reminders, not a ranking). Backend `position` +
    reorder endpoint stay so historical data isn't disturbed
    (deprecation backlog).

### Changed
- **Stock pages — feedback round 2 (2026-06-18).** Fixes and finer polish
  on the round-1 pass:
  - **Level updated really updates now.** Backend `update_stock_item.py`
    was hitting the same `lazy="noload"` trap on `stock_level` as the
    location/group fix — the FK column never went dirty on the
    boundary case, and the timestamp bump silently didn't land. The
    FK column is now written directly. SPA picks up the change via the
    next refetch.
  - **`useReactiveNow` composable.** A shared 30s-ticking `nowMs` ref so
    `relativeTime("…")` drifts forward as time passes ("just now" →
    "1m ago" → …) without needing the source DTO to re-fetch.
  - **Splitter gripper sticky.** The triple-dot handle now uses
    `position: sticky; top: 50vh` inside the separator so it stays
    reachable when the list overflows the viewport.
  - **Padding on the q-tab-panel.** Overview tab's inner content
    (image, editors) now has consistent `q-pa-md` breathing on every
    side.
  - **Peek panel grows naturally.** Dropped the `max-height: 80vh`
    independent scroll on `.stock-peek`; the page handles overflow
    instead, so the embedded header stops being hidden under a
    competing scroll.
  - **DoraTabs hover** matches the main menu — text colour transitions
    to accent on hover, no surface tint.
  - **Footer counts** use the picker palette exactly (Well-stocked
    green, Sufficient yellow, Low red, Out grey). "Auto-add" is
    neutral (matches "Shown"). "Flagged" renamed to **"Essential"** in
    the footer and on the FilterChip — same wording as the field on
    detail / the row tooltip / the row button. New optional `group`
    on `PageCount` drives a three-cluster `justify-evenly` layout:
    [Shown] · [stock levels] · [other counts].
  - **Row buttons consistent.** Every right-cluster button (expiry /
    essential / open / cart) is `flat dense round size="md"`. The
    essential flag is now an **interactive toggle** (active state in
    the warning tone). The cart button picks up `round` + `md` to
    match.

- **Stock pages — feedback pass (2026-06-18).** A focused polish round on
  Stock Item Detail and Stock Overview based on user feedback:
  - **DoraTabs** — a new shared tab strip with the same sliding accent
    indicator (wobble + flash on switch) used by the main menu, shrunk
    to tab-row scale. Replaces `q-tabs` on Stock Item Detail, Data →
    Barcodes & QR, and Help. Inactive tabs use default text colour;
    the indicator carries the colour work (less per-tab saturation).
  - **Stock Item Detail header pared back.** Removed the secondary
    toolbar row (Mark open / Set expiry / Add to list) — all three
    actions live inline on the page already. Header keeps back/name,
    Show QR (when scanning is enabled), and Delete.
  - **Level picker moved under Name** on the Overview tab, with
    "Updated X ago" beside it (combining the old chip + the bottom
    "Level updated" row into one obvious spot).
  - **"Set" label on the expiry row's calendar button** so the inline
    +1d / +7d / +14d / Set / × cluster picks up the responsibility of
    the deleted top-toolbar Set-expiry button.
  - **Notes** now reads as a regular field row (autogrow inline input)
    rather than a separate calm-textarea block.
  - **Placeholders use a dash** (`—`) instead of `Not set` across
    Location / Stock group / Usual store / Expiry / Level.
  - **Location & stock-group clear actually persists.** The
    relationships are mapped `lazy="noload"` so a relationship-only
    `None` assignment was a silent no-op and the picker rebounded to
    its previous value. New explicit `clear_stock_location` /
    `clear_stock_group` flags drive the FK column directly; the SPA
    routes the picker's X through them. Same mechanism that already
    backed `clear_usual_store`.
  - **Splitter** — opens at 58% (was 50%, per user preference) and the
    handle is now a styled gripper-dot motif that paints only while a
    peek is open, with an accent hover treatment that reads as
    draggable.
  - **Filter toggle lives in the page toolbar.** New
    `FilterToggleButton` companion to `FilterBar` lets pages embed the
    toggle (with badge + Clear) in their main toolbar; `FilterBar`
    takes `:toolbar="false"` and collapses to just the slide-out
    panel. Applied to Stock Overview, My Products, Cookbook overview.
  - **Stock Overview row polish** — more spacing between image /
    level / name; right-cluster buttons bumped to `size="md"`; recipe
    count chip removed (visible on the Recipes tab of the detail
    page); hover treatment swapped from a translateY lift (which
    clipped the first row's outline under the page chrome) to a
    surface + border accent tone; essential items now carry a
    warning-toned left-edge stripe AND a flag icon in the right
    cluster; the open / in-use button uses primary tone when open so
    its state pops in dark themes (was secondary, low contrast).
  - **Footer counts** — "Shown" reverts to the default text colour
    (a neutral cardinal shouldn't compete with the colour-coded level
    / flagged / attention counts). Applied to all PageCountsFooter
    consumers.

### Added
- **Stores (admin) replaces the legacy Merchants page (FU-189 / Phase E).**
  New `Settings → Stores` admin page lets you curate the retail stores Dora knows
  about (CRUD + per-store logo upload). Dora ships **zero pre-seeded stores** and
  never auto-creates one from the ingestion path (FU-190); when no logo is
  uploaded, a deterministic hash-swatch + initial pill fills in.
  Stock items now carry a **"Usual store"** picker on the detail page
  (`usual_store_id`). Plus all surfaces that previously talked about "merchants"
  now read as "stores" — `Spend by store` report, `Group by store` on shopping
  lists, `purchased_store_id` on shopping-list lines, etc. The producer's SKU
  code field (`merchant_stockcode` on `Product`) is intentionally retained
  verbatim — that's a producer code, not a reference to the renamed entity.

### Changed
- **Stores hydrate lazily; `boot/stores.ts` deleted (R-016 / ADR-011).**
  `web_app/src/boot/stores.ts` previously `await`ed an API health check + three collection
  fetches (`productStore`, `stockItemStore`, `stockLevelStore`) at module scope, blocking the
  router/app shell until everything resolved. The file is now **gone** — and removed from
  `quasar.config.ts`'s `boot:` array. The API-reachability surface it covered is already owned
  by `authStore.bootstrapAsync()` in `App.vue` (the splash screen surfaces the error visually
  with a Retry button — a better UX than a toast). Pages own their own data hydration via a new
  `ensureLoadedAsync()` method on each store, which no-ops if data is cached and dedupes
  concurrent first-time loads; bare `getXAsync()` remains the explicit force-refetch for
  post-mutation refresh and pull-to-refresh. User-visible impact: faster perceived startup on
  cold/slow API, no wasted bandwidth re-fetching the post-Phase-D product catalogue no surface
  reads.

### Removed
- **In-app live product search is gone (Phase D / FU-186).** Dora no longer scrapes retailer
  sites or runs the standalone `merchant_api` backend; the "Product Search" page and the admin
  "Merchants" scraper-provider settings page are retired. The retailer-scraping side lives in a
  sibling project the operator runs themselves; it pushes data into Dora through
  `POST /api/ingest` (the C-10 ingestion seam). The standalone `emailer/` weekly-deals service
  retired alongside it.

### Added
- **Product Search nav opens an admin-configured URL (Phase D / FU-186).** A new install-wide
  setting under **Settings → System → Product search** (admin only) lets the operator point the
  in-app "Product Search" nav entry at whatever search surface they run themselves. The entry is
  hidden when no product data is present, disabled with a "set up in Settings" hint when products
  is on but no URL is configured, and opens the configured URL in a new tab otherwise. The
  destination is never named in the app.
- **Power-user docs for sourcing product data (FU-212).** New
  [`docs/INGESTION_GUIDE.md`](docs/INGESTION_GUIDE.md) covers minting an API key, the store-mapping
  step (no auto-create), and the full `POST /api/ingest` contract — for admins who want to populate
  the product layer themselves. Not surfaced to end users; producer kept unnamed throughout.
- **Admin "API access" page — bearer-keyed ingestion seam (C-10, Phase B).** A new admin Settings
  page mints, lists, relabels, and revokes bearer keys that an external source uses to push data
  into Dora via `POST /api/ingest`. Each key shows accepted/skipped/failed counters + last-used,
  plus a per-source "Store mappings" panel where the admin links each pushed store name to one of
  Dora's existing merchants. **Stores are never auto-created (FU-190):** an unknown name skips the
  record and surfaces as **pending** for the admin to map. The endpoint is batched and accepts
  products, offers, and price observations; an `Idempotency-Key` header makes a re-send a no-op;
  bad records report per-record without failing the batch. The producer/companion is **never
  named** anywhere in the app (PROPOSAL_INGESTION_API invisibility rule). Migrations
  `d6f8a3b9c1e2` (IngestionSource), `e7a1c3b8d5f4` (IngestionStoreMapping, IdempotencyKey,
  `ProductHistoricOffer.source`).

### Changed
- **Adding a duplicate product now records the new price instead of erroring (FU-217).**
  `POST /api/products` used to reject a second submit for the same product with a 422
  "already exists". It now appends a new historic price point + moves the catalogue's current
  offer to the new value (the same offer-append path `/api/ingest` uses) and returns 201 with
  `{id, created: false, offer_appended: true}`. So manual product-add accrues price history just
  like ingestion does.
- **Onboarding's hero loop is honest now (FU-210 revisit).** The cinematic Story stage
  with the hero loop stays; the dimmed "Spend smarter — coming soon" satellite node
  (LOOP_INSIGHT) is gone — it advertised an unbuilt feature. The Finish step's loop recap
  is also dropped (Story already plays it). The persona-preview chips inside the loop are
  re-framed from persona identities ("Cooking" / "Spend" / "Everything") into outcome chips
  ("Mostly cooking" / "Watching spend" / "All of it") — they're illustrative only, set
  nothing, and exist to show how Dora emphasises different reasons for using it.
- **Stock value & recipe cost now also use the prices you've logged (FU-216).** If a pantry item has
  no linked product but you've logged what it cost (the FU-213 Prices section), that price now feeds
  the stock-value report and recipe cost estimates — so the numbers reflect your own price memory,
  not only linked-product offers.
- **Onboarding is now one simple "show everything" path — no setup personas (FU-210).** First-run
  no longer asks you to pick "Cooking / Spend tracking / Everything" (or Customise) up front.
  Everyone gets the same intro, starter packs, household headcount and finish — and you turn
  individual features (like spend tracking) on in **Settings** whenever you want. (The hero-loop
  preview illustrating how Dora shapes for different needs stays for now.)
- **Products now appear automatically when you have product data — there's no on/off switch
  (products-as-overlay groundwork, FU-209).** The admin "Products & prices" toggle is gone; the
  product surfaces (My Products, Price History, the stock-item Products tab, the cart's product
  behaviour, best-deals) show whenever product data exists in the install and stay hidden
  otherwise. Onboarding no longer shows the "stock items vs products" explainer, and the setup
  personas no longer toggle products. (Backend: `AppSetting.products_enabled` dropped — migration
  `f1a2b3c4d5e6`; `GET /api/health` `features.products` is now derived from whether any `Product`
  exists. First step of the change designed in
  `docs/04_proposals/PROPOSAL_PRODUCTS_AS_OVERLAY.md`.)

### Fixed
- **Linking a product to a stock item from My Products now works (FU-208).** The "Link…" dialog
  previously dropped you on the stock item with nothing actually linked; it now links the product
  in place and refreshes.

### Added
- **Log what things cost you, on the stock item (FU-213).** With spend tracking on, each stock item
  has a **Prices** section: log the **total you paid** + how much you got (qty + unit) and Dora works
  out the **per-unit cost** for you — no dividing. It's your own price memory (no merchant or product
  needed), shown only when spend tracking is enabled. New `StockItemPriceObservation` table
  (migration `b3d5f7a9c2e4`) + `/api/stock-items/{id}/price-observations`.
- **Use your "preferred buys" as shopping-list hints (FU-215).** On a shopping list, a line for a
  stock item that has preferred buys now offers a **hint picker** — tap to mark which one to grab
  (e.g. "Vitasoy Oat Milky 1L"); it's just a reminder, no price/product attached. New
  `ShoppingListLine.preferred_buy_id` (migration `c4e6a8b1d3f5`).
- **Remember what you actually buy — "Preferred buys" on a stock item (FU-211).** Each stock item
  now has a **Preferred buys** list: type the things you actually buy for it (e.g. "Vitasoy Oat
  Milky 1L") as free-text reminders — add, rename, reorder and remove them. It's a personal memory
  aid, not a product/price, and it's always available (no feature flag). New `PreferredBuy` table
  (migration `a2c4e6f8b1d3`) + endpoints under `/api/stock-items/{id}/preferred-buys`. Surfaced as
  shopping-list hints via FU-215.
- **Push notifications on this device (Alerts C-9.8 — Phase C).** Settings → Preferences
  has a new **Push notifications** card: turn it on and Dora delivers a system
  notification the moment a new **actionable** alert fires (FYI nudges stay in the hub +
  email digest so a quiet device doesn't buzz for low-signal items). One subscription per
  browser/device — you can subscribe on every device independently. The card surfaces
  the full lifecycle in its caption: VAPID-not-configured, browser-unsupported,
  permission-denied, subscribed-here. Same dedup rule as the email channel: each alert
  pushes once, then again only after it clears and re-fires. Dead subscriptions (revoked
  / 404'd by the vendor) are pruned automatically. New `PushSubscription` table
  (migration `e9a4b6c2d8f1`); new `AlertInteraction.last_pushed_at` paired with
  `last_emailed_at` (migration `d7b3e2a1f4c5`); new endpoints
  `GET /api/alerts/push/vapid-public-key`, `POST /api/alerts/push/subscribe`,
  `POST /api/alerts/push/unsubscribe`. Standalone push-only service worker at
  `/push-sw.js` (independent of Quasar's PWA Workbox chunk). Hourly evaluator at :30.
- **Email me my alerts (Alerts C-9.7 — Phase B).** Settings → Preferences has a new
  **Alerts email digest** card: turn it on and Dora emails you the same actionable list
  you'd see on the Alerts page, **daily** or **weekly** on a day of your choosing. The
  same alert won't email twice in a row — it only resends after the condition clears and
  re-fires. The digest mirrors the in-app hub exactly (one canonical source for "what
  counts"). The card is **shown-disabled until SMTP is configured** on the install
  (R-014), so a self-hosted box without email surfaces "ask an admin" instead of
  silently swallowing opt-ins. New `User.alerts_email_enabled` / `alerts_email_cadence`
  / `alerts_email_day` (migration `b8e5d2f1c9a3`); new `AlertInteraction.last_emailed_at`
  for delivery dedup (migration `c4f9a8b3e2d6`). Job runs at 07:00 on the existing
  background scheduler.
- **A "you're all set" finish (Onboarding C-5.6).** Onboarding now ends on a celebration — a
  **confetti** moment, a **recap of the loop** (the same interactive diagram from the intro), and
  **flow-cards** for the areas that matter to your setup (pantry, recipes, meal plans, shopping,
  alerts, price history when spend is on, and Dora's guides) — each jumping straight into that area
  or its help guide. Reduced-motion users get the calm version (no confetti).
- **Starter packs for a faster start (Onboarding C-5.5).** The setup step now offers **starter
  packs** of common items (Fridge staples, Pantry basics, Fruit & veg, Freezer, Cleaning &
  household) — tick a whole pack or expand it to choose individual items, all pre-grouped and
  located. Items you add show in a **slim "added" list** you can prune, and everything is created
  only when you press Finish (bailing creates nothing). First-item group/location pickers now offer
  the seeded defaults by name, so a brand-new pantry can be categorised straight away. New
  `GET /api/onboarding/catalog` + idempotent `POST /api/onboarding/seed-items`. *(Opt-in demo data
  is coming separately.)*
- **Tell Dora your household size (Onboarding C-5.4).** Onboarding now asks **"How many people do
  you usually cook for?"** — and **cook mode opens pre-scaled to that number** instead of each
  recipe's default servings (you can still nudge it per cook). Leave it blank and cook mode behaves
  as before. New `User.household_headcount` (nullable; migration `e2a9c5f1b7d4`), saved via
  `PATCH /api/users/me`.
- **Pick what Dora does for you, at setup (Onboarding C-5.3).** First-run now has a **persona
  step** (first user / admin): choose **Pantry & cooking**, **Pantry + spend tracking**, or
  **Everything** — or **Customise** to flip individual features yourself. Your pick sets the
  install's feature flags + your own money/nutrition preferences, applied in one go when you
  Finish (bailing changes nothing).
  - New install flag **`products_enabled`** (default **on**, so existing installs are unchanged) —
    the **Cooking** persona turns the products/prices layer off. It joins the existing feature-flag
    machinery (admin `PATCH /api/app-settings`, `GET /api/health` `features.products`); migration
    `d1f4b8c3e7a9`. *(Per-surface hiding when products are off is tracked separately and not part of
    this change.)*
  - When products are on, a short **"stock items vs products"** explainer ("Milk" is a stock item;
    "Vitasoy Oat Milky 1L @ Coles" is a product) appears before you add items; the Cooking persona
    skips it for a shorter setup.
- **A cinematic first-run intro (Onboarding C-5.2).** First-run now opens on a short, skippable
  "here's what Dora does" story instead of dropping you straight into a form:
  - **Three big, minimal scenes** (the problem → Dora is the brain → you're in control) wrapped
    around a **hero "loop" diagram** — a ring of Stock → Plan → List → Shop → Restock → Cook with
    **Dora at the centre**. It draws itself once, then every stage (and Dora) is **tappable** to
    see what it does and how it hands off to the next.
  - A **persona preview** under the loop (Cooking / Spend / Everything) lets you see how Dora
    shapes for each, before you choose — purely illustrative here; the actual choice comes later.
  - A persistent **progress rail** spans the Story and Setup sections so you can **jump anywhere,
    nothing gated**, and **"Skip to setup"** / **"Skip"** are always one tap.
  - Fully **keyboard-navigable** and honours **reduced-motion** (no autoplay, the final state is
    shown). Reuses the existing Dora mascot + motion tokens; the loop component is built to be
    reused at the finish step later.
  - *Note: the loop's sell-copy is provisional and will be reconciled against real app behaviour
    before it's considered final.*
- **Onboarding quick wins (Onboarding C-5.1).** First-run setup got safer and clearer:
  - **Nothing is saved until you press Finish.** Your name, theme, font, the default
    group/location seeds, and any first stock items you add are now collected as you go and
    applied in one step at the end — so bailing out part-way (the **"Skip"** button, renamed
    from "Skip everything") leaves your account exactly as it was, instead of silently keeping
    half your choices.
  - **Theme picker is just System / Light / Dark** here, mapping to Dora's brand palettes
    (Light → Pesto, Dark → Pesto Dark); the full palette catalogue stays available later in
    Settings → Preferences.
  - **Import copy no longer name-drops a specific app** ("import from a spreadsheet or another
    app"), and still links straight to the importer.
- **An "Upcoming" fortnight timeline on the Alerts hub (Alerts C-9.6).** The Alerts page now
  looks *ahead* with a two-week mini-calendar: each day shows coloured dots for what's coming —
  expiries, planned shopping days, and planned meals — and clicking a day expands the detail with
  one-tap links to the item, the list, or the recipe. The window and aggregation are computed
  server-side against your household's timezone, so "the next 14 days" is right wherever the
  server lives. New `GET /api/alerts/upcoming`.
- **Price watches on the Alerts hub (Alerts C-9.5).** Your armed "notify me below $X" price
  alerts now show up in a dedicated **Price watch** region on the Alerts page — each one listing
  the product, merchant, your target price, and when it last alerted, with a one-click jump back
  to the price-history explorer and a Remove button. Set new watches where you always have (the
  explorer); the hub is now where you see and manage them all in one place. The region only
  appears when the money/deals feature is on.
- **Forward-looking alert nudges (Alerts C-9.4).** Alerts now look *ahead*, not just at what
  already broke. Two new (FYI, default-on, per-person dismissable) kinds:
  - **"No meals planned for next week"** — a single gentle nudge when next week's planner is
    empty, clearing the moment you plan a meal for that week. Computed against your household's
    timezone so the week boundary is right wherever the server lives.
  - **"Shopping day coming up"** — a reminder for any not-yet-finished list whose planned shop
    date is within the next few days, deep-linking straight to that list and clearing once the
    list is done. Reads the planned-shop-date you already set; no new setup.
  Both render through the same alert row as everything else, carry their own icons, and appear
  in the bell, the Alerts hub, and the dashboard attention card — clicking one opens the planner
  or the list rather than a stock item.
- **A proper Alerts control centre (Alerts C-9.3).** The Alerts page is now a real hub:
  **summary tiles** (an at-a-glance "5 expiring soon · 2 expired" per type), the full **active
  list grouped by priority** with per-type icons and read items dimmed, a **Mark all read**
  control, a **Manage** panel to turn any alert kind off or move it between the badge-counted
  "Needs action" tier and "FYI" (the C-9.2 preferences, now with a UI), and a collapsible
  **History** of what you've read, snoozed, or dismissed. The bell becomes a fast **peek +
  jump**: the top few rows with their key action, the bulk "add low/out to my list" shortcut,
  and an **Open Alerts** button to the hub — no more two competing alert surfaces.
  - Shared `AlertRow` / `AlertList` components back both the bell and the page (one source of
    truth for how an alert renders); new `GET /api/alerts/history`.
- **Tune which alerts shout and which whisper (Alerts C-9.2).** Set **per-person alert
  preferences** — turn any alert kind off, or move it between the badge-counted
  "actionable" tier and the quieter "FYI" tier — so the bell is as noisy or as calm as
  *you* want, without changing what anyone else sees. Disabling a kind drops it from your
  list and your badge (and, later, your notifications); promoting a kind to actionable
  bumps your badge. Admins also get **household-wide alert thresholds** in
  Settings → System: the **expiring-soon window** (how many days ahead counts as "expiring
  soon") and a **default stocktake reminder** pre-filled on new items. The expiring-soon
  window now flows from one place into both the alerts list and the location heatmap, so
  changing it re-tunes them together.
  - New `AlertPreference` table (migration `b1e7d3f9a2c4`) + `GET`/`PATCH /api/alerts/prefs`
    (per user); `expiring_soon_window_days` + `default_days_until_stocktake_alert` added to
    app settings. *(The user-facing manage panel lands with the alerts hub page in a later
    C-9 chunk; this chunk ships the engine + the admin thresholds.)*
- **Alerts now remember what you've seen, snoozed, and dismissed (Alerts C-9.1).**
  Alert read/unread, snooze, and dismiss are now **saved server-side per user**, so they
  follow you across devices instead of living in one browser — snoozing on your phone
  hides the alert on your laptop too. And the **bell badge now matches the list**: it
  counts the **actionable** alerts (high + medium) actually shown, derived once on the
  server and respecting your snoozes/dismissals, so the "I see 6 but the bell shows 10"
  mismatch is gone. Low-severity items still appear as a clearly-separate FYI tier; they
  just don't inflate the badge.
  - New endpoints: `POST /api/alerts/<id>/read` · `/unread` · `/snooze` · `/dismiss`,
    `DELETE /api/alerts/<id>/suppression`, `POST /api/alerts/read-all`. Alert ids are now
    scoped keys (`stock:<id>:<kind>`) so non-stock alerts can join later. New
    `AlertInteraction` table (migration `f4d2a9c7b3e1`). *(In-app behaviour now; the
    read/dismiss/history UI and the email/push channels land in later C-9 chunks.)*
- **"Plan step-by-step" guided builder (Meal Plans C-2.J).** A guided flow for
  fresh-cooks: **pick** the meals you want this week → **see what you'd need to
  buy** (in-stock vs to-buy, computed with the same scaling as the saved-plan
  shopping list) → **build** the week (meals spread across the upcoming days) and
  **generate the shopping list** in one step. The finished step offers Print;
  emailing the plan is flagged as coming soon. Cancelling writes nothing.
  - New `POST /api/meal-plans/preview-ingredients` (aggregates an *unsaved*
    recipe selection via the shared ingredient-scaling function).
- **Meal-plan template sets + recurring planning (Meal Plans C-2.G).** Build a
  **rotating set** of templates (e.g. "Week A → Week B → repeat") on a new
  **Manage templates** page, and **apply recurringly** over a date range from
  the planner: each week is forked from the template (a set rotates through its
  templates week-by-week), past days skipped, up to 26 weeks. The Manage page
  also lets you rename / clone / delete templates and create / reorder / delete
  sets.
  - New `MealPlanTemplateSet` / `MealPlanTemplateSetItem` tables +
    `GET/POST/PATCH/DELETE /api/meal-plan-template-sets`,
    `POST /api/meal-plans/from-template/recurring`, and
    `POST /api/meal-plan-templates/<id>/clone`;
    `MealPlan.source_template_set_id` + `rotation_index` provenance. New page at
    `/meal-plans/templates`. Migration `a3c9e7b2f5d8`.
- **Meal-plan templates (Meal Plans C-2.F).** Save a week's meals as a reusable
  **template** and fork it onto any other week. The planner's right column gains
  a Templates card: **"Save this week as a template"** (name + optional
  description) captures the focused week's meals by day-of-week + slot;
  **"Apply a template…"** forks a chosen template onto the week you're viewing —
  **past days are skipped automatically**, and if the week already has planned
  meals you're warned before they're replaced. Editing or deleting a template
  never changes a week already created from it (it carries the template only as
  provenance).
  - New `MealPlanTemplate` / `MealPlanTemplateEntry` tables + `GET/POST/PATCH/
    DELETE /api/meal-plan-templates` and `POST /api/meal-plans/from-template`;
    `MealPlan.source_template_id` provenance. Migration `f2b8d4c6a1e3`
    (SQLite + Postgres portable).
- **Household timezone — correct "today" anywhere (Meal Plans C-2.K).** A new
  **Settings → System → Timezone** picker sets the household's IANA timezone
  (with a "Use this device's timezone" shortcut). The meal planner's date
  boundary — which days are in the past, what "today" is — is now worked out in
  that timezone on the **server**, so it's correct no matter where the server is
  hosted (e.g. an Australian household on a US-hosted server no longer sees the
  wrong day). Fixes the past-day-drop error where dropping a recipe near
  midnight could be rejected as "in the past".
  - New `AppSetting.timezone` (defaults to UTC) + `GET /api/meal-plans/today`;
    the meal-plan past-day rules and the consumed-meal reconcile sweep all
    evaluate "today" in the household zone. The planner trusts the server's
    date rather than the browser clock. Bundles `tzdata` so named zones work on
    Windows/desktop too.
- **Meal-slot vocabulary — household-wide & editable (Meal Plans C-2.A).**
  The meal-time slots (Breakfast / Lunch / Dinner / Snack / Dessert) are no
  longer a hard-coded constant — they're now an editable **household-wide
  vocabulary**, managed in **Settings → Recipe vocab** alongside Cuisines /
  Categories / Tools (a 4th card on the same `VocabListEditor`). You can add,
  rename, reorder (up/down), and delete slots.
  - New `MealSlot` `{name, sequence}` table + `GET/POST/PATCH/DELETE
    /api/meal-slots` (+ `PATCH /reorder`), mirroring the existing recipe-vocab
    CRUD. Seeded with the five defaults via a reversible migration
    (`b9f6d3a8c1e2`), SQLite + Postgres portable.
  - The planner's meal-plan edit dialog and every recipe `time_of_day` picker
    now read the household list (the planner dialog had silently dropped
    "Dessert" — restored).
  - **Slots are stored by name, not by foreign key:** meal-plan entries and
    recipes keep the slot *label*, so **deleting a slot never alters existing
    entries** (they keep their label, just drop out of the picker). New writes
    referencing an off-vocabulary slot are rejected at the API.

### Changed
- **Stock item detail — History tab is now an actual lifecycle.** The old level-only log on the
  **History** tab is replaced by a unified **item lifecycle timeline** — level changes (with
  inferred context like "Restocked → Well-stocked" or "Dropped to Low"), **waste events** you've
  logged (with reason + estimated value + your note), **past list-adds** with their provenance
  ("Auto-added: low stock → Tuesday shop"), and synthesised **Opened** and **Checked** entries
  from the item's current state. Each entry is colour-coded by event kind so the
  purchase → use → waste → restock loop is scannable at a glance. (Closes the Stock Item Detail
  cluster — feedback A-1.)
- **Stock item detail — Recipes, Lists and Substitutes tabs do what they look like they do.**
  On the **Recipes** tab, the heart icon now actually toggles the recipe's favourite, and
  **"Add all to list"** on a cookable recipe drops every ingredient onto your primary draft (both
  were dead before — feedback L132 / L134). On the **Shopping Lists** tab, the inert little arrow
  on each row is gone (the whole row was already clickable) and **"Primary"** shows as a real
  badge next to the primary draft's name instead of plain text. On the **Substitutes** tab, the
  per-row **"Swap into list"** button is gone — that affordance is being relocated to **Shop
  Mode**, where "this is out at the shelf, swap to a substitute" is the moment it actually helps.
- **Stock item detail — Products tab does the right thing in every state.** When you haven't
  linked any products yet, the **Products** tab now leads with a clear **"Find & link a product"**
  CTA (instead of a quiet "no products" line) — one click takes you to product search, seeded with
  this item's name. When products exist, the header carries a quieter **"Link another"**. The
  **cheapest** linked product is now visually highlighted (chip + tint) instead of needing a
  separate "Add cheapest" shortcut — use the cheapest card's own Add-to-list. When the Products
  feature is **turned off** (Cooking persona), the whole **Products tab disappears** — no empty
  state, no orphan price chrome; the page reads as a clean pantry + cooking detail.
- **Stock overview peek opens at 50% and can't be squished.** When you open a stock item's peek
  panel from the overview, it now opens at a balanced **50/50 split** (was 58/42) and the drag
  splitter is clamped so neither pane can be squashed below ~40% or grow past ~65% — both sides
  stay usable. With no peek open, the list still goes full-width.
- **Stock item detail — directly editable, much less messy.** A stock item's detail page is now a
  single-column overview where **every fact is its own editor** — click and type, no more separate
  "facts on the left, edit form on the right" split. The **level chip in the header is the editor**
  (no duplicate row), **Delete** moves to a quiet top-right slot, and the toolbar pares down to the
  things you actually use mid-pantry: **Mark open · Set expiry · Add to list · (Show QR)**. The
  Overview adds an inline **Stock group** picker (previously you couldn't set it from here at all),
  an **× clear** on Expiry with **+1d / +7d / +14d** quick-bumps, an **Opened toggle on the row**,
  and an **info tooltip** explaining opening doesn't change the expiry date. **Notes** are kept but
  calm at the bottom (cheap, occasionally useful — not a headline). Tabs go through theme tokens so
  the active tab is legible in every theme, and **Show QR** has a tooltip clarifying it's Dora's own
  per-item label, not the product's real barcode.
- **Stock — searchable location pickers everywhere, tidier buttons.** A stock item's **location
  picker** and the **stock overview's "Any location" filter** are both now **searchable** and list
  each option by its **full path** ("Pantry › Middle shelf › Left side"), so you can tell two "Left
  side" shelves apart. The image buttons on the detail page have a little more breathing room, and
  the toolbar **"Add to list"** button now matches the other toolbar buttons instead of looking like
  an odd one out.
- **Meal Plans recipe trays (Meal Plans C-2.I).** The planner's recipe list now
  groups into collapsible trays above the full list: **Favourites**, **Haven't
  had in a while** (never cooked or not in 21 days, oldest first), and
  **Frequently planned** (your household's most-planned recipes). Searching
  collapses to a single results list. The "haven't had" window and the
  "frequently planned" ranking are computed on the server (so the rule lives in
  one place), with the 21-day window evaluated in the household timezone.
- **Meal Plans shopping sidebar — per-item add, list status, hover-highlight (Meal Plans C-2.H).**
  Each ingredient you'll need to buy now shows **whether it's already on a
  shopping list** ("on Groceries" / "not on a list") and gets its own
  **add-to-list button** (the same one used across the app, so it knows what's
  already on a list and opens the list-picker when there's a choice). Hovering an
  ingredient (desktop) **highlights the meals in the week that use it**. The
  per-item stock-status colours now use the **app-wide** stock-level palette, so
  they match the Stock and Cookbook pages instead of a planner-only colour set.
- **Meal Plans — nameless week-plans + no more create/edit dialog (Meal Plans C-2.E).**
  A meal plan no longer has a user-typed name (feedback flagged it as useless) —
  a week is identified by its dates ("Week starting …"). Consequences:
  - **Creating is implicit:** navigate to any week and tap a slot + a recipe;
    the week's plan is created automatically. The **"New plan" button and the
    whole add/edit-entries dialog are gone** — servings and slot are edited
    directly on the meal chips.
  - **"Clear this week"** removes the focused week's plan; "Delete plan" as a
    concept is retired.
  - Backend: `MealPlan.name` is now nullable (migration `e1f7b3d9a2c4`,
    batch-mode, SQLite + Postgres); the create endpoint accepts a missing name.
    Existing named rows keep their name (ignored by the UI). Generated shopping
    lists are named "Meals: week of <date>".
- **Meal Plans calendar widget (Meal Plans C-2.D).** The right column gains a
  compact **month calendar** above the shopping summary: ~6 week-rows of small
  rounded day-squares with **status underlines** — green = planned, amber = a
  meal that day still needs cooking, dotted-grey = all cooked — plus a dot on
  today and a brand-coloured outline around the week you're viewing. Click any
  week to jump the carousel to it (they stay in sync); the month banner +
  earlier/later arrows let you browse. The focused week is now remembered in the
  URL (`?monday=…`), so a refresh lands you back on the same week, and the old
  "Jump to a plan" dropdown is gone.
- **Meal Plans planner rebuilt — vertical week carousel + tap-to-add (Meal Plans C-2.C).**
  The planner is now a three-column workspace: a searchable **recipe list** on
  the left, a **vertical week carousel** in the middle, and the shopping summary
  on the right.
  - **Week carousel:** up/down arrows (plus ↑/↓ keys and mobile swipe) move
    between weeks with a slide animation that respects "reduce motion". Each week
    is a vertical stack of day cards, and each day shows **named meal-slot rows**
    (Breakfast / Lunch / Dinner / … from your household vocabulary; off-vocab
    historical entries gather under "Other").
  - **Tap to add (no more drag-only, no more always-"Dinner"):** tap a day's
    slot to target it, then tap a recipe — the entry lands in *that* slot, so the
    long-standing "everything becomes Dinner" bug is gone by construction. Adding
    the same recipe to the same slot bumps its servings instead of duplicating.
    Desktop users can still drag a recipe onto a slot (mouse only; touch uses
    tap). The first add to an empty week creates that week's plan automatically.
  - **Inline editing:** each meal chip has a servings ± stepper and view / cook /
    remove actions in its menu — the separate "Edit entries" dialog is gone.
  - **Recipe rows** show "N free" (unallocated) with an inline ± to adjust the
    cooked pool and a quick "log a cook" action. Today is marked with a badge,
    past days are dimmed and read-only, and the whole surface reads the
    household "today" from the server (C-2.K) so date boundaries are correct.
- **Meal Plans page chrome cleanup (Meal Plans C-2.B).** First visible pass of
  the planner redesign — decluttering before the carousel rebuild:
  - The page-top **"You need to cook" shortfall banner is gone**; the summary
    moves into the sidebar as a single **chef-hat** line ("N to cook by <day>",
    not a warning triangle).
  - The **"Suggest meals I can cook now" button + modal are removed** —
    cookable-now belongs on the Cookbook, not the planner.
  - The **"Week of <date>" heading is removed** (the calendar widget will be
    the title) and the **Meal Plans nav icon is now a chef's hat** (was a
    calendar).
  - **Entry chips redesigned** into a reusable `MealPlanEntryChip` component:
    recipe name (wraps) + a separated **`×servings` pill**, with at most one
    status icon (a "consumed" check *or* a "needs cooking" warning, never both)
    — fixes the icon/text overflow. Theme-token colours throughout (the old
    `grey-5` consumed state now uses the neutral surface tokens).
- **Dialog chrome unified across the app (FU-008).** All 26 `BaseDialog`
  usages now drive their header through the `title` prop (or `#header`
  slot for the icon+title cheatsheet) and their footer through the
  `#actions` slot, instead of repeating bespoke `<q-card-section>` /
  `<q-card-actions>` markup. Add/Edit/Picker/Confirm dialogs across
  recipes, stock, products, meal plans, shopping lists, scanning,
  backup/restore, audit log, and onboarding all share the same chrome.
  Form-submit-style dialogs were rebound to explicit `@click` submit
  handlers when their action buttons moved outside `<q-form>`.
- **Logs rotate by date instead of by size (FU-027).** Switched
  `dora_api/infrastructure/logging_setup.py` from `RotatingFileHandler`
  (10 MB × 5) to `TimedRotatingFileHandler` (`when="midnight"`,
  `backupCount=14`, `suffix="%Y-%m-%d"`). The active `<service>.log`
  now contains only the current date's entries; previous days roll
  off into `<service>.log.YYYY-MM-DD` files, ~2 weeks kept.
- **Onboarding tour Alerts card now points at `/alerts` (FU-015).**
  `WelcomeWizard.vue` `TOUR_CARDS` Alerts entry no longer deep-links
  into Stock with `?attention=true`; it routes to the dedicated alerts
  page that already exists.

### Fixed
- **Production frontend build restored (FU-201).** `npm run build` was failing
  on four unused-symbol lint errors (surfaced via `vite-plugin-checker`'s ESLint
  step); the dead symbols were removed so the SPA builds cleanly again. No
  user-visible behaviour change — purely an unblock of the release build.
- **Session-secret file now lives under `DORA_DATA_DIR` (FU-037).**
  `dora_api/app.py` resolved `.secret_key` as a literal CWD-relative
  `./data/` path, escaping the configured data dir on the desktop
  build and silently invalidating session cookies if the app was
  launched from a different folder. Now resolved via
  `config_manager.get_data_dir() / '.secret_key'` (parent created
  on first run). The SQLAlchemy `data/` mkdir nearby was also rerouted
  through `get_data_dir()` for consistency.

### Removed
- **"Preferred product" annotation — gone end-to-end.** The
  `StockItem.preferred_product_id` field (driving the star toggle on the
  stock-item detail page) carried weight in only one place that changed
  behaviour — the stock-value report — and excluded every item the user
  hadn't manually starred. Removed in one pass: the report now estimates
  from the **cheapest** most-recent linked-product price instead (which is
  always available when offers are linked); the stock-item products list
  and shopping-list offer picker sort `cheapest → name` (was preferred
  first); the barcode-lookup → stock-item path collapsed to the m2m
  fallback it already had; the star toggle, API field, frontend models,
  and the table column + FK are gone. Reversible Alembic migration
  `d2a7f4c9e6b1` (batch mode, SQLite + Postgres). End-of-build follow-up
  FU-180 tracks whether a preferred-merchant (rather than per-product)
  affordance is worth adding back once real usage data exists.
- **App-wide undo / shopping-list Reopen — gone (FU-163).** The user
  retired the whole undo posture: "decided undo feature does not make sense,
  remove. Even the reopen functionality — once a list is done, it's done.
  The snapshot of stock levels feels so overengineered. Kill it."
  - Frontend: deleted `useUndo.ts` + `useNotifyUndoable.ts`; removed the
    header Undo button + Ctrl/Cmd-Z / Ctrl-Shift-Z keyboard handler in
    `MainLayout.vue`; stripped every `registerUndo` / `notifyUndoable`
    call site in `stockItemStore.ts` (level swap, scalar update, delete)
    and `ShoppingListDetail.vue` (tick/untick). Stock-item delete is now
    a plain delete — no Undo toast.
  - Shopping list: the **Reopen** button on a Done list is gone, along
    with its handler and `unfinishAsync` on the API service. A finished
    list is final; if the user wants to keep working with its lines, the
    "Copy to new list" button is still there.
  - Backend: deleted `POST /api/shopping-lists/<id>/unfinish` (handler
    + module) and `POST /api/stock-items/restore` (handler + module).
    The `finish_shopping_list` handler no longer captures the
    `level_restores` snapshot. `ShoppingList.finish_snapshot` column
    dropped from the entity, the `Fields` enum, and the table mapping.
    New migration `a1c4e7b3f5d2_20260614_drop_finish_snapshot` removes
    the column (batch mode, SQLite + Postgres parity, R-005).
  - Tests: `test_shopping_list_lifecycle.py` now asserts `/unfinish`
    returns 404 instead of round-tripping a finish→reopen.

### Changed
- **Cookbook revision Chunk C — optional ingredients (the cross-cutting one).**
  - **New `RecipeIngredient.is_optional` column** (NOT NULL, default false)
    on the server (`recipe_ingredient.py` + table mapping + batch-mode
    migration `b9e5c2a78f31`). Round-trips through create/update DTOs
    and the read DTO; per-row Optional checkbox added to the
    Cookbook overview edit dialog and the Recipe detail page's inline
    editor; URL-importer rows default to required (no auto-detection in
    v1 — parsing "to taste"/parens is brittle).
  - **Cookability rule (`recipe_cookability.py`) ignores optional rows
    entirely** — no `cookable_with_optional` half-state, no client
    second-cookable value. Every consumer of the rule
    (`missing_count_for` / `missing_stock_item_names_for`) inherits this
    transitively, so the **five surfaces** that read cookability all
    move together: recipe DTO (and via that, the cookbook card +
    stock-item recipe cards), the dashboard's `cookable_count`, the
    waste-rescue ranking, and both assistant tools
    (`_stock_coverage` in `tools.py`, `add_recipe_to_list` candidate
    list in `confirm_actions.py`).
  - **Picker modal renders optional rows under a "─── Optional ───"
    separator** at the bottom of the list, unchecked by default
    regardless of stock level. `Select all` and `Select missing` also
    leave optional rows unchecked — optional is opt-in only. If the
    same stock item appears as both required and optional in a recipe,
    the required commitment wins (treat as required, default checks
    follow stock level).
  - **Cook mode** renders an `(optional)` hint after the ingredient
    name and dims the row (`.ingredient-row--optional`) so the eye
    lands on what's required.
  - All 299 unit tests pass; vue-tsc clean. Batch-mode migration is
    SQLite + Postgres safe (R-005).
- **Cookbook revision Chunk B — picker modal, difficulty axis, time-of-day vocabulary.**
  - **New `RecipeIngredientPickerDialog.vue`** (under
    `web_app/src/components/recipes/`) replaces the old all-or-nothing
    "add to list" dialog on both the Cookbook overview and the Recipe
    detail page. Per-ingredient checkboxes with stock-level dots;
    `is_missing` / `is_low_stock` auto-checked, `sufficient` /
    `well_stocked` auto-unchecked. Rows are sorted so missing items
    surface first. `Select all` / `Select missing` quick actions.
    Target list picker integrated into the dialog. Card emits
    `add-all-to-list` (cookable) or `add-missing` (not cookable) — both
    open the same picker; the not-cookable path pre-selects the missing
    subset.
  - **Difficulty is now a closed-set vocabulary** (`Easy` / `Medium` /
    `Hard`) — `ALLOWED_DIFFICULTY_VALUES` on the server
    (`dora_api/domain/entities/recipe.py`) is validated at create + update
    boundaries (R-010) returning a 400 on out-of-vocab values; the edit
    dialog + detail page swap their free-form input for a `q-select`.
    **New filter** (single-select dropdown) and **new sort axis**
    (ordinal: Easy < Medium < Hard; recipes with no difficulty sink to
    the bottom regardless of direction) on the Cookbook overview.
  - **`Recipe.time_of_day` is now a closed-set vocabulary** sourced from
    the new `DEFAULT_MEAL_SLOTS` constant (`Breakfast` / `Lunch` /
    `Dinner` / `Snack` / `Dessert`) — shared with `MealPlanEntry.slot`
    (`PROPOSAL_MEAL_PLANS.md §4`, amended in this PR). Server-side
    validation matches the difficulty pattern. The Cookbook overview
    filter, edit dialog, and detail page all read from the same
    constant. The historical free-text `'Any'` option in the q-selects
    is dropped (existing recipes saved with off-vocab values round-trip
    on read; the next save migrates them to a valid choice).
  - Frontend constants live in `web_app/src/helpers/recipeVocabulary.ts`
    (mirror of the server constants); when `PROPOSAL_MEAL_PLANS.md §4`
    lands a user-configurable slot list, both surfaces will switch to
    reading from that list with this constant as the seeded default.
  - All 299 unit tests pass; vue-tsc clean.
- **Cookbook recipe card — visual redesign (Chunk A of the FU-088 revision).**
  The browser-verified follow-up to Cookbook Chunk 3 lands its first PR:
  - **Footer action row reshaped** — heart (leftmost) → Cook (icon-only
    `mdi-chef-hat`, no label) → add-to-list (icon-only). The kebab `⋮`
    menu is gone entirely; "Add to meal plan" was retired with it.
  - **Cookable state is now the Cook button's colour** (primary when
    cookable, warning when not) — the separate "Cookable now" / "Missing N"
    chip section is removed. The add-to-list button mirrors it
    (`mdi-cart-plus` / neutral vs `mdi-cart-remove` / warning) and emits
    `add-missing` instead of `add-all-to-list` when not cookable.
  - **Heart moves out of the image overlay** (and the dark scrim with it)
    into the footer's leftmost slot.
  - **Meta line reordered + extended** — the chips row (time / serves /
    difficulty / parts) now sits above the muted caption, which reads
    `[Cuisine] · [Category] · [Time of day]` (each segment optional).
  - **Allocated badge removed from the overview** — it lives on the meal
    planner now (per `PROPOSAL_MEAL_PLANS.md §3.1`).
  - **`MealStepper` removed from the card** — the cooked-pool stepper
    stays on the recipe detail page and on the stock-item detail page;
    it leaves the overview entirely. The planner-side pickup is noted in
    `PROPOSAL_MEAL_PLANS.md §3.1` for that proposal's eventual
    implementation.
  - **"X low" chip and the dim-on-restock-this-item visual are gone.**
  - **Dietary tag chips are larger** (default size, no `dense` /
    `size="sm"`) so they're readable at mobile zoom.
  - Followers: `RecipesOverview.vue` and `StockItemDetailPage.vue` drop
    the now-orphaned `@adjust-meals` / `@add-to-meal-plan` handlers and
    their bodies. `recipeStore.adjustMealsAsync` stays (still used by the
    detail page). New `ICONS.chef_hat` (`mdi-chef-hat`). vue-tsc clean.
  Chunks B (ingredient-picker modal + difficulty axis + `time_of_day`
  vocabulary) and C (optional ingredients) follow per
  `PROPOSAL_COOKBOOK_CARD_REVISION.md`.
- **E2E test suite: ~95× faster + realigned to the current API contract**
  (FU-166). The `tests/e2e` harness now dispatches in-process through Flask's
  test client instead of booting a real HTTP server and driving it over the
  loopback socket — the full ~300-test suite dropped from **~13.5 min to ~6s**
  (test bodies unchanged; `conftest` rebinds `requests.*`/`requests.Session`
  to test-client adapters, new rule **R-013** / **ADR-008**). The ~132 failing
  legacy CRUD router tests (stock items/levels/locations, users, merchants,
  products) were updated from the long-superseded contract — path-style
  `/filter=…` → query-string `?filter=…`, bare arrays → `{items,total,page,
  limit}` envelopes, RFC-2822 → ISO-8601 dates, refreshed seed data + DTO key
  sets, and reworked query-option error messages. Net: **0 failures** (was 122
  failed / 10 errors).
- **Meal-plan CSV export removed.** A meal plan is a calendar, not a tabular
  dataset — CSV added no real value, and the endpoint was 500ing anyway
  (`entry.meal_name` vs the DTO's `recipe_name`). Dropped the
  `GET /api/meal-plans/<id>/export` route and the CSV buttons; **print-view**
  (→ browser "Save as PDF") stays and its blank-meal-name bug is fixed (same
  field rename). (FU-168)
- **Unknown `GET /api/<x>` now returns the JSON problem-detail**, not the SPA's
  HTML 404 — matching POST/PATCH/DELETE. Shared `endpoint_not_found()` helper
  used by both the request middleware and the SPA catch-all. (FU-167)
- **Backup completeness confirmed.** `product_stock_item_links` already
  round-trips in the install backup; the failing test merely expected the
  removed `meals`/`meal_recipes` tables (meals→recipes rework) — test
  corrected. (FU-164)
- **Shopping lists UX v2 — one page for the whole shop**
  (`PROPOSAL_SHOPPING_LIST_UX_V2.md`, feedback S1–S18 + L400–L421).
  - **Shop mode is gone as a separate page.** The detail page is now the
    single shopping surface for every status. "Start shopping" flips the
    page into a live-shop state: bigger tick targets, ticked lines sink to
    the bottom with strikethrough, a sticky footer shows live progress +
    remaining spend + the Finish CTA, and quick-add stays available mid-shop
    (you remember the milk *in* the store). The one-item-at-a-time walk,
    skip, up-next preview and peek-list dialog are gone with the page; the
    price-as-you-go receipt loop, substitute swap, tap-to-type quantities
    and keyboard shortcuts (now incl. `u` = untick last) all survived the
    merge. The `/stop` ("pause") endpoint is gone — the lifecycle is Start
    shopping → Finish & restock → (Reopen).
  - **Finish & restock is now a restock review.** Finishing opens a modal
    listing every ticked item with a per-item stock-level picker (default
    Well-Stocked) above one "Restock & finish" button — one click for the
    common case, per-item tweaks (e.g. "only partly topped up → Sufficient")
    without extra screens. `POST /finish` accepts `level_overrides`.
  - **Desktop lists rail / mobile dropdown.** All lists — active and done —
    render as one virtualised, auto-scrolling continuum ordered by
    *effective date* (finalised shop date → planned shop date → created),
    past at the top, future at the bottom, with a "next up" marker. On
    mobile the same continuum is a dropdown at the top of the page. The
    landing redirect now follows a server-computed `next_up_list_id`
    (live shop → first list date-wise after the last completed → earliest
    pending → most recent done).
  - **Top info area.** Big list name with a heading-scale status badge
    (DRAFT / SHOPPING / DONE), readable meta row, the planned shop day as a
    real button (tinted when today/overdue — the old banner is folded in),
    and the completion doughnut is back (it died with the old overview page)
    next to the server-owned money totals.
  - **Custom names are clearable and lists self-label.** `name` is nullable;
    a list without one displays its planned-shop-date (else creation date)
    via a server-owned `display_name` — and re-labels itself when the shop
    day changes. Auto-generated date-names from the old behaviour were
    migrated to the new self-labelling.
  - **Toolbar instead of ellipsis menus (new rule R-012).** Quick add,
    group-by, refresh deals, select-many and the lifecycle action are
    visible buttons; only rare/destructive actions (template, print, move
    unticked, copy, clear, delete) live in a labelled "More" menu. Per-row
    actions (price, swap substitute, remove) sit directly on the row — the
    row kebab is gone, and the price control is a real outlined button.
  - **Removed:** the StockItemChip component app-wide (rows show a plain
    name-link + a new `StockLevelDot`; its second usage on the stock-item
    substitutes list got the same treatment); per-line "move to another
    list" (remove + re-add covers it; bulk "move unticked" stays);
    the "archive" action (finish or delete — "done without restock" was a
    redundant third path); shopping-list **CSV export** end-to-end (print
    view remains); the browser-tab title now reads "Shopping lists".

### Fixed
- **API dates are now ISO 8601.** Flask's default serialised dates as
  RFC 1123 ("Tue, 01 Sep 2026 00:00:00 GMT"), which silently broke every
  client-side date comparison — including the "open today's list" landing
  pick, which could never match. All `date`/`datetime` fields now serialise
  ISO (ADR-007).
- **Deliberate HTTP errors no longer masquerade as 500s.** The global
  exception handler swallowed `abort(404)`/`abort(503)` etc. and returned
  "An unexpected error occurred." for all of them; real status codes now
  pass through. Unknown `/api/...` URLs also 404 properly instead of
  serving the SPA's index.html.
- **Dora-chat add-to-list no longer queries a dropped column.** The
  assistant's primary-list lookup still filtered on `is_primary`, which was
  removed from the schema in the Chunk-2 rework — the action would crash at
  runtime; it now uses the shared draft-count resolver.
- **Empty-state flash on the shopping list page.** The first rendered frame
  could show "This list isn't available" before loading kicked in; the page
  now opens on skeletons.

### Added
- **Cart Button Chunk 3 UI side (FU-131).** The frontend half of
  L191 that was deferred from the schema/backend chunk lands here:
  - **Rule 4 modal.** Removing a product-only line from a shopping
    list now prompts *"Also remove the stock item from this list?"*
    when the product's linked stock item is also on the list as its
    own line. Yes removes both in one user action; No removes just
    the product line.
  - **Nested display.** A line with both `stock_item_id` and
    `product_id` set (a product nested under a stock-item parent,
    per rule 2) now renders indented under its parent with a left
    rail and a "Nested product" tooltip. Product-only lines (no
    `stock_item_id`) wear a softly tinted background + a "Product
    only — no linked stock item on this list" tooltip so the line
    type is legible at a glance.
  - **`AddToListButton variant="inline-product"`.** New variant
    anchored on `product-id` (rather than `stock-item-id`) that
    adds a standalone product-only line via Axis B: 1 draft →
    silent add, 2+ → radio picker, 0 → toast "create a draft
    first". The My Products page now uses it for unlinked products
    — previously those rows had a permanently-disabled cart icon
    with a "link to a stock item first" tooltip.

### Fixed
- **Shopping-list URL-param change now reloads the list (FU-157).**
  After Chunk 5 merged the overview into the detail page, switching
  lists via the header dropdown pushed a new `/shopping-lists/<id>`
  URL but left the previous list on screen — the component stayed
  mounted (same route component, different `:id`), and `onMounted`
  never re-fired. The "old list reappears after adding an item to
  another" symptom was a side-effect of the same gap (the page never
  actually moved off list A). Both `ShoppingListDetail` and
  `ShoppingListShopMode` now `watch(listId, load)` and clear stale
  detail at the start of `load()` so the user sees a spinner instead
  of the previous list's rows while the new fetch is in flight.

- **Unsaved-changes guard now covers every nav surface (FU-156).**
  Previously the recipe detail page only prompted "Discard unsaved
  changes?" when the Back button was clicked, and the stock-item
  detail page had no guard at all — so navigating via the main side
  menu, a related-recipe link, the browser back button, or a refresh
  silently lost edits. New `useUnsavedChangesGuard` composable wires
  the prompt into `onBeforeRouteLeave` (different-route nav),
  `onBeforeRouteUpdate` (same-component param change, e.g. clicking
  another recipe while editing one), and `beforeunload` (refresh /
  close) in one place. Both detail pages opt in: recipe detail guards
  field edits and image picks; stock-item detail guards basics-form
  edits (image upload was already auto-save). Delete handlers reset
  dirty state before navigating away.

- **Stock-item detail "Related recipes" tab now opens the recipe
  (FU-155).** Clicking a recipe in the related-recipes tab on a stock
  item's detail page used to push `/cookbook?recipe=<id>` — which
  matched the Cookbook overview route, not the recipe-detail route,
  so the URL changed but the page landed on the overview. Now pushes
  `/cookbook/<id>` to open the recipe.

- **Product images round-trip correctly on save (FU-014).** Saving a
  product from the Product Search page previously stored corrupted bytes:
  the frontend POSTed merchant_api's raw base64, Pydantic's
  `Base64Bytes` decoded that string into raw image bytes, and the read
  path called `.decode('utf-8', 'ignore')` on those bytes — producing a
  garbage string the browser rendered as the broken-image alt text
  squished into the avatar slot. Now follows the stock-item / recipe
  convention: the create endpoint takes a `data:image/...;base64,...`
  string, the image column is `deferred` to keep list payloads small,
  list/detail responses carry `has_image: bool`, and a new
  `GET /api/products/<id>/image` route serves the bytes with the right
  MIME type. A new Alembic migration nulls out the garbage bytes from
  the old path so the fallback icon shows cleanly until the user
  re-saves the product. `ImageService` now sniffs MIME from base64
  magic bytes instead of hard-coding `image/jpeg`. Touched:
  `MyProductsPage`, `DashboardPage` deals list, `ProductSearch` save.

- **Offer-price snapshot now captures at *add* / *select* time, not at
  tick (State Ownership Chunk 6).** Previously `picked_offer_price` and
  `list_price_at_pick` were frozen the first time a line was ticked —
  which meant adding a line on Monday at $5 and ticking it on Saturday
  at $6 lost the planning intent ($5), and a line that was never ticked
  had a `NULL` snapshot, leaving "what did I mean to pay?" unanswerable.
  The snapshot now fires when the user commits to an offer:
  - **Add line** with `selected_product_id` → snapshot captured.
  - **Update line** that sets/changes `selected_product_id` → snapshot
    re-captured at the new offer's current price.
  - **Update line** that clears `selected_product_id` → snapshot
    cleared (no priced intent).
  - **Tick** / **untick** no longer touches the snapshot. A
    belt-and-braces "snapshot on first tick if still NULL" stays for
    legacy rows; new lines reach that path already populated.
  Budget spend (`/api/budget/status`), waste reporting, and the
  shopping-list `finish` flow all consume the same `picked_offer_price`
  field — they now see the planning-time price the user actually meant
  to pay.

### Changed
- **Renaming a stock level no longer breaks the SPA
  (State Ownership Chunk 4).** Every client decision keyed on the
  literal string `'Out of Stock'` (or `'Low Stock'`, `'Well-Stocked'`,
  `'Sufficient Stock'`) now reads the server-derived booleans
  (`is_out_of_stock`, `is_low_stock`, `needs_restock`) on the stock-item
  DTO, or matches by the level's `sequence` via the new
  `helpers/stockStatus.ts` (`isOutOfStockSequence`,
  `needsRestockSequence`, `findLevelBySequence`). Migrated:
  `StockItemChip`, `StockItemRow`, `useStockFilters`, `WastePage`,
  `MealPlansOverview`, `ProductSearch`, `RecipeCookMode`,
  `NewListDialog`. Display-only colour helper
  (`stockLevelLogic.colourForSequence`) is now sequence-keyed too. The
  `StockLevelName` type union was dropped (custom level names are valid
  again), and the type-only casts to it were removed across
  `RecipeDetailPage`, `RecipesOverview`, `MyProductsPage`,
  `StockItemDetailPage`.

### Added
- **`missing_stock_item_names` on `RecipeDto` (State Ownership Chunk 2).**
  Each recipe now ships the distinct, alphabetised names of its missing
  stock items alongside `missing_count` / `cookable`, so the client can
  render a "Missing: flour, eggs" hint without re-joining the ingredient
  tree or the stock-level table. Computed set-based off the already-loaded
  ingredients in `from_entity` — no N+1, mirrors how `missing_count` is
  built. (Stock-item / recipe-ingredient DTO booleans + `missing_count` /
  `cookable` already shipped under the same chunk; this closes the
  field-list gap.)

### Changed
- **Server stock-status authority is now sequence-keyed everywhere
  (State Ownership Chunk 1).** The last two name-hardcodes are gone:
  the assistant's `_LEVEL_ALIASES` ("out", "low", "running low", …) now
  resolves to a `StockStatus` enum + `level_for_status` lookup instead
  of an `"Out of Stock"` string match, and the recipe missing-ingredient
  filter uses `is_missing()` instead of a `level.sequence < 3` magic
  literal. The 7-day "expiring soon" threshold is now defined once in
  `dora_api/domain/stock_status.py` (alongside the status contract);
  `attention.py`, `get_alerts.py`, and `assistant/tools.py` import the
  canonical name instead of redeclaring it. No user-visible behaviour
  change — renaming the "Out of Stock" stock level still does the right
  thing (asserted by `tests/test_confirm_actions_resolve_level.py`).

- **Meal-plan "Generate shopping list for this week" routes through Axis B
  (Cart Button Chunk 4 / L382).** When you have any draft list, the button
  now opens a small picker: pick an existing draft to **add to**, or **+
  Create new list** for the always-new path. With zero drafts it skips the
  prompt and creates a new list as before. The success toast distinguishes
  the two ("Added N items to your list." vs "Shopping list created with
  N items."). No schema change — the backend's `merge_into_list_id` already
  supported this; only the meal-plan call site was hard-coded to always-new.

### Fixed
- **Filter panels everywhere now open.** The "Filters" toggle on Cookbook,
  Stock Overview and every page using `FilterBar` rendered a dead button — the
  panel never opened on click and the desktop "open by default" rule never
  fired. Two latent bugs collided: Vue 3 coerces an unset Boolean prop to
  `false`, defeating the manual controlled/uncontrolled `modelValue ===
  undefined` sentinel; and Quasar's `$q.screen` was being read without ever
  being activated, so every viewport check returned `false`. Replaced with
  Vue 3.4 `defineModel()` + a `Screen.setDebounce()` boot file. (FU-087)

### Changed
- **Recipe routes now live under `/cookbook` (the cookbook is the
  page; a recipe is a single item in it).** New SPA URLs:
  - `/cookbook` — overview (unchanged).
  - `/cookbook/:id` — recipe detail (was `/recipes/:id`).
  - `/cookbook/:id/cook` — cook mode (was `/recipes/:id/cook`).
  Pre-release, so the legacy `/recipes*` paths were **deleted
  outright** — no redirects, clean break. Backend API paths
  (`/api/recipes/...`) are untouched; they're a resource name,
  not a SPA URL.

### Removed
- **Command palette retired (FU-029, INV-9 followed through).** The
  Ctrl/Cmd-K command palette and its commands registry are gone.
  Most palette commands duplicated nav already reachable in 1-2
  clicks from the side menu; the audience for a hidden Ctrl-K modal
  doesn't really exist in a pantry / mobile app. The
  `CommandPalette.vue` component, the `useCommands` registry, the
  `useCommandPalette` open-state, and the `useRecents`
  recent-commands store have all been deleted; the global Ctrl/Cmd-K
  key handler and the palette-feeder helpers in `MainLayout`
  (`autogenerateFromLowStock`, `openPrimaryList`,
  `openPrimaryShopMode`) went with them. **Kept:** the
  `useShortcut` keyboard-shortcut layer + `ShortcutsCheatsheet` —
  `?` cheatsheet, `/` focus, `g s` / `g l` / `g r` / `g d` / `g h`
  nav, and every page-specific shortcut still works. If
  power-user discoverability becomes a real ask, the cheatsheet is
  where it'll surface — not a hidden modal.

### Changed
- **Fullscreen 404 page redesigned (FU-030).** The typo-a-URL
  "Nothing here…" page now mirrors the login screen's off-app
  treatment — drifting mesh-gradient blobs, a floating Dora
  mascot (the "fatal-error-or-offline" variant), and a glassy
  card with a gradient "404", "This page wandered off"
  headline, and a "Take me home" CTA. Locally-scoped tokens
  (same rationale as LoginPage — 404 can render pre-auth where
  the app's theme cascade isn't trustworthy yet); respects
  `prefers-reduced-motion`.

### Fixed
- **Recipe detail dietary tags + tools were silently dropped on the
  detail endpoint (FU-147).** The `/api/recipes/<recipe_id>` route
  has no `uuid:` converter, so Flask passed `recipe_id` to
  `handle_by_id` as a string. The handler then did
  `tag_map.get(recipe_id, [])` against a dict whose keys were
  real UUIDs from SQLAlchemy — Python's `.get(str)` against UUID
  keys always missed, so every recipe came back from the detail
  endpoint with empty `dietary_tag_ids` + `tool_ids`. Cards on
  the overview were fine (different code path); only the detail
  view + its editors were affected. Fix: look up via the loaded
  entity's id, which is always a UUID.

### Added
- **Cookbook overview "Time of day" filter (FU-148).** Single-
  select dropdown alongside cuisine + category; values mirror
  the recipe-editor enum (Breakfast / Lunch / Dinner / Dessert /
  Snack / Any).
- **Cookbook overview "# ingredients" filter + sort axis
  (FU-149).** Numeric cap ("# ingredients ≤ N") for finding
  shorter recipes; new sort axis "# ingredients" defaulting to
  ascending ("fewest first") with the existing direction toggle
  to flip it.
- **Basic chat-mode recognises dietary, cuisine, and time-of-day
  queries (FU-150 step 1).** "I need a vegetarian recipe", "I
  need an asian recipe", "show me a breakfast recipe" no longer
  fall to the generic fallback bank. The `find_recipe` intent's
  trigger list now covers bare-noun phrasings, and its handler
  was rewritten to tokenise the whole message (stopwords
  stripped) and substring-match each token against recipe name,
  cuisine, category, time-of-day, and dietary tag names. The
  reply echoes which tokens it filtered on. (The full
  slot-extraction redesign — vocab-derived triggers + a real
  query parser — is logged as FU-152 for a focused later pass.)

### Changed
- **Removed external GitHub-issues links throughout the app
  (FU-146 — repo is private).** The assistant's fallback replies
  no longer suggest "the GitHub issues page" or "the issues link
  is your friend"; the `report_issue` intent acknowledges the
  problem and points at Help instead of an external tracker.
  The "Report a bug" button on `HelpPage` + the repo/issues links
  on `AboutSettings` + the pre-filled "Report this" button on
  `PageErrorState` (which built a GitHub-issues URL with the
  error message and correlation id) are all gone. The
  `report_issue` chat affordance stays — it just navigates to
  Help instead.

### Added
- **Standalone-product shopping-list lines (Cart Button Chunk 3 / L191
  / L130).** A shopping-list line now anchors on a **stock item, a
  product, or both**. Schema: `ShoppingListLine.stock_item_id` is
  nullable, new nullable `product_id` (FK→Product), plus a CHECK
  requiring at least one anchor. Behavioural rules wired:
  - **Rule 1 — standalone add:** adding a product whose linked
    stock item isn't on the list creates a product-only line ("on
    the list as a product, no stock-item row").
  - **Rule 2 — auto-nest on link:** linking a product to a stock
    item later (`POST /stock-items/<id>/products`) hunts active
    draft lists for any orphan product-only lines anchored on
    that product and **upgrades them in place** — folding into an
    existing stock-item line if one exists, or stamping
    `stock_item_id` on the orphan otherwise.
  - **Rule 3 — cascade remove:** deleting a stock-item line
    cascades-removes nested product-only lines whose product is
    linked to that stock item. Same rule applies on the
    cart-button quick-remove path.
  - **Rule 4 (TBD):** prompting "also remove the stock item?" when
    a product-only line is removed is the UI side of this chunk;
    logged as FU-131 alongside the inline-product variant + nested
    display.
  Migration is pre-release (no data preserve); existing dev/test
  rows recreate cleanly.

### Changed
- **Cart button routes through the combined modal when there's a real
  choice to make (Cart Button Chunk 2 / L84, decision 2).** Hitting
  "add to list" on a stock item with **2+ linked products** now opens
  the existing `QuickAddSheet` (one combined surface: target list +
  offer + quantity) instead of adding silently with no offer picked.
  Items with 0 or 1 linked product still use the silent quick-add
  path. **Quantity stays modal-only** (decision 5) — quick paths
  remain qty-1. Backed by a new `linked_product_count` field on the
  stock-item DTO (bulk-hydrated alongside `has_image`).

### Added
- **Unified cart button (Cart Button Chunk 1).** A new `AddToListButton`
  component owns every "add this to my shopping list" interaction
  app-wide. It's **state-aware** — the icon and colour reflect whether
  the item's already on your draft list (or two; the multi-list popover
  shows you exactly which) — and **toggles**: clicking an already-on
  row removes it silently when it's on one list, or opens a small
  popover with explicit Remove / Add-to-another when it's on
  multiple. Bulk variant resolves the target list **once** for the
  whole batch and surfaces a single summary toast ("5 added, 2
  already on list") instead of N per-item toasts. Adopted on the
  stock overview row, stock item detail toolbar, recipe detail
  ingredient rows, and the stock overview bulk action. **Fixes
  FU-038** — the old "0 added, 1 already" + "Added to your primary
  list" double-toast collision is no longer reachable.

### Added
- **Stock item images (Stock Overview Chunk 6 / FU-033 / L74).** Stock
  items now carry their own image, uploaded from the **detail page**
  (Overview tab, top of the right column). When a stock item has no
  image of its own, it **falls back to the image of any linked
  Product** — so connecting an item to a product auto-fills the photo
  without you doing anything. If neither has one, the row shows a
  neutral placeholder. The row's thumbnail respects the existing
  Show/hide images toggle (denser rows when off). Plumbing mirrors
  the recipe image pattern (data-URL storage, dedicated
  `/stock-items/<id>/image` bytes endpoint, `has_image` flag on the
  DTO, deferred SQL column so the list endpoint never loads
  megabytes per row).

### Changed
- **Stock Overview detail navigation is now responsive (Chunk 5 / L68–
  L72, decisions 1 + 2).** **Desktop** keeps the embedded side-
  drawer peek when you tap a row. **Mobile** routes to the full
  detail page instead — the drawer made no sense at narrow widths.
  One shared `StockItemDetailPage` component renders in both frames
  so the detail UI never forks. **Long-pressing a row on mobile**
  enters bulk-select mode with that row already ticked, matching
  the native multi-select gesture people expect from list apps.

- **Stock Overview expiry control reworked (Chunk 4 / L86–L88).** The
  expiry button now does two distinct things based on state. **No
  expiry set →** tapping opens a date picker (restricted to today +
  future) so you can pin a real date in one tap, instead of
  guessing with +7 / +30 shortcuts. **Expiry already set →** the
  menu now offers **+1 day · +7 days · +14 days · Clear** (replacing
  the old +7/+30/Clear), matching the cadence people actually use
  for nudging fridge dates.

- **Stock Overview row redesigned (Chunk 3).** Each row now reads
  left-to-right as **[■ LEVEL button] · Name (bold) · Zone · [img?]
  · · · [⏰ expiry] [🍽 #recipes] [open/in-use] [🛒 cart]**. The
  level button is the only place you change a level (no chip avatar,
  no right-side dropdown — one focus, L70); the level dot's colour
  carries the status. Retired the standalone `StockItemChip` from
  this row, the location chip (zone now lives inline next to the
  name and is lightly clickable), the "On N lists" chip, the
  OK/Mid/Low/Out badge, and the small red dot. Status now drives a
  **whole-row outline** — neutral by default, amber when expiring
  within 7 days, red when out-of-stock or expired (out rows also
  dim). **Selection fills the row** instead of outlining it so bulk
  ticks read clearly. Rows are taller and the name is emphasised
  (L78 / L79). `StockItemChip` itself stays in place for the
  shopping-list + detail-page consumers.
- **Stock Overview gains an inline "Hide row images" toggle (FU-106 /
  C-cross §2.8).** A small icon button next to the search input
  flips the per-user `show_stock_images` flag; with it off the
  row's image slot collapses out of the layout for denser rows.
  The toggle works today even though the actual image bytes
  haven't been wired (FU-033) — the slot is a neutral placeholder
  until then.

- **Stock Overview top toolbar consolidated (Chunk 2 / L94).** One tidy
  button group across the top: **New item · Export · Bulk select ·
  Scan · Stocktake**; search stays separate on the right. "Bulk
  select" moved up from inside the filter bar so it's reachable
  without expanding filters first.
- **Filter panels start closed by default everywhere (Chunk 2 / L95).**
  `FilterBar` no longer auto-opens on desktop — the page header now
  reads as one clean toolbar; click "Filters" to expand when you
  actually want to filter. Parents that own the expanded state
  (`v-model`) are unaffected.
- **Stock level filter → single "Any level" dropdown (Chunk 2 / L97).**
  The per-level filter chips with floating count badges were retired;
  one `q-select` replaces them. Per-level counts now live in the
  sticky page-counts footer (Shown · Well-stocked · Sufficient · Low
  · Out · Flagged · Auto-add · Needs attention).
- **Stock Overview "Used in a recipe" filter retired (Chunk 2 / L96).**
  Low-signal; recipe pages own that question. Cross-feature index
  (`recipesByStockItem`) survives because per-row "used in N recipes"
  badges still consume it.
- **Stock Overview search placeholder shortened (Chunk 2 / L98).**
  Compact "Search" replaces the cramped multi-word hint.

### Fixed
- **Stock Overview no longer silently caps at 50 items (FU-035 / Stock
  Overview Chunk 1).** The overview was fetching only page 1 of the
  stock-items endpoint and ignoring `page.total`, so any pantry past
  the first 50 items silently lost the rest. The store now pages until
  exhausted (asking for `limit=500` per call to minimise round-trips,
  matching the backend's `MAX_LIMIT`). A new `getAllPagesAsync`
  helper on the service is the single place that loop lives; callers
  that only want a quick page (autocomplete, snapshot) still use the
  one-page `getAllAsync`.

### Changed
- **Stock Overview virtualises large pantries.** Above 50 visible items
  the list switches to `q-virtual-scroll` so a 500-item pantry stays
  smooth; below the threshold the existing `ListTransition` glide-in
  is preserved so small pantries feel unchanged. Row markup is
  unchanged — every existing filter, footer count, bulk-select, and
  per-row action keeps working.
- **Stock Overview CSV + Print/PDF exports honour the current
  filter.** Previously both exported every item regardless of what
  was on screen. Now the on-screen filtered id list travels with the
  export request (`?ids=…`); no filter → the unfiltered fast path,
  same as before.

### Added
- **Multi-part recipes via named sections (Cookbook Chunk 10).** A recipe
  can now be split into named groups — "Sauce", "Filling", "Dressing" —
  via the new **Sections** card on the recipe detail editor. Add one or
  more sections, then pick a section per ingredient row with the new
  Section picker. Existing recipes are unchanged (no sections = the same
  flat list as before). Cook mode picks up on this: the ingredient panel
  groups under section headers instead of by stock-location when sections
  exist, and the current-step card + all-steps overview show which
  section each step belongs to. The recipe card surfaces a "N parts"
  badge when a recipe has more than one section. Sub-recipes (reusable
  components across recipes) remain deferred — log a follow-up if the
  named-section flow turns out to be insufficient for real meals.

- **Recipe cost estimate + simple nutrition (Cookbook Chunk 9).**
  - When **Money & budgets** is on (Settings → Account, or System →
    Features for the install layer), the recipe detail page shows an
    **Estimated cost** card in the sidebar. The number is server-
    derived: each ingredient that has a linked product offer is priced
    at `quantity × current offer price ÷ pack size`, summed across the
    recipe. The card labels itself an *estimate* loudly and says
    "based on N of M ingredients priced" so you know the coverage.
  - When **Nutrition** is set to Simple (Settings → Account, gated
    by System → Features → Nutrition), the recipe detail editor gains
    a **kcal per serving** field next to servings / prep / cook. The
    recipe detail sidebar shows a read-only Nutrition card when a
    value is set, and the cookbook overview adds a **Kcal** sort axis
    + a **Kcal ≤** filter input.
  - Both features hide entirely when their opt-ins are off — no
    surface change at all for users who haven't opted in.
  - The old free-form Nutrition expansion on the detail page is no
    longer rendered or editable; the column survives in the DB for
    now (FU-115) until we're sure no user has typed something
    irreplaceable in there.

- **Per-user image-display opt-in (C-cross Chunk 5).**
  - Recipes overview now has an **image / image-off icon button**
    next to "Import from URL" — flip it to hide photos on recipe
    cards and the detail-page header (the placeholder tile shows
    instead). The choice is saved per user across sessions and
    devices via `/api/users/me`. Defaults to on so you see photos
    out of the box.
  - When photos are off, the bytes endpoint isn't called at all —
    real bandwidth saving, not just CSS hiding.
  - Stock-side per-user flag also ships (`show_stock_images`) but
    has no inline toggle yet — the C-1 Stock Overview row redesign
    will wire its collapse/expand button when that chunk runs
    (FU-106).
  - Editor still works regardless: image upload, change, and delete
    keep functioning even with photos hidden.

### Fixed
- **Recipe list endpoint no longer loads image blobs.** The query
  used to fetch every recipe's image bytes just to compute the
  `has_image: bool` flag. The `image` column is now lazy-loaded and
  `has_image` comes from a single `image IS NOT NULL` SQL pass —
  removes a real bandwidth cost on the cookbook overview, especially
  for users who turn photos off via the new opt-in. (FU-090)

### Changed (C-cross Chunk 4 — location display policy)
- **Location chips now show the zone, with the full breadcrumb on
  hover.** "Right shelf" / "Left side" out of context was meaningless;
  every location chip across the app now displays the top-level zone
  ("Pantry" / "Fridge" / "Freezer") and reveals the full path
  ("Pantry › Middle shelf › Left side") in a tooltip when one exists.
  Applied on the stock overview row, the stock-item detail page's
  Location row, shopping-list line chips, and shop mode's section
  label.

### Added
- **Per-user Nutrition mode (C-cross Chunk 3).**
  - Settings → Account → **Nutrition** lets you pick **Off** (default),
    **Simple** (a single kcal number per recipe — coming in a future
    chunk), or **Complex** (auto-derive from a nutrition database).
  - Complex is a placeholder for now and stays disabled until an admin
    configures a nutrition source; the per-recipe kcal field + cookbook
    kcal sort axis will land in a future Cookbook chunk and gate on this
    opt-in.
  - Layered with the admin install-wide flag the same way Money is — if
    your install has Nutrition off (System → Features), the per-user
    control reads as disabled with a caption pointing at the admin
    setting.

- **Per-user "Money & budgets" opt-in (C-cross Chunk 2).**
  - Settings → Account → **Money & budgets** lets you turn dollar
    surfaces on or off for your account — recipe cost estimates,
    shopping-list totals, the dashboard budget card. Off by default
    (you opt in).
  - The existing Grocery budget card now lives under this toggle. When
    you turn money features off, the Grocery budget card hides
    automatically; your saved amount and period are kept, ready to come
    back the next time you turn it on.
  - Layered with the admin install-wide flag — if your install has
    money features off (System → Features), the per-user toggle reads as
    disabled with a caption pointing at the admin setting.
  - Future cost-estimate / budget surfaces (Cookbook cost, dashboard
    budget) will gate on this opt-in.

- **Install-wide feature flags + admin Features panel (C-cross Chunk 1).**
  - Settings → **System → Features** lets admins turn whole features on
    or off for the install. Five new flags: **Meal planning** (on by
    default, preserves existing behaviour), **Money & budgets**,
    **Nutrition**, **Companion ingestion**, and **Weekly deals emailer**
    (all off by default). When a feature is off here, it's hidden for
    everyone — per-user preferences only apply when the install allows
    the feature at all.
  - `/api/health` now carries the full `features.*` set so every
    client surface reads a single source of truth.
  - New `useFeatureFlags()` composable on the SPA returns named
    reactive booleans (`features.money`, `features.nutrition`, etc.).
    Consumers gate renders by reading this composable instead of
    AppSetting or their own probe.

- **Recipe versions (Cookbook Chunk 8).**
  - Recipes can now be **versioned**. A new **"New version"** action in
    the detail kebab makes a sibling copy — same ingredients, tools,
    steps, vocabulary, image, source URL, with the name pre-suffixed
    `(v2)`, `(v3)`, etc. The original and the copy become equal peers
    (no "current" version, no master pointer); pick whichever you want
    when scheduling a meal.
  - A new **"Other versions"** card appears in the detail-page sidebar
    when a recipe has siblings, listing their names + last-made + meals
    on hand. Click to jump straight to the sibling's detail page.
  - Deleting a version is the same as deleting any recipe — the
    remaining siblings stay linked.

### Fixed
- **"Planned" filter no longer surfaces yesterday's meals.** The
  recipes-overview "Planned" chip was string-comparing
  `scheduled_for` without parsing — yesterday's date sometimes
  passed the check, and consumed-but-past entries were never
  excluded. Now parses `YYYY-MM-DD` into a local-midnight `Date`,
  skips entries with `consumed_at` set, and gates on `>= today`
  proper. (FU-083)

### Changed (FU-083 follow-up — TriStateFilter gains a sort selector)
- **`TriStateFilter` now optionally accepts sort axes.** Pass a
  `sortOptions` array (each with `value` / `label` / `compare`) and a
  small inline `q-btn-toggle` appears under the search bar. The
  filter sorts the options live before grouping; existing call sites
  that don't pass `sortOptions` get the same behaviour as before.
- **Ingredients filter (Cookbook overview)** now exposes **Name** and
  **Stock level** sort axes — flip to *Stock level* to surface
  Out-of-stock / Low-stock ingredients first when planning around
  what needs using up.

### Changed (FU-083 follow-up — shared TriStateFilter + label tweaks)
- **One shared `TriStateFilter` component** for include/exclude filter
  controls. Dietary tags, Tools, and the new **"Ingredients"** filter
  all run through it. The component supports an optional **search
  typeahead** (essential at stock-item scale) and **per-row coloured
  dot** (the stock-level signal you asked to keep). The old paired
  "Uses ingredients" + "Doesn't use" `q-select`s collapse into a
  single button — click an ingredient once to require it, again to
  exclude it, again to clear.
- **"Missing ≤" → "Missing ingredients ≤"** label.

### Changed (recipes overview UX — FU-083 feedback pass)
- **Sort direction toggle** next to the Sort by dropdown — asc/desc
  with axis-aware tooltips ("Oldest first" / "Most recent first" /
  "A → Z" / etc.). Switching axis snaps direction to the
  conventional default (name = A→Z, recently-made = newest first,
  meals = most first, time = fastest first). Null values still sink
  to the bottom regardless of direction.
- **"Planned in" → "Planned"** (the "in" added nothing).
- **"Uses stock items" → "Uses ingredients"**.
- **New "Doesn't use" picker** pairs with "Uses ingredients" as a +/-
  filter on the same stock-item search. Replaces the old free-text
  "Free from ingredient(s)" chip-input.
- **Filter row de-cluttered** — hints removed from the `Meals ≥` /
  `Missing ≤` inputs; ingredient picker dropdown no longer carries
  the level-name caption (the colour dot was already the meaning).
  Row height stops jittering when those filters are active.
- **Recipe-card dim removed.** The "restocking this item alone
  wouldn't make it cookable" dim semantics wasn't legible without a
  legend; the card already says "missing N ingredients" on its face.

### Added
- **Recipe detail — "Last cooked" card** in the sidebar. Reads the
  recipe's `last_made_on`; shows "Never" when null. Closes the loop
  with the top-toolbar Mark cooked / Log cook actions.

### Fixed
- **Recipe detail load now returns structured steps + versions.** The
  detail-page fetch was filtering the list endpoint by id, which only
  returned the cheap list-shape DTO (no `steps[]`, no version siblings).
  New dedicated `GET /api/recipes/<id>` returns the fully hydrated
  detail; cookbook detail, cook mode, and the new versions card all read
  the right data now.

### Added
- **Recipe Source URL + smarter URL importer (Cookbook Chunk 7).**
  - Recipes now have a dedicated **Source URL** field on the detail page —
    typed in, or auto-filled when imported. A small **Open** button next
    to the field jumps to the original page. The URL importer no longer
    appends a `Source: <url>` line to Instructions; the URL goes straight
    to its own field.
  - **Import from URL is now on the Cookbook overview** as well as the
    detail page. Click the new "Import from URL" button next to "New
    recipe" — paste a URL, and a fresh recipe is created and opened for
    editing. Ingredients that couldn't be auto-matched to your stock
    items are called out in the success toast so you can add them by
    hand.
  - **Graceful degradation** for pages without schema.org JSON-LD: the
    importer falls back to scraping the page title and body text into
    Instructions and shows a "couldn't auto-structure — review and edit"
    banner. Cleaner than the old "Could not parse that URL" rejection.
  - The import dialog copy now names a few representative sites
    (BBC Good Food, NYT Cooking, Serious Eats, AllRecipes…) so you can
    set expectations before pasting.

- **Cook mode — Cooking-for headcount auto-rescale (Cook Mode Chunk 6).**
  - The cook-mode header now has a compact **"Cooking for ___"** number
    input. Bump it up or down and every ingredient quantity rescales on
    the fly — 4-serving lasagne becomes 6 servings without doing the
    arithmetic in your head. Defaults to the recipe's saved servings
    on entry.
  - Quantities round into kitchen-friendly buckets: countable units
    (eggs / cloves / scoops / pinches / etc.) round to whole numbers
    (minimum 1); mass / volume snap to **½ / ⅓ / ⅔ / ¼ / ¾** when close,
    otherwise nearest one decimal place. "1½ cups", "2⅔ tbsp",
    "300g" — not "1.5 cups", "2.667 tbsp", "300.0g".
  - **Session-only** — the saved recipe never changes. Exit and come
    back, you're back at the original servings.

- **Cook mode — per-step highlight + tools panel + step hints (Cook Mode Chunk 5).**
  - Structured-step recipes (set up via the Cookbook Chunk 6 editor) now
    drive cook mode directly: walking through the recipe, the ingredients
    a step uses are **highlighted** in the ingredient panel and the tools
    that step needs are highlighted in the new **Tools panel** below it.
    Untouched tools dim out so the eye lands on what's needed right now.
    Recipes without structured steps fall back to today's text-matched
    highlight (which is still the smarter-than-nothing default).
  - Each structured step can carry a **hint** — a small lightbulb-marked
    line under the step text — and **sub-steps** display a "Sub-step" chip
    so the cook knows they're nested inside the parent.
  - The **per-step "done" checkboxes** and the **mark-used** checkboxes
    on each ingredient row are gone. Cooking a recipe implies using all
    its ingredients; the finish flow now ranges over every recipe
    ingredient automatically. ("Done" voice command is retired alongside
    the checkboxes.)

- **Cook mode overhaul — finish flow + polish + ingredient list (Cook Mode Chunks 1–3).**
  - **Finish dialog rewrite (Chunk 1).** The old "Finished cooking?" dialog
    with three blanket toggles is gone. Each ingredient you marked used now
    gets its own row in the finish list with quick chips — **Down one
    level** (default), **Out**, or **Unchanged** — plus an override drop-down
    if you want a specific level, plus a per-row **Add to list** button.
    The "How many meals?" field defaults to **0** (because "I just ate it"
    is the common case) and lands a celebratory toast — *"You saved N meals
    — enjoy."* or *"All eaten — hope it was good."* when zero. Clicking
    outside the dialog now cancels cleanly without touching stock.
  - **Cook-mode polish (Chunk 2).** The step timer now shows a horizontal
    fill-bar that empties as time runs out and changes tone when it
    finishes, plus a short beep (silent fallback if the browser denies
    audio). The voice button is renamed **Sous Chef** with a help popover
    listing every hands-free command — Next, Previous, Repeat, Start
    timer, Pause / Reset timer, Done, Exit — so you don't have to discover
    the verbs by trial and error. Unit spacing is centralised through a
    new `formatQuantity()` helper (250g, 2ml, 1 tbsp, 2 cloves — the
    no-space units list is one source of truth).
  - **Mid-cook ingredient list (Chunk 3).** Ingredients are now grouped
    by their **base** stock location (a sub-area like "Pantry > Spice
    Rack" collapses to "Pantry"), each group its own card. Stock-level
    chips no longer render during cooking — the decision to cook is
    already made, and the noise belongs on the finish surface instead.
    Ingredients with no location land in a final "No location" group.

- **Structured recipe steps (Cookbook Chunk 6).**
  - The recipe detail page now has a **Structured / Freeform** toggle for
    instructions. Structured mode gives you a per-step editor: each step has
    its own text field, an optional **hint** line, a multi-select for the
    **ingredients** it uses, and a multi-select for the **tools** it needs.
    You can add **sub-steps** under any top-level step (one level deep),
    reorder steps within their siblings, and remove steps cleanly (any
    references from other steps stop pointing at deleted ingredients).
  - Freeform mode keeps the original textarea behaviour for recipes you
    just want to type out. Switching between modes preserves what you've
    written; saving in freeform clears the structured set on the server.
    Structured-mode users also get an **Advanced** disclosure with the
    freeform textarea, kept as a cook-mode fallback for now.
  - **URL importer** now reads schema.org `HowToStep` / `HowToSection` and
    pre-fills the structured editor automatically when the source publishes
    them; sites without structured markup still drop into the freeform
    textarea as before.
  - **Backup / restore** round-trips the new step structure end-to-end.
  - Unblocks cook-mode's per-step highlight + per-step tools/hints (C-3
    Chunk 5). Recipes without structured steps continue to work everywhere
    unchanged — cook mode keeps splitting the freeform `instructions` on
    newlines until a recipe is edited into structure.

- **Recipe images + tools (Cookbook Chunk 5).**
  - **Recipe images:** upload a photo on the recipe detail page (and the New-
    recipe dialog); it shows on the recipe card and detail, with a coloured-
    initial placeholder when there's none. Change/remove supported; ~4MB cap.
  - **Tools:** recipes can list the kitchen tools they need (frypan, food
    processor, …) — a **user-configurable vocabulary** edited in
    **Settings → Recipe tags & categories → Tools**, multi-selectable on a
    recipe, with an **include/exclude tri-state filter** on the cookbook
    overview (same control as dietary tags).

- **Recipe detail page cleanup (Cookbook Chunk 4).**
  - Actions now sit in a **sticky toolbar across the top** (no more buttons
    stranded at the bottom on mobile): a prominent **Mark cooked**, Cook mode,
    Log cook, Print, then Save + a kebab. **Delete moved into the kebab**, well
    away from Mark cooked. **CSV export removed** from this page.
  - The recipe **name is now its own clearly-labelled field** (was a heading
    that didn't look editable).
  - **Starting cook mode is guarded:** a confirm appears if there are unsaved
    changes or the recipe isn't cookable now. The dialog has a real **Cancel**,
    clicking outside no longer navigates, and you can't enter cook mode if the
    save failed. **Exiting cook mode returns to the recipe** (not the overview).
  - **Saving** no longer silently eats a half-filled ingredient row (it blocks
    with a prompt), and an unchanged name can no longer block the save.
  - Ingredient rows show **one status chip** ("Missing" wins) and tint the row
    when missing, instead of stacking two chips.
  - The cookable/missing summary box is **theme-aware** (readable in dark mode).
  - "Meals on hand" renamed to **"Available meals"**.

### Fixed
- The recipe meal +/− no longer flashes a not-allowed cursor (uses a proper
  disabled state).

### Added (continued)
- **Cookbook card redesign + naming (Chunk 3).**
  - Recipe cards get an **image placeholder** tile (real images land in
    Chunk 5), an emphasised name, and a clearer **meals box** with an inline
    ± stepper to adjust the cooked-meals pool right from the overview.
  - A recipe with meals committed to upcoming plans now shows an
    **"allocated" badge** that turns **red on a shortfall** (more committed
    than cooked) — backed by a new server-derived `committed_meals` field.
  - **Cook is the card's only primary action.** Edit/Duplicate/Delete are
    gone from the card — clicking a card opens its detail page (the edit +
    delete surface).
  - Collection groups on the overview are now **collapsible, rounded boxes**.
  - **Naming:** the main-menu item, command-palette/keyboard "go to" actions,
    and the recipe-detail breadcrumb now read **"Cookbook"**.
  - **Dietary tags are now editable on the recipe detail page** (previously
    only on the New-recipe modal).

- **Recipe tag taxonomy overhaul (Cookbook Chunk 2).** Cuisine, category,
  and dietary tags are now **user-configurable vocabularies** instead of
  free text / a hardcoded list:
  - **Cuisine** and **Category** are distinct **single-select** fields on
    recipes (no longer lumped into one "tags" filter), each backed by an
    editable table.
  - **Dietary tags** move from an in-code catalogue to an editable table,
    and the overview filter is now a single **tri-state control** — click a
    tag to cycle must-have (green +) → must-not (red −) → neutral, and the
    dropdown stays open while you set several.
  - New **Settings → "Recipe tags & categories"** page to add / rename /
    delete cuisines, categories, and dietary tags (with recipe-usage counts
    and delete warnings).
  - The recipe edit form and detail page use single-select dropdowns for
    cuisine/category sourced from these tables; the URL importer matches a
    scraped cuisine/category against existing rows when it can.
  - **Breaking schema change (pre-release):** `Recipe.cuisine` /
    `Recipe.category` string columns become `cuisine_id` / `category_id`
    FKs; the `RecipeTag` link swaps its `tag` string for a `dietary_tag_id`
    FK. New `Cuisine` / `Category` / `DietaryTag` tables, seeded with the
    previous defaults (migration `a7d2f4c9e1b8`). Existing recipe
    cuisine/category text and old tag rows are discarded, not converted —
    re-tag recipes after upgrading.

- **Recipes overview — sort axes + new filters (Cookbook Chunk 1).** The
  recipes overview gains a **Sort by** dropdown (Name, Recently made,
  Meals in pool, Prep + cook time) and four new chip filters
  (Favourites / Cookable now / Have meals in pool / Planned in) plus a
  numeric **Meals ≥ N** input. The existing **Uses stock item** picker
  is now **multi-select**, with each option row carrying a small dot
  coloured by current stock level. "Planned in" reads loaded meal plans
  client-side for now (any entry from today onward); moves server-side
  when state-ownership lands.

### Removed
- **Recipe comparison mode (Cookbook Chunk 1).** The Compare / Show
  comparison buttons, per-card checkbox, and side-by-side comparison
  dialog are gone — INV-6 found the feature wasn't pulling its weight,
  and the new sort + filter axes cover the comparisons the user was
  actually doing.

### Fixed
- **Menu items now highlight on subroutes.** Top nav + side drawer items
  driven off Vue Router's route-record matching went dark on flat
  sibling subroutes (`/recipes/:id`, `/stock/:id`,
  `/shopping-lists/:id`, etc.); they now use path-prefix matching so
  any route under the page highlights the parent. The Recipes menu link
  also re-targets `/cookbook` directly (with `/recipes` as a secondary
  prefix) so the highlight works on the actual landing page.

### Added
- **Planned shopping day (P6-01 Chunk 7).** Shopping lists now carry an
  optional `planned_shop_date` (ISO date, nullable). The **New shopping
  list** dialog accepts the field; the detail header surfaces it as a
  clickable chip with a dedicated date-editor dialog (set / change /
  clear); the router landing prefers a DRAFT whose planned date is today
  when picking which list to open; the in-detail list selector sorts
  scheduled lists ahead of unscheduled. When today is the planned day (or
  the day has passed without finishing), a banner appears at the top of
  the list detail. Backend: nullable `Date` column + migration
  `e1a4c7b2f9d0`, create + update endpoints accept the field (explicit
  `null` clears).

### Changed
- **In-store polish (P6-01 Chunk 6).** Several shop-mode UX gripes from the
  feedback resolved together:
  - **Skip / jump persist now.** Skipping the current item or jumping to a
    later one used to be client-only and reverted on refresh; both now call
    `reorderLinesAsync` so the new order survives. "Jump to" places the item
    just before the first unticked line so it becomes the next "Got it"
    candidate.
  - **Tap-to-type quantity.** The centre number in the qty row is now itself
    a tap target — opens a numeric input dialog, so a count of 8 is one tap
    + one type rather than eight + presses.
  - **Whole-list peek.** New "Peek the whole list" button in the shop-mode
    header opens a dialog of every line (ticked + unticked). Tapping an
    unticked item jumps it to the front of the queue and closes the peek.
  - **Drag-and-drop off-by-one fixed** on the detail page. The dropped line
    now lands at the visual slot of the dragged-over row (feedback L414).
- **Detail page back-arrow removed** (Chunk 6 / FU-070). Pre-Chunk-5 it
  pointed at the standalone overview; with Detail now the canonical surface
  and a list selector in the header, the arrow only ever bounced through
  the landing.

- **Shopping-list overview merged into detail (P6-01 Chunk 5).**
  The standalone overview page is gone as a destination: `/shopping-lists` is now a
  router landing that picks a list by status priority (SHOPPING → newest DRAFT →
  newest DONE) and `replace`s to its detail. The detail page is the canonical
  surface — its header gains a **list selector** dropdown showing every list
  (active, then archived, with the current list highlighted), per-list kebab
  actions (Archive list / Delete list / Copy unticked → new / Copy archived → new)
  moved from the old overview cards, a **"+ New list"** entry that opens the
  unified dialog inline, and a *Manage templates…* link. When the user has zero
  lists, the landing renders a one-button empty state ("New list"). The new-list
  dialog is now a shared component (`NewListDialog.vue`) used by both pages.

- **Shopping-list creation (P6-01 Chunk 4) — one composable form replaces the five doors.**
  The overview's auto-generate menu (From flagged · Advanced auto-generate · From all
  low/out · Top up the primary list) and the detail page's "Append low + essentials" are
  consolidated into a single **New shopping list** dialog: pick a *start-from* source
  (empty / template / recipe / meal plan) plus optional *auto-fill* checkboxes
  (low/out, essentials-only sub-option, flagged, frequently added), then pick a *target*
  (create new / add to existing). All paths land on the same backing endpoints —
  `createAsync`, `instantiateAsync`, `addLineAsync`, `autoGenerateAsync` — so behaviour
  matches the old buttons for any single combination. The toolbar shrinks to one
  "New list" button plus a small "Manage templates" icon shortcut; the empty-state CTA
  now opens the same dialog with **Low / out of stock** pre-ticked.

- **Shopping-list lifecycle UI (P6-01 Chunk 3) — one primary-action button per phase.**
  The detail page now shows a single status-driven CTA: **Start shopping** on DRAFT,
  **Reopen** on DONE. SHOPPING isn't a button — it's the *surface*: starting shopping
  routes directly to shop mode, and a status watcher takes the user there if the list
  flips to SHOPPING by any other path (assistant action, another tab). Shop mode's
  back-arrow now reads as **"← Back to editing"** and actually reopens the list (status
  → DRAFT) before navigating, so it can't bounce back. The standalone **Shop mode**,
  **Review mode**, **Start / Stop / Finish shopping**, and **Finish review** affordances
  on the detail page are gone, as is the "Shopping in progress" banner and shop mode's
  redundant "Open full list" menu item. **Review is folded into the Finish confirmation**
  on both surfaces: the dialog lists the ticked items that will be bumped to Well-Stocked
  (preview-before-commit, R-009) so the user sanity-checks at the moment of decision.
  Finish & restock is now reachable mid-shop, not just when every item is picked.

- **Shopping-list quick-add (P6-01 Chunk 2) — "primary" is now inferred, not stored.**
  The `ShoppingList.is_primary` column is gone. The server resolves the quick-add
  target by DRAFT-count: 0 drafts → `result: "no_draft"` (the client offers to
  create one), 1 draft → silent quick-add, 2+ drafts → `result: "ambiguous"` with
  candidate `{shopping_list_id, name}`s for the client to pick from (remembered for
  the tab session in `sessionStorage`). `POST /api/shopping-lists/primary/lines`
  accepts an optional `shopping_list_id` hint for the disambiguated case. Finish no
  longer auto-promotes a sibling; Reopen no longer restores a prior primary;
  Create-list dropped `make_primary`; PATCH-list dropped `is_primary`; the
  assistant's `set_primary_list` action is gone (no flag to set). The PWA
  "Shop now" shortcut now routes by status (1 SHOPPING → resume; else 1 DRAFT →
  open; else overview). The membership endpoint replaces
  `primary_shopping_list_id` with `quick_add_target_list_id` (non-null only when a
  single draft exists) and active-list infos carry `status` instead of
  `is_primary`. Migration `d5e9f3b2a1c8` drops the column.

- **Shopping-list lifecycle (P6-01 Chunk 1) — one `status` field + server-owned undo.**
  The `is_archived` / `is_in_progress` boolean pair is replaced by a single `status`
  enum (`draft` / `shopping` / `done`); list summaries and detail now expose `status`
  and the legacy flags are gone from the API. **Finish** marks a list `done`, restocks
  its ticked items to Well-Stocked, and records what it changed in a server-owned
  `finish_snapshot` (prior primary, any auto-promoted sibling, each item's prior
  level). **Reopen** (`POST /…/unfinish`, no request body) reverses the finish straight
  from that snapshot — the client no longer posts a level-restore snapshot. `start` /
  `stop` move a list between `draft` and `shopping`; an invalid `status` PATCH is
  rejected (400). Migration `c4d8e1a6f3b9` converts existing rows
  (`is_archived→done`, `is_in_progress→shopping`, else `draft`) and drops the old
  columns.

### Fixed
- **Shopping-list line tick / delete always returned 404.** The parent-ownership guard
  in `update_line` / `delete_line` compared the entity's `UUID` FK against the path
  param (always a `str`), so the comparison never matched and every PATCH/DELETE on a
  line 404'd. Now compared as strings. (Pre-existing; surfaced by the new lifecycle
  e2e test.)

### Changed
- **Scanning & QR labels (P6-02) — corrected model + off-by-default gating.** A
  real-world barcode now identifies a *Product* (`ProductBarcode`), never a stock
  item: the `StockItem.barcode` column and its register/clear routes + wrong-model
  UI are removed. The whole scanning + QR-label surface (Stock Overview scan/print
  buttons, stock-item "Show QR", the Data → "Scanning & QR labels" section, and the
  admin toggle) is gated behind a new install-wide `scanning_enabled` flag (off by
  default), surfaced to the client via health `features.scanning`. The section is
  relabelled to state plainly that **scanning is a navigation aid only — it never
  looks up live prices**. Dora's own per-item QR labels and the
  product-barcode→product lookup are kept. The register-against-product UI and the
  scan-unknown rework are deferred to Phase 2 (ingestion). Design:
  `docs/04_proposals/PROPOSAL_BARCODE_SCANNING.md`.

### Fixed
- **Health capability flags `features.assistant` never reflected reality.** The
  health check called a non-existent `get_or_create_app_settings()` (plural,
  no-arg), swallowed by a try/except, so `assistant` was always `false`. Now
  reads the real `AppSetting` and reports both `assistant` and `scanning`.
- **Frontend build breakage (pre-existing, surfaced during verification).** Fixed
  `//` line comments inside plain-CSS `<style>` blocks that broke Vue SFC
  compilation ("Unexpected '/'") — `LoginPage.vue` (the login route wouldn't
  compile, so the app couldn't start) converted to `/* */`; `DashboardPage.vue`
  and `ProductSearch.vue` (which actually use SCSS nesting) corrected to
  `<style scoped lang="scss">`. Also resolved a batch of strict-TypeScript
  (`exactOptionalPropertyTypes`) errors and lint warnings in shared components
  (`BaseButton`, `FilterBar`, `BulkMoveLocationDialog`) and a few pages
  (`RecipeCookMode`, `MealPlansOverview`, `suggestionsApiService`). None were
  related to the state-ownership work; they were latent on the branch.

### Changed
- **Phase 1 (state-ownership) Chunk 5b — finished the Type-B tail.** (1) **Best
  deals**: new `GET /api/products/best-deals?limit=N` ranks on-special products by
  discount % and returns only the top N — the dashboard card now queries it instead
  of downloading *every* product to sort in the browser. The ranking rule lives in
  one server helper (`dora_api/domain/product_offer.py`); the client keeps the
  shared `discountPercent` only for the `% off` display (the inline `discountPctFor`
  copy is gone). (2) **List totals everywhere**: shop-mode and the lists-overview
  primary-list stats now read the server `totals` block (added in Chunk 5) instead
  of re-summing lines client-side, matching the dashboard + detail page.
- **Phase 1 (state-ownership) Chunk 5 — server-owned shopping-list totals
  (Type B).** `GET /api/shopping-lists/<id>` now returns a `totals` block
  (`total_price`, `remaining_price`, `total_savings`, `unticked_count`,
  `ticked_count`, `line_count`) computed server-side. The dashboard's
  "primary list" stats and the shopping-list **detail page** headline totals now
  read these instead of each summing `priceOfLine` / `savingsOfLine` across the
  fetched lines in the browser — so the cross-line totals can't silently diverge
  between surfaces. Per-line *display* price stays a client concern (the accepted
  `priceOfLine` helper). The budget card and "use soon" card were already
  server-owned, so they needed no change. **Note:** the "best deals" card (still
  fetches all products + sorts by discount client-side) and the shop-mode /
  lists-overview line sums are deferred to a focused follow-up (they need a
  discount-sort capability / per-list-summary totals).

### Added
- **Phase 1 (state-ownership) Chunk 4 — queryable cookability + dashboard
  `cookable_count`.** `GET /api/recipes` now accepts `?cookable=true|false` and
  `?max_missing=N` so callers can *query* for cookable / nearly-cookable recipes
  instead of fetching every recipe + the whole pantry and filtering in the
  browser (§3.3). `/api/dashboard/summary` gained `recipes.cookable_count` (recipes
  with nothing missing and at least one ingredient), surfaced as a count beside
  the "Cookable tonight" card title. The cookability rule is single-sourced in a
  new `dora_api/domain/recipe_cookability.py` (`missing_count_for`) and the
  per-recipe aggregation in a shared `load_recipe_cookability` query, both consumed
  by the recipe DTO, the new filter, and the dashboard — so the definition can't
  drift (R-003). The TS `RecipeFilterArgs` + dashboard model gained the matching
  fields.

### Changed
- **Phase 1 (state-ownership) Chunk 3 — deleted the client-side cookability
  copies.** Removed the ~7 browser reimplementations that matched the stock
  level name `'Out of Stock'` and joined recipes → stock items client-side to
  decide cookability (`RecipesOverview`, `RecipeCard`, `RecipeDetailPage`,
  `MealPlansOverview`, `DashboardPage`, `DoraChat`). They now read the
  server-owned fields added in Chunk 2/3: `recipe.cookable`,
  `recipe.missing_count`, and per-ingredient `is_missing` / `is_low_stock`. As a
  result the **Dashboard and Recipes Overview no longer fetch the entire stock
  table + all stock levels** just to filter — the "fetch everything to compute a
  rule" pattern is gone for cookability. The `RecipeIngredientDto` gained
  `is_missing` / `is_low_stock`; the TS `StockItem` model gained the Chunk-1
  derived booleans (`is_out_of_stock` / `is_low_stock` / `needs_restock` /
  `stock_level_sequence`) so the recipe-editor's per-ingredient "Missing" badge
  reads a server boolean instead of a level name. **Effect:** renaming a stock
  level can no longer make the cookable filters/cards disagree with the rest of
  the app, and cookable surfaces stop downloading the whole pantry.
- **Phase 1 (state-ownership) Chunk 2 — server-owned cookability on `RecipeDto`.**
  `RecipeDto` now carries `missing_count` (count of ingredients whose stock item
  is out-of-stock or has no level record) and `cookable` (`missing_count == 0`),
  computed server-side from the already-loaded ingredient tree using the §3.1
  `is_missing()` contract. Decision: presence-only (not quantity-aware), matching
  the existing client behaviour. The client currently recomputes this in 7
  locations; those copies will be deleted in Chunk 3. New unit tests
  (`tests/test_recipe_cookability.py`, 7 tests) pin the logic.
- **Phase 1 (state-ownership) Chunk 1 — single server-owned stock-status
  contract.** New `dora_api/domain/stock_status.py` is the one authority for
  what a stock level *means*, keyed to the level's ordinal `sequence`, never its
  display name. Every server feature that previously matched the `"Out of
  Stock"` / `"Low Stock"` / `"Well-Stocked"` / `"Sufficient Stock"` strings (or
  bare sequence literals) on its own — dashboard buckets, waste rescue + waste
  mark-out, the "keeps running out" report, alerts, the assistant tools, and the
  restock/stocktake/import level-assignment paths — now consumes the shared
  predicates (`is_out_of_stock`, `is_low_stock`, `needs_restock`, `is_missing`,
  `level_for_status`). Stock-item DTOs now expose `stock_level_sequence` plus
  derived `is_out_of_stock` / `is_low_stock` / `needs_restock`, so the client
  will no longer need to match a level name (client de-duplication is a later
  chunk). "Missing" / cookability counts out-of-stock only. **Effect:** renaming
  a stock level in the UI can no longer make the dashboard counts and the
  cookable/low filters silently disagree.
- **B9.3 — Removed duplicate "Settings" entry from the main nav menu.**
  Settings lives on the user avatar dropdown already; carrying it in both
  surfaces was confusing. The avatar dropdown is unchanged.
- **B9.2 — Main-menu hover renders a single outline.** Quasar's built-in
  `.q-focus-helper` overlay was stacking on top of the custom `::before`
  hover ring, producing a "double outline" on inactive hover that
  disappeared on active. Hidden the helper so the custom ring is the
  single source of truth.

### Fixed
- **A1 theme regression (Chunk D) — recipe chips/heart now theme-aware again.**
  Later feature work had re-introduced hardcoded Quasar palette literals on
  recipe surfaces after Chunk D was first signed off: the ingredient chip's
  neutral state (`grey-3`), the untracked-level chip (`grey-4`, which also gave
  white-on-light-grey text), the favourite-heart "off" state (`grey`), and the
  available-meals chip (`grey-7`). Neutral states now ride the `dora-bg-sunken`/
  `dora-text-secondary`/`dora-text-muted` helpers so they flip correctly in dark
  themes; the saturated `positive`/`negative` states keep their white-on-colour
  treatment, and the favourited heart stays red by design. (Sister regressions
  in Stock / Meal-plans / settings chunks are tracked in `DORA_FOLLOWUPS.md`
  FU-046 for a follow-up re-sweep.)
- **B9.6 — Price-history chart now extends to the surrounding card edge
  and resizes with the viewport.** Width was hard-coded to 720px on the
  page; replaced with a `ResizeObserver` on the chart card element so
  the chart fills the available column at every breakpoint. (Selection
  → chart binding and tooltip theming were already correct in current
  code — A1 had token-ified the tooltip — so no change there; logged for
  browser confirm.)
- **B9.8 — Floating Dora visible on mobile login + properly centred on
  Product Search / Dashboard greeting.** `LoginPage`'s mobile breakpoint
  was `display: none` on the mascot below 760px; now keeps her visible
  centred above the card (96px / 72px at the tighter 360px breakpoint)
  using `right: 50%; margin-right: -<half-width>px` so the existing
  `bob` keyframe (which owns the `transform` property) doesn't clobber
  horizontal centring. `dora-empty-mascot` (ProductSearch) and
  `dora-hero-mascot` (Dashboard) now force their inner `<img>` to
  `width:100%; height:100%; object-fit: contain` so the mascot sits
  centred in its padded box regardless of intrinsic aspect ratio.

### Added
- **A6 — "Extra large" text size + a wider, re-spaced scale.** The text-size
  preference now has four steps instead of three, with a clearly distinct
  spread (~0.85 / 1.0 / 1.25 / 1.4) and a very slightly larger default:
  **Small 14px · Medium 16.5px · Large 20.5px · Extra large 23px** (was
  14 / 16 / 18, which sat too close together). The new step is wired
  end-to-end (preference type, picker, and backend `ALLOWED_FONT_SIZES`;
  the DB column already fit "xl", so no migration).
- **A7 — Sticky page-counts footer (`PageCountsFooter`).** New
  `web_app/src/components/PageCountsFooter.vue`: a reusable footer that
  sticks to the bottom of the page scroll area (top border + soft
  elevation, tokenised), wraps responsively, and renders a list of
  `{ label, value, tone? }` stats. Counts reflect the **filtered** view.
  - **StockOverview**: the cramped top summary banner is removed; its
    counts now live in the footer — Shown + one stat per stock level
    (Well-Stocked / Sufficient / Low / Out, derived dynamically so it
    survives level renames) + Flagged + Auto-add + Needs attention. (The
    top toolbar itself is untouched — that teardown belongs to the Stock
    Overview Wave-C brief.)
  - **RecipesOverview**: top count text moved to the footer — Shown +
    Cookable now + Favourites.
  - **MyProductsPage**: top count text moved to the footer — Shown + On
    deal + Unlinked.
- **A5 — Shared loading components (`AppSpinner` + `AppSkeleton`).** Two
  new components in `web_app/src/components/`:
  - `AppSpinner.vue` — the one inline/short-wait spinner: consistent
    default size, theme-aware colour, optional label, and a `block` mode
    that centres it in a padded column.
  - `AppSkeleton.vue` — layout-mimicking placeholder blocks (`line` /
    `rect` / `circle`) that pulse on the same 1.6s rhythm as the boot
    splash, with theme-aware colours (mixed from `--surface-sunken` +
    `--text-muted`) and `prefers-reduced-motion` support.
- **A4 — Standard filter bar (`FilterBar`).** New
  `web_app/src/components/FilterBar.vue` gives every data-list page one
  filter skin: a persistent search box (`#search` slot) kept outside the
  collapsible panel; a collapsible filter panel (`#filters` slot) that
  defaults to **shown on desktop, hidden on mobile**; an active-filter
  count badge on the Filters toggle; and a single standard "Clear
  filters" button that appears only when ≥1 filter is active. Pages keep
  their own filter fields/predicates — only the mechanics/skin are shared.
- **A3 — Standard modal (`BaseDialog`).** New
  `web_app/src/components/BaseDialog.vue` wraps `q-dialog` + `q-card` so
  dialog behaviour is defined in one place: **not** `persistent` by
  default, so backdrop-click and Esc always **dismiss = cancel** (never a
  commit or navigation); token-based corner radius; an optional
  standardised header (`title` + `closable` close button) and footer
  (`#actions` slot); and a `cancel` event fired on any close. Specialised
  overlays are intentionally left on raw `q-dialog`: `AlertsBell`
  (seamless side drawer, no backdrop), `CommandPalette` (custom search
  overlay), and `ScanOverlay` (persistent camera overlay).

### Changed
- **A6 — Text size now applies more consistently.** Because the root
  font-size is driven by the preference, rem-based text (including Quasar
  `text-*` classes) already scaled — the gaps were fixed-px hold-outs.
  Migrated those to scale tokens so they follow the setting: the app-bar
  page title (`PageTitle`, was 24px), the Preferences theme-card blurb,
  and the Audit-log payload/mono text. Added a rule so **tooltips** follow
  the preference too. Deliberately left fixed (with reason): the scan
  overlay's camera UI, price-history SVG chart labels, and the dashboard's
  3px/7.5px micro-gauge text.
- **A5 — Unified loading states across the active app.** Replaced ad-hoc
  `q-spinner`s and placeholder-text loads with the shared components:
  - **Detail pages now use skeletons that mirror their layout** instead of
    flashing literal placeholder text. `StockItemDetailPage` no longer
    shows "Stock item" while loading (skeleton title + toolbar/card
    blocks); `ShoppingListDetail` no longer shows "Loading…" (skeleton
    rows); `RecipeDetailPage` shows a header + two-column skeleton.
  - **Spinners unified to `AppSpinner`** on the overview/search/other
    active pages: StockOverview-adjacent flows, RecipesOverview,
    ShoppingListsOverview (incl. inline "Loading totals…"),
    MyProductsPage, DashboardPage, ProductSearch (the searching banner —
    now consistent/theme-aware), RecipeCookMode (page + swap-picker),
    RecipeDetailPage substitutes, ShoppingListShopMode,
    ShoppingListTemplates, ShopNowRedirect, QuickAddSheet.
  - Left on raw `q-spinner` for now (out of scope / deferred surfaces):
    Reports, Data→Export/Print, Settings sub-pages, and DoraChat's typing
    dots (a deliberate indicator).
- **B8 — Recipe substitutes are now a temporary cook-session swap (no
  longer edit the saved recipe).** Previously, picking a substitute for a
  missing ingredient on the recipe detail page rewrote the editable recipe
  form and, on Save, **permanently replaced the ingredient** in the saved
  recipe. That destructive swap is removed. Instead:
  - **Cook mode** gains a per-ingredient swap (↔ icon): pick a substitute
    and it applies **only to that cook** — the saved recipe is never
    changed. Swapped ingredients show "Y instead of X" with an undo, and
    the finish flow decrements / restocks the *substitute* that was
    actually used, not the original.
  - The recipe-detail "Find substitutes" dialog is now **informational**:
    it lists the substitutes recorded on each missing item's detail page
    and points you to cook mode to use one.
  - Clarified naming: the basic per-stock-item substitutes feature is
    kept; only the long-deleted standalone **substitute *graph* page**
    (N7 `/substitutes`) stays removed. Stale "substitutes graph" wording
    in recipe/stock comments + labels reworded to just "substitutes."
  - Audited the other reported B8 defects against current code: favourite
    toggle, recipe actions, and related-recipe navigation all behave
    correctly post meals→recipes merge (the inert-actions / dead-nav
    reports no longer reproduce; there is no related-recipes section).
- **A4 — Filter standardisation across the data-list pages.** Migrated
  `StockOverview`, `RecipesOverview`, `MyProductsPage`, and `ProductSearch`
  to `FilterBar`. Replaced one-off filter affordances with the standard
  set: ProductSearch's bespoke "show filters" toggle and its "Clear
  ranges" button are gone (folded into FilterBar's toggle + standard
  Clear); each page now exposes an active-filter count and a consistent
  Clear.
  - **"Empty = off" hardened (regression-proofing).** The reported bug
    (clearing a filter excludes every row) was already *not* reproducing
    — every page skipped blank predicates. But the dropdown predicates
    relied on truthiness (`if (value && …)`), which would break if a
    default were ever non-null. Made them explicit `!== null` checks, and
    guarded the numeric "Missing ≤" filter with `Number.isFinite` so a
    blank/non-numeric value reliably means "filter off." Applied in
    `useStockFilters.ts`, `RecipesOverview`, `MyProductsPage`.
- **A3 — Standard modal migration.** Migrated all ~28 standard
  template `<q-dialog>` modals across 25 files to `BaseDialog`
  (new-recipe / edit-recipe, recipe substitutes / import-URL /
  target-list / log-cook, cook-mode "finished cooking", stock-item QR /
  expiry / level / substitute pickers, stocktake change, shopping-list
  shop-mode price-editor / offer-picker, advanced options, list-template
  editor, my-products bulk-add / orphans / link, product compare / link,
  meal-plan suggest / log-cook, recipe compare / add-missing, quick-add
  sheet, shortcuts cheatsheet, data backup / import / barcodes reports,
  price alerts, waste logger, verify-email resend, audit detail, user
  edit / reset). Dismiss is now uniformly non-committal; the destructive
  policy is **backdrop = cancel for all** (delete only fires from its
  explicit button). Programmatic `$q.dialog()` confirms (recipe delete,
  unsaved-changes, cook-start) were audited and already correct — they
  only commit/navigate on `.onOk()`, never on dismiss — so they were left
  as-is. Dialog cards that sized themselves via a scoped CSS class
  (`comparison-card`, `orphans-card`, `quick-add-sheet`) had that sizing
  moved to the `card-style` prop, since the card now lives in
  `BaseDialog`'s style scope.
- **A2 follow-up — `BaseButton` `danger-ghost` variant.** Added a flat
  negative ("ghost danger") variant for low-emphasis destructive actions
  (`{ flat: true, color: 'negative' }`). Replaces the flat-negative
  `q-btn`s that A2 Phase 2 had deliberately left unmigrated:
  `StockItemDetailPage` Delete + clear-expiry, `MealPlansOverview` Delete
  plan.
- **A2 — Standard button (Phase 2: detail-page toolbars + dialog footers
  + onboarding + auth/settings/data).** Migrated approximately 95
  `q-btn` instances across 20 additional files to `BaseButton`. App-wide
  count: 399 → 304 `q-btn` usages (the remainder are inline list-row
  buttons, `q-btn-dropdown`, `q-btn-toggle`, and `q-btn` instances
  inside `q-input` append slots — all out of scope for the standard-
  button base).
  - Detail-page toolbars + dialog footers: `StockItemDetailPage` (back,
    9 toolbar actions, delete kept as q-btn for flat-negative pattern,
    QR dialog Close/Print, Reset/Save form pair, Link product, Add
    substitute), `RecipeDetailPage` (back, favourite toggle, menu
    trigger, Save, three dialog Cancel/CTA pairs), `ShoppingListDetail`
    (back, rename, Shop mode, Set primary, more-menu, Review/Start/Stop/
    Finish actions, Copy-to-new), `ShoppingListShopMode` (price-editor
    Clear/Cancel/Save + offer-picker Close), `RecipeCookMode` (Exit,
    voice and mic toggles, finish dialog Skip/Done).
  - Dialog components: `RecipeEditDialog`, `MealPlanEditDialog` (each:
    Add-row icon, Add line, Cancel, Save). `CreateStockItemDialog`,
    `BulkMoveLocationDialog` (Cancel/CTA).
  - Onboarding: `WelcomeWizard` Skip everything, step "I'll do this
    later" / Add stock item, tour "Show me" cards, Back/Next footer.
  - Auth: `ForgotPasswordPage`, `ResetPasswordPage`,
    `ConfirmEmailChangePage`, `VerifyEmailPage` (continue/resend/cancel
    + resend dialog Send).
  - Settings: `UsersAdminSettings` (close-icon + Cancel/Done),
    `AuditLogSettings` (close + Close), `MerchantsSettings` (Retry).
  - Data: `BackupRestore` (Select all / Clear selection / Cancel /
    Close), `DataImport` (Cancel / Close), `BarcodesQR` (Close).
- **A2 — Standard button + page toolbar (Phase 1: components + main-page toolbars).**
  Built two new shared components and migrated the top-of-page toolbars on
  the six main overview / index pages. Inline q-btns elsewhere left as-is —
  scoped to top-of-page CTAs in this pass.
  - New: `web_app/src/components/BaseButton.vue`. Wraps `q-btn` with a
    fixed 36px height (for toolbar alignment) and five variants:
    `primary` (filled brand) | `secondary` (outlined brand) | `ghost`
    (flat, page-text colour) | `danger` (filled negative) | `icon` (round
    flat, square 36×36). Plus an `attention` boolean modifier that adds
    a pulsing brand-accent glow (the stocktake-button "look at me" effect).
    Honours `prefers-reduced-motion` (animation off → static glow).
  - New: `web_app/src/components/PageToolbar.vue`. Standard left-title /
    optional back-arrow / right-actions-slot row. Replaces ad-hoc header
    div rows on pages that already had a title pattern.
  - Migrated page toolbars: `StockOverview` (4 buttons + empty-state CTA),
    `RecipesOverview` (3 buttons), `MealPlansOverview` (2 buttons),
    `MyProductsPage` (2 buttons), `ShoppingListTemplates` (1 button),
    `StocktakePage` (wrapped header in PageToolbar, Refresh → BaseButton).
    Stocktake "glow when overdue" hand-rolled CSS removed — now uses
    BaseButton's `:attention="stocktakeOverdue > 0"` instead.
  - Convention: **"New X" CTAs use `variant="primary"` (brand colour),
    not `color="positive"` (green semantic).** Decouples create-action
    from success-semantic so Cherry Cola's "New" reads brand-red, not
    green. ShoppingListsOverview was already on `color="primary"` —
    untouched (uses `q-btn-dropdown` split-button which is out of
    BaseButton scope).
- **A1b — Token value tuning, round 2 (Pesto Dark + dual-source sync).**
  Pesto Dark green was still too vibrant after round 1 — toned further:
  `--brand-primary` / `--brand-accent` / `--semantic-positive` from
  `hsl(150 62% 50%)` to `hsl(150 48% 40%)`; `--chart-1` to `hsl(150 48% 45%)`;
  Dora halo tokens retuned to match. White button labels and dark chip
  text now contrast comfortably (white-on-darker-green ~5.5:1 AA pass).
  Pesto Dark `--text-secondary` lifted `hsl(205 12% 67%)` → `hsl(205 14% 78%)`
  and `--text-muted` `hsl(205 10% 55%)` → `hsl(205 12% 66%)` so captions /
  subtitles pop on the dark page.
  - **Caught a dual-source bug:** `web_app/src/services/themeService.ts`
    holds a parallel `THEMES` palette dict that `setCssVar` writes into
    `--q-*` on every theme switch. Quasar's `color="primary"` / `bg-positive`
    components ride `--q-primary` / `--q-positive`, so the new values in
    `themes.scss` were getting overwritten by the stale themeService values
    on theme apply. Synced the Pesto, Pesto Dark, and Lemon Tart Dark
    palette entries so the Quasar-driven path matches the CSS-driven path.
    (The dual-source warning lives in the themeService comment — flagged
    for collapse into a single source in a future refactor.)
- **A1b — Token value tuning.** Pure-value sweep over `tokens.scss` and
  `themes.scss` (plus three template clean-ups that became possible once the
  underlying tokens flipped).
  - Added two missing tokens to `tokens.scss`: `--overlay-hover-on-coloured`
    / `--overlay-active-on-coloured` (light veils for hover on saturated
    brand surfaces — toolbar, main-menu strip) and `--highlight-search`
    (alpha-blended search-match background, theme-tinted via
    `color-mix(var(--brand-accent) 40%, transparent)`).
  - Rewired `MainMenuButton.vue` hover veil to `--overlay-hover-on-coloured`
    (was `rgba(255,255,255,0.08)`). Rewired `CommandPalette.vue` `.cp-hl`
    matched-substring background to `--highlight-search` (was raw rgba).
    Rewired `CommandPalette.vue` `.cp-row--selected` to `color-mix(in srgb,
    var(--brand-primary) 12%, transparent)` so the selection band picks up
    the active brand.
  - Deleted the `.body--dark` overrides in `CommandPalette.vue:404,428` and
    `ShortcutsCheatsheet.vue:85` — they were legacy workarounds for a
    token-flip gap that no longer exists (`--overlay-hover` already flips
    per dark theme in `themes.scss`).
  - `--ring-focus` is now theme-aware in every theme via
    `color-mix(in srgb, var(--brand-primary) 35%, transparent)` (45% in
    Pesto Dark). Previously hardcoded to Pesto-green hsla in every theme.
  - Pesto: `--brand-primary` saturation toned from `hsl(150 76% 39%)` to
    `hsl(150 60% 36%)` — fixes the "add" / cookable green that read too
    bright across the app.
  - Pesto Dark: `--brand-primary`, `--brand-accent`, `--semantic-positive`,
    `--chart-1` toned from `hsl(150 75% 55%)` to `hsl(150 62% 50%)` —
    fixes the unreadable green chips (connections / stores / well-stocked).
    Dora halo tokens retuned to match the new brand value.
  - Lemon Tart Dark: `--semantic-warning` toned from `hsl(46 100% 55%)`
    (pure yellow at 100% saturation) to `hsl(40 90% 60%)` — readable
    warning chips again.
  - Cherry Cola Dark + Sourdough Dark: Dora halo alpha dropped (0.28→0.22,
    0.50→0.40, 0.55→0.42 etc.) so the dora-glow doesn't overpower the
    rest of the chrome.
  - `--text-muted` (Pesto defaults + `[data-theme="pesto"]` override) bumped
    from `hsl(168 8% 50%)` to `hsl(168 10% 42%)` — fixes the borderline
    AA contrast against `--surface-page`.
- **A1 STEP 2 — Theme token-compliance (Chunks D, G, C, B, E, H, F).**
  Completed the audit's remaining chunk list in one pass: recipes/cook (D),
  settings (G), products/price-history (C — minimal-touch per master Decision
  1; surface is companion-bound), stock (B), meal-plans/shopping (E),
  dashboard/reports/waste/data (H), and Dora chat/help (F). All Quasar
  numbered palette classes (`text-grey-7`, `bg-red-1`, …) and palette
  `color=` / `text-color=` / `track-color=` props swapped for semantic
  tokens or theme-aware Quasar semantics (`text-positive`, `bg-negative`,
  `color="warning"`, etc.). Hardcoded `rgba(23,176,115,…)` / `rgba(74,56,26,…)`
  literals routed through tokens via `color-mix(in srgb, var(--token) X%,
  transparent)`. Dashboard ink-shadows now use `var(--elevation-card[-hover])`
  (DEC-11). StockOverview's "just-added" pulse now uses `var(--brand-accent)`
  (DEC-7). MainMenuButtonStrip indicator glow uses `var(--brand-accent)` at
  α 55% (DEC-6).
  - **DEC-3 implemented:** added `--dora-disc-bg` / `--dora-halo` /
    `--dora-halo-strong` tokens to `tokens.scss` (Pesto defaults) plus
    per-theme overrides in `themes.scss` for all 10 theme variants.
    `DoraBubble.vue`'s disc backdrop and `DoraChat.vue`'s header / bubble
    gradients now ride these. The `.body--dark` workaround blocks for the
    bubble disc / chat bubble / chat thinking spinner removed — the tokens
    flip per theme automatically.
  - **Charts:** `usePriceHistoryPalette.ts` now reads `--chart-1`…`-5` from
    CSS at call time (with HSL fallbacks for SSR / pre-paint).
    `TrendSparkline.vue` reads `--semantic-positive`/`-negative` the same
    way. `PriceHistoryChart.vue` SVG strokes/fills moved to CSS classes
    (`.chart-gridline`/`.chart-axis-label`/`.chart-crosshair`) so they
    ride `--divider` / `--text-muted` / `--border-strong`.
  - **Accepted carve-outs:** brand-logo hex (Aldi/Coles/IGA),
    `ProductSearchCard.vue`'s deterministic-hash category swatch (DEC-8),
    `MerchantLogo.vue` placeholder (DEC-9), `ScanOverlay.vue` rings
    (DEC-4), `pages/settings/PreferencesSettings.vue:65,73` theme-picker
    swatches (DEC-10), and the canvas/EChart `read('--token', '#hex')`
    fallback pattern in `ReportsPage.vue` / `DashboardPage.vue` (the hex
    only paints if the token read fails, which it never does in this
    codebase).
  - **Deferred to A1b** (filed in `web_app/THEME_AUDIT.md §6b` and the
    new DEC-A-1 / DEC-A-2): `--overlay-hover` theme-flip + a
    `--highlight-search` alpha token, so `CommandPalette` /
    `ShortcutsCheatsheet` `.body--dark` overrides can be deleted later.
- **A1 STEP 2 — Theme token-compliance (Chunk I: onboarding).** Repainted
  `pages/onboarding/WelcomeWizard.vue` — all `text-grey*`, `bg-red-1` banner,
  and grey-shaded skip-button/icon colours now ride the semantic tokens
  introduced in Chunk A. Also dropped `track-color="grey-3"` from the step
  progress bar so the track theme-flips automatically.
- **A1 STEP 2 — Theme token-compliance (Chunk A: auth/shell).** Replaced
  hardcoded Quasar palette classes (`text-grey`, `bg-red-1`, `bg-grey-2`,
  etc.) and pinned colour literals with semantic design tokens across the
  always-on chrome and auth pages. No visible behaviour change in light mode;
  dark themes (Pesto Dark, Cherry Cola Dark, etc.) now read correctly on
  these surfaces. Added a small `dora-*` helper-class set in
  `web_app/src/css/colours.scss` (`dora-text-muted`, `dora-text-secondary`,
  `dora-bg-sunken/elevated`, `dora-bg-{positive,negative,warning,info}-soft`,
  `dora-text-on-{primary,toolbar}`) — these are reused by future chunks
  B–I. Files touched: `OfflineBanner.vue`, `PageErrorState.vue`,
  `CommandPalette.vue`, `AlertsBell.vue`, `PwaInstallPrompt.vue`,
  `ShortcutsCheatsheet.vue`, `FormErrorSummary.vue`, `MainMenuButtonStrip.vue`,
  `ErrorNotFound.vue`, `ForgotPasswordPage.vue`, `ResetPasswordPage.vue`,
  `VerifyEmailPage.vue`, `ConfirmEmailChangePage.vue`, `SettingsShell.vue`,
  `WelcomeLayout.vue`. `LoginPage.vue` deliberately excluded (its `--lp-*`
  splash ladder is kept as intentional per DEC-2). Audit + chunk plan at
  `web_app/THEME_AUDIT.md`.

### Removed
- **B7 — Quasar boot scaffold `boot/axios.ts`.** Dead-since-bootstrap file
  that exported an Axios instance pointed at `https://api.example.com` and
  hung `$api` / `$axios` on global properties. Never registered in
  `quasar.config.ts`'s `boot:` list, and nothing in `src/` referenced
  either property. The real API client lives in `src/services/api/axiosHttpClient.ts`.

### Added
- **B5 — Minimal Alerts page at `/alerts`.** Stopgap so the dashboard's
  "All N →" link and any other `/alerts` navigation no longer 404s. Reuses
  `alertStore` (the same data the header bell already fetches), groups items
  by severity (high / medium / low), shows a collapsed "Snoozed" section at
  the bottom, and click-throughs row → stock item detail. Deliberately does
  NOT carry inline actions (push expiry, mark restocked, snooze) — those
  still live on the bell panel. A banner on the page makes that explicit
  and points users at the bell. The full alerts control centre with bulk
  actions remains the C-wave design brief.

### Fixed
- **B7 — "I'm a notification!" placeholder caption removed from the global
  `info` toast type.** `boot/notifyTypeRegistration.ts` registered the
  custom `info` type with `message: 'Hey did you know...'` and
  `caption: "I'm a notification!"` as Quasar Notify defaults. Any
  `notify({ type: 'info' })` that didn't override the caption (most of
  them) rendered the placeholder underneath the real message — which is
  how it landed in the Meal Plans "Generate shopping list" toast in
  production. The type registration now sets visual defaults only
  (color/icon/progress) and leaves message+caption to the call site.
- **B7 — Stocktake quick-add no longer fires two contradictory toasts.**
  `StocktakeRunner.onAddToList` was calling the bulk-add composable
  (`useShoppingListActions.addItems`) for a single item — which emits
  its own summary toast ("0 added, 1 already on list." or "1 added.") —
  and then fired a second `${name} added to primary list.` toast on
  top, producing the reported double / contradictory pair. Switched
  StocktakeRunner to the existing single-item action
  `useStockItemActions.addToList`, which emits exactly one accurate
  toast ("Already on your primary list." vs "Added to primary list.")
  and handles the no-primary-list dialog for free. The unused
  `useShoppingListStore` / `useShoppingListActions` imports went with
  it. Sweep: the other four `addItems` callers (`QuickAddSheet`,
  `AlertsBell`, `MyProductsPage`, `DoraChat`) don't stack a second
  toast on top — clean.
- **B5 — Dashboard "All N alerts →" link no longer 404s.** Wired by adding
  the `/alerts` route (see Added above); no Dashboard code changed.
- **B5 (follow-up) — Dashboard "Continue" button on the skipped-setup
  banner no longer silently bounces back to the dashboard.** Same
  stale-state guard shape, mirror direction: Skip Everything stamps
  `onboarding_completed_at`, so the wizard route is now sealed off —
  the guard at `router/index.ts:103-109` redirects authed users with a
  non-null timestamp away from `/welcome`. The button was a bare
  `to="/welcome"` link, so the navigation fired and immediately
  reversed. Now wired to a handler that calls
  `onboardingApi.restartAsync()` (existing backend route at
  `POST /onboarding/restart`, frontend service method already in
  `onboardingApiService.ts`), `await authStore.refreshAsync()` so the
  guard sees the now-null timestamp, clears the
  `dora.onboarding.skipped_at` localStorage flag, then pushes
  `/welcome`. Mirrors the existing "Restart onboarding" flow in
  `AccountSettings.vue`.
- **B5 (follow-up) — Onboarding Skip everything / Finish / Show-me-X
  buttons no longer appear dead, requiring a browser refresh to escape
  the wizard.** Root cause was a stale-state guard race, not a missing
  click handler: `onboardingApi.completeAsync()` updates the server,
  but the frontend `authStore.currentUser` wasn't refreshed before
  `router.push(...)` ran. The global router guard
  (`router/index.ts:97`) reads
  `authStore.currentUser?.onboarding_completed_at` and bounces users
  with a `null` value straight back to `/welcome` — so the navigation
  fired, then the guard reverted it, and from the user's perspective
  nothing happened. A hard refresh re-bootstrapped the auth state and
  unblocked the path. `WelcomeWizard.complete()` and
  `onSkipEverything()` now `await authStore.refreshAsync()`
  immediately after `completeAsync()` so the guard sees the new
  timestamp on the very next navigation.
- **B4 — Stock-item delete no longer 500s when the item is used by a recipe.**
  The only FK with `ondelete="RESTRICT"` on `StockItem` is
  `RecipeIngredient.stock_item_id`; everything else already cascades
  (shopping lines, templates, product joins, level-change history, legacy
  substitutes) or sets-null to preserve history (waste events). The delete
  handler now pre-checks for blocking recipes and, when any exist, returns a
  structured 422 with a `blocked_by_recipes: [{recipe_id, name}, …]`
  extension on the problem-details body. The Stock Item Detail page parses
  that and pops a "Still used by recipes — remove from these first" dialog
  with the recipe names instead of the previous generic error toast. The
  vague "Recipes that use it will be left with a dangling reference" warning
  on the initial confirm dialog is gone — it described an outcome the FK
  constraint never actually allowed. Sweep confirmed there are no other
  delete routes exposing a RESTRICT FK (Product → Merchant is RESTRICT but
  has no delete endpoint).
- **B1 — "Extra inputs are not permitted" on product save / quick-add / link /
  mark-inactive.** Two frontend-side payload mismatches against
  `extra="forbid"` request models. (1) `productApiService.updateAsync` was
  PATCHing the entire `UpdateProductCommand` (including `product_id`) into the
  request body; now strips `product_id` before sending — fixes Save toggle,
  bulk Mark inactive, and per-row Mark active/inactive on Product Search and
  My Products. (2) `ProductSearch.vue`'s `ensureSaved` spread the full
  `ScrapedProductOffer` into `CreateProductCommand`, leaking
  `is_saved` / `is_saved_product_active` / `price_difference` / `price_per_cup`;
  now builds an explicit command — fixes Save (create), Quick-add to primary
  list, and Link to stock item (all three go through `ensureSaved` first).
  Backend request models unchanged — `extra="forbid"` kept as the guardrail.
  Link-to-stock-item already saved the product first via `ensureSaved`
  (single user action); confirmed and unchanged.

### Added
- **P2-13 — Voice-first Dora + hands-free cook mode.** Extracted the
  ad-hoc voice handling from `RecipeCookMode.vue` into two reusable
  composables and wired voice into the Dora chat panel.
  - `web_app/src/composables/useVoiceInput.ts` — Web SpeechRecognition
    wrapper. Supports both push-to-talk (Dora chat) and continuous
    (Cook mode) modes through one `continuous` option. Auto-restarts
    on browser-side `onend` in continuous mode, surfaces permission /
    capability failures through `available` and `error` refs.
  - `web_app/src/composables/useSpeechOutput.ts` — SpeechSynthesis
    wrapper. Cancels prior utterances before speaking the next so
    rapid commands ("next" → "next") don't queue up.
  - Dora chat header gains a **🔊 / 🔇** toggle (when the browser
    supports SpeechSynthesis) — Dora speaks her reply alongside the
    typewriter animation when enabled. The Dora input row gains a
    mic button (push-to-talk) when SpeechRecognition is available;
    the transcript fills the draft so the user reviews and presses
    Send — the spec's "confirm before mutating" without a separate
    confirmation step.
  - Cook mode picks up new voice commands beyond next / previous /
    repeat / stop: **start timer / pause timer / reset timer** (uses
    the auto-detected duration from the current step, falls back to
    5 minutes) and **mark done** (toggles the current step's checkbox
    without auto-advancing).
  - `User` gains `voice_input_enabled` + `voice_output_enabled`
    booleans (alembic `e7c4b8a1d2f9`). Off by default — the SPA seeds
    the per-page toggles from the user's saved preference and writes
    flips back through `PATCH /api/auth/me`. New **Voice** card in
    Settings → Preferences exposes both toggles, with explanatory
    captions when the browser doesn't support the underlying API.
- **P2-11 — One-handed shop mode.** Fullscreen mobile-first view for
  in-store use. One item at a time as a big card; tap "Got it" (or
  press Space / Enter) to mark picked and advance. Secondary actions
  on each item: quantity stepper, **Price** (opens the P2-02 actual-
  paid editor inline), **Substitute** (swap merchant from the line's
  known offers), **Skip** (locally re-order to the end of the queue —
  comes back later in the shop). **Undo** (ArrowUp / "u") un-ticks the
  last pick. Esc exits back to the full list view.
  - New route `/shopping-lists/:id/shop` and `ShoppingListShopMode.vue`.
    Reuses the existing offline queue (`tryWithQueue`,
    `shopping_list_line_tick` kind) so ticks survive flaky reception.
  - Items grouped by their stock-location breadcrumb so the natural
    pantry/store route reads as a sequence of sections; "Up next"
    preview shows the next two items so the shopper can anticipate.
  - Progress strip + footer totals (picked count, estimated total)
    sticky to top and bottom; **Finish** CTA appears once everything
    is ticked.
  - Big tap targets (≥56px), keyboard shortcuts with a focusable
    root, `<q-linear-progress>` for accessibility-friendly progress.
  - Entry point: "Shop mode" button on `ShoppingListDetail` toolbar
    (disabled when the list is empty); command palette entry
    "Shop mode on primary list"; new PWA shortcut **Shop now** that
    lands on `/shop-now` and resolves to the primary list's shop view
    (falls back to the lists overview when no primary is set).
- **P2-08 — Recipe dietary tags + tag-aware filtering.** Reframed
  from the spec's "per-user dietary profile" model into recipe-level
  metadata that's useful when cooking *for* people — household guests
  with allergies, dietary preferences, etc.
  - New `RecipeTag` association table (alembic `d3a5e8c1f9b2`).
    Composite PK + index on `tag` for the "find recipes with X" hot
    path. Pure association table — no entity, accessed via
    `dora_api/features/recipes/recipe_tag_access.py`.
  - Canonical curated vocabulary in `dora_api/domain/recipe_tags.py`:
    20 tags across dietary patterns, allergen-free, nutritional,
    diet patterns, religious. Server validates writes against this
    catalogue; the SPA pulls it from `GET /api/recipes/tags`
    (catalogue + plain-English disclaimer) so picker UIs stay in sync.
  - `POST /api/recipes` + `PATCH /api/recipes/<id>` accept `tags: []`.
    Invalid tags surface as 400 with the offending value.
  - `GET /api/recipes` accepts three composable filter axes via
    repeated/comma-separated query params:
    - `tags_include` — recipe must carry every tag (AND semantics).
    - `tags_exclude` — recipe must carry none of the tags.
    - `ingredient_exclude` — recipe must not have an ingredient whose
      stock-item name contains any of the substrings (case-insensitive),
      so "free from egg" / "no mushrooms" work without an allergen
      taxonomy.
  - Recipe edit dialog gains a multi-select tag picker grouped by
    category, with the catalogue's disclaimer surfaced underneath.
  - Recipes overview gets three new filters (must have / must not have
    / free from ingredient) wired client-side off the loaded recipe
    list. Disclaimer surfaces whenever any dietary filter is active.
  - Recipe cards render tag chips when present.
  - Meals derive an effective tag set by intersecting the tags of every
    constituent recipe — a meal is honestly "vegan" only if every
    recipe in it is. A single untagged recipe blanks the intersection
    so we don't imply unsubstantiated dietary claims.
  - `suggest_recipes` Dora tool extended with `tags_include`,
    `tags_exclude`, `ingredient_exclude` parameters. Tool description
    explicitly steers dietary asks ("vegan dinner", "gluten-free
    pasta", "free from egg") to the filter args rather than keywords,
    and repeats the planning-aid framing so the model doesn't claim
    food-safety guarantees.
- **P2-04 — Dora suggestion inbox (deterministic, no LLM-generated
  facts).** Surfaces actionable proposals as a small badge on the Dora
  launcher and a "Dora suggests" dashboard card. Opening the chat shows
  the same suggestions as cards above the conversation, each with
  **Accept** (deep-links to the relevant page + auto-snoozes 1h so it
  doesn't immediately re-surface), **Snooze 1d**, **Dismiss**, and a
  **Why?** expander.
  - Generated suggestions are *not* persisted. Generators recompute
    fresh each call so the list always matches current pantry state.
    Only *negative* decisions land in storage as
    `DoraSuggestionSuppression` rows (alembic `c9f2d6b3e8a1`, composite
    index on `kind + dedup_key`). Elapsed snoozes self-clean on the
    read path.
  - Four generators wired up, each piggy-backing on data we already
    capture: `use_soon` (≤3 day expiry — uses P2-06), `over_budget`
    (current period spend exceeds target — uses P2-05),
    `likely_due` (purchase cadence says they're past their usual gap —
    uses P2-02 cadence; needs ≥3 priced archived buys to fire),
    `frequent_waster` (3+ waste events for the same item in 90 days —
    uses P2-06's log).
  - `GET /api/suggestions` returns the filtered, ranked list (high →
    medium → low). `POST /api/suggestions/dismiss`,
    `POST /api/suggestions/snooze` (hours, clamped 1–168),
    `POST /api/suggestions/unsuppress` (undo).
  - New Pinia `suggestionStore` shared by `DoraBubble`, `DoraChat`, and
    `DashboardPage` so dismiss/snooze in one place propagates to all
    three. Store swallows endpoint errors so older backends just keep
    the badge hidden.
  - New assistant tool `list_suggestions` returning the same rows so
    Dora can answer "what do you suggest?" / "anything I should do?".
    Each suggestion includes its plain-English `reason` so the model
    can repeat it back without re-deriving the fact.
- **P2-06 — Expiry rescue + (optional) waste log.** Closes the
  "what's about to spoil and what can I do about it?" loop without
  asking the user to enter shelf-life metadata up-front.
  - New `StockItemWasteEvent` table (alembic `b8d4e1c7a2f3`). FK to
    StockItem is SET NULL with a denormalised `stock_item_name` so
    waste history survives renames and deletions.
  - `GET /api/waste/rescue?horizon_days=N` returns at-risk items
    (existing `expiry_date` ≤ horizon) and the recipes from the user's
    library ranked by how many at-risk items they'd use. Pre-fills
    `estimated_value` from the most recent captured price (P2-02)
    so the rescue page can put a dollar figure on what's on the line.
  - `POST /api/waste/events` + `GET /api/waste/events` for the log,
    `GET /api/waste/insights?window_days=N` for the aggregated view.
    Logging an event optionally bumps the level to Out of Stock so the
    common "throw it out → pantry's empty" case is one tap.
  - New `/waste` page: at-risk items with one-tap **Used** (clear
    expiry + mark Out of Stock), **Freeze** (clear expiry), **Wasted**
    (open log dialog with reason / value / note). A side panel ranks
    recipes by rescue coverage; an insights strip at the bottom shows
    what's been wasted in the last 90 days.
  - New dashboard card **Use soon** — peek-only, hidden when nothing
    is at risk, deep-links to `/waste`.
  - Two new Dora tools: `expiry_rescue` ("what should I use before it
    goes off?") and `waste_insights` ("what am I wasting often?"). The
    insights tool returns `status: no_data` cleanly when the user
    hasn't logged anything, so Dora can suggest the Waste page rather
    than hallucinate stats.
- **P2-05 — Optional grocery budget (cross-shopping-list).** Users opt
  in from Settings → Preferences → Grocery budget; the dashboard then
  shows spent / remaining for the current rolling period (weekly or
  monthly) and Dora can answer "what's left in my budget?".
  - `User` gains `budget_amount` (nullable; NULL = feature off) and
    `budget_period` (default `weekly`) — alembic `a6e3b5d2c8f1`.
    Surfaced on `AuthenticatedUserDto` and mutated through the existing
    `PATCH /api/auth/me` with `clear_budget_amount` to opt back out.
  - `GET /api/budget/status` returns `{ enabled, amount, period,
    period_start, period_end, spent, projected_active, remaining,
    over_budget }`. Spent = sum across every *archived* shopping list
    whose `completed_at` falls inside the period, using the
    actual_unit_price / picked_offer_price ladder from P2-02. Projected
    = same calc for active lists at current offer prices (never counted
    as spent, but shown as "+X in active lists").
  - `GET /api/budget/history?periods=N` for a trailing window — clamped
    1–26.
  - New dashboard card "Grocery budget" — degrades to a passive
    "spend this period" line for users who haven't opted in.
  - New read-only assistant tool `budget_status` answering "what's
    left?", "how much have I spent this week?", "am I over budget?".
    Reports `enabled=false` cleanly when the user hasn't opted in so
    Dora can nudge them to Settings.
- **P2-02 — Actual price + merchant capture per line, and a Dora
  purchase-price-stats tool.** Closes the planned-vs-paid loop without
  asking the user to scan receipts: a tap on the price chip in
  ShoppingListDetail opens an inline editor for the unit price the till
  actually charged and (optionally) the merchant they bought from.
  - `ShoppingListLine` gains `actual_unit_price` and
    `purchased_merchant_id` (alembic `f5c2a7e91b08`). Both NULL by
    default; reports + the assistant fall back to the existing
    `picked_offer_price` snapshot when no override is set.
  - `PATCH /api/shopping-lists/<id>/lines/<lid>` accepts the new fields
    plus `clear_actual_unit_price` / `clear_purchased_merchant` to wipe
    a prior override. Editing these does NOT flip `added_via` back to
    `manual` — it's a shopping-mode capture, not a re-curation.
  - Frontend `priceOfLine` + `savingsOfLine` now prefer
    `actual_unit_price` over the offer price; list totals reflect what
    the user actually paid.
  - New read-only assistant tool `purchase_price_stats(item_name)`
    answering "what's the average price for broccoli?" and similar.
    Walks finished (archived) shopping lists, prefers
    `actual_unit_price`, falls back to `picked_offer_price`. Returns
    samples / avg / min / max / stdev / last-paid plus a per-merchant
    breakdown derived from `purchased_merchant_id` (or the chosen
    offer's merchant when not overridden). Also surfaces cadence stats
    from the same walk — `days_since_last_purchase`,
    `average_days_between_purchase`, `average_quantity`,
    `usual_merchant` (+ share) — so Dora can answer "how often do I
    buy bread?" and "where do I usually shop for cheese?" without a
    second tool call.
- **Desktop bundle — Phase 4 (AppImage packaging).** Wraps the
  PyInstaller one-folder output into a single
  `Dora-vX.Y.Z-x86_64.AppImage` distributable. AppImages run
  unchanged on any modern Linux desktop with `fuse` installed —
  copy the file, `chmod +x`, double-click.
  - [`packaging/appimage/AppRun`](packaging/appimage/AppRun) —
    entry stub that exports `LD_LIBRARY_PATH` + `GI_TYPELIB_PATH`
    so WebKitGTK / glib / cairo resolve to bundled copies, then
    execs the Dora binary.
  - [`packaging/appimage/dora.desktop`](packaging/appimage/dora.desktop)
    — desktop entry. Categories + Keywords picked so the file
    manager + menu searches surface it on terms like "pantry",
    "groceries", "deals".
  - [`packaging/appimage/build-appimage.sh`](packaging/appimage/build-appimage.sh)
    — builds the AppDir tree, fetches `appimagetool` on first run
    (cached in `packaging/.cache/`), packs to
    `dist/Dora-vX.Y.Z-x86_64.AppImage`. Version pulled live from
    `dora_api.features.help.version_info.CURRENT_VERSION`.
  - `packaging/build-linux.sh` learns `--appimage` to chain into
    the AppImage step automatically.
  - `.gitignore` adds `packaging/.cache/` for the cached
    appimagetool.

### Added
- **Desktop bundle — Phase 3 (PyInstaller spec + build script).**
  Produces a self-contained `dist/Dora/Dora` binary on Linux that
  bundles the Python runtime, both Flask APIs, the built SPA, all
  alembic migrations, the seed JSONs, and the email templates.
  - [`dora.spec`](dora.spec) — PyInstaller one-folder spec. Explicit
    hidden imports for sqlite dialect, alembic runtime, apscheduler
    triggers, pywebview's GTK backend, dependency_injector wiring.
    `collect_submodules()` for the dynamically-discovered `features/`
    packages so PyInstaller doesn't miss them. Data files bundled:
    `web_app/dist/spa`, `dora_api/persistence/migrations`,
    `dora_api/email_templates`, `emailer/templates`, the bundled
    seed JSONs. Bundle's icon is `packaging/icons/dora.png`.
  - [`packaging/build-linux.sh`](packaging/build-linux.sh) —
    one-button build script. Defaults: install npm deps if missing
    → `quasar build` → `pyinstaller dora.spec`. Flags
    (`--skip-spa`, `--skip-pyinstaller`, `--clean`) for iteration.
    Prints final bundle size + smoke-check instructions.
  - `requirements.txt` adds `pyinstaller==6.10.0` so the toolchain
    is one `pip install -r requirements.txt` away.
  - `.gitignore` ignores `build/` + `*.AppImage` (Phase 4 output).

### Changed
- **Distribution prereqs (desktop + mobile clients).** Backend
  prep that unblocks both deliverables in the
  `Distribution Spec - Desktop App & Mobile Client.md`.
  - **`/api/health` now returns a JSON object** with `ok`, `version`
    (`CURRENT_VERSION`), `schema_version` (alembic head, resolved
    once at module load), `profile` (`DORA_ENV`), and a `features`
    map (`auth`, `audit`, `barcodes`, `multi_user`, `email`,
    `assistant`). Mobile and desktop clients use this for
    compatibility + feature-gating decisions. The boot-time boolean
    health probe still works because any 2xx counts as healthy.
  - **Mobile CORS origins baked into dev defaults.** Development
    profile now includes `capacitor://localhost`, `ionic://localhost`,
    and `http://localhost` alongside the web SPA origins, so a
    Capacitor mobile build pointed at a local dev backend works
    without surgery. Documented in `.env.example`.
  - `HealthApiService` on the frontend exposes a typed `HealthInfo`
    + `getInfoAsync()` for clients that want the rich payload.
  - Distribution spec §0 snapshot refreshed to reflect what D1–D4
    actually shipped; original snapshot preserved in a collapsible
    block.

- **D4 — manual-release CI/CD.** Two workflows replacing the old
  single-stage `build-and-test.yml`:
  - [`.github/workflows/ci.yml`](.github/workflows/ci.yml) — runs
    automatically on every push and PR. Parallel jobs: frontend
    (lint + typecheck + build), dora_api (pytest against
    `tests/e2e/dora_api`), merchant_api + emailer (compileall smoke
    check). Concurrency guard cancels superseded runs. **Never
    publishes anything.**
  - [`.github/workflows/release.yml`](.github/workflows/release.yml)
    — `workflow_dispatch` only. Takes a `version` input
    (`vMAJOR.MINOR.PATCH` with optional pre-release suffix);
    validates it, refuses if the tag already exists, builds the
    monolithic Docker image, pushes to
    `ghcr.io/bentalese/discountdora` tagged both `vX.Y.Z` and
    `latest`, and cuts a GitHub Release with the `[Unreleased]`
    CHANGELOG block as the body. `dry_run` flag builds + tags
    without pushing or releasing.
  - README gains a **Releasing** section walking through the
    button-push flow.

- **D3 — production / development profile split.** New `DORA_ENV` env
  var (values: `development` / `production` / `test`, aliases
  accepted) selects a runtime profile that drives sensible defaults
  for every "is this dev or prod?" decision. Layering order is now
  env var → JSON appsettings → profile default.
  - New [`dora_api/infrastructure/profile.py`](dora_api/infrastructure/profile.py)
    is the single source of truth — exposes `current_profile()`,
    `is_production()`, and a boot-time gate
    `validate_production_requirements()` that **refuses to start in
    production** when `DORA_SECRET_KEY`, `DORA_CORS_ORIGINS`, or
    `ADMIN_BOOTSTRAP_EMAIL` is missing. Prints a friendly multi-line
    error listing what's missing, then exits non-zero so compose
    marks the container failed.
  - Per-profile defaults: log level (`DEBUG` in dev / `INFO` in
    prod), debug mode flag, CORS origins (open localhost list in dev
    / required-pinned list in prod), seed-allowed flag (always false
    in prod regardless of `DORA_ALLOW_DESTRUCTIVE`).
  - **CORS now configurable.** Both API startups read
    `DORA_CORS_ORIGINS` (comma-separated) via the new
    `get_cors_origins()` method instead of the hardcoded localhost
    list. Merchant API also honours `MAPI_CORS_ORIGINS` if set
    separately.
  - **Appsettings JSON relocated** to `<DATA_DIR>/config/{dapi,mapi}.appsettings.json`
    so the operator's persistent overrides ride the data volume.
    Migration helpers
    ([`dora_api/.../path_migration.py`](dora_api/infrastructure/path_migration.py),
    [`merchant_api/.../path_migration.py`](merchant_api/infrastructure/path_migration.py))
    move an existing legacy `./config/*.appsettings.json` once on
    first boot.
  - Compose defaults `DORA_ENV=production` so `docker compose up`
    behaves prod-strict; dev installs set `DORA_ENV=development`
    in their `.env`. `.env.example` documents the profile + every
    required var.

- **D2 — runtime state moved out of the source tree.** Every disk
  write now routes through the per-service config helpers
  (`get_data_dir()`, `get_cache_dir()`, `get_log_dir()`,
  `get_uploads_dir()`, `get_image_cache_dir()`) so paths honour the
  `DORA_*` / `MAPI_*` env vars and the named volumes in compose.
  - Replaced hardcoded paths: `dora_api/startup.py` log dir,
    `merchant_api/startup.py` log dir, `emailer/startup.py` log dir,
    `dora_api/features/data/uploads.py` upload dir,
    `merchant_api/.../product_image_provider.py` `.image_cache`,
    `merchant_api/.../aldi_provider.py` category-seed JSON.
  - **One-time migrations** on boot (idempotent, non-destructive):
    [`dora_api/infrastructure/path_migration.py`](dora_api/infrastructure/path_migration.py)
    moves a legacy `./data/dora.data.db` + `./data/uploads/*` into
    the new locations when the operator relocates the data dir;
    [`merchant_api/infrastructure/path_migration.py`](merchant_api/infrastructure/path_migration.py)
    relocates the repo-root `.image_cache/*` into
    `<CACHE_DIR>/images/` and seeds the bundled
    `aldi_products_by_category.json` into `<CACHE_DIR>/` so operators
    can curate it without forking.
  - `.gitignore` cleaned: retired `.image_cache`, ignored
    `data/`, `cache/`, `logs/` instead of the old ad-hoc patterns.
  - Latent bug fixed in `ProductImageProvider.__init__` — it was
    `open(_Filename, "rb")` (a relative name) instead of the full
    `_Filepath`, which would have errored on cold-cache load outside
    the right CWD.

- **D1 — Docker compose finalised (monolithic image, env-first
  config).** Single-container deployment, but the runtime is now
  proper:
  - `Dockerfile` installs nginx + curl; nginx serves the built SPA
    on :5174 instead of `quasar serve`. New
    [`nginx.conf`](nginx.conf) ships with gzip, cache headers,
    SPA-fallback for vue-router, and a `/healthz` probe. Commented-
    out `/api/` + `/mapi/` proxy blocks are the migration path to a
    single-port deployment later.
  - `Dockerfile` declares a `HEALTHCHECK` against `/healthz` so the
    container reports unhealthy when nginx is wedged (a stuck Python
    API leaves the SPA up while you debug).
  - `startup.sh` boots dora_api + merchant_api in the background,
    optionally boots the emailer when `DORA_EMAIL_ENABLED=true`, then
    runs nginx in the foreground so the container lifecycle matches
    nginx's.
  - `compose.yml` splits the named volumes into `dora_data`,
    `dora_cache`, `dora_logs`, `dora_config` (was `dora_cache` /
    `dora_data` / `dora_config`) and declares a healthcheck stanza.
    Documents `compose.override.yml` for host customisations.
  - Both Python config managers
    ([`dora_api/.../configuration_manager.py`](dora_api/infrastructure/configuration_manager.py),
    [`merchant_api/.../configuration_manager.py`](merchant_api/infrastructure/configuration_manager.py))
    now read env vars first and fall back to the JSON appsettings.
    New getters: `get_log_dir()`, `get_cache_dir()`.
  - `.env.example` overhauled — every variable grouped by purpose
    (storage paths, API tuning, email, bootstrap admin) with inline
    docs.

- **DS2 — icon set standardised on Material Design Icons (mdi-v7).**
  Quasar `iconSet` switched to `mdi-v7`; the previous `material-icons`
  font is kept loaded as a safety net for any straggler. New
  [`web_app/src/style/icons.ts`](web_app/src/style/icons.ts) is the
  single source of truth — every icon used by the app has a key in
  this map. Keys are the historic Material Icons names (so swept
  call sites read as `ICONS.add`, `ICONS.shopping_cart` etc.), with
  a block of semantic aliases at the bottom (`ICONS.cartAdd`,
  `ICONS.expiry`, `ICONS.essential`) that new code should prefer.
  Mechanical sweep: ~287 static template `icon="x"` attrs, ~50
  `<q-icon name="x">` static names, and every JS object literal
  `{ icon: 'x' }` across 70+ files now route through `ICONS.x`.
  `iconFor()` in [alert.ts](web_app/src/models/alert.ts) returns
  `ICONS.*` values too. Grep `icon="[a-z_]+"` in `web_app/src/`
  returns no hits.

- **Theme families — five palettes, each in Light + Dark**.
  Restructure of the named-theme catalogue: instead of seven loose
  themes, the picker now shows five *families*, each with a Light and
  a Dark variant accessible via paired buttons inside the card.
  - **Pesto** / **Pesto Dark** (forest teal + bright lime — Group 3)
  - **Lemon Tart** / **Lemon Tart Dark** (charcoal + golden + sunset
    orange — Group 4; absorbs the former Midnight Snack)
  - **Blueberry** / **Blueberry Dark** (cool muted teals + lavender —
    Group 1)
  - **Cherry Cola** / **Cherry Cola Dark** (deep merlot + olive
    sage — Group 2)
  - **Sourdough** / **Sourdough Dark** (toasty amber + brown crust)
  Legacy theme keys still accepted on the wire and migrated at apply
  time: `pesto-noir` → `pesto-dark`, `midnight-snack` →
  `lemon-tart-dark`, `dark` → `pesto-dark`, `light` / `avocado` →
  `pesto`. `theme: 'system'` resolves to Pesto / Pesto Dark by OS
  preference.
- **Theme picker UI** rebuilt around family cards. Each card shows a
  split swatch (light variant on the left, dark on the right), a
  blurb, and two Light / Dark buttons. The active variant is
  highlighted; the family card also gets a brand-coloured border when
  either of its variants is the active theme.
- **Toolbar contrast fix (Lemon Tart yellow-on-yellow).** The top
  header used `bg-primary text-white` which became invisible under
  Lemon Tart (primary IS yellow). New `--surface-toolbar` +
  `--text-on-toolbar` tokens; every theme controls them. Defaults to
  brand-secondary (a deep teal/navy/cocoa) with light text, so the
  active main-nav button and the "Discount Dora" wordmark stay
  legible in every theme.
- **Backend theme allowlist** updated for all 10 family variants;
  legacy values still accepted.

- **Design system rework — bolder themes, signature dashboard, login
  detached.** Followup pass over DS1 that addresses the regressions
  the first pass introduced.
  - **Login page** is now fully self-scoped — it does not read the
    app's `data-theme` tokens or honour Quasar's `Dark` flag, so the
    white-on-white input bug under OS dark mode is fixed. New vibrant
    animated mesh-gradient backdrop (magenta / amber / mint blobs
    drifting), a floating mascot bob, and a card slide-in entrance.
    `prefers-reduced-motion` disables every animation.
  - **`boot/theme.ts`** defaults to the brand theme pre-auth instead
    of honouring OS preference. OS dark mode no longer flips signed-out
    surfaces into the dark theme.
  - **Six themes** now ship, each owning the full surface ladder
    (page, components, sunken, elevated, borders, text), a signature
    three-stop *hero gradient*, and a six-hue chart palette. The
    dashboard reads `--hero-gradient` as its page background so each
    theme gets its own "special touch" on the landing page:
    - **Pesto** (default) — fresh garden green + teal + golden accent
      on a pale mint page. Your original brand palette.
    - **Lemon Tart** — warm yellow + cream, the previous Dora vibe.
    - **Blueberry** — cool cobalt + navy on a soft blue page.
    - **Cherry Cola** — bold cherry red + cocoa + caramel on warm
      cream.
    - **Sourdough** — toasty amber + brown crust on proofed cream.
    - **Midnight Snack** — warm-tinted dark mode (unchanged scope,
      refreshed surfaces).
    Avocado was retired; persisted preferences migrate to Pesto.
  - **Chart colours theme-aware.** Reports' ECharts series read the
    `--chart-1..6` tokens off the active theme instead of hardcoded
    swatches.
  - **Coverage pass.** Brand-coloured washes (`rgba(245,196,98,…)`,
    `rgba(23,176,115,…)`) on DataManagement, SettingsShell,
    PriceHistory, MyProducts now read `--brand-primary-soft`.
    AlertsBell high/medium washes read the
    semantic-soft tokens. Side menu active state uses
    `--text-on-accent`. DoraChat name + accent button reference
    `--text-primary` instead of hard `#000`.

### Added
- **Design tokens + named themes** (DS1, foundation pass). The app
  now has a real design-token system:
  - `css/tokens.scss` declares the full token catalogue — brand
    colours, neutrals, semantic (positive / warning / negative /
    info), surfaces, text, borders, spacing scale, radius scale,
    font-size scale, elevation shadows. Colours are HSL-declared in
    sRGB (no `oklch()` / wide-gamut) to neutralise the Chrome-vs-
    Firefox drift the taskboard flagged.
  - `css/themes.scss` overrides the **semantic** tokens per theme
    via `[data-theme="<name>"]` blocks. Five named themes:
    **Lemon Tart** (warm yellow on cream — Dora's default),
    **Sourdough** (warm cream + golden crust), **Blueberry** (cool
    fresh blue), **Avocado** (deep ripe green + golden accent), and
    **Midnight Snack** (dark, warm-tinted). Switching themes is a
    single attribute flip on `<html>`.
  - `css/quasar.variables.scss` is wired with the Lemon Tart
    palette as the build-time default; `themeService.ts`
    re-applies the active theme's palette via `setCssVar()` at
    runtime so Quasar's component palette stays in step.
  - `services/themeService.ts` exports the named-theme catalogue
    (label + blurb + 3-colour swatch strip per theme) used by the
    Preferences picker. Legacy `light` / `dark` values still in the
    DB map to Lemon Tart / Midnight Snack on the way in.
  - **Settings → Preferences** gets a new card-grid theme picker:
    each card shows the theme name, a one-line blurb, and a 3-strip
    swatch preview. The active card is ringed in the brand primary.
  - Backend `User.theme` now accepts the five named-theme values
    alongside `system` / `light` / `dark` (legacy).
  - **Per-component sweep** done: 103 hex/rgba replacements across
    31 .vue / .scss files map every surface, text, border, overlay,
    scrim and ring to a token. Brand-identity values (merchant
    logos, data-viz palettes in Dashboard / Reports, the explicit
    colour-per-series palette in Price History) intentionally stay
    literal — they aren't theme surfaces. `colours.scss` shim points
    `--q-*` fallbacks at the
    matching DS1 token (was hard-coded `#000000` placeholders).
  - Two extra overlay tokens added on the way in:
    `--overlay-scrim` / `--overlay-dim` / `--overlay-hover` /
    `--overlay-active` / `--ring-focus`. Midnight Snack flips the
    hover/active overlays from black-on-light to white-on-dark so
    the press-state contrast still reads.
- **Price History Explorer** (N8). New `/price-history` route lets the
  user compare up to **5** products' price curves side-by-side. Backend
  endpoints:
  - `GET /api/price-history?product_ids=<csv>&range=30d|90d|1y|all` —
    pulls historic points from `ProductHistoricOffer`, returns
    `series[]` with `points` (date, unit + list prices, `on_deal`),
    `current` (live `ProductOffer` row + computed deal %),
    `all_time_low` (across the full history regardless of range), and
    a `(unknown)` placeholder for any requested id that doesn't exist
    (so the SPA can render "no data" rather than silently dropping it).
  - `POST /api/price-history/alerts` — per-user subscription
    (`{product_id, threshold_unit_price}`), validated against the
    `Product` row.
  - `GET /api/price-history/alerts` + `DELETE /api/price-history/alerts/<id>`
    — both user-scoped so one account can't see or remove another's.
  - New `PriceAlert` table + migration `d3b6e1f9a720` (indexed on
    `(user_id, product_id)` and `(product_id)`).
  Frontend: a left-rail picker with autocomplete + selected-chip
  display, a hand-rolled multi-series SVG line chart
  (`components/PriceHistoryChart.vue` — 5-colour palette matching the
  chip colours, gridlines + $-formatted y-axis ticks, deal markers as
  dots on the line, hover crosshair with a tooltip listing every
  selected product's nearest-point price), 30d / 90d / 1y / all range
  toggle, per-product comparison cards (current price + deal % chip,
  all-time low + "currently X% above" indicator, "Notify me below $___"
  input wired to the alerts endpoint), and a "Manage alerts" modal.
  Deep-link via `?product_id=<id>` pre-selects that product. Command
  palette gains a **Go to Price History** entry.
- **Undirected substitute pairs.** Migration `c8a1d3b6e9f4` rebuilds
  `StockItemSubstitute` as an undirected pair table — columns
  `stock_item_a_id`, `stock_item_b_id`, `notes`, `created_at`, with
  a CHECK enforcing canonical (a < b) ordering so each unordered
  pair has exactly one row. Pre-release destructive migration; dev
  DB re-seeds with canonical pairs. Existing per-stock-item add /
  remove endpoints canonicalise transparently; the stock detail
  page reads pairs in both directions and the backup/restore
  pipeline tracks the new column names.

- **Reports / Analytics page** (N6). New `/reports` route with six
  cards backed by `/api/reports/*` endpoints — stock value over time,
  spend by merchant, top 10 most-bought, items that keep running out,
  savings captured, and multi-product price trends. Range selector
  (30d / 90d / 1y / all). Charts rendered with ECharts via
  `vue-echarts`. Every item chip deep-links to the matching stock
  detail page; "Mark all essential" on the keeps-running-out card
  flags items in one click.
  - **Price snapshot on shopping list lines**. Migration
    `c6e9f4a82d15` adds `picked_offer_price` + `list_price_at_pick` to
    `ShoppingListLine`. Captured when a line is first ticked (cleared
    on untick); finishing a list backfills any ticked-without-snapshot
    rows so reports stay honest after future price moves.

- **Auto-generated shopping lists** (X5). The "build me a list" path is
  now one endpoint with seven sources you can mix-and-match.
  - `POST /api/shopping-lists/auto-generate` replaces the older single-
    source `/autogenerate`. Body shape:
    `{ name?, merge_into_list_id?, sources: { low_stock?, out_of_stock?,
      essentials_only_for_low?, flagged?, frequently_added?,
      frequently_added_limit?, meal_plan_week?, recipes?[] } }`.
    Items collected by more than one source are deduped, keeping the
    highest-priority provenance — order is
    `auto_recipe > auto_meal_plan > auto_flagged > auto_essential >
     auto_low_stock > auto_frequently_added`. Recipe and meal-plan
    sources subtract anything already at "Well-Stocked".
  - `POST /api/shopping-lists/<id>/append-low-stock-essentials` —
    one-click convenience wrapper that tops up an existing list with
    essentials that are low or out.
  - **Per-line provenance**. New `ShoppingListLine.added_via` (enum:
    `manual` / `auto_low_stock` / `auto_essential` / `auto_flagged` /
    `auto_recipe` / `auto_meal_plan` / `auto_frequently_added`) and
    `added_at` (timestamp) columns — migration `b5d8e2f3c14a`. Drives a
    chip on every non-manual line in **Shopping List detail** so the
    user can see *why* something landed on the list. Manual edits to
    quantity or merchant selection flip the line back to `manual`
    automatically.
  - **Silent auto-add on low**. The existing `StockItem.auto_add_when_low`
    trigger (which fires when a level drops to Low or Out) now lands
    the line with `added_via=auto_low_stock` and skips the silent add
    if the item is already on **any** non-archived list (not just the
    primary). `PATCH /api/stock-items/<id>` returns
    `{ auto_added: { line_id, shopping_list_id } }` when it fires, so
    the frontend can surface an undoable "Tomato Soup auto-added to
    <list>" toast.
  - **Stock item detail** gains the "Always include in auto-generated
    lists" toggle (`is_flagged`) alongside the existing "Auto-add when
    low or out" (`auto_add_when_low`); both have explanatory tooltips
    spelling out the difference.
  - **Stock Overview** filter chips: "Flagged for auto" and the new
    "Will auto-add on low".
  - **Shopping Lists overview** "New list" dropdown gains **Advanced
    auto-generate…** — a modal with checkboxes for every source plus a
    merge-into picker.
  - **Recipes overview** "Add missing to list" routes through
    `/auto-generate` with `sources.recipes=[id]`, so the lines land
    tagged `auto_recipe` with the recipe name as the chip detail.
  - **Meal Plans overview** "Generate shopping list for this week" now
    routes through `/auto-generate` with `sources.meal_plan_week=<start>`
    — well-stocked ingredients are subtracted server-side and every
    line is tagged `auto_meal_plan`.
- **Stocktake / focused review** (X1). New `StockItem.last_checked_at`
  column (migration `a4c7e1d9b832`, indexed) — distinct from
  `stock_level_last_updated` so a user confirming "yes, the level is
  still correct" stamps a check without rewriting the level history.
  Updating the level still bumps both timestamps.
  - `GET /api/stocktake/queue?limit=` — items past their per-item
    `days_until_stocktake_alert` window, ordered most-overdue-first;
    never-checked items surface ahead of everyone else (with an
    `overdue_days = -1` sentinel for the UI).
  - `POST /api/stock-items/<id>/check` — idempotent, only touches
    `last_checked_at`.
  - `POST /api/stocktake/bulk-check` — bulk variant.
  - `POST /api/shopping-lists/<id>/review/complete` — for the
    shopping-list review-mode flow; bulk-sets ticked items to
    Well-Stocked and stamps `last_checked_at`.
  - New `/stocktake` overview page (top-of-queue preview + "Start
    review" CTA) and `/stocktake/run` fullscreen focus mode: one item
    at a time, big "Still correct (1) / Change level (2) / Out of
    stock (3) / Skip (s)" buttons with keyboard shortcuts, "Add to
    list" secondary action, session-complete summary card.
  - **Stock Overview** toolbar gains a **Stocktake (N)** button that
    pulses with a brand-coloured glow when the overdue count is
    positive.
  - **Shopping List detail** menu gains **Finish review** —
    bulk-marks every ticked item as Well-Stocked + stamps the check
    (the spiritual sibling of the existing finish-shopping flow).
- **PWA mode** (M1). Discount Dora is now installable on every
  major surface. Quasar's `pwa` config block is fully wired:
  - **Manifest** — `name`, `short_name=Dora`, `description`,
    `theme_color` + `background_color` matching the brand swatches,
    `display: standalone`, `orientation: portrait-primary` (kitchen-
    phone use), icon set spanning 192/512 px (with the 512 doubling
    as the maskable), and three launcher shortcuts: **Primary list**
    (`/shopping-lists?open=primary`), **Scan**
    (`/data/barcodes?action=scan`), and **Add item**
    (`/stock?new=1`).
  - **Service worker** — Workbox `GenerateSW` with
    `skipWaiting + clientsClaim + cleanupOutdatedCaches`. Runtime
    caching: `/api/*` → NetworkFirst with a 5 s timeout (keeps the
    UI snappy when the backend lags), stock-item images → CacheFirst
    (30 days × 200 entries), merchant product images → CacheFirst
    (7 days × 500 entries). Navigation failures fall through to
    `index.html`; `/api/*` is on the navigate-fallback denylist so a
    backend outage doesn't silently swap a JSON response for HTML.
  - **Offline page** — `public/offline.html` (branded, mentions the
    F3 offline queue so the user knows their ticks aren't lost).
  - **Install prompt** — new `composables/usePwaLifecycle.ts` defers
    `beforeinstallprompt`; a `<PwaInstallPrompt />` component
    surfaces an "Install Dora" button in Settings → About. iOS
    Safari (which doesn't fire the event) gets a tailored
    "Share → Add to Home Screen" hint.
  - **Update flow** — `controllerchange` on `navigator.serviceWorker`
    pops a "New version available · Reload / Later" Notify (zero
    timeout — the user opts in to the reload).
  - **Per-mode dev ports** — SPA stays on 5174; PWA dev runs on
    5175, SSR on 5176, so all three can be served side-by-side
    during development.
- **Self-serve auth surface** (A1). The full out-of-band flow lands:
  - `POST /api/auth/register` enforces password rules (≥10 chars + a
    letter + a digit), email-format validation, and case-insensitive
    email uniqueness. First user still auto-becomes admin AND
    auto-verifies (so a fresh install without SMTP isn't locked out).
    Every other registration emails a verification link with a 24 h
    SHA-256-hashed token.
  - `POST /api/auth/verify-email`, `POST /api/auth/resend-verification`
    (anti-enumeration + 1/min/IP-email).
  - `POST /api/auth/forgot-password` (anti-enumeration, 5/min/IP-email)
    issues a single-use 1 h reset token; `POST /api/auth/reset-password`
    consumes it, applies the new password, bumps `password_changed_at`,
    revokes any still-live reset tokens, and emails a notification.
  - `POST /api/auth/me/password` extended with the same password rules
    + notification email; bumping `password_changed_at` invalidates
    every other-device session on its next `/me` probe via a new
    session-staleness check.
  - `POST /api/auth/me/email` (request) + `POST /api/auth/email-change/confirm`
    confirm a new address before it swaps (anti-account-takeover).
  - Login is rate-limited (5/min/IP) with proper `Retry-After`.
  - Every auth event audits via I2's `audit.emit`
    (`auth.user.registered`, `auth.email.verified`,
    `auth.password.reset_requested`, `auth.password.reset`,
    `auth.password.changed`, `auth.email.changed`,
    `auth.login.success`, `auth.login.failed`).
- **Deployment-aware email links.** A new `DORA_PUBLIC_URL` env var is
  the canonical home for the SPA across PWA, mobile-shell, and
  self-hosted-desktop deploys — verify / reset links are built off it
  (falls back to the request's `Origin` header, then
  `http://localhost:5174` for dev).
- **Transactional email helper.** New `dora_api/infrastructure/email_sender.py`
  drives SMTP from `DORA_SMTP_*` env vars with a Jinja-template loader at
  `dora_api/email_templates/` (`verify_email.html`, `reset_password.html`,
  `password_changed.html`, shared `_layout.html`). **Dry-run** mode
  kicks in when `DORA_SMTP_USERNAME` is unset — the email body lands
  in the regular log stream instead of being sent, so self-hosted
  desktop installs without SMTP can still copy-paste verification
  links.
- **Frontend auth pages.** `/verify-email`, `/forgot-password`,
  `/reset-password`, `/confirm-email-change` all land outside the
  main layout (no nav chrome for someone clicking a link in a fresh
  browser). LoginPage gains a **Forgot password?** link, a
  password-rule hint in register mode, and a "Email verified" toast
  on arrival from `?verified=1`. Frontend `AuthApiService` exposes
  every new endpoint with typed wrappers.
- **Audit log + admin viewer** (I2 round B). A new `AuditEvent` table
  (migration `e9a2c4b1f7d8`) captures every mutating API request,
  every login success/failure, every client-side `warn`/`error` shipped
  via `/api/client-logs`, and any explicit `audit.emit(...)` from
  service code. Rows carry `occurred_at`, `source` (`dapi` / `mapi` /
  `emailer` / `web` / `system`), `actor_user_id`, `actor_ip`, `action`
  (verb-noun, e.g. `stock_item.created`, `auth.login.failed`),
  `entity_type` + `entity_id`, `request_id` (matches the existing
  X-Request-Id correlation), JSON `payload`, and `severity`. Indexed
  on `occurred_at` plus per-actor / per-entity / per-action compound
  indexes for the admin filters. An `audit.scrub(payload)` pass strips
  any key matching the privacy deny-list (`password`, `token`,
  `api_key`, …) before persistence. Nightly `BackgroundScheduler` job
  prunes events older than `DORA_AUDIT_RETENTION_DAYS` (default 365).
  Admin-only `GET /api/audit/events` (filter by source / severity /
  actor / action / entity / request id / time range, paginated up to
  500 per page) plus `GET /api/audit/events/<id>`. New
  **Settings → Admin → Audit log** page with a filter strip, paginated
  table with severity chips, click-to-open detail dialog (pretty-printed
  payload, "Find related" button that pivots the filter to the same
  `request_id`), and **Export CSV** of the current page.
- **Structured logging across every service** (I1 round A). All three
  services (dora_api, merchant_api, emailer) now route through a single
  `configure_logging(service_name, log_dir, debug=...)` helper that
  wires a stdout `StreamHandler` (for `docker logs`-style aggregation)
  plus a `RotatingFileHandler` (10 MB × 5 backups, e.g.
  `data/logs/dapi/dapi.log`). The shared formatter is
  `%(asctime)s %(levelname)s [%(name)s] [req=…] [user=…] %(message)s`,
  with `request_id` and `user_id` injected from `contextvars` by a
  `LogContextFilter` so every line in a request emits with the same
  IDs without any caller plumbing. The dora_api middleware now
  generates a `request_id` (or honours an incoming `X-Request-Id`),
  binds the session user, logs `→ GET /api/...` at start +
  `← 200 GET /api/... (12.3ms)` at end, and echoes `X-Request-Id` on
  every response so the SPA's axios correlation id round-trips. The
  per-service old `configure_logger` helpers are gone; `sqlalchemy.engine`
  is pinned to WARNING regardless of root so SQL echo doesn't drown
  the stream, and Werkzeug's per-request INFO line is silenced (the
  middleware already emits a richer equivalent).
- **Client-side logger + `/api/client-logs`.** A new
  `useClientLogger` composable mirrors the standard levels and ships
  `warn` / `error` to the new `POST /api/client-logs` endpoint
  (rate-limited at 10 events / 60 s per session, server-side and
  client-side). The existing `boot/globalErrorHandler.ts` is hooked
  up to it, so Vue render errors, `window.onerror`, and unhandled
  promise rejections all land in the server's log stream now —
  including pre-login crashes (the endpoint is in `PUBLIC_ENDPOINTS`).
  Payload includes URL, user-agent, stack excerpt; capped at 2 KB.
  Audit-table persistence lands in the next round.
- **Export & Print: stock overview + meal plans.** Two new sections in
  Data → Export & print:
  - **Stock overview** — install-wide CSV (`location, name, level,
    expiry, is_flagged, is_open, auto_add_when_low, barcode, notes`,
    grouped by location) and a stocktake-friendly print view with
    checkbox column per item.
  - **Meal plans** — per-plan CSV (`scheduled_for, slot, meal, servings`)
    and a weekly-calendar print view with days as rows and slots
    (Breakfast / Lunch / Dinner / Snack + any custom ones) as columns.
  Both surface as `GET …/export?format=csv` and `…/print-view` to match
  the existing N4 endpoints. New "Export" dropdown on the Stock Overview
  toolbar (CSV / Print) and new CSV / Print buttons in the Meal Plans
  toolbar. The bulk-action banner on Stock Overview also gains a
  **Print QRs** action that opens the QR sheet for the current
  selection.
- **Scan polish.** The ScanOverlay shows a fading "Decoded: <value>"
  banner on a successful read, and a new `close-on-decode` prop closes
  the overlay automatically after the first valid scan (used by the
  Stock Overview Scan and the StockItemDetail "Register barcode" flows,
  where the user only ever wants one scan). The Data → Barcodes & QR
  Scan tab keeps the default continuous-scan behaviour.
- **Camera setup notes.** `web_app/README.md` calls out the HTTPS
  requirement for `getUserMedia` outside `localhost` so phone / LAN
  testing doesn't silently fail.
- **Backup uploader refactor.** Data → Backup & restore now uses the
  shared `useChunkedUpload` composable that powers DataImport, so the
  start/chunk/finish/abort plumbing has a single home. Behaviour is
  unchanged.
- **Barcodes & QR.** Data → Barcodes & QR is now live with three tabs:
  - **Scan** — fullscreen `@zxing/browser` camera overlay with a
    crosshair box, dim mask, debounced repeat-decodes (2 s window),
    torch toggle on supporting cameras, and a manual-entry escape
    hatch. On decode, hits `GET /api/data/barcodes/lookup?value=...`
    which resolves either a `dora://stock-item/<uuid>` link, a raw
    `StockItem.barcode` match, or a `ProductBarcode` (returning the
    linked stock item if any). Unknown values prompt
    "Register against a stock item" with a typeahead.
  - **Print sheets** — pick stock items (filter box, virtualised
    list), choose a layout (A4 21-up or Avery 5160), open a printable
    HTML grid in a new tab. PDF via the browser's Save-as-PDF, same as
    N4. A "Print all stock items" shortcut covers the stocktake case.
  - **Manage** — inline edit / clear / "Print one" QR per item.
  Stock-item detail page gets two new toolbar buttons: **Show QR**
  (modal with a big QR + Print One) and **Register barcode** (opens
  the scan overlay focused on the current item). Stock overview gets
  a **Scan** button that jumps straight to the matched item's detail
  page on a successful decode.
  Backend additions: a new `barcode` column on `StockItem` (globally
  unique per install), a new `ProductBarcode` table for many-to-one
  product↔barcode links, plus four endpoints:
  - `GET /api/stock-items/<id>/qr?size=...` — PNG, 64-1024 px range.
  - `GET /api/stock-items/qr/sheet?ids=&layout=` — printable HTML
    label sheet; missing `ids` falls back to all stock items.
  - `POST /api/stock-items/<id>/barcode` — 409 on collision.
  - `DELETE /api/stock-items/<id>/barcode` — clear.
  - `POST /api/data/barcodes/register-against-product` — wire an
    unknown scanned code to a saved product.
  QR encoding is `dora://stock-item/<uuid>` so a printed QR scanned
  back through the overlay round-trips to the item. ProductBarcode
  rows ride along in backups by default (new section in
  `restore_shared.SECTIONS`). Migration `d7f4a2c98e15`.
- **Export & Print.** Data → Export & print now lists every shopping list
  (filterable Active / Archived / All, primary pinned to the top) and
  every recipe (with name-filter), each row carrying **CSV** and
  **Print** buttons. New backend endpoints:
  - `GET /api/shopping-lists/<id>/export?format=csv` — columns
    `location, item, quantity, merchant, unit_price, total, picked_up,
    notes`, grouped by location and alphabetised within each group.
  - `GET /api/shopping-lists/<id>/print-view` — server-rendered HTML
    with a printer-friendly stylesheet (`@media print` strips the
    floating toolbar; big tap-friendly checkboxes; sections per
    location; totals strip showing remaining / picked-up / estimated
    total).
  - `GET /api/recipes/<id>/export?format=csv` — ingredient list
    (`ingredient, quantity, unit, notes, location`).
  - `GET /api/recipes/<id>/print-view` — recipe card with ingredient
    list + instructions + nutrition, sized for a fridge magnet pin.
  PDF generation is **browser-side** (Save as PDF from the print
  dialog) — no new server dependencies. Download filenames are
  slugified to e.g. `shopping-list-weekly-shop-2026-05-21.csv`. A new
  shared `useShoppingListExport` composable powers both ExportPrint and
  a new "Export as CSV" / "Print / Save as PDF" pair on the
  ShoppingListDetail overflow menu; a sibling `useRecipeExport` does
  the same for recipes.
- **Spreadsheet import.** Data → Import now accepts `.xlsx` and `.csv`
  files and turns them into stock items. The file is staged via the
  existing chunked-upload stack, then `POST /api/data/import/spreadsheet/inspect`
  reads its sheets, shows a five-row preview, and auto-picks the most
  likely column for each Dora field (Name [required], Stock level,
  Location, Group, Expiry, Is essential). The mapping is editable per
  sheet; the preview re-renders live as the user reassigns columns.
  `POST /api/data/import/spreadsheet/commit` walks every row in a
  single transaction with row-level error reporting — bad stock-level
  text becomes "Stock level 'foo' isn't recognised. Valid options:
  Well-Stocked, Sufficient Stock, Low Stock, Out of Stock", missing
  Location / Group can be auto-created via toggles, and
  **Halt on first error** rolls the whole import back. After commit the
  result dialog lists each row with a coloured chip (`ok` / `dup` / `err`)
  and a one-click **Download error rows (CSV)** so the user can fix
  problem rows offline and re-import only those. `is_essential` maps
  to `StockItem.is_flagged` (the closest existing flag in the schema).
- **Data Management shell** (backup/restore, import, export & print, barcodes —
  sections to follow). New top-level **Data** entry in the nav and command
  palette opens `/data`, with a left rail listing the four sub-sections and a
  breadcrumb crumbed `Data › <section>`. The sub-pages are placeholders for
  now; subsequent rounds wire up the actual backup, import, export and
  barcode tooling.
- **Backup export.** Data → Backup & restore now offers a one-click
  **Download backup** that streams a single JSON snapshot
  (`dora-backup-<date>.json`) of every in-scope entity — stock groups,
  levels, locations and items (including substitutes and product links),
  saved products, shopping lists and templates, recipe collections,
  recipes and ingredients, meals and meal plans. Images round-trip via
  base64. Cached merchant data (merchants, offer history, change log,
  notifications, app settings) and user credentials are intentionally
  excluded. Backed by a new `GET /api/data/backup` endpoint that records
  `exported_by` for provenance.
- **Chunked-resumable backup uploads.** New endpoints
  `POST /api/data/uploads/{start,chunk,finish}` and
  `DELETE /api/data/uploads/<id>` stage backup files under
  `data/uploads/` 8 MB at a time; a failed chunk retries up to three
  times without restarting the whole upload. Total cap is now **2 GB**.
  The SPA no longer parses backup files client-side at all — picking a
  file streams it via chunks, shows an upload progress bar, then calls
  `inspect` with the `upload_id`. `restore` likewise accepts
  `upload_id` (still backwards-compatible with inline `backup` bodies).
  Stale uploads older than an hour are swept on every new `start`, and
  cancelling the file picker issues `DELETE` proactively.
- **Stream-parsed inspect.** The backup preview now uses `ijson` to
  walk the staged file without ever instantiating the full document in
  server memory. Counts, duplicate-flagged names, and per-section
  sample rows (capped at 500 per section with an overflow indicator)
  are streamed out — multi-GB backups can be inspected on modest
  hardware. The tree view in the SPA renders straight from the
  inspect response.
- **Last-backup timestamp + restore report + bigger uploads.** The
  Create-backup card now shows "Last backup: N min/hr/days ago" using a
  new `User.last_backup_at` column (migration `c5e8f3a91b07`) that the
  backup endpoint stamps on every successful download. `/api/auth/me`
  carries the value so the card updates without a separate round-trip.
  After a restore lands, the page now opens a results dialog with a
  per-section "+N created · M skipped" breakdown plus an expandable
  warnings list, and a **Reload now** button to swap to a fresh app
  state on the user's own pace (no more silent auto-reload). Upload cap
  raised from 50 MB to **500 MB** on both client and server; the inspect
  endpoint streams multipart uploads to a temp file 8 MB at a time
  instead of holding them in memory. (True chunked-resumable uploads
  are still future work — flaky network mid-upload still requires a
  restart.)
- **Backup section toggles + more sections.** The Create-backup card now
  shows per-section checkboxes grouped into "Core data" (on by default —
  stock, lists, recipes, meals, etc.) and "Optional" (off by default).
  Three new optional sections are wired up: **System settings** (the
  install-wide AppSetting row), **User accounts** (every user row minus
  `password_hash` — restoring leaves the hash null so an admin reset is
  required for those accounts to log in), and **Historic product offers**.
  Each group has _All / None_ shortcuts and an "X of Y selected" caption.
  Under the hood the section catalogue is declared once in
  `restore_shared.SECTIONS` — adding a new section is a single entry there
  plus its FK classification, and both the export filter and the restore
  iterator pick it up automatically. `GET /api/data/backup` now accepts
  `?sections=a,b,c` to narrow the dump (unknown keys → 400) and records
  the included list in the payload's `sections` field.
- **Backup inspect + restore.** Picking a backup file in
  Data → Backup & restore now uploads it to a new `POST /api/data/backup/inspect`
  endpoint and renders a preview tree: counts per section, one branch per
  entity type, leaves checkbox-tickable. Rows whose natural key (name for
  most entities, name+parent for locations, merchant+stockcode for
  products) already exists locally are flagged with a `duplicate` chip and
  greyed out. A header counter reports "X of Y items selected, Z
  duplicates skipped" alongside select-all / clear-selection actions. Two
  commit buttons hit `POST /api/data/backup/restore`: **Restore selection**
  (partial mode) and **Restore all (skip duplicates)**. A confirm dialog
  precedes either. The restore is single-transaction; on failure the
  whole thing rolls back. Hard-FK targets (stock locations including
  parents, stock groups, recipe collections, stock levels) are pulled in
  transparently when partial mode would have orphaned them; soft FKs
  (preferred / selected product) null out with a warning if the target
  isn't being imported; required FKs that can't resolve skip the row
  with a warning. On success the page reloads so every store reflects
  the new data.

### Changed
- **Command palette anywhere with Cmd/Ctrl-K.** A top-of-screen palette opens
  from any page (even when an input is focused) and searches across stock
  items, shopping lists, recipes, locations, products, meals and meal plans —
  plus runs in-app commands like _Create stock item_, _Open primary shopping
  list_, _Auto-generate shopping list from low stock_, _Toggle dark mode_,
  _Show keyboard shortcuts_, and every _Go to …_ navigation. Substring and
  fuzzy matches are highlighted in the result title. Empty query shows your
  recents (last 20 entities you visited, kept per-device) and your most-used
  commands. Arrow keys move the selection, **Enter** runs it, the first
  **Esc** clears the query and the second closes. Pages can register their
  own contextual commands via `useCommands()`, auto-deregistered on unmount.
  The locations "find item" overlay now rides the same unified `/api/search`
  endpoint.
- **Keyboard shortcuts everywhere.** Press **?** anywhere to open a cheatsheet
  of every shortcut live on the current screen, grouped by area. Global keys:
  **/** focuses the Stock search (or jumps there), and **g** then **s / l / r /
  d / h** navigates to Stock, Lists, Recipes, Dashboard or Help. On the Stock
  screen, **n** adds an item, **f** focuses the filter, arrow keys move a
  highlight through the grid, **Enter** opens the focused item, and **a** adds
  the focused (or selected) items to your primary list. On a shopping list,
  arrow keys move between lines, **Space** ticks the focused line and **n** adds
  an item. Shortcuts ignore your typing in text fields, and **Esc** closes the
  cheatsheet. (Ctrl/Cmd-Z undo/redo from the undo system still works alongside.)
- **One-click Undo across the app.** A new Undo button in the header
  (tooltip shows the most-recent action label) reverses the last 20
  actions; Ctrl/Cmd-Z does the same from anywhere outside a text input,
  Ctrl/Cmd-Shift-Z (or Ctrl-Y) redoes. Destructive actions also pop a
  toast with an inline Undo for 10 seconds. Wired actions: bumping a
  stock item's level, ticking or unticking a shopping list line, moving
  / editing a stock item, **deleting a stock item** (round-trips through
  a new `/api/stock-items/restore` so the item comes back with the same
  id and references), removing a line from a shopping list, and the big
  one — **Finish shopping**: un-archives the list, rolls back the bulk
  stock-level bumps from the original ticks, and demotes whichever list
  was auto-promoted to primary, all in one click. Undoing an action that
  was processed via the offline queue works once sync completes.
- **Dora keeps working when the network doesn't.** A slim banner pins
  under the header whenever you're offline or we can't reach the server
  — with a Retry button and a live "N changes queued" counter. While
  offline, the four most common mid-shop actions (ticking shopping-list
  lines, bumping a stock item's level, marking it opened or restocked,
  pushing or clearing an expiry date) are queued in the browser and
  drained automatically when we reconnect — your optimistic ticks stay
  put in the meantime. Creates and deletes still fail loudly because
  silently inventing-or-vanishing entities is rarely what you want.
- **Errors no longer take down the whole screen.** A new error boundary
  wraps every page; if something on the page throws while rendering,
  the rest of the app (header, drawer, Dora bubble, alerts bell) stays
  alive and the page itself shows a friendly recovery card with Reload,
  Go to dashboard, and Report this (pre-fills a GitHub issue with the
  error message and a reference id). New `/errors/server` and
  `/errors/not-found` routes pick up failed lazy-chunk loads and
  in-app "not found" links respectively. Server (5xx) responses now
  surface a normalised "the server tripped" toast instead of silently
  collapsing.
- **HTTP client is harder to surprise.** Every request now carries a
  unique X-Request-Id so any error you see references back to the exact
  server log line. GETs auto-retry up to 3 times with exponential
  backoff on network errors and 502/503/504; mutations never auto-retry
  (the offline queue is the right tool for that). Every error reaching
  callers is normalised into the same shape — status, code, message,
  details, correlation id — instead of leaking raw axios objects.
- **Dora is now context-aware.** Open the chat on any screen and a fresh
  "On this page" chip row sits above the generic quick-actions, suggesting
  the 2-3 most useful next moves for that screen. On a stock item it's
  **Find cheaper alternatives** (jumps to Product Search pre-filtered),
  **Add to my list** (uses the same composable as the cart button), and
  **Find substitutes** (opens the substitutes section on the detail
  page). On a recipe: **What's missing?** (lists out-of-stock or
  untracked ingredients in chat), **Plan this for a day** (jumps to Meal
  Plans with the recipe pre-targeted), and **Add missing to a list**
  (bulk-adds the missing ingredients straight to your primary list).
  Stock overview, recipes overview, shopping list detail, my products,
  locations and the dashboard get their own contextual chips too. Every
  action routes through the same cross-feature composables (P0) the rest
  of the app uses, so behaviour stays identical wherever you trigger it.
- **Alerts panel rounded out.** Alerts are now grouped under **High
  priority / Medium / Low / FYI** headers so the eye doesn't have to
  scan for severity. Every row picks up two new actions alongside the
  existing extend-expiry / mark-restocked / acknowledge: **View in
  context** jumps you to the Stock screen pre-filtered to attention
  items, and **Snooze 7d** hides the alert on this device for a week
  (with a one-click Undo in the toast). Snoozed alerts get their own
  collapsed section at the bottom of the panel with per-row Unsnooze.
  A new bottom action — **Add N low/out items to primary list** —
  bulk-queues every low- and out-of-stock item from the panel onto your
  primary shopping list in one click (skipping anything already on it).
- **Dashboard is now the morning glance.** Four new cards sit above the
  pantry/totals strip and surface what to actually do, not just what
  exists:
  - **Needs your attention** lists the top alerts (expired, expiring soon,
    low/out, essentials low) with the same inline actions as the alerts
    panel — push expiry, mark restocked, acknowledge — and each item name
    deep-links to its stock detail page.
  - **Primary shopping list** shows the live "to grab" count, dollar
    remaining, and savings-vs-RRP total for whatever list is primary, with
    a one-tap jump-to-list. When no primary is set the card prompts you
    to pick one.
  - **Cookable tonight** lists up to three recipes that have every
    ingredient in stock right now (favourites and recently-cooked-less
    bubble up first), each with prep+cook time, servings, a deep link to
    the recipe and a "Cook" button straight into cook mode.
  - **Best deals on your saved products** ranks your saved products by %
    off, showing the merchant, the linked stock item chip, the price now
    vs the strike-through RRP, and the discount badge.
  Every chip, number, and "See more" link deep-links into the relevant
  screen (Stock, Recipes with `?cookable=true`, My Products, etc.). Cards
  can be toggled in the existing **Cards** menu.
- **Product search is now a deal-comparison surface.** Results render as cards
  with a discount badge that deepens from amber to red as the saving grows, the
  unit price (per 100g/ml or each), the merchant logo, and — for products you've
  saved — a price-trend sparkline. Each card can save to favourites, link to an
  existing stock item, or "quick-add" (saves the product, starts tracking it as
  a stock item, links them, and drops it on your primary list in one tap). Pick
  2–3 results and open a side-by-side comparison. New filters: price range,
  unit-price ceiling, size/weight range, and a half-price-or-better toggle;
  sort by relevancy, name, price, unit price or biggest saving. Merchant
  connection status badges sit up top so you can see at a glance which scrapers
  are healthy.
- **Meal plans are now a drag-and-drop week.** Drag any meal from the palette
  onto a day to plan it (cookable-now meals are flagged green), and click a
  planned entry to jump to its recipe or straight into cook mode. A sidebar
  rolls up the whole week's ingredient demand against current stock and shows
  exactly how many items you'll need to buy, with one click to generate a
  shopping list for the week. A "Suggest meals I can cook now" button surfaces
  everything fully in stock right now. (Also fixed the week's ingredient
  rollup, which was silently returning nothing.)
- **Cook mode now closes the loop on what you used.** The ingredients pane
  shows the shared stock-item chips and marks each one "used" as you tick a
  step (or advance through it) — names mentioned in a step are matched
  automatically, and you can toggle any ingredient by hand. Finishing prompts
  to update stock levels (used items step down one level), log it as a meal
  eaten, and add anything that's now low or out straight onto your primary
  shopping list. Per-step timers and voice control are unchanged.
- **Recipes overview is now a cooking command center.** Recipes are grouped
  by collection (with an "Uncategorised" bucket), every card surfaces a live
  **Cookable now** badge — or a one-click **Missing N** chip that opens an
  "add ingredients to a shopping list" dialog — and the action menu on each
  card covers cook, edit, duplicate, mark made, add all ingredients to a
  list, add to a meal plan and delete. New filters: cookable now, missing
  ≤ N ingredients, collection (incl. uncategorised), tags pulled from
  cuisine + category, and "uses stock item" (which deep-links here from the
  stock item detail page via `?usesStockItem=…`). A new **Compare** mode
  lets you pick 2–3 recipes and pop them open side-by-side — ingredients,
  times, difficulty and what's missing right now — so you can decide what
  to cook tonight at a glance.
- **Stock screen reads location + attention deep-links.** The Stock
  screen now accepts `?location_id=…&attention=true&level_id=…` query
  params so other screens can link straight into a filtered view.
- **Shopping lists overview is the launchpad for every kind of list.** The
  "New list" menu now bundles every starting point in one place: from
  flagged essentials, from every low-or-out item (with a live count of how
  many that is), from a recipe (pulls the recipe's ingredients into a fresh
  list), from a meal plan (aggregates ingredients across every meal in the
  plan, scaled by servings), or from a saved template. Each card carries
  more actions — open, set primary, copy unticked → new list (active),
  copy archived → new list, archive without finishing, delete — and the
  primary list gets a richer stats strip showing remaining, full list and
  Savings vs RRP totals at a glance. The empty state recommends
  auto-generating from low/out items when stock data says there's something
  worth restocking.
- **Shopping list detail is now a shopping-trip companion.** Lines render as
  the shared stock-item chip — same level badge, alert dot, on-list
  indicator and overflow menu as everywhere else — with a per-line menu to
  swap an item with one of its recorded substitutes or move it onto another
  list. You can group lines by stock location (for a shopper's route through
  the storage areas at home) or by chosen merchant. Offer chips now mark
  your preferred merchant with a star and show how much you save vs the
  product's RRP, and the totals card carries a "Savings vs RRP" headline.
  A new **Review mode** hides unticked items and shows exactly which stock
  items will bump to Well-Stocked when you finish. Finishing a list with
  unticked items now offers to copy them straight into a new active list
  before archiving, so nothing falls through the cracks. The inline picker
  has been replaced by the shared **Quick add** sheet so the same search,
  offer-selection and frequently-added suggestions appear wherever you
  trigger it.
- **Stock item detail is now a relationship hub.** A tabbed page — Overview,
  Linked Products, Recipes, Substitutes, Lists and History — with a toolbar to
  mark open, restock, set expiry, find deals or add to a list. Linked products
  show the current deal, a price-trend sparkline and a preferred-merchant star,
  with one-click "add cheapest to list". Recipes that use the item appear as
  cards, dimmed when other ingredients are also missing. You can now record
  substitute items and swap one straight onto a shopping list, see every active
  list the item is on, and review a timeline of its stock-level changes.
- **Pantry is now the command center.** Every item row is built from the shared
  stock-item chip and surfaces its live cross-feature links inline: a location
  chip that filters to that spot, an "on N lists" chip that shows (and jumps to)
  the lists it's on, an expiry control to push or clear dates without leaving the
  page, and a "used in N recipes" badge that previews the recipes on hover. Click
  a row to peek at the full item detail in a side panel without navigating away.
  New filters for "needs attention" and "used in a recipe", and the bulk bar can
  now add to a list, move location, mark restocked or set a substitute. Empty
  state points you at building a pantry from a recipe or a shopping list.

### Added
- **First-run setup wizard.** New users (and anyone with a fresh
  `onboarding_completed_at`) land on a guarded `/welcome` route that
  walks them through five short steps: a name + theme + font picker,
  an admin "you're in charge" callout for the first user, optional
  seeding of Dora's default stock groups and locations (idempotent —
  re-importing won't duplicate), adding their first stock item with
  inline "add another" and skip, and a four-card tour with deep links
  into the screens that matter. Progress persists to localStorage so
  refresh resumes where you left off. **Skip everything** stamps the
  completion timestamp and surfaces a 24-hour "finish setting up"
  banner on the dashboard with a one-tap Continue. Settings → Account
  carries a **Restart onboarding** entry for returning users who want
  to redo the tour.
- **My Products is now its own screen.** A dedicated grid at `/my-products`
  shows every saved product with the stock item it links to (click the chip
  to jump to that item), the live deal badge, the merchant, and an
  inactive/out-of-stock marker. Filters: by linked stock item, on-deal-now,
  by merchant, plus search across name/brand/merchant/size. Bulk-select adds
  **Add all on-deal to a list** (pre-selecting the merchant offer per line),
  **Unlink** and **Mark inactive**. A "Stock items without products"
  shortcut lists every tracked item that no active product links to, with
  one-click jumps into Product Search to find a match.
- **Dedicated recipe detail / edit page.** Recipes now have a proper editing
  surface at `/recipes/:id` with a two-column layout. Each ingredient row
  is an autocomplete bound to your tracked stock items — type a name that
  doesn't exist and "Create '<name>'" inlines a new stock item without
  leaving the page — plus a live level badge, a "Missing" chip when it's
  out of stock or untracked, and a per-row "add to primary list" button.
  A sidebar carries the cooking shortcuts: **Start cook mode**, **Add all
  missing to a shopping list**, and **Find substitutes for missing
  ingredients** (uses each stock item's recorded substitutes — click a
  chip to swap it straight into the recipe).
  Secondary actions (mark made, delete, mark favourite) are one click away.
- **Import a recipe from a URL.** Paste any recipe page that publishes
  schema.org/Recipe JSON-LD (which is most major recipe sites) and Dora
  pulls the name, cuisine, category, times, servings, instructions,
  nutrition and ingredients. Ingredients are fuzzy-matched against your
  tracked stock items so most rows land pre-filled; unmatched items keep
  their raw text in the notes so you can pick a match or create a new
  stock item inline.
- **Frequently-added suggestions in Quick add.** The Quick add sheet now
  surfaces the stock items you've added to a list most often — based on
  every line you've ever added — so opening it without typing puts your
  usual basket one tap away. Each frequent suggestion is starred so it's
  obvious why it's first.
- **Shared building blocks for stock and shopping actions.** Stock items now
  appear as a consistent chip everywhere — picture, live stock level, an
  on-a-list indicator and an attention dot — with a built-in menu to add to a
  list, mark restocked, push expiry, find substitutes or jump to recipes that
  use it. Products get a matching chip with the current deal and merchant. A
  global quick-add sheet lets you drop any item onto a list from anywhere,
  picking the merchant offer as you go. These are groundwork the upcoming
  screens build on, so the same action behaves identically wherever you trigger
  it.
- **Dora's chat can be backed by your own language model.** An optional,
  bring-your-own-LLM assistant: an admin enables it in **Settings → System** and
  points it at a language model they run themselves (e.g. a local Ollama),
  entering the base URL and model name. Off by default — nothing is bundled,
  downloaded, or dictated, and when it's off Dora uses its built-in rule-based
  helper. With it on, the chat understands plain-English questions about your
  data — "what's low in the fridge?", "any specials on cheese?". The model uses
  tool-calling to fetch real rows, so it can't invent items or prices.
- **Add to your shopping list by asking.** "Add 3 apples and some milk" now
  works: the model extracts the items and quantities, Dora matches each to your
  tracked stock items, and adds them to your primary list. When a name matches
  more than one item ("which milk?") she shows the options as chips and waits
  for you to pick before committing — nothing is added until you confirm. Items
  with no tracked match are reported, not invented.
- **"What should I cook?"** Dora now suggests recipes. Ask for an idea by mood
  ("something spicy", "something light") and she translates it into recipe
  terms; or ask what you can make from what you have and she ranks recipes by
  how many of their ingredients are in stock — calling out the ones you can
  make right now and what's missing for the rest.
- **Dora answers how-to and general questions too.** Beyond data queries and
  shopping-list actions, the assistant now handles "how do I…?", app-help and
  general/chit-chat messages conversationally, grounded in a guide to what Dora
  can do — so it points you to the right page (e.g. "open Product Search") rather
  than shrugging. The old rule-based replies are now only used as a fallback
  when the model isn't reachable.

## [0.7.0] - 2026-05-20

### Added — the killer loop

- **Shopping list overhaul.** Multiple lists, primary/default flag for
  quick actions, archive on completion, copy archived → new active list,
  copy unticked items to a new list. Detail page lets you tick items off,
  adjust quantity, and pick which merchant offer to buy per line. Live
  totals (remaining, picked up, full list). Finish-shopping flow archives
  the list and auto-bumps every ticked item's stock level to "Well-Stocked".
- **Stock overview filters + cart-button quick-add.** Autofocus search,
  filter chips for stock level, location, essentials-only and on-list /
  off-list. Sort menu (name, level, last-updated). Cart button on each row
  one-clicks the item onto your primary shopping list, with the icon and
  colour reflecting where the item already sits across all your lists.
  Bulk-select mode adds multiple items to the primary list at once.
- **In-app alerts.** Bell icon in the header with a live badge for
  high/medium-severity items. Slide-in panel lists everything that needs
  attention — expired, expiring soon, out/low stock (essentials called
  out separately), stocktake overdue — with inline actions (push expiry
  7 days, clear expiry, mark restocked, acknowledge stocktake). Polls
  every 60 seconds.
- **Dora now answers "what needs my attention?"** — new quick-action chip
  pulls the same data as the bell.

### Added
- **Dora help assistant.** A floating mascot (bottom-right) opens a chat
  panel with quick actions for "What can I do on this page?", "What's new?",
  "Tell me something" and more. A dedicated `/help` page surfaces guides,
  the changelog, and a random food fact.
- **Version + update detection.** Dora checks the GitHub repo for newer
  releases and surfaces an update banner when one is available.

## [0.5.0] - 2026-05-19

### Added
- **User & global options.** Per-user theme (System / Light / Dark with OS
  auto-follow), font family (Default / Urbanist / Nunito), and text size
  (small / medium / large). Update username and password in-app. Subscribe
  / unsubscribe to the weekly deals email and choose compact format.
- **Admin Users page.** View all accounts, toggle admin role, toggle the
  deals subscription on another user, edit username and email, and reset
  another user's password (one-time generated value, copy-to-clipboard).
- **First-user-is-admin** on fresh installs.

## [0.4.0] - 2026-05-19

### Added
- **Hierarchical locations.** Zones → Areas → Sections replace the old flat
  Stock Locations list. Managed from Settings → Stock locations as a tree
  editor; stock items reference any node in the tree.
- **`is_admin` flag** on users; admin-only routes gated server-side.

### Changed
- Stock locations table rewritten with `parent_id`, `kind` and `sequence`.
  Pre-release migration drops existing rows.

## [0.3.0] - 2026-05-19

### Added
- Initial settings page with per-user and admin (global) sections.

## [0.2.0] - 2025-02-23

### Added
- Recipes, meals, meal plans.
- Stock items get expiry dates and flags.

## [0.1.0] - 2025-01-18

### Added
- Initial release. Stock items, stock locations, shopping lists, merchant
  scraping (Coles, Woolworths, IGA, Aldi).
