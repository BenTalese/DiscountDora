<template>
    <!-- Auto-mode surface (owner 2026-08-13): instead of the confirm-each
         runner, a read-only LOG of what Dora did with past-day meals so the
         user can see what happened. Same full-bleed shell as the runner;
         corrections are out of scope for now (tracked as a follow-up). -->
    <q-page class="runner-shell" :style-fn="pageStyleFn">
        <div class="runner-topbar">
            <BaseButton
                variant="icon"
                :icon="ICONS.close"
                color="white"
                :to="'/meal-plans'"
                aria-label="Close log"
            />
            <div class="col text-subtitle2 text-weight-medium q-ml-sm">
                Meal log
            </div>
            <BaseButton
                variant="icon"
                :icon="ICONS.help_outline"
                color="white"
                aria-label="How the meal log works"
                @click="helpOpen = true"
            />
        </div>

        <div class="log-body">
            <!-- Loading -->
            <div v-if="loading && entries.length === 0" class="log-centre">
                <q-spinner color="primary" size="42px" />
            </div>

            <!-- Error -->
            <q-banner
                v-else-if="error"
                class="dora-bg-negative-soft text-negative q-ma-md"
                rounded
                dense
            >
                Couldn't load the meal log. {{ error }}
            </q-banner>

            <!-- Empty -->
            <div v-else-if="entries.length === 0" class="log-centre">
                <q-icon :name="ICONS.event_note" size="56px" class="dora-text-muted-5" />
                <div class="text-h6 q-mt-sm">Nothing logged yet</div>
                <div class="text-caption dora-text-muted-7 q-mt-xs text-center">
                    As days roll past, Dora records what happened to your
                    planned meals here.
                </div>
            </div>

            <!-- Log, grouped by day (newest first) -->
            <div v-else class="log-list">
                <div class="log-intro dora-text-muted-7">
                    Auto mode is on — Dora assumes planned meals were cooked as
                    each day passes. This is the record of what she did.
                </div>

                <section
                    v-for="group in grouped"
                    :key="group.day"
                    class="log-group"
                >
                    <h2 class="log-group__day">{{ formatDay(group.day) }}</h2>
                    <div
                        v-for="entry in group.items"
                        :key="entry.entry_id"
                        class="log-row"
                    >
                        <div class="log-row__main">
                            <span class="log-row__recipe">{{ entry.recipe.name }}</span>
                            <span class="log-row__meta dora-text-muted-7">
                                {{ entry.slot }} · planned
                                {{ entry.planned_servings }}
                                serving{{ entry.planned_servings === 1 ? '' : 's' }}
                            </span>
                        </div>
                        <span class="log-pill" :class="`log-pill--${outcome(entry).tone}`">
                            {{ outcome(entry).label }}
                        </span>
                    </div>
                </section>

                <div v-if="hasMore" class="log-more">
                    <BaseButton
                        variant="secondary"
                        label="Load older"
                        :loading="loading"
                        @click="loadMore"
                    />
                </div>
            </div>
        </div>

        <!-- (?) help dialog -->
        <BaseDialog v-model="helpOpen" title="About the meal log" closable card-style="min-width: 320px; max-width: 480px">
            <q-card-section class="log-help">
                <p>
                    Your install is in <strong>auto</strong> mode: as each day
                    passes, Dora assumes the meals you planned were cooked and
                    drains the recipe pool for you — no confirming needed.
                </p>
                <p>
                    This page is the record of what she did. Each row shows a
                    past-day planned meal and its outcome:
                </p>
                <dl>
                    <dt>Logged as cooked</dt>
                    <dd>Dora assumed you cooked it as planned (the auto default).</dd>
                    <dt>Cooked / Cooked · N</dt>
                    <dd>You confirmed it — as planned, or with a different amount.</dd>
                    <dt>Not cooked</dt>
                    <dd>You marked that it didn't happen; the pool was put back.</dd>
                    <dt>Skipped</dt>
                    <dd>Left undecided for later.</dd>
                </dl>
                <p class="dora-text-muted-7">
                    To confirm each meal by hand instead, an admin can switch
                    off auto mode in Settings → Admin → System → Meal
                    reconciliation.
                </p>
            </q-card-section>
        </BaseDialog>
    </q-page>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import BaseButton from 'src/components/BaseButton.vue';
    import BaseDialog from 'src/components/BaseDialog.vue';
    import { computed, onMounted, ref } from 'vue';
    import MealPlanApiService, {
        type ReconcileEntry,
    } from 'src/services/api/mealPlanApiService';

    const api = new MealPlanApiService();

    const entries = ref<ReconcileEntry[]>([]);
    const nextCursor = ref<string | null>(null);
    const loading = ref(false);
    const error = ref<string | null>(null);
    const helpOpen = ref(false);

    const hasMore = computed(() => nextCursor.value !== null);

    // FU-609 / R-036 — full-bleed shell height from the layout's live chrome.
    function pageStyleFn(offset: number, height: number) {
        return {
            height: height === 0 ? `calc(100vh - ${offset}px)` : `${height - offset}px`,
        };
    }

    type Group = { day: string; items: ReconcileEntry[] };
    // Entries arrive newest-first, already ordered by day desc; group runs of
    // the same day without re-sorting (server owns the order, R-003).
    const grouped = computed<Group[]>(() => {
        const out: Group[] = [];
        for (const e of entries.value) {
            const last = out[out.length - 1];
            if (last && last.day === e.scheduled_for) last.items.push(e);
            else out.push({ day: e.scheduled_for, items: [e] });
        }
        return out;
    });

    function formatDay(iso: string): string {
        const d = new Date(iso);
        return d.toLocaleDateString(undefined, {
            weekday: 'short', day: 'numeric', month: 'short', year: 'numeric',
        });
    }

    /** Human outcome + colour tone for a log row's latest receipt state. */
    function outcome(entry: ReconcileEntry): { label: string; tone: string } {
        const r = entry.receipt;
        switch (r.state) {
            case 'unresolved_auto':
                return { label: 'Logged as cooked', tone: 'auto' };
            case 'resolved_confirmed':
                return { label: 'Cooked', tone: 'ok' };
            case 'resolved_adjusted':
                return {
                    label: `Cooked · ${r.actual_servings ?? entry.planned_servings} served`,
                    tone: 'ok',
                };
            case 'resolved_not_cooked':
                return { label: 'Not cooked', tone: 'off' };
            case 'resolved_deferred':
                return { label: 'Skipped', tone: 'wait' };
            case 'unresolved_manual':
                return { label: 'Awaiting confirmation', tone: 'wait' };
            default:
                return { label: r.state, tone: 'auto' };
        }
    }

    async function loadInitial() {
        loading.value = true;
        error.value = null;
        try {
            const page = await api.getReconcileLogAsync({ limit: 30 });
            entries.value = page.entries;
            nextCursor.value = page.next_cursor;
        } catch (err) {
            error.value = err instanceof Error ? err.message : String(err);
        } finally {
            loading.value = false;
        }
    }

    async function loadMore() {
        if (!nextCursor.value || loading.value) return;
        loading.value = true;
        try {
            const page = await api.getReconcileLogAsync({
                cursor: nextCursor.value, limit: 30,
            });
            entries.value.push(...page.entries);
            nextCursor.value = page.next_cursor;
        } catch (err) {
            error.value = err instanceof Error ? err.message : String(err);
        } finally {
            loading.value = false;
        }
    }

    onMounted(loadInitial);
