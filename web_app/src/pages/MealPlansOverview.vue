<template>
    <!-- FU-609 / R-036 — root on <q-page> for the layout height contract.
         **Fixed-height app-shell page** (the second shape R-036 sanctions, and
         an application of ADR-032 — not a new pattern). Converted from
         document-scroll on 2026-08-29 by Unit 1 of
         BRIEF_MEAL_PLANNER_RAIL_AND_SHELL.
         The three panes own their own scroll; the document does not scroll at
         all above 1024px. This replaced `.planner-sticky`, whose sticky
         columns kept the rails visible while the page's own chrome scrolled
         away — and which subtracted a hardcoded 32px while ignoring the 64px
         header entirely, so both rails overhung the viewport by about a
         header's height (and a further 48px whenever OfflineBanner rendered).
         `:style-fn` takes the *live* offset instead, which is exactly what
         R-036's "never hardcode the offset" clause exists for. Do not
         reintroduce a `calc(100vh - Npx)` here. -->
    <q-page class="q-pa-md meal-plans" :style-fn="pageStyleFn">
        <!-- R-Phase 6 §9-I — skeleton during the initial parallel mount load
            so the planner shape arrives instantly instead of popcorning in. -->
        <MealPlanSkeleton
            v-if="planner.isInitialLoading.value"
            :variant="$q.screen.lt.md ? 'mobile' : 'list'"
        />

        <!-- R-Phase 2 first-run path (§6.7). When the user has no recipes, the
            planner can't do its job — replace the empty 3-column layout with
            a single hero that points to the Cookbook. -->
        <MealPlanFirstRun v-else-if="!planner.recipes.value.length" />

        <template v-else>
            <!-- FU-317 Chunk 5 — reconcile nudge line above the planner
                 when past-day meals need confirming. Hide-when-empty
                 (R-029); the server owns the count via `useReconcileQueue`. -->
            <router-link
                v-if="reconcileTotal > 0"
                to="/meal-plans/reconcile"
                class="meal-plans-reconcile-nudge q-mb-sm"
            >
                {{ reconcileTotal }} past-day meal{{ reconcileTotal === 1 ? '' : 's' }} need{{ reconcileTotal === 1 ? 's' : '' }} confirming →
            </router-link>

            <!-- R-Phase 4 — shared mobile single-day focus (§8.2). Both A
                and B render the same mobile view; the A/B toggle is desktop-
                only because the carousel-vs-grid experiment doesn't apply
                below md. -->
            <template v-if="$q.screen.lt.md">
                <MealPlanMobileFocus
                    :week-days="planner.weekDays.value"
                    :slot-names="planner.slotNames.value"
                    :entries-for="planner.dayEntries"
                    :is-past-day="planner.isPastDay"
                    :current-day-iso="planner.currentDayIso.value"
                    :week-range-label="planner.weekRangeLabel.value"
                    :planned-count="plannedCount"
                    :can-save-current-week="canSaveCurrentWeek"
                    @entry-view="planner.goToRecipe"
                    @entry-cook="planner.cookRecipe"
                    @entry-remove="planner.removeEntry"
                    @entry-adjust="planner.adjustEntryServings"
                    @entry-link="onEntryLink"
                    @entry-unlink="onEntryUnlink"
                    @entry-lighter="onEntryLighter"
                    @entry-fresh="planner.toggleCookFresh"
                    @add-to-slot="onMobileAddToSlot"
                    @open-builder="builderOpen = true"
                    @go-prev-week="planner.goPrevWeek"
                    @go-next-week="planner.goNextWeek"
                    @duplicate-week="planner.confirmDuplicateToNextWeek"
                    @print="planner.printFocusedWeek"
                    @save-template="openSaveTemplate"
                    @open-templates="templatesDrawerOpen = true"
                    @clear-week="planner.confirmClearWeek"
                />

                <!-- The week's consequences, on the phone. Owner feedback
                     2026-09-03: the collapsible card that used to live inside
                     `MealPlanMobileFocus` *"duplicates information so much —
                     just make it a normal card with the expanded contents
                     shown"*, and separately, the ingredient breakdown *"can't
                     be seen properly"* there because that card never had one.
                     Both stop being mobile problems once the phone renders the
                     SAME two components the desktop right rail does (R-001):
                     the status strip, then "This week's shopping" with its
                     per-ingredient rows and the full-demand disclosure. No
                     wrapper, no header restating what is inside it. -->
                <div v-if="plannedCount > 0" class="planner-mobile-week q-mt-md">
                    <MealPlanWeekStatus
                        :planned-count="plannedCount"
                        :shortfall-count="planner.needsCookingEntries.value.length"
                        :fresh-count="planner.freshEntries.value.length"
                        :outstanding-count="planner.needToBuyOutstanding.value.length"
                        :on-list-count="planner.needToBuyOnList.value.length"
                        :cook-by-label="planner.cookByLabel.value"
                    />
                    <MealPlanShoppingSummary
                        :focused-plan="planner.focusedPlan.value"
                        :ingredients-loading="planner.ingredientsLoading.value"
                        :ingredients="planner.ingredients.value"
                        :need-to-buy="planner.needToBuy.value"
                        :outstanding="planner.needToBuyOutstanding.value"
                        :generating="planner.generating.value"
                        @add-to-list="planner.openAddToList"
                    />
                </div>
            </template>
            <!-- ── Desktop: the fixed-height three-pane shell (Unit 1 §3.1) ──
                 Panes scroll, the page does not. The rail keeps its search and
                 target banner pinned; the week keeps its toolbar pinned; the
                 right pane keeps the calendar pinned. -->
            <template v-else>
            <div class="planner-shell">
                <!-- ── Left: the recipe rail (Unit 2, §4.1-§4.2) ──────────── -->
                <!--
                     THE COLLAPSE CONTRACT — D-023 carve-out, read before changing.

                     D-023 says a persistent control keeps its shape and its
                     place across modes, and its establishing case is *a
                     shopping-list side rail hidden per mode*, with the owner's
                     verdict: "this will only lead to confusion with UI elements
                     shape shifting." That rule lands directly on this rail, and
                     it is why the predecessor plan's "picker drawer" route was
                     rejected — a drawer that appears per mode is exactly the
                     shape D-023 forbids.

                     A user-operated disclosure is nonetheless compliant:
                     D-023's stated violation signal is "two controls with
                     different shapes and the same verb, each v-if'd to a
                     different mode". This is ONE control in ONE place whose
                     size the user chose, and the collapsed form is a LABELLED
                     strip rather than a bare icon, so it reads as the same
                     rail, smaller.

                     **The system may only ever OPEN the rail. It may never
                     close it.** No auto-collapse after an add, on target
                     cancel, or on week change. Nothing shape-shifts under the
                     user unless the user did it. Do not "fix" this to close
                     after an add — that reintroduces precisely the confusion
                     D-023 exists to prevent. -->
                <div
                    class="planner-pane planner-pane--rail"
                    :class="{ 'planner-pane--rail-collapsed': !railOpen }"
                >
                    <!-- S1 — resting, collapsed. This is the DEFAULT on every
                         arrival (D4/D3, owner 2026-08-29): the rail does not
                         remember being open, and it does NOT auto-open on an
                         empty week — the brief recommended that and the owner
                         declined it. It opens on exactly two events: a slot is
                         selected, or this strip is clicked. -->
                    <button
                        v-if="!railOpen"
                        type="button"
                        class="rail-strip"
                        aria-label="Show recipes"
                        :aria-expanded="false"
                        @click="openRail"
                    >
                        <q-icon :name="ICONS.search" size="18px" />
                        <!-- L100 — "filter button changes based on filter
                             state": a dot when the list is narrowed, so the
                             collapsed rail still says something is filtered. -->
                        <span v-if="railFilterActive" class="rail-strip__dot" />
                        <span class="rail-strip__label">
                            Recipes · {{ planner.recipes.value.length }}
                        </span>
                        <q-icon :name="ICONS.chevron_right" size="18px" />
                        <q-tooltip anchor="center right" self="center left">
                            Show recipes
                        </q-tooltip>
                    </button>

                    <!-- S2 / S3 — open. The picker owns browsing vs targeting;
                         the page owns only whether the rail is open. -->
                    <template v-else>
                        <div class="rail-head">
                            <BaseButton
                                variant="icon"
                                size="sm"
                                :icon="ICONS.chevron_left"
                                aria-label="Hide recipes"
                                @click="railOpen = false"
                            >
                                <q-tooltip>Hide recipes</q-tooltip>
                            </BaseButton>
                            <span class="rail-head__label">Recipes</span>
                        </div>
                        <MealPlanRecipePicker
                            v-model:recipe-search="planner.recipeSearch.value"
                            class="planner-pane__fill"
                            :recipes="planner.recipes.value"
                            :focused-target="planner.focusedTarget.value"
                            :suggestions="planner.suggestions.value"
                            :format-date="planner.formatDate"
                            @cancel-target="planner.clearFocusedTarget"
                            @recipe-pick="planner.pickRecipe"
                            @palette-meal-adjust="planner.adjustPaletteMeals"
                            @suggestions-requested="planner.loadSuggestions"
                        />
                    </template>
                </div>

                <!-- ── Middle: consolidated toolbar + the week ─────────────── -->
                <div class="planner-pane planner-pane--week">
                    <!-- Pinned chrome (§3.2). Row 1 is navigation + the two
                         primary actions; row 2 is the week's status. Neither
                         scrolls away, which is the whole point of the shell.
                         Acceptance: <= 96px at 1280x900 with batchEnabled and a
                         full week, and nothing wraps to a third line. FU-738 is
                         the cautionary tale — a toolbar band allowed to overflow
                         put the primary CTA off-screen on the shopping list. -->
                    <div class="planner-toolbar">
                        <div class="row items-center no-wrap planner-toolbar__nav">
                            <!-- D4 (owner, 2026-08-29) — the page takes NO
                                 title. The week range is not promoted to one
                                 either; it stays exactly where it is, between
                                 the prev/next buttons. F40 stands: no "Week
                                 of…" prefix. The relative sub-label is what
                                 says *which* week, since a bare date range
                                 doesn't. -->
                            <BaseButton
                                variant="icon"
                                :icon="ICONS.chevron_left"
                                aria-label="Previous week"
                                @click="planner.goPrevWeek"
                            >
                                <q-tooltip>Previous week</q-tooltip>
                            </BaseButton>
                            <div class="planner-toolbar__week">
                                <div class="text-subtitle2">{{ planner.weekRangeLabel.value }}</div>
                                <div class="text-caption dora-text-muted">
                                    {{ planner.weekRelativeLabel.value }}
                                </div>
                            </div>
                            <!-- F17 asked for the next-week arrow *below* the
                                 working area. That bottom arrow is removed:
                                 under the shell the week pane scrolls
                                 internally, so a control at the foot of the
                                 scroller is only reachable after scrolling
                                 seven day cards. Both arrows now sit together
                                 in pinned chrome, reachable at any scroll
                                 position — which is the intent F17 was after. -->
                            <BaseButton
                                variant="icon"
                                :icon="ICONS.chevron_right"
                                aria-label="Next week"
                                @click="planner.goNextWeek"
                            >
                                <q-tooltip>Next week</q-tooltip>
                            </BaseButton>

                            <q-space />

                            <!-- FU-304 closed 2026-07-07 — Direction A won; the
                                 A/B `BaseSegmented` toggle and the sibling
                                 `/meal-plans/board` page were retired. -->
                            <BaseButton
                                variant="secondary"
                                :icon="ICONS.dora_voice"
                                :label="compactToolbar ? undefined : 'Build my week'"
                                @click="builderOpen = true"
                            >
                                <q-tooltip>Build my week</q-tooltip>
                            </BaseButton>

                            <!-- The overflow menu (§3.2). Absorbs what used to
                                 be three toolbar siblings (duplicate, print,
                                 Clear week), a full row for one toggle, and a
                                 right-pane card that wrapped a single button.
                                 F37 keeps Clear week labelled and destructive
                                 rather than an icon-only sibling of print. -->
                            <BaseButton
                                variant="icon"
                                :icon="ICONS.more_vert"
                                aria-label="More week actions"
                                class="q-ml-xs"
                            >
                                <q-tooltip>More week actions</q-tooltip>
                                <q-menu anchor="bottom right" self="top right">
                                    <q-list style="min-width: 220px">
                                        <q-item
                                            v-close-popup clickable
                                            :disable="!planner.focusedPlan.value"
                                            @click="planner.confirmDuplicateToNextWeek"
                                        >
                                            <q-item-section avatar>
                                                <q-icon :name="ICONS.content_copy" />
                                            </q-item-section>
                                            <q-item-section>Duplicate to next week</q-item-section>
                                        </q-item>
                                        <q-item
                                            v-close-popup clickable
                                            :disable="!planner.focusedPlan.value"
                                            @click="planner.printFocusedWeek"
                                        >
                                            <q-item-section avatar>
                                                <q-icon :name="ICONS.print" />
                                            </q-item-section>
                                            <q-item-section>Print this week</q-item-section>
                                        </q-item>

                                        <q-separator />

                                        <!-- F12 stays satisfied — the templates
                                             drawer itself is unchanged; only the
                                             card that wrapped its button is
                                             gone. -->
                                        <q-item
                                            v-close-popup clickable
                                            :disable="!canSaveCurrentWeek"
                                            @click="openSaveTemplate"
                                        >
                                            <q-item-section avatar>
                                                <q-icon :name="ICONS.save" />
                                            </q-item-section>
                                            <q-item-section>Save week as template…</q-item-section>
                                        </q-item>
                                        <q-item
                                            v-close-popup clickable
                                            @click="templatesDrawerOpen = true"
                                        >
                                            <q-item-section avatar>
                                                <q-icon :name="ICONS.event_repeat" />
                                            </q-item-section>
                                            <!-- Owner feedback 2026-09-03 —
                                             "browse + apply" named the drawer's
                                             mechanics; "Apply template…" names
                                             what you came for, and the drawer
                                             still browses. -->
                                        <q-item-section>Apply template…</q-item-section>
                                        </q-item>

                                        <q-separator />

                                        <!-- U7 / F37 — the destructive action
                                             keeps its label and its colour. -->
                                        <q-item
                                            v-close-popup clickable
                                            :disable="!planner.focusedPlan.value"
                                            class="text-negative"
                                            @click="planner.confirmClearWeek"
                                        >
                                            <q-item-section avatar>
                                                <q-icon :name="ICONS.delete_outline" color="negative" />
                                            </q-item-section>
                                            <q-item-section>Clear week</q-item-section>
                                        </q-item>
                                    </q-list>
                                </q-menu>
                            </BaseButton>
                        </div>

                        <!-- Row 2 — the status strip (D8: it stays in the
                             toolbar rather than becoming a `PageCountsFooter`).
                             This is a *status* strip, not a count of listed
                             records, and F45 wants the shortfall to have exactly
                             one home, near the week nav. The divergence from the
                             app-wide sticky-footer convention (L93/L212/L231) is
                             deliberate and recorded in the worklog — it is not
                             an oversight, and it should not be "made
                             consistent" without revisiting D8.
                             R-Phase 2 (U2 + H1) promoted this block; it now
                             lives in pinned chrome, which is what its own
                             comment always said it was for. -->
                        <div class="planner-toolbar__statusrow">
                            <MealPlanWeekStatus
                                class="planner-toolbar__status"
                                :planned-count="plannedCount"
                                :shortfall-count="planner.needsCookingEntries.value.length"
                                :fresh-count="planner.freshEntries.value.length"
                                :outstanding-count="planner.needToBuyOutstanding.value.length"
                                :on-list-count="planner.needToBuyOnList.value.length"
                                :cook-by-label="planner.cookByLabel.value"
                            />
                            <!-- Owner feedback 2026-09-01 — "show all meal
                                 slots feels like it should be always visible
                                 (not in an overflow menu)". It is a *view*
                                 switch over the week you are looking at, not a
                                 week action like duplicate/print/clear, so
                                 burying it among those was a category error as
                                 well as a discoverability one: nothing else in
                                 that menu changes what the day cards render.
                                 It sits on the status row rather than row 1
                                 because row 1 is already at its width budget
                                 (§3.2 — <= 96px, nothing wraps to a third
                                 line), and this row has slack. -->
                            <q-toggle
                                v-model="showAllSlots"
                                dense
                                size="sm"
                                label="All slots"
                                class="planner-toolbar__allslots"
                            >
                                <q-tooltip>
                                    {{ showAllSlots
                                        ? 'Showing every household meal slot on each day'
                                        : 'Showing only slots with a meal planned' }}
                                </q-tooltip>
                            </q-toggle>
                        </div>
                    </div>

                    <!-- The week itself — the only scrolling part of this
                         pane. §3.7: day cards MUST stay a vertical stack of
                         full-width blocks with slot rows inside them. When the
                         rail expands in Unit 2 the pane narrows, and because the
                         cards are full-width stacked blocks that reflow is
                         horizontal only — so a card's vertical position doesn't
                         move and the slot just clicked stays under the cursor.
                         Make the week columnar and the rail's auto-open stops
                         being safe. (Also F46/F27, already implemented.) -->
                    <!-- The "Plan this week" empty-week banner was removed on
                         2026-09-04 (owner): it sat directly under a toolbar
                         that already carries "Build my week", so an empty week
                         showed the same primary button twice, one above the
                         other. The toolbar's copy is always there — the
                         banner's wasn't adding an affordance, only a second
                         instance of one. -->
                    <div ref="weekScrollRef" class="planner-pane__scroll">
                        <transition :name="planner.weekTransition.value" mode="out-in">
                            <div
                                :key="planner.focusedMonday.value"
                                @touchstart.passive="planner.onTouchStart"
                                @touchend.passive="planner.onTouchEnd"
                            >
                                <MealPlanWeekDayCard
                                    v-for="day in planner.weekDays.value"
                                    :key="day.iso"
                                    :data-day-iso="day.iso"
                                    :class="day.iso === arrivedDayIso ? arrivalFeedback : undefined"
                                    :day="day"
                                    :is-past="planner.isPastDay(day.iso)"
                                    :is-today="day.iso === planner.currentDayIso.value"
                                    :collapsed-by-default="weekHasToday && planner.isPastDay(day.iso)"
                                    :slot-names="planner.slotNames.value"
                                    :slot-entries="(slot: string) => planner.slotEntries(day.iso, slot)"
                                    :other-entries="planner.otherSlotEntries(day.iso)"
                                    :is-targeted-slot="(slot: string) => planner.isTargeted(day.iso, slot)"
                                    :hovered-recipe-ids="planner.hoveredRecipeIds.value"
                                    :format-date="planner.formatDate"
                                    :show-all-slots="showAllSlots"
                                    :nutrition="planner.dayNutrition(day.iso)"
                                    @select-slot="(slot: string) => planner.selectSlot(day.iso, slot)"
                                    @entry-view="planner.goToRecipe"
                                    @entry-cook="planner.cookRecipe"
                                    @entry-remove="planner.removeEntry"
                                    @entry-adjust="planner.adjustEntryServings"
                                    @entry-link="onEntryLink"
                                    @entry-unlink="onEntryUnlink"
                                    @entry-lighter="onEntryLighter"
                                    @entry-fresh="planner.toggleCookFresh"
                                />
                            </div>
                        </transition>

                        <!-- FU-451 — budget-defense swaps (renders itself only when
                             money features are on AND the week is over budget). -->
                        <SwapSuggestionsPanel
                            :meal-plan-id="planner.focusedPlan.value?.meal_plan_id ?? null"
                            @changed="onSwapApplied"
                        />
                    </div>
                </div>

                <!-- ── Right: calendar pinned, shopping summary scrolling ──── -->
                <!-- §3.3 — deliberately NOT merged into the middle pane. The
                     calendar is navigation, and scrolling navigation away
                     repeats the bottom-arrow mistake; the shopping summary is
                     the payoff of planning, so putting it below seven day cards
                     buries it. F14 is honoured verbatim: the calendar widget
                     sits on the right, above the shopping info. -->
                <div class="planner-pane planner-pane--context">
                    <!-- Owner feedback 2026-09-01 — "make the 'this week's
                         shopping' and 'full ingredient demand' the same width
                         as the calendar". They were narrower, and not by a
                         style choice: the calendar sat OUTSIDE
                         `.planner-pane__scroll` at full pane width while the
                         two cards sat inside it, behind its `padding-right`
                         and its reserved scrollbar gutter. Matching the two
                         edges by hand is not possible — the gutter's width is
                         the OS's, not ours — so the calendar moves inside the
                         same scroller and stays pinned with `position: sticky`
                         instead. One containing block, one right edge, and
                         §3.3's "the calendar is navigation and must not scroll
                         away" still holds. -->
                    <div class="planner-pane__scroll">
                        <MealPlanCalendar
                            v-model:focused-monday="planner.focusedMonday.value"
                            class="planner-context__cal q-mb-sm"
                            @day-selected="scrollWeekToDay"
                        />
                        <MealPlanShoppingSummary
                            :focused-plan="planner.focusedPlan.value"
                            :ingredients-loading="planner.ingredientsLoading.value"
                            :ingredients="planner.ingredients.value"
                            :need-to-buy="planner.needToBuy.value"
                            :outstanding="planner.needToBuyOutstanding.value"
                            :generating="planner.generating.value"
                            @add-to-list="planner.openAddToList"
                            @hover-ingredient="planner.hoverIngredient"
                            @clear-hover="planner.clearHover"
                        />
                    </div>
                </div>
            </div>
            </template>
        </template>

        <!-- Mobile-only bottom-sheet picker (R-Phase 4 / Q4). -->
        <MealPlanPickerSheet
            v-if="$q.screen.lt.md"
            v-model="pickerSheetOpen"
            v-model:recipe-search="planner.recipeSearch.value"
            :suggestions="planner.suggestions.value"
            :recipes="planner.recipes.value"
            :focused-target="planner.focusedTarget.value"
            :format-date="planner.formatDate"
            @cancel-target="planner.clearFocusedTarget"
            @recipe-pick="planner.pickRecipe"
            @palette-meal-adjust="planner.adjustPaletteMeals"
            @suggestions-requested="planner.loadSuggestions"
        />

        <!-- FU-637 — "find a lighter option" for one meal. Opened from the
            meal's own menu; Dora never raises it herself. -->
        <MealPlanLighterDialog
            v-model="lighterOpen"
            :meal-plan-id="planner.focusedPlan.value?.meal_plan_id ?? null"
            :entry="lighterEntry"
            @swapped="onLighterSwapped"
        />

        <!-- Templates drawer (R-Phase 5 / §9-E). Apply + manage in-place;
            no page hop. Shared by both A and B pages. -->
        <MealPlanTemplatesDrawer
            v-model="templatesDrawerOpen"
            :templates="planner.templates.value"
            :can-save-current-week="canSaveCurrentWeek"
            @save-current-week="openSaveTemplate"
            @apply-recurring="openRecurring"
            @apply-template="onTemplateApply"
        />

        <!-- Save the focused week as a template ─────────────────────── -->
        <BaseDialog v-model="saveTemplateOpen" title="Save as a template" closable card-style="min-width: 340px">
            <q-card-section class="q-pt-none q-gutter-sm">
                <q-input v-model="templateName" outlined dense autofocus label="Template name" />
                <q-input
                    v-model="templateDescription"
                    outlined dense type="textarea" autogrow
                    label="Description (optional)"
                />
            </q-card-section>
            <template #actions>
                <BaseButton variant="ghost" label="Cancel" v-close-popup />
                <BaseButton
                    variant="primary" label="Save template"
                    :loading="savingTemplate"
                    :disable="!templateName.trim()"
                    @click="confirmSaveTemplate"
                />
            </template>
        </BaseDialog>

        <!-- "Build my week" auto-planner (FU-596) ──────────────────── -->
        <!-- Owner feedback 2026-08-27 — one dialog for the page: the mobile
             card, the desktop summary and the builder's final step all open
             this same picker, so there is exactly one add-to-list flow on the
             planner and it is the recipe page's flow (R-001). -->
        <AddToListDialog
            ref="addToListRef"
            v-model="planner.addToListOpen.value"
            title="Add this week's shopping to a list"
            :rows="planner.addToListRows.value"
            :unlinked="planner.addToListUnlinked.value"
            :default-new-list-name="planner.addToListNewName.value"
            @confirm="onAddToListConfirm"
        />

        <MealPlanBuilderDialog
            v-model="builderOpen"
            :recipes="planner.recipes.value"
            :slot-names="planner.slotNames.value"
            :week-days="planner.weekDays.value"
            :current-day-iso="planner.currentDayIso.value"
            :is-past-day="planner.isPastDay"
            :format-date="planner.formatDate"
            :money-enabled="moneyEnabled"
            :build-plan="planner.builderBuildPlan"
            :open-add-to-list="planner.openAddToList"
            :print-week="planner.printFocusedWeek"
        />

        <!-- Apply a template recurringly over a week range ─────────── -->
        <!-- Owner feedback 2026-09-03 — *"apply recurring modal needs some
             polish on it with the alignment and spacing of elements/inputs."*
             Three things were off and all three were the markup, not taste:
             `q-gutter-sm` puts a NEGATIVE top margin on its container and a
             margin on every child, so the section's own top padding was
             cancelled and the select sat tight under the title; the two date
             inputs used `q-col-gutter-sm` while their parent used `q-gutter-sm`,
             so the row's spacing didn't match the gap above it; and the
             explanatory caption sat hard against the second field with no
             separation from the controls it describes. One flex column with one
             token gap, and the note gets its own space. `min-width: 360px` also
             went — a floor beats `max-width: 95vw` on a 320px phone, which is
             the FU-852 / builder-dialog lesson applied here. -->
        <BaseDialog v-model="recurringOpen" title="Apply recurring" closable card-style="min-width: 0; width: min(420px, 94vw)">
            <q-card-section class="q-pt-none recurring-form">
                <q-select
                    v-model="recurringSource"
                    outlined dense
                    :options="planner.recurringSourceOptions.value"
                    emit-value map-options
                    label="Template or rotating set"
                />
                <div class="recurring-form__dates">
                    <q-input v-model="recurringStart" outlined dense type="date" label="From (week of)" />
                    <q-input v-model="recurringEnd" outlined dense type="date" label="To (week of)" />
                </div>
                <div class="text-caption dora-text-muted recurring-form__note">
                    Each week is forked from the template (a set rotates through its templates).
                    Past days are skipped; up to 26 weeks.
                </div>
            </q-card-section>
            <template #actions>
                <BaseButton variant="ghost" label="Cancel" v-close-popup />
                <BaseButton
                    variant="primary" label="Apply"
                    :loading="recurringApplying"
                    :disable="!recurringSource || !recurringStart || !recurringEnd"
                    @click="confirmRecurring"
                />
            </template>
        </BaseDialog>
    </q-page>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import BaseButton from 'src/components/BaseButton.vue';
    import BaseDialog from 'src/components/BaseDialog.vue';
    import MealPlanCalendar from 'components/MealPlanCalendar.vue';
    import MealPlanFirstRun from 'src/components/MealPlanFirstRun.vue';
    import MealPlanMobileFocus from 'src/components/MealPlanMobileFocus.vue';
    import MealPlanPickerSheet from 'src/components/MealPlanPickerSheet.vue';
    import MealPlanRecipePicker from 'src/components/MealPlanRecipePicker.vue';
    import MealPlanShoppingSummary from 'src/components/MealPlanShoppingSummary.vue';
    import AddToListDialog from 'src/components/shoppingList/AddToListDialog.vue';
    import type { AddToListConfirm } from 'src/components/shoppingList/addToListTypes';
    import MealPlanSkeleton from 'src/components/MealPlanSkeleton.vue';
    import MealPlanTemplatesDrawer from 'src/components/MealPlanTemplatesDrawer.vue';
    import MealPlanLighterDialog from 'src/components/MealPlanLighterDialog.vue';
    import MealPlanWeekDayCard from 'src/components/MealPlanWeekDayCard.vue';
    import MealPlanWeekStatus from 'src/components/MealPlanWeekStatus.vue';
    import MealPlanBuilderDialog from 'components/MealPlanBuilderDialog.vue';
    import SwapSuggestionsPanel from 'src/components/SwapSuggestionsPanel.vue';
    import { useMealPlanner } from 'src/composables/useMealPlanner';
    import { useMealPlanStore } from 'src/stores/mealPlanStore';
    // FU-317 Chunk 5 — reconcile nudge line count.
    import { useReconcileQueue } from 'src/composables/useReconcileQueue';
    import { useMoneyEnabled } from 'src/composables/useMoneyEnabled';
    import { shiftDays } from 'src/helpers/weekDates';
    import { useQuasar } from 'quasar';
    import type { MealPlanEntry } from 'src/models/mealPlan';
    import { useMicroFeedback } from 'src/composables/useMicroFeedback';
    import { computed, nextTick, ref, watch } from 'vue';

    const planner = useMealPlanner();
    const { moneyEnabled } = useMoneyEnabled();
    const { total: reconcileTotal } = useReconcileQueue();
    const mealPlanStore = useMealPlanStore();
    const $q = useQuasar();

    // FU-451 — a budget-defense swap mutates a meal-plan entry's recipe via a
    // dedicated endpoint, so reload the plans (week grid) + ingredient demand
    // to reflect it.
    async function onSwapApplied() {
        await mealPlanStore.getMealPlansAsync();
        await planner.loadIngredients();
    }

    // FU-304 closed 2026-07-07 — Direction A wins. The A/B view helper
    // (`useMealPlannerView`), the desktop `BaseSegmented` toggle, and the
    // `onMounted` "restore Grid view" redirect were all retired with the
    // Direction B page. `MealPlansOverview` is now the only planner surface.

    // ── Q2 — slot visibility default ───────────────────────────────────────
    // Default off: only used slots render per day (collapses the empty-cell
    // sprawl, U1). Toggle reveals every household slot if the user prefers
    // the legacy view.
    //
    // FU-306 — the toggle is a per-device view preference (not a household
    // pref), so it rides `localStorage` rather than a User/Preference column.
    // Multi-slot households that flip it "on" now keep it on across reloads;
    // a genuine per-household setting can graduate to `Preference` later if
    // the same user wants it synced across their devices.
    const SHOW_ALL_SLOTS_KEY = 'mealPlanShowAllSlots';
    const showAllSlots = ref(readShowAllSlots());
    watch(showAllSlots, (value) => {
        try {
            localStorage.setItem(SHOW_ALL_SLOTS_KEY, value ? '1' : '0');
        } catch {
            // localStorage can be unavailable (private-mode Safari, disk
            // quota exceeded) — fail silent; the session-local ref still
            // works, we just lose cross-reload persistence.
        }
    });
    function readShowAllSlots(): boolean {
        try {
            return localStorage.getItem(SHOW_ALL_SLOTS_KEY) === '1';
        } catch {
            return false;
        }
    }

    const addToListRef = ref<{ setBusy: (v: boolean) => void; newListName: string } | null>(null);
    async function onAddToListConfirm(payload: AddToListConfirm) {
        addToListRef.value?.setBusy(true);
        try {
            await planner.confirmAddToList(
                payload, addToListRef.value?.newListName ?? 'Shopping list',
            );
        } finally {
            addToListRef.value?.setBusy(false);
        }
    }

    const plannedCount = computed(
        () => (planner.focusedPlan.value?.entries ?? []).filter((e) => !e.consumed_at).length,
    );

    // R-036 / ADR-032 — the fixed-height app-shell contract, copied verbatim
    // from `StockOverview.vue` (the canonical implementation) rather than
    // reinvented. `offset` is the live chrome height Quasar measures, so the
    // header and a rendered OfflineBanner are both accounted for; the
    // `height === 0` branch is Quasar's pre-measurement first paint.
    function pageStyleFn(offset: number, height: number) {
        return {
            height: height === 0 ? `calc(100vh - ${offset}px)` : `${height - offset}px`,
        };
    }

    // ── The rail's open state (§4.2, D3 as answered) ───────────────────────
    //
    // DERIVED, never remembered. Two house precedents disagreed —
    // `useListViewMode` persists to localStorage, `useFilterPanelExpanded`
    // deliberately stopped in favour of "the panel is open when there is
    // something in it" (owner, 2026-08-20, annotated "adopt elsewhere") — and
    // the owner chose derivation, narrower than the brief proposed: the rail is
    // **always collapsed on arrival**, and the brief's empty-week auto-open was
    // explicitly declined. Do not add it back, and do not persist this.
    const railOpen = ref(false);

    function openRail() {
        railOpen.value = true;
    }

    // Arming a slot opens the rail — one of the only two things that may.
    // This watcher deliberately has NO symmetric close: it fires on every
    // target change, so a close branch would yank the rail out from under a
    // user who was mid-scroll. See the collapse contract in the template.
    //
    // Moving focus into the rail's search (§4.6) is the picker's own job, not
    // this watcher's — it mounts as a *result* of `openRail()`, so a template
    // ref read here is still null. See `MealPlanRecipePicker`'s focus block.
    watch(() => planner.focusedTarget.value, (target) => {
        if (target) openRail();
    });

    // ── Calendar → week pane (Unit 3, §5) ─────────────────────────────────
    //
    // Clicking a day in the calendar focuses its week AND scrolls the week pane
    // to that day's card. This is the payoff of the whole redesign and is only
    // possible because Unit 1 gave the middle pane its own scroll container —
    // under document-scroll there was nothing to scroll *within*.
    //
    // The page owns this rather than the calendar because the page owns the
    // scroller; the calendar only names the day. The card is found by a
    // `data-day-iso` attribute rather than a ref array: the week re-renders
    // through a <transition> on every week change, so a ref collected before
    // the change points at a card that is on its way out.
    const weekScrollRef = ref<HTMLElement | null>(null);
    const arrivedDayIso = ref<string | null>(null);
    // One `dora-settle` on the arriving card — a one-shot marking the arrival,
    // never bound to a persistent condition (§4.7 / D-010: an animation that
    // repeats on its own becomes wallpaper).
    const arrivalFeedback = useMicroFeedback(() => arrivedDayIso.value, 'settle');

    async function scrollWeekToDay(dayIso: string) {
        // The week may have just changed, so wait for the new cards to render.
        await nextTick();
        const card = weekScrollRef.value
            ?.querySelector<HTMLElement>(`[data-day-iso="${dayIso}"]`);
        if (!card) return;
        card.scrollIntoView({ behavior: 'smooth', block: 'start' });
        arrivedDayIso.value = dayIso;
    }

    // L100 — the collapsed strip shows a dot when the list is narrowed. The
    // search box is the only narrowing the page can see from out here; the chip
    // selection lives inside the picker, which is unmounted while collapsed.
    const railFilterActive = computed(() => !!planner.recipeSearch.value.trim());

    // §3.2 acceptance — the toolbar must not wrap to a third line. Measured at
    // 1024px it did (129px tall, the FU-738 failure mode where an overflowing
    // toolbar band pushes the primary CTA out of reach), because the week pane
    // is whatever the two fixed side panes leave behind: 280 + 300 + gutters,
    // so ~380px at 1024 against ~636px at 1280.
    //
    // Same treatment as `StockOverview.vue`'s `compactToolbar`: the action drops
    // its label and rides its icon alone, with the tooltip carrying the name.
    // The threshold is expressed against the *viewport* because that is what
    // Quasar makes reactive, but it is derived from the pane: below ~1120px the
    // week pane falls under ~480px, which is where the labelled button stops
    // fitting beside the week nav. Re-measure this if the side-pane widths
    // change — Unit 2's collapsible rail will hand the week ~234px back, at
    // which point this may be able to relax.
    // 1180, up from 1120 on 2026-09-01: the rail widened 280 -> 340, so the
    // week pane loses 60px at every viewport width and the labelled button
    // stops fitting 60px sooner.
    const WEEK_TOOLBAR_COMPACT_BELOW_PX = 1180;
    const compactToolbar = computed(() => $q.screen.width < WEEK_TOOLBAR_COMPACT_BELOW_PX);

    // Shared by the toolbar's overflow menu and the templates drawer, which
    // both gate "save this week" on the same fact (R-003: one source, not two
    // copies of the same predicate).
    // Owner feedback 2026-09-01 — past days fold "if today is within the
    // displayed week, because we want to see the whole past week in one go".
    // So the trigger is a fact about the WEEK, computed once here rather than
    // seven times inside the cards.
    const weekHasToday = computed(
        () => planner.weekDays.value.some((d) => d.iso === planner.currentDayIso.value),
    );

    const canSaveCurrentWeek = computed(
        () => !!planner.focusedPlan.value && planner.focusedPlan.value.entries.length > 0,
    );

    // ── Save-template dialog (page-local UI state) ─────────────────────────
    const saveTemplateOpen = ref(false);
    const templateName = ref('');
    const templateDescription = ref('');
    const savingTemplate = ref(false);

    function openSaveTemplate() {
        templateName.value = `Week of ${planner.formatDate(planner.focusedMonday.value)}`;
        templateDescription.value = '';
        saveTemplateOpen.value = true;
    }
    async function confirmSaveTemplate() {
        savingTemplate.value = true;
        try {
            const ok = await planner.saveFocusedWeekAsTemplate(templateName.value, templateDescription.value);
            if (ok) saveTemplateOpen.value = false;
        } finally {
            savingTemplate.value = false;
        }
    }

    // ── Recurring-apply dialog (page-local UI state) ───────────────────────
    const recurringOpen = ref(false);
    const recurringSource = ref<string | null>(null);
    const recurringStart = ref('');
    const recurringEnd = ref('');
    const recurringApplying = ref(false);

    async function openRecurring() {
        const ready = await planner.loadRecurringSources();
        if (!ready) return;
        recurringSource.value = planner.recurringSourceOptions.value[0]?.value ?? null;
        recurringStart.value = planner.focusedMonday.value;
        recurringEnd.value = shiftDays(planner.focusedMonday.value, 28); // default 4 weeks
        recurringOpen.value = true;
    }
    async function confirmRecurring() {
        if (!recurringSource.value || !recurringStart.value || !recurringEnd.value) return;
        recurringApplying.value = true;
        try {
            const ok = await planner.applyRecurring({
                source: recurringSource.value,
                startMonday: recurringStart.value,
                endMonday: recurringEnd.value,
            });
            if (ok) recurringOpen.value = false;
        } finally {
            recurringApplying.value = false;
        }
    }

    // ── Sequential builder (page-local open state) ─────────────────────────
    const builderOpen = ref(false);

    // ── Mobile add-flow (R-Phase 4) ────────────────────────────────────────
    const pickerSheetOpen = ref(false);
    function onMobileAddToSlot(dayIso: string, slot: string) {
        planner.selectSlot(dayIso, slot);
        if (planner.focusedTarget.value) pickerSheetOpen.value = true;
    }

    // FU-637 — lighter-alternative dialog for a single meal.
    const lighterOpen = ref(false);
    const lighterEntry = ref<MealPlanEntry | null>(null);
    function onEntryLighter(entry: MealPlanEntry) {
        lighterEntry.value = entry;
        lighterOpen.value = true;
    }
    async function onLighterSwapped() {
        // Same refresh the budget axis uses — one applied-swap path, one reload.
        await onSwapApplied();
        $q.notify({
            type: 'positive', position: 'bottom-right',
            message: 'Swapped for the lighter meal.',
        });
    }

    // PROPOSAL_MEAL_PLANS_PART_2 — link/unlink a cook batch (one cook, several
    // days). The day picker ticks the days this cook covers; >=2 links them.
    const dayOf = (iso: string) => iso.slice(0, 10);
    function onEntryLink(entry: MealPlanEntry) {
        const covered = new Set([dayOf(entry.scheduled_for), ...planner.cookBatchDays(entry)]);
        const items = planner.weekDays.value
            .filter((d) => !planner.isPastDay(d.iso))
            .map((d) => ({ label: `${d.label} · ${planner.formatDate(d.iso)}`, value: d.iso }));
        if (items.length < 2) {
            $q.notify({
                type: 'info', position: 'bottom-right',
                message: 'No other upcoming days this week to cook ahead for.',
            });
            return;
        }
        $q.dialog({
            title: entry.cook_batch_id ? 'Change cook days' : 'Cook once for more days',
            message: `Cook ${entry.recipe_name} once (${entry.slot}) and eat it on the days you tick.`,
            options: {
                type: 'checkbox',
                model: items.filter((i) => covered.has(dayOf(i.value))).map((i) => i.value),
                items,
            },
            cancel: { noCaps: true },
            persistent: false,
        }).onOk((picked: string[]) => {
            void planner.setCookDays(entry, picked);
        });
    }
    // "Separate this cook" keeps every day's meal and only breaks the link
    // between them — the one case the owner wanted a copy left behind for
    // (2026-09-03). `setCookDays` in its default `redefine` mode does the
    // opposite, and used to be what this called, which is how un-ticking a day
    // in "Change cook days" left an unlinked duplicate.
    function onEntryUnlink(entry: MealPlanEntry) {
        void planner.separateCook(entry);
    }

    // ── Templates drawer (R-Phase 5 / §9-E) ────────────────────────────────
    const templatesDrawerOpen = ref(false);
    async function onTemplateApply(templateId: string) {
        const ok = await planner.warnBeforeReplaceWeek();
        if (!ok) return;
        await planner.applyTemplate(templateId);
        templatesDrawerOpen.value = false;
    }
