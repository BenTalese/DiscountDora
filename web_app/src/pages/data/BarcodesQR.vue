<template>
    <div class="q-gutter-md">
        <q-banner class="bg-grey-2 text-grey-8 text-caption" dense rounded>
            <template #avatar>
                <q-icon name="info" size="18px" />
            </template>
            Scan barcodes with your camera, print QR sheets for pantry items,
            or manage registered barcodes. Camera access requires HTTPS in
            production.
        </q-banner>

        <q-tabs
            v-model="tab"
            dense
            align="left"
            inline-label
            no-caps
            indicator-color="primary"
            active-color="primary"
        >
            <q-tab name="scan" icon="qr_code_scanner" label="Scan" />
            <q-tab name="sheets" icon="print" label="Print sheets" />
            <q-tab name="manage" icon="list_alt" label="Manage" />
        </q-tabs>
        <q-separator />

        <!-- ── Scan tab ──────────────────────────────────────────────── -->
        <div v-if="tab === 'scan'">
            <q-card flat bordered>
                <q-card-section class="row items-center q-gutter-md">
                    <q-icon name="qr_code_scanner" size="32px" class="text-primary" />
                    <div>
                        <div class="text-h6">Scan a barcode</div>
                        <div class="text-caption text-grey">
                            Opens the camera in a fullscreen overlay. The first
                            valid decode opens the matching stock item or
                            offers to register a new barcode.
                        </div>
                    </div>
                </q-card-section>
                <q-separator />
                <q-card-section>
                    <q-btn
                        color="primary"
                        icon="photo_camera"
                        label="Open camera"
                        unelevated
                        @click="scanOpen = true"
                    />
                </q-card-section>
            </q-card>
        </div>

        <!-- ── Print sheets tab ──────────────────────────────────────── -->
        <div v-else-if="tab === 'sheets'">
            <q-card flat bordered>
                <q-card-section class="row items-center q-gutter-md">
                    <q-icon name="print" size="32px" class="text-primary" />
                    <div>
                        <div class="text-h6">Print QR sheets</div>
                        <div class="text-caption text-grey">
                            Pick items, choose a layout, open a printable
                            sheet. Save as PDF from your browser's print dialog.
                        </div>
                    </div>
                </q-card-section>
                <q-separator />
                <q-card-section>
                    <div class="row q-col-gutter-md items-end">
                        <q-input
                            v-model="sheetFilter"
                            dense
                            outlined
                            clearable
                            label="Filter items"
                            class="col-12 col-sm-6"
                        />
                        <q-select
                            v-model="sheetLayout"
                            :options="layoutOptions"
                            label="Sheet layout"
                            outlined
                            dense
                            emit-value
                            map-options
                            class="col-12 col-sm-4"
                        />
                        <div class="col-auto">
                            <q-btn
                                flat
                                dense
                                no-caps
                                label="All"
                                @click="onSelectAllVisible"
                            />
                            <q-btn
                                flat
                                dense
                                no-caps
                                label="None"
                                @click="selectedItemIds = []"
                            />
                        </div>
                    </div>
                </q-card-section>
                <q-separator />
                <q-card-section class="q-pa-none" style="max-height: 360px; overflow: auto">
                    <q-list dense>
                        <q-item
                            v-for="item in filteredStockItems"
                            :key="item.stock_item_id"
                            clickable
                            @click="toggleItem(item.stock_item_id)"
                        >
                            <q-item-section avatar>
                                <q-checkbox
                                    :model-value="selectedItemIds.includes(item.stock_item_id)"
                                    @update:model-value="toggleItem(item.stock_item_id)"
                                    @click.stop
                                />
                            </q-item-section>
                            <q-item-section>
                                <q-item-label>{{ item.name }}</q-item-label>
                                <q-item-label caption>
                                    {{ item.stock_level_name ?? '—' }}
                                    <span v-if="item.barcode">· {{ item.barcode }}</span>
                                </q-item-label>
                            </q-item-section>
                        </q-item>
                    </q-list>
                </q-card-section>
                <q-separator />
                <q-card-actions align="right">
                    <q-btn
                        flat
                        no-caps
                        label="Print all items"
                        icon="print"
                        @click="openSheet({ allItems: true })"
                    />
                    <q-btn
                        color="primary"
                        no-caps
                        icon="picture_as_pdf"
                        :label="`Open sheet (${selectedItemIds.length})`"
                        :disable="selectedItemIds.length === 0"
                        @click="openSheet({ allItems: false })"
                    />
                </q-card-actions>
            </q-card>
        </div>

        <!-- ── Manage tab ────────────────────────────────────────────── -->
        <div v-else-if="tab === 'manage'">
            <q-card flat bordered>
                <q-card-section class="row items-center q-gutter-md">
                    <q-icon name="list_alt" size="32px" class="text-primary" />
                    <div>
                        <div class="text-h6">Manage barcodes</div>
                        <div class="text-caption text-grey">
                            Inline edit / clear / print individual QRs.
                        </div>
                    </div>
                </q-card-section>
                <q-separator />
                <q-card-section>
                    <q-input
                        v-model="manageFilter"
                        dense
                        outlined
                        clearable
                        label="Filter items"
                    />
                </q-card-section>
                <q-list separator>
                    <q-item
                        v-for="item in filteredManageItems"
                        :key="item.stock_item_id"
                    >
                        <q-item-section>
                            <q-item-label>{{ item.name }}</q-item-label>
                            <q-item-label caption>
                                <span v-if="editingId === item.stock_item_id">
                                    <q-input
                                        v-model="editingValue"
                                        dense
                                        outlined
                                        autofocus
                                        @keyup.enter="commitEdit(item.stock_item_id)"
                                        @keyup.escape="cancelEdit"
                                    />
                                </span>
                                <span v-else-if="item.barcode">
                                    <code>{{ item.barcode }}</code>
                                </span>
                                <span v-else class="text-grey-5">no barcode registered</span>
                            </q-item-label>
                        </q-item-section>
                        <q-item-section side>
                            <div class="row q-gutter-xs">
                                <q-btn
                                    v-if="editingId === item.stock_item_id"
                                    flat
                                    dense
                                    no-caps
                                    color="primary"
                                    icon="check"
                                    label="Save"
                                    @click="commitEdit(item.stock_item_id)"
                                />
                                <q-btn
                                    v-if="editingId === item.stock_item_id"
                                    flat
                                    dense
                                    no-caps
                                    label="Cancel"
                                    @click="cancelEdit"
                                />
                                <q-btn
                                    v-else
                                    flat
                                    dense
                                    no-caps
                                    icon="edit"
                                    label="Edit"
                                    @click="startEdit(item)"
                                />
                                <q-btn
                                    v-if="item.barcode && editingId !== item.stock_item_id"
                                    flat
                                    dense
                                    no-caps
                                    color="negative"
                                    icon="clear"
                                    label="Clear"
                                    @click="clearBarcode(item)"
                                />
                                <q-btn
                                    flat
                                    dense
                                    no-caps
                                    icon="print"
                                    label="Print one"
                                    @click="openSingleSheet(item.stock_item_id)"
                                />
                            </div>
                        </q-item-section>
                    </q-item>
                </q-list>
            </q-card>
        </div>

        <!-- ── Shared scan overlay ──────────────────────────────────── -->
        <ScanOverlay
            v-model="scanOpen"
            @decoded="onScanDecoded"
        />

        <!-- ── Lookup-result dialog (after a successful scan) ───────── -->
        <q-dialog v-model="resultOpen">
            <q-card style="min-width: 320px; max-width: 480px">
                <q-card-section v-if="resultKind === 'stock_item'">
                    <div class="text-h6">{{ matchedItem?.name ?? 'Stock item' }}</div>
                    <div class="text-caption text-grey">
                        {{ matchedItem?.stock_level_name ?? '—' }}
                    </div>
                </q-card-section>
                <q-card-section v-else-if="resultKind === 'unknown'">
                    <div class="text-h6">Unknown barcode</div>
                    <div class="text-caption text-grey">
                        <code>{{ lastScannedValue }}</code>
                    </div>
                    <q-separator class="q-my-md" />
                    <div class="text-body2 q-mb-sm">
                        Register against a stock item:
                    </div>
                    <q-select
                        v-model="registerTarget"
                        :options="stockItemOptions"
                        outlined
                        dense
                        use-input
                        clearable
                        emit-value
                        map-options
                        label="Pick a stock item"
                        @filter="filterStockItemOptions"
                    />
                </q-card-section>
                <q-card-section v-else>
                    <div class="text-h6">No match</div>
                </q-card-section>
                <q-card-actions align="right">
                    <q-btn flat no-caps label="Close" v-close-popup />
                    <q-btn
                        v-if="resultKind === 'stock_item' && matchedItem"
                        flat
                        no-caps
                        icon="open_in_new"
                        label="Open detail"
                        color="primary"
                        @click="openDetail(matchedItem.stock_item_id)"
                    />
                    <q-btn
                        v-if="resultKind === 'unknown'"
                        color="primary"
                        no-caps
                        icon="check"
                        label="Register"
                        :disable="!registerTarget"
                        @click="registerUnknownBarcode"
                    />
                </q-card-actions>
            </q-card>
        </q-dialog>
    </div>
