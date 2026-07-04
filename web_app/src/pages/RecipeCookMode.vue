<template>
    <div class="q-pa-md cook-mode">
        <div v-if="!recipe" class="text-center q-pa-xl">
            <AppSpinner v-if="loading" size="40px" />
            <q-banner v-else class="dora-bg-sunken">Recipe not found.</q-banner>
        </div>

        <template v-else>
            <div class="row items-center q-mb-md cook-header q-gutter-sm">
                <BaseButton variant="ghost" :icon="ICONS.arrow_back" label="Exit" @click="exitCookMode" />
                <q-space />
                <div class="text-h5 ellipsis">{{ recipe.name }}</div>
                <q-space />
                <!-- C-3 Chunk 6 — headcount control. Session-only; the
                     saved recipe stays at `recipe.servings`. -->
                <div class="row items-center q-gutter-xs cooking-for">
                    <q-icon :name="ICONS.group" size="20px" class="dora-text-muted" />
                    <span class="text-caption dora-text-muted">Cooking for</span>
                    <q-input
                        v-model.number="cookingFor"
                        type="number"
                        min="1"
                        dense
                        outlined
                        hide-bottom-space
                        :style="{ width: '72px' }"
                        @blur="onCookingForBlur"
                    >
                        <q-tooltip>
                            Rescales quantities for this cook only — the saved recipe stays at {{ recipe.servings ?? '?' }} serving{{ recipe.servings === 1 ? '' : 's' }}.
                        </q-tooltip>
                    </q-input>
                </div>
                <!-- C-3 Chunk 2 — Sous Chef. Single labelled button activates
                     speech + listening; the popover lists the hands-free
                     commands so users don't have to discover them. -->
                <BaseButton
                    variant="ghost"
                    :icon="ICONS.record_voice_over"
                    :label="speechEnabled ? 'Sous Chef on' : 'Sous Chef'"
                    :class="{ 'text-primary': speechEnabled, 'dora-text-muted': !speechEnabled }"
                    @click="toggleSpeech"
                >
                    <q-tooltip>{{ speechEnabled ? 'Disable Sous Chef voice' : 'Enable Sous Chef voice — Dora reads each step aloud' }}</q-tooltip>
                </BaseButton>
                <BaseButton
                    v-if="speechRecognitionAvailable"
                    variant="icon"
                    :icon="listening ? 'mic' : 'mic_off'"
                    :class="{ 'text-negative': listening, 'dora-text-muted': !listening }"
                    @click="toggleListening"
                >
                    <q-tooltip>{{ listening ? 'Stop listening' : 'Listen for hands-free commands' }}</q-tooltip>
                </BaseButton>
                <BaseButton
                    variant="icon"
                    :icon="ICONS.help_outline"
                    aria-label="Sous Chef commands"
                >
                    <q-tooltip>What can I say?</q-tooltip>
                    <q-menu>
                        <q-card class="sous-chef-help" flat>
                            <q-card-section>
                                <div class="text-subtitle1 q-mb-sm">Sous Chef commands</div>
                                <div class="text-caption dora-text-muted q-mb-sm">
                                    With listening on, say any of these. Sous Chef stays quiet for anything else — chat with someone in the kitchen freely.
                                </div>
                                <q-list dense>
                                    <q-item v-for="cmd in sousChefCommands" :key="cmd.label">
                                        <q-item-section>
                                            <div class="row items-baseline q-gutter-xs">
                                                <span class="text-weight-medium">{{ cmd.label }}</span>
                                                <span class="text-caption dora-text-muted">— {{ cmd.does }}</span>
                                            </div>
                                        </q-item-section>
                                    </q-item>
                                </q-list>
                            </q-card-section>
                        </q-card>
                    </q-menu>
                </BaseButton>
            </div>

            <!-- PROPOSAL_RECIPE_IMAGE_STEPS — image-mode replaces the step-
                 by-step navigation with a scrollable image gallery. The
                 ingredients panel, finish flow, and substitute swaps still
                 render below (same as the other modes). -->
            <RecipeCookModeImageView
                v-if="isImageMode"
                :recipe-id="recipe.recipe_id"
                :images="recipe.step_images ?? []"
            />

            <q-linear-progress
                v-if="!isImageMode"
                :value="(currentStepIndex + 1) / steps.length"
                class="q-mb-md"
                size="10px"
                color="primary"
                rounded
            />

            <div v-if="!isImageMode" class="text-caption q-mb-sm">
                Step {{ currentStepIndex + 1 }} of {{ steps.length }}
            </div>

            <q-card v-if="!isImageMode" flat bordered class="step-card q-mb-md">
                <q-card-section>
                    <div class="row items-center q-gutter-xs q-mb-xs">
                        <!-- C-4 Chunk 10 — section header for the current step. -->
                        <q-chip
                            v-if="currentStepObject?.sectionName"
                            dense
                            outline
                            color="primary"
                            :icon="ICONS.list"
                        >
                            {{ currentStepObject.sectionName }}
                        </q-chip>
                        <q-chip
                            v-if="currentStepObject?.isSubStep"
                            dense
                            color="primary"
                            text-color="white"
                            :icon="ICONS.subdirectory_arrow_right"
                        >
                            Sub-step
                        </q-chip>
                    </div>
                    <div class="text-h4 step-text">{{ currentStep }}</div>
                    <div
                        v-if="currentStepObject?.hint"
                        class="step-hint q-mt-sm dora-text-muted text-body2"
                    >
                        <q-icon :name="ICONS.lightbulb" size="16px" class="q-mr-xs" />
                        {{ currentStepObject.hint }}
                    </div>
                </q-card-section>

                <q-card-section v-if="detectedTimerMinutes !== null" class="dora-bg-sunken">
                    <div class="row items-center q-gutter-sm">
                        <q-icon :name="ICONS.timer" size="32px" color="primary" />
                        <div class="text-h6 timer-text">
                            {{ formatTimer(timerRemaining ?? detectedTimerMinutes * 60) }}
                        </div>
                        <q-space />
                        <BaseButton
                            v-if="!timerRunning"
                            variant="primary"
                            :icon="ICONS.play_arrow"
                            label="Start"
                            @click="startTimer(detectedTimerMinutes * 60)"
                        />
                        <!-- FU-006: ambiguous — color="warning" has no matching BaseButton variant; left as raw q-btn for review. -->
                        <q-btn
                            v-else
                            color="warning"
                            :icon="ICONS.pause"
                            label="Pause"
                            @click="pauseTimer"
                        />
                        <BaseButton
                            v-if="timerRemaining !== null"
                            variant="ghost"
                            :icon="ICONS.restart_alt"
                            label="Reset"
                            @click="resetTimer"
                        />
                    </div>
                    <!-- C-3 Chunk 2 — fill-bar that empties as time passes.
                         Tone shifts to negative when finished so the bar
                         itself confirms the toast/audio. -->
                    <q-linear-progress
                        v-if="timerTotal !== null && timerTotal > 0"
                        :value="timerProgress"
                        :color="timerRemaining === 0 ? 'negative' : 'primary'"
                        rounded
                        size="10px"
                        class="q-mt-sm timer-bar"
                    />
                </q-card-section>
            </q-card>

            <div v-if="!isImageMode" class="row q-gutter-sm justify-center q-mb-lg">
                <!-- FU-006: ambiguous, mapped to ghost -->
                <BaseButton
                    variant="ghost"
                    size="lg"
                    :icon="ICONS.arrow_back"
                    label="Previous"
                    :disable="currentStepIndex === 0"
                    @click="prevStep"
                />
                <!-- FU-006: ambiguous, mapped to ghost -->
                <BaseButton
                    variant="ghost"
                    size="lg"
                    :icon="ICONS.replay"
                    label="Repeat"
                    @click="speakCurrent"
                    :disable="!speechEnabled"
                />
                <BaseButton
                    size="lg"
                    variant="primary"
                    :icon-right="currentStepIndex === steps.length - 1 ? 'check' : 'arrow_forward'"
                    :label="currentStepIndex === steps.length - 1 ? 'Finish' : 'Next'"
                    @click="nextStep"
                />
            </div>

            <!-- C-3 Chunk 3 — ingredients grouped by base stock location.
                 Stock-level chips intentionally removed mid-cook: the
                 decision to cook this recipe is already made; visual noise
                 about what's low/out only belongs on the finish surface
                 (Chunk 1). The expansion stays for collapse, but the
                 inner list is a card per location group rather than one
                 long flat list. -->
            <q-expansion-item
                default-opened
                :icon="ICONS.kitchen"
                header-class="text-subtitle1"
            >
                <template #header>
                    <q-item-section avatar><q-icon :name="ICONS.kitchen" /></q-item-section>
                    <q-item-section>Ingredients</q-item-section>
                    <q-item-section side>
                        <span class="text-caption dora-text-muted">
                            {{ ingredientRows.length }} total
                        </span>
                    </q-item-section>
                </template>
                <div class="q-pt-sm">
                    <q-card
                        v-for="group in ingredientGroups"
                        :key="group.key"
                        flat
                        bordered
                        class="q-mb-sm ingredient-group"
                    >
                        <q-card-section class="q-pb-xs">
                            <div class="row items-center q-gutter-xs">
                                <q-icon :name="ICONS.place" size="16px" class="dora-text-muted" />
                                <span class="text-subtitle2">{{ group.label }}</span>
                            </div>
                        </q-card-section>
                        <q-list dense>
                            <q-item
                                v-for="row in group.rows"
                                :key="row.ingredient.recipe_ingredient_id"
                                :class="{
                                    'ingredient-row--highlighted': highlightedIngredientIds.has(row.ingredient.recipe_ingredient_id),
                                    'ingredient-row--optional': row.ingredient.is_optional,
                                }"
                            >
                                <q-item-section>
                                    <div class="row items-center q-gutter-xs no-wrap">
                                        <span class="text-caption dora-text-muted ingredient-quantity">
                                            {{ displayQuantity(row.ingredient.quantity, row.ingredient.unit) }}
                                        </span>
                                        <!-- IMPL_PLAN_RECIPE_IMPORTER §Chunk 4:
                                             unlinked ingredients (stock_item_id === null) render
                                             as read-only raw_text — no substitute machinery, no
                                             swap chip, since there's no stock item to swap FROM.
                                             No existing recipe has unlinked ingredients on
                                             Chunk-4 ship; the paste importer (Chunk 5) is the
                                             first source. -->
                                        <template v-if="row.ingredient.stock_item_id === null">
                                            <span class="ingredient-name">{{ row.ingredient.raw_text ?? 'Unlinked ingredient' }}</span>
                                            <q-chip dense outline color="grey-6" text-color="grey-8" class="q-ml-xs">
                                                Unlinked
                                            </q-chip>
                                        </template>
                                        <template v-else-if="sessionSwaps.has(row.ingredient.stock_item_id)">
                                            <q-chip
                                                dense
                                                color="secondary"
                                                text-color="white"
                                                :icon="ICONS.swap_horiz"
                                            >
                                                {{ sessionSwaps.get(row.ingredient.stock_item_id)!.substituteName }}
                                            </q-chip>
                                            <span class="text-caption dora-text-muted">
                                                instead of {{ row.ingredient.stock_item_name }}
                                            </span>
                                            <BaseButton
                                                variant="icon"
                                                size="sm"
                                                :icon="ICONS.undo"
                                                @click="clearSwap(row.ingredient.stock_item_id!)"
                                            >
                                                <q-tooltip>Undo substitute</q-tooltip>
                                            </BaseButton>
                                        </template>
                                        <template v-else>
                                            <span class="ingredient-name">{{ row.ingredient.stock_item_name }}</span>
                                            <span
                                                v-if="row.ingredient.is_optional"
                                                class="text-caption dora-text-muted"
                                            >
                                                (optional)
                                            </span>
                                            <BaseButton
                                                variant="icon"
                                                size="sm"
                                                :icon="ICONS.swap_horiz"
                                                @click="openSwapPicker(row.ingredient.stock_item_id!, row.ingredient.stock_item_name!)"
                                            >
                                                <q-tooltip>Use a substitute for this cook</q-tooltip>
                                            </BaseButton>
                                        </template>
                                    </div>
                                    <q-item-label
                                        v-if="row.ingredient.notes"
                                        caption
                                        class="dora-text-muted"
                                    >
                                        {{ row.ingredient.notes }}
                                    </q-item-label>
                                </q-item-section>
                            </q-item>
                        </q-list>
                    </q-card>
                </div>
            </q-expansion-item>

            <!-- C-3 Chunk 5 — tools panel. Shown only when the recipe lists
                 tools (Cookbook Chunk 5 vocab). Highlights the tools the
                 current step needs; un-referenced tools dim out. -->
            <q-expansion-item
                v-if="recipeTools.length > 0"
                default-opened
                :icon="ICONS.kitchen"
                header-class="text-subtitle1"
            >
                <template #header>
                    <q-item-section avatar><q-icon :name="ICONS.kitchen" /></q-item-section>
                    <q-item-section>Tools</q-item-section>
                    <q-item-section side>
                        <span class="text-caption dora-text-muted">
                            {{ recipeTools.length }} total
                        </span>
                    </q-item-section>
                </template>
                <div class="q-pa-sm row q-gutter-xs">
                    <q-chip
                        v-for="tool in recipeTools"
                        :key="tool.tool_id"
                        :class="{
                            'tool-chip--highlighted': highlightedToolIds.has(tool.tool_id),
                            'tool-chip--dim': highlightedToolIds.size > 0 && !highlightedToolIds.has(tool.tool_id),
                        }"
                        dense
                    >
                        {{ tool.name }}
                    </q-chip>
                </div>
            </q-expansion-item>

            <q-expansion-item v-if="!isImageMode" label="All steps" :icon="ICONS.list" header-class="text-subtitle1">
                <q-list>
                    <q-item
                        v-for="(step, idx) in cookSteps"
                        :key="idx"
                        :active="idx === currentStepIndex"
                        clickable
                        @click="goToStep(idx)"
                        :class="{ 'all-steps-row--sub': step.isSubStep }"
                    >
                        <q-item-section side>{{ idx + 1 }}.</q-item-section>
                        <q-item-section>
                            <!-- C-4 Chunk 10 — show the section header at the
                                 first step of each section in the overview. -->
                            <div
                                v-if="step.sectionName && (idx === 0 || cookSteps[idx - 1]?.sectionName !== step.sectionName)"
                                class="text-caption text-primary q-mb-xs"
                            >
                                {{ step.sectionName }}
                            </div>
                            {{ step.text }}
                        </q-item-section>
                    </q-item>
                </q-list>
            </q-expansion-item>
        </template>

        <!-- B8 — cook-session substitute picker (temporary; never edits recipe) -->
        <BaseDialog v-model="swapPickerOpen" :title="`Substitute for ${swapForName}`" closable card-style="min-width: 360px; max-width: 520px">
            <q-card-section v-if="loadingSwapOptions" class="text-center q-py-lg">
                <AppSpinner size="32px" />
            </q-card-section>
            <q-card-section v-else-if="swapOptions.length === 0" class="dora-text-muted">
                No substitutes recorded for {{ swapForName }}. Add some on the
                stock item's detail page.
            </q-card-section>
            <q-card-section v-else class="q-pt-sm">
                <div class="text-caption dora-text-muted q-mb-sm">
                    Just for this cook — your saved recipe won't change.
                </div>
                <!-- FU-034 — when the substitute carries a note or ratio,
                     surface it next to the chip so the cook has the hint
                     in front of them at swap time. Mirrors the detail-page
                     layout so the same shape reads the same in both
                     places. Ratios are shown as "1 tsp → 1 tsp"; the
                     "from" side is the recipe's ingredient. -->
                <q-list separator>
                    <q-item
                        v-for="opt in swapOptions"
                        :key="opt.stock_item_id"
                        clickable
                        @click="applySwap(opt.stock_item_id, opt.name)"
                    >
                        <q-item-section>
                            <q-item-label>{{ opt.name }}</q-item-label>
                            <q-item-label
                                v-if="substituteRatioText(opt)"
                                caption
                                class="dora-text-secondary"
                            >
                                {{ substituteRatioText(opt) }}
                            </q-item-label>
                            <q-item-label v-if="opt.notes" caption class="dora-text-muted">
                                {{ opt.notes }}
                            </q-item-label>
                        </q-item-section>
                        <q-item-section side>
                            <q-icon :name="ICONS.arrow_forward" class="dora-text-muted" />
                        </q-item-section>
                    </q-item>
                </q-list>
            </q-card-section>
            <template #actions>
                <BaseButton variant="ghost" label="Close" v-close-popup />
            </template>
        </BaseDialog>

        <!-- C-3 Chunk 1 — finish-flow rewrite. Per-ingredient level control
             replaces the old blanket "update stock levels" / "auto-add ran
             out" toggles; `meals_cooked` defaults to 0 ("just ate it" is the
             common case); click-out cancels (BaseDialog v-model leaves the
             state untouched until "Done"). Celebration message lands as a
             toast after success. -->
        <BaseDialog v-model="finishDialogOpen" title="Finished cooking?" closable card-style="min-width: 360px; max-width: 720px">
            <q-card-section v-if="finishRows.length === 0" class="dora-text-muted">
                This recipe has no ingredients to adjust — tap "Done" to log the meals.
            </q-card-section>
            <q-card-section v-else class="q-pt-none">
                <div class="text-caption dora-text-muted q-mb-sm">
                    {{ finishRows.length }} ingredient{{ finishRows.length === 1 ? '' : 's' }} used. Pick a stock change for each — defaults to "Down one level".
                </div>
                <q-list bordered separator class="finish-list">
                    <q-item v-for="row in finishRows" :key="row.targetStockItemId">
                        <q-item-section>
                            <q-item-label>
                                <div class="row items-center q-gutter-xs">
                                    <span class="text-weight-medium">{{ row.targetName }}</span>
                                    <q-chip
                                        v-if="row.currentLevelName"
                                        dense
                                        :color="row.currentLevelColour ?? undefined"
                                        :text-color="row.currentLevelColour ? 'white' : undefined"
                                    >
                                        {{ row.currentLevelName }}
                                    </q-chip>
                                </div>
                            </q-item-label>
                            <q-item-label caption>
                                <BaseSegmented
                                    v-model="row.action"
                                    :options="[
                                        { label: 'Down one', value: 'down_one' },
                                        { label: 'Out', value: 'out' },
                                        { label: 'Unchanged', value: 'unchanged' },
                                    ]"
                                    flat
                                    dense
                                    spread
                                    class="q-mt-xs"
                                />
                                <div class="row items-center q-gutter-sm q-mt-xs">
                                    <q-select
                                        v-model="row.overrideLevelId"
                                        :options="levelSelectOptions"
                                        option-value="value"
                                        option-label="label"
                                        emit-value
                                        map-options
                                        dense
                                        outlined
                                        clearable
                                        label="Override to a specific level"
                                        class="col"
                                    />
                                    <BaseButton
                                        variant="ghost"
                                        :icon="ICONS.shopping_cart"
                                        label="Add to list"
                                        @click="onFinishAddToList(row.targetStockItemId)"
                                    />
                                </div>
                            </q-item-label>
                        </q-item-section>
                    </q-item>
                </q-list>
            </q-card-section>
            <q-card-section class="q-pt-md">
                <q-input
                    v-model.number="finishMealsCooked"
                    type="number"
                    min="0"
                    label="How many meals did you cook?"
                    outlined
                    dense
                    hint="Added to this recipe's pool. Leave at 0 if you just ate it."
                />
            </q-card-section>
            <template #actions>
                <BaseButton variant="ghost" label="Cancel" @click="finishDialogOpen = false" />
                <BaseButton variant="primary" label="Done" :loading="finishing" @click="confirmFinish" />
            </template>
        </BaseDialog>
    </div>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import AppSpinner from 'src/components/AppSpinner.vue';
    import BaseButton from 'src/components/BaseButton.vue';
    import BaseSegmented from 'src/components/BaseSegmented.vue';
    import BaseDialog from 'src/components/BaseDialog.vue';
    import RecipeCookModeImageView from 'src/components/recipes/RecipeCookModeImageView.vue';
    import { storeToRefs } from 'pinia';
    import { useQuasar } from 'quasar';
    import { useShoppingListActions } from 'src/composables/useShoppingListActions';
    import { formatQuantity } from 'src/helpers/formatQuantity';
    import { scaleQuantity } from 'src/helpers/scaleQuantity';
    import { colourForSequence } from 'src/helpers/stockLevelLogic';
    import {
        findLevelBySequence,
        OUT_OF_STOCK_SEQUENCE,
    } from 'src/helpers/stockStatus';
    // P2-13 — extracted browser-speech composables. Cook mode opts into
    // continuous listening so the user can keep their hands in the
    // mixing bowl while saying "next" / "start timer".
    import { useSpeechOutput } from 'src/composables/useSpeechOutput';
    import { useVoiceInput } from 'src/composables/useVoiceInput';
    import { useWakeLock } from 'src/composables/useWakeLock';
    import type { Recipe } from 'src/models/recipe';
    import type { StockItem } from 'src/models/stockItem';
    import type { Substitute } from 'src/models/stockItemDetail';
    import RecipeApiService from 'src/services/api/recipeApiService';
    import StockItemApiService from 'src/services/api/stockItemApiService';
    import { useAuthStore } from 'src/stores/authStore';
    import { useLocationStore } from 'src/stores/locationStore';
    import { useRecipeStore } from 'src/stores/recipeStore';
    import { useRecipeVocabStore } from 'src/stores/recipeVocabStore';
    import { useShoppingListStore } from 'src/stores/shoppingListStore';
    import { useStockItemStore } from 'src/stores/stockItemStore';
    import { useStockLevelStore } from 'src/stores/stockLevelStore';
    import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
    import { useRoute, useRouter } from 'vue-router';

    const route = useRoute();
    const router = useRouter();
    const $q = useQuasar();
    const recipeStore = useRecipeStore();
    const recipeVocabStore = useRecipeVocabStore();
    const locationStore = useLocationStore();
    const stockItemStore = useStockItemStore();
    const stockLevelStore = useStockLevelStore();
    const shoppingListStore = useShoppingListStore();
    const recipeApiService = new RecipeApiService();
    const stockItemApi = new StockItemApiService();
    const slActions = useShoppingListActions();
    const authStore = useAuthStore();

    // P8-10 — hold the screen awake for the whole cook session (both the
    // running timer and the read-along steps assume a visible screen the
    // user isn't tapping). Released automatically on unmount.
    const wakeLockWanted = ref(true);
    useWakeLock(wakeLockWanted);

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

    // PROPOSAL_RECIPE_IMAGE_STEPS — image mode swaps the step-by-step
    // navigation for a scrollable image gallery. Other surfaces
    // (ingredients, finish flow, B8 swaps, sous-chef speech) stay shared.
    const isImageMode = computed(
        () => recipe.value?.steps_mode === 'image',
    );

    // C-3 Chunk 6 / C-5.4 — session-only headcount. Seeds from the user's
    // `household_headcount` (set in onboarding) when present, otherwise the
    // recipe's own `servings`. Never writes back to the saved recipe —
    // matches the B8-substitute discipline of "this cook only".
    const householdHeadcount = computed(
        () => authStore.currentUser?.household_headcount ?? null,
    );
    const cookingFor = ref<number>(
        householdHeadcount.value && householdHeadcount.value > 0
            ? householdHeadcount.value
            : 1,
    );
    watch(recipe, (next) => {
        const headcount = householdHeadcount.value;
        if (headcount && headcount > 0) {
            cookingFor.value = headcount;
        } else if (next?.servings && next.servings > 0) {
            cookingFor.value = next.servings;
        }
    }, { immediate: true });

    /** Format a recipe ingredient's quantity for display, rescaled to the
     *  current headcount and routed through `formatQuantity` for unit
     *  spacing. The two helpers are deliberately separate — `scaleQuantity`
     *  owns the rounding (DEC-4), `formatQuantity` owns the spacing (DEC-3).
     *  Returns an empty string when both quantity and unit are null. */
    function displayQuantity(quantity: number | null | undefined, unit: string | null | undefined): string {
        const baseServings = recipe.value?.servings ?? null;
        const scaled = scaleQuantity(quantity, baseServings, cookingFor.value, unit);
        return formatQuantity(scaled, unit);
    }

    /** Re-clamp the headcount input on blur. `q-input.number` lets the user
     *  type "0" or clear the field (giving NaN); coerce back to a sane
     *  minimum of 1 so quantities never collapse to zero mid-cook. */
    function onCookingForBlur() {
        const value = cookingFor.value;
        if (!Number.isFinite(value) || value < 1) cookingFor.value = 1;
        else cookingFor.value = Math.floor(value);
    }

    // ── P2-13 voice (extracted into composables) ────────────────────────
    // The user's persisted preference seeds the local toggle; subsequent
    // in-page taps flip the session view and persist back via authStore
    // (declared above with the other stores).
    const speechOut = useSpeechOutput();
    const speechEnabled = ref<boolean>(
        authStore.currentUser?.voice_output_enabled ?? false,
    );

    const voiceInput = useVoiceInput({
        continuous: true,
        // Cook mode bypasses the chat draft entirely — the transcript is
        // interpreted as a command and dispatched immediately. Wrapping
        // the dispatcher in onFinal keeps the composable agnostic of
        // cook-mode-specific verbs.
        onFinal(text) {
            handleVoiceCommand(text);
        },
    });
    const listening = computed(() => voiceInput.listening.value);
    const speechRecognitionAvailable = computed(() => voiceInput.available.value);

    const timerRemaining = ref<number | null>(null);
    const timerRunning = ref(false);
    // C-3 Chunk 2 — captured at start so the fill-bar has a stable
    // denominator even after pause/reset shuffles `timerRemaining`.
    const timerTotal = ref<number | null>(null);
    let timerIntervalId: ReturnType<typeof setInterval> | null = null;

    const timerProgress = computed<number>(() => {
        if (timerTotal.value === null || timerTotal.value <= 0) return 0;
        if (timerRemaining.value === null) return 1;
        return Math.max(0, Math.min(1, timerRemaining.value / timerTotal.value));
    });

    // C-3 Chunk 2 — Sous Chef voice command list, surfaced via the help
    // popover so users discover the verbs without trial and error.
    const sousChefCommands: ReadonlyArray<{ label: string; does: string }> = [
        { label: '"Next"', does: 'advance to the next step' },
        { label: '"Previous" / "Back"', does: 'go to the previous step' },
        { label: '"Repeat"', does: 'read the current step again' },
        { label: '"Start timer"', does: 'start the step timer (uses detected duration, or 5 min)' },
        { label: '"Pause timer"', does: 'pause the running timer' },
        { label: '"Reset timer"', does: 'clear the timer' },
        { label: '"Exit"', does: 'leave cook mode' },
    ];

    // C-3 Chunk 5 — step model. Structured recipes (Chunk 4) carry a
    // flat `recipe.steps[]` with optional parent_step_id for one level of
    // sub-steps and per-step ingredient/tool references; we flatten that to
    // a linear sequence (top, its subs, next top, …) for navigation.
    // Unstructured recipes fall back to splitting `instructions` on newline.
    type CookStep = {
        text: string;
        hint: string | null;
        ingredientIds: string[]; // references RecipeIngredient.recipe_ingredient_id
        toolIds: string[];       // references Tool.tool_id
        isSubStep: boolean;
        // C-4 Chunk 10 — name of the section this step belongs to (the
        // sub-step inherits its parent's section so the header doesn't
        // flicker mid-group). Null when the step is unsectioned.
        sectionName: string | null;
    };

    const cookSteps = computed<CookStep[]>(() => {
        const structured = recipe.value?.steps ?? [];
        const sectionById = new Map(
            (recipe.value?.sections ?? []).map((s) => [s.section_id, s]),
        );
        const sectionName = (id: string | null) =>
            id ? (sectionById.get(id)?.name ?? null) : null;
        if (structured.length > 0) {
            const flat: CookStep[] = [];
            const tops = structured
                .filter((s) => s.parent_step_id === null)
                .sort((a, b) => a.sequence - b.sequence);
            for (const top of tops) {
                flat.push({
                    text: top.text,
                    hint: top.hint,
                    ingredientIds: [...top.ingredient_ids],
                    toolIds: [...top.tool_ids],
                    isSubStep: false,
                    sectionName: sectionName(top.section_id),
                });
                const subs = structured
                    .filter((s) => s.parent_step_id === top.step_id)
                    .sort((a, b) => a.sequence - b.sequence);
                for (const sub of subs) {
                    flat.push({
                        text: sub.text,
                        hint: sub.hint,
                        ingredientIds: [...sub.ingredient_ids],
                        toolIds: [...sub.tool_ids],
                        isSubStep: true,
                        sectionName: sectionName(top.section_id),
                    });
                }
            }
            return flat;
        }
        // Unstructured fallback — same shape, empty refs.
        const raw = recipe.value?.instructions;
        if (!raw) {
            return [{
                text: 'No instructions provided.',
                hint: null,
                ingredientIds: [],
                toolIds: [],
                isSubStep: false,
                sectionName: null,
            }];
        }
        const parts = raw
            .split(/\r?\n+/)
            .map((s) => s.replace(/^\s*\d+[.)]\s*/, '').trim())
            .filter((s) => s.length > 0);
        const lines = parts.length > 0 ? parts : [raw];
        return lines.map((t) => ({
            text: t,
            hint: null,
            ingredientIds: [],
            toolIds: [],
            isSubStep: false,
            sectionName: null,
        }));
    });

    // Linear step text (consumed by the speech / nav / timer code that
    // existed before structured steps landed).
    const steps = computed(() => cookSteps.value.map((s) => s.text));

    const currentStep = computed(() => steps.value[currentStepIndex.value] ?? '');
    const currentStepObject = computed<CookStep | null>(
        () => cookSteps.value[currentStepIndex.value] ?? null,
    );
    // (was a `hasStructuredSteps` computed; removed as unused — Chunk 5
    //  reads `currentStepObject.ingredientIds.length > 0` directly to
    //  decide whether to apply the text-match fallback.)

    type IngredientRow = { ingredient: Recipe['ingredients'][number]; stockItem: StockItem | null };
    const ingredientRows = computed<IngredientRow[]>(() =>
        (recipe.value?.ingredients ?? []).map((ingredient) => ({
            ingredient,
            stockItem:
                stockItems.value.find((si) => si.stock_item_id === ingredient.stock_item_id) ?? null,
        })),
    );

    // C-3 Chunk 3 — group ingredients by their *base* stock location (the
    // top-level node of the breadcrumb). Sub-areas collapse into their parent
    // — "Pantry > Spice Rack" reads as "Pantry" — keeping the mid-cook view
    // calm. Ingredients with no location land in a final "No location" group.
    //
    // C-4 Chunk 10 — when the recipe defines named sections, sections win as
    // the top-level grouping (their semantic intent — "this is the sauce" —
    // is stronger than where the ingredient lives). Falls back to location
    // grouping for flat recipes so existing recipes render unchanged.
    type IngredientGroup = { key: string; label: string; rows: IngredientRow[] };
    const ingredientGroups = computed<IngredientGroup[]>(() => {
        const sections = recipe.value?.sections ?? [];
        if (sections.length > 0) {
            // Section grouping. Order follows `sequence` (server already
            // sorted); unsectioned ingredients drop into "Main" at the end.
            const sectionById = new Map(sections.map((s) => [s.section_id, s]));
            const groups = new Map<string, IngredientGroup>();
            const orderedKeys: string[] = [];
            const ensure = (key: string, label: string) => {
                if (!groups.has(key)) {
                    groups.set(key, { key, label, rows: [] });
                    orderedKeys.push(key);
                }
                return groups.get(key)!;
            };
            for (const s of sections) {
                ensure(`s:${s.section_id}`, s.name);
            }
            for (const row of ingredientRows.value) {
                const sid = row.ingredient.section_id;
                const sec = sid ? sectionById.get(sid) : null;
                if (sec) {
                    ensure(`s:${sec.section_id}`, sec.name).rows.push(row);
                } else {
                    ensure('__main__', 'Main').rows.push(row);
                }
            }
            return orderedKeys
                .map((k) => groups.get(k)!)
                .filter((g) => g.rows.length > 0);
        }
        const groups = new Map<string, IngredientGroup>();
        const orderedKeys: string[] = [];
        for (const row of ingredientRows.value) {
            const locId = row.ingredient.stock_location_id;
            let key: string;
            let label: string;
            if (locId) {
                const breadcrumb = breadcrumbFor(locId);
                label = breadcrumb[0] ?? row.ingredient.stock_location_name ?? 'Other';
                key = label;
            } else {
                key = '__none__';
                label = 'No location';
            }
            if (!groups.has(key)) {
                groups.set(key, { key, label, rows: [] });
                orderedKeys.push(key);
            }
            groups.get(key)!.rows.push(row);
        }
        // Push the "No location" bucket to the bottom so the cook reads the
        // located groups in order first.
        const ordered = orderedKeys.map((k) => groups.get(k)!).filter(Boolean);
        ordered.sort((a, b) => {
            if (a.key === '__none__') return 1;
            if (b.key === '__none__') return -1;
            return 0;
        });
        return ordered;
    });

    // C-3 Chunk 5 — per-step highlight. Structured recipes use the step's
    // own `ingredient_ids` / `tool_ids` lists; unstructured recipes fall
    // back to matching ingredient names inside the step text (same logic
    // as the pre-Chunk-5 auto-mark behaviour, repurposed for visual
    // highlight rather than tick state).
    const highlightedIngredientIds = computed<Set<string>>(() => {
        const step = currentStepObject.value;
        if (!step) return new Set();
        if (step.ingredientIds.length > 0) {
            return new Set(step.ingredientIds);
        }
        // Unstructured fallback — text match.
        const text = step.text.toLowerCase();
        const matched = new Set<string>();
        for (const ing of recipe.value?.ingredients ?? []) {
            // Chunk 4 — unlinked ingredients have no stock_item_name.
            // Fall back to raw_text for matching so paste-imported
            // recipes still get highlighted where possible.
            const name = ing.stock_item_name ?? ing.raw_text ?? '';
            if (name && text.includes(name.toLowerCase())) {
                matched.add(ing.recipe_ingredient_id);
            }
        }
        return matched;
    });

    const highlightedToolIds = computed<Set<string>>(() => {
        const step = currentStepObject.value;
        if (!step) return new Set();
        return new Set(step.toolIds);
    });

    // C-3 Chunk 5 — tools panel. Resolves the recipe's `tool_ids` against
    // the vocab store so the panel can render `{tool_id, name}` rows; only
    // shown when the recipe references any tools at all.
    type CookTool = { tool_id: string; name: string };
    const recipeTools = computed<CookTool[]>(() => {
        const ids = recipe.value?.tool_ids ?? [];
        if (ids.length === 0) return [];
        const vocab = recipeVocabStore.tools;
        return ids
            .map((id) => {
                const match = vocab.find((t) => t.tool_id === id);
                return match ? { tool_id: id, name: match.name } : null;
            })
            .filter((t): t is CookTool => t !== null);
    });

    // ── B8 — temporary, cook-session-only substitutions ─────────────────
    // Picking a substitute here applies ONLY to this cook: it never edits the
    // saved recipe. It changes what gets decremented / added-to-list on finish.
    // Keyed by the recipe ingredient's original stock_item_id.
    const sessionSwaps = ref(new Map<string, { substituteId: string; substituteName: string }>());
    const swapPickerOpen = ref(false);
    const swapForId = ref<string | null>(null);
    const swapForName = ref('');
    const swapOptions = ref<Substitute[]>([]);
    const loadingSwapOptions = ref(false);

    /** FU-034 — compact "1 tsp → 1 tsp" caption for a substitute in the
     *  swap picker. Same shape as the stock-item detail page's substitute
     *  list so the user reads the swap the same way in both places. */
    function substituteRatioText(sub: Substitute): string | null {
        if (sub.ratio_quantity_in == null || sub.ratio_unit_in == null
            || sub.ratio_quantity_out == null || sub.ratio_unit_out == null) {
            return null;
        }
        const from = formatQuantity(sub.ratio_quantity_in, sub.ratio_unit_in);
        const to = formatQuantity(sub.ratio_quantity_out, sub.ratio_unit_out);
        return `${from} → ${to}`;
    }

    async function openSwapPicker(stockItemId: string, name: string) {
        swapForId.value = stockItemId;
        swapForName.value = name;
        swapOptions.value = [];
        swapPickerOpen.value = true;
        loadingSwapOptions.value = true;
        try {
            const detail = await stockItemApi.getDetailAsync(stockItemId);
            swapOptions.value = detail.substitutes ?? [];
        } catch {
            swapOptions.value = [];
        } finally {
            loadingSwapOptions.value = false;
        }
    }
    function applySwap(substituteId: string, substituteName: string) {
        if (!swapForId.value) return;
        sessionSwaps.value.set(swapForId.value, { substituteId, substituteName });
        sessionSwaps.value = new Map(sessionSwaps.value);
        swapPickerOpen.value = false;
    }
    function clearSwap(stockItemId: string) {
        sessionSwaps.value.delete(stockItemId);
        sessionSwaps.value = new Map(sessionSwaps.value);
    }

    // C-3 Chunk 5 — `markIngredientsUsedInStep` + `toggleStepDone` removed
    // along with `usedIds` / `doneSteps`. "Used" is no longer a per-cook
    // toggle; every ingredient on a recipe is used by definition, and the
    // finish flow now ranges over `recipe.ingredients` directly.

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
        if (timerRemaining.value === null) {
            timerRemaining.value = seconds;
            timerTotal.value = seconds;
        }
        timerRunning.value = true;
        if (timerIntervalId) clearInterval(timerIntervalId);
        timerIntervalId = setInterval(() => {
            if (timerRemaining.value === null) return;
            timerRemaining.value -= 1;
            if (timerRemaining.value <= 0) {
                timerRemaining.value = 0;
                pauseTimer();
                $q.notify({ type: 'positive', message: 'Timer finished!', icon: ICONS.timer });
                // FU-287 — on iOS / macOS WKWebView a timer callback is not
                // a user activation, so both `speak()` (HTMLAudioElement)
                // and `playTimerFinishTone()` (Web Audio) are subject to
                // the autoplay gate. `useSpeechOutput` primes the audio
                // context on first user gesture (session-scoped), which
                // covers most in-session timers; a timer that fires long
                // after the last interaction may still be silent. The
                // visible Notify above is the load-bearing "timer done"
                // signal; audio + narration are best-effort.
                if (speechEnabled.value) speak('Timer finished');
                playTimerFinishTone();
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
        timerTotal.value = null;
    }

    // C-3 Chunk 2 — generated beep via WebAudio. Stays silent if the
    // browser denies audio (PWA / iOS may require a user gesture before any
    // sound plays; we ignore the failure rather than spam the console). The
    // toast + voice prompt keep the user informed regardless.
    function playTimerFinishTone() {
        try {
            const AudioCtor: typeof AudioContext | undefined =
                typeof window !== 'undefined'
                    ? (window.AudioContext
                        ?? (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext)
                    : undefined;
            if (!AudioCtor) return;
            const ctx = new AudioCtor();
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.type = 'sine';
            osc.frequency.value = 880; // a brief A5
            gain.gain.setValueAtTime(0.0001, ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.2, ctx.currentTime + 0.02);
            gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.5);
            osc.connect(gain).connect(ctx.destination);
            osc.start();
            osc.stop(ctx.currentTime + 0.55);
            osc.onended = () => { void ctx.close(); };
        } catch {
            // Silent fallback — see comment above.
        }
    }

    function speak(text: string) {
        if (!speechEnabled.value) return;
        speechOut.speak(text);
    }

    function speakCurrent() {
        speak(currentStep.value);
    }

    async function toggleSpeech() {
        const next = !speechEnabled.value;
        speechEnabled.value = next;
        if (next) speakCurrent();
        else speechOut.cancel();
        // Persist the preference back to the user row. Silent failure
        // is fine — the session-local toggle still applies.
        try {
            await authStore.updateMeAsync({ voice_output_enabled: next });
        } catch {
            /* leave local state as-is */
        }
    }

    function nextStep() {
        resetTimer();
        // C-3 Chunk 5 — no more per-step tick state; advancing just navigates
        // (or opens the finish flow when we've run out of steps).
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
    // C-3 Chunk 1 — per-ingredient finish checklist. The blanket
    // `finishUpdateLevels` / `finishAddRanOut` toggles are gone; each used
    // ingredient gets its own action (`down_one` / `out` / `unchanged`) with
    // an optional override to any specific level. `meals_cooked` defaults to
    // 0 ("just ate it" is the common case).
    type FinishAction = 'down_one' | 'out' | 'unchanged';
    type FinishRow = {
        // After session swaps: the stock item whose level we actually
        // touch on finish (the substitute, not the original recipe item).
        targetStockItemId: string;
        targetName: string;
        currentLevelId: string | undefined;
        currentLevelName: string | null;
        currentLevelColour: string | null;
        action: FinishAction;
        overrideLevelId: string | null;
    };
    const finishDialogOpen = ref(false);
    const finishing = ref(false);
    const finishMealsCooked = ref<number>(0);
    const finishRows = ref<FinishRow[]>([]);

    const levelSelectOptions = computed(() =>
        [...stockLevels.value]
            .sort((a, b) => a.sequence - b.sequence)
            .map((l) => ({ value: l.stock_level_id, label: l.name })),
    );

    function levelNameById(levelId: string | undefined): string | null {
        if (!levelId) return null;
        return stockLevels.value.find((l) => l.stock_level_id === levelId)?.name ?? null;
    }
    function levelColourById(levelId: string | undefined): string | null {
        if (!levelId) return null;
        const seq = stockLevels.value.find((l) => l.stock_level_id === levelId)?.sequence;
        return typeof seq === 'number' ? colourForSequence(seq) : null;
    }

    function buildFinishRows(): FinishRow[] {
        // C-3 Chunk 5 — finish ranges over every ingredient on the recipe,
        // applying any session swaps. The user no longer ticks ingredients
        // mid-cook; cooking the recipe implies using all of them.
        //
        // IMPL_PLAN_RECIPE_IMPORTER §Chunk 4 — unlinked ingredients
        // (stock_item_id === null) can't participate in the finish flow
        // (no stock item to decrement). They're skipped here; the cook
        // still succeeds for the linked ingredients. On Chunk-4 ship no
        // existing recipe has unlinked ingredients so this branch is
        // exercised only by paste-imported recipes from Chunk 5 onward.
        const rows: FinishRow[] = [];
        for (const ing of recipe.value?.ingredients ?? []) {
            if (ing.stock_item_id === null) continue;
            const swap = sessionSwaps.value.get(ing.stock_item_id);
            const targetId = swap?.substituteId ?? ing.stock_item_id;
            const item = stockItems.value.find((si) => si.stock_item_id === targetId);
            const fallbackName = swap?.substituteName ?? ing.stock_item_name ?? ing.raw_text ?? '';
            rows.push({
                targetStockItemId: targetId,
                targetName: item?.name ?? fallbackName,
                currentLevelId: item?.stock_level_id,
                currentLevelName: levelNameById(item?.stock_level_id),
                currentLevelColour: levelColourById(item?.stock_level_id),
                action: 'down_one',
                overrideLevelId: null,
            });
        }
        return rows;
    }

    function openFinish() {
        pauseTimer();
        finishRows.value = buildFinishRows();
        finishDialogOpen.value = true;
    }

    function nextLowerLevelId(currentLevelId: string | undefined): string | null {
        if (!currentLevelId) return null;
        const current = stockLevels.value.find((l) => l.stock_level_id === currentLevelId);
        if (!current) return null;
        const lower = stockLevels.value
            .filter((l) => l.sequence > current.sequence)
            .sort((a, b) => a.sequence - b.sequence)[0];
        return lower?.stock_level_id ?? null;
    }

    function outOfStockLevelId(): string | null {
        const out = findLevelBySequence(stockLevels.value, OUT_OF_STOCK_SEQUENCE);
        return out?.stock_level_id ?? null;
    }

    /** Resolve a row's stated intent into the level id to write (or null
     *  to leave the stock alone). Override wins over the action chips. */
    function resolveTargetLevel(row: FinishRow): string | null {
        if (row.overrideLevelId) return row.overrideLevelId;
        switch (row.action) {
            case 'down_one': return nextLowerLevelId(row.currentLevelId);
            case 'out': return outOfStockLevelId();
            case 'unchanged': return null;
        }
    }

    async function onFinishAddToList(stockItemId: string) {
        const targetId = shoppingListStore.quickAddTargetListId;
        if (!targetId) {
            $q.notify({
                type: 'info',
                position: 'bottom-right',
                message: 'No active shopping list — set a primary list first.',
            });
            return;
        }
        try {
            await slActions.addItems(targetId, [{ stock_item_id: stockItemId }]);
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: 'Added to your shopping list.',
            });
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not add to shopping list.',
            });
            console.warn('add-to-list failed during finish', err);
        }
    }

    async function confirmFinish() {
        finishing.value = true;
        try {
            // Fan out per-row level updates with fail-soft semantics: one
            // failed item doesn't take down the rest of the batch.
            // P8-07 / FU-449 — tag each finish-driven level change as a
            // `cook` consumption so the server persists a ConsumptionEvent
            // (the depletion leg of the loop). The server only records one
            // when the level actually drops, so an "unchanged"/manual-up row
            // that slips through carries no false consumption signal.
            const recipeId = recipe.value?.recipe_id;
            const updates = finishRows.value
                .map((row) => {
                    const target = resolveTargetLevel(row);
                    if (!target || target === row.currentLevelId) return null;
                    return {
                        stock_item_id: row.targetStockItemId,
                        stock_level_id: target,
                        consumption_source: 'cook' as const,
                        ...(recipeId ? { consumption_recipe_id: recipeId } : {}),
                    };
                })
                .filter((u): u is NonNullable<typeof u> => u !== null);
            await Promise.allSettled(
                updates.map((u) => stockItemStore.updateStockLevelAsync(u)),
            );

            let mealsCooked = 0;
            if (recipe.value) {
                mealsCooked = Math.max(0, Math.floor(finishMealsCooked.value || 0));
                await recipeStore.cookAsync(recipe.value.recipe_id, mealsCooked);
            }

            // Celebration. Copy reads off `meals_cooked` per L337 / DEC-5.
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                timeout: 4000,
                message:
                    mealsCooked === 0
                        ? 'All eaten — hope it was good.'
                        : `You saved ${mealsCooked} meal${mealsCooked === 1 ? '' : 's'} — enjoy.`,
                icon: ICONS.check_circle,
            });
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
        // L298 — exit returns to the recipe's detail page (where the user
        // came from), not all the way back to the cookbook overview.
        const id = route.params.id as string;
        void router.push(id ? `/cookbook/${id}` : '/cookbook');
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

    // ── P2-13 voice command dispatcher ──────────────────────────────────
    // Called by `useVoiceInput.onFinal` whenever the browser hands us a
    // finalised utterance. Each branch maps to a hands-free action that
    // mirrors a visible button in the UI — we deliberately don't expose
    // voice-only side effects, so the user can always verify what we
    // think they said by spotting the corresponding click.
    function handleVoiceCommand(rawTranscript: string) {
        const transcript = rawTranscript.toLowerCase();
        if (/(^|\s)(next|forward|continue)(\s|$)/.test(transcript)) {
            nextStep();
        } else if (/(^|\s)(previous|back|go back)(\s|$)/.test(transcript)) {
            prevStep();
        } else if (/(^|\s)(repeat|again|say it again)(\s|$)/.test(transcript)) {
            speakCurrent();
        } else if (/(^|\s)(start timer|begin timer|set timer)(\s|$)/.test(transcript)) {
            // "start timer" → use whatever duration the current step
            // implies; fall back to 5 minutes when nothing's detectable.
            const minutes = detectedTimerMinutes.value ?? 5;
            startTimer(minutes * 60);
            if (speechEnabled.value) speak(`Timer set for ${minutes} minutes.`);
        } else if (/(^|\s)(pause timer|stop timer)(\s|$)/.test(transcript)) {
            pauseTimer();
            if (speechEnabled.value) speak('Timer paused.');
        } else if (/(^|\s)(reset timer|clear timer)(\s|$)/.test(transcript)) {
            resetTimer();
            if (speechEnabled.value) speak('Timer reset.');
        } else if (/(^|\s)(stop|exit|quit)(\s|$)/.test(transcript)) {
            exitCookMode();
        }
        // Unrecognised commands are deliberately ignored — silence is
        // less annoying than a "I didn't understand that" interjection
        // every time the user talks to someone else in the kitchen.
    }

    function stopListening() { voiceInput.stop(); }
    function toggleListening() { voiceInput.toggle(); }

    watch(currentStepIndex, () => {
        if (speechEnabled.value) speakCurrent();
    });

    onMounted(async () => {
        // speechRecognitionAvailable is a computed off the composable
        // now, so no manual seeding required.
        window.addEventListener('keydown', handleKeydown);

        const recipeId = route.params.id as string;
        try {
            await recipeStore.ensureLoadedAsync();
            // C-3 Chunk 5 — the list endpoint doesn't return `steps[]`
            // (only `has_structured_steps`), and cook mode needs structured
            // steps for per-step highlights / hints. Always fetch detail so
            // `recipe.value.steps` is present when the recipe has them.
            recipe.value = await recipeApiService.getAsync(recipeId);
        } catch {
            recipe.value = null;
        } finally {
            loading.value = false;
        }

        // Warm the locations tree so ingredient breadcrumbs render without
        // a flash. Fire-and-forget — cook mode is usable without it.
        void locationStore.ensureLoadedAsync();

        // Stock items + levels back the ingredient chips and the finish flow;
        // membership/primary feed the "add ran-out items" step; tools vocab
        // (Chunk 5) feeds the per-step tools panel.
        await Promise.all([
            stockItemStore.ensureLoadedAsync(),
            stockLevelStore.ensureLoadedAsync(),
            shoppingListStore.ensureLoadedAsync(),
            recipeVocabStore.ensureLoadedAsync(),
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

<style scoped lang="scss">
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
    // C-3 Chunk 3 — calm location-grouped ingredient cards. No mid-cook
    // stock-level colour noise; just legible names + quantities.
    .ingredient-group {
        background: var(--surface-card);
    }
    .ingredient-quantity {
        min-width: 64px;
    }
    .ingredient-name {
        font-weight: 500;
    }
    // C-3 Chunk 2 — fill-bar visually echoes the MM:SS countdown.
    .timer-bar {
        transition: opacity var(--motion-normal, 200ms) ease;
    }
    .timer-text {
        font-variant-numeric: tabular-nums;
    }
    .sous-chef-help {
        min-width: 300px;
        max-width: 360px;
    }
    .finish-list {
        max-height: 50vh;
        overflow-y: auto;
        border-radius: var(--radius-md);
    }
    // C-3 Chunk 5 — per-step highlight. A soft tint + accented border on
    // ingredient rows / tool chips that the current step references; the
    // unhighlighted neighbours dim slightly when at least one highlight is
    // active, so the eye lands where it should.
    .ingredient-row--highlighted {
        background: var(--semantic-info-soft, color-mix(in srgb, var(--brand-primary) 12%, transparent));
        border-left: 3px solid var(--brand-primary);
    }
    // Cookbook revision §1.9 — optional ingredients render dimmed so the
    // eye lands on what's required to cook.
    .ingredient-row--optional {
        opacity: 0.65;
    }
    .tool-chip--highlighted {
        background: var(--brand-primary) !important;
        color: var(--text-on-primary, white) !important;
        font-weight: 500;
    }
    .tool-chip--dim {
        opacity: 0.55;
    }
    .all-steps-row--sub {
        padding-left: 32px;
    }
    .step-hint {
        line-height: 1.4;
    }
    // C-3 Chunk 6 — headcount input.
    .cook-header {
        flex-wrap: wrap;
    }
    .cooking-for {
        white-space: nowrap;
    }
</style>
