<template>
    <div class="settings-page">
        <SettingsPageHeader
            title="Features"
            description="Turn whole features on or off for this install. When a feature is off here, it's hidden for everyone — per-user preferences only apply when the install allows the feature at all."
            :icon="ICONS.tune"
        />

        <q-banner v-if="!isAdmin" class="dora-bg-negative-soft text-negative" dense rounded>
            You don't have admin permissions to view this page.
        </q-banner>

        <template v-else>
            <SettingsSection>
                <template #title>Install-wide flags</template>

                <SettingsRow
                    v-for="flag in featureFlagItems"
                    :key="flag.key"
                    :label="flag.label"
                    :help="flag.caption"
                >
                    <q-toggle
                        :model-value="flag.value"
                        @update:model-value="(next: boolean) => onFeatureFlagToggle(flag.key, next)"
                    />
                </SettingsRow>

                <SettingsRow
                    label="Scanning & QR labels"
                    help="Camera scanning of product barcodes (to jump to a linked stock item) and printing Dora's own QR labels. Navigation only — never looks up live prices. Off by default."
                >
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
                     scanning is on — it's not a reason to avoid enabling it,
                     since QR labels and manual entry are unaffected. -->
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
                        secure connection. QR label printing and typing a barcode
                        by hand are unaffected. To scan with a camera, use the
                        <strong>Dashy Dora Android app</strong> (it scans against
                        any instance) or serve Dora over HTTPS.
                    </div>
                </q-banner>

                <!-- buy-verdict oracle. Personal-data-only: no
                     external calls, no crowd data. On by default. -->
                <SettingsRow
                    label='"Should I buy?" oracle'
                    help="Show a personal buy/wait/skip verdict on stock items and shopping-list lines, using only your own price / cadence / waste history. On by default; turn off if the row-level badges feel noisy."
                >
                    <q-toggle
                        :model-value="buyVerdictDraft"
                        @update:model-value="onBuyVerdictToggle"
                    />
                </SettingsRow>
            </SettingsSection>

            <!-- Product search URL is part of the products overlay, so it
                 follows the same data-presence gate as the rest of the surface
                 — hidden entirely until the products feature is on. Setting a
                 URL is what makes the "Product Search" main-nav entry appear;
                 leave it blank and the entry stays hidden (no dead "not set up"
                 link for non-admins to land on). -->
            <SettingsSection v-if="productsEnabled">
                <template #title>Product search</template>
                <template #description>
                    Enter the URL to your product search / product data importer
                    tool. When set, a "Product Search" entry appears in the main
                    menu that opens it in a new tab; leave blank to hide it.
                </template>

                <SettingsRow v-if="!loading" stacked>
                    <q-input
                        v-model="productSearchUrlDraft"
                        placeholder="https://your-search.example/"
                        outlined
                        dense
                        :loading="savingProductSearchUrl"
                        :error="!!productSearchUrlError"
                        :error-message="productSearchUrlError ?? undefined"
                        hint="Must start with http:// or https://. Leave blank to clear."
                        @blur="onSaveProductSearchUrl"
                    />
                </SettingsRow>
            </SettingsSection>

        </template>
    </div>
</template>

