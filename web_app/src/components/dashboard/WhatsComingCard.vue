<template>
    <DashboardCard :icon="ICONS.calendar_month" title="What's coming">
        <template #action>
            <!-- No `flat`: BaseSegmented forces `--text-on-primary` on the
                 pressed segment (to beat Quasar's `.text-primary !important`),
                 so it needs Quasar to actually paint the primary fill
                 underneath. With `flat` there is no fill and the selected label
                 came out white-on-light — measured **1.21:1** against the pill
                 track, i.e. invisible (D-002 wants 4.5). The component's own
                 header comment describes this trap; it caught me anyway. -->
            <BaseSegmented
                :model-value="span"
                :options="spans"
                aria-label="Days to show"
                dense
                size="sm"
                @update:model-value="(v: CalendarSpan) => emit('update:span', v)"
            />
        </template>

        <div class="dora-cal-legend q-mb-sm">
            <span class="dora-cal-leg"><span class="dora-cal-dot dot-meal" /> meals</span>
            <span class="dora-cal-leg"><span class="dora-cal-dot dot-expiry" /> expiry</span>
            <span class="dora-cal-leg"><span class="dora-cal-dot dot-shopping" /> shopping</span>
        </div>

        <CardLoadError
            v-if="failed"
            line="I couldn't load what's coming up."
            @retry="emit('retry')"
        />
        <template v-else-if="cells.length > 0">
            <div class="dora-cal-grid" role="grid">
                <button
                    v-for="cell in cells"
                    :key="cell.iso"
                    type="button"
                    class="dora-cal-cell"
                    :class="{
                        'is-today': cell.isToday,
                        'is-selected': cell.iso === selected,
                        'has-events': cell.hasMeal || cell.hasExpiry || cell.hasShopping,
                    }"
                    :aria-pressed="cell.iso === selected"
                    :aria-label="cell.label"
                    @click="emit('select', cell.iso)"
                >
                    <!-- The weekday label came across from the retired week
                         strip. Losing it in the merge would have left a bare
                         number grid, and D-012 explicitly wants calendar cells
                         labelled rather than reduced to dots. -->
                    <span class="dora-cal-dow">{{ cell.dow }}</span>
                    <span class="dora-cal-num">{{ cell.dayNum }}</span>
                    <span class="dora-cal-dots">
                        <span v-if="cell.hasMeal" class="dora-cal-dot dot-meal" />
                        <span v-if="cell.hasExpiry" class="dora-cal-dot dot-expiry" />
                        <span v-if="cell.hasShopping" class="dora-cal-dot dot-shopping" />
                    </span>
                </button>
            </div>
            <div v-if="selectedDay" class="dora-cal-detail">
                <div class="dora-cal-detail-date">
                    {{ formatRelativeDay(selectedDay.date) }}
                </div>
                <div v-if="selectedDay.meals.length > 0" class="dora-cal-group">
                    <div class="dora-cal-group-label">Meals</div>
                    <router-link
                        v-for="(m, i) in selectedDay.meals"
                        :key="`${m.recipe_id}-${m.slot}-${i}`"
                        class="dora-cal-item"
                        :to="`/cookbook/${m.recipe_id}`"
                    >
                        {{ m.recipe_name }} <span class="dora-cal-slot">· {{ m.slot }}</span>
                    </router-link>
                </div>
                <div v-if="selectedDay.expiries.length > 0" class="dora-cal-group">
                    <div class="dora-cal-group-label">Expiring</div>
                    <router-link
                        v-for="e in selectedDay.expiries"
                        :key="e.stock_item_id"
                        class="dora-cal-item"
                        :to="`/stock/${e.stock_item_id}`"
                    >
                        {{ e.name }}
                    </router-link>
                </div>
                <div v-if="selectedDay.shopping.length > 0" class="dora-cal-group">
                    <div class="dora-cal-group-label">Shopping</div>
                    <router-link
                        v-for="s in selectedDay.shopping"
                        :key="s.list_id"
                        class="dora-cal-item"
                        :to="`/shopping-lists/${s.list_id}`"
                    >
                        {{ s.name }}
                    </router-link>
                </div>
            </div>
            <div v-else class="dora-cal-hint">
                Tap a day with dots to see what's on.
            </div>
        </template>
        <div v-else class="dora-empty">
            Nothing scheduled {{ spanLabel }} — enjoy the calm.
            <router-link class="dora-empty-cta" to="/meal-plans">Plan a week →</router-link>
        </div>
    </DashboardCard>
