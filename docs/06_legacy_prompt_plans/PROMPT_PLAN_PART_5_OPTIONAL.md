# DiscountDora - Prompt Plan Part 5 Optional

This optional prompt plan covers the extra layers that make DiscountDora more
trustworthy, fast, resilient, adoptable, and demo-ready.

Parts 1-4 are the main arc:

- capability
- intelligence
- restraint
- polish

Part 5 is optional by design. These prompts are not all required before Dora is
useful. Use them when the app is approaching a public release, when a specific
risk becomes real, or when you want the project to feel more production-grade.

---

## When to Use This Plan

Run these prompts if:

- users outside the developer household will use Dora
- household sharing or assistant features are enabled
- merchant price data is important to trust
- performance starts feeling sluggish
- you want a convincing demo/release
- the app stores enough personal data that privacy/security need a formal pass

Skip or defer them if:

- you are still validating the core grocery loop
- the app is only local/private
- you are actively changing major data models
- the extra process would slow down product discovery

---

## Recommended Order

1. **Trust and safety** - P5-01 -> P5-02
2. **Speed and reliability** - P5-03 -> P5-04
3. **AI quality** - P5-05
4. **Adoption and first impressions** - P5-06 -> P5-07
5. **Data confidence** - P5-08 -> P5-09
6. **Support and operations** - P5-10
7. **Optional final release gate** - P5-11

---

## Cross-Cutting Rules

- **Optional does not mean sloppy.** If a prompt is run, it should be completed
  to a professional standard.
- **Do not add process theater.** Every check, doc, or dashboard must help debug,
  protect users, improve trust, or ship with confidence.
- **Keep Dora simple.** Hardening should not make the daily UI heavier.
- **Prefer measurable quality.** Add budgets, test cases, audits, and reports
  where they make future regressions easier to catch.
- **Security and privacy beat convenience.** Especially for assistant, household,
  backup, and share-link features.

---

# Tier P5-A - Security and Privacy

## P5-01 - Security and Privacy Hardening

```
Run a security and privacy hardening pass across DiscountDora.

READ FIRST:
- Auth implementation.
- Household sharing if implemented.
- Backup/restore and import/export.
- Dora assistant and LLM/tool-calling code.
- Share links if implemented.
- Logging/audit strategy.
- Config/env handling.
- docs/product/DORA_PRODUCT_CONSTITUTION.md.

AUDIT:
1. Auth and sessions:
   - Password hashing.
   - Session invalidation.
   - Cookie flags.
   - CSRF/CORS posture.
   - Rate limits.
2. Authorization:
   - User/household scoping on every route.
   - Admin-only routes.
   - Invite flow.
   - Share-link access.
3. Secrets:
   - No secrets in logs.
   - No secrets committed.
   - .env.example complete.
   - Production refuses unsafe defaults.
4. Data privacy:
   - Backups exclude passwords/tokens.
   - Debug exports are redacted.
   - Assistant only sees allowed data.
   - Logs avoid sensitive household details where possible.
5. Uploads/imports:
   - File type validation.
   - File size limits.
   - Safe storage paths.
   - No path traversal.
6. Dependencies:
   - npm audit or equivalent.
   - Python dependency audit.

BUILD:
1. docs/security/SECURITY_REVIEW.md with findings and fixes.
2. SECURITY.md with vulnerability reporting guidance.
3. Add or tighten tests for household/user isolation.
4. Add security headers in the web/server layer where appropriate.
5. Add dependency scanning to CI if not present.

DEFINITION OF DONE:
- Security review document exists.
- High-risk findings are fixed or explicitly tracked.
- Route authorization tests cover critical entities.
- CHANGELOG entry under [Unreleased].
```

## P5-02 - Privacy Controls and User Data Rights

```
Make it clear and easy for users to understand, export, and delete their data.

READ FIRST:
- Data Management prompts N1-N5.
- Backup/restore/export implementation.
- Auth/user model.
- Household model if present.
- Dora assistant settings.

BUILD:
1. Settings > Privacy page:
   - What data Dora stores.
   - What data Dora sends to local/external assistant services.
   - Export my data.
   - Delete account/data, if supported.
   - Clear assistant history, if stored.
2. Backend endpoints:
   - GET /api/privacy/summary
   - POST /api/privacy/export
   - POST /api/privacy/delete-request or DELETE /api/account
   - POST /api/privacy/clear-assistant-history
3. Data deletion rules:
   - Single-user data.
   - Household-owned data.
   - Audit logs.
   - Shared lists/recipes.
4. Docs:
   - docs/security/PRIVACY_MODEL.md.

UX DETAILS:
- Deletion must be explicit and carefully confirmed.
- Export should reuse backup/export logic where possible.
- Do not expose scary legal language in daily UI.

DEFINITION OF DONE:
- User can see a plain-language privacy summary.
- User can export their data.
- Data deletion behavior is documented.
- CHANGELOG entry under [Unreleased].
```

