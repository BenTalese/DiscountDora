// Per-user "should I buy this?" display opt-out.
//
// D-12 (`IMPL_PLAN_STOCK_SIGNAL_CONSOLIDATION.md`, 2026-08-19): this used to
// read `features.buy_verdict` off GET /api/health, backed by the install-wide
// `AppSetting.buy_verdict_enabled`. That was the wrong scope for a pure display
// overlay — one person hiding a badge hid it for the whole household (B7). The
// flag now lives on the user, beside `inferred_pantry_enabled`, and rides
// /auth/me like every other personal display preference. No install-wide
// layer, because this is not a feature-availability gate.
//
// The module-level probe + `refreshBuyVerdict` are gone with the health flag:
// the auth store already owns the user's freshness, so there is nothing
// separate to re-probe. Callers that flip the toggle go through
// `authStore.updateMeAsync`, which updates the in-memory user, and every
// consumer of this computed repaints from that.

import { computed } from 'vue';
import { storeToRefs } from 'pinia';
import { useAuthStore } from 'src/stores/authStore';
import { useMoneyEnabled } from 'src/composables/useMoneyEnabled';

export function useBuyVerdictEnabled() {
    const { currentUser } = storeToRefs(useAuthStore());
    const { moneyEnabled } = useMoneyEnabled();

    // The per-user half defaults to **true** while the user is still loading:
    // it is a pure display opt-out, so on is the honest default and a first
    // paint that shows the verdict beats one that flashes it in a moment later.
    const userOptedIn = computed(
        () => currentUser.value?.buy_verdict_enabled ?? true,
    );

    // Money is a **prerequisite**, not a co-equal toggle (owner call
    // 2026-08-27). The verdict reasons in money — the price axis is money, the
    // `wait` direction is only reachable from a price signal, and price
    // modulates strength — so an install with money off has no honest verdict
    // to show, only need + waste, which `PantryBeliefCard` already says.
    // Server refuses these endpoints outright too; this is the render gate.
    //
    // Unlike the user half, this does NOT default on: `moneyEnabled` reads
    // false until the health probe lands, matching every other dollar surface
    // in the app (StockOverview, ShoppingListDetail). A verdict that appears a
    // beat late is right; one that flashes up on a money-off install is not.
    const buyVerdictEnabled = computed(
        () => moneyEnabled.value && userOptedIn.value,
    );

    return { buyVerdictEnabled, moneyEnabled, userOptedIn };
}
