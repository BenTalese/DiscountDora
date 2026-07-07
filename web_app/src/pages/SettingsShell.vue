<template>
    <div class="settings-shell">
        <header class="settings-shell__header">
            <h1 class="settings-shell__title">Settings</h1>
        </header>

        <!-- Mobile (<md): top tab strip (§6.3). Shown via CSS below. -->
        <SettingsMobileNav class="settings-shell__mnav" :groups="navGroups" />

        <div class="settings-shell__body">
            <aside class="settings-shell__nav">
                <SettingsNavGroup
                    v-for="group in navGroups"
                    :key="group.label"
                    :label="group.label"
                    :items="group.items"
                    :icon="group.icon"
                />
            </aside>

            <main ref="mainEl" class="settings-shell__main">
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
    import SettingsMobileNav, { type SettingsNavGroupDef } from 'src/components/settings/SettingsMobileNav.vue';
    import { useScanningEnabled } from 'src/composables/useScanningEnabled';
    import { computed, nextTick, ref, watch } from 'vue';
    import { useRoute } from 'vue-router';

    // IMPL_PLAN_SETTINGS_REBUILD §2.1 — three top-level groups, Account first.
    // §6.5 (user pick): nested groupings render as an indented sub-list under a
    // non-clickable sub-header (Recipe taxonomies under Kitchen setup; System
    // under Admin). Captions dropped — label + icon only.
    // §6.3 (user pick): on <md the sidebar is replaced by SettingsMobileNav (a
    // top tab strip). Both navs read the SAME `navGroups` definition (R-003 —
    // one source for the IA), so they can't drift.

    const accountSections: SettingsNavEntry[] = [
        { path: '/settings/account', label: 'Account', icon: ICONS.person },
        { path: '/settings/preferences', label: 'Preferences', icon: ICONS.tune },
        { path: '/settings/notifications', label: 'Notifications', icon: ICONS.notifications },
        { path: '/settings/money', label: 'Money', icon: ICONS.savings },
        { path: '/settings/voice', label: 'Voice', icon: ICONS.record_voice_over },
        { path: '/settings/nutrition', label: 'Nutrition', icon: ICONS.restaurant },
        { path: '/settings/assistant', label: 'Assistant', icon: ICONS.smart_toy },
        { path: '/settings/about', label: 'About', icon: ICONS.info },
    ];

    // QR labels only surfaces when scanning is enabled (matches
    // the install-wide gate the page itself enforces). Hiding the nav
    // entry keeps the sidebar honest for installs that never opted in.
    const { scanningEnabled } = useScanningEnabled();

    const kitchenSetupSections = computed<SettingsNavEntry[]>(() => {
        const base: SettingsNavEntry[] = [
            { path: '/settings/kitchen-setup/stock-locations', label: 'Stock locations', icon: ICONS.place },
            { path: '/settings/kitchen-setup/stock-groups', label: 'Stock groups', icon: ICONS.label },
            { path: '/settings/kitchen-setup/stores', label: 'Stores', icon: ICONS.store },
        ];
        if (scanningEnabled.value) {
            base.push({ path: '/settings/kitchen-setup/qr-labels', label: 'QR labels', icon: ICONS.qr_code });
        }
        base.push({
            subheader: 'Recipe taxonomies',
            items: [
                { path: '/settings/kitchen-setup/recipe-cuisines', label: 'Cuisines', icon: ICONS.menu_book },
                { path: '/settings/kitchen-setup/recipe-categories', label: 'Categories', icon: ICONS.menu_book },
                { path: '/settings/kitchen-setup/recipe-tools', label: 'Tools', icon: ICONS.menu_book },
                { path: '/settings/kitchen-setup/recipe-meal-slots', label: 'Meal slots', icon: ICONS.menu_book },
                { path: '/settings/kitchen-setup/recipe-dietary-tags', label: 'Dietary tags', icon: ICONS.label },
            ],
        });
        return base;
    });

    const adminSections: SettingsNavEntry[] = [
        { path: '/settings/admin/users', label: 'Users', icon: ICONS.group },
        {
            subheader: 'System',
            items: [
                { path: '/settings/admin/system/timezone', label: 'Timezone', icon: ICONS.event },
                { path: '/settings/admin/system/locale', label: 'Currency & locale', icon: ICONS.language },
                { path: '/settings/admin/system/alerts', label: 'Alert thresholds', icon: ICONS.notifications },
                { path: '/settings/admin/system/stocktake', label: 'Stocktake', icon: ICONS.fact_check },
                { path: '/settings/admin/system/stock', label: 'Stock', icon: ICONS.inventory_2 },
                { path: '/settings/admin/system/assistant', label: 'AI assistant', icon: ICONS.smart_toy },
                { path: '/settings/admin/system/features', label: 'Features', icon: ICONS.tune },
                // operational config that used to be env-only.
                { path: '/settings/admin/system/email', label: 'Email', icon: ICONS.mark_email_read },
                { path: '/settings/admin/system/push', label: 'Push notifications', icon: ICONS.notifications_active },
                { path: '/settings/admin/system/voice', label: 'Voice', icon: ICONS.record_voice_over },
                { path: '/settings/admin/system/hosting', label: 'Hosting', icon: ICONS.cloud_upload },
            ],
        },
        // Data sub-group: relocated from the retired `/data`
        // shell. Backup & restore + Import land here so their chrome
        // matches every other Settings page.
        {
            subheader: 'Data',
            items: [
                { path: '/settings/admin/data/backup', label: 'Backup & restore', icon: ICONS.cloud_download },
                { path: '/settings/admin/data/import', label: 'Import', icon: ICONS.file_upload },
                // IMPL_PLAN_RECIPE_IMPORTER §Chunk 6 — bulk-linker page.
                { path: '/settings/admin/data/unlinked-ingredients', label: 'Unlinked ingredients', icon: ICONS.link },
            ],
        },
        { path: '/settings/admin/audit-log', label: 'Audit log', icon: ICONS.fact_check },
        { path: '/settings/admin/api-access', label: 'API access', icon: ICONS.key },
    ];

    const { isAdmin } = storeToRefs(useAuthStore());

    // Independent-scroll shell: the sidebar and the main pane each own their
    // own overflow (see styles below), so the *window* never needs to scroll
    // while inside settings. That in turn means the router's global
    // `scrollBehavior: {top:0}` has nothing to yank when the user clicks a
    // nav item after scrolling deep into a section — no jarring jump. But
    // switching leaves should still land the user at the top of the new
    // section (typical settings expectation), so reset the main pane's
    // scrollTop on route path change. `nextTick` waits for the fade
    // transition's new component to mount before we scroll it.
    const mainEl = ref<HTMLElement | null>(null);
    const route = useRoute();
    watch(
        () => route.path,
        () => {
            void nextTick(() => {
                if (mainEl.value) mainEl.value.scrollTop = 0;
            });
        },
    );

    const navGroups = computed<SettingsNavGroupDef[]>(() => [
        { label: 'Account', items: accountSections },
        { label: 'Kitchen setup', items: kitchenSetupSections.value },
        ...(isAdmin.value
            ? [{ label: 'Admin · global', items: adminSections, icon: ICONS.shield }]
            : []),
    ]);
