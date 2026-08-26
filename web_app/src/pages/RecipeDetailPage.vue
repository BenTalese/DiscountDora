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
                <!-- Every photo control lives on the photo itself. The page used
                     to carry a second, fuller uploader in a disclosure at the
                     very bottom — the last place you look for the picture at the
                     top. With no photo the tile opens the file picker on the
                     first tap; with one it offers Change / Remove first, which
                     is what `manual` is for. -->
                <ImageEditTile
                    ref="photoTile"
                    class="rn__photo"
                    :class="{ 'rn__photo--empty': !photoUrl }"
                    :label="hasPhoto ? 'Change the recipe photo' : 'Add a recipe photo'"
                    shape="rounded"
                    fill
                    :manual="hasPhoto"
                    @activate="photoDialogOpen = true"
                    @pick="onPickPhoto"
                >
                    <img v-if="photoUrl" :src="photoUrl" alt="" class="rn__photoimg" />
                    <div v-else class="rn__photoplaceholder">
                        <q-icon :name="ICONS.photo_camera" size="28px" />
                        <span>{{ hasPhoto ? 'Photo hidden' : 'Add a photo' }}</span>
                    </div>
                </ImageEditTile>

                <div class="rn__identity">
                    <div class="rn__backrow">
                        <BaseButton
                            variant="icon"
                            class="dora-text-secondary"
                            :icon="ICONS.arrow_back"
                            to="/cookbook"
                            aria-label="Back to cookbook"
                        />
                        <h1 v-if="!headerEditing" class="rn__title">{{ form.name || 'Untitled recipe' }}</h1>
                        <h1 v-else class="rn__title rn__title--edit">
                            <q-input
                                v-model="form.name"
                                dense
                                outlined
                                autofocus
                                maxlength="255"
                                aria-label="Recipe name"
                                @update:model-value="markDirty"
                            />
                        </h1>
                        <BaseButton
                            class="rn__pencil"
                            :variant="headerEditing ? 'secondary' : 'icon'"
                            :icon="headerEditing ? ICONS.check : ICONS.edit"
                            :label="headerEditing ? 'Done' : undefined"
                            :aria-label="headerEditing ? 'Finish editing the recipe details' : 'Edit the recipe details'"
                            :aria-pressed="headerEditing"
                            :loading="headerEditing && saveState === 'saving'"
                            @click="onToggleHeaderEdit"
                        >
                            <q-tooltip v-if="!headerEditing">Edit the recipe details</q-tooltip>
                        </BaseButton>
                    </div>

                    <!-- Read: a sentence. Edit: three fields on the same grid
                         the facts use, so the block keeps its shape across the
                         flip instead of every control resizing to its own
                         longest option (R-055 / ADR-051). -->
                    <!-- Owner feedback 2026-08-26 — every axis in this block
                         already has a glyph on the cookbook page's filter row,
                         and the header was the one place naming them in bare
                         words. Same icon, same meaning, both modes (D-005). The
                         "·" separators went with them: a leading glyph already
                         marks where one fact stops and the next starts, and
                         dot-plus-icon reads as punctuation noise. -->
                    <div v-if="!headerEditing" class="rn__eyebrow">
                        <span class="rn__brow">
                            <q-icon :name="ICONS.collection" size="15px" />
                            {{ collectionName || 'No collection' }}
                        </span>
                        <span class="rn__brow">
                            <q-icon :name="ICONS.public" size="15px" />
                            {{ cuisineName || 'Any cuisine' }}
                        </span>
                        <span class="rn__brow">
                            <q-icon :name="ICONS.category" size="15px" />
                            {{ categoryName || 'No category' }}
                        </span>
                    </div>
                    <div v-else class="rn__fields">
                        <BaseSelect
                            v-model="form.recipe_collection_id"
                            label="Collection"
                            :options="collectionOptions"
                            emit-value map-options clearable
                            @update:model-value="markDirty"
                        >
                            <template #prepend><q-icon :name="ICONS.collection" size="18px" /></template>
                        </BaseSelect>
                        <BaseSelect
                            v-model="form.cuisine_id"
                            label="Cuisine"
                            :options="cuisineOptions"
                            emit-value map-options clearable
                            @update:model-value="markDirty"
                        >
                            <template #prepend><q-icon :name="ICONS.public" size="18px" /></template>
                        </BaseSelect>
                        <BaseSelect
                            v-model="form.category_id"
                            label="Category"
                            :options="categoryOptions"
                            emit-value map-options clearable
                            @update:model-value="markDirty"
                        >
                            <template #prepend><q-icon :name="ICONS.category" size="18px" /></template>
                        </BaseSelect>
                    </div>

                    <div v-if="!headerEditing" class="rn__facts">
                        <div class="rn__fact">
                            <span class="rn__factk"><q-icon :name="ICONS.people" size="14px" />Serves</span>
                            <span class="rn__factv">{{ form.servings ?? '—' }}</span>
                        </div>
                        <div class="rn__fact">
                            <span class="rn__factk"><q-icon :name="ICONS.prepTime" size="14px" />Prep</span>
                            <span class="rn__factv">{{ form.prep_time_minutes ? form.prep_time_minutes + ' min' : '—' }}</span>
                        </div>
                        <div class="rn__fact">
                            <span class="rn__factk"><q-icon :name="ICONS.cookTime" size="14px" />Cook</span>
                            <span class="rn__factv">{{ form.cook_time_minutes ? form.cook_time_minutes + ' min' : '—' }}</span>
                        </div>
                        <div v-if="totalMinutes !== null" class="rn__fact">
                            <span class="rn__factk"><q-icon :name="ICONS.timer" size="14px" />Total</span>
                            <span class="rn__factv">{{ totalMinutes }} min</span>
                        </div>
                        <div class="rn__fact">
                            <span class="rn__factk"><q-icon :name="ICONS.difficulty" size="14px" />Difficulty</span>
                            <span class="rn__factv">{{ form.difficulty || '—' }}</span>
                        </div>
                        <div class="rn__fact">
                            <span class="rn__factk"><q-icon :name="ICONS.schedule" size="14px" />When</span>
                            <span class="rn__factv">{{ form.time_of_day || '—' }}</span>
                        </div>
                        <div v-if="headlineKcal !== null" class="rn__fact">
                            <span class="rn__factk">
                                <q-icon :name="ICONS.local_fire_department" size="14px" />Per serving
                            </span>
                            <span class="rn__factv">{{ headlineKcal }} kcal</span>
                        </div>
                    </div>
                    <!-- Total and Per serving are derived, so they have no field
                         here — there is nothing to type into them. -->
                    <div v-else class="rn__fields">
                        <q-input
                            v-model.number="form.servings"
                            dense outlined type="number" min="1" label="Serves"
                            @update:model-value="markDirty"
                        >
                            <template #prepend><q-icon :name="ICONS.people" size="18px" /></template>
                        </q-input>
                        <q-input
                            v-model.number="form.prep_time_minutes"
                            dense outlined type="number" min="0" label="Prep (min)"
                            @update:model-value="markDirty"
                        >
                            <template #prepend><q-icon :name="ICONS.prepTime" size="18px" /></template>
                        </q-input>
                        <q-input
                            v-model.number="form.cook_time_minutes"
                            dense outlined type="number" min="0" label="Cook (min)"
                            @update:model-value="markDirty"
                        >
                            <template #prepend><q-icon :name="ICONS.cookTime" size="18px" /></template>
                        </q-input>
                        <BaseSelect
                            v-model="form.difficulty"
                            label="Difficulty"
                            :options="DIFFICULTY_OPTIONS"
                            clearable
                            @update:model-value="markDirty"
                        >
                            <template #prepend><q-icon :name="ICONS.difficulty" size="18px" /></template>
                        </BaseSelect>
                        <BaseSelect
                            v-model="form.time_of_day"
                            label="When"
                            :options="timeOfDayOptions"
                            clearable
                            @update:model-value="markDirty"
                        >
                            <template #prepend><q-icon :name="ICONS.schedule" size="18px" /></template>
                        </BaseSelect>
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
                    class="rn__cell rn__cell--split"
                    :class="missingIngredients.length > 0 ? 'rn__cell--bad' : (cookableNow ? 'rn__cell--ok' : '')"
                >
                    <div class="rn__cellbody">
                        <span class="rn__cellk">Right now</span>
                        <span class="rn__cellv">{{ cookableHeadline }}</span>
                        <!-- "You're missing two things, but you have a substitute
                             for one" is a different answer to "you're missing two
                             things", so it belongs in the cell that answers it. -->
                        <span v-if="coverableCount > 0" class="rn__cellswap">
                            <q-icon :name="ICONS.swap_horiz" size="14px" />
                            {{ coverableCount === 1
                                ? '1 has a substitute you already have'
                                : `${coverableCount} have substitutes you already have` }}
                        </span>
                        <!-- Owner feedback 2026-08-24 — the action said nothing
                             about what was already on a list, so it offered to
                             add things the user had added ten minutes earlier.
                             The copy now counts only what's actually left; the
                             action itself is the cell's button, on the right. -->
                        <template v-if="missingIngredients.length > 0">
                            <span v-if="missingNotOnListCount === 0" class="rn__cellsub">
                                <q-icon :name="ICONS.check" size="14px" />
                                Already on a shopping list
                            </span>
                            <span v-else-if="missingOnListCount > 0" class="rn__cellsub">
                                {{ missingOnListCount }} already on a list
                            </span>
                        </template>
                        <span v-else class="rn__cellsub">{{ cookableCaption }}</span>
                    </div>
                    <!-- The cell's action, at the cell's edge — a real button on
                         the right rather than a text link buried under the copy
                         it belongs to. It disappears (rather than going inert)
                         once everything missing is already on a list. -->
                    <BaseButton
                        v-if="missingIngredients.length > 0 && missingNotOnListCount > 0"
                        variant="secondary"
                        :icon="ICONS.add_shopping_cart"
                        :label="compact ? undefined : addMissingLabel"
                        :aria-label="`${addMissingLabel} — the ingredients you're missing`"
                        @click="onAddMissingToList"
                    >
                        <q-tooltip v-if="compact">{{ addMissingLabel }}</q-tooltip>
                    </BaseButton>
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
                    <span class="rn__cellsub">
                        {{ recipe.estimated_cost_priced_count }} of
                        {{ recipe.estimated_cost_total_count }} priced
                    </span>
                    <!-- Feedback 2026-08-24 — the breakdown was a section on
                         the page reached by a text link; it's a question with
                         an answer, so it's a button and a modal. -->
                    <BaseButton
                        variant="subtle"
                        dense
                        class="rn__cellbtn"
                        :icon="ICONS.receipt_long"
                        label="Details"
                        @click="costDialogOpen = true"
                    />
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
                            <!-- Owner feedback 2026-08-24 — a section used to be a
                                 bare underlined caption above its rows, which read
                                 as another free-text ingredient, and its controls
                                 lived in an "Organise ingredients" disclosure at the
                                 very bottom of the page. A section is a container, so
                                 it looks like one: a card holding its own name, its
                                 own rows and its own add button. The disclosure is
                                 gone with it. -->
                            <div
                                v-for="group in ingredientGroups"
                                :key="group.key"
                                class="rn__group"
                                :class="{ 'rn__group--card': group.sectionId !== null }"
                            >
                                <div v-if="group.sectionId !== null" class="rn__grouphead">
                                    <InlineEditTarget
                                        class="rn__groupname rn__edit"
                                        :label="`Rename the ${group.name} section`"
                                    >
                                        {{ group.name }}
                                        <q-popup-edit
                                            :model-value="sectionNameOf(group.sectionId)"
                                            v-slot="scope"
                                            auto-save
                                            @save="(v) => renameSection(String(group.sectionId), String(v ?? ''))"
                                        >
                                            <q-input
                                                v-model="scope.value"
                                                dense
                                                autofocus
                                                label="Section name"
                                                placeholder="For the sauce"
                                                @keyup.enter="scope.set"
                                            />
                                        </q-popup-edit>
                                    </InlineEditTarget>
                                    <span class="rn__groupcount">{{ group.rows.length }}</span>
                                    <BaseButton
                                        variant="icon"
                                        dense
                                        :icon="ICONS.more_vert"
                                        :aria-label="`Section options for ${group.name}`"
                                    >
                                        <q-menu auto-close>
                                            <q-list dense style="min-width: 190px">
                                                <q-item
                                                    clickable
                                                    :disable="sectionIndexOf(group.sectionId) === 0"
                                                    @click="moveSection(String(group.sectionId), -1)"
                                                >
                                                    <q-item-section avatar>
                                                        <q-icon :name="ICONS.arrow_upward" />
                                                    </q-item-section>
                                                    <q-item-section>Move section up</q-item-section>
                                                </q-item>
                                                <q-item
                                                    clickable
                                                    :disable="sectionIndexOf(group.sectionId) === form.sections.length - 1"
                                                    @click="moveSection(String(group.sectionId), 1)"
                                                >
                                                    <q-item-section avatar>
                                                        <q-icon :name="ICONS.arrow_downward" />
                                                    </q-item-section>
                                                    <q-item-section>Move section down</q-item-section>
                                                </q-item>
                                                <q-separator />
                                                <q-item clickable @click="removeSection(String(group.sectionId))">
                                                    <q-item-section avatar>
                                                        <q-icon :name="ICONS.delete" color="negative" />
                                                    </q-item-section>
                                                    <q-item-section>
                                                        Remove section
                                                        <q-item-label caption>
                                                            Its ingredients move to the main list
                                                        </q-item-label>
                                                    </q-item-section>
                                                </q-item>
                                            </q-list>
                                        </q-menu>
                                    </BaseButton>
                                </div>

                                <ul class="rn__ing">
                                    <li
                                        v-for="(row, rowIndex) in group.rows"
                                        :key="row.client_id"
                                        class="rn__ing--target"
                                        :class="{ 'rn__ing--lit': litIngredients.has(String(row.client_id)) }"
                                        role="button"
                                        tabindex="0"
                                        :aria-label="`Edit ${ingredientLabel(row)}`"
                                        @click="openRowEditor(String(row.client_id))"
                                        @keydown.enter.prevent="openRowEditor(String(row.client_id))"
                                        @keydown.space.prevent="openRowEditor(String(row.client_id))"
                                    >
                                        <!-- Quantity, unit, name, section, note and
                                             the optional flag are one thing to a
                                             cook, so the whole row opens one editor
                                             rather than the quantity and the name
                                             each owning their own target. The
                                             quantity popup also carried a free-text
                                             unit, which the row editor's canonical
                                             dropdown had already replaced. -->
                                        <span class="rn__qty">
                                            {{ formatQuantity(row.quantity, row.unit) || '—' }}
                                        </span>
                                        <span class="rn__ingname">
                                            <span class="rn__ingtext">{{ ingredientLabel(row) }}</span>
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
                                            <!-- "Missing" and "missing, but you have
                                                 something you could use instead" are
                                                 different answers to tonight's
                                                 question, so the chip says which one
                                                 this is (feedback 2026-08-24). The
                                                 swap list itself stays one tap away in
                                                 the substitutes chip beside it. -->
                                            <q-chip
                                                v-else-if="isMissingItem(row.stock_item_id)"
                                                dense square size="sm"
                                                :color="hasSwapInStock(row) ? 'warning' : 'negative'"
                                                :text-color="hasSwapInStock(row) ? 'dark' : 'white'"
                                                class="rn__chip"
                                            >
                                                {{ hasSwapInStock(row) ? 'Missing — swap in stock' : 'Missing' }}
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
                                            <span @click.stop>
                                                <RecipeIngredientSubstitutes
                                                    :entries="substitutesForRow(row)"
                                                    :ingredient-name="ingredientLabel(row)"
                                                />
                                            </span>
                                            <span v-if="row.notes" class="rn__ingnote">{{ row.notes }}</span>
                                        </span>
                                        <!-- Per-row actions. Reordering lives here now
                                             that the organise disclosure is gone; on a
                                             phone the cluster is permanently visible,
                                             because hover isn't a gesture a thumb has. -->
                                        <span class="rn__ingact" @click.stop>
                                            <BaseButton
                                                variant="icon" dense
                                                :icon="ICONS.arrow_upward"
                                                :disable="rowIndex === 0"
                                                :aria-label="`Move ${ingredientLabel(row)} up`"
                                                @click="moveIngredientWithin(group.rows, rowIndex, -1)"
                                            />
                                            <BaseButton
                                                variant="icon" dense
                                                :icon="ICONS.arrow_downward"
                                                :disable="rowIndex === group.rows.length - 1"
                                                :aria-label="`Move ${ingredientLabel(row)} down`"
                                                @click="moveIngredientWithin(group.rows, rowIndex, 1)"
                                            />
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

                                <p v-if="group.rows.length === 0" class="rn__ingsecempty">
                                    Nothing in this section yet.
                                </p>

                                <BaseButton
                                    variant="subtle"
                                    class="rn__add"
                                    :icon="ICONS.add"
                                    :label="group.sectionId === null ? 'Add ingredient' : `Add to ${group.name}`"
                                    @click="addIngredient(group.sectionId)"
                                />
                            </div>
                        </div>

                        <BaseButton
                            variant="ghost"
                            class="rn__addsec"
                            :icon="ICONS.add"
                            label="Add section"
                            @click="addSection"
                        >
                            <q-tooltip>
                                Sections group the list under headings — "For the
                                sauce", "To serve".
                            </q-tooltip>
                        </BaseButton>
                    </section>
                </div>

                <section aria-labelledby="rnMet">
                    <div class="rn__sechead">
                        <h2 class="rn__sectitle" id="rnMet">Method</h2>
                        <span class="rn__seccount">{{ methodCountLabel }}</span>
                    </div>

                    <!-- Owner feedback 2026-08-24 — the three-way control now
                         says what it switches ("Step style") and names the
                         styles in full, and the editor is one pencil shared by
                         all three rather than a per-style disclosure whose
                         label changed under you. One edit button, whatever the
                         style, because it is always the same intent: change
                         the method. -->
                    <div class="rn__stylebar">
                        <span class="rn__stylek">Step style</span>
                        <BaseSegmented
                            v-model="form.steps_mode"
                            dense
                            unelevated
                            class="rn__modes"
                            :options="[
                                { label: 'Structured', value: 'structured' },
                                { label: 'Free text', value: 'freeform' },
                                { label: 'Image', value: 'image' },
                            ]"
                            @update:model-value="markDirty"
                        />
                        <BaseButton
                            variant="secondary"
                            dense
                            class="rn__styleedit"
                            :icon="ICONS.edit"
                            :label="compact ? undefined : 'Edit'"
                            :aria-label="methodEditLabel"
                            @click="methodEditorOpen = true"
                        >
                            <q-tooltip>{{ methodEditLabel }}</q-tooltip>
                        </BaseButton>
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
                                    <!-- Sub-steps read as the same kind of
                                         thing as a step, one level in: same
                                         numbered bullet, toned down and
                                         indented rather than a plain bulleted
                                         list in a different visual language
                                         (feedback 2026-08-24). -->
                                    <ol v-if="subStepsOf(step).length > 0" class="rn__substeps">
                                        <li v-for="sub in subStepsOf(step)" :key="sub.client_id">
                                            <p>{{ sub.text || 'Empty sub-step' }}</p>
                                            <span v-if="sub.hint" class="rn__hint">{{ sub.hint }}</span>
                                        </li>
                                    </ol>
                                </li>
                            </ol>
                            <p v-else class="rn__empty">No steps yet — tap Edit to add them.</p>
                        </template>

                        <!-- Free text — one block, edited in the shared method
                             editor. It used to edit through an inline popup,
                             which on a phone opened the keyboard *over* the
                             field with nothing to scroll (feedback
                             2026-08-24); the dialog puts the field above the
                             keyboard and scrolls itself. -->
                        <template v-else-if="form.steps_mode === 'freeform'">
                            <button
                                v-if="freeformLines.length > 0"
                                type="button"
                                class="rn__free rn__edit rn__freebtn"
                                aria-label="Edit the instructions"
                                @click="methodEditorOpen = true"
                            >
                                <p v-for="(line, i) in freeformLines" :key="`f-${i}`">{{ line }}</p>
                            </button>
                            <button
                                v-else
                                type="button"
                                class="rn__empty rn__edit rn__freebtn"
                                aria-label="Add instructions"
                                @click="methodEditorOpen = true"
                            >
                                No instructions yet — tap to write them.
                            </button>
                        </template>

                        <!-- Photo steps. -->
                        <template v-else>
                            <RecipeStepImagesViewer
                                v-if="(recipe.step_images ?? []).length > 0"
                                :recipe-id="recipe.recipe_id"
                                :images="recipe.step_images ?? []"
                            />
                            <p v-else class="rn__empty">No step photos yet — tap Edit to add them.</p>
                        </template>
                    </div>
                </section>
            </div>

            <!-- ═══ Details — everything administrative ═════════════════
                 Owner feedback 2026-08-24 — dietary tags, tools, the source
                 URL and the notes were four separate disclosures for four
                 fields nobody opens twice. They are one "Additional details"
                 chunk now. What stayed separate genuinely answers its own
                 question: nutrition, the photo, and the version history. The
                 cost breakdown left this list entirely — it is a modal on the
                 status strip — and so did "Organise ingredients", which the
                 ingredient section cards absorbed. -->
            <div class="rn__details">
                <q-expansion-item
                    v-model="detailOpen.extra"
                    dense-toggle
                    label="Additional details"
                    :caption="extraCaption"
                >
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
                            class="q-mb-sm"
                            @update:model-value="markDirty"
                        />
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

                <!-- Version information. Was "Other versions", captioned "N
                     siblings" — a word from the data model, not the kitchen.
                     It now answers the two questions actually asked of a
                     recipe's history: when did this one come about, and what
                     other versions of it exist (feedback 2026-08-24). It
                     renders even for a singleton, because created/updated are
                     facts about every recipe. -->
                <q-expansion-item
                    v-model="detailOpen.versions"
                    dense-toggle
                    label="Version information"
                    :caption="versionsCaption"
                >
                    <div class="rn__disc">
                        <div class="rn__vfacts">
                            <div class="rn__vfact">
                                <span class="rn__cellk">Created</span>
                                <span>{{ recipe.created_at ? formatDate(recipe.created_at) : 'Unknown' }}</span>
                            </div>
                            <div class="rn__vfact">
                                <span class="rn__cellk">Last updated</span>
                                <span>
                                    {{ recipe.updated_at
                                        ? formatDate(recipe.updated_at)
                                        : 'Not edited since it was added' }}
                                </span>
                            </div>
                        </div>

                        <template v-if="versionSiblings.length > 0">
                            <div class="rn__discsub">Versions of this recipe</div>
                            <q-list dense separator>
                                <q-item class="rn__vthis">
                                    <q-item-section>
                                        <q-item-label>{{ recipe.name }}</q-item-label>
                                        <q-item-label caption>
                                            {{ recipe.created_at ? `Created ${formatDate(recipe.created_at)}` : 'Created — unknown' }}
                                        </q-item-label>
                                    </q-item-section>
                                    <q-item-section side>
                                        <q-badge outline color="primary" label="You're here" />
                                    </q-item-section>
                                </q-item>
                                <q-item
                                    v-for="sib in versionSiblings"
                                    :key="sib.recipe_id"
                                    clickable
                                    @click="goToSibling(sib.recipe_id)"
                                >
                                    <q-item-section>
                                        <q-item-label>{{ sib.name }}</q-item-label>
                                        <q-item-label caption>
                                            {{ sib.created_at ? `Created ${formatDate(sib.created_at)}` : 'Created — unknown' }}
                                        </q-item-label>
                                    </q-item-section>
                                    <q-item-section side>
                                        <q-icon :name="ICONS.chevron_right" />
                                    </q-item-section>
                                </q-item>
                            </q-list>
                        </template>
                        <p v-else class="rn__hintblock rn__vnone">
                            This is the only version. "New version" makes a copy you
                            can change without losing this one.
                        </p>
                    </div>
                </q-expansion-item>

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
            :substitutable="substitutableNames"
            @start="goToCookMode"
            @save-and-start="onSaveAndCook"
        />

        <RecipeMethodEditorDialog
            v-model="methodEditorOpen"
            :mode="form.steps_mode"
            :steps="form.steps"
            :instructions="form.instructions"
            :step-images="form.step_images"
            :ingredient-options="ingredientOptions"
            :tool-options="toolOptions"
            :section-options="sectionOptions"
            @update:steps="onStepsChanged"
            @update:instructions="onInstructionsChanged"
            @update:step-images="onStepImagesChanged"
        />

        <RecipeCostDialog
            v-if="recipe"
            v-model="costDialogOpen"
            :lines="recipe.estimated_cost_lines ?? []"
            :total="recipe.estimated_cost"
            :priced-count="recipe.estimated_cost_priced_count"
            :total-count="recipe.estimated_cost_total_count"
            :servings="form.servings"
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

        <!-- No preview here: you opened this by tapping the photo, so you have
             just looked at it. Two buttons, nothing else. -->
        <BaseDialog v-model="photoDialogOpen" title="Recipe photo" closable card-style="min-width: 300px">
            <q-card-section class="rn__photoacts">
                <BaseButton
                    variant="primary"
                    :icon="ICONS.photo_camera"
                    label="Change photo"
                    @click="onChangePhoto"
                />
                <BaseButton
                    variant="danger-ghost"
                    :icon="ICONS.delete"
                    label="Remove photo"
                    @click="onRemovePhoto"
                />
            </q-card-section>
        </BaseDialog>
    </q-page>
