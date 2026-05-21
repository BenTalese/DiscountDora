<template>
    <q-dialog v-model="open" persistent>
        <q-card style="min-width: 360px; max-width: 480px">
            <q-card-section class="row items-center q-pb-none">
                <div>
                    <div class="text-h6">Move "{{ itemName }}"</div>
                    <div class="text-caption text-grey">
                        Pick a destination. Items here will be placed there
                        immediately.
                    </div>
                </div>
                <q-space />
                <q-btn flat round dense icon="close" v-close-popup />
            </q-card-section>

            <q-separator class="q-mt-md" />

            <q-card-section v-if="loading" class="text-center">
                <q-spinner color="primary" size="32px" />
            </q-card-section>

            <q-card-section v-else>
                <q-input
                    v-model="filterText"
                    outlined
                    dense
                    placeholder="Filter locations…"
                    clearable
                    autofocus
                >
                    <template #prepend><q-icon name="search" /></template>
                </q-input>

                <q-list class="q-mt-sm move-picker-list" separator>
                    <q-item
                        v-if="currentZoneNode"
                        clickable
                        :active="selectedId === currentZoneNode.location_id"
                        @click="selectedId = currentZoneNode.location_id"
                    >
                        <q-item-section avatar>
                            <q-icon name="home_pin" />
                        </q-item-section>
                        <q-item-section>
                            <q-item-label class="text-weight-medium">
                                {{ currentZoneNode.name }}
                            </q-item-label>
                            <q-item-label caption>Current zone — top level</q-item-label>
                        </q-item-section>
                    </q-item>

                    <q-item-label
                        v-if="currentZoneFlatNodes.length > 1"
                        header
                        class="picker-section-header"
                    >
                        Other places in {{ currentZoneNode?.name }}
                    </q-item-label>

                    <q-item
                        v-for="node in currentZoneFlatNodes.filter(
                            (n) => n.location_id !== currentZoneNode?.location_id
                        )"
                        :key="node.location_id"
                        clickable
                        :active="selectedId === node.location_id"
                        @click="selectedId = node.location_id"
                    >
                        <q-item-section avatar>
                            <q-icon :name="iconForKind(node.kind)" />
                        </q-item-section>
                        <q-item-section>
                            <q-item-label>{{ node.name }}</q-item-label>
                            <q-item-label caption>
                                {{ pathFor(node.location_id).join(' › ') }}
                            </q-item-label>
                        </q-item-section>
                    </q-item>

                    <q-item-label
                        v-if="otherZoneFlatNodes.length > 0"
                        header
                        class="picker-section-header"
                    >
                        Other zones
                    </q-item-label>

                    <q-item
                        v-for="node in otherZoneFlatNodes"
                        :key="node.location_id"
                        clickable
                        :active="selectedId === node.location_id"
                        @click="selectedId = node.location_id"
                    >
                        <q-item-section avatar>
                            <q-icon :name="iconForKind(node.kind)" />
                        </q-item-section>
                        <q-item-section>
                            <q-item-label>{{ node.name }}</q-item-label>
                            <q-item-label caption>
                                {{ pathFor(node.location_id).join(' › ') }}
                            </q-item-label>
                        </q-item-section>
                    </q-item>

                    <q-item
                        clickable
                        :active="selectedId === '__unassigned__'"
                        @click="selectedId = '__unassigned__'"
                    >
                        <q-item-section avatar>
                            <q-icon name="inbox" />
                        </q-item-section>
                        <q-item-section>
                            <q-item-label>Unassigned</q-item-label>
                            <q-item-label caption>
                                Park the item without a home for now.
                            </q-item-label>
                        </q-item-section>
                    </q-item>
                </q-list>
            </q-card-section>

            <q-separator />

            <q-card-actions align="right">
                <q-btn flat no-caps label="Cancel" v-close-popup />
                <q-btn
                    color="primary"
                    no-caps
                    label="Move here"
                    :disable="!selectedId"
                    :loading="saving"
                    @click="onConfirm"
                />
            </q-card-actions>
        </q-card>
    </q-dialog>
