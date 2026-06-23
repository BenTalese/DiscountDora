<template>
    <div class="q-gutter-md">
        <!-- Off state — the whole surface is gated by the install-wide flag. -->
        <q-banner
            v-if="scanningLoaded && !scanningEnabled"
            class="dora-bg-sunken dora-text-secondary"
            rounded
        >
            <template #avatar>
                <q-icon :name="ICONS.info" />
            </template>
            Scanning &amp; QR labels are turned off. An admin can enable them in
            <router-link to="/settings/admin/system/features">Settings → System → Features</router-link>.
        </q-banner>

        <template v-else-if="scanningEnabled">
            <q-banner class="dora-bg-sunken dora-text-secondary text-caption" dense rounded>
                <template #avatar>
                    <q-icon :name="ICONS.info" size="18px" />
                </template>
                Scan a real-world product barcode to jump to its linked stock item,
                or print Dora's own QR labels for your items. Scanning is a
                navigation aid only — it never looks up live prices. Camera access
                requires HTTPS in production.
            </q-banner>

            <DoraTabs
                v-model="tab"
                :tabs="[
                    { name: 'scan', label: 'Scan', icon: ICONS.qr_code_scanner },
                    { name: 'sheets', label: 'Print labels', icon: ICONS.print },
                ]"
            />

            <!-- ── Scan tab ──────────────────────────────────────────────── -->
            <div v-if="tab === 'scan'">
                <q-card flat bordered>
                    <q-card-section class="row items-center q-gutter-md">
                        <q-icon :name="ICONS.qr_code_scanner" size="32px" class="text-primary" />
                        <div>
                            <div class="text-h6">Scan a barcode</div>
                            <div class="text-caption dora-text-muted">
                                Opens the camera in a fullscreen overlay. The first
                                valid decode opens the matching stock item (via its
                                Dora QR, or via a product barcode you've linked).
                            </div>
                        </div>
                    </q-card-section>
                    <q-separator />
                    <q-card-section>
                        <q-btn
                            color="primary"
                            :icon="ICONS.photo_camera"
                            label="Open camera"
                            unelevated
                            @click="scanOpen = true"
                        />
                    </q-card-section>
                </q-card>
            </div>

            <!-- ── Print labels tab ──────────────────────────────────────── -->
            <div v-else-if="tab === 'sheets'">
                <q-card flat bordered>
                    <q-card-section class="row items-center q-gutter-md">
                        <q-icon :name="ICONS.print" size="32px" class="text-primary" />
                        <div>
                            <div class="text-h6">Print QR labels</div>
                            <div class="text-caption dora-text-muted">
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
                            :icon="ICONS.print"
                            @click="openSheet({ allItems: true })"
                        />
                        <q-btn
                            color="primary"
                            no-caps
                            :icon="ICONS.picture_as_pdf"
                            :label="`Open sheet (${selectedItemIds.length})`"
                            :disable="selectedItemIds.length === 0"
                            @click="openSheet({ allItems: false })"
                        />
                    </q-card-actions>
                </q-card>
            </div>

            <!-- ── Shared scan overlay ──────────────────────────────────── -->
            <ScanOverlay
                v-model="scanOpen"
                @decoded="onScanDecoded"
            />

            <!-- ── Lookup-result dialog (after a successful scan) ───────── -->
            <BaseDialog v-model="resultOpen" card-style="min-width: 320px; max-width: 480px">
                <q-card-section v-if="matchedItem">
                    <div class="text-h6">{{ matchedItem.name }}</div>
                    <div class="text-caption dora-text-muted">
                        {{ matchedItem.stock_level_name ?? '—' }}
                    </div>
                </q-card-section>
                <q-card-section v-else-if="resultKind === 'product'">
                    <div class="text-h6">Product not linked</div>
                    <div class="text-caption dora-text-muted">
                        This barcode is linked to a product, but that product isn't
                        attached to any stock item yet.
                    </div>
                </q-card-section>
                <q-card-section v-else>
                    <div class="text-h6">No match</div>
                    <div class="text-caption dora-text-muted">
                        <code>{{ lastScannedValue }}</code> isn't linked to a product
                        yet.
                    </div>
                </q-card-section>
                <template #actions>
                    <BaseButton variant="ghost" label="Close" v-close-popup />
                    <q-btn
                        v-if="matchedItem"
                        flat
                        no-caps
                        :icon="ICONS.open_in_new"
                        label="Open detail"
                        color="primary"
                        @click="openDetail(matchedItem.stock_item_id)"
                    />
                </template>
            </BaseDialog>
        </template>
    </div>
</template>

<script lang="ts" setup>
    import BaseButton from 'src/components/BaseButton.vue';
    import BaseDialog from 'src/components/BaseDialog.vue';
    import DoraTabs from 'src/components/DoraTabs.vue';
    import { ICONS } from 'src/style/icons';
    import { useQuasar } from 'quasar';
    import { computed, onMounted, ref } from 'vue';
    import { useRouter } from 'vue-router';
    import ScanOverlay from 'src/components/ScanOverlay.vue';
    import { resolveBaseURL } from 'src/services/api/axiosHttpClient';
    import BarcodeApiService from 'src/services/api/barcodeApiService';
    import StockItemApiService from 'src/services/api/stockItemApiService';
    import { useScanningEnabled } from 'src/composables/useScanningEnabled';
    import { useStockItemStore } from 'src/stores/stockItemStore';
    import type { StockItem } from 'src/models/stockItem';

    const $q = useQuasar();
    const router = useRouter();
    const { scanningEnabled, scanningLoaded } = useScanningEnabled();
    const stockItemStore = useStockItemStore();
    const barcodeApi = new BarcodeApiService();
    const stockItemApi = new StockItemApiService();

    type Tab = 'scan' | 'sheets';
    const tab = ref<Tab>('scan');

    // ── Scan ──────────────────────────────────────────────────────────
    const scanOpen = ref(false);
    const resultOpen = ref(false);
    const resultKind = ref<'stock_item' | 'product' | 'unknown' | null>(null);
    const lastScannedValue = ref('');
    const matchedItem = ref<StockItem | null>(null);

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

    // ── Print labels ──────────────────────────────────────────────────
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
        const baseUrl = resolveBaseURL();
        const ids = args.allItems ? '' : selectedItemIds.value.join(',');
        const url =
            `${baseUrl}/stock-items/qr/sheet` +
            `?layout=${encodeURIComponent(sheetLayout.value)}` +
            (ids ? `&ids=${encodeURIComponent(ids)}` : '');
        window.open(url, '_blank', 'noopener');
    }

    onMounted(async () => {
        // Hydrate the store on first visit so the print tab has items.
        await stockItemStore.ensureLoadedAsync();
    });
</script>
