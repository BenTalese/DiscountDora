<template>
    <q-page padding>
        <div class="wizard-shell q-mx-auto">
            <!-- ── Shared, non-linear progress rail (Story + Setup) ────── -->
            <div class="wizard-rail q-mb-lg">
                <OnboardingStepRail
                    :sections="railSections"
                    :active-section="view"
                    :active-index="railActiveIndex"
                    @jump="onRailJump"
                />
            </div>

            <!-- ══ STORY — cinematic intro + the hero loop ══════════════ -->
            <OnboardingStory
                v-if="view === 'story'"
                v-model:scene-index="storySceneIndex"
                v-model:persona="personaPreview"
                @enter-setup="enterSetup"
                @skip="onSkipEverything"
            />

            <!-- ══ SETUP — the steps (draft-until-finish; applied on Finish) ══ -->
            <template v-else>
            <!-- ── Header: progress + skip-everything ─────────────────── -->
            <div class="row items-center q-mb-md">
                <div class="col">
                    <div class="text-h5">Welcome to Dashy Dora</div>
                    <div class="text-caption dora-text-muted">
                        Step {{ stepIndex + 1 }} of {{ visibleSteps.length }}
                        · {{ visibleSteps[stepIndex]?.title }}
                    </div>
                </div>
                <BaseButton
                    variant="ghost"
                    class="dora-text-secondary"
                    :icon="ICONS.skip_next"
                    label="Skip"
                    :loading="completing"
                    @click="onSkipEverything"
                />
            </div>
            <q-linear-progress
                :value="(stepIndex + 1) / visibleSteps.length"
                size="6px"
                rounded
                color="primary"
                class="q-mb-lg"
            />

            <q-banner v-if="loadError" class="dora-bg-negative-soft text-negative q-mb-md" dense rounded>
                {{ loadError }}
            </q-banner>

            <!-- ── Step 1: Welcome + display name + theme + font ──────── -->
            <q-card
                v-show="currentStep?.id === 'welcome'"
                flat
                bordered
                class="q-mb-md"
            >
                <q-card-section class="row items-center q-gutter-md">
                    <q-avatar square size="72px">
                        <img src="../../assets/logo-mascot.png" alt="Dora" />
                    </q-avatar>
                    <div class="col">
                        <div class="text-h6">Hi! I'm Dora.</div>
                        <div class="text-body2 dora-text-secondary">
                            I keep your pantry, deals and meals in one place
                            so the weekly shop stops feeling like detective
                            work. Let's get you set up — takes about a minute.
                        </div>
                    </div>
                </q-card-section>
                <q-separator />
                <q-card-section class="q-gutter-md">
                    <q-input
                        v-model="form.displayName"
                        outlined
                        dense
                        label="What should I call you?"
                        autofocus
                        :error="!!displayNameError"
                        :error-message="displayNameError ?? undefined"
                        @update:model-value="displayNameError = null"
                        @keydown.enter.prevent="advance"
                    />
                    <div class="row q-col-gutter-md">
                        <q-select
                            v-model="form.theme"
                            outlined
                            dense
                            label="Theme"
                            :options="THEME_OPTIONS"
                            emit-value
                            map-options
                            class="col-12 col-sm-6"
                        />
                        <q-select
                            v-model="form.fontFamily"
                            outlined
                            dense
                            label="Font"
                            :options="FONT_OPTIONS"
                            emit-value
                            map-options
                            class="col-12 col-sm-6"
                        />
                    </div>
                    <q-input
                        v-model.number="form.headcount"
                        outlined
                        dense
                        type="number"
                        min="1"
                        max="99"
                        label="How many people do you usually cook for?"
                        hint="Cook mode scales recipes to this. Leave blank to use each recipe's own serving size."
                        @blur="onHeadcountBlur"
                    />
                </q-card-section>
            </q-card>

            <!-- ── Step 2: Admin bootstrap (first user only) ──────────── -->
            <q-card
                v-show="currentStep?.id === 'admin'"
                flat
                bordered
                class="q-mb-md"
            >
                <q-card-section>
                    <div class="text-h6 q-mb-sm">You're the admin</div>
                    <div class="text-body2 dora-text-secondary q-mb-md">
                        First user on a fresh install gets the admin role
                        automatically — so all the global settings (stores,
                        stock levels, user management) are unlocked for you
                        out of the gate. There's nothing to change here, but
                        a couple of pointers:
                    </div>
                    <q-list bordered class="rounded-borders">
                        <q-item>
                            <q-item-section avatar>
                                <q-icon :name="ICONS.storefront" color="primary" />
                            </q-item-section>
                            <q-item-section>
                                <q-item-label>Curate the stores you shop at</q-item-label>
                                <q-item-label caption>
                                    Settings → Stores. Add the stores you actually
                                    use; upload a logo so they're recognisable.
                                </q-item-label>
                            </q-item-section>
                        </q-item>
                        <q-item>
                            <q-item-section avatar>
                                <q-icon :name="ICONS.people" color="primary" />
                            </q-item-section>
                            <q-item-section>
                                <q-item-label>Invite teammates later</q-item-label>
                                <q-item-label caption>
                                    Settings → Users. Sharing is opt-in;
                                    a solo household never needs it.
                                </q-item-label>
                            </q-item-section>
                        </q-item>
                    </q-list>
                </q-card-section>
            </q-card>

            <!-- ── Step 3: Seed catalogues ──────────────────────────── -->
            <div
                v-show="currentStep?.id === 'seed'"
                class="row q-col-gutter-md q-mb-md"
            >
                <div class="col-12 col-md-6">
                    <q-card
                        flat
                        bordered
                        class="seed-card"
                        :class="{ 'seed-card--picked': form.seedGroups }"
                        @click="form.seedGroups = !form.seedGroups"
                    >
                        <q-card-section class="row items-center">
                            <q-icon :name="ICONS.category" size="28px" class="q-mr-sm" color="primary" />
                            <div class="col">
                                <div class="text-subtitle1">Use Dora's default stock groups</div>
                                <div class="text-caption dora-text-muted">
                                    Pantry, Fridge, Freezer, Cleaning, Toiletries, Pet, Other.
                                </div>
                            </div>
                            <q-checkbox
                                v-model="form.seedGroups"
                                @click.stop
                                :disable="state?.has_groups"
                            />
                        </q-card-section>
                        <q-separator v-if="state?.has_groups" />
                        <q-card-section
                            v-if="state?.has_groups"
                            class="text-caption dora-text-muted q-py-sm"
                        >
                            You already have some groups set up. Skipping
                            this leaves them alone; opting in won't create
                            duplicates.
                        </q-card-section>
                    </q-card>
                </div>
                <div class="col-12 col-md-6">
                    <q-card
                        flat
                        bordered
                        class="seed-card"
                        :class="{ 'seed-card--picked': form.seedLocations }"
                        @click="form.seedLocations = !form.seedLocations"
                    >
                        <q-card-section class="row items-center">
                            <q-icon :name="ICONS.place" size="28px" class="q-mr-sm" color="primary" />
                            <div class="col">
                                <div class="text-subtitle1">Use Dora's default locations</div>
                                <div class="text-caption dora-text-muted">
                                    Kitchen (Pantry, Fridge, Freezer), Bathroom (Cabinet),
                                    Laundry (Shelf).
                                </div>
                            </div>
                            <q-checkbox
                                v-model="form.seedLocations"
                                @click.stop
                                :disable="state?.has_locations"
                            />
                        </q-card-section>
                        <q-separator v-if="state?.has_locations" />
                        <q-card-section
                            v-if="state?.has_locations"
                            class="text-caption dora-text-muted q-py-sm"
                        >
                            You already have locations. Same deal — opting
                            in here won't double them up.
                        </q-card-section>
                    </q-card>
                </div>
                <div class="col-12 text-caption dora-text-muted q-mt-xs">
                    Prefer to bring in your own data?
                    <router-link to="/data/import" class="text-primary">
                        Import from a spreadsheet or another app instead →
                    </router-link>
                </div>

                <!-- Starter packs (L37) — tick a pack to add its common items. -->
                <div v-if="(catalog?.packs?.length ?? 0) > 0" class="col-12">
                    <div class="text-subtitle1 q-mt-sm">Starter packs</div>
                    <div class="text-caption dora-text-muted q-mb-sm">
                        Tick a pack to add its common items (already grouped + located).
                        Expand one to choose individual items.
                    </div>
                    <q-list bordered class="rounded-borders">
                        <q-expansion-item
                            v-for="pack in catalog?.packs ?? []"
                            :key="pack.key"
                        >
                            <template #header>
                                <q-item-section avatar>
                                    <q-checkbox
                                        :model-value="packState(pack)"
                                        toggle-indeterminate
                                        @update:model-value="togglePack(pack, $event)"
                                        @click.stop
                                    />
                                </q-item-section>
                                <q-item-section>
                                    <q-item-label>{{ pack.label }}</q-item-label>
                                    <q-item-label caption>
                                        {{ pack.blurb }} ·
                                        {{ packSelectedCount(pack) }}/{{ pack.items.length }} chosen
                                    </q-item-label>
                                </q-item-section>
                            </template>
                            <q-list>
                                <q-item
                                    v-for="item in pack.items"
                                    :key="item.name"
                                    tag="label"
                                    dense
                                >
                                    <q-item-section>
                                        <q-item-label>{{ item.name }}</q-item-label>
                                        <q-item-label
                                            v-if="item.group || item.location"
                                            caption
                                        >
                                            {{ [item.group, item.location].filter(Boolean).join(' · ') }}
                                        </q-item-label>
                                    </q-item-section>
                                    <q-item-section side>
                                        <q-checkbox v-model="packItemSelected[item.name]" />
                                    </q-item-section>
                                </q-item>
                            </q-list>
                        </q-expansion-item>
                    </q-list>
                </div>
            </div>

            <!-- ── Step 4: First stock item ─────────────────────────── -->
            <q-card
                v-show="currentStep?.id === 'first_item'"
                flat
                bordered
                class="q-mb-md"
            >
                <q-card-section>
                    <div class="text-h6 q-mb-sm">Add your first stock item</div>
                    <div class="text-body2 dora-text-secondary q-mb-md">
                        Pick something obvious — a staple you always have on
                        hand. You can add the rest in batches later.
                    </div>
                    <q-form @submit.prevent="onAddFirstItem" class="q-gutter-md">
                        <q-input
                            v-model="firstItem.name"
                            outlined
                            dense
                            label="Name"
                            placeholder="e.g. Milk, Olive oil, Pasta"
                            autofocus
                            :rules="[(v: string) => !!v || 'Give it a name']"
                        />
                        <div class="row q-col-gutter-sm">
                            <q-select
                                v-model="firstItem.group_name"
                                outlined
                                dense
                                label="Group"
                                :options="groupNameOptions"
                                clearable
                                class="col-12 col-sm-6"
                            />
                            <q-select
                                v-model="firstItem.location_name"
                                outlined
                                dense
                                label="Location"
                                :options="locationNameOptions"
                                clearable
                                class="col-12 col-sm-6"
                            />
                        </div>
                        <div class="row justify-end q-gutter-sm">
                            <BaseButton
                                variant="ghost"
                                class="dora-text-secondary"
                                label="I'll do this later"
                                @click="advance"
                            />
                            <BaseButton
                                variant="primary"
                                :icon="ICONS.add"
                                :label="draftItems.length > 0
                                    ? `Add another (${draftItems.length} added)`
                                    : 'Add stock item'"
                                type="submit"
                            />
                        </div>
                    </q-form>

                    <!-- Slim "added" list (L36) — the queued first items. -->
                    <q-list
                        v-if="draftItems.length > 0"
                        bordered
                        class="rounded-borders q-mt-md"
                    >
                        <q-item-label header class="q-pb-xs">
                            Added ({{ draftItems.length }}) — saved when you finish
                        </q-item-label>
                        <q-item v-for="(item, idx) in draftItems" :key="idx">
                            <q-item-section>
                                <q-item-label>{{ item.name }}</q-item-label>
                                <q-item-label
                                    v-if="item.group_name || item.location_name"
                                    caption
                                >
                                    {{ [item.group_name, item.location_name].filter(Boolean).join(' · ') }}
                                </q-item-label>
                            </q-item-section>
                            <q-item-section side>
                                <BaseButton
                                    variant="icon"
                                    :icon="ICONS.delete"
                                    aria-label="Remove"
                                    @click="removeDraftItem(idx)"
                                />
                            </q-item-section>
                        </q-item>
                    </q-list>
                </q-card-section>
            </q-card>

            <!-- ── Step: Finish — celebrate + flow-cards (C-5.6) ── -->
            <!-- FU-210 revisit (2026-06-17): the loop recap was removed from
                 Finish — the hero already plays in Story, replaying it here
                 was repetitive. The loop survives in Story; a help-section
                 home is tracked separately. -->
            <div
                v-show="currentStep?.id === 'finish'"
                class="finish-step q-mb-md"
            >
                <OnboardingConfetti v-if="currentStep?.id === 'finish'" />
                <div class="text-center q-mb-lg">
                    <div class="text-h5">You're all set! 🎉</div>
                    <div class="text-body2 dora-text-secondary q-mt-xs">
                        Pick where to go next.
                    </div>
                </div>
                <div class="text-subtitle1 q-mb-sm">Where to go next</div>
                <div class="row q-col-gutter-md">
                    <div
                        v-for="card in flowCards"
                        :key="card.path"
                        class="col-12 col-sm-6"
                    >
                        <q-card flat bordered class="full-height">
                            <q-card-section>
                                <q-icon
                                    :name="card.icon"
                                    size="30px"
                                    color="primary"
                                    class="q-mb-sm"
                                />
                                <div class="text-subtitle1">{{ card.title }}</div>
                                <div class="text-body2 dora-text-secondary q-mt-xs">
                                    {{ card.description }}
                                </div>
                            </q-card-section>
                            <q-separator />
                            <q-card-actions>
                                <BaseButton
                                    variant="ghost"
                                    class="text-primary"
                                    :label="`Open ${card.shortTitle}`"
                                    @click="onShowMe(card.path)"
                                />
                                <q-space />
                                <BaseButton
                                    v-if="card.help"
                                    variant="ghost"
                                    class="dora-text-secondary"
                                    label="Guide"
                                    :icon-right="ICONS.open_in_new"
                                    @click="onShowMe(card.help)"
                                />
                            </q-card-actions>
                        </q-card>
                    </div>
                </div>
            </div>

            <!-- ── Footer: Back / Next ──────────────────────────────── -->
            <div class="row items-center q-mt-md">
                <BaseButton
                    variant="ghost"
                    :icon="ICONS.arrow_back"
                    label="Back"
                    :disable="stepIndex === 0"
                    @click="onBack"
                />
                <q-space />
                <BaseButton
                    variant="primary"
                    :icon-right="isLastStep ? 'check' : 'arrow_forward'"
                    :label="isLastStep ? 'Finish' : 'Next'"
                    :loading="completing"
                    @click="advance"
                />
            </div>
            </template>
        </div>
    </q-page>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import BaseButton from 'src/components/BaseButton.vue';
    import OnboardingConfetti from 'src/components/onboarding/OnboardingConfetti.vue';
    import OnboardingStepRail from 'src/components/onboarding/OnboardingStepRail.vue';
    import OnboardingStory from 'src/pages/onboarding/OnboardingStory.vue';
    import { storeToRefs } from 'pinia';
    import { useQuasar } from 'quasar';
    import type { FontFamilyPreference, ThemePreference } from 'src/models/auth';
    import type {
        LocationNode,
        OnboardingCatalog,
        OnboardingState,
        StarterPack,
        StarterPackItem,
    } from 'src/models/onboarding';
    import {
        DEFAULT_PERSONA_PREVIEW,
        NARRATIVE_SCENES,
        type PersonaPreviewKey,
    } from 'src/pages/onboarding/onboardingContent';
    import type { StockGroup } from 'src/models/stockGroup';
    import OnboardingApiService from 'src/services/api/onboardingApiService';
    import StockGroupApiService from 'src/services/api/stockGroupApiService';
    import { extractFieldErrors } from 'src/services/errorHandling/apiErrorHandler';
    import { useAuthStore } from 'src/stores/authStore';
    import { useStockLocationStore } from 'src/stores/stockLocationStore';
    import { computed, onMounted, reactive, ref, watch } from 'vue';
    import { useRouter } from 'vue-router';

    const $q = useQuasar();
    const router = useRouter();
    const onboardingApi = new OnboardingApiService();
    const stockGroupApi = new StockGroupApiService();
    const authStore = useAuthStore();
    const stockLocationStore = useStockLocationStore();

    const { currentUser } = storeToRefs(authStore);

    // Stock groups don't have a store of their own; load them locally.
    const stockGroups = ref<StockGroup[]>([]);
    async function loadStockGroups() {
        try {
            stockGroups.value = await stockGroupApi.getAllAsync();
        } catch {
            stockGroups.value = [];
        }
    }

    // ── Static option lists ──────────────────────────────────────────
    // L28 — onboarding offers only System / Light / Dark. Light maps to the
    // brand light theme (Pesto) and Dark to Pesto Dark; the rest of the
    // palette catalogue (lemon-tart, blueberry, …) is pickable later in
    // Preferences. Values are real ThemePreference keys so we persist the
    // resolved theme rather than the legacy 'light'/'dark' aliases.
    const THEME_OPTIONS: { label: string; value: ThemePreference }[] = [
        { label: 'System (follow OS)', value: 'system' },
        { label: 'Light', value: 'pesto' },
        { label: 'Dark', value: 'pesto-dark' },
    ];
    const FONT_OPTIONS = [
        { label: 'Default', value: 'default' },
        { label: 'Urbanist', value: 'urbanist' },
        { label: 'Nunito', value: 'nunito' },
        { label: 'Inter', value: 'inter' },
        { label: 'Lexend', value: 'lexend' },
        { label: 'Plus Jakarta Sans', value: 'plus_jakarta_sans' },
    ];
    // ── Wizard step state ────────────────────────────────────────────
    type StepId =
        | 'welcome' | 'admin' | 'persona'
        | 'seed' | 'first_item' | 'finish';
    type Step = { id: StepId; title: string };

    const state = ref<OnboardingState | null>(null);
    const loadError = ref<string | null>(null);
    const displayNameError = ref<string | null>(null);
    const stepIndex = ref(0);
    const completing = ref(false);

    // ── Story / Setup view model (C-5.2) ─────────────────────────────
    // Two sections with instant, non-linear cross-jump via the shared rail.
    const view = ref<'story' | 'setup'>('story');
    const storySceneIndex = ref(0);
    // Persona PREVIEW only — sets no flags. Remembered so the C-5.3 fork can
    // pre-fill from whatever the user last previewed in the hero loop.
    const personaPreview = ref<PersonaPreviewKey>(DEFAULT_PERSONA_PREVIEW);

    // Setup steps are built per-state: admin is first-user only. (FU-210: the
    // persona fork step is removed — onboarding is one "show everything" path;
    // features are enabled in Settings, not chosen here. FU-209 removed the
    // stock-vs-product explainer.)
    const visibleSteps = computed<Step[]>(() => {
        const steps: Step[] = [{ id: 'welcome', title: 'Welcome' }];
        if (state.value?.first_user) {
            steps.push({ id: 'admin', title: "You're the admin" });
        }
        steps.push({ id: 'seed', title: 'Seed catalogues' });
        steps.push({ id: 'first_item', title: 'First stock item' });
        steps.push({ id: 'finish', title: "You're all set" });
        return steps;
    });

    // ── Finish flow-cards (C-5.6) — persona-relevant key areas, each a
    // jump-in + a link to the help guides (FU-015: Alerts → /alerts). Copy
    // kept factual; the sell-copy honesty pass is FU-184.
    const flowCards = computed(() => {
        const cards: {
            path: string;
            title: string;
            shortTitle: string;
            description: string;
            icon: string;
            help?: string;
        }[] = [
            { path: '/stock', shortTitle: 'Stock', title: 'Your pantry',
              description: 'Everything you keep, with levels, locations and expiry — your home base.',
              icon: ICONS.inventory_2, help: '/help' },
            { path: '/cookbook', shortTitle: 'Recipes', title: 'Cookbook & cook mode',
              description: 'See what you can cook from what’s in, then cook it step by step.',
              icon: ICONS.menu_book, help: '/help' },
            { path: '/meal-plans', shortTitle: 'Meals', title: 'Plan the week',
              description: 'Plan meals and turn the week into a shopping list.',
              icon: ICONS.event, help: '/help' },
            { path: '/shopping-lists', shortTitle: 'Shopping', title: 'Shopping lists',
              description: 'Auto-built from what’s low or out; finish a shop and your stock refills.',
              icon: ICONS.shopping_cart, help: '/help' },
            { path: '/alerts', shortTitle: 'Alerts', title: 'Alerts',
              description: 'The bell flags what’s expiring, low or out — with one-tap actions.',
              icon: ICONS.notifications_active, help: '/help' },
        ];
        // Show everything — price history is available whenever the user turns
        // on spend tracking in Settings (FU-210: no onboarding flag gating).
        cards.push({
            path: '/price-history', shortTitle: 'Prices', title: 'Price history',
            description: 'See how your prices have moved over time.',
            icon: ICONS.savings, help: '/help',
        });
        cards.push({
            path: '/help', shortTitle: 'guides', title: 'Dora & the guides',
            description: 'Dora’s help bubble follows you everywhere; the guides explain each area in depth.',
            icon: ICONS.smart_toy,
        });
        return cards;
    });

    const currentStep = computed<Step | null>(
        () => visibleSteps.value[stepIndex.value] ?? null,
    );
    const isLastStep = computed(
        () => stepIndex.value === visibleSteps.value.length - 1,
    );

    // ── Shared rail model (Story scenes + Setup steps) ───────────────
    // Nothing is gated — every dot is a jump target across both sections.
    const railSections = computed(() => [
        {
            key: 'story',
            label: 'Story',
            dots: NARRATIVE_SCENES.map((s) => ({
                key: s.id,
                label: s.kicker ?? s.headline,
            })),
        },
        {
            key: 'setup',
            label: 'Setup',
            dots: visibleSteps.value.map((s) => ({ key: s.id, label: s.title })),
        },
    ]);
    const railActiveIndex = computed(() =>
        view.value === 'story' ? storySceneIndex.value : stepIndex.value,
    );
    function onRailJump(sectionKey: string, index: number) {
        if (sectionKey === 'story') {
            view.value = 'story';
            storySceneIndex.value = index;
        } else {
            view.value = 'setup';
            stepIndex.value = index;
        }
    }
    function enterSetup() {
        view.value = 'setup';
    }

    // ── Form state (persists to localStorage so refresh resumes) ─────
    type WizardDraft = {
        displayName: string;
        theme: ThemePreference;
        fontFamily: FontFamilyPreference;
        headcount: number | null;
        seedGroups: boolean;
        seedLocations: boolean;
        stepIndex: number;
    };

    // A first stock item the user queued — created on Finish (L35), never
    // on each Add, so a mid-wizard bail leaves nothing behind.
    type DraftItem = {
        name: string;
        group_name: string | null;
        location_name: string | null;
    };

    const DRAFT_KEY = (userId: string) =>
        `dora.onboarding.draft.${userId || 'anonymous'}`;

    const form = reactive<WizardDraft>({
        displayName: '',
        theme: 'system',
        fontFamily: 'default',
        headcount: null,
        seedGroups: true,
        seedLocations: true,
        stepIndex: 0,
    });

    const firstItem = reactive({
        name: '',
        group_name: null as string | null,
        location_name: null as string | null,
    });

    // Queued first items, awaiting creation on Finish.
    const draftItems = ref<DraftItem[]>([]);

    // C-5.5 — starter catalogue (default groups/locations + packs), fetched on
    // mount, and the pack items the user has ticked (keyed by item name).
    const catalog = ref<OnboardingCatalog | null>(null);
    const packItemSelected = reactive<Record<string, boolean>>({});
    async function loadCatalog() {
        try {
            catalog.value = await onboardingApi.getCatalogAsync();
        } catch {
            catalog.value = null;
        }
    }

    function saveDraft() {
        try {
            const userId = currentUser.value?.user_id ?? '';
            localStorage.setItem(
                DRAFT_KEY(userId),
                JSON.stringify({
                    ...form,
                    stepIndex: stepIndex.value,
                    draftItems: draftItems.value,
                    view: view.value,
                    storySceneIndex: storySceneIndex.value,
                    personaPreview: personaPreview.value,
                    packItemSelected: { ...packItemSelected },
                }),
            );
        } catch {
            // localStorage may be unavailable.
        }
    }
    function loadDraft() {
        try {
            const userId = currentUser.value?.user_id ?? '';
            const raw = localStorage.getItem(DRAFT_KEY(userId));
            if (!raw) return;
            const parsed = JSON.parse(raw) as Partial<WizardDraft> & {
                stepIndex?: number;
                draftItems?: DraftItem[];
                view?: 'story' | 'setup';
                storySceneIndex?: number;
                personaPreview?: PersonaPreviewKey;
                packItemSelected?: Record<string, boolean>;
            };
            const {
                stepIndex: savedIndex,
                draftItems: savedItems,
                view: savedView,
                storySceneIndex: savedScene,
                personaPreview: savedPersona,
                packItemSelected: savedPacks,
                ...formFields
            } = parsed;
            Object.assign(form, formFields);
            if (typeof savedIndex === 'number') {
                stepIndex.value = Math.max(0, savedIndex);
            }
            if (Array.isArray(savedItems)) {
                draftItems.value = savedItems;
            }
            if (savedView === 'story' || savedView === 'setup') {
                view.value = savedView;
            }
            if (typeof savedScene === 'number') {
                storySceneIndex.value = Math.max(0, savedScene);
            }
            if (savedPersona) {
                personaPreview.value = savedPersona;
            }
            if (savedPacks) {
                Object.assign(packItemSelected, savedPacks);
            }
        } catch {
            // Bad draft — ignore.
        }
    }
    function clearDraft() {
        try {
            const userId = currentUser.value?.user_id ?? '';
            localStorage.removeItem(DRAFT_KEY(userId));
        } catch {
            // Best effort.
        }
    }
    // Auto-save the draft on any form change so a refresh resumes.
    watch(
        [
            form, stepIndex, draftItems, view, storySceneIndex,
            personaPreview, packItemSelected,
        ],
        saveDraft,
        { deep: true },
    );

    // ── Starter-pack helpers + first-item name options ───────────────
    function uniqueSorted(values: (string | null | undefined)[]): string[] {
        const set = new Set<string>();
        for (const v of values) {
            const name = (v ?? '').trim();
            if (name) set.add(name);
        }
        return [...set].sort((a, b) => a.localeCompare(b));
    }
    function flattenLocationNames(nodes: LocationNode[]): string[] {
        const names: string[] = [];
        for (const node of nodes) {
            names.push(node.name);
            names.push(...flattenLocationNames(node.children));
        }
        return names;
    }

    // The pack items the user has ticked (catalog packs ∩ packItemSelected),
    // deduped by name (the server dedupes again on create).
    const selectedPackItemsList = computed<StarterPackItem[]>(() => {
        const out: StarterPackItem[] = [];
        const seen = new Set<string>();
        for (const pack of catalog.value?.packs ?? []) {
            for (const item of pack.items) {
                if (packItemSelected[item.name] && !seen.has(item.name)) {
                    seen.add(item.name);
                    out.push(item);
                }
            }
        }
        return out;
    });

    // First-item group/location pickers offer NAMES (resolved server-side on
    // Finish — FU-191): seeded defaults (if chosen) + any pack groups +
    // whatever already exists.
    const groupNameOptions = computed(() =>
        uniqueSorted([
            ...(form.seedGroups ? (catalog.value?.groups ?? []) : []),
            ...selectedPackItemsList.value.map((it) => it.group),
            ...stockGroups.value.map((g) => g.name),
        ]),
    );
    const locationNameOptions = computed(() =>
        uniqueSorted([
            ...(form.seedLocations
                ? flattenLocationNames(catalog.value?.locations ?? [])
                : []),
            ...selectedPackItemsList.value.map((it) => it.location),
            ...stockLocationStore.stockLocations.map((l) => l.name),
        ]),
    );

    function packSelectedCount(pack: StarterPack): number {
        return pack.items.filter((it) => packItemSelected[it.name]).length;
    }
    function packState(pack: StarterPack): boolean | null {
        const n = packSelectedCount(pack);
        if (n === 0) return false;
        if (n === pack.items.length) return true;
        return null; // some selected → indeterminate
    }
    function togglePack(pack: StarterPack, value: boolean | null) {
        const on = value === true;
        for (const item of pack.items) packItemSelected[item.name] = on;
    }

    // ── Navigation ───────────────────────────────────────────────────
    function onBack() {
        if (stepIndex.value === 0) return;
        stepIndex.value--;
    }

    // Next / Finish. Advancing a step has NO side effects now — every
    // choice (prefs, seeds, queued items) is applied once, in complete(),
    // so a mid-wizard bail leaves the account untouched (L35). The final
    // step triggers that one-shot apply.
    function advance() {
        if (isLastStep.value) {
            void finish('/');
            return;
        }
        stepIndex.value++;
    }

    // Finish (or "Show me X") = apply the draft, then navigate. On a failed
    // apply we stay put with the error shown so the user can fix + retry.
    async function finish(destination: string) {
        if (await complete()) void router.push(destination);
    }

    // Apply everything the user chose, once, in dependency order: prefs →
    // persona → seed catalogues → stock items (pack picks + queued first
    // items), so the items resolve against the groups/locations just seeded.
    async function applyDraft() {
        await persistPreferences();
        if (form.seedGroups || form.seedLocations) {
            await onboardingApi.seedAsync({
                groups: form.seedGroups,
                locations: form.seedLocations,
            });
        }
        // Pack picks + first items, created by NAME (server resolves group /
        // location against the just-seeded catalogues — FU-191 — and dedupes).
        const items = [
            ...selectedPackItemsList.value.map((it) => ({
                name: it.name,
                group_name: it.group,
                location_name: it.location,
            })),
            ...draftItems.value.map((d) => ({
                name: d.name,
                group_name: d.group_name,
                location_name: d.location_name,
            })),
        ];
        if (items.length > 0) {
            await onboardingApi.seedItemsAsync({ items });
        }
    }

    function handleApplyError(err: unknown) {
        const extracted = extractFieldErrors(err);
        // The displayName field maps to the server's `username` validator.
        // Surface it and jump back to the welcome step — by Finish it may
        // be off-screen.
        if (extracted.fieldErrors.username) {
            displayNameError.value = extracted.fieldErrors.username;
            delete extracted.fieldErrors.username;
            const welcomeIdx = visibleSteps.value.findIndex((s) => s.id === 'welcome');
            if (welcomeIdx >= 0) stepIndex.value = welcomeIdx;
        }
        const remainingFields = Object.values(extracted.fieldErrors).filter(Boolean);
        loadError.value =
            [extracted.generalError, ...remainingFields].filter(Boolean).join(' ') ||
            "Couldn't finish setting up. Please try again.";
    }

    async function persistPreferences() {
        const updates: Record<string, unknown> = {};
        if (form.displayName.trim().length > 0
            && form.displayName !== currentUser.value?.username) {
            updates.username = form.displayName.trim();
        }
        if (form.theme !== currentUser.value?.theme) {
            updates.theme = form.theme;
        }
        if (form.fontFamily !== currentUser.value?.font_family) {
            updates.font_family = form.fontFamily;
        }
        if (form.headcount !== (currentUser.value?.household_headcount ?? null)) {
            updates.household_headcount = form.headcount;
        }
        if (Object.keys(updates).length === 0) return;
        await authStore.updateMeAsync(updates);
    }

    // Clamp the headcount field on blur: empty/invalid → null (use recipe
    // servings), otherwise a 1–99 integer (matches the server bounds).
    function onHeadcountBlur() {
        const value = form.headcount;
        if (value === null || value === undefined || !Number.isFinite(value) || value < 1) {
            form.headcount = null;
        } else {
            form.headcount = Math.min(99, Math.floor(value));
        }
    }

    function onAddFirstItem() {
        const name = firstItem.name.trim();
        if (!name) return;
        // Queue, don't persist — created on Finish so a bail leaves nothing (L35).
        draftItems.value.push({
            name,
            group_name: firstItem.group_name,
            location_name: firstItem.location_name,
        });
        firstItem.name = '';
        $q.notify({
            type: 'positive',
            position: 'bottom-right',
            message: 'Added — saved when you finish.',
        });
    }

    function removeDraftItem(index: number) {
        draftItems.value.splice(index, 1);
    }

    function onShowMe(path: string) {
        // "Show me X" = finish onboarding (applying the draft), then land on
        // that screen. The user can always run "Restart onboarding" from
        // Settings → Account if they want to redo the tour.
        void finish(path);
    }

    async function onSkipEverything() {
        completing.value = true;
        try {
            // Persist the timestamp + drop a flag so the dashboard can
            // show a 24h "finish setting up" banner.
            await onboardingApi.completeAsync();
            // Refresh the cached user so the router guard sees the new
            // `onboarding_completed_at`. Without this, the guard reads the
            // stale (null) value and bounces the user straight back to
            // /welcome — making the button look dead until a hard refresh.
            await authStore.refreshAsync();
            try {
                localStorage.setItem(
                    'dora.onboarding.skipped_at',
                    new Date().toISOString(),
                );
            } catch {
                // Ignore — banner just won't fire.
            }
            clearDraft();
            void router.push('/');
        } catch (err) {
            const extracted = extractFieldErrors(err);
            loadError.value =
                extracted.generalError ?? "Couldn't skip onboarding. Please try again.";
        } finally {
            completing.value = false;
        }
    }

    // Apply the collected draft + stamp completion. Returns true on success;
    // the caller navigates (Finish → '/', Show-me → the chosen path) so a
    // failed apply keeps the user in the wizard with the error shown.
    async function complete(): Promise<boolean> {
        completing.value = true;
        loadError.value = null;
        displayNameError.value = null;
        try {
            await applyDraft();
            await onboardingApi.completeAsync();
            // Refresh the cached user so the router guard sees the new
            // `onboarding_completed_at`. Without this, Finish / Show-me-X
            // navigations bounce straight back to /welcome on the first
            // attempt (the guard reads stale null); user only escapes
            // after a hard refresh re-bootstraps the auth state.
            await authStore.refreshAsync();
            clearDraft();
            // Clear any stale "skipped" flag so the dashboard banner
            // doesn't reappear after a proper completion.
            try {
                localStorage.removeItem('dora.onboarding.skipped_at');
            } catch {
                // Ignore.
            }
            return true;
        } catch (err) {
            handleApplyError(err);
            return false;
        } finally {
            completing.value = false;
        }
    }

    onMounted(async () => {
        try {
            state.value = await onboardingApi.getStateAsync();
        } catch (err) {
            const extracted = extractFieldErrors(err);
            loadError.value =
                extracted.generalError ?? "Couldn't load onboarding state. Please refresh.";
        }
        // Seed the displayName from the current username, theme/font from
        // the user's prefs, then layer the saved draft on top.
        if (currentUser.value) {
            form.displayName = currentUser.value.username ?? '';
            // Pre-fill from the user's saved prefs. If their stored theme
            // isn't one of the three onboarding options (e.g. they picked a
            // richer palette in Preferences on a re-run), the select shows
            // blank and persistPreferences leaves it untouched — we never
            // clobber a real choice.
            form.theme = currentUser.value.theme ?? 'system';
            form.fontFamily = currentUser.value.font_family ?? 'default';
            form.headcount = currentUser.value.household_headcount ?? null;
        }
        loadDraft();

        // Pre-load existing groups/locations (so the first-item name pickers
        // include what's already there) + the starter catalogue (default
        // names + packs to preview and pick from).
        await Promise.all([
            loadStockGroups(),
            stockLocationStore.stockLocations.length === 0
                ? stockLocationStore.getStockLocationsAsync()
                : Promise.resolve(),
            loadCatalog(),
        ]);
    });
</script>

<style scoped>
    .wizard-shell {
        max-width: 720px;
    }
    /* Bounds the absolutely-positioned finish confetti to the step. */
    .finish-step {
        position: relative;
    }
    .seed-card {
        cursor: pointer;
        transition: outline-color 120ms ease, transform 120ms ease,
            box-shadow 120ms ease;
        outline: 2px solid transparent;
        outline-offset: -2px;
        height: 100%;
    }
    .seed-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 14px var(--overlay-active);
    }
    .seed-card--picked {
        outline-color: var(--q-primary);
    }
    .full-height {
        height: 100%;
    }
</style>
