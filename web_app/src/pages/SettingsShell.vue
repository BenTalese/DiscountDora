<template>
    <div class="settings-shell">
        <header class="settings-shell__header">
            <h1 class="settings-shell__title">Settings</h1>
        </header>

        <div class="settings-shell__body">
            <aside class="settings-shell__nav">
                <SettingsNavGroup label="Account" :items="accountSections" />
                <SettingsNavGroup label="Kitchen setup" :items="kitchenSetupSections" />
                <SettingsNavGroup
                    v-if="isAdmin"
                    label="Admin · global"
                    :items="adminSections"
                    :icon="ICONS.shield"
                />
            </aside>

            <main class="settings-shell__main">
                <router-view />
            </main>
        </div>
    </div>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import { storeToRefs } from 'pinia';
    import { useAuthStore } from 'src/stores/authStore';
    import SettingsNavGroup, { type SettingsNavEntry } from 'src/components/settings/SettingsNavGroup.vue';

    // IMPL_PLAN_SETTINGS_REBUILD §2.1 — three top-level groups, Account first.
    // §6.5 (user pick): nested groupings render as an indented sub-list under a
    // non-clickable sub-header (Recipe taxonomies under Kitchen setup; System
    // under Admin). Captions dropped — label + icon only.
    // Phase 3 §2.7: the per-group template is now lifted into SettingsNavGroup;
    // the §2.8 shell sheds its card chrome, drops the non-admin banner, and the
    // page header carries the real h1 (was a soft caption).

    const accountSections: SettingsNavEntry[] = [
        { path: '/settings/account', label: 'Account', icon: ICONS.person },
        { path: '/settings/preferences', label: 'Preferences', icon: ICONS.tune },
        { path: '/settings/notifications', label: 'Notifications', icon: ICONS.notifications },
        { path: '/settings/money', label: 'Money', icon: ICONS.savings },
        { path: '/settings/voice', label: 'Voice', icon: ICONS.record_voice_over },
        { path: '/settings/nutrition', label: 'Nutrition', icon: ICONS.restaurant },
        { path: '/settings/about', label: 'About', icon: ICONS.info },
    ];

    const kitchenSetupSections: SettingsNavEntry[] = [
        { path: '/settings/kitchen-setup/stock-locations', label: 'Stock locations', icon: ICONS.place },
        { path: '/settings/kitchen-setup/stock-groups', label: 'Stock groups', icon: ICONS.label },
        { path: '/settings/kitchen-setup/stores', label: 'Stores', icon: ICONS.store },
        {
            subheader: 'Recipe taxonomies',
            items: [
                { path: '/settings/kitchen-setup/recipe-cuisines', label: 'Cuisines', icon: ICONS.menu_book },
                { path: '/settings/kitchen-setup/recipe-categories', label: 'Categories', icon: ICONS.menu_book },
                { path: '/settings/kitchen-setup/recipe-tools', label: 'Tools', icon: ICONS.menu_book },
                { path: '/settings/kitchen-setup/recipe-meal-slots', label: 'Meal slots', icon: ICONS.menu_book },
                { path: '/settings/kitchen-setup/recipe-dietary-tags', label: 'Dietary tags', icon: ICONS.label },
            ],
        },
    ];

    const adminSections: SettingsNavEntry[] = [
        { path: '/settings/admin/users', label: 'Users', icon: ICONS.group },
        {
            subheader: 'System',
            items: [
                { path: '/settings/admin/system/timezone', label: 'Timezone', icon: ICONS.event },
                { path: '/settings/admin/system/alerts', label: 'Alert thresholds', icon: ICONS.notifications },
                { path: '/settings/admin/system/assistant', label: 'AI assistant', icon: ICONS.smart_toy },
                { path: '/settings/admin/system/features', label: 'Features', icon: ICONS.tune },
            ],
        },
        { path: '/settings/admin/audit-log', label: 'Audit log', icon: ICONS.fact_check },
        { path: '/settings/admin/api-access', label: 'API access', icon: ICONS.key },
    ];

    const { isAdmin } = storeToRefs(useAuthStore());
</script>

<style scoped lang="scss">
    .settings-shell {
        padding: 28px;
        max-width: 1280px;
        margin: 0 auto;
    }
    .settings-shell__header {
        margin-bottom: 20px;
    }
    .settings-shell__title {
        margin: 0;
        font-size: 1.5rem;
        font-weight: 700;
        letter-spacing: -0.01em;
        color: var(--text-primary);
        line-height: 1.2;
    }
    .settings-shell__body {
        display: grid;
        grid-template-columns: 232px 1fr;
        gap: 40px;
        align-items: flex-start;
    }
    .settings-shell__nav {
        position: sticky;
        top: 16px;
        align-self: flex-start;
        display: flex;
        flex-direction: column;
        gap: 4px;
    }
    .settings-shell__main {
        min-width: 0;
    }

    @media (max-width: 1023px) {
        .settings-shell { padding: 20px; }
        .settings-shell__body {
            grid-template-columns: 1fr;
            gap: 20px;
        }
        .settings-shell__nav {
            position: static;
            flex-direction: row;
            overflow-x: auto;
            scrollbar-width: none;
        }
        .settings-shell__nav::-webkit-scrollbar { display: none; }
    }
</style>
