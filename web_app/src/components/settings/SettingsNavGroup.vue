<template>
    <nav class="settings-nav-group" :aria-label="label">
        <div class="settings-nav-group__eyebrow">
            <q-icon v-if="icon" :name="icon" size="12px" class="q-mr-xs" />
            {{ label }}
        </div>
        <ul class="settings-nav-group__list">
            <template v-for="entry in items" :key="entryKey(entry)">
                <template v-if="'subheader' in entry">
                    <li class="settings-nav-group__subheader">{{ entry.subheader }}</li>
                    <li v-for="item in entry.items" :key="item.path" class="settings-nav-group__item--sub">
                        <router-link
                            :to="item.path"
                            class="settings-nav-group__link"
                            active-class="settings-nav-group__link--active"
                            exact-active-class="settings-nav-group__link--active"
                        >
                            <q-icon :name="item.icon" size="18px" class="settings-nav-group__icon" />
                            <span class="settings-nav-group__label">{{ item.label }}</span>
                        </router-link>
                    </li>
                </template>
                <li v-else>
                    <router-link
                        :to="entry.path"
                        class="settings-nav-group__link"
                        active-class="settings-nav-group__link--active"
                        exact-active-class="settings-nav-group__link--active"
                    >
                        <q-icon :name="entry.icon" size="18px" class="settings-nav-group__icon" />
                        <span class="settings-nav-group__label">{{ entry.label }}</span>
                    </router-link>
                </li>
            </template>
        </ul>
    </nav>
</template>

<script setup lang="ts">
    // IMPL_PLAN_SETTINGS_REBUILD §2.7 — side-nav group. Drops the card
    // wrapper + captions; eyebrow group header (11px / uppercase /
    // weight 600 / muted); active state = soft brand tint + 3px accent
    // left-edge bar. §6.5 (user pick): nested groupings use indented
    // sub-list under a non-clickable sub-header.
    export interface SettingsNavLeaf {
        path: string;
        label: string;
        icon: string;
    }
    export interface SettingsNavSubGroup {
        subheader: string;
        items: SettingsNavLeaf[];
    }
    export type SettingsNavEntry = SettingsNavLeaf | SettingsNavSubGroup;

    defineProps<{
        label: string;
        items: SettingsNavEntry[];
        icon?: string;
    }>();

    function entryKey(e: SettingsNavEntry): string {
        return 'subheader' in e ? `sub:${e.subheader}` : e.path;
    }
</script>

<style scoped lang="scss">
    .settings-nav-group {
        display: flex;
        flex-direction: column;
        gap: 4px;
    }
    .settings-nav-group + .settings-nav-group {
        margin-top: 18px;
    }
    .settings-nav-group__eyebrow {
        display: flex;
        align-items: center;
        font-size: 0.6875rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--text-muted);
        padding: 4px 12px;
    }
    .settings-nav-group__list {
        list-style: none;
        margin: 0;
        padding: 0;
        display: flex;
        flex-direction: column;
        gap: 2px;
    }
    .settings-nav-group__subheader {
        font-size: 0.6875rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: var(--text-muted);
        padding: 8px 12px 2px 28px;
    }
    .settings-nav-group__link {
        position: relative;
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 8px 12px;
        min-height: 36px;
        border-radius: 6px;
        color: var(--text-primary);
        text-decoration: none;
        font-size: 0.875rem;
        line-height: 1.2;
        transition: background-color 0.18s ease, color 0.18s ease;
    }
    .settings-nav-group__item--sub .settings-nav-group__link {
        padding-left: 28px;
    }
    .settings-nav-group__link:hover {
        background: color-mix(in srgb, var(--text-primary) 4%, transparent);
    }
    .settings-nav-group__link--active {
        background: var(--brand-primary-soft);
        font-weight: 600;
    }
    .settings-nav-group__link--active::before {
        content: '';
        position: absolute;
        left: 0;
        top: 6px;
        bottom: 6px;
        width: 3px;
        border-radius: 2px;
        background: var(--q-accent);
    }
    .settings-nav-group__icon { flex: 0 0 auto; }
    .settings-nav-group__label {
        flex: 1 1 auto;
        min-width: 0;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
</style>
