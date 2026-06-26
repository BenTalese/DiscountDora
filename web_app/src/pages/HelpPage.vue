<template>
    <q-page padding>
        <div class="row items-center q-mb-md">
            <DoraMascot mood="excited" :size="48" />
            <div class="q-ml-md col">
                <div class="text-caption dora-text-muted">
                    Guides by area, a peek at what's new, and a fun fact while you're here.
                </div>
            </div>
            <!-- FU-006: ambiguous — flat with color="accent"; no BaseButton variant supports the accent palette. Left as raw q-btn for review. -->
            <q-btn
                flat
                no-caps
                color="accent"
                :icon="ICONS.smart_toy"
                label="Meet DoraBot"
                :to="{ path: '/help/dora' }"
                class="q-mr-sm"
            />
            <!-- Repo is private — no public issues page. Bug reports
                 go through whatever channel the operator has set up
                 with the user; removed the dead-link button. -->

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
                A newer version of Discount Dora is available
                ({{ versionInfo.latest_version }}). You're on
                {{ versionInfo.current_version }}.
            </div>
            <template #action>
                <!-- FU-006: ambiguous — type="a" anchor form not in BaseButton's type union; left as raw q-btn for review. -->
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
                            Discount Dora {{ versionInfo.current_version }}
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
                    <!-- Repo is private — the public-repo + issues
                         links were removed. Bug reports and feature
                         requests go through whatever channel the
                         operator has set up. -->
                    <q-card-section class="dora-text-muted text-caption">
                        Found a bug or want a feature? Note the steps
                        you took and what you expected, and pass it
                        to whoever runs this Dora instance.
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
    import { useRouter } from 'vue-router';
    import { describeApiError } from 'src/services/errorHandling/apiErrorHandler';

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
                        'On the Stock page, click "+ New stock item". Set the name, stock level, and optionally a location, expiry, or flag.',
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
                        "Only when an admin has connected the AI assistant (Settings > System). With it on, I understand plain-language questions about your data, suggest recipes, and add to your shopping list. With it off, I'm a simpler rule-based helper that matches keywords.",
                },
                {
                    title: 'Set up the AI assistant (admin)',
                    summary:
                        "The assistant is opt-in and uses a language model you host yourself (e.g. Ollama). Install Ollama on a machine on your network, pull a tool-capable model like qwen2.5:7b, then in Settings > System > AI assistant enter its base URL (e.g. http://localhost:11434) and model name, enable, and save. Nothing is downloaded or enabled by default.",
                    path: '/settings/admin/system/assistant',
                },
            ],
        },
    ];

    const $q = useQuasar();
    const router = useRouter();
    const helpApi = new HelpApiService();

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
</style>
