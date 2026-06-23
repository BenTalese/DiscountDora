<template>
    <div class="settings-shell q-pa-md">
        <div class="row items-center q-mb-md">
            <div class="text-caption dora-text-muted">
                Manage your account and, if you're an admin, the install itself.
            </div>
        </div>

        <div class="row q-col-gutter-md">
            <!-- Side nav ──────────────────────────────────────────────── -->
            <aside class="col-12 col-md-3">
                <q-card flat bordered>
                    <q-list>
                        <q-item-label header class="settings-group-header">
                            Account
                        </q-item-label>
                        <template v-for="entry in accountSections" :key="entryKey(entry)">
                            <!-- Sub-group: non-clickable header + indented leaves -->
                            <template v-if="'subheader' in entry">
                                <q-item-label header class="settings-subheader">
                                    {{ entry.subheader }}
                                </q-item-label>
                                <q-item
                                    v-for="item in entry.items"
                                    :key="item.path"
                                    clickable
                                    :to="item.path"
                                    active-class="settings-section-active"
                                    class="settings-subitem"
                                    exact
                                >
                                    <q-item-section avatar><q-icon :name="item.icon" /></q-item-section>
                                    <q-item-section><q-item-label>{{ item.label }}</q-item-label></q-item-section>
                                </q-item>
                            </template>
                            <q-item
                                v-else
                                clickable
                                :to="entry.path"
                                active-class="settings-section-active"
                                exact
                            >
                                <q-item-section avatar><q-icon :name="entry.icon" /></q-item-section>
                                <q-item-section><q-item-label>{{ entry.label }}</q-item-label></q-item-section>
                            </q-item>
                        </template>

                        <q-separator class="q-my-sm" />
                        <q-item-label header class="settings-group-header">
                            Kitchen setup
                        </q-item-label>
                        <template v-for="entry in kitchenSetupSections" :key="entryKey(entry)">
                            <template v-if="'subheader' in entry">
                                <q-item-label header class="settings-subheader">
                                    {{ entry.subheader }}
                                </q-item-label>
                                <q-item
                                    v-for="item in entry.items"
                                    :key="item.path"
                                    clickable
                                    :to="item.path"
                                    active-class="settings-section-active"
                                    class="settings-subitem"
                                    exact
                                >
                                    <q-item-section avatar><q-icon :name="item.icon" /></q-item-section>
                                    <q-item-section><q-item-label>{{ item.label }}</q-item-label></q-item-section>
                                </q-item>
                            </template>
                            <q-item
                                v-else
                                clickable
                                :to="entry.path"
                                active-class="settings-section-active"
                                exact
                            >
                                <q-item-section avatar><q-icon :name="entry.icon" /></q-item-section>
                                <q-item-section><q-item-label>{{ entry.label }}</q-item-label></q-item-section>
                            </q-item>
                        </template>

                        <template v-if="isAdmin">
                            <q-separator class="q-my-sm" />
                            <q-item-label header class="settings-group-header">
                                <q-icon :name="ICONS.shield" size="14px" class="q-mr-xs" />
                                Admin · global
                            </q-item-label>
                            <template v-for="entry in adminSections" :key="entryKey(entry)">
                                <template v-if="'subheader' in entry">
                                    <q-item-label header class="settings-subheader">
                                        {{ entry.subheader }}
                                    </q-item-label>
                                    <q-item
                                        v-for="item in entry.items"
                                        :key="item.path"
                                        clickable
                                        :to="item.path"
                                        active-class="settings-section-active"
                                        class="settings-subitem"
                                        exact
                                    >
                                        <q-item-section avatar><q-icon :name="item.icon" /></q-item-section>
                                        <q-item-section><q-item-label>{{ item.label }}</q-item-label></q-item-section>
                                    </q-item>
                                </template>
                                <q-item
                                    v-else
                                    clickable
                                    :to="entry.path"
                                    active-class="settings-section-active"
                                    exact
                                >
                                    <q-item-section avatar><q-icon :name="entry.icon" /></q-item-section>
                                    <q-item-section><q-item-label>{{ entry.label }}</q-item-label></q-item-section>
                                </q-item>
                            </template>
                        </template>
                    </q-list>
                </q-card>

                <q-banner
                    v-if="!isAdmin"
                    class="dora-bg-sunken dora-text-secondary q-mt-md text-caption"
                    dense
                    rounded
                >
                    <template #avatar>
                        <q-icon :name="ICONS.lock" size="18px" />
                    </template>
                    Admin (global) settings are only visible to admin accounts.
                </q-banner>
            </aside>

            <!-- Active section ─────────────────────────────────────────── -->
            <main class="col-12 col-md-9">
                <router-view />
            </main>
        </div>
    </div>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import { storeToRefs } from 'pinia';
    import { useAuthStore } from 'src/stores/authStore';

    // IMPL_PLAN_SETTINGS_REBUILD §2.1 — three top-level groups, Account first.
    // §6.5 (user pick): nested groupings render as an indented sub-list under a
    // non-clickable sub-header (Recipe taxonomies under Kitchen setup; System
    // under Admin). Captions dropped — label + icon only.
    // NOTE: the SettingsNavGroup.vue extraction + visual rebuild are Phase 3;
    // the per-group template here is intentionally repeated until then (the
    // shared structure is what Phase 3 lifts out).
    type NavLeaf = { path: string; label: string; icon: string };
    type NavSubGroup = { subheader: string; items: NavLeaf[] };
    type NavEntry = NavLeaf | NavSubGroup;

    const entryKey = (e: NavEntry): string =>
        'subheader' in e ? `sub:${e.subheader}` : e.path;

    const accountSections: NavEntry[] = [
        { path: '/settings/account', label: 'Account', icon: ICONS.person },
        { path: '/settings/preferences', label: 'Preferences', icon: ICONS.tune },
        { path: '/settings/notifications', label: 'Notifications', icon: ICONS.notifications },
        { path: '/settings/money', label: 'Money', icon: ICONS.savings },
        { path: '/settings/voice', label: 'Voice', icon: ICONS.record_voice_over },
        { path: '/settings/nutrition', label: 'Nutrition', icon: ICONS.restaurant },
        { path: '/settings/about', label: 'About', icon: ICONS.info },
    ];

    const kitchenSetupSections: NavEntry[] = [
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

    const adminSections: NavEntry[] = [
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

<style scoped>
    .settings-section-active {
        background: var(--brand-primary-soft);
        font-weight: 600;
    }
    .settings-group-header {
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: var(--text-muted);
        padding-top: 12px;
    }
    /* §6.5 — second-level sub-header + indented children. */
    .settings-subheader {
        font-size: 0.68rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--text-muted);
        padding-top: 8px;
        padding-left: 28px;
        min-height: unset;
    }
    .settings-subitem {
        padding-left: 28px;
    }
</style>
