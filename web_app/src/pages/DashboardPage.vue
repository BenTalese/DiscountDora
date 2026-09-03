<template>
    <!-- FU-609 / R-036 — root on <q-page> for the layout height contract.
         Document-scroll page (the window scrolls the dashboard); no :style-fn. -->
    <q-page class="dora-dash">
        <!-- ───── Hero band ─────────────────────────────────────────────── -->
        <section class="dora-hero">
            <q-avatar size="72px" square class="dora-hero-mascot">
                <img src="../assets/logo-mascot.png" alt="Dashy Dora" />
            </q-avatar>
            <div class="dora-hero-text">
                <div class="dora-hero-greeting">
                    {{ greeting }}<span v-if="firstName">, {{ firstName }}</span>
                </div>
                <div class="dora-hero-line">{{ heroLine }}</div>
            </div>

            <q-space />

            <div class="dora-hero-actions">
                <!-- D3 / feedback C16: the manual refresh button was removed —
                     `onMounted(loadAll)` already refreshes on every navigation
                     to the dashboard, so the button earned nothing. `loadAll`
                     itself stays (alert actions re-fetch through it). -->
                <BaseButton variant="ghost" dense :icon="ICONS.tune" label="Cards">
                    <q-menu anchor="bottom right" self="top right" transition-show="jump-down" transition-hide="jump-up">
                        <q-list dense style="min-width: 300px">
                            <q-item-label header>Show & order cards</q-item-label>
                            <!-- Grouped by zone; reorder is within a zone via the
                                 up/down buttons (C13 tap alternative — works on
                                 mobile, keyboard-accessible). -->
                            <template v-for="group in cardsByZone" :key="group.zone.id">
                                <q-item-label header class="dora-cards-menu-zone">
                                    {{ group.zone.label }}
                                </q-item-label>
                                <q-item
                                    v-for="card in group.cards"
                                    :key="card.id"
                                    :class="cardDnd.bind(card.id).rowClass"
                                    v-bind="cardDnd.bind(card.id).rowProps"
                                >
                                    <!-- desktop-only drag handle. The
                                         up/down buttons remain (C13's
                                         tap-mandatory alternative); drag is
                                         the power-user extra. The handle's
                                         `draggable` attribute is gated by
                                         `$q.platform.is.mobile` so touch
                                         devices keep tap-only. -->
                                    <q-item-section
                                        v-if="cardDragEnabled"
                                        avatar
                                        class="dora-dnd-handle"
                                        v-bind="cardDnd.bind(card.id).handleProps"
                                    >
                                        <q-icon :name="ICONS.drag_indicator" />
                                        <q-tooltip>Drag to reorder within {{ ZONE_LABEL[card.zone] }}</q-tooltip>
                                    </q-item-section>
                                    <q-item-section avatar>
                                        <q-icon :name="card.icon" />
                                    </q-item-section>
                                    <q-item-section>{{ card.label }}</q-item-section>
                                    <q-item-section side>
                                        <div class="row items-center no-wrap">
                                            <BaseButton
                                                variant="icon"
                                                size="sm"
                                                :icon="ICONS.arrow_upward"
                                                :disable="!canMove(card.id, 'up')"
                                                @click="moveCard(card.id, 'up')"
                                            >
                                                <q-tooltip>Move up</q-tooltip>
                                            </BaseButton>
                                            <BaseButton
                                                variant="icon"
                                                size="sm"
                                                :icon="ICONS.arrow_downward"
                                                :disable="!canMove(card.id, 'down')"
                                                @click="moveCard(card.id, 'down')"
                                            >
                                                <q-tooltip>Move down</q-tooltip>
                                            </BaseButton>
                                            <q-toggle
                                                :model-value="isCardVisible(card.id)"
                                                @update:model-value="toggleCard(card.id)"
                                            />
                                        </div>
                                    </q-item-section>
                                </q-item>
                            </template>
                        </q-list>
                    </q-menu>
                </BaseButton>
            </div>
        </section>

        <!-- Phase 5 quick actions (decision §9): the home screen *does*, not just
             routes. Lightweight inline dialogs — Add item opens the shared
             CreateStockItemDialog; Add to list pops the global QuickAddSheet;
             Log price (FU-300) pops the global LogPriceSheet which picks a
             stock item first, then hands off to the shared PriceEntry form.
             Log price is money-gated to match the row-level "Log a price"
             button (ADR-005). -->
        <div class="dora-quick-actions">
            <BaseButton
                variant="secondary"
                :icon="ICONS.add"
                label="Add item"
                @click="showCreateStockItem = true"
            />
            <BaseButton
                variant="secondary"
                :icon="ICONS.shopping_cart"
                label="Add to list"
                @click="openQuickAdd()"
            />
            <BaseButton
                v-if="moneyEnabled"
                variant="secondary"
                :icon="ICONS.cash_plus"
                label="Log price"
                @click="openLogPrice()"
            />
        </div>

        <!-- FU-840 / §3.13 — the banner carries its own Retry. Its copy used to
             say "Try refreshing", which pointed at the manual refresh button that
             D3 deliberately removed; and when the summary fails the whole grid
             renders nothing (every card reads off `summary`), so this banner was
             the only thing on the page with no way forward. -->
        <q-banner v-if="loadError" class="dora-bg-negative-soft text-negative q-mb-md" dense rounded>
            {{ loadError }}
            <template #action>
                <BaseButton
                    variant="ghost"
                    dense
                    :icon="ICONS.refresh"
                    label="Try again"
                    :loading="loading"
                    @click="loadAll"
                />
            </template>
        </q-banner>

        <!-- D1: the 24h skip-reminder and the day's welcome share one warm
             "Dora says" treatment. The skip-reminder (F1) owns the
             not-yet-finished-onboarding window — its Continue/Hide buttons are
             now inline (D1b), not on their own row. Once that window lapses or
             is hidden, the rotating welcome (D1c/d/e) takes over; it replaces
             the old bottom-right "Dora says" bubble but keeps its look. -->
        <transition name="fade">
            <aside
                v-if="showSkipReminder"
                class="dora-welcome dora-welcome--warn q-mb-md"
                role="note"
                aria-label="Finish setup"
            >
                <q-avatar size="40px" square class="dora-welcome-mascot">
                    <img src="../assets/logo-mascot.png" alt="" />
                </q-avatar>
                <div class="dora-welcome-body">
                    <div class="dora-welcome-line">
                        <strong>Welcome —</strong> you skipped the setup wizard.
                        Finish in two minutes whenever you're ready.
                    </div>
                    <div class="dora-welcome-actions">
                        <BaseButton
                            variant="ghost"
                            dense
                            :icon="ICONS.east"
                            label="Continue"
                            :loading="continuingOnboarding"
                            @click="onContinueOnboarding"
                        />
                        <BaseButton
                            variant="ghost"
                            dense
                            :icon="ICONS.close"
                            label="Hide"
                            @click="dismissSkipReminder"
                        />
                    </div>
                </div>
            </aside>
        </transition>

        <transition name="fade">
            <aside
                v-if="showWelcome"
                class="dora-welcome q-mb-md"
                role="note"
                aria-label="A note from Dora"
            >
                <q-avatar size="40px" square class="dora-welcome-mascot">
                    <img src="../assets/logo-mascot.png" alt="" />
                </q-avatar>
                <div class="dora-welcome-body">
                    <div class="dora-welcome-line">
                        <strong>Dora says</strong> · {{ welcomeMessage }}
                    </div>
                    <div class="dora-welcome-hint">{{ welcomeHint }}</div>
                </div>
                <BaseButton
                    variant="icon"
                    size="sm"
                    :icon="ICONS.close"
                    aria-label="Hide Dora's note for today"
                    @click="dismissWelcome"
                >
                    <q-tooltip>Hide for today</q-tooltip>
                </BaseButton>
            </aside>
        </transition>

        <FadeTransition mode="out-in">
        <!-- D-007 (DR-8): a content-shaped skeleton of the card grid, not a
             lone centred spinner — the dashboard settles into its own shape
             rather than flashing empty then popping. Reuses the real
             DashboardCard shell so the placeholders match the loaded cards by
             construction. -->
        <div
            v-if="loading && !summary"
            key="dash-loading"
            class="row q-col-gutter-lg dora-cards"
            aria-hidden="true"
        >
            <!-- Skeleton placeholders take the same half-width shape the real
                 cards do, so the loading grid settles into the loaded one
                 rather than reflowing (D-007). Four is an even count, so it
                 needs no parity fix of its own. -->
            <div v-for="n in 4" :key="n" :class="CARD_COL_HALF">
                <DashboardCard>
                    <template #title>
                        <AppSkeleton type="line" width="45%" />
                    </template>
                    <AppSkeleton type="line" width="92%" class="dash-skel-line" />
                    <AppSkeleton type="line" width="78%" class="dash-skel-line" />
                    <AppSkeleton type="line" width="64%" class="dash-skel-line" />
                </DashboardCard>
            </div>
        </div>

        <!-- `q-col-gutter-lg` is 24px = `--space-6`, which is what B4 specifies
             between sibling cards; this grid was on `-md` (16px). -->
        <div v-else-if="summary" key="dash-content" class="row q-col-gutter-lg dora-cards">
            <!-- Zone band headers (Phase 2). Full-width flex items whose CSS
                 `order` places each just before its zone's cards, forcing a
                 line break so the cards below read as a labelled band. Shown
                 only when the zone has at least one visible card. -->
            <div
                v-for="z in ZONES"
                v-show="zoneHasVisibleCards(z.id)"
                :key="z.id"
                class="col-12 dora-zone-label"
                :style="{ order: zoneHeaderOrder(z.id) }"
            >
                {{ z.label }}
            </div>

            <!-- ───── Needs your attention (P12) ─────────────────────────── -->
            <!-- Calm empty-state: renders whenever the card is visible —
                 an "all clear" state instead of vanishing, so the dashboard
                 looks best (not emptiest) when nothing's wrong. This is a
                 different pattern from R-029 (hide-when-off) — a happy zero
                 isn't an off-state, so the card stays. -->
            <div
                v-if="cardRendered('attention')"
                :class="cardCol('attention')"
                :style="{ order: cardCssOrder('attention') }"
            >
                <AttentionCard
                    :alerts="alerts"
                    :failed="slotFailed('alerts')"
                    @retry="loadAlerts"
                    @action="applyAlertAction"
                />
            </div>

            <!-- ───── Draft my shop (FU-351 / P6-10) ──────────────────────── -->
            <!-- One-click "Draft my shop" entry point on top of the existing
                 /auto-generate engine (meal plan + low/out + flagged as
                 sensible defaults). Lands the user in a fresh DRAFT list
                 ready to edit before they head out. Component owns its own
                 fetch + navigate + toast branches. -->
            <div
                v-if="cardRendered('draft_shop')"
                :class="cardCol('draft_shop')"
                :style="{ order: cardCssOrder('draft_shop') }"
            >
                <DraftShopCard />
            </div>

            <!-- ───── Primary shopping list (P12) ─────────────────────────── -->
            <div
                v-if="cardRendered('primary_list')"
                :class="cardCol('primary_list')"
                :style="{ order: cardCssOrder('primary_list') }"
            >
                <PrimaryListCard
                    :list="quickAddTargetSummary"
                    :stats="primaryListStats"
                    :other-active-count="otherActiveListCount"
                    :failed="slotFailed('primary_list')"
                    @retry="loadPrimaryListDetail"
                />
            </div>

            <!-- ───── Dora suggests (P2-04) ───────────────────────────────── -->
            <!-- Calm empty state instead of vanishing when Dora has
                 nothing to suggest — separate pattern from R-029. -->
            <div
                v-if="cardRendered('suggestions')"
                :class="cardCol('suggestions')"
                :style="{ order: cardCssOrder('suggestions') }"
            >
                <SuggestionsCard
                    :suggestions="suggestionStore.suggestions"
                    :count="suggestionStore.count"
                    @accept="acceptSuggestion"
                    @dismiss="dismissSuggestion"
                />
            </div>

            <!-- C-waste W5 — the standalone "Use soon" card was removed
                 (PROPOSAL_WASTE_MINIMISATION §4.5). Near-expiry items
                 surface via the existing "Needs your attention" card's
                 `expired` / `expiring_soon` alert kinds. -->

            <!-- ───── Next to cook (FU-298: meal-plan-driven, ready/missing) ─ -->
            <div
                v-if="cardRendered('cookable')"
                :class="cardCol('cookable')"
                :style="{ order: cardCssOrder('cookable') }"
            >
                <NextToCookCard
                    :entries="nextToCook"
                    @cook="cookPlannedMeal"
                />
            </div>

            <!-- ───── Kitchen health (P8-08 Dora Score) ─────────────────── -->
            <div
                v-if="cardRendered('dora_score')"
                :class="cardCol('dora_score')"
                :style="{ order: cardCssOrder('dora_score') }"
            >
                <DoraScoreCard />
            </div>

            <!-- ───── FU-317 — reconcile past meals ─────────────────────
                 Chip-shaped, not a full card. Hide-when-empty is done
                 inside the component itself; the wrapper still renders
                 an empty div when isCardVisible is true, so we double-
                 guard on the composable's `total` for the wrapper too. -->
            <div
                v-if="cardRendered('reconcile_pending')"
                :class="cardCol('reconcile_pending')"
                :style="{ order: cardCssOrder('reconcile_pending') }"
            >
                <ReconcilePastMealsChip />
            </div>

            <!-- ───── Stock card (with donut) ────────────────────────────── -->
            <div
                v-if="cardRendered('stock_items')"
                :class="cardCol('stock_items')"
                :style="{ order: cardCssOrder('stock_items') }"
            >
                <PantryDonutCard
                    :total="summary.stock_items.total"
                    :in-stock="stockInStockCount"
                    :low="summary.stock_items.low_stock"
                    :out="summary.stock_items.out_of_stock"
                    :segments="stockSegments"
                    :low-link="stockLowLink"
                    :out-link="stockOutLink"
                    @open="goTo"
                />
            </div>

            <!-- ───── What's coming (FU-818: the week strip + the fortnight
                 calendar, merged) ────────────────────────────────────────────
                 These were two cards rendering the same days from two DIFFERENT
                 endpoints — the strip from `/dashboard/summary`'s 7-day
                 `upcoming_entries`, the grid from `/alerts/upcoming`'s 14 — so
                 the overlapping week could disagree on one screen with no way
                 to tell which was right (R-003). Now one card, one source, with
                 a 7/14-day range toggle; 7 is the default because a week is the
                 planning unit.
                 D-012 also applies: a 7-day pip strip and a 14-day dot grid are
                 the same widget at two zoom levels, so they were never two
                 cards' worth of information.
                 The old "Next up" callout is gone with them — it restated the
                 hero line verbatim (§3.2), which is where that sentence lives.
                 Fed by `/alerts/upcoming`, the strip also gains expiry and
                 shopping dots, which it never had. -->
            <div
                v-if="cardRendered('meal_plan')"
                :class="cardCol('meal_plan')"
                :style="{ order: cardCssOrder('meal_plan') }"
            >
                <WhatsComingCard
                    :cells="calendarCells"
                    :span="calendarSpan"
                    :spans="CALENDAR_SPANS"
                    :span-label="calendarSpanLabel"
                    :selected="selectedCalDate"
                    :selected-day="selectedCalDay"
                    :failed="slotFailed('upcoming')"
                    @update:span="calendarSpan = $event"
                    @select="selectCalDate"
                    @retry="loadUpcoming"
                />
            </div>

            <!-- ───── Restock radar (Phase 5) ─────────────────────────────── -->
            <div
                v-if="cardRendered('restock')"
                :class="cardCol('restock')"
                :style="{ order: cardCssOrder('restock') }"
            >
                <RestockRadarCard
                    :items="restockItems"
                    :failed="slotFailed('restock')"
                    @retry="loadKeepsRunningOut"
                    @add="addRestockToList"
                />
            </div>

            <!-- ───── Savings captured (Phase 4 — Money zone flagship) ────── -->
            <div
                v-if="cardRendered('savings')"
                :class="cardCol('savings')"
                :style="{ order: cardCssOrder('savings') }"
            >
                <MoneyCard
                    :budget="budgetStatus"
                    :savings="savings"
                    :swaps="swapSummary"
                    :range="savingsRange"
                    :ranges="SAVINGS_RANGES"
                    :range-label="savingsRangeLabel"
                    :budget-failed="slotFailed('budget')"
                    :savings-failed="slotFailed('savings')"
                    @update:range="savingsRange = $event"
                    @retry-budget="loadBudget"
                    @retry-savings="loadSavings"
                    @open-swaps="router.push('/meal-plans')"
                />
            </div>

            <!-- ───── Spend by store (Phase 4 — opt-in) ───────────────────── -->
            <div
                v-if="cardRendered('spend_trend')"
                :class="cardCol('spend_trend')"
                :style="{ order: cardCssOrder('spend_trend') }"
            >
                <SpendByStoreCard
                    :top="topSpendStores"
                    :total="spendTotal"
                    :store-count="spendStoreCount"
                    :failed="slotFailed('spend')"
                    @retry="loadSpendByStore"
                />
            </div>

            <!-- ───── Pantry value (Phase 4 — opt-in) ─────────────────────── -->
            <div
                v-if="cardRendered('pantry_value')"
                :class="cardCol('pantry_value')"
                :style="{ order: cardCssOrder('pantry_value') }"
            >
                <PantryValueCard
                    :latest="pantryValueLatest"
                    :delta="pantryValueDelta"
                    :estimate-note="pantryValue?.estimate_note"
                    :failed="slotFailed('pantry_value')"
                    @retry="loadPantryValue"
                />
            </div>

            <!-- ───── Price drops (Phase 4 — Money zone, product-gated) ──── -->
            <div
                v-if="cardRendered('price_drops')"
                :class="cardCol('price_drops')"
                :style="{ order: cardCssOrder('price_drops') }"
            >
                <PriceDropsCard
                    :rows="priceDropRows"
                    :failed="slotFailed('price_drops')"
                    @retry="loadPriceDrops"
                />
            </div>

            <!-- §2.6: the `recipes`, `meals`, `shopping_lists` and `products`
                 counter cards were cut — raw totals answer no question the user
                 has. `shopping_lists` merged into the primary-list card above
                 (the "+N other lists" footer); cookable-tonight + the week-ahead
                 cover the recipe questions; product totals → the Money zone
                 widgets (Phase 4). -->

            <div v-if="visibleCardCount === 0" class="col-12">
                <q-banner class="dora-bg-sunken">
                    All cards are hidden. Use the <q-icon :name="ICONS.tune" /> Cards menu above to show some.
                </q-banner>
            </div>
        </div>
        </FadeTransition>

        <!-- Phase 5 "Add item" quick action — the shared create dialog; refreshes
             the summary/restock on success so the new item shows immediately. -->
        <CreateStockItemDialog
            v-model="showCreateStockItem"
            @created="onStockItemCreated"
        />
    </q-page>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    // FU-820 — `formatRelativeDay` and the local-ISO parse now come from the
    // shared date authority (D-006/R-003). The page's own copies parsed
    // `YYYY-MM-DD` with `new Date(iso)`, i.e. as UTC midnight, so every relative
    // day was off by one west of Greenwich.
    import { formatRelativeDay } from 'src/composables/useDateFormat';
    import { parseLocalIso } from 'src/helpers/weekDates';
    import FadeTransition from 'src/components/transitions/FadeTransition.vue';
    import AppSkeleton from 'src/components/AppSkeleton.vue';
    import BaseButton from 'src/components/BaseButton.vue';
    import DashboardCard from 'src/components/dashboard/DashboardCard.vue';
    // FU-829 chunk 5 — cards extracted out of this page. Data stays owned here
    // (the parallel load, the per-slot error tracking and the post-action
    // refresh are page concerns); each card takes what it renders and emits what
    // it wants doing.
    import AttentionCard from 'src/components/dashboard/AttentionCard.vue';
    import MoneyCard from 'src/components/dashboard/MoneyCard.vue';
    import PriceDropsCard from 'src/components/dashboard/PriceDropsCard.vue';
    import SpendByStoreCard from 'src/components/dashboard/SpendByStoreCard.vue';
    import PantryValueCard from 'src/components/dashboard/PantryValueCard.vue';
    import RestockRadarCard from 'src/components/dashboard/RestockRadarCard.vue';
    import PantryDonutCard, {
        type DonutSegment,
    } from 'src/components/dashboard/PantryDonutCard.vue';
    import NextToCookCard from 'src/components/dashboard/NextToCookCard.vue';
    import SuggestionsCard from 'src/components/dashboard/SuggestionsCard.vue';
    import PrimaryListCard from 'src/components/dashboard/PrimaryListCard.vue';
    import WhatsComingCard, {
        type CalendarCell,
        type CalendarSpan,
    } from 'src/components/dashboard/WhatsComingCard.vue';
    import DoraScoreCard from 'src/components/dashboard/DoraScoreCard.vue';
    import ReconcilePastMealsChip from 'src/components/dashboard/ReconcilePastMealsChip.vue';
    import DraftShopCard from 'src/components/dashboard/DraftShopCard.vue';
    import { storeToRefs } from 'pinia';
    // The alert *presentation* helpers (icon / colour / kind label / deep link)
    // moved into `AttentionCard.vue` with the card. What the page still needs is
    // the Alert shape it fetches, the action type it forwards, and the upcoming
    // types the merged calendar reads.
    import {
        type Alert,
        type AlertAction,
        type Upcoming,
        type UpcomingDay,
    } from 'src/models/alert';
    import type { DashboardSummary, UpcomingMealPlanEntry } from 'src/models/dashboard';
    import { epochDay, pickWelcome, pickHint } from 'src/helpers/dashboardMessages';
    import type { ShoppingListDetail } from 'src/models/shoppingList';
    import AlertApiService from 'src/services/api/alertApiService';
    import { useAlertActions } from 'src/composables/useAlertActions';
    import BudgetApiService, {
        type BudgetStatus,
    } from 'src/services/api/budgetApiService';
    import MealPlanApiService from 'src/services/api/mealPlanApiService';
    import { useSuggestionStore } from 'src/stores/suggestionStore';
    import type { DoraSuggestion } from 'src/services/api/suggestionsApiService';
    import DashboardApiService from 'src/services/api/dashboardApiService';
    import OnboardingApiService from 'src/services/api/onboardingApiService';
    import ShoppingListApiService from 'src/services/api/shoppingListApiService';
    import ReportsApiService, {
        type ReportRange,
        type SavingsCapturedResponse,
        type StoreSpendResponse,
        type StockValueResponse,
        type KeepsRunningOutResponse,
        type PriceDropsResponse,
    } from 'src/services/api/reportsApiService';
    import CreateStockItemDialog from 'src/components/stock/CreateStockItemDialog.vue';
    import { useAuthStore } from 'src/stores/authStore';
    import { useShoppingListStore } from 'src/stores/shoppingListStore';
    import { useStockLevelStore } from 'src/stores/stockLevelStore';
    import {
        LOW_STOCK_SEQUENCE,
        OUT_OF_STOCK_SEQUENCE,
        findLevelBySequence,
    } from 'src/helpers/stockStatus';
    import { useMoneyEnabled } from 'src/composables/useMoneyEnabled';
    import { useFeatureFlags } from 'src/composables/useFeatureFlags';
    import { useReconcileQueue } from 'src/composables/useReconcileQueue';
    import { useStockItemActions } from 'src/composables/useStockItemActions';
    import { useQuickAdd } from 'src/composables/useQuickAdd';
    import { useLogPrice } from 'src/composables/useLogPrice';
    import { useDragDropList } from 'src/composables/useDragDropList';
    import { computed, onMounted, ref, watch } from 'vue';
    import { useQuasar } from 'quasar';
    import { useRouter } from 'vue-router';
    // FU-824 — reactive token reads for the SVG donut (see `stockSegments`).
    import { paletteToken } from 'src/composables/useThemePalette';
    // FU-631 #3 — column classes that never leave a card beside dead air.
    import { CARD_COL_HALF, zoneColClasses } from 'src/helpers/dashboardGrid';
    // FU-830 — the card registry, extracted so its default-visible count (a
    // decision §2.2 owns) can be held by a test rather than by nothing.
    import {
        CARD_DEFS,
        ZONES,
        type CardId,
        type ZoneId,
    } from 'src/helpers/dashboardCards';

    // FU-821 — every money render goes through `formatMoney`, including the
    // tweened <AnimatedNumber> ones (via its `format` prop). The old
    // `currencySymbol` prefix is gone: it returned the symbol only, so it lost
    // `formatMoney`'s decimals, grouping and locale-correct symbol *placement*
    // (D-006 — one formatting authority, not a symbol plus a guess). Those
    // renders now live in the extracted cards, which is why this page no longer
    // imports the formatter at all.

    // Card registry (ids, zones, gates, default visibility) + the zone list
    // now live in `helpers/dashboardCards.ts` — extracted in FU-830 so the
    // default-visible count, which is a decision §2.2 owns, can be asserted by
    // a test instead of drifting unnoticed. Read that file before adding a card.

    const authStore = useAuthStore();
    const router = useRouter();
    const $q = useQuasar();
    const { currentUser } = storeToRefs(authStore);

    // Feature gates for the Money/Products cards (Phase 4). `moneyEnabled`
    // layers install + per-user money opt-in (ADR-005); `productsEnabled` is the
    // product data-presence flag (§2.4). Read by `cardAvailable`.
    const { moneyEnabled } = useMoneyEnabled();
    const { products: productsEnabled } = useFeatureFlags();
    // FU-317 Chunk 5 — reconcile queue count (drives the dashboard chip's
    // visibility + the meal-plans header nudge). Server-owned total.
    const { total: reconcileTotal } = useReconcileQueue();
    // Phase 5 — quick actions reuse the shared cross-feature actions so add-to-
    // list / create behave identically to the rest of the app (R-011).
    const { addToList } = useStockItemActions();
    const { openQuickAdd } = useQuickAdd();
    const { openLogPrice } = useLogPrice();

    const dashboardApiService = new DashboardApiService();
    const alertApi = new AlertApiService();
    const { applyAction } = useAlertActions();
    const budgetApi = new BudgetApiService();
    const reportsApi = new ReportsApiService();
    // suggestion store shared with the Dora launcher badge and
    // the chat panel so dismiss/snooze here propagates everywhere.
    const suggestionStore = useSuggestionStore();
    const shoppingListApi = new ShoppingListApiService();

    const shoppingListStore = useShoppingListStore();
    // donut segments deep-link to /stock?level_id=<id>. The stock
    // overview already reads `level_id` from the query; we just need the two
    // level ids (low / out) that match the canonical status sequences.
    const stockLevelStore = useStockLevelStore();
    const { stockLevels } = storeToRefs(stockLevelStore);

    const summary = ref<DashboardSummary | null>(null);
    const loading = ref(false);
    const loadError = ref<string | null>(null);

    // ── "Dora says" welcome band, dismissible for the day (FU-825) ───────
    // The button's tooltip says "Hide for today", and it used to set a plain
    // `ref(false)` that was recreated on every mount — so the band came back on
    // the next navigation to the dashboard. Persist the epoch-day it was
    // dismissed on, keyed off the SAME `epochDay` the message rotation uses
    // (R-003), so "today" means one thing: the band stays hidden until the
    // message itself changes at local midnight.
    const WELCOME_DISMISSED_KEY = 'dora.dashboard.welcome_dismissed_day';
    const welcomeDismissedDay = ref<number | null>(readWelcomeDismissedDay());
    function readWelcomeDismissedDay(): number | null {
        try {
            const raw = localStorage.getItem(WELCOME_DISMISSED_KEY);
            if (!raw) return null;
            const day = Number(raw);
            return Number.isFinite(day) ? day : null;
        } catch {
            // Private mode / storage disabled — the band just isn't dismissible
            // across navigations, which is the old behaviour and no worse.
            return null;
        }
    }
    function dismissWelcome() {
        const today = epochDay(new Date());
        welcomeDismissedDay.value = today;
        try {
            localStorage.setItem(WELCOME_DISMISSED_KEY, String(today));
        } catch {
            // Ignore — the in-memory ref still hides it for this visit.
        }
    }

    // ── 24h "you skipped the wizard" reminder (F1) ───────────────────
    // The wizard writes `dora.onboarding.skipped_at` on Skip-everything;
    // we surface a soft banner on the dashboard for 24 hours after that
    // moment. Dismissing it sets a session-scoped flag so the banner
    // stays hidden for this tab.
    const SKIP_REMINDER_WINDOW_MS = 24 * 60 * 60 * 1000;
    const skipReminderDismissed = ref(false);
    const showSkipReminder = computed(() => {
        if (skipReminderDismissed.value) return false;
        try {
            const raw = localStorage.getItem('dora.onboarding.skipped_at');
            if (!raw) return false;
            const stamped = new Date(raw).getTime();
            if (!Number.isFinite(stamped)) return false;
            return Date.now() - stamped < SKIP_REMINDER_WINDOW_MS;
        } catch {
            return false;
        }
    });
    function dismissSkipReminder() {
        skipReminderDismissed.value = true;
    }
    // Continue → re-open the wizard. The Skip-everything path stamps
    // `onboarding_completed_at` on the backend so subsequent visits don't
    // get bounced to /welcome. To re-enter we need that timestamp cleared
    // (POST /onboarding/restart) AND the cached auth state refreshed,
    // otherwise the router guard sees the stale non-null value and
    // bounces straight back here. Same shape as the AccountSettings
    // "Restart onboarding" action.
    const onboardingApi = new OnboardingApiService();
    const continuingOnboarding = ref(false);
    async function onContinueOnboarding() {
        if (continuingOnboarding.value) return;
        continuingOnboarding.value = true;
        try {
            await onboardingApi.restartAsync();
            await authStore.refreshAsync();
            try {
                localStorage.removeItem('dora.onboarding.skipped_at');
            } catch {
                // Ignore — banner hides on the next render anyway once
                // the guard sends us to /welcome.
            }
            void router.push('/welcome');
        } finally {
            continuingOnboarding.value = false;
        }
    }

    // ── Per-slot failure tracking (FU-840) ──────────────────────────────
    // Every loader below used to `catch { thing.value = null }`, so the card
    // then rendered its **empty** state. A 500 on savings told a household that
    // had shopped for months "finish a shop and I'll tally what you kept"; a
    // failed alerts fetch said "all clear — nothing needs your attention".
    // Failure was indistinguishable from absence, in the direction that
    // reassures — Honesty inverted, eleven times (`DASHBOARD_PAGE_REVIEW.md`
    // §4.7 / finding 10).
    //
    // So each slot now records whether it failed, and its card renders
    // <CardLoadError> instead of "nothing here yet". Kept as one id-keyed set
    // rather than a per-slot `error` ref beside each data ref: the cards need
    // "did *this* slot fail" and the banner needs "did *anything* fail", and one
    // structure answers both without eleven more refs to keep in step (R-003).
    type SlotId =
        | 'alerts'
        | 'primary_list'
        | 'budget'
        | 'swaps'
        | 'savings'
        | 'spend'
        | 'pantry_value'
        | 'price_drops'
        | 'restock'
        | 'upcoming';

    const slotErrors = ref<Set<SlotId>>(new Set());
    function slotFailed(id: SlotId): boolean {
        return slotErrors.value.has(id);
    }
    /** Run a slot's fetch, recording success or failure against its id.
     *
     *  Still never throws — one bad slot must not take the page down, which is
     *  what the original blanket catches were protecting. The difference is that
     *  the failure is now *visible* instead of being laundered into an empty
     *  state. A later retry that succeeds clears the flag, so the card recovers
     *  without a reload. */
    async function loadSlot(id: SlotId, run: () => Promise<void>): Promise<void> {
        try {
            await run();
            if (slotErrors.value.has(id)) {
                const next = new Set(slotErrors.value);
                next.delete(id);
                slotErrors.value = next;
            }
        } catch (err) {
            // Logged, not swallowed: the console is how a self-hosting owner
            // finds out *which* endpoint is unhappy.
            console.warn(`dashboard slot "${id}" failed to load`, err);
            const next = new Set(slotErrors.value);
            next.add(id);
            slotErrors.value = next;
        }
    }

    // Independent slot loaders. Each card surfaces a small chunk of data
    // beyond what the bulk dashboard summary endpoint returns. They live
    // in parallel and never block each other — a slow alerts response
    // shouldn't gate the rest of the dashboard.
    const alerts = ref<Alert[]>([]);
    const primaryListDetail = ref<ShoppingListDetail | null>(null);
    // Feeds the budget half of the merged Money card. Always loads (so the
    // passive "spent this period" figure works for users who haven't set a
    // target), and the block is `v-if`'d out when the loader errors so a failed
    // slot never blocks the rest of the card — the savings half still renders.
    const budgetStatus = ref<BudgetStatus | null>(null);
    // FU-451 — budget-defense swap summary for the current week (bullet + deep
    // link on the budget card). Null when money's off, no current-week plan, or
    // the week isn't projected over budget.
    const mealPlanApi = new MealPlanApiService();
    const swapSummary = ref<{ saved: number; count: number } | null>(null);
    // Phase 4 — Money zone widgets, each backed by an existing reports endpoint.
    // Only loaded when money is enabled (the cards are gated on it anyway). The
    // savings widget carries its own range toggle; spend/pantry use a sensible
    // default window.
    const savings = ref<SavingsCapturedResponse | null>(null);
    const savingsRange = ref<ReportRange>('30d');
    const spendByStore = ref<StoreSpendResponse | null>(null);
    const pantryValue = ref<StockValueResponse | null>(null);
    const priceDrops = ref<PriceDropsResponse | null>(null);
    // Phase 5 — restock radar (items the user keeps running out of) + the
    // "Add item" quick-action dialog state.
    const keepsRunningOut = ref<KeepsRunningOutResponse | null>(null);
    const showCreateStockItem = ref(false);
    // Phase 6 — the fortnight calendar's server-aggregated dated events + the
    // currently-expanded day.
    const upcoming = ref<Upcoming | null>(null);
    const selectedCalDate = ref<string | null>(null);

    // DR-4 (FU-578 #21): present the username capitalised so the greeting reads
    // "Good afternoon, Dora" not the raw lowercase handle "dora".
    const firstName = computed(() => {
        const name = currentUser.value?.username ?? '';
        return name ? name.charAt(0).toUpperCase() + name.slice(1) : '';
    });

    const greeting = computed(() => {
        const h = new Date().getHours();
        if (h < 5) return 'Up late';
        if (h < 12) return 'Good morning';
        if (h < 17) return 'Good afternoon';
        return 'Good evening';
    });

    // ── Dashboard layout prefs (server-persisted, §2.1) ──────────────────
    // Card order + hidden set live on the user (`dashboard_layout` JSON) so the
    // layout survives a cache clear and follows the user across devices. We
    // render with CSS `order` rather than moving markup — each card keeps its
    // template position and flexbox sorts them, with full-width zone headers
    // forcing the visual bands (see `cardCssOrder` / the `.dora-zone-label`s).
    type DashLayout = { order: CardId[]; hidden: CardId[] };

    const KNOWN_CARD_IDS = new Set<CardId>(CARD_DEFS.map((c) => c.id));
    const ZONE_OF = new Map<CardId, ZoneId>(CARD_DEFS.map((c) => [c.id, c.zone]));

    function defaultOrder(): CardId[] {
        return CARD_DEFS.map((c) => c.id);
    }
    function baseHiddenSet(): Set<CardId> {
        return new Set(CARD_DEFS.filter((c) => c.defaultHidden).map((c) => c.id));
    }
    function parseLayout(raw: string | null): DashLayout {
        if (!raw) return { order: defaultOrder(), hidden: [...baseHiddenSet()] };
        try {
            // Untrusted JSON — treat the arrays as raw strings and narrow each
            // entry to a known CardId at runtime.
            const parsed = JSON.parse(raw) as { order?: string[]; hidden?: string[] };
            const order = (parsed.order ?? []).filter(
                (id): id is CardId => KNOWN_CARD_IDS.has(id as CardId)
            );
            // Append any card missing from the stored order (e.g. a card shipped
            // since the user last saved) at its CARD_DEFS position.
            for (const def of CARD_DEFS) if (!order.includes(def.id)) order.push(def.id);
            const hidden = new Set<CardId>(
                (parsed.hidden ?? []).filter(
                    (id): id is CardId => KNOWN_CARD_IDS.has(id as CardId)
                )
            );
            // A card the user has never seen inherits its default visibility, so
            // a new opt-in-by-default card starts hidden even for existing users.
            const seen = new Set<string>([...(parsed.order ?? []), ...(parsed.hidden ?? [])]);
            for (const def of CARD_DEFS) {
                if (def.defaultHidden && !seen.has(def.id)) hidden.add(def.id);
            }
            return { order, hidden: [...hidden] };
        } catch {
            return { order: defaultOrder(), hidden: [...baseHiddenSet()] };
        }
    }

    const cardOrder = ref<CardId[]>(defaultOrder());
    const hiddenCards = ref<Set<CardId>>(baseHiddenSet());

    function applyLayoutFromUser() {
        const parsed = parseLayout(currentUser.value?.dashboard_layout ?? null);
        cardOrder.value = parsed.order;
        hiddenCards.value = new Set(parsed.hidden);
    }
    applyLayoutFromUser();
    // Reload on user switch (or another device's update landing via refresh).
    // Our own saves also replace currentUser, but re-applying is idempotent.
    watch(() => currentUser.value?.user_id, applyLayoutFromUser);

    function persistLayout() {
        const payload: DashLayout = {
            order: cardOrder.value,
            hidden: [...hiddenCards.value],
        };
        // Fire-and-forget — local refs already reflect the change optimistically;
        // a failed save just means it isn't remembered.
        void authStore.updateMeAsync({ dashboard_layout: JSON.stringify(payload) });
    }

    // A card is *available* unless its feature gate is off — gated-off cards
    // vanish from both the dashboard and the Cards menu (§2.4 / ADR-005), so we
    // never offer a dollar widget with money disabled or a product widget to a
    // user with no products.
    const CARD_GATE = new Map(CARD_DEFS.map((c) => [c.id, c.gate]));
    function cardAvailable(id: CardId): boolean {
        const gate = CARD_GATE.get(id);
        if (gate === 'money') return moneyEnabled.value;
        if (gate === 'products') return productsEnabled.value;
        return true;
    }

    function isCardVisible(id: CardId): boolean {
        return KNOWN_CARD_IDS.has(id) && cardAvailable(id) && !hiddenCards.value.has(id);
    }
    function toggleCard(id: CardId) {
        const next = new Set(hiddenCards.value);
        if (next.has(id)) next.delete(id);
        else next.add(id);
        hiddenCards.value = next;
        persistLayout();
    }
    const visibleCardCount = computed(
        () => CARD_DEFS.filter((c) => isCardVisible(c.id)).length
    );

    // ── Does this card actually render? (FU-631 #3) ──────────────────────
    // `isCardVisible` answers "is it registered, gated on, and un-hidden".
    // `reconcile_pending` additionally vanishes on its own *data* — it is
    // hide-when-empty (R-029). This predicate folds that in, and is the ONE
    // thing both the template's `v-if` and the column-width maths below consult:
    // if they disagreed, the grid would pair a card that isn't there and leave
    // the gap it was meant to fill (R-003).
    //
    // The merged Money card (`savings`) needs no data guard — it always has
    // something to say, since the budget block is `v-if`'d inside it and the
    // savings half carries its own empty state.
    function cardRendered(id: CardId): boolean {
        if (!isCardVisible(id)) return false;
        if (id === 'reconcile_pending') return reconcileTotal.value > 0;
        return true;
    }

    // Cards that are full-width by design rather than by parity.
    //
    // Currently none: the fortnight calendar used to be the one entry, and
    // FU-818 merged it into `meal_plan`, which is half-width at both spans — the
    // grid is 7 columns either way, so 14 days is simply two rows of it. Keeping
    // the seam (rather than deleting it) because the *next* wide card should
    // declare itself here instead of hard-coding `col-12` at its call site,
    // which is how the mixed widths that caused the dead regions got in.
    const FULL_WIDTH_CARDS: ReadonlySet<CardId> = new Set<CardId>();

    // Column classes per card, computed per zone so no card is left in a
    // half-width column beside dead air (D-011 / B4) — see
    // `helpers/dashboardGrid` for the measured counts and why the parity is per
    // run of consecutive half-width cards rather than per zone.
    const cardColClasses = computed<Record<string, string>>(() => {
        const out: Record<string, string> = {};
        for (const zone of ZONES) {
            const rendered = cardOrder.value.filter(
                (id) => ZONE_OF.get(id) === zone.id && cardRendered(id),
            );
            Object.assign(out, zoneColClasses(rendered, FULL_WIDTH_CARDS));
        }
        return out;
    });
    function cardCol(id: CardId): string {
        // A card that isn't rendered has no entry; the half default keeps the
        // binding total rather than resolving to `undefined`.
        return cardColClasses.value[id] ?? CARD_COL_HALF;
    }

    // CSS `order` per card: a fixed per-zone base (so a card never visually
    // leaves its zone) plus its index in the user's order array (so reorder
    // within a zone sticks). The base spacing (100) ≫ the card indices (17 and
    // counting), so zones never interleave. Zone headers sit just before their
    // band.
    const ZONE_BASE = 100;
    function orderIndexOf(id: CardId): number {
        const i = cardOrder.value.indexOf(id);
        return i === -1 ? CARD_DEFS.findIndex((c) => c.id === id) : i;
    }
    function cardCssOrder(id: CardId): number {
        const zi = ZONES.findIndex((z) => z.id === ZONE_OF.get(id));
        return zi * ZONE_BASE + orderIndexOf(id);
    }
    function zoneHeaderOrder(zone: ZoneId): number {
        return ZONES.findIndex((z) => z.id === zone) * ZONE_BASE - 1;
    }
    function zoneHasVisibleCards(zone: ZoneId): boolean {
        // `cardRendered`, not `isCardVisible` — otherwise a Money zone whose
        // only visible card is `budget` with an unloaded status, or a Kitchen
        // zone holding just an empty `reconcile_pending`, draws its band header
        // above nothing.
        return CARD_DEFS.some((c) => c.zone === zone && cardRendered(c.id));
    }

    // Reorder within a zone — the tap alternative to drag (C13: drag is the
    // power-user extra, the tap control is always present + works on mobile).
    function zonePeers(id: CardId): CardId[] {
        const zone = ZONE_OF.get(id);
        return cardOrder.value.filter((c) => ZONE_OF.get(c) === zone);
    }
    function canMove(id: CardId, dir: 'up' | 'down'): boolean {
        const peers = zonePeers(id);
        const i = peers.indexOf(id);
        return dir === 'up' ? i > 0 : i < peers.length - 1;
    }
    function moveCard(id: CardId, dir: 'up' | 'down') {
        const peers = zonePeers(id);
        const i = peers.indexOf(id);
        const j = dir === 'up' ? i - 1 : i + 1;
        if (j < 0 || j >= peers.length) return;
        const other = peers[j]!;
        const next = [...cardOrder.value];
        const oi = next.indexOf(id);
        const oj = next.indexOf(other);
        [next[oi], next[oj]] = [next[oj]!, next[oi]!];
        cardOrder.value = next;
        persistLayout();
    }

    // drag-handle reorder for the Cards menu. Sits on top of the
    // existing tap up/down: drag is the desktop power-user extra; tap is the
    // mobile/keyboard mandate (C13). Same-zone-only via `canDropOn`.
    // `cardDragEnabled` gates the handle on non-touch — `$q.platform.is.mobile`
    // includes tablets so touch-first surfaces keep the tap path uncluttered.
    const ZONE_LABEL: Record<ZoneId, string> = Object.fromEntries(
        ZONES.map((z) => [z.id, z.label]),
    ) as Record<ZoneId, string>;
    const cardDragEnabled = computed(() => !$q.platform.is.mobile);
    const cardDnd = useDragDropList<CardId>({
        mime: 'application/x-dora-dashboard-card',
        getId: (id) => id,
        canDragStart: () => cardDragEnabled.value,
        canDropOn: (source, target) => ZONE_OF.get(source) === ZONE_OF.get(target),
        onDrop: ({ id: sourceId }, { id: targetId }) => {
            if (sourceId === targetId) return;
            const next = [...cardOrder.value];
            const fromIdx = next.indexOf(sourceId as CardId);
            const toIdx = next.indexOf(targetId as CardId);
            if (fromIdx < 0 || toIdx < 0) return;
            const [moved] = next.splice(fromIdx, 1);
            // Insert at the target's *current* index after removal — drop-on
            // semantics (the dragged row takes the target's slot, the target
            // shifts toward where the dragged row came from).
            next.splice(toIdx, 0, moved!);
            cardOrder.value = next;
            persistLayout();
        },
    });

    // Cards grouped by zone for the toggle menu (display order). Gated-off cards
    // are dropped (so the menu never offers an unavailable card), and zones with
    // nothing left collapse.
    const cardsByZone = computed(() =>
        ZONES.map((z) => ({
            zone: z,
            cards: cardOrder.value
                .filter((id) => ZONE_OF.get(id) === z.id && cardAvailable(id))
                .map((id) => CARD_DEFS.find((c) => c.id === id)!),
        })).filter((g) => g.cards.length > 0)
    );

    // ── Derived data for stock donut ─────────────────────────────────────
    const stockInStockCount = computed(() => {
        if (!summary.value) return 0;
        const s = summary.value.stock_items;
        // "In stock" = anything not low/out. Items with no stock level
        // (shouldn't happen with the seeded levels) fall into this bucket;
        // the alternative is a fourth "unknown" slice for an edge case.
        return Math.max(0, s.total - s.low_stock - s.out_of_stock);
    });

    // pre-computed deep-link targets for each donut bucket. Falls
    // back to the un-filtered `/stock` when the levels aren't loaded yet, so
    // clicks never dead-end.
    const stockLowLink = computed(() => {
        const lvl = findLevelBySequence(stockLevels.value, LOW_STOCK_SEQUENCE);
        return lvl ? `/stock?level_id=${lvl.stock_level_id}` : '/stock';
    });
    const stockOutLink = computed(() => {
        const lvl = findLevelBySequence(stockLevels.value, OUT_OF_STOCK_SEQUENCE);
        return lvl ? `/stock?level_id=${lvl.stock_level_id}` : '/stock';
    });

    // `DonutSegment` is the card's own shape, so it lives with the card and is
    // imported above. The *building* of the segments stays here: it needs the
    // stock-level ids for the deep links and the theme-token reads.
    const stockSegments = computed<DonutSegment[]>(() => {
        if (!summary.value || summary.value.stock_items.total === 0) return [];
        const total = summary.value.stock_items.total;
        const inStock = stockInStockCount.value;
        const low = summary.value.stock_items.low_stock;
        const out = summary.value.stock_items.out_of_stock;
        const pct = (n: number) => (n / total) * 100;

        // The SVG is rotated -90deg in CSS so the first segment starts at the
        // 12-o'clock position. stroke-dashoffset walks clockwise.
        let cursor = 0;
        const segs: DonutSegment[] = [];
        const push = (label: string, count: number, colour: string, link: string | null) => {
            if (count <= 0) return;
            const p = pct(count);
            segs.push({ label, percent: p, offset: cursor, colour, link });
            // Negative offsets walk clockwise around the circle.
            cursor = (cursor - p + 100) % 100;
        };
        // Read the semantic-* tokens off the document so the donut recolours
        // when the user switches theme without a full reload.
        //
        // FU-824: that comment was a lie until now. The read was a bare
        // `getComputedStyle`, which is not reactive, so this computed had no
        // dependency on the theme and the palette was sampled once and frozen —
        // switch light→dark on the dashboard and the donut kept its old colours
        // until the summary refetched. `paletteToken` touches a version ref that
        // `themeService.applyThemeKey` bumps, so the dependency is real now.
        const okColour = paletteToken('--semantic-positive', '#6ba368');
        const warnColour = paletteToken('--semantic-warning', '#e89a45');
        const badColour = paletteToken('--semantic-negative', '#c85a4f');
        // "In stock" has no bucket-filter — it's the residual; clicking the
        // segment does nothing (would need `?level_id != low/out`, which the
        // page doesn't model). Low + out link to their filtered view.
        push('in stock', inStock, okColour, null);
        push('low', low, warnColour, stockLowLink.value);
        push('out', out, badColour, stockOutLink.value);
        return segs;
    });

    // FU-818 — `weekStrip` is gone. It built its own 7 days from
    // `summary.meal_plan.upcoming_entries` while the fortnight calendar built 14
    // from `/alerts/upcoming`, so the overlapping week was answered twice from
    // two queries that could disagree (R-003). The merged card renders both
    // spans from `calendarCells`, i.e. from `/alerts/upcoming` alone — which
    // also gives the week view the expiry and shopping dots it never had.
    //
    // `nextEntry` survives because the hero line reads it (and that sentence is
    // now the *only* place the next meal is stated in prose — the card's old
    // "Next up" callout repeated it verbatim).
    const nextEntry = computed<UpcomingMealPlanEntry | null>(
        () => summary.value?.meal_plan.upcoming_entries[0] ?? null
    );

    // ── Hero "right now" line. Pick the single most useful thing. ───────
    const heroLine = computed(() => {
        if (!summary.value) return 'Loading the pantry…';
        const s = summary.value;
        if (s.stock_items.out_of_stock > 0) {
            return `${s.stock_items.out_of_stock} ${plural(s.stock_items.out_of_stock, 'item is', 'items are')} out of stock.`;
        }
        if (nextEntry.value) {
            const when = formatRelativeDay(nextEntry.value.scheduled_for).toLowerCase();
            return `${capitalise(when)}: ${nextEntry.value.recipe_name} for ${nextEntry.value.servings}.`;
        }
        if (s.stock_items.low_stock > 0) {
            return `${s.stock_items.low_stock} ${plural(s.stock_items.low_stock, 'item is', 'items are')} running low.`;
        }
        if (s.recipes.total === 0) {
            return "Your recipe book's empty — add one when you have a minute.";
        }
        return "Everything's stocked, planned, and quietly humming along.";
    });

    // ── Welcome + hint of the day (D1c/d/e) ──────────────────────────────
    // A day-of-week-flavoured welcome plus a day-agnostic hint, both stable
    // per calendar day (see helpers/dashboardMessages). This replaces the old
    // bottom-right "Dora says" tip bubble — the warm "Dora says" treatment is
    // kept, but it now lives inline near the top of the dashboard and only
    // shows once onboarding is actually complete (the skip-reminder banner
    // owns the not-yet-finished case). Recomputed cheaply on each render; the
    // underlying pick is deterministic so it doesn't flicker.
    const welcomeMessage = computed(() => pickWelcome());
    // FU-823 — the hint pool is filtered by the install's feature gates, so a
    // money-off household is never told to set a grocery budget and a
    // product-less one isn't sold the deals card (feedback L254 / ADR-005).
    const welcomeHint = computed(() =>
        pickHint({ money: moneyEnabled.value, products: productsEnabled.value })
    );
    // Only greet once the user has finished (or skipped past) onboarding —
    // while the skip-reminder is showing, that banner is the message.
    // Dismissal is per-day (FU-825): hidden only while the stored day is still
    // today, so tomorrow's message arrives on its own.
    const showWelcome = computed(
        () =>
            welcomeDismissedDay.value !== epochDay(new Date()) &&
            !showSkipReminder.value
    );

    // ── Helpers ──────────────────────────────────────────────────────────
    function plural(n: number, one: string, many: string): string {
        return n === 1 ? one : many;
    }

    function capitalise(s: string): string {
        return s.length === 0 ? s : s.charAt(0).toUpperCase() + s.slice(1);
    }

    function isoOf(d: Date): string {
        // Local date (not UTC) — matches the meal plan's `scheduled_for`.
        const y = d.getFullYear();
        const m = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        return `${y}-${m}-${day}`;
    }

    function goTo(path: string) {
        void router.push(path);
    }

    /**
     * Owner 2026-09-04 — *"When clicking cook now from a meal slot, auto adjust
     * the servings based on what the meal plan says for that slot."* The
     * planner's chips do this too (`useMealPlanner.cookRecipe`); this card is
     * the other place a planned meal opens cook mode, and opening it at the
     * household headcount when the plan says six is the same surprise.
     *
     * The dashboard's payload carries the entry's own servings but not a
     * batch's total yield, so a linked cook opens at this day's share. Living
     * with that beats teaching the summary endpoint the batch view for one
     * button — the pill is adjustable on the page it lands on.
     */
    function cookPlannedMeal(entry: UpcomingMealPlanEntry) {
        const query = entry.servings > 0 ? `?for=${entry.servings}` : '';
        goTo(`/cookbook/${entry.recipe_id}/cook${query}`);
    }

    // ── Needs your attention ────────────────────────────────────────────
    // The card is `components/dashboard/AttentionCard.vue` now (FU-829); the
    // severity sort, the by-kind grouping and the peek slice moved with it,
    // since they are presentation of the already-fetched list. What stays here
    // is the fetch, the slot-error flag and the action handler — the action
    // refreshes BOTH the alerts and the summary, which is a page-level concern.
    async function loadAlerts() {
        await loadSlot('alerts', async () => {
            const result = await alertApi.getAlertsAsync();
            alerts.value = result.items;
        });
    }

    // Routed through the shared useAlertActions composable (FU-521); the
    // dashboard passes its own refresh because it also reloads the summary/score
    // cards, not just the alert store.
    async function applyAlertAction(alert: Alert, action: AlertAction) {
        await applyAction(alert, action, {
            refresh: async () => {
                await Promise.all([loadAlerts(), loadSummary()]);
            },
        });
    }

    // ── Cookable tonight ────────────────────────────────────────────────
    // Cookability is server-owned (§3.2): recipes carry `cookable`. A recipe
    // with no ingredients is `cookable` server-side, but "cook tonight" should
    // only suggest real recipes, so require at least one ingredient.
    // Favourites bubble up first within the cookable subset so your usuals
    // show up before the long tail.
    // "Next to cook" is meal-plan-driven now (feedback L272):
    // upcoming entries from `summary.meal_plan.upcoming_entries`, deduped by
    // recipe so the same recipe scheduled twice in the week only shows once
    // (earliest slot wins), capped at 3, each tagged with a ready / missing-N
    // badge from the server-derived `missing_count`.
    const nextToCook = computed<UpcomingMealPlanEntry[]>(() => {
        const entries = summary.value?.meal_plan.upcoming_entries ?? [];
        const seen = new Set<string>();
        const picks: UpcomingMealPlanEntry[] = [];
        for (const e of entries) {
            if (seen.has(e.recipe_id)) continue;
            seen.add(e.recipe_id);
            picks.push(e);
            if (picks.length >= 3) break;
        }
        return picks;
    });

    // The when-label and the ready/missing/to-link badge moved into
    // `NextToCookCard.vue` with the card (FU-829) — they are presentation of the
    // entry, and the tri-state badge logic is easier to follow next to the
    // markup that renders it.

    // FU-819/830 — `loadBestDeals` is gone with the card. That leaves
    // `productApiService.getBestDealsAsync` and the `/products/best-deals`
    // endpoint behind it with no caller in the SPA, and the shared
    // `discountPercent` helper with none either. Both logged as [[FU-838]]
    // rather than deleted here: R-057 is explicit that a replaced surface's
    // contracts are an inventory to check, not a casualty list.

    // ── Primary shopping list ────────────────────────────────────────────
    const quickAddTargetListId = computed(() => shoppingListStore.quickAddTargetListId);
    const quickAddTargetSummary = computed(() => shoppingListStore.quickAddTargetSummary);

    // Totals are server-owned (state-ownership Type B) — read them off the
    // detail's `totals` instead of summing `priceOfLine`/`savingsOfLine` here.
    // Shape kept identical so the template bindings are unchanged.
    const primaryListStats = computed(() => {
        const t = primaryListDetail.value?.totals;
        if (!t) return null;
        return {
            remaining: t.remaining_price,
            full: t.total_price,
            savings: t.total_savings,
            unticked: t.unticked_count,
            ticked: t.ticked_count,
            total: t.line_count,
        };
    });

    // Count of *other* active lists, surfaced as a footer link on the primary
    // card (the standalone "Shopping" counter card was merged in here, §2.6).
    // The summary counts active (non-done) lists; the primary is one of them.
    const otherActiveListCount = computed(() => {
        const total = summary.value?.shopping_lists.total ?? 0;
        return quickAddTargetSummary.value ? Math.max(0, total - 1) : total;
    });

    async function loadPrimaryListDetail() {
        const id = quickAddTargetListId.value;
        if (!id) {
            // No primary list set is a real state, not a failure — the card has
            // its own "pick one" empty state for it.
            primaryListDetail.value = null;
            return;
        }
        await loadSlot('primary_list', async () => {
            primaryListDetail.value = await shoppingListApi.getDetailAsync(id);
        });
    }

    // Re-fetch detail when the primary list changes (e.g. set-primary from
    // another tab) so the card stays honest.
    watch(quickAddTargetListId, () => {
        void loadPrimaryListDetail();
    });

    async function loadSummary() {
        loading.value = true;
        loadError.value = null;
        try {
            summary.value = await dashboardApiService.getSummaryAsync();
        } catch (err) {
            // This one is fatal to the grid — every card reads off `summary`, so
            // the banner is the whole page's state. The copy no longer says "try
            // refreshing": D3 deliberately removed the refresh button, so that
            // sentence pointed at a control that doesn't exist. The banner now
            // carries its own Retry (§3.13).
            loadError.value = "I couldn't load your dashboard.";
            console.warn('dashboard summary failed', err);
        } finally {
            loading.value = false;
        }
    }

    async function loadBudget() {
        // budget is money-gated; skip the fetch when money is off.
        if (!moneyEnabled.value) { budgetStatus.value = null; return; }
        await loadSlot('budget', async () => {
            budgetStatus.value = await budgetApi.getStatusAsync();
        });
    }

    async function loadSwapSummary() {
        if (!moneyEnabled.value) { swapSummary.value = null; return; }
        await loadSlot('swaps', async () => {
            const [today, page] = await Promise.all([
                mealPlanApi.getTodayAsync(),
                mealPlanApi.getAllAsync(),
            ]);
            const todayMs = Date.parse(`${today}T00:00:00`);
            const weekMs = 7 * 24 * 60 * 60 * 1000;
            const plan = page.items.find((p) => {
                const startMs = Date.parse(`${p.start_date}T00:00:00`);
                return startMs <= todayMs && todayMs < startMs + weekMs;
            });
            if (!plan) { swapSummary.value = null; return; }
            const s = await mealPlanApi.getSwapSuggestionsAsync(plan.meal_plan_id);
            if (s.projected_over && s.candidates.length > 0) {
                swapSummary.value = {
                    saved: Math.max(0, s.cost_per_week - s.projected_after_applying_all),
                    count: s.candidates.length,
                };
            } else {
                swapSummary.value = null;
            }
        });
    }

    // ── Money zone loaders (Phase 4) ─────────────────────────────────────
    // Guarded on `moneyEnabled` — the cards are gated on it, so there's no point
    // fetching dollar reports when money is off. Each records its own failure
    // through `loadSlot` so the card can say "couldn't load this" rather than
    // "nothing here yet". The reports endpoints already aggregate server-side
    // (state-ownership) — we just render.
    const RANGE_LABEL: Record<ReportRange, string> = {
        '30d': 'last 30 days',
        '90d': 'last 90 days',
        '1y': 'last year',
        '2y': 'last 2 years',
        '5y': 'last 5 years',
        'all': 'all time',
    };
    const savingsRangeLabel = computed(() => RANGE_LABEL[savingsRange.value]);
    // The savings range toggle (Month / Year / All). Now driven by
    // `BaseSegmented` rather than the hand-rolled `.dora-range-chip` buttons it
    // used to be: B2a says one-of-several goes through that component, and the
    // lookalike carried no `aria-pressed`, no focus-visible state and an 11.5px
    // label (R-048, D-003). Same option shape the component takes.
    const SAVINGS_RANGES: { value: ReportRange; label: string }[] = [
        { value: '30d', label: 'Month' },
        { value: '1y', label: 'Year' },
        { value: 'all', label: 'All' },
    ];

    async function loadSavings() {
        if (!moneyEnabled.value) { savings.value = null; return; }
        await loadSlot('savings', async () => {
            savings.value = await reportsApi.getSavingsCapturedAsync(savingsRange.value);
        });
    }
    // Re-fetch when the user flips the savings range toggle.
    watch(savingsRange, () => { void loadSavings(); });

    async function loadSpendByStore() {
        if (!moneyEnabled.value) { spendByStore.value = null; return; }
        await loadSlot('spend', async () => {
            spendByStore.value = await reportsApi.getSpendByStoreAsync('30d');
        });
    }

    async function loadPantryValue() {
        if (!moneyEnabled.value) { pantryValue.value = null; return; }
        await loadSlot('pantry_value', async () => {
            pantryValue.value = await reportsApi.getStockValueAsync('90d');
        });
    }

    // price-drops is product-gated (not money-gated); still cheap to
    // load, hides itself when empty.
    async function loadPriceDrops() {
        if (!productsEnabled.value) { priceDrops.value = null; return; }
        await loadSlot('price_drops', async () => {
            priceDrops.value = await reportsApi.getPriceDropsAsync(5);
        });
    }
    const priceDropRows = computed(() => priceDrops.value?.rows ?? []);

    // ── Restock radar (Phase 5) ──────────────────────────────────────────
    async function loadKeepsRunningOut() {
        await loadSlot('restock', async () => {
            keepsRunningOut.value = await reportsApi.getKeepsRunningOutAsync(5);
        });
    }
    const restockItems = computed(() => keepsRunningOut.value?.rows ?? []);

    // One-tap "Add to list" from a restock row — routes through the shared
    // cross-feature action (handles the no-draft / multiple-draft cases +
    // toast), so it behaves exactly like the cart button elsewhere.
    function addRestockToList(stockItemId: string) {
        void addToList(stockItemId);
    }

    // After creating a stock item via the quick-action dialog, refresh the
    // summary/restock so the new item is reflected.
    function onStockItemCreated() {
        void loadSummary();
        void loadKeepsRunningOut();
    }

    // ── Fortnight calendar (Phase 6 / D7) ────────────────────────────────
    // The server aggregates dated events (C-9.6 /alerts/upcoming); the client
    // only builds the grid + renders per-category dots (R-003 — no client-side
    // joining of three sources). `dates` carries non-empty days only, so we
    // walk the full window and look each date up.
    async function loadUpcoming() {
        await loadSlot('upcoming', async () => {
            upcoming.value = await alertApi.getUpcomingAsync(14);
        });
    }

    // FU-818 — the merged card's range toggle. 7 is the default because a week
    // is the planning unit; 14 is the old "This fortnight" view. Both come from
    // the SAME already-fetched 14 days, so flipping the toggle is a slice, not a
    // refetch. `CalendarSpan` and `CalendarCell` are the card's own types, so
    // they live with the card and are imported above.
    const CALENDAR_SPANS: { label: string; value: CalendarSpan }[] = [
        { label: '7 days', value: 7 },
        { label: '14 days', value: 14 },
    ];
    const calendarSpan = ref<CalendarSpan>(7);
    const calendarSpanLabel = computed(() =>
        calendarSpan.value === 7 ? 'in the next week' : 'in the next fortnight'
    );

    const DOW_LABELS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    const calendarCells = computed<CalendarCell[]>(() => {
        const u = upcoming.value;
        if (!u) return [];
        const byDate = new Map(u.dates.map((d) => [d.date, d]));
        const todayIso = isoOf(new Date());
        // Shared parser (`helpers/weekDates`) — this page used to declare its own
        // correct copy here while `formatRelativeDay` a few hundred lines up used
        // the broken `new Date(iso)` form. One source now (R-003).
        const start = parseLocalIso(u.start);
        if (!start) return [];
        const cells: CalendarCell[] = [];
        // Never render more than the server sent, however the toggle is set.
        const span = Math.min(calendarSpan.value, u.days);
        for (let i = 0; i < span; i++) {
            const d = new Date(start);
            d.setDate(start.getDate() + i);
            const iso = isoOf(d);
            const day = byDate.get(iso);
            const marks = [
                day && day.meals.length > 0 ? 'meals' : null,
                day && day.expiries.length > 0 ? 'expiring items' : null,
                day && day.shopping.length > 0 ? 'shopping' : null,
            ].filter(Boolean);
            cells.push({
                iso,
                dayNum: d.getDate(),
                dow: DOW_LABELS[d.getDay()]!,
                label:
                    `${formatRelativeDay(iso)}` +
                    (marks.length > 0 ? ` — ${marks.join(', ')}` : ' — nothing on'),
                isToday: iso === todayIso,
                hasExpiry: !!day && day.expiries.length > 0,
                hasShopping: !!day && day.shopping.length > 0,
                hasMeal: !!day && day.meals.length > 0,
            });
        }
        return cells;
    });
    const selectedCalDay = computed<UpcomingDay | null>(() =>
        upcoming.value?.dates.find((d) => d.date === selectedCalDate.value) ?? null
    );
    function selectCalDate(iso: string) {
        selectedCalDate.value = selectedCalDate.value === iso ? null : iso;
    }
    // FU-818 — `/alerts/upcoming` used to be lazy-loaded only when the opt-in
    // fortnight card was switched on (R-016). It is now the merged card's only
    // data source and that card is default-on, so it loads with everything else
    // in `loadAll` and the visibility watch is gone. Net request count is
    // unchanged for a user who had the calendar enabled, and +1 for everyone
    // else — who in exchange get expiry and shopping dots on their week view,
    // and one card instead of two rendering the same days.

    // Top stores by spend for the spend-trend card (display slice of the
    // server-aggregated rows).
    const topSpendStores = computed(() => spendByStore.value?.rows.slice(0, 3) ?? []);
    // R-041 / state-ownership — the total and its coverage come from the server
    // now. This used to be a client-side `reduce` over every fetched row while
    // the card displayed only the top 3, which is both a cross-collection
    // aggregate computed in the browser and a total rendered without the count
    // it was built from.
    const spendTotal = computed(() => spendByStore.value?.total_spend ?? 0);
    const spendStoreCount = computed(() => spendByStore.value?.store_count ?? 0);

    // Latest pantry value + the delta since the window's first point.
    const pantryValueLatest = computed(() => {
        const pts = pantryValue.value?.points ?? [];
        return pts.length > 0 ? pts[pts.length - 1]!.value : null;
    });
    const pantryValueDelta = computed(() => {
        const pts = pantryValue.value?.points ?? [];
        if (pts.length < 2) return null;
        return pts[pts.length - 1]!.value - pts[0]!.value;
    });

    async function acceptSuggestion(suggestion: DoraSuggestion) {
        if (!suggestion.primary_action) return;
        try {
            await suggestionStore.snoozeAsync(suggestion, 1);
        } catch {
            // Non-fatal — navigate anyway.
        }
        void router.push(suggestion.primary_action.path);
    }

    async function dismissSuggestion(suggestion: DoraSuggestion) {
        try {
            await suggestionStore.dismissAsync(suggestion);
        } catch (err) {
            console.error('Failed to dismiss suggestion', err);
        }
    }

    async function loadAll() {
        // Fire everything in parallel — the hero/card shells render off the
        // bulk summary, the four P12 cards each have their own slot loader.
        // Stores are deduped, so calling getX() when already populated is
        // ~free (they return the cached array).
        await Promise.all([
            loadSummary(),
            loadAlerts(),
            loadBudget(),
            loadSwapSummary(),
            loadSavings(),
            loadSpendByStore(),
            loadPantryValue(),
            loadPriceDrops(),
            loadKeepsRunningOut(),
            // FU-818 — the merged "What's coming" card is default-on and this is
            // its only source, so it is no longer conditional.
            loadUpcoming(),
            suggestionStore.refreshAsync(),
            shoppingListStore.ensureLoadedAsync(),
            // the donut's low/out segments deep-link to
            // /stock?level_id=<id>; the store hydrates those ids.
            stockLevelStore.ensureLoadedAsync(),
        ]);
        // Primary list detail depends on the shoppingListStore refresh
        // having landed, so it runs after.
        await loadPrimaryListDetail();
    }

    // FU-586: the money/products cards gate on the once-per-document
    // `/api/health` flags probe (and, for money, on `currentUser`'s per-user
    // opt-in). On a cold load — a hard reload or a PWA cold start — those
    // usually haven't resolved when the dashboard mounts, so the gated loaders
    // above early-return and, with nothing re-running them when the flags land,
    // the money/deal card bodies stay blank until the user navigates away and
    // back. Re-fire just the gated loaders when a gate transitions on. On a warm
    // navigation the gate is already true at mount, `loadAll` fetches normally,
    // and these never fire.
    watch(moneyEnabled, (on) => {
        if (!on) return;
        void loadBudget();
        void loadSwapSummary();
        void loadSavings();
        void loadSpendByStore();
        void loadPantryValue();
    });
    watch(productsEnabled, (on) => {
        if (!on) return;
        void loadPriceDrops();
    });

    onMounted(loadAll);
