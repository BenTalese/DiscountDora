<template>
    <div v-if="!currentUser">
        <q-banner class="dora-bg-sunken" dense>Not signed in.</q-banner>
    </div>

    <div v-else class="settings-page">
        <SettingsPageHeader
            title="Voice"
            :icon="ICONS.record_voice_over"
            description="Talk to Dora and let her talk back. Speech recognition uses your browser's built-in support, so it only works where the browser supports it and will ask for microphone permission the first time. For Dora's replies you can choose her natural neural voice or your browser's built-in one."
        />

        <SettingsSection>
            <template #title>Enable microphone voice input</template>
            <template #actions>
                <q-toggle
                    :model-value="currentUser.voice_input_enabled"
                    :disable="!voiceInputAvailable"
                    aria-label="Enable microphone voice input"
                    @update:model-value="onVoiceInputChange"
                />
            </template>
            <div v-if="!voiceInputAvailable" class="settings-page__note dora-text-muted">
                Your browser doesn't expose the Web Speech API for
                recognition. Try Chrome or Edge.
            </div>
        </SettingsSection>

        <hr class="settings-divider" />

        <SettingsSection>
            <template #title>Let Dora speak her replies</template>
            <template #actions>
                <q-toggle
                    :model-value="currentUser.voice_output_enabled"
                    :disable="!voiceOutputAvailable"
                    aria-label="Let Dora speak her replies"
                    @update:model-value="onVoiceOutputChange"
                />
            </template>
            <div v-if="!voiceOutputAvailable" class="settings-page__note dora-text-muted">
                Your browser doesn't expose SpeechSynthesis.
            </div>
        </SettingsSection>

        <hr class="settings-divider" />

        <SettingsSection>
            <template #title>Dora's voice</template>
            <template #description>
                Choose how Dora sounds when she speaks her replies and reads cook-mode steps.
                Download a neural voice you like and select it, or use the default device text-to-speech voice.
            </template>

            <div v-if="!piperAvailable" class="settings-page__note dora-text-muted">
                Dora's neural-voice engine isn't installed on this server, so
                replies use the browser voice. (The Docker image and desktop app
                include it; you can still download voices below for when it's
                available.)
            </div>
            <div
                v-else-if="!anyVoiceReady"
                class="settings-page__note dora-text-muted"
            >
                Download a voice below to start using Dora's neural voice.
            </div>

            <div v-if="!loadingVoices" class="settings-page__voices">
                <VoicePicker
                    :model-value="currentUser.voice_id"
                    :voices="voices"
                    :piper-available="piperAvailable"
                    :device-default-active="currentUser.voice_engine === 'browser'"
                    @update:model-value="onVoiceChange"
                    @select-device-default="onSelectDeviceDefault"
                    @download="onDownload"
                />
            </div>
        </SettingsSection>
    </div>
</template>

<script lang="ts" setup>
    import { storeToRefs } from 'pinia';
    import { useAuthStore } from 'src/stores/authStore';
    import { useSpeechOutput } from 'src/composables/useSpeechOutput';
    import { useVoiceInput } from 'src/composables/useVoiceInput';
    import { computed, onBeforeUnmount, onMounted, ref } from 'vue';
    import { useSettingsSave } from 'src/composables/useSettingsSave';
    import TtsApiService, { type TtsVoice } from 'src/services/api/ttsApiService';
    import SettingsSection from 'src/components/settings/SettingsSection.vue';
    import { ICONS } from 'src/style/icons';
    import SettingsPageHeader from 'src/components/settings/SettingsPageHeader.vue';
    import VoicePicker from 'src/components/settings/VoicePicker.vue';

    const authStore = useAuthStore();
    const { currentUser } = storeToRefs(authStore);
    const ttsApi = new TtsApiService();

    // R-003 / FU-601 — shared save-toast helper (see useSettingsSave).
    const { notifySuccess, notifyError, update } = useSettingsSave();
    const loadingVoices = ref(true);
    const voices = ref<TtsVoice[]>([]);
    const piperAvailable = ref(false);

    const anyVoiceReady = computed(() => voices.value.some((v) => v.status === 'ready'));

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
    // Picking a neural voice card both selects it AND switches Dora onto the
    // neural engine — the standalone engine toggle was removed, so selection is
    // the one place engine intent is expressed (owner feedback). Both fields go
    // in one save.
    async function onVoiceChange(value: string) {
        await update(
            'Voice updated.',
            () => authStore.updateMeAsync({ voice_id: value, voice_engine: 'piper' }),
        );
    }
    // "Device default voice" card → the browser/device engine.
    async function onSelectDeviceDefault() {
        await update(
            'Using your device voice.',
            () => authStore.updateMeAsync({ voice_engine: 'browser' }),
        );
    }

    async function refreshVoices() {
        const res = await ttsApi.getVoicesAsync();
        voices.value = res.voices;
        piperAvailable.value = res.piper_available;
    }

    // Poll while any voice is mid-download, so the cards flip to Ready when the
    // server-side fetch finishes.
    let pollTimer: ReturnType<typeof setInterval> | null = null;
    function stopPolling() {
        if (pollTimer !== null) { clearInterval(pollTimer); pollTimer = null; }
    }
    async function pollOnce() {
        try {
            await refreshVoices();
        } catch { /* transient; keep polling */ }
        if (!voices.value.some((v) => v.status === 'downloading')) stopPolling();
    }
    function ensurePolling() {
        if (pollTimer !== null) return;
        pollTimer = setInterval(() => { void pollOnce(); }, 2500);
    }

    async function onDownload(voiceId: string) {
        const voice = voices.value.find((v) => v.id === voiceId);
        try {
            await ttsApi.downloadVoiceAsync(voiceId);
            await refreshVoices();
            ensurePolling();
            notifySuccess(`Downloading ${voice?.label ?? 'voice'}…`);
        } catch (err) {
            notifyError(`Could not start downloading ${voice?.label ?? 'voice'}.`, err);
        }
    }

    onMounted(async () => {
        try {
            await refreshVoices();
            if (voices.value.some((v) => v.status === 'downloading')) ensurePolling();
        } catch {
            // Catalog unreachable — leave Piper disabled; replies fall back to
            // the browser voice. The section notes cover the why.
            voices.value = [];
            piperAvailable.value = false;
        } finally {
            loadingVoices.value = false;
        }
    });

    onBeforeUnmount(stopPolling);
</script>

<style scoped lang="scss">
    .settings-page { display: flex; flex-direction: column; }
    .settings-page__note {
        font-size: 0.8125rem;
        line-height: 1.4;
        margin-top: 4px;
    }
    .settings-page__voices { margin-top: 12px; }
    .settings-divider {
        border: 0;
        height: 1px;
        background: color-mix(in srgb, var(--text-primary) 8%, transparent);
        margin: 0;
    }
</style>
