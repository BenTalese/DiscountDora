<template>
    <!-- FU-609 / R-036 — app-shell root: <q-page :style-fn> so the full-bleed
         runner fills the viewport below the header without a hardcoded offset. -->
    <q-page class="runner-shell" :style-fn="pageStyleFn">
        <!-- ── Top progress strip ─────────────────────────────────────
             Same shape as StocktakeRunner: close X, progress bar,
             (?) help. Empty-queue is a state of the runner, not a
             separate landing page. -->
        <div class="runner-topbar">
            <BaseButton
                variant="icon"
                :icon="ICONS.close"
                color="white"
                :to="'/meal-plans'"
                aria-label="Close reconcile"
            />
            <q-linear-progress
                v-if="hasEntry"
                :value="progress"
                rounded
                size="6px"
                color="primary"
                class="col q-mx-md"
            />
            <div v-else class="col" />
            <div v-if="hasEntry" class="text-caption dora-text-muted-3 q-mr-sm">
                {{ resolvedCount }} / {{ initialCount }}
            </div>
            <BaseButton
                variant="icon"
                :icon="ICONS.help_outline"
                color="white"
                aria-label="How reconcile works"
                @click="helpOpen = true"
            />
        </div>

        <!-- ── Loading ─────────────────────────────────────────────── -->
        <div v-if="loading" class="runner-card-wrap">
            <q-spinner color="primary" size="42px" />
        </div>

        <!-- ── Empty queue (matches StocktakeRunner's empty state) ─── -->
        <div v-else-if="entries.length === 0 && index === 0" class="runner-card-wrap">
            <q-card class="runner-card" flat>
                <q-card-section class="text-center q-pt-lg">
                    <q-icon :name="ICONS.check_circle" color="positive" size="64px" />
                    <div class="text-h5 q-mt-sm">Nothing to reconcile.</div>
                    <div class="text-caption dora-text-muted-7 q-mt-xs">
                        Every past-day meal has been confirmed. Dora will
                        surface entries here as days roll past.
                    </div>
                </q-card-section>
                <q-card-actions align="center" class="q-pb-lg">
                    <BaseButton label="Back to Meal plans" :to="'/meal-plans'" />
                </q-card-actions>
            </q-card>
        </div>

        <!-- ── Current entry card ──────────────────────────────────── -->
        <div v-else-if="current" class="runner-card-wrap">
            <q-card class="runner-card" flat>
                <q-card-section class="text-center">
                    <div class="text-caption dora-text-muted-5 q-mb-xs">
                        {{ formatScheduledFor(current.scheduled_for) }} · {{ current.slot }}
                    </div>
                    <div class="text-h5">{{ current.recipe.name }}</div>
                    <div class="text-caption dora-text-muted-7 q-mt-xs">
                        Planned {{ current.planned_servings }} serving{{ current.planned_servings === 1 ? '' : 's' }}
                    </div>
                </q-card-section>

                <q-card-section>
                    <!-- Primary: Cooked (as planned). Big button. -->
                    <BaseButton
                        variant="primary"
                        class="full-width q-mb-sm"
                        :icon="ICONS.check_circle"
                        label="Cooked"
                        :disable="busy"
                        @click="onVerb('cooked')"
                    />

                    <!-- Secondary: Cooked (different portions) / Cooked later.
                         Both drop an inline field before submitting. -->
                    <div class="row q-gutter-sm q-mb-sm">
                        <BaseButton
                            variant="secondary"
                            class="col"
                            label="Different portions"
                            :disable="busy"
                            @click="adjustOpen = true"
                        />
                        <BaseButton
                            variant="secondary"
                            class="col"
                            label="Cooked later"
                            :disable="busy"
                            @click="laterOpen = true"
                        />
                    </div>

                    <!-- Tertiary: Didn't cook. Reverses any drain. -->
                    <BaseButton
                        variant="danger-ghost"
                        class="full-width q-mb-md"
                        label="Didn't cook"
                        :disable="busy"
                        @click="onVerb('not_cooked')"
                    />

                    <!-- Small: Skip for now (session defer). -->
                    <div class="row justify-center">
                        <BaseButton
                            variant="ghost"
                            label="Skip for now"
                            :disable="busy"
                            @click="onVerb('skip')"
                        />
                    </div>
                </q-card-section>
            </q-card>
        </div>

        <!-- ── Session-complete card ───────────────────────────────── -->
        <div v-else class="runner-card-wrap">
            <q-card class="runner-card" flat>
                <q-card-section class="text-center">
                    <q-icon :name="ICONS.check_circle" color="positive" size="64px" />
                    <div class="text-h5 q-mt-sm">Reconcile complete</div>
                    <div class="runner-summary">
                        <div class="runner-summary__row">
                            <span class="runner-summary__count">{{ summary.cooked }}</span>
                            <span class="dora-text-muted-7">cooked</span>
                        </div>
                        <div class="runner-summary__row">
                            <span class="runner-summary__count">{{ summary.adjusted }}</span>
                            <span class="dora-text-muted-7">adjusted</span>
                        </div>
                        <div class="runner-summary__row">
                            <span class="runner-summary__count">{{ summary.notCooked }}</span>
                            <span class="dora-text-muted-7">not cooked</span>
                        </div>
                        <div class="runner-summary__row">
                            <span class="runner-summary__count">{{ summary.cookedLater }}</span>
                            <span class="dora-text-muted-7">cooked later</span>
                        </div>
                        <div class="runner-summary__row">
                            <span class="runner-summary__count">{{ summary.skipped }}</span>
                            <span class="dora-text-muted-7">still open</span>
                        </div>
                    </div>
                </q-card-section>
                <q-card-actions align="center" class="q-pb-md">
                    <BaseButton label="Done" :to="'/'" />
                </q-card-actions>
            </q-card>
        </div>

        <!-- ── Different portions dialog ───────────────────────────── -->
        <BaseDialog v-model="adjustOpen" title="How many did you actually make?" closable card-style="min-width: 320px">
            <q-card-section>
                <q-input
                    v-model.number="adjustServings"
                    type="number"
                    min="0"
                    max="999"
                    outlined
                    dense
                    autofocus
                    label="Servings"
                />
            </q-card-section>
            <q-card-actions align="right">
                <BaseButton variant="ghost" label="Cancel" v-close-popup />
                <BaseButton
                    variant="primary"
                    label="Save"
                    :disable="!Number.isFinite(adjustServings) || adjustServings < 0"
                    @click="onVerbAdjust"
                />
            </q-card-actions>
        </BaseDialog>

        <!-- ── Cooked later dialog ─────────────────────────────────── -->
        <BaseDialog v-model="laterOpen" title="When did you cook it?" closable card-style="min-width: 320px">
            <q-card-section>
                <q-input
                    v-model="laterCookedOn"
                    type="date"
                    outlined
                    dense
                    autofocus
                    :max="todayIso"
                    label="Date cooked"
                />
            </q-card-section>
            <q-card-actions align="right">
                <BaseButton variant="ghost" label="Cancel" v-close-popup />
                <BaseButton
                    variant="primary"
                    label="Save"
                    :disable="!laterCookedOn"
                    @click="onVerbLater"
                />
            </q-card-actions>
        </BaseDialog>

        <!-- ── (?) help dialog ─────────────────────────────────────── -->
        <BaseDialog v-model="helpOpen" title="How reconcile works" closable card-style="min-width: 320px; max-width: 480px">
            <q-card-section class="runner-help">
                <p>
                    Dora walks you through past-day meals from your plan
                    that haven't been confirmed yet — one at a time,
                    oldest first. For each entry you have five options:
                </p>
                <dl>
                    <dt>Cooked</dt>
                    <dd>You made it as planned. The cooked count and pool
                        are correct.</dd>
                    <dt>Different portions</dt>
                    <dd>You made a different amount — say 3 instead of 2.
                        Dora reflows the pool.</dd>
                    <dt>Cooked later</dt>
                    <dd>You made it, but on a later day. Dora records the
                        date on the receipt.</dd>
                    <dt>Didn't cook</dt>
                    <dd>The meal didn't happen. Dora puts the pool back
                        the way it was.</dd>
                    <dt>Skip for now</dt>
                    <dd>Not sure yet — the entry stays in the queue for
                        next time.</dd>
                </dl>
                <p class="dora-text-muted-7">
                    Whether past-day meals are assumed cooked or stay pending
                    is set globally in Settings → Admin → System → Meal
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
    import { useQuasar } from 'quasar';
    import { computed, onMounted, reactive, ref } from 'vue';
    import { useReconcileQueue } from 'src/composables/useReconcileQueue';
    import type {
        ReconcileEntry,
        ReconcileVerb,
        ReconcileVerbCommand,
    } from 'src/services/api/mealPlanApiService';
    import { toastCaption } from 'src/services/errorHandling/apiErrorHandler';

    const $q = useQuasar();
    const { entries, loading, submitVerb, reload } = useReconcileQueue();

    // FU-609 / R-036 — app-shell height. QPage hands us the layout's live chrome
    // `offset` (header, incl. the OfflineBanner when it shows) + viewport
    // `height`, so the full-bleed runner fills exactly the area below the header
    // instead of overshooting by a hardcoded 100dvh (which ignored the offset).
    function pageStyleFn(offset: number, height: number) {
        return {
            height: height === 0 ? `calc(100vh - ${offset}px)` : `${height - offset}px`,
        };
    }

    const index = ref(0);
    const busy = ref(false);
    const helpOpen = ref(false);
    const adjustOpen = ref(false);
    const adjustServings = ref<number>(0);
    const laterOpen = ref(false);
    const laterCookedOn = ref<string>('');

    /** Snapshot the initial queue length so the progress bar's
     *  denominator is stable across the session (each resolved verb
     *  removes an entry from the live list). */
    const initialCount = ref(0);
    const resolvedCount = computed(() => Math.min(index.value, initialCount.value));
    const hasEntry = computed(() => index.value < initialCount.value);
    const progress = computed(() =>
        initialCount.value === 0 ? 0 : resolvedCount.value / initialCount.value,
    );

    /** Because `submitVerb` removes the resolved entry from `entries`,
     *  the "current" item is always `entries[0]` while there's still
     *  something in the queue. `index` is a monotonic session counter
     *  for the progress bar; `current` is what's on screen. */
    const current = computed<ReconcileEntry | null>(() => entries.value[0] ?? null);

    const summary = reactive({
        cooked: 0,
        adjusted: 0,
        notCooked: 0,
        cookedLater: 0,
        skipped: 0,
    });

    const todayIso = computed(() => new Date().toISOString().slice(0, 10));

    function formatScheduledFor(iso: string): string {
        // "Mon 7 Jul" — same shape stocktake uses inline.
        const d = new Date(iso);
        return d.toLocaleDateString(undefined, {
            weekday: 'short', day: 'numeric', month: 'short',
        });
    }

    onMounted(async () => {
        await reload();
        initialCount.value = entries.value.length;
    });

    async function onVerb(verb: ReconcileVerb): Promise<void> {
        const c = current.value;
        if (!c || busy.value) return;
        await runVerb(c.entry_id, { verb });
    }

    async function onVerbAdjust(): Promise<void> {
        const c = current.value;
        if (!c || busy.value) return;
        adjustOpen.value = false;
        await runVerb(c.entry_id, {
            verb: 'cooked_adjusted',
            actual_servings: adjustServings.value,
        });
        adjustServings.value = 0;
    }

    async function onVerbLater(): Promise<void> {
        const c = current.value;
        if (!c || busy.value) return;
        laterOpen.value = false;
        await runVerb(c.entry_id, {
            verb: 'cooked_later',
            cooked_on: laterCookedOn.value,
        });
        laterCookedOn.value = '';
    }

    async function runVerb(entryId: string, command: ReconcileVerbCommand): Promise<void> {
        busy.value = true;
        try {
            await submitVerb(entryId, command);
            // Book the outcome for the completion-screen recap.
            if (command.verb === 'cooked') summary.cooked += 1;
            else if (command.verb === 'cooked_adjusted') summary.adjusted += 1;
            else if (command.verb === 'not_cooked') summary.notCooked += 1;
            else if (command.verb === 'cooked_later') summary.cookedLater += 1;
            else if (command.verb === 'skip') summary.skipped += 1;
            index.value += 1;
        } catch (err: unknown) {
            $q.notify({
                type: 'negative',
                message: 'Could not save that.',
                caption: toastCaption(err),
                position: 'bottom',
            });
        } finally {
            busy.value = false;
        }
    }
</script>

<style scoped lang="scss">
    // Shape mirrors StocktakeRunner.vue — same shell, same rem-based
    // typography, same warm accent. Colour flips to brand-primary
    // (reconcile is a meal-plan surface, not a stock surface).
    .runner-shell {
        /* FU-609 / R-036 — height comes from the <q-page :style-fn> (viewport −
           live layout offset); no hardcoded 100dvh (which ignored the header). */
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

    .runner-card-wrap {
        flex: 1 1 auto;
        display: flex;
        justify-content: center;
        align-items: flex-start;
        padding: 1.5rem 1rem;
    }

    .runner-card {
        width: min(28rem, 100%);
        background: var(--surface-component);
        border-radius: var(--radius-lg);
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
    }

    .runner-summary {
        display: flex;
        flex-direction: column;
        gap: 0.4rem;
        margin-top: 1rem;
        align-items: center;
    }

    .runner-summary__row {
        display: flex;
        gap: 0.5rem;
        align-items: baseline;
    }

    .runner-summary__count {
        font-variant-numeric: tabular-nums;
        font-weight: 600;
        min-width: 1.5rem;
        text-align: right;
    }

    .runner-help dl {
        margin: 0.75rem 0;
    }

    .runner-help dt {
        font-weight: 600;
        margin-top: 0.5rem;
    }

    .runner-help dd {
        margin: 0 0 0.5rem 0;
    }
</style>
