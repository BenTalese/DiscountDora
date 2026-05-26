<template>
    <q-page padding>
        <div class="row items-center q-mb-md">
            <q-btn flat round dense icon="arrow_back" @click="onBack" />
            <div class="q-ml-sm">
                <div class="text-h5">{{ zone?.name ?? 'Loading…' }}</div>
                <div class="text-caption text-grey">
                    {{ zone?.descendant_item_count ?? 0 }} items ·
                    score {{ zone?.attention_score ?? 0 }}
                </div>
            </div>
            <q-space />
            <q-btn
                v-if="zone"
                flat
                no-caps
                icon="add"
                :label="`Add ${childKind(zone.kind)}`"
                @click="onAddChild(zone)"
            />
            <q-btn
                v-if="zone"
                outline
                no-caps
                icon="priority_high"
                label="Needs attention here"
                class="q-ml-sm"
                :disable="(zone.attention_score ?? 0) === 0"
                @click="onShowAttentionInStock(zone!)"
            >
                <q-tooltip>
                    Jump to Stock filtered to attention items in this zone.
                </q-tooltip>
            </q-btn>
            <q-btn
                v-if="zone"
                color="primary"
                no-caps
                icon="auto_awesome"
                :label="
                    lowOrOutSubtreeIds.length > 0
                        ? `Shopping list (${lowOrOutSubtreeIds.length})`
                        : 'Shopping list'
                "
                class="q-ml-sm"
                :loading="generatingList"
                :disable="lowOrOutSubtreeIds.length === 0"
                @click="onGenerateListForZone(zone!)"
            >
                <q-tooltip>
                    Create a list from every low/out item stored anywhere
                    under this zone.
                </q-tooltip>
            </q-btn>
        </div>

        <q-banner
            v-if="zone && (zone.attention_reasons.expired || zone.attention_score > 0)"
            class="q-mb-md"
            :style="{ background: attentionBackground(zone.attention_score) }"
            rounded
        >
            <template #avatar>
                <q-icon name="local_fire_department" />
            </template>
            <div class="text-weight-medium">
                {{ zone.primary_reason ?? 'All quiet.' }}
            </div>
            <div v-if="reasonChips(zone).length > 0" class="row q-gutter-xs q-mt-xs">
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
        </q-banner>

        <div v-if="zone" class="q-mb-lg">
            <div class="text-subtitle1 q-mb-sm">
                Items directly in {{ zone.name }}
                <span class="text-caption text-grey q-ml-sm">
                    · drop here to move
                </span>
            </div>
            <div
                class="row q-col-gutter-sm drop-target q-pa-sm"
                :class="{ 'drop-target-active': hoveringLocationId === zone.location_id }"
                @dragenter="onDragEnter($event, zone!.location_id)"
                @dragover="onDragOver($event, zone!.location_id)"
                @dragleave="onDragLeave($event, zone!.location_id)"
                @drop="onDrop($event, zone!.location_id)"
            >
                <ItemChip
                    v-for="item in zone.items"
                    :key="item.stock_item_id"
                    :item="item"
                    :current-location-id="zone.location_id"
                    @click="onOpenItem(item.stock_item_id)"
                    @move="onStartMove(item.stock_item_id, item.name, zone!.location_id)"
                />
                <span
                    v-if="zone.items.length === 0"
                    class="text-caption text-grey q-pa-sm"
                >
                    Nothing here. Drop an item or
                    <a href="#" class="text-primary" @click.prevent="onAddChild(zone!)">
                        add an area
                    </a>.
                </span>
            </div>
        </div>

        <template v-if="zone">
            <div
                v-for="area in zone.children"
                :key="area.location_id"
                class="q-mb-md"
            >
                <q-card
                    flat
                    bordered
                    class="drop-target"
                    :class="{ 'drop-target-active': hoveringLocationId === area.location_id }"
                    :style="{ background: attentionBackground(area.attention_score) }"
                    @dragenter="onDragEnter($event, area.location_id)"
                    @dragover="onDragOver($event, area.location_id)"
                    @dragleave="onDragLeave($event, area.location_id)"
                    @drop="onDrop($event, area.location_id)"
                >
                    <q-card-section
                        class="row items-center cursor-pointer"
                        @click="toggleExpanded(area.location_id)"
                    >
                        <q-icon
                            :name="
                                expanded.has(area.location_id)
                                    ? 'expand_more'
                                    : 'chevron_right'
                            "
                            size="20px"
                        />
                        <div class="q-ml-sm col">
                            <div class="text-subtitle1">{{ area.name }}</div>
                            <div class="text-caption text-grey">
                                {{ area.descendant_item_count }} items
                                <span v-if="area.primary_reason">
                                    · {{ area.primary_reason }}
                                </span>
                            </div>
                        </div>
                        <q-chip
                            dense
                            square
                            :color="attentionColor(area.attention_score)"
                            text-color="white"
                        >
                            {{ area.attention_score }}
                        </q-chip>
                        <q-btn
                            v-if="area.kind === 'area'"
                            flat
                            round
                            dense
                            icon="add"
                            class="q-ml-sm"
                            @click.stop="onAddChild(area)"
                        >
                            <q-tooltip>Add a section here</q-tooltip>
                        </q-btn>
                    </q-card-section>

                    <q-slide-transition>
                        <div v-show="expanded.has(area.location_id)">
                            <q-separator />
                            <q-card-section v-if="area.items.length > 0">
                                <div class="row q-col-gutter-sm">
                                    <ItemChip
                                        v-for="item in area.items"
                                        :key="item.stock_item_id"
                                        :item="item"
                                        :current-location-id="area.location_id"
                                        @click="onOpenItem(item.stock_item_id)"
                                        @move="
                                            onStartMove(
                                                item.stock_item_id,
                                                item.name,
                                                area.location_id
                                            )
                                        "
                                    />
                                </div>
                            </q-card-section>

                            <q-separator
                                v-if="area.items.length > 0 && area.children.length > 0"
                            />

                            <q-card-section
                                v-for="section in area.children"
                                :key="section.location_id"
                                class="q-py-sm drop-target"
                                :class="{
                                    'drop-target-active':
                                        hoveringLocationId === section.location_id
                                }"
                                @dragenter.stop="onDragEnter($event, section.location_id)"
                                @dragover.stop="onDragOver($event, section.location_id)"
                                @dragleave.stop="onDragLeave($event, section.location_id)"
                                @drop.stop="onDrop($event, section.location_id)"
                            >
                                <div class="row items-center q-mb-xs">
                                    <q-icon name="splitscreen" size="14px" />
                                    <div class="q-ml-xs text-weight-medium">
                                        {{ section.name }}
                                    </div>
                                    <q-chip
                                        v-if="section.attention_score > 0"
                                        dense
                                        square
                                        size="sm"
                                        :color="attentionColor(section.attention_score)"
                                        text-color="white"
                                        class="q-ml-sm"
                                    >
                                        {{ section.attention_score }}
                                    </q-chip>
                                    <span
                                        v-if="section.primary_reason"
                                        class="text-caption text-grey q-ml-sm"
                                    >
                                        {{ section.primary_reason }}
                                    </span>
                                </div>
                                <div class="row q-col-gutter-sm">
                                    <ItemChip
                                        v-for="item in section.items"
                                        :key="item.stock_item_id"
                                        :item="item"
                                        :current-location-id="section.location_id"
                                        @click="onOpenItem(item.stock_item_id)"
                                        @move="
                                            onStartMove(
                                                item.stock_item_id,
                                                item.name,
                                                section.location_id
                                            )
                                        "
                                    />
                                    <span
                                        v-if="section.items.length === 0"
                                        class="text-caption text-grey q-pl-sm"
                                    >
                                        Empty — drop something here.
                                    </span>
                                </div>
                            </q-card-section>
                        </div>
                    </q-slide-transition>
                </q-card>
            </div>
        </template>

        <MoveItemDialog
            v-if="moveTarget"
            v-model="moveDialogOpen"
            :item-id="moveTarget.itemId"
            :item-name="moveTarget.itemName"
            :current-location-id="moveTarget.currentLocationId"
        />
    </q-page>
