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

            <q-expansion-item label="Ingredients" icon="kitchen" header-class="text-subtitle1">
                <q-list dense>
                    <q-item v-for="ingredient in recipe.ingredients" :key="ingredient.recipe_ingredient_id">
                        <q-item-section>
                            <q-item-label>
                                <span v-if="ingredient.quantity">{{ ingredient.quantity }}</span>
                                <span v-if="ingredient.unit"> {{ ingredient.unit }}</span>
                                {{ ingredient.stock_item_name }}
                                <span v-if="ingredient.notes" class="text-grey">
                                    — {{ ingredient.notes }}
                                </span>
                            </q-item-label>
                            <q-item-label
                                v-if="ingredient.stock_location_id"
                                caption
                            >
                                <q-icon name="place" size="14px" />
                                {{ breadcrumbFor(ingredient.stock_location_id).join(' › ') }}
                            </q-item-label>
                            <q-item-label
                                v-else
                                caption
                                class="text-grey"
                            >
                                <q-icon name="help_outline" size="14px" />
                                Unassigned — drop into a location when you find it.
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
                        clickable
                        :active="idx === currentStepIndex"
                        @click="goToStep(idx)"
                    >
                        <q-item-section side>{{ idx + 1 }}.</q-item-section>
                        <q-item-section>{{ step }}</q-item-section>
                    </q-item>
                </q-list>
            </q-expansion-item>
        </template>
    </div>
</template>

<script lang="ts" setup>
    import { useQuasar } from 'quasar';
    import type { Recipe } from 'src/models/recipe';
    import RecipeApiService from 'src/services/api/recipeApiService';
    import { useLocationStore } from 'src/stores/locationStore';
    import { useRecipeStore } from 'src/stores/recipeStore';
    import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
    import { useRoute, useRouter } from 'vue-router';

    const route = useRoute();
    const router = useRouter();
    const $q = useQuasar();
    const recipeStore = useRecipeStore();
    const locationStore = useLocationStore();
    const recipeApiService = new RecipeApiService();

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
        if (currentStepIndex.value < steps.value.length - 1) {
            currentStepIndex.value += 1;
        } else {
            $q.notify({ type: 'positive', message: 'Recipe complete!', icon: 'check_circle' });
            exitCookMode();
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
            recipe.value = fromStore ?? (await recipeApiService.getAsync(recipeId));
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
