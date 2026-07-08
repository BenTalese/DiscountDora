<template>
    <div v-if="!currentUser">
        <q-banner class="dora-bg-sunken" dense>Not signed in.</q-banner>
    </div>

    <div v-else class="settings-page">
        <SettingsPageHeader
            title="Assistant (AI mode)"
            description="Connect Dora's chat to a language model. Pick a provider, enter the bits it needs, and turn on AI mode. When off, Dora uses its built-in rule-based replies."
            :icon="ICONS.smart_toy"
        />

        <!-- install-wide master flag layered with the per-user toggle.
             When the install master is off, the user's toggle is forced
             visually off + disabled with an explanatory note. R-029
             carve-out: this is the assistant's own per-user settings
             screen (the one legitimate place the disabled state may
             render); every other surface hides the assistant entry point
             when the master is off. -->
        <q-banner
            v-if="!installEnabled"
            class="dora-bg-sunken"
            dense
            rounded
        >
            <template #avatar>
                <q-icon :name="ICONS.info" size="20px" class="dora-text-muted" />
            </template>
            AI mode is disabled install-wide. An admin can turn the master
            switch back on at System → AI assistant.
        </q-banner>

        <SettingsSection>
            <template #title>Show the Dora helper</template>
            <template #description>
                The floating Dora bubble sits in the corner of every page and
                answers questions, points you around, and takes quick actions.
                Turn it off to hide it completely for your account — you can
                switch it back on here any time.
            </template>

            <SettingsRow label="Show Dora on every page">
                <q-toggle
                    :model-value="currentUser.show_assistant !== false"
                    :disable="saving"
                    @update:model-value="onShowAssistantChange"
                />
            </SettingsRow>
        </SettingsSection>

        <hr class="settings-divider" />

        <SettingsSection>
            <template #title>Enable AI mode</template>
            <template #description>
                Basic mode (the default, no setup needed) answers questions
                about your pantry, meals, and lists — and can add items to your
                list when you type things like "add milk". AI mode routes
                <em>tool-able requests</em> through your configured provider for
                richer, multi-step help (disambiguating items, expiry rescue,
                price stats). Most people are fine on Basic mode; AI mode is the
                power-up if you run a language model.
            </template>

            <SettingsRow label="Use AI mode for this account">
                <q-toggle
                    :model-value="currentUser.llm_enabled"
                    :disable="!installEnabled || saving || !canEnable"
                    @update:model-value="onEnabledChange"
                />
            </SettingsRow>
            <div
                v-if="installEnabled && !canEnable && !currentUser.llm_enabled"
                class="settings-page__note dora-text-muted"
            >
                {{ enableBlockedReason }}
            </div>
        </SettingsSection>

        <hr class="settings-divider" />

        <SettingsSection>
            <template #title>Provider</template>
            <template #description>
                <strong>Ollama</strong> runs locally on a machine you
                control (no key needed). <strong>OpenAI</strong>,
                <strong>Anthropic</strong>, and <strong>Google Gemini</strong>
                are paid hosted APIs — bring your own key.
            </template>

            <SettingsRow label="Provider">
                <DoraSegmented
                    :model-value="providerDraft ?? 'ollama'"
                    :options="providerOptions"
                    @update:model-value="onProviderChange"
                />
            </SettingsRow>
        </SettingsSection>

        <template v-if="providerDraft === 'ollama'">
            <hr class="settings-divider" />
            <SettingsSection>
                <template #title>Ollama server</template>
                <template #description>
                    The host address of your Ollama install. The Dora
                    backend reaches this URL (not your browser); on a
                    household NAS deployment you may need port-forwarding
                    so the backend can see the LLM.
                </template>

                <SettingsRow label="Base URL">
                    <q-input
                        v-model="baseUrlDraft"
                        outlined
                        dense
                        placeholder="http://localhost:11434"
                        style="max-width: 360px"
                        :disable="saving"
                        @blur="onBaseUrlBlur"
                        @keydown.enter.prevent="onBaseUrlBlur"
                    />
                </SettingsRow>
                <SettingsRow label="Model">
                    <q-input
                        v-model="modelDraft"
                        outlined
                        dense
                        placeholder="qwen2.5:7b"
                        style="max-width: 360px"
                        :disable="saving"
                        @blur="onModelBlur"
                        @keydown.enter.prevent="onModelBlur"
                    />
                </SettingsRow>

                <!-- Test connection. Probes the saved config
                     (or the in-flight draft values if the user hasn't
                     blurred yet) via /api/assistant/probe. Rate-limited
                     server-side at 10/min and audit-logged. -->
                <SettingsRow label="">
                    <div class="row q-gutter-sm items-center">
                        <BaseButton
                            variant="secondary"
                            :icon="ICONS.wifi_tethering"
                            label="Test connection"
                            :loading="probing"
                            :disable="saving || !baseUrlDraft.trim() || !modelDraft.trim()"
                            @click="onTest"
                        />
                        <span
                            v-if="probeResult"
                            class="text-caption"
                            :class="probeResult.available ? 'text-positive' : 'text-negative'"
                        >
                            <q-icon
                                :name="probeResult.available ? ICONS.check_circle : ICONS.warning"
                                size="14px"
                                class="q-mr-xs"
                            />
                            <template v-if="probeResult.available">
                                Connected.
                                <span v-if="probeResult.models?.length">
                                    {{ probeResult.models.length }}
                                    model{{ probeResult.models.length === 1 ? '' : 's' }}
                                    detected.
                                </span>
                            </template>
                            <template v-else>{{ probeResult.reason ?? "Couldn't reach the provider." }}</template>
                        </span>
                    </div>
                </SettingsRow>
            </SettingsSection>
        </template>

        <template v-else>
            <hr class="settings-divider" />
            <SettingsSection>
                <template #title>API key</template>
                <template #description>
                    Bring your own
                    {{ providerDisplayName(providerDraft) }} API key.
                    Stored encrypted at rest; never echoed back to the
                    browser.
                </template>

                <SettingsRow label="API key">
                    <q-input
                        v-model="apiKeyDraft"
                        outlined
                        dense
                        type="password"
                        autocomplete="off"
                        :placeholder="currentUser.has_llm_api_key ? '••••••••• (saved)' : 'Paste your key here'"
                        style="max-width: 360px"
                        :disable="saving"
                        @blur="onApiKeyBlur"
                        @keydown.enter.prevent="onApiKeyBlur"
                    />
                </SettingsRow>
                <SettingsRow v-if="currentUser.has_llm_api_key" label="">
                    <BaseButton
                        variant="danger-ghost"
                        :icon="ICONS.delete"
                        label="Remove saved key"
                        :disable="saving"
                        @click="onClearApiKey"
                    />
                </SettingsRow>

                <SettingsRow label="Model">
                    <q-input
                        v-model="modelDraft"
                        outlined
                        dense
                        :placeholder="modelPlaceholder"
                        style="max-width: 360px"
                        :disable="saving"
                        @blur="onModelBlur"
                        @keydown.enter.prevent="onModelBlur"
                    />
                </SettingsRow>
                <SettingsRow v-if="providerDraft !== 'gemini'" label="Base URL (optional)">
                    <q-input
                        v-model="baseUrlDraft"
                        outlined
                        dense
                        :placeholder="defaultBaseUrl"
                        style="max-width: 360px"
                        :disable="saving"
                        @blur="onBaseUrlBlur"
                        @keydown.enter.prevent="onBaseUrlBlur"
                    />
                </SettingsRow>

                <!-- Test connection for paid providers. Uses
                     the saved encrypted key (server falls back to it
                     when the body's api_key is null); if the user just
                     typed a new key into the masked field, that takes
                     precedence so they can test pre-save. -->
                <SettingsRow label="">
                    <div class="row q-gutter-sm items-center">
                        <BaseButton
                            variant="secondary"
                            :icon="ICONS.wifi_tethering"
                            label="Test connection"
                            :loading="probing"
                            :disable="saving || !modelDraft.trim() || !canTestPaidProvider"
                            @click="onTest"
                        />
                        <span
                            v-if="probeResult"
                            class="text-caption"
                            :class="probeResult.available ? 'text-positive' : 'text-negative'"
                        >
                            <q-icon
                                :name="probeResult.available ? ICONS.check_circle : ICONS.warning"
                                size="14px"
                                class="q-mr-xs"
                            />
                            <template v-if="probeResult.available">Connected.</template>
                            <template v-else>{{ probeResult.reason ?? "Couldn't reach the provider." }}</template>
                        </span>
                    </div>
                </SettingsRow>
            </SettingsSection>
        </template>
    </div>
</template>

<script lang="ts" setup>
    import BaseButton from 'src/components/BaseButton.vue';
    import { ICONS } from 'src/style/icons';
    import { storeToRefs } from 'pinia';
    import { useQuasar } from 'quasar';
    import type { LlmProvider } from 'src/models/auth';
    import AppSettingsApiService from 'src/services/api/appSettingsApiService';
    import AssistantApiService from 'src/services/api/assistantApiService';
    import { useAuthStore } from 'src/stores/authStore';
    import { computed, onMounted, ref, watch } from 'vue';
    import { toastCaption } from 'src/services/errorHandling/apiErrorHandler';
    import SettingsSection from 'src/components/settings/SettingsSection.vue';
    import SettingsRow from 'src/components/settings/SettingsRow.vue';
    import SettingsPageHeader from 'src/components/settings/SettingsPageHeader.vue';
    import DoraSegmented, { type DoraSegmentedOption } from 'src/components/settings/DoraSegmented.vue';

    const $q = useQuasar();
    const authStore = useAuthStore();
    const { currentUser } = storeToRefs(authStore);
    const appSettingsApi = new AppSettingsApiService();
    const assistantApi = new AssistantApiService();

    const installEnabled = ref(true);
    const saving = ref(false);
    // Test connection. `probing` gates the button; `probeResult`
    // mirrors the last probe outcome inline next to the button so the
    // user sees the verdict without a toast for the (frequent) "try a
    // few URLs in a row" workflow. Cleared on any field edit so a stale
    // green tick can't mislead.
    const probing = ref(false);
    const probeResult = ref<{ available: boolean; reason: string | null; models: string[] | null } | null>(null);

    // Local drafts mirror the per-row controls; each saves on blur (or on
    // change for the provider segmented). Pattern matches MoneySettings.vue
    // (R-020 carve-out: save-on-blur surfaces don't need the unsaved-changes
    // guard — every blur fires the API).
    const providerDraft = ref<LlmProvider | null>(currentUser.value?.llm_provider ?? null);
    const baseUrlDraft = ref<string>(currentUser.value?.llm_base_url ?? '');
    const modelDraft = ref<string>(currentUser.value?.llm_model ?? '');
    const apiKeyDraft = ref<string>('');

    watch(currentUser, (u) => {
        if (!u) return;
        providerDraft.value = u.llm_provider;
        baseUrlDraft.value = u.llm_base_url ?? '';
        modelDraft.value = u.llm_model ?? '';
        // Don't reset the api-key draft — the saved blob is opaque to the
        // SPA; a watch firing on every PATCH would wipe an in-flight type.
    }, { deep: true });

    onMounted(async () => {
        try {
            const s = await appSettingsApi.getAsync();
            installEnabled.value = s.master_llm_enabled;
        } catch {
            // The master flag isn't strictly needed — failing to read it
            // just means we can't surface the "disabled install-wide"
            // hint. Don't block the rest of the page.
        }
    });

    const providerOptions: DoraSegmentedOption<LlmProvider>[] = [
        { label: 'Ollama (local)', value: 'ollama' },
        { label: 'OpenAI', value: 'openai' },
        { label: 'Anthropic', value: 'anthropic' },
        { label: 'Gemini', value: 'gemini' },
    ];

    function providerDisplayName(p: LlmProvider | null): string {
        switch (p) {
            case 'openai': return 'OpenAI';
            case 'anthropic': return 'Anthropic';
            case 'gemini': return 'Google Gemini';
            default: return 'Ollama';
        }
    }

    const defaultBaseUrl = computed(() => {
        switch (providerDraft.value) {
            case 'openai': return 'https://api.openai.com/v1';
            case 'anthropic': return 'https://api.anthropic.com';
            default: return '';
        }
    });

    const modelPlaceholder = computed(() => {
        switch (providerDraft.value) {
            case 'openai': return 'gpt-4o-mini';
            case 'anthropic': return 'claude-3-5-sonnet-20241022';
            case 'gemini': return 'gemini-2.0-flash';
            default: return 'qwen2.5:7b';
        }
    });

    // "Can enable AI mode right now?" — checks the per-provider
    // prerequisites match what's saved server-side, so the toggle
    // doesn't go on with a half-finished config.
    const canEnable = computed(() => {
        const u = currentUser.value;
        if (!u) return false;
        if (u.llm_enabled) return true;
        if (!u.llm_provider) return false;
        if (!u.llm_model) return false;
        if (u.llm_provider === 'ollama') {
            return !!u.llm_base_url;
        }
        return u.has_llm_api_key;
    });

    const enableBlockedReason = computed(() => {
        const u = currentUser.value;
        if (!u) return '';
        if (!u.llm_provider) return 'Pick a provider first.';
        if (u.llm_provider === 'ollama') {
            if (!u.llm_base_url) return 'Save a base URL first.';
            if (!u.llm_model) return 'Save a model name first.';
            return '';
        }
        if (!u.has_llm_api_key) return 'Save an API key first.';
        if (!u.llm_model) return 'Save a model name first.';
        return '';
    });

    function notifySuccess(message: string) {
        $q.notify({ type: 'positive', position: 'bottom-right', message });
    }
    function notifyError(message: string, err?: unknown) {
        $q.notify({
            type: 'negative',
            position: 'bottom-right',
            message,
            caption: toastCaption(err),
        });
    }
    async function update<T>(label: string, run: () => Promise<T>): Promise<T | null> {
        saving.value = true;
        try {
            const result = await run();
            notifySuccess(label);
            return result;
        } catch (err) {
            notifyError(`Could not save ${label.toLowerCase()}.`, err);
            return null;
        } finally {
            saving.value = false;
        }
    }

    async function onEnabledChange(value: boolean) {
        await update(
            value ? 'AI mode turned on.' : 'AI mode turned off.',
            () => authStore.updateMeAsync({ llm_enabled: value }),
        );
    }

    async function onShowAssistantChange(value: boolean) {
        await update(
            value ? 'Dora helper shown.' : 'Dora helper hidden.',
            () => authStore.updateMeAsync({ show_assistant: value }),
        );
    }

    async function onProviderChange(value: LlmProvider) {
        // Drafts that don't apply to the new provider are kept (the user
        // might be flipping between providers to compare); the server
        // just doesn't care about fields the chosen provider ignores.
        const previous = providerDraft.value;
        providerDraft.value = value;
        const result = await update('Provider updated.', () =>
            authStore.updateMeAsync({ llm_provider: value }),
        );
        if (result === null) providerDraft.value = previous;
    }

    async function onBaseUrlBlur() {
        const next = baseUrlDraft.value.trim();
        if ((currentUser.value?.llm_base_url ?? '') === next) return;
        const previous = currentUser.value?.llm_base_url ?? null;
        const result = await update('Base URL updated.', () =>
            authStore.updateMeAsync({ llm_base_url: next || null }),
        );
        if (result === null) baseUrlDraft.value = previous ?? '';
    }

    async function onModelBlur() {
        const next = modelDraft.value.trim();
        if ((currentUser.value?.llm_model ?? '') === next) return;
        const previous = currentUser.value?.llm_model ?? null;
        const result = await update('Model updated.', () =>
            authStore.updateMeAsync({ llm_model: next || null }),
        );
        if (result === null) modelDraft.value = previous ?? '';
    }

    async function onApiKeyBlur() {
        const next = apiKeyDraft.value.trim();
        if (!next) return;
        const result = await update('API key saved.', () =>
            authStore.updateMeAsync({ llm_api_key: next }),
        );
        if (result !== null) {
            // Clear the visible field after save so the placeholder
            // ("••••••••• (saved)") tells the user the key is on file.
            apiKeyDraft.value = '';
        }
    }

    async function onClearApiKey() {
        await update('API key removed.', () =>
            authStore.updateMeAsync({ clear_llm_api_key: true }),
        );
        probeResult.value = null;
    }

    // guard the paid-provider Test button: must either have a
    // saved key OR a freshly-typed plaintext to send.
    const canTestPaidProvider = computed(() => {
        if (providerDraft.value === 'ollama') return true;
        return !!apiKeyDraft.value.trim() || !!currentUser.value?.has_llm_api_key;
    });

    async function onTest() {
        if (!providerDraft.value) return;
        probing.value = true;
        probeResult.value = null;
        try {
            const result = await assistantApi.probeAsync({
                provider: providerDraft.value,
                base_url: baseUrlDraft.value.trim() || null,
                model: modelDraft.value.trim() || null,
                // Plaintext takes precedence; null falls back to the
                // saved encrypted blob server-side. Either way, the
                // raw plaintext is dropped from the SPA state once
                // the probe responds (no need to keep it).
                api_key: apiKeyDraft.value.trim() || null,
            });
            probeResult.value = result;
        } catch (err) {
            probeResult.value = {
                available: false,
                reason: toastCaption(err) ?? "Couldn't reach the server.",
                models: null,
            };
        } finally {
            probing.value = false;
        }
    }

    // Clear the inline probe result when the user edits any field —
    // a stale "Connected" tick next to a now-different URL is worse
    // than no tick at all.
    watch([providerDraft, baseUrlDraft, modelDraft, apiKeyDraft], () => {
        probeResult.value = null;
    });
</script>

<style scoped lang="scss">
    .settings-page { display: flex; flex-direction: column; }
    .settings-page__note {
        font-size: 0.8125rem;
        line-height: 1.4;
        margin-top: 4px;
    }
    .settings-divider {
        border: 0;
        height: 1px;
        background: color-mix(in srgb, var(--text-primary) 8%, transparent);
        margin: 0;
    }
</style>
