<template>
    <div class="settings-page">
        <SettingsPageHeader
            title="Push notifications"
            description="Web-push (VAPID) keys the browser needs to sign notification subscriptions. The private key is stored encrypted-at-rest (Fernet, wrapped by DORA_LLM_KEY_ENCRYPTION_KEY)."
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
                    Push notifications stay hidden across the app while
                    both halves aren't configured (R-029 — respect the
                    off-state; hide, don't nag).
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

                <!-- VAPID private key lives encrypted-
                     at-rest on AppSetting.vapid_private_key_encrypted. The
                     read DTO returns only `vapid_private_key_configured`.
                     Write-only input: submit replaces / empty clears. -->
                <SettingsRow
                    :label="privateKeyConfigured ? 'Private key (change)' : 'Private key'"
                    :help="privateKeyConfigured
                        ? 'A private key is stored. Enter a new one to replace it, or use Clear to remove.'
                        : 'Encrypted at rest with DORA_LLM_KEY_ENCRYPTION_KEY. Push sends stay in dry-run until this is set.'"
                    stacked
                >
                    <div class="column q-gutter-sm">
                        <q-input
                            v-model="privateKeyDraft"
                            type="password"
                            outlined dense
                            autogrow
                            :placeholder="privateKeyConfigured
                                ? '••••••••'
                                : 'Paste base64 / PEM private key'"
                            :disable="saving"
                        />
                        <div class="row q-gutter-sm">
                            <BaseButton
                                variant="primary"
                                label="Save"
                                :disable="saving || privateKeyDraft.length === 0"
                                @click="() => onSavePrivateKey(privateKeyDraft)"
                            />
                            <BaseButton
                                v-if="privateKeyConfigured"
                                variant="danger-ghost"
                                label="Clear"
                                :disable="saving"
                                @click="() => onSavePrivateKey('')"
                            />
                        </div>
                    </div>
                </SettingsRow>
            </SettingsSection>
        </template>
    </div>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import BaseButton from 'src/components/BaseButton.vue';
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
    const privateKeyConfigured = ref(false);
    const privateKeyDraft = ref('');

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

    async function onSavePrivateKey(nextValue: string) {
        saving.value = true;
        try {
            const result = await api.updateAsync({ vapid_private_key: nextValue });
            privateKeyConfigured.value = result.vapid_private_key_configured;
            privateKeyDraft.value = '';
            $q.notify({
                type: 'positive', position: 'bottom-right',
                message: nextValue.length === 0
                    ? 'VAPID private key cleared.'
                    : 'VAPID private key saved.',
            });
        } catch (err) {
            $q.notify({
                type: 'negative', position: 'bottom-right',
                message: 'Could not save VAPID private key.',
                caption: toastCaption(err),
            });
        } finally {
            saving.value = false;
        }
    }

    function hydrate(s: AppSettings) {
        saved.vapid_public_key = s.vapid_public_key;
        saved.vapid_subject = s.vapid_subject;
        privateKeyConfigured.value = s.vapid_private_key_configured;
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
            // Leave defaults; admin can retry once DB is reachable.
        } finally {
            loading.value = false;
        }
    });
</script>

<style scoped lang="scss">
    .settings-page { display: flex; flex-direction: column; }
</style>