</template>

<script lang="ts" setup>
    /**
     * "What's coming" — the dashboard's one forward-looking calendar.
     *
     * FU-818 merged two cards into this: the 7-day meal-pip strip ("The week
     * ahead") and the 14-day dot grid ("This fortnight"). They rendered the same
     * days from **two different endpoints** — the strip from
     * `/dashboard/summary`'s `upcoming_entries`, the grid from
     * `/alerts/upcoming` — so the overlapping week could disagree with itself on
     * one screen with no way to tell which was right (R-003). One source now,
     * with a 7/14-day toggle; D-012's reading is that a pip strip and a dot grid
     * are the same widget at two zoom levels, so they were never two cards'
     * worth of information.
     *
     * Two things improved in the merge: the week view gained the **expiry and
     * shopping** dots it never had, and the old "Next up" callout went — it
     * restated the hero line verbatim.
     *
     * Extracted from `DashboardPage.vue` (FU-829). The page owns the fetch and
     * builds `cells` (it needs the household's local-date logic and the shared
     * `parseLocalIso`), so this component renders and emits.
     */
    import { ICONS } from 'src/style/icons';
    import { formatRelativeDay } from 'src/composables/useDateFormat';
    import BaseSegmented from 'src/components/BaseSegmented.vue';
    import DashboardCard from 'src/components/dashboard/DashboardCard.vue';
    import CardLoadError from 'src/components/dashboard/CardLoadError.vue';
    import type { UpcomingDay } from 'src/models/alert';

    /** How many days the grid shows. 7 is the default — a week is the planning
     *  unit; 14 is the old "This fortnight" view. */
    export type CalendarSpan = 7 | 14;

    export type CalendarCell = {
        iso: string;
        dayNum: number;
        dow: string;
        /** Accessible name — the cell's visible text is an abbreviation. */
        label: string;
        isToday: boolean;
        hasExpiry: boolean;
        hasShopping: boolean;
        hasMeal: boolean;
    };

    withDefaults(
        defineProps<{
            cells: CalendarCell[];
            span: CalendarSpan;
            spans: { label: string; value: CalendarSpan }[];
            /** "in the next week" / "in the next fortnight", for the empty copy. */
            spanLabel: string;
            selected: string | null;
            selectedDay: UpcomingDay | null;
            failed?: boolean;
        }>(),
        { failed: false },
    );

    const emit = defineEmits<{
        (e: 'update:span', value: CalendarSpan): void;
        (e: 'select', iso: string): void;
        (e: 'retry'): void;
    }>();
</script>

