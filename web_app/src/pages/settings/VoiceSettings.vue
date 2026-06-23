<template>
    <div v-if="!currentUser">
        <q-card flat bordered>
            <q-card-section>
                <q-banner class="dora-bg-sunken" dense>Not signed in.</q-banner>
            </q-card-section>
        </q-card>
    </div>

    <div v-else class="column q-gutter-md">
        <!-- Voice (P2-13) ──────────────────────────────────────────── -->
        <q-card flat bordered>
            <q-card-section>
                <div class="text-h6">Voice</div>
                <div class="text-caption dora-text-muted">
                    Talk to Dora and let her talk back. Voice features
                    use your browser's built-in speech recognition and
                    synthesis — they only work where the browser
                    supports them, and your browser will ask for
                    microphone permission the first time you tap the mic.
                </div>
            </q-card-section>
            <q-separator />

            <q-card-section>
                <q-toggle
                    :model-value="currentUser.voice_input_enabled"
                    :disable="!voiceInputAvailable || saving"
                    label="Enable voice input (microphone)"
                    @update:model-value="onVoiceInputChange"
                />
                <div v-if="!voiceInputAvailable" class="text-caption dora-text-muted q-mt-xs">
                    Your browser doesn't expose the Web Speech API for
                    recognition. Try Chrome or Edge.
                </div>
            </q-card-section>

            <q-card-section>
                <q-toggle
                    :model-value="currentUser.voice_output_enabled"
                    :disable="!voiceOutputAvailable || saving"
                    label="Let Dora speak her replies"
                    @update:model-value="onVoiceOutputChange"
                />
                <div v-if="!voiceOutputAvailable" class="text-caption dora-text-muted q-mt-xs">
                    Your browser doesn't expose SpeechSynthesis.
                </div>
            </q-card-section>
        </q-card>
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

    // P2-13 — voice prefs. Availability flags come from cheap probes
    // against the browser's globals; they don't actually start a
    // recognition session, so the user can flip the toggle without
    // a microphone prompt firing here.
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
        // Cancel any in-flight utterance when the user opts out so the
        // toggle's effect is immediate.
        if (!value) voiceProbeOutput.cancel();
        await update(
            value ? 'Dora will speak her replies.' : 'Dora\'s voice muted.',
            () => authStore.updateMeAsync({ voice_output_enabled: value }),
        );
    }
</script>
