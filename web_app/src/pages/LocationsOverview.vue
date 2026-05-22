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
                    @click="onOpenPanel(zone)"
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

        <!-- Side panel: opens when a zone card is clicked. Lists the items
             living anywhere under the zone (flattened across descendants)
             and exposes the cross-feature shortcuts the spec calls for
             (filter Stock to attention items here, generate a shopping list
             from low/out items here). Click-to-navigate stays available
             via the "Open zone page" button. -->
        <q-dialog v-model="panelOpen" position="right" :maximized="$q.screen.lt.sm">
            <q-card class="location-panel column no-wrap">
                <q-card-section
                    class="row items-center q-py-sm"
                    :style="{
                        background: panelZone
                            ? attentionBackground(panelZone.attention_score)
                            : undefined,
                    }"
                >
                    <div class="col">
                        <div class="text-h6">{{ panelZone?.name ?? 'Zone' }}</div>
                        <div class="text-caption text-grey">
                            {{ panelZone?.descendant_item_count ?? 0 }} items ·
                            score {{ panelZone?.attention_score ?? 0 }}
                            <span v-if="panelZone?.primary_reason">
                                · {{ panelZone.primary_reason }}
                            </span>
                        </div>
                    </div>
                    <q-btn flat round dense icon="close" v-close-popup />
                </q-card-section>

                <q-card-section class="q-py-sm">
                    <div class="row q-gutter-xs">
                        <q-btn
                            color="primary"
                            no-caps
                            icon="open_in_new"
                            label="Open zone page"
                            size="sm"
                            @click="onOpenPanelZonePage"
                        />
                        <q-btn
                            outline
                            no-caps
                            icon="priority_high"
                            label="Needs attention here"
                            size="sm"
                            :disable="(panelZone?.attention_score ?? 0) === 0"
                            @click="onShowAttentionInStock"
                        />
                        <q-btn
                            outline
                            no-caps
                            icon="auto_awesome"
                            :label="
                                lowOrOutSubtreeIds.length > 0
                                    ? `Shopping list (${lowOrOutSubtreeIds.length})`
                                    : 'Shopping list'
                            "
                            size="sm"
                            :loading="generatingList"
                            :disable="lowOrOutSubtreeIds.length === 0"
                            @click="onGenerateListForZone"
                        />
                    </div>
                </q-card-section>

                <q-separator />

                <q-card-section class="col scroll q-pt-sm">
                    <div
                        v-if="panelZoneItems.length === 0"
                        class="text-center text-grey q-py-md"
                    >
                        Nothing stored anywhere under this zone yet.
                    </div>
                    <div v-else class="row q-col-gutter-sm">
                        <ItemChip
                            v-for="item in panelZoneItems"
                            :key="`${item.locationId}:${item.stock_item_id}`"
                            :item="item"
                            :current-location-id="item.locationId"
                            @click="onOpenItem(item.stock_item_id)"
                            @move="onStartMoveFromPanel(item)"
                        />
                    </div>
                </q-card-section>

                <MoveItemDialog
                    v-if="panelMoveTarget"
                    v-model="panelMoveOpen"
                    :item-id="panelMoveTarget.itemId"
                    :item-name="panelMoveTarget.itemName"
                    :current-location-id="panelMoveTarget.currentLocationId"
                />
            </q-card>
        </q-dialog>
    </q-page>
</template>

