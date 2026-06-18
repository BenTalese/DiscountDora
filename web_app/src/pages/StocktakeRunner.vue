<template>
    <div class="runner-shell">
        <!-- ── Top progress strip ──────────────────────────────────── -->
        <div class="runner-topbar">
            <q-btn flat round :icon="ICONS.close" color="white" :to="'/stocktake'" />
            <q-linear-progress
                :value="progress"
                rounded
                size="6px"
                color="warning"
                
                class="col q-mx-md"
            />
            <div class="text-caption dora-text-muted-3">
                {{ reviewedCount }} / {{ session.length }}
            </div>
        </div>

        <!-- ── Current item card ──────────────────────────────────── -->
        <div v-if="current" class="runner-card-wrap">
            <q-card class="runner-card" flat>
                <q-card-section class="text-center">
                    <div class="text-h5">{{ current.name }}</div>
                    <div class="text-caption dora-text-muted-7 q-mt-xs">
                        {{ current.stock_location_name ?? 'No location' }}
                    </div>
                </q-card-section>
                <q-card-section class="text-center">
                    <div class="text-overline dora-text-secondary">Current level</div>
                    <div class="text-h6">{{ current.stock_level_name ?? '—' }}</div>
                    <div
                        class="text-caption q-mt-xs"
                        :class="current.overdue_days < 0 ? 'dora-text-secondary' : 'text-warning'"
                    >
                        {{ current.overdue_days < 0
                            ? 'Never checked'
                            : `${current.overdue_days} day(s) overdue` }}
                    </div>
                </q-card-section>
                <q-card-section class="q-gutter-sm">
                    <q-btn
                        color="positive"
                        size="lg"
                        class="full-width"
                        no-caps
                        :icon="ICONS.check"
                        label="Still correct (1)"
                        :loading="busy"
                        @click="onStillCorrect"
                    />
                    <q-btn
                        color="primary"
                        size="lg"
                        class="full-width"
                        no-caps
                        :icon="ICONS.tune"
                        label="Change level (2)"
                        :loading="busy"
                        @click="changeOpen = true"
                    />
                    <q-btn
                        color="negative"
                        size="lg"
                        class="full-width"
                        no-caps
                        :icon="ICONS.remove_shopping_cart"
                        label="Out of stock (3)"
                        :loading="busy"
                        @click="onOutOfStock"
                    />
                </q-card-section>
                <q-card-actions align="between">
                    <q-btn flat no-caps class="dora-text-secondary" label="Skip (s)" @click="onSkip" />
                    <q-btn
                        flat
                        no-caps
                        color="primary"
                        :icon="ICONS.add_shopping_cart"
                        label="Add to list"
                        @click="onAddToList"
                    />
                </q-card-actions>
            </q-card>
        </div>

        <!-- ── Session-complete card ──────────────────────────────── -->
        <div v-else class="runner-card-wrap">
            <q-card class="runner-card" flat>
                <q-card-section class="text-center">
                    <q-icon :name="ICONS.check_circle" color="positive" size="64px" />
                    <div class="text-h5 q-mt-sm">Stocktake complete</div>
                    <div class="text-caption dora-text-muted-7">
                        Checked {{ summary.checked }} ·
                        Updated {{ summary.changed }} ·
                        Skipped {{ summary.skipped }}
                    </div>
                </q-card-section>
                <q-card-actions align="center">
                    <q-btn color="primary" no-caps label="Done" :to="'/stocktake'" />
                </q-card-actions>
            </q-card>
        </div>

        <!-- ── Level picker dialog ────────────────────────────────── -->
        <BaseDialog v-model="changeOpen" title="Set level" closable card-style="min-width: 280px">
                <q-card-section>
                    <q-list>
                        <q-item
                            v-for="level in stockLevels"
                            :key="level.stock_level_id"
                            clickable
                            v-close-popup
                            @click="onPickLevel(level.stock_level_id)"
                        >
                            <q-item-section>{{ level.name }}</q-item-section>
                        </q-item>
                    </q-list>
                </q-card-section>
        </BaseDialog>
    </div>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import BaseDialog from 'src/components/BaseDialog.vue';
    import { useQuasar } from 'quasar';
    import { storeToRefs } from 'pinia';
    import { computed, onMounted, onUnmounted, reactive, ref } from 'vue';
    import StockItemApiService from 'src/services/api/stockItemApiService';
    import StocktakeApiService, { type StocktakeQueueItem } from 'src/services/api/stocktakeApiService';
    import { useStockItemActions } from 'src/composables/useStockItemActions';
    import { useStockLevelStore } from 'src/stores/stockLevelStore';

    const $q = useQuasar();
    const api = new StocktakeApiService();
    const stockApi = new StockItemApiService();
    const stockLevelStore = useStockLevelStore();
    const { stockLevels } = storeToRefs(stockLevelStore);
    const { addToList } = useStockItemActions();

    const session = ref<StocktakeQueueItem[]>([]);
    const index = ref(0);
    const busy = ref(false);
    const changeOpen = ref(false);
    const summary = reactive({ checked: 0, changed: 0, skipped: 0 });

    const current = computed<StocktakeQueueItem | null>(() =>
        index.value < session.value.length ? session.value[index.value]! : null,
    );
    const reviewedCount = computed(() => index.value);
    const progress = computed(() =>
        session.value.length === 0 ? 1 : index.value / session.value.length,
    );

    function next() { index.value += 1; }

    async function onStillCorrect() {
        if (!current.value) return;
        busy.value = true;
        try {
            await api.checkOneAsync(current.value.stock_item_id);
            summary.checked += 1;
            next();
        } finally { busy.value = false; }
    }

    async function onPickLevel(levelId: string) {
        if (!current.value) return;
        busy.value = true;
        try {
            await stockApi.updateAsync({
                stock_item_id: current.value.stock_item_id,
                stock_level_id: levelId,
            });
            summary.changed += 1;
            next();
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'top',
                message: 'Could not update.',
                caption: err instanceof Error ? err.message : String(err),
            });
        } finally { busy.value = false; }
    }

    async function onOutOfStock() {
        const out = stockLevels.value.find(
            (l) => l.name.toLowerCase().includes('out'),
        );
        if (!out) {
            $q.notify({ type: 'negative', position: 'top', message: 'Out-of-stock level not configured.' });
            return;
        }
        await onPickLevel(out.stock_level_id);
    }

    function onSkip() {
        summary.skipped += 1;
        next();
    }

    async function onAddToList() {
        if (!current.value) return;
        // Delegate to the shared single-item action: it emits exactly one
        // toast — "Already on your primary list." or "Added to primary list."
        // — and pops the no-primary-list dialog when needed. Previously this
        // called the bulk addItems(...) and then fired its own toast, which
        // produced the B7 "0 added, 1 already on list" + "X added to primary
        // list." double-toast.
        await addToList(current.value.stock_item_id);
    }

    // ── Keyboard: 1/2/3/s ───────────────────────────────────────
    function onKey(event: KeyboardEvent) {
        if (changeOpen.value) return;
        const k = event.key.toLowerCase();
        if (k === '1') { event.preventDefault(); void onStillCorrect(); }
        else if (k === '2') { event.preventDefault(); changeOpen.value = true; }
        else if (k === '3') { event.preventDefault(); void onOutOfStock(); }
        else if (k === 's') { event.preventDefault(); onSkip(); }
    }

    onMounted(async () => {
        await stockLevelStore.ensureLoadedAsync();
        const result = await api.queueAsync(100);
        session.value = result.items;
        if (typeof window !== 'undefined') window.addEventListener('keydown', onKey);
    });
    onUnmounted(() => {
        if (typeof window !== 'undefined') window.removeEventListener('keydown', onKey);
    });
</script>

<style scoped>
    /* X1: fullscreen focus mode. Stays dark across every theme — the
       contrast is part of the "you're concentrating" affordance — so we
       use raw palette tokens rather than the semantic surface ones. */
    .runner-shell {
        min-height: 100vh;
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
</style>
