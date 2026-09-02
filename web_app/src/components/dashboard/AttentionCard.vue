<template>
    <DashboardCard :icon="ICONS.notifications_active" title="Needs your attention">
        <template #action>
            <router-link
                v-if="alerts.length > 0"
                class="dora-card-action dora-card-link"
                to="/alerts"
            >
                All {{ alerts.length }} →
            </router-link>
        </template>

        <!-- FU-840 — the error state comes FIRST. A failed alerts fetch used to
             fall through to "All clear", i.e. it told you nothing was wrong
             precisely when it couldn't know. -->
        <CardLoadError
            v-if="failed"
            line="I couldn't check your alerts just now."
            @retry="emit('retry')"
        />
        <div v-else-if="sorted.length === 0" class="dora-empty dora-empty-ok">
            <q-icon :name="ICONS.check_circle" size="18px" class="q-mr-xs" />
            All clear — nothing needs your attention right now.
        </div>
        <template v-else>
            <!-- D6 top section: a by-kind summary so you see the *shape* of
                 what's wrong at a glance ("5 expiring soon", "3 out of stock")
                 before the detail rows. Each chip opens the alerts page. -->
            <div class="dora-alert-summary">
                <router-link
                    v-for="g in kindSummary"
                    :key="g.kind"
                    to="/alerts"
                    class="dora-alert-chip"
                >
                    <q-icon
                        :name="alertIconFor(g.kind)"
                        :color="alertColorFor(g.severity)"
                        size="16px"
                    />
                    <span class="dora-alert-chip-num">{{ g.count }}</span>
                    <span class="dora-alert-chip-label">{{ kindTheme(g.kind) }}</span>
                </router-link>
            </div>

            <!-- D6 bottom section: a peek at the top few, most-urgent first,
                 with the inline quick-actions. -->
            <ul class="dora-attn-list">
                <li v-for="p in peek" :key="p.alert.alert_id" class="dora-attn-row">
                    <span class="dora-attn-dot" :class="`dora-attn-dot-${p.alert.severity}`" />
                    <q-icon
                        :name="alertIconFor(p.alert.kind)"
                        :color="alertColorFor(p.alert.severity)"
                        size="18px"
                    />
                    <!-- a11y: a real <router-link> when the alert has a
                         deep-link target (this replaced an `href="#"` handler).
                         Stock alerts link the item name; non-stock nudges link
                         the message text. -->
                    <router-link
                        v-if="p.alert.stock_item_name && p.link"
                        :to="p.link"
                        class="dora-attn-name"
                    >
                        {{ p.alert.stock_item_name }}
                    </router-link>
                    <span v-else-if="p.alert.stock_item_name" class="dora-attn-name">
                        {{ p.alert.stock_item_name }}
                    </span>
                    <router-link
                        v-if="!p.alert.stock_item_name && p.link"
                        :to="p.link"
                        class="dora-attn-msg dora-attn-msg-link"
                    >
                        {{ p.alert.message }}
                    </router-link>
                    <span v-else class="dora-attn-msg">{{ p.alert.message }}</span>
                    <span class="dora-attn-actions">
                        <BaseButton
                            v-for="a in alertActionsFor(p.alert.kind)"
                            :key="a.action"
                            variant="ghost"
                            dense
                            size="sm"
                            :icon="a.icon"
                            :label="a.label"
                            @click="emit('action', p.alert, a.action)"
                        />
                    </span>
                </li>
            </ul>

            <router-link to="/alerts" class="dora-alert-seeall">
                See all alerts →
            </router-link>
        </template>
    </DashboardCard>
</template>

