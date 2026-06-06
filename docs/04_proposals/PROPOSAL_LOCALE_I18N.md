# C-locale — Locale & international readiness → `PROPOSAL_LOCALE_I18N.md`

**Type:** 🔵 design brief — produces this proposal, changes **NO code.**

**Origin.** User-floated (2026-06-06), not from the feedback doc: *"ensure this app
can be used by people outside Australia — removing the merchant API to its own
companion app probably solves most of this, as products can now be from
anywhere."* This brief tests that hypothesis against the live code and scopes what
locale-readiness actually requires beyond the companion split.

**The hypothesis, refined.** The companion split (master Decision 1) does solve the
*product-sourcing* half: once scraping and the merchant catalogue leave Dora-core
and data arrives via the C-10 ingestion API carrying its own `source` label,
products can come from any country's merchants — Dora-core stops assuming
Australian retailers. **But that is necessary, not sufficient.** Dora-core still
carries AU/locale assumptions in its own UI and seed/copy that the companion split
doesn't touch: a hardcoded currency symbol, a hardcoded BCP-47 voice locale, AU
merchant branding baked into the core, and the deals-email day model. This brief
separates "what the companion fixes for free" from "what Dora-core must still do."

**Charter check.** Effortless + Anti-creep. The cheap, high-value win is
**currency/format-neutrality + de-AU-ifying core copy** — a small, contained change
that makes Dora usable anywhere. **Full UI translation (multi-language)** is a
genuine big rock and is explicitly scoped *out* of the near-term here (§2.5) —
recommended as a deferred someday, not bundled in, to avoid creep.

---

## 1. Current state (grounded in code)

**What the companion split already handles (no Dora-core work):**
- Merchant scraping, the merchant/provider model, and "which retailers exist" move
  to the companion (C-6/C-8). Dora-core only ingests `product`/`offer`/
  `price_observation` rows via C-10, each carrying a `source` label — country-
  agnostic by construction.

**AU/locale residue still in Dora-core (the actual work):**
- **i18n is plumbed but dormant.** `web_app/src/boot/i18n.ts` installs `vue-i18n`
  with `locale: 'en-US'` hardcoded; `src/i18n/en-US/index.ts` is still the
  **untouched Quasar scaffold stub** (`{ failed, success }`); there are **zero
  `$t()` calls** in the app. So the machinery exists but nothing routes through it
  — strings are hardcoded English in templates.
- **Currency symbol is hardcoded `$`** in price/budget inputs (e.g.
  `ShoppingListShopMode.vue` `prefix="$"`, `PreferencesSettings.vue` budget input)
  and likely in price *displays*. No currency setting; `$` happens to read fine for
  AUD/USD but is wrong for €/£/¥ and assumes symbol-prefix placement.
- **Voice defaults to `en-AU`** — `useVoiceInput.ts` (`options.lang ?? 'en-AU'`).
- **AU merchants baked into core** — `seed.py` seeds Woolworths/Coles/Aldi/IGA;
  `AldiLogo.vue` / `IgaLogo.vue` are core components; the assistant's
  `app_knowledge.py` + `tools.py` copy names "(Coles, Woolworths, IGA, Aldi)"
  inline. Post-companion these are demo/branding/copy residue, not functional, but
  they signal "this is an Australian app."
- **Dates already locale-aware** — `toLocaleString()` uses the browser locale;
  `Intl.Collator('en', …)` for sorting is locale-generic. These are fine.
- **Deals email day** — `User.send_deals_on_day` (int) + weekly cadence; locale-
  neutral mechanically, but its framing ties to the AU deals cycle (companion-fed
  post-split).

**Net:** the scaffold for real i18n exists but is unused; the concrete blockers to
"usable outside Australia" are **currency, the AU voice default, and AU branding/
copy in core** — all small and contained.

---

## 2. The design

### 2.0 Three layers, ranked by value-per-effort

| Layer | What | Effort | Recommend |
|---|---|---|---|
| **A. Currency & number format neutrality** | A currency/locale setting; route every money render + price input through one formatter; stop hardcoding `$` | small | **do now** |
| **B. De-AU the core** | Move AU merchant branding/copy/seed to companion or behind config; voice locale follows the locale setting | small–medium | **do now** |
| **C. Full UI translation (multi-language)** | Adopt the dormant `vue-i18n`: extract every string to `$t()`, add locale message files, a language picker | large | **defer (someday)** |

A + B make Dora **usable** anywhere (an Italian user sees €, no IGA branding, voice
in their tongue). C makes Dora **localized** (UI in their language) — a separate,
much larger effort that the user did not ask for. Recommend committing to A + B and
explicitly parking C.

### 2.1 Currency & number formatting (Layer A)

- **One locale/currency setting.** Where it lives is the open decision (§4-1):
  per-user (`User.locale` / `User.currency`) vs install-wide (`AppSetting`).
  Recommend **install-wide currency** (a household shares a currency) with an
  optional per-user display-locale; this also fits C-cross's two-tier model.
- **One money formatter, server-aware.** Replace every hardcoded `$` with a single
  formatter (`Intl.NumberFormat(locale, { style: 'currency', currency })`) so
  symbol, placement, decimal/grouping separators all follow the setting. Price
  *inputs* (budget, shop-mode pricing) read the symbol from the same source rather
  than a literal `prefix="$"`.
- **State-ownership:** currency is a server-owned fact the client reads (aligns
  with the standing principle); the client never hardcodes the symbol.
- **Ingestion tie-in:** C-10 `price_observation` rows should carry (or be
  normalised to) a currency, so multi-source data isn't silently summed across
  currencies. Note as a ripple into C-10's payload (§4-3).

