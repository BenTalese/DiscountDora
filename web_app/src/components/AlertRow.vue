<template>
    <q-item
        clickable
        :class="{ 'alert-row--read': alert.read }"
        @click="emit('open')"
    >
        <q-item-section avatar>
            <q-avatar
                :color="colorFor(alert.severity)"
                text-color="white"
                :size="slim ? '32px' : '36px'"
            >
                <q-icon :name="iconFor(alert.kind)" :size="slim ? '16px' : undefined" />
            </q-avatar>
        </q-item-section>

        <q-item-section>
            <q-item-label :class="alert.read ? '' : 'text-weight-medium'">
                {{ alert.message }}
            </q-item-label>
            <q-item-label caption>
                <span v-if="alert.detail">{{ alert.detail }}</span>
                <span v-if="alert.related_date"> · {{ formatDate(alert.related_date) }}</span>
            </q-item-label>

            <!-- Action bar. `@click.stop` so tapping an action doesn't also
                 fire the row's open/navigate. -->
            <div class="row q-gutter-xs q-mt-xs items-center wrap" @click.stop>
                <BaseButton
                    v-for="action in inlineActions"
                    :key="action.action"
                    variant="secondary"
                    size="sm"
                    dense
                    :icon="action.icon"
                    :label="action.label"
                    :loading="busy"
                    @click="emit('action', action.action)"
                />
                <template v-if="!slim">
                    <BaseButton
                        variant="secondary"
                        size="sm"
                        dense
                        :icon="ICONS.filter_list"
                        label="View in context"
                        @click="emit('view-in-context')"
                    />
                    <BaseButton
                        variant="ghost"
                        size="sm"
                        dense
                        :icon="ICONS.snooze"
                        label="Snooze 7d"
                        @click="emit('snooze')"
                    >
                        <q-tooltip>Hide for 7 days.</q-tooltip>
                    </BaseButton>
                    <BaseButton
                        variant="ghost"
                        size="sm"
                        dense
                        :icon="ICONS.close"
                        label="Dismiss"
                        @click="emit('dismiss')"
                    >
                        <q-tooltip>Hide until it re-fires.</q-tooltip>
                    </BaseButton>
                </template>
                <BaseButton
                    variant="ghost"
                    size="sm"
                    dense
                    :icon="alert.read ? ICONS.undo : ICONS.mark_email_read"
                    :label="alert.read ? 'Unread' : 'Mark read'"
                    @click="emit('toggle-read', !alert.read)"
                />
            </div>
        </q-item-section>
    </q-item>
</template>

<script lang="ts" setup>
    import BaseButton from 'src/components/BaseButton.vue';
    import { ICONS } from 'src/style/icons';
    import { actionsFor, colorFor, iconFor, type Alert, type AlertAction } from 'src/models/alert';
    import { computed } from 'vue';

    // Shared alert row (C-9.3, R-001) — the single source of row markup for
    // both the bell peek and the hub page. Presentational: it renders the row +
    // its action bar and *emits* what the user wants done; the parent owns the
    // store/API side effects so there's no duplicated mutation logic (R-003).
    const props = defineProps<{
        alert: Alert;
        /** An action for THIS alert is in flight (parent passes busy === alert.alert_id). */
        busy?: boolean;
        /** Peek mode (bell): only the primary inline action + read toggle. */
        slim?: boolean;
    }>();

    const emit = defineEmits<{
        (e: 'open'): void;
        (e: 'action', action: AlertAction): void;
        (e: 'snooze'): void;
        (e: 'dismiss'): void;
        (e: 'toggle-read', read: boolean): void;
        (e: 'view-in-context'): void;
    }>();

    // Slim rows keep only the single most useful in-context action; the full
    // row shows every action the kind supports.
    const inlineActions = computed(() => {
        const all = actionsFor(props.alert.kind);
        return props.slim ? all.slice(0, 1) : all;
    });

    function formatDate(iso: string): string {
        const d = new Date(iso);
        return Number.isFinite(d.getTime()) ? d.toLocaleDateString() : iso;
    }
</script>

<style scoped>
    /* Read items recede so unread/new ones stand out (hub + bell). */
    .alert-row--read {
        opacity: 0.62;
    }
</style>
