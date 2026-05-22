<template>
    <div class="q-pa-md cook-mode">
        <div v-if="!recipe" class="text-center q-pa-xl">
            <q-spinner size="40px" v-if="loading" />
            <q-banner v-else class="bg-grey-2">Recipe not found.</q-banner>
        </div>

        <template v-else>
            <div class="row items-center q-mb-md">
                <q-btn flat icon="arrow_back" label="Exit" @click="exitCookMode" />
                <q-space />
                <div class="text-h5 ellipsis">{{ recipe.name }}</div>
                <q-space />
                <q-btn
                    flat
                    round
                    :icon="speechEnabled ? 'volume_up' : 'volume_off'"
                    :color="speechEnabled ? 'primary' : 'grey'"
                    @click="toggleSpeech"
                >
                    <q-tooltip>{{ speechEnabled ? 'Disable voice' : 'Enable voice' }}</q-tooltip>
                </q-btn>
                <q-btn
                    v-if="speechRecognitionAvailable"
                    flat
                    round
                    :icon="listening ? 'mic' : 'mic_off'"
                    :color="listening ? 'red' : 'grey'"
                    @click="toggleListening"
                >
                    <q-tooltip>{{ listening ? 'Stop listening' : 'Listen for "next" / "previous" / "repeat"' }}</q-tooltip>
                </q-btn>
            </div>

            <q-linear-progress
                :value="(currentStepIndex + 1) / steps.length"
                class="q-mb-md"
                size="10px"
                color="primary"
                rounded
            />

            <div class="text-caption q-mb-sm">
                Step {{ currentStepIndex + 1 }} of {{ steps.length }}
            </div>

            <q-card flat bordered class="step-card q-mb-md">
                <q-card-section>
                    <div class="text-h4 step-text">{{ currentStep }}</div>
                </q-card-section>

                <q-card-section v-if="detectedTimerMinutes !== null" class="bg-grey-2">
                    <div class="row items-center q-gutter-sm">
                        <q-icon name="timer" size="32px" color="primary" />
                        <div class="text-h6">
                            {{ formatTimer(timerRemaining ?? detectedTimerMinutes * 60) }}
                        </div>
                        <q-space />
                        <q-btn
                            v-if="!timerRunning"
                            color="primary"
                            icon="play_arrow"
                            label="Start"
                            @click="startTimer(detectedTimerMinutes * 60)"
                        />
                        <q-btn
                            v-else
                            color="warning"
                            icon="pause"
                            label="Pause"
                            @click="pauseTimer"
                        />
                        <q-btn
                            v-if="timerRemaining !== null"
                            flat
                            icon="restart_alt"
                            label="Reset"
                            @click="resetTimer"
                        />
                    </div>
                </q-card-section>
            </q-card>

            <div class="row q-gutter-sm justify-center q-mb-lg">
                <q-btn
                    size="lg"
                    icon="arrow_back"
                    label="Previous"
                    :disable="currentStepIndex === 0"
                    @click="prevStep"
                />
                <q-btn
                    size="lg"
                    icon="replay"
                    label="Repeat"
                    @click="speakCurrent"
                    :disable="!speechEnabled"
                />
                <q-btn
                    size="lg"
                    color="primary"
                    :icon-right="currentStepIndex === steps.length - 1 ? 'check' : 'arrow_forward'"
                    :label="currentStepIndex === steps.length - 1 ? 'Finish' : 'Next'"
                    @click="nextStep"
                />
            </div>

            <q-expansion-item
                default-opened
                icon="kitchen"
                header-class="text-subtitle1"
            >
                <template #header>
                    <q-item-section avatar><q-icon name="kitchen" /></q-item-section>
                    <q-item-section>Ingredients</q-item-section>
                    <q-item-section side>
                        <span class="text-caption text-grey">
                            {{ usedIds.size }} / {{ ingredientRows.length }} used
                        </span>
                    </q-item-section>
                </template>
                <q-list dense>
                    <q-item v-for="row in ingredientRows" :key="row.ingredient.recipe_ingredient_id">
                        <q-item-section side top>
                            <q-checkbox
                                :model-value="usedIds.has(row.ingredient.stock_item_id)"
                                @update:model-value="toggleUsed(row.ingredient.stock_item_id)"
                            >
                                <q-tooltip>Mark used</q-tooltip>
                            </q-checkbox>
                        </q-item-section>
                        <q-item-section>
                            <div class="row items-center q-gutter-xs no-wrap">
                                <span class="text-caption text-grey">
                                    <span v-if="row.ingredient.quantity">{{ row.ingredient.quantity }}</span>
                                    <span v-if="row.ingredient.unit"> {{ row.ingredient.unit }}</span>
                                </span>
                                <StockItemChip v-if="row.stockItem" :stock-item="row.stockItem" />
                                <span v-else>{{ row.ingredient.stock_item_name }}</span>
                            </div>
                            <q-item-label
                                v-if="row.ingredient.notes"
                                caption
                                class="text-grey"
                            >
                                {{ row.ingredient.notes }}
                            </q-item-label>
                            <q-item-label
                                v-if="row.ingredient.stock_location_id"
                                caption
                            >
                                <q-icon name="place" size="14px" />
                                {{ breadcrumbFor(row.ingredient.stock_location_id).join(' › ') }}
                            </q-item-label>
                        </q-item-section>
                    </q-item>
                </q-list>
            </q-expansion-item>

            <q-expansion-item label="All steps" icon="list" header-class="text-subtitle1">
                <q-list>
                    <q-item
                        v-for="(step, idx) in steps"
                        :key="idx"
                        :active="idx === currentStepIndex"
                    >
                        <q-item-section side top>
                            <q-checkbox
                                :model-value="doneSteps.has(idx)"
                                @update:model-value="toggleStepDone(idx)"
                            >
                                <q-tooltip>Mark step done (marks its ingredients used)</q-tooltip>
                            </q-checkbox>
                        </q-item-section>
                        <q-item-section side>{{ idx + 1 }}.</q-item-section>
                        <q-item-section clickable @click="goToStep(idx)">{{ step }}</q-item-section>
                    </q-item>
                </q-list>
            </q-expansion-item>
        </template>

        <!-- Finish flow ─────────────────────────────────────────────────── -->
        <q-dialog v-model="finishDialogOpen" persistent>
            <q-card style="min-width: 360px; max-width: 95vw">
                <q-card-section class="text-h6">Finished cooking?</q-card-section>
                <q-card-section class="q-gutter-sm q-pt-none">
                    <q-toggle v-model="finishUpdateLevels" label="Update stock levels (use up what you cooked with)" />
                    <q-toggle v-model="finishLogMeal" label="Log this as a meal eaten" />
                    <q-toggle v-model="finishAddRanOut" label="Add anything that ran out to a shopping list" />
                    <div class="text-caption text-grey">
                        {{ usedIds.size }} ingredient(s) marked used.
                    </div>
                </q-card-section>
                <q-card-actions align="right">
                    <q-btn flat no-caps label="Skip & exit" @click="finishDialogOpen = false; exitCookMode()" />
                    <q-btn color="primary" no-caps label="Done" :loading="finishing" @click="confirmFinish" />
                </q-card-actions>
            </q-card>
        </q-dialog>
    </div>
