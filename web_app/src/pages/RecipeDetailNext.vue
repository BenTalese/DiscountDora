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
                    v-if="hasPhoto || photoBusy"
                    class="rn__photo"
                    label="Change the recipe photo"
                    shape="rounded"
                    :width="0"
                    :height="0"
                    :busy="photoBusy"
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
                            <span class="rn__edit" tabindex="0">
                                {{ form.name || 'Untitled recipe' }}
                                <q-popup-edit
                                    v-model="form.name"
                                    v-slot="scope"
                                    auto-save
                                    :validate="(v) => !!(v || '').trim()"
                                    @save="onFieldSaved"
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
                            </span>
                        </h1>
                    </div>

                    <div class="rn__eyebrow">
                        <span class="rn__edit" tabindex="0">
                            {{ collectionName || 'No collection' }}
                            <q-popup-edit v-model="form.recipe_collection_id" v-slot="scope" @save="onFieldSaved">
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
                        </span>
                        <span class="rn__dot">·</span>
                        <span class="rn__edit" tabindex="0">
                            {{ cuisineName || 'Any cuisine' }}
                            <q-popup-edit v-model="form.cuisine_id" v-slot="scope" @save="onFieldSaved">
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
                        </span>
                        <span class="rn__dot">·</span>
                        <span class="rn__edit" tabindex="0">
                            {{ categoryName || 'No category' }}
                            <q-popup-edit v-model="form.category_id" v-slot="scope" @save="onFieldSaved">
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
                        </span>
                    </div>

                    <div class="rn__facts">
                        <div class="rn__fact">
                            <span class="rn__factk">Serves</span>
                            <span class="rn__factv rn__edit" tabindex="0">
                                {{ form.servings ?? '—' }}
                                <q-popup-edit v-model.number="form.servings" v-slot="scope" auto-save @save="onFieldSaved">
                                    <q-input v-model.number="scope.value" type="number" min="1" dense autofocus label="Servings" @keyup.enter="scope.set" />
                                </q-popup-edit>
                            </span>
                        </div>
                        <div class="rn__fact">
                            <span class="rn__factk">Prep</span>
                            <span class="rn__factv rn__edit" tabindex="0">
                                {{ form.prep_time_minutes ? form.prep_time_minutes + ' min' : '—' }}
                                <q-popup-edit v-model.number="form.prep_time_minutes" v-slot="scope" auto-save @save="onFieldSaved">
                                    <q-input v-model.number="scope.value" type="number" min="0" dense autofocus label="Prep (min)" @keyup.enter="scope.set" />
                                </q-popup-edit>
                            </span>
                        </div>
                        <div class="rn__fact">
                            <span class="rn__factk">Cook</span>
                            <span class="rn__factv rn__edit" tabindex="0">
                                {{ form.cook_time_minutes ? form.cook_time_minutes + ' min' : '—' }}
                                <q-popup-edit v-model.number="form.cook_time_minutes" v-slot="scope" auto-save @save="onFieldSaved">
                                    <q-input v-model.number="scope.value" type="number" min="0" dense autofocus label="Cook (min)" @keyup.enter="scope.set" />
                                </q-popup-edit>
                            </span>
                        </div>
                        <div v-if="totalMinutes !== null" class="rn__fact">
                            <span class="rn__factk">Total</span>
                            <span class="rn__factv">{{ totalMinutes }} min</span>
                        </div>
                        <div class="rn__fact">
                            <span class="rn__factk">Difficulty</span>
                            <span class="rn__factv rn__edit" tabindex="0">
                                {{ form.difficulty || '—' }}
                                <q-popup-edit v-model="form.difficulty" v-slot="scope" @save="onFieldSaved">
                                    <BaseSelect
                                        v-model="scope.value"
                                        label="Difficulty"
                                        :options="DIFFICULTY_OPTIONS"
                                        clearable
                                        autofocus
                                        @update:model-value="scope.set"
                                    />
                                </q-popup-edit>
                            </span>
                        </div>
                        <div v-if="headlineKcal !== null" class="rn__fact">
                            <span class="rn__factk">Per serving</span>
                            <span class="rn__factv">{{ headlineKcal }} kcal</span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- ═══ Actions — their own full-width row ═══════════════════ -->
            <div class="rn__actions">
                <BaseButton
                    variant="primary"
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
                                        <span class="rn__qty rn__edit" tabindex="0">
                                            {{ formatQuantity(row.quantity, row.unit) || '—' }}
                                            <q-popup-edit v-model="row.quantity" v-slot="scope" auto-save @save="onFieldSaved">
                                                <div class="row q-gutter-sm items-center">
                                                    <q-input v-model.number="scope.value" type="number" min="0" step="any" dense autofocus label="Qty" style="width: 90px" @keyup.enter="scope.set" />
                                                    <q-input v-model="row.unit" dense label="Unit" style="width: 110px" @update:model-value="onFieldSaved" />
                                                </div>
                                            </q-popup-edit>
                                        </span>
                                        <span class="rn__ingname">
                                            <span class="rn__edit" tabindex="0">
                                                {{ ingredientLabel(row) }}
                                                <q-popup-edit v-model="row.stock_item_id" v-slot="scope" @save="onFieldSaved">
                                                    <BaseSelect
                                                        v-model="scope.value"
                                                        label="Stock item"
                                                        :options="stockItemOptions"
                                                        emit-value
                                                        map-options
                                                        use-input
                                                        autofocus
                                                        @update:model-value="scope.set"
                                                    />
                                                </q-popup-edit>
                                            </span>
                                            <q-chip v-if="row.is_optional" dense square size="sm" class="rn__chip">Optional</q-chip>
                                            <q-chip
                                                v-if="!row.stock_item_id"
                                                dense square size="sm"
                                                class="rn__chip rn__chip--unlinked"
                                            >
                                                Not linked
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
                            @update:model-value="onFieldSaved"
                        />
                    </div>

                    <div class="rn__pane">
                        <!-- Structured — the only mode that can tie a step to
                             its ingredients, because it's the only one that
                             stores the link. -->
                        <template v-if="form.steps_mode === 'structured'">
                            <ol v-if="topLevelSteps.length > 0" class="rn__steps">
                                <li
                                    v-for="step in topLevelSteps"
                                    :key="step.client_id"
                                    tabindex="0"
                                    :class="{ 'rn__step--lit': litStep === step.client_id }"
                                    @mouseenter="litStep = step.client_id"
                                    @mouseleave="litStep = null"
                                    @focusin="litStep = step.client_id"
                                    @focusout="litStep = null"
                                >
                                    <p class="rn__edit" tabindex="0">
                                        {{ step.text || 'Empty step' }}
                                        <q-popup-edit v-model="step.text" v-slot="scope" auto-save @save="onFieldSaved">
                                            <q-input v-model="scope.value" type="textarea" autogrow dense autofocus label="Step" />
                                        </q-popup-edit>
                                    </p>
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
                            <div v-if="freeformLines.length > 0" class="rn__free rn__edit" tabindex="0">
                                <p v-for="(line, i) in freeformLines" :key="`f-${i}`">{{ line }}</p>
                                <q-popup-edit v-model="form.instructions" v-slot="scope" auto-save @save="onFieldSaved">
                                    <q-input v-model="scope.value" type="textarea" autogrow dense autofocus label="Instructions" style="min-width: 320px" />
                                </q-popup-edit>
                            </div>
                            <p v-else class="rn__empty rn__edit" tabindex="0">
                                No instructions yet.
                                <q-popup-edit v-model="form.instructions" v-slot="scope" auto-save @save="onFieldSaved">
                                    <q-input v-model="scope.value" type="textarea" autogrow dense autofocus label="Instructions" style="min-width: 320px" />
                                </q-popup-edit>
                            </p>
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
                            @update:model-value="onFieldSaved"
                        />
                        <BaseSelect
                            v-model="form.tool_ids"
                            label="Tools"
                            :options="toolSelectOptions"
                            emit-value map-options multiple use-chips clearable
                            @update:model-value="onFieldSaved"
                        />
                    </div>
                </q-expansion-item>

                <q-expansion-item v-model="detailOpen.sections" dense-toggle label="Ingredient sections" :caption="sectionsCaption">
                    <div class="rn__disc">
                        <p class="rn__hintblock">
                            Groups the ingredient list under headings — "For the sauce", "To serve".
                            A recipe with no sections shows one flat list.
                        </p>
                        <div v-for="(sec, i) in form.sections" :key="sec.client_id" class="row items-center q-gutter-sm q-mb-sm">
                            <q-input
                                v-model="sec.name"
                                dense outlined
                                class="col"
                                label="Section name"
                                @update:model-value="onFieldSaved"
                            />
                            <BaseButton
                                variant="danger-icon"
                                :icon="ICONS.delete"
                                :aria-label="`Remove section ${sec.name || i + 1}`"
                                @click="removeSection(sec.client_id)"
                            />
                        </div>
                        <BaseButton variant="subtle" :icon="ICONS.add" label="Add section" @click="addSection" />
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
                            @update:model-value="onFieldSaved"
                        />
                        <q-input
                            v-model="form.notes"
                            dense outlined type="textarea" autogrow
                            label="Notes"
                            @update:model-value="onFieldSaved"
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
                            @update:model-value="onFieldSaved"
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

            <!-- The comparison hatch. Temporary — see FU-683. -->
            <div class="rn__flip">
                <BaseButton
                    variant="ghost"
                    :icon="ICONS.arrow_back"
                    label="Back to the old layout"
                    :to="`/cookbook/${recipeId}`"
                />
            </div>
        </template>

        <!-- Save indicator. With no Save button, this is the only thing that
             tells you a change landed — so it names failures loudly. -->
        <div v-if="saveState !== 'idle'" class="rn__savebar" :class="`rn__savebar--${saveState}`" role="status">
            <q-spinner v-if="saveState === 'saving'" size="16px" />
            <q-icon v-else-if="saveState === 'saved'" :name="ICONS.check" />
            <q-icon v-else :name="ICONS.error" />
            <span>{{ saveMessage }}</span>
        </div>

        <CookModeGuardDialog
            v-model="cookGuardOpen"
            :recipe="recipe"
            :dirty="false"
            :saving="false"
            @start="goToCookMode"
            @save-and-start="goToCookMode"
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
     * other. **One of them is going to be deleted** (FU-683).
     *
     * Three things make it different from the old page:
     *
     * 1. **No modes.** The owner's call: the read/edit toggle and its Edit/Done
     *    buttons are gone. Values render as text and edit in place via
     *    `q-popup-edit`, committing on close. This is a deliberate, recorded
     *    departure from **D-015** ("read-view + explicit edit mode for detail
     *    pages, never an always-editable form") — the rule exists *because of*
     *    this page, so reversing it needed to be a decision, not a drift. What
     *    the rule was protecting against is a wall of form inputs; inline
     *    editing keeps the page reading as a recipe, which is the rule's
     *    intent even where it breaks its letter.
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
    import { computed, onMounted, reactive, ref, watch } from 'vue';
    import { useRoute, useRouter } from 'vue-router';
    import { useQuasar } from 'quasar';
    import { storeToRefs } from 'pinia';

    import AppSkeleton from 'src/components/AppSkeleton.vue';
    import BaseButton from 'src/components/BaseButton.vue';
    import BaseDialog from 'src/components/BaseDialog.vue';
    import BaseSegmented from 'src/components/BaseSegmented.vue';
    import BaseSelect from 'src/components/BaseSelect.vue';
    import ImageEditTile from 'src/components/ImageEditTile.vue';
    import ImageUploadField from 'src/components/ImageUploadField.vue';
    import MealStepper from 'src/components/recipes/MealStepper.vue';
    import RecipeNutritionCard from 'src/components/recipes/RecipeNutritionCard.vue';
    import RecipeStepImagesEditor from 'src/components/recipes/RecipeStepImagesEditor.vue';
    import RecipeStepImagesViewer from 'src/components/recipes/RecipeStepImagesViewer.vue';
    import RecipeStepsEditor from 'src/components/recipes/RecipeStepsEditor.vue';
    import CookModeGuardDialog from 'src/components/recipes/CookModeGuardDialog.vue';
    import RecipeIngredientPickerDialog from 'src/components/recipes/RecipeIngredientPickerDialog.vue';
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
    import { useShoppingListActions } from 'src/composables/useShoppingListActions';
    import {
        buildUpdateCommand,
        hydrateRecipeForm,
        newClientId,
        useRecipeForm,
        type IngredientForm,
    } from 'src/composables/useRecipeEditor';

    import RecipeApiService, { recipeImageUrl } from 'src/services/api/recipeApiService';
    import { useRecipeStore } from 'src/stores/recipeStore';
    import { useRecipeVocabStore } from 'src/stores/recipeVocabStore';
    import { useStockItemStore } from 'src/stores/stockItemStore';
    import { useShoppingListStore } from 'src/stores/shoppingListStore';
    import type { Recipe, RecipeCostLine } from 'src/models/recipe';
    import type { EditableStep } from 'src/components/recipes/recipeStepEditorTypes';
    import type { EditableStepImage } from 'src/components/recipes/recipeStepImageEditorTypes';

    const DIFFICULTY_OPTIONS = ['Easy', 'Medium', 'Hard'];

    const $q = useQuasar();
    const route = useRoute();
    const router = useRouter();

    const recipeStore = useRecipeStore();
    const stockItemStore = useStockItemStore();
    const recipeVocabStore = useRecipeVocabStore();
    const shoppingListStore = useShoppingListStore();
    const recipeApi = new RecipeApiService();
    const { stockItems } = storeToRefs(stockItemStore);
    const { recipeCollections } = storeToRefs(recipeStore);
    const { cuisines, categories, dietaryTags, tools } = storeToRefs(recipeVocabStore);

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
    const photoBusy = ref(false);
    const imageDirty = ref(false);
    const stepImagesDirty = ref(false);
    const imageVersion = ref(0);
    const litStep = ref<string | null>(null);
    const detailOpen = reactive({
        tags: false, sections: false, cost: false,
        nutrition: false, notes: false, kcal: false, versions: false, photo: false,
    });

    // ── Save: no button, so the indicator is the whole feedback channel ──
    type SaveState = 'idle' | 'saving' | 'saved' | 'error';
    const saveState = ref<SaveState>('idle');
    const saveMessage = ref('');
    let saveTimer: ReturnType<typeof setTimeout> | null = null;
    let idleTimer: ReturnType<typeof setTimeout> | null = null;

    /** Every inline commit lands here. Debounced so a burst of edits (a
     *  popup-edit that fires per keystroke, a multi-select) is one PATCH. */
    function onFieldSaved() {
        if (saveTimer) clearTimeout(saveTimer);
        saveTimer = setTimeout(() => { void save(); }, 500);
    }

    async function save() {
        const src = recipe.value;
        if (!src) return;
        if (!form.name.trim()) {
            saveState.value = 'error';
            saveMessage.value = 'A recipe needs a name — not saved.';
            return;
        }
        // The old page blocks a save on any ingredient without a stock item.
        // Same rule here: an unlinked row is legal on load (imported recipes
        // have them) but must not be *sent* half-built.
        if (form.ingredients.some((i) => !i.stock_item_id && !i.raw_text)) {
            saveState.value = 'error';
            saveMessage.value = 'Every ingredient needs an item — not saved.';
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
            await loadRecipe();
            if (didImageChange) imageVersion.value++;
            saveState.value = 'saved';
            saveMessage.value = 'Saved';
            if (idleTimer) clearTimeout(idleTimer);
            idleTimer = setTimeout(() => { saveState.value = 'idle'; }, 1600);
        } catch (err) {
            saveState.value = 'error';
            saveMessage.value = `Couldn't save. ${toastCaption(err)}`;
        }
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
    const stockItemOptions = computed(() =>
        stockItems.value.map((s) => ({ label: s.name, value: s.stock_item_id })));

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
     *  rows first under no heading — matching how the list reads on paper. */
    const ingredientGroups = computed(() => {
        const flat = form.ingredients.filter((i) => !i.section_client_id);
        const groups: { key: string; name: string; rows: IngredientForm[] }[] = [];
        if (flat.length > 0) groups.push({ key: 'main', name: '', rows: flat });
        for (const sec of [...form.sections].sort((a, b) => a.sequence - b.sequence)) {
            const rows = form.ingredients.filter((i) => i.section_client_id === sec.client_id);
            if (rows.length > 0) groups.push({ key: sec.client_id, name: sec.name, rows });
        }
        return groups;
    });

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
        onFieldSaved();
    }
    function onStepImagesChanged(images: EditableStepImage[]) {
        form.step_images = images;
        stepImagesDirty.value = true;
        onFieldSaved();
    }

    // ── Captions for the collapsed Details rows ─────────────────────────
    const tagsCaption = computed(() => {
        const names = [
            ...form.dietary_tag_ids.map((id) => dietaryTags.value.find((t) => t.dietary_tag_id === id)?.name),
            ...form.tool_ids.map((id) => tools.value.find((t) => t.tool_id === id)?.name),
        ].filter(Boolean);
        return names.length > 0 ? names.join(' · ') : 'None';
    });
    const sectionsCaption = computed(() =>
        form.sections.length > 0 ? form.sections.map((s) => s.name).join(' · ') : 'One flat list');
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
    }
    function removeIngredient(clientId: string) {
        const idx = form.ingredients.findIndex((i) => i.client_id === clientId);
        if (idx >= 0) {
            form.ingredients.splice(idx, 1);
            onFieldSaved();
        }
    }
    function addSection() {
        form.sections.push({ client_id: newClientId(), sequence: form.sections.length, name: '' });
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
        onFieldSaved();
    }

    // ── Photo ───────────────────────────────────────────────────────────
    async function onPickPhoto(image: { dataUrl: string }) {
        photoBusy.value = true;
        form.image = image.dataUrl;
        imageDirty.value = true;
        await save();
        photoBusy.value = false;
    }
    function onPickPhotoDataUrl(dataUrl: string) {
        form.image = dataUrl;
        imageDirty.value = true;
        onFieldSaved();
    }
    function onClearPhoto() {
        form.image = null;
        imageDirty.value = true;
        onFieldSaved();
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
        if (needsCookGuard(recipe.value, false)) {
            cookGuardOpen.value = true;
            return;
        }
        goToCookMode();
    }
    function goToCookMode() {
        void router.push(`/cookbook/${recipeId.value}/cook`);
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

    // ── Mount ───────────────────────────────────────────────────────────
    onMounted(async () => {
        await Promise.all([
            recipeStore.ensureCollectionsLoadedAsync(),
            stockItemStore.ensureLoadedAsync(),
            recipeVocabStore.ensureLoadedAsync(),
            shoppingListStore.ensureLoadedAsync(),
        ]);
        await loadRecipe();
    });
    watch(recipeId, () => { void loadRecipe(); });
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
