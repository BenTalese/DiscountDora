# A8 — Renames + remove refresh buttons + nav-state policy

**Wave:** A · **Risk:** low (mechanical) but wide · **Depends on:** none (do after naming decisions)

## Impact & decisions (read first)
Three small mechanical passes bundled. **Confirm the names before running — these are product decisions:**
- **App name:** Discount Dora → **Dashy Dora** everywhere (UI strings, titles, manifest, emails, docs). Confirm scope incl. PWA manifest / window title / email templates.
- **Bot name:** Dorabot → **D.O.R.A.** (Delicious Organised Restock Assistant)? Confirm final form.
- **"Mark made" → "Mark cooked"** everywhere.
- **Recipes page → "Cookbook"** wherever the *page* is named (routes/labels/help). Confirm whether the URL/route changes too or just the label.
- Nav-state policy needs a decision (below).

---

## PROMPT (run as three sections; can split)

### Section 1 — Rename pass
In a Vue 3 + Quasar SPA (`web_app/`) + backend strings:
- Replace user-facing "Discount Dora" / "DiscountDora" with **Dashy Dora** (keep code identifiers/package names unless trivial). Cover: UI copy, page titles, PWA manifest, email templates, About/help.
- "Mark made" → "Mark cooked" in all UI + any related tooltips/toasts.
- Recipes page label → "Cookbook" (label/help; change route only if I confirm).
- Bot → "D.O.R.A." in chat header/labels (confirm final form first).
- List every changed string location. Don't rename DB columns/enums.

### Section 2 — Remove refresh buttons
- Find manual "refresh" buttons (dashboard, my products, stocktake, anywhere). Remove them where the data already refreshes on navigation; if a screen genuinely needs manual refresh, list it and ask before removing. Ensure on-navigation refresh is actually happening for the screens whose button you remove.

### Section 3 — Navigation-state policy
- **Decision needed:** when navigating away and back to a list page, should filters/search/sort/scroll **persist** or **reset**? Propose one consistent rule (suggest: filters/sort persist within a session; reset on full reload), then apply it uniformly. Today it's partial/inconsistent (e.g. product search keeps some state).

Output per section: changed locations, anything that needed a judgment call, and confirmation of the chosen nav-state rule applied everywhere.
