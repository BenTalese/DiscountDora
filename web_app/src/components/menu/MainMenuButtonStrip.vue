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
            ref="indicatorEl"
            class="dora-mainMenuButtonStrip-indicator"
            :class="{ 'is-ready': indicator.ready, 'is-sliding': indicator.sliding }"
            :style="indicatorStyle"
            @transitionend="onIndicatorTransitionEnd"
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
    const indicatorEl = ref<HTMLElement | null>(null);
    const isHovering = ref(false);

    // Sliding active-route indicator. Measured from the DOM rather than computed
    // from widths because each button uses flex: 1 with clamp()'d label sizes,
    // so positions only resolve after layout.
    const indicator = reactive({ left: 0, width: 0, ready: false, sliding: false });

    const indicatorStyle = computed(() => ({
        translate: `${indicator.left}px 0`,
        width: `${indicator.width}px`,
    }));

    function measure() {
        const strip = stripEl.value;
        if (!strip) return;
        const active = strip.querySelector<HTMLElement>('.dora-mainMenuButton-active');
        if (!active) {
            indicator.width = 0;
            indicator.ready = false;
            indicator.sliding = false;
            return;
        }
        const stripRect = strip.getBoundingClientRect();
        const activeRect = active.getBoundingClientRect();
        const nextLeft = activeRect.left - stripRect.left;
        const nextWidth = activeRect.width;
        // If the active button hasn't moved (sub-route nav under the
        // same section — e.g. /cookbook → /cookbook/<id>),
        // `transitionend` for `translate` will never fire because the
        // CSS transition no-ops on an unchanged value. The route-change
        // watcher below sets `sliding = true` preemptively, so without
        // this clear the slide-flash colour sticks until the next real
        // movement. Same microtask as the preemptive set → no visible
        // flash on no-move navigations.
        const moved = indicator.ready
            && (nextLeft !== indicator.left || nextWidth !== indicator.width);
        indicator.left = nextLeft;
        indicator.width = nextWidth;
        indicator.ready = true;
        if (!moved) indicator.sliding = false;
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
        () => {
            indicator.sliding = true;
            void nextTick(measure);
        },
    );

    function onIndicatorTransitionEnd(e: TransitionEvent) {
        if (e.propertyName === 'translate') indicator.sliding = false;
    }
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
        box-shadow: 0 0 8px color-mix(in srgb, var(--brand-accent) 55%, transparent);
        opacity: 0;
        transition:
            translate 0.55s cubic-bezier(0.65, 0, 0.2, 1),
            width 0.55s cubic-bezier(0.65, 0, 0.2, 1),
            opacity 0.25s ease,
            background-color 0.3s ease,
            box-shadow 0.3s ease;
        pointer-events: none;
        will-change: translate, width, scale;
    }

    .dora-mainMenuButtonStrip-indicator.is-ready {
        opacity: 1;
    }

    .dora-mainMenuButtonStrip-indicator.is-sliding {
        background: var(--nav-slide-flash);
        box-shadow: 0 0 8px color-mix(in srgb, var(--nav-slide-flash) 60%, transparent);
        animation: nav-indicator-wobble 0.55s cubic-bezier(0.4, 0, 0.2, 1);
    }

    @keyframes nav-indicator-wobble {
        0%   { scale: 1 1; }
        25%  { scale: 1.22 1.5; }
        55%  { scale: 1.42 1.75; }
        80%  { scale: 1.0 1.12; }
        100% { scale: 1 1; }
    }
</style>
