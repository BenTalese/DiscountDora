<template>
    <div>
        <q-btn flat round dense :icon="bellIcon" :color="bellColor" @click="open = true">
            <q-badge
                v-if="badgeCount > 0"
                floating
                color="negative"
                text-color="white"
                rounded
            >
                {{ badgeCount }}
            </q-badge>
            <q-tooltip>
                {{
                    totalCount === 0
                        ? 'Nothing needs your attention'
                        : `${totalCount} thing${totalCount === 1 ? '' : 's'} need attention`
                }}
            </q-tooltip>
        </q-btn>

        <q-dialog v-model="open" position="right" full-height seamless>
            <q-card class="alerts-panel column no-wrap" flat>
                <q-card-section class="row items-center q-pb-none">
                    <q-icon name="notifications" size="22px" class="q-mr-sm" />
                    <div class="col">
                        <div class="text-h6">What needs your attention</div>
                        <div class="text-caption text-grey">
                            <span v-if="totalCount === 0 && snoozedCount === 0">
                                All quiet. Good work.
                            </span>
                            <span v-else>
                                {{ alerts.high_count }} high ·
                                {{ alerts.medium_count }} medium ·
                                {{ alerts.low_count }} low
                                <span v-if="snoozedCount > 0">
                                    · {{ snoozedCount }} snoozed
                                </span>
                            </span>
                        </div>
                    </div>
                    <q-btn flat round dense icon="refresh" :loading="loading" @click="refresh" />
                    <q-btn flat round dense icon="close" @click="open = false" />
                </q-card-section>

                <q-separator class="q-mt-sm" />

                <q-banner v-if="loadError" class="bg-red-1 text-red-9 q-ma-md" dense rounded>
                    {{ loadError }}
                </q-banner>

                <!-- ── Grouped list (scrolls) ────────────────────────────── -->
                <div class="alerts-panel-list col scroll">
                    <template
                        v-for="group in groups"
                        :key="group.severity"
                    >
                        <div
                            v-if="group.items.length > 0"
                            class="alerts-group"
                        >
                            <div
                                class="alerts-group-head row items-center"
                                :class="`alerts-group-head--${group.severity}`"
                            >
                                <q-icon :name="group.icon" size="16px" class="q-mr-xs" />
                                {{ group.label }}
                                <q-chip dense outline size="sm" class="q-ml-sm">
                                    {{ group.items.length }}
                                </q-chip>
                            </div>
                            <q-list separator>
                                <q-item
                                    v-for="alert in group.items"
                                    :key="alert.alert_id"
                                    clickable
                                    @click="goToItem(alert.stock_item_id)"
                                >
                                    <q-item-section avatar>
                                        <q-avatar
                                            :color="colorFor(alert.severity)"
                                            text-color="white"
                                            size="36px"
                                        >
                                            <q-icon :name="iconFor(alert.kind)" />
                                        </q-avatar>
                                    </q-item-section>
                                    <q-item-section>
                                        <q-item-label class="text-weight-medium">
                                            {{ alert.message }}
                                        </q-item-label>
                                        <q-item-label caption>
                                            <span v-if="alert.detail">{{ alert.detail }}</span>
                                            <span v-if="alert.related_date">
                                                · {{ formatDate(alert.related_date) }}
                                            </span>
                                        </q-item-label>
                                        <div class="row q-gutter-xs q-mt-xs items-center wrap">
                                            <!-- Same inline actions as the chip's overflow menu
                                                 elsewhere; routed through act_on_alert backend. -->
                                            <q-btn
                                                v-for="action in actionsFor(alert.kind)"
                                                :key="action.action"
                                                size="sm"
                                                dense
                                                outline
                                                no-caps
                                                :icon="action.icon"
                                                :label="action.label"
                                                :loading="busy === alert.alert_id"
                                                @click.stop="apply(alert, action.action)"
                                            />
                                            <!-- View-in-context: deep-link into Stock with the
                                                 right filters pre-applied for this kind. -->
                                            <q-btn
                                                size="sm"
                                                dense
                                                outline
                                                no-caps
                                                icon="filter_list"
                                                label="View in context"
                                                @click.stop="viewInContext(alert)"
                                            />
                                            <!-- Snooze: hide for 7 days client-side. The alert
                                                 will re-surface if its underlying state still
                                                 holds at that point. -->
                                            <q-btn
                                                size="sm"
                                                dense
                                                flat
                                                no-caps
                                                icon="snooze"
                                                label="Snooze 7d"
                                                @click.stop="snooze(alert)"
                                            >
                                                <q-tooltip>
                                                    Hide for 7 days on this device.
                                                </q-tooltip>
                                            </q-btn>
                                        </div>
                                    </q-item-section>
                                </q-item>
                            </q-list>
                        </div>
                    </template>

                    <!-- Snoozed group at the bottom — collapsed by default,
                         expand to peek at what's been kicked down the road. -->
                    <q-expansion-item
                        v-if="snoozedCount > 0"
                        class="alerts-snoozed-section"
                        icon="snooze"
                        :label="`Snoozed (${snoozedCount})`"
                        header-class="text-grey-7"
                    >
                        <q-list separator>
                            <q-item
                                v-for="alert in snoozedAlerts"
                                :key="alert.alert_id"
                                clickable
                                @click="goToItem(alert.stock_item_id)"
                            >
                                <q-item-section avatar>
                                    <q-avatar
                                        :color="colorFor(alert.severity)"
                                        text-color="white"
                                        size="32px"
                                    >
                                        <q-icon :name="iconFor(alert.kind)" size="16px" />
                                    </q-avatar>
                                </q-item-section>
                                <q-item-section>
                                    <q-item-label>{{ alert.message }}</q-item-label>
                                    <q-item-label caption>
                                        Snoozed until {{ formatDate(snoozedUntilOf(alert)) }}
                                    </q-item-label>
                                </q-item-section>
                                <q-item-section side>
                                    <q-btn
                                        flat
                                        dense
                                        no-caps
                                        size="sm"
                                        icon="undo"
                                        label="Unsnooze"
                                        @click.stop="unsnooze(alert)"
                                    />
                                </q-item-section>
                            </q-item>
                        </q-list>
                    </q-expansion-item>

                    <q-item v-if="!loading && totalCount === 0 && snoozedCount === 0">
                        <q-item-section class="text-center text-grey q-py-lg">
                            <q-icon name="check_circle" size="48px" color="positive" />
                            <div class="q-mt-sm">Nothing to do right now.</div>
                        </q-item-section>
                    </q-item>
                </div>

                <!-- ── Bottom action: add all low/out to primary list ────── -->
                <q-separator v-if="lowOrOutStockItemIds.length > 0" />
                <q-card-section
                    v-if="lowOrOutStockItemIds.length > 0"
                    class="bg-grey-1 q-py-sm"
                >
                    <q-btn
                        unelevated
                        color="primary"
                        no-caps
                        icon="add_shopping_cart"
                        :label="`Add ${lowOrOutStockItemIds.length} low/out item${
                            lowOrOutStockItemIds.length === 1 ? '' : 's'
                        } to primary list`"
                        class="full-width"
                        :loading="addingAll"
                        @click="addAllLowOrOutToPrimary"
                    />
                    <div class="text-caption text-grey q-mt-xs">
                        Skips items already on your primary list.
                    </div>
                </q-card-section>
            </q-card>
        </q-dialog>
    </div>
</template>

<script lang="ts" setup>
    import { useQuasar } from 'quasar';
    import { useShoppingListActions } from 'src/composables/useShoppingListActions';
    import {
        actionsFor,
        colorFor,
        iconFor,
        type Alert,
        type AlertAction,
        type AlertSeverity,
    } from 'src/models/alert';
    import AlertApiService from 'src/services/api/alertApiService';
    import { useAlertStore } from 'src/stores/alertStore';
    import { useShoppingListStore } from 'src/stores/shoppingListStore';
    import { computed, onMounted, onUnmounted, ref } from 'vue';
    import { useRouter } from 'vue-router';

    const $q = useQuasar();
    const router = useRouter();
    const alertStore = useAlertStore();
    const shoppingListStore = useShoppingListStore();
    const { addItems } = useShoppingListActions();
    const api = new AlertApiService();

    const open = ref(false);
    const busy = ref<string | null>(null);
    const addingAll = ref(false);

    const alerts = computed(() => alertStore.alerts);
    const loading = computed(() => alertStore.loading);
    const loadError = computed(() => alertStore.loadError);
    const badgeCount = computed(() => alertStore.badgeCount);
    const totalCount = computed(() => alertStore.totalCount);
    const snoozedCount = computed(() => alertStore.snoozedCount);
    const snoozedAlerts = computed(() => alertStore.snoozedAlerts);

    const bellIcon = computed(() =>
        badgeCount.value > 0 ? 'notifications_active' : 'notifications'
    );
    const bellColor = computed(() => {
        if (alerts.value.high_count > 0) return 'negative';
        if (alerts.value.medium_count > 0) return 'warning';
        return undefined;
    });

    // Group-by-severity buckets so the panel scans visually rather than
    // forcing the eye to walk the list looking for the red rows.
    type Group = {
        severity: AlertSeverity;
        label: string;
        icon: string;
        items: Alert[];
    };
    const groups = computed<Group[]>(() => {
        const buckets: Record<AlertSeverity, Alert[]> = { high: [], medium: [], low: [] };
        for (const a of alerts.value.items) {
            buckets[a.severity].push(a);
        }
        return [
            { severity: 'high', label: 'High priority', icon: 'priority_high', items: buckets.high },
            { severity: 'medium', label: 'Medium', icon: 'warning', items: buckets.medium },
            { severity: 'low', label: 'Low / FYI', icon: 'info', items: buckets.low },
        ];
    });

    // Stock items currently flagged by a low/out (or essential-out/essential-low)
    // alert. De-duplicated so the bulk-add button doesn't queue the same item
    // twice when an essential is also separately out.
    const lowOrOutKinds = new Set<string>([
        'low_stock',
        'out_of_stock',
        'essential_low',
    ]);
    const lowOrOutStockItemIds = computed<string[]>(() => [
        ...new Set(
            alerts.value.items
                .filter((a) => lowOrOutKinds.has(a.kind))
                .map((a) => a.stock_item_id),
        ),
    ]);

    function formatDate(iso: string): string {
        try {
            return new Date(iso).toLocaleDateString();
        } catch {
            return iso;
        }
    }

    async function refresh() {
        await alertStore.refreshAsync();
    }

    function goToItem(id: string) {
        open.value = false;
        void router.push(`/stock/${id}`);
    }

    // ── View in context ─────────────────────────────────────────────
    // Maps an alert kind to the StockOverview filter combo that surfaces
    // *just the items in that bucket*. The page hydrates these filters
    // from the query (P3 wired it up), so we keep the mapping client-side.
    function viewInContext(_alert: Alert) {
        // Stock's `attention` filter already collects expiring / low / out /
        // flagged items in one bucket, so for every alert kind we land the
        // user on the same filtered slice and let them eyeball which row
        // is theirs. If a future iteration wants per-kind slicing (e.g.
        // expiry vs stocktake), the StockOverview hydrator from P3 reads
        // the appropriate query params and we can extend here.
        open.value = false;
        void router.push({ path: '/stock', query: { attention: 'true' } });
    }

    // ── Inline alert actions (extend/reset/restocked/acknowledge) ───
    async function apply(alert: Alert, action: AlertAction) {
        busy.value = alert.alert_id;
        try {
            await api.applyActionAsync(alert.alert_id, action);
            await alertStore.refreshAsync();
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: 'Done.',
            });
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not apply.',
                caption: String(err),
            });
        } finally {
            busy.value = null;
        }
    }

    // ── Snooze / unsnooze ───────────────────────────────────────────
    function snooze(alert: Alert) {
        alertStore.snoozeAlert(alert.alert_id, 7);
        $q.notify({
            type: 'info',
            position: 'bottom-right',
            message: `Snoozed "${alert.stock_item_name}" for 7 days.`,
            actions: [
                {
                    label: 'Undo',
                    color: 'white',
                    handler: () => alertStore.unsnoozeAlert(alert.alert_id),
                },
            ],
        });
    }
    function unsnooze(alert: Alert) {
        alertStore.unsnoozeAlert(alert.alert_id);
    }
    function snoozedUntilOf(alert: Alert): string {
        return alertStore.snoozedUntil(alert.alert_id) ?? '';
    }

    // ── Add all low/out items to primary list ───────────────────────
    async function addAllLowOrOutToPrimary() {
        const ids = lowOrOutStockItemIds.value;
        if (ids.length === 0) return;
        const primary = shoppingListStore.primaryListId;
        if (!primary) {
            $q.dialog({
                title: 'No primary list',
                message:
                    'Set a primary shopping list first — the bell uses it for the bulk-add shortcut.',
                ok: { label: 'Open lists', color: 'primary', noCaps: true },
                cancel: { noCaps: true },
            }).onOk(() => {
                open.value = false;
                void router.push('/shopping-lists');
            });
            return;
        }
        addingAll.value = true;
        try {
            await addItems(
                primary,
                ids.map((stock_item_id) => ({ stock_item_id })),
            );
        } finally {
            addingAll.value = false;
        }
    }

    // Poll every 60s so the bell stays roughly fresh without hammering.
    // Refreshing the page also picks up changes; this is just so the bell
    // doesn't get stale while the user is mid-flow.
    let pollHandle: ReturnType<typeof setInterval> | null = null;

    onMounted(async () => {
        await alertStore.refreshAsync();
        pollHandle = setInterval(() => {
            void alertStore.refreshAsync();
        }, 60_000);
    });

    onUnmounted(() => {
        if (pollHandle) clearInterval(pollHandle);
    });
</script>

<style scoped>
    .alerts-panel {
        width: 480px;
        max-width: 100vw;
        height: 100%;
    }
    .alerts-panel-list {
        max-height: 100%;
        overflow-y: auto;
    }
    .alerts-group + .alerts-group {
        margin-top: 4px;
    }
    .alerts-group-head {
        padding: 8px 16px 4px;
        font-size: 0.78rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: var(--q-grey-7);
        background: rgba(0, 0, 0, 0.02);
    }
    .alerts-group-head--high {
        color: var(--q-negative);
        background: rgba(244, 67, 54, 0.06);
    }
    .alerts-group-head--medium {
        color: var(--q-warning);
        background: rgba(255, 152, 0, 0.06);
    }
    .alerts-group-head--low {
        color: var(--q-grey-7);
    }
    .alerts-snoozed-section {
        border-top: 1px solid rgba(0, 0, 0, 0.08);
    }
</style>
