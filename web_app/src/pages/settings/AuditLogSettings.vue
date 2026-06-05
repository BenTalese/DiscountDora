<template>
    <q-card flat bordered>
        <q-card-section class="row items-center q-gutter-md">
            <q-icon :name="ICONS.fact_check" size="32px" class="text-primary" />
            <div class="col">
                <div class="text-h6">Audit log</div>
                <div class="text-caption dora-text-muted">
                    Every mutating request, login attempt, client crash, and
                    explicit service-layer event lands here. Filters narrow
                    the view; click a row to see the full payload.
                </div>
            </div>
            <q-btn
                outline
                no-caps
                :icon="ICONS.file_download"
                label="Export CSV"
                :disable="rows.length === 0"
                @click="exportCsv"
            />
        </q-card-section>
        <q-separator />

        <!-- ── Filters ───────────────────────────────────────────────── -->
        <q-card-section>
            <div class="row q-col-gutter-sm">
                <q-select
                    v-model="filters.source"
                    :options="sourceOptions"
                    label="Source"
                    outlined
                    dense
                    clearable
                    emit-value
                    map-options
                    class="col-12 col-sm-3"
                />
                <q-select
                    v-model="filters.severity"
                    :options="severityOptions"
                    label="Severity"
                    outlined
                    dense
                    clearable
                    multiple
                    emit-value
                    map-options
                    use-chips
                    class="col-12 col-sm-3"
                />
                <q-input
                    v-model="filters.action"
                    label="Action (exact match)"
                    outlined
                    dense
                    clearable
                    class="col-12 col-sm-3"
                />
                <q-input
                    v-model="filters.actor_user_id"
                    label="Actor user id"
                    outlined
                    dense
                    clearable
                    class="col-12 col-sm-3"
                />
                <q-input
                    v-model="filters.entity_type"
                    label="Entity type"
                    outlined
                    dense
                    clearable
                    class="col-12 col-sm-3"
                />
                <q-input
                    v-model="filters.entity_id"
                    label="Entity id"
                    outlined
                    dense
                    clearable
                    class="col-12 col-sm-3"
                />
                <q-input
                    v-model="filters.request_id"
                    label="Request id"
                    outlined
                    dense
                    clearable
                    class="col-12 col-sm-3"
                />
                <q-input
                    v-model="filters.occurred_from"
                    label="From (ISO datetime)"
                    placeholder="2026-05-01T00:00:00"
                    outlined
                    dense
                    clearable
                    class="col-12 col-sm-3"
                />
                <q-input
                    v-model="filters.occurred_to"
                    label="To (ISO datetime, exclusive)"
                    placeholder="2026-05-28T00:00:00"
                    outlined
                    dense
                    clearable
                    class="col-12 col-sm-3"
                />
            </div>
            <div class="row q-mt-sm q-gutter-sm">
                <q-btn
                    color="primary"
                    no-caps
                    :icon="ICONS.search"
                    label="Apply filters"
                    :loading="loading"
                    @click="reload(1)"
                />
                <q-btn
                    flat
                    no-caps
                    label="Clear"
                    @click="clearFilters"
                />
            </div>
        </q-card-section>
        <q-separator />

        <!-- ── Table ─────────────────────────────────────────────────── -->
        <q-card-section v-if="loadError" class="text-negative">
            {{ loadError }}
        </q-card-section>
        <q-table
            v-else
            :rows="rows"
            :columns="columns"
            row-key="audit_event_id"
            flat
            bordered
            :loading="loading"
            hide-pagination
            :rows-per-page-options="[0]"
            @row-click="(_, row) => openDetail(row)"
        >
            <template #body-cell-severity="props">
                <q-td :props="props">
                    <q-chip
                        dense
                        size="sm"
                        :color="severityColour(props.row.severity)"
                        text-color="white"
                    >
                        {{ props.row.severity }}
                    </q-chip>
                </q-td>
            </template>
            <template #body-cell-source="props">
                <q-td :props="props">
                    <q-chip dense size="sm" class="dora-bg-sunken dora-text-secondary">
                        {{ props.row.source }}
                    </q-chip>
                </q-td>
            </template>
        </q-table>

        <q-card-section class="row items-center q-gutter-sm">
            <q-btn
                flat
                dense
                :icon="ICONS.chevron_left"
                label="Previous"
                no-caps
                :disable="page <= 1 || loading"
                @click="reload(page - 1)"
            />
            <div class="text-caption dora-text-muted">
                Page {{ page }} of {{ pageCount }} ({{ total.toLocaleString() }} event(s))
            </div>
            <q-btn
                flat
                dense
                icon-right="chevron_right"
                label="Next"
                no-caps
                :disable="page >= pageCount || loading"
                @click="reload(page + 1)"
            />
            <q-space />
            <q-select
                v-model="size"
                :options="[25, 50, 100, 200]"
                label="Per page"
                outlined
                dense
                style="min-width: 110px"
                @update:model-value="reload(1)"
            />
        </q-card-section>

        <!-- ── Detail drawer ─────────────────────────────────────────── -->
        <BaseDialog
            v-model="detailOpen"
            maximized
            card-style="width: 100%; max-width: 100vw; height: 100%; max-height: 100vh"
        >
                <q-toolbar>
                    <q-toolbar-title>
                        Audit event
                        <q-chip
                            v-if="detail"
                            dense
                            size="sm"
                            class="q-ml-sm"
                            :color="severityColour(detail.severity)"
                            text-color="white"
                        >
                            {{ detail.severity }}
                        </q-chip>
                    </q-toolbar-title>
                    <BaseButton variant="icon" :icon="ICONS.close" v-close-popup />
                </q-toolbar>
                <q-separator />
                <q-card-section v-if="detail">
                    <q-list dense separator>
                        <q-item><q-item-section>Action</q-item-section><q-item-section side><code>{{ detail.action }}</code></q-item-section></q-item>
                        <q-item><q-item-section>Source</q-item-section><q-item-section side>{{ detail.source }}</q-item-section></q-item>
                        <q-item><q-item-section>When</q-item-section><q-item-section side>{{ formatWhen(detail.occurred_at) }}</q-item-section></q-item>
                        <q-item><q-item-section>Actor</q-item-section><q-item-section side>{{ detail.actor_username || '—' }} <span v-if="detail.actor_user_id" class="dora-text-muted">({{ detail.actor_user_id }})</span></q-item-section></q-item>
                        <q-item><q-item-section>Actor IP</q-item-section><q-item-section side>{{ detail.actor_ip || '—' }}</q-item-section></q-item>
                        <q-item v-if="detail.entity_type"><q-item-section>Entity</q-item-section><q-item-section side>{{ detail.entity_type }} <span v-if="detail.entity_id" class="dora-text-muted">({{ detail.entity_id }})</span></q-item-section></q-item>
                        <q-item v-if="detail.request_id"><q-item-section>Request id</q-item-section><q-item-section side><code>{{ detail.request_id }}</code></q-item-section></q-item>
                    </q-list>
                </q-card-section>
                <q-separator />
                <q-card-section v-if="detail">
                    <div class="text-subtitle2 q-mb-sm">Payload</div>
                    <pre class="audit-payload">{{ formatPayload(detail.payload) }}</pre>
                </q-card-section>
                <q-card-actions align="right">
                    <q-btn
                        v-if="detail?.request_id"
                        flat
                        no-caps
                        color="primary"
                        :icon="ICONS.link"
                        label="Find related"
                        @click="findRelated(detail.request_id)"
                    />
                    <BaseButton variant="ghost" label="Close" v-close-popup />
                </q-card-actions>
        </BaseDialog>
    </q-card>
