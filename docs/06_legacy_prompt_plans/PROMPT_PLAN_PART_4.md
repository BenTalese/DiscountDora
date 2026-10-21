# DiscountDora - Prompt Plan Part 4

This final prompt plan is for making DiscountDora easier to build, debug,
maintain, polish, and proudly ship.

Parts 1-3 define what Dora should do and how it should feel for users.

Part 4 is about the development experience and final product finish:

- human-readable code
- predictable architecture
- clean boundaries
- fewer debugging mysteries
- useful logs and diagnostics
- polished, consistent UI
- professional visual quality
- a product that feels sellable, not like a side-project held together with tape

This plan should be run after the major user-facing features have mostly landed,
or in small slices whenever the codebase starts feeling hard to reason about.

---

## How to Use

- Do not treat these as cosmetic-only prompts. Developer experience is product
  quality.
- Prefer small, mechanical refactors with tests over sweeping rewrites.
- When a prompt finds messy or duplicated code, improve the local area and write
  down the pattern so future work follows it.
- Preserve behavior unless the prompt explicitly asks for a UX change.
- Every cleanup should make the next debugging session easier.

---

## Recommended Order

1. **Understand and document the system** - P4-01 -> P4-02
2. **Clean architecture and code readability** - P4-03 -> P4-04 -> P4-05
3. **Debuggability and diagnostics** - P4-06 -> P4-07
4. **Frontend consistency and polish** - P4-08 -> P4-09 -> P4-10
5. **Visual QA and professional finish** - P4-11 -> P4-12
6. **Developer workflow** - P4-13 -> P4-14
7. **Final release readiness** - P4-15

---

## Cross-Cutting Rules

Apply these to every Part 4 prompt:

- **Readable beats clever.** Prefer explicit names, obvious data flow, and small
  modules over dense abstractions.
- **One owner per responsibility.** Shared behavior belongs in a composable,
  service, store, or component, not copy-pasted across screens.
- **No silent magic.** If something is inferred, cached, retried, synced, or
  automated, it must be visible in logs/devtools and explainable in code.
- **Debug paths are product paths.** Empty, error, loading, offline, permission,
  and partial-data states must look intentional.
- **Polish is systematic.** Spacing, typography, icons, motion, contrast, and
  responsive behavior should come from shared rules, not one-off tweaking.
- **Professional UI is quiet and useful.** Avoid decorative clutter. Make the app
  feel calm, capable, and sellable.
- **Every refactor needs a safety net.** Add or adjust tests around changed
  behavior.

---

# Tier P4-A - System Understanding

## P4-01 - Architecture Map and Codebase Tour

```
Create a clear architecture map for DiscountDora so a developer can understand
the codebase without spelunking through every folder.

READ FIRST:
- Repo root structure.
- web_app/src.
- dora_api.
- merchant_api.
- emailer.
- compose.yml / Docker files.
- Existing README, CONTRIBUTING, and docs.
- PROMPT_PLAN.md through PROMPT_PLAN_PART_3.md if present.

CREATE:
1. docs/dev/ARCHITECTURE.md

CONTENT:
1. High-level system diagram:
   - web app
   - dora_api
   - merchant_api
   - emailer
   - database/storage/cache
   - background jobs/scrapers if present
2. Request flow examples:
   - Add item to shopping list
   - Finish shopping
   - Dora asks a data question
   - Merchant product search
   - Receipt import if present
3. Frontend structure:
   - pages
   - components
   - composables
   - stores
   - API clients
   - router/layouts
4. Backend structure:
   - routers
   - schemas
   - services
   - repositories/models
   - auth/permissions
   - config
5. Data ownership:
   - Which service owns which data.
   - Which tables/entities are user/household-scoped.
6. Extension guide:
   - Where to add a new page.
   - Where to add a new endpoint.
   - Where to put shared frontend behavior.
   - Where to put domain logic.

DEFINITION OF DONE:
- A new contributor can read ARCHITECTURE.md and know where to start.
- README or CONTRIBUTING links to it.
- CHANGELOG entry under [Unreleased].
```

## P4-02 - Domain Glossary and Naming Cleanup

