<template>
    <q-page padding>
        <div class="row items-center q-mb-md">
            <div class="col">
                <div class="text-h5">Use soon</div>
                <div class="text-caption dora-text-muted">
                    Items expiring within the next
                    <q-btn flat dense no-caps :label="`${horizonDays} days`" class="waste-horizon-btn">
                        <q-menu auto-close>
                            <q-list dense style="min-width: 120px">
                                <q-item
                                    v-for="opt in HORIZON_OPTIONS"
                                    :key="opt"
                                    clickable
                                    @click="setHorizon(opt)"
                                >
                                    <q-item-section>
                                        {{ opt }} days
                                    </q-item-section>
                                    <q-item-section avatar v-if="horizonDays === opt">
                                        <q-icon :name="ICONS.check" size="16px" />
                                    </q-item-section>
                                </q-item>
                            </q-list>
                        </q-menu>
                    </q-btn>
                    — pick one, freeze it, or log it as wasted.
                </div>
            </div>
            <q-btn
                flat
                no-caps
                :icon="ICONS.refresh"
                label="Refresh"
                :loading="loading"
                @click="loadRescue"
            />
        </div>

        <q-banner
            v-if="loadError"
            class="bg-negative dora-text-on-primary q-mb-md"
            rounded
        >
            {{ loadError }}
        </q-banner>

        <div v-if="!loading && rescue && rescue.items.length === 0" class="q-pa-lg text-center">
            <q-icon :name="ICONS.check" size="48px" color="positive" />
            <div class="text-subtitle1 q-mt-sm">Nothing's at risk right now.</div>
            <div class="text-caption dora-text-muted">
                Stretch the horizon above if you want a longer look ahead.
            </div>
        </div>

        <div v-else-if="rescue" class="row q-col-gutter-md">
            <!-- Expiring items -->
            <div class="col-12 col-md-7">
                <q-card flat bordered>
                    <q-card-section>
                        <div class="text-subtitle1">
                            {{ rescue.items.length }} item{{ rescue.items.length === 1 ? '' : 's' }} at risk
                        </div>
                        <div v-if="totalValueAtRisk > 0" class="text-caption dora-text-muted">
                            Roughly ${{ totalValueAtRisk.toFixed(2) }} on the line
                        </div>
                    </q-card-section>
                    <q-separator />
                    <q-list separator>
                        <q-item
                            v-for="item in rescue.items"
                            :key="item.stock_item_id"
                            class="waste-row"
                        >
                            <q-item-section avatar>
                                <q-icon
                                    :name="item.is_expired ? ICONS.warning : ICONS.expiry"
                                    :color="dotColorFor(item)"
                                    size="22px"
                                />
                            </q-item-section>
                            <q-item-section>
                                <q-item-label>
                                    <a
                                        href="#"
                                        class="waste-item-name"
                                        @click.prevent="openItem(item.stock_item_id)"
                                    >
                                        {{ item.name }}
                                    </a>
                                </q-item-label>
                                <q-item-label caption>
                                    {{ daysLabel(item) }}
                                    <span v-if="item.estimated_value != null">
                                        · ~${{ item.estimated_value.toFixed(2) }}
                                    </span>
                                </q-item-label>
                            </q-item-section>
                            <q-item-section side>
                                <div class="row q-gutter-xs items-center no-wrap">
                                    <q-btn
                                        flat
                                        dense
                                        no-caps
                                        size="sm"
                                        :icon="ICONS.check"
                                        label="Used"
                                        :loading="busyItemId === item.stock_item_id && busyAction === 'used'"
                                        @click="markUsed(item)"
                                    >
                                        <q-tooltip>Mark Out of Stock and clear expiry</q-tooltip>
                                    </q-btn>
                                    <q-btn
                                        flat
                                        dense
                                        no-caps
                                        size="sm"
                                        icon="mdi-snowflake"
                                        label="Freeze"
                                        :loading="busyItemId === item.stock_item_id && busyAction === 'freeze'"
                                        @click="markFrozen(item)"
                                    >
                                        <q-tooltip>Clear expiry — you've moved it to the freezer</q-tooltip>
                                    </q-btn>
                                    <q-btn
                                        flat
                                        dense
                                        no-caps
                                        size="sm"
                                        :icon="ICONS.delete_outline"
                                        label="Wasted"
                                        color="negative"
                                        @click="openWasteDialog(item)"
                                    >
                                        <q-tooltip>Log as wasted</q-tooltip>
                                    </q-btn>
                                </div>
                            </q-item-section>
                        </q-item>
                    </q-list>
                </q-card>
            </div>

            <!-- Rescue recipes -->
            <div class="col-12 col-md-5">
                <q-card flat bordered>
                    <q-card-section>
                        <div class="text-subtitle1">Recipes that help</div>
                        <div class="text-caption dora-text-muted">
                            Ranked by how many at-risk items they'd use.
                        </div>
                    </q-card-section>
                    <q-separator />
                    <div v-if="rescue.recipes.length === 0" class="q-pa-md text-caption dora-text-muted">
                        No recipes in your library use any of these items.
                    </div>
                    <q-list v-else separator>
                        <q-item
                            v-for="recipe in rescue.recipes"
                            :key="recipe.recipe_id"
                            clickable
                            @click="openRecipe(recipe.recipe_id)"
                        >
                            <q-item-section>
                                <q-item-label>
                                    <q-icon
                                        v-if="recipe.is_favourite"
                                        name="star"
                                        size="14px"
                                        color="warning"
                                        class="q-mr-xs"
                                    />
                                    {{ recipe.name }}
                                </q-item-label>
                                <q-item-label caption>
                                    Uses {{ recipe.matching_count }} at-risk item{{ recipe.matching_count === 1 ? '' : 's' }}:
                                    {{ recipe.matching_expiring_items.join(', ') }}
                                </q-item-label>
                                <q-item-label
                                    v-if="recipe.missing_ingredients.length > 0"
                                    caption
                                    class="dora-text-muted"
                                >
                                    Missing: {{ recipe.missing_ingredients.join(', ') }}
                                </q-item-label>
                            </q-item-section>
                            <q-item-section side>
                                <div class="text-caption dora-text-muted">
                                    {{ recipe.cook_time_minutes ? `${recipe.cook_time_minutes} min` : '' }}
                                </div>
                            </q-item-section>
                        </q-item>
                    </q-list>
                </q-card>
            </div>
        </div>

        <!-- Insights strip ─────────────────────────────────────────── -->
        <q-card v-if="insights && insights.total_events > 0" flat bordered class="q-mt-lg">
            <q-card-section>
                <div class="text-subtitle1">
                    What you've been wasting (last {{ insights.window_days }} days)
                </div>
                <div class="text-caption dora-text-muted">
                    {{ insights.total_events }} event{{ insights.total_events === 1 ? '' : 's' }} logged
                    <span v-if="insights.total_estimated_value > 0">
                        · ~${{ insights.total_estimated_value.toFixed(2) }} in food
                    </span>
                </div>
            </q-card-section>
            <q-separator />
            <q-list separator dense>
                <q-item v-for="row in insights.by_item.slice(0, 6)" :key="row.stock_item_name">
                    <q-item-section>
                        <q-item-label>{{ row.stock_item_name }}</q-item-label>
                        <q-item-label caption>
                            {{ row.event_count }}× ·
                            {{ Object.keys(row.reasons).join(', ') }}
                        </q-item-label>
                    </q-item-section>
                    <q-item-section side v-if="row.estimated_value > 0">
                        <div class="dora-text-muted">~${{ row.estimated_value.toFixed(2) }}</div>
                    </q-item-section>
                </q-item>
            </q-list>
        </q-card>

        <!-- Log-waste dialog -->
        <BaseDialog v-model="wasteDialogOpen" title="Log as wasted" closable card-style="min-width: 320px">
                <q-card-section v-if="wasteTarget">
                    <div class="text-caption dora-text-muted">
                        {{ wasteTarget.name }}
                    </div>
                </q-card-section>
                <q-card-section class="q-gutter-sm">
                    <q-select
                        v-model="wasteDraft.reason"
                        :options="REASON_OPTIONS"
                        emit-value
                        map-options
                        dense
                        outlined
                        label="Reason"
                    />
                    <q-input
                        v-model.number="wasteDraft.estimated_value"
                        dense
                        outlined
                        type="number"
                        step="0.01"
                        min="0"
                        label="Estimated value (optional)"
                        prefix="$"
                    />
                    <q-input
                        v-model="wasteDraft.note"
                        dense
                        outlined
                        type="textarea"
                        autogrow
                        label="Note (optional)"
                    />
                    <q-toggle
                        v-model="wasteDraft.mark_out_of_stock"
                        label="Also mark as Out of Stock"
                    />
                </q-card-section>
                <template #actions>
                    <q-btn flat no-caps label="Cancel" v-close-popup />
                    <q-btn
                        unelevated
                        color="negative"
                        no-caps
                        label="Log waste"
                        :loading="wasteSaving"
                        @click="submitWaste"
                    />
                </template>
        </BaseDialog>
    </q-page>