</script>

<style scoped lang="scss">
    /* Desktop shell (>= md): fill the viewport under the app toolbar, then
       let the sidebar and the main pane each scroll independently. Keeps
       the sidebar always in view no matter how far the user scrolls, and
       (with the scrollTop reset above) means clicking a nav item after
       scrolling deep into a section doesn't jarringly jump the whole
       window — the router's window-scroll reset now has nothing to yank
       because the window itself isn't the scroller. */
    .settings-shell {
        /* q-header dora-titlebar is 64px; subtract to fit under it without
           double-scroll. dvh keeps it correct on mobile browsers that
           collapse their address bar. */
        height: calc(100dvh - 64px);
        max-width: 1280px;
        margin: 0 auto;
        padding: 28px 28px 0;
        display: flex;
        flex-direction: column;
        min-height: 0;
    }
    .settings-shell__header {
        margin-bottom: 20px;
        flex: 0 0 auto;
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
        flex: 1 1 auto;
        min-height: 0; /* required for children's overflow to compute */
        display: grid;
        grid-template-columns: 232px 1fr;
        gap: 40px;
        align-items: stretch;
    }
    .settings-shell__nav {
        display: flex;
        flex-direction: column;
        gap: 4px;
        overflow-y: auto;
        min-height: 0;
        /* Breathing room so the last nav item isn't flush to the viewport
           edge when the list overflows. */
        padding-bottom: 20px;
    }
    .settings-shell__main {
        min-width: 0;
        overflow-y: auto;
        min-height: 0;
        /* The main pane owns bottom padding so long forms don't jam into
           the viewport edge; the shell itself has padding: 0 on the bottom
           so the scrollbar runs the full height. */
        padding-bottom: 28px;
    }

    // §6.3 — the mobile tab strip is hidden on desktop; the sidebar shows.
    .settings-shell__mnav {
        display: none;
    }

    /* Mobile: fall back to a single-column, window-scrolled layout. The
       top-tab strip replaces the sidebar; there's no dual-scroll to
       preserve, and internal overflow on a mobile viewport just makes the
       page feel truncated. */
    @media (max-width: 1023px) {
        .settings-shell {
            height: auto;
            padding: 20px;
            display: block;
        }
        .settings-shell__nav { display: none; }
        .settings-shell__mnav {
            display: flex;
            margin-bottom: 20px;
        }
        .settings-shell__body {
            display: block;
        }
        .settings-shell__main {
            overflow: visible;
            padding-bottom: 0;
        }
    }
</style>
