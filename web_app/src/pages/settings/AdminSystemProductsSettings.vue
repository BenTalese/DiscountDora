<template>
    <div class="settings-page">
        <SettingsPageHeader
            title="Products"
            description="Install-wide settings for the products overlay — the Product Search nav entry and the URL it opens."
            :icon="ICONS.shopping_bag"
        />

        <q-banner v-if="!isAdmin" class="dora-bg-negative-soft text-negative" dense rounded>
            You don't have admin permissions to view this page.
        </q-banner>

        <template v-else>
            <SettingsSection>
                <template #title>Product search</template>

                <SettingsRow v-if="!loading" stacked>
                    <template #label>Search URL</template>
                    <template #help>
                        Enter the URL to your product search/product data importer tool. Useful for quick navigation.
                    </template>
                    <q-input
                        v-model="productSearchUrlDraft"
                        placeholder="https://your-search.example/"
                        outlined
                        dense
                        :disable="savingProductSearchUrl"
                        :loading="savingProductSearchUrl"
                        :error="!!productSearchUrlError"
                        :error-message="productSearchUrlError ?? undefined"
                        hint="Must start with http:// or https://. Leave blank to clear."
                        @blur="onSaveProductSearchUrl"
                    />
                </SettingsRow>

                <SettingsRow
                    label="Hide menu button"
                    help="Hide the Product Search entry from the main navigation entirely."
                >
                    <q-toggle
                        :model-value="productSearchHiddenDraft"
                        :disable="savingProductSearchHidden"
                        @update:model-value="onProductSearchHiddenToggle"
                    />
                </SettingsRow>
            </SettingsSection>
        </template>
    </div>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import { storeToRefs } from 'pinia';
    import { useQuasar } from 'quasar';
    import AppSettingsApiService from 'src/services/api/appSettingsApiService';
    import { useAuthStore } from 'src/stores/authStore';
    import { onMounted, ref } from 'vue';
    import { toastCaption } from 'src/services/errorHandling/apiErrorHandler';
    import { useProductSearchUrl } from 'src/composables/useProductSearchUrl';
    import SettingsSection from 'src/components/settings/SettingsSection.vue';
    import SettingsRow from 'src/components/settings/SettingsRow.vue';
    import SettingsPageHeader from 'src/components/settings/SettingsPageHeader.vue';

    const $q = useQuasar();
    const { isAdmin } = storeToRefs(useAuthStore());
    const api = new AppSettingsApiService();
    const productSearch = useProductSearchUrl();

    const loading = ref(true);

    const productSearchUrlDraft = ref('');
    const savedProductSearchUrl = ref('');
    const savingProductSearchUrl = ref(false);
    const productSearchUrlError = ref<string | null>(null);

    const productSearchHiddenDraft = ref(false);
    const savingProductSearchHidden = ref(false);

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

    async function onProductSearchHiddenToggle(value: boolean) {
        savingProductSearchHidden.value = true;
        try {
            const updated = await api.updateAsync({ product_search_hidden: value });
            productSearchHiddenDraft.value = updated.product_search_hidden;
            await productSearch.refresh();
            $q.notify({
                type: 'positive', position: 'bottom-right',
                message: value ? 'Menu button hidden.' : 'Menu button visible.',
            });
        } catch (err) {
            productSearchHiddenDraft.value = !value;
            $q.notify({
                type: 'negative', position: 'bottom-right',
                message: 'Could not save setting.',
                caption: toastCaption(err),
            });
        } finally {
            savingProductSearchHidden.value = false;
        }
    }

    onMounted(async () => {
        if (!isAdmin.value) {
            loading.value = false;
            return;
        }
        try {
            const s = await api.getAsync();
            savedProductSearchUrl.value = s.product_search_url;
            productSearchUrlDraft.value = s.product_search_url;
            productSearchHiddenDraft.value = s.product_search_hidden;
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