<script lang="ts" setup>
    /**
     * The dashboard's "Needs your attention" card — feedback D6's two-section
     * design: a by-kind summary above a peek at the most urgent few.
     *
     * Extracted from `DashboardPage.vue` (FU-829). **Data stays owned by the
     * page**: the alerts list is fetched by the page's slot loader, which also
     * tracks the per-slot error state and re-runs after an alert action refreshes
     * the summary. Pushing the fetch in here would either duplicate that
     * orchestration or lose it, so the card takes what it needs and emits what
     * it wants doing — the derived shapes below are presentation of an
     * already-fetched list, which is the R-003-sanctioned client-side case.
     */
    import { computed } from 'vue';
    import { ICONS } from 'src/style/icons';
    import BaseButton from 'src/components/BaseButton.vue';
    import DashboardCard from 'src/components/dashboard/DashboardCard.vue';
    import CardLoadError from 'src/components/dashboard/CardLoadError.vue';
    import {
        actionsFor as alertActionsFor,
        colorFor as alertColorFor,
        iconFor as alertIconFor,
        kindTheme,
        linkFor as alertLinkFor,
        type Alert,
        type AlertAction,
        type AlertKind,
        type AlertSeverity,
    } from 'src/models/alert';

    const props = withDefaults(
        defineProps<{
            alerts: Alert[];
            /** The page's slot-error flag for this card (FU-840). */
            failed?: boolean;
        }>(),
        { failed: false },
    );

    const emit = defineEmits<{
        (e: 'retry'): void;
        (e: 'action', alert: Alert, action: AlertAction): void;
    }>();

    const SEVERITY_RANK: Record<AlertSeverity, number> = { high: 0, medium: 1, low: 2 };
    const PEEK_LIMIT = 3;

    const sorted = computed(() =>
        [...props.alerts].sort(
            (a, b) => (SEVERITY_RANK[a.severity] ?? 9) - (SEVERITY_RANK[b.severity] ?? 9),
        ),
    );

    // By-kind breakdown for the summary chips. This is display grouping of the
    // *already-fetched* list, not a new cross-entity aggregate, so it stays
    // client-side — R-003 note carried over from the page. The per-kind
    // label/icon come from the shared alert model, so there is one source.
    type AlertKindGroup = { kind: AlertKind; count: number; severity: AlertSeverity };
    const kindSummary = computed<AlertKindGroup[]>(() => {
        const groups = new Map<AlertKind, AlertKindGroup>();
        for (const a of props.alerts) {
            const g = groups.get(a.kind);
            if (g) {
                g.count += 1;
                if (SEVERITY_RANK[a.severity] < SEVERITY_RANK[g.severity]) g.severity = a.severity;
            } else {
                groups.set(a.kind, { kind: a.kind, count: 1, severity: a.severity });
            }
        }
        return [...groups.values()].sort(
            (x, y) => SEVERITY_RANK[x.severity] - SEVERITY_RANK[y.severity] || y.count - x.count,
        );
    });

    // The peek rows, each with its deep-link target precomputed so the template
    // can render a real <router-link> (a11y).
    const peek = computed(() =>
        sorted.value.slice(0, PEEK_LIMIT).map((alert) => ({
            alert,
            link: alertLinkFor(alert),
        })),
    );
</script>

<style scoped lang="scss">
    /* Moved here with the card (R-027 — the component owns its intrinsic
       appearance). These referenced the page-local `--c-*` aliases, which are
       declared on `.dora-dash` and so resolve to nothing from a component — the
       R-060 failure mode. On the real tokens now. */

    /* Top: by-kind summary chips. */
    .dora-alert-summary {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        margin-bottom: 12px;
    }
    .dora-alert-chip {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        padding: 4px 10px;
        border-radius: var(--radius-pill);
        background: var(--surface-elevated);
        border: 1px solid var(--border-default);
        text-decoration: none;
        color: var(--text-primary);
        font-size: 0.8rem;
        transition: border-color 0.15s ease, background 0.15s ease;
    }
    .dora-alert-chip:hover {
        border-color: var(--border-strong);
        background: var(--brand-primary-soft);
    }
    .dora-alert-chip-num {
        font-weight: 700;
    }
    .dora-alert-chip-label {
        color: var(--text-secondary);
    }

    /* Bottom: peek + "see all". */
    .dora-alert-seeall {
        display: inline-block;
        margin-top: 12px;
        font-size: 0.85rem;
        font-weight: 600;
        color: var(--brand-primary);
        text-decoration: none;
    }
    .dora-alert-seeall:hover {
        text-decoration: underline;
    }
    .dora-attn-list {
        list-style: none;
        margin: 0;
        padding: 0;
        display: flex;
        flex-direction: column;
        gap: 8px;
    }
    .dora-attn-row {
        display: grid;
        grid-template-columns: 6px 20px minmax(0, auto) 1fr auto;
        align-items: center;
        gap: 8px;
        padding: 8px 10px;
        background: var(--surface-elevated);
        border-radius: 10px;
    }
    .dora-attn-dot {
        width: 6px;
        height: 100%;
        min-height: 26px;
        border-radius: 3px;
    }
    .dora-attn-dot-high { background: var(--semantic-negative); }
    .dora-attn-dot-medium { background: var(--semantic-warning); }
    .dora-attn-dot-low { background: var(--brand-primary); }
    .dora-attn-name {
        font-weight: 600;
        color: var(--text-primary);
        text-decoration: none;
        max-width: 220px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    .dora-attn-name:hover {
        text-decoration: underline;
    }
    .dora-attn-msg {
        color: var(--text-secondary);
        font-size: 0.85rem;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    /* When the message itself is the deep-link (non-stock nudges) — strip the
       default anchor chrome, reveal an underline on hover. */
    .dora-attn-msg-link {
        text-decoration: none;
    }
    .dora-attn-msg-link:hover {
        text-decoration: underline;
    }
    .dora-attn-actions {
        display: flex;
        gap: 2px;
        flex-shrink: 0;
    }

    @media (max-width: 600px) {
        .dora-attn-row {
            grid-template-columns: auto minmax(0, 1fr) auto;
            grid-template-rows: auto auto;
        }
        .dora-attn-msg,
        .dora-attn-actions {
            grid-column: 1 / -1;
        }
        /* The summary chips wrap freely; keep them from getting too cramped. */
        .dora-alert-chip {
            padding: 6px 12px;
        }
    }
</style>
