<template>
    <q-card flat bordered>
        <q-card-section class="row items-center">
            <div>
                <div class="text-h6">
                    <q-icon :name="ICONS.shield" size="20px" class="q-mr-xs" />
                    System
                </div>
                <div class="text-caption dora-text-muted">
                    Install-wide settings. Changes here apply to every account.
                </div>
            </div>
        </q-card-section>

        <q-separator />

        <q-card-section v-if="!isAdmin">
            <q-banner class="dora-bg-negative-soft text-negative" dense rounded>
                You don't have admin permissions to view this page.
            </q-banner>
        </q-card-section>

        <template v-else>
            <!-- Household timezone (C-2.K) ─────────────────────────────── -->
            <q-card-section>
                <div class="text-subtitle1 text-weight-medium">
                    <q-icon :name="ICONS.event" size="20px" class="q-mr-xs" />
                    Timezone
                </div>
                <div class="text-caption dora-text-muted">
                    The household's timezone. Dates like "today" on the meal
                    planner are worked out here, so they stay correct no matter
                    where the server runs.
                </div>
            </q-card-section>
            <q-card-section v-if="!loading" class="row q-col-gutter-md items-center">
                <q-select
                    :model-value="timezoneDraft"
                    :options="timezoneOptions"
                    label="Household timezone"
                    outlined
                    dense
                    use-input
                    input-debounce="0"
                    options-dense
                    class="col-12 col-sm-8"
                    :disable="savingTimezone"
                    :loading="savingTimezone"
                    @filter="onTimezoneFilter"
                    @update:model-value="onSaveTimezone"
                />
                <div class="col-12 col-sm-4">
                    <q-btn
                        color="secondary"
                        no-caps
                        outline
                        label="Use this device's timezone"
                        :disable="savingTimezone"
                        @click="onDetectTimezone"
                    />
                </div>
            </q-card-section>
            <q-separator />

            <!-- Alert thresholds (C-9.2) ───────────────────────────────── -->
            <q-card-section>
                <div class="text-subtitle1 text-weight-medium">
                    <q-icon :name="ICONS.notifications" size="20px" class="q-mr-xs" />
                    Alert thresholds
                </div>
                <div class="text-caption dora-text-muted">
                    Household-wide tuning for inventory alerts. These shape the
                    alerts list and the location heatmap for everyone; each
                    account's own on/off and priority preferences layer on top.
                </div>
            </q-card-section>
            <q-card-section v-if="!loading" class="row q-col-gutter-md items-start">
                <q-input
                    v-model.number="expiringSoonWindowDraft"
                    type="number"
                    label="Expiring-soon window (days)"
                    outlined
                    dense
                    class="col-12 col-sm-6"
                    :min="1"
                    :max="365"
                    :disable="savingThresholds"
                    :loading="savingThresholds"
                    hint="Items within this many days of their expiry date show as 'expiring soon'."
                    @blur="() => onSaveThreshold('expiring_soon_window_days', expiringSoonWindowDraft)"
                />
                <q-input
                    v-model.number="stocktakeDefaultDraft"
                    type="number"
                    label="Default stocktake reminder (days)"
                    outlined
                    dense
                    class="col-12 col-sm-6"
                    :min="0"
                    :max="3650"
                    :disable="savingThresholds"
                    :loading="savingThresholds"
                    hint="Pre-filled check-in cadence for new stock items (0 = no reminder)."
                    @blur="() => onSaveThreshold('default_days_until_stocktake_alert', stocktakeDefaultDraft)"
                />
            </q-card-section>
            <q-separator />

            <!-- Product search URL (Phase D / FU-186) ──────────────────── -->
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
            <q-separator />

            <!-- AI assistant ─────────────────────────────────────────── -->
            <q-card-section>
                <div class="text-subtitle1 text-weight-medium">
                    <q-icon :name="ICONS.smart_toy" size="20px" class="q-mr-xs" />
                    AI assistant
                </div>
                <div class="text-caption dora-text-muted">
                    Optional. Connect Dora's chat to a language model you run
                    yourself. Off by default — when off, the assistant uses its
                    built-in rule-based replies.
                </div>
            </q-card-section>

            <q-card-section v-if="loading" class="row justify-center">
                <q-spinner-dots size="28px" color="primary" />
            </q-card-section>

            <template v-else>
                <q-card-section>
                    <q-toggle
                        v-model="enabledDraft"
                        label="Enable the AI assistant"
                        :disable="saving"
                    />
                    <div class="text-caption dora-text-muted q-ml-sm">
                        {{ enabledDraft
                            ? 'Enter a base URL and model below, then Save to apply.'
                            : 'Toggle on to configure. Nothing is applied until you Save.' }}
                    </div>
                </q-card-section>

                <q-card-section class="row q-col-gutter-md items-start">
                    <q-input
                        v-model="baseUrlDraft"
                        label="LLM base URL"
                        placeholder="http://localhost:11434"
                        outlined
                        dense
                        class="col-12 col-sm-8"
                        :disable="saving || !enabledDraft"
                        hint="Your LLM server's address (Ollama's default is shown). Models load when you leave this field."
                        @blur="onBaseUrlBlur"
                    />
                    <div class="col-12 col-sm-4">
                        <q-btn
                            color="secondary"
                            no-caps
                            outline
                            :icon="ICONS.wifi_tethering"
                            label="Test connection"
                            :loading="probing"
                            :disable="saving || !enabledDraft || !baseUrlDraft.trim()"
                            @click="() => onTest(true)"
                        />
                    </div>
                </q-card-section>

                <q-card-section v-if="probeResult" class="q-pt-none">
                    <q-banner
                        :class="probeResult.reachable ? 'dora-bg-positive-soft text-positive' : 'dora-bg-negative-soft text-negative'"
                        dense
                        rounded
                    >
                        <template #avatar>
                            <q-icon :name="probeResult.reachable ? 'check_circle' : 'error'" />
                        </template>
                        <span v-if="probeResult.reachable">
                            Connected — found {{ allModels.length }}
                            model{{ allModels.length === 1 ? '' : 's' }}.
                            <span v-if="allModels.length === 0">
                                Pull one on your server (e.g.
                                <code>ollama pull qwen2.5:7b</code>) then test again.
                            </span>
                        </span>
                        <span v-else>
                            Couldn't reach that URL.
                            <span v-if="probeResult.error" class="text-caption">
                                ({{ probeResult.error }})
                            </span>
                        </span>
                    </q-banner>
                </q-card-section>

                <q-card-section class="row q-col-gutter-md">
                    <q-select
                        v-model="modelDraft"
                        label="Model"
                        outlined
                        dense
                        class="col-12 col-sm-7"
                        :options="modelOptions"
                        use-input
                        fill-input
                        hide-selected
                        input-debounce="0"
                        new-value-mode="add-unique"
                        :disable="saving || !enabledDraft"
                        :hint="allModels.length
                            ? 'Pick a detected model, or type one to pull later.'
                            : 'Type a model name, or test the connection to list installed models. Must support tool-calling.'"
                        @filter="onFilterModels"
                        @new-value="onNewModel"
                    >
                        <template #no-option>
                            <q-item>
                                <q-item-section class="dora-text-muted">
                                    No detected models — type a name (e.g. qwen2.5:7b).
                                </q-item-section>
                            </q-item>
                        </template>
                    </q-select>
                </q-card-section>

                <q-card-section>
                    <q-btn
                        color="primary"
                        no-caps
                        :icon="ICONS.save"
                        label="Save AI settings"
                        :loading="saving"
                        :disable="!canSave"
                        @click="onSave"
                    />
                    <div
                        v-if="!unchanged && !canSave"
                        class="text-caption dora-text-muted q-mt-xs"
                    >
                        Enable, then fill in both the base URL and the model
                        before saving.
                    </div>
                </q-card-section>

                <q-card-section>
                    <q-banner class="dora-bg-info-soft text-info" dense rounded>
                        <template #avatar>
                            <q-icon :name="ICONS.info" size="20px" />
                        </template>
                        <div class="text-weight-medium q-mb-xs">Setting up your own LLM</div>
                        <ol class="q-my-none q-pl-md">
                            <li>
                                Install <a href="https://ollama.com" target="_blank" rel="noopener">Ollama</a>
                                on a machine on your network (a desktop or home server).
                            </li>
                            <li>
                                Pull a tool-capable model:
                                <code>ollama pull qwen2.5:7b</code>
                                (larger models answer better but need more RAM).
                            </li>
                            <li>
                                Make sure it's serving (<code>ollama serve</code>; on Linux it
                                usually runs as a service already).
                            </li>
                            <li>
                                Enter the base URL (e.g. <code>http://localhost:11434</code>)
                                and model name above, enable, and save.
                            </li>
                        </ol>
                        <div class="q-mt-sm">
                            More detail is on the
                            <router-link to="/help">Help page</router-link>.
                        </div>
                    </q-banner>
                </q-card-section>

                <q-separator />

                <q-card-section>
                    <q-toggle
                        v-model="scanningDraft"
                        label="Enable scanning & QR labels"
                        :disable="savingScanning"
                        @update:model-value="onScanningToggle"
                    />
                    <div class="text-caption dora-text-muted q-ml-sm">
                        Camera scanning of real-world product barcodes (to jump to
                        a linked stock item) and printing Dora's own QR labels for
                        items and shelves. Navigation only — scanning never looks up
                        live prices. Off by default.
                    </div>
                </q-card-section>
            </template>

            <q-separator />

            <!-- C-cross Chunk 1 — install-wide feature flags. Each toggle
                 is wired to AppSetting via PATCH /api/app-settings; the
                 server-side `_feature_flags()` exposes them through
                 `/api/health features.*` for consumer composables. -->
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
            </q-list>
        </template>
    </q-card>
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

    // AI assistant config (install-wide). Drafts are saved explicitly.
    const enabledDraft = ref(false);
    const baseUrlDraft = ref('');
    const modelDraft = ref('');
    const saved = ref({ enabled: false, baseUrl: '', model: '' });
    const loading = ref(true);
    const saving = ref(false);

    // Connection test + model discovery.
    const probing = ref(false);
    const probeResult = ref<{ reachable: boolean; error: string | null } | null>(null);
    const allModels = ref<string[]>([]); // every model the endpoint reported
    const modelOptions = ref<string[]>([]); // filtered view shown in the dropdown
    // The last URL we probed, so leaving the field doesn't re-probe an
    // unchanged value on every blur. The explicit Test button bypasses this.
    const lastProbedUrl = ref('');

    async function onTest(force = false) {
        const url = baseUrlDraft.value.trim();
        if (!url) return;
        if (!force && url === lastProbedUrl.value) return;
        probing.value = true;
        probeResult.value = null;
        lastProbedUrl.value = url;
        try {
            const result = await api.probeAsync(url);
            allModels.value = result.models;
            modelOptions.value = result.models;
            probeResult.value = { reachable: result.reachable, error: result.error };
        } catch (err) {
            allModels.value = [];
            modelOptions.value = [];
            probeResult.value = { reachable: false, error: String(err) };
        } finally {
            probing.value = false;
        }
    }

    function onBaseUrlBlur() {
        void onTest(false);
    }

    // q-select combobox plumbing: filter the detected list as the admin types,
    // and accept a typed value that isn't in the list (a model to pull later).
    function onFilterModels(val: string, update: (fn: () => void) => void) {
        update(() => {
            const needle = val.toLowerCase();
            modelOptions.value = needle
                ? allModels.value.filter((m) => m.toLowerCase().includes(needle))
                : allModels.value;
        });
    }

    function onNewModel(
        val: string,
        done: (item?: string, mode?: 'add' | 'add-unique' | 'toggle') => void
    ) {
        const trimmed = val.trim();
        if (trimmed) done(trimmed, 'add-unique');
    }

    const unchanged = computed(
        () =>
            enabledDraft.value === saved.value.enabled &&
            baseUrlDraft.value === saved.value.baseUrl &&
            modelDraft.value === saved.value.model
    );

    // Save is gated on: something changed AND (if enabling, valid inputs).
    // Disabling is always valid — turning AI off doesn't need a URL/model.
    const canSave = computed(() => {
        if (unchanged.value) return false;
        if (!enabledDraft.value) return true;
        return baseUrlDraft.value.trim().length > 0 && modelDraft.value.trim().length > 0;
    });

    // Placeholder state for the not-yet-wired toggles.
    // (the old `allowRegistrations` / `maintenanceMode` / `emailerEnabled`
    //  placeholder refs were removed when the Features panel replaced their
    //  list. Re-add if/when those flags graduate to real install settings.)

    // Scanning & QR labels — a real install-wide flag, saved on toggle (no
    // extra config to validate, unlike the LLM block).
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

    type LoadedSettings = {
        llm_enabled: boolean; llm_base_url: string; llm_model: string;
        scanning_enabled: boolean;
        meal_planning_enabled?: boolean;
        money_enabled?: boolean;
        nutrition_enabled?: boolean;
        companion_ingestion_enabled?: boolean;
        deals_email_enabled?: boolean;
        timezone?: string;
        expiring_soon_window_days?: number;
        default_days_until_stocktake_alert?: number;
        product_search_url?: string;
    };
    function applyLoaded(s: LoadedSettings) {
        enabledDraft.value = s.llm_enabled;
        baseUrlDraft.value = s.llm_base_url;
        modelDraft.value = s.llm_model;
        scanningDraft.value = s.scanning_enabled;
        if (s.timezone) timezoneDraft.value = s.timezone;
        if (s.expiring_soon_window_days !== undefined) {
            savedThresholds.expiring_soon_window_days = s.expiring_soon_window_days;
            expiringSoonWindowDraft.value = s.expiring_soon_window_days;
        }
        if (s.default_days_until_stocktake_alert !== undefined) {
            savedThresholds.default_days_until_stocktake_alert = s.default_days_until_stocktake_alert;
            stocktakeDefaultDraft.value = s.default_days_until_stocktake_alert;
        }
        if (s.product_search_url !== undefined) {
            savedProductSearchUrl.value = s.product_search_url;
            productSearchUrlDraft.value = s.product_search_url;
        }
        saved.value = { enabled: s.llm_enabled, baseUrl: s.llm_base_url, model: s.llm_model };
        // The new feature-flag fields might be absent on older /api/app-settings
        // responses (server-side default in the dataclass means they always
        // come through post-Chunk-1, but the optional types here keep the
        // frontend tolerant during a partial-deploy window).
        if (s.meal_planning_enabled !== undefined) featureFlags.meal_planning_enabled = s.meal_planning_enabled;
        if (s.money_enabled !== undefined) featureFlags.money_enabled = s.money_enabled;
        if (s.nutrition_enabled !== undefined) featureFlags.nutrition_enabled = s.nutrition_enabled;
        if (s.companion_ingestion_enabled !== undefined) featureFlags.companion_ingestion_enabled = s.companion_ingestion_enabled;
        if (s.deals_email_enabled !== undefined) featureFlags.deals_email_enabled = s.deals_email_enabled;
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

    // ── Household timezone (C-2.K) ───────────────────────────────────────
    const timezoneDraft = ref<string>('UTC');
    const savingTimezone = ref(false);
    // `Intl.supportedValuesOf` ships in modern engines but isn't in every TS
    // lib target — feature-detect with a precise type rather than `any`.
    type IntlWithSupported = typeof Intl & { supportedValuesOf?: (key: string) => string[] };
    const _supportedValuesOf = (Intl as IntlWithSupported).supportedValuesOf;
    const allTimezones: string[] = _supportedValuesOf ? _supportedValuesOf('timeZone') : ['UTC'];
    const timezoneOptions = ref<string[]>(allTimezones);

    function onTimezoneFilter(val: string, update: (cb: () => void) => void) {
        update(() => {
            const needle = val.toLowerCase();
            timezoneOptions.value = needle
                ? allTimezones.filter((t) => t.toLowerCase().includes(needle))
                : allTimezones;
        });
    }

    function onDetectTimezone() {
        const detected = Intl.DateTimeFormat().resolvedOptions().timeZone;
        if (detected) void onSaveTimezone(detected);
    }

    async function onSaveTimezone(value: string) {
        if (!value || value === timezoneDraft.value) return;
        savingTimezone.value = true;
        try {
            const result = await api.updateAsync({ timezone: value });
            timezoneDraft.value = result.timezone;
            $q.notify({
                type: 'positive', position: 'bottom-right',
                message: `Household timezone set to ${result.timezone}.`,
            });
        } catch (err) {
            $q.notify({
                type: 'negative', position: 'bottom-right',
                message: 'Could not save the timezone.',
                caption: describeApiError(err) || '',
            });
        } finally {
            savingTimezone.value = false;
        }
    }

    // ── Alert thresholds (C-9.2) ─────────────────────────────────────────
    // Household-wide. Saved on blur (one PATCH per committed edit), mirroring
    // the timezone field; a no-op blur (unchanged value) is skipped.
    const expiringSoonWindowDraft = ref<number>(7);
    const stocktakeDefaultDraft = ref<number>(0);
    const savedThresholds = reactive({
        expiring_soon_window_days: 7,
        default_days_until_stocktake_alert: 0,
    });
    const savingThresholds = ref(false);

    type ThresholdKey = 'expiring_soon_window_days' | 'default_days_until_stocktake_alert';

    function resetThresholdDrafts() {
        expiringSoonWindowDraft.value = savedThresholds.expiring_soon_window_days;
        stocktakeDefaultDraft.value = savedThresholds.default_days_until_stocktake_alert;
    }

    async function onSaveThreshold(key: ThresholdKey, value: number) {
        // q-input can hand back '' / NaN mid-edit; ignore those and reset the
        // field, and skip a no-op save (blur fires even with no change).
        if (typeof value !== 'number' || Number.isNaN(value)) {
            resetThresholdDrafts();
            return;
        }
        if (value === savedThresholds[key]) return;
        savingThresholds.value = true;
        try {
            const result = await api.updateAsync({ [key]: value });
            savedThresholds.expiring_soon_window_days = result.expiring_soon_window_days;
            savedThresholds.default_days_until_stocktake_alert = result.default_days_until_stocktake_alert;
            resetThresholdDrafts();
            $q.notify({
                type: 'positive', position: 'bottom-right',
                message: 'Alert thresholds saved.',
            });
        } catch (err) {
            resetThresholdDrafts();
            $q.notify({
                type: 'negative', position: 'bottom-right',
                message: 'Could not save alert thresholds.',
                caption: describeApiError(err) || '',
            });
        } finally {
            savingThresholds.value = false;
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

    async function onSave() {
        saving.value = true;
        try {
            const result = await api.updateAsync({
                llm_enabled: enabledDraft.value,
                llm_base_url: baseUrlDraft.value.trim(),
                llm_model: modelDraft.value.trim()
            });
            applyLoaded(result);
            $q.notify({ type: 'positive', position: 'bottom-right', message: 'AI settings saved.' });
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not save AI settings.',
                caption: describeApiError(err) || ''
            });
        } finally {
            saving.value = false;
        }
    }

    onMounted(async () => {
        if (!isAdmin.value) {
            loading.value = false;
            return;
        }
        try {
            applyLoaded(await api.getAsync());
        } catch {
            // Leave defaults; the banner explains setup.
        } finally {
            loading.value = false;
        }
    });
</script>