</template>

<script lang="ts" setup>
    import { storeToRefs } from 'pinia';
    import { useQuasar } from 'quasar';
    import StockItemChip from 'src/components/chips/StockItemChip.vue';
    import { useShoppingListActions } from 'src/composables/useShoppingListActions';
    import type { Recipe } from 'src/models/recipe';
    import type { StockItem } from 'src/models/stockItem';
    import RecipeApiService from 'src/services/api/recipeApiService';
    import { useLocationStore } from 'src/stores/locationStore';
    import { useRecipeStore } from 'src/stores/recipeStore';
    import { useShoppingListStore } from 'src/stores/shoppingListStore';
    import { useStockItemStore } from 'src/stores/stockItemStore';
    import { useStockLevelStore } from 'src/stores/stockLevelStore';
    import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
    import { useRoute, useRouter } from 'vue-router';

    const route = useRoute();
    const router = useRouter();
    const $q = useQuasar();
    const recipeStore = useRecipeStore();
    const locationStore = useLocationStore();
    const stockItemStore = useStockItemStore();
    const stockLevelStore = useStockLevelStore();
    const shoppingListStore = useShoppingListStore();
    const recipeApiService = new RecipeApiService();
    const slActions = useShoppingListActions();

    const { stockItems } = storeToRefs(stockItemStore);
    const { stockLevels } = storeToRefs(stockLevelStore);

    // Resolve location_id → breadcrumb names using the locations tree.
    // We hit the location store lazily on mount so cook mode keeps working
    // even when the tree hasn't been opened yet.
    function breadcrumbFor(locationId: string): string[] {
        return locationStore.breadcrumb(locationId);
    }

    const recipe = ref<Recipe | null>(null);
    const loading = ref(true);
    const currentStepIndex = ref(0);

    const speechEnabled = ref(false);
    const listening = ref(false);
    const speechRecognitionAvailable = ref(false);

    const timerRemaining = ref<number | null>(null);
    const timerRunning = ref(false);
    let timerIntervalId: ReturnType<typeof setInterval> | null = null;

    type SpeechRecognitionLike = {
        continuous: boolean;
        interimResults: boolean;
        lang: string;
        start: () => void;
        stop: () => void;
        onresult: ((event: { results: ArrayLike<ArrayLike<{ transcript: string }>> }) => void) | null;
        onend: (() => void) | null;
        onerror: ((event: unknown) => void) | null;
    };
    type SpeechRecognitionCtor = new () => SpeechRecognitionLike;

    let recognition: SpeechRecognitionLike | null = null;

    const steps = computed(() => {
        if (!recipe.value?.instructions) return ['No instructions provided.'];
        const parts = recipe.value.instructions
            .split(/\r?\n+/)
            .map((s) => s.replace(/^\s*\d+[.)]\s*/, '').trim())
            .filter((s) => s.length > 0);
        return parts.length > 0 ? parts : [recipe.value.instructions];
    });

    const currentStep = computed(() => steps.value[currentStepIndex.value] ?? '');

    // ── Ingredient "used" tracking ───────────────────────────────────────
    const usedIds = ref<Set<string>>(new Set());
    const doneSteps = ref<Set<number>>(new Set());

    type IngredientRow = { ingredient: Recipe['ingredients'][number]; stockItem: StockItem | null };
    const ingredientRows = computed<IngredientRow[]>(() =>
        (recipe.value?.ingredients ?? []).map((ingredient) => ({
            ingredient,
            stockItem:
                stockItems.value.find((si) => si.stock_item_id === ingredient.stock_item_id) ?? null,
        })),
    );

    function toggleUsed(stockItemId: string) {
        if (usedIds.value.has(stockItemId)) usedIds.value.delete(stockItemId);
        else usedIds.value.add(stockItemId);
        usedIds.value = new Set(usedIds.value);
    }

    // Mark every ingredient whose name appears in a step's text as used.
    function markIngredientsUsedInStep(stepText: string) {
        const text = stepText.toLowerCase();
        for (const ing of recipe.value?.ingredients ?? []) {
            if (text.includes(ing.stock_item_name.toLowerCase())) {
                usedIds.value.add(ing.stock_item_id);
            }
        }
        usedIds.value = new Set(usedIds.value);
    }

    function toggleStepDone(idx: number) {
        if (doneSteps.value.has(idx)) doneSteps.value.delete(idx);
        else {
            doneSteps.value.add(idx);
            markIngredientsUsedInStep(steps.value[idx] ?? '');
        }
        doneSteps.value = new Set(doneSteps.value);
    }

    const detectedTimerMinutes = computed<number | null>(() => {
        const text = currentStep.value.toLowerCase();
        const minMatch = text.match(/(\d+(?:\.\d+)?)\s*(?:minutes?|mins?|m\b)/);
        if (minMatch) return parseFloat(minMatch[1]!);
        const hourMatch = text.match(/(\d+(?:\.\d+)?)\s*(?:hours?|hrs?|h\b)/);
        if (hourMatch) return parseFloat(hourMatch[1]!) * 60;
        return null;
    });

    function formatTimer(seconds: number): string {
        const m = Math.floor(seconds / 60);
        const s = Math.floor(seconds % 60);
        return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
    }

    function startTimer(seconds: number) {
        if (timerRemaining.value === null) timerRemaining.value = seconds;
        timerRunning.value = true;
        if (timerIntervalId) clearInterval(timerIntervalId);
        timerIntervalId = setInterval(() => {
            if (timerRemaining.value === null) return;
            timerRemaining.value -= 1;
            if (timerRemaining.value <= 0) {
                timerRemaining.value = 0;
                pauseTimer();
                $q.notify({ type: 'positive', message: 'Timer finished!', icon: 'timer' });
                if (speechEnabled.value) speak('Timer finished');
            }
        }, 1000);
    }

    function pauseTimer() {
        timerRunning.value = false;
        if (timerIntervalId) {
            clearInterval(timerIntervalId);
            timerIntervalId = null;
        }
    }

    function resetTimer() {
        pauseTimer();
        timerRemaining.value = null;
    }

    function speak(text: string) {
        if (!speechEnabled.value || typeof window === 'undefined' || !window.speechSynthesis) return;
        window.speechSynthesis.cancel();
        const utter = new SpeechSynthesisUtterance(text);
        window.speechSynthesis.speak(utter);
    }

    function speakCurrent() {
        speak(currentStep.value);
    }

    function toggleSpeech() {
        speechEnabled.value = !speechEnabled.value;
        if (speechEnabled.value) speakCurrent();
        else if (typeof window !== 'undefined') window.speechSynthesis?.cancel();
    }

    function nextStep() {
        resetTimer();
        // Advancing past a step counts it done and uses up its ingredients.
        doneSteps.value.add(currentStepIndex.value);
        doneSteps.value = new Set(doneSteps.value);
        markIngredientsUsedInStep(currentStep.value);
        if (currentStepIndex.value < steps.value.length - 1) {
            currentStepIndex.value += 1;
        } else {
            openFinish();
        }
    }

    function prevStep() {
        if (currentStepIndex.value > 0) {
            resetTimer();
            currentStepIndex.value -= 1;
        }
    }

    function goToStep(idx: number) {
        resetTimer();
        currentStepIndex.value = idx;
    }

    // ── Finish flow ──────────────────────────────────────────────────────
    const finishDialogOpen = ref(false);
    const finishing = ref(false);
    const finishUpdateLevels = ref(true);
    const finishLogMeal = ref(true);
    const finishAddRanOut = ref(true);

    function openFinish() {
        pauseTimer();
        finishDialogOpen.value = true;
    }

    // The next level "down" toward Out of Stock (one higher sequence).
    function nextLowerLevelId(currentLevelId: string): string | null {
        const current = stockLevels.value.find((l) => l.stock_level_id === currentLevelId);
        if (!current) return null;
        const lower = stockLevels.value
            .filter((l) => l.sequence > current.sequence)
            .sort((a, b) => a.sequence - b.sequence)[0];
        return lower?.stock_level_id ?? null;
    }

    function isLowOrOut(levelId: string | undefined): boolean {
        const name = stockLevels.value.find((l) => l.stock_level_id === levelId)?.name;
        return name === 'Low Stock' || name === 'Out of Stock';
    }

    async function confirmFinish() {
        finishing.value = true;
        try {
            const used = [...usedIds.value];

            if (finishUpdateLevels.value) {
                for (const id of used) {
                    const item = stockItems.value.find((si) => si.stock_item_id === id);
                    if (!item) continue;
                    const next = nextLowerLevelId(item.stock_level_id);
                    if (next && next !== item.stock_level_id) {
                        await stockItemStore.updateStockLevelAsync({
                            stock_item_id: id,
                            stock_level_id: next,
                        });
                    }
                }
            }

            if (finishLogMeal.value && recipe.value) {
                await recipeStore.markMadeAsync(recipe.value.recipe_id);
            }

            if (finishAddRanOut.value) {
                // After decrementing, anything now low/out is a candidate to
                // restock. Read fresh levels from the store.
                const ranOut = used.filter((id) => {
                    const item = stockItems.value.find((si) => si.stock_item_id === id);
                    return item && isLowOrOut(item.stock_level_id);
                });
                const primary = shoppingListStore.primaryListId;
                if (ranOut.length > 0 && primary) {
                    await slActions.addItems(
                        primary,
                        ranOut.map((id) => ({ stock_item_id: id })),
                    );
                } else if (ranOut.length > 0) {
                    $q.notify({
                        type: 'info',
                        position: 'bottom-right',
                        message: 'Set a primary shopping list to auto-add ran-out items.',
                    });
                }
            }

            $q.notify({ type: 'positive', message: 'Nice cooking!', icon: 'check_circle' });
            finishDialogOpen.value = false;
            exitCookMode();
        } finally {
            finishing.value = false;
        }
    }

    function exitCookMode() {
        pauseTimer();
        if (typeof window !== 'undefined') window.speechSynthesis?.cancel();
        stopListening();
        void router.push('/recipes');
    }

    function handleKeydown(event: KeyboardEvent) {
        if (event.key === 'ArrowRight' || event.key === ' ') {
            event.preventDefault();
            nextStep();
        } else if (event.key === 'ArrowLeft') {
            event.preventDefault();
            prevStep();
        } else if (event.key === 'Escape') {
            exitCookMode();
        } else if (event.key.toLowerCase() === 'r') {
            speakCurrent();
        }
    }

    function getSpeechRecognitionCtor(): SpeechRecognitionCtor | null {
        if (typeof window === 'undefined') return null;
        const w = window as unknown as {
            SpeechRecognition?: SpeechRecognitionCtor;
            webkitSpeechRecognition?: SpeechRecognitionCtor;
        };
        return w.SpeechRecognition ?? w.webkitSpeechRecognition ?? null;
    }

    function startListening() {
        const Ctor = getSpeechRecognitionCtor();
        if (!Ctor) return;
        recognition = new Ctor();
        recognition.continuous = true;
        recognition.interimResults = false;
        recognition.lang = 'en-US';
        recognition.onresult = (event) => {
            const lastIdx = event.results.length - 1;
            const transcript = event.results[lastIdx]![0]!.transcript.trim().toLowerCase();
            if (/(^|\s)(next|forward|continue)(\s|$)/.test(transcript)) nextStep();
            else if (/(^|\s)(previous|back|go back)(\s|$)/.test(transcript)) prevStep();
            else if (/(^|\s)(repeat|again|say it again)(\s|$)/.test(transcript)) speakCurrent();
            else if (/(^|\s)(stop|exit|quit)(\s|$)/.test(transcript)) exitCookMode();
        };
        recognition.onend = () => {
            if (listening.value && recognition) {
                try {
                    recognition.start();
                } catch {
                    listening.value = false;
                }
            }
        };
        recognition.onerror = () => {
            listening.value = false;
        };
        try {
            recognition.start();
            listening.value = true;
        } catch {
            listening.value = false;
        }
    }

    function stopListening() {
        listening.value = false;
        if (recognition) {
            try {
                recognition.stop();
            } catch {
                /* ignore */
            }
            recognition = null;
        }
    }

    function toggleListening() {
        if (listening.value) stopListening();
        else startListening();
    }

    watch(currentStepIndex, () => {
        if (speechEnabled.value) speakCurrent();
    });

    onMounted(async () => {
        speechRecognitionAvailable.value = getSpeechRecognitionCtor() !== null;
        window.addEventListener('keydown', handleKeydown);

        const recipeId = route.params.id as string;
        try {
            if (recipeStore.recipes.length === 0) {
                await recipeStore.getRecipesAsync();
            }
            const fromStore = recipeStore.recipes.find((r) => r.recipe_id === recipeId);
            recipe.value = (fromStore ?? (await recipeApiService.getAsync(recipeId))) as Recipe;
        } catch {
            recipe.value = null;
        } finally {
            loading.value = false;
        }

        // Warm the locations tree so ingredient breadcrumbs render without
        // a flash. Fire-and-forget — cook mode is usable without it.
        if (locationStore.tree.length === 0) {
            void locationStore.refreshAsync();
        }

        // Stock items + levels back the ingredient chips and the finish flow;
        // membership/primary feed the "add ran-out items" step.
        await Promise.all([
            stockItems.value.length === 0 ? stockItemStore.getStockItemsAsync() : Promise.resolve(),
            stockLevels.value.length === 0 ? stockLevelStore.getStockLevelsAsync() : Promise.resolve(),
            shoppingListStore.refreshAsync(),
        ]);
    });

    onBeforeUnmount(() => {
        pauseTimer();
        stopListening();
        if (typeof window !== 'undefined') {
            window.speechSynthesis?.cancel();
            window.removeEventListener('keydown', handleKeydown);
        }
    });
</script>

<style scoped>
    .cook-mode {
        max-width: 900px;
        margin: 0 auto;
    }
    .step-card {
        min-height: 200px;
    }
    .step-text {
        line-height: 1.4;
        font-weight: 400;
    }
</style>
