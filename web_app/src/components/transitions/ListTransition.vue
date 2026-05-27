<template>
    <transition-group
        :tag="tag ?? 'div'"
        name="dora-list"
        :appear="!!appear"
    >
        <slot />
    </transition-group>
</template>

<script lang="ts" setup>
    // Wraps <transition-group> for v-for grids/lists. Animates enter/leave
    // AND reorder (the `-move` class) so filtering/sorting a stock grid
    // glides instead of snapping. Children MUST carry a stable :key.
    //
    // Note: leaving items need position: absolute during leave for `-move`
    // to look right on a wrapping grid; consumers add that in their own
    // scoped styles since layout (grid vs flex) is theirs to own.
    withDefaults(
        defineProps<{ tag?: string; appear?: boolean }>(),
        { tag: 'div', appear: false },
    );
</script>

<style scoped>
    .dora-list-enter-active {
        transition: opacity var(--motion-normal) var(--motion-ease-out),
            transform var(--motion-normal) var(--motion-ease-out);
    }
    .dora-list-leave-active {
        transition: opacity var(--motion-fast) var(--motion-ease-in),
            transform var(--motion-fast) var(--motion-ease-in);
    }
    .dora-list-move {
        transition: transform var(--motion-normal) var(--motion-ease);
    }
    .dora-list-enter-from,
    .dora-list-leave-to {
        opacity: 0;
        transform: translateY(var(--motion-slide-distance));
    }
</style>