---

# Tier P5-B - Performance and Scale

## P5-03 - Performance and Scale Pass

```
Profile and improve DiscountDora performance across frontend, backend, and data
queries.

READ FIRST:
- Major pages and their data-loading patterns.
- API routers/services.
- Database models/indexes.
- Merchant product search and scraping/cache.
- PWA/cache setup.
- E2E and visual QA scripts.

MEASURE:
1. Frontend:
   - Bundle size.
   - Route load time.
   - Largest pages/components.
   - Slow renders.
   - Image sizes.
2. Backend:
   - Slow endpoints.
   - N+1 queries.
   - Missing indexes.
   - Large payloads.
3. User flows:
   - Today page load.
   - Pantry load with many items.
   - Shopping list detail.
   - Product search.
   - Recipe overview.
   - Dora data query.

BUILD:
1. docs/performance/PERFORMANCE_BASELINE.md.
2. Add performance budgets:
   - frontend bundle thresholds
   - key route response time targets
   - page load targets
3. Fix top bottlenecks:
   - virtualize long lists
   - add indexes
   - reduce over-fetching
   - cache safe GETs
   - optimize images
   - lazy-load advanced pages
4. Add lightweight CI checks for bundle size and critical API tests.

DEFINITION OF DONE:
- Performance baseline exists.
- Top bottlenecks are fixed or tracked.
- Critical pages feel fast with seeded large data.
- CHANGELOG entry under [Unreleased].
```

## P5-04 - Mobile/PWA Field Test

```
Test Dora as a real mobile grocery companion under realistic conditions.

READ FIRST:
- PWA setup M1.
- One-handed shopping mode P2-11.
- Fast Add P3-04.
- Scan/barcode N5.
- Offline experience F3.
- Visual QA P4-11.

FIELD TEST SCENARIOS:
1. Add to home screen.
2. Open primary list from app shortcut.
3. Add item by Fast Add.
4. Shop with one hand.
5. Tick items while offline.
6. Reconnect and sync.
7. Scan barcode/QR if available.
8. Use Dora voice fallback if voice unsupported.
9. Finish shopping.
10. Recover from app reload mid-shop.

BUILD:
1. docs/qa/MOBILE_FIELD_TEST.md:
   - Devices/browsers tested.
   - Results.
   - Issues.
2. Fix high-priority mobile issues:
   - tap target size
   - sticky actions
   - keyboard overlap
   - scroll jumps
   - install prompt roughness
   - offline banner clarity
3. Add Playwright mobile smoke tests where possible.

DEFINITION OF DONE:
- Dora works as a phone-first shopping tool.
- Mobile field test report exists.
- Top issues are fixed or tracked.
- CHANGELOG entry under [Unreleased].
```

---

# Tier P5-C - AI Reliability

## P5-05 - Dora AI Reliability and Evaluation Suite

```
Make Dora's assistant behavior testable, traceable, and reliable.

READ FIRST:
- Dora assistant implementation.
- LLM/tool-calling setup.
- Rule-based fallback.
- Tool schemas.
- Prompt text/system instructions.
- Automation/suggestion flows.
- Privacy model.

BUILD:
1. Dora evaluation fixtures:
   - Seeded household data.
   - Known stock/list/recipe/product states.
   - Expected tool calls and answers.
2. Evaluation cases:
   - "What's low?"
   - "Add milk and eggs."
   - Ambiguous item disambiguation.
   - "What can I cook?"
   - "What should I use soon?"
   - "Why did you add this?"
   - Unsupported request.
   - No hallucinated item/product.
3. Tool-call contract tests:
   - Required args.
   - Permission boundaries.
   - No mutation without confirmation where required.
4. Trace viewer/log:
   - Prompt version.
   - Tool calls.
   - Final response.
   - Redacted user data.
5. Fallback tests:
   - Model unreachable.
   - Tool error.
   - Low confidence.

CREATE:
- docs/ai/DORA_AI_EVALS.md.

DEFINITION OF DONE:
- Dora has repeatable evals.
- Tool-call behavior is covered by tests.
- Hallucination-prone flows have guardrails.
- CHANGELOG entry under [Unreleased].
```

