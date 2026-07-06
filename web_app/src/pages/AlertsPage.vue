<template>
    <q-page padding>
        <!-- ── Header ─────────────────────────────────────────────────── -->
        <div class="row items-center q-mb-md">
            <div class="col">
                <div class="text-h5">Alerts</div>
                <div class="text-caption dora-text-muted">
                    <span v-if="totalCount === 0 && snoozedCount === 0">All quiet. Good work.</span>
                    <span v-else>
                        {{ alerts.actionable_count }} need action · {{ alerts.fyi_count }} FYI
                        <q-icon :name="ICONS.help_outline" size="14px" class="q-ml-xs">
                            <q-tooltip>
                                Needs action = things you should decide on soon
                                (expiring items, low stock, run-outs). FYI = things
                                worth knowing about but no decision required (price
                                drops, stocktake nudges).
                            </q-tooltip>
                        </q-icon>
                        <span v-if="snoozedCount > 0"> · {{ snoozedCount }} snoozed</span>
                    </span>
                </div>
            </div>
            <BaseButton
                v-if="totalCount > 0"
                variant="ghost"
                dense
                :icon="ICONS.done_all"
                label="Mark all read"
                class="q-mr-sm"
                @click="onMarkAllRead"
            />
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

        <!-- ── Summary boxes (per-kind theme + count) ─────────────────── -->
        <div v-if="summaryBoxes.length > 0" class="row q-col-gutter-sm q-mb-md">
            <div v-for="box in summaryBoxes" :key="box.kind" class="col-6 col-sm-4 col-md-3">
                <q-card flat bordered>
                    <q-card-section class="row items-center no-wrap q-pa-sm">
                        <q-avatar :color="box.color" text-color="white" size="34px" class="q-mr-sm">
                            <q-icon :name="box.icon" />
                        </q-avatar>
                        <div class="col">
                            <div class="text-h6 text-weight-bold">{{ box.count }}</div>
                            <div class="text-caption dora-text-muted">{{ box.theme }}</div>
                        </div>
                    </q-card-section>
                </q-card>
            </div>
        </div>

        <!-- ── Upcoming "this fortnight" timeline ─────────────────────── -->
        <UpcomingTimeline class="q-mb-md" />

        <!-- ── Empty state ────────────────────────────────────────────── -->
        <div
            v-if="!loading && totalCount === 0 && snoozedCount === 0"
            class="row justify-center q-py-xl"
        >
            <div class="column items-center dora-text-muted">
                <q-icon :name="ICONS.check_circle" size="48px" color="positive" />
                <div class="q-mt-sm">Nothing to do right now.</div>
            </div>
        </div>

        <!-- ── Active list (tiered, shared row) ───────────────────────── -->
        <q-card v-if="totalCount > 0" flat bordered class="q-mb-md">
            <AlertList
                :alerts="alerts.items"
                :busy-id="busy"
                @open="onOpen"
                @action="onAction"
                @snooze="onSnooze"
                @dismiss="onDismiss"
                @toggle-read="onToggleRead"
                @view-in-context="onViewInContext"
            />
        </q-card>

        <!-- ── Snoozed (operational — un-hide) ────────────────────────── -->
        <q-expansion-item
            v-if="snoozedCount > 0"
            :icon="ICONS.snooze"
            :label="`Snoozed (${snoozedCount})`"
            header-class="dora-text-secondary"
            class="q-mb-md"
        >
            <q-list separator bordered class="q-mt-sm rounded-borders">
                <q-item
                    v-for="alert in snoozedAlerts"
                    :key="alert.alert_id"
                    clickable
                    @click="onOpen(alert)"
                >
                    <q-item-section avatar>
                        <q-avatar :color="colorFor(alert.severity)" text-color="white" size="32px">
                            <q-icon :name="iconFor(alert.kind)" size="16px" />
                        </q-avatar>
                    </q-item-section>
                    <q-item-section>
                        <q-item-label>{{ alert.message }}</q-item-label>
                        <q-item-label caption>Snoozed until {{ formatDate(snoozedUntilOf(alert)) }}</q-item-label>
                    </q-item-section>
                    <q-item-section side>
                        <BaseButton
                            variant="ghost"
                            size="sm"
                            :icon="ICONS.undo"
                            label="Unsnooze"
                            @click.stop="onUnsnooze(alert)"
                        />
                    </q-item-section>
                </q-item>
            </q-list>
        </q-expansion-item>

        <!-- ── Subscriptions (armed price watches) ────────────────────── -->
        <SubscriptionsPanel v-if="money" class="q-mb-md" />

        <!-- ── Manage (per-user prefs) ────────────────────────────────── -->
        <q-card flat bordered class="q-mb-md">
            <q-card-section class="row items-center q-pb-none">
                <q-icon :name="ICONS.tune" size="20px" class="q-mr-sm" />
                <div class="text-subtitle1">Manage your alerts</div>
            </q-card-section>
            <q-card-section class="text-caption dora-text-muted q-pt-xs q-pb-none">
                Turn a kind off, or move it between <strong>Needs action</strong> (counts on the
                bell) and <strong>FYI</strong>. These are your personal preferences.
            </q-card-section>
            <q-list separator>
                <q-item v-for="pref in managePrefs" :key="pref.kind">
                    <q-item-section avatar>
                        <q-avatar :color="colorForKind(pref.kind)" text-color="white" size="32px">
                            <q-icon :name="iconFor(pref.kind)" size="18px" />
                        </q-avatar>
                    </q-item-section>
                    <q-item-section>
                        <q-item-label>{{ kindTheme(pref.kind) }}</q-item-label>
                        <q-item-label caption class="row items-center q-gutter-x-sm q-mt-xs">
                            <BaseSegmented
                                :model-value="pref.effective_tier"
                                :options="tierOptions"
                                size="sm"
                                dense
                                unelevated
                                :disable="!pref.enabled || prefBusy.has(pref.kind)"
                                @update:model-value="(t) => onSetTier(pref, t as AlertTier)"
                            />
                            <q-icon :name="ICONS.help_outline" size="14px">
                                <q-tooltip>
                                    Choose whether this alert kind lands in
                                    Needs action, FYI, or is silenced entirely.
                                    Overrides the app-wide default set in Settings.
                                </q-tooltip>
                            </q-icon>
                            <span v-if="pref.tier_override">· default {{ tierLabel(pref.default_tier) }}</span>
                        </q-item-label>
                    </q-item-section>
                    <q-item-section side>
                        <q-toggle
                            :model-value="pref.enabled"
                            :disable="prefBusy.has(pref.kind)"
                            @update:model-value="(v) => onToggleKind(pref, v as boolean)"
                        />
                    </q-item-section>
                </q-item>
            </q-list>
            <q-card-section class="text-caption dora-text-muted q-pt-none">
                <q-icon :name="ICONS.info" size="16px" class="q-mr-xs" />
                Household-wide thresholds (the expiring-soon window, default stocktake reminder)
                live in <router-link to="/settings">Settings → System</router-link>.
            </q-card-section>
        </q-card>

        <!-- ── History (audit trail) ──────────────────────────────────── -->
        <q-expansion-item
            :icon="ICONS.history"
            label="History"
            caption="What you've read, snoozed, or dismissed"
            header-class="dora-text-secondary"
            @show="onExpandHistory"
        >
            <div class="relative-position q-mt-sm">
                <q-inner-loading :showing="historyLoading" />
                <q-list v-if="history.length > 0" separator bordered class="rounded-borders">
                    <q-item
                        v-for="entry in history"
                        :key="entry.alert_key + entry.state"
                        :clickable="!!entry.stock_item_id"
                        @click="onOpenHistory(entry)"
                    >
                        <q-item-section>
                            <q-item-label>{{ entry.label }}</q-item-label>
                            <q-item-label caption>{{ entry.kind.replace('_', ' ') }}</q-item-label>
                        </q-item-section>
                        <q-item-section side class="items-end">
                            <q-chip dense size="sm" :color="historyChipColor(entry.state)" text-color="white">
                                {{ entry.state }}
                            </q-chip>
                            <div class="text-caption dora-text-muted q-mt-xs">{{ formatDate(entry.at) }}</div>
                        </q-item-section>
                    </q-item>
                </q-list>
                <div v-else-if="!historyLoading" class="text-caption dora-text-muted q-pa-md">
                    Nothing here yet — alerts you read, snooze, or dismiss will show up.
                </div>
            </div>
        </q-expansion-item>
    </q-page>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import BaseButton from 'src/components/BaseButton.vue';
    import BaseSegmented from 'src/components/BaseSegmented.vue';
    import AlertList from 'src/components/AlertList.vue';
    import SubscriptionsPanel from 'src/components/SubscriptionsPanel.vue';
    import UpcomingTimeline from 'src/components/UpcomingTimeline.vue';
    import {
        colorFor,
        colorForKind,
        iconFor,
        kindTheme,
        linkFor,
        tierLabel,
        type Alert,
        type AlertAction,
        type AlertHistoryEntry,
        type AlertHistoryState,
        type AlertKind,
        type AlertPref,
        type AlertTier,
    } from 'src/models/alert';
    import AlertApiService from 'src/services/api/alertApiService';
    import { useAlertStore } from 'src/stores/alertStore';
    import { useAlertPrefsStore } from 'src/stores/alertPrefsStore';
    import { toastCaption } from 'src/services/errorHandling/apiErrorHandler';
    import { useFeatureFlags } from 'src/composables/useFeatureFlags';
    import { computed, onMounted, ref } from 'vue';
    import { useQuasar } from 'quasar';
    import { useRouter } from 'vue-router';

    const $q = useQuasar();
    const router = useRouter();
    const alertStore = useAlertStore();
    const alertPrefsStore = useAlertPrefsStore();
    const api = new AlertApiService();
    const { money } = useFeatureFlags();

    const alerts = computed(() => alertStore.alerts);
    const loading = computed(() => alertStore.loading);
    const loadError = computed(() => alertStore.loadError);
    const totalCount = computed(() => alertStore.totalCount);
    const snoozedCount = computed(() => alertStore.snoozedCount);
    const snoozedAlerts = computed(() => alertStore.snoozedAlerts);
    const managePrefs = computed(() => alertPrefsStore.prefs);

    const busy = ref<string | null>(null);
    const prefBusy = ref<Set<string>>(new Set());

    const tierOptions = [
        { label: 'Needs action', value: 'actionable' },
        { label: 'FYI', value: 'fyi' },
    ];

    // ── Summary boxes — per-kind counts over the active set, in a fixed
    // worst-first order so the layout is stable as counts change.
    const SUMMARY_ORDER: AlertKind[] = [
        'expired', 'essential_low', 'expiring_soon', 'out_of_stock', 'low_stock',
        'stocktake_overdue', 'shopping_day', 'no_planned_meals',
    ];
    const summaryBoxes = computed(() => {
        const counts = new Map<AlertKind, number>();
        for (const a of alerts.value.items) counts.set(a.kind, (counts.get(a.kind) ?? 0) + 1);
        return SUMMARY_ORDER.filter((k) => counts.has(k)).map((k) => ({
            kind: k,
            count: counts.get(k) ?? 0,
            theme: kindTheme(k),
            icon: iconFor(k),
            color: colorForKind(k),
        }));
    });

    function formatDate(iso: string): string {
        if (!iso) return '';
        const d = new Date(iso);
        return Number.isFinite(d.getTime()) ? d.toLocaleDateString() : iso;
    }

    function snoozedUntilOf(alert: Alert): string {
        return alertStore.snoozedUntil(alert.alert_id) ?? '';
    }

    function refresh(): Promise<void> {
        return alertStore.refreshAsync();
    }

    function onOpen(alert: Alert): void {
        const link = linkFor(alert);
        if (link) void router.push(link);
    }

    function onViewInContext(alert: Alert): void {
        // Non-stock nudges open their own surface; stock alerts go to the
        // attention-filtered overview (expiring/low/out/flagged items).
        const link = linkFor(alert);
        if (alert.kind === 'no_planned_meals' || alert.kind === 'shopping_day') {
            if (link) void router.push(link);
            return;
        }
        void router.push({ path: '/stock', query: { attention: 'true' } });
    }

    // ── Inline act_on_alert actions (extend/reset/restocked/acknowledge) ──
    async function onAction(alert: Alert, action: AlertAction): Promise<void> {
        busy.value = alert.alert_id;
        try {
            await api.applyActionAsync(alert.alert_id, action);
            await alertStore.refreshAsync();
            $q.notify({ type: 'positive', position: 'bottom-right', message: 'Done.' });
        } catch (err) {
            $q.notify({
                type: 'negative', position: 'bottom-right',
                message: 'Could not apply.', caption: toastCaption(err),
            });
        } finally {
            busy.value = null;
        }
    }

    async function onSnooze(alert: Alert): Promise<void> {
        await alertStore.snoozeAlert(alert.alert_id, 7);
        $q.notify({
            type: 'info', position: 'bottom-right',
            message: alert.stock_item_name
                ? `Snoozed "${alert.stock_item_name}" for 7 days.`
                : 'Snoozed for 7 days.',
            actions: [{ label: 'Undo', color: 'white', handler: () => void alertStore.unsnoozeAlert(alert.alert_id) }],
        });
    }

    async function onDismiss(alert: Alert): Promise<void> {
        await alertStore.dismissAlert(alert.alert_id);
        $q.notify({
            type: 'info', position: 'bottom-right',
            message: alert.stock_item_name
                ? `Dismissed "${alert.stock_item_name}".`
                : 'Dismissed.',
            caption: 'It returns only if the condition clears and re-fires.',
            actions: [{ label: 'Undo', color: 'white', handler: () => void alertStore.unsnoozeAlert(alert.alert_id) }],
        });
    }

    async function onToggleRead(alert: Alert, read: boolean): Promise<void> {
        if (read) await alertStore.markRead(alert.alert_id);
        else await alertStore.markUnread(alert.alert_id);
    }

    async function onMarkAllRead(): Promise<void> {
        await alertStore.markAllRead();
        $q.notify({ type: 'positive', position: 'bottom-right', message: 'All marked read.' });
    }

    async function onUnsnooze(alert: Alert): Promise<void> {
        await alertStore.unsnoozeAlert(alert.alert_id);
    }

    // ── Manage panel (per-user prefs; server applies them to GET /alerts,
    // so refresh the alert set after each change) ──────────────────────
    function setPrefBusy(kind: string, on: boolean): void {
        const next = new Set(prefBusy.value);
        if (on) next.add(kind);
        else next.delete(kind);
        prefBusy.value = next;
    }

    async function onToggleKind(pref: AlertPref, enabled: boolean): Promise<void> {
        setPrefBusy(pref.kind, true);
        try {
            await alertPrefsStore.setEnabled(pref.kind, enabled);
            await alertStore.refreshAsync();
        } catch (err) {
            $q.notify({ type: 'negative', position: 'bottom-right', message: 'Could not save.', caption: toastCaption(err) });
        } finally {
            setPrefBusy(pref.kind, false);
        }
    }

    async function onSetTier(pref: AlertPref, tier: AlertTier): Promise<void> {
        setPrefBusy(pref.kind, true);
        try {
            // Clear the override when the chosen tier IS the default — keeps the
            // ledger free of redundant rows (absence = default).
            await alertPrefsStore.setTierOverride(pref.kind, tier === pref.default_tier ? null : tier);
            await alertStore.refreshAsync();
        } catch (err) {
            $q.notify({ type: 'negative', position: 'bottom-right', message: 'Could not save.', caption: toastCaption(err) });
        } finally {
            setPrefBusy(pref.kind, false);
        }
    }

    // ── History (lazy — only fetched when the section is first opened) ──
    const history = ref<AlertHistoryEntry[]>([]);
    const historyLoading = ref(false);
    const historyLoaded = ref(false);

    async function onExpandHistory(): Promise<void> {
        if (historyLoaded.value) return;
        historyLoading.value = true;
        try {
            history.value = (await api.getHistoryAsync()).entries;
            historyLoaded.value = true;
        } catch (err) {
            $q.notify({ type: 'negative', position: 'bottom-right', message: 'Could not load history.', caption: toastCaption(err) });
        } finally {
            historyLoading.value = false;
        }
    }

    function onOpenHistory(entry: AlertHistoryEntry): void {
        if (entry.stock_item_id) void router.push(`/stock/${entry.stock_item_id}`);
    }

    function historyChipColor(state: AlertHistoryState): string {
        // R-002: dismissed routes through the theme-bound `info`
        // semantic; the saturated `orange-7` / `blue-grey-5` cases for
        // snoozed / read are part of a graded severity ladder and
        // are flagged for the FU-313 designed-token-ladder work.
        if (state === 'dismissed') return 'info';
        if (state === 'snoozed') return 'orange-7';
        return 'blue-grey-5';
    }

    onMounted(async () => {
        await Promise.all([
            alerts.value.items.length === 0 && !loading.value ? alertStore.refreshAsync() : Promise.resolve(),
            alertPrefsStore.refreshAsync(),
        ]);
    });
</script>
