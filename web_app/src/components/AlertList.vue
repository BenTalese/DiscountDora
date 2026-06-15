<template>
    <div>
        <template v-for="group in groups" :key="group.tier">
            <div v-if="group.items.length > 0" class="alert-tier">
                <div
                    class="alert-tier-head row items-center"
                    :class="`alert-tier-head--${group.tier}`"
                >
                    <q-icon :name="group.icon" size="16px" class="q-mr-xs" />
                    {{ group.label }}
                    <q-chip dense outline size="sm" class="q-ml-sm">{{ group.items.length }}</q-chip>
                </div>
                <q-list separator>
                    <AlertRow
                        v-for="alert in group.items"
                        :key="alert.alert_id"
                        :alert="alert"
                        :busy="busyId === alert.alert_id"
                        @open="emit('open', alert)"
                        @action="(action) => emit('action', alert, action)"
                        @snooze="emit('snooze', alert)"
                        @dismiss="emit('dismiss', alert)"
                        @toggle-read="(read) => emit('toggle-read', alert, read)"
                        @view-in-context="emit('view-in-context', alert)"
                    />
                </q-list>
            </div>
        </template>
    </div>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import AlertRow from 'src/components/AlertRow.vue';
    import { tierLabel, type Alert, type AlertAction, type AlertTier } from 'src/models/alert';
    import { computed } from 'vue';

    // Shared, tier-grouped alert list (C-9.3, R-001). Groups the active set into
    // the badge-counted "Needs action" tier and the quieter "FYI" tier, each row
    // a shared AlertRow. Re-emits AlertRow events tagged with their alert so the
    // parent (the hub page, later the dashboard card) owns the side effects.
    const props = defineProps<{
        alerts: Alert[];
        /** alert_id whose action is in flight, so only that row spins. */
        busyId?: string | null;
    }>();

    const emit = defineEmits<{
        (e: 'open', alert: Alert): void;
        (e: 'action', alert: Alert, action: AlertAction): void;
        (e: 'snooze', alert: Alert): void;
        (e: 'dismiss', alert: Alert): void;
        (e: 'toggle-read', alert: Alert, read: boolean): void;
        (e: 'view-in-context', alert: Alert): void;
    }>();

    type TierGroup = { tier: AlertTier; label: string; icon: string; items: Alert[] };

    const groups = computed<TierGroup[]>(() => {
        const buckets: Record<AlertTier, Alert[]> = { actionable: [], fyi: [] };
        for (const a of props.alerts) buckets[a.tier].push(a);
        return [
            { tier: 'actionable', label: tierLabel('actionable'), icon: ICONS.priority_high, items: buckets.actionable },
            { tier: 'fyi', label: tierLabel('fyi'), icon: ICONS.info, items: buckets.fyi },
        ];
    });
</script>

<style scoped>
    .alert-tier + .alert-tier {
        margin-top: 4px;
    }
    .alert-tier-head {
        padding: 8px 16px 4px;
        font-size: 0.78rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: var(--q-grey-7);
        background: var(--overlay-hover);
    }
    .alert-tier-head--actionable {
        color: var(--q-negative);
        background: var(--semantic-negative-soft);
    }
    .alert-tier-head--fyi {
        color: var(--q-grey-7);
    }
</style>
