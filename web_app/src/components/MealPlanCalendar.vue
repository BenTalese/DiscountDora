<template>
    <q-card flat bordered>
        <q-card-section class="row items-center q-py-xs no-wrap">
            <q-btn flat round dense size="sm" :icon="ICONS.arrow_upward" @click="pageWindow(-WINDOW_WEEKS)">
                <q-tooltip>Earlier weeks</q-tooltip>
            </q-btn>
            <q-space />
            <div class="text-subtitle2 text-weight-bold cal__month">{{ monthBanner }}</div>
            <q-space />
            <q-btn flat round dense size="sm" :icon="ICONS.arrow_downward" @click="pageWindow(WINDOW_WEEKS)">
                <q-tooltip>Later weeks</q-tooltip>
            </q-btn>
        </q-card-section>
        <q-separator />
        <q-card-section class="q-pa-sm column q-gutter-xs">
            <div
                v-for="week in weeks"
                :key="week.monday"
                class="cal-week"
                :class="{ 'cal-week--focused': week.monday === focusedMonday }"
                @click="selectWeek(week.monday)"
            >
                <div
                    v-for="cell in week.days"
                    :key="cell.iso"
                    class="cal-day"
                    :class="`cal-day--${cell.status}`"
                >
                    <span v-if="cell.showLabel" class="cal-day__dd">{{ cell.dd }}</span>
                    <span v-if="cell.isToday" class="cal-day__today" />
                </div>
                <q-tooltip>Week of {{ formatDate(week.monday) }}</q-tooltip>
            </div>
        </q-card-section>
    </q-card>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import { storeToRefs } from 'pinia';
    import { isoDate, localTodayIso, mondayOf, shiftDays } from 'src/helpers/weekDates';
    import type { MealPlanEntry } from 'src/models/mealPlan';
    import { useMealPlanStore } from 'src/stores/mealPlanStore';
    import { computed, ref, watch } from 'vue';

    const focusedMonday = defineModel<string>('focusedMonday', { required: true });

    const WINDOW_WEEKS = 6;

    const mealPlanStore = useMealPlanStore();
    const { mealPlans, shortfall, today } = storeToRefs(mealPlanStore);

    const shortfallRecipeIds = computed(() => new Set(shortfall.value.map((s) => s.recipe_id)));

    // Entries for every plan, keyed by day — the calendar spans many weeks, so
    // it reads across all plans (not just the focused one).
    const entriesByDay = computed(() => {
        const map = new Map<string, MealPlanEntry[]>();
        for (const plan of mealPlans.value) {
            for (const entry of plan.entries) {
                const key = isoDate(entry.scheduled_for);
                const list = map.get(key) ?? [];
                if (!map.has(key)) map.set(key, list);
                list.push(entry);
            }
        }
        return map;
    });

    type DayStatus = 'empty' | 'planned' | 'short' | 'consumed';
    function dayStatus(dayIso: string): DayStatus {
        const entries = entriesByDay.value.get(dayIso);
        if (!entries || entries.length === 0) return 'empty';
        // Status is derived from the server's shortfall set (R-003) — the
        // client never re-judges cookability here.
        if (entries.some((e) => !e.consumed_at && shortfallRecipeIds.value.has(e.recipe_id))) return 'short';
        if (entries.every((e) => e.consumed_at)) return 'consumed';
        return 'planned';
    }

    // Visible window: 6 weeks. It re-anchors only when the focused week scrolls
    // out of view (so clicking a visible week doesn't make the list jump).
    const calendarStart = ref(shiftDays(mondayOf(focusedMonday.value), -7));
    watch(focusedMonday, (m) => {
        const start = calendarStart.value;
        const end = shiftDays(start, WINDOW_WEEKS * 7);
        if (m < start || m >= end) calendarStart.value = shiftDays(mondayOf(m), -7);
    });
    function pageWindow(deltaWeeks: number) {
        calendarStart.value = shiftDays(calendarStart.value, deltaWeeks * 7);
    }

    const todayIso = computed(() => today.value ?? localTodayIso());

    type CalCell = { iso: string; dd: string; showLabel: boolean; status: DayStatus; isToday: boolean };
    const weeks = computed<{ monday: string; days: CalCell[] }[]>(() => {
        const out: { monday: string; days: CalCell[] }[] = [];
        for (let w = 0; w < WINDOW_WEEKS; w++) {
            const monday = shiftDays(calendarStart.value, w * 7);
            const days: CalCell[] = [];
            for (let i = 0; i < 7; i++) {
                const iso = shiftDays(monday, i);
                days.push({
                    iso,
                    dd: iso.slice(8, 10),
                    showLabel: i === 0,
                    status: dayStatus(iso),
                    isToday: iso === todayIso.value,
                });
            }
            out.push({ monday, days });
        }
        return out;
    });

    const monthBanner = computed(() => {
        const [y, m, d] = focusedMonday.value.split('-').map(Number);
        return new Date(Date.UTC(y!, m! - 1, d))
            .toLocaleDateString(undefined, { month: 'long', year: 'numeric' })
            .toUpperCase();
    });

    function selectWeek(monday: string) {
        focusedMonday.value = monday;
    }
    function formatDate(iso: string): string {
        return new Date(iso).toLocaleDateString();
    }
</script>

<style scoped>
    .cal__month {
        letter-spacing: 0.06em;
    }
    .cal-week {
        display: flex;
        gap: 4px;
        padding: 3px;
        border-radius: 6px;
        border: 2px solid transparent;
        cursor: pointer;
        transition: background 0.12s ease;
    }
    .cal-week:hover {
        background: var(--surface-sunken);
    }
    .cal-week--focused {
        border-color: var(--brand-primary);
    }
    .cal-day {
        position: relative;
        flex: 1 1 0;
        min-width: 0;
        aspect-ratio: 1 / 1;
        border-radius: 5px;
        background: var(--surface-sunken);
        display: flex;
        align-items: center;
        justify-content: center;
        border-bottom: 2px solid transparent;
    }
    .cal-day__dd {
        font-size: 0.68rem;
        color: var(--text-secondary);
    }
    .cal-day--planned {
        border-bottom-color: var(--semantic-positive);
    }
    .cal-day--short {
        border-bottom-color: var(--semantic-warning);
    }
    .cal-day--consumed {
        border-bottom-style: dotted;
        border-bottom-color: var(--text-muted);
    }
    .cal-day__today {
        position: absolute;
        top: 3px;
        right: 3px;
        width: 5px;
        height: 5px;
        border-radius: 50%;
        background: var(--brand-primary);
    }
</style>
