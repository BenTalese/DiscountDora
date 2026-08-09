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
            <UserAvatar
                :user-id="currentUser.user_id"
                :has-image="currentUser.has_image"
                size="60px"
                fallback="initials"
                :username="currentUser.username"
                color="accent"
                text-color="dark"
            />
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
            <template #title>Profile picture</template>
            <template #description>
                Shown in the menu bar and anywhere Dora needs to identify you.
            </template>
            <SettingsRow stacked>
                <ImageUploadField
                    :preview-url="profilePreviewUrl"
                    :name="currentUser.username"
                    :alt="`${currentUser.username}'s profile picture`"
                    :can-clear="currentUser.has_image"
                    @pick="onPickImage"
                    @clear="onClearImage"
                />
            </SettingsRow>
        </SettingsSection>

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
                        autocomplete="username"
                    />
                    <BaseButton
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
            <template #description>
                Changing your email requires your current password. We'll
                send a confirmation link to the new address — the change
                only takes effect once you click it. A heads-up notice
                goes to your current address too.
            </template>
            <SettingsRow stacked>
                <div class="row q-col-gutter-sm items-end">
                    <q-input
                        v-model="emailDraft"
                        outlined
                        dense
                        placeholder="you@example.com"
                        class="col-12 col-sm-5"
                        autocomplete="email"
                    />
                    <q-input
                        v-model="emailChangePassword"
                        outlined
                        dense
                        type="password"
                        label="Current password"
                        class="col-12 col-sm-4"
                        :disable="emailUnchanged"
                        autocomplete="current-password"
                    />
                    <BaseButton
                        :icon="ICONS.save"
                        label="Send confirmation"
                        :loading="savingEmail"
                        :disable="!canRequestEmailChange"
                        @click="onRequestEmailChange"
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
                        hint="At least 8 characters — a passphrase works well."
                        :rules="[(v) => !v || v.length >= 8 || 'At least 8 characters']"
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
                    <BaseButton
                        :icon="ICONS.lock_reset"
                        label="Change password"
                        :loading="savingPassword"
                        :disable="!canChangePassword"
                        @click="onChangePassword"
                    />
                </div>
            </SettingsRow>
        </SettingsSection>
    </div>
</template>

<script lang="ts" setup>
    import BaseButton from 'src/components/BaseButton.vue';
    import { ICONS } from 'src/style/icons';
    import { storeToRefs } from 'pinia';
    import { useQuasar } from 'quasar';
    import { useAuthStore } from 'src/stores/authStore';
    import { computed, ref, watch } from 'vue';
    import { toastCaption } from 'src/services/errorHandling/apiErrorHandler';
    import SettingsSection from 'src/components/settings/SettingsSection.vue';
    import SettingsRow from 'src/components/settings/SettingsRow.vue';
    import SettingsPageHeader from 'src/components/settings/SettingsPageHeader.vue';
    import UserAvatar from 'src/components/UserAvatar.vue';
    import ImageUploadField from 'src/components/ImageUploadField.vue';
    import { userImageUrl } from 'src/services/api/authApiService';
    import { useUnsavedChangesGuard } from 'src/composables/useUnsavedChangesGuard';

    const $q = useQuasar();
    const authStore = useAuthStore();
    const { currentUser } = storeToRefs(authStore);

    // Profile-picture preview: the live bytes URL (cache-busted by the store's
    // image-version counter) when one exists, else null so ImageUploadField
    // renders its initial placeholder.
    const profilePreviewUrl = computed(() =>
        currentUser.value?.has_image
            ? userImageUrl(currentUser.value.user_id, authStore.imageVersionOf(currentUser.value.user_id))
            : null
    );

    async function onPickImage(dataUrl: string) {
        try {
            await authStore.updateMeAsync({ image: dataUrl });
            notifySuccess('Profile picture updated.');
        } catch (err) {
            notifyError('Could not update your profile picture.', err);
        }
    }

    async function onClearImage() {
        try {
            await authStore.updateMeAsync({ clear_image: true });
            notifySuccess('Profile picture removed.');
        } catch (err) {
            notifyError('Could not remove your profile picture.', err);
        }
    }

    const usernameDraft = ref(currentUser.value?.username ?? '');
    const emailDraft = ref(currentUser.value?.email ?? '');
    // proof-of-possession for the verified change-email flow.
    // Kept separate from the change-password input below so the two
    // forms don't accidentally share state.
    const emailChangePassword = ref('');
    const currentPassword = ref('');
    const newPassword = ref('');
    const confirmPassword = ref('');

    const savingEmail = ref(false);
    const savingUsername = ref(false);
    const savingPassword = ref(false);

    watch(currentUser, (u) => {
        if (!u) return;
        usernameDraft.value = u.username;
        emailDraft.value = u.email ?? '';
    });

    const usernameUnchanged = computed(
        () => (currentUser.value?.username ?? '') === usernameDraft.value
    );
    const emailUnchanged = computed(
        () => (currentUser.value?.email ?? '') === emailDraft.value
    );
    // R-020 — deferred-save surface, must wire the unsaved-changes guard.
    // Only the two draft fields (username + email) drive the predicate:
    // profile picture saves immediately on pick/clear (no draft window) and
    // password fields are the rule's documented "password field" exclusion
    // (browsers expect typed passwords to be lost on nav).
    useUnsavedChangesGuard(computed(
        () => !usernameUnchanged.value || !emailUnchanged.value,
    ));
    const canChangePassword = computed(
        () =>
            currentPassword.value.length > 0 &&
            newPassword.value.length >= 4 &&
            confirmPassword.value === newPassword.value
    );
    const canRequestEmailChange = computed(
        () =>
            !emailUnchanged.value &&
            emailDraft.value.trim().length > 0 &&
            emailChangePassword.value.length > 0,
    );

    function notifySuccess(message: string) {
        $q.notify({ type: 'positive', position: 'bottom-right', message });
    }
    function notifyError(message: string, err?: unknown) {
        $q.notify({
            type: 'negative',
            position: 'bottom-right',
            message,
            caption: toastCaption(err)
        });
    }

    async function onRequestEmailChange() {
        if (!canRequestEmailChange.value) return;
        savingEmail.value = true;
        try {
            await authStore.requestEmailChangeAsync(
                emailDraft.value.trim(),
                emailChangePassword.value,
            );
            notifySuccess(
                'Confirmation link sent. Check your new inbox to finish the change.',
            );
            emailChangePassword.value = '';
            // Leave emailDraft as the entered value so the UI shows
            // what's pending; the displayed email above (currentUser)
            // doesn't update until the user clicks the confirmation
            // link and the next /auth/me refresh sees the new value.
        } catch (err) {
            notifyError('Could not request email change.', err);
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