---

# Tier P5-D - Adoption and First Impressions

## P5-06 - Onboarding and First-Week Experience

```
Make Dora prove its value quickly for a new user without demanding a huge setup
session.

READ FIRST:
- First-run onboarding F1.
- Minimal stock item model P3-06.
- Fast Add P3-04.
- Grocy import N3/P3-15.
- Today page P3-09.
- Dora assistant.

GOAL:
The user should reach a useful first shopping list in under five minutes.

BUILD:
1. Onboarding paths:
   - Start from scratch.
   - Import from Grocy/spreadsheet.
   - Start with a few common essentials.
   - Use Dora to add items conversationally.
2. First-week nudges:
   - Day 1: Create/finish first list.
   - Day 2-3: Mark common items low/restocked.
   - Day 4-7: Try recipe or deal suggestion.
   - Keep nudges quiet and dismissible.
3. Demo seed option:
   - Realistic pantry/list/recipes/products.
   - Clear "demo data" label.
4. Empty app states:
   - Every empty state should offer the shortest next action.

DEFINITION OF DONE:
- New user can get to first useful list quickly.
- Blank app does not feel dead.
- First-week nudges are helpful, not naggy.
- CHANGELOG entry under [Unreleased].
- E2E onboarding test covers the first-list path.
```

## P5-07 - Demo and Sellable Showcase Mode

```
Create a polished demo mode so DiscountDora can be shown to someone and make
sense in under one minute.

READ FIRST:
- README.
- Demo/seed scripts.
- Today page.
- Major polished screens.
- Visual QA report.

BUILD:
1. Demo seed data:
   - Household pantry.
   - Primary shopping list.
   - Low/out essentials.
   - Expiring items.
   - Recipes.
   - Meal plan.
   - Saved products/deals.
   - Dora suggestions.
2. Demo reset command.
3. Demo script:
   - docs/demo/DEMO_SCRIPT.md.
   - 60-second version.
   - 5-minute version.
4. Screenshot pack:
   - Today
   - Shopping list
   - Pantry
   - Dora assistant
   - Recipes
   - Mobile shop mode
5. README/demo section:
   - How to launch demo mode.

UX DETAILS:
- Demo data should look realistic, not lorem ipsum.
- Avoid fake-perfect data. Include believable grocery messiness.

DEFINITION OF DONE:
- One command starts a convincing demo.
- Demo script and screenshots exist.
- CHANGELOG entry under [Unreleased].
```

---

# Tier P5-E - Data Confidence

## P5-08 - Data Model Sanity Review

```
Review the data model for clarity, lifecycle correctness, and long-term
maintainability.

READ FIRST:
- All database models/migrations.
- Domain glossary.
- Household sharing if present.
- Receipt/forecast/waste/leftover models if present.
- Backup/restore.

AUDIT:
1. Entity ownership:
   - user vs household vs global.
2. Lifecycle:
   - active/archived/deleted.
   - completed/cancelled/skipped.
   - suggested/accepted/dismissed.
3. Deletion behavior:
   - hard delete vs archive.
   - foreign key handling.
4. Duplication:
   - product vs stock item vs list item.
   - meal vs recipe vs planned meal.
5. Required fields:
   - confirm minimal daily data.
6. Indexes:
   - common query paths.
7. Backup/restore:
   - every important entity included.

CREATE:
- docs/dev/DATA_MODEL_REVIEW.md.
- Entity relationship diagram if useful.

BUILD:
- Fix safe model inconsistencies.
- Document migration risks for larger fixes.

DEFINITION OF DONE:
- Data model review exists.
- High-risk inconsistencies are fixed or tracked.
- CHANGELOG entry under [Unreleased].
```

## P5-09 - Backup, Restore, and Recovery Drills

```
Prove that Dora users can recover their data when something goes wrong.

READ FIRST:
- Backup/restore N2.
- Import/export N3/N4.
- Data paths D1/D2.
- Privacy/data deletion P5-02.
- E2E data-management tests.

DRILLS:
1. Export backup from seeded household.
2. Restore into clean DB.
3. Restore partial subset.
4. Re-import same backup without duplicates.
5. Try corrupt backup.
6. Try newer unsupported schema_version.
7. Restore after app version bump/migration if applicable.

BUILD:
1. docs/qa/RECOVERY_DRILLS.md.
2. Automated test script for the repeatable drills.
3. Clear user-facing restore errors.
4. Backup schema documentation.

DEFINITION OF DONE:
- Recovery drills are documented and automated where practical.
- Restore failures are safe and understandable.
- CHANGELOG entry under [Unreleased].
```

