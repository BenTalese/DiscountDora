import { fileURLToPath } from 'node:url';
import { defineConfig } from 'vitest/config';

// FU-390 — unit/eval harness for the Dora assistant's pure logic (the
// Basic-mode rule engine). Kept deliberately minimal: node environment, no
// jsdom, no Vue runtime — the functions under test (`detectIntent`,
// `extractAddToListItems`) are dependency-free string logic. The `src` alias
// mirrors Quasar's (.quasar/tsconfig.json) so imports resolve the same way
// they do in the app build.
export default defineConfig({
    resolve: {
        alias: {
            src: fileURLToPath(new URL('./src', import.meta.url)),
        },
    },
    test: {
        environment: 'node',
        include: ['test/**/*.spec.ts'],
    },
});
