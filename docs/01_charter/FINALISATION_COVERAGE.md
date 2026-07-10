# Finalisation Coverage Register

Companion to [FINALISATION_PLAN.md](FINALISATION_PLAN.md). This is the
single source of truth for "what has been walked, what hasn't". Update it
every session — the plan is only credible if this table stays honest.

**Legend (per cell):**

- ⬜ not started
- 🟡 in progress (partial)
- ✅ done
- ➖ N/A for this chunk (with reason in the notes)

**Track columns:**

- **FST** — rows added to [../04_proposals/FULL_SYSTEMS_TEST.md](../04_proposals/FULL_SYSTEMS_TEST.md).
- **Help** — content added to `HelpPage.vue` / `(?)` chips / DoraBot corpus.
- **Review** — section added to [../05_investigations/FINALISATION_REVIEW.md](../05_investigations/FINALISATION_REVIEW.md).
- **Tests** — rows added to [../04_proposals/TEST_PLAN_INVENTORY.md](../04_proposals/TEST_PLAN_INVENTORY.md).

**Coverage matrix:**

| # | Chunk | FST | Help | Review | Tests | Session | Notes |
|---|---|---|---|---|---|---|---|
| 1 | Cookbook | ⬜ | ⬜ | ⬜ | ⬜ | — | |
| 2 | Meal Plans | ⬜ | ⬜ | ⬜ | ⬜ | — | |
| 3 | Shopping Lists | ⬜ | ⬜ | ⬜ | ⬜ | — | |
| 4 | Cook Mode | ⬜ | ⬜ | ⬜ | ⬜ | — | |
| 5 | Stock Overview + Stocktake | ⬜ | ⬜ | ⬜ | ⬜ | — | |
| 6 | Stock-Item Detail | ⬜ | ⬜ | ⬜ | ⬜ | — | |
| 7 | Zero-Input Pantry (P8-07) | ⬜ | ⬜ | ⬜ | ⬜ | — | |
| 8 | Dashboard | ⬜ | ⬜ | ⬜ | ⬜ | — | |
| 9 | Alerts + Suggestions | ⬜ | ⬜ | ⬜ | ⬜ | — | |
| 10 | Products / History / Deals | ⬜ | ⬜ | ⬜ | ⬜ | — | |
| 11 | Assistant (Dora) | ⬜ | ⬜ | ⬜ | ⬜ | — | |
| 12 | Reports / Memory (P8-09) | ⬜ | ⬜ | ⬜ | ⬜ | — | |
| 13 | Settings shell | ⬜ | ⬜ | ⬜ | ⬜ | — | |
| 14 | Onboarding | ⬜ | ⬜ | ⬜ | ⬜ | — | |
| 15 | Auth shell | ⬜ | ⬜ | ⬜ | ⬜ | — | |
| 16 | Ingestion API + companion seam | ⬜ | ⬜ | ⬜ | ⬜ | — | |
| 17 | Offline / PWA / native | ⬜ | ⬜ | ⬜ | ⬜ | — | |
| 18 | Backup & restore + Import | ⬜ | ⬜ | ⬜ | ⬜ | — | |
| 19 | Ops / self-host | ⬜ | ⬜ | ⬜ | ⬜ | — | |
| 20 | Cross-cutting concerns | ⬜ | ⬜ | ⬜ | ⬜ | — | |

**Closing checklist (see PLAN §7):**

- ⬜ FST document walked end-to-end on a near-final build by the user.
- ⬜ Release-gate checklist green.
- ⬜ Help content deployed (HelpPage + `(?)` chips + DoraBot).
- ⬜ Senior review triaged — every finding actioned or waived.
- ✅ FU-361, FU-320, FU-395 archived to `DORA_FOLLOWUPS_RESOLVED.md` (done 2026-07-10 at plan draft; this plan is their sole tracker).
- ⬜ FU-510 Phase 1 state note; Phase 2 kept open.
- ⬜ FU-406 + FU-404 state notes on partial coverage.
- ⬜ PROJECT_STATE workstream row promoted to "recently shipped".
