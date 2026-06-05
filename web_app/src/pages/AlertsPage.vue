<template>
    <q-page padding>
        <div class="row items-center q-mb-md">
            <div class="col">
                <div class="text-h5">Alerts</div>
                <div class="text-caption dora-text-muted">
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
            <BaseButton
                variant="secondary"
                :icon="ICONS.refresh"
                label="Refresh"
                :loading="loading"
                @click="refresh"
            />
        </div>

        <q-banner v-if="loadError" class="dora-bg-negative-soft text-negative q-mb-md" dense rounded>
            {{ loadError }}
        </q-banner>

        <q-banner class="dora-bg-info-soft q-mb-md" dense rounded>
            Inline actions (snooze, mark-restocked, push expiry, view in context)
            live on the bell panel for now — open the bell from any page.
            The full alerts control centre is on the way.
        </q-banner>

        <div v-if="!loading && totalCount === 0 && snoozedCount === 0" class="row justify-center q-py-xl">
            <div class="column items-center dora-text-muted">
                <q-icon :name="ICONS.check_circle" size="48px" color="positive" />
                <div class="q-mt-sm">Nothing to do right now.</div>
            </div>
        </div>

        <template v-for="group in groups" :key="group.severity">
            <q-card v-if="group.items.length > 0" flat bordered class="q-mb-md">
                <q-card-section class="row items-center q-pb-sm">
                    <q-icon :name="group.icon" size="18px" class="q-mr-sm" />
                    <div class="text-subtitle1">{{ group.label }}</div>
                    <q-chip dense outline size="sm" class="q-ml-sm">
                        {{ group.items.length }}
                    </q-chip>
                </q-card-section>
                <q-separator />
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
                        </q-item-section>
                        <q-item-section side>
                            <q-icon :name="ICONS.chevron_right" />
                        </q-item-section>
                    </q-item>
                </q-list>
            </q-card>
        </template>

        <q-expansion-item
            v-if="snoozedCount > 0"
            :icon="ICONS.snooze"
            :label="`Snoozed (${snoozedCount})`"
            header-class="dora-text-secondary"
            class="q-mt-md"
        >
            <q-list separator bordered class="q-mt-sm">
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
                        <BaseButton
                            variant="ghost"
                            size="sm"
                            :icon="ICONS.undo"
                            label="Unsnooze"
                            @click.stop="alertStore.unsnoozeAlert(alert.alert_id)"
                        />
                    </q-item-section>
                </q-item>
            </q-list>
        </q-expansion-item>
    </q-page>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import BaseButton from 'src/components/BaseButton.vue';
    import {
        colorFor,
        iconFor,
        type Alert,
        type AlertSeverity,
    } from 'src/models/alert';
    import { useAlertStore } from 'src/stores/alertStore';
    import { computed, onMounted } from 'vue';
    import { useRouter } from 'vue-router';

    const router = useRouter();
    const alertStore = useAlertStore();

    const alerts = computed(() => alertStore.alerts);
    const loading = computed(() => alertStore.loading);
    const loadError = computed(() => alertStore.loadError);
    const totalCount = computed(() => alertStore.totalCount);
    const snoozedCount = computed(() => alertStore.snoozedCount);
    const snoozedAlerts = computed(() => alertStore.snoozedAlerts);

    type Group = {
        severity: AlertSeverity;
        label: string;
        icon: string;
        items: Alert[];
    };

    const groups = computed<Group[]>(() => {
        const buckets: Record<AlertSeverity, Alert[]> = { high: [], medium: [], low: [] };
        for (const a of alerts.value.items) buckets[a.severity].push(a);
        return [
            { severity: 'high', label: 'High', icon: ICONS.priority_high, items: buckets.high },
            { severity: 'medium', label: 'Medium', icon: ICONS.warning, items: buckets.medium },
            { severity: 'low', label: 'Low', icon: ICONS.info, items: buckets.low },
        ];
    });

    function snoozedUntilOf(alert: Alert): string {
        return alertStore.snoozedUntil(alert.alert_id) ?? '';
    }

    function formatDate(iso: string): string {
        if (!iso) return '';
        const d = new Date(iso);
        if (!Number.isFinite(d.getTime())) return iso;
        return d.toLocaleDateString();
    }

    function goToItem(stockItemId: string): void {
        void router.push(`/stock/${stockItemId}`);
    }

    async function refresh(): Promise<void> {
        await alertStore.refreshAsync();
    }

    onMounted(() => {
        if (alerts.value.items.length === 0 && !loading.value) void refresh();
    });
</script>