<script lang="ts" setup>
    import { cameraBlockedByInsecureContext } from 'src/helpers/cameraAvailability';
    import { ICONS } from 'src/style/icons';
    import { storeToRefs } from 'pinia';
    import { useQuasar } from 'quasar';
    import AppSettingsApiService from 'src/services/api/appSettingsApiService';
    import { useAuthStore } from 'src/stores/authStore';
    import { computed, onMounted, reactive, ref } from 'vue';
    import { toastCaption } from 'src/services/errorHandling/apiErrorHandler';
    import { useFeatureFlags } from 'src/composables/useFeatureFlags';
    import { useScanningEnabled } from 'src/composables/useScanningEnabled';
    import { useBuyVerdictEnabled } from 'src/composables/useBuyVerdictEnabled';
    import { useProductSearchUrl } from 'src/composables/useProductSearchUrl';
    import SettingsSection from 'src/components/settings/SettingsSection.vue';
    import SettingsRow from 'src/components/settings/SettingsRow.vue';
    import SettingsPageHeader from 'src/components/settings/SettingsPageHeader.vue';

    // C-cross Chunk 1 — when the admin flips a flag, refresh the cached
    // `/api/health features.*` answer so every consumer composable picks
    // up the new value without a page reload. `products` gates the Product
    // Search URL row (it belongs to the products overlay).
    const { refresh: featureFlags$refresh, products: productsEnabled } = useFeatureFlags();
    // FU-580 — scanning and buy-verdict have their own dedicated module-level
    // probe composables (separate from useFeatureFlags), so their toggle
    // handlers must refresh *those* caches too or the gated UI (Stock Overview
    // scan button, QR labels, buy-verdict badges) stays stale until a reload.
    const { refreshScanning } = useScanningEnabled();
    // Same authority the scan overlay consults, so the warning here and the
    // explainer there can't drift apart (R-003). Evaluated once — the page's
    // origin can't change under it.
    const cameraInsecure = cameraBlockedByInsecureContext();
    const { refreshBuyVerdict } = useBuyVerdictEnabled();
    // Session-wide Product Search URL cache — refreshed after a save so the
    // main-nav "Product Search" entry appears/updates without a page reload.
    const productSearch = useProductSearchUrl();

    const $q = useQuasar();
    const { isAdmin } = storeToRefs(useAuthStore());
    const api = new AppSettingsApiService();

    // Scanning & QR labels — a real install-wide flag, saved on toggle.
    const scanningDraft = ref(false);

    // buy-verdict oracle install-wide toggle. Defaults on (see
    // AppSetting entity docstring); the API returns the current value.
    const buyVerdictDraft = ref(true);

    // Product search URL (Phase D / FU-186). `loading` gates the input so the
    // draft is only rendered once the saved value has arrived.
    const loading = ref(true);
    const productSearchUrlDraft = ref('');
    const savedProductSearchUrl = ref('');
    const savingProductSearchUrl = ref(false);
    const productSearchUrlError = ref<string | null>(null);

    // C-cross Chunk 1 — install-wide feature flags.
    type FeatureFlagKey =
        | 'meal_planning_enabled'
        | 'money_enabled'
        | 'companion_ingestion_enabled'
        | 'deals_email_enabled';
    const featureFlags = reactive<Record<FeatureFlagKey, boolean>>({
        meal_planning_enabled: true,
        money_enabled: false,
        companion_ingestion_enabled: false,
        deals_email_enabled: false,
    });

    const featureFlagItems = computed(() => [
        {
            key: 'meal_planning_enabled' as const,
            label: 'Meal planning',
            caption: 'Plan recipes against days of the week + headcount. Hides the meal-plans surface when off.',
            value: featureFlags.meal_planning_enabled,
        },
        {
            key: 'money_enabled' as const,
            label: 'Money & budgets',
            // Stale copy fixed in passing: the per-user money opt-in it
            // referred to was removed on 2026-08-12 — this is the only switch.
            caption: 'Per-recipe cost estimates, budget tracking on the dashboard, and shopping-list totals. This is the only switch — there is no per-user opt-in.',
            value: featureFlags.money_enabled,
        },

        {
            key: 'companion_ingestion_enabled' as const,
            label: 'Companion ingestion',
            caption: 'Accept data feeds from a self-hosted Dora companion app (retailer scraping, URL imports). Off here means the companion can\'t push anything in.',
            value: featureFlags.companion_ingestion_enabled,
        },
        {
            key: 'deals_email_enabled' as const,
            label: 'Weekly deals emailer',
            caption: 'Sends per-user weekly summary emails of low-stock items and deals. Requires DORA_EMAIL_ENABLED in the environment too.',
            value: featureFlags.deals_email_enabled,
        },
    ]);

    async function onFeatureFlagToggle(key: FeatureFlagKey, next: boolean) {
        const previous = featureFlags[key];
        // Optimistic flip for snappy feel; rollback on failure.
        featureFlags[key] = next;
        try {
            await api.updateAsync({ [key]: next });
            await featureFlags$refresh();
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: next ? 'Feature enabled.' : 'Feature disabled.',
            });
        } catch (err) {
            featureFlags[key] = previous;
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not save feature flag.',
                caption: toastCaption(err),
            });
        }
    }

    async function onScanningToggle(value: boolean) {
        try {
            const result = await api.updateAsync({ scanning_enabled: value });
            scanningDraft.value = result.scanning_enabled;
            // FU-580 — re-probe both composables that gate scanning UI so it
            // appears/disappears without a page reload.
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

    async function onBuyVerdictToggle(value: boolean) {
        try {
            const result = await api.updateAsync({ buy_verdict_enabled: value });
            buyVerdictDraft.value = result.buy_verdict_enabled;
            // FU-580 — re-probe the buy-verdict cache so the row-level badges
            // appear/disappear without a page reload.
            await refreshBuyVerdict();
            $q.notify({
                type: 'positive', position: 'bottom-right',
                message: value
                    ? '"Should I buy?" verdicts enabled.'
                    : '"Should I buy?" verdicts disabled.',
            });
        } catch (err) {
            buyVerdictDraft.value = !value;
            $q.notify({
                type: 'negative', position: 'bottom-right',
                message: 'Could not save buy-verdict setting.',
                caption: toastCaption(err),
            });
        }
    }

    async function onSaveProductSearchUrl() {
        const trimmed = productSearchUrlDraft.value.trim();
        productSearchUrlError.value = null;
        if (trimmed === savedProductSearchUrl.value) return;
        if (trimmed && !(trimmed.startsWith('http://') || trimmed.startsWith('https://'))) {
            productSearchUrlError.value = 'Must start with http:// or https://.';
            return;
        }
        savingProductSearchUrl.value = true;
        try {
            const updated = await api.updateAsync({ product_search_url: trimmed });
            savedProductSearchUrl.value = updated.product_search_url;
            productSearchUrlDraft.value = updated.product_search_url;
            await productSearch.refresh();
            $q.notify({ type: 'positive', position: 'bottom-right', message: 'Product search URL saved.' });
        } catch (e) {
            productSearchUrlError.value = e instanceof Error ? e.message : 'Save failed.';
        } finally {
            savingProductSearchUrl.value = false;
        }
    }

    type LoadedSettings = {
        scanning_enabled: boolean;
        buy_verdict_enabled?: boolean;
        meal_planning_enabled?: boolean;
        money_enabled?: boolean;
        companion_ingestion_enabled?: boolean;
        deals_email_enabled?: boolean;
        product_search_url?: string;
    };
    function applyLoaded(s: LoadedSettings) {
        scanningDraft.value = s.scanning_enabled;
        if (s.product_search_url !== undefined) {
            savedProductSearchUrl.value = s.product_search_url;
            productSearchUrlDraft.value = s.product_search_url;
        }
        if (s.buy_verdict_enabled !== undefined) {
            buyVerdictDraft.value = s.buy_verdict_enabled;
        }
        // The feature-flag fields are server-defaulted post-Chunk-1, so they
        // always come through; the optional types keep the frontend tolerant.
        if (s.meal_planning_enabled !== undefined) featureFlags.meal_planning_enabled = s.meal_planning_enabled;
        if (s.money_enabled !== undefined) featureFlags.money_enabled = s.money_enabled;
        if (s.companion_ingestion_enabled !== undefined) featureFlags.companion_ingestion_enabled = s.companion_ingestion_enabled;
        if (s.deals_email_enabled !== undefined) featureFlags.deals_email_enabled = s.deals_email_enabled;
    }

    onMounted(async () => {
        if (!isAdmin.value) {
            loading.value = false;
            return;
        }
        try {
            applyLoaded(await api.getAsync() as LoadedSettings);
        } catch {
            // Leave defaults.
        } finally {
            loading.value = false;
        }
    });
</script>

<style scoped lang="scss">
    .settings-page { display: flex; flex-direction: column; }
</style>
