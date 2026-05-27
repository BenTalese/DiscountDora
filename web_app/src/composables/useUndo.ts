// Global undo / redo registry (F5).
//
// Module-singleton state shared across every consumer (the header Undo
// button, Ctrl-Z handler, undoable-notify toasts). Lives in-memory only
// — undo history doesn't survive a reload because the world might have
// changed underneath us in the meantime.
//
// Each registered entry carries a label (for tooltips / toasts), an
// inverse function (re-applies prior state), and an optional redo
// function (re-applies the undone action — defaults to "do nothing"
// for actions where redo doesn't make sense, e.g. delete-then-undo
// shouldn't auto-delete again on redo).
//
// Optimistic mutations register up-front but stay `pending` until the
// server confirms. Pending entries are skipped by the user-facing undo
// stack (canUndo doesn't count them) until `finalise()` runs.

import { computed, readonly, ref } from 'vue';

const MAX_STACK = 20;

export type UndoEntry = {
    /** Stable identifier so optimistic registrations can be finalised
     *  later by the caller. */
    id: string;
    /** Short, user-facing label: "Deleted 'Tomato Soup'", etc. */
    label: string;
    /** Re-applies the state prior to the action. Throws on failure. */
    inverse: () => Promise<void>;
    /** Optional: re-applies the action itself. When undefined, redo
     *  removes the entry from the redo stack but does nothing. */
    redo?: () => Promise<void>;
    /** Optimistic flag: until finalised, the entry doesn't surface to
     *  the user. Cleared by `finaliseEntry`. */
    pending?: boolean;
    /** When the entry was registered, for sort tiebreaks + UX hints. */
    registeredAt: Date;
};

export type RegisterArgs = Omit<UndoEntry, 'id' | 'registeredAt' | 'pending'> & {
    /** When true, the entry stays hidden from canUndo / undo() until
     *  finalised. Use for optimistic mutations awaiting server confirm. */
    pending?: boolean;
};

const undoStack = ref<UndoEntry[]>([]);
const redoStack = ref<UndoEntry[]>([]);
const undoing = ref(false);
// Listeners other modules can hook into for cross-cutting reactions
// (e.g. the undoable-notify helper bumps a toast when a new entry lands).
type Listener = (entry: UndoEntry) => void;
const registerListeners: Set<Listener> = new Set();

function newId(): string {
    if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
        return (crypto as Crypto & { randomUUID: () => string }).randomUUID();
    }
    return `u-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

/** Push an entry on the undo stack. Clears the redo stack — any new
 *  action invalidates the "future" the user could have redone into. */
export function register(args: RegisterArgs): string {
    const entry: UndoEntry = {
        id: newId(),
        label: args.label,
        inverse: args.inverse,
        ...(args.redo !== undefined ? { redo: args.redo } : {}),
        ...(args.pending ? { pending: true } : {}),
        registeredAt: new Date(),
    };
    undoStack.value = [...undoStack.value, entry].slice(-MAX_STACK);
    redoStack.value = [];
    if (!entry.pending) notifyListeners(entry);
    return entry.id;
}

/** Promote a previously-registered optimistic entry from `pending` →
 *  visible. Called by mutation paths after the server round-trip lands. */
export function finaliseEntry(id: string): void {
    const idx = undoStack.value.findIndex((e) => e.id === id);
    if (idx < 0) return;
    const entry = undoStack.value[idx]!;
    if (!entry.pending) return;
    entry.pending = false;
    // Force reactivity (we mutated in place).
    undoStack.value = [...undoStack.value];
    notifyListeners(entry);
}

/** Drop a pending entry (the optimistic mutation failed server-side). */
export function discardEntry(id: string): void {
    undoStack.value = undoStack.value.filter((e) => e.id !== id);
}

/** Pop the most-recently-registered visible entry and run its inverse.
 *  Returns true if anything ran. */
export async function undo(): Promise<boolean> {
    if (undoing.value) return false;
    const visible = visibleUndoStack();
    const entry = visible[visible.length - 1];
    if (!entry) return false;
    undoing.value = true;
    try {
        await entry.inverse();
        // Remove from the live stack (the entry object identity is what
        // we filter by, not the index — pending entries may have been
        // inserted between visibility windows).
        undoStack.value = undoStack.value.filter((e) => e.id !== entry.id);
        // Push onto redo so Ctrl-Shift-Z brings it back.
        redoStack.value = [...redoStack.value, entry].slice(-MAX_STACK);
        return true;
    } finally {
        // On failure the error propagates to the caller (who toasts); the
        // entry stays in place so the user can retry once they've fixed the
        // underlying issue. `finally` only resets the in-flight flag.
        undoing.value = false;
    }
}

/** Re-apply the most recently undone action. No-op if its redo is null. */
export async function redo(): Promise<boolean> {
    if (undoing.value) return false;
    const entry = redoStack.value[redoStack.value.length - 1];
    if (!entry) return false;
    undoing.value = true;
    try {
        if (entry.redo) await entry.redo();
        redoStack.value = redoStack.value.filter((e) => e.id !== entry.id);
        // Bring it back to the undo stack so a second Ctrl-Z undoes it again.
        undoStack.value = [...undoStack.value, entry].slice(-MAX_STACK);
        return true;
    } finally {
        undoing.value = false;
    }
}

/** Clear everything (e.g. on logout). */
export function clearUndo(): void {
    undoStack.value = [];
    redoStack.value = [];
}

function visibleUndoStack(): UndoEntry[] {
    return undoStack.value.filter((e) => !e.pending);
}

function notifyListeners(entry: UndoEntry) {
    for (const listener of registerListeners) {
        try {
            listener(entry);
        } catch {
            // Listener errors must not break the registration itself.
        }
    }
}

/** Subscribe to new visible entries. Returns an unsubscribe fn. */
export function onRegister(listener: Listener): () => void {
    registerListeners.add(listener);
    return () => registerListeners.delete(listener);
}

export function useUndo() {
    return {
        // Reactive views.
        canUndo: computed(() => visibleUndoStack().length > 0),
        canRedo: computed(() => redoStack.value.length > 0),
        topUndoLabel: computed(() => {
            const visible = visibleUndoStack();
            return visible[visible.length - 1]?.label ?? '';
        }),
        topRedoLabel: computed(() => {
            const top = redoStack.value[redoStack.value.length - 1];
            return top?.label ?? '';
        }),
        undoStack: readonly(undoStack),
        redoStack: readonly(redoStack),
        // Actions.
        register,
        finaliseEntry,
        discardEntry,
        undo,
        redo,
        clearUndo,
        onRegister,
    };
}
