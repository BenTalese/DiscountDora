<template>
    <q-item
        :to="link"
        active-class="dora-sideMenuButton-active"
        clickable
        exact
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
    defineProps<MenuButtonProps>();
</script>

<style scoped lang="scss">
    .dora-sideMenuButton-active {
        background: var(--q-accent);
        color: var(--text-on-accent);
        font-weight: 600;
    }
</style>
