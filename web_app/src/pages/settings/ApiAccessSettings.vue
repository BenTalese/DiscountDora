<template>
    <q-card flat bordered>
        <q-card-section class="row items-center">
            <div>
                <div class="text-h6">
                    <q-icon :name="ICONS.key" size="20px" class="q-mr-xs" />
                    API access
                </div>
                <div class="text-caption dora-text-muted">
                    Bearer keys for authenticated sources that push data into
                    Dora. Always-on; not tied to any feature being enabled.
                </div>
            </div>
            <q-space />
            <q-btn
                flat
                round
                dense
                :icon="ICONS.refresh"
                :loading="loading"
                @click="loadSources"
            >
                <q-tooltip>Refresh</q-tooltip>
            </q-btn>
            <q-btn
                color="primary"
                no-caps
                :icon="ICONS.add"
                label="New key"
                class="q-ml-sm"
                @click="openCreate"
            />
        </q-card-section>

        <q-banner
            v-if="loadError"
            class="dora-bg-negative-soft text-negative q-mx-md q-mb-md"
            dense
            rounded
        >
            {{ loadError }}
        </q-banner>

        <q-separator />

        <q-list separator>
            <q-expansion-item
                v-for="src in sources"
                :key="src.id"
                :icon="ICONS.key"
                :label="src.label"
                :caption="captionFor(src)"
                @show="loadMappings(src.id)"
            >
                <template #header>
                    <q-item-section avatar>
                        <q-avatar
                            :color="src.enabled ? 'primary' : undefined"
                            :class="src.enabled ? '' : 'dora-bg-sunken dora-text-secondary'"
                            text-color="white"
                            size="42px"
                            :icon="ICONS.key"
                        />
                    </q-item-section>
                    <q-item-section>
                        <q-item-label class="text-weight-medium">
                            {{ src.label }}
                            <q-badge
                                v-if="!src.enabled"
                                color="grey"
                                text-color="white"
                                class="q-ml-sm"
                            >
                                disabled
                            </q-badge>
                            <q-badge
                                v-if="pendingCountFor(src.id) > 0"
                                color="warning"
                                text-color="white"
                                class="q-ml-sm"
                            >
                                {{ pendingCountFor(src.id) }} pending
                            </q-badge>
                        </q-item-label>
                        <q-item-label caption>
                            Created {{ formatDate(src.created_at) }}
                            ·
                            <span v-if="src.last_used_at">
                                Last used {{ formatDate(src.last_used_at) }}
                            </span>
                            <span v-else>Never used</span>
                            ·
                            <span class="dora-text-muted">
                                Accepted {{ src.accepted_count }}
                                · Skipped {{ src.skipped_count }}
                                · Failed {{ src.failed_count }}
                            </span>
                        </q-item-label>
                    </q-item-section>
                    <q-item-section side>
                        <div class="row q-gutter-xs items-center" @click.stop>
                            <q-btn
                                flat
                                dense
                                no-caps
                                :icon="src.enabled ? ICONS.lock : ICONS.lock_open"
                                :label="src.enabled ? 'Disable' : 'Enable'"
                                :loading="togglingId === src.id"
                                @click="onToggle(src)"
                            />
                            <q-btn
                                flat
                                dense
                                no-caps
                                :icon="ICONS.edit"
                                label="Rename"
                                @click="openRename(src)"
                            />
                            <q-btn
                                flat
                                dense
                                no-caps
                                color="negative"
                                :icon="ICONS.delete"
                                label="Revoke"
                                :loading="revokingId === src.id"
                                @click="onRevoke(src)"
                            />
                        </div>
                    </q-item-section>
                </template>

                <q-card flat class="dora-bg-sunken q-mx-md q-mb-md q-mt-none">
                    <q-card-section>
                        <div class="text-subtitle2 q-mb-xs">
                            Store mappings
                        </div>
                        <div class="text-caption dora-text-muted q-mb-md">
                            Each store name the source pushes must be
                            mapped to one of your Dora merchants. Pushes
                            against an unmapped name are skipped and
                            surface here as pending — they never
                            auto-create a merchant.
                        </div>

                        <q-list dense>
                            <q-item
                                v-for="m in mappingsBySource[src.id] ?? []"
                                :key="m.id"
                            >
                                <q-item-section>
                                    <q-item-label>
                                        {{ m.external_name }}
                                        <q-badge
                                            v-if="!m.merchant_id"
                                            color="warning"
                                            text-color="white"
                                            class="q-ml-sm"
                                        >
                                            pending
                                        </q-badge>
                                    </q-item-label>
                                    <q-item-label caption>
                                        <span v-if="m.merchant_name">
                                            → {{ m.merchant_name }}
                                        </span>
                                        <span v-else class="dora-text-muted">
                                            Awaiting mapping
                                        </span>
                                        <span v-if="m.last_seen_at">
                                            · last pushed {{ formatDate(m.last_seen_at) }}
                                        </span>
                                    </q-item-label>
                                </q-item-section>
                                <q-item-section side>
                                    <div class="row q-gutter-xs items-center">
                                        <q-select
                                            :model-value="m.merchant_id"
                                            :options="merchantOptions"
                                            option-value="value"
                                            option-label="label"
                                            emit-value
                                            map-options
                                            dense
                                            outlined
                                            clearable
                                            label="Merchant"
                                            style="min-width: 200px"
                                            @update:model-value="(value: string | null) => onAssign(src.id, m, value)"
                                        />
                                        <q-btn
                                            flat
                                            dense
                                            round
                                            color="negative"
                                            :icon="ICONS.delete"
                                            @click="onDeleteMapping(src.id, m)"
                                        >
                                            <q-tooltip>Drop this mapping entirely</q-tooltip>
                                        </q-btn>
                                    </div>
                                </q-item-section>
                            </q-item>

                            <q-item v-if="(mappingsBySource[src.id] ?? []).length === 0">
                                <q-item-section>
                                    <q-item-label class="dora-text-muted">
                                        No mappings yet. They appear here
                                        the first time this source pushes
                                        a record.
                                    </q-item-label>
                                </q-item-section>
                            </q-item>
                        </q-list>
                    </q-card-section>
                </q-card>
            </q-expansion-item>

            <q-item v-if="!loading && sources.length === 0">
                <q-item-section>
                    <q-item-label class="dora-text-muted">
                        No keys yet. Create one for each authenticated
                        source that should be able to push data.
                    </q-item-label>
                </q-item-section>
            </q-item>
        </q-list>

        <q-inner-loading :showing="loading && sources.length === 0">
            <q-spinner color="primary" size="48px" />
        </q-inner-loading>

        <!-- Create dialog ─────────────────────────────────────────── -->
        <BaseDialog
            v-model="createOpen"
            title="New API key"
            closable
            card-style="min-width: 320px; max-width: 480px"
        >
            <q-card-section>
                <q-input
                    v-model="newLabel"
                    label="Label"
                    placeholder="e.g. home box"
                    outlined
                    dense
                    autofocus
                />
                <div class="text-caption dora-text-muted q-mt-sm">
                    Free-text; only you see it. The key itself is shown
                    once after you create it — copy it then.
                </div>
            </q-card-section>
            <template #actions>
                <BaseButton variant="ghost" label="Cancel" v-close-popup />
                <q-btn
                    color="primary"
                    no-caps
                    label="Create"
                    :loading="creating"
                    :disable="!newLabel.trim()"
                    @click="onCreate"
                />
            </template>
        </BaseDialog>

        <!-- Reveal-once dialog ────────────────────────────────────── -->
        <BaseDialog
            v-model="revealOpen"
            title="Copy this key now"
            closable
            card-style="min-width: 320px; max-width: 560px"
        >
            <q-card-section>
                <div class="text-caption dora-text-muted">
                    This is the only time the key will be shown. If you
                    lose it, revoke it and mint a new one.
                </div>
            </q-card-section>
            <q-card-section>
                <q-input
                    :model-value="revealedKey"
                    readonly
                    outlined
                    dense
                    class="reveal-readout"
                >
                    <template #append>
                        <q-btn
                            flat
                            round
                            dense
                            :icon="ICONS.content_copy"
                            @click="copyRevealed"
                        />
                    </template>
                </q-input>
            </q-card-section>
            <template #actions>
                <BaseButton variant="ghost" label="Done" v-close-popup />
            </template>
        </BaseDialog>

        <!-- Rename dialog ─────────────────────────────────────────── -->
        <BaseDialog
            v-model="renameOpen"
            :title="`Rename ${renameTarget?.label ?? ''}`"
            closable
            card-style="min-width: 320px; max-width: 480px"
        >
            <q-card-section>
                <q-input
                    v-model="renameValue"
                    label="Label"
                    outlined
                    dense
                    autofocus
                />
            </q-card-section>
            <template #actions>
                <BaseButton variant="ghost" label="Cancel" v-close-popup />
                <q-btn
                    color="primary"
                    no-caps
                    label="Save"
                    :loading="renaming"
                    :disable="!renameValue.trim()"
                    @click="onRename"
                />
            </template>
        </BaseDialog>
    </q-card>
