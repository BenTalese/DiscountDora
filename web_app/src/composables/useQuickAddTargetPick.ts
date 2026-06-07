// P6-01 Chunk 2 — remember the user's quick-add-target choice for the
// 2+ drafts case. sessionStorage (not localStorage) so the pick lives for
// the tab session only — opening a fresh tab re-prompts, matching the
// plan's "remember the session pick" framing.

const STORAGE_KEY = 'dora.quick_add_target_list_id';

export function useQuickAddTargetPick() {
    function load(): string | null {
        try {
            return window.sessionStorage.getItem(STORAGE_KEY);
        } catch {
            return null;
        }
    }

    function save(listId: string): void {
        try {
            window.sessionStorage.setItem(STORAGE_KEY, listId);
        } catch {
            // Storage disabled (private mode etc.) — degrade silently; the
            // user just gets re-prompted on the next quick-add.
        }
    }

    function clear(): void {
        try {
            window.sessionStorage.removeItem(STORAGE_KEY);
        } catch {
            // Same rationale as save().
        }
    }

    return { load, save, clear };
}
