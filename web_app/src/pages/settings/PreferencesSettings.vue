<template>
    <div v-if="!currentUser">
        <q-card flat bordered>
            <q-card-section>
                <q-banner class="dora-bg-sunken" dense>Not signed in.</q-banner>
            </q-card-section>
        </q-card>
    </div>

    <div v-else class="column q-gutter-md">
        <!-- Appearance ─────────────────────────────────────────────── -->
        <q-card flat bordered>
            <q-card-section>
                <div class="text-h6">Appearance</div>
                <div class="text-caption dora-text-muted">
                    Theme, font, and text size for this account.
                </div>
            </q-card-section>
            <q-separator />

            <q-card-section class="q-pb-none">
                <div class="text-subtitle2">Mode</div>
                <div class="text-caption dora-text-muted q-mb-md">
                    <strong>System</strong> follows your browser's
                    <code>prefers-color-scheme</code> for whichever theme
                    you pick below. <strong>Light</strong> and <strong>Dark</strong>
                    lock the mode regardless of the OS.
                </div>
                <q-btn-toggle
                    v-model="modeDraft"
                    no-caps
                    spread
                    toggle-color="primary"
                    :options="[
                        { label: 'System', value: 'system', icon: ICONS.brightness_auto },
                        { label: 'Light', value: 'light', icon: ICONS.light_mode },
                        { label: 'Dark', value: 'dark', icon: ICONS.dark_mode },
                    ]"
                    @update:model-value="onModeChange"
                />
            </q-card-section>

            <q-card-section class="q-pb-none">
                <div class="text-subtitle2">Theme</div>
                <div class="text-caption dora-text-muted q-mb-md">
                    Pick a palette. The swatch on each card shows the
                    {{ modeDraft === 'system'
                        ? `variant your OS is currently set to (${osCurrentlyDark ? 'dark' : 'light'})`
                        : modeDraft + ' variant' }}.
                </div>
                <div class="theme-grid">
                    <!-- Round-19: one card per family, single-swatch
                         (no light/dark buttons inside). Mode lives in the
                         toggle above; clicking a card just selects the
                         family. The swatch reflects whichever variant the
                         current mode resolves to right now. -->
                    <button
                        v-for="family in themeFamilies"
                        :key="family.key"
                        type="button"
                        class="theme-card theme-card--family"
                        :class="{
                            'theme-card--active': familyDraft === family.key,
                        }"
                        @click="onFamilyChange(family)"
                    >
                        <div class="theme-swatch theme-swatch--single">
                            <span
                                v-for="(hex, i) in swatchFor(family)"
                                :key="`s-${i}`"
                                class="theme-swatch-strip"
                                :style="{ background: hex }"
                            />
                        </div>
                        <div class="theme-card-body">
                            <div class="theme-card-label">{{ family.label }}</div>
                            <div class="theme-card-blurb">{{ family.blurb }}</div>
                        </div>
                    </button>
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
                            { label: 'Large', value: 'lg' },
                            { label: 'Extra large', value: 'xl' }
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
                <div class="text-caption dora-text-muted">
                    Dashy Dora can email you a digest of the latest deals
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

        <!-- C-9.7 — Alerts email digest. SMTP-gated (R-014): the master
             toggle disables when the backend doesn't have email
             configured, so a self-hosted install without SMTP doesn't
             silently swallow opt-ins. -->
        <q-card flat bordered>
            <q-card-section>
                <div class="text-h6">Alerts email digest</div>
                <div class="text-caption dora-text-muted">
                    Get your actionable alerts emailed to you on a daily or
                    weekly cadence. The digest matches what you'd see on the
                    Alerts page; the same alert won't email again until it
                    clears and re-fires.
                </div>
            </q-card-section>
            <q-separator />

            <q-card-section>
                <q-toggle
                    :model-value="currentUser.alerts_email_enabled"
                    label="Email me a digest of my alerts"
                    :disable="saving || !emailSmtpConfigured"
                    @update:model-value="onAlertsEmailEnabledChange"
                />
                <div
                    v-if="!emailSmtpConfigured"
                    class="text-caption dora-text-muted q-mt-xs"
                >
                    Email isn't set up on this install yet — ask an admin
                    to configure SMTP and this toggle will unlock.
                </div>
            </q-card-section>

            <q-card-section
                v-if="currentUser.alerts_email_enabled"
                class="row q-col-gutter-md items-center"
            >
                <div class="col-12 col-sm-4 text-subtitle2">Cadence</div>
                <div class="col-12 col-sm-8">
                    <q-select
                        v-model="alertsEmailCadenceDraft"
                        :options="alertsCadenceOptions"
                        option-value="value"
                        option-label="label"
                        emit-value
                        map-options
                        outlined
                        dense
                        style="max-width: 260px"
                        :disable="saving"
                        @update:model-value="onAlertsEmailCadenceChange"
                    />
                </div>
            </q-card-section>

            <q-card-section
                v-if="currentUser.alerts_email_enabled && alertsEmailCadenceDraft === 'weekly'"
                class="row q-col-gutter-md items-center"
            >
                <div class="col-12 col-sm-4 text-subtitle2">Send on</div>
                <div class="col-12 col-sm-8">
                    <q-select
                        v-model="alertsEmailDayDraft"
                        :options="dayOptions"
                        option-value="value"
                        option-label="label"
                        emit-value
                        map-options
                        outlined
                        dense
                        style="max-width: 260px"
                        :disable="saving"
                        @update:model-value="onAlertsEmailDayChange"
                    />
                </div>
            </q-card-section>
        </q-card>

        <!-- C-9.8 — Push notifications. VAPID-gated (R-014): the toggle
             disables when the backend isn't configured, mirroring the
             alerts-email SMTP gate. The four-state lifecycle (loading /
             unsupported / denied / subscribed) is surfaced via the
             caption beneath the toggle. -->
        <q-card flat bordered>
            <q-card-section>
                <div class="text-h6">Push notifications</div>
                <div class="text-caption dora-text-muted">
                    Get a system notification on this device the moment a new
                    actionable alert fires. Only actionable alerts are pushed —
                    FYI items stay in the hub and the email digest. Subscribe
                    on every device you want to be notified on.
                </div>
            </q-card-section>
            <q-separator />

            <q-card-section>
                <q-toggle
                    :model-value="pushSubscribed"
                    label="Send me push notifications on this device"
                    :disable="saving || !pushVapidConfigured || !pushSupported || pushLoading"
                    @update:model-value="onPushToggle"
                />
                <div
                    v-if="!pushVapidConfigured"
                    class="text-caption dora-text-muted q-mt-xs"
                >
                    Push isn't set up on this install yet — ask an admin
                    to generate VAPID keys and this toggle will unlock.
                </div>
                <div
                    v-else-if="!pushSupported"
                    class="text-caption dora-text-muted q-mt-xs"
                >
                    This browser doesn't support web push.
                </div>
                <div
                    v-else-if="pushState === 'denied'"
                    class="text-caption dora-text-muted q-mt-xs"
                >
                    Notifications are blocked for this site. Re-enable them in
                    your browser's site settings, then refresh.
                </div>
                <div
                    v-else-if="pushError"
                    class="text-caption text-negative q-mt-xs"
                >
                    {{ pushError }}
                </div>
                <div
                    v-else-if="pushSubscribed"
                    class="text-caption dora-text-muted q-mt-xs"
                >
                    This device is subscribed. Toggle off to stop receiving
                    pushes here (other devices keep their own subscriptions).
                </div>
            </q-card-section>
        </q-card>

        <!-- C-cross Chunk 2 — Money features opt-in.
             Layered with the install-wide `money_enabled` flag (admin
             owns that one in Settings → System → Features). The Grocery
             budget card below stays hidden until both layers are on.
             Saved `budget_amount` survives toggling this off. -->
        <q-card flat bordered>
            <q-card-section>
                <div class="text-h6">Money & budgets</div>
                <div class="text-caption dora-text-muted">
                    Show dollar surfaces — recipe cost estimates, shopping-list
                    totals, the dashboard budget card. Off by default; turn on
                    to opt in. Your saved budget number is kept either way.
                </div>
            </q-card-section>
            <q-separator />

            <q-card-section>
                <q-toggle
                    :model-value="currentUser.money_features_enabled"
                    :disable="!moneyInstallEnabled || saving"
                    label="Show money features"
                    @update:model-value="onMoneyFeaturesChange"
                />
                <div
                    v-if="!moneyInstallEnabled"
                    class="text-caption dora-text-muted q-mt-xs"
                >
                    This install has money features turned off. Ask an admin
                    to enable them in System → Features.
                </div>
            </q-card-section>
        </q-card>

        <!-- Grocery budget (P2-05) ─────────────────────────────────── -->
        <!-- C-cross Chunk 2 — hidden when money features are off
             (install-wide OR per-user). Saved value preserved. -->
        <q-card v-if="moneyEnabled" flat bordered>
            <q-card-section>
                <div class="text-h6">Grocery budget</div>
                <div class="text-caption dora-text-muted">
                    Optional. Set a weekly or monthly target and Dora will
                    track how much you've spent across every finished
                    shopping list in the period.
                </div>
            </q-card-section>
            <q-separator />

            <q-card-section>
                <q-toggle
                    :model-value="budgetEnabledDraft"
                    label="Track a grocery budget"
                    :disable="saving"
                    @update:model-value="onBudgetEnabledChange"
                />
            </q-card-section>

            <q-card-section
                v-if="budgetEnabledDraft"
                class="row q-col-gutter-md items-end"
            >
                <q-input
                    v-model.number="budgetAmountDraft"
                    label="Amount"
                    type="number"
                    step="1"
                    min="0"
                    prefix="$"
                    outlined
                    dense
                    class="col-12 col-sm-4"
                    :disable="saving"
                    @blur="onBudgetAmountBlur"
                    @keydown.enter.prevent="onBudgetAmountBlur"
                />
                <div class="col-12 col-sm-8">
                    <q-btn-toggle
                        v-model="budgetPeriodDraft"
                        no-caps
                        spread
                        toggle-color="primary"
                        :options="[
                            { label: 'Weekly (Mon–Sun)', value: 'weekly' },
                            { label: 'Monthly', value: 'monthly' }
                        ]"
                        @update:model-value="onBudgetPeriodChange"
                    />
                </div>
            </q-card-section>
        </q-card>

        <!-- C-cross Chunk 3 — per-user nutrition mode (proposal §2.3).
             Three-way toggle. `complex` is disabled when the install
             admin hasn't configured a nutrition source (the reserved
             seam). The per-recipe kcal field + cookbook kcal sort axis
             are C-4 Chunk 9, gated on this composable. -->
        <q-card flat bordered>
            <q-card-section>
                <div class="text-h6">Nutrition</div>
                <div class="text-caption dora-text-muted">
                    Off by default. <strong>Simple</strong> adds a single kcal
                    number per recipe that you type in.
                    <strong>Complex</strong> would derive nutrition from a
                    nutrition database — not built yet, and disabled until an
                    admin configures a source.
                </div>
            </q-card-section>
            <q-separator />

            <q-card-section>
                <div class="row items-center q-gutter-md">
                    <q-btn-toggle
                        :model-value="currentUser.nutrition_mode"
                        :options="nutritionToggleOptions"
                        no-caps
                        toggle-color="primary"
                        :disable="!nutritionInstallEnabled || saving"
                        @update:model-value="onNutritionModeChange"
                    />
                </div>
                <div
                    v-if="!nutritionInstallEnabled"
                    class="text-caption dora-text-muted q-mt-xs"
                >
                    This install has nutrition turned off. Ask an admin to
                    enable it in System → Features.
                </div>
                <div
                    v-else-if="currentUser.nutrition_mode === 'complex' && !complexAvailable"
                    class="text-caption dora-text-muted q-mt-xs"
                >
                    Complex mode needs an admin-configured nutrition source.
                </div>
            </q-card-section>
        </q-card>

        <!-- Voice (P2-13) ──────────────────────────────────────────── -->
        <q-card flat bordered>
            <q-card-section>
                <div class="text-h6">Voice</div>
                <div class="text-caption dora-text-muted">
                    Talk to Dora and let her talk back. Voice features
                    use your browser's built-in speech recognition and
                    synthesis — they only work where the browser
                    supports them, and your browser will ask for
                    microphone permission the first time you tap the mic.
                </div>
            </q-card-section>
            <q-separator />

            <q-card-section>
                <q-toggle
                    :model-value="currentUser.voice_input_enabled"
                    :disable="!voiceInputAvailable || saving"
                    label="Enable voice input (microphone)"
                    @update:model-value="onVoiceInputChange"
                />
                <div v-if="!voiceInputAvailable" class="text-caption dora-text-muted q-mt-xs">
                    Your browser doesn't expose the Web Speech API for
                    recognition. Try Chrome or Edge.
                </div>
            </q-card-section>

            <q-card-section>
                <q-toggle
                    :model-value="currentUser.voice_output_enabled"
                    :disable="!voiceOutputAvailable || saving"
                    label="Let Dora speak her replies"
                    @update:model-value="onVoiceOutputChange"
                />
                <div v-if="!voiceOutputAvailable" class="text-caption dora-text-muted q-mt-xs">
                    Your browser doesn't expose SpeechSynthesis.
                </div>
            </q-card-section>
        </q-card>

        <!-- Account ────────────────────────────────────────────────── -->
        <q-card flat bordered>
            <q-card-section>
                <div class="text-h6">Account</div>
                <div class="text-caption dora-text-muted">
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
    </div>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import { storeToRefs } from 'pinia';
    import { useQuasar } from 'quasar';
    import type {
        BudgetPeriod,
        FontFamilyPreference,
        FontSizePreference,
        ThemePreference
    } from 'src/models/auth';
    import {
        THEMES,
        THEME_FAMILIES,
        familyAndModeOf,
        themeKeyFor,
        osPrefersDark,
        type ThemeFamily,
    } from 'src/services/themeService';
    import { useAuthStore } from 'src/stores/authStore';
    import { useSpeechOutput } from 'src/composables/useSpeechOutput';
    import { useVoiceInput } from 'src/composables/useVoiceInput';
    import { useFeatureFlags } from 'src/composables/useFeatureFlags';
    import { useMoneyEnabled } from 'src/composables/useMoneyEnabled';
    import { usePushSubscription } from 'src/composables/usePushSubscription';
    import {
        useNutritionMode,
        type NutritionMode,
    } from 'src/composables/useNutritionMode';
    import { computed, ref, watch } from 'vue';
    import { describeApiError } from 'src/services/errorHandling/apiErrorHandler';

    const $q = useQuasar();
    const authStore = useAuthStore();
    const { currentUser } = storeToRefs(authStore);
    // C-cross Chunk 2 — money opt-in layering. The Settings page exposes
    // both layers explicitly so the user can see why the budget card
    // might be missing (install off vs. their own toggle off).
    const {
        moneyEnabled,
        installEnabled: moneyInstallEnabled,
    } = useMoneyEnabled();
    // C-cross Chunk 3 — nutrition opt-in layering. `complexAvailable`
    // gates the third toggle button + caption; the install flag gates
    // the whole control.
    const {
        installEnabled: nutritionInstallEnabled,
        complexAvailable,
    } = useNutritionMode();
    const nutritionToggleOptions = computed(() => [
        { label: 'Off', value: 'off' as NutritionMode },
        { label: 'Simple', value: 'simple' as NutritionMode },
        { label: 'Complex', value: 'complex' as NutritionMode, disable: !complexAvailable.value },
    ]);

    // C-9.7 — alerts email digest gating. The backend feature flag
    // mirrors `email_sender._config().dry_run` so the toggle reflects
    // whether emails would actually leave the box (R-014).
    const { emailSmtpConfigured, pushVapidConfigured } = useFeatureFlags();
    const alertsCadenceOptions = [
        { label: 'Daily', value: 'daily' as const },
        { label: 'Weekly', value: 'weekly' as const },
    ];

    // C-9.8 — push subscription lifecycle for this device. The
    // composable owns the four-state machine; the card binds against it.
    const {
        state: pushState,
        error: pushError,
        subscribed: pushSubscribed,
        supported: pushSupported,
        subscribe: pushSubscribe,
        unsubscribe: pushUnsubscribe,
    } = usePushSubscription();
    const pushLoading = computed(() => pushState.value === 'loading');

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
    // C-9.7 — alerts email digest. Cadence and day are draft refs so the
    // q-select reflects the freshly saved value without flickering through
    // the watcher; the toggle reads `currentUser` directly (instant-flip).
    const alertsEmailCadenceDraft = ref<'daily' | 'weekly'>(
        (currentUser.value?.alerts_email_cadence === 'weekly') ? 'weekly' : 'daily'
    );
    const alertsEmailDayDraft = ref<number>(currentUser.value?.alerts_email_day ?? 0);
    // Theme catalogue surfaced by the picker. Round-19: mode (System /
    // Light / Dark) and family (Pesto / Lemon Tart / …) are two
    // independent draft refs, derived from the persisted single-key
    // ThemePreference at load time and resolved back to one key on save.
    const themeFamilies = computed(() => THEME_FAMILIES);
    type ThemeMode = 'system' | 'light' | 'dark';

    function modeAndFamilyForKey(key: string): { mode: ThemeMode; familyKey: string } {
        const decoded = familyAndModeOf(key);
        if (decoded) return { mode: decoded.mode, familyKey: decoded.family.key };
        // Unknown / legacy fallback — default to System + Pesto.
        return { mode: 'system', familyKey: THEME_FAMILIES[0]!.key };
    }

    const initialThemeKey: string = currentUser.value?.theme ?? 'system';
    const initial = modeAndFamilyForKey(initialThemeKey);
    const modeDraft = ref<ThemeMode>(initial.mode);
    const familyDraft = ref<string>(initial.familyKey);

    // Track the OS's current preference so the "swatch shows X" caption
    // and per-card single swatch reflect it under mode=system. matchMedia
    // change events let the cards update if the OS flips while the user
    // is on this page.
    const osCurrentlyDark = ref<boolean>(osPrefersDark());
    let mql: MediaQueryList | null = null;
    if (typeof window !== 'undefined' && window.matchMedia) {
        mql = window.matchMedia('(prefers-color-scheme: dark)');
        const onChange = (e: MediaQueryListEvent) => { osCurrentlyDark.value = e.matches; };
        if ('addEventListener' in mql) {
            mql.addEventListener('change', onChange);
        }
    }

    /** Show whichever variant's swatch the current mode resolves to. For
     *  `system`, that's whichever side the OS is on right now. */
    function swatchFor(family: ThemeFamily): string[] {
        const key = modeDraft.value === 'dark'
            ? family.dark
            : modeDraft.value === 'light'
                ? family.light
                : osCurrentlyDark.value ? family.dark : family.light;
        return THEMES[key]?.swatch ?? [];
    }

    const themeDraft = ref<ThemePreference>(currentUser.value?.theme ?? 'system');
    const fontFamilyDraft = ref<FontFamilyPreference>(
        currentUser.value?.font_family ?? 'default'
    );
    const fontSizeDraft = ref<FontSizePreference>(currentUser.value?.font_size ?? 'md');

    // P2-05 — budget drafts. `enabled` is derived from amount-being-set;
    // we keep it as a separate draft so toggling off doesn't blow away
    // the user's amount typing (we restore it if they toggle back on
    // without saving).
    const budgetAmountDraft = ref<number | null>(currentUser.value?.budget_amount ?? null);
    const budgetPeriodDraft = ref<BudgetPeriod>(currentUser.value?.budget_period ?? 'weekly');
    const budgetEnabledDraft = ref<boolean>(
        currentUser.value?.budget_amount != null && currentUser.value.budget_amount > 0
    );

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
        const decoded = modeAndFamilyForKey(u.theme);
        modeDraft.value = decoded.mode;
        familyDraft.value = decoded.familyKey;
        fontFamilyDraft.value = u.font_family;
        fontSizeDraft.value = u.font_size;
        budgetAmountDraft.value = u.budget_amount ?? null;
        budgetPeriodDraft.value = u.budget_period ?? 'weekly';
        budgetEnabledDraft.value = u.budget_amount != null && u.budget_amount > 0;
        alertsEmailCadenceDraft.value = u.alerts_email_cadence === 'weekly' ? 'weekly' : 'daily';
        alertsEmailDayDraft.value = u.alerts_email_day ?? 0;
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
        if (result === null) {
            themeDraft.value = previous;
            const decoded = modeAndFamilyForKey(previous);
            modeDraft.value = decoded.mode;
            familyDraft.value = decoded.familyKey;
        }
    }

    /** Mode pill changed (System / Light / Dark). Persist by recombining
     *  with the current family. */
    async function onModeChange(value: ThemeMode) {
        const family = THEME_FAMILIES.find((f) => f.key === familyDraft.value)
            ?? THEME_FAMILIES[0]!;
        const next = themeKeyFor(value, family);
        await onThemeChange(next);
    }

    /** Family card clicked. Persist by recombining with the current mode. */
    async function onFamilyChange(family: ThemeFamily) {
        familyDraft.value = family.key;
        const next = themeKeyFor(modeDraft.value, family);
        await onThemeChange(next);
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

    // C-9.7 — alerts email digest handlers. Toggling the master switch
    // sends both `alerts_email_enabled` and the current cadence so a
    // fresh-opt-in user starts on a sensible default ('daily') without
    // a second click. Cadence/day changes are saved instantly.
    async function onAlertsEmailEnabledChange(value: boolean) {
        const cadence = value ? alertsEmailCadenceDraft.value : 'off';
        await update(
            value
                ? 'Subscribed to the alerts email digest.'
                : 'Unsubscribed from the alerts email digest.',
            () => authStore.updateMeAsync({
                alerts_email_enabled: value,
                alerts_email_cadence: cadence,
            })
        );
    }

    async function onAlertsEmailCadenceChange(value: 'daily' | 'weekly') {
        const previous = alertsEmailCadenceDraft.value;
        alertsEmailCadenceDraft.value = value;
        const result = await update('Digest cadence updated.', () =>
            authStore.updateMeAsync({ alerts_email_cadence: value })
        );
        if (result === null) alertsEmailCadenceDraft.value = previous;
    }

    async function onAlertsEmailDayChange(value: number) {
        const previous = alertsEmailDayDraft.value;
        alertsEmailDayDraft.value = value;
        const result = await update('Digest day updated.', () =>
            authStore.updateMeAsync({ alerts_email_day: value })
        );
        if (result === null) alertsEmailDayDraft.value = previous;
    }

    // C-9.8 — push toggle. The composable handles the permission
    // prompt + server round-trip; we just translate success/failure
    // into the standard $q.notify pattern.
    async function onPushToggle(value: boolean) {
        try {
            if (value) {
                await pushSubscribe();
                if (pushSubscribed.value) notifySuccess('Subscribed to push notifications on this device.');
            } else {
                await pushUnsubscribe();
                notifySuccess('Unsubscribed from push notifications on this device.');
            }
        } catch (err) {
            notifyError('Push subscription failed.', err);
        }
    }

    // P2-05 — budget handlers.
    async function onBudgetEnabledChange(value: boolean) {
        budgetEnabledDraft.value = value;
        if (!value) {
            // Toggling off clears the persisted amount but keeps the draft
            // so a quick "actually, keep tracking" toggle restores it.
            const result = await update('Budget tracking turned off.', () =>
                authStore.updateMeAsync({ clear_budget_amount: true })
            );
            if (result === null) budgetEnabledDraft.value = true;
            return;
        }
        // Turning on without a number is a no-op until the user types one
        // and blurs — keeps the wire calm.
        if (
            budgetAmountDraft.value != null
            && budgetAmountDraft.value > 0
            && currentUser.value?.budget_amount !== budgetAmountDraft.value
        ) {
            const result = await update('Budget enabled.', () =>
                authStore.updateMeAsync({
                    budget_amount: budgetAmountDraft.value!,
                    budget_period: budgetPeriodDraft.value,
                })
            );
            if (result === null) budgetEnabledDraft.value = false;
        }
    }

    async function onBudgetAmountBlur() {
        if (!budgetEnabledDraft.value) return;
        const value = budgetAmountDraft.value;
        if (value == null || Number.isNaN(value) || value <= 0) {
            // Empty / zero input is treated as "turn this off" — saves the
            // user a trip back to the toggle.
            budgetEnabledDraft.value = false;
            await update('Budget tracking turned off.', () =>
                authStore.updateMeAsync({ clear_budget_amount: true })
            );
            return;
        }
        if (currentUser.value?.budget_amount === value) return;
        const previous = currentUser.value?.budget_amount ?? null;
        const result = await update('Budget updated.', () =>
            authStore.updateMeAsync({ budget_amount: value })
        );
        if (result === null) budgetAmountDraft.value = previous;
    }

    async function onBudgetPeriodChange(value: BudgetPeriod) {
        const previous = currentUser.value?.budget_period ?? 'weekly';
        const result = await update('Budget period updated.', () =>
            authStore.updateMeAsync({ budget_period: value })
        );
        if (result === null) budgetPeriodDraft.value = previous;
    }

    // P2-13 — voice prefs. Availability flags come from cheap probes
    // against the browser's globals; they don't actually start a
    // recognition session, so the user can flip the toggle without
    // a microphone prompt firing here.
    const voiceProbeInput = useVoiceInput();
    const voiceProbeOutput = useSpeechOutput();
    const voiceInputAvailable = computed(() => voiceProbeInput.available.value);
    const voiceOutputAvailable = computed(() => voiceProbeOutput.available.value);

    async function onVoiceInputChange(value: boolean) {
        await update(
            value ? 'Voice input enabled.' : 'Voice input disabled.',
            () => authStore.updateMeAsync({ voice_input_enabled: value }),
        );
    }
    async function onVoiceOutputChange(value: boolean) {
        // Cancel any in-flight utterance when the user opts out so the
        // toggle's effect is immediate.
        if (!value) voiceProbeOutput.cancel();
        await update(
            value ? 'Dora will speak her replies.' : 'Dora\'s voice muted.',
            () => authStore.updateMeAsync({ voice_output_enabled: value }),
        );
    }

    // C-cross Chunk 2 — per-user money-features opt-in. The save-saved
    // budget value isn't touched (proposal §2.2: "data preserved").
    async function onMoneyFeaturesChange(value: boolean) {
        await update(
            value ? 'Money features turned on.' : 'Money features turned off.',
            () => authStore.updateMeAsync({ money_features_enabled: value }),
        );
    }

    // C-cross Chunk 3 — per-user nutrition mode. Server rejects
    // `complex` when no nutrition source is configured; the toggle
    // option is also disabled in that state so this should never
    // 422 in normal use.
    async function onNutritionModeChange(value: NutritionMode) {
        const labelByMode: Record<NutritionMode, string> = {
            off: 'Nutrition turned off.',
            simple: 'Simple nutrition turned on.',
            complex: 'Complex nutrition turned on.',
        };
        await update(
            labelByMode[value],
            () => authStore.updateMeAsync({ nutrition_mode: value }),
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
    /* Theme picker — round 19. Mode (System / Light / Dark) is a
       separate q-btn-toggle above; the cards are one-per-family and
       carry only the single swatch the current mode resolves to. */
    .theme-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
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
        cursor: pointer;
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
    .theme-swatch--single {
        height: 44px;
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
        /* A6 — scale token (was fixed 12px). */
        font-size: calc(var(--font-size-xs) * 1rem);
        line-height: 1.35;
    }
</style>
