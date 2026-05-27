<template>
    <transition v-bind="bindings">
        <slot />
    </transition>
</template>

<script lang="ts" setup>
    // Plain opacity fade. The default for content that swaps in place
    // (panels, empty/loaded states, route changes) where movement would be
    // noise. Pass mode="out-in" for router-view so the old page fades out
    // before the new one fades in (avoids the two overlapping mid-swap).
    import { computed } from 'vue';
    import type { TransitionProps } from 'vue';

    const props = withDefaults(
        defineProps<{ appear?: boolean; mode?: TransitionProps['mode'] }>(),
        { appear: false, mode: undefined },
    );

    // Build the binding object in script and omit `mode` when unset — under
    // exactOptionalPropertyTypes we can't hand `mode: undefined` to <transition>.
    const bindings = computed<TransitionProps>(() => {
        const b: TransitionProps = { name: 'dora-fade', appear: props.appear };
        if (props.mode) b.mode = props.mode;
        return b;
    });
</script>

<style scoped>
    .dora-fade-enter-active,
    .dora-fade-leave-active {
        transition: opacity var(--motion-normal) var(--motion-ease);
    }
    .dora-fade-enter-from,
    .dora-fade-leave-to {
        opacity: 0;
    }
</style>
