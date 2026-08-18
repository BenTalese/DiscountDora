<template>
    <div class="settings-page">
        <SettingsPageHeader
            title="QR labels"
            description="Print Dora's own QR labels for your stock items — pick items, choose a sheet layout, and open a printable sheet. Save as PDF from your browser's print dialog. These are Dora's labels (a scannable QR that opens the item's page); they are not the product's real EAN/UPC barcode."
            :icon="ICONS.qr_code"
        />

        <!-- Off-state: install-wide `scanning_enabled` gate. The nav link is
             also hidden when the flag is off, so this banner mostly appears
             for admins reaching the page by URL / a stale bookmark. -->
        <q-banner
            v-if="scanningLoaded && !scanningEnabled"
            class="dora-bg-sunken dora-text-secondary q-mb-md"
            rounded
        >
            <template #avatar>
                <q-icon :name="ICONS.info" />
            </template>
            Scanning &amp; QR labels are turned off. An admin can enable them in
            <router-link to="/settings/admin/system/features">Settings → System → Features</router-link>.
        </q-banner>

        <q-card v-if="scanningEnabled" flat bordered>
            <q-card-section>
                <div class="row q-col-gutter-md items-end">
                    <SearchInput
                        v-model="sheetFilter"
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
                        <BaseButton
                            variant="ghost"
                            dense
                            label="All"
                            @click="onSelectAllVisible"
                        />
                        <BaseButton
                            variant="ghost"
                            dense
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
                <BaseButton
                    variant="ghost"
                    label="Print all items"
                    :icon="ICONS.print"
                    @click="openSheet({ allItems: true })"
                />
                <BaseButton
                    variant="primary"
                    :icon="ICONS.picture_as_pdf"
                    :label="`Open sheet (${selectedItemIds.length})`"
                    :disable="selectedItemIds.length === 0"
                    @click="openSheet({ allItems: false })"
                />
            </q-card-actions>
        </q-card>
    </div>
</template>

<script lang="ts" setup>
    import { Notify } from 'quasar';
    import SearchInput from 'src/components/SearchInput.vue';
    import BaseButton from 'src/components/BaseButton.vue';
    import SettingsPageHeader from 'src/components/settings/SettingsPageHeader.vue';
    import { ICONS } from 'src/style/icons';
    import { computed, onMounted, ref } from 'vue';
    import { describeQrFailure, openQrSheetAsync } from 'src/composables/useQrLabels';
    import { useScanningEnabled } from 'src/composables/useScanningEnabled';
    import { useStockItemStore } from 'src/stores/stockItemStore';

    const { scanningEnabled, scanningLoaded } = useScanningEnabled();
    const stockItemStore = useStockItemStore();

    // this page owns the Print QR labels surface only. The Scan
    // tab that used to live alongside it on /data/barcodes was removed:
    // every page that needs scanning already has its own Scan button
    // (Stock Overview toolbar, Add-to-list flows, etc.), and per-item
    // barcode registration lives on the stock item detail page.
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

    // Sync entry so the click's gesture still reaches `window.open` (R-046),
    // and the rejection is reported rather than voided — a blocked pop-up used
    // to look identical to the button not being wired up.
    function openSheet(args: { allItems: boolean }) {
        openQrSheetAsync({
            layout: sheetLayout.value,
            ...(args.allItems ? {} : { ids: selectedItemIds.value }),
        }).catch((err: unknown) => {
            Notify.create({
                type: 'negative',
                position: 'bottom-right',
                message: describeQrFailure(err),
            });
        });
    }

    onMounted(async () => {
        await stockItemStore.ensureLoadedAsync();
    });
</script>
