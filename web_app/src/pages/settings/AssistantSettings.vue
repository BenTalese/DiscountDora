<template>
    <div v-if="!currentUser">
        <q-banner class="dora-bg-sunken" dense>Not signed in.</q-banner>
    </div>

    <div v-else class="settings-page">
        <SettingsPageHeader title="Assistant" :icon="ICONS.smart_toy">
            <template #description>
                Settings to control D.O.R.A., your personal assistant in the
                kitchen. Learn more about using her capabilities
                <router-link to="/help/dora" class="settings-page__link">here</router-link>.
            </template>
        </SettingsPageHeader>

        <!-- Warns (and offers to generate a key) when the install hasn't set
             DORA_SECRET_ENCRYPTION_KEY — a paid-provider API key can't be
             stored encrypted without it, so saving one would be refused. -->
        <EncryptionKeyBanner secret-label="a paid provider's API key" />

        <SettingsSection>
            <SettingsRow label="Show digital assistant chat bubble">
                <q-toggle
                    :model-value="currentUser.show_assistant !== false"
                    @update:model-value="onShowAssistantChange"
                />
            </SettingsRow>
        </SettingsSection>

        <hr class="settings-divider" />

        <SettingsSection>
            <template #title>Zero-Input Pantry</template>
            <template #description>
                Dora can infer each item's stock level from your shopping,
                cooking, and buying rhythm — showing what it thinks beside the
                level you last recorded, and asking a quick check only when it's
                unsure. Your recorded level always stays the source of truth for
                shopping and cooking.
                <router-link
                    :to="{ path: '/help', query: { q: 'Dora thinks' } }"
                    class="settings-page__link"
                >Learn more</router-link>.
            </template>

            <SettingsRow
                label="Infer stock levels"
                help="When on, Dora shows an inferred level (with a reason and confidence) alongside the recorded one, and can ask a targeted quick-check. Turn off for purely manual levels."
            >
                <q-toggle
                    :model-value="currentUser.inferred_pantry_enabled"
                    @update:model-value="onInferredPantryChange"
                />
            </SettingsRow>
        </SettingsSection>

        <hr class="settings-divider" />

        <SettingsSection>
            <template #title>Mode</template>
            <template #description>
                <strong>Basic</strong> (the default, no setup) answers questions
                about your pantry, meals, and lists and can add items when you
                type things like "add milk". Selecting a language model routes
                <em>tool-able requests</em> through it for richer, multi-step
                help. Only providers you've connected below can be picked.
            </template>

            <SettingsRow label="Mode">
                <q-select
                    :model-value="modeValue"
                    :options="modeOptions"
                    emit-value
                    map-options
                    outlined
                    dense
                    style="min-width: 220px"
                    @update:model-value="onModeChange"
                />
            </SettingsRow>
        </SettingsSection>

        <hr class="settings-divider" />

        <SettingsSection>
            <template #title>Providers</template>
            <template #description>
                Connect one or more language models. <strong>Ollama</strong>
                runs locally (no key needed); <strong>OpenAI</strong>,
                <strong>Anthropic</strong>, and <strong>Google Gemini</strong>
                are paid hosted APIs — bring your own key. Details are checked
                the moment you enter them.
            </template>

            <div
                v-for="provider in PROVIDERS"
                :key="provider"
                class="provider-card"
            >
                <div class="provider-card__head">
                    <h3 class="provider-card__name">{{ providerDisplayName(provider) }}</h3>
                    <div class="provider-card__status">
                        <q-spinner
                            v-if="state[provider].status === 'checking'"
                            size="14px"
                            color="primary"
                        />
                        <q-icon
                            v-else
                            :name="statusIcon(provider)"
                            :color="statusColor(provider)"
                            size="16px"
                        />
                        <span :class="`text-${statusColor(provider)}`">
                            {{ statusLabel(provider) }}
                        </span>
                        <BaseButton
                            v-if="canTest(provider)"
                            variant="ghost"
                            :icon="ICONS.wifi_tethering"
                            label="Test"
                            :disable="state[provider].status === 'checking'"
                            @click="onTest(provider)"
                        />
                    </div>
                </div>

                <div class="provider-card__body">
                    <!-- Ollama: base URL + model (model becomes a picker of
                         installed models once a probe succeeds). No API key. -->
                    <template v-if="provider === 'ollama'">
                        <SettingsRow label="Base URL" stacked>
                            <q-input
                                v-model="state.ollama.base_url"
                                outlined
                                dense
                                placeholder="http://localhost:11434"
                                @blur="onOllamaBaseUrlBlur"
                                @keydown.enter.prevent="onOllamaBaseUrlBlur"
                            />
                        </SettingsRow>
                        <SettingsRow label="Model" stacked>
                            <q-select
                                v-if="state.ollama.models.length"
                                v-model="state.ollama.model"
                                :options="state.ollama.models"
                                outlined
                                dense
                                use-input
                                fill-input
                                hide-selected
                                new-value-mode="add-unique"
                                input-debounce="0"
                                placeholder="qwen2.5:7b"
                                @update:model-value="onOllamaModelCommit"
                                @blur="onOllamaModelBlur"
                            />
                            <q-input
                                v-else
                                v-model="state.ollama.model"
                                outlined
                                dense
                                placeholder="qwen2.5:7b"
                                hint="Enter your Ollama base URL first to list installed models."
                                @blur="onOllamaModelBlur"
                                @keydown.enter.prevent="onOllamaModelBlur"
                            />
                        </SettingsRow>
                    </template>

                    <!-- Paid providers: API key (write-only) + model + optional
                         base URL (a self-hosted relay). Gemini has no base URL. -->
                    <template v-else>
                        <SettingsRow label="API key" stacked>
                            <q-input
                                v-model="state[provider].api_key"
                                outlined
                                dense
                                type="password"
                                autocomplete="off"
                                :placeholder="state[provider].has_api_key ? '••••••••• (saved)' : 'Paste your key here'"
                                @blur="onApiKeyBlur(provider)"
                                @keydown.enter.prevent="onApiKeyBlur(provider)"
                            />
                            <BaseButton
                                v-if="state[provider].has_api_key"
                                variant="danger-ghost"
                                :icon="ICONS.delete"
                                label="Remove key"
                                @click="onClearApiKey(provider)"
                            />
                        </SettingsRow>
                        <SettingsRow label="Model" stacked>
                            <q-input
                                v-model="state[provider].model"
                                outlined
                                dense
                                :placeholder="modelPlaceholder(provider)"
                                @blur="onPaidModelBlur(provider)"
                                @keydown.enter.prevent="onPaidModelBlur(provider)"
                            />
                        </SettingsRow>
                        <SettingsRow v-if="provider !== 'gemini'" label="Base URL (optional)" stacked>
                            <q-input
                                v-model="state[provider].base_url"
                                outlined
                                dense
                                :placeholder="defaultBaseUrl(provider)"
                                @blur="onPaidBaseUrlBlur(provider)"
                                @keydown.enter.prevent="onPaidBaseUrlBlur(provider)"
                            />
                        </SettingsRow>
                    </template>
                </div>
            </div>
        </SettingsSection>
    </div>
