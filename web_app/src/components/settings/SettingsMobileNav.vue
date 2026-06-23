<template>
    <!--
        IMPL_PLAN_SETTINGS_REBUILD §6.3 (user pick: top tab strip) — the
        mobile (<md) settings nav. Row of group tabs along the top; the
        selected group reveals its destinations as a horizontally-scrolling
        chip strip below. Replaces Phase 3's placeholder horizontal-scroll of
        the desktop sidebar. The desktop sidebar (SettingsNavGroup) is shown
        instead at >=md by the shell.
    -->
    <nav class="settings-mnav" aria-label="Settings sections">
        <div class="settings-mnav__groups" role="tablist">
            <button
                v-for="group in groups"
                :key="group.label"
                type="button"
                role="tab"
                class="settings-mnav__group"
                :class="{ 'settings-mnav__group--active': group.label === activeLabel }"
                :aria-selected="group.label === activeLabel"
                @click="activeLabel = group.label"
            >
                <q-icon v-if="group.icon" :name="group.icon" size="14px" class="q-mr-xs" />
                {{ group.label }}
            </button>
        </div>

        <div class="settings-mnav__chips">
            <router-link
                v-for="leaf in activeLeaves"
                :key="leaf.path"
                :to="leaf.path"
                class="settings-mnav__chip"
                active-class="settings-mnav__chip--active"
                exact-active-class="settings-mnav__chip--active"
            >
                <q-icon :name="leaf.icon" size="16px" class="q-mr-xs" />
                {{ leaf.label }}
            </router-link>
        </div>
    </nav>
</template>

<script setup lang="ts">
    import type {
        SettingsNavEntry,
        SettingsNavLeaf,
    } from 'src/components/settings/SettingsNavGroup.vue';
    import { computed, ref, watch } from 'vue';
    import { useRoute } from 'vue-router';

    export interface SettingsNavGroupDef {
        label: string;
        icon?: string;
        items: SettingsNavEntry[];
    }

    const props = defineProps<{ groups: SettingsNavGroupDef[] }>();

    const route = useRoute();

    // Subgroups (Recipe taxonomies / System) flatten to their leaves — the
    // chip strip is one flat scrollable row, no second-level nesting on mobile.
    function leavesOf(group: SettingsNavGroupDef): SettingsNavLeaf[] {
        return group.items.flatMap((entry) =>
            'subheader' in entry ? entry.items : [entry],
        );
    }

    // Default the open tab to whichever group owns the current route, so a
    // deep link / redirect lands with the right strip already showing.
    function groupOwningRoute(): string {
        const match = props.groups.find((g) =>
            leavesOf(g).some((leaf) => leaf.path === route.path),
        );
        return match?.label ?? props.groups[0]?.label ?? '';
    }

    const activeLabel = ref(groupOwningRoute());

    // Follow route changes (e.g. the user taps a chip, or navigates from
    // elsewhere) so the active tab tracks where they actually are.
    watch(
        () => route.path,
        () => { activeLabel.value = groupOwningRoute(); },
    );

    const activeLeaves = computed<SettingsNavLeaf[]>(() => {
        const group = props.groups.find((g) => g.label === activeLabel.value);
        return group ? leavesOf(group) : [];
    });
</script>

<style scoped lang="scss">
    .settings-mnav {
        display: flex;
        flex-direction: column;
        gap: 10px;
    }
    .settings-mnav__groups {
        display: flex;
        gap: 4px;
        overflow-x: auto;
        scrollbar-width: none;
        border-bottom: 1px solid color-mix(in srgb, var(--text-primary) 8%, transparent);
    }
    .settings-mnav__groups::-webkit-scrollbar { display: none; }
    .settings-mnav__group {
        all: unset;
        display: inline-flex;
        align-items: center;
        white-space: nowrap;
        cursor: pointer;
        padding: 8px 12px;
        font-size: 0.8125rem;
        font-weight: 600;
        color: var(--text-secondary);
        border-bottom: 2px solid transparent;
        margin-bottom: -1px;
    }
    .settings-mnav__group:focus-visible {
        outline: 2px solid var(--ring-focus);
        outline-offset: -2px;
    }
    .settings-mnav__group--active {
        color: var(--text-primary);
        border-bottom-color: var(--q-accent);
    }
    .settings-mnav__chips {
        display: flex;
        gap: 6px;
        overflow-x: auto;
        scrollbar-width: none;
        padding-bottom: 2px;
    }
    .settings-mnav__chips::-webkit-scrollbar { display: none; }
    .settings-mnav__chip {
        display: inline-flex;
        align-items: center;
        white-space: nowrap;
        text-decoration: none;
        padding: 6px 12px;
        border-radius: 999px;
        font-size: 0.8125rem;
        color: var(--text-primary);
        background: color-mix(in srgb, var(--text-primary) 5%, transparent);
        transition: background-color 0.18s ease, color 0.18s ease;
    }
    .settings-mnav__chip--active {
        background: var(--brand-primary-soft);
        font-weight: 600;
    }
</style>
