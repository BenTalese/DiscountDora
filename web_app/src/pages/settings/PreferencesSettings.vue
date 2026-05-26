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

            <q-card-section class="q-pb-none">
                <div class="text-subtitle2">Theme</div>
                <div class="text-caption text-grey q-mb-md">
                    Pick a palette for the app. <strong>System</strong>
                    follows your browser's <code>prefers-color-scheme</code>
                    and flips between Pesto and Pesto Dark. Every other
                    family ships a Light and Dark variant — pick whichever
                    you prefer.
                </div>
                <div class="theme-grid">
                    <!-- System card stays separate — it's a meta-option. -->
                    <button
                        type="button"
                        class="theme-card theme-card--system"
                        :class="{ 'theme-card--active': themeDraft === 'system' }"
                        @click="onThemeChange('system')"
                    >
                        <div class="theme-swatch theme-swatch--system">
                            <q-icon name="brightness_auto" size="28px" />
                        </div>
                        <div class="theme-card-body">
                            <div class="theme-card-label">System</div>
                            <div class="theme-card-blurb">
                                Follows your OS — Pesto by day, Pesto
                                Dark at night.
                            </div>
                        </div>
                    </button>

                    <!-- One card per family, with Light + Dark toggle inside. -->
                    <div
                        v-for="family in themeFamilies"
                        :key="family.key"
                        class="theme-card theme-card--family"
                        :class="{
                            'theme-card--active': themeDraft === family.light || themeDraft === family.dark,
                        }"
                    >
                        <div class="theme-swatch-pair">
                            <div class="theme-swatch theme-swatch--half">
                                <span
                                    v-for="(hex, i) in lightSwatch(family)"
                                    :key="`l-${i}`"
                                    class="theme-swatch-strip"
                                    :style="{ background: hex }"
                                />
                            </div>
                            <div class="theme-swatch theme-swatch--half theme-swatch--half-dark">
                                <span
                                    v-for="(hex, i) in darkSwatch(family)"
                                    :key="`d-${i}`"
                                    class="theme-swatch-strip"
                                    :style="{ background: hex }"
                                />
                            </div>
                        </div>
                        <div class="theme-card-body">
                            <div class="theme-card-label">{{ family.label }}</div>
                            <div class="theme-card-blurb">{{ family.blurb }}</div>
                            <div class="theme-variant-toggle">
                                <q-btn
                                    no-caps
                                    dense
                                    flat
                                    size="sm"
                                    icon="light_mode"
                                    label="Light"
                                    class="theme-variant-btn"
                                    :class="{ 'theme-variant-btn--active': themeDraft === family.light }"
                                    @click="onThemeChange(family.light as ThemePreference)"
                                />
                                <q-btn
                                    no-caps
                                    dense
                                    flat
                                    size="sm"
                                    icon="dark_mode"
                                    label="Dark"
                                    class="theme-variant-btn"
                                    :class="{ 'theme-variant-btn--active': themeDraft === family.dark }"
                                    @click="onThemeChange(family.dark as ThemePreference)"
                                />
                            </div>
                        </div>
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
    import { THEMES, THEME_FAMILIES, type ThemeFamily } from 'src/services/themeService';
    import { useAuthStore } from 'src/stores/authStore';
    import { computed, ref, watch } from 'vue';
    import { describeApiError } from 'src/services/errorHandling/apiErrorHandler';

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
    // Theme catalogue surfaced by the picker. `system` is rendered
    // manually (meta-option), then one card per family — each family
    // has paired Light + Dark variant buttons inside.
    const themeFamilies = computed(() => THEME_FAMILIES);
    function lightSwatch(family: ThemeFamily): string[] {
        return THEMES[family.light]?.swatch ?? [];
    }
    function darkSwatch(family: ThemeFamily): string[] {
        return THEMES[family.dark]?.swatch ?? [];
    }

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
            caption: describeApiError(err) || ''
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

<style scoped>
    /* Theme picker — one card per family, each with paired Light/Dark
       buttons inside. System (a meta-option) renders as its own card. */
    .theme-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
        gap: 16px;
    }
    .theme-card {
        appearance: none;
        background: var(--surface-component);
        border: 1.5px solid var(--border-default);
        border-radius: var(--radius-lg, 10px);
        padding: 12px;
        text-align: left;
        transition: border-color 120ms ease, box-shadow 120ms ease;
        display: flex;
        flex-direction: column;
        gap: 10px;
    }
    .theme-card--system {
        cursor: pointer;
        flex-direction: row;
        align-items: center;
    }
    .theme-card:hover {
        border-color: var(--border-strong);
        box-shadow: var(--elevation-1);
    }
    .theme-card--active {
        border-color: var(--brand-primary);
        box-shadow: 0 0 0 3px var(--ring-focus);
    }
    .theme-swatch {
        display: flex;
        gap: 4px;
        height: 44px;
        border-radius: var(--radius-sm, 4px);
        overflow: hidden;
        align-items: stretch;
        justify-content: center;
        background: var(--surface-sunken);
    }
    .theme-swatch--system {
        width: 56px;
        height: 56px;
        flex: 0 0 56px;
        background: var(--brand-primary-soft);
        color: var(--brand-primary);
    }
    .theme-swatch-pair {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 14px;
        height: 44px;
    }
    .theme-swatch--half {
        height: 100%;
        margin-bottom: 0;
    }
    .theme-swatch--half-dark {
        outline: 1px solid var(--border-default);
        outline-offset: -1px;
    }
    .theme-swatch-strip {
        flex: 1 1 0;
        height: 100%;
    }
    .theme-card-body {
        display: flex;
        flex-direction: column;
        gap: 4px;
    }
    .theme-card-label {
        font-weight: 600;
        color: var(--text-primary);
    }
    .theme-card-blurb {
        color: var(--text-secondary);
        font-size: 12px;
        line-height: 1.35;
    }
    .theme-variant-toggle {
        display: flex;
        gap: 6px;
        margin-top: 6px;
    }
    .theme-variant-btn {
        flex: 1 1 0;
        border: 1px solid var(--border-default);
        border-radius: var(--radius-md, 6px);
        color: var(--text-secondary);
        transition: background 120ms ease, color 120ms ease, border-color 120ms ease;
    }
    .theme-variant-btn:hover {
        border-color: var(--border-strong);
        color: var(--text-primary);
    }
    .theme-variant-btn--active {
        background: var(--brand-primary);
        color: var(--text-on-primary);
        border-color: var(--brand-primary);
    }
</style>
