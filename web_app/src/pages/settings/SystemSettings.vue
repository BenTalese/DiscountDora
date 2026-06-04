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
            </template>

            <q-separator />

            <!-- Existing install-wide placeholders (not yet wired) ─────── -->
            <q-list separator>
                <q-item>
                    <q-item-section>
                        <q-item-label>Allow new registrations</q-item-label>
                        <q-item-label caption>
                            When off, the public sign-up form is hidden and the
                            register endpoint refuses new users.
                        </q-item-label>
                    </q-item-section>
                    <q-item-section side>
                        <q-toggle v-model="allowRegistrations" disable>
                            <q-tooltip>Backed by a future setting — UI placeholder</q-tooltip>
                        </q-toggle>
                    </q-item-section>
                </q-item>

                <q-item>
                    <q-item-section>
                        <q-item-label>Maintenance mode</q-item-label>
                        <q-item-label caption>
                            Show a banner and disable writes while running migrations.
                        </q-item-label>
                    </q-item-section>
                    <q-item-section side>
                        <q-toggle v-model="maintenanceMode" disable>
                            <q-tooltip>Backed by a future setting — UI placeholder</q-tooltip>
                        </q-toggle>
                    </q-item-section>
                </q-item>

                <q-item>
                    <q-item-section>
                        <q-item-label>Weekly emailer enabled</q-item-label>
                        <q-item-label caption>
                            Globally enable/disable the weekly deals emailer job.
                        </q-item-label>
                    </q-item-section>
                    <q-item-section side>
                        <q-toggle v-model="emailerEnabled" disable>
                            <q-tooltip>Backed by a future setting — UI placeholder</q-tooltip>
                        </q-toggle>
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
    import { computed, onMounted, ref } from 'vue';
    import { describeApiError } from 'src/services/errorHandling/apiErrorHandler';

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
    const allowRegistrations = ref(true);
    const maintenanceMode = ref(false);
    const emailerEnabled = ref(true);

    function applyLoaded(s: { llm_enabled: boolean; llm_base_url: string; llm_model: string }) {
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
