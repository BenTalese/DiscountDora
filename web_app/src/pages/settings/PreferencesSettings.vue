<template>
    <div v-if="!currentUser">
        <q-banner class="dora-bg-sunken" dense>Not signed in.</q-banner>
    </div>

    <div v-else class="settings-page">
        <SettingsPageHeader
            title="Appearance"
            description="Theme, font, and text size for this account."
        />

        <SettingsSection>
            <template #title>Mode</template>
            <template #description>
                <strong>System</strong> follows your browser's
                <code>prefers-color-scheme</code>. <strong>Light</strong> and
                <strong>Dark</strong> lock the mode regardless of the OS.
            </template>

            <DoraSegmented
                :model-value="modeDraft"
                :options="modeOptions"
                @update:model-value="onModeChange"
            />
        </SettingsSection>

        <hr class="settings-divider" />

        <SettingsSection>
            <template #title>Theme</template>
            <template #description>
                Pick a palette. The swatch shows the
                {{ modeDraft === 'system'
                    ? `variant your OS is currently set to (${osCurrentlyDark ? 'dark' : 'light'})`
                    : modeDraft + ' variant' }}.
            </template>

            <div class="theme-grid">
                <button
                    v-for="family in themeFamilies"
                    :key="family.key"
                    type="button"
                    class="theme-card"
                    :class="{ 'theme-card--active': familyDraft === family.key }"
                    @click="onFamilyChange(family)"
                >
                    <q-tooltip v-if="family.blurb" anchor="top middle" self="bottom middle" :delay="400">
                        {{ family.blurb }}
                    </q-tooltip>
                    <q-icon
                        v-if="familyDraft === family.key"
                        :name="ICONS.check_circle"
                        size="18px"
                        class="theme-card__badge"
                    />
                    <div class="theme-swatch">
                        <span
                            v-for="(hex, i) in swatchFor(family)"
                            :key="`s-${i}`"
                            class="theme-swatch-strip"
                            :style="{ background: hex }"
                        />
                    </div>
                    <div class="theme-card__label">{{ family.label }}</div>
                </button>
            </div>
        </SettingsSection>

        <hr class="settings-divider" />

        <SettingsSection>
            <template #title>Typography</template>
            <template #description>
                Font family and text size apply across the whole app.
            </template>

            <SettingsRow label="Font family">
                <DoraSegmented
                    :model-value="fontFamilyDraft"
                    :options="fontFamilyOptions"
                    @update:model-value="onFontFamilyChange"
                />
            </SettingsRow>

            <SettingsRow label="Text size">
                <DoraSegmented
                    :model-value="fontSizeDraft"
                    :options="fontSizeOptions"
                    @update:model-value="onFontSizeChange"
                />
            </SettingsRow>
        </SettingsSection>

        <hr class="settings-divider" />

        <SettingsSection>
            <template #title>Shopping lists</template>
            <template #description>
                Controls how quick-add ("Add to list") behaves when you have
                more than one draft shopping list open.
            </template>

            <SettingsRow
                label="Always ask which list"
                help="When on, the picker fires every time — Dora won't remember the last list you picked for the tab session."
            >
                <q-toggle
                    :model-value="currentUser.always_ask_which_shopping_list"
                    :disable="savingAlwaysAsk"
                    @update:model-value="onAlwaysAskChange"
                />
            </SettingsRow>
        </SettingsSection>

        <hr class="settings-divider" />

        <SettingsSection>
            <template #title>Meal planning</template>
            <template #description>
                Cooking style controls what the meal planner shows.
                <strong>Fresh</strong> keeps the planner pure scheduling.
                <strong>Batch</strong> adds the cook pool (per-recipe ± /
                log-cook), the cook-shortfall warning, and the
                "to cook by" sidebar line.
            </template>

            <SettingsRow label="Cooking style">
                <DoraSegmented
                    :model-value="batchEnabled ? 'batch' : 'fresh'"
                    :options="cookingStyleOptions"
                    @update:model-value="onCookingStyleChange"
                />
            </SettingsRow>

            <SettingsRow
                label="Meals per week"
                help="How many meals the sequential builder aims for. Leave blank to use the default of 7."
            >
                <q-input
                    v-model.number="mealsPerWeekDraft"
                    outlined
                    dense
                    type="number"
                    :min="1"
                    :max="21"
                    style="max-width: 100px"
                    :placeholder="String(BUILDER_TARGET_MEALS_FALLBACK)"
                    :disable="savingMealsPerWeek"
                    @change="onMealsPerWeekChange"
                />
            </SettingsRow>
        </SettingsSection>
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
    import { useBatchEnabled } from 'src/composables/useBatchEnabled';
    import { BUILDER_TARGET_MEALS_FALLBACK } from 'src/composables/useMealPlanner';
    import { ref, watch } from 'vue';
    import { toastCaption } from 'src/services/errorHandling/apiErrorHandler';
    import SettingsSection from 'src/components/settings/SettingsSection.vue';
    import SettingsRow from 'src/components/settings/SettingsRow.vue';
    import SettingsPageHeader from 'src/components/settings/SettingsPageHeader.vue';
    import DoraSegmented, { type DoraSegmentedOption } from 'src/components/settings/DoraSegmented.vue';

    const $q = useQuasar();
    const authStore = useAuthStore();
    const { currentUser } = storeToRefs(authStore);
    const { batchEnabled, setBatchEnabled } = useBatchEnabled();

    type CookingStyle = 'fresh' | 'batch';
    const cookingStyleOptions: DoraSegmentedOption<CookingStyle>[] = [
        { label: 'Fresh', value: 'fresh' },
        { label: 'Batch', value: 'batch' },
    ];
    // FU-316 — "always ask which list" quick-add opt-in. Optimistic flip
    // with rollback on error, same shape as the other single-toggle prefs
    // on this page.
    const savingAlwaysAsk = ref(false);
    async function onAlwaysAskChange(value: boolean) {
        savingAlwaysAsk.value = true;
        try {
            await authStore.updateMeAsync({ always_ask_which_shopping_list: value });
            notifySuccess(
                value ? 'Dora will always ask which list.' : 'Dora will remember your pick.',
            );
        } catch (err) {
            notifyError('Could not save shopping-list preference.', err);
        } finally {
            savingAlwaysAsk.value = false;
        }
    }

    // FU-181 loose-end 2 — meals-per-week input. Null / cleared → server
    // stores NULL and the builder falls back to
    // BUILDER_TARGET_MEALS_FALLBACK. Validated 1–21 server-side.
    const mealsPerWeekDraft = ref<number | null>(currentUser.value?.meals_per_week ?? null);
    const savingMealsPerWeek = ref(false);
    watch(currentUser, (u) => {
        if (u) mealsPerWeekDraft.value = u.meals_per_week ?? null;
    });
    async function onMealsPerWeekChange() {
        const raw = mealsPerWeekDraft.value;
        const next: number | null =
            typeof raw === 'number' && Number.isFinite(raw) && raw >= 1 && raw <= 21
                ? Math.round(raw)
                : null;
        // Normalise the local field so a blanked / out-of-range input
        // reverts to the placeholder shape immediately.
        mealsPerWeekDraft.value = next;
        if (next === (currentUser.value?.meals_per_week ?? null)) return;
        savingMealsPerWeek.value = true;
        try {
            await authStore.updateMeAsync({ meals_per_week: next });
            notifySuccess(
                next === null
                    ? `Meals per week reset to the default (${BUILDER_TARGET_MEALS_FALLBACK}).`
                    : `Meals per week set to ${next}.`,
            );
        } catch (err) {
            notifyError('Could not save meals per week.', err);
            mealsPerWeekDraft.value = currentUser.value?.meals_per_week ?? null;
        } finally {
            savingMealsPerWeek.value = false;
        }
    }

    async function onCookingStyleChange(next: CookingStyle) {
        try {
            await setBatchEnabled(next === 'batch');
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not change cooking style.',
                caption: toastCaption(err),
            });
        }
    }

    const themeFamilies = THEME_FAMILIES;
    type ThemeMode = 'system' | 'light' | 'dark';

    const modeOptions: DoraSegmentedOption<ThemeMode>[] = [
        { label: 'System', value: 'system', icon: ICONS.brightness_auto },
        { label: 'Light', value: 'light', icon: ICONS.light_mode },
        { label: 'Dark', value: 'dark', icon: ICONS.dark_mode },
    ];
    const fontFamilyOptions: DoraSegmentedOption<FontFamilyPreference>[] = [
        { label: 'Default', value: 'default' },
        { label: 'Urbanist', value: 'urbanist' },
        { label: 'Nunito', value: 'nunito' },
        { label: 'Inter', value: 'inter' },
        { label: 'Lexend', value: 'lexend' },
        { label: 'Plus Jakarta', value: 'plus_jakarta_sans' },
    ];
    const fontSizeOptions: DoraSegmentedOption<FontSizePreference>[] = [
        { label: 'Small', value: 'sm' },
        { label: 'Medium', value: 'md' },
        { label: 'Large', value: 'lg' },
        { label: 'Extra large', value: 'xl' },
    ];

    function modeAndFamilyForKey(key: string): { mode: ThemeMode; familyKey: string } {
        const decoded = familyAndModeOf(key);
        if (decoded) return { mode: decoded.mode, familyKey: decoded.family.key };
        return { mode: 'system', familyKey: THEME_FAMILIES[0]!.key };
    }

    const initialThemeKey: string = currentUser.value?.theme ?? 'system';
    const initial = modeAndFamilyForKey(initialThemeKey);
    const modeDraft = ref<ThemeMode>(initial.mode);
    const familyDraft = ref<string>(initial.familyKey);

    const osCurrentlyDark = ref<boolean>(osPrefersDark());
    if (typeof window !== 'undefined' && window.matchMedia) {
        const mql = window.matchMedia('(prefers-color-scheme: dark)');
        const onChange = (e: MediaQueryListEvent) => { osCurrentlyDark.value = e.matches; };
        if ('addEventListener' in mql) {
            mql.addEventListener('change', onChange);
        }
    }

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
            caption: toastCaption(err)
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

    async function onModeChange(value: ThemeMode) {
        const family = THEME_FAMILIES.find((f) => f.key === familyDraft.value)
            ?? THEME_FAMILIES[0]!;
        const next = themeKeyFor(value, family);
        modeDraft.value = value;
        await onThemeChange(next);
    }

    async function onFamilyChange(family: ThemeFamily) {
        familyDraft.value = family.key;
        const next = themeKeyFor(modeDraft.value, family);
        await onThemeChange(next);
    }

    async function onFontFamilyChange(value: FontFamilyPreference) {
        const previous = currentUser.value?.font_family ?? 'default';
        fontFamilyDraft.value = value;
        const result = await update('Font updated.', () =>
            authStore.updateMeAsync({ font_family: value })
        );
        if (result === null) fontFamilyDraft.value = previous;
    }

    async function onFontSizeChange(value: FontSizePreference) {
        const previous = currentUser.value?.font_size ?? 'md';
        fontSizeDraft.value = value;
        const result = await update('Text size updated.', () =>
            authStore.updateMeAsync({ font_size: value })
        );
        if (result === null) fontSizeDraft.value = previous;
    }
