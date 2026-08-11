<template>
    <!-- FU-609 / R-036 — app-shell root: <q-page :style-fn> so the full-bleed
         runner fills the viewport below the header without a hardcoded offset. -->
    <q-page class="runner-shell" :style-fn="pageStyleFn">
        <!-- ── Top progress strip ──────────────────────────────────────
             Close X on the left, progress bar with count in the middle,
             (?) help on the right. No separate landing page any more —
             empty-queue is a state of this same view. -->
        <div class="runner-topbar">
            <BaseButton
                variant="icon"
                :icon="ICONS.close"
                color="white"
                :to="'/stock'"
                aria-label="Close stocktake"
            />
            <q-linear-progress
                v-if="hasQueue"
                :value="progress"
                rounded
                size="6px"
                color="warning"
                class="col q-mx-md"
            />
            <div v-else class="col" />
            <div v-if="hasQueue" class="text-caption dora-text-muted-3 q-mr-sm">
                {{ reviewedCount }} / {{ session.length }}
            </div>
            <BaseButton
                variant="icon"
                :icon="ICONS.help_outline"
                color="white"
                aria-label="How stocktake works"
                @click="helpOpen = true"
            />
        </div>

        <!-- ── Loading ─────────────────────────────────────────────── -->
        <div v-if="loading" class="runner-card-wrap">
            <q-spinner color="warning" size="42px" />
        </div>

        <!-- ── Empty queue (was the old landing card) ─────────────── -->
        <div v-else-if="session.length === 0" class="runner-card-wrap">
            <q-card class="runner-card" flat>
                <q-card-section class="text-center q-pt-lg">
                    <q-icon :name="ICONS.check_circle" color="positive" size="64px" />
                    <div class="text-h5 q-mt-sm">You're all caught up.</div>
                    <div class="text-caption dora-text-muted-7 q-mt-xs">
                        Nothing needs a check right now. Dora will surface
                        items again when they're due.
                    </div>
                </q-card-section>
                <q-card-actions align="center" class="q-pb-lg">
                    <BaseButton label="Back to Stock" :to="'/stock'" />
                </q-card-actions>
            </q-card>
        </div>

        <!-- ── Current item card ──────────────────────────────────── -->
        <div v-else-if="current" class="runner-card-wrap">
            <q-card class="runner-card" flat>
                <q-card-section class="text-center">
                    <div class="text-h5">{{ current.name }}</div>
                    <div class="text-caption dora-text-muted-7 q-mt-xs">
                        {{ current.stock_location_name ?? 'No location' }}
                    </div>
                    <div class="text-caption dora-text-muted-5 q-mt-xs">
                        Checked every {{ bandLabel(current.cadence_band) }}
                        · {{ current.overdue_days }} day{{ current.overdue_days === 1 ? '' : 's' }} overdue
                        <q-icon :name="ICONS.help_outline" size="14px" class="q-ml-xs">
                            <q-tooltip>
                                How often stocktake mode wants you to re-check this
                                item (Weekly / Fortnightly / Monthly) and how far
                                past the last check date you are. Cadence is set
                                globally in Settings or per-item on the detail page.
                            </q-tooltip>
                        </q-icon>
                    </div>
                </q-card-section>

                <!-- Primary row: two big buttons, side by side.
                     Still correct: positive.
                     Change level: coloured to the current level so the
                     button doubles as the level readout. Small "(change)"
                     underneath makes the action explicit. -->
                <q-card-section class="runner-primary-row">
                    <BaseButton
                        variant="positive"
                        size="lg"
                        class="col runner-primary"
                        :icon="ICONS.check"
                        label="Still correct"
                        :loading="busy"
                        @click="onStillCorrect"
                    />
                    <!-- carve-out — raw q-btn: labeled dynamic-color button with custom stacked children, not an icon-variant fit -->
                    <q-btn
                        unelevated
                        no-caps
                        size="lg"
                        :color="currentLevelColour ?? undefined"
                        :class="[
                            'col runner-primary runner-change-level',
                            { 'runner-change-level--neutral': !currentLevelColour },
                        ]"
                        :loading="busy"
                        @click="changeOpen = true"
                    >
                        <div class="runner-change-level__stack">
                            <div class="runner-change-level__level">
                                {{ current.stock_level_name ?? '—' }}
                            </div>
                            <div class="runner-change-level__hint">(change)</div>
                        </div>
                    </q-btn>
                </q-card-section>

                <!-- Secondary row: three smaller buttons.
                     Skip = session-only, no API.
                     Push = 3-day snooze, no last_checked bump.
                     Mute = per-item off, with confirmation. -->
                <q-card-section class="runner-secondary-row">
                    <BaseButton
                        variant="ghost"
                        class="col"
                        :icon="ICONS.skip_next"
                        label="Skip"
                        :disable="busy"
                        @click="onSkip"
                    />
                    <BaseButton
                        variant="ghost"
                        class="col"
                        :icon="ICONS.snooze"
                        label="Push 3 days"
                        :loading="busy"
                        @click="onPush"
                    >
                        <q-tooltip>
                            Delays this item's next stocktake prompt by 3 days
                            without recording a check. Use when you'll be able to
                            look properly soon.
                        </q-tooltip>
                    </BaseButton>
                    <BaseButton
                        variant="danger-ghost"
                        class="col"
                        :icon="ICONS.mute"
                        label="Mute"
                        :disable="busy"
                        @click="onMute"
                    />
                </q-card-section>
            </q-card>
        </div>

        <!-- ── Session-complete card ────────────────────────────────
             Five-counter summary + optional batch add-to-list for
             items marked Low or Out during the session (SK-7). -->
        <div v-else class="runner-card-wrap">
            <q-card class="runner-card" flat>
                <q-card-section class="text-center">
                    <q-icon :name="ICONS.check_circle" color="positive" size="64px" />
                    <div class="text-h5 q-mt-sm">Stocktake complete</div>
                    <div class="runner-summary">
                        <div class="runner-summary__row">
                            <span class="runner-summary__count">{{ summary.checked }}</span>
                            <span class="dora-text-muted-7">checked</span>
                        </div>
                        <div class="runner-summary__row">
                            <span class="runner-summary__count">{{ summary.changed }}</span>
                            <span class="dora-text-muted-7">changed</span>
                        </div>
                        <div class="runner-summary__row">
                            <span class="runner-summary__count">{{ summary.skipped }}</span>
                            <span class="dora-text-muted-7">skipped</span>
                        </div>
                        <div class="runner-summary__row">
                            <span class="runner-summary__count">{{ summary.pushed }}</span>
                            <span class="dora-text-muted-7">pushed</span>
                        </div>
                        <div class="runner-summary__row">
                            <span class="runner-summary__count">{{ summary.muted }}</span>
                            <span class="dora-text-muted-7">muted</span>
                        </div>
                    </div>
                </q-card-section>

                <!-- SK-7: if anything went Low or Out this session, offer to
                     add them all to a shopping list in one action. Any active
                     list is a valid target. -->
                <q-card-section v-if="restockNeeded.length > 0" class="runner-restock-prompt">
                    <div class="text-subtitle2 q-mb-sm text-center">
                        {{ restockNeeded.length }} item{{ restockNeeded.length === 1 ? '' : 's' }}
                        went Low or Out.
                    </div>
                    <div class="text-caption dora-text-muted-7 q-mb-sm text-center">
                        Add {{ restockNeeded.length === 1 ? 'it' : 'them' }} to a shopping list?
                    </div>
                    <BaseButton
                        variant="primary"
                        class="full-width"
                        :icon="ICONS.add_shopping_cart"
                        :label="`Add to list…`"
                        :loading="restockBusy"
                        :disable="restockDone"
                        @click="onBatchAddToList"
                    />
                    <div v-if="restockDone" class="text-caption dora-text-muted-7 text-center q-mt-sm">
                        Added.
                    </div>
                </q-card-section>

                <q-card-actions align="center" class="q-pb-md">
                    <BaseButton label="Done" :to="'/stock'" />
                </q-card-actions>
            </q-card>
        </div>

        <!-- ── Level picker dialog ─────────────────────────────────
             SK-8: each option renders the level's colour dot so the
             picker matches the Stock Overview visual language. -->
        <BaseDialog v-model="changeOpen" title="Set level" closable card-style="min-width: 280px">
            <q-card-section>
                <q-list>
                    <q-item
                        v-for="level in stockLevels"
                        :key="level.stock_level_id"
                        clickable
                        v-close-popup
                        @click="onPickLevel(level.stock_level_id, level.sequence, level.name)"
                    >
                        <q-item-section avatar>
                            <StockLevelDot :sequence="level.sequence" size="14px" />
                        </q-item-section>
                        <q-item-section>{{ level.name }}</q-item-section>
                    </q-item>
                </q-list>
            </q-card-section>
        </BaseDialog>

        <!-- ── (?) help dialog — plain-English "how it works" -->
        <BaseDialog v-model="helpOpen" title="How stocktake works" closable card-style="min-width: 320px; max-width: 480px">
            <q-card-section class="runner-help">
                <p>
                    Dora walks you through the items she thinks need a
                    check — one at a time, most-overdue first. For each,
                    you have five options:
                </p>
                <dl>
                    <dt>Still correct</dt>
                    <dd>The level's right. Resets the check clock.</dd>
                    <dt>Change level</dt>
                    <dd>Pick a new level. Also resets the check clock.</dd>
                    <dt>Skip</dt>
                    <dd>
                        Later today — the item drops to the end and
                        comes back if you reopen this queue.
                    </dd>
                    <dt>Push 3 days</dt>
                    <dd>
                        Not now — Dora stops asking about this item for
                        three days. Doesn't count as a check.
                    </dd>
                    <dt>Mute</dt>
                    <dd>
                        Stop asking about this item entirely. You can
                        un-mute later from the item's detail page.
                    </dd>
                </dl>
                <p class="dora-text-muted-7">
                    How often each item shows up (Weekly / Fortnightly /
                    Monthly) is set globally in Settings → Stocktake, with
                    Auto self-tuning by how fast the item actually moves.
                </p>
            </q-card-section>
        </BaseDialog>
    </q-page>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import BaseButton from 'src/components/BaseButton.vue';
    import BaseDialog from 'src/components/BaseDialog.vue';
    import StockLevelDot from 'src/components/stock/StockLevelDot.vue';
    import { useQuasar } from 'quasar';
    import { storeToRefs } from 'pinia';
    import { computed, onMounted, reactive, ref } from 'vue';
    import StockItemApiService from 'src/services/api/stockItemApiService';
    import StocktakeApiService, {
        type CadenceBand,
        type StocktakeQueueItem,
    } from 'src/services/api/stocktakeApiService';
    import { useShoppingListActions } from 'src/composables/useShoppingListActions';
    import { useShoppingListStore } from 'src/stores/shoppingListStore';
    import { useStockLevelStore } from 'src/stores/stockLevelStore';
    import { colourForSequence } from 'src/helpers/stockLevelLogic';
    import {
        LOW_STOCK_SEQUENCE,
        OUT_OF_STOCK_SEQUENCE,
    } from 'src/helpers/stockStatus';
    import { toastCaption } from 'src/services/errorHandling/apiErrorHandler';

    const $q = useQuasar();
    const api = new StocktakeApiService();
    const stockApi = new StockItemApiService();

    // FU-609 / R-036 — app-shell height. QPage hands us the layout's live chrome
    // `offset` + viewport `height`, so the full-bleed runner fills exactly the
    // area below the header instead of overshooting by a hardcoded 100vh.
    function pageStyleFn(offset: number, height: number) {
        return {
            height: height === 0 ? `calc(100vh - ${offset}px)` : `${height - offset}px`,
        };
    }
    const stockLevelStore = useStockLevelStore();
    const { stockLevels } = storeToRefs(stockLevelStore);
    const shoppingListStore = useShoppingListStore();
    const { addItems } = useShoppingListActions();

    const loading = ref(true);
    const session = ref<StocktakeQueueItem[]>([]);
    const index = ref(0);
    const busy = ref(false);
    const changeOpen = ref(false);
    const helpOpen = ref(false);

    /** Five-counter summary powering the completion screen. */
    const summary = reactive({
        checked: 0,
        changed: 0,
        skipped: 0,
        pushed: 0,
        muted: 0,
    });

    /**
     * Items the user set to Low or Out via Change-level during THIS
     * session. Drives the SK-7 batch add-to-list prompt on the
     * completion screen. A later Change-level on the same item
     * upgrades whatever it was to the latest choice (e.g. flip Low →
     * Stocked → drop; last write wins).
     */
    const restockNeeded = ref<Array<{ stock_item_id: string; name: string }>>([]);
    const restockBusy = ref(false);
    const restockDone = ref(false);

    const hasQueue = computed(() => session.value.length > 0 && index.value < session.value.length);
    const current = computed<StocktakeQueueItem | null>(() =>
        index.value < session.value.length ? session.value[index.value]! : null,
    );
    const reviewedCount = computed(() => index.value);
    const progress = computed(() =>
        session.value.length === 0 ? 0 : index.value / session.value.length,
    );

    const currentLevelColour = computed(() => {
        const c = current.value;
        if (!c) return null;
        const level = stockLevels.value.find((l) => l.name === c.stock_level_name);
        return colourForSequence(level?.sequence);
    });

    function bandLabel(band: CadenceBand): string {
        // Weekly → "week", Fortnightly → "fortnight", Monthly → "month".
        // Matches how the copy reads inline ("Checked every week").
        switch (band) {
            case 'weekly': return 'week';
            case 'fortnightly': return 'fortnight';
            case 'monthly': return 'month';
        }
    }

    function advance() {
        index.value += 1;
    }

    async function onStillCorrect() {
        if (!current.value) return;
        busy.value = true;
        try {
            await api.checkOneAsync(current.value.stock_item_id);
            summary.checked += 1;
            advance();
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'top',
                message: 'Could not confirm.',
                caption: toastCaption(err),
            });
        } finally { busy.value = false; }
    }

    async function onPickLevel(
        levelId: string,
        sequence: number,
        levelName: string,
    ) {
        if (!current.value) return;
        const stockItemId = current.value.stock_item_id;
        const itemName = current.value.name;
        busy.value = true;
        try {
            await stockApi.updateAsync({
                stock_item_id: stockItemId,
                stock_level_id: levelId,
            });
            summary.changed += 1;
            // SK-7 tracking: this session's Low/Out flips feed the
            // batch add-to-list prompt on the completion screen.
            // Dedupe if the user Changes the same item twice.
            const isRestockable =
                sequence >= LOW_STOCK_SEQUENCE || sequence === OUT_OF_STOCK_SEQUENCE;
            const existingIdx = restockNeeded.value.findIndex(
                (r) => r.stock_item_id === stockItemId,
            );
            if (isRestockable) {
                if (existingIdx === -1) {
                    restockNeeded.value.push({ stock_item_id: stockItemId, name: itemName });
                }
            } else if (existingIdx !== -1) {
                // User flipped it back to Stocked — take it out again.
                restockNeeded.value.splice(existingIdx, 1);
            }
            void levelName;
            advance();
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'top',
                message: 'Could not update.',
                caption: toastCaption(err),
            });
        } finally { busy.value = false; }
    }

    function onSkip() {
        if (!current.value) return;
        // Session-only: move the item to the end of the queue and
        // advance. It reappears if the user reaches the end. No API.
        const skipped = current.value;
        session.value = [...session.value, skipped];
        summary.skipped += 1;
        advance();
    }

    async function onPush() {
        if (!current.value) return;
        busy.value = true;
        try {
            await api.snoozeAsync(current.value.stock_item_id);
            summary.pushed += 1;
            advance();
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'top',
                message: 'Could not push.',
                caption: toastCaption(err),
            });
        } finally { busy.value = false; }
    }

    function onMute() {
        if (!current.value) return;
        const stockItemId = current.value.stock_item_id;
        const itemName = current.value.name;
        // Mute is nuclear (persistent, only un-mutable from item
        // detail) — always confirm before firing.
        $q.dialog({
            title: `Mute ${itemName}?`,
            message:
                "Dora will stop asking about this item entirely. You can un-mute it later from the item's detail page.",
            cancel: true,
            persistent: false,
            ok: { label: 'Mute', color: 'negative', unelevated: true },
        }).onOk(() => {
            void (async () => {
                busy.value = true;
                try {
                    await stockApi.updateAsync({
                        stock_item_id: stockItemId,
                        stocktake_alerts_are_enabled: false,
                    });
                    summary.muted += 1;
                    advance();
                } catch (err) {
                    $q.notify({
                        type: 'negative',
                        position: 'top',
                        message: 'Could not mute.',
                        caption: toastCaption(err),
                    });
                } finally { busy.value = false; }
            })();
        });
    }

    async function onBatchAddToList() {
        if (restockNeeded.value.length === 0 || restockBusy.value || restockDone.value) return;
        const listId = await pickActiveListId();
        if (!listId) return;
        restockBusy.value = true;
        try {
            await addItems(
                listId,
                restockNeeded.value.map((r) => ({ stock_item_id: r.stock_item_id })),
            );
            restockDone.value = true;
        } finally {
            restockBusy.value = false;
        }
    }

    /**
     * Prompt the user to pick an active list. Same shape as the Stock
     * Overview bulk-add flow (radio dialog over `active_lists`). Returns
     * the chosen list id or null on cancel / no lists.
     */
    async function pickActiveListId(): Promise<string | null> {
        const active =
            (shoppingListStore.membership?.active_lists ?? [])
                .filter((l) => l.status !== 'done');
        if (active.length === 0) {
            $q.notify({
                type: 'info',
                position: 'bottom-right',
                message: 'No active lists. Create one first.',
            });
            return null;
        }
        return await new Promise<string | null>((resolve) => {
            $q.dialog({
                title: 'Add to which list?',
                options: {
                    type: 'radio',
                    model: active[0]!.shopping_list_id,
                    items: active.map((l) => ({ label: l.name, value: l.shopping_list_id })),
                },
                cancel: true,
                persistent: false,
            })
                .onOk((val: string) => resolve(val))
                .onCancel(() => resolve(null))
                .onDismiss(() => resolve(null));
        });
    }

    onMounted(async () => {
        try {
            await stockLevelStore.ensureLoadedAsync();
            await shoppingListStore.refreshAsync();
            const result = await api.queueAsync(100);
            session.value = result.items;
        } finally {
            loading.value = false;
        }
    });
