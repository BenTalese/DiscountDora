<template>
    <q-page padding>
        <!-- Loading shell -->
        <FadeTransition mode="out-in">
        <div v-if="loading && !recipe" key="rd-loading">
            <!-- Skeleton mirrors the header + the two-column editor layout. -->
            <div class="row items-center q-mb-md q-gutter-sm">
                <AppSkeleton type="circle" width="36px" height="36px" />
                <AppSkeleton type="line" width="240px" height="1.6rem" />
                <q-space />
                <AppSkeleton type="rect" width="110px" height="36px" />
            </div>
            <div class="row q-col-gutter-lg">
                <div class="col-12 col-md-8">
                    <AppSkeleton type="rect" width="100%" height="200px" class="q-mb-md" />
                    <AppSkeleton type="rect" width="100%" height="260px" />
                </div>
                <div class="col-12 col-md-4">
                    <AppSkeleton type="rect" width="100%" height="120px" class="q-mb-md" />
                    <AppSkeleton type="rect" width="100%" height="180px" />
                </div>
            </div>
        </div>

        <q-banner v-else-if="loadError" key="rd-error" class="dora-bg-negative-soft text-negative" dense rounded>
            {{ loadError }}
        </q-banner>

        <div v-else-if="recipe" key="rd-content">
            <!-- ── Header ─────────────────────────────────────────── -->
            <div class="row items-center q-mb-md">
                <BaseButton variant="icon" :icon="ICONS.arrow_back" @click="onBack" />
                <div class="q-ml-sm col">
                    <div class="text-caption dora-text-muted">
                        <router-link to="/recipes" class="dora-text-muted">
                            Recipes
                        </router-link>
                        <q-icon :name="ICONS.chevron_right" size="14px" />
                        {{ form.name || 'Untitled recipe' }}
                    </div>
                    <q-input
                        v-model="form.name"
                        dense
                        borderless
                        class="text-h5 recipe-name-input"
                        placeholder="Recipe name"
                        @blur="markDirty"
                    />
                </div>
                <BaseButton
                    variant="ghost"
                    :icon="recipe.is_favourite ? 'favorite' : 'favorite_border'"
                    :label="recipe.is_favourite ? 'Favourited' : 'Favourite'"
                    :class="{ 'text-negative': recipe.is_favourite }"
                    @click="onToggleFavourite"
                />
                <BaseButton variant="icon" :icon="ICONS.more_vert" class="q-ml-sm">
                    <q-menu anchor="bottom right" self="top right" transition-show="jump-down" transition-hide="jump-up">
                        <q-list dense style="min-width: 220px">
                            <q-item clickable v-close-popup @click="onExportCsv">
                                <q-item-section avatar>
                                    <q-icon :name="ICONS.file_download" />
                                </q-item-section>
                                <q-item-section>
                                    <q-item-label>Export as CSV</q-item-label>
                                    <q-item-label caption>
                                        Ingredient list as a spreadsheet
                                    </q-item-label>
                                </q-item-section>
                            </q-item>
                            <q-item clickable v-close-popup @click="onPrint">
                                <q-item-section avatar>
                                    <q-icon :name="ICONS.print" />
                                </q-item-section>
                                <q-item-section>
                                    <q-item-label>Print / Save as PDF</q-item-label>
                                    <q-item-label caption>
                                        Opens a printable recipe card in a new tab
                                    </q-item-label>
                                </q-item-section>
                            </q-item>
                        </q-list>
                    </q-menu>
                </BaseButton>
                <BaseButton
                    variant="primary"
                    :icon="ICONS.save"
                    label="Save"
                    class="q-ml-sm"
                    :disable="!isDirty"
                    :loading="saving"
                    @click="onSave"
                />
            </div>

            <div class="row q-col-gutter-lg">
                <!-- ── Main editor column ─────────────────────────── -->
                <div class="col-12 col-md-8">
                    <q-card flat bordered class="q-mb-md">
                        <q-card-section>
                            <div class="row q-col-gutter-sm">
                                <q-input
                                    v-model="form.cuisine"
                                    outlined
                                    dense
                                    label="Cuisine"
                                    class="col-12 col-sm-6"
                                    @update:model-value="markDirty"
                                />
                                <q-input
                                    v-model="form.category"
                                    outlined
                                    dense
                                    label="Category"
                                    class="col-12 col-sm-6"
                                    @update:model-value="markDirty"
                                />
                                <q-select
                                    v-model="form.time_of_day"
                                    outlined
                                    dense
                                    label="Time of day"
                                    :options="['Breakfast', 'Lunch', 'Dinner', 'Dessert', 'Snack', 'Any']"
                                    clearable
                                    class="col-6 col-sm-3"
                                    @update:model-value="markDirty"
                                />
                                <q-select
                                    v-model="form.difficulty"
                                    outlined
                                    dense
                                    label="Difficulty"
                                    :options="['Easy', 'Medium', 'Hard']"
                                    clearable
                                    class="col-6 col-sm-3"
                                    @update:model-value="markDirty"
                                />
                                <q-input
                                    v-model.number="form.servings"
                                    outlined
                                    dense
                                    type="number"
                                    label="Servings"
                                    min="1"
                                    class="col-6 col-sm-2"
                                    @update:model-value="markDirty"
                                />
                                <q-input
                                    v-model.number="form.prep_time_minutes"
                                    outlined
                                    dense
                                    type="number"
                                    label="Prep (min)"
                                    min="0"
                                    class="col-6 col-sm-2"
                                    @update:model-value="markDirty"
                                />
                                <q-input
                                    v-model.number="form.cook_time_minutes"
                                    outlined
                                    dense
                                    type="number"
                                    label="Cook (min)"
                                    min="0"
                                    class="col-6 col-sm-2"
                                    @update:model-value="markDirty"
                                />
                                <q-select
                                    v-model="form.recipe_collection_id"
                                    outlined
                                    dense
                                    label="Collection"
                                    :options="collectionOptions"
                                    emit-value
                                    map-options
                                    clearable
                                    class="col-12 col-sm-6"
                                    @update:model-value="markDirty"
                                />
                            </div>
                        </q-card-section>
                    </q-card>

                    <!-- ── Meals on hand ──────────────────────────── -->
                    <q-card v-if="recipe" flat bordered class="q-mb-md">
                        <q-card-section class="row items-center q-gutter-md no-wrap">
                            <div>
                                <div class="text-subtitle1">Meals on hand</div>
                                <div class="text-caption dora-text-muted">
                                    {{ recipe.unallocated_meals }} unallocated
                                    of {{ recipe.available_meals }} cooked
                                </div>
                            </div>
                            <q-space />
                            <q-btn
                                dense
                                round
                                outline
                                :icon="ICONS.remove"
                                :disable="recipe.available_meals <= 0 || adjusting"
                                aria-label="Remove one meal"
                                @click="onAdjustMeals(-1)"
                            />
                            <div class="text-h5 q-px-sm" style="min-width: 2.5rem; text-align: center;">
                                {{ recipe.available_meals }}
                            </div>
                            <q-btn
                                dense
                                round
                                outline
                                :icon="ICONS.add"
                                :disable="adjusting"
                                aria-label="Add one meal"
                                @click="onAdjustMeals(1)"
                            />
                            <q-btn
                                no-caps
                                outline
                                color="primary"
                                :icon="ICONS.restaurant"
                                label="Log cook…"
                                @click="logCookOpen = true"
                            />
                        </q-card-section>
                    </q-card>

                    <!-- ── Ingredients ────────────────────────────── -->
                    <q-card flat bordered class="q-mb-md">
                        <q-card-section class="row items-center q-pb-sm">
                            <div class="text-subtitle1">
                                Ingredients
                                <span class="text-caption dora-text-muted q-ml-sm">
                                    {{ form.ingredients.length }}
                                </span>
                            </div>
                            <q-space />
                            <q-btn
                                flat
                                dense
                                no-caps
                                :icon="ICONS.add"
                                label="Add ingredient"
                                @click="addIngredient"
                            />
                        </q-card-section>
                        <q-separator />
                        <q-list separator>
                            <q-item
                                v-for="(ing, idx) in form.ingredients"
                                :key="idx"
                                class="ingredient-row"
                            >
                                <q-item-section style="min-width: 240px">
                                    <!-- Stock-item autocomplete with inline create. The
                                         picker shows existing tracked items, and offers
                                         "Create '<typed>'" when there's no exact match. -->
                                    <q-select
                                        v-model="ing.stock_item_id"
                                        dense
                                        outlined
                                        use-input
                                        input-debounce="150"
                                        :options="rowOptionsFor(ing)"
                                        option-value="value"
                                        option-label="label"
                                        emit-value
                                        map-options
                                        label="Stock item"
                                        @filter="onIngredientFilter"
                                        @update:model-value="onIngredientChosen($event, idx)"
                                    >
                                        <template #no-option>
                                            <q-item>
                                                <q-item-section class="dora-text-muted">
                                                    Type to search — or press
                                                    <em>Create new</em>.
                                                </q-item-section>
                                            </q-item>
                                        </template>
                                        <template
                                            v-if="ingredientFilter.trim().length > 0"
                                            #after-options
                                        >
                                            <q-item
                                                clickable
                                                @click="createInlineStockItem(idx, ingredientFilter)"
                                            >
                                                <q-item-section avatar>
                                                    <q-icon :name="ICONS.add" color="primary" />
                                                </q-item-section>
                                                <q-item-section class="text-primary">
                                                    Create "{{ ingredientFilter }}"
                                                </q-item-section>
                                            </q-item>
                                        </template>
                                    </q-select>
                                </q-item-section>

                                <!-- Live level badge + low/out chip -->
                                <q-item-section side top style="min-width: 130px">
                                    <div v-if="ing.stock_item_id" class="column items-end">
                                        <q-chip
                                            dense
                                            :color="levelColourFor(ing.stock_item_id) ?? 'grey-4'"
                                            text-color="white"
                                        >
                                            {{ levelNameFor(ing.stock_item_id) ?? 'Untracked' }}
                                        </q-chip>
                                        <q-chip
                                            v-if="isMissing(ing.stock_item_id)"
                                            dense
                                            outline
                                            color="negative"
                                            :icon="ICONS.report"
                                            class="q-mt-xs"
                                        >
                                            Missing
                                        </q-chip>
                                    </div>
                                </q-item-section>

                                <q-item-section style="max-width: 90px">
                                    <q-input
                                        v-model.number="ing.quantity"
                                        dense
                                        outlined
                                        type="number"
                                        label="Qty"
                                        @update:model-value="markDirty"
                                    />
                                </q-item-section>
                                <q-item-section style="max-width: 90px">
                                    <q-input
                                        v-model="ing.unit"
                                        dense
                                        outlined
                                        label="Unit"
                                        @update:model-value="markDirty"
                                    />
                                </q-item-section>
                                <q-item-section style="max-width: 200px">
                                    <q-input
                                        v-model="ing.notes"
                                        dense
                                        outlined
                                        label="Notes"
                                        @update:model-value="markDirty"
                                    />
                                </q-item-section>

                                <q-item-section side top>
                                    <div class="row q-gutter-xs">
                                        <q-btn
                                            flat
                                            round
                                            dense
                                            :icon="ICONS.add_shopping_cart"
                                            color="primary"
                                            :disable="!ing.stock_item_id"
                                            @click="onAddRowToList(ing)"
                                        >
                                            <q-tooltip>Add to primary shopping list</q-tooltip>
                                        </q-btn>
                                        <q-btn
                                            flat
                                            round
                                            dense
                                            :icon="ICONS.delete"
                                            color="negative"
                                            @click="removeIngredient(idx)"
                                        />
                                    </div>
                                </q-item-section>
                            </q-item>
                            <q-item v-if="form.ingredients.length === 0">
                                <q-item-section class="dora-text-muted text-center">
                                    No ingredients yet. Add one or
                                    <a
                                        href="#"
                                        class="text-primary"
                                        @click.prevent="onImportFromUrl"
                                    >
                                        import from a URL
                                    </a>.
                                </q-item-section>
                            </q-item>
                        </q-list>
                    </q-card>

                    <!-- ── Instructions ───────────────────────────── -->
                    <q-card flat bordered class="q-mb-md">
                        <q-card-section>
                            <div class="text-subtitle1 q-mb-sm">Instructions</div>
                            <q-input
                                v-model="form.instructions"
                                outlined
                                type="textarea"
                                autogrow
                                placeholder="One step per line."
                                @update:model-value="markDirty"
                            />
                        </q-card-section>
                    </q-card>

                    <!-- ── Nutrition (optional) ───────────────────── -->
                    <q-card flat bordered>
                        <q-expansion-item
                            label="Nutrition (optional)"
                            :icon="ICONS.monitor_heart"
                            :default-opened="!!form.nutrition"
                        >
                            <q-card-section>
                                <q-input
                                    v-model="form.nutrition"
                                    outlined
                                    type="textarea"
                                    autogrow
                                    placeholder="Free-form — e.g. 320 kcal, 12g fat, 28g carbs"
                                    @update:model-value="markDirty"
                                />
                            </q-card-section>
                        </q-expansion-item>
                    </q-card>
                </div>

                <!-- ── Sidebar ────────────────────────────────────── -->
                <div class="col-12 col-md-4">
                    <q-card
                        flat
                        bordered
                        class="q-mb-md"
                        :class="cookableNow ? 'bg-positive dora-text-on-primary' : 'dora-bg-warning-soft'"
                    >
                        <q-card-section>
                            <div class="row items-center q-gutter-sm">
                                <q-icon
                                    :name="cookableNow ? 'check_circle' : 'shopping_cart'"
                                    size="28px"
                                />
                                <div>
                                    <div class="text-subtitle1">
                                        {{ cookableNow
                                            ? 'Cookable now'
                                            : `Missing ${missingIngredients.length} ingredient${
                                                missingIngredients.length === 1 ? '' : 's'
                                            }`
                                        }}
                                    </div>
                                    <div class="text-caption">
                                        {{ inStockCount }} of {{ trackedCount }} in stock
                                    </div>
                                </div>
                            </div>
                        </q-card-section>
                    </q-card>

                    <q-card flat bordered class="q-mb-md">
                        <q-list separator>
                            <q-item
                                clickable
                                @click="onStartCookMode"
                            >
                                <q-item-section avatar>
                                    <q-icon :name="ICONS.restaurant" color="primary" />
                                </q-item-section>
                                <q-item-section>
                                    <q-item-label>Start cook mode</q-item-label>
                                    <q-item-label caption>
                                        Step-by-step view with a tick-as-you-go ingredient list.
                                    </q-item-label>
                                </q-item-section>
                            </q-item>
                            <q-item
                                clickable
                                :disable="missingIngredients.length === 0"
                                @click="onAddMissingToList"
                            >
                                <q-item-section avatar>
                                    <q-icon :name="ICONS.add_shopping_cart" color="primary" />
                                </q-item-section>
                                <q-item-section>
                                    <q-item-label>
                                        Add all missing to a shopping list
                                    </q-item-label>
                                    <q-item-label caption>
                                        {{ missingIngredients.length === 0
                                            ? 'Nothing missing.'
                                            : `${missingIngredients.length} item${missingIngredients.length === 1 ? '' : 's'} to add.`
                                        }}
                                    </q-item-label>
                                </q-item-section>
                            </q-item>
                            <q-item
                                clickable
                                :disable="missingIngredients.length === 0"
                                @click="onFindSubstitutes"
                            >
                                <q-item-section avatar>
                                    <q-icon :name="ICONS.swap_horiz" color="primary" />
                                </q-item-section>
                                <q-item-section>
                                    <q-item-label>
                                        Find substitutes for missing
                                    </q-item-label>
                                    <q-item-label caption>
                                        Shows substitutes recorded on each item's detail page.
                                    </q-item-label>
                                </q-item-section>
                            </q-item>
                        </q-list>
                    </q-card>

                    <q-card flat bordered class="q-mb-md">
                        <q-list dense separator>
                            <q-item clickable @click="onImportFromUrl">
                                <q-item-section avatar>
                                    <q-icon :name="ICONS.link" />
                                </q-item-section>
                                <q-item-section>
                                    <q-item-label>Import from URL…</q-item-label>
                                    <q-item-label caption>
                                        Pulls structured recipe data from the page.
                                    </q-item-label>
                                </q-item-section>
                            </q-item>
                            <q-item clickable @click="onDelete">
                                <q-item-section avatar>
                                    <q-icon :name="ICONS.delete" color="negative" />
                                </q-item-section>
                                <q-item-section class="text-negative">
                                    Delete recipe
                                </q-item-section>
                            </q-item>
                        </q-list>
                    </q-card>
                </div>
            </div>
        </div>
        </FadeTransition>

        <!-- ── Substitutes dialog ───────────────────────────────── -->
        <BaseDialog v-model="substitutesOpen" card-style="min-width: 460px; max-width: 640px">
                <q-card-section>
                    <div class="text-h6">Substitutes for missing ingredients</div>
                    <div class="text-caption dora-text-muted">
                        These are recorded on each item's detail page. To cook
                        with one, start cook mode and tap the swap icon on the
                        ingredient — it applies to that cook only and never
                        changes the saved recipe.
                    </div>
                </q-card-section>
                <q-separator />
                <q-card-section
                    v-if="loadingSubstitutes"
                    class="text-center q-py-xl"
                >
                    <AppSpinner />
                </q-card-section>
                <q-card-section v-else class="q-pt-sm">
                    <div
                        v-for="entry in substituteOptions"
                        :key="entry.stockItemId"
                        class="q-mb-md"
                    >
                        <div class="text-subtitle2">
                            <q-icon :name="ICONS.report" color="negative" size="16px" />
                            {{ entry.name }}
                        </div>
                        <div v-if="entry.substitutes.length === 0" class="text-caption dora-text-muted">
                            No substitutes recorded — set some on the stock item's detail page.
                        </div>
                        <div v-else class="row q-gutter-xs q-mt-xs">
                            <q-chip
                                v-for="sub in entry.substitutes"
                                :key="sub.stock_item_id"
                                color="primary"
                                text-color="white"
                            >
                                {{ sub.name }}
                            </q-chip>
                        </div>
                    </div>
                </q-card-section>
                <q-card-actions align="right">
                    <BaseButton variant="ghost" label="Close" v-close-popup />
                </q-card-actions>
        </BaseDialog>

        <!-- ── Import-from-URL dialog ───────────────────────────── -->
        <BaseDialog v-model="importOpen" card-style="min-width: 460px; max-width: 600px">
                <q-card-section>
                    <div class="text-h6">Import from URL</div>
                    <div class="text-caption dora-text-muted">
                        Works on sites that publish schema.org/Recipe JSON-LD
                        (most major recipe sites do). Your existing recipe
                        will be overwritten with the imported fields.
                    </div>
                </q-card-section>
                <q-card-section class="q-pt-none">
                    <q-input
                        v-model="importUrl"
                        outlined
                        dense
                        label="Recipe URL"
                        placeholder="https://example.com/recipes/lasagne"
                        :error="!!importError"
                        :error-message="importError ?? ''"
                        @keydown.enter.prevent="onConfirmImport"
                    />
                </q-card-section>
                <q-card-actions align="right">
                    <BaseButton variant="ghost" label="Cancel" v-close-popup />
                    <BaseButton
                        variant="primary"
                        label="Import"
                        :loading="importing"
                        :disable="importUrl.trim().length === 0"
                        @click="onConfirmImport"
                    />
                </q-card-actions>
        </BaseDialog>

        <!-- ── Target-list picker (for add-all-missing) ─────────── -->
        <BaseDialog v-model="targetListOpen" card-style="min-width: 360px">
                <q-card-section>
                    <div class="text-h6">Add to which list?</div>
                </q-card-section>
                <q-card-section class="q-pt-none">
                    <q-select
                        v-model="targetListId"
                        outlined
                        dense
                        emit-value
                        map-options
                        :options="activeListOptions"
                        label="Active list"
                    />
                </q-card-section>
                <q-card-actions align="right">
                    <BaseButton variant="ghost" label="Cancel" v-close-popup />
                    <BaseButton
                        variant="primary"
                        label="Add"
                        :loading="addingMissing"
                        :disable="!targetListId"
                        @click="confirmAddMissing"
                    />
                </q-card-actions>
        </BaseDialog>

        <!-- Log cook ──────────────────────────────────────────────── -->
        <BaseDialog v-model="logCookOpen" card-style="min-width: 320px">
                <q-card-section class="text-h6">Log a cook</q-card-section>
                <q-card-section class="q-pt-none">
                    <q-input
                        v-model.number="logCookCount"
                        type="number"
                        min="1"
                        max="999"
                        outlined
                        dense
                        autofocus
                        label="Meals cooked"
                        hint="Adds to this recipe's pool."
                    />
                </q-card-section>
                <q-card-actions align="right">
                    <BaseButton variant="ghost" label="Cancel" v-close-popup />
                    <BaseButton
                        variant="primary"
                        label="Log"
                        :loading="logging"
                        :disable="!(logCookCount > 0)"
                        @click="onLogCook"
                    />
                </q-card-actions>
        </BaseDialog>
    </q-page>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import AppSkeleton from 'src/components/AppSkeleton.vue';
    import AppSpinner from 'src/components/AppSpinner.vue';
    import BaseButton from 'src/components/BaseButton.vue';
    import BaseDialog from 'src/components/BaseDialog.vue';
    import FadeTransition from 'src/components/transitions/FadeTransition.vue';
    import { storeToRefs } from 'pinia';
    import { useQuasar } from 'quasar';
    import { useRecipeExport } from 'src/composables/useRecipeExport';
    import { useShoppingListActions } from 'src/composables/useShoppingListActions';
    import { useStockItemActions } from 'src/composables/useStockItemActions';
    import { getStockLevelColour } from 'src/helpers/stockLevelLogic';
    import type { Recipe } from 'src/models/recipe';
    import type { StockLevelName } from 'src/models/stockLevel';
    import type { Substitute } from 'src/models/stockItemDetail';
    import RecipeApiService from 'src/services/api/recipeApiService';
    import type {
        CreateRecipeIngredientCommand,
        UpdateRecipeCommand,
    } from 'src/services/api/recipeApiService';
    import StockItemApiService from 'src/services/api/stockItemApiService';
    import { useRecipeStore } from 'src/stores/recipeStore';
    import { useShoppingListStore } from 'src/stores/shoppingListStore';
    import { useStockItemStore } from 'src/stores/stockItemStore';
    import { useStockLevelStore } from 'src/stores/stockLevelStore';
    import { computed, onMounted, reactive, ref, watch } from 'vue';
    import { useRoute, useRouter } from 'vue-router';
    import { describeApiError } from 'src/services/errorHandling/apiErrorHandler';

    const route = useRoute();
    const router = useRouter();
    const $q = useQuasar();

    const recipeStore = useRecipeStore();
    const stockItemStore = useStockItemStore();
    const stockLevelStore = useStockLevelStore();
    const shoppingListStore = useShoppingListStore();
    const recipeApi = new RecipeApiService();
    const stockItemApi = new StockItemApiService();
    const stockActions = useStockItemActions();
    const { addItems } = useShoppingListActions();

    const { recipeCollections } = storeToRefs(recipeStore);
    const { stockItems } = storeToRefs(stockItemStore);
    const { stockLevels } = storeToRefs(stockLevelStore);

    const recipeId = computed(() => String(route.params.id ?? ''));
    const recipe = ref<Recipe | null>(null);

    // Export actions — shared with the Data → Export & Print page so URL
    // shape and filename slug stay in lockstep.
    const recipeExport = useRecipeExport();
    function onExportCsv() {
        if (!recipeId.value) return;
        void recipeExport.downloadCsv(recipeId.value);
    }
    function onPrint() {
        if (!recipeId.value) return;
        recipeExport.openPrintView(recipeId.value);
    }
    const loading = ref(false);
    const loadError = ref<string | null>(null);
    const saving = ref(false);
    const isDirty = ref(false);

    // ── Form state (mirrors the editable recipe shape) ───────────────
    type IngredientForm = CreateRecipeIngredientCommand;

    type RecipeForm = {
        name: string;
        category: string | null;
        cook_time_minutes: number | null;
        cuisine: string | null;
        difficulty: string | null;
        instructions: string | null;
        nutrition: string | null;
        prep_time_minutes: number | null;
        recipe_collection_id: string | null;
        servings: number | null;
        time_of_day: string | null;
        ingredients: IngredientForm[];
    };

    const emptyForm = (): RecipeForm => ({
        name: '',
        category: null,
        cook_time_minutes: null,
        cuisine: null,
        difficulty: null,
        instructions: null,
        nutrition: null,
        prep_time_minutes: null,
        recipe_collection_id: null,
        servings: null,
        time_of_day: null,
        ingredients: [],
    });

    const form = reactive<RecipeForm>(emptyForm());

    function hydrateForm(source: Recipe) {
        Object.assign(form, {
            name: source.name,
            category: source.category,
            cook_time_minutes: source.cook_time_minutes,
            cuisine: source.cuisine,
            difficulty: source.difficulty,
            instructions: source.instructions,
            nutrition: source.nutrition,
            prep_time_minutes: source.prep_time_minutes,
            recipe_collection_id: source.recipe_collection_id,
            servings: source.servings,
            time_of_day: source.time_of_day,
            ingredients: source.ingredients.map((i) => ({
                stock_item_id: i.stock_item_id,
                quantity: i.quantity,
                unit: i.unit,
                notes: i.notes,
            })),
        });
        isDirty.value = false;
    }

    function markDirty() {
        isDirty.value = true;
    }

    // ── Stock-level helpers ──────────────────────────────────────────
    function levelNameFor(stockItemId: string): StockLevelName | null {
        const item = stockItems.value.find((s) => s.stock_item_id === stockItemId);
        if (!item) return null;
        const level = stockLevels.value.find((l) => l.stock_level_id === item.stock_level_id);
        return (level?.name) ?? null;
    }
    function levelColourFor(stockItemId: string): string | null {
        const name = levelNameFor(stockItemId);
        return name ? getStockLevelColour(name) : null;
    }
    function isMissing(stockItemId: string): boolean {
        if (!stockItemId) return true;
        const name = levelNameFor(stockItemId);
        // "Missing" matches the rest of the app: not tracked OR out of stock.
        return name === null || name === 'Out of Stock';
    }

    const missingIngredients = computed(() =>
        form.ingredients
            .filter((i) => i.stock_item_id && isMissing(i.stock_item_id))
            // Dedupe — an ingredient on multiple rows is still one shopping line.
            .filter((i, idx, arr) => arr.findIndex((x) => x.stock_item_id === i.stock_item_id) === idx),
    );

    const trackedCount = computed(
        () => new Set(form.ingredients.map((i) => i.stock_item_id).filter(Boolean)).size,
    );
    const inStockCount = computed(
        () =>
            new Set(
                form.ingredients
                    .map((i) => i.stock_item_id)
                    .filter((id) => Boolean(id) && !isMissing(id)),
            ).size,
    );
    const cookableNow = computed(() => missingIngredients.value.length === 0);

    // ── Picker (autocomplete + inline create) ────────────────────────
    const ingredientFilter = ref('');

    function onIngredientFilter(value: string, update: (cb: () => void) => void) {
        update(() => {
            ingredientFilter.value = value;
        });
    }

    function rowOptionsFor(_ing: IngredientForm) {
        // Show all stock items, filtered by the active typed text.
        const q = ingredientFilter.value.trim().toLowerCase();
        return stockItems.value
            .filter((s) => !q || s.name.toLowerCase().includes(q))
            .slice(0, 60)
            .map((s) => ({ label: s.name, value: s.stock_item_id }));
    }

    function onIngredientChosen(_value: unknown, _idx: number) {
        markDirty();
    }

    async function createInlineStockItem(idx: number, rawName: string) {
        const name = rawName.trim();
        if (!name) return;
        // Default the new item to the most-stocked level so it doesn't
        // immediately count as "missing" — the user hasn't told us otherwise
        // and slotting it straight into a recipe implies they have it.
        const wellStocked = stockLevels.value[0];
        if (!wellStocked) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'No stock levels configured — cannot create stock item.',
            });
            return;
        }
        try {
            await stockItemStore.createStockItemAsync({
                name,
                stock_level_id: wellStocked.stock_level_id,
                stock_location_id: null,
            });
            // Refresh-and-locate: createStockItemAsync pushes onto the store,
            // so the new id is there waiting for us.
            const created = stockItems.value.find((s) => s.name === name);
            if (created) {
                form.ingredients[idx]!.stock_item_id = created.stock_item_id;
                markDirty();
                $q.notify({
                    type: 'positive',
                    position: 'bottom-right',
                    message: `Created stock item "${name}".`,
                });
            }
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not create stock item.',
                caption: describeApiError(err) || '',
            });
        }
    }

    function addIngredient() {
        form.ingredients.push({
            stock_item_id: '',
            quantity: null,
            unit: null,
            notes: null,
        });
        markDirty();
    }
    function removeIngredient(idx: number) {
        form.ingredients.splice(idx, 1);
        markDirty();
    }

    // ── Collection options ───────────────────────────────────────────
    const collectionOptions = computed(() =>
        recipeCollections.value.map((c) => ({
            label: c.name,
            value: c.recipe_collection_id,
        })),
    );

    // ── Save / load ──────────────────────────────────────────────────
    async function loadRecipe() {
        loading.value = true;
        loadError.value = null;
        try {
            const fresh = await recipeApi.getAsync(recipeId.value);
            recipe.value = fresh;
            hydrateForm(fresh);
        } catch (err) {
            loadError.value = `Could not load recipe: ${describeApiError(err)}`;
        } finally {
            loading.value = false;
        }
    }

    async function onSave() {
        if (!recipe.value) return;
        saving.value = true;
        try {
            const ingredients = form.ingredients.filter((i) => Boolean(i.stock_item_id));
            const command: UpdateRecipeCommand = {
                recipe_id: recipe.value.recipe_id,
                name: form.name,
                category: form.category,
                cook_time_minutes: form.cook_time_minutes,
                cuisine: form.cuisine,
                difficulty: form.difficulty,
                instructions: form.instructions,
                nutrition: form.nutrition,
                prep_time_minutes: form.prep_time_minutes,
                recipe_collection_id: form.recipe_collection_id,
                servings: form.servings,
                time_of_day: form.time_of_day,
                ingredients,
            };
            await recipeStore.updateRecipeAsync(command);
            await loadRecipe();
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: 'Recipe saved.',
            });
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not save recipe.',
                caption: describeApiError(err) || '',
            });
        } finally {
            saving.value = false;
        }
    }

    // ── Sidebar actions ──────────────────────────────────────────────
    async function onToggleFavourite() {
        if (!recipe.value) return;
        try {
            await recipeStore.toggleFavouriteAsync(recipe.value);
            await loadRecipe();
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not toggle favourite.',
                caption: describeApiError(err) || '',
            });
        }
    }

    function onStartCookMode() {
        if (!recipe.value) return;
        if (isDirty.value) {
            $q.dialog({
                title: 'Unsaved changes',
                message: 'Save before starting cook mode? Unsaved tweaks will be lost otherwise.',
                ok: { label: 'Save and cook', color: 'primary', noCaps: true },
                cancel: { label: 'Cook without saving', noCaps: true },
            })
                .onOk(() => {
                    void (async () => {
                        await onSave();
                        void router.push(`/recipes/${recipeId.value}/cook`);
                    })();
                })
                .onCancel(() => { void router.push(`/recipes/${recipeId.value}/cook`); });
            return;
        }
        void router.push(`/recipes/${recipeId.value}/cook`);
    }

    function onAddRowToList(ing: IngredientForm) {
        if (!ing.stock_item_id) return;
        void stockActions.addToList(ing.stock_item_id);
    }

    // Add-all-missing → opens a small target-list picker dialog.
    const targetListOpen = ref(false);
    const targetListId = ref<string | null>(null);
    const addingMissing = ref(false);

    const activeListOptions = computed(() =>
        shoppingListStore.summaries
            .filter((s) => !s.is_archived)
            .map((s) => ({
                label: s.name + (s.is_primary ? ' (primary)' : ''),
                value: s.shopping_list_id,
            })),
    );

    function onAddMissingToList() {
        if (missingIngredients.value.length === 0) return;
        targetListId.value =
            shoppingListStore.primaryListId ?? activeListOptions.value[0]?.value ?? null;
        if (!targetListId.value) {
            $q.dialog({
                title: 'No active shopping list',
                message: 'Create or unarchive one first.',
                ok: { label: 'Open lists', color: 'primary', noCaps: true },
                cancel: { noCaps: true },
            }).onOk(() => { void router.push('/shopping-lists'); });
            return;
        }
        targetListOpen.value = true;
    }

    async function confirmAddMissing() {
        if (!targetListId.value) return;
        addingMissing.value = true;
        try {
            await addItems(
                targetListId.value,
                missingIngredients.value.map((i) => ({
                    stock_item_id: i.stock_item_id,
                })),
            );
            targetListOpen.value = false;
        } finally {
            addingMissing.value = false;
        }
    }

    // ── Substitutes ──────────────────────────────────────────────────
    const substitutesOpen = ref(false);
    const loadingSubstitutes = ref(false);
    const substituteOptions = ref<
        { stockItemId: string; name: string; substitutes: Substitute[] }[]
    >([]);

    async function onFindSubstitutes() {
        if (missingIngredients.value.length === 0) return;
        substitutesOpen.value = true;
        loadingSubstitutes.value = true;
        try {
            // Fan-out: one detail fetch per missing item. N is small and this
            // is interactive, so the parallelism is fine.
            const results = await Promise.all(
                missingIngredients.value.map(async (ing) => {
                    const detail = await stockItemApi.getDetailAsync(ing.stock_item_id);
                    const ingName =
                        recipe.value?.ingredients.find(
                            (i) => i.stock_item_id === ing.stock_item_id,
                        )?.stock_item_name ?? detail.name;
                    return {
                        stockItemId: ing.stock_item_id,
                        name: ingName,
                        substitutes: detail.substitutes ?? [],
                    };
                }),
            );
            substituteOptions.value = results;
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not load substitutes.',
                caption: describeApiError(err) || '',
            });
            substitutesOpen.value = false;
        } finally {
            loadingSubstitutes.value = false;
        }
    }

    // ── Import from URL ──────────────────────────────────────────────
    const importOpen = ref(false);
    const importUrl = ref('');
    const importError = ref<string | null>(null);
    const importing = ref(false);

    function onImportFromUrl() {
        importUrl.value = '';
        importError.value = null;
        importOpen.value = true;
    }

    async function onConfirmImport() {
        const url = importUrl.value.trim();
        if (!url) return;
        importing.value = true;
        importError.value = null;
        try {
            const imported = await recipeApi.importFromUrlAsync(url);
            // Confirm overwrite — the imported result might wipe out
            // careful local edits if we just clobber the form.
            const proceed = await new Promise<boolean>((resolve) => {
                $q.dialog({
                    title: `Import "${imported.name}"?`,
                    message:
                        `Found ${imported.ingredients.length} ingredient${
                            imported.ingredients.length === 1 ? '' : 's'
                        }. ${
                            imported.ingredients.filter((i) => i.stock_item_id).length
                        } matched existing stock items.${
                            isDirty.value
                                ? ' Your unsaved edits to this recipe will be discarded.'
                                : ''
                        }`,
                    ok: { label: 'Replace fields', color: 'primary', noCaps: true },
                    cancel: { noCaps: true },
                })
                    .onOk(() => resolve(true))
                    .onCancel(() => resolve(false))
                    .onDismiss(() => resolve(false));
            });
            if (!proceed) return;

            form.name = imported.name;
            form.cuisine = imported.cuisine;
            form.category = imported.category;
            form.difficulty = imported.difficulty;
            form.servings = imported.servings;
            form.prep_time_minutes = imported.prep_time_minutes;
            form.cook_time_minutes = imported.cook_time_minutes;
            form.instructions = [
                imported.instructions,
                imported.source_url ? `Source: ${imported.source_url}` : '',
            ]
                .filter(Boolean)
                .join('\n\n') || null;
            form.nutrition = imported.nutrition;
            form.ingredients = imported.ingredients.map((i) => ({
                stock_item_id: i.stock_item_id ?? '',
                quantity: i.quantity,
                unit: i.unit,
                notes:
                    i.stock_item_id
                        ? i.notes ?? null
                        : `Raw: ${i.raw_text}` + (i.notes ? ` (${i.notes})` : ''),
            }));
            markDirty();
            importOpen.value = false;
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message:
                    `Imported "${imported.name}". ` +
                    `${imported.ingredients.filter((i) => !i.stock_item_id).length} ingredients need a stock-item match.`,
            });
        } catch (err) {
            importError.value =
                'Could not import. The URL might not publish structured recipe data.';
             
            console.warn('Import failed', err);
        } finally {
            importing.value = false;
        }
    }

    // ── Meals-on-hand controls ────────────────────────────────────────
    const adjusting = ref(false);
    const logCookOpen = ref(false);
    const logCookCount = ref<number>(1);
    const logging = ref(false);

    async function onAdjustMeals(delta: number) {
        if (!recipe.value) return;
        adjusting.value = true;
        try {
            await recipeStore.adjustMealsAsync(recipe.value.recipe_id, delta);
            await loadRecipe();
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not update meals.',
                caption: describeApiError(err) || '',
            });
        } finally {
            adjusting.value = false;
        }
    }

    async function onLogCook() {
        if (!recipe.value) return;
        const n = Math.max(1, Math.floor(logCookCount.value || 0));
        logging.value = true;
        try {
            await recipeStore.cookAsync(recipe.value.recipe_id, n);
            await loadRecipe();
            logCookOpen.value = false;
            logCookCount.value = 1;
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: `Logged ${n} cooked meal${n === 1 ? '' : 's'}.`,
            });
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not log cook.',
                caption: describeApiError(err) || '',
            });
        } finally {
            logging.value = false;
        }
    }

    async function onDelete() {
        if (!recipe.value) return;
        const ok = await new Promise<boolean>((resolve) => {
            $q.dialog({
                title: 'Delete recipe',
                message: `Delete "${recipe.value!.name}"? This cannot be undone.`,
                ok: { label: 'Delete', color: 'negative', noCaps: true },
                cancel: { noCaps: true },
            })
                .onOk(() => resolve(true))
                .onCancel(() => resolve(false))
                .onDismiss(() => resolve(false));
        });
        if (!ok) return;
        try {
            await recipeStore.deleteRecipeAsync(recipe.value.recipe_id);
            void router.push('/recipes');
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not delete.',
                caption: describeApiError(err) || '',
            });
        }
    }

    function onBack() {
        if (isDirty.value) {
            $q.dialog({
                title: 'Discard unsaved changes?',
                message: 'Your edits will be lost.',
                ok: { label: 'Discard', color: 'negative', noCaps: true },
                cancel: { noCaps: true },
            }).onOk(() => { void router.push('/recipes'); });
            return;
        }
        void router.push('/recipes');
    }

    // ── Mount ────────────────────────────────────────────────────────
    onMounted(async () => {
        await Promise.all([
            recipeStore.getRecipeCollectionsAsync(),
            stockItemStore.getStockItemsAsync(),
            stockLevelStore.getStockLevelsAsync(),
            shoppingListStore.refreshAsync(),
        ]);
        await loadRecipe();
    });

    // Re-load when navigating between recipes without unmount.
    watch(recipeId, () => {
        if (recipeId.value) void loadRecipe();
    });
</script>

<style scoped>
    .recipe-name-input :deep(input) {
        font-size: 1.5rem;
        font-weight: 500;
    }
    .ingredient-row {
        align-items: flex-start;
    }
</style>
