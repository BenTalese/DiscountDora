<template>
    <q-page padding>
        <div class="wizard-shell q-mx-auto">
            <!-- ── Header: progress + skip-everything ─────────────────── -->
            <div class="row items-center q-mb-md">
                <div class="col">
                    <div class="text-h5">Welcome to Discount Dora</div>
                    <div class="text-caption text-grey">
                        Step {{ stepIndex + 1 }} of {{ visibleSteps.length }}
                        · {{ visibleSteps[stepIndex]?.title }}
                    </div>
                </div>
                <q-btn
                    flat
                    no-caps
                    color="grey-7"
                    icon="skip_next"
                    label="Skip everything"
                    :loading="completing"
                    @click="onSkipEverything"
                />
            </div>
            <q-linear-progress
                :value="(stepIndex + 1) / visibleSteps.length"
                size="6px"
                rounded
                color="primary"
                track-color="grey-3"
                class="q-mb-lg"
            />

            <q-banner v-if="loadError" class="bg-red-1 text-red-9 q-mb-md" dense rounded>
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
                        <div class="text-body2 text-grey-8">
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
                        @keydown.enter.prevent="onNext"
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
                    <div class="text-body2 text-grey-8 q-mb-md">
                        First user on a fresh install gets the admin role
                        automatically — so all the global settings (merchants,
                        stock levels, user management) are unlocked for you
                        out of the gate. There's nothing to change here, but
                        a couple of pointers:
                    </div>
                    <q-list bordered class="rounded-borders">
                        <q-item>
                            <q-item-section avatar>
                                <q-icon name="storefront" color="primary" />
                            </q-item-section>
                            <q-item-section>
                                <q-item-label>Pick which merchants to scrape</q-item-label>
                                <q-item-label caption>
                                    Settings → Merchants. Off by default;
                                    enable only the chains you actually shop at.
                                </q-item-label>
                            </q-item-section>
                        </q-item>
                        <q-item>
                            <q-item-section avatar>
                                <q-icon name="people" color="primary" />
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
                            <q-icon name="category" size="28px" class="q-mr-sm" color="primary" />
                            <div class="col">
                                <div class="text-subtitle1">Use Dora's default stock groups</div>
                                <div class="text-caption text-grey">
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
                            class="text-caption text-grey q-py-sm"
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
                            <q-icon name="place" size="28px" class="q-mr-sm" color="primary" />
                            <div class="col">
                                <div class="text-subtitle1">Use Dora's default locations</div>
                                <div class="text-caption text-grey">
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
                            class="text-caption text-grey q-py-sm"
                        >
                            You already have locations. Same deal — opting
                            in here won't double them up.
                        </q-card-section>
                    </q-card>
                </div>
                <div class="col-12 text-caption text-grey q-mt-xs">
                    Prefer to bring in your own data?
                    <router-link to="/data/import" class="text-primary">
                        Import from Grocy or a spreadsheet instead →
                    </router-link>
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
                    <div class="text-body2 text-grey-8 q-mb-md">
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
                                v-model="firstItem.stock_group_id"
                                outlined
                                dense
                                label="Group"
                                :options="groupOptions"
                                emit-value
                                map-options
                                clearable
                                class="col-12 col-sm-4"
                            />
                            <q-select
                                v-model="firstItem.stock_location_id"
                                outlined
                                dense
                                label="Location"
                                :options="locationOptions"
                                emit-value
                                map-options
                                clearable
                                class="col-12 col-sm-4"
                            />
                            <q-select
                                v-model="firstItem.stock_level_id"
                                outlined
                                dense
                                label="Level"
                                :options="levelOptions"
                                emit-value
                                map-options
                                class="col-12 col-sm-4"
                            />
                        </div>
                        <div class="row justify-end q-gutter-sm">
                            <q-btn
                                flat
                                no-caps
                                color="grey-7"
                                label="I'll do this later"
                                @click="advance"
                            />
                            <q-btn
                                unelevated
                                no-caps
                                color="primary"
                                icon="add"
                                :label="firstItemsAdded > 0
                                    ? `Add another (${firstItemsAdded} added)`
                                    : 'Add stock item'"
                                :loading="addingItem"
                                type="submit"
                            />
                        </div>
                    </q-form>
                </q-card-section>
            </q-card>

            <!-- ── Step 5: Tour ─────────────────────────────────────── -->
            <div
                v-show="currentStep?.id === 'tour'"
                class="row q-col-gutter-md q-mb-md"
            >
                <div
                    v-for="card in TOUR_CARDS"
                    :key="card.path"
                    class="col-12 col-sm-6"
                >
                    <q-card flat bordered class="full-height">
                        <q-card-section>
                            <q-icon
                                :name="card.icon"
                                size="32px"
                                color="primary"
                                class="q-mb-sm"
                            />
                            <div class="text-subtitle1">{{ card.title }}</div>
                            <div class="text-body2 text-grey-8 q-mt-xs">
                                {{ card.description }}
                            </div>
                        </q-card-section>
                        <q-separator />
                        <q-card-actions align="right">
                            <q-btn
                                flat
                                no-caps
                                color="primary"
                                :label="`Show me ${card.shortTitle}`"
                                @click="onShowMe(card.path)"
                            />
                        </q-card-actions>
                    </q-card>
                </div>
            </div>

            <!-- ── Footer: Back / Next ──────────────────────────────── -->
            <div class="row items-center q-mt-md">
                <q-btn
                    flat
                    no-caps
                    icon="arrow_back"
                    label="Back"
                    :disable="stepIndex === 0"
                    @click="onBack"
                />
                <q-space />
                <q-btn
                    unelevated
                    color="primary"
                    no-caps
                    :icon-right="isLastStep ? 'check' : 'arrow_forward'"
                    :label="isLastStep ? 'Finish' : 'Next'"
                    :loading="advancing"
                    @click="onNext"
                />
            </div>
        </div>
    </q-page>
