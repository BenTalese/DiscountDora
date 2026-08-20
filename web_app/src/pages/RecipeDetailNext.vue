<template>
    <q-page padding class="rn">
        <!-- Loading shell. Mirrors the real layout (D-007) rather than
             announcing itself in words. -->
        <div v-if="loading && !recipe">
            <div class="rn__masthead">
                <AppSkeleton type="rect" width="100%" height="200px" />
                <div>
                    <AppSkeleton type="line" width="60%" height="2rem" class="q-mb-sm" />
                    <AppSkeleton type="line" width="40%" height="1rem" />
                </div>
            </div>
            <AppSkeleton type="rect" width="100%" height="64px" class="q-mt-md" />
            <AppSkeleton type="rect" width="100%" height="320px" class="q-mt-md" />
        </div>

        <q-banner v-else-if="loadError" class="dora-bg-negative-soft text-negative" dense rounded>
            {{ loadError }}
        </q-banner>

        <template v-else-if="recipe">
            <!-- ═══ Masthead — photo, identity, facts ═══════════════════
                 One unit replacing the old page's breadcrumb row, heading row,
                 toolbar row, hero image and 11-field meta card. -->
            <div class="rn__masthead">
                <ImageEditTile
                    v-if="hasPhoto"
                    class="rn__photo"
                    label="Change the recipe photo"
                    shape="rounded"
                    :width="0"
                    :height="0"
                    @pick="onPickPhoto"
                >
                    <img v-if="photoUrl" :src="photoUrl" alt="" class="rn__photoimg" />
                    <div v-else class="rn__photoempty"></div>
                </ImageEditTile>
                <button
                    v-else
                    type="button"
                    class="rn__photo rn__photo--empty"
                    @click="photoDialogOpen = true"
                >
                    <q-icon :name="ICONS.photo_camera" size="28px" />
                    <span>Add a photo</span>
                </button>

                <div class="rn__identity">
                    <div class="rn__backrow">
                        <BaseButton
                            variant="icon"
                            class="dora-text-secondary"
                            :icon="ICONS.arrow_back"
                            to="/cookbook"
                            aria-label="Back to cookbook"
                        />
                        <h1 class="rn__title">
                            <InlineEditTarget class="rn__edit" label="Edit the recipe name">
                                {{ form.name || 'Untitled recipe' }}
                                <q-popup-edit
                                    v-model="form.name"
                                    v-slot="scope"
                                    auto-save
                                    :validate="(v) => !!(v || '').trim()"
                                    @save="markDirty"
                                >
                                    <q-input
                                        v-model="scope.value"
                                        dense
                                        autofocus
                                        counter
                                        maxlength="255"
                                        label="Recipe name"
                                        @keyup.enter="scope.set"
                                    />
                                </q-popup-edit>
                            </InlineEditTarget>
                        </h1>
                    </div>

                    <div class="rn__eyebrow">
                        <InlineEditTarget class="rn__edit" label="Edit the collection">
                            {{ collectionName || 'No collection' }}
                            <q-popup-edit v-model="form.recipe_collection_id" v-slot="scope" @save="markDirty">
                                <BaseSelect
                                    v-model="scope.value"
                                    label="Collection"
                                    :options="collectionOptions"
                                    emit-value
                                    map-options
                                    clearable
                                    autofocus
                                    @update:model-value="scope.set"
                                />
                            </q-popup-edit>
                        </InlineEditTarget>
                        <span class="rn__dot">·</span>
                        <InlineEditTarget class="rn__edit" label="Edit the cuisine">
                            {{ cuisineName || 'Any cuisine' }}
                            <q-popup-edit v-model="form.cuisine_id" v-slot="scope" @save="markDirty">
                                <BaseSelect
                                    v-model="scope.value"
                                    label="Cuisine"
                                    :options="cuisineOptions"
                                    emit-value
                                    map-options
                                    clearable
                                    autofocus
                                    @update:model-value="scope.set"
                                />
                            </q-popup-edit>
                        </InlineEditTarget>
                        <span class="rn__dot">·</span>
                        <InlineEditTarget class="rn__edit" label="Edit the category">
                            {{ categoryName || 'No category' }}
                            <q-popup-edit v-model="form.category_id" v-slot="scope" @save="markDirty">
                                <BaseSelect
                                    v-model="scope.value"
                                    label="Category"
                                    :options="categoryOptions"
                                    emit-value
                                    map-options
                                    clearable
                                    autofocus
                                    @update:model-value="scope.set"
                                />
                            </q-popup-edit>
                        </InlineEditTarget>
                    </div>

                    <div class="rn__facts">
                        <div class="rn__fact">
                            <span class="rn__factk">Serves</span>
                            <InlineEditTarget class="rn__factv rn__edit" label="Edit the number of servings">
                                {{ form.servings ?? '—' }}
                                <q-popup-edit v-model.number="form.servings" v-slot="scope" auto-save @save="markDirty">
                                    <q-input v-model.number="scope.value" type="number" min="1" dense autofocus label="Servings" @keyup.enter="scope.set" />
                                </q-popup-edit>
                            </InlineEditTarget>
                        </div>
                        <div class="rn__fact">
                            <span class="rn__factk">Prep</span>
                            <InlineEditTarget class="rn__factv rn__edit" label="Edit the prep time">
                                {{ form.prep_time_minutes ? form.prep_time_minutes + ' min' : '—' }}
                                <q-popup-edit v-model.number="form.prep_time_minutes" v-slot="scope" auto-save @save="markDirty">
                                    <q-input v-model.number="scope.value" type="number" min="0" dense autofocus label="Prep (min)" @keyup.enter="scope.set" />
                                </q-popup-edit>
                            </InlineEditTarget>
                        </div>
                        <div class="rn__fact">
                            <span class="rn__factk">Cook</span>
                            <InlineEditTarget class="rn__factv rn__edit" label="Edit the cook time">
                                {{ form.cook_time_minutes ? form.cook_time_minutes + ' min' : '—' }}
                                <q-popup-edit v-model.number="form.cook_time_minutes" v-slot="scope" auto-save @save="markDirty">
                                    <q-input v-model.number="scope.value" type="number" min="0" dense autofocus label="Cook (min)" @keyup.enter="scope.set" />
                                </q-popup-edit>
                            </InlineEditTarget>
                        </div>
                        <div v-if="totalMinutes !== null" class="rn__fact">
                            <span class="rn__factk">Total</span>
                            <span class="rn__factv">{{ totalMinutes }} min</span>
                        </div>
                        <div class="rn__fact">
                            <span class="rn__factk">Difficulty</span>
                            <InlineEditTarget class="rn__factv rn__edit" label="Edit the difficulty">
                                {{ form.difficulty || '—' }}
                                <q-popup-edit v-model="form.difficulty" v-slot="scope" @save="markDirty">
                                    <BaseSelect
                                        v-model="scope.value"
                                        label="Difficulty"
                                        :options="DIFFICULTY_OPTIONS"
                                        clearable
                                        autofocus
                                        @update:model-value="scope.set"
                                    />
                                </q-popup-edit>
                            </InlineEditTarget>
                        </div>
                        <div class="rn__fact">
                            <span class="rn__factk">When</span>
                            <InlineEditTarget class="rn__factv rn__edit" label="Edit the meal this suits">
                                {{ form.time_of_day || '—' }}
                                <q-popup-edit v-model="form.time_of_day" v-slot="scope" @save="markDirty">
                                    <BaseSelect
                                        v-model="scope.value"
                                        label="Time of day"
                                        :options="timeOfDayOptions"
                                        clearable
                                        autofocus
                                        @update:model-value="scope.set"
                                    />
                                </q-popup-edit>
                            </InlineEditTarget>
                        </div>

                        <div v-if="headlineKcal !== null" class="rn__fact">
                            <span class="rn__factk">Per serving</span>
                            <span class="rn__factv">{{ headlineKcal }} kcal</span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- ═══ Actions — their own full-width row ═══════════════════
                 Save and Discard only exist while there is something to save,
                 so a recipe being *read* still leads with Cook mode. While
                 they're present Save is the primary and Cook mode steps back —
                 two primaries in one row is no primary at all. -->
            <div class="rn__actions">
                <BaseButton
                    v-if="dirty"
                    variant="primary"
                    :icon="ICONS.save"
                    label="Save"
                    aria-label="Save changes"
                    :loading="saveState === 'saving'"
                    :disable="!canSave"
                    @click="onSave"
                />
                <BaseButton
                    v-if="dirty"
                    variant="ghost"
                    :icon="ICONS.undo"
                    :label="compact ? undefined : 'Discard'"
                    aria-label="Discard changes"
                    :disable="saveState === 'saving'"
                    @click="onDiscard"
                >
                    <q-tooltip v-if="compact">Discard changes</q-tooltip>
                </BaseButton>
                <BaseButton
                    :variant="dirty ? 'secondary' : 'primary'"
                    :icon="ICONS.restaurant_menu"
                    :label="compact ? undefined : 'Cook mode'"
                    aria-label="Cook mode"
                    @click="onStartCookMode"
                >
                    <q-tooltip v-if="compact">Cook mode</q-tooltip>
                </BaseButton>
                <BaseButton
                    variant="ghost"
                    :icon="recipe.is_favourite ? 'favorite' : 'favorite_border'"
                    :label="compact ? undefined : (recipe.is_favourite ? 'Favourited' : 'Favourite')"
                    :class="{ 'text-negative': recipe.is_favourite }"
                    :aria-label="recipe.is_favourite ? 'Remove from favourites' : 'Add to favourites'"
                    @click="onToggleFavourite"
                >
                    <q-tooltip v-if="compact">{{ recipe.is_favourite ? 'Favourited' : 'Favourite' }}</q-tooltip>
                </BaseButton>
                <BaseButton
                    variant="ghost"
                    :icon="ICONS.content_copy"
                    :label="compact ? undefined : 'New version'"
                    aria-label="New version"
                    :loading="newVersionLoading"
                    @click="onNewVersion"
                >
                    <q-tooltip v-if="compact">New version</q-tooltip>
                </BaseButton>
                <BaseButton
                    variant="ghost"
                    :icon="ICONS.print"
                    :label="compact ? undefined : 'Print'"
                    aria-label="Print"
                    @click="onPrint"
                >
                    <q-tooltip v-if="compact">Print</q-tooltip>
                </BaseButton>
                <BaseButton
                    variant="danger-ghost"
                    class="rn__delete"
                    :icon="ICONS.delete"
                    :label="compact ? undefined : 'Delete'"
                    aria-label="Delete recipe"
                    @click="onDelete"
                >
                    <q-tooltip v-if="compact">Delete recipe</q-tooltip>
                </BaseButton>
            </div>

            <!-- ═══ Status strip — replaces seven sidebar cards ══════════
                 Severity lives in a 3px edge stripe rather than a washed cell
                 (D-013): it stays legible on both grounds and doesn't shout.
                 Cells that have nothing to say don't render. -->
            <div class="rn__status">
                <div
                    class="rn__cell"
                    :class="missingIngredients.length > 0 ? 'rn__cell--bad' : (cookableNow ? 'rn__cell--ok' : '')"
                >
                    <span class="rn__cellk">Right now</span>
                    <span class="rn__cellv">{{ cookableHeadline }}</span>
                    <!-- "You're missing two things, but you have a substitute
                         for one" is a different answer to "you're missing two
                         things", so it belongs in the cell that answers it. -->
                    <span v-if="coverableCount > 0" class="rn__cellsub">
                        {{ coverableCount === 1
                            ? '1 has a substitute you already have'
                            : `${coverableCount} have substitutes you already have` }}
                    </span>
                    <button
                        v-if="missingIngredients.length > 0"
                        type="button"
                        class="rn__link"
                        @click="onAddMissingToList"
                    >
                        Add {{ missingIngredients.length === 1 ? 'it' : 'them' }} to a list →
                    </button>
                    <span v-else class="rn__cellsub">{{ cookableCaption }}</span>
                </div>

                <div v-if="atRiskCount > 0" class="rn__cell rn__cell--warn">
                    <span class="rn__cellk">Worth cooking</span>
                    <span class="rn__cellv">{{ atRiskHeadline }}</span>
                    <span class="rn__cellsub">Uses it up</span>
                </div>

                <div v-if="moneyEnabled && showCostCell" class="rn__cell">
                    <span class="rn__cellk">Estimated cost</span>
                    <span class="rn__cellv">
                        {{ recipe.estimated_cost !== null ? formatMoney(recipe.estimated_cost) : 'Not enough price info' }}
                    </span>
                    <button type="button" class="rn__link" @click="openDetail('cost')">
                        {{ recipe.estimated_cost_priced_count }} of {{ recipe.estimated_cost_total_count }} priced · breakdown →
                    </button>
                </div>

                <div class="rn__cell">
                    <span class="rn__cellk">Last cooked</span>
                    <span class="rn__cellv">
                        {{ recipe.last_made_on ? formatDate(recipe.last_made_on) : 'Never' }}
                    </span>
                    <!-- The meal pool merged in here rather than owning a card
                         of its own. Batch-cooking households only. -->
                    <span v-if="batchEnabled" class="rn__pool">
                        <MealStepper
                            :available="recipe.available_meals"
                            :busy="adjusting"
                            size="sm"
                            @adjust="onAdjustMeals"
                        />
                        <span class="rn__cellsub">
                            {{ recipe.unallocated_meals }} free of {{ recipe.available_meals }}
                        </span>
                    </span>
                </div>
            </div>

            <!-- ═══ Body — ingredients rail + method ════════════════════ -->
            <div class="rn__body">
                <div class="rn__rail">
                    <section aria-labelledby="rnIng">
                        <div class="rn__sechead">
                            <h2 class="rn__sectitle" id="rnIng">Ingredients</h2>
                            <span class="rn__seccount">{{ form.ingredients.length }}</span>
                        </div>

                        <div class="rn__pane">
                            <template v-for="group in ingredientGroups" :key="group.key">
                                <div v-if="group.name" class="rn__ingsec">{{ group.name }}</div>
                                <ul class="rn__ing">
                                    <li
                                        v-for="row in group.rows"
                                        :key="row.client_id"
                                        :class="{ 'rn__ing--lit': litIngredients.has(String(row.client_id)) }"
                                    >
                                        <InlineEditTarget
                                            class="rn__qty rn__edit"
                                            :label="`Edit how much ${ingredientLabel(row)}`"
                                        >
                                            {{ formatQuantity(row.quantity, row.unit) || '—' }}
                                            <q-popup-edit v-model="row.quantity" v-slot="scope" auto-save @save="markDirty">
                                                <div class="row q-gutter-sm items-center">
                                                    <q-input v-model.number="scope.value" type="number" min="0" step="any" dense autofocus label="Qty" style="width: 90px" @keyup.enter="scope.set" />
                                                    <q-input v-model="row.unit" dense label="Unit" style="width: 110px" @update:model-value="markDirty" />
                                                </div>
                                            </q-popup-edit>
                                        </InlineEditTarget>
                                        <span class="rn__ingname">
                                            <!-- Opens the whole row's editor rather
                                                 than a bare stock-item picker: an
                                                 ingredient also carries a free-text
                                                 anchor, a section, an optional flag
                                                 and a note, and all four were
                                                 unreachable from this page. -->
                                            <button
                                                type="button"
                                                class="rn__edit rn__ingbtn"
                                                :aria-label="`Edit ${ingredientLabel(row)}`"
                                                @click="openRowEditor(String(row.client_id))"
                                            >
                                                {{ ingredientLabel(row) }}
                                            </button>
                                            <q-chip v-if="row.is_optional" dense square size="sm" class="rn__chip">Optional</q-chip>
                                            <!-- A row with neither an item nor text is
                                                 the one thing that can refuse the save,
                                                 so it says so on the row instead of only
                                                 in the save message. -->
                                            <q-chip
                                                v-if="isHalfBuilt(row)"
                                                dense square size="sm"
                                                color="warning"
                                                text-color="dark"
                                                class="rn__chip"
                                                clickable
                                                @click="openRowEditor(String(row.client_id))"
                                            >
                                                Needs an item
                                            </q-chip>
                                            <q-chip
                                                v-else-if="!row.stock_item_id"
                                                dense square size="sm"
                                                class="rn__chip rn__chip--unlinked"
                                            >
                                                Free text
                                                <q-tooltip>
                                                    Not linked to a pantry item, so Dora
                                                    can't tell whether you have it.
                                                </q-tooltip>
                                            </q-chip>
                                            <q-chip
                                                v-else-if="isMissingItem(row.stock_item_id)"
                                                dense square size="sm"
                                                color="negative"
                                                text-color="white"
                                                class="rn__chip"
                                            >
                                                Missing
                                            </q-chip>
                                            <q-chip
                                                v-if="expiringChipFor(row.stock_item_id)"
                                                dense square size="sm"
                                                :color="expiringChipFor(row.stock_item_id)!.colour"
                                                text-color="dark"
                                                :icon="expiringChipFor(row.stock_item_id)!.icon"
                                                class="rn__chip"
                                            >
                                                {{ expiringChipFor(row.stock_item_id)!.label }}
                                                <q-tooltip>{{ expiringChipFor(row.stock_item_id)!.tooltip }}</q-tooltip>
                                            </q-chip>
                                            <RecipeIngredientSubstitutes
                                                :entries="substitutesForRow(row)"
                                                :ingredient-name="ingredientLabel(row)"
                                            />
                                            <span v-if="row.notes" class="rn__ingnote">{{ row.notes }}</span>
                                        </span>
                                        <!-- Per-row quick action, revealed on hover/focus. -->
                                        <span class="rn__ingact">
                                            <AddToListButton
                                                v-if="row.stock_item_id && isMissingItem(row.stock_item_id)"
                                                :stock-item-id="row.stock_item_id"
                                                variant="row"
                                            />
                                            <BaseButton
                                                variant="danger-icon" dense
                                                :icon="ICONS.delete"
                                                :aria-label="`Remove ${ingredientLabel(row)}`"
                                                @click="removeIngredient(String(row.client_id))"
                                            />
                                        </span>
                                    </li>
                                </ul>
                                <!-- A section you just created has nothing in it
                                     yet, and saying so is what makes it obvious
                                     where the ingredients go. -->
                                <p v-if="group.rows.length === 0" class="rn__ingsecempty">
                                    Nothing in this section yet — open an ingredient
                                    and set its section.
                                </p>
                            </template>

                            <p v-if="form.ingredients.length === 0" class="rn__empty">
                                No ingredients yet.
                            </p>
                        </div>

                        <BaseButton
                            variant="subtle"
                            class="rn__add"
                            :icon="ICONS.add"
                            label="Add ingredient"
                            @click="addIngredient"
                        />
                    </section>
                </div>

                <section aria-labelledby="rnMet">
                    <div class="rn__sechead">
                        <h2 class="rn__sectitle" id="rnMet">Method</h2>
                        <span class="rn__seccount">{{ methodCountLabel }}</span>
                        <BaseSegmented
                            v-model="form.steps_mode"
                            dense
                            class="rn__modes"
                            :options="[
                                { label: 'Steps', value: 'structured' },
                                { label: 'Text', value: 'freeform' },
                                { label: 'Photos', value: 'image' },
                            ]"
                            @update:model-value="markDirty"
                        />
                    </div>

                    <div class="rn__pane">
                        <!-- Structured — the only mode that can tie a step to
                             its ingredients, because it's the only one that
                             stores the link. -->
                        <template v-if="form.steps_mode === 'structured'">
                            <ol v-if="topLevelSteps.length > 0" class="rn__steps">
                                <!-- The `li` was focusable purely to drive the
                                     ingredient highlight, which put two tab
                                     stops on every step and named neither. The
                                     edit target is the stop now, and focus/
                                     hover on it lights the same rail rows. -->
                                <li
                                    v-for="step in topLevelSteps"
                                    :key="step.client_id"
                                    :class="{ 'rn__step--lit': litStep === step.client_id }"
                                    @mouseenter="litStep = step.client_id"
                                    @mouseleave="litStep = null"
                                >
                                    <InlineEditTarget
                                        tag="p"
                                        class="rn__edit"
                                        :label="`Edit step ${step.sequence + 1}`"
                                        @focusin="litStep = step.client_id"
                                        @focusout="litStep = null"
                                    >
                                        {{ step.text || 'Empty step' }}
                                        <q-popup-edit v-model="step.text" v-slot="scope" auto-save @save="markDirty">
                                            <q-input v-model="scope.value" type="textarea" autogrow dense autofocus label="Step" />
                                        </q-popup-edit>
                                    </InlineEditTarget>
                                    <span v-if="step.hint" class="rn__hint">{{ step.hint }}</span>
                                    <span v-if="usesLabel(step)" class="rn__uses">Uses {{ usesLabel(step) }}</span>
                                    <ol v-if="subStepsOf(step).length > 0" class="rn__substeps">
                                        <li v-for="sub in subStepsOf(step)" :key="sub.client_id">{{ sub.text }}</li>
                                    </ol>
                                </li>
                            </ol>
                            <p v-else class="rn__empty">No steps yet — add them in the step editor below.</p>
                        </template>

                        <!-- Freeform — one editable block of text. -->
                        <template v-else-if="form.steps_mode === 'freeform'">
                            <InlineEditTarget
                                v-if="freeformLines.length > 0"
                                tag="div"
                                class="rn__free rn__edit"
                                label="Edit the instructions"
                            >
                                <p v-for="(line, i) in freeformLines" :key="`f-${i}`">{{ line }}</p>
                                <q-popup-edit v-model="form.instructions" v-slot="scope" auto-save @save="markDirty">
                                    <q-input v-model="scope.value" type="textarea" autogrow dense autofocus label="Instructions" style="min-width: 320px" />
                                </q-popup-edit>
                            </InlineEditTarget>
                            <InlineEditTarget
                                v-else
                                tag="p"
                                class="rn__empty rn__edit"
                                label="Add instructions"
                            >
                                No instructions yet.
                                <q-popup-edit v-model="form.instructions" v-slot="scope" auto-save @save="markDirty">
                                    <q-input v-model="scope.value" type="textarea" autogrow dense autofocus label="Instructions" style="min-width: 320px" />
                                </q-popup-edit>
                            </InlineEditTarget>
                        </template>

                        <!-- Photo steps. -->
                        <template v-else>
                            <RecipeStepImagesViewer
                                v-if="(recipe.step_images ?? []).length > 0"
                                :recipe-id="recipe.recipe_id"
                                :images="recipe.step_images ?? []"
                            />
                            <p v-else class="rn__empty">No step photos yet — add them below.</p>
                        </template>
                    </div>

                    <!-- Structural editing (reorder, sub-steps, per-step
                         ingredients, photo management) lives behind one
                         disclosure. Inline editing covers the text; this
                         covers the shape. -->
                    <q-expansion-item
                        v-if="form.steps_mode !== 'freeform'"
                        dense-toggle
                        class="rn__editor"
                        :label="form.steps_mode === 'structured' ? 'Reorder steps, link ingredients & tools' : 'Add or reorder step photos'"
                    >
                        <RecipeStepsEditor
                            v-if="form.steps_mode === 'structured'"
                            :steps="form.steps"
                            :ingredient-options="ingredientOptions"
                            :tool-options="toolOptions"
                            :section-options="sectionOptions"
                            @update:steps="onStepsChanged"
                        />
                        <RecipeStepImagesEditor
                            v-else
                            :model-value="form.step_images"
                            @update:model-value="onStepImagesChanged"
                        />
                    </q-expansion-item>
                </section>
            </div>

            <!-- ═══ Details — everything administrative ═════════════════ -->
            <div class="rn__details">
                <q-expansion-item v-model="detailOpen.tags" dense-toggle label="Tags & tools" :caption="tagsCaption">
                    <div class="rn__disc">
                        <BaseSelect
                            v-model="form.dietary_tag_ids"
                            label="Dietary tags"
                            :options="dietaryTagOptions"
                            emit-value map-options multiple use-chips clearable
                            class="q-mb-sm"
                            @update:model-value="markDirty"
                        />
                        <BaseSelect
                            v-model="form.tool_ids"
                            label="Tools"
                            :options="toolSelectOptions"
                            emit-value map-options multiple use-chips clearable
                            @update:model-value="markDirty"
                        />
                    </div>
                </q-expansion-item>

                <!-- ── Organise ─────────────────────────────────────────
                     The shape of the list, in the same place the method keeps
                     the shape of its steps. Deliberately not drag-and-drop:
                     the old page's handles doubled as drag-into-a-section, on
                     the surface most likely to be used one-handed at a bench.
                     ↑/↓ are keyboard-operable for free and can't fire by
                     accident while scrolling. -->
                <q-expansion-item
                    v-model="detailOpen.sections"
                    dense-toggle
                    label="Organise ingredients"
                    :caption="organiseCaption"
                >
                    <div class="rn__disc">
                        <p class="rn__hintblock">
                            Sections group the list under headings — "For the sauce",
                            "To serve". A recipe with no sections shows one flat list.
                        </p>

                        <div v-for="(sec, i) in orderedSections" :key="sec.client_id" class="rn__secrow">
                            <q-input
                                v-model="sec.name"
                                dense outlined
                                class="col"
                                placeholder="For the sauce"
                                label="Section name"
                                @update:model-value="markDirty"
                            />
                            <BaseButton
                                variant="icon"
                                :icon="ICONS.arrow_upward"
                                :disable="i === 0"
                                :aria-label="`Move section ${sec.name || i + 1} up`"
                                @click="moveSection(sec.client_id, -1)"
                            />
                            <BaseButton
                                variant="icon"
                                :icon="ICONS.arrow_downward"
                                :disable="i === orderedSections.length - 1"
                                :aria-label="`Move section ${sec.name || i + 1} down`"
                                @click="moveSection(sec.client_id, 1)"
                            />
                            <BaseButton
                                variant="danger-icon"
                                :icon="ICONS.delete"
                                :aria-label="`Remove section ${sec.name || i + 1}`"
                                @click="removeSection(sec.client_id)"
                            />
                        </div>
                        <BaseButton
                            variant="subtle"
                            :icon="ICONS.add"
                            label="Add section"
                            @click="addSection"
                        />

                        <template v-if="form.ingredients.length > 1">
                            <div class="rn__discsub">Order</div>
                            <ol class="rn__order">
                                <li v-for="(entry, i) in orderedIngredients" :key="entry.row.client_id">
                                    <span class="rn__ordername">
                                        {{ ingredientLabel(entry.row) }}
                                        <span v-if="entry.section" class="rn__ordersec">{{ entry.section }}</span>
                                    </span>
                                    <BaseButton
                                        variant="icon"
                                        :icon="ICONS.arrow_upward"
                                        :disable="i === 0"
                                        :aria-label="`Move ${ingredientLabel(entry.row)} up`"
                                        @click="moveIngredient(String(entry.row.client_id), -1)"
                                    />
                                    <BaseButton
                                        variant="icon"
                                        :icon="ICONS.arrow_downward"
                                        :disable="i === orderedIngredients.length - 1"
                                        :aria-label="`Move ${ingredientLabel(entry.row)} down`"
                                        @click="moveIngredient(String(entry.row.client_id), 1)"
                                    />
                                </li>
                            </ol>
                            <p class="rn__hintblock">
                                Which section an ingredient belongs to is set on the
                                ingredient itself — tap its name in the list above.
                            </p>
                        </template>
                    </div>
                </q-expansion-item>

                <q-expansion-item
                    v-if="moneyEnabled && showCostCell"
                    v-model="detailOpen.cost"
                    dense-toggle
                    label="Cost breakdown"
                    :caption="costCaption"
                >
                    <div class="rn__disc">
                        <q-markup-table flat dense class="rn__costtable">
                            <tbody>
                                <tr v-for="(line, i) in recipe.estimated_cost_lines" :key="`c-${i}`">
                                    <td>
                                        {{ line.name }}
                                        <span v-if="formatQuantity(line.quantity, line.unit)" class="dora-text-muted">
                                            · {{ formatQuantity(line.quantity, line.unit) }}
                                        </span>
                                    </td>
                                    <td class="text-right">
                                        <template v-if="line.line_cost !== null">
                                            {{ formatMoney(line.line_cost) }}
                                            <div class="text-caption dora-text-muted">
                                                {{ formatMoney(line.unit_price) }} / {{ line.priced_unit }}
                                            </div>
                                        </template>
                                        <span v-else class="text-caption dora-text-muted">{{ costLineReason(line) }}</span>
                                    </td>
                                </tr>
                            </tbody>
                        </q-markup-table>
                    </div>
                </q-expansion-item>

                <q-expansion-item
                    v-if="isComplex && recipe.nutrition"
                    v-model="detailOpen.nutrition"
                    dense-toggle
                    label="Nutrition"
                    :caption="nutritionCaption"
                >
                    <div class="rn__disc">
                        <RecipeNutritionCard :nutrition="recipe.nutrition" />
                    </div>
                </q-expansion-item>

                <q-expansion-item v-model="detailOpen.notes" dense-toggle label="Source & notes" :caption="notesCaption">
                    <div class="rn__disc">
                        <q-input
                            v-model="form.source"
                            dense outlined clearable
                            class="q-mb-sm"
                            label="Source URL"
                            @update:model-value="markDirty"
                        />
                        <q-input
                            v-model="form.notes"
                            dense outlined type="textarea" autogrow
                            label="Notes"
                            @update:model-value="markDirty"
                        />
                    </div>
                </q-expansion-item>

                <q-expansion-item
                    v-if="!isComplex && nutritionEnabled"
                    v-model="detailOpen.kcal"
                    dense-toggle
                    label="Calories"
                    :caption="form.kcal ? `${form.kcal} kcal per serving` : 'Not set'"
                >
                    <div class="rn__disc">
                        <q-input
                            v-model.number="form.kcal"
                            dense outlined type="number" min="0"
                            label="kcal per serving"
                            style="max-width: 220px"
                            @update:model-value="markDirty"
                        />
                    </div>
                </q-expansion-item>

                <q-expansion-item
                    v-if="versionSiblings.length > 0"
                    v-model="detailOpen.versions"
                    dense-toggle
                    label="Other versions"
                    :caption="`${versionSiblings.length} sibling${versionSiblings.length === 1 ? '' : 's'}`"
                >
                    <div class="rn__disc">
                        <q-list dense separator>
                            <q-item
                                v-for="sib in versionSiblings"
                                :key="sib.recipe_id"
                                clickable
                                @click="goToSibling(sib.recipe_id)"
                            >
                                <q-item-section>
                                    <q-item-label>{{ sib.name }}</q-item-label>
                                    <q-item-label caption>
                                        {{ sib.last_made_on ? `Last cooked ${formatDate(sib.last_made_on)}` : 'Never cooked' }}
                                    </q-item-label>
                                </q-item-section>
                            </q-item>
                        </q-list>
                    </div>
                </q-expansion-item>

                <q-expansion-item v-model="detailOpen.photo" dense-toggle label="Recipe photo" :caption="hasPhoto ? 'Set' : 'None'">
                    <div class="rn__disc">
                        <ImageUploadField
                            :preview-url="photoUrl"
                            :can-clear="hasPhoto"
                            :name="form.name"
                            alt="Recipe photo"
                            @pick="onPickPhotoDataUrl"
                            @clear="onClearPhoto"
                        />
                    </div>
                </q-expansion-item>
            </div>

            <!-- The comparison hatch. Temporary — see FU-688. -->
            <div class="rn__flip">
                <BaseButton
                    variant="ghost"
                    :icon="ICONS.arrow_back"
                    label="Back to the old layout"
                    :to="`/cookbook/${recipeId}`"
                />
            </div>
        </template>

        <!-- Two different jobs, deliberately not merged. The dirty pill is a
             standing statement of fact ("there is unsaved work here") and has
             to survive until it stops being true; the bar below is a transient
             outcome. One element doing both is how the old autosave indicator
             ended up being the only feedback channel for either. -->
        <div v-if="dirty && saveState !== 'saving'" class="rn__dirty" role="status">
            <q-icon :name="ICONS.edit" size="14px" />
            <span>Unsaved changes</span>
        </div>

        <div v-if="saveState !== 'idle'" class="rn__savebar" :class="`rn__savebar--${saveState}`" role="status">
            <q-spinner v-if="saveState === 'saving'" size="16px" />
            <q-icon v-else-if="saveState === 'saved'" :name="ICONS.check" />
            <q-icon v-else :name="ICONS.error" />
            <span>{{ saveMessage }}</span>
        </div>

        <!-- With an explicit save there is a real answer to "you have unsaved
             changes, cook anyway?", so the guard is wired to it instead of the
             hardcoded `false` the autosave version had to pass. -->
        <CookModeGuardDialog
            v-model="cookGuardOpen"
            :recipe="recipe"
            :dirty="dirty"
            :saving="saveState === 'saving'"
            @start="goToCookMode"
            @save-and-start="onSaveAndCook"
        />

        <RecipeIngredientRowEditor
            v-model="rowEditorOpen"
            :row="rowEditorRow"
            :sections="form.sections"
            @save="onRowEditorSave"
        />

        <RecipeIngredientPickerDialog
            ref="pickerRef"
            v-model="pickerOpen"
            :recipe="recipe"
            :initial-checked-ids="pickerInitialCheckedIds"
            @confirm="onPickerConfirm"
        />

        <BaseDialog v-model="photoDialogOpen" title="Recipe photo" closable card-style="min-width: 300px">
            <q-card-section class="q-pt-none">
                <ImageUploadField
                    :preview-url="photoUrl"
                    :can-clear="hasPhoto"
                    :name="form.name"
                    alt="Recipe photo"
                    @pick="onPickPhotoDataUrl"
                    @clear="onClearPhoto"
                />
            </q-card-section>
        </BaseDialog>
    </q-page>
