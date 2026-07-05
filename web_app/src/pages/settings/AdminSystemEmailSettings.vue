<template>
    <div class="settings-page">
        <SettingsPageHeader
            title="Email"
            description="SMTP configuration for transactional emails (verification, password reset, alerts digest). The install-wide switch reveals or hides email-related surfaces across the app."
            :icon="ICONS.mark_email_read"
        />

        <q-banner v-if="!isAdmin" class="dora-bg-negative-soft text-negative" dense rounded>
            You don't have admin permissions to view this page.
        </q-banner>

        <template v-else-if="!loading">
            <SettingsSection>
                <template #title>Email subsystem</template>
                <template #description>
                    Turn this off if the install should never send email. When
                    off, the alerts digest, verification and reset flows fall
                    back to logging the link server-side.
                </template>

                <SettingsRow label="Email enabled">
                    <q-toggle
                        v-model="draft.email_enabled"
                        :disable="saving"
                        @update:model-value="() => onSaveField('email_enabled')"
                    />
                </SettingsRow>
            </SettingsSection>

            <SettingsSection>
                <template #title>SMTP</template>
                <template #description>
                    Reached via TLS when the toggle below is on. Username
                    identifies the mailbox transactional emails are sent from;
                    leave blank to keep the sender in dry-run mode (links
                    logged, no real send).
                </template>

                <SettingsRow label="Host" stacked>
                    <q-input
                        v-model="draft.smtp_host"
                        outlined dense clearable
                        placeholder="smtp.gmail.com"
                        :disable="saving"
                        @blur="() => onSaveField('smtp_host')"
                    />
                </SettingsRow>

                <SettingsRow label="Port">
                    <q-input
                        v-model.number="draft.smtp_port"
                        type="number"
                        outlined dense
                        style="max-width: 140px"
                        :min="1"
                        :max="65535"
                        :disable="saving"
                        @blur="() => onSaveField('smtp_port')"
                    />
                </SettingsRow>

                <SettingsRow label="Username" stacked>
                    <q-input
                        v-model="draft.smtp_username"
                        outlined dense clearable
                        placeholder="dora@example.com"
                        :disable="saving"
                        @blur="() => onSaveField('smtp_username')"
                    />
                </SettingsRow>

                <SettingsRow label="From address" stacked>
                    <q-input
                        v-model="draft.smtp_from"
                        outlined dense clearable
                        placeholder="Leave blank to use username"
                        :disable="saving"
                        @blur="() => onSaveField('smtp_from')"
                    />
                </SettingsRow>

                <SettingsRow label="Use TLS">
                    <q-toggle
                        v-model="draft.smtp_use_tls"
                        :disable="saving"
                        @update:model-value="() => onSaveField('smtp_use_tls')"
                    />
                </SettingsRow>

                <!-- R-014 reveal-and-disable: the SMTP password stays in
                     env until FU-333 Bucket C (encrypted-in-DB storage)
                     lands. Show the field so an operator sees where it
                     will live; disable it with the reason so nobody
                     wastes time typing. -->
                <SettingsRow
                    label="Password"
                    help="Set DORA_SMTP_PASSWORD in the environment. Encrypted-in-database storage lands with FU-333 Bucket C — this input will unlock then."
                    stacked
                >
                    <q-input
                        model-value=""
                        outlined dense disable
                        placeholder="Managed via DORA_SMTP_PASSWORD environment variable"
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

    type EmailField = 'email_enabled' | 'smtp_host' | 'smtp_port'
        | 'smtp_username' | 'smtp_from' | 'smtp_use_tls';

    const $q = useQuasar();
    const { isAdmin } = storeToRefs(useAuthStore());
    const api = new AppSettingsApiService();

    const loading = ref(true);
    const saving = ref(false);
    const saved = reactive({
        email_enabled: false,
        smtp_host: '',
        smtp_port: 587,
        smtp_username: '',
        smtp_from: '',
        smtp_use_tls: true,
    });
    const draft = reactive({ ...saved });

    function resetDrafts() {
        Object.assign(draft, saved);
    }

    async function onSaveField(field: EmailField) {
        const value = draft[field];
        if (value === saved[field]) return;
        saving.value = true;
        try {
            const result = await api.updateAsync({ [field]: value });
            (saved as Record<EmailField, unknown>)[field] = result[field];
            resetDrafts();
            $q.notify({
                type: 'positive', position: 'bottom-right',
                message: 'Email settings saved.',
            });
        } catch (err) {
            resetDrafts();
            $q.notify({
                type: 'negative', position: 'bottom-right',
                message: 'Could not save email settings.',
                caption: toastCaption(err),
            });
        } finally {
            saving.value = false;
        }
    }

    function hydrate(s: AppSettings) {
        saved.email_enabled = s.email_enabled;
        saved.smtp_host = s.smtp_host;
        saved.smtp_port = s.smtp_port;
        saved.smtp_username = s.smtp_username;
        saved.smtp_from = s.smtp_from;
        saved.smtp_use_tls = s.smtp_use_tls;
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
            // Leave defaults; the resolver's env fallback is still active.
        } finally {
            loading.value = false;
        }
    });
</script>

<style scoped lang="scss">
    .settings-page { display: flex; flex-direction: column; }
</style>
