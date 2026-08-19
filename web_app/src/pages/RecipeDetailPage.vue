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
            <!-- ── Header ──────────────────────────────────────────────
                 Feedback 2026-08-19: one toolbar, not three rows. The
                 breadcrumb is gone (the back arrow already says where you
                 came from), the name sits inline beside that arrow (matching
                 the stock-item detail header), and every action lives in the
                 shared `PageToolbar` actions slot — including the three that
                 used to hide behind an ellipsis menu, because an extra click
                 to reach Delete / New version / Favourite is pure cost.
                 Phones drop the labels to icons on the same `lt.sm` gate the
                 cookbook and stock overview use; the label survives as the
                 tooltip. -->
            <PageToolbar :title="form.name || 'Untitled recipe'" back-to="/cookbook">
                <template #actions>
                    <BaseButton
                        variant="primary"
                        :icon="ICONS.restaurant_menu"
                        :label="compactToolbar ? undefined : 'Cook mode'"
                        aria-label="Cook mode"
                        @click="onStartCookMode"
                    >
                        <q-tooltip v-if="compactToolbar">Cook mode</q-tooltip>
                    </BaseButton>
                    <BaseButton
                        v-if="!editing"
                        variant="secondary"
                        :icon="ICONS.edit"
                        :label="compactToolbar ? undefined : 'Edit'"
                        aria-label="Edit"
                        @click="editing = true"
                    >
                        <q-tooltip v-if="compactToolbar">Edit</q-tooltip>
                    </BaseButton>
                    <BaseButton
                        v-if="editing"
                        variant="secondary"
                        :icon="ICONS.save"
                        :label="compactToolbar ? undefined : 'Save'"
                        aria-label="Save"
                        :disable="!isDirty"
                        :loading="saving"
                        @click="onSave"
                    >
                        <q-tooltip v-if="compactToolbar">Save</q-tooltip>
                    </BaseButton>
                    <BaseButton
                        v-if="editing"
                        variant="ghost"
                        :icon="ICONS.check"
                        :label="compactToolbar ? undefined : 'Done'"
                        aria-label="Done"
                        @click="editing = false"
                    >
                        <q-tooltip v-if="compactToolbar">Done</q-tooltip>
                    </BaseButton>
                    <!-- Feedback 2026-08-19: import is a toolbar button here
                         too, the way it is on the cookbook overview — it was
                         a row buried in a sidebar card. -->
                    <BaseButton
                        variant="ghost"
                        :icon="ICONS.content_paste"
                        :label="compactToolbar ? undefined : 'Import'"
                        aria-label="Import a recipe"
                        @click="onImportFromUrl"
                    >
                        <q-tooltip>
                            {{ compactToolbar ? 'Import a recipe — ' : '' }}paste a
                            recipe over this one
                        </q-tooltip>
                    </BaseButton>
                    <BaseButton
                        variant="ghost"
                        :icon="recipe.is_favourite ? 'favorite' : 'favorite_border'"
                        :label="compactToolbar ? undefined : (recipe.is_favourite ? 'Favourited' : 'Favourite')"
                        :aria-label="recipe.is_favourite ? 'Remove from favourites' : 'Add to favourites'"
                        :class="{ 'text-negative': recipe.is_favourite }"
                        @click="onToggleFavourite"
                    >
                        <q-tooltip v-if="compactToolbar">
                            {{ recipe.is_favourite ? 'Favourited' : 'Favourite' }}
                        </q-tooltip>
                    </BaseButton>
                    <!-- copies the recipe into a sibling version (same
                         `version_group_id`) and routes into it. -->
                    <BaseButton
                        variant="ghost"
                        :icon="ICONS.content_copy"
                        :label="compactToolbar ? undefined : 'New version'"
                        aria-label="New version"
                        :loading="newVersionLoading"
                        @click="onNewVersion"
                    >
                        <q-tooltip v-if="compactToolbar">New version</q-tooltip>
                    </BaseButton>
                    <BaseButton
                        variant="ghost"
                        :icon="ICONS.print"
                        :label="compactToolbar ? undefined : 'Print'"
                        aria-label="Print"
                        @click="onPrint"
                    >
                        <q-tooltip v-if="compactToolbar">Print</q-tooltip>
                    </BaseButton>
                    <BaseButton
                        variant="danger-ghost"
                        :icon="ICONS.delete"
                        :label="compactToolbar ? undefined : 'Delete'"
                        aria-label="Delete recipe"
                        @click="onDelete"
                    >
                        <q-tooltip v-if="compactToolbar">Delete recipe</q-tooltip>
                    </BaseButton>
                    <!-- Temporary hatch to the redesigned page so the two can
                         be compared on the same recipe. One of them gets
                         deleted — see FU-683. -->
                    <BaseButton
                        variant="subtle"
                        :icon="ICONS.auto_awesome"
                        :label="compactToolbar ? undefined : 'New layout'"
                        aria-label="Try the new layout"
                        :to="`/cookbook/${recipeId}/new`"
                    >
                        <q-tooltip>Try the new layout for this recipe</q-tooltip>
                    </BaseButton>
                </template>
            </PageToolbar>

            <!-- L289 — the name is its own clearly-editable field (matching
                 the stock-item screen), not a heading masquerading as one. -->
            <q-input
                v-if="editing"
                v-model="form.name"
                outlined
                dense
                label="Recipe name"
                class="q-mb-md recipe-name-input"
                :error="!!nameError"
                :error-message="nameError ?? undefined"
                @update:model-value="onNameInput"
            />

            <div class="row q-col-gutter-lg">
                <!-- â”€â”€ Main editor column â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ -->
                <div class="col-12 col-md-8">
                    <!-- ── DR-11 (D-015) read view ─────────────────────────
                         Default reading surface. Renders the same `form` model
                         the editor writes, so it can't drift; the Edit toggle
                         swaps to the cards below. "Available meals" (a status +
                         stepper action) stays visible in both modes. -->
                    <div v-if="!editing" class="recipe-read">
                        <q-img
                            v-if="imagePreviewUrl"
                            :src="imagePreviewUrl"
                            :ratio="16 / 9"
                            class="recipe-read__hero q-mb-md"
                        />
                        <div class="row items-center q-gutter-sm q-mb-md">
                            <q-chip v-if="readCuisine" dense square :icon="ICONS.restaurant_menu">{{ readCuisine }}</q-chip>
                            <q-chip v-if="readCategory" dense square>{{ readCategory }}</q-chip>
                            <q-chip v-if="form.time_of_day" dense square :icon="ICONS.schedule">{{ form.time_of_day }}</q-chip>
                            <q-chip v-if="form.difficulty" dense square :icon="ICONS.trending_up">{{ form.difficulty }}</q-chip>
                            <q-chip v-if="form.servings" dense square :icon="ICONS.restaurant">
                                {{ form.servings }} {{ form.servings === 1 ? 'serving' : 'servings' }}
                            </q-chip>
                            <q-chip v-if="readTimeLabel" dense square :icon="ICONS.timer">{{ readTimeLabel }}</q-chip>
                            <q-chip v-if="isSimple && form.kcal" dense square :icon="ICONS.monitor_heart">{{ form.kcal }} kcal</q-chip>
                            <!-- FU-635 — in complex mode the headline number
                                 is the rollup, not the typed field. -->
                            <q-chip
                                v-else-if="isComplex && recipe?.nutrition?.kcal"
                                dense
                                square
                                :icon="ICONS.monitor_heart"
                            >
                                {{ Math.round(recipe.nutrition.kcal) }} kcal
                            </q-chip>
                        </div>
                        <div v-if="readTags.length > 0 || readTools.length > 0" class="q-mb-md">
                            <q-chip v-for="t in readTags" :key="`tag-${t}`" dense outline size="sm">{{ t }}</q-chip>
                            <q-chip v-for="t in readTools" :key="`tool-${t}`" dense outline size="sm" :icon="ICONS.restaurant">{{ t }}</q-chip>
                        </div>

                        <q-card flat bordered class="q-mb-md">
                            <q-card-section>
                                <div class="text-subtitle1 q-mb-sm">Ingredients</div>
                                <div v-if="form.ingredients.length === 0" class="dora-text-muted text-caption">
                                    No ingredients listed.
                                </div>
                                <template v-for="(grp, gi) in readIngredientGroups" :key="`ig-${gi}`">
                                    <div v-if="grp.name" class="text-caption text-weight-medium dora-text-secondary q-mt-sm">
                                        {{ grp.name }}
                                    </div>
                                    <ul class="recipe-read__ings">
                                        <li
                                            v-for="(ing, ii) in grp.rows"
                                            :key="`ig-${gi}-${ii}`"
                                            :class="{ 'recipe-read__ing--optional': ing.is_optional }"
                                        >
                                            <span v-if="ing.quantity" class="text-weight-medium">
                                                {{ ing.quantity }}{{ ing.unit ? ' ' + ing.unit : '' }}
                                            </span>
                                            {{ ingredientDisplayName(ing) }}
                                            <span v-if="ing.notes" class="dora-text-muted">— {{ ing.notes }}</span>
                                            <span v-if="ing.is_optional" class="dora-text-muted text-caption q-ml-xs">(optional)</span>
                                            <q-chip
                                                v-if="ing.stock_item_id && isMissingItem(ing.stock_item_id)"
                                                dense
                                                square
                                                size="sm"
                                                color="negative"
                                                text-color="white"
                                                class="q-ml-xs"
                                            >
                                                Missing
                                            </q-chip>
                                            <!-- Feedback 2026-08-17 — which ingredient
                                                 is the expiring one. Sits beside Missing
                                                 rather than replacing it: an item can be
                                                 in stock and about to go off, which is
                                                 exactly the case worth cooking. -->
                                            <!-- D-002: `dark` ink, not white. Measured against
                                                 every theme's semantic tokens, white on the
                                                 amber chip lands at 1.7–3.0:1 (the floor is
                                                 4.5); `dark` clears it at 5.5–9.5. The Missing
                                                 chip above still uses white — that's the
                                                 app-wide sweep in FU-671, not a difference
                                                 that means anything. -->
                                            <q-chip
                                                v-if="ing.expiringChip"
                                                dense
                                                square
                                                size="sm"
                                                :color="ing.expiringChip.colour"
                                                text-color="dark"
                                                :icon="ing.expiringChip.icon"
                                                class="q-ml-xs"
                                            >
                                                {{ ing.expiringChip.label }}
                                                <q-tooltip>{{ ing.expiringChip.tooltip }}</q-tooltip>
                                            </q-chip>
                                        </li>
                                    </ul>
                                </template>
                            </q-card-section>
                        </q-card>

                        <q-card flat bordered class="q-mb-md">
                            <q-card-section>
                                <div class="text-subtitle1 q-mb-sm">Instructions</div>
                                <ol
                                    v-if="form.steps_mode === 'structured' && readSteps.length > 0"
                                    class="recipe-read__steps"
                                >
                                    <li v-for="s in readSteps" :key="s.client_id">
                                        {{ s.text }}
                                        <div v-if="s.hint" class="text-caption dora-text-muted">{{ s.hint }}</div>
                                    </li>
                                </ol>
                                <ol
                                    v-else-if="readFreeformLines.length > 0"
                                    class="recipe-read__steps"
                                >
                                    <li v-for="(line, li) in readFreeformLines" :key="`step-${li}`">{{ line }}</li>
                                </ol>
                                <div
                                    v-else-if="form.steps_mode === 'image' && form.step_images.length > 0"
                                    class="column q-gutter-sm"
                                >
                                    <img
                                        v-for="img in form.step_images"
                                        :key="img.client_id"
                                        :src="img.preview_url"
                                        alt="Recipe step"
                                        class="recipe-read__stepimg"
                                    />
                                </div>
                                <div v-else class="dora-text-muted text-caption">No instructions yet.</div>
                            </q-card-section>
                        </q-card>

                        <q-card v-if="form.source" flat bordered class="q-mb-md">
                            <q-card-section class="row items-center q-gutter-sm no-wrap">
                                <q-icon :name="ICONS.link" class="dora-text-muted" />
                                <a
                                    v-if="form.source.startsWith('http')"
                                    :href="form.source"
                                    target="_blank"
                                    rel="noopener"
                                    class="text-primary ellipsis"
                                >{{ form.source }}</a>
                                <span v-else class="ellipsis">{{ form.source }}</span>
                            </q-card-section>
                        </q-card>

                        <q-card v-if="form.notes" flat bordered class="q-mb-md">
                            <q-card-section>
                                <div class="text-caption dora-text-muted q-mb-xs">Notes</div>
                                <div class="recipe-read__notes">{{ form.notes }}</div>
                            </q-card-section>
                        </q-card>
                    </div>

                    <!-- recipe image (FU-039). -->
                    <q-card v-if="editing" flat bordered class="q-mb-md">
                        <q-card-section>
                            <ImageUploadField
                                :preview-url="imagePreviewUrl"
                                :can-clear="hasRemovableImage"
                                :name="form.name"
                                alt="Recipe image"
                                @pick="onPickImage"
                                @clear="onClearImage"
                            />
                        </q-card-section>
                    </q-card>

                    <q-card v-if="editing" flat bordered class="q-mb-md">
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
                                    :options="timeOfDayOptions"
                                    clearable
                                    class="col-6 col-sm-3"
                                    @update:model-value="markDirty"
                                />
                                <q-select
                                    v-model="form.difficulty"
                                    outlined
                                    dense
                                    label="Difficulty"
                                    :options="difficultyOptions"
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
                                <!-- simple nutrition (kcal). Hidden when
                                     nutrition is `off`, and when it's
                                     `complex` — there the figure is rolled up
                                     from the ingredients' linked foods, and a
                                     typed number beside it would be a second
                                     answer nobody could reconcile (R-029). -->
                                <q-input
                                    v-if="isSimple"
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
                    <q-card v-if="recipe && batchEnabled" flat bordered class="q-mb-md">
                        <q-card-section class="row items-center q-gutter-md no-wrap">
                            <div>
                                <div class="text-subtitle1">Available meals</div>
                                <div class="text-caption dora-text-muted">
                                    <!-- DR-11 (FU-578 #11): "cooked" implied a cook event
                                         and clashed with "Last cooked: Never" — the pool is
                                         raisable via the stepper without ever cooking. "on
                                         hand" matches the card title + the tooltip's "in
                                         your pool" wording, so the two widgets agree. -->
                                    {{ recipe.unallocated_meals }} unallocated
                                    of {{ recipe.available_meals }} on hand
                                    <q-icon :name="ICONS.help_outline" size="14px" class="q-ml-xs">
                                        <q-tooltip>
                                            Portions of this recipe already in your
                                            pool but not yet earmarked for any
                                            meal-plan slot. Cook mode adds to the
                                            pool; planning a meal subtracts from it.
                                        </q-tooltip>
                                    </q-icon>
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
                    <q-card v-if="editing" flat bordered class="q-mb-md">
                        <q-card-section class="row items-center q-pb-sm">
                            <div class="text-subtitle1">
                                Sections
                                <span class="text-caption dora-text-muted q-ml-sm">
                                    {{ form.sections.length }}
                                </span>
                            </div>
                            <q-space />
                            <BaseButton
                                variant="ghost"
                                dense
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
                                        <BaseButton
                                            variant="icon"
                                            icon="arrow_upward"
                                            :disable="sIdx === 0"
                                            @click="moveSection(sIdx, -1)"
                                        />
                                        <BaseButton
                                            variant="icon"
                                            icon="arrow_downward"
                                            :disable="sIdx === form.sections.length - 1"
                                            @click="moveSection(sIdx, 1)"
                                        />
                                        <BaseButton
                                            variant="danger-icon"
                                            :icon="ICONS.delete"
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
                    <q-card v-if="editing" flat bordered class="q-mb-md">
                        <q-card-section class="row items-center q-pb-sm">
                            <div class="text-subtitle1">
                                Ingredients
                                <span class="text-caption dora-text-muted q-ml-sm">
                                    {{ form.ingredients.length }}
                                </span>
                            </div>
                            <q-space />
                            <BaseButton
                                variant="ghost"
                                dense
                                :icon="ICONS.add"
                                label="Add ingredient"
                                @click="addIngredient"
                            />
                        </q-card-section>
                        <q-separator />
                        <q-list separator>
                            <q-item
                                v-for="(ing, idx) in form.ingredients"
                                :key="ing.client_id ?? idx"
                                class="ingredient-row"
                                :class="{
                                    'ingredient-row--missing': ing.stock_item_id && isMissingItem(ing.stock_item_id),
                                    ...ingredientDnd.bind(ing).rowClass,
                                }"
                                v-bind="ingredientDnd.bind(ing).rowProps"
                            >
                                <!-- drag handle via
                                     `useDragDropList`. Only this icon is
                                     draggable; the row body keeps default
                                     cursor so the selects/inputs stay
                                     normally interactive. Dropping onto
                                     another row both reorders AND copies
                                     the target's section_client_id, so
                                     cross-section reassignment is a
                                     single gesture. -->
                                <q-item-section side style="min-width: 28px; padding-right: 4px">
                                    <div
                                        class="dora-dnd-handle dora-text-muted"
                                        aria-label="Drag to reorder or move section"
                                        v-bind="ingredientDnd.bind(ing).handleProps"
                                    >
                                        <q-icon :name="ICONS.drag_indicator" />
                                        <q-tooltip>Drag to reorder; drop onto a row in another section to move it there</q-tooltip>
                                    </div>
                                </q-item-section>
                                <q-item-section style="min-width: 240px">
                                    <!-- Stock-item autocomplete with inline create. The
                                         picker shows existing tracked items, and offers
                                         "Create '<typed>'" or "Use as free-text" (FU-506)
                                         when there's no exact match. -->
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
                                        :label="ing.raw_text && !ing.stock_item_id ? 'Free-text ingredient' : 'Stock item'"
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
                                            <!-- FU-506 — free-text ingredient path.
                                                 Saves the typed text as raw_text with
                                                 no linked pantry item. Cookability
                                                 stays "unknown" while any required
                                                 ingredient is unlinked; user can link
                                                 later from the same picker. -->
                                            <q-item
                                                clickable
                                                @click="useAsRawText(idx, ingredientFilter)"
                                            >
                                                <q-item-section avatar>
                                                    <q-icon :name="ICONS.edit" color="secondary" />
                                                </q-item-section>
                                                <q-item-section class="dora-text-secondary">
                                                    Use "{{ ingredientFilter }}" as free text (no pantry link)
                                                </q-item-section>
                                            </q-item>
                                        </template>
                                    </q-select>
                                    <!-- FU-506 — surface the free-text label so an
                                         unlinked row isn't just a blank picker. -->
                                    <div
                                        v-if="ing.raw_text && !ing.stock_item_id"
                                        class="text-caption dora-text-muted q-mt-xs ellipsis"
                                    >
                                        "{{ ing.raw_text }}"
                                    </div>
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

                                <!-- section picker, only when
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

                                <!-- Cookbook revision §1.9 — optional flag.
                                     Excluded from cookability + missing
                                     count + shopping-list picker defaults. -->
                                <q-item-section side style="max-width: 110px">
                                    <q-checkbox
                                        v-model="ing.is_optional"
                                        dense
                                        label="Optional"
                                        @update:model-value="markDirty"
                                    >
                                        <q-tooltip>
                                            Optional ingredients don't affect whether the recipe is cookable.
                                        </q-tooltip>
                                    </q-checkbox>
                                </q-item-section>

                                <q-item-section side top>
                                    <div class="row q-gutter-xs items-center">
                                        <!-- unified AddToListButton.
                                             State-aware + toggle behaviour;
                                             replaces the row's hand-rolled
                                             "add to primary" path. -->
                                        <AddToListButton
                                            v-if="ing.stock_item_id"
                                            variant="row"
                                            :stock-item-id="ing.stock_item_id"
                                        />
                                        <BaseButton
                                            variant="danger-icon"
                                            :icon="ICONS.delete"
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
                                        paste a recipe
                                    </a>.
                                </q-item-section>
                            </q-item>
                        </q-list>
                    </q-card>

                    <!-- ── Instructions ─ Structured steps + freeform fallback ─ -->
                    <q-card v-if="editing" flat bordered class="q-mb-md">
                        <q-card-section>
                            <div class="row items-center q-mb-sm">
                                <div class="text-subtitle1">Instructions</div>
                                <q-space />
                                <BaseSegmented
                                    v-model="form.steps_mode"
                                    :options="[
                                        { label: 'Structured', value: 'structured' },
                                        { label: 'Freeform', value: 'freeform' },
                                        { label: 'Image', value: 'image' },
                                    ]"
                                    flat
                                    dense
                                    spread
                                    @update:model-value="markDirty"
                                />
                            </div>

                            <RecipeStepsEditor
                                v-if="form.steps_mode === 'structured'"
                                :steps="form.steps"
                                :ingredient-options="stepIngredientOptions"
                                :tool-options="stepToolOptions"
                                :section-options="sectionOptions"
                                @update:steps="onStepsChange"
                            />

                            <q-input
                                v-else-if="form.steps_mode === 'freeform'"
                                v-model="form.instructions"
                                outlined
                                type="textarea"
                                autogrow
                                placeholder="One step per line. Cook mode will split on newlines."
                                hint="Paste the recipe text or type freeform — Ctrl+V works."
                                @update:model-value="markDirty"
                            />

                            <!-- PROPOSAL_RECIPE_IMAGE_STEPS — image-mode
                                 editor. Multi-file picker + drag-reorder;
                                 the centralised processImageFile resizes
                                 client-side before save. -->
                            <RecipeStepImagesEditor
                                v-else
                                :model-value="form.step_images"
                                @update:model-value="onStepImagesChange"
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
                    <q-card v-if="editing" flat bordered class="q-mb-md">
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

                    <!-- ── RD-29 — Personal notes (optional) ──────────────── -->
                    <q-card v-if="editing" flat bordered class="q-mb-md">
                        <q-card-section>
                            <q-input
                                v-model="form.notes"
                                outlined
                                dense
                                autogrow
                                type="textarea"
                                label="Personal notes (optional)"
                                placeholder="Your own notes — tweaks you make, who liked it, what to serve it with. Shown in cook mode under the steps."
                                @update:model-value="markDirty"
                            />
                        </q-card-section>
                    </q-card>

                    <!-- freeform Nutrition field deliberately
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
                        :class="cookableCardClass"
                    >
                        <q-card-section>
                            <div class="row items-center q-gutter-sm">
                                <q-icon :name="cookableIcon" size="28px" />
                                <div>
                                    <div class="text-subtitle1">
                                        {{ cookableHeadline }}
                                    </div>
                                    <div class="text-caption dora-text-secondary">
                                        {{ cookableCaption }}
                                    </div>
                                </div>
                            </div>
                        </q-card-section>
                        <q-tooltip v-if="cookableNow === null">
                            Link ingredients to check cookability — this
                            is a stock-item feature.
                        </q-tooltip>
                    </q-card>

                    <!-- FU-653 — Dora's belief about this recipe, as a remark
                         *under* the verdict card rather than inside it: the
                         card states what your recorded levels say, and this
                         says what she suspects. Deliberately separate so the
                         two can't be mistaken for one answer. Rendered only
                         when the user opted the recipes surface in (the server
                         sends nothing otherwise). -->
                    <q-card
                        v-if="recipe?.inference_hint"
                        flat
                        bordered
                        class="q-mb-md recipe-inference"
                        :class="recipe.inference_hint === 'at_risk'
                            ? 'recipe-inference--risk' : 'recipe-inference--good'"
                    >
                        <q-card-section class="row items-start no-wrap q-gutter-sm">
                            <q-icon :name="ICONS.inferred_hunch" size="22px" />
                            <div>
                                <div class="text-subtitle2">
                                    {{ recipe.inference_hint === 'at_risk'
                                        ? 'Dora thinks you may be short'
                                        : 'Dora thinks you may be able to cook this' }}
                                </div>
                                <div class="text-caption dora-text-secondary">
                                    {{ inferenceCaption }}
                                </div>
                            </div>
                        </q-card-section>
                    </q-card>

                    <!-- read-only "last cooked". The cook + log-cook
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

                    <!-- cost estimate. Server-derived from linked product
                         offers and price observations; rendered only when the
                         C-cross money opt-in is on.

                         Feedback 2026-08-19: collapsed it shows what it always
                         showed; expanded it shows the working — per ingredient,
                         the quantity, the unit price it was matched against,
                         and the line total, or why that ingredient couldn't be
                         priced. Costing has enough "why is that number what it
                         is?" in it (unit reconciliation, offers vs what you
                         actually paid) that hiding the arithmetic makes the
                         estimate untrustworthy. It also renders now when the
                         estimate is *null* but ingredients are linked — the
                         old card vanished silently, which reads as a bug. -->
                    <q-card
                        v-if="moneyEnabled && recipe && showCostCard"
                        flat
                        bordered
                        class="q-mb-md"
                    >
                        <q-expansion-item dense-toggle expand-separator>
                            <template #header>
                                <q-item-section avatar class="recipe-cost__avatar">
                                    <q-icon :name="ICONS.payments" size="22px" class="dora-text-muted" />
                                </q-item-section>
                                <q-item-section>
                                    <div class="text-caption dora-text-muted">Estimated cost</div>
                                    <div class="text-body2">
                                        <strong v-if="recipe.estimated_cost !== null">
                                            {{ formatMoney(recipe.estimated_cost) }}
                                        </strong>
                                        <strong v-else class="dora-text-muted">Not enough price info</strong>
                                        <span class="text-caption dora-text-muted q-ml-xs">
                                            ({{ recipe.estimated_cost_priced_count }} /
                                            {{ recipe.estimated_cost_total_count }}
                                            ingredients priced)
                                        </span>
                                    </div>
                                </q-item-section>
                            </template>

                            <q-card-section class="q-pt-none">
                                <div class="text-caption dora-text-muted q-mb-sm">
                                    Each ingredient is priced from its cheapest linked
                                    product offer, or from what you last paid for it.
                                    An ingredient measured in units the price can't be
                                    converted into is left out rather than guessed at.
                                </div>
                                <q-markup-table flat dense class="recipe-cost__table">
                                    <tbody>
                                        <tr
                                            v-for="(line, li) in recipe.estimated_cost_lines"
                                            :key="`cost-${li}`"
                                        >
                                            <td>
                                                {{ line.name }}
                                                <span v-if="costLineQuantity(line)" class="dora-text-muted">
                                                    · {{ costLineQuantity(line) }}
                                                </span>
                                            </td>
                                            <td class="text-right">
                                                <template v-if="line.line_cost !== null">
                                                    {{ formatMoney(line.line_cost) }}
                                                    <div class="text-caption dora-text-muted">
                                                        {{ formatMoney(line.unit_price) }} / {{ line.priced_unit }}
                                                    </div>
                                                </template>
                                                <span v-else class="text-caption dora-text-muted">
                                                    {{ costLineReason(line) }}
                                                </span>
                                            </td>
                                        </tr>
                                    </tbody>
                                </q-markup-table>
                            </q-card-section>
                        </q-expansion-item>
                    </q-card>

                    <!-- FU-635 — complex mode replaces the typed number with
                         the rollup over the ingredients' linked foods. Two
                         nutrition cards would be two answers to one question,
                         so this and the kcal card below are alternatives. -->
                    <RecipeNutritionCard
                        v-if="isComplex && recipe && recipe.nutrition"
                        :nutrition="recipe.nutrition"
                    />

                    <!-- kcal card. Read-only echo of the
                         editor field; renders only when nutrition is in
                         simple mode AND the recipe has a value. -->
                    <q-card
                        v-if="!isComplex && nutritionEnabled && recipe && recipe.kcal !== null && recipe.kcal !== undefined"
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

                    <!-- Feedback 2026-08-19: the "Paste a recipe…" row that
                         lived here is now the toolbar's Import button, so
                         importing looks the same on this page as it does on
                         the cookbook overview. -->

                    <!-- Versions card. Only renders when this
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
        <BaseDialog v-model="substitutesOpen" title="Substitutes for missing ingredients" closable card-style="min-width: 460px; max-width: 640px">
                <q-card-section>
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
                <template #actions>
                    <BaseButton variant="ghost" label="Close" v-close-popup />
                </template>
        </BaseDialog>

        <!-- â”€â”€ Import-from-URL dialog â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ -->
        <!-- shared dialog. The detail surface adds the
             "overwrite" caption sentence via :degraded-hint and handles
             the confirm-then-patch flow on `@imported`. -->
        <RecipeImportDialog
            v-model="importOpen"
            degraded-hint="Your existing recipe will be overwritten with the imported fields."
            @imported="onRecipeImported"
        />

        <!-- ── Per-ingredient picker (Chunk B §1.4) ──────────────── -->
        <RecipeIngredientPickerDialog
            ref="pickerRef"
            v-model="pickerOpen"
            :recipe="recipe"
            :initial-checked-ids="pickerInitialCheckedIds"
            @confirm="onPickerConfirm"
        />

        <!-- Cook-mode guard (L297/L299/L309). Extracted 2026-08-19 to
             `CookModeGuardDialog` so the cookbook shows the same confirm this
             page does — the rule used to live only here. -->
        <CookModeGuardDialog
            v-model="cookGuardOpen"
            :recipe="recipe"
            :dirty="isDirty"
            :saving="saving"
            @start="goToCookMode"
            @save-and-start="onGuardSaveAndCook"
        />
    </q-page>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import { formatDate as formatLocaleDate } from 'src/composables/useDateFormat';
    import AppSkeleton from 'src/components/AppSkeleton.vue';
    import AppSpinner from 'src/components/AppSpinner.vue';
    import AddToListButton from 'src/components/AddToListButton.vue';
    import RecipeIngredientPickerDialog from 'src/components/recipes/RecipeIngredientPickerDialog.vue';
    import CookModeGuardDialog from 'src/components/recipes/CookModeGuardDialog.vue';
    import { needsCookGuard } from 'src/helpers/cookModeGuard';
    import RecipeNutritionCard from 'src/components/recipes/RecipeNutritionCard.vue';
    import BaseButton from 'src/components/BaseButton.vue';
    import PageToolbar from 'src/components/PageToolbar.vue';
    import BaseDialog from 'src/components/BaseDialog.vue';
    import BaseSegmented from 'src/components/BaseSegmented.vue';
    import MealStepper from 'src/components/recipes/MealStepper.vue';
    import ImageUploadField from 'src/components/ImageUploadField.vue';
    import RecipeStepsEditor from 'src/components/recipes/RecipeStepsEditor.vue';
    import RecipeStepImagesEditor from 'src/components/recipes/RecipeStepImagesEditor.vue';
    import type { EditableStepImage } from 'src/components/recipes/recipeStepImageEditorTypes';
    import type {
        EditableStep as EditableRecipeStep,
        IngredientOption,
        ToolOption,
    } from 'src/components/recipes/recipeStepEditorTypes';
    import FadeTransition from 'src/components/transitions/FadeTransition.vue';
    import { storeToRefs } from 'pinia';
    import { useQuasar } from 'quasar';
    import { useRecipeExport } from 'src/composables/useRecipeExport';
    import { formatMoney } from 'src/composables/useMoney';
    import { formatQuantity } from 'src/helpers/formatQuantity';
    import { useShoppingListActions } from 'src/composables/useShoppingListActions';
    import { colourForSequence } from 'src/helpers/stockLevelLogic';
    import type { Recipe, RecipeCostLine, RecipeStepsMode } from 'src/models/recipe';
    import type { Substitute } from 'src/models/stockItemDetail';
    import RecipeApiService, { recipeImageUrl, recipeStepImageUrl, type ImportedRecipe } from 'src/services/api/recipeApiService';
    import RecipeImportDialog from 'src/components/recipes/RecipeImportDialog.vue';
    import { useImagePrefs } from 'src/composables/useImagePrefs';
    import { useDragDropList } from 'src/composables/useDragDropList';
    import { useMoneyEnabled } from 'src/composables/useMoneyEnabled';
    import { useBatchEnabled } from 'src/composables/useBatchEnabled';
    import { useNutritionMode } from 'src/composables/useNutritionMode';
    import { useUnsavedChangesGuard } from 'src/composables/useUnsavedChangesGuard';
    import type {
        CreateRecipeIngredientCommand,
        RecipeStepCommand,
        UpdateRecipeCommand,
    } from 'src/services/api/recipeApiService';
    import StockItemApiService from 'src/services/api/stockItemApiService';
    import { useMealSlotStore } from 'src/stores/mealSlotStore';
    import { useRecipeStore } from 'src/stores/recipeStore';
    import { useRecipeVocabStore } from 'src/stores/recipeVocabStore';
    import { useShoppingListStore } from 'src/stores/shoppingListStore';
    import { useStockItemStore } from 'src/stores/stockItemStore';
    import { useStockLevelStore } from 'src/stores/stockLevelStore';
    import {
        DEFAULT_MEAL_SLOTS,
        DIFFICULTY_VALUES,
    } from 'src/helpers/recipeVocabulary';
    import { computed, onMounted, reactive, ref, watch } from 'vue';

    const difficultyOptions = [...DIFFICULTY_VALUES];
    import { useRoute, useRouter } from 'vue-router';
    import { describeApiError, toastCaption } from 'src/services/errorHandling/apiErrorHandler';

    const route = useRoute();
    const router = useRouter();
    const $q = useQuasar();

    const recipeStore = useRecipeStore();
    const stockItemStore = useStockItemStore();
    const stockLevelStore = useStockLevelStore();
    const shoppingListStore = useShoppingListStore();
    const recipeVocabStore = useRecipeVocabStore();
    const mealSlotStore = useMealSlotStore();
    const recipeApi = new RecipeApiService();
    // C-cross Chunk 5 — recipe-image render gate (covers the saved-
    // preview branch only; pick/clear is always live).
    const { showRecipeImages } = useImagePrefs();
    // money + nutrition gates for the new estimate/kcal
    // surfaces. Both render-only; consumers fall back to no-render when
    // either flag is off.
    const { moneyEnabled } = useMoneyEnabled();
    const { nutritionEnabled, isSimple, isComplex } = useNutritionMode();
    // Feedback 2026-08-19: the meal pool is a batch-cooking concept. With
    // cook-style "fresh" there is no pool to show, so the card doesn't
    // render — same gate the cookbook already applies to "Meals prepared".
    const { batchEnabled } = useBatchEnabled();
    // Phones drop every toolbar label down to its icon — same gate and the
    // same name as the cookbook overview and stock overview toolbars.
    const compactToolbar = computed(() => $q.screen.lt.sm);
    const stockItemApi = new StockItemApiService();
    const { addItems } = useShoppingListActions();

    const { recipeCollections } = storeToRefs(recipeStore);
    const { stockItems } = storeToRefs(stockItemStore);
    const { stockLevels } = storeToRefs(stockLevelStore);
    const { cuisines, categories, dietaryTags, tools } = storeToRefs(recipeVocabStore);
    const { mealSlotNames } = storeToRefs(mealSlotStore);

    // `time_of_day` reads the household meal-slot vocabulary; falls
    // back to the seed constant only before the store's first load.
    const timeOfDayOptions = computed(() =>
        mealSlotNames.value.length > 0 ? mealSlotNames.value : [...DEFAULT_MEAL_SLOTS],
    );

    const recipeId = computed(() => String(route.params.id ?? ''));
    const recipe = ref<Recipe | null>(null);

    const recipeExport = useRecipeExport();
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
    // R-020 — deferred-save surface, must wire the unsaved-changes guard.
    // Dirty iff any field edit OR an image pick/clear is pending save.
    useUnsavedChangesGuard(computed(() => isDirty.value || imageDirty.value));

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
        // RD-29 — free-text personal notes about the recipe.
        notes: string | null;
        prep_time_minutes: number | null;
        recipe_collection_id: string | null;
        servings: number | null;
        // origin URL.
        source: string | null;
        time_of_day: string | null;
        ingredients: IngredientForm[];
        dietary_tag_ids: string[];
        tool_ids: string[];
        // null = no change (existing image, shown via the endpoint). A data URL
        // sets a new image; explicit null + imageDirty clears it.
        image: string | null;
        // structured steps editor state.
        steps: EditableRecipeStep[];
        // Editor mode toggle. PROPOSAL_RECIPE_IMAGE_STEPS extended this to
        // a tri-state — `structured` sends `steps[]`, `freeform` sends an
        // empty `steps[]` so the server clears structure, `image` sends
        // `step_images[]`. Mode switching is non-destructive: switching
        // away from a mode does NOT clear its payload on save (the user
        // can flip back without re-entry).
        steps_mode: RecipeStepsMode;
        // PROPOSAL_RECIPE_IMAGE_STEPS — image-mode editor state. Each row
        // carries its data URL (sent on save) + a preview URL (the same
        // data URL for freshly-uploaded rows, or the bytes-endpoint URL
        // for rows hydrated from the server). The dirty flag flips when
        // the user reorders / adds / removes, so we only POST step_images
        // when there's been a change.
        step_images: EditableStepImage[];
        // simple nutrition kcal. Editor input renders only
        // when nutrition is enabled; the form field exists regardless.
        kcal: number | null;
        // named sections. Empty list = flat recipe.
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
        notes: null,
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
        step_images: [],
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
            // Carry the free-text label through load so an unlinked ingredient
            // (imported or hand-entered) still shows what it was — without this
            // the row renders as a blank "Stock item" picker with no name.
            raw_text: i.raw_text,
            quantity: i.quantity,
            unit: i.unit,
            notes: i.notes,
            client_id: i.recipe_ingredient_id,
            // re-use the existing section UUID as client_id
            // (see hydrate below) so round-tripping keeps the reference.
            section_client_id: i.section_id,
            // Cookbook revision §1.9 — optional flag round-trip.
            is_optional: i.is_optional ?? false,
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
            // round-trip the section grouping so editing
            // existing recipes preserves the importer's HowToSection
            // assignments (and any subsequent picks).
            section_client_id: s.section_id,
        }));
        Object.assign(form, {
            name: source.name,
            category_id: source.category_id,
            cook_time_minutes: source.cook_time_minutes,
            cuisine_id: source.cuisine_id,
            difficulty: source.difficulty,
            instructions: source.instructions,
            notes: source.notes,
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
            // PROPOSAL_RECIPE_IMAGE_STEPS — trust the server's declared
            // steps_mode rather than re-deriving from has_structured_steps;
            // backfill falls through to the old "structured if rows exist,
            // else freeform" guess for resilience.
            steps_mode: source.steps_mode
                ?? (source.has_structured_steps ? 'structured' : 'freeform'),
            step_images: (source.step_images ?? []).map(img => ({
                client_id: img.image_id,
                existing_image_id: img.image_id,
                preview_url: recipeStepImageUrl(source.recipe_id, img.image_id),
                data_url: '',
            })),
            kcal: source.kcal,
            sections,
        });
        imageDirty.value = false;
        stepImagesDirty.value = false;
        isDirty.value = false;
    }

    function markDirty() {
        isDirty.value = true;
    }

    function onStepsChange(next: EditableRecipeStep[]) {
        form.steps = next;
        markDirty();
    }

    // PROPOSAL_RECIPE_IMAGE_STEPS — tracks whether the step_images set has
    // been touched in this edit session. The save flow only POSTs
    // step_images when this is true so a mode flip alone (without an
    // upload/remove/reorder) leaves the rows in place.
    const stepImagesDirty = ref(false);

    function onStepImagesChange(next: EditableStepImage[]) {
        form.step_images = next;
        stepImagesDirty.value = true;
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
        // sequence-keyed (R-003). The item's own
        // `stock_level_sequence` is populated by the server; fall back to a
        // store lookup if absent (older cached items).
        const item = stockItems.value.find((s) => s.stock_item_id === stockItemId);
        if (!item) return null;
        const seq = item.stock_level_sequence
            ?? stockLevels.value.find((l) => l.stock_level_id === item.stock_level_id)?.sequence;
        return typeof seq === 'number' ? colourForSequence(seq) : null;
    }
    // Per-ingredient "missing" badge in the live editor. Reads the stock item's
    // server-derived `is_out_of_stock` boolean (Â§3.1) rather than matching a
    // level name; untracked / unknown items count as missing.
    function isMissingItem(stockItemId: string): boolean {
        if (!stockItemId) return true;
        const item = stockItems.value.find((s) => s.stock_item_id === stockItemId);
        return !item || Boolean(item.is_out_of_stock);
    }
    // Feedback 2026-08-17 — filtering the cookbook to "uses expiring
    // ingredients" told you a recipe qualified but not which ingredient made
    // it qualify, so opening a result left you comparing the list against the
    // pantry by hand. These read the server's per-ingredient verdict off the
    // loaded recipe (never the stock store, and never recomputed from the
    // date) so the chips and that filter share one horizon by construction.
    //
    // Keyed by stock item rather than by row: the read view renders the edit
    // form's ingredients, which carry no `recipe_ingredient_id`. Two rows
    // pointing at the same pantry item both chip, which is correct anyway.
    const expiringItems = computed(() => {
        const map = new Map<string, { expired: boolean; date: string | null }>();
        for (const ing of recipe.value?.ingredients ?? []) {
            if (!ing.stock_item_id || !ing.is_expiring) continue;
            map.set(ing.stock_item_id, {
                expired: ing.is_expired,
                date: ing.expiry_date,
            });
        }
        return map;
    });
    /** Chip copy + tone for an at-risk ingredient, or null for the rest.
     *  D-001 escalation: amber for "use it soon", red once it's gone off. */
    function expiringChipFor(stockItemId: string | null | undefined) {
        if (!stockItemId) return null;
        const hit = expiringItems.value.get(stockItemId);
        if (!hit) return null;
        // D-006 — the date reads through the household formatter, never a
        // raw ISO echo.
        const when = hit.date ? formatLocaleDate(hit.date) : null;
        return hit.expired
            ? {
                label: 'Expired',
                colour: 'negative',
                icon: ICONS.error,
                tooltip: when ? `Expired ${when}` : 'Past its expiry date',
            }
            : {
                label: 'Use soon',
                colour: 'warning',
                icon: ICONS.event_busy,
                tooltip: when ? `Expires ${when}` : 'Expiring soon',
            };
    }
    // Cookability is server-owned (Â§3.2): the loaded recipe carries `cookable`
    // and each ingredient carries `is_missing`. We read those off the saved
    // recipe rather than recomputing from stock data â€” the summary reflects the
    // persisted recipe and refreshes after each save (`loadRecipe`).
    // IMPL_PLAN_RECIPE_IMPORTER §Chunk 4 — unlinked ingredients
    // (stock_item_id === null) can't be "missing" in the stock-status
    // sense; they're filtered here so the downstream "add missing to
    // list" and "find substitutes" flows never see a null id. The
    // "N ingredients need linking" prompt is shown separately when
    // unlinked_ingredient_count > 0.
    const missingIngredients = computed(() => {
        const r = recipe.value;
        if (!r) return [];
        return r.ingredients
            .filter((i): i is typeof i & { stock_item_id: string; stock_item_name: string } =>
                i.is_missing && i.stock_item_id !== null,
            )
            // Dedupe — an ingredient on multiple rows is still one shopping line.
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
    // IMPL_PLAN_RECIPE_IMPORTER §Chunk 4 — cookableNow is now tri-state.
    // ``null`` fires when the recipe has any unlinked required ingredient.
    // The card renders dimmed with a tooltip; the "Cook mode" guard
    // downstream (line ~1791) treats null as "not cookable" for the
    // "confirm before starting" prompt, but the *label* on the guard's
    // prompt is different — see cookableHeadline / cookableCaption below.
    const cookableNow = computed<boolean | null>(
        () => recipe.value?.cookable ?? false,
    );
    const unlinkedCount = computed(
        () => recipe.value?.unlinked_ingredient_count ?? 0,
    );
    const cookableCardClass = computed(() => {
        if (cookableNow.value === null) return 'dora-bg-sunken dora-text-muted';
        return cookableNow.value
            ? 'dora-bg-positive-soft text-positive'
            : 'dora-bg-warning-soft text-warning';
    });
    const cookableIcon = computed(() => {
        if (cookableNow.value === null) return ICONS.help_outline;
        return cookableNow.value ? ICONS.check_circle : ICONS.shopping_cart;
    });
    const cookableHeadline = computed(() => {
        if (cookableNow.value === null) {
            return `${unlinkedCount.value} ingredient${unlinkedCount.value === 1 ? '' : 's'} to link`;
        }
        if (cookableNow.value) return 'Cookable now';
        return `Missing ${missingIngredients.value.length} ingredient${missingIngredients.value.length === 1 ? '' : 's'}`;
    });
    const cookableCaption = computed(() => {
        if (cookableNow.value === null) {
            return 'Cookability check needs every ingredient linked to a stock item.';
        }
        return `${inStockCount.value} of ${trackedCount.value} in stock`;
    });

    // FU-653 — the belief remark's copy. Names the items and says plainly that
    // nothing above it has changed, so the two cards can't be read as one
    // contradictory verdict.
    const inferenceCaption = computed(() => {
        const names = (recipe.value?.inference_stock_item_names ?? []).join(', ');
        return recipe.value?.inference_hint === 'at_risk'
            ? `From your shopping and cooking rhythm, she suspects ${names} has run out since you last recorded it. Cookability above still follows what you recorded.`
            : `You've got ${names} recorded as missing, but her reading of your rhythm says otherwise. Record a level to settle it.`;
    });

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
                // copy shifted from "Created stock item" (internal
                // jargon) to a user-facing "Added to your pantry" so the user
                // isn't surprised by a new tracked item on the next Stock
                // overview visit. The inline-create path persists the item
                // regardless of whether the recipe save goes through.
                $q.notify({
                    type: 'positive',
                    position: 'bottom-right',
                    message: `Added "${name}" to your pantry.`,
                });
            }
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not create stock item.',
                caption: toastCaption(err),
            });
        }
    }

    function addIngredient() {
        form.ingredients.push({
            stock_item_id: '',
            raw_text: null,
            quantity: null,
            unit: null,
            notes: null,
            // every ingredient row needs a stable client_id so
            // a step can highlight it before the server assigns a real UUID.
            client_id: newClientId(),
            section_client_id: null,
            // Cookbook revision §1.9 — new rows default to required.
            is_optional: false,
        });
        markDirty();
    }

    // FU-506 — save the typed text as an unlinked ingredient. Server
    // accepts `stock_item_id=null` when `raw_text` is set (the
    // recipe_ingredient_anchor CHECK constraint). The user can link
    // it later from the same picker.
    function useAsRawText(idx: number, rawText: string) {
        const text = rawText.trim();
        if (!text) return;
        const row = form.ingredients[idx];
        if (!row) return;
        row.stock_item_id = null;
        row.raw_text = text;
        ingredientFilter.value = '';
        markDirty();
    }

    // section helpers.
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
        // detach any top-level steps that pointed at it too.
        for (const step of form.steps) {
            if (step.section_client_id === removed.client_id) {
                step.section_client_id = null;
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
    // ── FU-118 / R-022 — ingredient DnD reorder + cross-section move ───
    // `useDragDropList` owns the drag state machine + the dragover/leave/
    // drop wiring. We supply the per-drop effect: re-insert source at the
    // target's original slot AND copy the target's `section_client_id` to
    // source, so reorder-within-section and move-between-sections are one
    // gesture. Empty sections still need the per-row Section picker (you
    // can't drop onto something that doesn't exist).
    //
    // FU-161 partner-bug — both indices are captured BEFORE the splice so
    // the "insert at target's original slot" semantic matches shopping-list
    // and recipe-step DnD. The previous pattern computed `toIdx` AFTER
    // removing the source, which shifted the target's index down by one
    // whenever the user dragged downwards — the drop landed one row above
    // where the user let go. Same shape as feedback L414 on shopping
    // lists; the fix is the same too.
    const ingredientDnd = useDragDropList<IngredientForm>({
        mime: 'application/x-dora-recipe-ingredient',
        getId: (ing) => ing.client_id ?? null,
        onDrop: ({ item: source }, { item: target }) => {
            const fromIdx = form.ingredients.indexOf(source);
            const toIdx = form.ingredients.indexOf(target);
            if (fromIdx < 0 || toIdx < 0) return;
            // `section_client_id` is optional on the command type but always
            // present in form rows (null = unsectioned). Normalise so the
            // assignment stays well-typed under exactOptionalPropertyTypes.
            source.section_client_id = target.section_client_id ?? null;
            form.ingredients.splice(fromIdx, 1);
            form.ingredients.splice(toIdx, 0, source);
            markDirty();
        },
    });

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

    // ── DR-11 (D-015): read view state + display derivations ──────────────
    // The page defaults to a READ view; an explicit Edit toggle reveals the
    // form (a detail page is never an always-editable form — the cook-mode
    // surface already proved a reading view is the right shape). These
    // derivations map the same `form` model + option lists + stock helpers the
    // editor uses, so read and edit can't drift.
    const editing = ref(false);

    function labelOf(
        opts: ReadonlyArray<{ value: string | null; label: string }>,
        id: string | null | undefined,
    ): string | null {
        if (!id) return null;
        return opts.find((o) => o.value === id)?.label ?? null;
    }
    const readCuisine = computed(() => labelOf(cuisineOptions.value, form.cuisine_id));
    const readCategory = computed(() => labelOf(categoryOptions.value, form.category_id));
    const readTags = computed(() =>
        form.dietary_tag_ids
            .map((id) => labelOf(dietaryTagOptions.value, id))
            .filter((x): x is string => !!x),
    );
    const readTools = computed(() =>
        form.tool_ids
            .map((id) => labelOf(toolOptions.value, id))
            .filter((x): x is string => !!x),
    );
    const readTimeLabel = computed(() => {
        const parts: string[] = [];
        if (form.prep_time_minutes) parts.push(`${form.prep_time_minutes} min prep`);
        if (form.cook_time_minutes) parts.push(`${form.cook_time_minutes} min cook`);
        return parts.join(' · ');
    });
    function ingredientDisplayName(ing: typeof form.ingredients[number]): string {
        if (ing.stock_item_id) {
            return stockItems.value.find((s) => s.stock_item_id === ing.stock_item_id)?.name
                ?? '(unknown ingredient)';
        }
        return (ing.raw_text ?? '').trim() || '(ingredient)';
    }
    // Ingredients grouped by named section (section order), unsectioned last.
    //
    // The rows are a *read model*, not the edit form's rows: each carries the
    // at-risk chip already resolved, so the template renders one property
    // instead of calling a lookup four times per ingredient. Everything the
    // read view derives per-row belongs here for the same reason.
    type ReadIngredientRow = typeof form.ingredients[number] & {
        expiringChip: ReturnType<typeof expiringChipFor>;
    };
    const readIngredientGroups = computed(() => {
        const toRow = (i: typeof form.ingredients[number]): ReadIngredientRow =>
            ({ ...i, expiringChip: expiringChipFor(i.stock_item_id) });
        const sections = [...form.sections].sort((a, b) => a.sequence - b.sequence);
        const groups: Array<{ name: string | null; rows: ReadIngredientRow[] }> = [];
        for (const sec of sections) {
            const rows = form.ingredients
                .filter((i) => i.section_client_id === sec.client_id)
                .map(toRow);
            if (rows.length > 0) groups.push({ name: sec.name || 'Section', rows });
        }
        const known = new Set(sections.map((s) => s.client_id));
        const loose = form.ingredients
            .filter((i) => !i.section_client_id || !known.has(i.section_client_id))
            .map(toRow);
        if (loose.length > 0) groups.push({ name: null, rows: loose });
        return groups;
    });
    // Structured steps for the read list: top-level (no parent), by sequence.
    const readSteps = computed(() =>
        [...form.steps]
            .filter((s) => !s.parent_client_id)
            .sort((a, b) => a.sequence - b.sequence),
    );
    // Freeform instructions → non-empty lines for an ordered read list.
    const readFreeformLines = computed(() =>
        (form.instructions ?? '')
            .split('\n')
            .map((l) => l.trim())
            .filter((l) => l.length > 0),
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
    // Feedback 2026-08-19: "no way to remove/clear image of a recipe". The
    // claim above was only half true — ImageUploadField derives Remove from
    // its `previewUrl` when `canClear` isn't passed, and that URL is gated on
    // `showRecipeImages`. With photos turned off the recipe still HAD an
    // image and there was no way to delete it. Whether an image exists is a
    // fact about the recipe; whether it's displayed is a viewing preference.
    // They're separate questions, so Remove now reads the fact.
    // ── Cost card (feedback 2026-08-19) ────────────────────────────────
    // Show the card whenever the recipe has something the estimator could
    // have priced — i.e. at least one ingredient linked to a stock item.
    // Without that, "no estimate" isn't information, it's an empty card.
    const showCostCard = computed(
        () => recipe.value !== null
            && (recipe.value.estimated_cost !== null
                || recipe.value.estimated_cost_lines.some((l) => l.reason !== 'no_link')),
    );
    function costLineQuantity(line: RecipeCostLine): string {
        return formatQuantity(line.quantity, line.unit);
    }
    // Server ships the reason code; the sentence lives here (R-003 — one
    // owner per fact, and copy is the client's fact).
    function costLineReason(line: RecipeCostLine): string {
        switch (line.reason) {
            case 'no_link':
                return 'Not linked to a stock item';
            case 'no_price':
                return 'No price recorded yet';
            case 'unit_mismatch':
                return line.priced_unit
                    ? `Priced per ${line.priced_unit} — can't convert`
                    : "Units don't match";
            default:
                return '';
        }
    }

    const hasRemovableImage = computed(() =>
        imageDirty.value ? !!form.image : !!recipe.value?.has_image,
    );
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
            // sections always go with the ingredient
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
            if (form.notes !== src.notes) command.notes = form.notes;
            // always send `steps` so the server knows whether
            // this save replaces the structured set or clears it (freeform
            // mode sends []). Map the editor's EditableStep shape into the
            // wire RecipeStepCommand.
            // PROPOSAL_RECIPE_IMAGE_STEPS — only replace the structured
            // step set when the user is *in* structured mode. Image / free
            // form mode leaves existing structured rows untouched (mode
            // switch is non-destructive — switching back finds them
            // intact).
            if (form.steps_mode === 'structured') {
                const stepsToSend: RecipeStepCommand[] = form.steps.map((s) => ({
                    client_id: s.client_id,
                    parent_client_id: s.parent_client_id,
                    sequence: s.sequence,
                    text: s.text,
                    hint: s.hint,
                    ingredient_client_ids: [...s.ingredient_client_ids],
                    tool_ids: [...s.tool_ids],
                    // round-trip the section grouping. Sub-steps
                    // stay null (the editor doesn't expose a picker on
                    // depth-1 rows); server flattens by parent.
                    section_client_id: s.parent_client_id === null
                        ? s.section_client_id
                        : null,
                }));
                command.steps = stepsToSend;
            }
            // PROPOSAL_RECIPE_IMAGE_STEPS — flip steps_mode if it changed,
            // and replace step_images only when the user touched them in
            // this edit session. A bare mode flip preserves existing rows.
            if (form.steps_mode !== src.steps_mode) {
                command.steps_mode = form.steps_mode;
            }
            if (stepImagesDirty.value) {
                command.step_images = form.step_images.map(img =>
                    img.data_url || '',
                ).filter(s => s.startsWith('data:image/'));
            }
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
                caption: toastCaption(err),
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
                caption: toastCaption(err),
            });
        }
    }

    // L297/L299/L309 — guard cook-mode entry. A confirm is shown when there
    // are unsaved edits OR the recipe isn't cookable now. The guard uses a
    // real dialog with an explicit Cancel; clicking outside / Esc just closes
    // it (never navigates). Clean entry (saved + cookable) goes straight in.
    function goToCookMode() {
        cookGuardOpen.value = false;
        void router.push(`/cookbook/${recipeId.value}/cook`);
    }
    function onStartCookMode() {
        if (!recipe.value) return;
        // Shared predicate (R-003) — the cookbook asks the same question.
        if (needsCookGuard(recipe.value, isDirty.value)) {
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

    // `onAddRowToList` retired; the per-row
    // AddToListButton owns the click now.

    // Add-all-missing → opens the shared per-ingredient picker (Chunk B §1.4)
    // pre-selected to the currently missing items.
    const pickerRef = ref<{ setBusy: (v: boolean) => void } | null>(null);
    const pickerOpen = ref(false);
    const pickerInitialCheckedIds = ref<string[] | undefined>(undefined);

    function onAddMissingToList() {
        if (missingIngredients.value.length === 0) return;
        const hasActiveList = shoppingListStore.summaries.some((s) => s.status !== 'done');
        if (!hasActiveList) {
            $q.dialog({
                title: 'No active shopping list',
                message: 'Create or unarchive one first.',
                ok: { label: 'Open lists', color: 'primary', noCaps: true },
                cancel: { noCaps: true },
            }).onOk(() => { void router.push('/shopping-lists'); });
            return;
        }
        pickerInitialCheckedIds.value = missingIngredients.value.map((i) => i.stock_item_id);
        pickerOpen.value = true;
    }

    async function onPickerConfirm(payload: { stockItemIds: string[]; targetListId: string }) {
        pickerRef.value?.setBusy(true);
        try {
            await addItems(
                payload.targetListId,
                payload.stockItemIds.map((id) => ({ stock_item_id: id })),
            );
            pickerOpen.value = false;
            pickerInitialCheckedIds.value = undefined;
        } finally {
            pickerRef.value?.setBusy(false);
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
                caption: toastCaption(err),
            });
            substitutesOpen.value = false;
        } finally {
            loadingSubstitutes.value = false;
        }
    }

    // ── Import a recipe (paste) ─────────────────────────────────────────
    // IMPL_PLAN_RECIPE_IMPORTER §Chunk 5 — the dialog (RecipeImportDialog)
    // now owns a paste textarea + optional source URL, and calls
    // `importFromContentAsync`. This page opens it via v-model and
    // handles the result: confirm-overwrite → patch form fields →
    // close + toast.
    const importOpen = ref(false);

    function onImportFromUrl() {
        importOpen.value = true;
    }

    async function onRecipeImported(imported: ImportedRecipe) {
        // Confirm overwrite — the imported result might wipe out careful
        // local edits if we just clobber the form.
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
        if (!proceed) {
            // User backed out — close the import dialog so we don't leave
            // a stale URL on screen.
            importOpen.value = false;
            return;
        }

        form.name = imported.name;
        // Importer resolves scraped names to vocab ids when it can; null
        // id (no match) leaves the select empty for the user to pick.
        form.cuisine_id = imported.cuisine_id;
        form.category_id = imported.category_id;
        form.difficulty = imported.difficulty;
        form.servings = imported.servings;
        form.prep_time_minutes = imported.prep_time_minutes;
        form.cook_time_minutes = imported.cook_time_minutes;
        // `source` is its own field now; stop appending
        // "Source: <url>" to the instructions blob.
        form.instructions = imported.instructions || null;
        form.source = imported.source_url || null;
        // IMPL_PLAN_RECIPE_IMPORTER §Chunk 4/5 — every ingredient rides
        // through save now. Linked rows send stock_item_id; unlinked
        // rows send raw_text and stock_item_id: null. The user resolves
        // unlinked rows later via the recipe editor's picker OR the
        // bulk-linker page (Chunk 6). Pre-Chunk-4 this branch coerced
        // stock_item_id to '' which no longer parses server-side.
        form.ingredients = imported.ingredients.map((i) => ({
            stock_item_id: i.stock_item_id,
            raw_text: i.raw_text,
            quantity: i.quantity,
            unit: i.unit,
            notes: i.notes,
            client_id: newClientId(),
            // Cookbook revision §1.9 — importer v1 makes no attempt to
            // detect optional from the source text (parsing "or to
            // taste" / parens is brittle). User toggles per-row after
            // import.
            is_optional: false,
        }));
        // Importer never lands a recipe in image mode — image steps
        // are hand-entered only. Pre-flip back if the user was just
        // experimenting before kicking off an import.
        form.steps_mode = 'freeform';
        // adopt parsed structured steps when the source
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
                section_client_id: null,
            }));
            form.steps_mode = 'structured';
        } else {
            form.steps = [];
            form.steps_mode = 'freeform';
        }
        markDirty();
        importOpen.value = false;
        // IMPL_PLAN_RECIPE_IMPORTER §Chunk 5 — distinct toast when the
        // parser fell back to its lowest-shape output (typically < 3
        // ingredients found). The user knows to clean up rather than
        // assume the structured fields are accurate.
        if (imported.is_degraded) {
            $q.notify({
                type: 'warning',
                position: 'bottom-right',
                timeout: 6000,
                message: 'Couldn’t auto-structure that paste',
                caption:
                    'Pulled the text into Instructions and saved the URL. ' +
                    'Review and edit to clean it up.',
            });
        } else {
            const unlinkedCount = imported.ingredients.filter((i) => !i.stock_item_id).length;
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message:
                    `Imported "${imported.name}".` +
                    (unlinkedCount === 0
                        ? ''
                        : ` ${unlinkedCount} ingredient${unlinkedCount === 1 ? '' : 's'} unlinked — link later from the recipe.`),
            });
        }
    }

    // ── Meals-on-hand controls ─────────────────────────────────────────
    // Feedback 2026-08-19: "Mark cooked" and "Log cook…" are gone. Cooking
    // is an *implicit* fact — nobody navigates to a recipe to remember to
    // record that they made it — so the only writer of `last_made_on` and
    // the pool bump is now finishing a cook session. The stepper below stays
    // as the direct way to correct the pool count.
    const adjusting = ref(false);

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
                caption: toastCaption(err),
            });
        } finally {
            adjusting.value = false;
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
            if (newId) void router.push(`/cookbook/${newId}`);
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not create version.',
                caption: toastCaption(err),
            });
        } finally {
            newVersionLoading.value = false;
        }
    }

    function onJumpToSibling(recipeId: string) {
        void router.push(`/cookbook/${recipeId}`);
    }

    function formatLastMade(isoDate: string): string {
        try {
            const d = new Date(isoDate);
            if (Number.isNaN(d.getTime())) return 'recently';
            return formatLocaleDate(d, { day: 'numeric', month: 'short', year: 'numeric' });
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
            // The recipe is gone — drop dirty flags so the unsaved-changes
            // guard (FU-156) doesn't prompt about edits to a now-deleted row.
            isDirty.value = false;
            imageDirty.value = false;
            void router.push('/cookbook');
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not delete.',
                caption: toastCaption(err),
            });
        }
    }

    // `onBack` was retired 2026-08-19 — PageToolbar's `back-to` is a plain
    // router link to /cookbook, which is all this did. The unsaved-changes
    // prompt is owned by `useUnsavedChangesGuard` (FU-156) and fires on the
    // resulting router-leave whatever triggered it, so nothing is lost.

    // â”€â”€ Mount â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    onMounted(async () => {
        await Promise.all([
            recipeStore.ensureCollectionsLoadedAsync(),
            stockItemStore.ensureLoadedAsync(),
            stockLevelStore.ensureLoadedAsync(),
            shoppingListStore.ensureLoadedAsync(),
            recipeVocabStore.ensureLoadedAsync(),
            mealSlotStore.ensureLoadedAsync(),
        ]);
        await loadRecipe();
    });

    // Re-load when navigating between recipes without unmount.
    watch(recipeId, () => {
        if (recipeId.value) void loadRecipe();
    });
