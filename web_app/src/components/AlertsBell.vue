<template>
    <div>
        <BaseButton variant="icon" :icon="bellIcon" :color="bellColor" @click="open = true">
            <q-badge v-if="badgeCount > 0" floating color="negative" text-color="white" rounded>
                {{ badgeCount }}
            </q-badge>
            <q-tooltip>
                {{
                    totalCount === 0
                        ? 'Nothing needs your attention'
                        : `${totalCount} thing${totalCount === 1 ? '' : 's'} need attention`
                }}
            </q-tooltip>
        </BaseButton>

        <q-dialog v-model="open" position="right" full-height seamless>
            <q-card class="alerts-panel column no-wrap" flat>
                <q-card-section class="row items-center q-pb-none">
                    <q-icon :name="ICONS.notifications" size="22px" class="q-mr-sm" />
                    <div class="col">
                        <div class="text-h6">What needs your attention</div>
                        <div class="text-caption dora-text-muted">
                            <span v-if="totalCount === 0 && snoozedCount === 0">
                                All quiet. Good work.
                            </span>
                            <span v-else>
                                {{ alerts.actionable_count }} need action ·
                                {{ alerts.fyi_count }} FYI
                                <span v-if="snoozedCount > 0"> · {{ snoozedCount }} snoozed</span>
                            </span>
                        </div>
                    </div>
                    <BaseButton variant="icon" :icon="ICONS.refresh" :loading="loading" @click="refresh" />
                    <BaseButton variant="icon" :icon="ICONS.close" @click="open = false" />
                </q-card-section>

                <q-separator class="q-mt-sm" />

                <q-banner v-if="loadError" class="dora-bg-negative-soft text-negative q-ma-md" dense rounded>
                    {{ loadError }}
                </q-banner>

                <!-- ── Peek: top few rows (shared AlertRow, slim) ────────── -->
                <div class="alerts-panel-list col scroll">
                    <q-list separator>
                        <AlertRow
                            v-for="alert in peekItems"
                            :key="alert.alert_id"
                            :alert="alert"
                            :busy="busyAlertId === alert.alert_id"
                            slim
                            @open="goToItem(alert)"
                            @action="(action) => applyAction(alert, action)"
                            @toggle-read="(read) => toggleRead(alert, read)"
                        />
                    </q-list>

                    <div v-if="hiddenCount > 0" class="text-caption dora-text-muted q-pa-sm text-center">
                        + {{ hiddenCount }} more on the Alerts page
                    </div>

                    <q-item v-if="!loading && totalCount === 0 && snoozedCount === 0">
                        <q-item-section class="text-center dora-text-muted q-py-lg">
                            <q-icon :name="ICONS.check_circle" size="48px" color="positive" />
                            <div class="q-mt-sm">Nothing to do right now.</div>
                        </q-item-section>
                    </q-item>
                </div>

                <!-- ── Footer: bulk shortcut + jump to the hub ───────────── -->
                <q-separator />
                <q-card-section class="dora-bg-elevated q-py-sm column q-gutter-sm">
                    <BaseButton
                        v-if="lowOrOutStockItemIds.length > 0"
                        :icon="ICONS.add_shopping_cart"
                        :label="`Add ${lowOrOutStockItemIds.length} low/out item${
                            lowOrOutStockItemIds.length === 1 ? '' : 's'
                        } to primary list`"
                        class="full-width"
                        :loading="addingAll"
                        @click="addAllLowOrOutToPrimary"
                    />
                    <BaseButton
                        variant="secondary"
                        :icon="ICONS.open_in_new"
                        label="Open Alerts"
                        class="full-width"
                        @click="openHub"
                    />
                </q-card-section>
            </q-card>
        </q-dialog>
    </div>
</template>

<script lang="ts" setup>
    import BaseButton from 'src/components/BaseButton.vue';
    import { ICONS } from 'src/style/icons';
    import { useQuasar } from 'quasar';
    import { useShoppingListActions } from 'src/composables/useShoppingListActions';
    import AlertRow from 'src/components/AlertRow.vue';
    import { linkFor, type Alert } from 'src/models/alert';
    import { useAlertActions } from 'src/composables/useAlertActions';
    import { useAlertStore } from 'src/stores/alertStore';
    import { useShoppingListStore } from 'src/stores/shoppingListStore';
    import { computed, onMounted, onUnmounted, ref } from 'vue';
    import { useRouter } from 'vue-router';

    // The bell is a fast PEEK + jump (C-9.3): the top few rows + the bulk
    // shortcut, then "Open Alerts" → the hub page, which owns the rich
    // management/history/snoozed surfaces. Rows are the shared AlertRow (R-001)
    // so the bell and page never diverge.
    const PEEK_LIMIT = 5;

    const $q = useQuasar();
    const router = useRouter();
    const alertStore = useAlertStore();
    const shoppingListStore = useShoppingListStore();
    const { addItems } = useShoppingListActions();
    const { busyAlertId, applyAction } = useAlertActions();

    const open = ref(false);
    const addingAll = ref(false);

    const alerts = computed(() => alertStore.alerts);
    const loading = computed(() => alertStore.loading);
    const loadError = computed(() => alertStore.loadError);
    const badgeCount = computed(() => alertStore.badgeCount);
    const totalCount = computed(() => alertStore.totalCount);
    const snoozedCount = computed(() => alertStore.snoozedCount);

    const peekItems = computed<Alert[]>(() => alerts.value.items.slice(0, PEEK_LIMIT));
    const hiddenCount = computed(() => Math.max(0, alerts.value.items.length - peekItems.value.length));

    const bellIcon = computed(() =>
        badgeCount.value > 0 ? 'notifications_active' : 'notifications'
    );
    const bellColor = computed(() => {
        if (alerts.value.high_count > 0) return 'negative';
        if (alerts.value.medium_count > 0) return 'warning';
        return undefined;
    });

    // Stock items currently flagged low/out (de-duplicated) for the bulk-add.
    const lowOrOutKinds = new Set<string>(['low_stock', 'out_of_stock', 'essential_low']);
    const lowOrOutStockItemIds = computed<string[]>(() => [
        ...new Set(
            alerts.value.items
                .filter((a) => lowOrOutKinds.has(a.kind))
                .map((a) => a.stock_item_id)
                .filter((id): id is string => id !== null),
        ),
    ]);

    async function refresh() {
        await alertStore.refreshAsync();
    }

    function goToItem(alert: Alert) {
        const link = linkFor(alert);
        if (!link) return;
        open.value = false;
        void router.push(link);
    }

    function openHub() {
        open.value = false;
        void router.push('/alerts');
    }

    // The single in-context action kept on the peek row (mark-restocked /
    // push-expiry) is routed through the shared useAlertActions composable
    // (FU-521) so the bell, hub, and dashboard behave identically.

    async function toggleRead(alert: Alert, read: boolean) {
        if (read) await alertStore.markRead(alert.alert_id);
        else await alertStore.markUnread(alert.alert_id);
    }

    async function addAllLowOrOutToPrimary() {
        const ids = lowOrOutStockItemIds.value;
        if (ids.length === 0) return;
        const primary = shoppingListStore.quickAddTargetListId;
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
        width: 420px;
        max-width: 100vw;
        height: 100%;
    }
    .alerts-panel-list {
        max-height: 100%;
        overflow-y: auto;
    }
</style>
