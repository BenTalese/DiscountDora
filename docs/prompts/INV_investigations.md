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