</script>

<style scoped>
    /* FU-653 — the belief remark. A tinted edge only: it sits under the
       cookability verdict and must read as a note about it, not a second
       verdict competing with it. */
    .recipe-inference--risk {
        border-color: color-mix(in srgb, var(--semantic-warning) 55%, transparent);
    }
    .recipe-inference--good {
        border-color: color-mix(in srgb, var(--semantic-positive) 55%, transparent);
    }
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
    /* FU-118 / R-022 — drag affordances live in src/css/dnd.scss
       (.dora-dnd-row / .dora-dnd-handle); the composable applies the
       classes via `rowClass`, the template uses .dora-dnd-handle on
       the handle wrapper. */
    /* ── DR-11 (D-015) read view ──────────────────────────────────────── */
    .recipe-read__hero {
        border-radius: var(--radius-lg, 12px);
        max-height: 320px;
    }
    .recipe-read__ings {
        margin: 0;
        padding-left: var(--space-5, 20px);
        line-height: 1.6;
    }
    .recipe-read__ing--optional {
        color: var(--text-secondary);
    }
    .recipe-read__steps {
        margin: 0;
        padding-left: var(--space-5, 20px);
        line-height: 1.6;
    }
    .recipe-read__steps li {
        margin-bottom: var(--space-2, 8px);
    }
    .recipe-read__stepimg {
        max-width: 100%;
        border-radius: var(--radius-md, 8px);
    }
    .recipe-read__notes {
        white-space: pre-wrap;
        line-height: 1.5;
    }
</style>
