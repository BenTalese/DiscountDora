<template>
    <div v-if="!currentUser">
        <q-card flat bordered>
            <q-card-section>
                <q-banner class="bg-grey-2" dense>Not signed in.</q-banner>
            </q-card-section>
        </q-card>
    </div>

    <div v-else class="column q-gutter-md">
        <!-- Appearance ─────────────────────────────────────────────── -->
        <q-card flat bordered>
            <q-card-section>
                <div class="text-h6">Appearance</div>
                <div class="text-caption text-grey">
                    Theme, font, and text size for this account.
                </div>
            </q-card-section>
            <q-separator />

            <q-card-section class="row q-col-gutter-md items-center">
                <div class="col-12 col-sm-4 text-subtitle2">Theme</div>
                <div class="col-12 col-sm-8">
                    <q-btn-toggle
                        v-model="themeDraft"
                        no-caps
                        spread
                        toggle-color="primary"
                        :options="[
                            { label: 'System', value: 'system', slot: 'system' },
                            { label: 'Light', value: 'light', slot: 'light' },
                            { label: 'Dark', value: 'dark', slot: 'dark' }
                        ]"
                        @update:model-value="onThemeChange"
                    >
                        <template #system>
                            <q-icon name="brightness_auto" class="q-mr-xs" />
                            System
                        </template>
                        <template #light>
                            <q-icon name="light_mode" class="q-mr-xs" />
                            Light
                        </template>
                        <template #dark>
                            <q-icon name="dark_mode" class="q-mr-xs" />
                            Dark
                        </template>
                    </q-btn-toggle>
                    <div class="text-caption text-grey q-mt-xs">
                        System follows your browser's
                        <code>prefers-color-scheme</code>.
                    </div>
                </div>
            </q-card-section>

            <q-separator />

            <q-card-section class="row q-col-gutter-md items-center">
                <div class="col-12 col-sm-4 text-subtitle2">Font family</div>
                <div class="col-12 col-sm-8">
                    <q-btn-toggle
                        v-model="fontFamilyDraft"
                        no-caps
                        spread
                        toggle-color="primary"
                        :options="[
                            { label: 'Default', value: 'default' },
                            { label: 'Urbanist', value: 'urbanist' },
                            { label: 'Nunito', value: 'nunito' },
                            { label: 'Inter', value: 'inter' },
                            { label: 'Lexend', value: 'lexend' },
                            { label: 'Plus Jakarta Sans', value: 'plus_jakarta_sans' }
                        ]"
                        @update:model-value="onFontFamilyChange"
                    />
                </div>
            </q-card-section>

            <q-separator />

            <q-card-section class="row q-col-gutter-md items-center">
                <div class="col-12 col-sm-4 text-subtitle2">Text size</div>
                <div class="col-12 col-sm-8">
                    <q-btn-toggle
                        v-model="fontSizeDraft"
                        no-caps
                        spread
                        toggle-color="primary"
                        :options="[
                            { label: 'Small', value: 'sm' },
                            { label: 'Medium', value: 'md' },
                            { label: 'Large', value: 'lg' }
                        ]"
                        @update:model-value="onFontSizeChange"
                    />
                </div>
            </q-card-section>
        </q-card>

        <!-- Weekly deals email ─────────────────────────────────────── -->
        <q-card flat bordered>
            <q-card-section>
                <div class="text-h6">Weekly deals email</div>
                <div class="text-caption text-grey">
                    Discount Dora can email you a digest of the latest deals
                    once a week.
                </div>
            </q-card-section>
            <q-separator />

            <q-card-section>
                <q-toggle
                    :model-value="currentUser.deals_email_enabled"
                    label="Subscribe me to the weekly deals email"
                    :disable="saving"
                    @update:model-value="onDealsEnabledChange"
                />
            </q-card-section>

            <q-card-section
                v-if="currentUser.deals_email_enabled"
                class="row q-col-gutter-md items-center"
            >
                <div class="col-12 col-sm-4 text-subtitle2">Send on</div>
                <div class="col-12 col-sm-8">
                    <q-select
                        v-model="sendDealsOnDay"
                        :options="dayOptions"
                        option-value="value"
                        option-label="label"
                        emit-value
                        map-options
                        outlined
                        dense
                        style="max-width: 260px"
                        :disable="saving"
                        @update:model-value="onSendDealsOnDayChange"
                    />
                </div>
            </q-card-section>

            <q-card-section v-if="currentUser.deals_email_enabled">
                <q-toggle
                    :model-value="currentUser.deals_email_compact"
                    label="Compact format (one-line per deal)"
                    :disable="saving"
                    @update:model-value="onDealsCompactChange"
                />
            </q-card-section>
        </q-card>

        <!-- Account ────────────────────────────────────────────────── -->
        <q-card flat bordered>
            <q-card-section>
                <div class="text-h6">Account</div>
                <div class="text-caption text-grey">
                    Update your username, email, or password.
                </div>
            </q-card-section>
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
                    icon="save"
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
                    icon="save"
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
                        icon="lock_reset"
                        label="Change password"
                        :loading="savingPassword"
                        :disable="!canChangePassword"
                        @click="onChangePassword"
                    />
                </div>
            </q-card-section>
        </q-card>
    </div>