</template>

<script lang="ts" setup>
    import { useQuasar } from 'quasar';
    import ItemChip from 'src/components/locations/ItemChip.vue';
    import MoveItemDialog from 'src/components/locations/MoveItemDialog.vue';
    import { useItemDrop } from 'src/components/locations/useItemDrop';
    import {
        attentionBackground,
        attentionColor,
        summarizeReasons,
        type LocationKind,
        type LocationNode
    } from 'src/models/location';
    import ShoppingListApiService from 'src/services/api/shoppingListApiService';
    import { useLocationStore } from 'src/stores/locationStore';
    import { useShoppingListStore } from 'src/stores/shoppingListStore';
    import { computed, onMounted, ref } from 'vue';
    import { useRoute, useRouter } from 'vue-router';
    import { describeApiError } from 'src/services/errorHandling/apiErrorHandler';

    const route = useRoute();
    const router = useRouter();
    const $q = useQuasar();
    const locationStore = useLocationStore();
    const shoppingListStore = useShoppingListStore();
    const shoppingListApi = new ShoppingListApiService();

    const zoneId = computed(() => String(route.params.id ?? ''));
    const zone = computed<LocationNode | null>(() =>
        zoneId.value ? locationStore.findNode(zoneId.value) : null
    );

    // Areas default to expanded so the page is useful immediately; user can
    // collapse if a zone gets noisy.
    const expanded = ref<Set<string>>(new Set());

    const moveDialogOpen = ref(false);
    const moveTarget = ref<{ itemId: string; itemName: string; currentLocationId: string } | null>(
        null
    );

    // Drag-and-drop wiring. Desktop users can pick up an ItemChip and drop it
    // onto a zone/area/section to move it. Click-to-move (MoveItemDialog) is
    // the fallback for touch/mobile and is unaffected.
    const { hoveringLocationId, onDragEnter, onDragOver, onDragLeave, onDrop } = useItemDrop();

    function reasonChips(node: LocationNode): string[] {
        return summarizeReasons(node.attention_reasons).slice(0, 4);
    }

    // ── Per-zone cross-feature actions ────────────────────────────────
    // Subtree walk: every stock item stored anywhere under this zone, used
    // to spin up a shopping list scoped to "everything that needs restocking
    // in here". Item ids are unique per subtree (a stock item lives in one
    // location), so no dedup needed.
    function subtreeLowOrOutIds(node: LocationNode): string[] {
        const lowOutNames = new Set(['Low Stock', 'Out of Stock']);
        const ids: string[] = [];
        const stack: LocationNode[] = [node];
        while (stack.length) {
            const n = stack.pop()!;
            for (const item of n.items) {
                if (item.stock_level_name && lowOutNames.has(item.stock_level_name)) {
                    ids.push(item.stock_item_id);
                }
            }
            for (const child of n.children) stack.push(child);
        }
        return ids;
    }

    const lowOrOutSubtreeIds = computed<string[]>(() =>
        zone.value ? subtreeLowOrOutIds(zone.value) : [],
    );

    const generatingList = ref(false);

    function onShowAttentionInStock(node: LocationNode) {
        void router.push({
            path: '/stock',
            query: {
                location_id: node.location_id,
                attention: 'true',
            },
        });
    }

    async function onGenerateListForZone(node: LocationNode) {
        const ids = subtreeLowOrOutIds(node);
        if (ids.length === 0) return;
        generatingList.value = true;
        try {
            const { shopping_list_id } = await shoppingListApi.createAsync({
                name: `Restock ${node.name}`,
                make_primary: !shoppingListStore.primarySummary,
            });
            let added = 0;
            let skipped = 0;
            for (const id of ids) {
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
                    `Created "Restock ${node.name}". ${added} added` +
                    (skipped > 0 ? `, ${skipped} skipped` : '') + '.',
                actions: [
                    {
                        label: 'Open',
                        color: 'white',
                        handler: () => router.push(`/shopping-lists/${shopping_list_id}`),
                    },
                ],
            });
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not generate list.',
                caption: describeApiError(err) || '',
            });
        } finally {
            generatingList.value = false;
        }
    }

    function toggleExpanded(id: string) {
        if (expanded.value.has(id)) expanded.value.delete(id);
        else expanded.value.add(id);
    }

    function onBack() {
        void router.push('/locations');
    }

    function onOpenItem(id: string) {
        void router.push(`/stock/${id}`);
    }

    function onStartMove(itemId: string, itemName: string, currentLocationId: string) {
        moveTarget.value = { itemId, itemName, currentLocationId };
        moveDialogOpen.value = true;
    }

    function childKind(parentKind: LocationKind): string {
        if (parentKind === 'zone') return 'area';
        if (parentKind === 'area') return 'section';
        return '';
    }

    async function onAddChild(parent: LocationNode) {
        const kind = childKind(parent.kind);
        if (!kind) return;
        const name = await new Promise<string | null>((resolve) => {
            $q.dialog({
                title: `New ${kind}`,
                message: `What's this ${kind} called?`,
                prompt: { model: '', type: 'text' },
                cancel: true
            })
                .onOk((data: string) => resolve(data.trim()))
                .onCancel(() => resolve(null))
                .onDismiss(() => resolve(null));
        });
        if (!name) return;
        try {
            await locationStore.createAsync({
                name,
                kind: kind as LocationKind,
                parent_id: parent.location_id
            });
            expanded.value.add(parent.location_id);
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: `Added ${kind} "${name}".`
            });
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: `Could not add ${kind}.`,
                caption: describeApiError(err) || ''
            });
        }
    }

    onMounted(async () => {
        if (locationStore.tree.length === 0) {
            await locationStore.refreshAsync();
        }
        // Auto-expand all areas under this zone for an at-a-glance view.
        if (zone.value) {
            for (const area of zone.value.children) {
                expanded.value.add(area.location_id);
            }
        }
    });
</script>

<style scoped>
    .drop-target {
        transition: outline-color 120ms ease, background-color 120ms ease;
        outline: 2px dashed transparent;
        outline-offset: -2px;
        border-radius: 6px;
    }
    .drop-target-active {
        outline-color: var(--q-primary);
        background-color: var(--brand-primary-soft);
    }
</style>
