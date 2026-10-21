import { onMounted, onUnmounted, reactive, readonly, ref } from 'vue';

// A lightweight keyboard-shortcut layer. Shortcuts auto-register on mount and
// deregister on unmount, so a component's shortcuts are only live while it's on
// screen — that's how per-page scoping works without route matching. The
// `scope` field is just a display group label for the cheatsheet.
//
// Supports single keys ('n', '/', '?', 'space', 'escape', 'arrowup') and
// two-step sequences ('g s'). Plain keys only — modifier combos (Ctrl/Cmd/Alt)
// are left to their owners (e.g. the undo handler), so we never swallow them.

export interface ShortcutDef {
    /** e.g. 'n', '/', '?', 'g s', 'space', 'arrowdown'. Lower-case. */
    keys: string;
    /** Display group label, e.g. 'Global', 'Stock overview'. */
    scope: string;
    description: string;
    handler: (event: KeyboardEvent) => void;
    /** When true the shortcut also fires while typing in an input/textarea. */
    allowInInput?: boolean;
}

interface RegisteredShortcut extends ShortcutDef {
    id: number;
}

const registry = reactive<RegisteredShortcut[]>([]);
const cheatsheetOpen = ref(false);

let nextId = 1;
let installed = false;
let seqPrefix: string | null = null;
let seqTimer: ReturnType<typeof setTimeout> | null = null;

function isTypingTarget(event: KeyboardEvent): boolean {
    const t = event.target as HTMLElement | null;
    if (!t) return false;
    const tag = (t.tagName || '').toLowerCase();
    if (tag === 'input' || tag === 'textarea' || tag === 'select') return true;
    return t.isContentEditable;
}

function tokenFor(event: KeyboardEvent): string {
    if (event.key === ' ') return 'space';
    return event.key.toLowerCase();
}

function clearSequence(): void {
    seqPrefix = null;
    if (seqTimer) {
        clearTimeout(seqTimer);
        seqTimer = null;
    }
}

function findMatch(keys: string, typing: boolean): RegisteredShortcut | null {
    // Iterate newest-first so a page shortcut (registered after the global one)
    // wins over a global with the same keys.
    for (let i = registry.length - 1; i >= 0; i--) {
        const s = registry[i]!;
        if (s.keys === keys && (s.allowInInput || !typing)) return s;
    }
    return null;
}

function handleKeydown(event: KeyboardEvent): void {
    // We own plain keys (+Shift for '?'). Leave modifier combos alone.
    if (event.ctrlKey || event.metaKey || event.altKey) return;

    const typing = isTypingTarget(event);
    const token = tokenFor(event);

    if (token === 'escape') {
        clearSequence();
        if (cheatsheetOpen.value) {
            event.preventDefault();
            cheatsheetOpen.value = false;
        }
        return;
    }

    let candidate = token;
    if (seqPrefix) {
        candidate = `${seqPrefix} ${token}`;
        clearSequence();
    }

    const match = findMatch(candidate, typing);
    if (match) {
        event.preventDefault();
        match.handler(event);
        return;
    }

    // Not a full match — is this token the first half of a known sequence?
    if (!seqPrefix && registry.some((s) => s.keys.startsWith(`${token} `) && (s.allowInInput || !typing))) {
        seqPrefix = token;
        seqTimer = setTimeout(clearSequence, 1000);
        event.preventDefault();
    }
}

function install(): void {
    if (installed || typeof window === 'undefined') return;
    window.addEventListener('keydown', handleKeydown);
    installed = true;
}

/** Register one or more shortcuts for the lifetime of the calling component. */
export function useShortcut(defs: ShortcutDef | ShortcutDef[]): void {
    const list = Array.isArray(defs) ? defs : [defs];
    const ids: number[] = [];

    onMounted(() => {
        install();
        for (const def of list) {
            const id = nextId++;
            registry.push({ ...def, id });
            ids.push(id);
        }
    });

    onUnmounted(() => {
        for (const id of ids) {
            const idx = registry.findIndex((s) => s.id === id);
            if (idx >= 0) registry.splice(idx, 1);
        }
    });
}

/** Reactive view of every currently-registered shortcut (for the cheatsheet). */
export function useShortcutRegistry() {
    return {
        shortcuts: readonly(registry),
        cheatsheetOpen,
        openCheatsheet: () => (cheatsheetOpen.value = true),
        closeCheatsheet: () => (cheatsheetOpen.value = false),
    };
}