<script lang="ts" setup>
    import { useQuasar } from 'quasar';
    import ItemChip from 'src/components/locations/ItemChip.vue';
    import MoveItemDialog from 'src/components/locations/MoveItemDialog.vue';
    import SearchOverlay from 'src/components/locations/SearchOverlay.vue';
    import { useItemDrop } from 'src/components/locations/useItemDrop';
    import {
        attentionBackground,
        attentionColor,
        summarizeReasons,
        type LocationItem,
        type LocationNode,
    } from 'src/models/location';
    import ShoppingListApiService from 'src/services/api/shoppingListApiService';
    import { useLocationStore } from 'src/stores/locationStore';
    import { useShoppingListStore } from 'src/stores/shoppingListStore';
    import { computed, onMounted, ref } from 'vue';
    import { useRouter } from 'vue-router';

    const $q = useQuasar();
    const router = useRouter();
    const locationStore = useLocationStore();
    const shoppingListStore = useShoppingListStore();
    const shoppingListApi = new ShoppingListApiService();

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

    // ── Side panel ───────────────────────────────────────────────────
    // Clicking a card opens this; the panel shows everything stored
    // anywhere under the zone (a flat roll-up), plus the spec's
    // cross-feature shortcuts. The zone *page* is one button away so
    // power-users keep their existing navigation.
    const panelOpen = ref(false);
    const panelZone = ref<LocationNode | null>(null);
    const panelMoveOpen = ref(false);
    const panelMoveTarget = ref<{
        itemId: string;
        itemName: string;
        currentLocationId: string;
    } | null>(null);
    const generatingList = ref(false);

    type ZoneItem = LocationItem & { locationId: string };

    // Walk a subtree and flatten every item, tagging each with the
    // location it actually lives in so drag-from-panel works and
    // grouping is possible if we want it later.
    function collectItems(node: LocationNode): ZoneItem[] {
        const out: ZoneItem[] = [];
        const stack: LocationNode[] = [node];
        while (stack.length) {
            const n = stack.pop()!;
            for (const item of n.items) {
                out.push({ ...item, locationId: n.location_id });
            }
            for (const child of n.children) stack.push(child);
        }
        return out.sort((a, b) => b.attention_score - a.attention_score
            || a.name.localeCompare(b.name));
    }

    const panelZoneItems = computed<ZoneItem[]>(() =>
        panelZone.value ? collectItems(panelZone.value) : [],
    );

    // Stock-item ids in the subtree that are Low or Out — used to
    // pre-fill an auto-generated shopping list scoped to this area.
    const lowOrOutSubtreeIds = computed<string[]>(() => {
        if (!panelZone.value) return [];
        const lowOutNames = new Set(['Low Stock', 'Out of Stock']);
        return panelZoneItems.value
            .filter((i) => i.stock_level_name !== null && lowOutNames.has(i.stock_level_name))
            .map((i) => i.stock_item_id);
    });

    function onOpenPanel(zone: LocationNode) {
        panelZone.value = zone;
        panelOpen.value = true;
    }

    function onOpenPanelZonePage() {
        if (!panelZone.value) return;
        const id = panelZone.value.location_id;
        panelOpen.value = false;
        void router.push(`/locations/${id}`);
    }

    function onShowAttentionInStock() {
        if (!panelZone.value) return;
        panelOpen.value = false;
        void router.push({
            path: '/stock',
            query: {
                location_id: panelZone.value.location_id,
                attention: 'true',
            },
        });
    }

    function onOpenItem(stockItemId: string) {
        panelOpen.value = false;
        void router.push(`/stock/${stockItemId}`);
    }

    function onStartMoveFromPanel(item: ZoneItem) {
        panelMoveTarget.value = {
            itemId: item.stock_item_id,
            itemName: item.name,
            currentLocationId: item.locationId,
        };
        panelMoveOpen.value = true;
    }

    async function onGenerateListForZone() {
        if (!panelZone.value || lowOrOutSubtreeIds.value.length === 0) return;
        const zone = panelZone.value;
        generatingList.value = true;
        try {
            const { shopping_list_id } = await shoppingListApi.createAsync({
                name: `Restock ${zone.name}`,
                make_primary: !shoppingListStore.primarySummary,
            });
            let added = 0;
            let skipped = 0;
            for (const id of lowOrOutSubtreeIds.value) {
                try {
                    const result = await shoppingListApi.addLineAsync(shopping_list_id, {
                        stock_item_id: id,
                    });
                    if (result.already_on_list) skipped++;
                    else added++;
                } catch {
                    skipped++;
                }
            }
            await shoppingListStore.refreshAsync();
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message:
                    `Created "Restock ${zone.name}". ${added} added` +
                    (skipped > 0 ? `, ${skipped} skipped` : '') + '.',
                actions: [
                    {
                        label: 'Open',
                        color: 'white',
                        handler: () => router.push(`/shopping-lists/${shopping_list_id}`),
                    },
                ],
            });
            panelOpen.value = false;
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not generate list.',
                caption: String(err),
            });
        } finally {
            generatingList.value = false;
        }
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
    .location-panel {
        width: 480px;
        max-width: 100vw;
        height: 100vh;
    }
</style>
