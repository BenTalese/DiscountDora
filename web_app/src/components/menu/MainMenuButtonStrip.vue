<template>
    <div
        v-if="isVisible"
        ref="stripEl"
        class="dora-mainMenuButtonStrip row no-wrap items-stretch"
        @mouseenter="isHovering = true"
        @mouseleave="isHovering = false"
    >
        <MainMenuButton
            v-for="link in menuLinks"
            :key="link.label"
            :is-expanded="isHovering"
            v-bind="link"
        />
        <div
            class="dora-mainMenuButtonStrip-indicator"
            :class="{ 'is-ready': indicator.ready }"
            :style="indicatorStyle"
        />
    </div>
</template>

<script setup lang="ts">
    import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue';
    import { useRoute } from 'vue-router';
    import MainMenuButton from './MainMenuButton.vue';
    import type { MenuButtonProps } from './menuButtonProps';

    const props = defineProps<{
        isVisible: boolean;
        menuLinks: MenuButtonProps[];
    }>();

    const route = useRoute();
    const stripEl = ref<HTMLElement | null>(null);
    const isHovering = ref(false);

    // Sliding active-route indicator. Measured from the DOM rather than computed
    // from widths because each button uses flex: 1 with clamp()'d label sizes,
    // so positions only resolve after layout.
    const indicator = reactive({ left: 0, width: 0, ready: false });

    const indicatorStyle = computed(() => ({
        transform: `translateX(${indicator.left}px)`,
        width: `${indicator.width}px`,
    }));

    function measure() {
        const strip = stripEl.value;
        if (!strip) return;
        const active = strip.querySelector<HTMLElement>('.dora-mainMenuButton-active');
        if (!active) {
            indicator.width = 0;
            indicator.ready = false;
            return;
        }
        const stripRect = strip.getBoundingClientRect();
        const activeRect = active.getBoundingClientRect();
        indicator.left = activeRect.left - stripRect.left;
        indicator.width = activeRect.width;
        indicator.ready = true;
    }

    let resizeObserver: ResizeObserver | null = null;

    onMounted(() => {
        void nextTick(measure);
        if (typeof ResizeObserver !== 'undefined' && stripEl.value) {
            resizeObserver = new ResizeObserver(() => measure());
            resizeObserver.observe(stripEl.value);
        }
        window.addEventListener('resize', measure);
    });

    onBeforeUnmount(() => {
        resizeObserver?.disconnect();
        window.removeEventListener('resize', measure);
    });

    watch(
        () => route.fullPath,
        () => void nextTick(measure),
    );
    watch(
        () => props.isVisible,
        () => void nextTick(measure),
    );
    watch(
        () => props.menuLinks,
        () => void nextTick(measure),
        { deep: true },
    );
</script>

<style scoped lang="scss">
    .dora-mainMenuButtonStrip {
        flex: 1 1 auto;
        min-width: 0;
        position: relative;
        gap: 2px;
        padding: 0 4px;
    }

    .dora-mainMenuButtonStrip-indicator {
        position: absolute;
        bottom: -6px;
        left: 0;
        height: 3px;
        border-radius: 3px;
        background: var(--q-accent);
        box-shadow: 0 0 8px rgba(242, 192, 55, 0.55);
        opacity: 0;
        transition:
            transform 0.42s cubic-bezier(0.65, 0, 0.2, 1),
            width 0.42s cubic-bezier(0.65, 0, 0.2, 1),
            opacity 0.25s ease;
        pointer-events: none;
        will-change: transform, width;
    }

    .dora-mainMenuButtonStrip-indicator.is-ready {
        opacity: 1;
    }
</style>