</template>

<script lang="ts" setup>
    /**
     * RecipeDetailNext — the redesigned recipe page (2026-08-20).
     *
     * Runs in parallel with `RecipeDetailPage.vue` at `/cookbook/:id/new` so the
     * two can be compared on the same recipe; each carries a button to the
     * other. **This is the page that survives** — the owner's call, 2026-08-20,
     * conditional on feature parity, which is what the gap-closing pass below
     * was for. The old page and both hatch buttons go once the route swap
     * lands (FU-688); Import is deliberately *not* migrated (FU-689 closed
     * won't-do — importing over an existing recipe was never wanted here).
     *
     * Three things make it different from the old page:
     *
     * 1. **No modes, but an explicit save.** The read/edit toggle is gone —
     *    values render as text and edit in place via `q-popup-edit`. What is
     *    *not* gone is the commit: edits mark the form dirty and a Save button
     *    appears. The first cut autosaved on a 500ms debounce and the owner
     *    reversed it; see the save block below for the three ways that failed.
     *    D-015's "read-view + explicit edit mode for detail pages" clause was
     *    retired when this page won the comparison (FU-688) — it had been
     *    written against the old page's form-as-detail, which no longer
     *    exists, and it was the only clause of that rule about detail pages.
     *    Inline editing keeps the page reading as a recipe, which is what the
     *    clause was actually protecting.
     * 2. **Structural edits stay behind a disclosure.** Reordering steps,
     *    linking ingredients to steps, managing photos — the things that need a
     *    real editor — live in one expansion under the method, not inline.
     * 3. **No business logic of its own.** The form model, hydrate and PATCH
     *    build all come from `useRecipeEditor` (R-003); everything else reads
     *    server-derived values off the loaded recipe exactly as the old page
     *    does.
     *
     * All three step modes are supported. Only `structured` can highlight the
     * ingredients a step uses, because it's the only mode that stores the link.
     */
    import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue';
    import { onBeforeRouteLeave, useRoute, useRouter } from 'vue-router';
    import { useQuasar } from 'quasar';
    import { storeToRefs } from 'pinia';

    import AppSkeleton from 'src/components/AppSkeleton.vue';
    import BaseButton from 'src/components/BaseButton.vue';
    import BaseDialog from 'src/components/BaseDialog.vue';
    import BaseSegmented from 'src/components/BaseSegmented.vue';
    import BaseSelect from 'src/components/BaseSelect.vue';
    import InlineEditTarget from 'src/components/InlineEditTarget.vue';
    import ImageEditTile from 'src/components/ImageEditTile.vue';
    import ImageUploadField from 'src/components/ImageUploadField.vue';
    import MealStepper from 'src/components/recipes/MealStepper.vue';
    import RecipeNutritionCard from 'src/components/recipes/RecipeNutritionCard.vue';
    import RecipeStepImagesEditor from 'src/components/recipes/RecipeStepImagesEditor.vue';
    import RecipeStepImagesViewer from 'src/components/recipes/RecipeStepImagesViewer.vue';
    import RecipeStepsEditor from 'src/components/recipes/RecipeStepsEditor.vue';
    import CookModeGuardDialog from 'src/components/recipes/CookModeGuardDialog.vue';
    import RecipeIngredientPickerDialog from 'src/components/recipes/RecipeIngredientPickerDialog.vue';
    import RecipeIngredientRowEditor from 'src/components/recipes/RecipeIngredientRowEditor.vue';
    import RecipeIngredientSubstitutes from 'src/components/recipes/RecipeIngredientSubstitutes.vue';
    import AddToListButton from 'src/components/AddToListButton.vue';

    import { ICONS } from 'src/style/icons';
    import { formatQuantity } from 'src/helpers/formatQuantity';
    import { formatDate } from 'src/composables/useDateFormat';
    import { formatMoney } from 'src/composables/useMoney';
    import { needsCookGuard } from 'src/helpers/cookModeGuard';
    import { toastCaption } from 'src/services/errorHandling/apiErrorHandler';
    import { useBatchEnabled } from 'src/composables/useBatchEnabled';
    import { useImagePrefs } from 'src/composables/useImagePrefs';
    import { useMoneyEnabled } from 'src/composables/useMoneyEnabled';
    import { useNutritionMode } from 'src/composables/useNutritionMode';
    import { useRecipeExport } from 'src/composables/useRecipeExport';
    import { DEFAULT_MEAL_SLOTS, DIFFICULTY_VALUES } from 'src/helpers/recipeVocabulary';
    import { useShoppingListActions } from 'src/composables/useShoppingListActions';
    import {
        buildUpdateCommand,
        hydrateRecipeForm,
        newClientId,
        useRecipeForm,
        type IngredientForm,
        type IngredientPatch,
    } from 'src/composables/useRecipeEditor';

    import RecipeApiService, { recipeImageUrl } from 'src/services/api/recipeApiService';
    import { useRecipeStore } from 'src/stores/recipeStore';
    import { useRecipeVocabStore } from 'src/stores/recipeVocabStore';
    import { useStockItemStore } from 'src/stores/stockItemStore';
    import { useMealSlotStore } from 'src/stores/mealSlotStore';
    import { useStockLevelStore } from 'src/stores/stockLevelStore';
    import { useShoppingListStore } from 'src/stores/shoppingListStore';
    import StockItemApiService from 'src/services/api/stockItemApiService';
    import type { Recipe, RecipeCostLine } from 'src/models/recipe';
    import type { SubstituteOption } from 'src/components/recipes/recipeSubstituteTypes';
    import type { EditableStep } from 'src/components/recipes/recipeStepEditorTypes';
    import type { EditableStepImage } from 'src/components/recipes/recipeStepImageEditorTypes';

    // Domain vocabulary, not a page constant: the same three values rank
    // recipes in the cookbook's sort. R-003 — one home, four readers.
    const DIFFICULTY_OPTIONS = [...DIFFICULTY_VALUES];

    const $q = useQuasar();
    const route = useRoute();
    const router = useRouter();

    const recipeStore = useRecipeStore();
    const stockItemStore = useStockItemStore();
    const recipeVocabStore = useRecipeVocabStore();
    const shoppingListStore = useShoppingListStore();
    const mealSlotStore = useMealSlotStore();
    const stockLevelStore = useStockLevelStore();
    const recipeApi = new RecipeApiService();
    const stockItemApi = new StockItemApiService();
    const { stockItems } = storeToRefs(stockItemStore);
    const { recipeCollections } = storeToRefs(recipeStore);
    const { cuisines, categories, dietaryTags, tools } = storeToRefs(recipeVocabStore);
    const { mealSlotNames } = storeToRefs(mealSlotStore);

    const { moneyEnabled } = useMoneyEnabled();
    const { nutritionEnabled, isComplex } = useNutritionMode();
    const { batchEnabled } = useBatchEnabled();
    const { showRecipeImages } = useImagePrefs();
    const { addItems } = useShoppingListActions();
    const recipeExport = useRecipeExport();

    const compact = computed(() => $q.screen.lt.sm);
    const recipeId = computed(() => String(route.params.id ?? ''));

    const recipe = ref<Recipe | null>(null);
    const form = useRecipeForm();
    const loading = ref(false);
    const loadError = ref<string | null>(null);
    const adjusting = ref(false);
    const newVersionLoading = ref(false);
    const cookGuardOpen = ref(false);
    const photoDialogOpen = ref(false);
    const imageDirty = ref(false);
    const stepImagesDirty = ref(false);
    const imageVersion = ref(0);
    const litStep = ref<string | null>(null);
    const detailOpen = reactive({
        tags: false, sections: false, cost: false,
        nutrition: false, notes: false, kcal: false, versions: false, photo: false,
    });

    // ── Save ────────────────────────────────────────────────────────────
    // Inline editing, explicit commit. The page shipped with a 500ms debounced
    // autosave behind every popup-edit, which had three failure modes the
    // owner reversed it over: (1) each save ended in `loadRecipe()`, which
    // re-hydrates `form` — so a save firing while a second popup was open
    // rebound that popup to an orphaned row object and dropped the edit;
    // (2) a fresh, not-yet-linked ingredient row failed the anchor check, so
    // every *unrelated* save was refused until it was filled or deleted, with
    // no button to retry from; (3) navigating inside the debounce window sent
    // the PATCH into a torn-down component, so a failure had nowhere to show.
    // An explicit Save fixes all three by construction: nothing re-hydrates
    // mid-edit, validation is reported when the user asks to commit, and the
    // dirty flag is what the route guard reads.
    //
    // D-019 is why the *fields* are never disabled while saving — only the
    // Save button is, which is that rule's stated carve-out.
    type SaveState = 'idle' | 'saving' | 'saved' | 'error';
    const saveState = ref<SaveState>('idle');
    const saveMessage = ref('');
    const dirty = ref(false);
    let idleTimer: ReturnType<typeof setTimeout> | null = null;

    /** Every edit path lands here. It records that there is something to
     *  save; it never saves. */
    function markDirty() {
        dirty.value = true;
        // A previous failure is no longer describing the current form.
        if (saveState.value === 'error') saveState.value = 'idle';
    }

    /** Mirrors the server's `recipe_ingredient_anchor` CHECK and the name
     *  requirement, as human sentences. Empty = safe to send. */
    const saveBlockers = computed(() => {
        const out: string[] = [];
        if (!form.name.trim()) out.push('the recipe needs a name');
        const halfBuilt = form.ingredients.filter((i) => !i.stock_item_id && !i.raw_text).length;
        if (halfBuilt > 0) {
            out.push(halfBuilt === 1
                ? '1 ingredient has no item or text yet'
                : `${halfBuilt} ingredients have no item or text yet`);
        }
        return out;
    });

    /** True for a row that would block the save — used to point at the row
     *  rather than only naming a count in the message. */
    function isHalfBuilt(row: IngredientForm): boolean {
        return !row.stock_item_id && !row.raw_text;
    }

    const canSave = computed(() => dirty.value && saveState.value !== 'saving');

    async function onSave() {
        const src = recipe.value;
        if (!src || saveState.value === 'saving') return;
        if (saveBlockers.value.length > 0) {
            saveState.value = 'error';
            saveMessage.value = `Not saved — ${saveBlockers.value.join(', and ')}.`;
            return;
        }
        saveState.value = 'saving';
        saveMessage.value = 'Saving…';
        try {
            const command = buildUpdateCommand(form, src, {
                image: imageDirty.value,
                stepImages: stepImagesDirty.value,
            });
            const didImageChange = imageDirty.value;
            await recipeStore.updateRecipeAsync(command);
            // Safe to re-hydrate here in a way autosave never was: the user
            // asked to commit, so nothing is mid-edit. This is what picks up
            // the server-derived values the page reads (cost, cookability,
            // per-ingredient expiry) rather than recomputing them.
            await loadRecipe();
            if (didImageChange) imageVersion.value++;
            dirty.value = false;
            saveState.value = 'saved';
            saveMessage.value = 'Saved';
            if (idleTimer) clearTimeout(idleTimer);
            idleTimer = setTimeout(() => { saveState.value = 'idle'; }, 1600);
        } catch (err) {
            saveState.value = 'error';
            saveMessage.value = `Couldn't save. ${toastCaption(err)}`;
        }
    }

    /** Discard: re-hydrate from the last loaded recipe. No refetch — the point
     *  is to undo local edits, and `recipe.value` is what they departed from. */
    function onDiscard() {
        const src = recipe.value;
        if (!src) return;
        $q.dialog({
            title: 'Discard changes',
            message: 'Throw away every change you’ve made since the last save?',
            cancel: true,
            ok: { label: 'Discard', color: 'negative' },
        }).onOk(() => {
            hydrateRecipeForm(form, src);
            imageDirty.value = false;
            stepImagesDirty.value = false;
            dirty.value = false;
            saveState.value = 'idle';
        });
    }

    async function loadRecipe() {
        loading.value = true;
        loadError.value = null;
        try {
            const fresh = await recipeApi.getAsync(recipeId.value);
            recipe.value = fresh;
            hydrateRecipeForm(form, fresh);
            imageDirty.value = false;
            stepImagesDirty.value = false;
        } catch (err) {
            loadError.value = toastCaption(err) || "Couldn't load this recipe.";
        } finally {
            loading.value = false;
        }
        // After the form is hydrated, so `missingIngredients` is current.
        // Deliberately not awaited by callers: the page is fully usable while
        // the chips fill in.
        void loadSubstitutes();
    }

    // ── Derived display ─────────────────────────────────────────────────
    const collectionName = computed(
        () => recipeCollections.value.find((c) => c.recipe_collection_id === form.recipe_collection_id)?.name ?? '',
    );
    const cuisineName = computed(() => cuisines.value.find((c) => c.cuisine_id === form.cuisine_id)?.name ?? '');
    const categoryName = computed(() => categories.value.find((c) => c.category_id === form.category_id)?.name ?? '');

    const collectionOptions = computed(() =>
        recipeCollections.value.map((c) => ({ label: c.name, value: c.recipe_collection_id })));
    const cuisineOptions = computed(() => cuisines.value.map((c) => ({ label: c.name, value: c.cuisine_id })));
    const categoryOptions = computed(() => categories.value.map((c) => ({ label: c.name, value: c.category_id })));
    const dietaryTagOptions = computed(() => dietaryTags.value.map((t) => ({ label: t.name, value: t.dietary_tag_id })));
    const toolSelectOptions = computed(() => tools.value.map((t) => ({ label: t.name, value: t.tool_id })));

    // `time_of_day` reads the household's own meal-slot names; the seed
    // constant is only the pre-first-load fallback.
    const timeOfDayOptions = computed(() =>
        (mealSlotNames.value.length > 0 ? mealSlotNames.value : [...DEFAULT_MEAL_SLOTS]));

    const totalMinutes = computed(() => {
        const p = form.prep_time_minutes ?? 0;
        const c = form.cook_time_minutes ?? 0;
        return p + c > 0 ? p + c : null;
    });
    const headlineKcal = computed(() => {
        if (isComplex.value && recipe.value?.nutrition?.kcal) return Math.round(recipe.value.nutrition.kcal);
        return form.kcal ?? null;
    });

    const photoUrl = computed(() => {
        if (imageDirty.value) return form.image;
        if (showRecipeImages.value && recipe.value?.has_image) {
            return recipeImageUrl(recipe.value.recipe_id, imageVersion.value);
        }
        return null;
    });
    // Whether a photo *exists* — independent of whether photos are displayed,
    // which is a viewing preference (the bug fixed on the old page 2026-08-19).
    const hasPhoto = computed(() => (imageDirty.value ? !!form.image : !!recipe.value?.has_image));

    function ingredientLabel(row: IngredientForm): string {
        if (row.stock_item_id) {
            return stockItems.value.find((s) => s.stock_item_id === row.stock_item_id)?.name
                ?? row.raw_text ?? 'Unknown item';
        }
        return row.raw_text || 'Unnamed ingredient';
    }

    /** Ingredients bucketed by section, in section order, with the unsectioned
     *  rows first under no heading — matching how the list reads on paper.
     *
     *  Sections with no rows are rendered too. Skipping them (which this page
     *  shipped doing) made a brand-new section invisible the moment it was
     *  created, so there was no visible place to move anything into and the
     *  feature read as broken. An empty section shows its own hint instead. */
    const ingredientGroups = computed(() => {
        const flat = form.ingredients.filter((i) => !i.section_client_id);
        const groups: { key: string; name: string; rows: IngredientForm[] }[] = [];
        if (flat.length > 0) groups.push({ key: 'main', name: '', rows: flat });
        for (const sec of [...form.sections].sort((a, b) => a.sequence - b.sequence)) {
            groups.push({
                key: sec.client_id,
                name: sec.name || 'Untitled section',
                rows: form.ingredients.filter((i) => i.section_client_id === sec.client_id),
            });
        }
        return groups;
    });

    // ── Substitutes ─────────────────────────────────────────────────────
    // Fetched per missing ingredient, because "what could I use instead" is
    // only a question when something is actually absent. N is the number of
    // missing rows — small, and the fan-out is the same shape the old page
    // used for its bulk dialog.
    const substitutesFor = ref(new Map<string, SubstituteOption[]>());

    async function loadSubstitutes() {
        const targets = missingIngredients.value.map((i) => i.stock_item_id);
        if (targets.length === 0) {
            substitutesFor.value = new Map();
            return;
        }
        const next = new Map<string, SubstituteOption[]>();
        const results = await Promise.allSettled(
            targets.map((id) => stockItemApi.getDetailAsync(id)),
        );
        results.forEach((res, i) => {
            const id = targets[i]!;
            // A single failed lookup shouldn't cost the others their chip, and
            // it isn't worth a toast: substitutes are an enhancement to a row
            // that already reads "Missing" correctly without them.
            if (res.status !== 'fulfilled') return;
            const entries = (res.value.substitutes ?? []).map((sub) => ({
                sub,
                inStock: !isMissingItem(sub.stock_item_id),
            }));
            if (entries.length > 0) next.set(id, entries);
        });
        substitutesFor.value = next;
    }

    function substitutesForRow(row: IngredientForm): SubstituteOption[] {
        if (!row.stock_item_id) return [];
        return substitutesFor.value.get(row.stock_item_id) ?? [];
    }

    /** Missing rows that a substitute you already have would cover. This is
     *  the fact that changes tonight's answer, so the status strip says it. */
    const coverableCount = computed(() =>
        missingIngredients.value.filter(
            (i) => (substitutesFor.value.get(i.stock_item_id) ?? []).some((e) => e.inStock),
        ).length);

    function isMissingItem(stockItemId: string | null | undefined): boolean {
        if (!stockItemId) return false;
        const item = stockItems.value.find((s) => s.stock_item_id === stockItemId);
        return !item || Boolean(item.is_out_of_stock);
    }

    // Server's per-ingredient expiry verdict, read off the loaded recipe so the
    // chips and the cookbook's expiring filter share one horizon (as the old
    // page does). Keyed by stock item, not row.
    const expiringItems = computed(() => {
        const map = new Map<string, { expired: boolean; date: string | null }>();
        for (const ing of recipe.value?.ingredients ?? []) {
            if (!ing.stock_item_id || !ing.is_expiring) continue;
            map.set(ing.stock_item_id, { expired: ing.is_expired, date: ing.expiry_date });
        }
        return map;
    });
    function expiringChipFor(stockItemId: string | null | undefined) {
        if (!stockItemId) return null;
        const hit = expiringItems.value.get(stockItemId);
        if (!hit) return null;
        const when = hit.date ? formatDate(hit.date) : null;
        return hit.expired
            ? { label: 'Expired', colour: 'negative', icon: ICONS.error, tooltip: when ? `Expired ${when}` : 'Past its expiry date' }
            : { label: 'Use soon', colour: 'warning', icon: ICONS.event_busy, tooltip: when ? `Expires ${when}` : 'Expiring soon' };
    }
    const atRiskCount = computed(() => expiringItems.value.size);
    const atRiskHeadline = computed(() => {
        const names = [...expiringItems.value.keys()]
            .map((id) => stockItems.value.find((s) => s.stock_item_id === id)?.name)
            .filter(Boolean);
        if (names.length === 1) return `${names[0]} needs using`;
        return `${atRiskCount.value} ingredients need using`;
    });

    const missingIngredients = computed(() => {
        const r = recipe.value;
        if (!r) return [];
        return r.ingredients
            .filter((i): i is typeof i & { stock_item_id: string; stock_item_name: string } =>
                i.is_missing && i.stock_item_id !== null)
            .filter((i, idx, arr) => arr.findIndex((x) => x.stock_item_id === i.stock_item_id) === idx);
    });
    const cookableNow = computed<boolean | null>(() => recipe.value?.cookable ?? false);
    const unlinkedCount = computed(() => recipe.value?.unlinked_ingredient_count ?? 0);
    const cookableHeadline = computed(() => {
        if (unlinkedCount.value > 0 && missingIngredients.value.length === 0) {
            return `${unlinkedCount.value} ingredient${unlinkedCount.value === 1 ? '' : 's'} to link`;
        }
        if (missingIngredients.value.length === 0) return 'Everything in stock';
        return `${missingIngredients.value.length} ingredient${missingIngredients.value.length === 1 ? '' : 's'} missing`;
    });
    const cookableCaption = computed(() =>
        cookableNow.value === null ? 'Link them to know for sure' : 'You can cook this now');

    const showCostCell = computed(() => {
        const r = recipe.value;
        if (!r) return false;
        return r.estimated_cost !== null
            || (r.estimated_cost_lines ?? []).some((l) => l.reason !== 'no_link');
    });
    function costLineReason(line: RecipeCostLine): string {
        switch (line.reason) {
            case 'no_link': return 'Not linked to a stock item';
            case 'no_price': return 'No price recorded yet';
            case 'unit_mismatch':
                return line.priced_unit ? `Priced per ${line.priced_unit} — can't convert` : "Units don't match";
            default: return '';
        }
    }

    const versionSiblings = computed(() => recipe.value?.version_siblings ?? []);

    // ── Method ──────────────────────────────────────────────────────────
    const topLevelSteps = computed(() =>
        [...form.steps].filter((s) => !s.parent_client_id).sort((a, b) => a.sequence - b.sequence));
    function subStepsOf(step: EditableStep) {
        return form.steps
            .filter((s) => s.parent_client_id === step.client_id)
            .sort((a, b) => a.sequence - b.sequence);
    }
    const freeformLines = computed(() =>
        (form.instructions ?? '').split('\n').map((l) => l.trim()).filter((l) => l.length > 0));
    const methodCountLabel = computed(() => {
        if (form.steps_mode === 'structured') {
            const n = topLevelSteps.value.length;
            return `${n} step${n === 1 ? '' : 's'}`;
        }
        if (form.steps_mode === 'image') {
            const n = (recipe.value?.step_images ?? []).length;
            return `${n} photo${n === 1 ? '' : 's'}`;
        }
        return `${freeformLines.value.length} line${freeformLines.value.length === 1 ? '' : 's'}`;
    });
    /** Ingredient names a structured step declares — the only mode that has
     *  the link, which is why the highlight is structured-only. */
    function usesLabel(step: EditableStep): string {
        const names = step.ingredient_client_ids
            .map((id) => form.ingredients.find((i) => i.client_id === id))
            .filter((i): i is IngredientForm => !!i)
            .map((i) => ingredientLabel(i));
        return names.join(', ');
    }
    const litIngredients = computed(() => {
        const ids = new Set<string>();
        if (!litStep.value) return ids;
        const step = form.steps.find((s) => s.client_id === litStep.value);
        for (const id of step?.ingredient_client_ids ?? []) ids.add(id);
        return ids;
    });

    // The steps editor's option shape is {value,label} for all three lists.
    const ingredientOptions = computed(() =>
        form.ingredients.map((i) => ({ value: String(i.client_id), label: ingredientLabel(i) })));
    const toolOptions = computed(() => tools.value.map((t) => ({ value: t.tool_id, label: t.name })));
    const sectionOptions = computed(() =>
        form.sections.map((s) => ({ value: s.client_id, label: s.name || 'Untitled section' })));

    function onStepsChanged(steps: EditableStep[]) {
        form.steps = steps;
        markDirty();
    }
    function onStepImagesChanged(images: EditableStepImage[]) {
        form.step_images = images;
        stepImagesDirty.value = true;
        markDirty();
    }

    // ── Captions for the collapsed Details rows ─────────────────────────
    const tagsCaption = computed(() => {
        const names = [
            ...form.dietary_tag_ids.map((id) => dietaryTags.value.find((t) => t.dietary_tag_id === id)?.name),
            ...form.tool_ids.map((id) => tools.value.find((t) => t.tool_id === id)?.name),
        ].filter(Boolean);
        return names.length > 0 ? names.join(' · ') : 'None';
    });
    const orderedSections = computed(() =>
        [...form.sections].sort((a, b) => a.sequence - b.sequence));

    const organiseCaption = computed(() => {
        if (form.sections.length === 0) return 'One flat list';
        return orderedSections.value.map((s) => s.name || 'Untitled').join(' · ');
    });
    const costCaption = computed(() => {
        const r = recipe.value;
        if (!r) return '';
        const total = r.estimated_cost !== null ? formatMoney(r.estimated_cost) : 'No estimate';
        return `${total} · ${r.estimated_cost_priced_count} of ${r.estimated_cost_total_count} priced`;
    });
    const nutritionCaption = computed(() => {
        const n = recipe.value?.nutrition;
        if (!n) return '';
        return n.kcal ? `${Math.round(n.kcal)} kcal per serving` : 'Per serving';
    });
    const notesCaption = computed(() => {
        const bits: string[] = [];
        if (form.source) bits.push('Has a source');
        bits.push(form.notes ? 'Has notes' : 'No notes');
        return bits.join(' · ');
    });

    function openDetail(which: 'cost') {
        detailOpen[which] = true;
    }

    // ── Ingredient + section mutations ──────────────────────────────────
    function addIngredient() {
        form.ingredients.push({
            client_id: newClientId(),
            stock_item_id: null,
            raw_text: null,
            quantity: null,
            unit: null,
            notes: null,
            section_client_id: null,
            is_optional: false,
        } as IngredientForm);
        markDirty();
        // A fresh row has no anchor yet, so open the editor on it straight
        // away rather than leaving a blank line the user has to discover is
        // clickable — and which would block the save if they didn't.
        const added = form.ingredients[form.ingredients.length - 1];
        if (added?.client_id) openRowEditor(String(added.client_id));
    }
    function removeIngredient(clientId: string) {
        const idx = form.ingredients.findIndex((i) => i.client_id === clientId);
        if (idx < 0) return;
        form.ingredients.splice(idx, 1);
        // A step that pointed at this row would otherwise keep a dangling
        // reference, which survives the PATCH as a step that "uses" nothing.
        for (const step of form.steps) {
            step.ingredient_client_ids = step.ingredient_client_ids.filter((id) => id !== clientId);
        }
        markDirty();
    }

    /** Ingredient order is array order — there is no `sequence` on the wire,
     *  and arrays are sent with replace semantics — so a move is a splice. */
    function moveIngredient(clientId: string, delta: -1 | 1) {
        const from = form.ingredients.findIndex((i) => i.client_id === clientId);
        const to = from + delta;
        if (from < 0 || to < 0 || to >= form.ingredients.length) return;
        const [row] = form.ingredients.splice(from, 1);
        if (row) form.ingredients.splice(to, 0, row);
        markDirty();
    }

    // ── The row editor ──────────────────────────────────────────────────
    const rowEditorOpen = ref(false);
    const rowEditorFor = ref<string | null>(null);
    const rowEditorRow = computed(
        () => form.ingredients.find((i) => i.client_id === rowEditorFor.value) ?? null);

    function openRowEditor(clientId: string) {
        rowEditorFor.value = clientId;
        rowEditorOpen.value = true;
    }

    /** The editor hands back a whole patch rather than mutating the row, so
     *  Cancel is a real cancel (R-006 safe mutations). */
    function onRowEditorSave(patch: IngredientPatch) {
        const row = form.ingredients.find((i) => i.client_id === rowEditorFor.value);
        if (!row) return;
        Object.assign(row, patch);
        markDirty();
    }

    // ── Sections ────────────────────────────────────────────────────────
    /** `sequence` is what the server sorts on, so it is kept dense and
     *  0-based after every structural change rather than left with gaps. */
    function resequenceSections() {
        [...form.sections]
            .sort((a, b) => a.sequence - b.sequence)
            .forEach((sec, i) => { sec.sequence = i; });
    }
    function addSection() {
        form.sections.push({ client_id: newClientId(), sequence: form.sections.length, name: '' });
        resequenceSections();
        markDirty();
    }
    function removeSection(clientId: string) {
        const idx = form.sections.findIndex((s) => s.client_id === clientId);
        if (idx < 0) return;
        form.sections.splice(idx, 1);
        // Rows in a deleted section fall back to the flat list, mirroring the
        // server's ON DELETE SET NULL.
        for (const ing of form.ingredients) {
            if (ing.section_client_id === clientId) ing.section_client_id = null;
        }
        // Steps carry a section reference too (C-4 Chunk 10), and a stale one
        // would point at a section the PATCH no longer contains.
        for (const step of form.steps) {
            if (step.section_client_id === clientId) step.section_client_id = null;
        }
        resequenceSections();
        markDirty();
    }
    function moveSection(clientId: string, delta: -1 | 1) {
        const ordered = [...form.sections].sort((a, b) => a.sequence - b.sequence);
        const from = ordered.findIndex((s) => s.client_id === clientId);
        const to = from + delta;
        if (from < 0 || to < 0 || to >= ordered.length) return;
        const [sec] = ordered.splice(from, 1);
        if (sec) ordered.splice(to, 0, sec);
        ordered.forEach((s, i) => { s.sequence = i; });
        markDirty();
    }

    /** The flat, ordered ingredient list the organise disclosure walks —
     *  reading order, so ↑/↓ mean what they look like they mean. */
    const orderedIngredients = computed(() =>
        ingredientGroups.value.flatMap((g) =>
            g.rows.map((row) => ({ row, section: g.name }))));

    // ── Photo ───────────────────────────────────────────────────────────
    function onPickPhoto(image: { dataUrl: string }) {
        form.image = image.dataUrl;
        imageDirty.value = true;
        markDirty();
    }
    function onPickPhotoDataUrl(dataUrl: string) {
        form.image = dataUrl;
        imageDirty.value = true;
        markDirty();
    }
    function onClearPhoto() {
        form.image = null;
        imageDirty.value = true;
        markDirty();
    }

    // ── Actions ─────────────────────────────────────────────────────────
    async function onToggleFavourite() {
        if (!recipe.value) return;
        try {
            await recipeStore.toggleFavouriteAsync(recipe.value);
            await loadRecipe();
        } catch (err) {
            $q.notify({ type: 'negative', position: 'bottom-right', message: "Couldn't update favourite.", caption: toastCaption(err) });
        }
    }

    function onStartCookMode() {
        if (!recipe.value) return;
        // `dirty` is a real guard reason now — the shared helper has always
        // taken it, and the autosave page had nothing truthful to pass.
        if (needsCookGuard(recipe.value, dirty.value)) {
            cookGuardOpen.value = true;
            return;
        }
        goToCookMode();
    }
    function goToCookMode() {
        void router.push(`/cookbook/${recipeId.value}/cook`);
    }
    /** The guard's "save and start" branch. Cook mode reads the *server's*
     *  recipe, so starting without committing would cook the old version. */
    async function onSaveAndCook() {
        await onSave();
        if (saveState.value === 'error') return;
        goToCookMode();
    }

    function onPrint() {
        if (!recipeId.value) return;
        recipeExport.openPrintView(recipeId.value);
    }

    async function onNewVersion() {
        if (!recipe.value) return;
        newVersionLoading.value = true;
        try {
            const created = await recipeApi.createNewVersionAsync(recipe.value.recipe_id);
            // CreatedResponse carries either `recipe_id` (created() body) or
            // `id` (Location-style). Cover both, as the old page does.
            const newId = (created as Record<string, unknown>).recipe_id as string | undefined
                ?? created.id;
            await recipeStore.getRecipesAsync();
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: 'New version created.',
                caption: 'Both versions are equal peers — pick either when scheduling.',
            });
            // Stay on the new layout so a comparison session isn't kicked back.
            if (newId) void router.push(`/cookbook/${newId}/new`);
        } catch (err) {
            $q.notify({ type: 'negative', position: 'bottom-right', message: "Couldn't create a new version.", caption: toastCaption(err) });
        } finally {
            newVersionLoading.value = false;
        }
    }

    function onDelete() {
        if (!recipe.value) return;
        $q.dialog({
            title: 'Delete recipe',
            message: `Delete "${recipe.value.name}"? This can't be undone.`,
            cancel: true,
            ok: { label: 'Delete', color: 'negative' },
        }).onOk(() => { void doDelete(); });
    }
    async function doDelete() {
        if (!recipe.value) return;
        try {
            await recipeStore.deleteRecipeAsync(recipe.value.recipe_id);
            await router.push('/cookbook');
        } catch (err) {
            $q.notify({ type: 'negative', position: 'bottom-right', message: "Couldn't delete.", caption: toastCaption(err) });
        }
    }

    async function onAdjustMeals(delta: number) {
        if (!recipe.value) return;
        adjusting.value = true;
        try {
            await recipeStore.adjustMealsAsync(recipe.value.recipe_id, delta);
            await loadRecipe();
        } catch (err) {
            $q.notify({ type: 'negative', position: 'bottom-right', message: 'Could not update meals.', caption: toastCaption(err) });
        } finally {
            adjusting.value = false;
        }
    }

    // Reuses the shared picker (and its list-target step) rather than a
    // second, thinner add path — same flow the old page runs (R-001).
    const pickerOpen = ref(false);
    const pickerRef = ref<InstanceType<typeof RecipeIngredientPickerDialog> | null>(null);
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

    function goToSibling(id: string) {
        void router.push(`/cookbook/${id}/new`);
    }

    // ── Mount / unmount / leaving ───────────────────────────────────────
    onMounted(async () => {
        await Promise.all([
            recipeStore.ensureCollectionsLoadedAsync(),
            stockItemStore.ensureLoadedAsync(),
            stockLevelStore.ensureLoadedAsync(),
            recipeVocabStore.ensureLoadedAsync(),
            shoppingListStore.ensureLoadedAsync(),
            mealSlotStore.ensureLoadedAsync(),
        ]);
        await loadRecipe();
        window.addEventListener('beforeunload', onBeforeUnload);
    });

    onBeforeUnmount(() => {
        // The page shipped with neither of these. The autosave timer it had
        // outlived the component, so a PATCH could land with nothing mounted
        // to report its failure to.
        if (idleTimer) clearTimeout(idleTimer);
        window.removeEventListener('beforeunload', onBeforeUnload);
    });

    /** Tab close / reload. The browser shows its own generic prompt; the
     *  string is ignored by every current engine but `preventDefault` is what
     *  actually arms it. */
    function onBeforeUnload(e: BeforeUnloadEvent) {
        if (!dirty.value) return;
        e.preventDefault();
        e.returnValue = '';
    }

    // In-app navigation — the Back arrow, a sibling version, cook mode.
    onBeforeRouteLeave((_to, _from, next) => {
        if (!dirty.value) {
            next();
            return;
        }
        $q.dialog({
            title: 'Unsaved changes',
            message: 'You have changes that haven’t been saved yet.',
            cancel: { label: 'Stay', flat: true, noCaps: true },
            ok: { label: 'Leave without saving', color: 'negative', noCaps: true },
        })
            .onOk(() => { next(); })
            .onCancel(() => { next(false); });
    });

    // Switching recipes in place (a sibling version) is a fresh load; the
    // guard above has already dealt with any unsaved work.
    watch(recipeId, () => {
        dirty.value = false;
        saveState.value = 'idle';
        void loadRecipe();
    });
