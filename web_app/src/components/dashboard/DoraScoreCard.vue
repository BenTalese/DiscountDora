<template>
    <!-- dashboard's kitchen-health card. Reads the composite +
         five-component breakdown from `useDoraScore()`; renders each
         component as a mini-bar chip that links to a remediating
         action (charter: every weak component should nudge toward the
         feature that improves it, never shame). -->
    <DashboardCard :icon="ICONS.favorite">
        <template #title>
            Kitchen health
            <InfoTip label="Kitchen health">
                A 0–100 score of how your kitchen's tracking right now — waste,
                on-budget, freshness, unplanned run-outs, and stocktake staleness,
                averaged. Only signals with real data count; missing signals
                don't drag the score down.
            </InfoTip>
        </template>
        <template #action>
            <span
                v-if="score && score.trend_direction && score.trend_direction !== 'flat'"
                class="dora-score-trend"
                :class="`dora-score-trend--${score.trend_direction}`"
                :aria-label="trendAriaLabel"
            >
                <q-icon :name="trendIcon" size="16px" />
                <span class="dora-score-trend__delta">
                    {{ score.trend_delta! > 0 ? '+' : '' }}{{ score.trend_delta }}
                </span>
            </span>
        </template>

        <div v-if="loading && !score" class="dora-text-muted text-caption">
            Loading…
        </div>

        <div v-else-if="!score" class="dora-text-muted text-caption">
            Kitchen health will appear here once you've been using
            Dora for a bit.
        </div>

        <div v-else-if="score.composite === null" class="dora-text-muted text-caption">
            Kitchen health appears once you've tracked a few stock
            items — nothing to score yet.
        </div>

        <template v-else>
            <div class="dora-score-hero">
                <div class="dora-score-hero__number">{{ score.composite }}</div>
                <div class="dora-score-hero__caption">
                    <div>out of 100</div>
                    <div class="text-caption dora-text-muted">
                        last {{ score.window_days }} days
                    </div>
                </div>
            </div>

            <ul class="dora-score-components">
                <li
                    v-for="c in score.components"
                    :key="c.key"
                    class="dora-score-component"
                    :class="{ 'dora-score-component--dormant': c.score === null }"
                >
                    <div class="dora-score-component__head">
                        <span class="dora-score-component__label">{{ c.label }}</span>
                        <span class="dora-score-component__score">
                            {{ c.score === null ? '—' : c.score }}
                        </span>
                    </div>
                    <div
                        v-if="c.score !== null"
                        class="dora-score-component__bar"
                        :aria-label="`${c.label} score ${c.score} out of 100`"
                    >
                        <div
                            class="dora-score-component__bar-fill"
                            :style="{ width: `${c.score}%` }"
                            :class="barClass(c.score)"
                        />
                    </div>
                    <div class="dora-score-component__foot">
                        <span class="dora-score-component__reason">{{ c.reason }}</span>
                        <router-link
                            v-if="actionLinkFor(c.key)"
                            :to="actionLinkFor(c.key)!.to"
                            class="dora-score-component__action"
                        >
                            {{ actionLinkFor(c.key)!.label }} →
                        </router-link>
                    </div>
                </li>
            </ul>
        </template>
    </DashboardCard>
</template>

<script setup lang="ts">
    /**
     * P8-08 — Dora Score dashboard card.
     *
     * The component is pure presentation over `useDoraScore()`:
     * loading, empty (brand-new install, no data), zero-scoring, and
     * the full breakdown all live here. The composable owns caching
     * (5-min stale window) and fetch orchestration; this file only
     * renders what it hands back.
     *
     * Component→action links are hardcoded here rather than server-
     * assigned because the routes are SPA-owned identifiers, not
     * kitchen-health facts. If the routes ever move, this is the one
     * place to touch. Charter P1 Effortless: every weak component
     * points at the feature that improves it (waste → waste page,
     * budget → preferences, freshness → filtered stock view,
     * run-outs → shopping lists, stocktake → filtered stock view).
     */
    import { computed } from 'vue';
    import DashboardCard from 'src/components/dashboard/DashboardCard.vue';
    import { ICONS } from 'src/style/icons';
    import InfoTip from 'src/components/help/InfoTip.vue';
    import { useDoraScore } from 'src/composables/useDoraScore';
    import { useMoneyEnabled } from 'src/composables/useMoneyEnabled';
    import type {
        DoraScoreComponentKey,
    } from 'src/models/doraScore';

    const { doraScore: score, loading } = useDoraScore();
    // Layers the install flag with the per-user money opt-in — the server's
    // `money_features_enabled` is install-wide only, so a user who personally
    // opted out still needs the render-side guard (FU-823).
    const { moneyEnabled } = useMoneyEnabled();

    const trendIcon = computed(() => {
        if (score.value?.trend_direction === 'up') return ICONS.trending_up;
        if (score.value?.trend_direction === 'down') return ICONS.trending_down;
        return ICONS.trending_flat;
    });

    const trendAriaLabel = computed(() => {
        const s = score.value;
        if (!s || s.trend_delta === null) return '';
        return s.trend_delta > 0
            ? `Up ${s.trend_delta} points from a week ago`
            : `Down ${Math.abs(s.trend_delta)} points from a week ago`;
    });

    function barClass(v: number): string {
        // Traffic-light banding for the mini-bar fills — the composite
        // number is honest and the bar is a shape-of-story cue.
        // Server owns the score; the client just paints the tone.
        if (v >= 80) return 'dora-score-component__bar-fill--good';
        if (v >= 50) return 'dora-score-component__bar-fill--fair';
        return 'dora-score-component__bar-fill--weak';
    }

    type ActionLink = { to: string; label: string };
    function actionLinkFor(key: DoraScoreComponentKey): ActionLink | null {
        switch (key) {
            // FU-823 / R-058 — belt and braces on the money gate. The server no
            // longer emits a budget component at all when money features are
            // off, so this branch shouldn't be reachable then; the guard is here
            // because a "Set a budget →" link into /settings/money is the exact
            // leak the FU was about, and a render-side check costs nothing if a
            // future caller ever hands us a component the server didn't gate.
            case 'budget':
                return moneyEnabled.value
                    ? { to: '/settings/money', label: 'Set a budget' }
                    : null;
            case 'waste':
                // No dedicated action link — PROPOSAL_WASTE_MINIMISATION
                // dissolved the /waste page (D10). Users log waste inline
                // via the StockItemRow expiry dropdown's "Mark as wasted"
                // action, and review history per-item on StockItemDetail's
                // History tab; there is no aggregated "waste review" surface
                // to link to. Score row still explains the number, just
                // without a dead button — this is the calm-empty-state
                // pattern, not R-029 hide-when-off.
                return null;
            case 'freshness':
                // Filter stock to expiring / expired items so the user
                // can act. The stock overview reads ?expiring=1.
                return { to: '/stock?expiring=1', label: 'Expiring items' };
            case 'runouts':
                // The primary shopping-list overview is where planned
                // buys land — the answer to "fewer surprise run-outs".
                return { to: '/shopping-lists', label: 'Shopping lists' };
            case 'stocktake':
                // The stocktake page IS the queue. This used to deep-link to
                // the stock overview's "Needs check" chip (?stocktake=1);
                // that chip was retired 2026-08-21, and pointing straight at
                // /stocktake was always the shorter path to the same work.
                return { to: '/stocktake', label: 'Do a stocktake' };
            default:
                return null;
        }
    }
