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
            <!-- â”€â”€ Header â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ -->
            <div class="row items-center q-mb-sm no-wrap">
                <BaseButton variant="icon" :icon="ICONS.arrow_back" @click="onBack" />
                <div class="q-ml-sm col">
                    <div class="text-caption dora-text-muted">
                        <router-link to="/cookbook" class="dora-text-muted">
                            Cookbook
                        </router-link>
                        <q-icon :name="ICONS.chevron_right" size="14px" />
                        {{ form.name || 'Untitled recipe' }}
                    </div>
                </div>
                <BaseButton
                    variant="ghost"
                    :icon="recipe.is_favourite ? 'favorite' : 'favorite_border'"
                    :label="recipe.is_favourite ? 'Favourited' : 'Favourite'"
                    :class="{ 'text-negative': recipe.is_favourite }"
                    @click="onToggleFavourite"
                />
            </div>

            <!-- L289 — the name is its own clearly-editable field (matching
                 the stock-item screen), not a heading masquerading as one. -->
            <q-input
                v-model="form.name"
                outlined
                dense
                label="Recipe name"
                class="q-mb-md recipe-name-input"
                :error="!!nameError"
                :error-message="nameError ?? undefined"
                @update:model-value="onNameInput"
            />

            <!-- L308 — actions across the top (sticky), never stranded at the
                 bottom on mobile. Mark cooked is the prominent action and sits
                 far from Delete (L305). -->
            <div class="recipe-toolbar row items-center q-gutter-sm q-mb-md">
                <BaseButton
                    variant="primary"
                    :icon="ICONS.restaurant"
                    label="Mark cooked"
                    :loading="adjusting"
                    @click="onMarkCooked"
                />
                <BaseButton
                    variant="secondary"
                    :icon="ICONS.restaurant_menu"
                    label="Cook mode"
                    @click="onStartCookMode"
                />
                <BaseButton
                    variant="ghost"
                    :icon="ICONS.history"
                    label="Log cook…"
                    @click="logCookOpen = true"
                />
                <BaseButton
                    variant="ghost"
                    :icon="ICONS.print"
                    label="Print"
                    @click="onPrint"
                />
                <q-space />
                <BaseButton
                    variant="primary"
                    :icon="ICONS.save"
                    label="Save"
                    :disable="!isDirty"
                    :loading="saving"
                    @click="onSave"
                />
                <BaseButton variant="icon" :icon="ICONS.more_vert">
                    <q-menu anchor="bottom right" self="top right" transition-show="jump-down" transition-hide="jump-up">
                        <q-list dense style="min-width: 220px">
                            <!-- C-4 Chunk 8 — copies the recipe into a sibling version
                                 (same `version_group_id`) and routes into it. -->
                            <q-item
                                clickable
                                v-close-popup
                                :disable="newVersionLoading"
                                @click="onNewVersion"
                            >
                                <q-item-section avatar>
                                    <q-icon :name="ICONS.content_copy" />
                                </q-item-section>
                                <q-item-section>New version</q-item-section>
                            </q-item>
                            <q-separator />
                            <q-item clickable v-close-popup @click="onDelete">
                                <q-item-section avatar>
                                    <q-icon :name="ICONS.delete" color="negative" />
                                </q-item-section>
                                <q-item-section class="text-negative">Delete recipe</q-item-section>
                            </q-item>
                        </q-list>
                    </q-menu>
                </BaseButton>
            </div>

            <div class="row q-col-gutter-lg">
                <!-- â”€â”€ Main editor column â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ -->
                <div class="col-12 col-md-8">
                    <!-- C-4 Chunk 5 — recipe image (FU-039). -->
                    <q-card flat bordered class="q-mb-md">
                        <q-card-section>
                            <RecipeImageField
                                :preview-url="imagePreviewUrl"
                                :name="form.name"
                                @pick="onPickImage"
                                @clear="onClearImage"
                            />
                        </q-card-section>
                    </q-card>

                    <q-card flat bordered class="q-mb-md">
                        <q-card-section>
                            <div class="row q-col-gutter-sm">
                                <q-select
                                    v-model="form.cuisine_id"
                                    outlined
                                    dense
                                    label="Cuisine"
                                    :options="cuisineOptions"
                                    emit-value
                                    map-options
                                    clearable
                                    class="col-12 col-sm-6"
                                    @update:model-value="markDirty"
                                />
                                <q-select
                                    v-model="form.category_id"
                                    outlined
                                    dense
                                    label="Category"
                                    :options="categoryOptions"
                                    emit-value
                                    map-options
                                    clearable
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
                                <!-- C-4 Chunk 9 — simple nutrition (kcal).
                                     Gated on C-cross nutrition opt-in being
                                     in `simple` (or `complex` once that
                                     ships); hidden when `off`. -->
                                <q-input
                                    v-if="nutritionEnabled"
                                    v-model.number="form.kcal"
                                    outlined
                                    dense
                                    type="number"
                                    label="kcal per serving"
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
                                <!-- L264 â€” dietary tags editable on the detail
                                     page (the primary edit surface), not only
                                     the add modal. -->
                                <q-select
                                    v-model="form.dietary_tag_ids"
                                    outlined
                                    dense
                                    label="Dietary tags"
                                    :options="dietaryTagOptions"
                                    emit-value
                                    map-options
                                    multiple
                                    use-chips
                                    clearable
                                    class="col-12 col-sm-6"
                                    @update:model-value="markDirty"
                                />
                                <!-- L310 — tools required (configurable). -->
                                <q-select
                                    v-model="form.tool_ids"
                                    outlined
                                    dense
                                    label="Tools"
                                    :options="toolOptions"
                                    emit-value
                                    map-options
                                    multiple
                                    use-chips
                                    clearable
                                    class="col-12 col-sm-6"
                                    @update:model-value="markDirty"
                                />
                            </div>
                        </q-card-section>
                    </q-card>

                    <!-- â”€â”€ Meals on hand â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ -->
                    <q-card v-if="recipe" flat bordered class="q-mb-md">
                        <q-card-section class="row items-center q-gutter-md no-wrap">
                            <div>
                                <div class="text-subtitle1">Available meals</div>
                                <div class="text-caption dora-text-muted">
                                    {{ recipe.unallocated_meals }} unallocated
                                    of {{ recipe.available_meals }} cooked
                                </div>
                            </div>
                            <q-space />
                            <MealStepper
                                :available="recipe.available_meals"
                                :busy="adjusting"
                                @adjust="onAdjustMeals"
                            />
                        </q-card-section>
                    </q-card>

                    <!-- ── Sections (C-4 Chunk 10) ─────────────────────
                         Optional named groups. Empty = flat recipe (existing
                         behaviour). Rows are assigned to a section via the
                         per-ingredient picker below. Renaming/reordering is
                         in-place; deleting a section unsections its rows. -->
                    <q-card flat bordered class="q-mb-md">
                        <q-card-section class="row items-center q-pb-sm">
                            <div class="text-subtitle1">
                                Sections
                                <span class="text-caption dora-text-muted q-ml-sm">
                                    {{ form.sections.length }}
                                </span>
                            </div>
                            <q-space />
                            <q-btn
                                flat
                                dense
                                no-caps
                                :icon="ICONS.add"
                                label="Add section"
                                @click="addSection"
                            />
                        </q-card-section>
                        <q-separator v-if="form.sections.length > 0" />
                        <q-list v-if="form.sections.length > 0" separator>
                            <q-item v-for="(sec, sIdx) in form.sections" :key="sec.client_id">
                                <q-item-section>
                                    <q-input
                                        v-model="sec.name"
                                        dense
                                        outlined
                                        label="Section name"
                                        placeholder="e.g. Sauce"
                                        @update:model-value="markDirty"
                                    />
                                </q-item-section>
                                <q-item-section side>
                                    <div class="row q-gutter-xs">
                                        <q-btn
                                            flat round dense
                                            icon="arrow_upward"
                                            :disable="sIdx === 0"
                                            @click="moveSection(sIdx, -1)"
                                        />
                                        <q-btn
                                            flat round dense
                                            icon="arrow_downward"
                                            :disable="sIdx === form.sections.length - 1"
                                            @click="moveSection(sIdx, 1)"
                                        />
                                        <q-btn
                                            flat round dense
                                            :icon="ICONS.delete"
                                            color="negative"
                                            @click="removeSection(sIdx)"
                                        />
                                    </div>
                                </q-item-section>
                            </q-item>
                        </q-list>
                        <q-card-section v-else class="dora-text-muted text-caption">
                            No sections. Add one if your recipe has named parts
                            (e.g. "Sauce", "Filling"); ingredients without a
                            section render as one flat list.
                        </q-card-section>
                    </q-card>

                    <!-- â”€â”€ Ingredients â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ -->
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
                                :class="{ 'ingredient-row--missing': ing.stock_item_id && isMissingItem(ing.stock_item_id) }"
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
                                                    Type to search â€” or press
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

                                <!-- L292 — one status chip per row. "Missing"
                                     wins (it's the actionable state) and the
                                     row itself is tinted; otherwise show the
                                     stock-level chip. -->
                                <q-item-section side top style="min-width: 130px">
                                    <div v-if="ing.stock_item_id" class="column items-end">
                                        <q-chip
                                            v-if="isMissingItem(ing.stock_item_id)"
                                            dense
                                            color="negative"
                                            text-color="white"
                                            :icon="ICONS.report"
                                        >
                                            Missing
                                        </q-chip>
                                        <q-chip
                                            v-else
                                            dense
                                            :color="levelColourFor(ing.stock_item_id) ?? undefined"
                                            :text-color="levelColourFor(ing.stock_item_id) ? 'white' : undefined"
                                            :class="levelColourFor(ing.stock_item_id) ? undefined : 'dora-bg-sunken dora-text-secondary'"
                                        >
                                            {{ levelNameFor(ing.stock_item_id) ?? 'Untracked' }}
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

                                <!-- C-4 Chunk 10 — section picker, only when
                                     the recipe has named sections. -->
                                <q-item-section
                                    v-if="form.sections.length > 0"
                                    style="max-width: 160px"
                                >
                                    <q-select
                                        v-model="ing.section_client_id"
                                        :options="sectionOptions"
                                        option-value="value"
                                        option-label="label"
                                        emit-value
                                        map-options
                                        dense
                                        outlined
                                        label="Section"
                                        @update:model-value="markDirty"
                                    />
                                </q-item-section>

                                <q-item-section side top>
                                    <div class="row q-gutter-xs items-center">
                                        <!-- C-7 Chunk 1 — unified AddToListButton.
                                             State-aware + toggle behaviour;
                                             replaces the row's hand-rolled
                                             "add to primary" path. -->
                                        <AddToListButton
                                            v-if="ing.stock_item_id"
                                            variant="row"
                                            :stock-item-id="ing.stock_item_id"
                                        />
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

                    <!-- ── Instructions ─ Structured steps + freeform fallback ─ -->
                    <q-card flat bordered class="q-mb-md">
                        <q-card-section>
                            <div class="row items-center q-mb-sm">
                                <div class="text-subtitle1">Instructions</div>
                                <q-space />
                                <q-btn-toggle
                                    v-model="form.steps_mode"
                                    :options="[
                                        { label: 'Structured', value: 'structured' },
                                        { label: 'Freeform', value: 'freeform' },
                                    ]"
                                    flat
                                    dense
                                    no-caps
                                    spread
                                    toggle-color="primary"
                                    @update:model-value="markDirty"
                                />
                            </div>

                            <RecipeStepsEditor
                                v-if="form.steps_mode === 'structured'"
                                :steps="form.steps"
                                :ingredient-options="stepIngredientOptions"
                                :tool-options="stepToolOptions"
                                @update:steps="onStepsChange"
                            />

                            <q-input
                                v-else
                                v-model="form.instructions"
                                outlined
                                type="textarea"
                                autogrow
                                placeholder="One step per line. Cook mode will split on newlines."
                                @update:model-value="markDirty"
                            />

                            <q-expansion-item
                                v-if="form.steps_mode === 'structured'"
                                label="Advanced — keep a freeform instructions blob too"
                                :icon="ICONS.notes"
                                class="q-mt-md"
                                dense
                            >
                                <q-input
                                    v-model="form.instructions"
                                    outlined
                                    type="textarea"
                                    autogrow
                                    placeholder="Optional plain-text instructions (kept as a fallback for cook mode if no structured steps exist)."
                                    @update:model-value="markDirty"
                                />
                            </q-expansion-item>
                        </q-card-section>
                    </q-card>

                    <!-- ── C-4 Chunk 7 — Source URL (optional) ────────────── -->
                    <q-card flat bordered class="q-mb-md">
                        <q-card-section>
                            <q-input
                                v-model="form.source"
                                outlined
                                dense
                                label="Source URL (optional)"
                                placeholder="https://example.com/recipes/lasagne"
                                :icon="ICONS.link"
                                @update:model-value="markDirty"
                            >
                                <template #append>
                                    <BaseButton
                                        v-if="form.source && form.source.startsWith('http')"
                                        variant="ghost"
                                        :icon="ICONS.open_in_new"
                                        label="Open"
                                        :href="form.source"
                                        target="_blank"
                                    />
                                </template>
                            </q-input>
                        </q-card-section>
                    </q-card>

                    <!-- C-4 Chunk 9 — freeform Nutrition field deliberately
                         no longer rendered/edited. The simple-mode kcal
                         input lives next to servings/prep/cook above. The
                         freeform column survives in the form/DTO for
                         backwards compatibility until we're sure no user
                         has typed something irreplaceable in there
                         (see FU-115). -->
                </div>

                <!-- â”€â”€ Sidebar â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ -->
                <div class="col-12 col-md-4">
                    <!-- L290 — theme-aware: soft tinted surfaces with
                         on-surface text instead of a hard bright green that
                         was unreadable in dark mode. -->
                    <q-card
                        flat
                        bordered
                        class="q-mb-md"
                        :class="cookableNow ? 'dora-bg-positive-soft text-positive' : 'dora-bg-warning-soft text-warning'"
                    >
                        <q-card-section>
                            <div class="row items-center q-gutter-sm">
                                <q-icon
                                    :name="cookableNow ? ICONS.check_circle : ICONS.shopping_cart"
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
                                    <div class="text-caption dora-text-secondary">
                                        {{ inStockCount }} of {{ trackedCount }} in stock
                                    </div>
                                </div>
                            </div>
                        </q-card-section>
                    </q-card>

                    <!-- FU-083 — read-only "last cooked". The cook + log-cook
                         actions in the top toolbar update this value;
                         displaying it here closes the loop ("when did I make
                         this last?") without needing a separate journal view. -->
                    <q-card flat bordered class="q-mb-md" v-if="recipe">
                        <q-card-section class="row items-center q-gutter-sm">
                            <q-icon :name="ICONS.history" size="22px" class="dora-text-muted" />
                            <div>
                                <div class="text-caption dora-text-muted">Last cooked</div>
                                <div class="text-body2">
                                    {{ recipe.last_made_on ? formatLastMade(recipe.last_made_on) : 'Never' }}
                                </div>
                            </div>
                        </q-card-section>
                    </q-card>

                    <!-- C-4 Chunk 9 / DEC-5 — cost estimate. Server-derived
                         from linked product offers; rendered only when the
                         C-cross money opt-in is on AND at least one
                         ingredient could be priced. "Estimate" is the loud
                         word — the tooltip explains the math + the
                         coverage. -->
                    <q-card
                        v-if="moneyEnabled && recipe && recipe.estimated_cost !== null"
                        flat
                        bordered
                        class="q-mb-md"
                    >
                        <q-card-section class="row items-center q-gutter-sm">
                            <q-icon :name="ICONS.payments" size="22px" class="dora-text-muted" />
                            <div>
                                <div class="text-caption dora-text-muted">
                                    Estimated cost
                                    <q-icon :name="ICONS.help_outline" size="14px" class="q-ml-xs">
                                        <q-tooltip>
                                            Estimate — sums each ingredient's
                                            quantity × current offer price
                                            (per unit) from any linked
                                            product. Based on
                                            {{ recipe.estimated_cost_priced_count }}
                                            of
                                            {{ recipe.estimated_cost_total_count }}
                                            ingredients with linked offers.
                                            Unit reconciliation is rough.
                                        </q-tooltip>
                                    </q-icon>
                                </div>
                                <div class="text-body2">
                                    <strong>${{ recipe.estimated_cost.toFixed(2) }}</strong>
                                    <span class="text-caption dora-text-muted q-ml-xs">
                                        ({{ recipe.estimated_cost_priced_count }} /
                                        {{ recipe.estimated_cost_total_count }}
                                        ingredients priced)
                                    </span>
                                </div>
                            </div>
                        </q-card-section>
                    </q-card>

                    <!-- C-4 Chunk 9 — kcal card. Read-only echo of the
                         editor field; renders only when nutrition is in
                         simple/complex mode AND the recipe has a value. -->
                    <q-card
                        v-if="nutritionEnabled && recipe && recipe.kcal !== null && recipe.kcal !== undefined"
                        flat
                        bordered
                        class="q-mb-md"
                    >
                        <q-card-section class="row items-center q-gutter-sm">
                            <q-icon :name="ICONS.monitor_heart" size="22px" class="dora-text-muted" />
                            <div>
                                <div class="text-caption dora-text-muted">
                                    Nutrition (per serving)
                                </div>
                                <div class="text-body2">
                                    <strong>{{ recipe.kcal }}</strong>
                                    <span class="dora-text-muted q-ml-xs">kcal</span>
                                </div>
                            </div>
                        </q-card-section>
                    </q-card>

                    <q-card flat bordered class="q-mb-md">
                        <q-list separator>
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
                                    <q-item-label>Import from URLâ€¦</q-item-label>
                                    <q-item-label caption>
                                        Pulls structured recipe data from the page.
                                    </q-item-label>
                                </q-item-section>
                            </q-item>
                        </q-list>
                    </q-card>

                    <!-- C-4 Chunk 8 — Versions card. Only renders when this
                         recipe has siblings sharing its version_group_id.
                         A lone group-id (singleton that's never been
                         versioned) hides the card. -->
                    <q-card v-if="versionSiblings.length > 0" flat bordered class="q-mb-md">
                        <q-card-section>
                            <div class="row items-center q-gutter-xs q-mb-xs">
                                <q-icon :name="ICONS.content_copy" size="18px" class="dora-text-muted" />
                                <div class="text-subtitle1">Other versions</div>
                            </div>
                            <div class="text-caption dora-text-muted q-mb-sm">
                                Equal peers — pick any when scheduling a meal.
                            </div>
                            <q-list dense separator>
                                <q-item
                                    v-for="sibling in versionSiblings"
                                    :key="sibling.recipe_id"
                                    clickable
                                    @click="onJumpToSibling(sibling.recipe_id)"
                                >
                                    <q-item-section>
                                        <q-item-label>{{ sibling.name }}</q-item-label>
                                        <q-item-label caption class="dora-text-muted">
                                            <span v-if="sibling.last_made_on">
                                                Last made {{ formatLastMade(sibling.last_made_on) }}
                                            </span>
                                            <span v-else>Never made</span>
                                            · {{ sibling.available_meals }} on hand
                                        </q-item-label>
                                    </q-item-section>
                                    <q-item-section side>
                                        <q-icon :name="ICONS.east" />
                                    </q-item-section>
                                </q-item>
                            </q-list>
                        </q-card-section>
                    </q-card>
                </div>
            </div>
        </div>
        </FadeTransition>

        <!-- â”€â”€ Substitutes dialog â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ -->
        <BaseDialog v-model="substitutesOpen" card-style="min-width: 460px; max-width: 640px">
                <q-card-section>
                    <div class="text-h6">Substitutes for missing ingredients</div>
                    <div class="text-caption dora-text-muted">
                        These are recorded on each item's detail page. To cook
                        with one, start cook mode and tap the swap icon on the
                        ingredient â€” it applies to that cook only and never
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
                            No substitutes recorded â€” set some on the stock item's detail page.
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

        <!-- â”€â”€ Import-from-URL dialog â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ -->
        <BaseDialog v-model="importOpen" card-style="min-width: 460px; max-width: 600px">
                <q-card-section>
                    <div class="text-h6">Import from URL</div>
                    <div class="text-caption dora-text-muted q-mt-xs">
                        Works on recipe sites that publish
                        <strong>schema.org Recipe JSON-LD</strong> — the
                        format most blogs, BBC Good Food, NYT Cooking,
                        Serious Eats, AllRecipes, and similar publishers
                        use. Other URLs still import: we'll pull the page
                        title and text into Instructions so you can clean
                        it up. Your existing recipe will be overwritten
                        with the imported fields.
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

        <!-- â”€â”€ Target-list picker (for add-all-missing) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ -->
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

        <!-- Log cook â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ -->
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

        <!-- Cook-mode guard (L297/L299/L309). Click-out / Esc just closes
             (BaseDialog v-model), never navigates. -->
        <BaseDialog v-model="cookGuardOpen" card-style="min-width: 340px; max-width: 460px">
            <q-card-section>
                <div class="text-h6">Start cook mode?</div>
                <ul class="q-mt-sm q-mb-none dora-text-secondary">
                    <li v-if="isDirty">You have unsaved changes.</li>
                    <li v-if="!cookableNow">
                        This recipe isn't cookable now —
                        {{ missingIngredients.length }} ingredient{{ missingIngredients.length === 1 ? '' : 's' }} missing.
                    </li>
                </ul>
            </q-card-section>
            <q-card-actions align="right">
                <BaseButton variant="ghost" label="Cancel" @click="cookGuardOpen = false" />
                <BaseButton
                    v-if="isDirty"
                    variant="ghost"
                    label="Start without saving"
                    @click="goToCookMode"
                />
                <BaseButton
                    v-if="isDirty"
                    variant="primary"
                    label="Save & start"
                    :loading="saving"
                    @click="onGuardSaveAndCook"
                />
                <BaseButton
                    v-else
                    variant="primary"
                    label="Start anyway"
                    @click="goToCookMode"
                />
            </q-card-actions>
        </BaseDialog>
    </q-page>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import AppSkeleton from 'src/components/AppSkeleton.vue';
    import AppSpinner from 'src/components/AppSpinner.vue';
    import AddToListButton from 'src/components/AddToListButton.vue';
    import BaseButton from 'src/components/BaseButton.vue';
    import BaseDialog from 'src/components/BaseDialog.vue';
    import MealStepper from 'src/components/recipes/MealStepper.vue';
    import RecipeImageField from 'src/components/recipes/RecipeImageField.vue';
    import RecipeStepsEditor from 'src/components/recipes/RecipeStepsEditor.vue';
    import type {
        EditableStep as EditableRecipeStep,
        IngredientOption,
        ToolOption,
    } from 'src/components/recipes/recipeStepEditorTypes';
    import FadeTransition from 'src/components/transitions/FadeTransition.vue';
    import { storeToRefs } from 'pinia';
    import { useQuasar } from 'quasar';
    import { useRecipeExport } from 'src/composables/useRecipeExport';
    import { useShoppingListActions } from 'src/composables/useShoppingListActions';
    import { useStockItemActions } from 'src/composables/useStockItemActions';
    import { getStockLevelColour } from 'src/helpers/stockLevelLogic';
    import type { Recipe } from 'src/models/recipe';
    import type { Substitute } from 'src/models/stockItemDetail';
    import RecipeApiService, { recipeImageUrl } from 'src/services/api/recipeApiService';
    import { useImagePrefs } from 'src/composables/useImagePrefs';
    import { useMoneyEnabled } from 'src/composables/useMoneyEnabled';
    import { useNutritionMode } from 'src/composables/useNutritionMode';
    import type {
        CreateRecipeIngredientCommand,
        RecipeStepCommand,
        UpdateRecipeCommand,
    } from 'src/services/api/recipeApiService';
    import StockItemApiService from 'src/services/api/stockItemApiService';
    import { useRecipeStore } from 'src/stores/recipeStore';
    import { useRecipeVocabStore } from 'src/stores/recipeVocabStore';
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
    const recipeVocabStore = useRecipeVocabStore();
    const recipeApi = new RecipeApiService();
    // C-cross Chunk 5 — recipe-image render gate (covers the saved-
    // preview branch only; pick/clear is always live).
    const { showRecipeImages } = useImagePrefs();
    // C-4 Chunk 9 — money + nutrition gates for the new estimate/kcal
    // surfaces. Both render-only; consumers fall back to no-render when
    // either flag is off.
    const { moneyEnabled } = useMoneyEnabled();
    const { nutritionEnabled } = useNutritionMode();
    const stockItemApi = new StockItemApiService();
    const stockActions = useStockItemActions();
    const { addItems } = useShoppingListActions();

    const { recipeCollections } = storeToRefs(recipeStore);
    const { stockItems } = storeToRefs(stockItemStore);
    const { stockLevels } = storeToRefs(stockLevelStore);
    const { cuisines, categories, dietaryTags, tools } = storeToRefs(recipeVocabStore);

    const recipeId = computed(() => String(route.params.id ?? ''));
    const recipe = ref<Recipe | null>(null);

    // Export actions â€” shared with the Data â†’ Export & Print page so URL
    // shape and filename slug stay in lockstep.
    const recipeExport = useRecipeExport();
    // L306 — CSV export removed from the recipe detail page (felt out of
    // place); Print/PDF stays as a top-toolbar action.
    function onPrint() {
        if (!recipeId.value) return;
        recipeExport.openPrintView(recipeId.value);
    }
    const loading = ref(false);
    const loadError = ref<string | null>(null);
    const saving = ref(false);
    const isDirty = ref(false);
    const nameError = ref<string | null>(null);
    const cookGuardOpen = ref(false);
    // Image edit state: imageDirty marks a pick/clear; imageVersion busts the
    // <img> cache after a save so the new image shows.
    const imageDirty = ref(false);
    const imageVersion = ref(0);

    function onNameInput() {
        nameError.value = null;
        markDirty();
    }

    // â”€â”€ Form state (mirrors the editable recipe shape) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    type IngredientForm = CreateRecipeIngredientCommand;

    type RecipeForm = {
        name: string;
        category_id: string | null;
        cook_time_minutes: number | null;
        cuisine_id: string | null;
        difficulty: string | null;
        instructions: string | null;
        nutrition: string | null;
        prep_time_minutes: number | null;
        recipe_collection_id: string | null;
        servings: number | null;
        // C-4 Chunk 7 — origin URL.
        source: string | null;
        time_of_day: string | null;
        ingredients: IngredientForm[];
        dietary_tag_ids: string[];
        tool_ids: string[];
        // null = no change (existing image, shown via the endpoint). A data URL
        // sets a new image; explicit null + imageDirty clears it.
        image: string | null;
        // C-4 Chunk 6 — structured steps editor state.
        steps: EditableRecipeStep[];
        // Editor mode toggle. Structured ⇒ steps[] is the source of truth and
        // gets sent on save; freeform ⇒ instructions textarea is the source
        // and an empty steps[] gets sent to clear server-side structure.
        steps_mode: 'structured' | 'freeform';
        // C-4 Chunk 9 — simple nutrition kcal. Editor input renders only
        // when nutrition is enabled; the form field exists regardless.
        kcal: number | null;
        // C-4 Chunk 10 — named sections. Empty list = flat recipe.
        // Hydrated from `recipe.sections`; the existing section_id is
        // reused as client_id so unchanged sections round-trip and
        // ingredient `section_client_id` references stay valid.
        sections: SectionForm[];
    };

    type SectionForm = {
        client_id: string;
        sequence: number;
        name: string;
    };

    function newClientId(): string {
        if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
            return crypto.randomUUID();
        }
        return `c${Date.now().toString(36)}${Math.random().toString(36).slice(2, 10)}`;
    }

    /** `q-input v-model.number` leaves an empty field as `''` (not null) and
     *  a non-numeric clear as `NaN`. The server expects `int | None`, so we
     *  coerce to a real integer or `null` here at the wire boundary. */
    function toIntOrNull(value: unknown): number | null {
        if (value === null || value === undefined || value === '') return null;
        const n = typeof value === 'number' ? value : Number(value);
        if (!Number.isFinite(n)) return null;
        return Math.trunc(n);
    }

    const emptyForm = (): RecipeForm => ({
        name: '',
        category_id: null,
        cook_time_minutes: null,
        cuisine_id: null,
        difficulty: null,
        instructions: null,
        nutrition: null,
        prep_time_minutes: null,
        recipe_collection_id: null,
        servings: null,
        source: null,
        time_of_day: null,
        ingredients: [],
        dietary_tag_ids: [],
        tool_ids: [],
        image: null,
        steps: [],
        steps_mode: 'structured',
        kcal: null,
        sections: [],
    });

    const form = reactive<RecipeForm>(emptyForm());

    function hydrateForm(source: Recipe) {
        // Use the existing recipe_ingredient_id as the client_id so already-
        // saved steps that reference real ingredient UUIDs round-trip cleanly:
        // unchanged ingredients keep their ids; the server resolves either
        // form (a fresh client_id from the editor or an existing UUID) on save.
        const ingredients = source.ingredients.map((i) => ({
            stock_item_id: i.stock_item_id,
            quantity: i.quantity,
            unit: i.unit,
            notes: i.notes,
            client_id: i.recipe_ingredient_id,
            // C-4 Chunk 10 — re-use the existing section UUID as client_id
            // (see hydrate below) so round-tripping keeps the reference.
            section_client_id: i.section_id,
        }));
        const sections: SectionForm[] = (source.sections ?? []).map((s) => ({
            client_id: s.section_id,
            sequence: s.sequence,
            name: s.name,
        }));
        const steps: EditableRecipeStep[] = (source.steps ?? []).map((s) => ({
            client_id: s.step_id,
            parent_client_id: s.parent_step_id,
            sequence: s.sequence,
            text: s.text,
            hint: s.hint,
            ingredient_client_ids: [...s.ingredient_ids],
            tool_ids: [...s.tool_ids],
        }));
        Object.assign(form, {
            name: source.name,
            category_id: source.category_id,
            cook_time_minutes: source.cook_time_minutes,
            cuisine_id: source.cuisine_id,
            difficulty: source.difficulty,
            instructions: source.instructions,
            nutrition: source.nutrition,
            prep_time_minutes: source.prep_time_minutes,
            recipe_collection_id: source.recipe_collection_id,
            servings: source.servings,
            source: source.source,
            time_of_day: source.time_of_day,
            ingredients,
            dietary_tag_ids: [...(source.dietary_tag_ids ?? [])],
            tool_ids: [...(source.tool_ids ?? [])],
            image: null,
            steps,
            // Default to structured when the recipe already has steps;
            // otherwise stay on the freeform path so existing imports don't
            // surprise the user with an empty editor.
            steps_mode: source.has_structured_steps ? 'structured' : 'freeform',
            kcal: source.kcal,
            sections,
        });
        imageDirty.value = false;
        isDirty.value = false;
    }

    function markDirty() {
        isDirty.value = true;
    }

    function onStepsChange(next: EditableRecipeStep[]) {
        form.steps = next;
        markDirty();
    }

    // Ingredient + tool option lists fed to RecipeStepsEditor. Ingredient
    // options use the form's per-row client_id as the value so a step can
    // reference an ingredient before the server has assigned it a real id.
    const stepIngredientOptions = computed<IngredientOption[]>(() =>
        form.ingredients
            .map((i, idx) => {
                const stockItem = stockItems.value.find((s) => s.stock_item_id === i.stock_item_id);
                return {
                    value: i.client_id ?? String(idx),
                    label: stockItem?.name ?? '(unknown ingredient)',
                };
            }),
    );
    const stepToolOptions = computed<ToolOption[]>(() =>
        tools.value.map((t) => ({ value: t.tool_id, label: t.name })),
    );

    // â”€â”€ Stock-level helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    function levelNameFor(stockItemId: string): string | null {
        const item = stockItems.value.find((s) => s.stock_item_id === stockItemId);
        if (!item) return null;
        const level = stockLevels.value.find((l) => l.stock_level_id === item.stock_level_id);
        return level?.name ?? null;
    }
    function levelColourFor(stockItemId: string): string | null {
        const name = levelNameFor(stockItemId);
        return name ? getStockLevelColour(name) : null;
    }
    // Per-ingredient "missing" badge in the live editor. Reads the stock item's
    // server-derived `is_out_of_stock` boolean (Â§3.1) rather than matching a
    // level name; untracked / unknown items count as missing.
    function isMissingItem(stockItemId: string): boolean {
        if (!stockItemId) return true;
        const item = stockItems.value.find((s) => s.stock_item_id === stockItemId);
        return !item || Boolean(item.is_out_of_stock);
    }
    // Cookability is server-owned (Â§3.2): the loaded recipe carries `cookable`
    // and each ingredient carries `is_missing`. We read those off the saved
    // recipe rather than recomputing from stock data â€” the summary reflects the
    // persisted recipe and refreshes after each save (`loadRecipe`).
    const missingIngredients = computed(() => {
        const r = recipe.value;
        if (!r) return [];
        return r.ingredients
            .filter((i) => i.is_missing)
            // Dedupe â€” an ingredient on multiple rows is still one shopping line.
            .filter((i, idx, arr) => arr.findIndex((x) => x.stock_item_id === i.stock_item_id) === idx);
    });

    const trackedCount = computed(
        () => new Set((recipe.value?.ingredients ?? []).map((i) => i.stock_item_id).filter(Boolean)).size,
    );
    const inStockCount = computed(
        () =>
            new Set(
                (recipe.value?.ingredients ?? [])
                    .filter((i) => !i.is_missing)
                    .map((i) => i.stock_item_id)
                    .filter(Boolean),
            ).size,
    );
    const cookableNow = computed(() => recipe.value?.cookable ?? false);

    // â”€â”€ Picker (autocomplete + inline create) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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
        // immediately count as "missing" â€” the user hasn't told us otherwise
        // and slotting it straight into a recipe implies they have it.
        const wellStocked = stockLevels.value[0];
        if (!wellStocked) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'No stock levels configured â€” cannot create stock item.',
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
            // C-4 Chunk 6 — every ingredient row needs a stable client_id so
            // a step can highlight it before the server assigns a real UUID.
            client_id: newClientId(),
            section_client_id: null,
        });
        markDirty();
    }

    // C-4 Chunk 10 — section helpers.
    function addSection() {
        form.sections.push({
            client_id: newClientId(),
            sequence: form.sections.length,
            name: '',
        });
        markDirty();
    }
    function removeSection(idx: number) {
        const removed = form.sections[idx];
        if (!removed) return;
        form.sections.splice(idx, 1);
        // Resequence so server-side sort stays tight.
        form.sections.forEach((s, i) => { s.sequence = i; });
        // Detach any ingredients that pointed at it.
        for (const ing of form.ingredients) {
            if (ing.section_client_id === removed.client_id) {
                ing.section_client_id = null;
            }
        }
        markDirty();
    }
    function moveSection(idx: number, delta: -1 | 1) {
        const target = idx + delta;
        if (target < 0 || target >= form.sections.length) return;
        const a = form.sections[idx];
        const b = form.sections[target];
        if (!a || !b) return;
        form.sections[idx] = b;
        form.sections[target] = a;
        form.sections.forEach((s, i) => { s.sequence = i; });
        markDirty();
    }
    const sectionOptions = computed(() => [
        { value: null, label: '(Main)' },
        ...form.sections.map((s) => ({
            value: s.client_id,
            label: s.name.trim() || '(Unnamed section)',
        })),
    ]);
    function removeIngredient(idx: number) {
        const removed = form.ingredients[idx];
        form.ingredients.splice(idx, 1);
        // Drop any step references to the removed ingredient so the request
        // stays consistent (the server would silently drop them too, but
        // keeping the editor honest avoids "ghost" highlights on re-edit).
        if (removed?.client_id) {
            const stale = removed.client_id;
            form.steps = form.steps.map((s) => ({
                ...s,
                ingredient_client_ids: s.ingredient_client_ids.filter((c) => c !== stale),
            }));
        }
        markDirty();
    }

    // â”€â”€ Collection + vocabulary options â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    const collectionOptions = computed(() =>
        recipeCollections.value.map((c) => ({
            label: c.name,
            value: c.recipe_collection_id,
        })),
    );
    const cuisineOptions = computed(() =>
        cuisines.value.map((c) => ({ label: c.name, value: c.cuisine_id })),
    );
    const categoryOptions = computed(() =>
        categories.value.map((c) => ({ label: c.name, value: c.category_id })),
    );
    // Dietary tag options, grouping-prefixed so a flat multiselect still reads
    // as clustered ("Allergen-free: Gluten-free").
    const dietaryTagOptions = computed(() =>
        dietaryTags.value.map((t) => ({ label: `${t.category}: ${t.name}`, value: t.dietary_tag_id })),
    );
    const toolOptions = computed(() =>
        tools.value.map((t) => ({ label: t.name, value: t.tool_id })),
    );

    // What the image field shows: a freshly-picked data URL while
    // editing, otherwise the saved image via the endpoint (cache-busted),
    // else nothing.
    // C-cross Chunk 5 — `showRecipeImages` gates the saved-preview
    // branch only. A freshly-picked image still renders so the user can
    // see what they're about to save; the editor itself (pick/clear)
    // stays fully usable regardless.
    const imagePreviewUrl = computed(() => {
        if (imageDirty.value) return form.image;
        if (showRecipeImages.value && recipe.value?.has_image) {
            return recipeImageUrl(recipe.value.recipe_id, imageVersion.value);
        }
        return null;
    });
    function onPickImage(dataUrl: string) {
        form.image = dataUrl;
        imageDirty.value = true;
        markDirty();
    }
    function onClearImage() {
        form.image = null;
        imageDirty.value = true;
        markDirty();
    }

    // â”€â”€ Save / load â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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

        // L289 — never silently drop a half-filled ingredient row. Block the
        // save and point the user at it.
        if (form.ingredients.some((i) => !i.stock_item_id)) {
            $q.notify({
                type: 'warning',
                position: 'bottom-right',
                message: 'Every ingredient needs a stock item.',
                caption: 'Pick an item for each row, or remove the empty one.',
            });
            return;
        }
        if (!form.name.trim()) {
            nameError.value = 'Give the recipe a name.';
            return;
        }

        saving.value = true;
        try {
            const src = recipe.value;
            // L286 — true PATCH semantics: only send scalar fields that
            // actually changed, so re-saving an unchanged name can't trip the
            // name-uniqueness check. Arrays are always sent (replace semantics).
            // C-4 Chunk 10 — sections always go with the ingredient
            // replace so a renamed section keeps its rows. Empty array =
            // clear all sections; rows fall back to the implicit main
            // group via ON DELETE SET NULL on the server.
            const command: UpdateRecipeCommand = {
                recipe_id: src.recipe_id,
                ingredients: form.ingredients,
                dietary_tag_ids: form.dietary_tag_ids,
                tool_ids: form.tool_ids,
                sections: form.sections.map((s, i) => ({
                    client_id: s.client_id,
                    sequence: i,
                    name: (s.name || '').trim() || 'Untitled section',
                })),
            };
            // Only touch the image when the user actually changed it.
            const didImageChange = imageDirty.value;
            if (didImageChange) command.image = form.image;
            if (form.name !== src.name) command.name = form.name;
            if (form.category_id !== src.category_id) command.category_id = form.category_id;
            if (form.cuisine_id !== src.cuisine_id) command.cuisine_id = form.cuisine_id;
            if (form.cook_time_minutes !== src.cook_time_minutes) command.cook_time_minutes = toIntOrNull(form.cook_time_minutes);
            if (form.difficulty !== src.difficulty) command.difficulty = form.difficulty;
            if (form.instructions !== src.instructions) command.instructions = form.instructions;
            // C-4 Chunk 6 — always send `steps` so the server knows whether
            // this save replaces the structured set or clears it (freeform
            // mode sends []). Map the editor's EditableStep shape into the
            // wire RecipeStepCommand.
            const stepsToSend: RecipeStepCommand[] =
                form.steps_mode === 'structured'
                    ? form.steps.map((s) => ({
                          client_id: s.client_id,
                          parent_client_id: s.parent_client_id,
                          sequence: s.sequence,
                          text: s.text,
                          hint: s.hint,
                          ingredient_client_ids: [...s.ingredient_client_ids],
                          tool_ids: [...s.tool_ids],
                      }))
                    : [];
            command.steps = stepsToSend;
            if (form.nutrition !== src.nutrition) command.nutrition = form.nutrition;
            if (form.prep_time_minutes !== src.prep_time_minutes) command.prep_time_minutes = toIntOrNull(form.prep_time_minutes);
            if (form.recipe_collection_id !== src.recipe_collection_id) command.recipe_collection_id = form.recipe_collection_id;
            if (form.servings !== src.servings) command.servings = toIntOrNull(form.servings);
            if (form.source !== src.source) command.source = form.source;
            if (form.time_of_day !== src.time_of_day) command.time_of_day = form.time_of_day;
            if (form.kcal !== src.kcal) command.kcal = toIntOrNull(form.kcal);
            await recipeStore.updateRecipeAsync(command);
            await loadRecipe();
            // Bust the <img> cache so a changed/cleared image shows immediately.
            if (didImageChange) imageVersion.value++;
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

    // â”€â”€ Sidebar actions â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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

    // L297/L299/L309 — guard cook-mode entry. A confirm is shown when there
    // are unsaved edits OR the recipe isn't cookable now. The guard uses a
    // real dialog with an explicit Cancel; clicking outside / Esc just closes
    // it (never navigates). Clean entry (saved + cookable) goes straight in.
    function goToCookMode() {
        cookGuardOpen.value = false;
        void router.push(`/recipes/${recipeId.value}/cook`);
    }
    function onStartCookMode() {
        if (!recipe.value) return;
        if (isDirty.value || !cookableNow.value) {
            cookGuardOpen.value = true;
            return;
        }
        goToCookMode();
    }
    async function onGuardSaveAndCook() {
        await onSave();
        // Don't proceed if the save surfaced a validation error (still dirty
        // or a name error means it didn't persist) — L297 "block when the
        // most recent save errored".
        if (!isDirty.value && !nameError.value) goToCookMode();
    }

    // C-7 Chunk 1 — `onAddRowToList` retired; the per-row
    // AddToListButton owns the click now.

    // Add-all-missing â†’ opens a small target-list picker dialog.
    const targetListOpen = ref(false);
    const targetListId = ref<string | null>(null);
    const addingMissing = ref(false);

    const activeListOptions = computed(() =>
        shoppingListStore.summaries
            .filter((s) => s.status !== 'done')
            .map((s) => ({
                label: s.name,
                value: s.shopping_list_id,
            })),
    );

    function onAddMissingToList() {
        if (missingIngredients.value.length === 0) return;
        targetListId.value =
            shoppingListStore.quickAddTargetListId ?? activeListOptions.value[0]?.value ?? null;
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

    // â”€â”€ Substitutes â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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

    // â”€â”€ Import from URL â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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
            // Confirm overwrite â€” the imported result might wipe out
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
            // Importer resolves scraped names to vocab ids when it can; null
            // id (no match) leaves the select empty for the user to pick.
            form.cuisine_id = imported.cuisine_id;
            form.category_id = imported.category_id;
            form.difficulty = imported.difficulty;
            form.servings = imported.servings;
            form.prep_time_minutes = imported.prep_time_minutes;
            form.cook_time_minutes = imported.cook_time_minutes;
            // C-4 Chunk 7 — `source` is its own field now; stop appending
            // "Source: <url>" to the instructions blob.
            form.instructions = imported.instructions || null;
            form.source = imported.source_url || null;
            form.nutrition = imported.nutrition;
            form.ingredients = imported.ingredients.map((i) => ({
                stock_item_id: i.stock_item_id ?? '',
                quantity: i.quantity,
                unit: i.unit,
                notes:
                    i.stock_item_id
                        ? i.notes ?? null
                        : `Raw: ${i.raw_text}` + (i.notes ? ` (${i.notes})` : ''),
                client_id: newClientId(),
            }));
            // C-4 Chunk 6 — adopt parsed structured steps when the source
            // shipped HowToStep / HowToSection. Empty list ⇒ source only had a
            // string, freeform mode stays active.
            if (imported.steps && imported.steps.length > 0) {
                form.steps = imported.steps.map((s) => ({
                    client_id: s.client_id,
                    parent_client_id: s.parent_client_id,
                    sequence: s.sequence,
                    text: s.text,
                    hint: s.hint,
                    ingredient_client_ids: [],
                    tool_ids: [],
                }));
                form.steps_mode = 'structured';
            } else {
                form.steps = [];
                form.steps_mode = 'freeform';
            }
            markDirty();
            importOpen.value = false;
            // C-4 Chunk 7 — distinct toast when we fell back to scraping
            // raw page text (no JSON-LD found). The user knows to clean
            // up rather than assume the structured fields are accurate.
            if (imported.is_degraded) {
                $q.notify({
                    type: 'warning',
                    position: 'bottom-right',
                    timeout: 6000,
                    message: 'Couldn’t auto-structure that page',
                    caption:
                        'Pulled the page text into Instructions and saved the URL. ' +
                        'Review and edit to clean it up.',
                });
            } else {
                $q.notify({
                    type: 'positive',
                    position: 'bottom-right',
                    message:
                        `Imported "${imported.name}". ` +
                        `${imported.ingredients.filter((i) => !i.stock_item_id).length} ingredients need a stock-item match.`,
                });
            }
        } catch (err) {
            importError.value =
                'Could not import. The URL might not publish structured recipe data.';
             
            console.warn('Import failed', err);
        } finally {
            importing.value = false;
        }
    }

    // â”€â”€ Meals-on-hand controls â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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

    // L304 — "Mark cooked" = the one-tap "I made it once": logs a single
    // cook (bumps the pool + last-cooked date). "Log cook…" stays for N.
    async function onMarkCooked() {
        if (!recipe.value) return;
        adjusting.value = true;
        try {
            await recipeStore.cookAsync(recipe.value.recipe_id, 1);
            await loadRecipe();
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: 'Marked as cooked.',
            });
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not mark cooked.',
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

    // ── C-4 Chunk 8 — versions ──────────────────────────────────────────
    const versionSiblings = computed(() => recipe.value?.version_siblings ?? []);
    const newVersionLoading = ref(false);

    async function onNewVersion() {
        if (!recipe.value) return;
        newVersionLoading.value = true;
        try {
            const created = await recipeApi.createNewVersionAsync(recipe.value.recipe_id);
            // CreatedResponse carries either `recipe_id` (created() body) or
            // `id` (Location-style). Cover both.
            const newId =
                (created as Record<string, unknown>).recipe_id as string | undefined
                ?? created.id;
            await recipeStore.getRecipesAsync();
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: 'New version created.',
                caption: 'Both versions are equal peers — pick either when scheduling.',
            });
            if (newId) void router.push(`/recipes/${newId}`);
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not create version.',
                caption: describeApiError(err) || '',
            });
        } finally {
            newVersionLoading.value = false;
        }
    }

    function onJumpToSibling(recipeId: string) {
        void router.push(`/recipes/${recipeId}`);
    }

    function formatLastMade(isoDate: string): string {
        try {
            const d = new Date(isoDate);
            if (Number.isNaN(d.getTime())) return 'recently';
            return d.toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' });
        } catch {
            return 'recently';
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
            void router.push('/cookbook');
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
            }).onOk(() => { void router.push('/cookbook'); });
            return;
        }
        void router.push('/cookbook');
    }

    // â”€â”€ Mount â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    onMounted(async () => {
        await Promise.all([
            recipeStore.getRecipeCollectionsAsync(),
            stockItemStore.getStockItemsAsync(),
            stockLevelStore.getStockLevelsAsync(),
            shoppingListStore.refreshAsync(),
            recipeVocabStore.getAllAsync(),
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
        font-size: 1.15rem;
        font-weight: 600;
    }
    .ingredient-row {
        align-items: flex-start;
    }
    /* L292 — tint the whole row when its ingredient is missing, instead of
       stacking a second chip. */
    .ingredient-row--missing {
        background: color-mix(in srgb, var(--q-negative) 9%, transparent);
    }
    /* L308 — keep the action toolbar reachable at the top on every width. */
    .recipe-toolbar {
        position: sticky;
        top: 0;
        z-index: 2;
        background: var(--surface-page);
        padding: 6px 0;
    }
</style>
