<template>
    <!-- FU-609 / R-036 — app-shell root: <q-page :style-fn> gives the desktop
         dual-scroll shell its height from the *live* layout offset instead of a
         hardcoded `calc(100dvh - 64px)` (which rotted when chrome changed, e.g.
         the OfflineBanner). On mobile the shell falls back to window-scroll — the
         media query overrides the inline height (see styles). -->
    <q-page class="settings-shell" :style-fn="pageStyleFn">
        <header class="settings-shell__header">
            <!-- FU-346: for admins, the h1 becomes a two-mode segmented
                 toggle. "Settings" holds the personal groups (Account,
                 Kitchen setup); "Admin" holds the admin sections. The
                 sidebar underneath is filtered to only the active mode's
                 groups — Admin is a peer mode, not a buried third group.
                 Non-admins see the plain h1. Sign-out is the header's
                 right-hand peer of the toggle/title. -->
            <div v-if="isAdmin" class="settings-shell__mode-toggle" role="tablist" aria-label="Settings section">
                <button
                    type="button"
                    role="tab"
                    class="settings-shell__mode-btn"
                    :class="{ 'is-active': mode === 'settings' }"
                    :aria-selected="mode === 'settings'"
                    @click="switchMode('settings')"
                >
                    Settings
                </button>
                <button
                    type="button"
                    role="tab"
                    class="settings-shell__mode-btn"
                    :class="{ 'is-active': mode === 'admin' }"
                    :aria-selected="mode === 'admin'"
                    @click="switchMode('admin')"
                >
                    <q-icon :name="ICONS.shield" size="18px" class="q-mr-xs" />
                    Admin
                </button>
            </div>
            <h1 v-else class="settings-shell__title">Settings</h1>

            <div class="settings-shell__header-actions">
                <DonateButton variant="settings" />
                <BaseButton
                    variant="danger-ghost"
                    :icon="ICONS.logout"
                    label="Sign out"
                    :loading="signingOut"
                    @click="onSignOut"
                />
            </div>
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
    </q-page>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import { storeToRefs } from 'pinia';
    import { useAuthStore } from 'src/stores/authStore';
    import { useUnlinkedIngredientsStore } from 'src/stores/unlinkedIngredientsStore';
    import BaseButton from 'src/components/BaseButton.vue';
    import DonateButton from 'src/components/donate/DonateButton.vue';
    import SettingsNavGroup, { type SettingsNavEntry, type SettingsNavLeaf } from 'src/components/settings/SettingsNavGroup.vue';
    import SettingsMobileNav, { type SettingsNavGroupDef } from 'src/components/settings/SettingsMobileNav.vue';
    import { useScanningEnabled } from 'src/composables/useScanningEnabled';
    import { useFeatureFlags } from 'src/composables/useFeatureFlags';
    import { suppressUnsavedChangesGuard } from 'src/composables/useUnsavedChangesGuard';
    import { computed, nextTick, ref, watch } from 'vue';
    import { useRoute, useRouter } from 'vue-router';

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
        { path: '/settings/voice', label: 'Voice', icon: ICONS.record_voice_over },
        { path: '/settings/nutrition', label: 'Nutrition', icon: ICONS.restaurant },
        { path: '/settings/assistant', label: 'Assistant', icon: ICONS.smart_toy },
        { path: '/settings/about', label: 'About', icon: ICONS.info },
    ];

    // QR labels only surfaces when scanning is enabled (matches
    // the install-wide gate the page itself enforces). Hiding the nav
    // entry keeps the sidebar honest for installs that never opted in.
    const { scanningEnabled } = useScanningEnabled();
    // Money is an install-wide "kitchen setup" concern now (household budget +
    // dollar surfaces), gated on the install money flag — not a personal
    // account section. Hidden entirely when the install has money off.
    const { money: moneyEnabled } = useFeatureFlags();

    // Attention badge on the Unlinked-ingredients nav entry. The store caches
    // the count (server owns the grouping, R-003); we refetch on mount so each
    // settings visit reflects the current backlog, and the page keeps it in
    // sync after every link.
    const unlinkedStore = useUnlinkedIngredientsStore();
    const { count: unlinkedCount } = storeToRefs(unlinkedStore);
    void unlinkedStore.refreshAsync().catch(() => { /* badge just stays 0 */ });

    const kitchenSetupSections = computed<SettingsNavEntry[]>(() => {
        const base: SettingsNavEntry[] = [
            { path: '/settings/kitchen-setup/stock-locations', label: 'Stock locations', icon: ICONS.place },
            { path: '/settings/kitchen-setup/stock-groups', label: 'Stock groups', icon: ICONS.tag_multiple },
            { path: '/settings/kitchen-setup/stores', label: 'Stores', icon: ICONS.store },
        ];
        if (moneyEnabled.value) {
            base.push({ path: '/settings/money', label: 'Money', icon: ICONS.savings });
        }
        if (scanningEnabled.value) {
            base.push({ path: '/settings/kitchen-setup/qr-labels', label: 'QR labels', icon: ICONS.qr_code });
        }
        // Recipe-ingredient bulk-linker — moved out of Admin → Data
        // (user-curated recipe data, no admin guard on its endpoints).
        base.push({
            path: '/settings/kitchen-setup/unlinked-ingredients',
            label: 'Unlinked ingredients',
            icon: ICONS.link,
            badge: unlinkedCount.value,
        });
        // Recipe taxonomies — flat leaves (no sub-group), each with a
        // distinct icon: globe for world cuisines, shape for categories,
        // blender for equipment/tools, clock for time-of-day meal slots,
        // leaf for dietary tags.
        base.push(
            { path: '/settings/kitchen-setup/recipe-cuisines', label: 'Cuisines', icon: ICONS.public },
            { path: '/settings/kitchen-setup/recipe-categories', label: 'Categories', icon: ICONS.category },
            { path: '/settings/kitchen-setup/recipe-tools', label: 'Tools', icon: ICONS.blender },
            { path: '/settings/kitchen-setup/recipe-meal-slots', label: 'Meal slots', icon: ICONS.schedule },
            { path: '/settings/kitchen-setup/recipe-dietary-tags', label: 'Dietary tags', icon: ICONS.eco },
        );
        return base;
    });

    const adminSystemItems = computed<SettingsNavLeaf[]>(() => {
        const items: SettingsNavLeaf[] = [
            { path: '/settings/admin/system/region', label: 'Region & locale', icon: ICONS.language },
            { path: '/settings/admin/system/alerts', label: 'Alert thresholds', icon: ICONS.notifications },
            { path: '/settings/admin/system/stocktake', label: 'Stocktake', icon: ICONS.fact_check },
            { path: '/settings/admin/system/stock', label: 'Stock', icon: ICONS.inventory_2 },
            { path: '/settings/admin/system/meal-reconcile', label: 'Meal reconciliation', icon: ICONS.event_note },
            { path: '/settings/admin/system/cooking', label: 'Cooking', icon: ICONS.restaurant },
            { path: '/settings/admin/system/features', label: 'Features', icon: ICONS.tune },
        ];
        items.push(
            // operational config that used to be env-only.
            { path: '/settings/admin/system/email', label: 'Email', icon: ICONS.mark_email_read },
            { path: '/settings/admin/system/push', label: 'Push notifications', icon: ICONS.notifications_active },
            { path: '/settings/admin/system/voice', label: 'Voice', icon: ICONS.record_voice_over },
            { path: '/settings/admin/system/hosting', label: 'Hosting', icon: ICONS.cloud_upload },
        );
        return items;
    });

    const adminSections = computed<SettingsNavEntry[]>(() => [
        { path: '/settings/admin/users', label: 'Users', icon: ICONS.group },
        {
            subheader: 'System',
            items: adminSystemItems.value,
        },
        // Data sub-group: relocated from the retired `/data`
        // shell. Backup & restore + Import land here so their chrome
        // matches every other Settings page.
        {
            subheader: 'Data',
            items: [
                { path: '/settings/admin/data/backup', label: 'Backup & restore', icon: ICONS.cloud_download },
                { path: '/settings/admin/data/import', label: 'Import', icon: ICONS.file_upload },
            ],
        },
        { path: '/settings/admin/audit-log', label: 'Audit log', icon: ICONS.fact_check },
        { path: '/settings/admin/api-access', label: 'API access', icon: ICONS.key },
    ]);

    const authStore = useAuthStore();
    const { isAdmin } = storeToRefs(authStore);

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

    // FU-346: mode is derived from the URL, so refresh / back-button /
    // deep-link all preserve it without a separate stored flag. Any
    // /settings/admin/* path is Admin mode; everything else is Settings.
    const mode = computed<'settings' | 'admin'>(() =>
        route.path.startsWith('/settings/admin') ? 'admin' : 'settings',
    );

    const router = useRouter();

    const signingOut = ref(false);
    async function onSignOut() {
        signingOut.value = true;
        // Sign-out is an intentional exit; suppress the unsaved-changes
        // guard so a page whose draft-vs-user diff goes stale the moment
        // logout clears currentUser (e.g. AccountSettings) doesn't fire
        // a false-positive "discard unsaved changes?" prompt. Cancel on
        // that prompt would also strand the app on a settings page while
        // already logged-out.
        try {
            await suppressUnsavedChangesGuard(async () => {
                await authStore.logoutAsync();
                await router.push('/login');
            });
        } finally {
            signingOut.value = false;
        }
    }

    function switchMode(next: 'settings' | 'admin') {
        if (next === mode.value) return;
        // Land on the first item of the mode's sidebar so the destination
        // matches what the user is about to see. `/settings/admin/users`
        // is the first admin section; `/settings/account` is the first
        // personal one.
        void router.push(next === 'admin' ? '/settings/admin/users' : '/settings/account');
    }

    const navGroups = computed<SettingsNavGroupDef[]>(() => {
        if (isAdmin.value && mode.value === 'admin') {
            return [{ label: 'Admin · global', items: adminSections.value, icon: ICONS.shield }];
        }
        return [
            { label: 'Account', items: accountSections },
            { label: 'Kitchen setup', items: kitchenSetupSections.value },
        ];
    });

    // FU-609 / R-036 — app-shell height from the live layout offset (header, plus
    // the OfflineBanner when it shows), replacing the old hardcoded
    // `calc(100dvh - 64px)`. Applied inline by <q-page>; the mobile media query
    // overrides it back to `height: auto` so the shell window-scrolls on <md.
    function pageStyleFn(offset: number, height: number) {
        return {
            height: height === 0 ? `calc(100vh - ${offset}px)` : `${height - offset}px`,
        };
    }
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
        /* FU-609 / R-036 — height comes from the <q-page :style-fn> (viewport −
           live layout offset), not a hardcoded `calc(100dvh - 64px)` that
           ignored the real chrome height. Desktop fills the viewport under the
           toolbar, then the sidebar + main pane each scroll independently. */
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
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 16px;
    }
    .settings-shell__header-actions {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .settings-shell__title {
        margin: 0;
        font-size: 1.5rem;
        font-weight: 700;
        letter-spacing: -0.01em;
        color: var(--text-primary);
        line-height: 1.2;
    }
    /* FU-346 — admin-only mode toggle sits where the h1 does. Segmented
       control: two pills inside a bordered pill container. Active pill
       takes the brand-primary background; inactive pill stays flat but
       shows a hover affordance so it clearly reads as clickable. */
    .settings-shell__mode-toggle {
        display: inline-flex;
        gap: 4px;
        padding: 4px;
        border-radius: 999px;
        background: var(--surface-sunken);
        border: 1px solid var(--border-default, transparent);
    }
    .settings-shell__mode-btn {
        display: inline-flex;
        align-items: center;
        padding: 8px 20px;
        border: none;
        border-radius: 999px;
        background: transparent;
        color: var(--text-primary);
        font: inherit;
        font-size: 1.15rem;
        font-weight: 700;
        letter-spacing: -0.01em;
        line-height: 1.2;
        cursor: pointer;
        transition: background 0.15s ease, color 0.15s ease;
    }
    .settings-shell__mode-btn:hover:not(.is-active) {
        background: var(--overlay-hover, rgba(0, 0, 0, 0.05));
    }
    .settings-shell__mode-btn:focus-visible {
        outline: 2px solid var(--focus-ring);
        outline-offset: 2px;
    }
    .settings-shell__mode-btn.is-active {
        background: var(--brand-primary);
        color: var(--text-inverse);
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
            /* !important overrides the inline height the <q-page :style-fn> sets
               (FU-609) so mobile reverts to a single window-scrolled column. */
            height: auto !important;
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
