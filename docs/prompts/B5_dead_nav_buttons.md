# B5 — Dead navigation buttons (onboarding, dashboard, alerts→404)

**Wave:** B · **Risk:** low · **Depends on:** none

## Impact & decisions (read first)
- Cluster of buttons that do nothing / 404:
  - Onboarding: **Skip everything**, **Finish**, and the **"Show me X"** cards at the finish screen — no navigation.
  - Dashboard: skipped-setup **Continue** button — does nothing.
  - **Alerts → 404** (from dashboard alert card / bell).
- Scope here is **just the navigation wiring** — not the onboarding redesign (big rock) or the alerts control centre (big rock). Make the existing buttons go somewhere sensible now; full redesign later.
- **Decision:** for Alerts, a real alerts page is a big-rock (C). Short-term: point the alert nav at a **minimal working alerts view or the closest existing surface**, not 404. Confirm you want the stopgap, or to leave Alerts for C only.

---

## PROMPT

Fix dead/broken navigation in a Vue 3 + Quasar SPA (`web_app/`).

### 1. Locate (read current code)
- Onboarding skip-everything, finish, and finish-screen "Show me X" cards: find their click handlers / missing routes.
- Dashboard "Continue" (skipped-setup banner).
- Alerts navigation target (dashboard alert card + top-bar bell) that 404s.

### 2. Fix wiring
- Onboarding **Skip** and **Finish**: navigate to the dashboard (and persist onboarding-complete on Finish). "Show me X" cards: route to the relevant feature page each names.
- Dashboard **Continue**: route into the resume point of onboarding (or dismiss + go to the relevant setup), per current intent.
- **Alerts:** stopgap — route to a minimal alerts list (or nearest existing surface) instead of 404. Note clearly that the full alerts control centre is the C-wave design brief; don't build it here.

### 3. Verify
- Every listed button navigates correctly; onboarding Finish marks completion; no 404.

Output: each button → handler/route fixed; what Alerts was pointed at as a stopgap; confirmation onboarding completion persists.
