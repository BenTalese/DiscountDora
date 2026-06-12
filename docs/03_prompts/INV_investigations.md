# INV — Investigations (report first, then we decide/act)

**Wave:** INV · **Risk:** none (read-only/reporting) · **Depends on:** none

These answer questions you asked. Each produces a short written report — **no code changes** — so you can decide. Run independently.

---

## INV-1 — Orphaned-field audit ("what else is like stock groups?")
You flagged stock groups as a field that exists with no UI to set/use it. Find all of them.

**Prompt:** Audit the app for **fields/relationships that exist in the data model or DTOs but have no way to be set or meaningfully used in the UI** (or are set but never read). For each: name, where defined (entity/DTO), whether it's writable in any UI, whether it's read/displayed/used in logic anywhere, and a one-line recommendation (wire up / surface / remove / leave). Cover stock groups, notes (stock item + ingredient), preferred merchant/product, nutrition fields, and anything else. Output `ORPHANED_FIELDS_AUDIT.md`. No code changes.

---

## INV-2 — Stock-overview perf & the "DS4 animations" change
You reported 1–3s nav lag (worst on stock overview, ~1s elsewhere), then said it "no longer feels laggy" after the DS4 animation task — and want to know what changed.

**Prompt:** Investigate navigation/render performance for the stock overview and general page transitions. (a) Profile what makes stock-overview mount slow (data fetch waterfall? client-side compute? large render?). (b) Review the DS4 animation-related changes in git history to explain what likely changed the *perceived* performance. Report findings + concrete optimisation options (e.g. server-side aggregation per the state-ownership proposal, virtualised rows, deferred fetch). Output `STOCK_OVERVIEW_PERF.md`. No code changes yet.

---

## INV-3 — Logging & `.local` folder layout
You noted logs not rolling, a 46k-line file with a wrong date span, logs in two locations, and a messy `.local`/data folder split.

**Prompt:** Investigate the logging setup and on-disk data layout. (a) Where are logs written, is rotation configured, why is the current file huge/wrong-dated? (b) Why is data split between `.local` and a `data` folder, and logs in two places? Recommend a single coherent layout (keep-as-data vs consolidate-into-.local) and a correct rolling config (size/time, retention). Output `LOGGING_AND_DATA_LAYOUT.md` with findings + recommendation. No changes yet.

---

## INV-4 — Forgot-password email wiring
You asked how forgot-password email actually works and proposed: admin sets up a sending account in onboarding; if unset, hide the button.

**Prompt:** Trace the password-reset email flow end to end (SMTP config, where credentials come from, what happens if unconfigured). Report whether it currently works out-of-the-box, and outline a **flexible** admin email-setup approach (multiple providers, minimal complexity) plus the "hide forgot-password if no sender configured" logic. Output `EMAIL_SETUP_FINDINGS.md`. No changes yet.

---

## INV-5 — Feature clarifications (QR vs barcode, relevancy filter, etc.)
Small "how does this work / is it redundant" questions.

**Prompt:** Briefly document the current behaviour of: (a) "show QR code" vs "register barcode" vs "print QR" — are they distinct features, redundant? (b) the product-search **relevancy** filter — how it ranks, whether it works well; (c) expiry↔open relationship (do they affect each other?). For each, state what the code does today and a recommendation (keep/merge/clarify/cut). Output `FEATURE_CLARIFICATIONS.md`. No code changes.

---

## INV-6 — Recipe-comparison worth (keep / rework / cut)
You called the recipe comparison tool "useless" but want its worth assessed before cutting (master plan Decision 3).

**Prompt:** Assess whether the recipe-comparison feature (X2, in the Cookbook) earns its place. Report: what it does today, any signal it's used, what a *useful* comparison would need (sorting / highlighting / decision support), and whether that serves a Charter principle or is anti-creep (P10). Recommend **keep-as-is / rework (with a concrete sketch) / cut**. One-page memo, not a full design. Output `RECIPE_COMPARISON_ASSESSMENT.md`. No code changes. The Cookbook brief (C-4) defers to this outcome.

---

## INV-7 — Stock-item detail "History" tab worth (keep / rework / cut)
You said "the history tab as-is feels unuseful. Maybe if it had a bit more data/info in it…maybe? I'd need to be convinced."

**Prompt:** Assess whether the History tab on Stock Item Detail earns its surface. Document what it shows today (level changes, what else?), what *could* be there to make it decision-useful (last-time-restocked, who/when, level cadence, expiry events, on-list events), and whether the resulting feature serves the closed loop (Charter P5) or is incremental noise (P10). Recommend **keep-as-is / rework (with a concrete sketch of "what would be useful") / cut**. One-page memo. Output `05_investigations/HISTORY_TAB_ASSESSMENT.md`. No code changes.

---

## INV-8 — Substitute "swap into list" behaviour (keep / rework / cut)
You said "swap into list for substitutes feels like a weird feature. Would it even get used?"

**Prompt:** Trace the current "swap substitute into shopping list" path (where the affordance lives, what action it triggers, where it appears in cook mode). Assess: is the user mental model "I'm at the shop and the planned item is out, swap it in here" actually served by the current implementation? Or is the cook-mode-temporary-swap (B8) the real ask and this list-level swap is leftover? Recommend **keep-as-is / rework / cut**. One-page memo. Output `05_investigations/SUBSTITUTE_SWAP_ASSESSMENT.md`. No code changes.

---

## ~~INV-9~~ — Command-palette worth (keep / shrink / cut) — **SUPERSEDED 2026-06-12**

The 2026-06-12 user decision was **cut entirely** (palette retired
from the SPA — see `05_investigations/COMMAND_PALETTE_ASSESSMENT.md`
which already recommended SHRINK; the final call landed harder).
The original prompt below is preserved for the audit trail. Do not
re-run.

> ~~You said "how useful is the command palette feature really? Let's assess."~~
>
> ~~**Prompt:** Assess the Ctrl-K command palette (`CommandPalette.vue` + `useCommands`). Document the static command set, search wiring, usage frequency signals (none today — note that), and the Charter-fit (Effortless+keyboard for power users vs Anti-creep surface area). Distinguish between (a) the palette as a power-user accelerator, and (b) the entity-search inside it which arguably belongs on a global search bar instead. Recommend **keep / shrink to entity-search-only / cut**. One-page memo. Output `05_investigations/COMMAND_PALETTE_ASSESSMENT.md`. No code changes.~~

---

## INV-10 — "Essential" flag — where is it, how to set it, is it the right model?
You said "no way to set 'essential' that I can see. Might be missing it?" The auto-generate shopping-list path already references an `essentials_only_for_low` criterion, so the concept exists somewhere.

**Prompt:** Trace where "essential" lives in the data model and code. Specifically: does `StockItem` carry an `is_essential` (or similar) column? Where is it read (auto-gen low-stock path, anywhere else)? Where SHOULD users be able to set it (detail page toolbar? stock-overview quick-toggle? settings → essentials list?). And is "essential" the right primitive at all, or should it be derived (e.g. "you buy this every shop" auto-detected)? Report findings + a concrete recommendation. Output `05_investigations/ESSENTIAL_FLAG_FINDINGS.md`. No code changes.