</script>

<style scoped lang="scss">
    /* Fraunces is the DISPLAY face only — recipe title + section labels.
       Body text deliberately inherits the user's chosen font (Settings →
       Appearance, themeService FONT_FAMILY_CSS): overriding that here would
       silently ignore their preference on this one page. */
    .rn {
        --rn-display: 'Fraunces Variable', 'Fraunces', Georgia, serif;
    }

    /* ── Masthead ─────────────────────────────────────────────────────── */
    .rn__masthead {
        display: grid;
        grid-template-columns: 220px 1fr;
        gap: var(--space-5, 20px);
        align-items: start;
    }
    .rn__photo {
        width: 100%;
        aspect-ratio: 1 / 1;
        border-radius: var(--radius-lg, 10px);
        overflow: hidden;
        border: 1px solid var(--border-default);
    }
    .rn__photoimg { width: 100%; height: 100%; object-fit: cover; display: block; }
    .rn__photoempty { width: 100%; height: 100%; background: var(--surface-sunken); }
    .rn__photo--empty {
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        gap: var(--space-2, 8px);
        background: var(--surface-sunken);
        color: var(--text-muted);
        cursor: pointer;
        font: inherit;
        font-size: 0.875rem;
    }
    .rn__photo--empty:hover { border-color: var(--brand-primary); color: var(--brand-primary); }

    .rn__identity { min-width: 0; }
    .rn__backrow { display: flex; align-items: center; gap: var(--space-2, 8px); }
    .rn__title {
        font-family: var(--rn-display);
        font-size: 2rem;
        font-weight: 600;
        line-height: 1.15;
        letter-spacing: -0.01em;
        margin: 0;
        min-width: 0;
        text-wrap: balance;
    }
    .rn__eyebrow {
        display: flex; flex-wrap: wrap; align-items: center; gap: var(--space-2, 8px);
        margin-top: var(--space-2, 8px);
        color: var(--text-secondary);
        font-size: 0.875rem;
    }
    .rn__dot { color: var(--text-muted); }

    /* The inline-edit affordance: reads as text, reveals on hover/focus. */
    .rn__edit {
        border-radius: var(--radius-sm, 4px);
        cursor: pointer;
        padding: 0 3px;
        margin: 0 -3px;
        box-shadow: inset 0 -1px 0 0 transparent;
        transition: background 100ms ease, box-shadow 100ms ease;
    }
    .rn__edit:hover {
        background: var(--overlay-hover);
        box-shadow: inset 0 -1px 0 0 var(--border-strong);
    }
    .rn__edit:focus-visible {
        outline: 2px solid var(--brand-primary);
        outline-offset: 1px;
    }

    .rn__facts {
        display: flex; flex-wrap: wrap;
        gap: var(--space-2, 8px) var(--space-6, 24px);
        margin-top: var(--space-4, 16px);
    }
    .rn__fact { display: flex; flex-direction: column; gap: 2px; min-width: 60px; }
    .rn__factk {
        font-size: 0.6875rem; font-weight: 700; letter-spacing: 0.07em;
        text-transform: uppercase; color: var(--text-muted);
    }
    .rn__factv { font-size: 1rem; font-weight: 600; font-variant-numeric: tabular-nums; }

    /* ── Actions ──────────────────────────────────────────────────────── */
    .rn__actions {
        display: flex; align-items: center; gap: var(--space-2, 8px);
        margin-top: var(--space-5, 20px);
        padding-top: var(--space-4, 16px);
        border-top: 1px solid var(--divider);
        flex-wrap: wrap;
    }
    .rn__delete { margin-left: auto; }

    /* ── Status strip ─────────────────────────────────────────────────── */
    .rn__status {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1px;
        margin-top: var(--space-5, 20px);
        background: var(--border-default);
        border: 1px solid var(--border-default);
        border-radius: var(--radius-lg, 10px);
        overflow: hidden;
    }
    .rn__cell {
        background: var(--surface-component);
        padding: var(--space-3, 12px) var(--space-4, 16px);
        display: flex; flex-direction: column; gap: 2px;
        position: relative;
    }
    /* Severity as an edge stripe rather than a washed cell: it survives both
       themes and doesn't drown the text it's qualifying (D-002/D-013). */
    .rn__cell--bad::before,
    .rn__cell--warn::before,
    .rn__cell--ok::before {
        content: '';
        position: absolute; left: 0; top: 0; bottom: 0; width: 3px;
    }
    .rn__cell--bad::before { background: var(--semantic-negative); }
    .rn__cell--warn::before { background: var(--semantic-warning); }
    .rn__cell--ok::before { background: var(--semantic-positive); }
    .rn__cellk {
        font-size: 0.6875rem; font-weight: 700; letter-spacing: 0.07em;
        text-transform: uppercase; color: var(--text-muted);
    }
    .rn__cellv { font-weight: 600; }
    .rn__cellsub { font-size: 0.8125rem; color: var(--text-muted); }
    .rn__pool { display: flex; align-items: center; gap: var(--space-2, 8px); flex-wrap: wrap; }
    .rn__link {
        background: none; border: 0; padding: 0;
        font: inherit; font-size: 0.8125rem; font-weight: 600;
        color: var(--brand-primary); cursor: pointer; text-align: left;
    }
    .rn__link:hover { text-decoration: underline; }
    .rn__link:focus-visible { outline: 2px solid var(--brand-primary); outline-offset: 2px; }

    /* ── Body ─────────────────────────────────────────────────────────── */
    .rn__body {
        display: grid;
        grid-template-columns: minmax(280px, 34%) 1fr;
        gap: var(--space-8, 32px);
        margin-top: var(--space-6, 24px);
        align-items: start;
    }
    /* The rail follows the method down a long recipe, and each pane scrolls
       inside itself rather than the page (owner ask). */
    .rn__rail { position: sticky; top: var(--space-4, 16px); }
    .rn__pane {
        max-height: calc(100vh - 220px);
        overflow-y: auto;
        overscroll-behavior: contain;
    }
    .rn__sechead {
        display: flex; align-items: center; gap: var(--space-3, 12px);
        padding-bottom: var(--space-2, 8px);
        margin-bottom: var(--space-3, 12px);
        border-bottom: 1px solid var(--border-default);
    }
    .rn__sectitle {
        font-family: var(--rn-display);
        font-size: 0.9375rem; font-weight: 700;
        letter-spacing: 0.08em; text-transform: uppercase;
        color: var(--text-secondary);
        margin: 0;
    }
    .rn__seccount {
        font-size: 0.8125rem; color: var(--text-muted);
        font-variant-numeric: tabular-nums; margin-left: auto;
    }
    .rn__modes { margin-left: var(--space-2, 8px); }

    .rn__ingsec {
        font-family: var(--rn-display);
        font-size: 0.75rem; font-weight: 700; letter-spacing: 0.08em;
        text-transform: uppercase; color: var(--brand-primary);
        display: flex; align-items: center; gap: var(--space-2, 8px);
        padding: var(--space-3, 12px) var(--space-2, 8px) var(--space-1, 4px);
    }
    .rn__ingsec::after {
        content: ''; flex: 1; height: 1px; background: var(--border-default);
    }
    .rn__ing { list-style: none; margin: 0; padding: 0; }
    .rn__ing li {
        display: grid;
        grid-template-columns: auto 1fr;
        gap: var(--space-3, 12px);
        align-items: baseline;
        padding: var(--space-2, 8px);
        border-bottom: 1px solid var(--divider);
        border-radius: var(--radius-sm, 4px);
        position: relative;
    }
    .rn__ing li:hover { background: var(--overlay-hover); }
    .rn__ing--lit {
        background: var(--brand-primary-soft) !important;
        box-shadow: inset 3px 0 0 0 var(--brand-primary);
    }
    .rn__qty {
        font-variant-numeric: tabular-nums; font-weight: 700;
        white-space: nowrap; min-width: 58px;
    }
    .rn__ingname { min-width: 0; }
    .rn__ingnote { display: block; font-size: 0.8125rem; color: var(--text-muted); }
    .rn__chip { margin-left: var(--space-1, 4px); }
    .rn__chip--unlinked { background: var(--surface-sunken); color: var(--text-muted); }
    .rn__ingact {
        position: absolute; right: var(--space-1, 4px); top: 50%;
        transform: translateY(-50%);
        display: flex; align-items: center; gap: var(--space-1, 4px);
        opacity: 0;
        transition: opacity 120ms ease;
        background: var(--surface-component);
        border-radius: var(--radius-sm, 4px);
    }
    .rn__ing li:hover .rn__ingact,
    .rn__ing li:focus-within .rn__ingact { opacity: 1; }
    .rn__add { margin-top: var(--space-3, 12px); width: 100%; }

    /* Method — the v1 treatment the owner preferred: roomy rows, a filled
       brand-soft numeral, generous measure. */
    .rn__steps {
        list-style: none; counter-reset: rnstep;
        margin: 0; padding: 0;
        display: flex; flex-direction: column; gap: var(--space-4, 16px);
    }
    .rn__steps > li {
        counter-increment: rnstep;
        display: grid; grid-template-columns: 34px 1fr;
        gap: var(--space-4, 16px);
        align-items: start;
        padding: var(--space-2, 8px);
        border-radius: var(--radius-md, 6px);
    }
    .rn__steps > li::before {
        content: counter(rnstep);
        display: flex; align-items: center; justify-content: center;
        width: 34px; height: 34px; border-radius: 50%;
        background: var(--brand-primary-soft);
        color: var(--brand-primary);
        font-weight: 700; font-variant-numeric: tabular-nums;
    }
    .rn__steps > li.rn__step--lit { background: var(--overlay-hover); }
    .rn__steps > li.rn__step--lit::before {
        background: var(--brand-primary); color: var(--text-on-primary);
    }
    .rn__steps p { margin: 0; max-width: 62ch; line-height: 1.6; }
    .rn__hint { display: block; font-size: 0.8125rem; color: var(--text-muted); margin-top: var(--space-1, 4px); }
    .rn__uses { display: block; font-size: 0.75rem; color: var(--text-muted); margin-top: var(--space-2, 8px); }
    .rn__substeps { margin: var(--space-2, 8px) 0 0; padding-left: var(--space-5, 20px); color: var(--text-secondary); }
    .rn__free p { margin: 0 0 var(--space-3, 12px); max-width: 62ch; line-height: 1.6; }
    .rn__empty { color: var(--text-muted); font-size: 0.875rem; }
    .rn__hintblock { color: var(--text-muted); font-size: 0.8125rem; margin: 0 0 var(--space-3, 12px); }
    .rn__editor { margin-top: var(--space-4, 16px); border-top: 1px solid var(--divider); }

    .rn__details { margin-top: var(--space-8, 32px); border-top: 1px solid var(--divider); }
    .rn__disc { padding: var(--space-3, 12px) var(--space-2, 8px) var(--space-4, 16px); }
    .rn__costtable td { vertical-align: top; }
    .rn__flip { margin-top: var(--space-6, 24px); display: flex; justify-content: center; }

    .rn__savebar {
        position: fixed; bottom: var(--space-5, 20px); left: 50%;
        transform: translateX(-50%); z-index: 6000;
        display: flex; align-items: center; gap: var(--space-2, 8px);
        padding: var(--space-2, 8px) var(--space-4, 16px);
        border-radius: var(--radius-pill, 999px);
        background: var(--surface-elevated);
        border: 1px solid var(--border-default);
        box-shadow: 0 2px 10px var(--overlay-dim);
        font-size: 0.875rem;
        color: var(--text-secondary);
    }
    .rn__savebar--error { border-color: var(--semantic-negative); color: var(--semantic-negative); }

    /* The standing "there is unsaved work" statement. Sits above the transient
       savebar's slot so the two never occupy the same space. */
    .rn__dirty {
        position: fixed; bottom: var(--space-5, 20px); left: 50%;
        transform: translateX(-50%); z-index: 6000;
        display: flex; align-items: center; gap: var(--space-2, 8px);
        padding: var(--space-2, 8px) var(--space-4, 16px);
        border-radius: var(--radius-pill, 999px);
        background: var(--surface-elevated);
        border: 1px solid var(--semantic-warning);
        box-shadow: 0 2px 10px var(--overlay-dim);
        font-size: 0.875rem;
        font-weight: 600;
        color: var(--text-secondary);
    }

    /* The ingredient name is a real <button> (it opens the row editor), so it
       has to be talked back out of looking like one — the row reads as a
       recipe, not a form. `.rn__edit` supplies the hover/focus affordance. */
    .rn__ingbtn {
        appearance: none;
        background: none;
        border: 0;
        font: inherit;
        color: inherit;
        text-align: left;
    }

    .rn__ingsecempty {
        color: var(--text-muted);
        font-size: 0.8125rem;
        margin: 0;
        padding: var(--space-2, 8px);
    }

    .rn__secrow {
        display: flex;
        align-items: center;
        gap: var(--space-2, 8px);
        margin-bottom: var(--space-2, 8px);
    }

    .rn__discsub {
        font-size: 0.75rem; font-weight: 700; letter-spacing: 0.06em;
        text-transform: uppercase; color: var(--text-muted);
        margin: var(--space-5, 20px) 0 var(--space-2, 8px);
    }

    .rn__order {
        list-style: none;
        margin: 0 0 var(--space-3, 12px);
        padding: 0;
    }
    .rn__order li {
        display: flex;
        align-items: center;
        gap: var(--space-2, 8px);
        padding: var(--space-1, 4px) 0;
        border-bottom: 1px solid var(--divider);
    }
    .rn__ordername { flex: 1; min-width: 0; }
    .rn__ordersec {
        margin-left: var(--space-2, 8px);
        font-size: 0.75rem;
        color: var(--text-muted);
    }

    /* ── Phone ────────────────────────────────────────────────────────── */
    @media (max-width: 1023px) {
        .rn__masthead { grid-template-columns: 1fr; }
        .rn__photo { aspect-ratio: 16 / 9; }
        .rn__body { grid-template-columns: 1fr; gap: var(--space-6, 24px); }
        .rn__rail { position: static; }
        /* A phone scrolls the page, not two nested panes. */
        .rn__pane { max-height: none; overflow: visible; }
        .rn__title { font-size: 1.5rem; }
        /* Actions scroll sideways rather than stacking three deep (D-011:
           wide content scrolls inside its own container, never the page). */
        .rn__actions {
            flex-wrap: nowrap;
            overflow-x: auto;
            scrollbar-width: none;
        }
        .rn__actions::-webkit-scrollbar { display: none; }
        .rn__delete { margin-left: 0; }
    }
</style>
