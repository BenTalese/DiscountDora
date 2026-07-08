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
    <q-item
        v-else
        :to="link"
        :class="{ 'dora-sideMenuButton-active': isActive }"
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
