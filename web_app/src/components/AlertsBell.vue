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
            <q-card class="alerts-panel" flat>
                <q-card-section class="row items-center q-pb-none">
                    <q-icon name="notifications" size="22px" class="q-mr-sm" />
                    <div class="col">
                        <div class="text-h6">What needs your attention</div>
                        <div class="text-caption text-grey">
                            <span v-if="totalCount === 0">All quiet. Good work.</span>
                            <span v-else>
                                {{ alerts.high_count }} high ·
                                {{ alerts.medium_count }} medium ·
                                {{ alerts.low_count }} low
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

                <q-list separator class="alerts-panel-list">
                    <q-item
                        v-for="alert in alerts.items"
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
                            <div class="row q-gutter-xs q-mt-xs">
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
                                    @click.stop="apply(alert.alert_id, action.action)"
                                />
                            </div>
                        </q-item-section>
                    </q-item>

                    <q-item v-if="!loading && alerts.items.length === 0">
                        <q-item-section class="text-center text-grey q-py-lg">
                            <q-icon name="check_circle" size="48px" color="positive" />
                            <div class="q-mt-sm">Nothing to do right now.</div>
                        </q-item-section>
                    </q-item>
                </q-list>
            </q-card>
        </q-dialog>
    </div>
</template>

<script lang="ts" setup>
    import { useQuasar } from 'quasar';
    import {
        actionsFor,
        colorFor,
        iconFor,
        type AlertAction,
    } from 'src/models/alert';
    import AlertApiService from 'src/services/api/alertApiService';
    import { useAlertStore } from 'src/stores/alertStore';
    import { computed, onMounted, onUnmounted, ref } from 'vue';
    import { useRouter } from 'vue-router';

    const $q = useQuasar();
    const router = useRouter();
    const alertStore = useAlertStore();
    const api = new AlertApiService();

    const open = ref(false);
    const busy = ref<string | null>(null);

    const alerts = computed(() => alertStore.alerts);
    const loading = computed(() => alertStore.loading);
    const loadError = computed(() => alertStore.loadError);
    const badgeCount = computed(() => alertStore.badgeCount);
    const totalCount = computed(() => alertStore.totalCount);

    const bellIcon = computed(() =>
        badgeCount.value > 0 ? 'notifications_active' : 'notifications'
    );
    const bellColor = computed(() => {
        if (alerts.value.high_count > 0) return 'negative';
        if (alerts.value.medium_count > 0) return 'warning';
        return undefined;
    });

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

    async function apply(alertId: string, action: AlertAction) {
        busy.value = alertId;
        try {
            await api.applyActionAsync(alertId, action);
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
        width: 420px;
        max-width: 100vw;
        height: 100%;
    }
    .alerts-panel-list {
        max-height: calc(100vh - 96px);
        overflow-y: auto;
    }
</style>