```
Make the domain language consistent and human-readable across code, UI, docs,
and API names.

READ FIRST:
- Existing models/schemas for stock items, products, shopping lists, recipes,
  meals, meal plans, locations, alerts, Dora suggestions, receipts.
- UI labels in web_app/src.
- API route names.
- CHANGELOG terminology.

CREATE:
1. docs/dev/DOMAIN_GLOSSARY.md

CONTENT:
For each core concept, define:
- User-facing name.
- Code name.
- Short definition.
- Examples.
- What it is not.

AUDIT:
1. Find inconsistent naming:
   - pantry vs stock
   - stock item vs product
   - merchant product vs saved product
   - location vs store section
   - alert vs suggestion
   - meal vs recipe vs planned meal
2. Produce a rename plan.
3. Apply low-risk frontend label cleanups immediately.
4. For code/API renames, only make safe local changes unless the project is
   clearly pre-release and tests can be updated.

RULES:
- UI should use friendly names.
- Code should use precise names.
- Avoid leaking persistence concepts like IDs into domain language.
- Avoid abbreviations unless already universal.

DEFINITION OF DONE:
- DOMAIN_GLOSSARY.md exists.
- UI labels use consistent product language.
- Rename plan exists for deeper code/API inconsistencies.
- CHANGELOG entry under [Unreleased].
```

---

# Tier P4-B - Clean Architecture and Readability

## P4-03 - Frontend Boundary Cleanup

```
Clean up frontend boundaries so pages stay readable and shared behavior is easy
to find.

READ FIRST:
- web_app/src/pages.
- web_app/src/components.
- web_app/src/composables.
- web_app/src/stores.
- web_app/src/api or equivalent API client location.
- Existing lint/typecheck setup.

TARGET STRUCTURE:
1. Pages:
   - Own layout composition and route-specific orchestration.
   - Should not contain large API/data transformation logic.
2. Components:
   - Present reusable UI.
   - Emit clear events.
   - Do not know unrelated route details.
3. Composables:
   - Own reusable interaction logic.
   - Examples: useQuickAdd, useStockItemActions, useShoppingListExport.
4. Stores:
   - Own shared state and caching.
   - Avoid becoming dumping grounds for domain rules.
5. API clients:
   - Own HTTP calls and response typing.
   - No direct fetch/axios calls scattered through pages.

BUILD:
1. Audit the five largest Vue pages by line count and complexity.
2. For each, identify:
   - API logic to extract
   - repeated UI to componentize
   - repeated actions to composables
   - dead code
3. Refactor at least three high-impact pages.
4. Add docs/dev/FRONTEND_PATTERNS.md with examples.

DEFINITION OF DONE:
- Pages are shorter and easier to scan.
- No behavior regressions.
- Typecheck/lint pass.
- CHANGELOG entry under [Unreleased].
```

## P4-04 - Backend Service Layer Cleanup

```
Make backend code easier to debug by separating routing, validation, permissions,
domain logic, and persistence.

READ FIRST:
- dora_api route files.
- merchant_api route files.
- Existing models/schemas/services.
- Tests.

TARGET PATTERN:
1. Router:
   - Parse request.
   - Check auth/permissions.
   - Call service.
   - Return typed response.
2. Schema:
   - Validate input/output.
3. Service:
   - Own domain behavior and transactions.
4. Repository/query helpers:
   - Own database access.
5. Background task/job:
   - Own long-running work.

BUILD:
1. Pick the three messiest/highest-change backend areas:
   - likely shopping lists
   - stock items
   - Dora assistant
   - receipts/forecasting if present
2. Extract service functions with clear names.
3. Move repeated permission checks into helpers.
4. Ensure service functions are unit-testable without HTTP.
5. Add docs/dev/BACKEND_PATTERNS.md with examples.

DEFINITION OF DONE:
- Selected routers are thinner.
- Domain logic has unit tests.
- Error responses stay consistent.
- CHANGELOG entry under [Unreleased].
```

## P4-05 - Dead Code, Duplication, and Dependency Audit

```
Remove clutter that makes DiscountDora harder to maintain.

READ FIRST:
- package.json and lockfile.
- Python requirements/pyproject files.
- web_app/src.
- dora_api, merchant_api, emailer.
- Existing test and build scripts.

AUDIT:
1. Dead frontend components.
2. Dead routes/pages.
3. Dead composables/stores.
4. Unused backend routes/functions.
5. Duplicate helper functions.
6. Duplicate CSS/classes/tokens.
7. Unused npm and Python dependencies.
8. Large dependencies used for tiny jobs.

BUILD:
1. Remove safe dead code.
2. Consolidate obvious duplicates.
3. Document risky removals in docs/dev/CLEANUP_BACKLOG.md instead of guessing.
4. Update imports/tests.
5. Run lint/typecheck/tests.

DEFINITION OF DONE:
- Safe dead code is removed.
- Cleanup backlog exists for uncertain cases.
- Dependency list is leaner or documented.
- CHANGELOG entry under [Unreleased].
```