</template>

<script lang="ts" setup>
    import { storeToRefs } from 'pinia';
    import { useQuasar } from 'quasar';
    import type {
        FontFamilyPreference,
        FontSizePreference,
        ThemePreference
    } from 'src/models/auth';
    import { useAuthStore } from 'src/stores/authStore';
    import { computed, ref, watch } from 'vue';

    const $q = useQuasar();
    const authStore = useAuthStore();
    const { currentUser } = storeToRefs(authStore);

    const dayOptions = [
        { value: 0, label: 'Monday' },
        { value: 1, label: 'Tuesday' },
        { value: 2, label: 'Wednesday' },
        { value: 3, label: 'Thursday' },
        { value: 4, label: 'Friday' },
        { value: 5, label: 'Saturday' },
        { value: 6, label: 'Sunday' }
    ];

    // Drafts for fields that need an explicit save (vs. instant-toggle).
    const usernameDraft = ref(currentUser.value?.username ?? '');
    const emailDraft = ref(currentUser.value?.email ?? '');
    const sendDealsOnDay = ref<number>(currentUser.value?.send_deals_on_day ?? 0);
    const themeDraft = ref<ThemePreference>(currentUser.value?.theme ?? 'system');
    const fontFamilyDraft = ref<FontFamilyPreference>(
        currentUser.value?.font_family ?? 'default'
    );
    const fontSizeDraft = ref<FontSizePreference>(currentUser.value?.font_size ?? 'md');

    const currentPassword = ref('');
    const newPassword = ref('');
    const confirmPassword = ref('');

    const saving = ref(false);
    const savingEmail = ref(false);
    const savingUsername = ref(false);
    const savingPassword = ref(false);

    // Re-sync drafts when the auth store reloads (e.g. after refresh, login).
    watch(currentUser, (u) => {
        if (!u) return;
        usernameDraft.value = u.username;
        emailDraft.value = u.email ?? '';
        sendDealsOnDay.value = u.send_deals_on_day ?? 0;
        themeDraft.value = u.theme;
        fontFamilyDraft.value = u.font_family;
        fontSizeDraft.value = u.font_size;
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
            caption: err ? String(err) : undefined
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

    async function onThemeChange(value: ThemePreference) {
        const previous = currentUser.value?.theme ?? 'system';
        const result = await update('Theme updated.', () =>
            authStore.updateMeAsync({ theme: value })
        );
        if (result === null) themeDraft.value = previous;
    }

    async function onFontFamilyChange(value: FontFamilyPreference) {
        const previous = currentUser.value?.font_family ?? 'default';
        const result = await update('Font updated.', () =>
            authStore.updateMeAsync({ font_family: value })
        );
        if (result === null) fontFamilyDraft.value = previous;
    }

    async function onFontSizeChange(value: FontSizePreference) {
        const previous = currentUser.value?.font_size ?? 'md';
        const result = await update('Text size updated.', () =>
            authStore.updateMeAsync({ font_size: value })
        );
        if (result === null) fontSizeDraft.value = previous;
    }

    async function onSendDealsOnDayChange(value: number) {
        const previous = currentUser.value?.send_deals_on_day ?? 0;
        const result = await update('Weekly deals day updated.', () =>
            authStore.updateMeAsync({ send_deals_on_day: value })
        );
        if (result === null) sendDealsOnDay.value = previous;
    }

    async function onDealsEnabledChange(value: boolean) {
        await update(
            value
                ? 'Subscribed to the weekly deals email.'
                : 'Unsubscribed from the weekly deals email.',
            () => authStore.updateMeAsync({ deals_email_enabled: value })
        );
    }

    async function onDealsCompactChange(value: boolean) {
        await update('Deals email format updated.', () =>
            authStore.updateMeAsync({ deals_email_compact: value })
        );
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
</script>
