<template>
    <div class="settings-page">
        <SettingsPageHeader
            title="API access"
            description="Bearer keys for authenticated sources that push data into Dora. Always-on; not tied to any feature being enabled."
            :icon="ICONS.key"
        >
            <template #actions>
                <BaseButton
                    variant="icon"
                    :icon="ICONS.refresh"
                    :loading="loading"
                    @click="loadSources"
                >
                    <q-tooltip>Refresh</q-tooltip>
                </BaseButton>
                <BaseButton
                    variant="primary"
                    :icon="ICONS.add"
                    label="New key"
                    @click="openCreate"
                />
            </template>
        </SettingsPageHeader>

        <q-banner
            v-if="loadError"
            class="dora-bg-negative-soft text-negative q-mb-md"
            dense
            rounded
        >
            {{ loadError }}
        </q-banner>

        <q-list class="settings-list" separator>
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
                            <BaseButton
                                variant="ghost"
                                dense
                                :icon="src.enabled ? ICONS.lock : ICONS.lock_open"
                                :label="src.enabled ? 'Disable' : 'Enable'"
                                :loading="togglingId === src.id"
                                @click="onToggle(src)"
                            />
                            <BaseButton
                                variant="ghost"
                                dense
                                :icon="ICONS.edit"
                                label="Rename"
                                @click="openRename(src)"
                            />
                            <BaseButton
                                variant="danger-ghost"
                                dense
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
                            mapped to one of your Dora stores. Pushes
                            against an unmapped name are skipped and
                            surface here as pending — they never
                            auto-create a store.
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
                                            v-if="!m.store_id"
                                            color="warning"
                                            text-color="white"
                                            class="q-ml-sm"
                                        >
                                            pending
                                        </q-badge>
                                    </q-item-label>
                                    <q-item-label caption>
                                        <span v-if="m.store_name">
                                            → {{ m.store_name }}
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
                                            :model-value="m.store_id"
                                            :options="storeOptions"
                                            option-value="value"
                                            option-label="label"
                                            emit-value
                                            map-options
                                            dense
                                            outlined
                                            clearable
                                            label="Store"
                                            style="min-width: 200px"
                                            @update:model-value="(value: string | null) => onAssign(src.id, m, value)"
                                        />
                                        <BaseButton
                                            variant="danger-icon"
                                            dense
                                            :icon="ICONS.delete"
                                            @click="onDeleteMapping(src.id, m)"
                                        >
                                            <q-tooltip>Drop this mapping entirely</q-tooltip>
                                        </BaseButton>
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
            <AppSpinner size="48px" />
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
                <BaseButton
                    variant="primary"
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
                        <BaseButton
                            variant="icon"
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
                <BaseButton
                    variant="primary"
                    label="Save"
                    :loading="renaming"
                    :disable="!renameValue.trim()"
                    @click="onRename"
                />
            </template>
        </BaseDialog>
    </div>
</template>

<script lang="ts" setup>
    import AppSpinner from 'src/components/AppSpinner.vue';
    import { formatDateTime as formatLocaleDateTime } from 'src/composables/useDateFormat';
    import BaseButton from 'src/components/BaseButton.vue';
    import BaseDialog from 'src/components/BaseDialog.vue';
    import { ICONS } from 'src/style/icons';
    import { copyToClipboard, useQuasar } from 'quasar';
    import SettingsPageHeader from 'src/components/settings/SettingsPageHeader.vue';
    import IngestionSourcesApiService, {
        type DoraStore,
        type IngestionSource,
        type IngestionStoreMapping
    } from 'src/services/api/ingestionSourcesApiService';
    import { computed, onMounted, ref } from 'vue';
    import { toastCaption } from 'src/services/errorHandling/apiErrorHandler';

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
    const stores = ref<DoraStore[]>([]);

    const storeOptions = computed(() =>
        stores.value.map(s => ({ value: s.store_id, label: s.name }))
    );

    function pendingCountFor(sourceId: string): number {
        return (mappingsBySource.value[sourceId] ?? []).filter(m => !m.store_id).length;
    }

    function captionFor(_src: IngestionSource): string {
        return '';
    }

    async function loadMappings(sourceId: string) {
        try {
            const items = await api.listMappingsAsync(sourceId);
            mappingsBySource.value = { ...mappingsBySource.value, [sourceId]: items };
        } catch (e) {
            $q.notify({ type: 'negative', message: "Couldn't load mappings.", caption: toastCaption(e) });
        }
    }

    async function onAssign(
        sourceId: string,
        mapping: IngestionStoreMapping,
        storeId: string | null
    ) {
        try {
            const updated = await api.upsertMappingAsync(sourceId, {
                external_name: mapping.external_name,
                store_id: storeId
            });
            mappingsBySource.value = {
                ...mappingsBySource.value,
                [sourceId]: (mappingsBySource.value[sourceId] ?? []).map(m =>
                    m.id === updated.id ? updated : m
                )
            };
        } catch (e) {
            $q.notify({ type: 'negative', message: "Couldn't update the mapping.", caption: toastCaption(e) });
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
                    $q.notify({ type: 'negative', message: "Couldn't drop the mapping.", caption: toastCaption(e) });
                }
            })();
        });
    }

    async function loadStores() {
        try {
            stores.value = await api.listStoresAsync();
        } catch (e) {
            $q.notify({ type: 'negative', message: "Couldn't load stores.", caption: toastCaption(e) });
        }
    }

    async function loadSources() {
        loading.value = true;
        loadError.value = null;
        try {
            sources.value = await api.listAsync();
        } catch (e) {
            loadError.value = toastCaption(e);
        } finally {
            loading.value = false;
        }
    }

    function formatDate(iso: string) {
        return formatLocaleDateTime(iso);
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
            $q.notify({ type: 'negative', message: "Couldn't create the API key.", caption: toastCaption(e) });
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
            $q.notify({ type: 'negative', message: "Couldn't rename the API key.", caption: toastCaption(e) });
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
            $q.notify({ type: 'negative', message: "Couldn't toggle the API key.", caption: toastCaption(e) });
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
                    $q.notify({ type: 'negative', message: "Couldn't revoke the API key.", caption: toastCaption(e) });
                } finally {
                    revokingId.value = null;
                }
            })();
        });
    }

    onMounted(() => {
        void loadSources();
        void loadStores();
    });
</script>

<style scoped lang="scss">
    .settings-page { display: flex; flex-direction: column; }
    .settings-list {
        border-top: 1px solid color-mix(in srgb, var(--text-primary) 8%, transparent);
        border-bottom: 1px solid color-mix(in srgb, var(--text-primary) 8%, transparent);
    }
    .reveal-readout :deep(input) {
        font-family: var(--font-mono, monospace);
        font-size: 0.9rem;
    }
</style>
