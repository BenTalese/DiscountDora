<template>
    <div class="column q-gutter-md">
        <!-- C-cross Chunk 1 — install-wide feature flags. Each toggle is
             wired to AppSetting via PATCH /api/app-settings; the server-side
             `_feature_flags()` exposes them through `/api/health features.*`
             for consumer composables. -->
        <q-card flat bordered>
            <q-card-section>
                <div class="text-subtitle1 text-weight-medium">
                    <q-icon :name="ICONS.tune" size="20px" class="q-mr-xs" />
                    Features
                </div>
                <div class="text-caption dora-text-muted">
                    Turn whole features on or off for this install. When a feature is off
                    here, it's hidden for everyone — per-user preferences only apply when
                    the install allows the feature at all.
                </div>
            </q-card-section>
            <q-separator />

            <q-card-section v-if="!isAdmin">
                <q-banner class="dora-bg-negative-soft text-negative" dense rounded>
                    You don't have admin permissions to view this page.
                </q-banner>
            </q-card-section>

            <template v-else>
                <q-list separator>
                    <q-item v-for="flag in featureFlagItems" :key="flag.key">
                        <q-item-section>
                            <q-item-label>{{ flag.label }}</q-item-label>
                            <q-item-label caption>{{ flag.caption }}</q-item-label>
                        </q-item-section>
                        <q-item-section side>
                            <q-toggle
                                :model-value="flag.value"
                                :disable="savingFeatures.has(flag.key)"
                                @update:model-value="(next: boolean) => onFeatureFlagToggle(flag.key, next)"
                            />
                        </q-item-section>
                    </q-item>

                    <!-- Scanning & QR labels — an install capability flag,
                         saved on toggle. Lives with the feature flags (was
                         under the AI assistant block pre-rebuild). -->
                    <q-item>
                        <q-item-section>
                            <q-item-label>Scanning &amp; QR labels</q-item-label>
                            <q-item-label caption>
                                Camera scanning of real-world product barcodes (to jump to
                                a linked stock item) and printing Dora's own QR labels for
                                items and shelves. Navigation only — scanning never looks up
                                live prices. Off by default.
                            </q-item-label>
                        </q-item-section>
                        <q-item-section side>
                            <q-toggle
                                :model-value="scanningDraft"
                                :disable="savingScanning"
                                @update:model-value="onScanningToggle"
                            />
                        </q-item-section>
                    </q-item>
                </q-list>
            </template>
        </q-card>

        <!-- Product search URL (Phase D / FU-186) — folded onto Features per
             the rebuild (§2.4): a single input controlling a single behaviour. -->
        <q-card v-if="isAdmin" flat bordered>
            <q-card-section>
                <div class="text-subtitle1 text-weight-medium">
                    <q-icon :name="ICONS.search" size="20px" class="q-mr-xs" />
                    Product search
                </div>
                <div class="text-caption dora-text-muted">
                    A URL the "Product Search" nav entry opens in a new tab
                    when product data is present. Point this at whatever
                    search surface you run yourself; Dora doesn't know or
                    care what it is. Leave blank to show the entry as
                    "not set up".
                </div>
            </q-card-section>
            <q-separator />
            <q-card-section v-if="!loading" class="row q-col-gutter-md items-start">
                <q-input
                    v-model="productSearchUrlDraft"
                    label="Product search URL"
                    placeholder="https://your-search.example/"
                    outlined
                    dense
                    class="col-12"
                    :disable="savingProductSearchUrl"
                    :loading="savingProductSearchUrl"
                    :error="!!productSearchUrlError"
                    :error-message="productSearchUrlError ?? undefined"
                    hint="Must start with http:// or https://. Leave blank to clear."
                    @blur="onSaveProductSearchUrl"
                />
            </q-card-section>
        </q-card>
    </div>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import { storeToRefs } from 'pinia';
    import { useQuasar } from 'quasar';
    import AppSettingsApiService from 'src/services/api/appSettingsApiService';
    import { useAuthStore } from 'src/stores/authStore';
    import { computed, onMounted, reactive, ref } from 'vue';
    import { describeApiError } from 'src/services/errorHandling/apiErrorHandler';
    import { useFeatureFlags } from 'src/composables/useFeatureFlags';

    // C-cross Chunk 1 — when the admin flips a flag, refresh the cached
    // `/api/health features.*` answer so every consumer composable picks
    // up the new value without a page reload.
    const { refresh: featureFlags$refresh } = useFeatureFlags();

    const $q = useQuasar();
    const { isAdmin } = storeToRefs(useAuthStore());
    const api = new AppSettingsApiService();

    const loading = ref(true);

    // Scanning & QR labels — a real install-wide flag, saved on toggle.
    const scanningDraft = ref(false);
    const savingScanning = ref(false);

    // C-cross Chunk 1 — install-wide feature flags.
    type FeatureFlagKey =
        | 'meal_planning_enabled'
        | 'money_enabled'
        | 'nutrition_enabled'
        | 'companion_ingestion_enabled'
        | 'deals_email_enabled';
    const featureFlags = reactive<Record<FeatureFlagKey, boolean>>({
        meal_planning_enabled: true,
        money_enabled: false,
        nutrition_enabled: false,
        companion_ingestion_enabled: false,
        deals_email_enabled: false,
    });
    const savingFeatures = ref<Set<FeatureFlagKey>>(new Set());

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
            caption: 'Per-recipe cost estimates, budget tracking on the dashboard, and shopping-list totals. Per-user opt-in still applies.',
            value: featureFlags.money_enabled,
        },
        {
            key: 'nutrition_enabled' as const,
            label: 'Nutrition',
            caption: 'Per-recipe kcal field + filters. Per-user opt-in still applies.',
            value: featureFlags.nutrition_enabled,
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
        savingFeatures.value.add(key);
        // Reassign to trigger reactivity on the Set.
        savingFeatures.value = new Set(savingFeatures.value);
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
                caption: describeApiError(err) || '',
            });
        } finally {
            savingFeatures.value.delete(key);
            savingFeatures.value = new Set(savingFeatures.value);
        }
    }

    async function onScanningToggle(value: boolean) {
        savingScanning.value = true;
        try {
            const result = await api.updateAsync({ scanning_enabled: value });
            scanningDraft.value = result.scanning_enabled;
            $q.notify({
                type: 'positive', position: 'bottom-right',
                message: value ? 'Scanning & QR labels enabled.' : 'Scanning & QR labels disabled.',
            });
        } catch (err) {
            scanningDraft.value = !value;
            $q.notify({
                type: 'negative', position: 'bottom-right',
                message: 'Could not save scanning setting.',
                caption: describeApiError(err) || '',
            });
        } finally {
            savingScanning.value = false;
        }
    }

    // Product search URL (Phase D / FU-186) ───────────────────────────────
    const productSearchUrlDraft = ref('');
    const savedProductSearchUrl = ref('');
    const savingProductSearchUrl = ref(false);
    const productSearchUrlError = ref<string | null>(null);

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
            const updated = await api.updateAsync({
                product_search_url: trimmed,
            });
            savedProductSearchUrl.value = updated.product_search_url;
            productSearchUrlDraft.value = updated.product_search_url;
            $q.notify({ type: 'positive', position: 'bottom-right', message: 'Product search URL saved.' });
        } catch (e) {
            productSearchUrlError.value = e instanceof Error ? e.message : 'Save failed.';
        } finally {
            savingProductSearchUrl.value = false;
        }
    }

    type LoadedSettings = {
        scanning_enabled: boolean;
        meal_planning_enabled?: boolean;
        money_enabled?: boolean;
        nutrition_enabled?: boolean;
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
        // The feature-flag fields are server-defaulted post-Chunk-1, so they
        // always come through; the optional types keep the frontend tolerant.
        if (s.meal_planning_enabled !== undefined) featureFlags.meal_planning_enabled = s.meal_planning_enabled;
        if (s.money_enabled !== undefined) featureFlags.money_enabled = s.money_enabled;
        if (s.nutrition_enabled !== undefined) featureFlags.nutrition_enabled = s.nutrition_enabled;
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