<style scoped lang="scss">
    /* Moved with the card (R-027); off the page-local `--c-*` aliases, which
       resolve to nothing from a component (R-060). */
    .dora-cal-legend {
        display: flex;
        gap: var(--space-3);
        /* Was 11.5px — under D-003's floor, on the card's own decoder ring
           (D-013). The legend must be the most legible thing here. */
        font-size: calc(var(--font-size-xs) * 1rem);
        color: var(--text-secondary);
    }
    .dora-cal-leg {
        display: inline-flex;
        align-items: center;
        gap: var(--space-1);
    }
    .dora-cal-grid {
        display: grid;
        grid-template-columns: repeat(7, minmax(0, 1fr));
        gap: var(--space-2);
    }
    .dora-cal-cell {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: var(--space-1);
        min-height: 56px;
        padding: var(--space-2) var(--space-1);
        border: 1px solid var(--border-default);
        border-radius: var(--radius-md);
        /* A1: nested rows are inset wells inside a card — `--surface-sunken`.
           `--surface-elevated` is for surfaces floating ABOVE a card. */
        background: var(--surface-sunken);
        color: var(--text-primary);
        cursor: pointer;
        transition: border-color 0.15s ease, background 0.15s ease, transform 0.15s ease;
    }
    .dora-cal-cell.has-events:hover {
        border-color: var(--border-strong);
        transform: translateY(-1px);
    }
    .dora-cal-cell.is-today {
        /* An accent-coloured hairline is `--accent-mark` (R-069). */
        border-color: var(--accent-mark);
        font-weight: 700;
    }
    .dora-cal-cell.is-selected {
        background: var(--brand-primary-soft);
        border-color: var(--brand-primary);
    }
    /* A6 — focus is always visible. These are real <button>s, so they were
       keyboard-reachable already; what they lacked was a ring. */
    .dora-cal-cell:focus-visible {
        outline: 2px solid var(--focus-ring);
        outline-offset: 2px;
    }
    /* Weekday label, inherited from the retired week strip (FU-818). D-012 wants
       calendar cells labelled rather than reduced to bare dots, and a 14-cell
       grid of numbers alone is genuinely hard to read. */
    .dora-cal-dow {
        font-size: calc(var(--font-size-xs) * 1rem);
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: var(--text-secondary);
        line-height: 1;
    }
    .dora-cal-cell.is-today .dora-cal-dow {
        color: var(--accent-ink);
        font-weight: 700;
    }
    .dora-cal-num {
        font-size: calc(var(--font-size-md) * 1rem);
        line-height: 1;
    }
    .dora-cal-dots {
        display: flex;
        gap: var(--space-1);
        min-height: 6px;
    }
    .dora-cal-dot {
        width: 6px;
        height: 6px;
        border-radius: var(--radius-pill);
        flex-shrink: 0;
    }
    .dora-cal-dot.dot-meal {
        background: var(--semantic-positive);
    }
    .dora-cal-dot.dot-expiry {
        background: var(--semantic-negative);
    }
    /* Owner 2026-09-04 — *"meals and shopping are too similar in colour"*. He
       is right, and it was theme-dependent rather than an oversight: meals take
       `--semantic-positive` (a green), shopping took `--brand-primary`, and on
       the themes whose brand tone is itself green the two dots were nearly the
       same swatch. Three categories on one cell need three *categorical*
       colours, not two semantics and a brand.

       `--semantic-info` is the fix: a blue in every theme, defined right beside
       the positive and negative these sit with, so the trio stays separable
       under any palette. Not a `--chart-*` ramp entry — those are for series in
       a chart, and these three are a fixed legend (D-001). */
    .dora-cal-dot.dot-shopping {
        background: var(--semantic-info);
    }
    .dora-cal-hint {
        margin-top: var(--space-3);
        font-size: calc(var(--font-size-sm) * 1rem);
        color: var(--text-secondary);
    }
    .dora-cal-detail {
        margin-top: var(--space-4);
        padding: var(--space-3) var(--space-4);
        background: var(--surface-sunken);
        border-radius: var(--radius-md);
    }
    .dora-cal-detail-date {
        font-weight: 700;
        margin-bottom: var(--space-2);
    }
    .dora-cal-group {
        margin-top: var(--space-2);
    }
    .dora-cal-group-label {
        font-size: calc(var(--font-size-xs) * 1rem);
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: var(--text-secondary);
        margin-bottom: var(--space-1);
    }
    .dora-cal-item {
        display: block;
        color: var(--text-primary);
        text-decoration: none;
        font-size: calc(var(--font-size-sm) * 1rem);
        padding: var(--space-1) 0;
    }
    .dora-cal-item:hover {
        text-decoration: underline;
    }
    .dora-cal-slot {
        color: var(--text-secondary);
        font-size: calc(var(--font-size-sm) * 1rem);
    }

    @media (prefers-reduced-motion: reduce) {
        .dora-cal-cell {
            transition: none !important;
        }
        .dora-cal-cell.has-events:hover {
            transform: none !important;
        }
    }
</style>