</script>

<style scoped>
    /* R-060 sweep (2026-09-02): every colour in this block used to reference a
       `--dora-*` custom property — `--dora-text`, `--dora-primary`,
       `--dora-positive(-bg)`, `--dora-negative(-bg)`, `--dora-muted-bg`,
       `--dora-text-muted` — and **none of them has ever been declared** (only
       `--dora-disc-bg` and `--dora-halo*` exist). So the card painted from its
       hard-coded hex fallbacks in all ten themes, light and dark: the "fair" bar
       and the action links came out yellow where the app's action colour is
       green, and the bar track was a black wash that disappeared on a dark
       surface. `--dora-text` had no fallback at all, so that declaration was
       invalid and the score's headline number silently inherited.
       Now on the real A1 tokens. This is also the honest close-out of feedback
       D2 ("dark mode not working"), which Phase 0 of the dashboard rebuild
       marked done. */
    .dora-score-hero {
        display: flex;
        align-items: baseline;
        gap: 12px;
        margin-bottom: 12px;
    }

    .dora-score-hero__number {
        font-size: 2.5rem;
        font-weight: 600;
        line-height: 1;
        color: var(--text-primary);
    }

    .dora-score-hero__caption {
        line-height: 1.2;
    }

    .dora-score-trend {
        display: inline-flex;
        align-items: center;
        gap: 2px;
        padding: 2px 6px;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 500;
    }
    /* A1 soft-token rule: a `-soft` token is a background only; the text on it
       takes the full-strength semantic token. */
    .dora-score-trend--up {
        background: var(--semantic-positive-soft);
        color: var(--semantic-positive);
    }
    .dora-score-trend--down {
        background: var(--semantic-negative-soft);
        color: var(--semantic-negative);
    }

    .dora-score-components {
        list-style: none;
        padding: 0;
        margin: 0;
        display: flex;
        flex-direction: column;
        gap: 10px;
    }

    .dora-score-component {
        padding: 0;
    }
    .dora-score-component--dormant {
        opacity: 0.55;
    }

    .dora-score-component__head {
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        margin-bottom: 4px;
    }
    .dora-score-component__label {
        font-weight: 500;
    }
    .dora-score-component__score {
        font-variant-numeric: tabular-nums;
        font-weight: 500;
    }

    .dora-score-component__bar {
        height: 4px;
        border-radius: var(--radius-pill);
        /* A1: an inset well sits on `--surface-sunken`, not a black wash. */
        background: var(--surface-sunken);
        overflow: hidden;
    }
    .dora-score-component__bar-fill {
        height: 100%;
        border-radius: var(--radius-pill);
        transition: width var(--motion-slow) ease-out;
    }
    /* Traffic-light banding straight off A1's semantic table, which names these
       exact roles: positive = "good scores", warning = "fair scores". */
    .dora-score-component__bar-fill--good {
        background: var(--semantic-positive);
    }
    .dora-score-component__bar-fill--fair {
        background: var(--semantic-warning);
    }
    .dora-score-component__bar-fill--weak {
        background: var(--semantic-negative);
    }

    .dora-score-component__foot {
        display: flex;
        justify-content: space-between;
        gap: 8px;
        margin-top: 4px;
        font-size: 0.75rem;
    }
    .dora-score-component__reason {
        color: var(--text-muted);
        flex: 1 1 auto;
    }
    .dora-score-component__action {
        white-space: nowrap;
        /* An action link takes the brand action colour, not the accent yellow
           the undeclared `--dora-primary` fallback was painting. */
        color: var(--brand-primary);
        text-decoration: none;
    }
    .dora-score-component__action:hover {
        text-decoration: underline;
    }
    /* A6: focus is always visible, and it was not defined anywhere on this card. */
    .dora-score-component__action:focus-visible {
        outline: 2px solid var(--focus-ring);
        outline-offset: 2px;
        border-radius: var(--radius-sm);
    }
</style>
