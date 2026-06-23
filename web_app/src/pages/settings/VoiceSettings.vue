<template>
    <div v-if="!currentUser">
        <q-banner class="dora-bg-sunken" dense>Not signed in.</q-banner>
    </div>

    <div v-else class="settings-page">
        <SettingsPageHeader
            title="Voice"
            description="Talk to Dora and let her talk back. Voice uses your browser's built-in speech recognition and synthesis — it only works where the browser supports it, and your browser will ask for microphone permission the first time."
        />

        <SettingsSection>
            <template #title>Microphone</template>
            <SettingsRow label="Enable voice input">
                <q-toggle
                    :model-value="currentUser.voice_input_enabled"
                    :disable="!voiceInputAvailable || saving"
                    @update:model-value="onVoiceInputChange"
                />
            </SettingsRow>
            <div v-if="!voiceInputAvailable" class="settings-page__note dora-text-muted">
                Your browser doesn't expose the Web Speech API for
                recognition. Try Chrome or Edge.
            </div>
        </SettingsSection>

        <hr class="settings-divider" />

        <SettingsSection>
            <template #title>Spoken replies</template>
            <SettingsRow label="Let Dora speak her replies">
                <q-toggle
                    :model-value="currentUser.voice_output_enabled"
                    :disable="!voiceOutputAvailable || saving"
                    @update:model-value="onVoiceOutputChange"
                />
            </SettingsRow>
            <div v-if="!voiceOutputAvailable" class="settings-page__note dora-text-muted">
                Your browser doesn't expose SpeechSynthesis.
            </div>
        </SettingsSection>
    </div>
</template>

<script lang="ts" setup>
    import { storeToRefs } from 'pinia';
    import { useQuasar } from 'quasar';
    import { useAuthStore } from 'src/stores/authStore';
    import { useSpeechOutput } from 'src/composables/useSpeechOutput';
    import { useVoiceInput } from 'src/composables/useVoiceInput';
    import { computed, ref } from 'vue';
    import { describeApiError } from 'src/services/errorHandling/apiErrorHandler';
    import SettingsSection from 'src/components/settings/SettingsSection.vue';
    import SettingsRow from 'src/components/settings/SettingsRow.vue';
    import SettingsPageHeader from 'src/components/settings/SettingsPageHeader.vue';

    const $q = useQuasar();
    const authStore = useAuthStore();
    const { currentUser } = storeToRefs(authStore);

    const saving = ref(false);

    function notifySuccess(message: string) {
        $q.notify({ type: 'positive', position: 'bottom-right', message });
    }
    function notifyError(message: string, err?: unknown) {
        $q.notify({
            type: 'negative',
            position: 'bottom-right',
            message,
            caption: describeApiError(err) || ''
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

    const voiceProbeInput = useVoiceInput();
    const voiceProbeOutput = useSpeechOutput();
    const voiceInputAvailable = computed(() => voiceProbeInput.available.value);
    const voiceOutputAvailable = computed(() => voiceProbeOutput.available.value);

    async function onVoiceInputChange(value: boolean) {
        await update(
            value ? 'Voice input enabled.' : 'Voice input disabled.',
            () => authStore.updateMeAsync({ voice_input_enabled: value }),
        );
    }
    async function onVoiceOutputChange(value: boolean) {
        if (!value) voiceProbeOutput.cancel();
        await update(
            value ? 'Dora will speak her replies.' : 'Dora\'s voice muted.',
            () => authStore.updateMeAsync({ voice_output_enabled: value }),
        );
    }
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