</template>

<script lang="ts" setup>
    import { useQuasar } from 'quasar';
    import { computed, onMounted, ref } from 'vue';
    import { useRouter } from 'vue-router';
    import ScanOverlay from 'src/components/ScanOverlay.vue';
    import { resolveBaseURL } from 'src/services/api/axiosHttpClient';
    import BarcodeApiService from 'src/services/api/barcodeApiService';
    import StockItemApiService from 'src/services/api/stockItemApiService';
    import { useStockItemStore } from 'src/stores/stockItemStore';
    import type { StockItem } from 'src/models/stockItem';

    const $q = useQuasar();
    const router = useRouter();
    const stockItemStore = useStockItemStore();
    const barcodeApi = new BarcodeApiService();
    const stockItemApi = new StockItemApiService();

    type Tab = 'scan' | 'sheets' | 'manage';
    const tab = ref<Tab>('scan');

    // ── Scan ──────────────────────────────────────────────────────────
    const scanOpen = ref(false);
    const resultOpen = ref(false);
    const resultKind = ref<'stock_item' | 'product' | 'unknown' | null>(null);
    const lastScannedValue = ref('');
    const matchedItem = ref<StockItem | null>(null);
    const registerTarget = ref<string | null>(null);

    async function onScanDecoded(value: string) {
        lastScannedValue.value = value;
        try {
            const result = await barcodeApi.lookupAsync(value);
            resultKind.value = result.kind;
            if (result.kind === 'stock_item') {
                matchedItem.value =
                    stockItemStore.stockItems.find((s) => s.stock_item_id === result.id)
                    ?? await stockItemApi.getAsync(result.id);
            } else if (result.kind === 'product') {
                matchedItem.value = result.stock_item_id
                    ? stockItemStore.stockItems.find((s) => s.stock_item_id === result.stock_item_id) ?? null
                    : null;
            } else {
                matchedItem.value = null;
                registerTarget.value = null;
            }
            resultOpen.value = true;
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Lookup failed.',
                caption: err instanceof Error ? err.message : String(err),
            });
        }
    }

    function openDetail(id: string) {
        resultOpen.value = false;
        scanOpen.value = false;
        void router.push(`/stock/${id}`);
    }

    async function registerUnknownBarcode() {
        if (!registerTarget.value || !lastScannedValue.value) return;
        try {
            await stockItemApi.registerBarcodeAsync(
                registerTarget.value, lastScannedValue.value,
            );
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: 'Barcode registered.',
            });
            resultOpen.value = false;
            await stockItemStore.getStockItemsAsync?.();
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: "Couldn't register barcode.",
                caption: err instanceof Error ? err.message : String(err),
            });
        }
    }

    // ── Print sheets ──────────────────────────────────────────────────
    const sheetFilter = ref('');
    const sheetLayout = ref('a4-21up');
    const layoutOptions = [
        { label: 'A4 21-up (3 × 7)', value: 'a4-21up' },
        { label: 'Avery 5160 (US Letter, 3 × 10)', value: 'avery-5160' },
    ];
    const selectedItemIds = ref<string[]>([]);

    const filteredStockItems = computed(() => {
        const needle = sheetFilter.value.trim().toLowerCase();
        const all = stockItemStore.stockItems ?? [];
        if (!needle) return all;
        return all.filter((s) => s.name.toLowerCase().includes(needle));
    });

    function toggleItem(id: string) {
        const idx = selectedItemIds.value.indexOf(id);
        if (idx >= 0) selectedItemIds.value.splice(idx, 1);
        else selectedItemIds.value.push(id);
    }

    function onSelectAllVisible() {
        selectedItemIds.value = filteredStockItems.value.map((s) => s.stock_item_id);
    }

    function openSheet(args: { allItems: boolean }) {
        const baseUrl = resolveBaseURL('dora');
        const ids = args.allItems ? '' : selectedItemIds.value.join(',');
        const url =
            `${baseUrl}/stock-items/qr/sheet` +
            `?layout=${encodeURIComponent(sheetLayout.value)}` +
            (ids ? `&ids=${encodeURIComponent(ids)}` : '');
        window.open(url, '_blank', 'noopener');
    }

    function openSingleSheet(id: string) {
        const baseUrl = resolveBaseURL('dora');
        const url =
            `${baseUrl}/stock-items/qr/sheet` +
            `?layout=${encodeURIComponent(sheetLayout.value)}` +
            `&ids=${encodeURIComponent(id)}`;
        window.open(url, '_blank', 'noopener');
    }

    // ── Manage ────────────────────────────────────────────────────────
    const manageFilter = ref('');
    const editingId = ref<string | null>(null);
    const editingValue = ref('');

    const filteredManageItems = computed(() => {
        const needle = manageFilter.value.trim().toLowerCase();
        const all = stockItemStore.stockItems ?? [];
        const filtered = needle
            ? all.filter((s) =>
                s.name.toLowerCase().includes(needle)
                || (s.barcode ?? '').toLowerCase().includes(needle),
            )
            : all;
        // Items with barcodes first so the user can see what's already wired up.
        return [...filtered].sort((a, b) => {
            const ab = a.barcode ? 0 : 1;
            const bb = b.barcode ? 0 : 1;
            if (ab !== bb) return ab - bb;
            return a.name.localeCompare(b.name);
        });
    });

    function startEdit(item: StockItem) {
        editingId.value = item.stock_item_id;
        editingValue.value = item.barcode ?? '';
    }
    function cancelEdit() {
        editingId.value = null;
        editingValue.value = '';
    }
    async function commitEdit(stockItemId: string) {
        const value = editingValue.value.trim();
        try {
            if (!value) {
                await stockItemApi.clearBarcodeAsync(stockItemId);
            } else {
                await stockItemApi.registerBarcodeAsync(stockItemId, value);
            }
            await stockItemStore.getStockItemsAsync?.();
            cancelEdit();
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: "Couldn't update barcode.",
                caption: err instanceof Error ? err.message : String(err),
            });
        }
    }
    async function clearBarcode(item: StockItem) {
        try {
            await stockItemApi.clearBarcodeAsync(item.stock_item_id);
            await stockItemStore.getStockItemsAsync?.();
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: "Couldn't clear barcode.",
                caption: err instanceof Error ? err.message : String(err),
            });
        }
    }

    // ── Stock-item autocomplete for register-unknown flow ────────────
    const stockItemOptionsRaw = computed(() =>
        (stockItemStore.stockItems ?? []).map((s) => ({
            label: s.name, value: s.stock_item_id,
        })),
    );
    const stockItemOptions = ref(stockItemOptionsRaw.value);
    function filterStockItemOptions(val: string, update: (cb: () => void) => void) {
        update(() => {
            const needle = val.toLowerCase();
            stockItemOptions.value = needle
                ? stockItemOptionsRaw.value.filter((o) => o.label.toLowerCase().includes(needle))
                : stockItemOptionsRaw.value;
        });
    }

    onMounted(async () => {
        // Hydrate the store on first visit so all three tabs have items.
        if ((stockItemStore.stockItems ?? []).length === 0) {
            await stockItemStore.getStockItemsAsync?.();
        }
        stockItemOptions.value = stockItemOptionsRaw.value;
    });
</script>
