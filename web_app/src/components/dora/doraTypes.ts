// Shared types for the Dora assistant components.
// Kept out of the .vue files because `<script setup>` blocks don't export
// named bindings — only the default component export. Importing
// `DoraMood` from DoraMascot.vue silently resolves to `any` at the type
// level, which means typos sneak through. This file is the source of truth.

export type DoraMood =
    | 'happy'
    | 'thinking'
    | 'confused'
    | 'excited'
    | 'curious';
