<template>
    <!-- The chip is deliberately just a count: it stays small on a wrapping
         ingredient row, and it counts *every* recorded swap rather than only
         the ones in stock — a swap you'd have to buy is still a swap the user
         may want to know about (owner feedback 2026-08-27). Which of them you
         actually have is what the menu is for. -->
    <button
        v-if="entries.length > 0"
        type="button"
        class="rsub__chip"
        :class="{ 'rsub__chip--have': haveOne }"
        :aria-label="`${chipLabel} for ${ingredientName}`"
    >
        <q-icon :name="ICONS.swap_horiz" size="14px" />
        <span>{{ chipLabel }}</span>

        <q-menu anchor="bottom left" self="top left" class="rsub__menu">
            <div class="rsub__head">
                <span class="rsub__headk">Instead of {{ ingredientName }}</span>
            </div>
            <q-list dense separator class="rsub__list">
                <q-item v-for="entry in ordered" :key="entry.sub.stock_item_id">
                    <!-- Stock level reads as the same dot-left-of-the-name it
                         does everywhere else in the app, rather than this
                         surface's own badge wording (D-013 / owner feedback
                         2026-08-27). Tooltip'd — a bare dot isn't decodable. -->
                    <q-item-section side class="rsub__dot">
                        <StockLevelDot :sequence="entry.levelSequence" size="12px">
                            <q-tooltip>{{ entry.levelLabel }}</q-tooltip>
                        </StockLevelDot>
                    </q-item-section>
                    <q-item-section>
                        <q-item-label class="rsub__name">
                            {{ entry.sub.name }}
                        </q-item-label>
                        <q-item-label v-if="formatSubstituteRatio(entry.sub)" caption>
                            {{ formatSubstituteRatio(entry.sub) }}
                        </q-item-label>
                        <q-item-label v-if="entry.sub.notes" caption class="dora-text-secondary">
                            {{ entry.sub.notes }}
                        </q-item-label>
                    </q-item-section>
                    <q-item-section side>
                        <AddToListButton
                            v-if="!entry.inStock"
                            :stock-item-id="entry.sub.stock_item_id"
                            variant="row"
                        />
                    </q-item-section>
                </q-item>
            </q-list>
        </q-menu>
    </button>
</template>

<script lang="ts" setup>
    /**
     * A missing ingredient's recorded substitutes, as a row-level chip.
     *
     * Replaces the old page's bulk "Find substitutes for missing" dialog, which
     * listed substitute *names* per missing item and stopped there — leaving
     * the reader to check each one against their own pantry by hand. The whole
     * value of the feature is the one fact that dialog didn't show: whether the
     * substitute is something you actually have. So the list carries a level
     * dot per option, and it sits on the row it's about rather than behind a
     * page-level action. The chip itself stays a bare count — see the template.
     *
     * Read-only by design. Substitutes are per-cook swaps (cook mode owns
     * them) and per-item facts (the stock-item detail page owns them); nothing
     * here writes either.
     */
    import { computed } from 'vue';

    import AddToListButton from 'src/components/AddToListButton.vue';
    import StockLevelDot from 'src/components/stock/StockLevelDot.vue';
    import { ICONS } from 'src/style/icons';
    import { formatSubstituteRatio } from 'src/helpers/substituteRatio';
    import type { SubstituteOption } from './recipeSubstituteTypes';

    const props = defineProps<{
        entries: SubstituteOption[];
        ingredientName: string;
    }>();

    /** In-stock options first — the actionable ones — then alphabetical so the
     *  order is stable between renders. */
    const ordered = computed(() =>
        [...props.entries].sort((a, b) => {
            if (a.inStock !== b.inStock) return a.inStock ? -1 : 1;
            return a.sub.name.localeCompare(b.sub.name);
        }));

    const haveOne = computed(() => props.entries.some((e) => e.inStock));

    /** Always the total number of recorded swaps — never a count filtered by
     *  what's in stock, which used to read "0 swaps" on a row that had swaps
     *  the user could buy. The tint still says whether one is available now;
     *  the menu says which. */
    const chipLabel = computed(() => {
        const n = props.entries.length;
        return `${n} swap${n === 1 ? '' : 's'}`;
    });
</script>

<style scoped lang="scss">
    .rsub__chip {
        display: inline-flex;
        align-items: center;
        gap: var(--space-1);
        /* D-011 — a real tap target, not bare text. Chips sit inline in a
           wrapping ingredient name, so the row's own height governs; 28px is
           the shared chip height on this page. */
        min-height: 28px;
        padding: 0 var(--space-2);
        border: 1px solid var(--border-default);
        border-radius: var(--radius-pill);
        background: var(--surface-sunken);
        color: var(--text-secondary);
        font-size: var(--font-size-xs);
        font-weight: 600;
        cursor: pointer;

        &:hover { background: var(--overlay-hover); }
        &:active { background: var(--overlay-active); }
        /* A6 / D-016 — focus is never suppressed. */
        &:focus-visible {
            outline: 2px solid var(--focus-ring);
            outline-offset: 2px;
        }
    }

    /* Colour carries one meaning only: is there something here you can act on
       right now. It is not a severity (D-013) — the row's own Missing chip
       already says that, and this chip sits beside it. */
    .rsub__chip--have {
        border-color: var(--semantic-positive);
        background: var(--semantic-positive-soft);
        color: var(--text-primary);
    }

    .rsub__head {
        padding: var(--space-3) var(--space-4) var(--space-2);
    }

    .rsub__headk {
        font-size: var(--font-size-xs);
        font-weight: 700;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        color: var(--text-muted);
    }

    .rsub__list {
        min-width: 260px;
        max-width: 360px;
    }

    .rsub__name {
        display: flex;
        align-items: center;
        gap: var(--space-2);
        flex-wrap: wrap;
    }

    .rsub__dot {
        padding-right: var(--space-2);
        min-width: 0;
    }
</style>
