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
                        @update:model-value="() => onSaveField('email_enabled')"
                    />
                </SettingsRow>
            </SettingsSection>

            <SettingsSection>
                <template #title>Setting up Gmail</template>
                <template #description>
                    Google no longer accepts your regular login here — you
                    need an <strong>App Password</strong> (16 characters)
                    tied to 2-Step Verification. Once you have one, fill in
                    the SMTP fields below.
                </template>

                <ol class="gmail-steps">
                    <li>
                        Turn on <strong>2-Step Verification</strong> on your
                        Google Account (Security → 2-Step Verification).
                        Required — App Passwords can't be created without it.
                    </li>
                    <li>
                        Open the App Passwords page, create one named
                        <em>&ldquo;Dora&rdquo;</em>, and copy the
                        16-character password Google shows you (spaces don't
                        matter).
                    </li>
                    <li>
                        Fill in the SMTP fields below with
                        <code>smtp.gmail.com</code>, port <code>587</code>,
                        <strong>Use TLS</strong> on, your full Gmail address
                        as <em>Username</em> and <em>From address</em>, and
                        paste the App Password as the SMTP password.
                    </li>
                    <li>
                        Turn <strong>Email enabled</strong> on and try a
                        password reset (or any email-emitting flow) to
                        confirm it works.
                    </li>
                </ol>

                <p class="gmail-note">
                    <strong>Gotchas.</strong> If sends fail with
                    <code>535-5.7.8 Username and Password not accepted</code>
                    you've pasted your account password instead of the App
                    Password. Free Gmail caps at ~500 recipients/day; fine
                    for a personal self-host, not a public multi-user
                    install — for that, use a transactional provider
                    (Postmark, Resend, SES).
                </p>

                <div class="gmail-cta">
                    <BaseButton
                        variant="secondary"
                        :icon="ICONS.google"
                        label="Create Gmail App Password"
                        href="https://myaccount.google.com/apppasswords"
                        target="_blank"
                    />
                </div>
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
                        @blur="() => onSaveField('smtp_port')"
                    />
                </SettingsRow>

                <SettingsRow label="Username" stacked>
                    <q-input
                        v-model="draft.smtp_username"
                        outlined dense clearable
                        placeholder="dora@example.com"
                        @blur="() => onSaveField('smtp_username')"
                    />
                </SettingsRow>

                <SettingsRow label="From address" stacked>
                    <q-input
                        v-model="draft.smtp_from"
                        outlined dense clearable
                        placeholder="Leave blank to use username"
                        @blur="() => onSaveField('smtp_from')"
                    />
                </SettingsRow>

                <SettingsRow label="Use TLS">
                    <q-toggle
                        v-model="draft.smtp_use_tls"
                        @update:model-value="() => onSaveField('smtp_use_tls')"
                    />
                </SettingsRow>

                <!-- SMTP password lives encrypted-at-rest
                     on AppSetting.smtp_password_encrypted. The response DTO
                     never returns the ciphertext; we know only whether one
                     is stored (`smtp_password_configured`). The input is
                     write-only: submitting a value replaces the stored
                     ciphertext; empty submit clears it. -->
                <SettingsRow
                    :label="passwordConfigured ? 'Password (change)' : 'Password'"
                    :help="passwordConfigured
                        ? 'A password is stored. Enter a new one to replace it, or use Clear to remove.'
                        : 'Encrypted at rest with DORA_SECRET_ENCRYPTION_KEY. Leave blank to keep the sender in dry-run mode.'"
                    stacked
                >
                    <div class="row items-center q-gutter-sm">
                        <q-input
                            v-model="passwordDraft"
                            type="password"
                            outlined dense
                            style="flex: 1 1 auto"
                            :placeholder="passwordConfigured ? '••••••••' : 'Enter SMTP password'"
                        />
                        <BaseButton
                            variant="primary"
                            label="Save"
                            :disable="saving || passwordDraft.length === 0"
                            @click="() => onSavePassword(passwordDraft)"
                        />
                        <BaseButton
                            v-if="passwordConfigured"
                            variant="danger-ghost"
                            label="Clear"
                            :disable="saving"
                            @click="() => onSavePassword('')"
                        />
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
    // Bucket-C secret is write-only — the server never returns the plaintext,
    // just a `_configured` bool. We hold the draft locally, submit explicitly.
    const passwordConfigured = ref(false);
    const passwordDraft = ref('');

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

    async function onSavePassword(nextValue: string) {
        saving.value = true;
        try {
            const result = await api.updateAsync({ smtp_password: nextValue });
            passwordConfigured.value = result.smtp_password_configured;
            passwordDraft.value = '';
            $q.notify({
                type: 'positive', position: 'bottom-right',
                message: nextValue.length === 0
                    ? 'SMTP password cleared.'
                    : 'SMTP password saved.',
            });
        } catch (err) {
            $q.notify({
                type: 'negative', position: 'bottom-right',
                message: 'Could not save SMTP password.',
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
        passwordConfigured.value = s.smtp_password_configured;
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
            // Leave defaults; admin can retry once the DB is reachable.
        } finally {
            loading.value = false;
        }
    });
</script>

<style scoped lang="scss">
    .settings-page { display: flex; flex-direction: column; }
    .gmail-steps {
        margin: 0;
        padding-left: 20px;
        display: flex;
        flex-direction: column;
        gap: 8px;
        color: var(--text-primary);
        font-size: 0.9375rem;
        line-height: 1.45;
        max-width: 68ch;
    }
    .gmail-steps code {
        font-size: 0.875em;
        padding: 1px 6px;
        border-radius: 4px;
        background: var(--surface-sunken);
        color: var(--text-primary);
    }
    .gmail-note {
        margin: 0;
        max-width: 68ch;
        color: var(--text-secondary);
        font-size: 0.875rem;
        line-height: 1.5;
    }
    .gmail-note code {
        font-size: 0.875em;
        padding: 1px 6px;
        border-radius: 4px;
        background: var(--surface-sunken);
        color: var(--text-primary);
    }
    .gmail-cta { display: flex; }
</style>
