import { onBeforeUnmount } from 'vue';
import type { ComputedRef, Ref } from 'vue';
import { onBeforeRouteLeave, onBeforeRouteUpdate } from 'vue-router';
import { useQuasar } from 'quasar';

/**
 * FU-156 — prompt "Discard unsaved changes?" whenever the user tries
 * to navigate away from the current page while `isDirty` is true.
 *
 * Covers every nav surface at once (so a new nav route — sidebar link,
 * router-link, `router.push`, browser back, browser refresh/close —
 * doesn't silently bypass the guard):
 * - Intra-app navigation goes through Vue Router → `onBeforeRouteLeave`
 *   intercepts and awaits a Quasar confirm dialog.
 * - Browser refresh / close / address-bar nav fires `beforeunload` →
 *   the native browser prompt fires while `isDirty` is true.
 *
 * Wire once at the top of `<script setup>`:
 *     useUnsavedChangesGuard(isDirty)
 *
 * The save path doesn't need any special handling — just flip
 * `isDirty` to false before / on successful save (as the pages already
 * do), and the next nav will pass straight through.
 */
export function useUnsavedChangesGuard(
    isDirty: Ref<boolean> | ComputedRef<boolean>,
): void {
    const $q = useQuasar();

    const confirmDiscard = (): Promise<boolean> =>
        new Promise<boolean>((resolve) => {
            $q.dialog({
                title: 'Discard unsaved changes?',
                message: 'Your edits will be lost.',
                ok: { label: 'Discard', color: 'negative', noCaps: true },
                cancel: { noCaps: true },
            })
                .onOk(() => resolve(true))
                .onCancel(() => resolve(false))
                .onDismiss(() => resolve(false));
        });

    onBeforeRouteLeave(async () => isDirty.value ? await confirmDiscard() : true);
    // Catches same-component param changes (e.g. clicking a related
    // recipe while editing the current one — both routes match the
    // same `/cookbook/:id` component, so `onBeforeRouteLeave` doesn't
    // fire; `onBeforeRouteUpdate` does).
    onBeforeRouteUpdate(async () => isDirty.value ? await confirmDiscard() : true);

    // Browser-level guard for refresh / close / address-bar nav. The
    // dialog text is ignored on modern browsers — setting `returnValue`
    // is what causes the native "Leave site?" prompt to fire.
    const onBeforeUnload = (event: BeforeUnloadEvent) => {
        if (!isDirty.value) return;
        event.preventDefault();
        event.returnValue = '';
    };
    window.addEventListener('beforeunload', onBeforeUnload);
    onBeforeUnmount(() => {
        window.removeEventListener('beforeunload', onBeforeUnload);
    });
}
