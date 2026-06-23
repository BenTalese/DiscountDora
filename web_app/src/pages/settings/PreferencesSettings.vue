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
        <!-- Settings rebuild Phase 2: Preferences is now Appearance-only.
             Notifications / Money / Voice / Nutrition split into their own
             pages; the misplaced identity edit forms moved to Account. -->
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
    </div>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import { storeToRefs } from 'pinia';
    import { useQuasar } from 'quasar';
    import type {
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
    import { ref, watch } from 'vue';
    import { describeApiError } from 'src/services/errorHandling/apiErrorHandler';

    const $q = useQuasar();
    const authStore = useAuthStore();
    const { currentUser } = storeToRefs(authStore);

    // Theme catalogue surfaced by the picker. Round-19: mode (System /
    // Light / Dark) and family (Pesto / Lemon Tart / …) are two
    // independent draft refs, derived from the persisted single-key
    // ThemePreference at load time and resolved back to one key on save.
    const themeFamilies = THEME_FAMILIES;
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
    if (typeof window !== 'undefined' && window.matchMedia) {
        const mql = window.matchMedia('(prefers-color-scheme: dark)');
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

    const saving = ref(false);

    // Re-sync drafts when the auth store reloads (e.g. after refresh, login).
    watch(currentUser, (u) => {
        if (!u) return;
        themeDraft.value = u.theme;
        const decoded = modeAndFamilyForKey(u.theme);
        modeDraft.value = decoded.mode;
        familyDraft.value = decoded.familyKey;
        fontFamilyDraft.value = u.font_family;
        fontSizeDraft.value = u.font_size;
    });

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
