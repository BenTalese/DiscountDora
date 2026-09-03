<template>
    <div class="settings-page">
        <SettingsPageHeader
            title="Stock"
            description="Install-wide stock defaults: how Dora auto-adds items when they run low, and whether this install can scan barcodes and print QR labels."
            :icon="ICONS.inventory_2"
        />

        <q-banner v-if="!isAdmin" class="dora-bg-negative-soft text-negative" dense rounded>
            You don't have admin permissions to view this page.
        </q-banner>

        <template v-else-if="!loading">
            <SettingsSection>
                <template #title>Auto-add on low</template>
                <template #description>
                    When a stock item transitions to Low or Out, Dora can
                    silently drop it onto your primary shopping list (with
                    an undoable toast). Pick which items this fires for.
                    Essential items are the ones you've marked with the
                    flag on the stock overview.
                </template>

                <SettingsRow label="Fire for">
                    <DoraSegmented
                        :model-value="modeDraft"
                        :options="MODE_OPTIONS"
                        @update:model-value="onModeChange"
                    />
                </SettingsRow>
            </SettingsSection>

            <!-- Moved here from the retired Features page 2026-09-03 (owner:
                 *"scanning & qr can go to stock section"*). It is a stock
                 affordance — the camera jumps to a stock item and the labels go
                 on shelves — so it reads better beside the other stock
                 defaults than in a pile of unrelated install switches. -->
            <SettingsSection>
                <template #title>Scanning &amp; QR labels</template>

                <SettingsRow inline>
                    <template #label>
                        Scanning enabled
                        <InfoTip label="Scanning and QR labels">
                            Point the camera at a product barcode to jump
                            straight to the stock item it's linked to, and print
                            Dora's own QR labels for shelves and containers.
                            Dora never looks up prices from a scan.
                        </InfoTip>
                    </template>
                    <q-toggle
                        :model-value="scanningDraft"
                        @update:model-value="onScanningToggle"
                    />
                </SettingsRow>

                <!-- 2026-08-15: tell the operator here, not at the viewfinder.
                     Browsers withhold the camera API on a non-secure origin, so
                     on a plain-http self-host the Scan button switches on and
                     then can't open a camera. Shown only when it's actually
                     true of the browser reading this page (so an admin on
                     localhost, or in the app, sees nothing), and only once
                     scanning is on. -->
                <q-banner
                    v-if="scanningDraft && cameraInsecure"
                    dense
                    rounded
                    class="dora-bg-warning-soft q-mt-sm"
                >
                    <template #avatar>
                        <q-icon :name="ICONS.info_outline" />
                    </template>
                    <div class="text-body2">
                        <strong>Camera scanning won't work in this browser.</strong>
                        You're reading this over a plain <code>http://</code>
                        address, and browsers only hand out camera access over a
                        secure connection. To scan with a camera, use the
                        <strong>Dashy Dora Android app</strong> (it scans against
                        any instance) or serve Dora over HTTPS.
                    </div>
                </q-banner>
            </SettingsSection>
        </template>
    </div>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import { storeToRefs } from 'pinia';
    import { useQuasar } from 'quasar';
    import AppSettingsApiService from 'src/services/api/appSettingsApiService';
    import type { AutoAddMode } from 'src/services/api/appSettingsApiService';
    import { useAuthStore } from 'src/stores/authStore';
    import { onMounted, ref } from 'vue';
    import { toastCaption } from 'src/services/errorHandling/apiErrorHandler';
    import SettingsSection from 'src/components/settings/SettingsSection.vue';
    import SettingsRow from 'src/components/settings/SettingsRow.vue';
    import SettingsPageHeader from 'src/components/settings/SettingsPageHeader.vue';
    import DoraSegmented, { type DoraSegmentedOption } from 'src/components/settings/DoraSegmented.vue';
    import InfoTip from 'src/components/help/InfoTip.vue';
    import { cameraBlockedByInsecureContext } from 'src/helpers/cameraAvailability';
    import { useFeatureFlags } from 'src/composables/useFeatureFlags';
    import { useScanningEnabled } from 'src/composables/useScanningEnabled';

    /**
     * FU-511 — install-wide auto-add mode. Replaces the retired per-item
     * `StockItem.auto_add_when_low` toggle. Single-value dial so we save
     * eagerly on change; no explicit Save button (matches the neighbouring
     * Stocktake page's pattern).
     */
    // 2026-09-03: was a raw `q-btn-toggle`, the last squared-off segmented
    // control on the settings pages. `DoraSegmented` is the same control with
    // the app's one anatomy and proper radiogroup semantics.
    const MODE_OPTIONS: DoraSegmentedOption<AutoAddMode>[] = [
        { label: 'Off', value: 'off' },
        { label: 'Essential only', value: 'essential_only' },
        { label: 'All items', value: 'all' },
    ];

    const $q = useQuasar();
    const { isAdmin } = storeToRefs(useAuthStore());
    const api = new AppSettingsApiService();

    const loading = ref(true);
    const modeDraft = ref<AutoAddMode>('essential_only');
    let savedMode: AutoAddMode = 'essential_only';

    // Scanning & QR labels — a real install-wide flag, saved on toggle.
    const scanningDraft = ref(false);
    // FU-580 — scanning has its own dedicated module-level probe composable
    // (separate from useFeatureFlags), so the toggle handler must refresh
    // *that* cache too or the gated UI (Stock Overview scan button, QR labels
    // nav entry) stays stale until a reload.
    const { refreshScanning } = useScanningEnabled();
    const { refresh: featureFlags$refresh } = useFeatureFlags();
    // Same authority the scan overlay consults, so the warning here and the
    // explainer there can't drift apart (R-003). Evaluated once — the page's
    // origin can't change under it.
    const cameraInsecure = cameraBlockedByInsecureContext();

    async function onScanningToggle(value: boolean) {
        try {
            const result = await api.updateAsync({ scanning_enabled: value });
            scanningDraft.value = result.scanning_enabled;
            await Promise.all([refreshScanning(), featureFlags$refresh()]);
            $q.notify({
                type: 'positive', position: 'bottom-right',
                message: value ? 'Scanning & QR labels enabled.' : 'Scanning & QR labels disabled.',
            });
        } catch (err) {
            scanningDraft.value = !value;
            $q.notify({
                type: 'negative', position: 'bottom-right',
                message: 'Could not save scanning setting.',
                caption: toastCaption(err),
            });
        }
    }

    async function onModeChange(next: AutoAddMode) {
        if (next === savedMode) return;
        try {
            const result = await api.updateAsync({ auto_add_mode: next });
            savedMode = result.auto_add_mode;
            modeDraft.value = savedMode;
            $q.notify({
                type: 'positive', position: 'bottom-right',
                message: 'Auto-add mode saved.',
            });
        } catch (err) {
            modeDraft.value = savedMode;
            $q.notify({
                type: 'negative', position: 'bottom-right',
                message: 'Could not save auto-add mode.',
                caption: toastCaption(err),
            });
        }
    }

    onMounted(async () => {
        if (!isAdmin.value) {
            loading.value = false;
            return;
        }
        try {
            const s = await api.getAsync();
            if (s.auto_add_mode) {
                savedMode = s.auto_add_mode;
                modeDraft.value = savedMode;
            }
            scanningDraft.value = s.scanning_enabled;
        } catch {
            // Leave defaults; nothing else on the page depends on the fetch.
        } finally {
            loading.value = false;
        }
    });
</script>

<style scoped lang="scss">
    .settings-page { display: flex; flex-direction: column; }
</style>
