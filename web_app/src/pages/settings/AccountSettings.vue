<template>
    <div v-if="!currentUser">
        <q-banner class="dora-bg-sunken" dense>Not signed in.</q-banner>
    </div>

    <div v-else class="settings-page">
        <SettingsPageHeader
            title="Account"
            description="Your sign-in identity."
        />

        <section class="account-identity">
            <q-avatar size="60px" color="accent" text-color="dark">
                {{ initials }}
            </q-avatar>
            <div class="account-identity__text">
                <div class="account-identity__name">{{ currentUser.username }}</div>
                <div class="account-identity__email dora-text-muted">
                    {{ currentUser.email ?? 'No email on file.' }}
                </div>
                <div class="account-identity__userid dora-text-muted">
                    <span class="text-mono">{{ currentUser.user_id }}</span>
                </div>
            </div>
        </section>

        <hr class="settings-divider" />

        <SettingsSection>
            <template #title>Username</template>
            <SettingsRow stacked>
                <div class="row q-col-gutter-sm items-end">
                    <q-input
                        v-model="usernameDraft"
                        outlined
                        dense
                        class="col-12 col-sm-8"
                        :disable="saving"
                        autocomplete="username"
                    />
                    <q-btn
                        color="primary"
                        unelevated
                        no-caps
                        :icon="ICONS.save"
                        label="Save"
                        :loading="savingUsername"
                        :disable="usernameUnchanged || !usernameDraft.trim()"
                        @click="onSaveUsername"
                    />
                </div>
            </SettingsRow>
        </SettingsSection>

        <hr class="settings-divider" />

        <SettingsSection>
            <template #title>Email</template>
            <SettingsRow stacked>
                <div class="row q-col-gutter-sm items-end">
                    <q-input
                        v-model="emailDraft"
                        outlined
                        dense
                        placeholder="you@example.com"
                        class="col-12 col-sm-8"
                        :disable="saving"
                        autocomplete="email"
                    />
                    <q-btn
                        color="primary"
                        unelevated
                        no-caps
                        :icon="ICONS.save"
                        label="Save"
                        :loading="savingEmail"
                        :disable="emailUnchanged"
                        @click="onSaveEmail"
                    />
                </div>
            </SettingsRow>
        </SettingsSection>

        <hr class="settings-divider" />

        <SettingsSection>
            <template #title>Change password</template>

            <SettingsRow stacked>
                <div class="row q-col-gutter-sm">
                    <q-input
                        v-model="currentPassword"
                        label="Current password"
                        outlined
                        dense
                        type="password"
                        class="col-12 col-sm-4"
                        autocomplete="current-password"
                    />
                    <q-input
                        v-model="newPassword"
                        label="New password"
                        outlined
                        dense
                        type="password"
                        class="col-12 col-sm-4"
                        autocomplete="new-password"
                        :rules="[(v) => !v || v.length >= 4 || 'At least 4 characters']"
                    />
                    <q-input
                        v-model="confirmPassword"
                        label="Confirm new password"
                        outlined
                        dense
                        type="password"
                        class="col-12 col-sm-4"
                        autocomplete="new-password"
                        :error="confirmPassword.length > 0 && confirmPassword !== newPassword"
                        :error-message="confirmPassword.length > 0 && confirmPassword !== newPassword
                            ? 'Passwords do not match' : ''"
                    />
                </div>
                <div class="q-mt-sm">
                    <q-btn
                        color="primary"
                        unelevated
                        no-caps
                        :icon="ICONS.lock_reset"
                        label="Change password"
                        :loading="savingPassword"
                        :disable="!canChangePassword"
                        @click="onChangePassword"
                    />
                </div>
            </SettingsRow>
        </SettingsSection>

        <hr class="settings-divider" />

        <SettingsSection>
            <template #title>Sign out</template>
            <template #description>
                Sign out of this device. Your data stays where it is on the
                server.
            </template>

            <SettingsRow stacked>
                <div>
                    <q-btn
                        color="negative"
                        unelevated
                        no-caps
                        :icon="ICONS.logout"
                        label="Sign out"
                        :loading="signingOut"
                        @click="onSignOut"
                    />
                </div>
            </SettingsRow>
        </SettingsSection>
    </div>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import { storeToRefs } from 'pinia';
    import { useQuasar } from 'quasar';
    import { useAuthStore } from 'src/stores/authStore';
    import { computed, ref, watch } from 'vue';
    import { useRouter } from 'vue-router';
    import { describeApiError } from 'src/services/errorHandling/apiErrorHandler';
    import SettingsSection from 'src/components/settings/SettingsSection.vue';
    import SettingsRow from 'src/components/settings/SettingsRow.vue';
    import SettingsPageHeader from 'src/components/settings/SettingsPageHeader.vue';

    const $q = useQuasar();
    const router = useRouter();
    const authStore = useAuthStore();
    const { currentUser } = storeToRefs(authStore);

    const usernameDraft = ref(currentUser.value?.username ?? '');
    const emailDraft = ref(currentUser.value?.email ?? '');
    const currentPassword = ref('');
    const newPassword = ref('');
    const confirmPassword = ref('');

    const saving = ref(false);
    const savingEmail = ref(false);
    const savingUsername = ref(false);
    const savingPassword = ref(false);
    const signingOut = ref(false);

    watch(currentUser, (u) => {
        if (!u) return;
        usernameDraft.value = u.username;
        emailDraft.value = u.email ?? '';
    });

    const initials = computed(() => {
        const name = currentUser.value?.username ?? '';
        return name.length > 0 ? name.charAt(0).toUpperCase() : '?';
    });

    const usernameUnchanged = computed(
        () => (currentUser.value?.username ?? '') === usernameDraft.value
    );
    const emailUnchanged = computed(
        () => (currentUser.value?.email ?? '') === emailDraft.value
    );
    const canChangePassword = computed(
        () =>
            currentPassword.value.length > 0 &&
            newPassword.value.length >= 4 &&
            confirmPassword.value === newPassword.value
    );

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

    async function onSaveEmail() {
        savingEmail.value = true;
        try {
            await authStore.updateMeAsync({
                email: emailDraft.value.trim() === '' ? null : emailDraft.value.trim()
            });
            notifySuccess('Email saved.');
        } catch (err) {
            notifyError('Could not save email.', err);
        } finally {
            savingEmail.value = false;
        }
    }

    async function onSaveUsername() {
        const next = usernameDraft.value.trim();
        if (!next) return;
        savingUsername.value = true;
        try {
            await authStore.updateMeAsync({ username: next });
            notifySuccess('Username saved.');
        } catch (err) {
            notifyError('Could not save username.', err);
        } finally {
            savingUsername.value = false;
        }
    }

    async function onChangePassword() {
        if (!canChangePassword.value) return;
        savingPassword.value = true;
        try {
            await authStore.changePasswordAsync({
                current_password: currentPassword.value,
                new_password: newPassword.value
            });
            notifySuccess('Password changed.');
            currentPassword.value = '';
            newPassword.value = '';
            confirmPassword.value = '';
        } catch (err) {
            notifyError('Could not change password.', err);
        } finally {
            savingPassword.value = false;
        }
    }

    async function onSignOut() {
        signingOut.value = true;
        try {
            await authStore.logoutAsync();
            void router.push('/login');
        } finally {
            signingOut.value = false;
        }
    }
</script>

<style scoped lang="scss">
    .settings-page { display: flex; flex-direction: column; }
    .settings-divider {
        border: 0;
        height: 1px;
        background: color-mix(in srgb, var(--text-primary) 8%, transparent);
        margin: 8px 0;
    }
    .account-identity {
        display: flex;
        align-items: center;
        gap: 16px;
        padding: 4px 0 12px;
    }
    .account-identity__text {
        display: flex;
        flex-direction: column;
        gap: 2px;
    }
    .account-identity__name {
        font-size: 1.125rem;
        font-weight: 700;
        color: var(--text-primary);
    }
    .account-identity__email {
        font-size: 0.875rem;
    }
    .account-identity__userid {
        font-size: 0.75rem;
    }
    .text-mono {
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        font-size: 0.85em;
    }
</style>
