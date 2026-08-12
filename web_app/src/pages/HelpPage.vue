<template>
    <q-page padding>
        <div class="row items-center q-mb-md">
            <DoraMascot mood="excited" :size="48" />
            <div class="q-ml-md col">
                <div class="text-caption dora-text-muted">
                    Guides by area, a peek at what's new, and a fun fact while you're here.
                </div>
            </div>
            <!-- ambiguous — flat with color="accent"; no BaseButton variant supports the accent palette. Left as raw q-btn for review. -->
            <q-btn
                flat
                no-caps
                color="accent"
                :icon="ICONS.smart_toy"
                label="Meet D.O.R.A."
                :to="{ path: '/help/dora' }"
                class="q-mr-sm"
            />
            <!-- FU-370 — renders only when the operator has configured a
                 support channel (see support_channel.py). Dormant installs
                 show nothing here, exactly as before. type="a" anchor form
                 isn't in BaseButton's type union; matches the sibling raw
                 q-btn pattern above. -->
            <q-btn
                v-if="hasChannel"
                flat
                no-caps
                color="accent"
                :icon="ICONS.bug_report"
                label="Report an issue"
                type="a"
                :href="reportHref"
                target="_blank"
                rel="noopener"
            />
        </div>

        <q-banner
            v-if="versionInfo?.update_available"
            class="dora-bg-warning-soft text-warning q-mb-md"
            rounded
        >
            <template #avatar>
                <q-icon :name="ICONS.system_update" />
            </template>
            <div class="text-weight-medium">
                A newer version of Dashy Dora is available
                ({{ versionInfo.latest_version }}). You're on
                {{ versionInfo.current_version }}.
            </div>
            <template #action>
                <!-- ambiguous — type="a" anchor form not in BaseButton's type union; left as raw q-btn for review. -->
                <q-btn
                    v-if="versionInfo.release_url"
                    flat
                    no-caps
                    label="See release notes"
                    type="a"
                    :href="versionInfo.release_url"
                    target="_blank"
                    rel="noopener"
                />
            </template>
        </q-banner>

        <q-card v-if="foodFact" flat bordered class="q-mb-md food-fact-card">
            <q-card-section class="row items-start">
                <q-icon :name="ICONS.restaurant" size="22px" color="primary" />
                <div class="q-ml-md col">
                    <div class="text-caption dora-text-muted">Food fact</div>
                    <div>{{ foodFact }}</div>
                </div>
                <BaseButton
                    variant="icon"
                    :icon="ICONS.refresh"
                    :loading="loadingFact"
                    @click="loadFoodFact"
                >
                    <q-tooltip>Another, please</q-tooltip>
                </BaseButton>
            </q-card-section>
        </q-card>

        <DoraTabs
            v-model="tab"
            :tabs="[
                { name: 'guides', label: 'Guides', icon: ICONS.menu_book },
                { name: 'changelog', label: `What's new`, icon: ICONS.new_releases },
                { name: 'about', label: 'About', icon: ICONS.info },
            ]"
        />

        <q-tab-panels v-model="tab" animated class="bg-transparent">
            <!-- Guides ──────────────────────────────────────────── -->
            <q-tab-panel name="guides" class="q-pa-none q-pt-md">
                <q-input
                    v-model="search"
                    outlined
                    dense
                    clearable
                    placeholder="Filter guides…"
                    class="q-mb-md"
                >
                    <template #prepend><q-icon :name="ICONS.search" /></template>
                </q-input>

                <div class="row q-col-gutter-md">
                    <div
                        v-for="group in filteredGuides"
                        :key="group.title"
                        class="col-12 col-md-6"
                    >
                        <q-card flat bordered>
                            <q-card-section class="row items-center">
                                <q-icon :name="group.icon" size="22px" color="primary" />
                                <div class="q-ml-sm text-h6">{{ group.title }}</div>
                            </q-card-section>
                            <q-separator />
                            <q-list separator>
                                <q-item
                                    v-for="entry in group.entries"
                                    :key="entry.title"
                                    clickable
                                    @click="onGuideClick(entry)"
                                >
                                    <q-item-section>
                                        <q-item-label>{{ entry.title }}</q-item-label>
                                        <q-item-label caption>
                                            {{ entry.summary }}
                                        </q-item-label>
                                    </q-item-section>
                                    <q-item-section side v-if="entry.path">
                                        <q-icon :name="ICONS.arrow_forward" />
                                    </q-item-section>
                                    <q-item-section side v-else-if="entry.dialog">
                                        <q-icon :name="ICONS.info_outline" />
                                    </q-item-section>
                                </q-item>
                            </q-list>
                        </q-card>
                    </div>

                    <div
                        v-if="filteredGuides.length === 0"
                        class="col-12 text-center dora-text-muted q-py-lg"
                    >
                        Nothing matches "{{ search }}".
                    </div>
                </div>
            </q-tab-panel>

            <!-- Changelog ───────────────────────────────────────── -->
            <q-tab-panel name="changelog" class="q-pa-none q-pt-md">
                <q-banner
                    v-if="changelogError"
                    class="dora-bg-negative-soft text-negative q-mb-md"
                    dense
                    rounded
                >
                    {{ changelogError }}
                </q-banner>

                <div v-if="changelogEntries.length === 0 && !changelogLoading" class="dora-text-muted">
                    No changelog entries found.
                </div>

                <q-list bordered>
                    <q-expansion-item
                        v-for="(entry, idx) in changelogEntries"
                        :key="entry.version"
                        :default-opened="idx < 2 || entry.version.toLowerCase() === 'unreleased'"
                        :label="entry.version"
                        :caption="entry.date ?? undefined"
                        header-class="text-weight-medium"
                        expand-separator
                    >
                        <q-card flat>
                            <q-card-section>
                                <pre class="changelog-body">{{ entry.body }}</pre>
                            </q-card-section>
                        </q-card>
                    </q-expansion-item>
                </q-list>
            </q-tab-panel>

            <!-- About ──────────────────────────────────────────── -->
            <q-tab-panel name="about" class="q-pa-none q-pt-md">
                <q-card flat bordered>
                    <q-card-section v-if="versionInfo">
                        <div class="text-h6">
                            Dashy Dora {{ versionInfo.current_version }}
                        </div>
                        <div class="text-caption dora-text-muted">
                            <span v-if="versionInfo.latest_version === null">
                                Couldn't check for updates ({{ versionInfo.error ?? 'unknown reason' }}).
                            </span>
                            <span v-else-if="versionInfo.update_available">
                                {{ versionInfo.latest_version }} is available.
                            </span>
                            <span v-else> You're on the latest version. </span>
                        </div>
                    </q-card-section>
                    <q-separator />
                    <!-- FU-370 — honest one-person/side-project support copy
                         (replaces the old "pass it to whoever runs this Dora
                         instance" line). The final paragraph adapts: when a
                         support channel is configured it points at the
                         Report-an-issue button above; when dormant it falls
                         back to the graceful "ask whoever runs this" form. -->
                    <q-card-section class="text-caption">
                        <div class="text-body2 text-weight-medium q-mb-xs">
                            Getting help &amp; reporting issues
                        </div>
                        <div class="dora-text-muted support-copy">
                            <p>
                                Dashy Dora is built by one person as a side
                                project. Bug reports and feature requests are
                                welcome and every one gets read — but replies can
                                take days or weeks. There's no on-call and no
                                support team; just someone doing this in evenings
                                and weekends.
                            </p>
                            <p>
                                If a family member set up this Dora for you, ask
                                them first — most problems are quicker to solve
                                locally.
                            </p>
                            <p v-if="hasChannel">
                                Otherwise, use the
                                <strong>Report an issue</strong> button at the top
                                of this page. Before filing, note the steps you
                                took, what you expected, and what happened
                                instead. Screenshots help.
                            </p>
                            <p v-else>
                                Otherwise, note the steps you took, what you
                                expected, and what happened instead (screenshots
                                help), and pass it to whoever runs this Dora
                                instance.
                            </p>
                        </div>
                    </q-card-section>
                </q-card>
            </q-tab-panel>
        </q-tab-panels>

        <AttentionRulesDialog v-model="attentionRulesOpen" />
    </q-page>
</template>

<script lang="ts" setup>
    import BaseButton from 'src/components/BaseButton.vue';
    import { ICONS } from 'src/style/icons';
    import { useQuasar } from 'quasar';
    import AttentionRulesDialog from 'src/components/help/AttentionRulesDialog.vue';
    import DoraMascot from 'src/components/dora/DoraMascot.vue';
    import DoraTabs from 'src/components/DoraTabs.vue';
    import HelpApiService, {
        type ChangelogEntry,
        type VersionInfo
    } from 'src/services/api/helpApiService';
    import { computed, onMounted, ref } from 'vue';
    import { useRoute, useRouter } from 'vue-router';
    import { describeApiError } from 'src/services/errorHandling/apiErrorHandler';
    import {
        useSupportChannel,
        supportHref,
    } from 'src/composables/useSupportChannel';

    type GuideEntry = {
        title: string;
        summary: string;
        path?: string;
        /** Opens an inline explainer dialog instead of navigating away.
         *  Used for visual-cue topics that benefit from swatches + tables. */
        dialog?: 'attention-rules';
    };
    type GuideGroup = { title: string; icon: string; entries: GuideEntry[] };

    const GUIDES: GuideGroup[] = [
        {
            title: 'Stock',
            icon: 'inventory_2',
            entries: [
                {
                    title: 'Add a stock item',
                    summary:
                        'On the Stock page, click "New item". Set the name and stock level, and optionally a location, stock group, or the Essential flag. Expiry is set on the item itself once it\'s added.',
                    path: '/stock',
                },
                {
                    title: 'Track expiry and flag essentials',
                    summary:
                        'In a stock item detail page, set an expiry date — Dora surfaces upcoming expiries on the Locations heatmap. Flag essentials so they always show up first.',
                    path: '/stock',
                },
                {
                    title: 'What the colours and outlines mean',
                    summary:
                        'When a row outlines amber or red, when an item is dimmed, and what "Needs attention" actually counts — one page of the rules with swatches and a cheat sheet.',
                    dialog: 'attention-rules',
                },
                {
                    title: 'The "Dora thinks…" hint',
                    summary:
                        'Dora quietly infers what you actually have — a coarse Out / Low / Stocked belief worked out from your purchases, how often you rebuy, and what you\'ve cooked, decayed by time since the last real signal. It never changes your recorded level; that stays the source of truth for shopping and cooking. She only speaks up when it\'s worth it: when her belief differs from what you recorded, a small amber "Dora thinks low/out/stocked" appears beside the item — hover for the reason and how sure she is, then a quick check sets things straight. When she agrees with you she stays silent. Turn the hint off entirely in Settings → Preferences.',
                    path: '/stock',
                },
                {
                    title: 'Link a product to a stock item',
                    summary:
                        'On the detail page, link a product to your stock item so its offers + price history ride alongside your pantry record.',
                    path: '/stock',
                },
            ],
        },
        {
            title: 'Recipes & meals',
            icon: ICONS.menu_book,
            entries: [
                {
                    title: 'Cook mode',
                    summary:
                        'Open a recipe and hit Cook. Steps render one card at a time and ingredients show where each one lives (e.g. Pantry > Top shelf).',
                    path: '/cookbook',
                },
                {
                    title: 'Build a meal plan',
                    summary:
                        'Group recipes into meals (e.g. roast + sides). Then schedule meals onto a meal plan; the dashboard shows the next entry on the home page.',
                    path: '/meal-plans',
                },
            ],
        },
        {
            title: 'Shopping & deals',
            icon: ICONS.shopping_cart,
            entries: [
                {
                    title: 'Search for products',
                    summary:
                        'Product Search opens an admin-configured external search surface in a new tab. The destination pushes data back into Dora via the ingestion seam.',
                    path: '/',
                },
            ],
        },
        {
            title: 'Settings & admin',
            icon: ICONS.settings,
            entries: [
                {
                    title: 'Theme, font, and text size',
                    summary:
                        'In Preferences, switch between System / Light / Dark, pick a font (Urbanist, Nunito, Inter, Lexend, or Plus Jakarta Sans), and adjust text size.',
                    path: '/settings/preferences',
                },
                {
                    title: 'Manage other users (admin)',
                    summary:
                        "Admins see a Users page in Settings: toggle admin role, edit username/email, manage who's subscribed to the weekly deals email, and reset a forgotten password.",
                    path: '/settings/admin/users',
                },
                {
                    title: 'Manage stores (admin)',
                    summary:
                        'Curate the list of retail stores Dora knows about. Add a store, upload a logo, or remove ones you no longer track. No stores ship by default.',
                    path: '/settings/kitchen-setup/stores',
                },
            ],
        },
        {
            title: 'Dora itself',
            icon: ICONS.mood,
            entries: [
                {
                    title: 'How does Dora know what page I\'m on?',
                    summary:
                        "I read the route. When you click 'What can I do on this page?' I look up a per-route summary. If I don't have one, I'll say so honestly.",
                },
                {
                    title: 'Can Dora do free-form questions?',
                    summary:
                        "Only when you've configured AI mode for your account (Settings > Assistant). With it on, I understand plain-language questions about your data, suggest recipes, and add to your shopping list. With it off, I'm a simpler rule-based helper that matches keywords. AI mode is per-account, so two people in the same household can use different providers.",
                },
                {
                    title: 'Set up AI mode (per account)',
                    summary:
                        "Go to Settings > Assistant. Pick a provider — Ollama (local LLM you run yourself, no API key), or OpenAI / Anthropic / Google Gemini (paid hosted APIs, bring your own key). For Ollama: enter the base URL (e.g. http://localhost:11434) + a tool-capable model like qwen2.5:7b. For paid providers: paste your API key + pick a model. Use Test connection to verify before turning AI mode on. Off by default.",
                    path: '/settings/assistant',
                },
                {
                    title: 'AI mode says "unavailable" — why?',
                    summary:
                        "The chat panel shows an \"AI mode unavailable\" banner when you've turned AI on but the configured LLM didn't respond. Common causes: your Ollama server isn't running; the API key is wrong; the model name is mistyped; or the backend can't reach the URL (see network topology below). Click Retry on the banner after fixing it, or hit Test connection in Settings > Assistant first to find the issue before turning AI on.",
                },
                {
                    title: "Network topology: who reaches the LLM?",
                    summary:
                        "The Dora backend reaches your LLM, not your browser. That means the backend's network has to see your LLM's URL. On a single-laptop install (backend + LLM on the same box) this is just localhost. On a household setup with the backend on a NAS/Pi and an LLM on a different desktop, the backend needs to be able to reach that desktop (LAN routing, Tailscale, or a port forward). The base URL you save in Settings is from the *backend's* point of view.",
                },
                {
                    title: "Paid providers: API-key encryption (DORA_SECRET_ENCRYPTION_KEY)",
                    summary:
                        "AI mode is per-account — there's no install-wide master switch; each person just configures it on Settings > Assistant. For paid providers (OpenAI / Anthropic / Gemini), the install needs the environment variable DORA_SECRET_ENCRYPTION_KEY set so your API key can be stored encrypted at rest — until it is, the Assistant page shows a warning and can generate a key for you to paste into the environment. Generate one from a shell with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\". Ollama-only installs don't need the env var. Rotating the key invalidates every saved key; users re-enter on next save.",
                    path: '/settings/assistant',
                },
            ],
        },
    ];

    const $q = useQuasar();
    const router = useRouter();
    const route = useRoute();
    const helpApi = new HelpApiService();

    // FU-370 — support channel; button + copy self-gate on `hasChannel`.
    const { channel, hasChannel } = useSupportChannel();
    const reportHref = computed(() =>
        supportHref(channel.value, {
            subject: `[Dora] Bug — v${versionInfo.value?.current_version ?? 'unknown'}`,
            body: `\n\n---\nDora ${versionInfo.value?.current_version ?? 'unknown'} · ${route.path}`,
        }),
    );

    const tab = ref<'guides' | 'changelog' | 'about'>('guides');
    const search = ref('');

    const changelogEntries = ref<ChangelogEntry[]>([]);
    const changelogLoading = ref(false);
    const changelogError = ref<string | null>(null);

    const versionInfo = ref<VersionInfo | null>(null);

    const foodFact = ref<string | null>(null);
    const loadingFact = ref(false);

    const filteredGuides = computed<GuideGroup[]>(() => {
        const q = (search.value ?? '').toLowerCase().trim();
        if (!q) return GUIDES;
        return GUIDES.map((g) => ({
            ...g,
            entries: g.entries.filter(
                (e) =>
                    e.title.toLowerCase().includes(q) ||
                    e.summary.toLowerCase().includes(q),
            ),
        })).filter((g) => g.entries.length > 0);
    });

    function onGuideClick(entry: GuideEntry) {
        if (entry.dialog === 'attention-rules') {
            attentionRulesOpen.value = true;
            return;
        }
        if (entry.path) void router.push(entry.path);
    }

    const attentionRulesOpen = ref(false);

    async function loadChangelog() {
        changelogLoading.value = true;
        changelogError.value = null;
        try {
            const result = await helpApi.getChangelogAsync();
            changelogEntries.value = result.entries;
        } catch (err) {
            changelogError.value = `Couldn't load the changelog: ${describeApiError(err)}`;
        } finally {
            changelogLoading.value = false;
        }
    }

    async function loadFoodFact() {
        loadingFact.value = true;
        try {
            foodFact.value = (await helpApi.getFoodFactAsync()).fact;
        } catch {
            foodFact.value = null;
            $q.notify({
                type: 'warning',
                position: 'bottom-right',
                message: "Couldn't fetch a food fact right now."
            });
        } finally {
            loadingFact.value = false;
        }
    }

    onMounted(async () => {
        // Fire everything in parallel — none of them block the page render.
        void loadChangelog();
        void loadFoodFact();
        try {
            versionInfo.value = await helpApi.getVersionAsync();
        } catch {
            versionInfo.value = null;
        }
    });
</script>

<style scoped>
    .food-fact-card {
        background: linear-gradient(
            120deg,
            color-mix(in srgb, var(--brand-primary) 6%, transparent),
            color-mix(in srgb, var(--brand-accent) 8%, transparent)
        );
    }
    .changelog-body {
        white-space: pre-wrap;
        font-family: inherit;
        margin: 0;
    }
    .support-copy p {
        margin: 0 0 8px;
    }
    .support-copy p:last-child {
        margin-bottom: 0;
    }
</style>