</template>

<script lang="ts" setup>
    import BaseButton from 'src/components/BaseButton.vue';
    import BaseDialog from 'src/components/BaseDialog.vue';
    import { ICONS } from 'src/style/icons';
    import { useQuasar } from 'quasar';
    import { computed, onMounted, reactive, ref } from 'vue';
    import AuditApiService, { type AuditEvent, type AuditFilters } from 'src/services/api/auditApiService';

    const $q = useQuasar();
    const auditApi = new AuditApiService();

    const sourceOptions = [
        { label: 'dapi (backend)', value: 'dapi' },
        { label: 'mapi (merchant)', value: 'mapi' },
        { label: 'emailer', value: 'emailer' },
        { label: 'web (client)', value: 'web' },
        { label: 'system', value: 'system' },
    ];
    const severityOptions = [
        { label: 'audit', value: 'audit' },
        { label: 'error', value: 'error' },
        { label: 'warn', value: 'warn' },
        { label: 'info', value: 'info' },
        { label: 'debug', value: 'debug' },
    ];

    const filters = reactive<AuditFilters>({});
    const page = ref(1);
    const size = ref(50);
    const total = ref(0);
    const rows = ref<AuditEvent[]>([]);
    const loading = ref(false);
    const loadError = ref<string | null>(null);

    const detail = ref<AuditEvent | null>(null);
    const detailOpen = ref(false);

    const pageCount = computed(() =>
        total.value === 0 ? 1 : Math.ceil(total.value / size.value),
    );

    const columns = [
        { name: 'occurred_at', label: 'When', field: (r: AuditEvent) => formatWhen(r.occurred_at), align: 'left' as const },
        { name: 'severity', label: 'Sev', field: 'severity', align: 'left' as const },
        { name: 'source', label: 'Source', field: 'source', align: 'left' as const },
        { name: 'action', label: 'Action', field: 'action', align: 'left' as const, classes: 'text-mono' },
        { name: 'actor', label: 'Actor', field: (r: AuditEvent) => r.actor_username || r.actor_ip || '—', align: 'left' as const },
        { name: 'entity', label: 'Entity', field: (r: AuditEvent) => r.entity_type ? `${r.entity_type}` : '—', align: 'left' as const },
    ];

    function severityColour(sev: AuditEvent['severity']): string {
        if (sev === 'error') return 'negative';
        if (sev === 'warn') return 'warning';
        if (sev === 'audit') return 'primary';
        if (sev === 'info') return 'grey-7';
        return 'grey-5';
    }

    function formatWhen(iso: string): string {
        try {
            return new Date(iso).toLocaleString();
        } catch {
            return iso;
        }
    }

    function formatPayload(payload: unknown): string {
        if (payload === null || payload === undefined) return '(empty)';
        try {
            return JSON.stringify(payload, null, 2);
        } catch {
            return typeof payload === 'bigint' ? String(payload) : '[unserialisable]';
        }
    }

    async function reload(nextPage: number) {
        loading.value = true;
        loadError.value = null;
        try {
            const result = await auditApi.listAsync({
                ...filters,
                page: nextPage,
                size: size.value,
            });
            rows.value = result.items;
            total.value = result.total;
            page.value = nextPage;
        } catch (err) {
            loadError.value = err instanceof Error ? err.message : String(err);
        } finally {
            loading.value = false;
        }
    }

    function clearFilters() {
        for (const key of Object.keys(filters)) {
            // @ts-expect-error AuditFilters is a flat record of optional strings
            filters[key] = undefined;
        }
        void reload(1);
    }

    async function openDetail(row: AuditEvent) {
        try {
            detail.value = await auditApi.getAsync(row.audit_event_id);
            detailOpen.value = true;
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: "Couldn't load that event.",
                caption: err instanceof Error ? err.message : String(err),
            });
        }
    }

    function findRelated(requestId: string | null) {
        if (!requestId) return;
        detailOpen.value = false;
        filters.request_id = requestId;
        void reload(1);
    }

    function exportCsv() {
        const header = [
            'occurred_at', 'source', 'severity', 'action', 'actor_username',
            'actor_user_id', 'actor_ip', 'entity_type', 'entity_id', 'request_id',
            'payload',
        ];
        const escape = (value: unknown) => {
            let s: string;
            if (value === null || value === undefined) s = '';
            else if (typeof value === 'string') s = value;
            else if (typeof value === 'number' || typeof value === 'boolean' || typeof value === 'bigint')
                s = String(value);
            else s = JSON.stringify(value) ?? '';
            return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
        };
        const lines = [header.join(',')];
        for (const row of rows.value) {
            lines.push([
                row.occurred_at,
                row.source,
                row.severity,
                row.action,
                row.actor_username ?? '',
                row.actor_user_id ?? '',
                row.actor_ip ?? '',
                row.entity_type ?? '',
                row.entity_id ?? '',
                row.request_id ?? '',
                row.payload === null || row.payload === undefined
                    ? ''
                    : JSON.stringify(row.payload),
            ].map(escape).join(','));
        }
        const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const anchor = document.createElement('a');
        anchor.href = url;
        anchor.download = `audit-events-${new Date().toISOString().slice(0, 10)}.csv`;
        document.body.appendChild(anchor);
        anchor.click();
        document.body.removeChild(anchor);
        URL.revokeObjectURL(url);
    }

    onMounted(() => {
        void reload(1);
    });
</script>

<style scoped>
    .audit-payload {
        background: var(--surface-sunken);
        border-radius: 4px;
        padding: 12px;
        font-size: 12px;
        white-space: pre-wrap;
        max-height: 360px;
        overflow: auto;
    }
    .text-mono {
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        font-size: 12px;
    }
</style>
