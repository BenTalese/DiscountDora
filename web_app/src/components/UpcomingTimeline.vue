<template>
    <q-card flat bordered>
        <q-card-section class="row items-center q-pb-none">
            <q-icon :name="ICONS.event" size="20px" class="q-mr-sm" />
            <div class="col">
                <div class="text-subtitle1">Upcoming</div>
                <div class="text-caption dora-text-muted">
                    What's coming over the next {{ windowDays }} days — expiries, shopping days,
                    and planned meals.
                </div>
            </div>
            <BaseButton variant="icon" :icon="ICONS.refresh" :loading="loading" @click="refresh" />
        </q-card-section>

        <q-banner v-if="loadError" class="dora-bg-negative-soft text-negative q-ma-md" dense rounded>
            {{ loadError }}
        </q-banner>

        <q-card-section>
            <!-- Legend -->
            <div class="row items-center q-gutter-md q-mb-sm text-caption dora-text-muted">
                <div class="row items-center no-wrap">
                    <span class="up-dot up-dot--expiry q-mr-xs" /> Expiry
                </div>
                <div class="row items-center no-wrap">
                    <span class="up-dot up-dot--shopping q-mr-xs" /> Shopping
                </div>
                <div class="row items-center no-wrap">
                    <span class="up-dot up-dot--meal q-mr-xs" /> Meals
                </div>
            </div>

            <!-- Weekday header -->
            <div class="up-grid up-grid--head">
                <div v-for="wd in WEEKDAYS" :key="wd" class="up-head-cell">{{ wd }}</div>
            </div>

            <!-- Week rows -->
            <div v-for="(week, wi) in weeks" :key="wi" class="up-grid">
                <div
                    v-for="cell in week"
                    :key="cell.iso"
                    class="up-cell"
                    :class="{
                        'up-cell--out': !cell.inWindow,
                        'up-cell--today': cell.isToday,
                        'up-cell--selected': cell.iso === selectedDate,
                        'up-cell--clickable': cell.hasEvents,
                    }"
                    @click="cell.hasEvents ? (selectedDate = cell.iso) : null"
                >
                    <span class="up-cell__dd">{{ cell.dd }}</span>
                    <div v-if="cell.hasEvents" class="up-cell__dots">
                        <span v-if="cell.hasExpiry" class="up-dot up-dot--expiry" />
                        <span v-if="cell.hasShopping" class="up-dot up-dot--shopping" />
                        <span v-if="cell.hasMeal" class="up-dot up-dot--meal" />
                    </div>
                </div>
            </div>

            <!-- Selected-day detail -->
            <div v-if="selectedDay" class="q-mt-md">
                <q-separator class="q-mb-sm" />
                <div class="text-subtitle2 q-mb-xs">{{ formatLong(selectedDay.date) }}</div>

                <q-list dense>
                    <q-item
                        v-for="e in selectedDay.expiries"
                        :key="`x-${e.stock_item_id}`"
                        clickable
                        @click="go(`/stock/${e.stock_item_id}`)"
                    >
                        <q-item-section avatar>
                            <q-icon :name="ICONS.schedule" color="warning" size="20px" />
                        </q-item-section>
                        <q-item-section>
                            <q-item-label>{{ e.name }}</q-item-label>
                            <q-item-label caption>Expires this day</q-item-label>
                        </q-item-section>
                        <q-item-section side><q-icon :name="ICONS.chevron_right" /></q-item-section>
                    </q-item>

                    <q-item
                        v-for="s in selectedDay.shopping"
                        :key="`s-${s.list_id}`"
                        clickable
                        @click="go(`/shopping-lists/${s.list_id}`)"
                    >
                        <q-item-section avatar>
                            <q-icon :name="ICONS.shopping_cart" color="primary" size="20px" />
                        </q-item-section>
                        <q-item-section>
                            <q-item-label>{{ s.name }}</q-item-label>
                            <q-item-label caption>Planned shopping day</q-item-label>
                        </q-item-section>
                        <q-item-section side><q-icon :name="ICONS.chevron_right" /></q-item-section>
                    </q-item>

                    <q-item
                        v-for="m in selectedDay.meals"
                        :key="`m-${m.recipe_id}-${m.slot}`"
                        clickable
                        @click="go(`/cookbook/${m.recipe_id}`)"
                    >
                        <q-item-section avatar>
                            <q-icon :name="ICONS.restaurant" color="positive" size="20px" />
                        </q-item-section>
                        <q-item-section>
                            <q-item-label>{{ m.recipe_name }}</q-item-label>
                            <q-item-label caption>{{ m.slot }}</q-item-label>
                        </q-item-section>
                        <q-item-section side><q-icon :name="ICONS.chevron_right" /></q-item-section>
                    </q-item>
                </q-list>
            </div>

            <div
                v-else-if="!loading"
                class="text-center dora-text-muted q-py-md text-caption"
            >
                Nothing scheduled in the next {{ windowDays }} days.
            </div>
        </q-card-section>
    </q-card>
</template>

