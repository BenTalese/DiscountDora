// FU-615 — batch cook-style is now an install-wide setting (a household has
// one cook-style), read from /api/health via `useCookingPolicy`. This thin
// wrapper is kept so the meal-planner components that read `batchEnabled`
// don't all have to change their import. There is no `setBatchEnabled` any
// more — the value is edited by an admin in Settings → System → Cooking
// (PATCH /app-settings), not per-user.
//
// When True ("batch"), the meal-planner reveals the cook-pool affordances
// (per-recipe ± / log-cook / "n free"), the shortfall warning, and the
// "to cook by" sidebar line. Default False ("fresh") — Charter P10 Anti-creep.

import { useCookingPolicy } from 'src/composables/useCookingPolicy';

export function useBatchEnabled() {
    const { batchEnabled } = useCookingPolicy();
    return { batchEnabled };
}
