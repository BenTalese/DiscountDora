<template>
    <div class="settings-page">
        <SettingsPageHeader
            title="Product data ingestion"
            description="Whether an outside tool may push product and offer data into Dora, and where that tool lives."
            :icon="ICONS.cloud_upload"
        />

        <q-banner v-if="!isAdmin" class="dora-bg-negative-soft text-negative" dense rounded>
            You don't have admin permissions to view this page.
        </q-banner>

        <template v-else-if="!loading">
            <SettingsSection>
                <SettingsRow inline>
                    <template #label>
                        Product data ingestion
                        <InfoTip label="Product data ingestion">
                            Accept product offer data from an external source.
                            Enable this if you have a tool or app that can scrape
                            product data from store websites and push that data
                            into Dora for analysis and additional functionality.
                        </InfoTip>
                    </template>
                    <q-toggle
                        :model-value="ingestionDraft"
                        @update:model-value="onIngestionToggle"
                    />
                </SettingsRow>
            </SettingsSection>

            <!-- Paired with the toggle above (owner 2026-09-03) — the tool that
                 pushes the data is usually the same tool you want to open when
                 you're hunting for a product, so setting up one without the
                 other is rare. Deliberately NOT gated on the `products`
                 data-presence flag the way it was on the old Features page:
                 that made the setup control appear only once the data it
                 produces already existed. -->
            <SettingsSection>
                <template #title>Product search</template>
                <template #description>
                    The URL of your product search / importer tool. When set, a
                    "Product Search" entry appears in the main menu that opens it
                    in a new tab; leave blank to hide it.
                </template>

                <SettingsRow stacked>
                    <q-input
                        v-model="productSearchUrlDraft"
                        placeholder="https://your-search.example/"
                        outlined
                        dense
                        :loading="savingProductSearchUrl"
                        :error="!!productSearchUrlError"
                        :error-message="productSearchUrlError ?? undefined"
                        @blur="onSaveProductSearchUrl"
                    />
                </SettingsRow>
            </SettingsSection>
        </template>
    </div>
</template>

<script lang="ts" setup>
    // Owner 2026-09-03 — was "Companion ingestion", a row on the dissolved
    // Features page, with the product-search URL in a separate section below
    // it. Renamed to what it actually is (any external source, not just the
    // Dora companion) and moved to Data & access, where the rest of "data
    // entering and leaving this install" lives.
    import { ICONS } from 'src/style/icons';
    import { storeToRefs } from 'pinia';
    import { useQuasar } from 'quasar';
    import AppSettingsApiService from 'src/services/api/appSettingsApiService';
    import { useAuthStore } from 'src/stores/authStore';
    import { onMounted, ref } from 'vue';
    import { toastCaption } from 'src/services/errorHandling/apiErrorHandler';
    import { useFeatureFlags } from 'src/composables/useFeatureFlags';
    import { useProductSearchUrl } from 'src/composables/useProductSearchUrl';
    import SettingsSection from 'src/components/settings/SettingsSection.vue';
    import SettingsRow from 'src/components/settings/SettingsRow.vue';
    import SettingsPageHeader from 'src/components/settings/SettingsPageHeader.vue';
    import InfoTip from 'src/components/help/InfoTip.vue';

    const $q = useQuasar();
    const { isAdmin } = storeToRefs(useAuthStore());
    const api = new AppSettingsApiService();
    const { refresh: featureFlags$refresh } = useFeatureFlags();
    // Session-wide Product Search URL cache — refreshed after a save so the
    // main-nav "Product Search" entry appears/updates without a page reload.
    const productSearch = useProductSearchUrl();

    const loading = ref(true);
    const ingestionDraft = ref(false);
    const productSearchUrlDraft = ref('');
    const savedProductSearchUrl = ref('');
    const savingProductSearchUrl = ref(false);
    const productSearchUrlError = ref<string | null>(null);

    async function onIngestionToggle(next: boolean) {
        const previous = ingestionDraft.value;
        ingestionDraft.value = next;
        try {
            const result = await api.updateAsync({ companion_ingestion_enabled: next });
            ingestionDraft.value = result.companion_ingestion_enabled;
            await featureFlags$refresh();
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: next ? 'Product data ingestion enabled.' : 'Product data ingestion disabled.',
            });
        } catch (err) {
            ingestionDraft.value = previous;
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not save the ingestion setting.',
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
        } catch (err) {
            productSearchUrlError.value = err instanceof Error ? err.message : 'Save failed.';
        } finally {
            savingProductSearchUrl.value = false;
        }
    }

    onMounted(async () => {
        if (!isAdmin.value) {
            loading.value = false;
            return;
        }
        try {
            const settings = await api.getAsync();
            ingestionDraft.value = settings.companion_ingestion_enabled;
            savedProductSearchUrl.value = settings.product_search_url;
            productSearchUrlDraft.value = settings.product_search_url;
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
