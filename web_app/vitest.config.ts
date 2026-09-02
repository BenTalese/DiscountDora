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
            // The bare-`quasar` alias below shadows Quasar's package-exports
            // map, so the `quasar/wrappers` subpath (used by boot modules like
            // globalErrorHandler) no longer resolves on its own. Point it at
            // the real file so boot-module specs can import it (tests still
            // vi.mock it to unwrap boot()).
            'quasar/wrappers': fileURLToPath(
                new URL('./node_modules/quasar/wrappers/index.js', import.meta.url),
            ),
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
        // FU-820 — pin a NEGATIVE-offset timezone for the whole suite.
        //
        // Date-only values (`YYYY-MM-DD`: expiry, scheduled_for, effective
        // dates) are the app's most common date shape, and `new Date(iso)` parses
        // that form as UTC midnight — so anything reading local parts afterwards
        // reports the previous day whenever the host is west of Greenwich. East
        // of Greenwich the two agree, which is precisely why the bug shipped:
        // Australia is the shipping default and every developer runs there.
        //
        // Running the suite in `America/New_York` means a date test that passes
        // here passes everywhere; running it in local time would have let
        // `relativeDay.spec.ts` pass vacuously on the machine that wrote it.
        // Node caches the zone before module evaluation, so it has to be set
        // here rather than inside a spec.
        env: { TZ: 'America/New_York' },
        // FU-541 — coverage is a MAP to find untested modules, not a gate.
        // Opt-in only: `npm run test:coverage` (passing --coverage enables
        // this block; a plain `npm test` run ignores it). Deliberately NO
        // `thresholds` / fail-under — green-means-correct, so a % target would
        // just incentivise filler tests. `all: true` is the point: it reports
        // every src file even if no spec imports it, so a completely-untested
        // module (e.g. the FU-539 resilience layer) shows up as 0% instead of
        // being invisibly absent.
        coverage: {
            provider: 'v8',
            all: true,
            include: ['src/**/*.{ts,vue}'],
            // Pure type declarations compile to nothing; excluding them keeps
            // the report from listing 0%-of-0-lines noise.
            exclude: ['src/**/*.d.ts'],
            reporter: ['text', 'html'],
        },
    },
});