</template>

<script lang="ts" setup>
    import BaseButton from 'src/components/BaseButton.vue';
    import BaseDialog from 'src/components/BaseDialog.vue';
    import { ICONS } from 'src/style/icons';
    import { copyToClipboard, useQuasar } from 'quasar';
    import IngestionSourcesApiService, {
        type DoraMerchant,
        type IngestionSource,
        type IngestionStoreMapping
    } from 'src/services/api/ingestionSourcesApiService';
    import { computed, onMounted, ref } from 'vue';
    import { describeApiError } from 'src/services/errorHandling/apiErrorHandler';

    const $q = useQuasar();
    const api = new IngestionSourcesApiService();

    const sources = ref<IngestionSource[]>([]);
    const loading = ref(false);
    const loadError = ref<string | null>(null);
    const togglingId = ref<string | null>(null);
    const revokingId = ref<string | null>(null);

    const createOpen = ref(false);
    const newLabel = ref('');
    const creating = ref(false);

    const revealOpen = ref(false);
    const revealedKey = ref('');

    const renameOpen = ref(false);
    const renameTarget = ref<IngestionSource | null>(null);
    const renameValue = ref('');
    const renaming = ref(false);

    const mappingsBySource = ref<Record<string, IngestionStoreMapping[]>>({});
    const merchants = ref<DoraMerchant[]>([]);

    const merchantOptions = computed(() =>
        merchants.value.map(m => ({ value: m.merchant_id, label: m.name }))
    );

    function pendingCountFor(sourceId: string): number {
        return (mappingsBySource.value[sourceId] ?? []).filter(m => !m.merchant_id).length;
    }

    function captionFor(_src: IngestionSource): string {
        return '';
    }

    async function loadMappings(sourceId: string) {
        try {
            const items = await api.listMappingsAsync(sourceId);
            mappingsBySource.value = { ...mappingsBySource.value, [sourceId]: items };
        } catch (e) {
            $q.notify({ type: 'negative', message: describeApiError(e) });
        }
    }

    async function onAssign(
        sourceId: string,
        mapping: IngestionStoreMapping,
        merchantId: string | null
    ) {
        try {
            const updated = await api.upsertMappingAsync(sourceId, {
                external_name: mapping.external_name,
                merchant_id: merchantId
            });
            mappingsBySource.value = {
                ...mappingsBySource.value,
                [sourceId]: (mappingsBySource.value[sourceId] ?? []).map(m =>
                    m.id === updated.id ? updated : m
                )
            };
        } catch (e) {
            $q.notify({ type: 'negative', message: describeApiError(e) });
        }
    }

    function onDeleteMapping(sourceId: string, mapping: IngestionStoreMapping) {
        $q.dialog({
            title: 'Drop mapping',
            message: `Drop the mapping for "${mapping.external_name}"? Future pushes will quarantine until you map it again.`,
            ok: { color: 'negative', label: 'Drop', noCaps: true },
            cancel: { flat: true, label: 'Cancel', noCaps: true },
            persistent: true
        }).onOk(() => {
            void (async () => {
                try {
                    await api.deleteMappingAsync(sourceId, mapping.id);
                    mappingsBySource.value = {
                        ...mappingsBySource.value,
                        [sourceId]: (mappingsBySource.value[sourceId] ?? []).filter(
                            m => m.id !== mapping.id
                        )
                    };
                } catch (e) {
                    $q.notify({ type: 'negative', message: describeApiError(e) });
                }
            })();
        });
    }

    async function loadMerchants() {
        try {
            merchants.value = await api.listMerchantsAsync();
        } catch (e) {
            $q.notify({ type: 'negative', message: describeApiError(e) });
        }
    }

    async function loadSources() {
        loading.value = true;
        loadError.value = null;
        try {
            sources.value = await api.listAsync();
        } catch (e) {
            loadError.value = describeApiError(e);
        } finally {
            loading.value = false;
        }
    }

    function formatDate(iso: string) {
        return new Date(iso).toLocaleString();
    }

    function openCreate() {
        newLabel.value = '';
        createOpen.value = true;
    }

    async function onCreate() {
        creating.value = true;
        try {
            const result = await api.createAsync({ label: newLabel.value.trim() });
            sources.value = [...sources.value, result.source];
            revealedKey.value = result.key;
            createOpen.value = false;
            revealOpen.value = true;
        } catch (e) {
            $q.notify({ type: 'negative', message: describeApiError(e) });
        } finally {
            creating.value = false;
        }
    }

    async function copyRevealed() {
        try {
            await copyToClipboard(revealedKey.value);
            $q.notify({ type: 'positive', message: 'Key copied' });
        } catch {
            $q.notify({ type: 'negative', message: 'Copy failed' });
        }
    }

    function openRename(src: IngestionSource) {
        renameTarget.value = src;
        renameValue.value = src.label;
        renameOpen.value = true;
    }

    async function onRename() {
        if (!renameTarget.value) return;
        renaming.value = true;
        try {
            const updated = await api.updateAsync(renameTarget.value.id, {
                label: renameValue.value.trim()
            });
            sources.value = sources.value.map(s => (s.id === updated.id ? updated : s));
            renameOpen.value = false;
        } catch (e) {
            $q.notify({ type: 'negative', message: describeApiError(e) });
        } finally {
            renaming.value = false;
        }
    }

    async function onToggle(src: IngestionSource) {
        togglingId.value = src.id;
        try {
            const updated = await api.updateAsync(src.id, { enabled: !src.enabled });
            sources.value = sources.value.map(s => (s.id === updated.id ? updated : s));
        } catch (e) {
            $q.notify({ type: 'negative', message: describeApiError(e) });
        } finally {
            togglingId.value = null;
        }
    }

    function onRevoke(src: IngestionSource) {
        $q.dialog({
            title: 'Revoke key',
            message: `"${src.label}" will stop being accepted immediately. This cannot be undone.`,
            ok: { color: 'negative', label: 'Revoke', noCaps: true },
            cancel: { flat: true, label: 'Cancel', noCaps: true },
            persistent: true
        }).onOk(() => {
            void (async () => {
                revokingId.value = src.id;
                try {
                    await api.deleteAsync(src.id);
                    sources.value = sources.value.filter(s => s.id !== src.id);
                } catch (e) {
                    $q.notify({ type: 'negative', message: describeApiError(e) });
                } finally {
                    revokingId.value = null;
                }
            })();
        });
    }

    onMounted(() => {
        void loadSources();
        void loadMerchants();
    });
</script>

<style scoped>
    .reveal-readout :deep(input) {
        font-family: var(--font-mono, monospace);
        font-size: 0.9rem;
    }
</style>
