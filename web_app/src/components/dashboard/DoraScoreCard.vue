<template>
    <!-- dashboard's kitchen-health card. Reads the composite +
         five-component breakdown from `useDoraScore()`; renders each
         component as a mini-bar chip that links to a remediating
         action (charter: every weak component should nudge toward the
         feature that improves it, never shame). -->
    <DashboardCard :icon="ICONS.favorite">
        <template #title>
            Kitchen health
            <q-icon :name="ICONS.help_outline" size="14px" class="q-ml-xs">
                <q-tooltip>
                    A 0–100 score of how your kitchen's tracking right now — waste,
                    on-budget, freshness, unplanned run-outs, and stocktake staleness,
                    averaged. Only signals with real data count; missing signals
                    don't drag the score down.
                </q-tooltip>
            </q-icon>
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
    import { useDoraScore } from 'src/composables/useDoraScore';
    import type {
        DoraScoreComponentKey,
    } from 'src/models/doraScore';

    const { doraScore: score, loading } = useDoraScore();

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
            case 'budget':
                // The budget input lives in Settings → Money.
                return { to: '/settings/money', label: 'Set a budget' };
            case 'freshness':
                // Filter stock to expiring / expired items so the user
                // can act. The stock overview reads ?expiring=1.
                return { to: '/stock?expiring=1', label: 'Expiring items' };
            case 'runouts':
                // The primary shopping-list overview is where planned
                // buys land — the answer to "fewer surprise run-outs".
                return { to: '/shopping-lists', label: 'Shopping lists' };
            case 'stocktake':
                // Stock overview's stocktake mode (?stocktake=1).
                return { to: '/stock?stocktake=1', label: 'Do a stocktake' };
            default:
                return null;
        }
    }
</script>

<style scoped>
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
        color: var(--dora-text);
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
    .dora-score-trend--up {
        background: var(--dora-positive-bg, rgba(34, 139, 34, 0.12));
        color: var(--dora-positive, #228b22);
    }
    .dora-score-trend--down {
        background: var(--dora-negative-bg, rgba(180, 60, 60, 0.12));
        color: var(--dora-negative, #b43c3c);
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
        border-radius: 999px;
        background: var(--dora-muted-bg, rgba(0, 0, 0, 0.06));
        overflow: hidden;
    }
    .dora-score-component__bar-fill {
        height: 100%;
        border-radius: 999px;
        transition: width 300ms ease-out;
    }
    .dora-score-component__bar-fill--good {
        background: var(--dora-positive, #228b22);
    }
    .dora-score-component__bar-fill--fair {
        background: var(--dora-primary, #f5c462);
    }
    .dora-score-component__bar-fill--weak {
        background: var(--dora-negative, #b43c3c);
    }

    .dora-score-component__foot {
        display: flex;
        justify-content: space-between;
        gap: 8px;
        margin-top: 4px;
        font-size: 0.75rem;
    }
    .dora-score-component__reason {
        color: var(--dora-text-muted, #666);
        flex: 1 1 auto;
    }
    .dora-score-component__action {
        white-space: nowrap;
        color: var(--dora-primary, #f5c462);
        text-decoration: none;
    }
    .dora-score-component__action:hover {
        text-decoration: underline;
    }
</style>