</script>

<style scoped lang="scss">
    .runner-shell {
        background: var(--surface-page);
        display: flex;
        flex-direction: column;
    }
    .runner-topbar {
        display: flex;
        align-items: center;
        padding: 0.5rem 0.75rem;
        background: var(--brand-primary);
        color: var(--text-on-primary);
        min-height: 3rem;
    }
    .log-body {
        flex: 1 1 auto;
        min-height: 0;
        overflow-y: auto;
        scrollbar-gutter: stable;
    }
    .log-centre {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 0.25rem;
        padding: 3rem 1.5rem;
    }
    .log-list {
        width: min(40rem, 100%);
        margin: 0 auto;
        padding: 1rem 1rem 2rem;
    }
    .log-intro {
        font-size: 0.85rem;
        line-height: 1.4;
        margin-bottom: 1rem;
    }
    .log-group {
        margin-bottom: 1.25rem;
    }
    .log-group__day {
        margin: 0 0 0.5rem;
        font-size: 0.8125rem;
        font-weight: 700;
        letter-spacing: 0.02em;
        text-transform: uppercase;
        color: var(--text-secondary);
    }
    .log-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.75rem;
        padding: 0.6rem 0.75rem;
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-md);
        background: var(--surface-component);
        margin-bottom: 0.5rem;
    }
    .log-row__main {
        min-width: 0;
        display: flex;
        flex-direction: column;
        gap: 2px;
    }
    .log-row__recipe {
        font-weight: 600;
        color: var(--text-primary);
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    .log-row__meta {
        font-size: 0.75rem;
    }
    .log-pill {
        flex: 0 0 auto;
        font-size: 0.6875rem;
        font-weight: 700;
        letter-spacing: 0.02em;
        padding: 3px 9px;
        border-radius: 999px;
        white-space: nowrap;
        color: var(--text-primary);
        border: 1px solid transparent;
    }
    // Tones lean on semantic soft tints; text stays primary for the contrast
    // floor (D-002 — no coloured-ink-on-coloured-tint).
    .log-pill--auto { background: var(--semantic-info-soft); border-color: color-mix(in srgb, var(--q-info) 30%, transparent); }
    .log-pill--ok   { background: var(--semantic-positive-soft); border-color: color-mix(in srgb, var(--q-positive) 30%, transparent); }
    .log-pill--off  { background: var(--semantic-negative-soft); border-color: color-mix(in srgb, var(--q-negative) 30%, transparent); }
    .log-pill--wait { background: var(--semantic-warning-soft); border-color: color-mix(in srgb, var(--q-warning) 30%, transparent); }
    .log-more {
        display: flex;
        justify-content: center;
        margin-top: 0.5rem;
    }
    .log-help dl { margin: 0.75rem 0; }
    .log-help dt { font-weight: 600; margin-top: 0.5rem; }
    .log-help dd { margin: 0 0 0.5rem 0; }
</style>
