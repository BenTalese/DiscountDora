<template>
    <q-page padding>
        <div class="row items-center q-mb-md">
            <div>
                <div class="text-h5">Where things live</div>
                <div class="text-caption text-grey">
                    Your zones, ranked by what needs attention.
                </div>
            </div>
            <q-space />
            <q-btn
                flat
                no-caps
                icon="search"
                label="Search"
                @click="searchOpen = true"
            />
            <q-btn
                flat
                round
                dense
                icon="refresh"
                :loading="loading"
                @click="locationStore.refreshAsync"
            >
                <q-tooltip>Refresh attention scores</q-tooltip>
            </q-btn>
            <q-btn
                color="primary"
                no-caps
                icon="add"
                label="New zone"
                class="q-ml-sm"
                @click="onCreateZone"
            />
        </div>

        <q-banner
            v-if="loadError"
            class="bg-red-1 text-red-9 q-mb-md"
            dense
            rounded
        >
            {{ loadError }}
        </q-banner>

        <div v-if="loading && tree.length === 0" class="text-center q-py-xl">
            <q-spinner color="primary" size="48px" />
        </div>

        <div v-else-if="tree.length === 0" class="text-center text-grey q-py-xl">
            <q-icon name="inbox" size="60px" class="q-mb-sm" />
            <div>No zones yet. Create one to get started.</div>
        </div>

        <div v-else class="row q-col-gutter-md">
            <div
                v-for="zone in sortedZones"
                :key="zone.location_id"
                class="col-12 col-sm-6 col-md-4 col-lg-3"
            >
                <q-card
                    flat
                    bordered
                    class="cursor-pointer zone-card drop-target"
                    :class="{ 'drop-target-active': hoveringLocationId === zone.location_id }"
                    :style="{ background: attentionBackground(zone.attention_score) }"
                    @click="onOpenZone(zone.location_id)"
                    @dragenter="onDragEnter($event, zone.location_id)"
                    @dragover="onDragOver($event, zone.location_id)"
                    @dragleave="onDragLeave($event, zone.location_id)"
                    @drop="onDrop($event, zone.location_id)"
                >
                    <q-card-section class="row items-start q-pb-none">
                        <div class="col">
                            <div class="text-h6">{{ zone.name }}</div>
                            <div class="text-caption text-grey">
                                {{ zone.descendant_item_count }} item{{
                                    zone.descendant_item_count === 1 ? '' : 's'
                                }}
                            </div>
                        </div>
                        <q-chip
                            dense
                            square
                            :color="attentionColor(zone.attention_score)"
                            text-color="white"
                            class="q-ml-sm"
                        >
                            {{ zone.attention_score }}
                        </q-chip>
                    </q-card-section>

                    <q-card-section class="q-pt-sm">
                        <div v-if="zone.primary_reason" class="text-body2">
                            {{ zone.primary_reason }}
                        </div>
                        <div v-else class="text-caption text-grey">
                            All quiet. Nothing here needs your attention.
                        </div>

                        <div
                            v-if="reasonChips(zone).length > 0"
                            class="row q-gutter-xs q-mt-sm"
                        >
                            <q-chip
                                v-for="(reason, idx) in reasonChips(zone)"
                                :key="idx"
                                dense
                                outline
                                size="sm"
                            >
                                {{ reason }}
                            </q-chip>
                        </div>
                    </q-card-section>
                </q-card>
            </div>
        </div>

        <SearchOverlay v-model="searchOpen" />
    </q-page>
</template>

<script lang="ts" setup>
    import { useQuasar } from 'quasar';
    import SearchOverlay from 'src/components/locations/SearchOverlay.vue';
    import { useItemDrop } from 'src/components/locations/useItemDrop';
    import {
        attentionBackground,
        attentionColor,
        summarizeReasons,
        type LocationNode
    } from 'src/models/location';
    import { useLocationStore } from 'src/stores/locationStore';
    import { computed, onMounted, ref } from 'vue';
    import { useRouter } from 'vue-router';

    const $q = useQuasar();
    const router = useRouter();
    const locationStore = useLocationStore();

    const tree = computed(() => locationStore.tree);
    const loading = computed(() => locationStore.loading);
    const loadError = computed(() => locationStore.loadError);

    const sortedZones = computed(() =>
        // Most-attention-grabbing first so users see what to deal with.
        [...tree.value].sort(
            (a, b) =>
                b.attention_score - a.attention_score ||
                a.sequence - b.sequence ||
                a.name.localeCompare(b.name)
        )
    );

    const searchOpen = ref(false);

    // Zone cards on this page accept dropped items from other zones (e.g.
    // dragging from a search result or another tab in a multi-window setup).
    // The drop goes straight to the zone-level bucket — users can drill in
    // to file it more precisely later.
    const { hoveringLocationId, onDragEnter, onDragOver, onDragLeave, onDrop } = useItemDrop();

    function reasonChips(node: LocationNode): string[] {
        return summarizeReasons(node.attention_reasons).slice(0, 3);
    }

    function onOpenZone(id: string) {
        void router.push(`/locations/${id}`);
    }

    async function onCreateZone() {
        const name = await new Promise<string | null>((resolve) => {
            $q.dialog({
                title: 'New zone',
                message: "What's this zone called? E.g. Pantry, Garage, Laundry cupboard.",
                prompt: { model: '', type: 'text' },
                cancel: true
            })
                .onOk((data: string) => resolve(data.trim()))
                .onCancel(() => resolve(null))
                .onDismiss(() => resolve(null));
        });
        if (!name) return;
        try {
            await locationStore.createAsync({ name, kind: 'zone', parent_id: null });
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: `Created zone "${name}".`
            });
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not create zone.',
                caption: String(err)
            });
        }
    }

    onMounted(() => {
        if (locationStore.tree.length === 0) {
            void locationStore.refreshAsync();
        }
    });
</script>

<style scoped>
    .zone-card {
        transition: transform 120ms ease, box-shadow 120ms ease,
            outline-color 120ms ease, background-color 120ms ease;
        outline: 2px dashed transparent;
        outline-offset: -2px;
    }
    .zone-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.08);
    }
    .drop-target-active {
        outline-color: var(--q-primary);
        transform: translateY(-2px);
    }
</style>
