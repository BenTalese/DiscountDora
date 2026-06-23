<template>
    <div v-if="!currentUser">
        <q-card flat bordered>
            <q-card-section>
                <q-banner class="dora-bg-sunken" dense>Not signed in.</q-banner>
            </q-card-section>
        </q-card>
    </div>

    <div v-else class="column q-gutter-md">
        <!-- Identity ───────────────────────────────────────────────── -->
        <q-card flat bordered>
            <q-card-section>
                <div class="text-h6">Account</div>
                <div class="text-caption dora-text-muted">Your sign-in identity.</div>
            </q-card-section>

            <q-separator />

            <q-card-section>
                <div class="row items-center q-gutter-md">
                    <q-avatar size="60px" color="accent" text-color="dark">
                        {{ initials }}
                    </q-avatar>
                    <div>
                        <div class="text-h6">{{ currentUser.username }}</div>
                        <div class="text-caption dora-text-muted">
                            {{ currentUser.email ?? 'No email on file.' }}
                        </div>
                    </div>
                </div>

                <q-list class="q-mt-md" separator>
                    <q-item>
                        <q-item-section>
                            <q-item-label caption>User ID</q-item-label>
                            <q-item-label class="text-mono">{{ currentUser.user_id }}</q-item-label>
                        </q-item-section>
                    </q-item>
                </q-list>
            </q-card-section>

            <!-- Identity edit forms — lifted from the (misnamed) "Account"
                 card that used to live on Preferences. This is where the
                 user feedback said they belong. -->
            <q-separator />

            <q-card-section class="row q-col-gutter-md items-end">
                <q-input
                    v-model="usernameDraft"
                    label="Username"
                    outlined
                    dense
                    class="col-12 col-sm-6"
                    :disable="saving"
                    autocomplete="username"
                />
                <q-btn
                    color="primary"
                    no-caps
                    :icon="ICONS.save"
                    label="Save username"
                    :loading="savingUsername"
                    :disable="usernameUnchanged || !usernameDraft.trim()"
                    @click="onSaveUsername"
                />
            </q-card-section>

            <q-separator />

            <q-card-section class="row q-col-gutter-md items-end">
                <q-input
                    v-model="emailDraft"
                    label="Email"
                    outlined
                    dense
                    class="col-12 col-sm-6"
                    placeholder="you@example.com"
                    :disable="saving"
                    autocomplete="email"
                />
                <q-btn
                    color="primary"
                    no-caps
                    :icon="ICONS.save"
                    label="Save email"
                    :loading="savingEmail"
                    :disable="emailUnchanged"
                    @click="onSaveEmail"
                />
            </q-card-section>

            <q-separator />

            <q-card-section>
                <div class="text-subtitle2 q-mb-sm">Change password</div>
                <div class="row q-col-gutter-md">
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
                        :rules="[
                            (v) =>
                                !v ||
                                v.length >= 4 ||
                                'At least 4 characters'
                        ]"
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
                        :error-message="
                            confirmPassword.length > 0 && confirmPassword !== newPassword
                                ? 'Passwords do not match'
                                : ''
                        "
                    />
                </div>
                <div class="q-mt-md">
                    <q-btn
                        color="primary"
                        no-caps
                        :icon="ICONS.lock_reset"
                        label="Change password"
                        :loading="savingPassword"
                        :disable="!canChangePassword"
                        @click="onChangePassword"
                    />
                </div>
            </q-card-section>
        </q-card>

        <!-- Sign out — sits on its own, no "Danger zone" theatre (sign-out
             is benign; the action's weight is signalled by the button
             colour, not a section label). -->
        <q-card flat bordered>
            <q-card-section>
                <div class="text-subtitle2 q-mb-sm">Sign out</div>
                <div class="text-caption dora-text-muted q-mb-md">
                    Sign out of this device. Your data stays where it is on the server.
                </div>
                <q-btn
                    color="negative"
                    no-caps
                    :icon="ICONS.logout"
                    label="Sign out"
                    :loading="signingOut"
                    @click="onSignOut"
                />
            </q-card-section>
        </q-card>
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

    // Re-sync drafts when the auth store reloads (e.g. after refresh, login).
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

<style scoped>
    .text-mono {
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        font-size: 0.85em;
    }
</style>
