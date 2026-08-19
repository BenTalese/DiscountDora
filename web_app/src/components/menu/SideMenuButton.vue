<template>
    <q-item
        v-if="href"
        :href="href"
        target="_blank"
        rel="noopener"
        clickable
        tag="a"
    >
        <q-item-section avatar>
            <q-icon :name="icon" />
        </q-item-section>
        <q-item-section>
            <q-item-label>
                {{ label }}
                <q-icon name="open_in_new" size="14px" class="q-ml-xs" />
            </q-item-label>
            <q-item-label caption v-if="caption">{{ caption }}</q-item-label>
        </q-item-section>
    </q-item>
    <!-- `active-class` / `exact-active-class` are blanked so Quasar's router
         active state can't style this item: it is route-record based, so the
         Dashboard entry (`/`, an empty child of the `/` layout record) matched
         as active on *every* route and Quasar's
         `.q-item.q-router-link--active { color: var(--q-primary) }` painted it
         primary everywhere. That rule also outranks the class below on genuinely
         active items. `isActive` (path-prefix based) is the single source of
         truth — see useMenuLinkActive. -->
    <q-item
        v-else
        :to="link"
        :class="{ 'dora-sideMenuButton-active': isActive }"
        active-class=""
        exact-active-class=""
        clickable
        tag="a"
    >
        <q-item-section avatar>
            <q-icon :name="icon" />
        </q-item-section>

        <q-item-section>
            <q-item-label>{{ label }}</q-item-label>
            <q-item-label caption v-if="caption">{{ caption }}</q-item-label>
        </q-item-section>
    </q-item>
</template>

<script setup lang="ts">
    import type { MenuButtonProps } from './menuButtonProps';
    import { useMenuLinkActive } from './useMenuLinkActive';

    const props = defineProps<MenuButtonProps>();
    const isActive = useMenuLinkActive(() => props.link, () => props.activePrefixes);
</script>

<style scoped lang="scss">
    .dora-sideMenuButton-active {
        background: var(--q-accent);
        color: var(--text-on-accent);
        font-weight: 600;
    }
</style>
