<template>
    <div class="settings-shell q-pa-md">
        <div class="row items-center q-mb-md">
            <div class="text-h5">Settings</div>
            <q-space />
            <div class="text-caption text-grey">
                Manage your account and, if you're an admin, the install itself.
            </div>
        </div>

        <div class="row q-col-gutter-md">
            <!-- Side nav ──────────────────────────────────────────────── -->
            <aside class="col-12 col-md-3">
                <q-card flat bordered>
                    <q-list>
                        <q-item-label header class="settings-group-header">
                            Your settings
                        </q-item-label>
                        <q-item
                            v-for="section in personalSections"
                            :key="section.path"
                            clickable
                            :to="section.path"
                            active-class="settings-section-active"
                            exact
                        >
                            <q-item-section avatar>
                                <q-icon :name="section.icon" />
                            </q-item-section>
                            <q-item-section>
                                <q-item-label>{{ section.label }}</q-item-label>
                                <q-item-label caption>{{ section.caption }}</q-item-label>
                            </q-item-section>
                        </q-item>

                        <template v-if="isAdmin">
                            <q-separator class="q-my-sm" />
                            <q-item-label header class="settings-group-header">
                                <q-icon name="shield" size="14px" class="q-mr-xs" />
                                Admin · global
                            </q-item-label>
                            <q-item
                                v-for="section in adminSections"
                                :key="section.path"
                                clickable
                                :to="section.path"
                                active-class="settings-section-active"
                                exact
                            >
                                <q-item-section avatar>
                                    <q-icon :name="section.icon" />
                                </q-item-section>
                                <q-item-section>
                                    <q-item-label>{{ section.label }}</q-item-label>
                                    <q-item-label caption>{{ section.caption }}</q-item-label>
                                </q-item-section>
                            </q-item>
                        </template>
                    </q-list>
                </q-card>

                <q-banner
                    v-if="!isAdmin"
                    class="bg-grey-2 text-grey-8 q-mt-md text-caption"
                    dense
                    rounded
                >
                    <template #avatar>
                        <q-icon name="lock" size="18px" />
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
    import { storeToRefs } from 'pinia';
    import { useAuthStore } from 'src/stores/authStore';

    type Section = { path: string; label: string; caption: string; icon: string };

    const personalSections: Section[] = [
        {
            path: '/settings/preferences',
            label: 'Preferences',
            caption: 'Email schedule and personal toggles',
            icon: 'tune'
        },
        {
            path: '/settings/stock-locations',
            label: 'Stock locations',
            caption: 'Pantry, Fridge, Freezer…',
            icon: 'place'
        },
        {
            path: '/settings/stock-groups',
            label: 'Stock groups',
            caption: 'Tag items for filtering',
            icon: 'label'
        },
        {
            path: '/settings/account',
            label: 'Account',
            caption: 'Your profile and sign-out',
            icon: 'person'
        },
        {
            path: '/settings/about',
            label: 'About',
            caption: 'Version + project info',
            icon: 'info'
        }
    ];

    const adminSections: Section[] = [
        {
            path: '/settings/admin/merchants',
            label: 'Merchants',
            caption: 'Enable/disable scrapers, health',
            icon: 'storefront'
        },
        {
            path: '/settings/admin/users',
            label: 'Users',
            caption: 'Accounts, admin role, deals subs',
            icon: 'group'
        },
        {
            path: '/settings/admin/system',
            label: 'System',
            caption: 'Install-wide toggles',
            icon: 'settings_applications'
        }
    ];

    const { isAdmin } = storeToRefs(useAuthStore());
</script>

<style scoped>
    .settings-section-active {
        background: rgba(245, 196, 98, 0.18);
        font-weight: 600;
    }
    .settings-group-header {
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #888;
        padding-top: 12px;
    }
</style>
