import vue from '@vitejs/plugin-vue';
import { fileURLToPath } from 'node:url';
import { defineConfig } from 'vitest/config';

// FU-390 — unit/eval harness for the Dora assistant's pure logic, extended
// by FU-520 with the composable/util suites and the first component tests.
// Default environment stays `node` (the pure-logic suites need no DOM);
// component specs opt into jsdom per-file with a `// @vitest-environment
// jsdom` pragma. The vue() plugin only engages for `.vue` imports. The
// `src` alias mirrors Quasar's (.quasar/tsconfig.json) so imports resolve
// the same way they do in the app build.
export default defineConfig({
    plugins: [vue()],
    resolve: {
        alias: {
            src: fileURLToPath(new URL('./src', import.meta.url)),
            // Vitest's node-side module resolution picks Quasar's SSR
            // bundle (quasar.server.prod.js), whose plugin install
            // expects an ssrContext and throws under jsdom mounts. Pin
            // the client ESM bundle — the same one the browser build
            // uses — so component tests mount with the real plugin.
            quasar: fileURLToPath(
                new URL('./node_modules/quasar/dist/quasar.client.js', import.meta.url),
            ),
        },
    },
    test: {
        environment: 'node',
        include: ['test/**/*.spec.ts'],
    },
});
