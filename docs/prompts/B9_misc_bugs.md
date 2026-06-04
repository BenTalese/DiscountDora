# B9 — Misc global bugs (small, mostly independent)

**Wave:** B · **Risk:** low each · **Depends on:** none (some overlap A1/A8)

## Impact & decisions (read first)
- A checklist of small, concrete bugs that don't need a redesign. Run as a batch or pick individually. A couple touch areas you deferred (settings/dashboard) but are **global-nav** fixes, not redesigns — included. Skip any you'd rather defer.
- **Decision:** confirm you're OK fixing the two nav items that touch deferred areas (settings duplicated in menu; main-menu hover outline).

---

## PROMPT (checklist — fix each, read current code first)

In a Vue 3 + Quasar SPA (`web_app/`) + Python backend, fix the following. For each, locate the cause in the live code, fix, and verify.

1. **Shopping-list detail drag-drop off-by-one** — reordering swaps the *wrong* items (index misalignment between the rendered list and the reorder payload). Fix the index mapping; verify the dragged item lands exactly where dropped.
2. **Main-menu inactive hover = double outline**, active = single. Make inactive hover a single outline to match.
3. **Settings appears in BOTH the main menu and the user dropdown** — remove it from the main menu (keep in the dropdown).
4. **Command palette (Ctrl+K)** doesn't trigger some actions (e.g. "create stock item"). Find the palette command registry; wire the missing/ broken commands.
5. **Cross-app undo inconsistency** — e.g. push expiry on dashboard, then clear expiry on the stock item: the undo stack behaves oddly. Investigate the undo registration across surfaces; ensure undo entries are scoped/invalidated correctly (don't undo into stale state).
6. **Product history:** selecting a product produces no change on the page; the price-history graph doesn't extend to the box edge; the hover bubble isn't theme-aware (white-on-white in dark). Fix selection→chart binding, chart sizing, and tooltip theming (use tokens).
7. **Logs not rolling** — current api log is ~46k lines spanning the wrong date range (likely since the `.local` move). Check the logging handler config (rotation size/time, path); make logs roll properly. (Note `.local` folder layout question is in INV.)
8. **Floating Dora disappears in mobile login view**; **Dora image off-centre** over its background box on Product Search (pre-search/no-results) and the Dashboard greeting card. Fix placement/centering responsively.
9. **404 page** uses the default Quasar styling — re-skin to the app theme (tokens).

### Verify
Each item: reproduce → fix → confirm. For #5 (undo) and #7 (logs), report findings if the fix needs a decision.

Output: per item — cause + fix + verification, and flag any that turned out larger than a quick fix.