</script>

<style scoped lang="scss">
    /* ───── Page root ───────────────────────────────────────────────────
       FU-747 / chunk 6: the page-local `--c-*` alias layer that used to be
       declared here is **gone**. It mapped 14 global tokens to page-local
       names, which cost a second vocabulary for no behaviour (every alias
       resolved to exactly one global token), and it could not be seen by the
       scoped blocks of the card components — the file's own Cards-menu comment
       said as much. Everything below references the global tokens directly.
    */
    .dora-dash {
        min-height: 100%;
        /* The bottom value is 2 × --space-12: clearance for the mobile bottom
           bar, kept on the scale rather than the old off-scale 96px (A3). */
        padding: var(--space-6) var(--space-6) calc(var(--space-12) * 2);
        /* Dashboard reads the active theme's signature hero gradient as its
           page background — the "special touch" per theme. Every other surface
           reference here goes through the global tokens so the dashboard
           reskins automatically with the rest of the app. */
        background: var(--hero-gradient);
        color: var(--text-primary);
    }

    /* ───── Hero ─────────────────────────────────────────────────────── */
    .dora-hero {
        display: flex;
        align-items: center;
        gap: var(--space-4);
        padding: var(--space-6);
        margin-bottom: var(--space-6);
        background: var(--surface-component);
        border: 1px solid var(--border-default);
        /* A4/D-017: a card is `--radius-lg`. This was 18px, off-scale, and
           shared its value with `DashboardCard` — corrected together, per the
           owner's FU-811 decision (10px is the app's card radius at 41 sites,
           18px at 3). */
        border-radius: var(--radius-lg);
        box-shadow: var(--elevation-card);
    }
    .dora-hero-mascot {
        /* Same radius as `.dora-welcome-mascot` — one element type, one
           radius (D-017). Was 14px here and 10px there for the same thing. */
        border-radius: var(--radius-lg);
        background: var(--brand-primary-soft);
        /* R-002 / A3 carve-out — do NOT round this to `--space-1` (4px).
           The mascot artwork is not centred within its own bounding box, so
           the padding that makes it *look* centred in the square is optical,
           not spatial: it was tuned by hand to 2px in commit 12229346
           ("Properly centre the dora mascot on dashboard"). The chunk-6 scale
           sweep put it on the token and silently doubled it, pushing the glyph
           off centre again. A token here would be wrong for the same reason a
           token is wrong inside an SVG viewBox — the number isn't spacing. */
        padding: 2px;
        flex-shrink: 0;
    }
    .dora-hero-text {
        min-width: 0;
    }
    .dora-hero-greeting {
        font-size: calc(var(--font-size-2xl) * 1rem);
        font-weight: 600;
        line-height: 1.2;
    }
    .dora-hero-line {
        margin-top: var(--space-1);
        color: var(--text-secondary);
        font-size: calc(var(--font-size-md) * 1rem);
    }
    .dora-hero-actions {
        display: flex;
        align-items: center;
        gap: var(--space-1);
    }

    /* Phase 5 quick-action bar — sits between the hero and the cards. */
    .dora-quick-actions {
        display: flex;
        flex-wrap: wrap;
        gap: var(--space-2);
        margin-bottom: var(--space-4);
    }

    /* ───── Cards ────────────────────────────────────────────────────── */
    .dora-cards {
        animation: dora-fade-up 0.4s ease-out both;
    }
    /* Zone band header — a full-width flex item; CSS `order` (set inline)
       places it just before its zone's cards, and being full-width it forces
       the cards onto the next line so each zone reads as a labelled band. */
    .dora-zone-label {
        /* Was 0.72rem (11.5px) — under D-003's 12px hard floor, and the
           smallest text on a page whose zones ARE its information
           architecture (§4.3). Owner decision 2026-09-02: keep the uppercase
           eyebrow treatment, raise it to `--font-size-sm`, rather than take
           A2's full 20px section-header row (which would restructure the
           page's vertical rhythm). The `opacity: 0.8` went with it — dimming
           an already-muted token is the contrast compounding D-002 warns
           about, and it was doing the work the size should have done. */
        font-size: calc(var(--font-size-sm) * 1rem);
        font-weight: 700;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: var(--text-secondary);
        margin-top: var(--space-2);
    }
    /* Zone sub-header inside the Cards toggle menu. NB: q-menu teleports to
       <body>, outside `.dora-dash`, so this cannot rely on any page-scoped
       custom property — one of the reasons the `--c-*` alias layer was
       retired (FU-747). */
    .dora-cards-menu-zone {
        font-size: calc(var(--font-size-xs) * 1rem);
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        /* R-069: `--brand-primary` is a *fill* tone and fails the contrast
           floor as text; `--accent-ink` is its ink-strength sibling. The
           `opacity: 0.9` that used to sit here was compounding that. */
        color: var(--accent-ink);
        padding-top: var(--space-2);
    }
    /* The card shell (`.dora-card`, head, icon, title, action, link, clickable
       + hover) lives in `components/dashboard/DashboardCard.vue`.

       FU-829 chunk 5 — the card BODY styles that used to sit here are gone too,
       now that every card is its own component:

         · shared by several cards  → `css/dashboardCards.scss`
           (`.dora-empty*`, `.dora-cook-*`, `.dora-stat-*`, `.dash-skel-line`)
         · used by exactly one card → that card's own scoped block (R-027)

       What remains below is the page's own chrome: the root, the hero, the
       quick-action bar, the zone band labels, the "Dora says" welcome band, and
       the grid's fade transition. All of it on global tokens — chunk 6 retired
       the `--c-*` alias layer this block used to declare (FU-747). */

    /* The deal-row styles (`.dora-deal-*`) and their mobile reflow moved into
       `components/dashboard/PriceDropsCard.vue`, the only card that still uses
       them now that FU-819 cut "Best deals" (R-027). */

    /* ───── Dora welcome / message banner (D1) ───────────────────────────
       Inline, top-of-dashboard greeting that replaced the old fixed
       bottom-right tip bubble — keeps the warm "Dora says" treatment. The
       `--warn` modifier is the skip-reminder variant. */
    .dora-welcome {
        display: flex;
        align-items: center;
        gap: var(--space-3);
        /* Asymmetric on purpose: the wider inline-start pad sits behind the
           4px accent rule so the text keeps an even optical inset. */
        padding: var(--space-3) var(--space-3) var(--space-3) var(--space-4);
        background: var(--surface-component);
        border: 1px solid var(--border-default);
        border-left: 4px solid var(--brand-primary);
        border-radius: var(--radius-lg);
        box-shadow: var(--elevation-card);
    }
    .dora-welcome--warn {
        border-left-color: var(--semantic-warning);
        background: var(--semantic-warning-soft);
    }
    .dora-welcome-mascot {
        border-radius: var(--radius-lg);
        background: var(--brand-primary-soft);
        /* Optical, hand-tuned — see the carve-out note on `.dora-hero-mascot`.
           This one is a 40px square rather than 72px, so it takes 1px, and the
           same sweep had quadrupled it. */
        padding: 1px;
    }
    .dora-welcome-body {
        min-width: 0;
        flex: 1;
    }
    .dora-welcome-line {
        font-size: calc(var(--font-size-md) * 1rem);
        line-height: 1.35;
        color: var(--text-primary);
    }
    .dora-welcome-line strong {
        /* R-069: accent as *text* is `--accent-ink`, not the fill tone. */
        color: var(--accent-ink);
        font-weight: 700;
    }
    .dora-welcome--warn .dora-welcome-line strong {
        color: var(--semantic-warning);
    }
    .dora-welcome-hint {
        margin-top: var(--space-1);
        font-size: calc(var(--font-size-sm) * 1rem);
        color: var(--text-secondary);
    }
    .dora-welcome-actions {
        margin-top: var(--space-2);
        display: flex;
        flex-wrap: wrap;
        gap: var(--space-2);
    }


    .fade-enter-active,
    .fade-leave-active {
        transition: opacity 0.25s ease, transform 0.25s ease;
    }
    .fade-enter-from,
    .fade-leave-to {
        opacity: 0;
        transform: translateY(8px);
    }

    @keyframes dora-fade-up {
        from {
            opacity: 0;
            transform: translateY(6px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    /* Respect the user's motion preference — no animation or transitions. */
    @media (prefers-reduced-motion: reduce) {
        /* `.dora-card`/`.dora-card-action` motion is handled inside
           DashboardCard's own reduced-motion rule, and the donut segments' in
           `PantryDonutCard` — a scoped rule can't reach into a child component
           anyway, which is why each extracted card carries its own guard. */
        .dora-cards,
        .fade-enter-active,
        .fade-leave-active {
            animation: none !important;
            transition: none !important;
        }
    }

    /* Stack the hero on narrow screens so the buttons don't push the
       greeting off-canvas. */
    @media (max-width: 600px) {
        .dora-hero {
            flex-wrap: wrap;
        }
        .dora-hero-actions {
            flex-basis: 100%;
            justify-content: flex-end;
        }
        .dora-dash {
            padding: var(--space-4) var(--space-4) calc(var(--space-12) * 2);
        }
        /* Phase 7 mobile pass. The zone grid already stacks (cards are
           col-12 below sm); these tidy the new Phase 4/5 bits for touch. */
        /* Quick-action buttons span the row so they're easy thumb targets. */
        .dora-quick-actions {
            gap: var(--space-2);
        }
        .dora-quick-actions :deep(.q-btn) {
            flex: 1 1 auto;
        }
        /* The savings range toggle's mobile tap-height rule is gone with the
           hand-rolled chips — `BaseSegmented` carries its own sizing (FU-830).
           Whether its `dense size="sm"` clears the D-004 44px floor on touch is
           a real question, and it belongs to the chunk-6 tap-target pass rather
           than a patch here. */
        /* The alert summary chips' mobile padding moved into
           `AttentionCard.vue`. */
    }
</style>