---

# Tier P5-F - Merchant and Support Operations

## P5-10 - Merchant Data Quality and Support Bundle

> **MOVED / PARKED — 2026-07-15 (FU-394). Do not run this prompt as-written against Dora-core.**
> This prompt splits into two halves with different homes:
> - **Merchant data quality** (data-quality checks, `GET /api/merchant-status`, stale-price
>   warnings) → **moved to the companion project** per §7 **Decision 1** (the scraper /
>   merchant / provider model was extracted so Dora-core stays Charter-clean). Confirmed
>   **absent from Dora-core** (2026-07-15): no `merchant-status` endpoint, no data-quality
>   checks. Any future work on this belongs in the companion, feeding Dora via `/api/ingest`.
> - **Support bundle** ("Copy support bundle", `docs/support/SUPPORT_PLAYBOOK.md`) → **not
>   companion-scope; simply never built.** It is generic operator/ops tooling, unrelated to
>   the scraper. **Not** to be confused with the *shipped* FU-370 "Report an issue" support
>   *channel* (`dora_api/features/support/support_channel.py` → `/api/health` support block),
>   which is a different thing. The copy-bundle feature + playbook remain a **parked,
>   un-built possible-future Dora-core item**, not moved anywhere. There is a `/api/health`
>   endpoint it could build on if ever picked up.
>
> Net: nothing from P5-10 landed in Dora-core; the merchant half is companion-scope, the
> support-bundle half is parked. FU-394 closed on this basis — no code change.

```
Improve trust in merchant/product data and make support/debugging easier without
exposing secrets.

READ FIRST:
- merchant_api.
- Product search P10.
- Saved products P11.
- Price history N8.
- Diagnostics panel P4-06.
- Structured errors P4-07.

MERCHANT QUALITY:
1. Add data quality checks:
   - missing price
   - impossible unit price
   - stale scrape
   - duplicate merchant products
   - image failures
   - unit normalization errors
2. Add merchant status endpoint:
   - GET /api/merchant-status
3. Product UI:
   - Show stale price warning where relevant.
   - Do not present stale data as current.

SUPPORT BUNDLE:
1. Add dev/admin "Copy support bundle":
   - app version
   - config summary
   - health statuses
   - recent request IDs
   - recent safe errors
   - merchant scrape status
   - redacted logs
2. Ensure no secrets/tokens/passwords are included.

CREATE:
- docs/support/SUPPORT_PLAYBOOK.md:
   - common failures
   - how to read logs
   - how to use request_id
   - how to diagnose merchant stale data

DEFINITION OF DONE:
- Merchant data quality is visible and testable.
- Support bundle is safe and useful.
- CHANGELOG entry under [Unreleased].
```

---

# Tier P5-G - Optional Final Gate

## P5-11 - Optional Production Readiness Review

```
Run a final production readiness review if Dora is going beyond private/local
use.

READ FIRST:
- All Part 4 release readiness docs.
- Security review P5-01.
- Performance baseline P5-03.
- Mobile field test P5-04.
- AI evals P5-05.
- Recovery drills P5-09.
- Support playbook P5-10.

CREATE:
- docs/release/PRODUCTION_READINESS_REVIEW.md

CHECK:
1. Security:
   - auth
   - secrets
   - dependency scanning
   - household isolation
2. Privacy:
   - export/delete
   - logs
   - assistant boundaries
3. Reliability:
   - backup/restore
   - health checks
   - offline behavior
4. Performance:
   - page load budgets
   - API response budgets
   - large-data behavior
5. UX:
   - onboarding
   - mobile shopping
   - empty/error states
6. AI:
   - eval pass
   - fallback behavior
   - traceability
7. Operations:
   - support bundle
   - logs
   - release process

OUTPUT:
- Go / no-go recommendation.
- Blockers.
- Risks accepted.
- Follow-up backlog.

DEFINITION OF DONE:
- Production readiness review exists.
- Blockers are fixed or explicitly accepted.
- CHANGELOG entry under [Unreleased].
```

---

# Notes

This optional plan is not here to make Dora bigger. It is here to make Dora more
trustworthy when the time is right.

The main product promise still wins:

> Dora should feel easier than Grocy, not more official than Grocy.

Run these prompts only when they support that promise.
