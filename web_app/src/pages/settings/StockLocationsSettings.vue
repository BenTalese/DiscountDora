<template>
    <div class="settings-page">
        <SettingsPageHeader
            title="Stock locations"
            description="Where things live. Zones at the top (e.g. Pantry), areas inside (e.g. Top shelf), sections inside those (e.g. Left). Items can attach at any level."
            :icon="ICONS.place"
        >
            <template #actions>
                <BaseButton
                    :icon="ICONS.add"
                    label="New zone"
                    @click="onAddChild(null, 'zone')"
                />
            </template>
        </SettingsPageHeader>

        <q-banner v-if="loadError" class="dora-bg-negative-soft text-negative q-mb-md" dense rounded>
            {{ loadError }}
        </q-banner>

        <div v-if="!loading && tree.length === 0" class="q-pa-lg text-center dora-text-muted">
            No zones yet. Create one to start organising your pantry.
        </div>

        <q-list class="settings-list" separator>
            <LocationRow
                v-for="zone in tree"
                :key="zone.location_id"
                :node="zone"
                :depth="0"
                :expanded="expanded"
                :editing-id="editingId"
                :rename-draft="renameDraft"
                @toggle="toggleExpanded"
                @start-rename="startRename"
                @save-rename="saveRename"
                @cancel-rename="cancelRename"
                @update:rename-draft="renameDraft = $event"
                @add-child="onAddChild"
                @delete="onDelete"
            />
        </q-list>

        <q-inner-loading :showing="loading && tree.length === 0">
            <q-spinner color="primary" size="48px" />
        </q-inner-loading>
    </div>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import { useQuasar } from 'quasar';
    import { computed, onMounted, ref } from 'vue';
    import type { LocationKind, LocationNode } from 'src/models/location';
    import { useLocationStore } from 'src/stores/locationStore';
    import { describeApiError } from 'src/services/errorHandling/apiErrorHandler';
    import BaseButton from 'src/components/BaseButton.vue';
    import LocationRow from 'src/components/settings/LocationRow.vue';
    import SettingsPageHeader from 'src/components/settings/SettingsPageHeader.vue';

    const $q = useQuasar();
    const locationStore = useLocationStore();

    const tree = computed(() => locationStore.tree);
    const loading = computed(() => locationStore.loading);
    const loadError = computed(() => locationStore.loadError);

    const expanded = ref<Set<string>>(new Set());
    const editingId = ref<string | null>(null);
    const renameDraft = ref('');

    function toggleExpanded(id: string) {
        if (expanded.value.has(id)) expanded.value.delete(id);
        else expanded.value.add(id);
    }

    function startRename(node: LocationNode) {
        editingId.value = node.location_id;
        renameDraft.value = node.name;
    }

    function cancelRename() {
        editingId.value = null;
        renameDraft.value = '';
    }

    async function saveRename(node: LocationNode) {
        const next = renameDraft.value.trim();
        if (!next || next === node.name) {
            cancelRename();
            return;
        }
        try {
            await locationStore.updateAsync(node.location_id, { name: next });
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not rename.',
                caption: describeApiError(err) || '',
            });
        } finally {
            cancelRename();
        }
    }

    function childKind(parentKind: LocationKind | null): LocationKind | null {
        if (parentKind === null) return 'zone';
        if (parentKind === 'zone') return 'area';
        if (parentKind === 'area') return 'section';
        return null;
    }

    async function onAddChild(parent: LocationNode | null, forcedKind?: LocationKind) {
        const kind = forcedKind ?? childKind(parent?.kind ?? null);
        if (!kind) return;
        const name = await new Promise<string | null>((resolve) => {
            $q.dialog({
                title: `New ${kind}`,
                message: `What's this ${kind} called?`,
                prompt: { model: '', type: 'text' },
                cancel: true,
            })
                .onOk((v: string) => resolve(v.trim()))
                .onCancel(() => resolve(null))
                .onDismiss(() => resolve(null));
        });
        if (!name) return;
        try {
            await locationStore.createAsync({
                name,
                kind,
                parent_id: parent?.location_id ?? null,
            });
            if (parent) expanded.value.add(parent.location_id);
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: `Could not add ${kind}.`,
                caption: describeApiError(err) || '',
            });
        }
    }

    async function onDelete(node: LocationNode) {
        const subtreeItems = node.descendant_item_count;
        const hasChildren = node.children.length > 0;
        const messageParts: string[] = [];
        if (hasChildren) {
            messageParts.push(
                `Everything under "${node.name}" (areas, sections) will also be removed.`
            );
        }
        if (subtreeItems > 0) {
            messageParts.push(
                `${subtreeItems} item${subtreeItems === 1 ? '' : 's'} stored here will become unassigned — the items themselves stay in your stock.`
            );
        }
        if (messageParts.length === 0) {
            messageParts.push('Nothing is stored here.');
        }

        const ok = await new Promise<boolean>((resolve) => {
            $q.dialog({
                title: `Delete "${node.name}"?`,
                message: messageParts.join(' '),
                cancel: true,
                ok: { label: 'Delete', color: 'negative', noCaps: true },
            })
                .onOk(() => resolve(true))
                .onCancel(() => resolve(false))
                .onDismiss(() => resolve(false));
        });
        if (!ok) return;
        try {
            await locationStore.deleteAsync(node.location_id);
            expanded.value.delete(node.location_id);
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not delete.',
                caption: describeApiError(err) || '',
            });
        }
    }

    onMounted(() => {
        if (locationStore.tree.length === 0) {
            void locationStore.refreshAsync();
        }
    });
</script>

<style scoped lang="scss">
    .settings-page { display: flex; flex-direction: column; position: relative; }
    .settings-list {
        border-top: 1px solid color-mix(in srgb, var(--text-primary) 8%, transparent);
        border-bottom: 1px solid color-mix(in srgb, var(--text-primary) 8%, transparent);
    }
</style>