</template>

<script lang="ts" setup>
    import BaseButton from 'src/components/BaseButton.vue';
    import { ICONS } from 'src/style/icons';
    import { storeToRefs } from 'pinia';
    import AssistantApiService, {
        type LlmProviderName,
        type ProviderConfig,
    } from 'src/services/api/assistantApiService';
    import { useAuthStore } from 'src/stores/authStore';
    import { computed, onMounted, reactive } from 'vue';
    import { toastCaption } from 'src/services/errorHandling/apiErrorHandler';
    import { useSettingsSave } from 'src/composables/useSettingsSave';
    import SettingsSection from 'src/components/settings/SettingsSection.vue';
    import SettingsRow from 'src/components/settings/SettingsRow.vue';
    import SettingsPageHeader from 'src/components/settings/SettingsPageHeader.vue';
    import EncryptionKeyBanner from 'src/components/settings/EncryptionKeyBanner.vue';

    const authStore = useAuthStore();
    const { currentUser } = storeToRefs(authStore);
    const assistantApi = new AssistantApiService();
    const { update } = useSettingsSave();

    const PROVIDERS: LlmProviderName[] = ['ollama', 'openai', 'anthropic', 'gemini'];

    // 'empty' — nothing entered; 'unverified' — details saved but no successful
    // probe yet; 'checking' — probe in flight; 'connected' — probe succeeded;
    // 'error' — last probe failed. Only 'connected' providers are selectable as
    // a Mode (mirrors the server-side guard on `llm_enabled`).
    type ProviderStatus = 'empty' | 'unverified' | 'checking' | 'connected' | 'error';

    interface ProviderUiState {
        base_url: string;
        model: string;
        api_key: string;       // draft plaintext; cleared once saved
        has_api_key: boolean;  // a key is on file server-side
        verified: boolean;
        status: ProviderStatus;
        reason: string | null;
        models: string[];      // Ollama models discovered by the last probe
    }

    function emptyState(): ProviderUiState {
        return {
            base_url: '',
            model: '',
            api_key: '',
            has_api_key: false,
            verified: false,
            status: 'empty',
            reason: null,
            models: [],
        };
    }

    const state = reactive<Record<LlmProviderName, ProviderUiState>>({
        ollama: emptyState(),
        openai: emptyState(),
        anthropic: emptyState(),
        gemini: emptyState(),
    });

    function providerDisplayName(p: LlmProviderName): string {
        switch (p) {
            case 'openai': return 'OpenAI';
            case 'anthropic': return 'Anthropic';
            case 'gemini': return 'Google Gemini';
            default: return 'Ollama';
        }
    }

    function defaultBaseUrl(p: LlmProviderName): string {
        switch (p) {
            case 'openai': return 'https://api.openai.com/v1';
            case 'anthropic': return 'https://api.anthropic.com';
            default: return '';
        }
    }

    function modelPlaceholder(p: LlmProviderName): string {
        switch (p) {
            case 'openai': return 'gpt-4o-mini';
            case 'anthropic': return 'claude-3-5-sonnet-20241022';
            case 'gemini': return 'gemini-2.0-flash';
            default: return 'qwen2.5:7b';
        }
    }

    function seedFrom(configs: ProviderConfig[]) {
        for (const cfg of configs) {
            const s = state[cfg.provider];
            if (!s) continue;
            s.base_url = cfg.base_url ?? '';
            s.model = cfg.model ?? '';
            s.has_api_key = cfg.has_api_key;
            s.verified = cfg.verified;
            const configured = !!(cfg.base_url || cfg.model || cfg.has_api_key);
            s.status = cfg.verified ? 'connected' : configured ? 'unverified' : 'empty';
        }
    }

    onMounted(async () => {
        try {
            const { providers } = await assistantApi.getProvidersAsync();
            seedFrom(providers);
        } catch (err) {
            // Non-fatal — the page still renders with empty fields the user
            // can fill; the toast explains the fetch failure.
            toastCaption(err);
        }
    });

    // ----- status chip -----

    function statusLabel(p: LlmProviderName): string {
        const s = state[p];
        switch (s.status) {
            case 'checking': return 'Checking…';
            case 'connected': return 'Connected';
            case 'error': return s.reason ?? "Couldn't connect";
            case 'unverified': return 'Not tested';
            default: return 'Not configured';
        }
    }

    function statusColor(p: LlmProviderName): string {
        switch (state[p].status) {
            case 'connected': return 'positive';
            case 'error': return 'negative';
            case 'unverified': return 'warning';
            default: return 'grey';
        }
    }

    function statusIcon(p: LlmProviderName): string {
        switch (state[p].status) {
            case 'connected': return ICONS.check_circle;
            case 'error': return ICONS.warning;
            case 'unverified': return ICONS.help_outline;
            default: return ICONS.help_outline;
        }
    }

    function canTest(p: LlmProviderName): boolean {
        // A manual re-check is useful once details exist (e.g. the server
        // came back up). Nothing to test on an empty provider.
        return state[p].status !== 'empty' && state[p].status !== 'checking';
    }

    // ----- save + probe -----

    async function saveProvider(p: LlmProviderName, patch: Record<string, unknown>): Promise<boolean> {
        try {
            const cfg = await assistantApi.updateProviderAsync(p, patch);
            state[p].has_api_key = cfg.has_api_key;
            state[p].verified = false;
            return true;
        } catch (err) {
            state[p].status = 'error';
            state[p].reason = toastCaption(err) ?? 'Save failed.';
            return false;
        }
    }

    async function probe(p: LlmProviderName) {
        state[p].status = 'checking';
        state[p].reason = null;
        try {
            const r = await assistantApi.probeAsync({
                provider: p,
                base_url: state[p].base_url.trim() || null,
                model: state[p].model.trim() || null,
                // Plaintext (just typed) takes precedence; null falls back to
                // the saved key server-side.
                api_key: state[p].api_key.trim() || null,
            });
            if (r.available) {
                state[p].status = 'connected';
                state[p].verified = true;
                if (r.models) state[p].models = r.models;
            } else {
                state[p].status = 'error';
                state[p].reason = r.reason ?? "Couldn't connect";
                state[p].verified = false;
            }
        } catch (err) {
            state[p].status = 'error';
            state[p].reason = toastCaption(err) ?? "Couldn't reach the server.";
            state[p].verified = false;
        }
        // Keep the Mode dropdown + DoraChat's readiness in sync with the new
        // verified state.
        await authStore.refreshAsync();
    }

    async function onTest(p: LlmProviderName) {
        await probe(p);
    }

    // Ollama handlers
    async function onOllamaBaseUrlBlur() {
        if (await saveProvider('ollama', { base_url: state.ollama.base_url.trim() || null })) {
            if (state.ollama.base_url.trim()) await probe('ollama');
            else state.ollama.status = state.ollama.model ? 'unverified' : 'empty';
        }
    }
    async function onOllamaModelBlur() {
        if (await saveProvider('ollama', { model: state.ollama.model.trim() || null })) {
            if (state.ollama.base_url.trim() && state.ollama.model.trim()) await probe('ollama');
        }
    }
    async function onOllamaModelCommit() {
        // q-select add-unique commits without a blur; persist + probe.
        await onOllamaModelBlur();
    }

    // Paid-provider handlers
    async function onApiKeyBlur(p: LlmProviderName) {
        const next = state[p].api_key.trim();
        if (!next) return;
        if (await saveProvider(p, { api_key: next })) {
            state[p].api_key = '';  // masked; placeholder now shows "(saved)"
            await probe(p);
        }
    }
    async function onClearApiKey(p: LlmProviderName) {
        if (await saveProvider(p, { clear_api_key: true })) {
            state[p].api_key = '';
            state[p].status = state[p].model ? 'unverified' : 'empty';
            await authStore.refreshAsync();
        }
    }
    async function onPaidModelBlur(p: LlmProviderName) {
        if (await saveProvider(p, { model: state[p].model.trim() || null })) {
            if (state[p].has_api_key && state[p].model.trim()) await probe(p);
        }
    }
    async function onPaidBaseUrlBlur(p: LlmProviderName) {
        await saveProvider(p, { base_url: state[p].base_url.trim() || null });
        if (state[p].has_api_key && state[p].model.trim()) await probe(p);
    }

    // ----- Mode -----

    const modeOptions = computed(() => {
        const opts: { label: string; value: LlmProviderName | null }[] = [
            { label: 'Basic (built-in)', value: null },
        ];
        for (const p of PROVIDERS) {
            if (state[p].verified) opts.push({ label: providerDisplayName(p), value: p });
        }
        return opts;
    });

    const modeValue = computed<LlmProviderName | null>(() =>
        currentUser.value?.llm_enabled ? (currentUser.value.llm_provider ?? null) : null,
    );

    async function onModeChange(value: LlmProviderName | null) {
        if (value === null) {
            await update('Switched to Basic mode.', () =>
                authStore.updateMeAsync({ llm_enabled: false }),
            );
        } else {
            await update(`AI mode on (${providerDisplayName(value)}).`, () =>
                authStore.updateMeAsync({ llm_provider: value, llm_enabled: true }),
            );
        }
    }

    async function onShowAssistantChange(value: boolean) {
        await update(
            value ? 'Dora helper shown.' : 'Dora helper hidden.',
            () => authStore.updateMeAsync({ show_assistant: value }),
        );
    }

    // Zero-Input Pantry opt-out (moved here from Appearance). Default true on
    // a fresh account. Same shared-toast shape as the toggles above.
    async function onInferredPantryChange(value: boolean) {
        await update(
            value
                ? 'Dora will infer your stock levels.'
                : 'Inference off — levels are now manual.',
            () => authStore.updateMeAsync({ inferred_pantry_enabled: value }),
        );
    }
</script>

<style scoped lang="scss">
    .settings-page { display: flex; flex-direction: column; }
    .settings-page__link { color: var(--brand-primary); font-weight: 600; }
    .settings-divider {
        border: 0;
        height: 1px;
        background: color-mix(in srgb, var(--text-primary) 8%, transparent);
        margin: 0;
    }
    .provider-card {
        border: 1px solid color-mix(in srgb, var(--text-primary) 10%, transparent);
        border-radius: 12px;
        padding: 14px 16px;
        display: flex;
        flex-direction: column;
        gap: 12px;
    }
    .provider-card__head {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
        flex-wrap: wrap;
    }
    .provider-card__name {
        margin: 0;
        font-size: 0.9375rem;
        font-weight: 700;
        color: var(--text-primary);
    }
    .provider-card__status {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 0.8125rem;
    }
    .provider-card__body {
        display: flex;
        flex-direction: column;
        gap: 10px;
    }
</style>