---

# Tier P4-C - Debuggability and Diagnostics

## P4-06 - Developer Diagnostics Panel

```
Add a development-only diagnostics panel so debugging Dora does not require
guessing what the frontend thinks is happening.

READ FIRST:
- App layout and dev/prod config.
- Pinia/store setup.
- API client.
- Offline queue F3 if present.
- Dora assistant state.
- Auth/session handling.

FRONTEND:
1. Add a dev-only diagnostics panel, hidden in production builds.
2. Open with keyboard shortcut, e.g. Ctrl+Alt+D.
3. Show:
   - Current user/session summary.
   - Current route and query params.
   - API base URLs.
   - Online/offline state.
   - Pending offline queue mutations.
   - Last 20 API calls with status/duration.
   - Active stores and key counts.
   - Dora assistant mode/model status.
   - Feature flags/config.
4. Add copy-debug-report button:
   - Copies redacted JSON summary.

SECURITY:
- Never show tokens, passwords, API keys, or private secrets.
- Guard by dev env only.

DEFINITION OF DONE:
- Dev panel helps diagnose common state/API issues.
- It is absent from production builds.
- CHANGELOG entry under [Unreleased].
- Tests or build checks ensure production does not include it.
```

## P4-07 - Structured Errors and Friendly Failure States

```
Make errors easier for developers to trace and easier for users to survive.

READ FIRST:
- API error handling.
- Frontend API client.
- Notify/Confirm primitives F4.
- Offline/error boundary F3.
- Logging strategy I1+I2.

BACKEND:
1. Standardize error shape:
   {
     "error": {
       "code": "stock_item.not_found",
       "message": "Human-readable summary",
       "details": {},
       "request_id": "..."
     }
   }
2. Add request_id to every response and log entry.
3. Ensure validation errors map to readable messages.
4. Ensure permission errors are distinct from not-found where safe.

FRONTEND:
1. API client parses standard errors.
2. User notifications use friendly messages.
3. Dev console/diagnostics panel includes request_id.
4. Error states are designed components, not raw stack traces.
5. Add retry actions for transient failures.

DEFINITION OF DONE:
- Common errors have stable codes.
- Users see friendly failure states.
- Developers can trace a UI error to backend logs using request_id.
- CHANGELOG entry under [Unreleased].
- Tests cover standard error response shape.
```

---

# Tier P4-D - Frontend Consistency and Polish

## P4-08 - Design System Completion Pass

```
Finish the practical design system so the UI looks intentional everywhere.

READ FIRST:
- DS1 Design tokens.
- DS2 Icon audit.
- DS4 Animation library.
- Existing CSS/SCSS.
- Quasar theme configuration.
- Major pages and shared components.

BUILD:
1. Create or complete tokens for:
   - spacing
   - radii
   - shadows
   - typography
   - color roles
   - border colors
   - focus states
   - motion durations/easing
2. Replace one-off magic values in major components with tokens.
3. Define density rules:
   - daily tools compact but breathable
   - cards <= 8px radius unless existing system says otherwise
   - no nested cards
   - no decorative clutter
4. Define component standards:
   - page header
   - toolbar
   - empty state
   - list row
   - chip
   - side panel
   - modal/sheet
   - table
   - status/alert
5. Add docs/dev/UI_SYSTEM.md with examples.

DEFINITION OF DONE:
- Major pages use consistent spacing, type, and component patterns.
- UI_SYSTEM.md documents the rules.
- CHANGELOG entry under [Unreleased].
```

## P4-09 - UI Copy and Microcopy Polish

```
Polish the words in DiscountDora so it feels calm, helpful, and professional.

READ FIRST:
- All visible strings in web_app/src.
- Empty states F2.
- Alerts P13.
- Dora assistant copy.
- Help docs Doc4.
- Product constitution P3-01.

VOICE:
- Plain.
- Brief.
- Helpful.
- Not cutesy.
- Not technical unless the user is in an advanced/dev/admin area.
- Avoid blame or shame around waste, missed shopping, or stale data.

AUDIT:
1. Button labels.
2. Empty states.
3. Error messages.
4. Confirmation dialogs.
5. Dora messages.
6. Form labels/help text.
7. Settings descriptions.
8. Onboarding copy.

BUILD:
1. Create docs/product/VOICE_AND_COPY.md.
2. Rewrite rough or inconsistent copy.
3. Make destructive actions explicit.
4. Make automated actions understandable.
5. Remove explanatory paragraphs from daily UI where concise labels/actions are
   enough.

DEFINITION OF DONE:
- Copy feels consistent and professional.
- Empty/error states are useful and short.
- CHANGELOG entry under [Unreleased].
```

