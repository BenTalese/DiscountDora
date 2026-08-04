<template>
    <div class="settings-page">
        <SettingsPageHeader
            title="AI assistant"
            description="Install-wide master switch for Dora's AI mode. Per-user URL, model, and API key live on each account's Settings → Assistant page."
            :icon="ICONS.smart_toy"
        />

        <q-banner v-if="!isAdmin" class="dora-bg-negative-soft text-negative" dense rounded>
            You don't have admin permissions to view this page.
        </q-banner>

        <div v-else-if="loading" class="row justify-center q-py-md">
            <AppSpinner size="28px" />
        </div>

        <template v-else>
            <!-- the install-wide knob is just the master
                 kill-switch now. Per-user provider config (URL, model,
                 API key) lives on each user's own Settings → Assistant
                 page; the admin controls the *availability* of that
                 feature at the install level. -->
            <SettingsSection>
                <template #title>Master switch</template>
                <template #description>
                    When this is off, every user's AI mode is forced off
                    regardless of their personal setting. Defence in
                    depth: any user can configure their own LLM, but the
                    admin keeps a single kill switch for the whole
                    install.
                </template>

                <SettingsRow label="Allow AI mode on this install">
                    <q-toggle
                        :model-value="masterEnabled"
                        :disable="saving"
                        @update:model-value="onToggleMaster"
                    />
                </SettingsRow>
            </SettingsSection>

            <hr class="settings-divider" />

            <q-banner class="dora-bg-sunken" dense rounded>
                <template #avatar>
                    <q-icon :name="ICONS.info" size="20px" class="dora-text-muted" />
                </template>
                <div class="text-weight-medium q-mb-xs">
                    Where users configure their own AI
                </div>
                <p class="q-mb-sm">
                    Each account picks a provider (Ollama, OpenAI,
                    Anthropic, or Google Gemini), enters a base URL or
                    API key, and saves a model name on their own
                    <router-link to="/settings/assistant">Settings → Assistant</router-link>
                    page. The server reads the *current user's* config
                    when answering — a household with two desktops can
                    point each user at their own LLM.
                </p>
                <p class="q-mb-none text-caption dora-text-muted">
                    For paid providers, this install needs the
                    <code>DORA_SECRET_ENCRYPTION_KEY</code> environment
                    variable set so user-saved API keys can be stored
                    encrypted at rest. Generate one with:
                    <code>python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"</code>.
                </p>
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
    import { onMounted, ref } from 'vue';
    import { toastCaption } from 'src/services/errorHandling/apiErrorHandler';
    import SettingsSection from 'src/components/settings/SettingsSection.vue';
    import SettingsRow from 'src/components/settings/SettingsRow.vue';
    import SettingsPageHeader from 'src/components/settings/SettingsPageHeader.vue';

    const $q = useQuasar();
    const { isAdmin } = storeToRefs(useAuthStore());
    const api = new AppSettingsApiService();

    const masterEnabled = ref(true);
    const loading = ref(false);
    const saving = ref(false);

    onMounted(async () => {
        if (!isAdmin.value) return;
        loading.value = true;
        try {
            const s = await api.getAsync();
            masterEnabled.value = s.master_llm_enabled;
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not load AI settings.',
                caption: toastCaption(err),
            });
        } finally {
            loading.value = false;
        }
    });

    async function onToggleMaster(next: boolean) {
        // Save-on-change (R-020 carve-out: no draft window, one boolean
        // — flipping immediately matches the other install-wide toggles
        // like meal_planning_enabled / scanning_enabled).
        const previous = masterEnabled.value;
        masterEnabled.value = next;
        saving.value = true;
        try {
            const s = await api.updateAsync({ master_llm_enabled: next });
            masterEnabled.value = s.master_llm_enabled;
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: next ? 'AI mode allowed on this install.' : 'AI mode disabled install-wide.',
            });
        } catch (err) {
            masterEnabled.value = previous;
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not save.',
                caption: toastCaption(err),
            });
        } finally {
            saving.value = false;
        }
    }
</script>
