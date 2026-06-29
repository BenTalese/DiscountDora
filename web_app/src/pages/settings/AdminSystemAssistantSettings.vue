<template>
    <div class="settings-page">
        <SettingsPageHeader
            title="AI assistant"
            description="Optional. Connect Dora's chat to a language model you run yourself. Off by default — when off, the assistant uses its built-in rule-based replies."
            :icon="ICONS.smart_toy"
        />

        <q-banner v-if="!isAdmin" class="dora-bg-negative-soft text-negative" dense rounded>
            You don't have admin permissions to view this page.
        </q-banner>

        <div v-else-if="loading" class="row justify-center q-py-md">
            <AppSpinner size="28px" />
        </div>

        <template v-else>
            <SettingsSection>
                <template #title>Enable</template>
                <template #description>
                    {{ enabledDraft
                        ? 'Enter a base URL and model below, then Save to apply.'
                        : 'Toggle on to configure. Nothing is applied until you Save.' }}
                </template>

                <SettingsRow label="Enable the AI assistant">
                    <q-toggle v-model="enabledDraft" :disable="saving" />
                </SettingsRow>
            </SettingsSection>

            <hr class="settings-divider" />

            <SettingsSection>
                <template #title>Server</template>
                <template #description>
                    Your LLM server's address (Ollama's default is shown).
                    Models load when you leave the URL field.
                </template>

                <SettingsRow stacked>
                    <div class="row q-col-gutter-sm items-end">
                        <q-input
                            v-model="baseUrlDraft"
                            label="LLM base URL"
                            placeholder="http://localhost:11434"
                            outlined
                            dense
                            class="col-12 col-sm-8"
                            :disable="saving || !enabledDraft"
                            @blur="onBaseUrlBlur"
                        />
                        <!-- FU-006: ambiguous — outline with Quasar palette color="secondary" (not the BaseButton "secondary" variant). Left as raw q-btn for review. -->
                        <q-btn
                            color="secondary"
                            no-caps
                            outline
                            :icon="ICONS.wifi_tethering"
                            label="Test"
                            :loading="probing"
                            :disable="saving || !enabledDraft || !baseUrlDraft.trim()"
                            @click="() => onTest(true)"
                        />
                    </div>
                </SettingsRow>

                <q-banner
                    v-if="probeResult"
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
            </SettingsSection>

            <hr class="settings-divider" />

            <SettingsSection>
                <template #title>Model</template>
                <template #description>
                    {{ allModels.length
                        ? 'Pick a detected model, or type one to pull later.'
                        : 'Type a model name, or test the connection to list installed models. Must support tool-calling.' }}
                </template>

                <SettingsRow stacked>
                    <q-select
                        v-model="modelDraft"
                        outlined
                        dense
                        :options="modelOptions"
                        use-input
                        fill-input
                        hide-selected
                        input-debounce="0"
                        new-value-mode="add-unique"
                        :disable="saving || !enabledDraft"
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
                </SettingsRow>

                <SettingsRow stacked>
                    <div>
                        <BaseButton
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
                    </div>
                </SettingsRow>
            </SettingsSection>

            <hr class="settings-divider" />

            <q-banner class="dora-bg-info-soft text-info" dense rounded>
                <template #avatar>
                    <q-icon :name="ICONS.info" size="20px" />
                </template>
                <div class="text-weight-medium q-mb-xs">Setting up your own LLM</div>
                <ol class="q-my-none q-pl-md">
                    <li>
                        Install <a href="https://ollama.com" target="_blank" rel="noopener">Ollama</a>
                        on a machine on your network.
                    </li>
                    <li>
                        Pull a tool-capable model:
                        <code>ollama pull qwen2.5:7b</code>.
                    </li>
                    <li>
                        Make sure it's serving (<code>ollama serve</code>).
                    </li>
                    <li>
                        Enter the base URL and model name above, enable, and save.
                    </li>
                </ol>
                <div class="q-mt-sm">
                    More detail is on the
                    <router-link to="/help">Help page</router-link>.
                </div>
            </q-banner>
        </template>
    </div>
</template>

<script lang="ts" setup>
    import AppSpinner from 'src/components/AppSpinner.vue';
    import { ICONS } from 'src/style/icons';
    import { storeToRefs } from 'pinia';
    import { useQuasar } from 'quasar';
    import AppSettingsApiService from 'src/services/api/appSettingsApiService';
    import { useAuthStore } from 'src/stores/authStore';
    import { computed, onMounted, ref } from 'vue';
    import { toastCaption } from 'src/services/errorHandling/apiErrorHandler';
    import SettingsSection from 'src/components/settings/SettingsSection.vue';
    import SettingsRow from 'src/components/settings/SettingsRow.vue';
    import SettingsPageHeader from 'src/components/settings/SettingsPageHeader.vue';
    import BaseButton from 'src/components/BaseButton.vue';
    import { useUnsavedChangesGuard } from 'src/composables/useUnsavedChangesGuard';

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

    // R-020 — deferred-save surface, must wire the unsaved-changes guard.
    // Dirty iff any of the three drafts diverges from `saved.value`.
    useUnsavedChangesGuard(computed(() => !unchanged.value));

    // Save is gated on: something changed AND (if enabling, valid inputs).
    // Disabling is always valid — turning AI off doesn't need a URL/model.
    const canSave = computed(() => {
        if (unchanged.value) return false;
        if (!enabledDraft.value) return true;
        return baseUrlDraft.value.trim().length > 0 && modelDraft.value.trim().length > 0;
    });

    type LoadedAssistant = { llm_enabled: boolean; llm_base_url: string; llm_model: string };
    function applyLoaded(s: LoadedAssistant) {
        enabledDraft.value = s.llm_enabled;
        baseUrlDraft.value = s.llm_base_url;
        modelDraft.value = s.llm_model;
        saved.value = { enabled: s.llm_enabled, baseUrl: s.llm_base_url, model: s.llm_model };
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
                caption: toastCaption(err)
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
            // Leave defaults; the help banner explains setup.
        } finally {
            loading.value = false;
        }
    });
</script>

<style scoped lang="scss">
    .settings-page { display: flex; flex-direction: column; }
    .settings-divider {
        border: 0;
        height: 1px;
        background: color-mix(in srgb, var(--text-primary) 8%, transparent);
        margin: 8px 0;
    }
</style>
