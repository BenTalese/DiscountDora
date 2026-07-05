<template>
    <div class="settings-page">
        <SettingsPageHeader
            title="Push notifications"
            description="Web-push (VAPID) keys the browser needs to sign notification subscriptions. The private key stays in the environment until encrypted-in-database storage lands."
            :icon="ICONS.notifications_active"
        />

        <q-banner v-if="!isAdmin" class="dora-bg-negative-soft text-negative" dense rounded>
            You don't have admin permissions to view this page.
        </q-banner>

        <template v-else-if="!loading">
            <SettingsSection>
                <template #title>VAPID</template>
                <template #description>
                    Both halves must be set for real pushes to leave the box.
                    Users see the Push toggle in Preferences as
                    reveal-and-disabled while push isn't fully configured.
                </template>

                <SettingsRow label="Public key" stacked>
                    <q-input
                        v-model="draft.vapid_public_key"
                        outlined dense clearable
                        placeholder="base64url-encoded uncompressed P-256 public key"
                        :disable="saving"
                        @blur="() => onSaveField('vapid_public_key')"
                    />
                </SettingsRow>

                <SettingsRow label="Subject" stacked>
                    <q-input
                        v-model="draft.vapid_subject"
                        outlined dense clearable
                        placeholder="mailto:admin@example.com"
                        :disable="saving"
                        @blur="() => onSaveField('vapid_subject')"
                    />
                </SettingsRow>

                <!-- R-014 reveal-and-disable: the private key stays in env
                     until FU-333 Bucket C lands. -->
                <SettingsRow
                    label="Private key"
                    help="Set DORA_VAPID_PRIVATE_KEY in the environment. Encrypted-in-database storage lands with FU-333 Bucket C — this input will unlock then."
                    stacked
                >
                    <q-input
                        model-value=""
                        outlined dense disable
                        placeholder="Managed via DORA_VAPID_PRIVATE_KEY environment variable"
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

    type PushField = 'vapid_public_key' | 'vapid_subject';

    const $q = useQuasar();
    const { isAdmin } = storeToRefs(useAuthStore());
    const api = new AppSettingsApiService();

    const loading = ref(true);
    const saving = ref(false);
    const saved = reactive({
        vapid_public_key: '',
        vapid_subject: 'mailto:admin@dora.local',
    });
    const draft = reactive({ ...saved });

    function resetDrafts() {
        Object.assign(draft, saved);
    }

    async function onSaveField(field: PushField) {
        const value = (draft[field] ?? '').trim();
        if (value === saved[field]) return;
        saving.value = true;
        try {
            const result = await api.updateAsync({ [field]: value });
            saved[field] = result[field];
            resetDrafts();
            $q.notify({
                type: 'positive', position: 'bottom-right',
                message: 'Push settings saved.',
            });
        } catch (err) {
            resetDrafts();
            $q.notify({
                type: 'negative', position: 'bottom-right',
                message: 'Could not save push settings.',
                caption: toastCaption(err),
            });
        } finally {
            saving.value = false;
        }
    }

    function hydrate(s: AppSettings) {
        saved.vapid_public_key = s.vapid_public_key;
        saved.vapid_subject = s.vapid_subject;
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