<script lang="ts" setup>
    import BaseButton from 'src/components/BaseButton.vue';
    import { ICONS } from 'src/style/icons';
    import { mondayOf, shiftDays } from 'src/helpers/weekDates';
    import AlertApiService from 'src/services/api/alertApiService';
    import type { Upcoming, UpcomingDay } from 'src/models/alert';
    import { describeApiError } from 'src/services/errorHandling/apiErrorHandler';
    import { computed, onMounted, ref } from 'vue';
    import { useRouter } from 'vue-router';

    // the "this fortnight" forward view. The window + aggregation are
    // server-owned (R-003, GET /alerts/upcoming); this component only renders the
    // grid + per-category dots and expands a clicked day. Token-based dot colours
    // (R-002) so it survives theme switches.
    const WEEKDAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

    const router = useRouter();
    const api = new AlertApiService();

    const data = ref<Upcoming | null>(null);
    const loading = ref(false);
    const loadError = ref('');
    const selectedDate = ref<string | null>(null);

    const windowDays = computed(() => data.value?.days ?? 14);

    // Date → its events, for O(1) cell lookup.
    const byDate = computed(() => {
        const map = new Map<string, UpcomingDay>();
        for (const day of data.value?.dates ?? []) map.set(day.date, day);
        return map;
    });

    const selectedDay = computed<UpcomingDay | null>(() =>
        selectedDate.value ? byDate.value.get(selectedDate.value) ?? null : null,
    );

    type Cell = {
        iso: string;
        dd: string;
        inWindow: boolean;
        isToday: boolean;
        hasEvents: boolean;
        hasExpiry: boolean;
        hasShopping: boolean;
        hasMeal: boolean;
    };

    // Calendar-aligned grid: whole Mon–Sun weeks spanning [start, end], with
    // days outside the window dimmed so columns line up by weekday.
    const weeks = computed<Cell[][]>(() => {
        const d = data.value;
        if (!d) return [];
        const gridStart = mondayOf(d.start);
        const rows: Cell[][] = [];
        // Enough weeks to cover end; cap defensively at 6 (max 31-day window).
        for (let w = 0; w < 6; w++) {
            const weekMonday = shiftDays(gridStart, w * 7);
            if (weekMonday > d.end) break;
            const row: Cell[] = [];
            for (let i = 0; i < 7; i++) {
                const iso = shiftDays(weekMonday, i);
                const inWindow = iso >= d.start && iso <= d.end;
                const day = byDate.value.get(iso);
                row.push({
                    iso,
                    dd: iso.slice(8, 10),
                    inWindow,
                    isToday: iso === d.start,
                    hasEvents: !!day,
                    hasExpiry: !!day && day.expiries.length > 0,
                    hasShopping: !!day && day.shopping.length > 0,
                    hasMeal: !!day && day.meals.length > 0,
                });
            }
            rows.push(row);
        }
        return rows;
    });

    function formatLong(iso: string): string {
        const [y, m, dd] = iso.split('-').map(Number);
        return new Date(Date.UTC(y!, m! - 1, dd)).toLocaleDateString(undefined, {
            weekday: 'long', day: 'numeric', month: 'long',
        });
    }

    function go(path: string): void {
        void router.push(path);
    }

    async function refresh(): Promise<void> {
        loading.value = true;
        loadError.value = '';
        try {
            const result = await api.getUpcomingAsync(14);
            data.value = result;
            // Default the detail to the first day that has events.
            selectedDate.value = result.dates[0]?.date ?? null;
        } catch (err) {
            loadError.value = describeApiError(err) || 'Could not load the timeline.';
        } finally {
            loading.value = false;
        }
    }

    onMounted(refresh);
</script>

<style scoped>
    .up-grid {
        display: grid;
        grid-template-columns: repeat(7, 1fr);
        gap: 4px;
    }
    .up-grid--head {
        margin-bottom: 4px;
    }
    .up-head-cell {
        text-align: center;
        font-size: 0.65rem;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    .up-cell {
        position: relative;
        aspect-ratio: 1 / 1;
        border-radius: 6px;
        background: var(--surface-sunken);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        border: 2px solid transparent;
        gap: 3px;
    }
    .up-cell--out {
        opacity: 0.35;
    }
    .up-cell--clickable {
        cursor: pointer;
    }
    .up-cell--clickable:hover {
        background: var(--surface-elevated);
    }
    .up-cell--today {
        border-color: var(--brand-primary);
    }
    .up-cell--selected {
        outline: 2px solid var(--brand-primary);
        outline-offset: 1px;
    }
    .up-cell__dd {
        font-size: 0.72rem;
        color: var(--text-secondary);
    }
    .up-cell__dots {
        display: flex;
        gap: 2px;
    }
    .up-dot {
        display: inline-block;
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background: var(--text-muted);
    }
    .up-dot--expiry {
        background: var(--semantic-warning);
    }
    .up-dot--shopping {
        background: var(--brand-primary);
    }
    .up-dot--meal {
        background: var(--semantic-positive);
    }
</style>
