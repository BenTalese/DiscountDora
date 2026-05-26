<template>
    <div class="q-pa-md">
        <!-- ── Toolbar ──────────────────────────────────────────────── -->
        <div class="row items-center q-mb-sm q-gutter-sm">
            <div class="text-h5">Stock map</div>
            <q-chip
                v-if="lastSavedLabel"
                dense
                size="sm"
                color="grey-3"
                text-color="grey-9"
            >
                {{ lastSavedLabel }}
            </q-chip>
            <q-space />

            <template v-if="!isMobile">
                <q-select
                    v-model="newNodeLocationId"
                    :options="unplacedLocationOptions"
                    label="Add location to map"
                    outlined
                    dense
                    emit-value
                    map-options
                    use-input
                    clearable
                    style="min-width: 220px"
                    @filter="filterUnplacedLocations"
                />
                <q-btn
                    color="primary"
                    no-caps
                    :icon="ICONS.add"
                    label="Add"
                    :disable="!newNodeLocationId"
                    @click="onAddNode"
                />
                <q-toggle
                    v-model="snapToGrid"
                    label="Snap to grid"
                    dense
                />
                <q-btn
                    flat
                    round
                    dense
                    :icon="ICONS.undo"
                    :disable="undoStack.length === 0"
                    @click="undo"
                >
                    <q-tooltip>Undo (Ctrl/Cmd-Z)</q-tooltip>
                </q-btn>
                <q-btn
                    flat
                    round
                    dense
                    :icon="ICONS.redo"
                    :disable="redoStack.length === 0"
                    @click="redo"
                >
                    <q-tooltip>Redo (Ctrl/Cmd-Shift-Z)</q-tooltip>
                </q-btn>
                <q-btn
                    flat
                    no-caps
                    :icon="ICONS.save"
                    label="Save"
                    :loading="saving"
                    @click="saveNow"
                />
                <q-btn
                    flat
                    no-caps
                    color="negative"
                    :icon="ICONS.restart_alt"
                    label="Reset"
                    @click="onReset"
                />
            </template>
        </div>

        <!-- ── Mobile read-only view ────────────────────────────────── -->
        <div v-if="isMobile" class="q-gutter-md">
            <q-banner class="bg-grey-2 text-grey-9" dense rounded>
                <template #avatar><q-icon :name="ICONS.phone_iphone" /></template>
                Read-only view on mobile. Open Dora on a larger screen to
                edit your pantry layout.
            </q-banner>
            <q-card v-for="node in layout.nodes" :key="node.location_id" flat bordered>
                <q-card-section class="row items-center q-gutter-sm">
                    <span class="map-swatch" :style="{ background: node.colour }" />
                    <div class="text-subtitle1">{{ node.label }}</div>
                </q-card-section>
                <q-separator />
                <q-card-section>
                    <div v-if="itemsByLocation[node.location_id]?.length" class="row q-gutter-xs">
                        <StockItemChip
                            v-for="item in itemsByLocation[node.location_id]"
                            :key="item.stock_item_id"
                            :stock-item="item"
                        />
                    </div>
                    <div v-else class="text-caption text-grey-5">
                        No items pinned here yet.
                    </div>
                </q-card-section>
            </q-card>
        </div>

        <!-- ── Desktop canvas + side panel ──────────────────────────── -->
        <div v-else class="map-layout">
            <div
                ref="hostRef"
                class="map-canvas"
                @dragover.prevent
                @drop="onDropItem"
                @contextmenu.prevent="onContextMenu"
            />
            <q-card flat bordered class="map-panel">
                <q-card-section>
                    <div class="text-subtitle2">Stock items</div>
                    <q-input
                        v-model="itemFilter"
                        dense
                        outlined
                        clearable
                        placeholder="Filter"
                        class="q-mt-xs"
                    />
                </q-card-section>
                <q-separator />
                <q-card-section class="q-pa-none" style="max-height: 540px; overflow: auto">
                    <q-list dense>
                        <q-item
                            v-for="item in filteredItems"
                            :key="item.stock_item_id"
                            draggable="true"
                            @dragstart="onItemDragStart($event, item.stock_item_id)"
                        >
                            <q-item-section>
                                <q-item-label>{{ item.name }}</q-item-label>
                                <q-item-label caption>
                                    {{ locationNameById[item.stock_location_id ?? ''] ?? 'No location' }}
                                </q-item-label>
                            </q-item-section>
                            <q-item-section side>
                                <q-icon :name="ICONS.drag_indicator" color="grey-6" />
                            </q-item-section>
                        </q-item>
                    </q-list>
                </q-card-section>
            </q-card>
        </div>

        <!-- ── Custom colour picker dialog ──────────────────────────── -->
        <q-dialog v-model="colourPickerOpen">
            <q-card style="min-width: 300px">
                <q-card-section>
                    <div class="text-h6">Pick a colour</div>
                    <div class="text-caption text-grey">
                        Use the picker or tap a swatch for a one-click apply.
                    </div>
                </q-card-section>
                <q-card-section class="q-pt-none">
                    <q-color
                        v-model="colourPickerValue"
                        no-header
                        no-footer
                        default-view="palette"
                    />
                </q-card-section>
                <q-separator />
                <q-card-section>
                    <div class="text-caption text-grey-7 q-mb-xs">Quick swatches</div>
                    <div class="row q-gutter-xs">
                        <button
                            v-for="hex in PALETTE"
                            :key="hex"
                            class="map-swatch-btn"
                            :style="{ background: hex }"
                            type="button"
                            @click="onColourPaletteSwatch(hex)"
                        />
                    </div>
                </q-card-section>
                <q-card-actions align="right">
                    <q-btn flat no-caps label="Cancel" v-close-popup />
                    <q-btn
                        color="primary"
                        no-caps
                        label="Apply"
                        @click="onColourSave"
                    />
                </q-card-actions>
            </q-card>
        </q-dialog>

        <!-- ── Per-node right-click menu ────────────────────────────── -->
        <q-menu
            v-model="contextOpen"
            :anchor="contextAnchor"
            self="top left"
            no-parent-event
        >
            <q-list dense style="min-width: 200px">
                <q-item clickable @click="onRenameNode">
                    <q-item-section avatar><q-icon :name="ICONS.edit" /></q-item-section>
                    <q-item-section>Rename label</q-item-section>
                </q-item>
                <q-item clickable @click="onChangeColour">
                    <q-item-section avatar><q-icon :name="ICONS.palette" /></q-item-section>
                    <q-item-section>Change colour…</q-item-section>
                </q-item>
                <q-item clickable @click="onToggleShape">
                    <q-item-section avatar>
                        <q-icon :name="contextNodeIsCircle ? 'square' : 'circle'" />
                    </q-item-section>
                    <q-item-section>
                        Switch to {{ contextNodeIsCircle ? 'rectangle' : 'circle' }}
                    </q-item-section>
                </q-item>
                <q-separator />
                <q-item clickable @click="onRemoveNode">
                    <q-item-section avatar><q-icon :name="ICONS.close" color="negative" /></q-item-section>
                    <q-item-section class="text-negative">Remove from map</q-item-section>
                </q-item>
            </q-list>
        </q-menu>
    </div>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import { useQuasar } from 'quasar';
    import Konva from 'konva';
    import { storeToRefs } from 'pinia';
    import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue';
    import StockItemChip from 'src/components/chips/StockItemChip.vue';
    import StockItemApiService from 'src/services/api/stockItemApiService';
    import StockMapApiService, {
        type StockMapLayout, type StockMapNode,
    } from 'src/services/api/stockMapApiService';
    import { useStockItemStore } from 'src/stores/stockItemStore';
    import { useStockLocationStore } from 'src/stores/stockLocationStore';

    const $q = useQuasar();
    const stockApi = new StockItemApiService();
    const mapApi = new StockMapApiService();

    const stockItemStore = useStockItemStore();
    const stockLocationStore = useStockLocationStore();
    const { stockItems } = storeToRefs(stockItemStore);
    const { stockLocations } = storeToRefs(stockLocationStore);

    const isMobile = computed(() => $q.screen.lt.md);

    // ── Layout state ──────────────────────────────────────────────
    const layout = reactive<StockMapLayout>({
        nodes: [],
        canvas: { w: 1200, h: 800 },
    });
    const lastSavedAt = ref<string | null>(null);
    const saving = ref(false);
    const snapToGrid = ref(true);
    const GRID = 20;

    const lastSavedLabel = computed(() => {
        if (!lastSavedAt.value) return null;
        try {
            return `Saved ${new Date(lastSavedAt.value).toLocaleTimeString()}`;
        } catch { return null; }
    });

    // ── Locations + items lookup ──────────────────────────────────
    const locationNameById = computed(() => {
        const out: Record<string, string> = {};
        for (const loc of stockLocations.value ?? []) {
            out[loc.stock_location_id] = loc.name;
        }
        return out;
    });

    const placedLocationIds = computed(() =>
        new Set(layout.nodes.map((n) => n.location_id)),
    );

    const allLocationOptions = computed(() =>
        (stockLocations.value ?? []).map((l) => ({
            label: l.name, value: l.stock_location_id,
        })),
    );
    const unplacedOptionsBase = computed(() =>
        allLocationOptions.value.filter((o) => !placedLocationIds.value.has(o.value)),
    );
    const unplacedLocationOptions = ref(unplacedOptionsBase.value);
    function filterUnplacedLocations(val: string, update: (cb: () => void) => void) {
        update(() => {
            const needle = val.toLowerCase();
            unplacedLocationOptions.value = needle
                ? unplacedOptionsBase.value.filter((o) => o.label.toLowerCase().includes(needle))
                : unplacedOptionsBase.value;
        });
    }
    watch(unplacedOptionsBase, (next) => { unplacedLocationOptions.value = next; });

    const itemsByLocation = computed(() => {
        const out: Record<string, typeof stockItems.value> = {};
        for (const item of stockItems.value ?? []) {
            const loc = item.stock_location_id ?? '';
            if (!loc) continue;
            (out[loc] ??= []).push(item);
        }
        return out;
    });

    const itemFilter = ref('');
    const filteredItems = computed(() => {
        const needle = itemFilter.value.trim().toLowerCase();
        const all = stockItems.value ?? [];
        if (!needle) return all.slice(0, 200);
        return all
            .filter((i) => i.name.toLowerCase().includes(needle))
            .slice(0, 200);
    });

    // ── Konva canvas ──────────────────────────────────────────────
    const hostRef = ref<HTMLElement | null>(null);
    let stage: Konva.Stage | null = null;
    let nodeLayer: Konva.Layer | null = null;
    let transformer: Konva.Transformer | null = null;
    // location_id → group (so we can find/update without scanning).
    const nodeGroups = new Map<string, Konva.Group>();
    const newNodeLocationId = ref<string | null>(null);

    // Right-click context menu.
    const contextOpen = ref(false);
    const contextAnchor = ref<`${number}:${number}`>('0:0' as any);
    const contextLocationIdRef = ref<string | null>(null);
    let contextLocationId: string | null = null;

    // Reactive flag for the "Switch to circle/rectangle" menu label.
    const contextNodeIsCircle = computed(() => {
        const id = contextLocationIdRef.value;
        if (!id) return false;
        return layout.nodes.find((n) => n.location_id === id)?.shape === 'circle';
    });

    const PALETTE = ['#f5c462', '#90caf9', '#a5d6a7', '#ce93d8', '#ffab91', '#80deea'];
    function defaultColour(): string {
        return PALETTE[layout.nodes.length % PALETTE.length]!;
    }

    // ── Undo / redo ─────────────────────────────────────────────────
    // Each entry is a deep-cloned snapshot of `layout.nodes` taken
    // immediately before a mutating action (drag, resize, rename,
    // colour, shape, add, remove, reset). Cmd/Ctrl-Z pops; Cmd/Ctrl-
    // Shift-Z or Ctrl-Y redoes. The stacks cap at 20 to keep RAM
    // bounded for very busy editing sessions.
    const UNDO_LIMIT = 20;
    const undoStack = ref<string[]>([]);
    const redoStack = ref<string[]>([]);

    function snapshot(): string {
        return JSON.stringify(layout.nodes);
    }

    function pushUndoSnapshot() {
        undoStack.value.push(snapshot());
        if (undoStack.value.length > UNDO_LIMIT) undoStack.value.shift();
        // Any new mutation invalidates the redo branch.
        redoStack.value = [];
    }

    function rebuildCanvasFromState() {
        // Tear down + redraw all node groups. Cheap enough for ≤ ~50
        // nodes; if a user ever blows past that, swap to a diff-based
        // patch.
        nodeGroups.forEach((g) => g.destroy());
        nodeGroups.clear();
        transformer?.nodes([]);
        for (const node of layout.nodes) drawNode(node);
        nodeLayer?.draw();
    }

    function undo() {
        const previous = undoStack.value.pop();
        if (previous === undefined) return;
        redoStack.value.push(snapshot());
        layout.nodes = JSON.parse(previous);
        rebuildCanvasFromState();
        scheduleSave();
    }

    function redo() {
        const next = redoStack.value.pop();
        if (next === undefined) return;
        undoStack.value.push(snapshot());
        layout.nodes = JSON.parse(next);
        rebuildCanvasFromState();
        scheduleSave();
    }

    function onKeydown(event: KeyboardEvent) {
        if (!stage) return;
        const target = event.target as HTMLElement | null;
        const tag = (target?.tagName || '').toLowerCase();
        // Don't steal Cmd-Z while the user is editing the rename prompt.
        if (tag === 'input' || tag === 'textarea' || (target as HTMLElement | null)?.isContentEditable) return;
        const mod = event.ctrlKey || event.metaKey;
        if (!mod) return;
        const k = event.key.toLowerCase();
        if (k === 'z' && !event.shiftKey) {
            event.preventDefault();
            undo();
        } else if ((k === 'z' && event.shiftKey) || k === 'y') {
            event.preventDefault();
            redo();
        }
    }

    function snap(value: number): number {
        if (!snapToGrid.value) return value;
        return Math.round(value / GRID) * GRID;
    }

    function buildStage() {
        if (!hostRef.value) return;
        stage = new Konva.Stage({
            container: hostRef.value,
            width: layout.canvas.w,
            height: layout.canvas.h,
        });

        const bgLayer = new Konva.Layer();
        // Grid background — light dashes every GRID pixels.
        for (let x = 0; x < layout.canvas.w; x += GRID) {
            bgLayer.add(new Konva.Line({
                points: [x, 0, x, layout.canvas.h],
                stroke: '#f0eee9',
                strokeWidth: 1,
            }));
        }
        for (let y = 0; y < layout.canvas.h; y += GRID) {
            bgLayer.add(new Konva.Line({
                points: [0, y, layout.canvas.w, y],
                stroke: '#f0eee9',
                strokeWidth: 1,
            }));
        }
        // Click outside any node clears selection.
        bgLayer.on('click', () => {
            transformer?.nodes([]);
            nodeLayer?.batchDraw();
        });
        stage.add(bgLayer);

        nodeLayer = new Konva.Layer();
        transformer = new Konva.Transformer({
            rotateEnabled: false,
            boundBoxFunc: (oldBox, newBox) => {
                if (newBox.width < 80 || newBox.height < 40) return oldBox;
                return newBox;
            },
        });
        nodeLayer.add(transformer);
        stage.add(nodeLayer);

        for (const node of layout.nodes) drawNode(node);
        nodeLayer.draw();
    }

    function buildBody(node: StockMapNode): Konva.Shape {
        // Children are named so refreshChipTexts / rename / colour-pick
        // can `findOne('.label')` etc. without depending on child order.
        if (node.shape === 'circle') {
            return new Konva.Ellipse({
                name: 'body',
                x: node.w / 2, y: node.h / 2,
                radiusX: node.w / 2,
                radiusY: node.h / 2,
                fill: node.colour,
                stroke: '#bbb',
                strokeWidth: 1,
            });
        }
        return new Konva.Rect({
            name: 'body',
            x: 0, y: 0,
            width: node.w, height: node.h,
            fill: node.colour,
            cornerRadius: 6,
            stroke: '#bbb',
            strokeWidth: 1,
        });
    }

    function applyBodySize(body: Konva.Shape, w: number, h: number) {
        if (body instanceof Konva.Ellipse) {
            body.position({ x: w / 2, y: h / 2 });
            body.radiusX(w / 2);
            body.radiusY(h / 2);
        } else {
            (body as Konva.Rect).width(w);
            (body as Konva.Rect).height(h);
        }
    }

    function drawNode(node: StockMapNode) {
        if (!nodeLayer || !stage) return;
        const group = new Konva.Group({
            x: node.x, y: node.y,
            draggable: true,
            name: node.location_id,
        });

        const body = buildBody(node);
        const label = new Konva.Text({
            name: 'label',
            x: 8, y: 6,
            text: node.label,
            fontSize: 14,
            fontStyle: 'bold',
            fill: '#222',
        });
        const chips = new Konva.Text({
            name: 'chips',
            x: 8, y: 28,
            width: node.w - 16,
            text: chipText(node.location_id),
            fontSize: 11,
            fill: '#555',
            ellipsis: true,
            wrap: 'word',
        });

        group.add(body);
        group.add(label);
        group.add(chips);

        group.on('click', () => {
            transformer?.nodes([group]);
            nodeLayer?.batchDraw();
        });

        group.on('dragstart', () => {
            pushUndoSnapshot();
        });

        group.on('dragend', () => {
            const x = snap(group.x());
            const y = snap(group.y());
            group.position({ x, y });
            const stored = layout.nodes.find((n) => n.location_id === node.location_id);
            if (stored) { stored.x = x; stored.y = y; }
            nodeLayer?.batchDraw();
            scheduleSave();
        });

        group.on('transformend', () => {
            const scaleX = group.scaleX();
            const scaleY = group.scaleY();
            const stored = layout.nodes.find((n) => n.location_id === node.location_id);
            const baseW = stored?.w ?? node.w;
            const baseH = stored?.h ?? node.h;
            // Convert the live scale into a real width/height so the
            // node's hit-region matches its visible bounds (works for
            // both Rect and Ellipse).
            const newW = snap(Math.max(80, baseW * scaleX));
            const newH = snap(Math.max(40, baseH * scaleY));
            applyBodySize(body, newW, newH);
            chips.width(newW - 16);
            group.scale({ x: 1, y: 1 });
            if (stored) {
                pushUndoSnapshot();
                stored.w = newW; stored.h = newH;
            }
            nodeLayer?.batchDraw();
            scheduleSave();
        });

        group.on('contextmenu', (event) => {
            event.evt.preventDefault();
            const pointer = stage!.getPointerPosition();
            if (!pointer || !hostRef.value) return;
            const bounds = hostRef.value.getBoundingClientRect();
            contextAnchor.value = `${Math.round(bounds.top + pointer.y)}:${Math.round(bounds.left + pointer.x)}` as any;
            contextLocationId = node.location_id;
            contextLocationIdRef.value = node.location_id;
            contextOpen.value = true;
        });

        nodeLayer.add(group);
        nodeGroups.set(node.location_id, group);
    }

    function chipText(locationId: string): string {
        const items = itemsByLocation.value[locationId] ?? [];
        if (items.length === 0) return '(empty)';
        const preview = items.slice(0, 6).map((i) => i.name).join(' · ');
        return items.length > 6
            ? `${preview} · +${items.length - 6} more`
            : preview;
    }

    function refreshChipTexts() {
        for (const [locationId, group] of nodeGroups) {
            const chips = group.findOne<Konva.Text>('.chips');
            if (chips) {
                chips.text(chipText(locationId));
            }
        }
        nodeLayer?.batchDraw();
    }

    watch(stockItems, refreshChipTexts);

    // ── Add / remove / colour / rename ────────────────────────────
    function onAddNode() {
        const locId = newNodeLocationId.value;
        if (!locId) return;
        if (placedLocationIds.value.has(locId)) return;
        pushUndoSnapshot();
        const label = locationNameById.value[locId] ?? 'Location';
        const node: StockMapNode = {
            location_id: locId,
            x: snap(40 + layout.nodes.length * 20),
            y: snap(40 + layout.nodes.length * 20),
            w: 200, h: 120,
            shape: 'rect',
            colour: defaultColour(),
            label,
        };
        layout.nodes.push(node);
        drawNode(node);
        nodeLayer?.draw();
        newNodeLocationId.value = null;
        scheduleSave();
    }

    function onRemoveNode() {
        contextOpen.value = false;
        if (!contextLocationId) return;
        pushUndoSnapshot();
        const idx = layout.nodes.findIndex((n) => n.location_id === contextLocationId);
        if (idx >= 0) layout.nodes.splice(idx, 1);
        const group = nodeGroups.get(contextLocationId);
        group?.destroy();
        nodeGroups.delete(contextLocationId);
        transformer?.nodes([]);
        nodeLayer?.batchDraw();
        scheduleSave();
        contextLocationId = null;
    }

    function onRenameNode() {
        contextOpen.value = false;
        if (!contextLocationId) return;
        const node = layout.nodes.find((n) => n.location_id === contextLocationId);
        if (!node) return;
        $q.dialog({
            title: 'Rename label',
            prompt: { model: node.label, type: 'text' },
            ok: { label: 'Save', noCaps: true, color: 'primary' },
            cancel: { noCaps: true },
        }).onOk((value: string) => {
            const trimmed = (value ?? '').trim();
            if (!trimmed) return;
            pushUndoSnapshot();
            node.label = trimmed;
            const group = nodeGroups.get(node.location_id);
            const label = group?.findOne<Konva.Text>('.label');
            label?.text(trimmed);
            nodeLayer?.batchDraw();
            scheduleSave();
        });
    }

    // Colour picker: open the q-color modal anchored to the context
    // location. Falls back to the next palette swatch if the user
    // dismisses without picking.
    const colourPickerOpen = ref(false);
    const colourPickerValue = ref('#f5c462');
    let colourPickerTarget: string | null = null;

    function onChangeColour() {
        contextOpen.value = false;
        const locId = contextLocationId;
        if (!locId) return;
        const node = layout.nodes.find((n) => n.location_id === locId);
        if (!node) return;
        colourPickerTarget = locId;
        colourPickerValue.value = node.colour;
        colourPickerOpen.value = true;
    }

    function applyColour(hex: string) {
        const locId = colourPickerTarget;
        if (!locId) return;
        const node = layout.nodes.find((n) => n.location_id === locId);
        if (!node) return;
        pushUndoSnapshot();
        node.colour = hex;
        const body = nodeGroups.get(locId)?.findOne<Konva.Shape>('.body');
        body?.fill(hex);
        nodeLayer?.batchDraw();
        scheduleSave();
    }

    function onColourSave() {
        applyColour(colourPickerValue.value);
        colourPickerOpen.value = false;
        colourPickerTarget = null;
    }

    function onColourPaletteSwatch(hex: string) {
        // Convenience: the in-dialog swatches apply immediately + close.
        colourPickerValue.value = hex;
        applyColour(hex);
        colourPickerOpen.value = false;
        colourPickerTarget = null;
    }

    function onToggleShape() {
        contextOpen.value = false;
        const locId = contextLocationId;
        if (!locId) return;
        const node = layout.nodes.find((n) => n.location_id === locId);
        if (!node) return;
        pushUndoSnapshot();
        node.shape = node.shape === 'circle' ? 'rect' : 'circle';
        // Tear the old body out and rebuild — switching between
        // Konva.Rect and Konva.Ellipse needs a fresh shape, mutating
        // the existing one isn't supported.
        const group = nodeGroups.get(locId);
        if (group) {
            const oldBody = group.findOne<Konva.Shape>('.body');
            oldBody?.destroy();
            const newBody = buildBody(node);
            // Keep the body underneath the label + chips so text stays
            // readable; Konva renders children in add order.
            newBody.zIndex(0);
            group.add(newBody);
            newBody.moveToBottom();
        }
        nodeLayer?.batchDraw();
        scheduleSave();
    }

    function onContextMenu(event: MouseEvent) {
        // Catches right-clicks on the bare canvas (outside any rect).
        // Konva's per-shape handler fires first when over a rect, so
        // this only runs when the user wanted the background.
        event.preventDefault();
    }

    // ── Drag stock item from side panel onto a rectangle ─────────
    function onItemDragStart(event: DragEvent, stockItemId: string) {
        event.dataTransfer?.setData('text/dora-stock-item-id', stockItemId);
        event.dataTransfer!.effectAllowed = 'move';
    }

    async function onDropItem(event: DragEvent) {
        const itemId = event.dataTransfer?.getData('text/dora-stock-item-id');
        if (!itemId || !stage || !hostRef.value) return;
        const bounds = hostRef.value.getBoundingClientRect();
        const localX = event.clientX - bounds.left;
        const localY = event.clientY - bounds.top;
        // Hit-test: find the topmost node whose bounding box covers
        // (localX, localY).
        const hit = [...layout.nodes].reverse().find((n) =>
            localX >= n.x && localX <= n.x + n.w
            && localY >= n.y && localY <= n.y + n.h,
        );
        if (!hit) return;
        try {
            await stockApi.moveAsync(itemId, hit.location_id);
            $q.notify({
                type: 'positive', position: 'bottom-right',
                message: `Moved to ${hit.label}.`,
            });
            await stockItemStore.getStockItemsAsync?.();
            refreshChipTexts();
        } catch (err) {
            $q.notify({
                type: 'negative', position: 'bottom-right',
                message: "Couldn't move that item.",
                caption: err instanceof Error ? err.message : String(err),
            });
        }
    }

    // ── Save (debounced + manual) ─────────────────────────────────
    let saveTimer: ReturnType<typeof setTimeout> | null = null;
    function scheduleSave() {
        if (saveTimer) clearTimeout(saveTimer);
        saveTimer = setTimeout(() => { void saveNow(); }, 2000);
    }

    async function saveNow() {
        if (saveTimer) { clearTimeout(saveTimer); saveTimer = null; }
        saving.value = true;
        try {
            const result = await mapApi.saveAsync({
                nodes: layout.nodes.map((n) => ({ ...n })),
                canvas: { ...layout.canvas },
            });
            lastSavedAt.value = result.updated_at;
        } catch (err) {
            $q.notify({
                type: 'negative', position: 'bottom-right',
                message: "Couldn't save the map.",
                caption: err instanceof Error ? err.message : String(err),
            });
        } finally {
            saving.value = false;
        }
    }

    async function onReset() {
        const ok = await new Promise<boolean>((resolve) => {
            $q.dialog({
                title: 'Reset the map?',
                message: 'Every placed location will be removed. Your stock items + locations are unchanged.',
                ok: { label: 'Reset', color: 'negative', noCaps: true },
                cancel: { noCaps: true },
                persistent: true,
            }).onOk(() => resolve(true)).onCancel(() => resolve(false)).onDismiss(() => resolve(false));
        });
        if (!ok) return;
        pushUndoSnapshot();
        layout.nodes.splice(0);
        nodeGroups.forEach((g) => g.destroy());
        nodeGroups.clear();
        transformer?.nodes([]);
        nodeLayer?.batchDraw();
        await saveNow();
    }

    // ── Lifecycle ─────────────────────────────────────────────────
    onMounted(async () => {
        await Promise.all([
            stockItemStore.getStockItemsAsync?.(),
            stockLocationStore.getStockLocationsAsync?.(),
        ]);
        try {
            const result = await mapApi.getAsync();
            layout.nodes = result.layout?.nodes ?? [];
            layout.canvas = result.layout?.canvas ?? { w: 1200, h: 800 };
            lastSavedAt.value = result.updated_at;
        } catch {
            // First-load failure leaves the empty default; user can
            // still place nodes — the next save creates the row.
        }
        if (!isMobile.value) {
            await nextTick();
            buildStage();
            if (typeof window !== 'undefined') {
                window.addEventListener('keydown', onKeydown);
            }
        }
    });

    onBeforeUnmount(() => {
        if (saveTimer) clearTimeout(saveTimer);
        if (typeof window !== 'undefined') {
            window.removeEventListener('keydown', onKeydown);
        }
        stage?.destroy();
        nodeGroups.clear();
    });
</script>

<style scoped>
    .map-layout {
        display: grid;
        grid-template-columns: 1fr 280px;
        gap: 12px;
        align-items: flex-start;
    }
    .map-canvas {
        background: var(--surface-page);
        border: 1px solid var(--border-default);
        border-radius: 8px;
        min-height: 600px;
        overflow: hidden;
    }
    .map-panel { position: sticky; top: 12px; }
    .map-swatch {
        display: inline-block;
        width: 14px; height: 14px;
        border-radius: 3px;
    }
    .map-swatch-btn {
        width: 28px; height: 28px;
        border-radius: 6px;
        border: 1px solid var(--border-strong);
        cursor: pointer;
        padding: 0;
    }
    .map-swatch-btn:hover { transform: scale(1.05); }
</style>
