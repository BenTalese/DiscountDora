import { onBeforeUnmount, readonly, ref } from 'vue';

/**
 * Reactive `prefers-reduced-motion: reduce`.
 *
 * CSS already collapses every token-driven transition globally (see
 * `css/motion.scss`'s kill-switch). Use this composable only for the things
 * CSS can't neutralise on its own — JS-driven sequences such as autoplay
 * timers and staggered reveals — so they can skip straight to the final state
 * instead of animating. Motion is polish, never a gate to the content.
 */
export function useReducedMotion() {
    const prefersReducedMotion = ref(false);
    let mq: MediaQueryList | null = null;
    let listener: ((event: MediaQueryListEvent) => void) | null = null;

    if (typeof window !== 'undefined' && window.matchMedia) {
        mq = window.matchMedia('(prefers-reduced-motion: reduce)');
        prefersReducedMotion.value = mq.matches;
        listener = (event) => {
            prefersReducedMotion.value = event.matches;
        };
        mq.addEventListener('change', listener);
    }

    onBeforeUnmount(() => {
        if (mq && listener) mq.removeEventListener('change', listener);
    });

    return readonly(prefersReducedMotion);
}