## P4-10 - Accessibility and Keyboard Polish

```
Make the app feel professionally built by tightening accessibility, focus, and
keyboard behavior.

READ FIRST:
- S5 Keyboard shortcuts.
- Major pages/components.
- Quasar accessibility patterns.
- Existing tests.

BUILD:
1. Audit:
   - semantic headings
   - labels
   - button names
   - focus order
   - modal focus trap
   - color contrast
   - keyboard reachability
   - reduced motion
   - screen reader text for icon-only controls
2. Fix high-impact issues.
3. Add axe/playwright accessibility checks for key pages:
   - Today/Dashboard
   - Pantry
   - Shopping List Detail
   - Recipes
   - Settings
   - Dora panel
4. Ensure command palette and shortcuts do not trap users.

DEFINITION OF DONE:
- Key flows are keyboard usable.
- Axe checks pass for major pages.
- Focus states look intentional.
- CHANGELOG entry under [Unreleased].
```

---

# Tier P4-E - Visual QA and Professional Finish

## P4-11 - Visual QA Sweep with Screenshots

```
Run a professional visual QA pass across the app using Playwright screenshots.

READ FIRST:
- E2E setup.
- Major routes.
- Existing screenshot or visual regression tooling.
- UI_SYSTEM.md from P4-08.

VIEWPORTS:
- Mobile narrow.
- Tablet.
- Desktop.
- Wide desktop.

PAGES:
- Today/Dashboard
- Pantry/Stock Overview
- Stock Item Detail
- Locations
- Shopping Lists Overview
- Shopping List Detail
- Recipes Overview
- Recipe Detail
- Cook Mode
- Meal Plans
- Product Search
- My Products
- Alerts
- Dora panel
- Settings
- Data Management
- Reports/advanced tools if present

CHECK FOR:
- Text overflow.
- Awkward empty space.
- Inconsistent spacing.
- Misaligned icons/buttons.
- Dense tables where cards/lists would be clearer.
- Poor mobile layout.
- Nested cards.
- Low contrast.
- Overly decorative or amateur-looking areas.
- Loading/empty/error states.

BUILD:
1. Add visual QA script:
   - Seeds representative data.
   - Opens each page.
   - Captures screenshots per viewport.
2. Create docs/qa/VISUAL_QA_REPORT.md:
   - Screenshot index.
   - Findings.
   - Fix list.
3. Fix the top visual issues discovered.

DEFINITION OF DONE:
- Screenshots exist for major pages/viewports.
- Top polish issues are fixed.
- Report documents remaining lower-priority issues.
- CHANGELOG entry under [Unreleased].
```

## P4-12 - Professional UI Polish Pass

```
Apply a final design polish pass so DiscountDora looks like a sellable product.

READ FIRST:
- VISUAL_QA_REPORT.md from P4-11.
- UI_SYSTEM.md from P4-08.
- Product constitution P3-01.
- Existing brand/logo/mascot assets.

POLISH AREAS:
1. App shell:
   - Navigation hierarchy.
   - Header density.
   - Mobile nav.
   - Active states.
2. Page headers:
   - Consistent title, subtitle, primary action, secondary actions.
3. Lists and rows:
   - Alignment.
   - Tap targets.
   - Hover/focus states.
   - Status chips.
4. Forms/sheets:
   - Label clarity.
   - Error placement.
   - Primary action alignment.
5. Empty states:
   - Helpful, compact, action-oriented.
6. Loading states:
   - Skeletons instead of layout jumps.
7. Dora assistant:
   - Panel polish.
   - Message spacing.
   - Quick-action chip styling.
8. Mobile:
   - No cramped controls.
   - Sticky actions where useful.
   - No horizontal overflow.

STYLE RULES:
- Quiet, capable, modern.
- Avoid novelty visuals.
- Avoid overusing brand mascot.
- Avoid one-note color palettes.
- Use icons consistently.
- Keep cards restrained.

DEFINITION OF DONE:
- Major screens feel visually cohesive.
- Mobile and desktop both look intentional.
- No obvious "student project" rough edges remain in daily flows.
- CHANGELOG entry under [Unreleased].
```

