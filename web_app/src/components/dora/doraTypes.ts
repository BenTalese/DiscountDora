// Shared types for the Dora assistant components.
// Kept out of the .vue files because `<script setup>` blocks don't export
// named bindings — only the default component export. Importing
// `DoraMood` from DoraMascot.vue silently resolves to `any` at the type
// level, which means typos sneak through. This file is the source of truth.

export type DoraMood =
    | 'happy'
    | 'thinking'
    | 'searching'
    | 'confused'
    | 'sad'
    | 'excited'
    | 'super_excited'
    // Added in Stage 1 / wired up properly in Stage 3 (idle alt cycling,
    // sparkle overlays, non-happy talking variants).
    | 'cute'
    | 'confident'
    | 'lightbulb'
    | 'worried';

// Short-lived behavioural overlays driven by the parent. `talking` swaps in
// the open-mouth frame for the lifetime of a spoken message; `idle` lets the
// mascot do its slow blink loop.
export type DoraState = 'idle' | 'talking';

// Orthogonal to mood: reflects whether the assistant is reachable / awake.
// `offline` overrides the mood face with the sad-eye error frame; `sleeping`
// is used on the collapsed launcher after a long stretch of inactivity.
export type DoraConnection = 'online' | 'offline' | 'sleeping';

// Moods that have a dedicated talking-overlay artwork. For these the mascot
// plays the lip-flap directly on the mood's own face; for the rest the
// launcher temporarily flips to `happy` during talking so the lip-flap (which
// only matches the ready-face artwork) still plays.
export const MOODS_WITH_TALKING_VARIANT: ReadonlySet<DoraMood> = new Set([
    'happy',
    'confused',
    'sad',
]);