</script>

<style scoped>
    /* D-010 — the week carousel hand-rolled `transform 0.18s ease` — a literal
       duration and a stock easing curve, which the rule names as the violation
       ("all animation reads `--motion-*` tokens — no literal `ms`"). 0.18s sat
       between two existing tokens for no reason; `--motion-normal` (200ms) is
       the nearest and is what the rest of the app's page-level transitions
       use. Fixed here as a side-effect of Unit 1, per the brief. */
    .wk-down-enter-active,
    .wk-down-leave-active,
    .wk-up-enter-active,
    .wk-up-leave-active {
        transition:
            transform var(--motion-normal) var(--motion-ease),
            opacity var(--motion-normal) var(--motion-ease);
    }
    .wk-down-enter-from { transform: translateY(20px); opacity: 0; }
    .wk-down-leave-to { transform: translateY(-20px); opacity: 0; }
    .wk-up-enter-from { transform: translateY(-20px); opacity: 0; }
    .wk-up-leave-to { transform: translateY(20px); opacity: 0; }

    /* ── The fixed-height three-pane shell (Unit 1 §3.1) ────────────────────
       Replaces U2's `.planner-side` / `.planner-sticky`, which pinned the two
       side columns inside the *document* scroller: the rails stayed visible but
       the page's own chrome scrolled away, and `max-height: calc(100vh - 32px)`
       ignored the 64px header entirely, so both rails overhung the viewport.
       The page no longer scrolls at all here — each pane does.

       §3.4 — mobile is untouched. `$q.screen.lt.md` routes to
       `MealPlanMobileFocus` and every rule below is scoped to >= 1024px, exactly
       as `.planner-sticky` was. Below that the shell is a plain block and the
       document scrolls as before. */
    .planner-shell {
        display: flex;
        flex-direction: column;
        gap: var(--space-4);
        min-height: 0;
    }

    /* §3.4 — mobile reverts to a single window-scrolled column. `:style-fn` is
       a prop, not a media query, so it sets its inline height at every width;
       without this the phone gets a viewport-locked page whose content can only
       overflow rather than scroll. Same escape hatch, same reason, as
       `SettingsShell.vue` (FU-609). Below 1024px the desktop branch isn't even
       mounted — `MealPlanMobileFocus` is. */
    @media (max-width: 1023px) {
        .meal-plans {
            height: auto !important;
        }
    }

    @media (min-width: 1024px) {
        /* The q-page root is sized by `pageStyleFn`; this makes it the flex
           column that hands the remaining height down to the pane row. */
        .meal-plans {
            display: flex;
            flex-direction: column;
            min-height: 0;
        }
        /* Page-level chrome above the shell (the reconcile nudge) keeps its
           natural height; the pane row takes what's left. */
        .planner-shell {
            flex: 1 1 auto;
            flex-direction: row;
            align-items: stretch;
            min-height: 0;
        }
        .planner-pane {
            display: flex;
            flex-direction: column;
            min-height: 0;
        }
        /* D2 — the rail collapses to a 46px LABELLED strip, not to nothing.
           The width animates on tokens (D-010: no literal ms), and because the
           week pane is `flex: 1 1 auto` it simply absorbs the difference — §3.7
           is what makes that safe, since the day cards are full-width stacked
           blocks and so the reflow is horizontal only. A slot the user just
           clicked does not move vertically under the cursor while the rail
           opens. */
        /* 340px, up from 280px (owner 2026-09-01: "make the left rail a little
           wider — feels like the recipe names are getting way too wrapped").
           The row's name clamps at two lines, so a narrow rail didn't truncate
           visibly, it just spent both lines on nearly every recipe. 60px is
           roughly five characters at the row's size — enough to put most names
           on one line without taking the week pane below the width the
           consolidated toolbar needs (see WEEK_TOOLBAR_COMPACT_BELOW_PX, moved
           up by the same 60px). */
        .planner-pane--rail {
            flex: 0 0 340px;
            width: 340px;
            transition: flex-basis var(--motion-normal) var(--motion-ease),
                width var(--motion-normal) var(--motion-ease);
        }
        .planner-pane--rail-collapsed {
            flex: 0 0 46px;
            width: 46px;
        }
        .planner-pane--week {
            flex: 1 1 auto;
            min-width: 0;
        }
        .planner-pane--context {
            flex: 0 0 300px;
            width: 300px;
        }
        /* §3.3 — the calendar is navigation and must stay put; it now does so
           from inside the scroller rather than beside it (see the template
           comment). `--surface-page` is the ground the pane sits on, so the
           shopping card cannot show through as it slides under. */
        .planner-context__cal {
            position: sticky;
            top: 0;
            z-index: 1;
            background: var(--surface-page);
        }
        /* A pane child that fills the pane and scrolls internally itself
           (the recipe picker card owns its own scroller). */
        .planner-pane__fill {
            flex: 1 1 auto;
            min-height: 0;
        }
        /* The canonical inner scroller (`.stock-list`, StockOverview.vue).
           The padding lives HERE, on the scroller, not on the pane: a
           scrollbar paints at the scroller's outer edge, so holding the
           padding here puts the bar hard against the pane edge with the gap
           between it and the content. On the pane instead, the scroller stops
           short and the bar reads as floating inside the content. */
        .planner-pane__scroll {
            flex: 1 1 auto;
            min-height: 0;
            overflow-y: auto;
            padding-right: var(--space-4);
            /* Reserve the gutter so content doesn't jump width when a week
               crosses from non-scrolling to scrolling. */
            scrollbar-gutter: stable;
        }
        /* Pinned chrome — the consolidated toolbar (§3.2). Natural height,
           never scrolls. */
        .planner-toolbar {
            flex: 0 0 auto;
            padding-right: var(--space-4);
        }
    }

    /* S1 — the collapsed rail. A labelled vertical strip, deliberately not a
       bare icon: D-023 is satisfied by this reading as *the same rail, smaller*
       rather than a differently-shaped stand-in for it. */
    .rail-strip {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: var(--space-2);
        height: 100%;
        width: 100%;
        padding: var(--space-2) 0;
        border: 1px solid var(--border-default);
        border-radius: var(--radius-sm);
        background: var(--surface-component);
        color: var(--text-secondary);
        cursor: pointer;
        transition: background var(--motion-fast) var(--motion-ease);
    }
    .rail-strip:hover {
        background: color-mix(in srgb, var(--brand-primary) 8%, var(--surface-component));
    }
    .rail-strip:focus-visible {
        outline: 2px solid var(--brand-primary);
        outline-offset: 2px;
    }
    .rail-strip__label {
        writing-mode: vertical-rl;
        white-space: nowrap;
        font-size: calc(var(--font-size-sm) * 1rem);
        font-weight: 500;
    }
    /* L100 — "filter button changes based on filter state". */
    .rail-strip__dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background: var(--brand-secondary-strong);
    }

    .rail-head {
        display: flex;
        align-items: center;
        gap: var(--space-1);
        flex: 0 0 auto;
        padding-bottom: var(--space-1);
    }
    .rail-head__label {
        font-size: calc(var(--font-size-sm) * 1rem);
        font-weight: 600;
        color: var(--text-secondary);
    }

    .planner-toolbar__week {
        margin-left: var(--space-2);
        margin-right: var(--space-2);
        line-height: 1.2;
    }
    .planner-toolbar__statusrow {
        display: flex;
        align-items: center;
        gap: var(--space-2);
        margin-top: var(--space-2);
    }
    .planner-toolbar__status {
        flex: 1 1 auto;
        min-width: 0;
        /* The strip owns its own bottom margin; inside the row the two
           siblings have to share one baseline. */
        margin-bottom: 0;
    }
    .planner-toolbar__allslots {
        flex: 0 0 auto;
        white-space: nowrap;
    }

    /* The phone's week consequences — the status strip then "This week's
       shopping", the same two components the desktop right rail renders. */
    .planner-mobile-week {
        display: flex;
        flex-direction: column;
        gap: var(--space-2);
    }

    /* The recurring-apply form: one column, one gap, and the note separated
       from the fields it explains (see the template comment for what this
       replaced). */
    .recurring-form {
        display: flex;
        flex-direction: column;
        gap: var(--space-3);
    }
    .recurring-form__dates {
        display: flex;
        gap: var(--space-3);
    }
    .recurring-form__dates > * {
        flex: 1 1 0;
        min-width: 0;
    }
    .recurring-form__note {
        line-height: 1.35;
    }
    /* Two date fields side by side stop fitting well below ~340px of usable
       width; they stack rather than squeeze their own labels (D-011). */
    @media (max-width: 400px) {
        .recurring-form__dates {
            flex-direction: column;
        }
    }

    /* FU-317 Chunk 5 — reconcile nudge above the planner. Text-link
       shape, no card chrome; hover tints via color-mix (matches the
       dashboard chip). */
    .meal-plans-reconcile-nudge {
        display: inline-block;
        padding: 0.35rem 0.75rem;
        color: var(--brand-primary);
        text-decoration: none;
        font-size: calc(var(--font-size-sm) * 1rem);
        font-weight: 500;
        border-radius: var(--radius-sm);
        transition: background 120ms ease;
    }
    .meal-plans-reconcile-nudge:hover,
    .meal-plans-reconcile-nudge:focus-visible {
        background: color-mix(in srgb, var(--brand-primary) 8%, transparent);
    }
</style>
