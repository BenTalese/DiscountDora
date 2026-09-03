// Configuration for your app
// https://v2.quasar.dev/quasar-cli-vite/quasar-config-file

import { defineConfig } from '#q-app/wrappers';
import { fileURLToPath } from 'node:url';

// `defineConfig` is over-strict about pwa.extendManifestJson typing —
// our generic `Record<string, unknown>` callback signature isn't
// assignable to PwaManifestOptions even though the runtime behaviour
// is identical. The whole inner object is cast to suppress that
// single false-positive without losing inference on the rest.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export default defineConfig((ctx): any => {
    return {
        // https://v2.quasar.dev/quasar-cli-vite/prefetch-feature
        // preFetch: true,

        // app boot file (/src/boot)
        // --> boot files are part of "main.js"
        // https://v2.quasar.dev/quasar-cli-vite/boot-files
        boot: [
            'quasarScreen',
            'fonts',
            'globalErrorHandler',
            'i18n',
            'notifyTypeRegistration',
            'pwaLifecycle',
            'theme',
            'capacitor'
        ],

        // https://v2.quasar.dev/quasar-cli-vite/quasar-config-file#css
        css: [
            // DS1: tokens.scss declares the full design-token system,
            // themes.scss overrides per-theme via [data-theme=…]. They
            // must load before app.scss / colours.scss so the legacy
            // styles can reference the new custom properties.
            'tokens.scss',
            'themes.scss',
            // DS4: motion tokens (duration/easing) + the prefers-reduced-motion
            // kill-switch. Loads after the design tokens, before component css.
            'motion.scss',
            'app.scss',
            'colours.scss',
            // R-022 / FU-326 — shared DnD affordances (dragging dim,
            // drop-target ring, handle grip). Loaded after colours so
            // it can reference `--brand-primary` / `--surface-sunken`.
            'dnd.scss',
            // 2026-08-26 — the bulk-select sub-bar, shared by Stock overview
            // and the shopping list so the two can't drift apart again.
            'subbar.scss',
            // v4 chunk 3/5 — the shopping-list surface's shared visual
            // language: the row skeleton (grid shell, name and money type
            // scale, inset divider), the panel slab and the section header,
            // used by all three faces so they can't drift apart. Same
            // precedent as dnd.scss / subbar.scss.
            'shoppingList.scss',
            // FU-829 chunk 5 — the dashboard's shared card-body primitives
            // (empty states, the list-row, the stat tile) as its cards move out
            // of the page into components. Only what several cards genuinely
            // share; the card shell stays in DashboardCard.vue and anything
            // used by one card lives in that card. Same precedent as above.
            'dashboardCards.scss',
            // 2026-09-03 — the numbered method step's read chrome (list,
            // numeral circle, content column, text measure), so the recipe
            // page's free-text method and RecipeStructuredMethod draw the
            // same step. Same precedent as the three above.
            'recipeSteps.scss',
            // 2026-09-03 — the settings "worklist" card (QR labels, Unlinked
            // ingredients, Nutrition matching). All three were bare
            // `q-card flat bordered`, which is the one place the app's own
            // card language wasn't being spoken. Same precedent as above.
            'settingsCards.scss',
        ],

        // https://github.com/quasarframework/quasar/tree/dev/extras
        extras: [
            // 'ionicons-v4',
            // 'mdi-v7',
            // 'fontawesome-v6',
            // 'eva-icons',
            // 'themify',
            // 'line-awesome',
            // 'roboto-font-latin-ext', // this or either 'roboto-font', NEVER both!

            'roboto-font',
            // DS2: single icon set across the app — Material Design Icons
            // (mdi-v7). 'material-icons' kept loaded as a fallback so any
            // legacy code paths we missed in the sweep still render rather
            // than showing the icon name as a text glyph.
            'mdi-v7',
            'material-icons'
        ],

        // Full list of options: https://v2.quasar.dev/quasar-cli-vite/quasar-config-file#build
        build: {
            target: {
                browser: ['esnext'],
                node: 'node20'
            },

            typescript: {
                strict: true,
                vueShim: true
                // extendTsConfig (tsConfig) {}
            },

            vueRouterMode: 'hash', // available values: 'hash', 'history'
            // vueRouterBase,
            vueDevtools: true,
            devtool: "source-map",
            // vueOptionsAPI: false,

            // rebuildCache: true, // rebuilds Vite/linter/etc cache on startup

            // publicPath: '/',
            // analyze: true,
            // env: {},
            // rawDefine: {}
            // ignorePublicFolder: true,
            // minify: false,
            // polyfillModulePreload: true,

            // FU-336: the build ships in PWA mode (`quasar build -m pwa`), whose
            // default output dir would be `dist/pwa`. Pin it back to `dist/spa`
            // so the one canonical frontend-output path stays mode-agnostic: the
            // whole serving layer keys off `dist/spa` (nginx.conf, dora_api
            // serve_spa.py, the PyInstaller `dora.spec` data tuple, packaging/
            // build-{linux,macos}.sh, and the Playwright e2e harness). A PWA is
            // still fundamentally the SPA bundle plus a service worker + manifest,
            // so one output path serves both modes — cheaper and less error-prone
            // than threading a second `dist/pwa` path through seven consumers.
            distDir: 'dist/spa',

            // extendViteConf (viteConf) {},
            // viteVuePluginOptions: {},

            vitePlugins: [
                [
                    '@intlify/unplugin-vue-i18n/vite',
                    {
                        // if you want to use Vue I18n Legacy API, you need to set `compositionOnly: false`
                        // compositionOnly: false,

                        // if you want to use named tokens in your Vue I18n messages, such as 'Hello {name}',
                        // you need to set `runtimeOnly: false`
                        // runtimeOnly: false,

                        ssr: ctx.modeName === 'ssr',

                        // you need to set i18n resource including paths !
                        include: [fileURLToPath(new URL('./src/i18n', import.meta.url))]
                    }
                ],

                [
                    'vite-plugin-checker',
                    {
                        vueTsc: true,
                        eslint: {
                            lintCommand: 'eslint -c ./eslint.config.js "./src*/**/*.{ts,js,mjs,cjs,vue}"',
                            useFlatConfig: true
                        }
                    },
                    { server: false }
                ]
            ]
        },

        // Full list of options: https://v2.quasar.dev/quasar-cli-vite/quasar-config-file#devserver
        // Per-mode port so SSR / PWA / SPA can run side-by-side during
        // dev (matches taskboard guidance about explicit dev ports per mode).
        devServer: {
            // https: true,
            port:
                ctx.modeName === 'pwa' ? 5175 :
                ctx.modeName === 'ssr' ? 5176 :
                5174,
            open: false // opens browser window automatically
        },

        // https://v2.quasar.dev/quasar-cli-vite/quasar-config-file#framework
        framework: {
            config: {
                dark: false, // TODO: Implement dark mode...
                loading: {
                    group: "default-group-name",
                    message: "Loading...",
                    messageColor: "info",
                    spinnerColor: "info",
                    spinner: "QSpinnerTail",
                },
            },

            iconSet: 'mdi-v7', // DS2: app standardised on Material Design Icons.
            lang: 'en-US', // Quasar language pack

            // For special cases outside of where the auto-import strategy can have an impact
            // (like functional components as one of the examples),
            // you can manually specify Quasar components/directives to be available everywhere:
            //
            // components: [],
            // C-1 Chunk 5 / L72 — long-press on a stock row enters bulk-
            // select on mobile. Quasar tree-shakes directives; registering
            // here makes `v-touch-hold` available without an explicit
            // import per consumer.
            directives: ['TouchHold'],

            // Quasar plugins
            plugins: [
                "Dialog",
                "Loading",
                "Notify"
            ]
        },

        // animations: 'all', // --- includes all animations
        // https://v2.quasar.dev/options/animations
        animations: [],

        // https://v2.quasar.dev/quasar-cli-vite/quasar-config-file#sourcefiles
        // sourceFiles: {
        //   rootComponent: 'src/App.vue',
        //   router: 'src/router/index',
        //   store: 'src/store/index',
        //   pwaRegisterServiceWorker: 'src-pwa/register-service-worker',
        //   pwaServiceWorker: 'src-pwa/custom-service-worker',
        //   pwaManifestFile: 'src-pwa/manifest.json',
        //   electronMain: 'src-electron/electron-main',
        //   electronPreload: 'src-electron/electron-preload'
        //   bexManifestFile: 'src-bex/manifest.json
        // },

        // https://v2.quasar.dev/quasar-cli-vite/developing-ssr/configuring-ssr
        ssr: {
            prodPort: 5174, // The default port that the production server should use
            // (gets superseded if process.env.PORT is specified at runtime)

            middlewares: [
                'render' // keep this as last one
            ],

            // extendPackageJson (json) {},
            // extendSSRWebserverConf (esbuildConf) {},

            // manualStoreSerialization: true,
            // manualStoreSsrContextInjection: true,
            // manualStoreHydration: true,
            // manualPostHydrationTrigger: true,

            pwa: false
            // pwaOfflineHtmlFilename: 'offline.html', // do NOT use index.html as name!

            // pwaExtendGenerateSWOptions (cfg) {},
            // pwaExtendInjectManifestOptions (cfg) {}
        },

        // https://v2.quasar.dev/quasar-cli-vite/developing-pwa/configuring-pwa
        // M1 — Dashy Dora as a real PWA. GenerateSW (Workbox builds the
        // service worker for us at build time) is the lower-friction
        // route since we only need standard runtime-caching rules.
        pwa: {
            workboxMode: 'GenerateSW',
            swFilename: 'sw.js',
            manifestFilename: 'manifest.json',
            injectPwaMetaTags: true,
            useCredentialsForManifestTag: false,
            extendManifestJson(json: Record<string, unknown>) {
                json.name = 'Dashy Dora';
                json.short_name = 'Dora';
                json.description = 'Your pantry at your fingertips.';
                json.theme_color = '#f5c462';        // matches DS1's primary swatch
                json.background_color = '#f9f6f0';
                json.display = 'standalone';
                json.orientation = 'portrait-primary';
                json.start_url = '.';
                json.scope = '/';
                json.icons = [
                    {
                        src: 'icons/web-app-manifest-192x192.png',
                        sizes: '192x192', type: 'image/png', purpose: 'any',
                    },
                    {
                        src: 'icons/web-app-manifest-512x512.png',
                        sizes: '512x512', type: 'image/png', purpose: 'any',
                    },
                    {
                        // The same 512 also serves as the maskable icon
                        // until a dedicated safe-area-padded asset exists.
                        // Browsers that need a strict maskable will crop
                        // gracefully; the Dora mascot is centered.
                        src: 'icons/web-app-manifest-512x512.png',
                        sizes: '512x512', type: 'image/png', purpose: 'maskable',
                    },
                ];
                // IMPL_PLAN_RECIPE_IMPORTER §Chunk 6 — PWA share target.
                // Installed on Android, Dashy Dora shows up in the system
                // Share sheet on any recipe page; sharing hands us the
                // page's title/text/url, and we land on /cookbook, which
                // reads the query params and auto-opens the paste import
                // dialog pre-filled with the shared content. GET-mode
                // (URL query params) because Workbox's service worker
                // doesn't need to intercept a POST body — the SPA route
                // just reads `?share_text=…&share_url=…&share_title=…`.
                // No new route: RecipesOverview owns the create-from-
                // imported flow already, so anything else would just
                // duplicate it.
                json.share_target = {
                    action: '/cookbook',
                    method: 'GET',
                    params: {
                        title: 'share_title',
                        text: 'share_text',
                        url: 'share_url',
                    },
                };
                json.shortcuts = [
                    {
                        name: 'Primary shopping list',
                        short_name: 'Primary list',
                        url: '/shopping-lists?open=primary',
                        icons: [{ src: 'icons/web-app-manifest-192x192.png', sizes: '192x192' }],
                    },
                    {
                        // P2-11 — one-handed in-store mode. Lands on the
                        // /shop-now stub which resolves the primary list
                        // id and replaces the URL with the actual shop
                        // route, falling back to the lists overview if
                        // no primary is configured.
                        name: 'Shop now (primary)',
                        short_name: 'Shop now',
                        url: '/shop-now',
                        icons: [{ src: 'icons/web-app-manifest-192x192.png', sizes: '192x192' }],
                    },
                    // FU-340 — "Scan a barcode" PWA shortcut retired along
                    // with the /data/barcodes Scan tab. Every page that
                    // needs scan already has its own Scan button (Stock
                    // Overview toolbar, Add-to-list flows); if a dedicated
                    // scan launcher is wanted later it belongs on a stable
                    // surface (`/stock?scan=1` would be the shape), not on
                    // a page that no longer exists.
                    {
                        name: 'Add a stock item',
                        short_name: 'Add item',
                        url: '/stock?new=1',
                        icons: [{ src: 'icons/web-app-manifest-192x192.png', sizes: '192x192' }],
                    },
                ];
            },
            extendGenerateSWOptions(cfg: Record<string, unknown>) {
                // Snappy upgrades: a new SW activates immediately and
                // claims open tabs so the user sees the new version on
                // their next navigation (the "New version" toast then
                // offers a quick reload).
                cfg.skipWaiting = true;
                cfg.clientsClaim = true;
                cfg.cleanupOutdatedCaches = true;

                // Anything not precached: fall back to /offline.html on
                // navigation failure (the SPA shell is still the source
                // of truth — this just stops a bare browser error.)
                cfg.navigateFallback = 'index.html';
                cfg.navigateFallbackDenylist = [/^\/api\//];

                cfg.runtimeCaching = [
                    {
                        // Dora API — NetworkFirst with a 5 s timeout so a
                        // slow backend doesn't pin the UI; falls back to
                        // the cached GET response when offline.
                        urlPattern: ({ url }: { url: URL }) =>
                            url.pathname.startsWith('/api/'),
                        handler: 'NetworkFirst',
                        method: 'GET',
                        options: {
                            cacheName: 'dora-api',
                            networkTimeoutSeconds: 5,
                            expiration: { maxEntries: 200, maxAgeSeconds: 60 * 60 * 24 },
                            cacheableResponse: { statuses: [0, 200] },
                        },
                    },
                    {
                        // Merchant product images — CacheFirst, generous
                        // TTL since SKU images are basically immutable.
                        urlPattern: /\/products\/.*\/image|merchant-images/,
                        handler: 'CacheFirst',
                        options: {
                            cacheName: 'dora-merchant-images',
                            expiration: { maxEntries: 500, maxAgeSeconds: 60 * 60 * 24 * 7 },
                            cacheableResponse: { statuses: [0, 200] },
                        },
                    },
                    {
                        // Stock-item images served back by dora_api —
                        // longer TTL.
                        urlPattern: /\/stock-items\/.*\/image|\/data\/images\//,
                        handler: 'CacheFirst',
                        options: {
                            cacheName: 'dora-stock-images',
                            expiration: { maxEntries: 200, maxAgeSeconds: 60 * 60 * 24 * 30 },
                            cacheableResponse: { statuses: [0, 200] },
                        },
                    },
                ];
            },
        },

        // Full list of options: https://v2.quasar.dev/quasar-cli-vite/developing-cordova-apps/configuring-cordova
        cordova: {
            // noIosLegacyBuildFlag: true, // uncomment only if you know what you are doing
        },

        // Full list of options: https://v2.quasar.dev/quasar-cli-vite/developing-capacitor-apps/configuring-capacitor
        capacitor: {
            hideSplashscreen: true
        },

        // Full list of options: https://v2.quasar.dev/quasar-cli-vite/developing-electron-apps/configuring-electron
        electron: {
            // extendElectronMainConf (esbuildConf) {},
            // extendElectronPreloadConf (esbuildConf) {},

            // extendPackageJson (json) {},

            // Electron preload scripts (if any) from /src-electron, WITHOUT file extension
            preloadScripts: ['electron-preload'],

            // specify the debugging port to use for the Electron app when running in development mode
            inspectPort: 5858,

            bundler: 'packager', // 'packager' or 'builder'

            packager: {
                // https://github.com/electron-userland/electron-packager/blob/master/docs/api.md#options
                // OS X / Mac App Store
                // appBundleId: '',
                // appCategoryType: '',
                // osxSign: '',
                // protocol: 'myapp://path',
                // Windows only
                // win32metadata: { ... }
            },

            builder: {
                // https://www.electron.build/configuration/configuration

                appId: 'dashy-dora'
            }
        },

        // Full list of options: https://v2.quasar.dev/quasar-cli-vite/developing-browser-extensions/configuring-bex
        bex: {
            // extendBexScriptsConf (esbuildConf) {},
            // extendBexManifestJson (json) {},

            /**
             * The list of extra scripts (js/ts) not in your bex manifest that you want to
             * compile and use in your browser extension. Maybe dynamic use them?
             *
             * Each entry in the list should be a relative filename to /src-bex/
             *
             * @example [ 'my-script.ts', 'sub-folder/my-other-script.js' ]
             */
            extraScripts: []
        }
    };
});