</script>

<style scoped>
    /* Fullscreen focus mode. Stays dark across every theme — the
       contrast is part of the "you're concentrating" affordance — so
       we use raw palette tokens rather than the semantic surface ones. */
    .runner-shell {
        /* FU-609 / R-036 — height comes from the <q-page :style-fn> (viewport −
           live layout offset); no hardcoded 100vh (which ignored the header). */
        background: var(--palette-neutral-900);
        color: var(--text-inverse);
        display: flex; flex-direction: column;
    }
    .runner-topbar {
        display: flex; align-items: center; padding: 12px;
        background: var(--palette-neutral-900);
    }
    .runner-card-wrap {
        flex: 1; display: flex; align-items: center; justify-content: center;
        padding: 24px;
    }
    .runner-card {
        max-width: 480px; width: 100%;
        background: var(--surface-component); color: var(--text-primary);
        border-radius: 12px;
    }

    /* Two big primary buttons side-by-side. gap comes from `q-gutter-*`
       being awkward across sections, so we use a flex row directly. */
    .runner-primary-row {
        display: flex;
        gap: 8px;
    }
    .runner-primary {
        min-height: 72px;
    }

    /* Change-level button: two stacked lines (level name + "(change)")
       inside q-btn's default slot. */
    .runner-change-level__stack {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 2px;
        line-height: 1.15;
    }
    .runner-change-level__level {
        font-size: var(--text-md, 1rem);
        font-weight: 600;
    }
    .runner-change-level__hint {
        font-size: var(--text-xs, 0.75rem);
        opacity: 0.85;
    }
    /* Out-of-stock / unknown level → neutral state. Uses theme tokens
       (R-002) rather than a hardcoded grey literal so it tracks dark
       + light themes. */
    .runner-change-level--neutral {
        background: var(--surface-sunken, rgba(0, 0, 0, 0.12));
        color: var(--text-primary);
    }
    .runner-change-level--neutral:hover {
        background: var(--surface-hover, rgba(0, 0, 0, 0.18));
    }

    /* Secondary row: three smaller ghost-style actions. */
    .runner-secondary-row {
        display: flex;
        gap: 8px;
        padding-top: 0;
    }

    /* Completion summary — five short rows, count on left, label on right. */
    .runner-summary {
        display: flex;
        flex-direction: column;
        gap: 4px;
        max-width: 200px;
        margin: 16px auto 0;
    }
    .runner-summary__row {
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        gap: 12px;
    }
    .runner-summary__count {
        font-size: var(--text-md, 1rem);
        font-weight: 600;
        min-width: 24px;
        text-align: right;
    }

    .runner-restock-prompt {
        border-top: 1px solid var(--c-line, rgba(0, 0, 0, 0.12));
    }

    .runner-help {
        font-size: var(--text-sm, 0.9rem);
        line-height: 1.4;
    }
    .runner-help dl {
        margin: 12px 0;
    }
    .runner-help dt {
        font-weight: 600;
        margin-top: 8px;
    }
    .runner-help dd {
        margin-left: 0;
        color: var(--text-secondary, inherit);
    }
</style>
