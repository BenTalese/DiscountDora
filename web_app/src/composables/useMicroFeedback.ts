import { nextTick, onBeforeUnmount, readonly, ref, watch, type Ref } from 'vue';

/**
 * DR-15 / D-010 — one-shot micro-feedback on the app's most-repeated gestures.
 *
 * Bind the returned `feedbackClass` onto an element and the matching utility
 * class from `css/motion.scss` (`dora-settle` / `dora-bump`) is applied for
 * exactly one animation cycle each time `source` changes, then removed. That
 * removal is the point: a class left on re-runs the animation on every
 * re-render, and an animation that fires on a *persistent* condition rather
 * than a *change* becomes wallpaper (see the retired row pulse in
 * `StockItemRow.vue`).
 *
 * Why a timer and not `animationend`: the caller owns the element, we only
 * hand back a class, so there is nothing here to attach a listener to. The
 * timer's length is read from the `--motion-*` token rather than hardcoded, so
 * D-010's no-literal-`ms` rule holds and `prefers-reduced-motion` (which
 * rewrites the tokens to ~0) shortens this too — the class is applied, the
 * animation resolves to no movement because the amplitude tokens flatten to 1,
 * and the class is dropped again on the next tick.
 */
export type MicroFeedbackKind = 'settle' | 'bump';

/** Fallback if the token can't be read (SSR, jsdom, a stylesheet that hasn't
 *  landed yet). Matches `--motion-fast`; only ever used to time a class
 *  *removal*, so being wrong here is invisible. */
const FALLBACK_MS = 120;

/** Slack between the animation ending and the class being dropped. Not an
 *  animation duration, so it isn't a D-010 literal — it only stops the class
 *  from being removed on the animation's final frame. */
const CLASS_TAIL_MS = 40;

/**
 * Resolve a motion token to milliseconds. Exported for tests — the parse has
 * to cope with both units the tokens use (`120ms`, and the `0.01ms` the
 * reduced-motion block swaps in) plus a `s`-suffixed value if one is ever set.
 */
export function motionDurationMs(
    token = '--motion-fast',
    fallbackMs = FALLBACK_MS,
): number {
    if (typeof window === 'undefined' || !window.getComputedStyle) return fallbackMs;
    const raw = window
        .getComputedStyle(document.documentElement)
        .getPropertyValue(token)
        .trim();
    if (!raw) return fallbackMs;
    const value = Number.parseFloat(raw);
    if (!Number.isFinite(value)) return fallbackMs;
    return raw.endsWith('ms') ? value : value * 1000;
}

export function useMicroFeedback(
    source: () => unknown,
    kind: MicroFeedbackKind = 'settle',
): Readonly<Ref<string>> {
    const active = ref('');
    let timer: ReturnType<typeof setTimeout> | null = null;

    watch(source, (next, previous) => {
        // Guard the initial resolve as well as no-op writes: only a genuine
        // change is feedback-worthy. Without this every row in a freshly
        // rendered list would animate at once on mount.
        if (next === previous) return;
        if (timer !== null) clearTimeout(timer);
        active.value = '';
        // Clear-then-re-apply across a DOM patch, so a second change inside one
        // animation cycle has a chance to restart the animation rather than
        // being swallowed by the one already running.
        //
        // `nextTick`, deliberately NOT `requestAnimationFrame`: rAF doesn't
        // fire in a throttled or backgrounded tab (the DR-8 splash wedge, and
        // the same starvation in the verify pane), and anything sequenced
        // behind it silently never happens. Motion is polish, so the failure
        // would be invisible — but a paint dependency is exactly the pattern
        // D-007/B10 tells us not to build, even where the stakes are low.
        void nextTick(() => {
            active.value = `dora-${kind}`;
            // A small tail past the token duration so the class outlives the
            // animation rather than clipping its last frame.
            timer = setTimeout(() => {
                active.value = '';
                timer = null;
            }, motionDurationMs() + CLASS_TAIL_MS);
        });
    });

    onBeforeUnmount(() => {
        if (timer !== null) clearTimeout(timer);
    });

    return readonly(active);
}
