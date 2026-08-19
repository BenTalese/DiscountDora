// Per-user "should I buy this?" display opt-out.
//
// D-12 (`IMPL_PLAN_STOCK_SIGNAL_CONSOLIDATION.md`, 2026-08-19): this used to
// read `features.buy_verdict` off GET /api/health, backed by the install-wide
// `AppSetting.buy_verdict_enabled`. That was the wrong scope for a pure display
// overlay — one person hiding a badge hid it for the whole household (B7). The
// flag now lives on the user, beside `inferred_pantry_enabled`, and rides
// /auth/me like every other personal display preference. Same shape as
// `useImagePrefs`; no install-wide layer, because this is not a
// feature-availability gate.
//
// The module-level probe + `refreshBuyVerdict` are gone with the health flag:
// the auth store already owns the user's freshness, so there is nothing
// separate to re-probe. Callers that flip the toggle go through
// `authStore.updateMeAsync`, which updates the in-memory user, and every
// consumer of this computed repaints from that.

import { computed } from 'vue';
import { storeToRefs } from 'pinia';
import { useAuthStore } from 'src/stores/authStore';

export function useBuyVerdictEnabled() {
    const { currentUser } = storeToRefs(useAuthStore());

    // Defaults to **true** while the user is still loading: the verdict is a
    // pure-personal feature with no external surface to disable, so on is the
    // honest default and a first paint that shows it beats one that flashes it
    // in a moment later.
    const buyVerdictEnabled = computed(
        () => currentUser.value?.buy_verdict_enabled ?? true,
    );

    return { buyVerdictEnabled };
}