</template>

<script lang="ts" setup>
    import { useQuasar } from 'quasar';
    import { ICONS } from 'src/style/icons';
    import BaseDialog from 'src/components/BaseDialog.vue';
    import { describeApiError } from 'src/services/errorHandling/apiErrorHandler';
    import {
        findLevelBySequence,
        OUT_OF_STOCK_SEQUENCE,
    } from 'src/helpers/stockStatus';
    import StockItemApiService from 'src/services/api/stockItemApiService';
    import { useStockLevelStore } from 'src/stores/stockLevelStore';
    import { useStockItemStore } from 'src/stores/stockItemStore';
    import WasteApiService, {
        type ExpiringItem,
        type WasteInsights,
        type WasteRescue,
        type WasteReason,
    } from 'src/services/api/wasteApiService';
    import { computed, onMounted, reactive, ref } from 'vue';
    import { useRouter } from 'vue-router';

    const $q = useQuasar();
    const router = useRouter();
    const wasteApi = new WasteApiService();
    const stockItemApi = new StockItemApiService();
    const stockLevelStore = useStockLevelStore();
    const stockItemStore = useStockItemStore();

    const HORIZON_OPTIONS = [3, 7, 14, 30];
    const REASON_OPTIONS: Array<{ label: string; value: WasteReason }> = [
        { label: 'Expired', value: 'expired' },
        { label: 'Spoiled', value: 'spoiled' },
        { label: 'Did not like', value: 'did_not_like' },
        { label: 'Bought too much', value: 'overbought' },
        { label: 'Other', value: 'other' },
    ];

    const horizonDays = ref<number>(7);
    const rescue = ref<WasteRescue | null>(null);
    const insights = ref<WasteInsights | null>(null);
    const loading = ref(false);
    const loadError = ref<string | null>(null);
    const busyItemId = ref<string | null>(null);
    const busyAction = ref<'used' | 'freeze' | null>(null);

    const wasteDialogOpen = ref(false);
    const wasteTarget = ref<ExpiringItem | null>(null);
    const wasteSaving = ref(false);
    const wasteDraft = reactive<{
        reason: WasteReason;
        estimated_value: number | null;
        note: string | null;
        mark_out_of_stock: boolean;
    }>({
        reason: 'expired',
        estimated_value: null,
        note: null,
        mark_out_of_stock: true,
    });

    const totalValueAtRisk = computed(() =>
        (rescue.value?.items ?? []).reduce(
            (sum, item) => sum + (item.estimated_value ?? 0),
            0,
        ),
    );

    function setHorizon(days: number) {
        if (horizonDays.value === days) return;
        horizonDays.value = days;
        void loadRescue();
    }

    async function loadRescue() {
        loading.value = true;
        loadError.value = null;
        try {
            const [r, i] = await Promise.all([
                wasteApi.getRescueAsync(horizonDays.value),
                wasteApi.getInsightsAsync(90).catch(() => null),
            ]);
            rescue.value = r;
            insights.value = i;
        } catch (err) {
            loadError.value = `Could not load: ${describeApiError(err)}`;
        } finally {
            loading.value = false;
        }
    }

    function daysLabel(item: ExpiringItem): string {
        if (item.is_expired) return `Expired ${Math.abs(item.days_until_expiry)}d ago`;
        if (item.days_until_expiry === 0) return 'Expires today';
        if (item.days_until_expiry === 1) return 'Expires tomorrow';
        return `Expires in ${item.days_until_expiry} days`;
    }

    function dotColorFor(item: ExpiringItem): string {
        if (item.is_expired) return 'negative';
        if (item.days_until_expiry <= 2) return 'orange';
        return 'grey';
    }

    function openItem(stockItemId: string) {
        void router.push(`/stock/${stockItemId}`);
    }

    function openRecipe(recipeId: string) {
        void router.push(`/cookbook/${recipeId}`);
    }

    async function markUsed(item: ExpiringItem) {
        // "Used" = clear expiry + bump stock level to Out of Stock. We
        // mirror the existing one-tap-finish pattern: optimistic UI is
        // skipped here because the page reloads from the source after.
        busyItemId.value = item.stock_item_id;
        busyAction.value = 'used';
        try {
            await stockLevelStore.ensureLoadedAsync();
            const outLevel = findLevelBySequence(
                stockLevelStore.stockLevels,
                OUT_OF_STOCK_SEQUENCE,
            );
            await stockItemApi.updateAsync({
                stock_item_id: item.stock_item_id,
                expiry_date: null,
                ...(outLevel ? { stock_level_id: outLevel.stock_level_id } : {}),
            });
            // Keep the store in sync — other pages cache stock levels.
            await stockItemStore.getStockItemsAsync();
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: `Marked ${item.name} as used.`,
            });
            await loadRescue();
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not update.',
                caption: describeApiError(err) || '',
            });
        } finally {
            busyItemId.value = null;
            busyAction.value = null;
        }
    }

    async function markFrozen(item: ExpiringItem) {
        // "Freeze" = clear the expiry date. The user's moved it to the
        // freezer and the printed expiry no longer applies; they can set
        // a new one later if they want. Audit trail (per the original
        // P2-06 spec) is out of scope here — kept intentionally simple.
        busyItemId.value = item.stock_item_id;
        busyAction.value = 'freeze';
        try {
            await stockItemApi.updateAsync({
                stock_item_id: item.stock_item_id,
                expiry_date: null,
            });
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: `Cleared expiry on ${item.name}.`,
            });
            await loadRescue();
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not update.',
                caption: describeApiError(err) || '',
            });
        } finally {
            busyItemId.value = null;
            busyAction.value = null;
        }
    }

    function openWasteDialog(item: ExpiringItem) {
        wasteTarget.value = item;
        wasteDraft.reason = item.is_expired ? 'expired' : 'spoiled';
        // Pre-fill the value from whatever the rescue endpoint estimated
        // so most users can just hit Save without typing a number.
        wasteDraft.estimated_value = item.estimated_value;
        wasteDraft.note = null;
        wasteDraft.mark_out_of_stock = true;
        wasteDialogOpen.value = true;
    }

    async function submitWaste() {
        if (!wasteTarget.value) return;
        wasteSaving.value = true;
        try {
            await wasteApi.logEventAsync({
                stock_item_id: wasteTarget.value.stock_item_id,
                reason: wasteDraft.reason,
                estimated_value: wasteDraft.estimated_value,
                note: wasteDraft.note,
                mark_out_of_stock: wasteDraft.mark_out_of_stock,
            });
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: `Logged ${wasteTarget.value.name} as wasted.`,
            });
            wasteDialogOpen.value = false;
            await loadRescue();
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not log waste event.',
                caption: describeApiError(err) || '',
            });
        } finally {
            wasteSaving.value = false;
        }
    }

    onMounted(() => {
        void loadRescue();
    });
</script>

<style scoped>
    .waste-row {
        padding-top: 8px;
        padding-bottom: 8px;
    }
    .waste-item-name {
        color: inherit;
        text-decoration: none;
        font-weight: 500;
    }
    .waste-item-name:hover {
        text-decoration: underline;
    }
    .waste-horizon-btn {
        text-decoration: underline dotted;
    }
</style>