### 2.2 De-AU the core (Layer B)

- **Merchant branding/copy → companion or config.** `AldiLogo`/`IgaLogo` and the
  inline "(Coles, Woolworths, IGA, Aldi)" assistant copy should not be hardcoded in
  Dora-core. Post-companion, merchant identity (incl. logos) is companion/ingested
  metadata; the assistant copy becomes generic ("your configured merchants"). Audit
  every inline AU-retailer mention.
- **Seed data.** `seed.py`'s AU merchants/products are demo data — keep them as
  *demo* (clearly optional, gated by the demo-data toggle from C-5 onboarding), not
  as implicit defaults a non-AU user inherits.
- **Voice locale follows the setting.** `useVoiceInput.ts` default `en-AU` →
  derives from the locale setting (fall back to browser locale, then a neutral
  default), not a hardcoded AU tag.

### 2.3 The dormant vue-i18n scaffold — decide its fate (§4-2)

The app already pays for `vue-i18n` (dependency + boot + unused stub). Two honest
options:
- **(a) Adopt-lite:** keep i18n installed, use it *only* for number/currency/date
  formatting (its `Intl` wrappers), not string translation. Cheap; gives Layer A a
  natural home; defers Layer C.
- **(b) Remove the dead scaffold** until/unless Layer C is greenlit, to stop
  carrying unused plumbing (Anti-creep on dependencies).
- **Recommend (a):** the formatting wrappers are exactly what Layer A needs, and it
  keeps the door open for C without a rebuild. Replace the stub `en-US` messages
  with real format definitions rather than the `failed/success` example.

### 2.4 What this unblocks / who consumes it
- **C-cross** gains a locale/currency setting slot (fits its two-tier config model).
- **C-2 / C-4 / dashboard** budget & cost surfaces render via the shared formatter.
- **C-10** ingestion gains a currency field on price observations.

### 2.5 Explicitly out of scope (deferred)
- **Full multi-language UI translation (Layer C)** — extracting ~every string,
  authoring locale catalogues, RTL support, a language picker. Big rock; no user
  demand beyond "usable outside Australia." Parked as a someday; the §2.3(a)
  decision keeps it cheap to start later.
- **Timezone handling** beyond what `toLocaleString()` already gives — only revisit
  if a concrete bug surfaces.
- **Companion-side** merchant/provider internationalization — lives in C-6/C-8.

---

## 3. Open decisions (for co-design)

1. **Currency home (§2.1)** — install-wide currency (recommended, household shares
   one) + optional per-user display locale, or fully per-user?
2. **vue-i18n fate (§2.3)** — adopt-lite for formatting only (recommended), or rip
   out the dead scaffold until full translation is greenlit?
3. **C-10 currency field (§2.1)** — add a currency to `price_observation` now
   (recommended; prevents cross-currency summing), or assume single-currency per
   install and skip?
4. **Merchant branding (§2.2)** — fully remove `AldiLogo`/`IgaLogo` from core and
   treat logos as ingested/companion metadata, or keep them as optional bundled
   assets for AU installs?

---

## 4. Ripple & dependencies

- **Companion (C-6/C-8)** — owns merchant/provider identity; this brief assumes the
  split has happened and only de-AUs what *remains* in core.
- **C-10 ingestion** — price observations should carry currency (§2.1, §4-3).
- **C-cross** — the locale/currency setting fits its config layer; coordinate so
  it's defined once.
- **C-2/C-4/dashboard** — all money rendering routes through the shared formatter.
- **Deferred surfaces** — dashboard/reports money displays inherit the formatter
  when picked up; note, don't build.
- **State-ownership** — currency/locale are server-owned facts the client reads.

---

## 5. From the original spec (historical — `docs/00_original_spec/`)

Non-authoritative. The **User & Global Options** board lists *"I can change the
language used in the UI (multi-language support)"* — **superseded/deferred**: it
confirms multi-language was always a someday aspiration (Layer C), corroborating
the recommendation to park full translation while shipping locale-readiness
(A + B) now. Nothing in the original spec addresses currency-neutrality —
historically the app assumed AUD, which is exactly the assumption this brief
removes.

---

## 6. Feedback coverage

This brief is **user-originated in conversation, not from the feedback doc** — so
per the CLAUDE.md cross-cutting rule there is no cluster of feedback bullets to
map; the motivation is the idea itself plus the companion-split decision. Related
bullets, for traceability:

| Source | Summary | Where |
|---|---|---|
| User idea (2026-06-06) | Usable outside Australia | §2 (Layers A+B); C deferred |
| Master Decision 1 | Scraping → companion; products from anywhere | §1 (the half already solved) |
| Original spec (User & Global Options) | Multi-language UI | §2.5 / §5 (deferred Layer C) |
| L496 (data-folder gripe) | unrelated, but the only other "why is it like this" infra bullet | out of scope (INV/FU territory) |

No existing feedback bullet is *closed* by this brief (it's net-new scope); it
*enables* correct rendering for C-2/C-4 budget bullets in non-AUD installs.

---

## 7. Suggested sequencing

1. **Currency setting + shared money formatter (§2.1)** — highest value; unblocks
   correct money rendering everywhere. Pair with the C-cross config work.
2. **vue-i18n adopt-lite for formatting (§2.3a)** — gives the formatter a home.
3. **De-AU core: voice locale, merchant branding/copy, demo-only seed (§2.2).**
4. **C-10 currency field (§2.1)** — coordinate with the ingestion impl.
5. **(Deferred) Layer C full translation** — only on explicit greenlight.

No code until approved — this is a brief.
