<template>
    <div class="settings-page">
        <SettingsPageHeader
            title="Voice (Piper TTS)"
            description="Install-wide paths to the Piper binary and its voice bundle. Each user's chosen voice lives on their own Voice settings page and layers on top of this."
            :icon="ICONS.record_voice_over"
        />

        <q-banner v-if="!isAdmin" class="dora-bg-negative-soft text-negative" dense rounded>
            You don't have admin permissions to view this page.
        </q-banner>

        <template v-else-if="!loading">
            <SettingsSection>
                <template #title>Piper binary</template>
                <template #description>
                    Path to the piper executable. Leave blank to search
                    <code>$PATH</code>. The desktop bundle resolves this
                    automatically.
                </template>

                <SettingsRow label="Executable" stacked>
                    <q-input
                        v-model="draft.piper_bin"
                        outlined dense clearable
                        placeholder="/usr/local/bin/piper"
                        :disable="saving"
                        @blur="() => onSaveField('piper_bin')"
                    />
                </SettingsRow>
            </SettingsSection>

            <SettingsSection>
                <template #title>Voices</template>
                <template #description>
                    The bundle directory holds pre-shipped <code>.onnx</code>
                    voice models. Legacy single-file voice override wins over
                    the catalog when set.
                </template>

                <SettingsRow label="Bundled voice directory" stacked>
                    <q-input
                        v-model="draft.piper_bundled_voice_dir"
                        outlined dense clearable
                        placeholder="/opt/dora/voices"
                        :disable="saving"
                        @blur="() => onSaveField('piper_bundled_voice_dir')"
                    />
                </SettingsRow>

                <SettingsRow
                    label="Legacy voice override"
                    help="Absolute path to a single .onnx voice file. When set and valid, it wins over every other resolution path. Prefer the bundle directory unless migrating from an older install."
                    stacked
                >
                    <q-input
                        v-model="draft.piper_voice"
                        outlined dense clearable
                        placeholder="/opt/dora/voices/en_US-amy-medium.onnx"
                        :disable="saving"
                        @blur="() => onSaveField('piper_voice')"
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

    type VoiceField = 'piper_bin' | 'piper_bundled_voice_dir' | 'piper_voice';

    const $q = useQuasar();
    const { isAdmin } = storeToRefs(useAuthStore());
    const api = new AppSettingsApiService();

    const loading = ref(true);
    const saving = ref(false);
    const saved = reactive({
        piper_bin: '',
        piper_bundled_voice_dir: '',
        piper_voice: '',
    });
    const draft = reactive({ ...saved });

    function resetDrafts() {
        Object.assign(draft, saved);
    }

    async function onSaveField(field: VoiceField) {
        const value = (draft[field] ?? '').trim();
        if (value === saved[field]) return;
        saving.value = true;
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
        } finally {
            saving.value = false;
        }
    }

    function hydrate(s: AppSettings) {
        saved.piper_bin = s.piper_bin;
        saved.piper_bundled_voice_dir = s.piper_bundled_voice_dir;
        saved.piper_voice = s.piper_voice;
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
</style>
