<template>
    <q-page padding>
        <div class="row items-center q-mb-md">
            <DoraMascot mood="excited" :size="48" />
            <div class="q-ml-md col">
                <div class="text-caption text-grey">
                    Guides by area, a peek at what's new, and a fun fact while you're here.
                </div>
            </div>
            <q-btn
                flat
                no-caps
                color="accent"
                :icon="ICONS.smart_toy"
                label="Meet DoraBot"
                :to="{ path: '/help/dora' }"
                class="q-mr-sm"
            />
            <q-btn
                flat
                no-caps
                :icon="ICONS.open_in_new"
                label="Report a bug"
                type="a"
                href="https://github.com/BenTalese/DiscountDora/issues/new"
                target="_blank"
                rel="noopener"
            />
        </div>

        <q-banner
            v-if="versionInfo?.update_available"
            class="bg-amber-2 text-amber-9 q-mb-md"
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
                    <div class="text-caption text-grey">Food fact</div>
                    <div>{{ foodFact }}</div>
                </div>
                <q-btn
                    flat
                    round
                    dense
                    :icon="ICONS.refresh"
                    :loading="loadingFact"
                    @click="loadFoodFact"
                >
                    <q-tooltip>Another, please</q-tooltip>
                </q-btn>
            </q-card-section>
        </q-card>

        <q-tabs
            v-model="tab"
            dense
            class="text-primary"
            active-color="primary"
            indicator-color="primary"
            align="left"
        >
            <q-tab name="guides" :icon="ICONS.menu_book" label="Guides" no-caps />
            <q-tab name="changelog" :icon="ICONS.new_releases" label="What's new" no-caps />
            <q-tab name="about" :icon="ICONS.info" label="About" no-caps />
        </q-tabs>

        <q-separator />

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
                                </q-item>
                            </q-list>
                        </q-card>
                    </div>

                    <div
                        v-if="filteredGuides.length === 0"
                        class="col-12 text-center text-grey q-py-lg"
                    >
                        Nothing matches "{{ search }}".
                    </div>
                </div>
            </q-tab-panel>

            <!-- Changelog ───────────────────────────────────────── -->
            <q-tab-panel name="changelog" class="q-pa-none q-pt-md">
                <q-banner
                    v-if="changelogError"
                    class="bg-red-1 text-red-9 q-mb-md"
                    dense
                    rounded
                >
                    {{ changelogError }}
                </q-banner>

                <div v-if="changelogEntries.length === 0 && !changelogLoading" class="text-grey">
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
                        <div class="text-caption text-grey">
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
                    <q-list separator>
                        <q-item
                            clickable
                            tag="a"
                            href="https://github.com/BenTalese/DiscountDora"
                            target="_blank"
                            rel="noopener"
                        >
                            <q-item-section avatar><q-icon :name="ICONS.code" /></q-item-section>
                            <q-item-section>
                                <q-item-label>Project repository</q-item-label>
                                <q-item-label caption>github.com/BenTalese/DiscountDora</q-item-label>
                            </q-item-section>
                        </q-item>
                        <q-item
                            clickable
                            tag="a"
                            href="https://github.com/BenTalese/DiscountDora/issues/new"
                            target="_blank"
                            rel="noopener"
                        >
                            <q-item-section avatar>
                                <q-icon :name="ICONS.bug_report" />
                            </q-item-section>
                            <q-item-section>
                                <q-item-label>Report a bug or request a feature</q-item-label>
                                <q-item-label caption>Opens a GitHub issue.</q-item-label>
                            </q-item-section>
                        </q-item>
                    </q-list>
                </q-card>
            </q-tab-panel>
        </q-tab-panels>
    </q-page>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import { useQuasar } from 'quasar';
    import DoraMascot from 'src/components/dora/DoraMascot.vue';
    import HelpApiService, {
        type ChangelogEntry,
        type VersionInfo
    } from 'src/services/api/helpApiService';
    import { computed, onMounted, ref } from 'vue';
    import { useRouter } from 'vue-router';
    import { describeApiError } from 'src/services/errorHandling/apiErrorHandler';

    type GuideEntry = { title: string; summary: string; path?: string };
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
                    title: 'Link a merchant product to a stock item',
                    summary:
                        'On the detail page, search for a product. Linking lets the live deal price ride alongside your pantry record.',
                    path: '/product-search',
                },
            ],
        },
        {
            title: 'Locations',
            icon: ICONS.place,
            entries: [
                {
                    title: 'Zones, areas and sections',
                    summary:
                        'Locations is a tree: Zone (e.g. Pantry) > Area (e.g. Middle shelf) > Section (e.g. Left side). Drill down or skip levels — items can attach at any depth.',
                    path: '/locations',
                },
                {
                    title: 'Read the heatmap',
                    summary:
                        'Each location gets a 0-100 attention score, coloured green > teal > yellow > orange > red. Reasons explain it: "2 expired, 4 low stock, 1 flagged".',
                    path: '/locations',
                },
                {
                    title: 'Move items between locations',
                    summary:
                        'Drag a chip onto any zone, area or section to move it. On mobile, tap the move icon for the hierarchical picker.',
                    path: '/locations',
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
                    path: '/recipes',
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
                        'Product Search hits the configured merchants live (Coles, Woolworths, IGA, Aldi). Disabled merchants are skipped. Use the admin Merchants page to toggle them.',
                    path: '/product-search',
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
                    title: 'Toggle merchants (admin)',
                    summary:
                        'Disable a scraper if it keeps breaking. Use the health check button to confirm each is reachable.',
                    path: '/settings/admin/merchants',
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
                        "The assistant is opt-in and uses a language model you host yourself (e.g. Ollama). Install Ollama on a machine on your network, pull a tool-capable model like qwen2.5:7b, then in Settings > System enter its base URL (e.g. http://localhost:11434) and model name, enable, and save. Nothing is downloaded or enabled by default.",
                    path: '/settings/admin/system',
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
        if (entry.path) void router.push(entry.path);
    }

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
        loadChangelog();
        loadFoodFact();
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
            rgba(23, 176, 115, 0.06),
            rgba(254, 210, 36, 0.08)
        );
    }
    .changelog-body {
        white-space: pre-wrap;
        font-family: inherit;
        margin: 0;
    }
</style>