</template>

<script lang="ts" setup>
    /**
     * The recipe page — the 2026-08-20 redesign, and since 2026-08-26 the only
     * one.
     *
     * It ran in parallel with the original at `/cookbook/:id/new` while the two
     * were compared on the same recipe. The owner picked this one (FU-688) and
     * the original — 2,727 lines, its own duplicate form model, both hatch
     * buttons and the `/new` route — was deleted with the swap. It kept the
     * bespoke masthead over the shared `PageToolbar` every other detail page
     * uses; that was the one piece explicitly reserved, and the same feedback
     * batch asked for the masthead to be *enriched*, so it stays. Import is
     * deliberately absent (FU-689 closed won't-do — importing over an existing
     * recipe was never wanted here).
     *
     * Three things made it different from the page it replaced:
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
    import MealStepper from 'src/components/recipes/MealStepper.vue';
    import RecipeNutritionCard from 'src/components/recipes/RecipeNutritionCard.vue';
    import RecipeStepImagesViewer from 'src/components/recipes/RecipeStepImagesViewer.vue';
    import RecipeCostDialog from 'src/components/recipes/RecipeCostDialog.vue';
    import RecipeMethodEditorDialog from 'src/components/recipes/RecipeMethodEditorDialog.vue';
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
    import { cartStateFor, type Membership } from 'src/models/shoppingList';
    import StockItemApiService from 'src/services/api/stockItemApiService';
    import type { Recipe } from 'src/models/recipe';
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
    // Shopping-list membership, read from the same place every cart button
    // reads it (R-003) so the page and the buttons can't disagree about
    // whether something is already on a list.
    const { membership: listMembership } = storeToRefs(shoppingListStore);
    const membership = computed<Membership | null>(
        () => (listMembership.value as Membership | null) ?? null,
    );

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
    const costDialogOpen = ref(false);
    const methodEditorOpen = ref(false);
    const detailOpen = reactive({
        extra: false, nutrition: false, kcal: false, versions: false,
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

    // ── Masthead edit mode (R-055 / ADR-051) ────────────────────────────
    // One pencil for the whole block, replacing the per-field `q-popup-edit`s
    // that used to sit on the name, collection, cuisine, category and every
    // fact. Those cost two clicks on every dropdown (one to summon the field,
    // one to open it) and sized each control to its own longest option, so an
    // empty Difficulty was a sliver. A block that flips whole keeps one grid
    // across both states, and a select is a select.
    //
    // The other two editable regions don't need a switch: an ingredient row
    // opens its editor on a tap of the row, and the method is prose, where an
    // editor over the paragraph you're reading is the right shape — R-055's
    // stated carve-out, served by `RecipeMethodEditorDialog`.
    const headerEditing = ref(false);

    /** Leaving edit mode commits, because the pencil reads as "done" — see the
     *  Done label it wears while open. A failed save keeps the block open so
     *  the error has something to point at. */
    async function onToggleHeaderEdit() {
        if (!headerEditing.value) {
            headerEditing.value = true;
            return;
        }
        if (dirty.value) {
            await onSave();
            if (saveState.value === 'error') return;
        }
        headerEditing.value = false;
    }

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
            // A save is the end of an edit: the masthead goes back to reading,
            // whichever button asked for it (the Save button in the action row
            // or the pencil).
            headerEditing.value = false;
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
            headerEditing.value = false;
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
    type IngredientGroup = {
        key: string;
        /** Null for the unsectioned rows — the group that renders bare. */
        sectionId: string | null;
        name: string;
        rows: IngredientForm[];
    };

    const ingredientGroups = computed<IngredientGroup[]>(() => {
        const flat = form.ingredients.filter((i) => !i.section_client_id);
        const groups: IngredientGroup[] = [];
        // The main group always renders, even empty: it owns the "Add
        // ingredient" button, and a recipe whose every row sits in a section
        // would otherwise have no way back to an unsectioned one.
        groups.push({ key: 'main', sectionId: null, name: '', rows: flat });
        for (const sec of [...form.sections].sort((a, b) => a.sequence - b.sequence)) {
            groups.push({
                key: sec.client_id,
                sectionId: sec.client_id,
                name: sec.name || 'Untitled section',
                rows: form.ingredients.filter((i) => i.section_client_id === sec.client_id),
            });
        }
        return groups;
    });

    function sectionNameOf(clientId: string | null): string {
        if (!clientId) return '';
        return form.sections.find((sec) => sec.client_id === clientId)?.name ?? '';
    }
    function sectionIndexOf(clientId: string | null): number {
        if (!clientId) return -1;
        return [...form.sections]
            .sort((a, b) => a.sequence - b.sequence)
            .findIndex((sec) => sec.client_id === clientId);
    }
    function renameSection(clientId: string, name: string) {
        const sec = form.sections.find((x) => x.client_id === clientId);
        if (!sec) return;
        sec.name = name;
        markDirty();
    }

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
     *  the fact that changes tonight's answer, so the status strip says it —
     *  and, since 2026-08-24, so do the ingredient row and the cook-mode
     *  guard, which is the last place it can still change the decision. */
    const coverableIngredients = computed(() =>
        missingIngredients.value.filter(
            (i) => (substitutesFor.value.get(i.stock_item_id) ?? []).some((e) => e.inStock),
        ));
    const coverableCount = computed(() => coverableIngredients.value.length);
    const substitutableNames = computed(() =>
        coverableIngredients.value.map(
            (i) => stockItems.value.find((s) => s.stock_item_id === i.stock_item_id)?.name
                ?? i.stock_item_name,
        ));

    /** True when this row is missing but something in the pantry could stand
     *  in for it. Drives the row chip's wording. */
    function hasSwapInStock(row: IngredientForm): boolean {
        if (!row.stock_item_id || !isMissingItem(row.stock_item_id)) return false;
        return (substitutesFor.value.get(row.stock_item_id) ?? []).some((e) => e.inStock);
    }

    // ── What's already on a shopping list ───────────────────────────────
    // Server-owned membership, not a client guess: the same map the cart
    // buttons read. Missing rows split into "still to buy" and "already
    // handled" so the status strip stops offering to add both.
    const missingOnListCount = computed(() =>
        missingIngredients.value.filter(
            (i) => cartStateFor(i.stock_item_id, membership.value) !== 'none',
        ).length);
    const missingNotOnListCount = computed(
        () => missingIngredients.value.length - missingOnListCount.value);

    // Names the button by what it will actually do. When some of the missing
    // rows are already handled the count has to be explicit ("Add 2 to a list"),
    // because "add them" would otherwise read as all of them.
    const addMissingLabel = computed(() => {
        const left = missingNotOnListCount.value;
        if (left === missingIngredients.value.length) {
            return left === 1 ? 'Add it to a list' : 'Add them to a list';
        }
        return `Add ${left} to a list`;
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

    /** One pencil, three styles — so the label has to say which one it will
     *  open (owner feedback 2026-08-24). */
    const methodEditLabel = computed(() => {
        switch (form.steps_mode) {
            case 'structured': return 'Edit steps';
            case 'image': return 'Edit step photos';
            default: return 'Edit instructions';
        }
    });

    function onStepsChanged(steps: EditableStep[]) {
        form.steps = steps;
        markDirty();
    }
    function onInstructionsChanged(text: string) {
        form.instructions = text;
        markDirty();
    }
    function onStepImagesChanged(images: EditableStepImage[]) {
        form.step_images = images;
        stepImagesDirty.value = true;
        markDirty();
    }

    // ── Captions for the collapsed Details rows ─────────────────────────
    /** Tags, tools, source and notes now share one row, so its caption has to
     *  say which of the four are set without listing everything. */
    const extraCaption = computed(() => {
        const bits: string[] = [];
        const names = [
            ...form.dietary_tag_ids.map((id) => dietaryTags.value.find((t) => t.dietary_tag_id === id)?.name),
            ...form.tool_ids.map((id) => tools.value.find((t) => t.tool_id === id)?.name),
        ].filter(Boolean);
        if (names.length > 0) bits.push(names.join(' · '));
        if (form.source) bits.push('Has a source');
        if (form.notes) bits.push('Has notes');
        return bits.length > 0 ? bits.join(' · ') : 'Tags, tools, source, notes';
    });
    const versionsCaption = computed(() => {
        const n = versionSiblings.value.length;
        if (n === 0) return 'Only version';
        return `${n + 1} versions`;
    });
    const nutritionCaption = computed(() => {
        const n = recipe.value?.nutrition;
        if (!n) return '';
        return n.kcal ? `${Math.round(n.kcal)} kcal per serving` : 'Per serving';
    });

    // ── Ingredient + section mutations ──────────────────────────────────
    /** `sectionId` is the card the button lives in, so a row lands where it
     *  was asked for rather than in the flat list every time. */
    function addIngredient(sectionId: string | null = null) {
        form.ingredients.push({
            client_id: newClientId(),
            stock_item_id: null,
            raw_text: null,
            quantity: null,
            unit: null,
            notes: null,
            section_client_id: sectionId,
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
     *  and arrays are sent with replace semantics — so a move is a splice.
     *
     *  Moves are *within a section card*: the visible neighbours are the
     *  section's rows, not the whole recipe's, so swapping array positions
     *  with the row directly above/below in that group is what makes ↑ and ↓
     *  mean what they look like they mean. Changing which section a row is in
     *  is a different act, done in the row editor. */
    function moveIngredientWithin(rows: IngredientForm[], index: number, delta: -1 | 1) {
        const target = rows[index + delta];
        const source = rows[index];
        if (!target || !source) return;
        const from = form.ingredients.findIndex((i) => i.client_id === source.client_id);
        const to = form.ingredients.findIndex((i) => i.client_id === target.client_id);
        if (from < 0 || to < 0) return;
        const [moved] = form.ingredients.splice(from, 1);
        if (moved) form.ingredients.splice(to, 0, moved);
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

    // ── Photo ───────────────────────────────────────────────────────────
    // Every photo control lives on the photo itself, so the tile is the only
    // uploader on the page; the dialog just picks which of the two things you
    // meant when a photo already exists.
    const photoTile = ref<InstanceType<typeof ImageEditTile> | null>(null);

    function onPickPhoto(image: { dataUrl: string }) {
        form.image = image.dataUrl;
        imageDirty.value = true;
        markDirty();
    }
    function onChangePhoto() {
        photoDialogOpen.value = false;
        photoTile.value?.openPicker();
    }
    function onRemovePhoto() {
        photoDialogOpen.value = false;
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
            if (newId) void router.push(`/cookbook/${newId}`);
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
        void router.push(`/cookbook/${id}`);
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
        headerEditing.value = false;
        saveState.value = 'idle';
        void loadRecipe();
    });
</script>

<style scoped lang="scss">
    /* No display face. The page shipped with Fraunces on the title and the
       section labels; the owner's verdict 2026-08-24 was that it "just
       doesn't feel like the same app" — which is the right call, because a
       page-specific typeface is a second brand nobody asked for. Everything
       here inherits the user's chosen font (Settings → Appearance,
       themeService FONT_FAMILY_CSS), like every other page. */

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
    .rn__photoplaceholder {
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        gap: var(--space-2, 8px);
        width: 100%; height: 100%;
        color: var(--text-muted);
        font-size: 0.875rem;
    }
    .rn__photoacts { display: flex; flex-direction: column; gap: var(--space-2, 8px); }
    /* The empty state is the tile itself now, not a separate <button>, so this
       only has to tint the well — `.rn__photoplaceholder` centres the content. */
    .rn__photo--empty { background: var(--surface-sunken); }
    .rn__photo--empty:hover { border-color: var(--brand-primary); }

    .rn__identity { min-width: 0; }
    .rn__pencil { flex: none; }

    /* One grid for both halves of the edit face, so a select is as wide as
       the cell it sits in rather than as wide as its longest option. */
    .rn__fields {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
        gap: var(--space-3, 12px);
        margin-top: var(--space-3, 12px);
    }
    .rn__backrow { display: flex; align-items: center; gap: var(--space-2, 8px); }
    .rn__title {
        font-size: 2rem;
        font-weight: 600;
        line-height: 1.15;
        letter-spacing: -0.01em;
        margin: 0;
        /* The h1 sits in a flex row; without `flex: 1` it is sized to its own
           text and wraps with half the row still empty. `text-wrap: balance`
           made that worse by splitting evenly across the lines it chose, so it
           goes too — the title should fill the row and only wrap when it must. */
        flex: 1;
        min-width: 0;
    }
    /* In edit mode the h1 is a wrapper around an input, so it drops the
       display sizing it uses when it is actually a heading. */
    .rn__title--edit { font-size: 1rem; font-weight: 400; }
    .rn__eyebrow {
        display: flex; flex-wrap: wrap; align-items: center;
        /* Wider than the old dot-separated gap — the glyphs are doing the
           separating now, so the space between facts has to read as bigger
           than the space inside one. */
        gap: var(--space-2, 8px) var(--space-4, 16px);
        margin-top: var(--space-2, 8px);
        color: var(--text-secondary);
        font-size: 0.875rem;
    }
    .rn__brow { display: inline-flex; align-items: center; gap: var(--space-1, 4px); }

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
    .rn__fact { display: flex; flex-direction: column; gap: 2px; min-width: 60px; flex: 0 0 auto; }
    .rn__factk {
        display: inline-flex; align-items: center; gap: var(--space-1, 4px);
        font-size: 0.6875rem; font-weight: 700; letter-spacing: 0.07em;
        text-transform: uppercase; color: var(--text-muted);
    }
    /* The letter-spacing above is set for capitals; on the glyph it just
       pushes it off its word. */
    .rn__factk .q-icon { letter-spacing: normal; }
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
    /* A cell that carries an action: copy on the left, the action on the
       right edge where it can be reached without reading past it. */
    .rn__cell--split {
        flex-direction: row;
        align-items: center;
        justify-content: space-between;
        gap: var(--space-3, 12px);
    }
    .rn__cellbody { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
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
    .rn__cellbtn { align-self: flex-start; margin-top: var(--space-1, 4px); }
    /* The swap line is good news on a cell that is otherwise bad news, so it
       carries the positive ink rather than the muted grey the other sub-lines
       use (D-013 — colour means something here). */
    .rn__cellswap {
        display: flex; align-items: center; gap: var(--space-1, 4px);
        font-size: 0.8125rem;
        color: var(--semantic-positive);
    }

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
        font-size: 0.9375rem; font-weight: 700;
        letter-spacing: 0.08em; text-transform: uppercase;
        color: var(--text-secondary);
        margin: 0;
    }
    .rn__seccount {
        font-size: 0.8125rem; color: var(--text-muted);
        font-variant-numeric: tabular-nums; margin-left: auto;
    }
    .rn__modes { min-width: 0; }
    /* The style switch is a labelled control on its own line rather than a
       nameless three-way crammed into the section heading. */
    .rn__stylebar {
        display: flex; align-items: center; gap: var(--space-2, 8px);
        flex-wrap: wrap;
        margin-bottom: var(--space-3, 12px);
    }
    .rn__stylek {
        font-size: 0.6875rem; font-weight: 700; letter-spacing: 0.07em;
        text-transform: uppercase; color: var(--text-muted);
    }
    .rn__styleedit { margin-left: auto; }

    /* A section is a container, so it is drawn as one (owner feedback
       2026-08-24). The unsectioned group deliberately gets no card: a box
       around "the rest of the ingredients" is a box around nothing. */
    .rn__group { margin-bottom: var(--space-3, 12px); }
    .rn__group--card {
        border: 1px solid var(--border-default);
        border-radius: var(--radius-lg, 10px);
        background: var(--surface-component);
        padding: var(--space-2, 8px);
    }
    .rn__grouphead {
        display: flex; align-items: center; gap: var(--space-2, 8px);
        padding: var(--space-1, 4px) var(--space-1, 4px) var(--space-2, 8px);
        border-bottom: 1px solid var(--divider);
        margin-bottom: var(--space-1, 4px);
    }
    .rn__groupname {
        font-size: 0.8125rem; font-weight: 700; letter-spacing: 0.06em;
        text-transform: uppercase; color: var(--brand-primary);
        min-width: 0;
    }
    .rn__groupcount {
        margin-left: auto;
        font-size: 0.8125rem; color: var(--text-muted);
        font-variant-numeric: tabular-nums;
    }
    .rn__addsec { margin-top: var(--space-2, 8px); }
    .rn__ing { list-style: none; margin: 0; padding: 0; }
    .rn__ing li {
        display: grid;
        grid-template-columns: auto 1fr auto;
        gap: var(--space-3, 12px);
        align-items: baseline;
        padding: var(--space-2, 8px);
        border-bottom: 1px solid var(--divider);
        border-radius: var(--radius-sm, 4px);
    }
    .rn__ing li:hover { background: var(--overlay-hover); }
    /* The whole row is the edit target, so it carries the affordance — the
       quantity and the name are plain text inside it. */
    .rn__ing--target { cursor: pointer; }
    .rn__ing--target:focus-visible {
        outline: 2px solid var(--brand-primary);
        outline-offset: -2px;
    }
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
        display: flex; align-items: center; gap: var(--space-1, 4px);
        opacity: 0;
        transition: opacity 120ms ease;
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
    /* Sub-steps: the step treatment one level in — same numbered bullet, a
       size down, toned and indented behind a rule (feedback 2026-08-24). */
    .rn__substeps {
        list-style: none; counter-reset: rnsub;
        margin: var(--space-3, 12px) 0 0;
        padding: 0 0 0 var(--space-4, 16px);
        border-left: 2px solid var(--border-default);
        display: flex; flex-direction: column; gap: var(--space-2, 8px);
        color: var(--text-secondary);
    }
    .rn__substeps > li {
        counter-increment: rnsub;
        display: grid; grid-template-columns: 24px 1fr;
        gap: var(--space-3, 12px);
        align-items: start;
    }
    .rn__substeps > li::before {
        content: counter(rnsub);
        display: flex; align-items: center; justify-content: center;
        width: 24px; height: 24px; border-radius: 50%;
        background: var(--surface-sunken);
        color: var(--text-muted);
        font-size: 0.75rem; font-weight: 700; font-variant-numeric: tabular-nums;
    }
    .rn__substeps p { margin: 0; max-width: 62ch; line-height: 1.55; font-size: 0.9375rem; }
    .rn__free p { margin: 0 0 var(--space-3, 12px); max-width: 62ch; line-height: 1.6; }
    /* The free-text block is a real <button> (it opens the method editor), so
       it has to be talked back out of looking like one — same trick as the
       ingredient name. */
    .rn__freebtn {
        appearance: none; background: none; border: 0;
        font: inherit; color: inherit; text-align: left;
        display: block; width: 100%; padding: var(--space-1, 4px);
    }
    .rn__empty { color: var(--text-muted); font-size: 0.875rem; }
    .rn__hintblock { color: var(--text-muted); font-size: 0.8125rem; margin: 0 0 var(--space-3, 12px); }
    .rn__editor { margin-top: var(--space-4, 16px); border-top: 1px solid var(--divider); }

    .rn__details { margin-top: var(--space-8, 32px); border-top: 1px solid var(--divider); }
    .rn__disc { padding: var(--space-3, 12px) var(--space-2, 8px) var(--space-4, 16px); }
    .rn__vfacts {
        display: flex; flex-wrap: wrap; gap: var(--space-2, 8px) var(--space-6, 24px);
        margin-bottom: var(--space-3, 12px);
    }
    .rn__vfact { display: flex; flex-direction: column; gap: 2px; }
    .rn__vthis { background: var(--surface-sunken); }
    .rn__vnone { margin-bottom: 0; }
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
        /* One line that scrolls, rather than three rows of facts pushing the
           method off the first screen (owner feedback 2026-08-24; D-011 —
           wide content scrolls inside its own container, never the page). */
        .rn__facts {
            flex-wrap: nowrap;
            overflow-x: auto;
            scrollbar-width: none;
        }
        .rn__facts::-webkit-scrollbar { display: none; }
        /* Hover isn't a gesture a thumb has, so the row cluster is always
           there on a phone. */
        .rn__ingact { opacity: 1; }
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