---

# Tier P4-F - Developer Workflow

## P4-13 - One-Command Local Development

```
Make it easy to run DiscountDora locally without remembering a pile of commands.

READ FIRST:
- README.
- CONTRIBUTING.
- package.json scripts.
- Python env setup.
- compose.yml / compose.override.yml.
- .env.example.

BUILD:
1. Add a single documented dev startup command.
   Examples:
   - `make dev`
   - `npm run dev:all`
   - `docker compose up`
   Pick the style that best fits the repo.
2. It should start:
   - web app
   - dora_api
   - merchant_api if needed
   - emailer if needed
   - database/cache dependencies
3. Add health check output:
   - web URL
   - API URL
   - docs URL
   - common troubleshooting hints
4. Add seed command:
   - Creates realistic demo data.
   - Safe to rerun in dev.
5. Add reset command:
   - Clearly dev-only.
   - Requires confirmation or obvious dev env.

DEFINITION OF DONE:
- A developer can clone, configure, seed, and run the app from README steps.
- Common startup failures have clear messages.
- CHANGELOG entry under [Unreleased].
```

## P4-14 - Quality Gate Command

```
Create one command that answers: "Is this branch healthy enough to hand to
someone else?"

READ FIRST:
- Existing lint/typecheck/test/build scripts.
- CI pipeline D4.
- E2E setup.
- Visual QA scripts if present.

BUILD:
1. Add a single local quality command:
   - frontend lint
   - frontend typecheck
   - frontend unit tests
   - frontend build
   - backend lint/format check
   - backend typecheck if available
   - backend tests
   - optional E2E smoke
2. Make output readable:
   - Section headings.
   - Clear pass/fail.
   - Stops on critical failures unless --continue is passed.
3. Document:
   - Quick check for everyday work.
   - Full check before PR/release.
4. Align CI with the same commands where possible.

DEFINITION OF DONE:
- One command runs the standard quality gate.
- README/CONTRIBUTING documents it.
- CI and local checks do not drift.
- CHANGELOG entry under [Unreleased].
```

---

# Tier P4-G - Final Release Readiness

## P4-15 - Release Candidate Polish Checklist

```
Create and run a release-candidate checklist for DiscountDora that covers
developer quality, product polish, and real user flows.

READ FIRST:
- CHANGELOG.md.
- README/CONTRIBUTING/docs.
- E2E tests.
- Visual QA report.
- Dora product constitution.
- Complexity budget.
- Ease score if implemented.

CREATE:
1. docs/release/RELEASE_CANDIDATE_CHECKLIST.md

CHECKLIST SECTIONS:
1. Product fit:
   - Fast paths still fast.
   - Advanced tools not dominant.
   - No data-for-data's-sake features visible in daily flows.
2. Core user flows:
   - Add item.
   - Generate list.
   - Shop and finish.
   - Stock update.
   - Recipe/cook flow.
   - Dora assistant.
3. Visual polish:
   - Mobile.
   - Desktop.
   - Empty/loading/error states.
   - Dark/light mode if supported.
4. Developer readiness:
   - One-command dev works.
   - Quality gate passes.
   - Logs/errors have request IDs.
   - Architecture docs are current.
5. Deployment:
   - Docker compose clean start.
   - Volumes/config documented.
   - Health checks.
6. Data safety:
   - Backup/restore.
   - Import/export.
   - Undo/destructive confirmations.
7. Accessibility:
   - Keyboard flows.
   - Contrast.
   - Screen reader basics.
8. Release notes:
   - Changelog updated.
   - Known limitations documented.

RUN:
- Execute the checklist once.
- Create docs/release/RC_FINDINGS.md with findings and fixes.
- Fix the highest-priority issues discovered.

DEFINITION OF DONE:
- Release checklist exists.
- RC findings are documented.
- Top blockers are fixed or explicitly deferred.
- CHANGELOG entry under [Unreleased].
```

---

# Notes

This plan is deliberately not about adding major product features. It is about
making DiscountDora feel like a tool someone could trust:

- clean to read
- easy to run
- easy to debug
- hard to accidentally break
- visually coherent
- calm in failure
- polished in the hands

The goal is not perfection for its own sake. The goal is that both the user and
the developer feel the same thing:

> Dora is doing the work with me, not making work for me.