</script>

<style scoped lang="scss">
    .settings-page {
        display: flex;
        flex-direction: column;
    }
    .settings-divider {
        border: 0;
        height: 1px;
        background: color-mix(in srgb, var(--text-primary) 8%, transparent);
        margin: 0;
    }

    .theme-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
        gap: 12px;
    }
    .theme-card {
        position: relative;
        appearance: none;
        background: var(--surface-component);
        border: 1.5px solid var(--border-default);
        border-radius: var(--radius-md, 8px);
        padding: 10px;
        text-align: left;
        transition: border-color 120ms ease;
        display: flex;
        flex-direction: column;
        gap: 8px;
        cursor: pointer;
    }
    .theme-card:hover {
        border-color: var(--border-strong);
    }
    .theme-card--active {
        border-color: var(--q-accent);
        border-width: 2px;
    }
    .theme-card__badge {
        position: absolute;
        top: 6px;
        right: 6px;
        color: var(--q-accent);
        background: var(--surface-component);
        border-radius: 50%;
    }
    .theme-swatch {
        display: flex;
        gap: 3px;
        height: 32px;
        border-radius: var(--radius-sm, 4px);
        overflow: hidden;
        background: var(--surface-sunken);
    }
    .theme-swatch-strip {
        flex: 1 1 0;
        height: 100%;
    }
    .theme-card__label {
        font-size: 0.875rem;
        font-weight: 600;
        color: var(--text-primary);
    }
</style>