</template>

<script lang="ts" setup>
    import { useQuasar } from 'quasar';
    import type { LocationNode } from 'src/models/location';
    import StockItemApiService from 'src/services/api/stockItemApiService';
    import { useLocationStore } from 'src/stores/locationStore';
    import { computed, ref, watch } from 'vue';

    const props = defineProps<{
        modelValue: boolean;
        itemId: string;
        itemName: string;
        // Optional. Used to highlight "current zone" first in the picker so
        // the most common move (within the same zone) is one click.
        currentLocationId?: string | null;
    }>();

    const emit = defineEmits<{
        (e: 'update:modelValue', value: boolean): void;
        (e: 'moved', destinationLocationId: string | null): void;
    }>();

    const $q = useQuasar();
    const locationStore = useLocationStore();
    const stockItemApi = new StockItemApiService();

    const open = computed({
        get: () => props.modelValue,
        set: (v) => emit('update:modelValue', v)
    });

    const loading = ref(false);
    const saving = ref(false);
    const filterText = ref('');
    const selectedId = ref<string | null>(null);

    watch(open, async (v) => {
        if (!v) return;
        selectedId.value = null;
        filterText.value = '';
        if (locationStore.tree.length === 0) {
            loading.value = true;
            try {
                await locationStore.refreshAsync();
            } finally {
                loading.value = false;
            }
        }
    });

    // Flatten a sub-tree for the picker list. We surface every descendant
    // so users can land on a zone, an area, or a section.
    function flatten(node: LocationNode): LocationNode[] {
        const out: LocationNode[] = [node];
        for (const child of node.children) out.push(...flatten(child));
        return out;
    }

    // Find the top-level zone that contains a given location id.
    function findZoneFor(locationId: string | null | undefined): LocationNode | null {
        if (!locationId) return null;
        for (const zone of locationStore.tree) {
            if (flatten(zone).some((n) => n.location_id === locationId)) {
                return zone;
            }
        }
        return null;
    }

    const currentZoneNode = computed(() => findZoneFor(props.currentLocationId));

    const matches = (n: LocationNode) =>
        !filterText.value ||
        n.name.toLowerCase().includes(filterText.value.toLowerCase()) ||
        pathFor(n.location_id).join(' ').toLowerCase().includes(filterText.value.toLowerCase());

    const currentZoneFlatNodes = computed(() => {
        if (!currentZoneNode.value) return [];
        return flatten(currentZoneNode.value).filter(matches);
    });

    const otherZoneFlatNodes = computed(() => {
        const currentId = currentZoneNode.value?.location_id ?? null;
        const out: LocationNode[] = [];
        for (const zone of locationStore.tree) {
            if (zone.location_id === currentId) continue;
            for (const n of flatten(zone)) {
                if (matches(n)) out.push(n);
            }
        }
        return out;
    });

    function pathFor(locationId: string): string[] {
        return locationStore.breadcrumb(locationId);
    }

    function iconForKind(kind: string) {
        if (kind === 'zone') return 'home_pin';
        if (kind === 'area') return 'shelves';
        return 'inventory_2';
    }

    async function onConfirm() {
        if (!selectedId.value) return;
        const destination = selectedId.value === '__unassigned__' ? null : selectedId.value;
        saving.value = true;
        try {
            await stockItemApi.moveAsync(props.itemId, destination);
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: 'Item moved.'
            });
            emit('moved', destination);
            await locationStore.refreshAsync();
            open.value = false;
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not move the item.',
                caption: String(err)
            });
        } finally {
            saving.value = false;
        }
    }
</script>

<style scoped>
    .move-picker-list {
        max-height: 50vh;
        overflow-y: auto;
    }
    .picker-section-header {
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #888;
        padding-top: 12px;
    }
</style>
