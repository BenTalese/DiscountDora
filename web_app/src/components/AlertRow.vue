<template>
    <q-item clickable class="alert-row" @click="emit('open')">
        <q-item-section avatar top>
            <q-avatar :color="colorFor(alert.severity)" text-color="white" size="32px">
                <q-icon :name="iconFor(alert.kind)" size="16px" />
            </q-avatar>
        </q-item-section>

        <q-item-section>
            <q-item-label class="text-weight-medium">{{ alert.message }}</q-item-label>
            <q-item-label caption>
                <span v-if="alert.amount !== null">{{ formatMoney(alert.amount) }}</span>
                <span v-if="alert.amount !== null && alert.detail"> · </span>
                <span v-if="alert.detail">{{ alert.detail }}</span>
                <span v-if="alert.related_date"> · {{ formatDate(alert.related_date) }}</span>
                <span v-if="alert.snoozed_until"> · Snoozed until {{ formatDate(alert.snoozed_until) }}</span>
            </q-item-label>

            <!-- Owner 2026-10-15 — two rows. The top acts on the thing the alert
                 is about; the bottom acts on the alert. `@click.stop` so a
                 button never also opens the row. -->
            <div v-if="hasItemActions" class="alert-row__actions" @click.stop>
                <BaseButton
                    v-for="action in serverActions"
                    :key="action.action"
                    variant="secondary"
                    size="sm"
                    dense
                    :icon="action.icon"
                    :label="action.label"
                    :loading="busy"
                    @click="emit('action', action.action)"
                />
                <template v-if="stockControls">
                    <StockLevelPicker
                        :level-id="currentLevelId"
                        :label="`Change the level of ${alert.stock_item_name ?? 'this item'}`"
                        @select="(id: string) => emit('set-level', id)"
                    />
                    <AddToListButton variant="row" :stock-item-id="alert.stock_item_id!" />
                </template>
                <BaseButton
                    v-if="navTarget"
                    variant="secondary"
                    size="sm"
                    dense
                    :icon="nav!.icon"
                    :label="nav!.label"
                    @click="emit('navigate', navTarget)"
                />
            </div>

            <div class="alert-row__actions alert-row__actions--alert" @click.stop>
                <BaseButton
                    v-if="alert.snoozed_until"
                    variant="ghost"
                    size="sm"
                    dense
                    :icon="ICONS.undo"
                    label="Unsnooze"
                    @click="emit('unsnooze')"
                />
                <BaseButton
                    v-else
                    variant="ghost"
                    size="sm"
                    dense
                    :icon="ICONS.snooze"
                    label="Snooze 7d"
                    @click="emit('snooze')"
                >
                    <BaseTooltip>Hide for 7 days.</BaseTooltip>
                </BaseButton>
                <BaseButton
                    variant="ghost"
                    size="sm"
                    dense
                    :icon="ICONS.close"
                    label="Dismiss"
                    @click="emit('dismiss')"
                >
                    <BaseTooltip>Gone until this happens again.</BaseTooltip>
                </BaseButton>
            </div>
        </q-item-section>
    </q-item>
</template>

<script lang="ts" setup>
    import BaseTooltip from 'src/components/BaseTooltip.vue';
    import BaseButton from 'src/components/BaseButton.vue';
    import AddToListButton from 'src/components/AddToListButton.vue';
    import StockLevelPicker from 'src/components/stock/StockLevelPicker.vue';
    import { formatDate as formatLocaleDate } from 'src/composables/useDateFormat';
    import { formatMoney } from 'src/composables/useMoney';
    import { ICONS } from 'src/style/icons';
    import {
        ALERT_KIND_META, actionsFor, colorFor, iconFor, type Alert, type AlertAction,
    } from 'src/models/alert';
    import { useStockItemStore } from 'src/stores/stockItemStore';
    import { computed } from 'vue';

    // The one alert row (R-001). Presentational: it renders the alert and its
    // two button rows and *emits* what the user wants done; the bell owns the
    // store/API side effects. The level picker and the cart are the shared
    // controls the stock row uses, so a shortage is handled here the same way.
    const props = defineProps<{
        alert: Alert;
        /** A server action for THIS alert is in flight. */
        busy?: boolean;
    }>();

    const emit = defineEmits<{
        (e: 'open'): void;
        (e: 'action', action: AlertAction): void;
        (e: 'set-level', levelId: string): void;
        (e: 'navigate', to: string): void;
        (e: 'snooze'): void;
        (e: 'unsnooze'): void;
        (e: 'dismiss'): void;
    }>();

    // `?? []` / `?.` are load-bearing: the backend can ship a kind the client
    // doesn't know yet (the 2026-07-09 crash), and that must degrade to a row
    // with only the alert's own buttons.
    const serverActions = computed(() => actionsFor(props.alert.kind) ?? []);
    const nav = computed(() => ALERT_KIND_META[props.alert.kind]?.nav ?? null);
    const navTarget = computed(() => nav.value?.to(props.alert) ?? null);
    const stockControls = computed(
        () => !!ALERT_KIND_META[props.alert.kind]?.stockControls && !!props.alert.stock_item_id,
    );
    const hasItemActions = computed(
        () => serverActions.value.length > 0 || !!navTarget.value || stockControls.value,
    );

    const stockItemStore = useStockItemStore();
    const currentLevelId = computed(() => stockItemStore.stockItems.find(
        (s) => s.stock_item_id === props.alert.stock_item_id,
    )?.stock_level_id ?? null);

    function formatDate(iso: string): string {
        // DR-14: household-locale date (falls back to the raw value if unparseable).
        return formatLocaleDate(iso) || iso;
    }
</script>

<style scoped>
    .alert-row__actions {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: var(--space-1);
        margin-top: var(--space-2);
    }
    .alert-row__actions--alert {
        margin-top: var(--space-1);
    }
</style>
