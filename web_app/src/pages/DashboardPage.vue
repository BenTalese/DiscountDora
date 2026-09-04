<template>
    <!-- FU-609 / R-036 — root on <q-page> for the layout height contract.
         Document-scroll page (the window scrolls the dashboard); no :style-fn. -->
    <q-page class="dora-dash">
        <!-- ───── Hero band ─────────────────────────────────────────────── -->
        <!-- Owner 2026-09-04 — "Dora says" was a separate dismissible band
             directly under this one, with its own 40px mascot. Two problems,
             both his: the band repeated the mascot standing right beside it
             ("Dora is literally right there. Seeing double feels a bit odd"),
             and it was a second card saying a softer version of what the hero
             already said. So the message moved *into* the hero and the band is
             gone — which also retires the per-day dismissal (`dashboard_welcome_
             dismissed_day` + `epochDay`): you can't dismiss half a header, and a
             message that rotates daily never needed a hide button.

             The factual line under the greeting went with it. It read
             "N items are out of stock", which the owner called out as pretty
             useless text to read — the alerts bell and the stock card both
             already answer that, better. Dora's message is the line now. -->
        <section class="dora-hero">
            <q-avatar size="72px" square class="dora-hero-mascot">
                <img src="../assets/logo-mascot.png" alt="Dashy Dora" />
            </q-avatar>
            <div class="dora-hero-text">
                <div class="dora-hero-greeting">
                    {{ greeting }}<span v-if="firstName">, {{ firstName }}</span>
                </div>
                <div class="dora-hero-line">{{ welcomeMessage }}</div>
                <div class="dora-hero-hint">{{ welcomeHint }}</div>
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
                            <!-- One flat list since the owner cut the zones
                                 (2026-09-04): reorder now spans every card
                                 rather than being trapped inside a band. The
                                 up/down buttons are C13's tap-mandatory
                                 alternative — they work on mobile and from the
                                 keyboard; drag is the desktop extra. -->
                            <q-item
                                v-for="card in menuCards"
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
                                    <q-tooltip>Drag to reorder</q-tooltip>
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
                        </q-list>
                    </q-menu>
                </BaseButton>
            </div>
        </section>

        <!-- The Phase 5 quick-action bar (Add item · Add to list · Log price)
             was removed on the owner's call, 2026-09-04. §9's "the home screen
             *does*, not just routes" is still right, but these three were not
             how it does it: each opened a dialog reachable from the surface
             that actually owns the object, and none of them was the thing you
             came to the dashboard to do. The cards below all carry their own
             verbs (Cook, Add to list, Use it up), which is doing-not-routing
             attached to a reason. The dialogs themselves are untouched — the
             global QuickAddSheet and LogPriceSheet keep every other caller. -->

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

        <!-- D1's second band — the rotating "Dora says" welcome — merged into
             the hero above (see the note there). What survives here is the
             *first* band: the 24h skip-reminder (F1), which owns the
             not-yet-finished-onboarding window. It stays because it is not a
             greeting — it's a one-off state with two verbs, and it genuinely
             disappears once you finish or hide it.

             Its 40px mascot went the way of the welcome band's, for the same
             reason: the 72px one is ~60px above it. -->
        <transition name="fade">
            <aside
                v-if="showSkipReminder"
                class="dora-welcome dora-welcome--warn q-mb-md"
                role="note"
                aria-label="Finish setup"
            >
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
            <!-- The zone band headers (Phase 2) are gone with the zones
                 themselves — owner, 2026-09-04. They were full-width flex items
                 whose CSS `order` forced a line break before each band; with one
                 flat user-owned order there is no band to label, and the grid is
                 a plain run of cards whose parity is computed once. -->

            <!-- ───── Next to cook (FU-298; batch-aware since 2026-09-04) ─── -->
            <div
                v-if="cardRendered('next_to_cook')"
                :class="cardCol('next_to_cook')"
                :style="{ order: cardCssOrder('next_to_cook') }"
            >
                <NextToCookCard
                    :entries="nextToCook"
                    :has-planned-meals="hasPlannedMeals"
                    @cook="cookPlannedMeal"
                />
            </div>

            <!-- ───── Use it up (owner 2026-09-04) ────────────────────────── -->
            <!-- One of the two cards that replaced "Needs your attention" and
                 "Dora suggests". Answers "what's about to go off, and what can
                 I cook with it *right now*" by joining near-expiry stock to the
                 recipes that use it — a question neither the alerts bell (which
                 states the expiry and stops) nor the chat (which has to be
                 asked) answers on its own.

                 C-waste W5 note: this is also where the retired "Use soon" card
                 landed. PROPOSAL_WASTE_MINIMISATION §4.5 cut it and sent
                 near-expiry items to the attention card's `expired` /
                 `expiring_soon` alert kinds; that card is now gone too, and this
                 one carries the signal with the cook action §4.5 never had. -->
            <div
                v-if="cardRendered('use_it_up')"
                :class="cardCol('use_it_up')"
                :style="{ order: cardCssOrder('use_it_up') }"
            >
                <UseItUpCard
                    :items="useItUp?.items ?? []"
                    :recipes="useItUp?.recipes ?? []"
                    :failed="slotFailed('use_it_up')"
                    @retry="loadUseItUp"
                />
            </div>

            <!-- ───── Before you shop (owner 2026-09-04) ──────────────────── -->
            <!-- The other replacement card. Two forward-looking signals the
                 rest of the app never puts together: items whose own
                 consumption rate says they run out before the household's next
                 shop, and what the coming week's plan needs that the pantry
                 can't cover. Both end in the same verb — add it to a list. -->
            <div
                v-if="cardRendered('before_you_shop')"
                :class="cardCol('before_you_shop')"
                :style="{ order: cardCssOrder('before_you_shop') }"
            >
                <BeforeYouShopCard
                    :running-out="beforeYouShop?.running_out ?? []"
                    :plan-gaps="beforeYouShop?.plan_gaps ?? []"
                    :shop-in-days="beforeYouShop?.shop_in_days ?? null"
                    :failed="slotFailed('before_you_shop')"
                    @retry="loadBeforeYouShop"
                />
            </div>

            <!-- ───── Shopping lists (owner 2026-09-04) ───────────────────── -->
            <!-- Was "Primary shopping list", which showed one list and labelled
                 it *primary* — a word from the era when the cart button's target
                 was the point. The owner's question ("why would I need to see my
                 shopping list?") has an answer, but it isn't one list: it's
                 quick nav to the three that matter, each with the totals that
                 tell you which one you want. -->
            <div
                v-if="cardRendered('shopping_lists')"
                :class="cardCol('shopping_lists')"
                :style="{ order: cardCssOrder('shopping_lists') }"
            >
                <ShoppingListsCard
                    :current="shoppingListCards.current"
                    :next="shoppingListCards.next"
                    :finished="shoppingListCards.finished"
                    :failed="slotFailed('shopping_lists')"
                    @retry="loadShoppingListCards"
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

            <!-- FU-317's "Reconcile past meals" chip card is gone (owner,
                 2026-09-04): *"that's quite odd … instead put that metric as the
                 link to go do meal reconciliation"*. A card whose whole body was
                 one button had to assert its own importance; the same queue is
                 now the `plan_adherence` component of Kitchen health below, and
                 that row links to `/meal-plans/reconcile`. The nudge on the
                 meal-plans header is untouched — it's in context there. -->

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
                    :recently-out="restockRadar?.recently_out ?? []"
                    :recently-low="restockRadar?.recently_low ?? []"
                    :failed="slotFailed('restock')"
                    @retry="loadRestockRadar"
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

            <!-- "Spend by store" and "Pantry value" were cut here (owner,
                 2026-09-04). Spend-by-store is a report and Reports has it —
                 *"there shouldn't be overlap between the dashboard and the
                 report page"* — and pantry value is the same call the reports
                 review already made about stock valuation. Both endpoints stay;
                 the reports page is their caller. -->

            <!-- ───── Price drops (Phase 4 — products-gated) ─────────────── -->
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
    import MoneyCard from 'src/components/dashboard/MoneyCard.vue';
    import PriceDropsCard from 'src/components/dashboard/PriceDropsCard.vue';
    import RestockRadarCard from 'src/components/dashboard/RestockRadarCard.vue';
    import PantryDonutCard, {
        type DonutSegment,
    } from 'src/components/dashboard/PantryDonutCard.vue';
    import NextToCookCard from 'src/components/dashboard/NextToCookCard.vue';
    import ShoppingListsCard from 'src/components/dashboard/ShoppingListsCard.vue';
    import UseItUpCard from 'src/components/dashboard/UseItUpCard.vue';
    import BeforeYouShopCard from 'src/components/dashboard/BeforeYouShopCard.vue';
    import WhatsComingCard, {
        type CalendarCell,
        type CalendarSpan,
    } from 'src/components/dashboard/WhatsComingCard.vue';
    import DoraScoreCard from 'src/components/dashboard/DoraScoreCard.vue';
    import { storeToRefs } from 'pinia';
    // `AttentionCard` and its alert presentation helpers went with the card
    // (owner, 2026-09-04 — the alerts bell says the same thing one row above).
    // The `Upcoming` types stay: the merged calendar still reads
    // `/alerts/upcoming`, which is a dated-events feed, not the alert list.
    import {
        type Upcoming,
        type UpcomingDay,
    } from 'src/models/alert';
    import type { DashboardSummary, UpcomingMealPlanEntry } from 'src/models/dashboard';
    import { pickWelcome, pickHint } from 'src/helpers/dashboardMessages';
    import AlertApiService from 'src/services/api/alertApiService';
    import BudgetApiService, {
        type BudgetStatus,
    } from 'src/services/api/budgetApiService';
    import MealPlanApiService from 'src/services/api/mealPlanApiService';
    import DashboardApiService, {
        type UseItUpResponse,
        type BeforeYouShopResponse,
        type DashboardListsResponse,
        type RestockRadarResponse,
    } from 'src/services/api/dashboardApiService';
    import OnboardingApiService from 'src/services/api/onboardingApiService';
    import ReportsApiService, {
        type ReportRange,
        type SavingsCapturedResponse,
        type PriceDropsResponse,
    } from 'src/services/api/reportsApiService';
    import { useAuthStore } from 'src/stores/authStore';
    import { useShoppingListStore } from 'src/stores/shoppingListStore';
    import { useStockLevelStore } from 'src/stores/stockLevelStore';
    import {
        LOW_STOCK_SEQUENCE,
        OUT_OF_STOCK_SEQUENCE,
        findLevelBySequence,
    } from 'src/helpers/stockStatus';
    import { useMoneyEnabled } from 'src/composables/useMoneyEnabled';
    import { useBatchEnabled } from 'src/composables/useBatchEnabled';
    import { useFeatureFlags } from 'src/composables/useFeatureFlags';
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
        type CardId,
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
    // install-wide products feature flag — which is what the owner asked Price
    // drops to be gated on (2026-09-04), and what it was already reading; the
    // registry comment calling it "data-presence" was simply wrong. Read by
    // `cardAvailable`.
    const { moneyEnabled } = useMoneyEnabled();
    const { products: productsEnabled } = useFeatureFlags();
    // Cook style — the install-wide batch switch. "Next to cook" selects
    // different rows under it (see `nextToCook`), and the card labels them.
    const { batchEnabled } = useBatchEnabled();
    const dashboardApiService = new DashboardApiService();
    const alertApi = new AlertApiService();
    const budgetApi = new BudgetApiService();
    const reportsApi = new ReportsApiService();

    const shoppingListStore = useShoppingListStore();
    // donut segments deep-link to /stock?level_id=<id>. The stock
    // overview already reads `level_id` from the query; we just need the two
    // level ids (low / out) that match the canonical status sequences.
    const stockLevelStore = useStockLevelStore();
    const { stockLevels } = storeToRefs(stockLevelStore);

    const summary = ref<DashboardSummary | null>(null);
    const loading = ref(false);
    const loadError = ref<string | null>(null);

    // FU-825's per-day dismissal (`dora.dashboard.welcome_dismissed_day` +
    // `epochDay`) is gone with the welcome band: the message lives in the hero
    // now, and a header is not dismissible. The `localStorage` key is simply
    // abandoned — it was only ever read by the code above, so a stale value on
    // an existing install has nothing left to hide.

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
        | 'shopping_lists'
        | 'use_it_up'
        | 'before_you_shop'
        | 'budget'
        | 'swaps'
        | 'savings'
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
    // in parallel and never block each other — one slow response shouldn't
    // gate the rest of the dashboard.
    //
    // The three lists worth quick nav to (current · next · most recently
    // finished), server-picked. See `dashboardApiService.getListsAsync`.
    const dashboardLists = ref<DashboardListsResponse | null>(null);
    // The two replacement insight cards (owner, 2026-09-04). Both are
    // server-computed joins — the client renders rows and emits verbs (R-003);
    // it does not decide what is expiring, what a recipe covers, or when the
    // household next shops.
    const useItUp = ref<UseItUpResponse | null>(null);
    const beforeYouShop = ref<BeforeYouShopResponse | null>(null);
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
    // Phase 4 — money widgets backed by the reports API. Only loaded when money
    // is enabled (the cards are gated on it anyway). `spendByStore` and
    // `pantryValue` went with their cards on 2026-09-04 — both were reports on
    // the dashboard, and Reports is where they live.
    const savings = ref<SavingsCapturedResponse | null>(null);
    const savingsRange = ref<ReportRange>('30d');
    const priceDrops = ref<PriceDropsResponse | null>(null);
    // Restock radar — what just ran out and what just went low. Reworked on
    // the owner's ask (2026-09-04) off `/dashboard/restock-radar`; the old
    // `/reports/keeps-running-out` lifetime ranking stays on the reports page,
    // which still calls it.
    const restockRadar = ref<RestockRadarResponse | null>(null);
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
    // template position and flexbox sorts them (see `cardCssOrder`).
    //
    // The stored `order` array is filtered to known ids on read, which is what
    // makes the 09-04 card cull a non-event for existing users: a layout naming
    // `attention` / `draft_shop` / `suggestions` / `spend_trend` /
    // `pantry_value` / `reconcile_pending` — or the renamed `cookable` and
    // `primary_list` — simply drops those entries and appends the new cards at
    // their registry positions.
    type DashLayout = { order: CardId[]; hidden: CardId[] };

    const KNOWN_CARD_IDS = new Set<CardId>(CARD_DEFS.map((c) => c.id));

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
    // `isCardVisible` answers "is it registered, gated on, and un-hidden", and
    // since 2026-09-04 that is the whole answer: `reconcile_pending` was the
    // only card that additionally vanished on its own *data* (hide-when-empty,
    // R-029), and it was deleted with the rest of the cull.
    //
    // The predicate stays rather than collapsing into `isCardVisible`, because
    // it is the ONE thing both the template's `v-if` and the column-width maths
    // consult: if those two ever disagreed, the grid would pair a card that
    // isn't there and leave the gap it was meant to fill (R-003). The next
    // hide-when-empty card belongs here, not in a second `v-if` condition at
    // its call site.
    function cardRendered(id: CardId): boolean {
        return isCardVisible(id);
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

    // Column classes per card, so no card is left in a half-width column beside
    // dead air (D-011 / B4) — see `helpers/dashboardGrid` for the measured
    // counts and why the parity is per run of consecutive half-width cards.
    //
    // One call, not one per zone: with the bands gone (owner, 2026-09-04) the
    // rendered cards are a single run, which is the case `zoneColClasses` was
    // always written for — a run is a run whether or not it has a label above
    // it. The parity fix is now *global*, which is strictly better: an odd
    // card count used to strand one card per band (up to four gaps on a
    // default desktop), and can now strand at most one on the whole page.
    const cardColClasses = computed<Record<string, string>>(() =>
        zoneColClasses(cardOrder.value.filter(cardRendered), FULL_WIDTH_CARDS),
    );
    function cardCol(id: CardId): string {
        // A card that isn't rendered has no entry; the half default keeps the
        // binding total rather than resolving to `undefined`.
        return cardColClasses.value[id] ?? CARD_COL_HALF;
    }

    // CSS `order` per card = its index in the user's order array. The zone base
    // (`zoneIndex * 100`) that used to be added here is gone with the zones: a
    // card no longer belongs to a band it can't leave, so the user's own order
    // is the whole answer.
    function cardCssOrder(id: CardId): number {
        const i = cardOrder.value.indexOf(id);
        return i === -1 ? CARD_DEFS.findIndex((c) => c.id === id) : i;
    }

    // Reorder — the tap alternative to drag (C13: drag is the power-user extra,
    // the tap control is always present + works on mobile). The peer list is now
    // simply every available card, so a card can be moved anywhere on the page
    // rather than shuffled inside its band.
    //
    // Gated-off cards are excluded, which matters: with money off, `savings` is
    // still in `cardOrder` but renders nowhere, and including it would make one
    // press of Move-up look like it did nothing.
    function orderedAvailableCards(): CardId[] {
        return cardOrder.value.filter(cardAvailable);
    }
    function canMove(id: CardId, dir: 'up' | 'down'): boolean {
        const peers = orderedAvailableCards();
        const i = peers.indexOf(id);
        return dir === 'up' ? i > 0 : i >= 0 && i < peers.length - 1;
    }
    function moveCard(id: CardId, dir: 'up' | 'down') {
        const peers = orderedAvailableCards();
        const i = peers.indexOf(id);
        const j = dir === 'up' ? i - 1 : i + 1;
        if (i < 0 || j < 0 || j >= peers.length) return;
        const other = peers[j]!;
        const next = [...cardOrder.value];
        const oi = next.indexOf(id);
        const oj = next.indexOf(other);
        [next[oi], next[oj]] = [next[oj]!, next[oi]!];
        cardOrder.value = next;
        persistLayout();
    }

    // drag-handle reorder for the Cards menu. Sits on top of the existing tap
    // up/down: drag is the desktop power-user extra; tap is the mobile/keyboard
    // mandate (C13). `canDropOn` used to refuse a cross-zone drop; with the
    // zones gone every card may land anywhere, so the only rejection left is
    // dropping a card on itself (handled in `onDrop`).
    // `cardDragEnabled` gates the handle on non-touch — `$q.platform.is.mobile`
    // includes tablets so touch-first surfaces keep the tap path uncluttered.
    const cardDragEnabled = computed(() => !$q.platform.is.mobile);
    const cardDnd = useDragDropList<CardId>({
        mime: 'application/x-dora-dashboard-card',
        getId: (id) => id,
        canDragStart: () => cardDragEnabled.value,
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

    // The toggle menu's rows, in display order. Gated-off cards are dropped so
    // the menu never offers an unavailable one. Flat since the zones went.
    const menuCards = computed(() =>
        orderedAvailableCards().map((id) => CARD_DEFS.find((c) => c.id === id)!),
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
    // `nextEntry` went with the hero's factual line on 2026-09-04 — that
    // sentence was its only reader. The next meal is still stated, in the one
    // place that also says whether you can cook it: the "Next to cook" card.

    // ── Welcome + hint of the day (D1c/d/e) ──────────────────────────────
    // A day-of-week-flavoured welcome plus a day-agnostic hint, both stable
    // per calendar day (see helpers/dashboardMessages).
    //
    // These are the hero's two lines now (owner, 2026-09-04). They used to sit
    // in a dismissible band below it, under a second mascot, beneath a factual
    // "N items are out of stock" line — three separate things saying hello. The
    // factual line is gone (the owner: *"that feels like pretty useless text to
    // read"*), and with it `heroLine`, `plural` and `capitalise`, which nothing
    // else on the page used.
    //
    // The old `showWelcome` gate is gone too. It suppressed the greeting while
    // the skip-reminder banner was up, on the reasoning that the banner *was*
    // the message; that only made sense while both were bands competing for the
    // same slot. A header does not compete with a banner underneath it.
    const welcomeMessage = computed(() => pickWelcome());
    // FU-823 — the hint pool is filtered by the install's feature gates, so a
    // money-off household is never told to set a grocery budget and a
    // product-less one isn't sold the deals card (feedback L254 / ADR-005).
    const welcomeHint = computed(() =>
        pickHint({ money: moneyEnabled.value, products: productsEnabled.value })
    );

    // ── Helpers ──────────────────────────────────────────────────────────
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

    // The alerts fetch and the alert-action handler went with `AttentionCard`
    // (owner, 2026-09-04). `alertApi` stays — the merged calendar below still
    // reads `/alerts/upcoming`, which is a different endpoint answering a
    // different question (dated events, not the alert list). The alert list
    // itself has one consumer now: the bell in the app header, which owns it.

    // ── Next to cook ────────────────────────────────────────────────────
    // Meal-plan-driven (feedback L272): upcoming entries from
    // `summary.meal_plan.upcoming_entries`, deduped by recipe so the same
    // recipe scheduled twice in the week only shows once (earliest slot wins),
    // capped at 3, each tagged with a ready / missing-N badge from the
    // server-derived `missing_count`.
    //
    // **Two selection strategies, keyed on cook style** (owner, 2026-09-04).
    // The 09-04 batch taught this card the pool model, but only as *labels* —
    // it still listed the next few days in order, which is the wrong question
    // for a household that batch-cooks. There, the plan is not a cook schedule:
    // one batch covers many planned days, so most of what's coming needs
    // nobody to cook it, and listing it is noise.
    //
    //   fresh household → the next planned meals, chronologically. Plan day is
    //                     cook day, so the calendar *is* the answer.
    //   batch household → the meals somebody actually has to cook: the ones the
    //                     pool is short of (`needs_cooking`), plus fresh-marked
    //                     entries (`cook_fresh`), which stand outside the pool
    //                     in both directions and are cooked on their own day.
    //
    // Both flags are server-owned and never both true (`_cook_verdicts` in
    // `get_dashboard_summary.py`) — this filters on the server's verdict, it
    // doesn't re-derive coverage (R-003). Chronological order is already "when
    // the shortfall bites", since the entries arrive sorted by date.
    const nextToCook = computed<UpcomingMealPlanEntry[]>(() => {
        const entries = summary.value?.meal_plan.upcoming_entries ?? [];
        const worthCooking = batchEnabled.value
            ? entries.filter((e) => e.needs_cooking || e.cook_fresh)
            : entries;
        const seen = new Set<string>();
        const picks: UpcomingMealPlanEntry[] = [];
        for (const e of worthCooking) {
            if (seen.has(e.recipe_id)) continue;
            seen.add(e.recipe_id);
            picks.push(e);
            if (picks.length >= 3) break;
        }
        return picks;
    });

    // Whether the week holds any planned meal at all — the card needs to tell
    // "nothing planned" apart from "planned, and the freezer already covers it",
    // which are the same empty list but opposite messages.
    const hasPlannedMeals = computed(
        () => (summary.value?.meal_plan.upcoming_entries.length ?? 0) > 0,
    );

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

    // ── Shopping lists (current · next · last finished) ──────────────────
    // Was one card showing the *primary* list's totals, which the owner read —
    // correctly — as a leftover from when the cart button's target was the
    // interesting fact about a list. It also fetched a whole `ShoppingListDetail`
    // (every line, every price) to render three numbers.
    //
    // The server now picks the three lists and returns their totals
    // (`/api/dashboard/lists`), which is both the smaller payload and the
    // right owner: "which list am I shopping, which is next, which did I just
    // finish" is a cross-entity question about status and dates (R-003).
    const shoppingListCards = computed(() => ({
        current: dashboardLists.value?.current ?? null,
        next: dashboardLists.value?.next ?? null,
        finished: dashboardLists.value?.finished ?? null,
    }));

    async function loadShoppingListCards() {
        await loadSlot('shopping_lists', async () => {
            dashboardLists.value = await dashboardApiService.getListsAsync();
        });
    }

    // The card's picks depend on which list is in flight, so re-fetch when the
    // store's quick-add target changes (e.g. set-primary from another tab).
    watch(() => shoppingListStore.quickAddTargetListId, () => {
        void loadShoppingListCards();
    });

    // ── Use it up / Before you shop (owner, 2026-09-04) ──────────────────
    // Both are server-computed joins. `use-it-up` walks near-expiry stock and
    // the recipes that use it; `before-you-shop` puts consumption rate against
    // the household's own shop cadence, and the coming week's plan against what
    // the pantry holds. Neither could be assembled client-side without the SPA
    // re-implementing expiry windows, per-item burn rates and plan demand — the
    // exact "client computing a cross-entity rule" smell the state-ownership
    // principle names.
    async function loadUseItUp() {
        await loadSlot('use_it_up', async () => {
            useItUp.value = await dashboardApiService.getUseItUpAsync();
        });
    }

    async function loadBeforeYouShop() {
        await loadSlot('before_you_shop', async () => {
            beforeYouShop.value = await dashboardApiService.getBeforeYouShopAsync();
        });
    }

    // No page-level add wrapper: both row-bearing cards render the shared
    // `AddToListButton` themselves, which is what the owner asked for — *"should
    // use the same shopping cart button from the stock overview rows"* — and is
    // the R-011 answer anyway. That component owns the target-list decision, the
    // already-on-a-list toggle and the toast, none of which the dashboard should
    // be re-deciding on the way past.

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

    // `loadSpendByStore` and `loadPantryValue` went with their cards (owner,
    // 2026-09-04). `reportsApi.getSpendByStoreAsync` / `getStockValueAsync` keep
    // their callers on the reports page, so nothing is orphaned here.

    // price-drops is products-gated (not money-gated); still cheap to
    // load, hides itself when empty.
    async function loadPriceDrops() {
        if (!productsEnabled.value) { priceDrops.value = null; return; }
        await loadSlot('price_drops', async () => {
            priceDrops.value = await reportsApi.getPriceDropsAsync(5);
        });
    }
    const priceDropRows = computed(() => priceDrops.value?.rows ?? []);

    // ── Restock radar ────────────────────────────────────────────────────
    async function loadRestockRadar() {
        await loadSlot('restock', async () => {
            restockRadar.value = await dashboardApiService.getRestockRadarAsync();
        });
    }

    // `onStockItemCreated` went with the quick-action "Add item" dialog. The
    // dialog itself is untouched; every other caller opens it from the surface
    // that owns stock items.

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

    // The spend-by-store and pantry-value display slices went with their cards
    // (owner, 2026-09-04), as did `acceptSuggestion` / `dismissSuggestion` and
    // the `suggestionStore` refresh — the suggestion store keeps its other
    // consumers (the Dora launcher badge and the chat panel), which is where
    // the owner said this content belongs: *"we're keeping the Dora chat"*.

    async function loadAll() {
        // Fire everything in parallel — the hero/card shells render off the
        // bulk summary, each card has its own slot loader. Stores are deduped,
        // so calling getX() when already populated is ~free.
        await Promise.all([
            loadSummary(),
            loadShoppingListCards(),
            loadUseItUp(),
            loadBeforeYouShop(),
            loadBudget(),
            loadSwapSummary(),
            loadSavings(),
            loadPriceDrops(),
            loadRestockRadar(),
            // FU-818 — the merged "What's coming" card is default-on and this is
            // its only source, so it is no longer conditional.
            loadUpcoming(),
            shoppingListStore.ensureLoadedAsync(),
            // the donut's low/out segments deep-link to
            // /stock?level_id=<id>; the store hydrates those ids.
            stockLevelStore.ensureLoadedAsync(),
        ]);
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
    /* Owner 2026-09-04 — the greeting is brand voice, not a heading: one token
       step down (2xl → xl), the Cute Dino face, and the theme's accent colour.
       Same treatment `PageTitle` gives a page name, which is the "title" the
       owner pointed at.

       `--accent-ink`, not `--brand-primary`: R-069 — the brand tone is a *fill*
       and misses the contrast floor as text; `--accent-ink` is its ink-strength
       sibling and is what every other accent-coloured string on this page uses.

       The font stack is spelled out rather than reusing `DoraBrand` — that
       component renders the literal words "Dashy Dora" and centralises the
       *mark*, not the face. Wrapping a greeting in it would be borrowing a
       component for its stylesheet (R-001). If a third caller ever wants the
       face on arbitrary text, that's the moment for a token. */
    .dora-hero-greeting {
        font-family: 'Cute Dino', 'Nunito Variable', 'Nunito', sans-serif;
        font-size: calc(var(--font-size-xl) * 1rem);
        font-weight: 600;
        line-height: 1.2;
        color: var(--accent-ink);
    }
    /* Dora's message of the day — the hero's main line since the "Dora says"
       band merged in. `--text-primary`, not the old `--text-secondary`: it is
       the sentence you actually read here now, not a caption under a heading. */
    .dora-hero-line {
        margin-top: var(--space-1);
        color: var(--text-primary);
        font-size: calc(var(--font-size-md) * 1rem);
        line-height: 1.35;
    }
    /* The hint that used to be `.dora-welcome-hint` in the merged band. */
    .dora-hero-hint {
        margin-top: var(--space-1);
        color: var(--text-secondary);
        font-size: calc(var(--font-size-sm) * 1rem);
    }
    .dora-hero-actions {
        display: flex;
        align-items: center;
        gap: var(--space-1);
    }

    /* ───── Cards ────────────────────────────────────────────────────── */
    .dora-cards {
        animation: dora-fade-up 0.4s ease-out both;
    }
    /* The zone band header and the Cards-menu zone sub-header are gone with
       the zones (owner, 2026-09-04). Their §4.3 rationale — "the zones ARE the
       page's information architecture" — was true of seventeen cards and isn't
       of nine; the order the user chooses is the architecture now. */
    /* The card shell (`.dora-card`, head, icon, title, action, link, clickable
       + hover) lives in `components/dashboard/DashboardCard.vue`.

       FU-829 chunk 5 — the card BODY styles that used to sit here are gone too,
       now that every card is its own component:

         · shared by several cards  → `css/dashboardCards.scss`
           (`.dora-empty*`, `.dora-cook-*`, `.dora-stat-*`, `.dash-skel-line`)
         · used by exactly one card → that card's own scoped block (R-027)

       What remains below is the page's own chrome: the root, the hero, the
       onboarding skip-reminder band, and the grid's fade transition. The
       quick-action bar, the zone band labels and the "Dora says" welcome band
       were all removed on 2026-09-04. All of it on global tokens — chunk 6 retired
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
    /* `.dora-welcome-mascot` went with the second mascot itself. The radius
       cross-reference on `.dora-hero-mascot` above is kept as written — it
       records *why* both were `--radius-lg`, which is still the reason the
       surviving one is. */
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
        /* Phase 7 mobile pass. The card grid already stacks (cards are
           col-12 below sm). The quick-action bar's thumb-target rules went
           with the bar itself (owner, 2026-09-04). */
        /* The savings range toggle's mobile tap-height rule is gone with the
           hand-rolled chips — `BaseSegmented` carries its own sizing (FU-830).
           Whether its `dense size="sm"` clears the D-004 44px floor on touch is
           a real question, and it belongs to the chunk-6 tap-target pass rather
           than a patch here. */
        /* The alert summary chips' mobile padding moved into
           `AttentionCard.vue`. */
    }
</style>