</template>

<script lang="ts" setup>
    import { storeToRefs } from 'pinia';
    import { useQuasar } from 'quasar';
    import type { OnboardingState } from 'src/models/onboarding';
    import type { StockGroup } from 'src/models/stockGroup';
    import OnboardingApiService from 'src/services/api/onboardingApiService';
    import StockGroupApiService from 'src/services/api/stockGroupApiService';
    import StockItemApiService from 'src/services/api/stockItemApiService';
    import { useAuthStore } from 'src/stores/authStore';
    import { useStockLevelStore } from 'src/stores/stockLevelStore';
    import { useStockLocationStore } from 'src/stores/stockLocationStore';
    import { computed, onMounted, reactive, ref, watch } from 'vue';
    import { useRouter } from 'vue-router';

    const $q = useQuasar();
    const router = useRouter();
    const onboardingApi = new OnboardingApiService();
    const stockItemApi = new StockItemApiService();
    const stockGroupApi = new StockGroupApiService();
    const authStore = useAuthStore();
    const stockLevelStore = useStockLevelStore();
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
    const THEME_OPTIONS = [
        { label: 'System (follow OS)', value: 'system' },
        { label: 'Light', value: 'light' },
        { label: 'Dark', value: 'dark' },
    ];
    const FONT_OPTIONS = [
        { label: 'Default', value: 'default' },
        { label: 'Urbanist', value: 'urbanist' },
        { label: 'Nunito', value: 'nunito' },
        { label: 'Inter', value: 'inter' },
        { label: 'Lexend', value: 'lexend' },
        { label: 'Plus Jakarta Sans', value: 'plus_jakarta_sans' },
    ];
    const TOUR_CARDS = [
        {
            path: '/stock',
            title: 'Stock overview — where you live',
            shortTitle: 'Stock',
            description:
                'Your pantry-at-a-glance. Every item, with level, location, and on-list indicator. The cart button is the single click that drops something on your shopping list.',
            icon: 'inventory_2',
        },
        {
            path: '/shopping-lists',
            title: 'Shopping lists — the killer loop',
            shortTitle: 'Shopping',
            description:
                'Auto-generate from low/out, finish a shop and your stock auto-bumps to Well-Stocked. Set a primary list so quick-adds know where to go.',
            icon: 'shopping_cart',
        },
        {
            path: '/stock?attention=true',
            title: 'Alerts — Dora pings you',
            shortTitle: 'Alerts',
            description:
                'The bell in the header. Expired, expiring soon, low/out, essentials low — with inline actions to push expiry, mark restocked, snooze.',
            icon: 'notifications_active',
        },
        {
            path: '/help',
            title: 'Help — Dora is here',
            shortTitle: 'Help',
            description:
                'The floating chat bubble follows you everywhere with context-aware actions for the screen you\'re on. Hit me up any time.',
            icon: 'help',
        },
    ];

    // ── Wizard step state ────────────────────────────────────────────
    type StepId = 'welcome' | 'admin' | 'seed' | 'first_item' | 'tour';
    type Step = { id: StepId; title: string };

    const ALL_STEPS: Step[] = [
        { id: 'welcome', title: 'Welcome' },
        { id: 'admin', title: 'You\'re the admin' },
        { id: 'seed', title: 'Seed catalogues' },
        { id: 'first_item', title: 'First stock item' },
        { id: 'tour', title: 'Take the tour' },
    ];

    const state = ref<OnboardingState | null>(null);
    const loadError = ref<string | null>(null);
    const stepIndex = ref(0);
    const advancing = ref(false);
    const completing = ref(false);
    const addingItem = ref(false);
    const firstItemsAdded = ref(0);

    // Step 2 (admin) is conditionally hidden for non-first-users.
    const visibleSteps = computed<Step[]>(() => {
        if (state.value?.first_user) return ALL_STEPS;
        return ALL_STEPS.filter((s) => s.id !== 'admin');
    });

    const currentStep = computed<Step | null>(
        () => visibleSteps.value[stepIndex.value] ?? null,
    );
    const isLastStep = computed(
        () => stepIndex.value === visibleSteps.value.length - 1,
    );

    // ── Form state (persists to localStorage so refresh resumes) ─────
    type WizardDraft = {
        displayName: string;
        theme: 'system' | 'light' | 'dark';
        fontFamily: 'default' | 'urbanist' | 'nunito';
        seedGroups: boolean;
        seedLocations: boolean;
        stepIndex: number;
    };

    const DRAFT_KEY = (userId: string) =>
        `dora.onboarding.draft.${userId || 'anonymous'}`;

    const form = reactive<WizardDraft>({
        displayName: '',
        theme: 'system',
        fontFamily: 'default',
        seedGroups: true,
        seedLocations: true,
        stepIndex: 0,
    });

    const firstItem = reactive({
        name: '',
        stock_group_id: null as string | null,
        stock_location_id: null as string | null,
        stock_level_id: '' as string,
    });

    function saveDraft() {
        try {
            const userId = currentUser.value?.user_id ?? '';
            localStorage.setItem(
                DRAFT_KEY(userId),
                JSON.stringify({ ...form, stepIndex: stepIndex.value }),
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
            const parsed = JSON.parse(raw) as Partial<WizardDraft>;
            Object.assign(form, parsed);
            if (typeof parsed.stepIndex === 'number') {
                stepIndex.value = Math.max(0, parsed.stepIndex);
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
    watch([form, stepIndex], saveDraft, { deep: true });

    // ── Option lists for the first-item form ─────────────────────────
    const groupOptions = computed(() =>
        stockGroups.value.map((g) => ({
            label: g.name,
            value: g.stock_group_id,
        })),
    );
    const locationOptions = computed(() =>
        stockLocationStore.stockLocations.map((l) => ({
            label: l.name,
            value: l.stock_location_id,
        })),
    );
    const levelOptions = computed(() =>
        stockLevelStore.stockLevels.map((l) => ({
            label: l.name,
            value: l.stock_level_id,
        })),
    );

    // ── Navigation ───────────────────────────────────────────────────
    async function onBack() {
        if (stepIndex.value === 0) return;
        stepIndex.value--;
    }

    async function onNext() {
        advancing.value = true;
        try {
            const step = currentStep.value;
            if (!step) return;

            // Per-step side effects on advance.
            if (step.id === 'welcome') {
                await persistPreferences();
            } else if (step.id === 'seed') {
                if (form.seedGroups || form.seedLocations) {
                    await onboardingApi.seedAsync({
                        groups: form.seedGroups,
                        locations: form.seedLocations,
                    });
                    // Refresh sources so step 4's pickers have something.
                    await Promise.all([
                        loadStockGroups(),
                        stockLocationStore.getStockLocationsAsync(),
                    ]);
                }
            }

            if (isLastStep.value) {
                await complete();
                return;
            }
            advance();
        } catch (err) {
            loadError.value = `Couldn't advance — ${String(err)}`;
        } finally {
            advancing.value = false;
        }
    }

    function advance() {
        if (isLastStep.value) {
            void complete();
            return;
        }
        stepIndex.value++;
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
        if (Object.keys(updates).length === 0) return;
        await authStore.updateMeAsync(updates);
    }

    async function onAddFirstItem() {
        if (!firstItem.name.trim()) return;
        addingItem.value = true;
        try {
            const wellStocked = stockLevelStore.stockLevels[0];
            const levelId = firstItem.stock_level_id || wellStocked?.stock_level_id || '';
            if (!levelId) {
                loadError.value = "No stock levels configured — skip this step.";
                return;
            }
            await stockItemApi.createAsync({
                name: firstItem.name.trim(),
                stock_level_id: levelId,
                stock_location_id: firstItem.stock_location_id ?? null,
                stock_group_id: firstItem.stock_group_id ?? null,
            });
            firstItemsAdded.value++;
            firstItem.name = '';
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: 'Added.',
            });
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not add — try again.',
                caption: String(err),
            });
        } finally {
            addingItem.value = false;
        }
    }

    function onShowMe(path: string) {
        // Closing the wizard = completing onboarding silently. The user can
        // always run "Restart onboarding" from Settings → Account if they
        // want to redo the tour.
        void complete().then(() => router.push(path));
    }

    async function onSkipEverything() {
        completing.value = true;
        try {
            // Persist the timestamp + drop a flag so the dashboard can
            // show a 24h "finish setting up" banner.
            await onboardingApi.completeAsync();
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
            loadError.value = `Couldn't skip — ${String(err)}`;
        } finally {
            completing.value = false;
        }
    }

    async function complete() {
        completing.value = true;
        try {
            await onboardingApi.completeAsync();
            clearDraft();
            // Clear any stale "skipped" flag so the dashboard banner
            // doesn't reappear after a proper completion.
            try {
                localStorage.removeItem('dora.onboarding.skipped_at');
            } catch {
                // Ignore.
            }
            void router.push('/');
        } catch (err) {
            loadError.value = `Couldn't finish — ${String(err)}`;
        } finally {
            completing.value = false;
        }
    }

    onMounted(async () => {
        try {
            state.value = await onboardingApi.getStateAsync();
        } catch (err) {
            loadError.value = `Couldn't load state — ${String(err)}`;
        }
        // Seed the displayName from the current username, theme/font from
        // the user's prefs, then layer the saved draft on top.
        if (currentUser.value) {
            form.displayName = currentUser.value.username ?? '';
            form.theme = (currentUser.value.theme ?? 'system') as
                'system' | 'light' | 'dark';
            form.fontFamily = (currentUser.value.font_family ?? 'default') as
                'default' | 'urbanist' | 'nunito';
        }
        loadDraft();

        // Pre-load the sources the first-item form needs so the pickers
        // aren't empty when the user reaches step 4.
        await Promise.all([
            loadStockGroups(),
            stockLevelStore.stockLevels.length === 0
                ? stockLevelStore.getStockLevelsAsync()
                : Promise.resolve(),
            stockLocationStore.stockLocations.length === 0
                ? stockLocationStore.getStockLocationsAsync()
                : Promise.resolve(),
        ]);

        // Default the level to the first ("most stocked").
        if (!firstItem.stock_level_id) {
            firstItem.stock_level_id =
                stockLevelStore.stockLevels[0]?.stock_level_id ?? '';
        }
    });
</script>

<style scoped>
    .wizard-shell {
        max-width: 720px;
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
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.08);
    }
    .seed-card--picked {
        outline-color: var(--q-primary);
    }
    .full-height {
        height: 100%;
    }
</style>
