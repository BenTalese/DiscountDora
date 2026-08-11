<template>
    <div class="settings-page">
        <SettingsPageHeader
            title="Voice (Piper TTS)"
            description="Where the server finds Piper — the offline engine that gives Dora a natural spoken voice in chat and cook mode. Shipped desktop and Docker builds fill these in automatically; you only need to touch this page on a source install, or to point at a custom binary or voice folder."
            :icon="ICONS.record_voice_over"
        />

        <q-banner v-if="!isAdmin" class="dora-bg-negative-soft text-negative" dense rounded>
            You don't have admin permissions to view this page.
        </q-banner>

        <template v-else-if="!loading">
            <SettingsSection>
                <template #title>How Dora's voice works</template>
                <template #description>
                    Two layers, set in two places — this page is only the first.
                </template>

                <ul class="voice-intro">
                    <li>
                        <strong>The engine (here).</strong> Piper is a small,
                        offline neural text-to-speech that runs on the server's
                        CPU — no cloud calls. The settings below tell the server
                        where the Piper program and its voice models live. If
                        Piper can't be found, Dora falls back to the browser's
                        built-in voice, so she's never silent.
                    </li>
                    <li>
                        <strong>The voice (elsewhere).</strong> Which voice each
                        person hears — and the download of extra voices — lives
                        on the per-user
                        <router-link to="/settings/voice">Voice
                        settings</router-link> page, not here. This page is
                        install-wide plumbing; that page is personal choice.
                    </li>
                </ul>
            </SettingsSection>

            <SettingsSection>
                <template #title>Piper program</template>
                <template #description>
                    The path to the <code>piper</code> executable on the server.
                    Leave blank to search the system <code>PATH</code> (which
                    works after <code>pip install piper-tts</code>). Desktop and
                    Docker builds ship Piper and set this for you — leave it
                    blank there.
                </template>

                <SettingsRow label="Executable path" stacked>
                    <q-input
                        v-model="draft.piper_bin"
                        outlined dense clearable
                        placeholder="/usr/local/bin/piper"
                        @blur="() => onSaveField('piper_bin')"
                    />
                </SettingsRow>
            </SettingsSection>

            <SettingsSection>
                <template #title>Voice models folder</template>
                <template #description>
                    The folder holding the pre-shipped <code>.onnx</code> voice
                    files. Blank is normal — the server already knows where the
                    bundled voices live (next to the app, or inside a desktop /
                    Docker build). Only set this to point at a custom folder of
                    voices you've placed yourself.
                </template>

                <SettingsRow label="Bundled voice folder" stacked>
                    <q-input
                        v-model="draft.piper_bundled_voice_dir"
                        outlined dense clearable
                        placeholder="/opt/dora/voices"
                        @blur="() => onSaveField('piper_bundled_voice_dir')"
                    />
                </SettingsRow>
            </SettingsSection>
        </template>
    </div>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import { storeToRefs } from 'pinia';
    import { useQuasar } from 'quasar';
    import AppSettingsApiService, { type AppSettings } from 'src/services/api/appSettingsApiService';
    import { useAuthStore } from 'src/stores/authStore';
    import { onMounted, reactive, ref } from 'vue';
    import { toastCaption } from 'src/services/errorHandling/apiErrorHandler';
    import SettingsSection from 'src/components/settings/SettingsSection.vue';
    import SettingsRow from 'src/components/settings/SettingsRow.vue';
    import SettingsPageHeader from 'src/components/settings/SettingsPageHeader.vue';

    type VoiceField = 'piper_bin' | 'piper_bundled_voice_dir';

    const $q = useQuasar();
    const { isAdmin } = storeToRefs(useAuthStore());
    const api = new AppSettingsApiService();

    const loading = ref(true);
    const saved = reactive({
        piper_bin: '',
        piper_bundled_voice_dir: '',
    });
    const draft = reactive({ ...saved });

    function resetDrafts() {
        Object.assign(draft, saved);
    }

    async function onSaveField(field: VoiceField) {
        const value = (draft[field] ?? '').trim();
        if (value === saved[field]) return;
        try {
            const result = await api.updateAsync({ [field]: value });
            saved[field] = result[field];
            resetDrafts();
            $q.notify({
                type: 'positive', position: 'bottom-right',
                message: 'Voice settings saved.',
            });
        } catch (err) {
            resetDrafts();
            $q.notify({
                type: 'negative', position: 'bottom-right',
                message: 'Could not save voice settings.',
                caption: toastCaption(err),
            });
        }
    }

    function hydrate(s: AppSettings) {
        saved.piper_bin = s.piper_bin;
        saved.piper_bundled_voice_dir = s.piper_bundled_voice_dir;
        resetDrafts();
    }

    onMounted(async () => {
        if (!isAdmin.value) {
            loading.value = false;
            return;
        }
        try {
            hydrate(await api.getAsync());
        } catch {
            // Leave defaults; env fallback still active.
        } finally {
            loading.value = false;
        }
    });
</script>

<style scoped lang="scss">
    .settings-page { display: flex; flex-direction: column; }
    .voice-intro {
        margin: 0;
        padding-left: 20px;
        display: flex;
        flex-direction: column;
        gap: 10px;
        max-width: 60ch;
        color: var(--text-secondary);
        font-size: 0.875rem;
        line-height: 1.5;
    }
</style>
