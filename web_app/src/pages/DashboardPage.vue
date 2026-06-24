<template>
    <div class="dora-dash">
        <!-- ───── Hero band ─────────────────────────────────────────────── -->
        <section class="dora-hero">
            <q-avatar size="72px" square class="dora-hero-mascot">
                <img src="../assets/logo-mascot.png" alt="Discount Dora" />
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
                <q-btn flat dense no-caps :icon="ICONS.tune" label="Cards">
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
                                <q-item v-for="card in group.cards" :key="card.id">
                                    <q-item-section avatar>
                                        <q-icon :name="card.icon" />
                                    </q-item-section>
                                    <q-item-section>{{ card.label }}</q-item-section>
                                    <q-item-section side>
                                        <div class="row items-center no-wrap">
                                            <q-btn
                                                flat
                                                dense
                                                round
                                                size="sm"
                                                :icon="ICONS.arrow_upward"
                                                :disable="!canMove(card.id, 'up')"
                                                @click="moveCard(card.id, 'up')"
                                            >
                                                <q-tooltip>Move up</q-tooltip>
                                            </q-btn>
                                            <q-btn
                                                flat
                                                dense
                                                round
                                                size="sm"
                                                :icon="ICONS.arrow_downward"
                                                :disable="!canMove(card.id, 'down')"
                                                @click="moveCard(card.id, 'down')"
                                            >
                                                <q-tooltip>Move down</q-tooltip>
                                            </q-btn>
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
                </q-btn>
            </div>
        </section>

        <!-- Phase 5 quick actions (decision §9): the home screen *does*, not just
             routes. Lightweight inline dialogs — Add item opens the shared
             CreateStockItemDialog; Add to list pops the global QuickAddSheet.
             No navigation. (Log-price is a future add — needs a product target.) -->
        <div class="dora-quick-actions">
            <q-btn
                outline
                no-caps
                :icon="ICONS.add"
                label="Add item"
                color="primary"
                @click="showCreateStockItem = true"
            />
            <q-btn
                outline
                no-caps
                :icon="ICONS.shopping_cart"
                label="Add to list"
                color="primary"
                @click="openQuickAdd()"
            />
        </div>

        <q-banner v-if="loadError" class="dora-bg-negative-soft text-negative q-mb-md" dense rounded>
            {{ loadError }}
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
                        <q-btn
                            flat
                            dense
                            no-caps
                            :icon="ICONS.east"
                            label="Continue"
                            :loading="continuingOnboarding"
                            @click="onContinueOnboarding"
                        />
                        <q-btn
                            flat
                            dense
                            no-caps
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
                <q-btn
                    flat
                    round
                    dense
                    size="sm"
                    :icon="ICONS.close"
                    @click="welcomeDismissed = true"
                >
                    <q-tooltip>Hide for today</q-tooltip>
                </q-btn>
            </aside>
        </transition>

        <FadeTransition mode="out-in">
        <div v-if="loading && !summary" key="dash-loading" class="row justify-center q-pa-xl">
            <AppSpinner size="48px" />
        </div>

        <div v-else-if="summary" key="dash-content" class="row q-col-gutter-md dora-cards">
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
            <!-- R-014: renders whenever the card is visible — a calm "all clear"
                 state instead of vanishing, so the dashboard looks best (not
                 emptiest) when nothing's wrong. -->
            <div
                v-if="isCardVisible('attention')"
                class="col-12 col-lg-6"
                :style="{ order: cardCssOrder('attention') }"
            >
                <DashboardCard :icon="ICONS.notifications_active" title="Needs your attention">
                    <template #action>
                        <router-link
                            v-if="alerts.length > 0"
                            class="dora-card-action dora-card-link"
                            to="/alerts"
                        >
                            All {{ alerts.length }} →
                        </router-link>
                    </template>
                    <div v-if="topAlerts.length === 0" class="dora-empty dora-empty-ok">
                        <q-icon :name="ICONS.check_circle" size="18px" class="q-mr-xs" />
                        All clear — nothing needs your attention right now.
                    </div>
                    <template v-else>
                        <!-- D6 top section: a by-kind summary so you see the
                             *shape* of what's wrong at a glance ("5 expiring
                             soon", "3 out of stock") before the detail rows.
                             Each chip opens the alerts control page. -->
                        <div class="dora-alert-summary">
                            <router-link
                                v-for="g in alertKindSummary"
                                :key="g.kind"
                                to="/alerts"
                                class="dora-alert-chip"
                            >
                                <q-icon
                                    :name="alertIconFor(g.kind)"
                                    :color="alertColorFor(g.severity)"
                                    size="16px"
                                />
                                <span class="dora-alert-chip-num">{{ g.count }}</span>
                                <span class="dora-alert-chip-label">{{ kindTheme(g.kind) }}</span>
                            </router-link>
                        </div>

                        <!-- D6 bottom section: a peek at the top few, most-urgent
                             first, with the inline quick-actions. -->
                        <ul class="dora-attn-list">
                            <li
                                v-for="p in peekAlerts"
                                :key="p.alert.alert_id"
                                class="dora-attn-row"
                            >
                                <span
                                    class="dora-attn-dot"
                                    :class="`dora-attn-dot-${p.alert.severity}`"
                                />
                                <q-icon
                                    :name="alertIconFor(p.alert.kind)"
                                    :color="alertColorFor(p.alert.severity)"
                                    size="18px"
                                />
                                <!-- a11y: real <router-link> when the alert has a
                                     deep-link target (replaces the old href="#"
                                     handler). Stock alerts link the item name;
                                     non-stock nudges link the message text. -->
                                <router-link
                                    v-if="p.alert.stock_item_name && p.link"
                                    :to="p.link"
                                    class="dora-attn-name"
                                >
                                    {{ p.alert.stock_item_name }}
                                </router-link>
                                <span v-else-if="p.alert.stock_item_name" class="dora-attn-name">
                                    {{ p.alert.stock_item_name }}
                                </span>
                                <router-link
                                    v-if="!p.alert.stock_item_name && p.link"
                                    :to="p.link"
                                    class="dora-attn-msg dora-attn-msg-link"
                                >
                                    {{ p.alert.message }}
                                </router-link>
                                <span v-else class="dora-attn-msg">{{ p.alert.message }}</span>
                                <span class="dora-attn-actions">
                                    <q-btn
                                        v-for="a in alertActionsFor(p.alert.kind)"
                                        :key="a.action"
                                        flat
                                        dense
                                        size="sm"
                                        no-caps
                                        :icon="a.icon"
                                        :label="a.label"
                                        @click="applyAlertAction(p.alert, a.action)"
                                    />
                                </span>
                            </li>
                        </ul>

                        <router-link to="/alerts" class="dora-alert-seeall">
                            See all alerts →
                        </router-link>
                    </template>
                </DashboardCard>
            </div>

            <!-- ───── Primary shopping list (P12) ─────────────────────────── -->
            <div
                v-if="isCardVisible('primary_list') && quickAddTargetSummary"
                class="col-12 col-sm-6 col-lg-6"
                :style="{ order: cardCssOrder('primary_list') }"
            >
                <DashboardCard :icon="ICONS.shopping_cart" title="Primary shopping list">
                    <template #action>
                        <router-link
                            class="dora-card-action dora-card-link"
                            :to="`/shopping-lists/${quickAddTargetSummary.shopping_list_id}`"
                        >
                            Open list →
                        </router-link>
                    </template>
                    <div class="dora-primary-list-name">
                        {{ quickAddTargetSummary.display_name }}
                    </div>
                    <div v-if="primaryListStats" class="dora-stat-grid q-mt-sm">
                        <div class="dora-stat">
                            <div class="dora-stat-num">
                                <AnimatedNumber :value="primaryListStats.unticked" />
                            </div>
                            <div class="dora-stat-label">to grab</div>
                        </div>
                        <div class="dora-stat">
                            <div class="dora-stat-num">
                                <AnimatedNumber :value="primaryListStats.remaining" prefix="$" />
                            </div>
                            <div class="dora-stat-label">remaining</div>
                        </div>
                        <div
                            v-if="primaryListStats.savings > 0"
                            class="dora-stat dora-stat-ok"
                        >
                            <div class="dora-stat-num">
                                <AnimatedNumber :value="primaryListStats.savings" prefix="$" />
                            </div>
                            <div class="dora-stat-label">saves vs rrp</div>
                        </div>
                    </div>
                    <div v-else class="dora-empty q-mt-sm">
                        Loading totals…
                    </div>
                    <router-link
                        v-if="otherActiveListCount > 0"
                        class="dora-card-footer-link"
                        to="/shopping-lists"
                    >
                        +{{ otherActiveListCount }} other active
                        {{ otherActiveListCount === 1 ? 'list' : 'lists' }} →
                    </router-link>
                </DashboardCard>
            </div>
            <div
                v-else-if="isCardVisible('primary_list') && !quickAddTargetSummary"
                class="col-12 col-sm-6 col-lg-6"
                :style="{ order: cardCssOrder('primary_list') }"
            >
                <DashboardCard :icon="ICONS.shopping_cart" title="Primary shopping list" :to="'/shopping-lists'">
                    <template #action>
                        <span class="dora-card-action">Pick one →</span>
                    </template>
                    <div class="dora-empty">
                        No primary set — the cart button needs one to one-tap items in.
                    </div>
                </DashboardCard>
            </div>

            <!-- ───── Grocery budget (P2-05) ──────────────────────────────── -->
            <div
                v-if="isCardVisible('budget') && budgetStatus"
                class="col-12 col-sm-6 col-lg-6"
                :style="{ order: cardCssOrder('budget') }"
            >
                <DashboardCard :icon="ICONS.savings" :to="'/settings/money'">
                    <template #title>
                        {{ budgetStatus.enabled ? 'Grocery budget' : 'Grocery spend this ' + budgetStatus.period.replace('ly', '') }}
                    </template>
                    <template #action>
                        <span class="dora-card-action">
                            {{ budgetStatus.enabled ? 'Settings →' : 'Set a budget →' }}
                        </span>
                    </template>
                    <div v-if="budgetStatus.enabled" class="dora-budget-body">
                        <div class="dora-budget-headline">
                            <span
                                class="dora-budget-spent"
                                :class="{ 'text-negative': budgetStatus.over_budget }"
                            >
                                ${{ budgetStatus.spent.toFixed(2) }}
                            </span>
                            <span class="dora-budget-of">
                                of ${{ budgetStatus.amount!.toFixed(2) }}
                            </span>
                            <span
                                class="dora-budget-remaining"
                                :class="budgetStatus.over_budget ? 'text-negative' : 'dora-text-muted'"
                            >
                                {{
                                    budgetStatus.over_budget
                                        ? `$${Math.abs(budgetStatus.remaining ?? 0).toFixed(2)} over`
                                        : `$${(budgetStatus.remaining ?? 0).toFixed(2)} left`
                                }}
                            </span>
                        </div>
                        <q-linear-progress
                            :value="Math.min(1, budgetStatus.spent / (budgetStatus.amount || 1))"
                            :color="budgetStatus.over_budget ? 'negative' : 'primary'"
                            class="q-mt-sm"
                            size="8px"
                            rounded
                        />
                        <div
                            v-if="budgetStatus.projected_active > 0"
                            class="text-caption dora-text-muted q-mt-xs"
                        >
                            +${{ budgetStatus.projected_active.toFixed(2) }} in active lists
                        </div>
                    </div>
                    <div v-else class="dora-empty">
                        ${{ budgetStatus.spent.toFixed(2) }} spent so far. Set a target
                        in Settings to see how you're tracking.
                    </div>
                </DashboardCard>
            </div>

            <!-- ───── Dora suggests (P2-04) ───────────────────────────────── -->
            <!-- R-014: calm empty state instead of vanishing when Dora has
                 nothing to suggest. -->
            <div
                v-if="isCardVisible('suggestions')"
                class="col-12 col-sm-6 col-lg-6"
                :style="{ order: cardCssOrder('suggestions') }"
            >
                <DashboardCard icon="auto_awesome" title="Dora suggests">
                    <template #action>
                        <span
                            v-if="suggestionStore.count > 2"
                            class="dora-card-action"
                        >
                            +{{ suggestionStore.count - 2 }} more in chat
                        </span>
                    </template>
                    <div v-if="suggestionStore.count === 0" class="dora-empty dora-empty-ok">
                        <q-icon :name="ICONS.check_circle" size="18px" class="q-mr-xs" />
                        Nothing to suggest right now — you're on top of things.
                    </div>
                    <div v-else class="dora-suggest-list">
                        <div
                            v-for="suggestion in suggestionStore.suggestions.slice(0, 2)"
                            :key="`${suggestion.kind}:${suggestion.dedup_key}`"
                            class="dora-suggest-row"
                            :class="`dora-suggest-${suggestion.severity}`"
                        >
                            <div class="dora-suggest-title">
                                {{ suggestion.title }}
                            </div>
                            <div class="dora-suggest-body">
                                {{ suggestion.body }}
                            </div>
                            <div class="row q-gutter-xs q-mt-xs">
                                <q-btn
                                    v-if="suggestion.primary_action"
                                    dense
                                    no-caps
                                    size="sm"
                                    unelevated
                                    color="primary"
                                    :label="suggestion.primary_action.label"
                                    @click="acceptSuggestion(suggestion)"
                                />
                                <q-btn
                                    dense
                                    no-caps
                                    size="sm"
                                    flat
                                    color="grey"
                                    label="Dismiss"
                                    @click="dismissSuggestion(suggestion)"
                                />
                            </div>
                        </div>
                    </div>
                </DashboardCard>
            </div>

            <!-- ───── Use soon (P2-06) ────────────────────────────────────── -->
            <!-- R-014: calm empty state instead of vanishing when nothing's
                 near its use-by date. -->
            <div
                v-if="isCardVisible('use_soon')"
                class="col-12 col-sm-6 col-lg-6"
                :style="{ order: cardCssOrder('use_soon') }"
            >
                <DashboardCard :icon="ICONS.expiry" title="Use soon">
                    <template #action>
                        <router-link
                            v-if="wasteRescue && wasteRescue.items.length > 0"
                            class="dora-card-action dora-card-link"
                            to="/waste"
                        >
                            Rescue ideas →
                        </router-link>
                    </template>
                    <div
                        v-if="!wasteRescue || wasteRescue.items.length === 0"
                        class="dora-empty dora-empty-ok"
                    >
                        <q-icon :name="ICONS.check_circle" size="18px" class="q-mr-xs" />
                        Nothing's near its use-by date. Nice.
                    </div>
                    <ul v-else class="dora-attn-list">
                        <li
                            v-for="item in wasteRescue.items.slice(0, 4)"
                            :key="item.stock_item_id"
                            class="dora-attn-row"
                        >
                            <span
                                class="dora-attn-dot"
                                :class="item.is_expired
                                    ? 'dora-attn-dot-high'
                                    : item.days_until_expiry <= 2
                                        ? 'dora-attn-dot-medium'
                                        : 'dora-attn-dot-low'"
                            />
                            <router-link
                                class="dora-attn-name"
                                :to="`/stock/${item.stock_item_id}`"
                            >
                                {{ item.name }}
                            </router-link>
                            <span class="dora-attn-msg">
                                {{
                                    item.is_expired
                                        ? `expired ${Math.abs(item.days_until_expiry)}d ago`
                                        : item.days_until_expiry === 0
                                            ? 'today'
                                            : item.days_until_expiry === 1
                                                ? 'tomorrow'
                                                : `in ${item.days_until_expiry}d`
                                }}
                            </span>
                        </li>
                    </ul>
                    <div
                        v-if="wasteRescue && wasteRescue.items.length > 0 && wasteRescue.recipes.length > 0"
                        class="text-caption dora-text-muted q-mt-xs"
                    >
                        {{ wasteRescue.recipes[0]!.matching_count }} can go into
                        <em>{{ wasteRescue.recipes[0]!.name }}</em>
                        <span v-if="wasteRescue.recipes.length > 1">
                            (+{{ wasteRescue.recipes.length - 1 }} more idea{{
                                wasteRescue.recipes.length === 2 ? '' : 's'
                            }})
                        </span>
                    </div>
                </DashboardCard>
            </div>

            <!-- ───── Cookable tonight (P12) ──────────────────────────────── -->
            <div
                v-if="isCardVisible('cookable')"
                class="col-12 col-sm-6 col-lg-6"
                :style="{ order: cardCssOrder('cookable') }"
            >
                <DashboardCard :icon="ICONS.restaurant_menu">
                    <template #title>
                        Cookable tonight
                        <span
                            v-if="summary && summary.recipes.cookable_count > 0"
                            class="dora-text-muted text-body2"
                        >({{ summary.recipes.cookable_count }})</span>
                    </template>
                    <template #action>
                        <router-link
                            class="dora-card-action dora-card-link"
                            to="/cookbook?cookable=true"
                        >
                            See more →
                        </router-link>
                    </template>
                    <ul v-if="cookableTonight.length > 0" class="dora-cook-list">
                        <li
                            v-for="r in cookableTonight"
                            :key="r.recipe_id"
                            class="dora-cook-row"
                        >
                            <router-link
                                class="dora-cook-name"
                                :to="`/cookbook/${r.recipe_id}`"
                            >
                                <q-icon
                                    v-if="r.is_favourite"
                                    name="favorite"
                                    color="negative"
                                    size="14px"
                                    class="q-mr-xs"
                                />
                                {{ r.name }}
                            </router-link>
                            <span class="dora-cook-meta">
                                <span v-if="recipeTotalTime(r) !== null">
                                    {{ recipeTotalTime(r) }}m
                                </span>
                                <span v-if="r.servings">
                                    · serves {{ r.servings }}
                                </span>
                            </span>
                            <q-btn
                                flat
                                dense
                                no-caps
                                size="sm"
                                :icon="ICONS.restaurant"
                                label="Cook"
                                color="primary"
                                @click="goTo(`/cookbook/${r.recipe_id}/cook`)"
                            />
                        </li>
                    </ul>
                    <div v-else class="dora-empty">
                        Nothing's fully in stock right now.
                        <router-link class="dora-empty-cta" to="/cookbook">Browse recipes →</router-link>
                    </div>
                </DashboardCard>
            </div>

            <!-- ───── Best deals on saved products (P12) ──────────────────── -->
            <div
                v-if="isCardVisible('best_deals')"
                class="col-12 col-sm-6 col-lg-6"
                :style="{ order: cardCssOrder('best_deals') }"
            >
                <DashboardCard :icon="ICONS.local_offer" title="Best deals on your saved products">
                    <template #action>
                        <router-link
                            class="dora-card-action dora-card-link"
                            to="/my-products"
                        >
                            My products →
                        </router-link>
                    </template>
                    <ul v-if="bestDeals.length > 0" class="dora-deal-list">
                        <li
                            v-for="p in bestDeals"
                            :key="p.product_id"
                            class="dora-deal-row"
                        >
                            <q-avatar rounded size="36px" class="dora-bg-sunken dora-deal-img">
                                <img
                                    v-if="p.has_image"
                                    :src="`/api/products/${p.product_id}/image`"
                                    :alt="p.name"
                                />
                                <q-icon v-else :name="ICONS.shopping_bag" size="18px" />
                            </q-avatar>
                            <div class="dora-deal-text">
                                <div class="dora-deal-name">{{ p.name }}</div>
                                <div class="dora-deal-meta">
                                    {{ p.store_name }}
                                    <span v-if="p.linked_stock_item_id">
                                        ·
                                        <router-link
                                            class="text-primary"
                                            :to="`/stock/${p.linked_stock_item_id}`"
                                        >
                                            {{ p.linked_stock_item_name }}
                                        </router-link>
                                    </span>
                                </div>
                            </div>
                            <div class="dora-deal-price">
                                <span class="dora-deal-now">
                                    ${{ p.price_now.toFixed(2) }}
                                </span>
                                <span class="dora-deal-was">
                                    ${{ p.price_was.toFixed(2) }}
                                </span>
                            </div>
                            <q-badge class="dora-deal-badge" color="negative" text-color="white">
                                {{ discountPercent(p) }}% off
                            </q-badge>
                        </li>
                    </ul>
                    <div v-else class="dora-empty">
                        Nothing on special among your saved products right now.
                        <router-link class="dora-empty-cta" to="/product-search">Hunt for deals →</router-link>
                    </div>
                </DashboardCard>
            </div>

            <!-- ───── Stock card (with donut) ────────────────────────────── -->
            <div
                v-if="isCardVisible('stock_items')"
                class="col-12 col-sm-6 col-lg-4"
                :style="{ order: cardCssOrder('stock_items') }"
            >
                <DashboardCard icon="inventory_2" title="Pantry" :to="'/stock'">
                    <template #action>
                        <span class="dora-card-action">View →</span>
                    </template>
                    <div class="dora-stock-body">
                        <svg
                            viewBox="0 0 36 36"
                            class="dora-donut"
                            :aria-label="`${summary.stock_items.total} stock items: ${stockInStockCount} in stock, ${summary.stock_items.low_stock} low, ${summary.stock_items.out_of_stock} out`"
                        >
                            <circle class="dora-donut-track" cx="18" cy="18" r="15.915" />
                            <circle
                                v-for="(seg, i) in stockSegments"
                                :key="seg.label"
                                cx="18"
                                cy="18"
                                r="15.915"
                                fill="none"
                                stroke-width="4"
                                :stroke="seg.colour"
                                :stroke-dasharray="`${seg.percent} ${100 - seg.percent}`"
                                :stroke-dashoffset="seg.offset"
                                :style="{ transitionDelay: `${i * 60}ms` }"
                                class="dora-donut-seg"
                            />
                            <text x="18" y="17" text-anchor="middle" class="dora-donut-big">
                                {{ summary.stock_items.total }}
                            </text>
                            <text x="18" y="22.5" text-anchor="middle" class="dora-donut-sub">items</text>
                        </svg>
                        <ul class="dora-legend">
                            <li>
                                <span class="dora-dot dora-dot-ok"></span>
                                <span class="dora-legend-num">{{ stockInStockCount }}</span>
                                <span class="dora-legend-label">in stock</span>
                            </li>
                            <li>
                                <span class="dora-dot dora-dot-warn"></span>
                                <span class="dora-legend-num">{{ summary.stock_items.low_stock }}</span>
                                <span class="dora-legend-label">running low</span>
                            </li>
                            <li>
                                <span class="dora-dot dora-dot-bad"></span>
                                <span class="dora-legend-num">{{ summary.stock_items.out_of_stock }}</span>
                                <span class="dora-legend-label">out</span>
                            </li>
                        </ul>
                    </div>
                </DashboardCard>
            </div>

            <!-- ───── Meal plan card (with 7-day strip) ──────────────────── -->
            <div
                v-if="isCardVisible('meal_plan')"
                class="col-12 col-lg-8"
                :style="{ order: cardCssOrder('meal_plan') }"
            >
                <DashboardCard :icon="ICONS.calendar_month" title="The week ahead" :to="'/meal-plans'">
                    <template #action>
                        <span class="dora-card-action">Plan →</span>
                    </template>
                    <div v-if="nextEntry" class="dora-next-up">
                        <div class="dora-next-up-label">Next up</div>
                        <div class="dora-next-up-meal">{{ nextEntry.recipe_name }}</div>
                        <div class="dora-next-up-meta">
                            {{ formatRelativeDay(nextEntry.scheduled_for) }} ·
                            {{ nextEntry.slot }} · ×{{ nextEntry.servings }}
                        </div>
                    </div>
                    <div v-else class="dora-empty">
                        Nothing planned. <span class="dora-empty-cta">Set up a week →</span>
                    </div>

                    <div class="dora-strip" role="list">
                        <div
                            v-for="day in weekStrip"
                            :key="day.iso"
                            class="dora-strip-day"
                            :class="{ 'is-today': day.isToday, 'has-meals': day.entries.length > 0 }"
                            role="listitem"
                        >
                            <div class="dora-strip-dow">{{ day.dow }}</div>
                            <div class="dora-strip-num">{{ day.dayNum }}</div>
                            <div class="dora-strip-meals">
                                <span
                                    v-for="entry in day.entries.slice(0, 2)"
                                    :key="entry.recipe_name + entry.slot"
                                    class="dora-strip-pip"
                                    :title="`${entry.recipe_name} (${entry.slot})`"
                                />
                                <span
                                    v-if="day.entries.length > 2"
                                    class="dora-strip-more"
                                >+{{ day.entries.length - 2 }}</span>
                            </div>
                        </div>
                    </div>
                </DashboardCard>
            </div>

            <!-- ───── This fortnight calendar (Phase 6 / D7) ──────────────── -->
            <div
                v-if="isCardVisible('calendar')"
                class="col-12"
                :style="{ order: cardCssOrder('calendar') }"
            >
                <DashboardCard :icon="ICONS.calendar_month" title="This fortnight">
                    <template #action>
                        <div class="dora-cal-legend">
                            <span class="dora-cal-leg"><span class="dora-cal-dot dot-meal" /> meals</span>
                            <span class="dora-cal-leg"><span class="dora-cal-dot dot-expiry" /> expiry</span>
                            <span class="dora-cal-leg"><span class="dora-cal-dot dot-shopping" /> shopping</span>
                        </div>
                    </template>
                    <template v-if="calendarCells.length > 0">
                        <div class="dora-cal-grid" role="grid">
                            <button
                                v-for="cell in calendarCells"
                                :key="cell.iso"
                                type="button"
                                class="dora-cal-cell"
                                :class="{
                                    'is-today': cell.isToday,
                                    'is-selected': cell.iso === selectedCalDate,
                                    'has-events': cell.hasMeal || cell.hasExpiry || cell.hasShopping,
                                }"
                                @click="selectCalDate(cell.iso)"
                            >
                                <span class="dora-cal-num">{{ cell.dayNum }}</span>
                                <span class="dora-cal-dots">
                                    <span v-if="cell.hasMeal" class="dora-cal-dot dot-meal" />
                                    <span v-if="cell.hasExpiry" class="dora-cal-dot dot-expiry" />
                                    <span v-if="cell.hasShopping" class="dora-cal-dot dot-shopping" />
                                </span>
                            </button>
                        </div>
                        <div v-if="selectedCalDay" class="dora-cal-detail">
                            <div class="dora-cal-detail-date">
                                {{ formatRelativeDay(selectedCalDay.date) }}
                            </div>
                            <div v-if="selectedCalDay.meals.length > 0" class="dora-cal-group">
                                <div class="dora-cal-group-label">Meals</div>
                                <router-link
                                    v-for="(m, i) in selectedCalDay.meals"
                                    :key="`${m.recipe_id}-${m.slot}-${i}`"
                                    class="dora-cal-item"
                                    :to="`/cookbook/${m.recipe_id}`"
                                >
                                    {{ m.recipe_name }} <span class="dora-cal-slot">· {{ m.slot }}</span>
                                </router-link>
                            </div>
                            <div v-if="selectedCalDay.expiries.length > 0" class="dora-cal-group">
                                <div class="dora-cal-group-label">Expiring</div>
                                <router-link
                                    v-for="e in selectedCalDay.expiries"
                                    :key="e.stock_item_id"
                                    class="dora-cal-item"
                                    :to="`/stock/${e.stock_item_id}`"
                                >
                                    {{ e.name }}
                                </router-link>
                            </div>
                            <div v-if="selectedCalDay.shopping.length > 0" class="dora-cal-group">
                                <div class="dora-cal-group-label">Shopping</div>
                                <router-link
                                    v-for="s in selectedCalDay.shopping"
                                    :key="s.list_id"
                                    class="dora-cal-item"
                                    :to="`/shopping-lists/${s.list_id}`"
                                >
                                    {{ s.name }}
                                </router-link>
                            </div>
                        </div>
                        <div v-else class="dora-cal-hint">
                            Tap a day with dots to see what's on.
                        </div>
                    </template>
                    <div v-else class="dora-empty">
                        Nothing scheduled in the next fortnight — enjoy the calm.
                    </div>
                </DashboardCard>
            </div>

            <!-- ───── Restock radar (Phase 5) ─────────────────────────────── -->
            <div
                v-if="isCardVisible('restock')"
                class="col-12 col-sm-6 col-lg-6"
                :style="{ order: cardCssOrder('restock') }"
            >
                <DashboardCard :icon="ICONS.replay" title="Restock radar">
                    <template #action>
                        <router-link
                            v-if="restockItems.length > 0"
                            class="dora-card-action dora-card-link"
                            to="/stock"
                        >
                            Pantry →
                        </router-link>
                    </template>
                    <ul v-if="restockItems.length > 0" class="dora-cook-list">
                        <li
                            v-for="item in restockItems"
                            :key="item.stock_item_id"
                            class="dora-cook-row"
                        >
                            <router-link class="dora-cook-name" :to="`/stock/${item.stock_item_id}`">
                                {{ item.name }}
                            </router-link>
                            <span class="dora-cook-meta">ran out {{ item.times_out_when_added }}×</span>
                            <q-btn
                                flat
                                dense
                                no-caps
                                size="sm"
                                :icon="ICONS.shopping_cart"
                                label="Add"
                                color="primary"
                                @click="addRestockToList(item.stock_item_id)"
                            />
                        </li>
                    </ul>
                    <div v-else class="dora-empty">
                        Once you've restocked the same things a few times, I'll flag
                        what to keep an eye on.
                    </div>
                </DashboardCard>
            </div>

            <!-- ───── Savings captured (Phase 4 — Money zone flagship) ────── -->
            <div
                v-if="isCardVisible('savings')"
                class="col-12 col-sm-6 col-lg-6"
                :style="{ order: cardCssOrder('savings') }"
            >
                <DashboardCard :icon="ICONS.savings" title="You've saved">
                    <template #action>
                        <div class="dora-range-toggle">
                            <button
                                v-for="r in SAVINGS_RANGES"
                                :key="r.value"
                                type="button"
                                class="dora-range-chip"
                                :class="{ 'is-active': savingsRange === r.value }"
                                @click="savingsRange = r.value"
                            >
                                {{ r.label }}
                            </button>
                        </div>
                    </template>
                    <div v-if="savings && savings.total_savings > 0">
                        <div class="dora-savings-amount">
                            <AnimatedNumber :value="savings.total_savings" prefix="$" />
                        </div>
                        <div class="dora-savings-sub">vs RRP, {{ savingsRangeLabel }}</div>
                        <div class="dora-savings-spent">
                            on ${{ savings.total_spent.toFixed(2) }} spent across
                            {{ savings.lists.length }} shop{{ savings.lists.length === 1 ? '' : 's' }}
                        </div>
                    </div>
                    <div v-else class="dora-empty">
                        Finish a shop and I'll tally what you saved vs RRP.
                    </div>
                </DashboardCard>
            </div>

            <!-- ───── Spend by store (Phase 4 — opt-in) ───────────────────── -->
            <div
                v-if="isCardVisible('spend_trend')"
                class="col-12 col-sm-6 col-lg-6"
                :style="{ order: cardCssOrder('spend_trend') }"
            >
                <DashboardCard :icon="ICONS.storefront" title="Spend by store">
                    <template #action>
                        <span class="dora-card-action">last 30 days</span>
                    </template>
                    <ul v-if="topSpendStores.length > 0" class="dora-spend-list">
                        <li
                            v-for="row in topSpendStores"
                            :key="row.store_id ?? row.store"
                            class="dora-spend-row"
                        >
                            <span class="dora-spend-store">{{ row.store }}</span>
                            <span class="dora-spend-amt">${{ row.spend.toFixed(2) }}</span>
                        </li>
                    </ul>
                    <div v-if="topSpendStores.length > 0" class="dora-spend-total">
                        ${{ totalSpend.toFixed(2) }} total
                    </div>
                    <div v-else class="dora-empty">
                        Your spend by store shows up once you complete a shop.
                    </div>
                </DashboardCard>
            </div>

            <!-- ───── Pantry value (Phase 4 — opt-in) ─────────────────────── -->
            <div
                v-if="isCardVisible('pantry_value')"
                class="col-12 col-sm-6 col-lg-4"
                :style="{ order: cardCssOrder('pantry_value') }"
            >
                <DashboardCard :icon="ICONS.inventory" title="Pantry value">
                    <div v-if="pantryValueLatest !== null">
                        <div class="dora-stat-num">${{ pantryValueLatest.toFixed(2) }}</div>
                        <div
                            v-if="pantryValueDelta !== null && pantryValueDelta !== 0"
                            class="dora-pantry-delta"
                            :class="pantryValueDelta > 0 ? 'is-up' : 'is-down'"
                        >
                            {{ pantryValueDelta > 0 ? '▲' : '▼' }}
                            ${{ Math.abs(pantryValueDelta).toFixed(2) }} over 90 days
                        </div>
                        <div
                            v-if="pantryValue?.estimate_note"
                            class="text-caption dora-text-muted q-mt-xs"
                        >
                            {{ pantryValue.estimate_note }}
                        </div>
                    </div>
                    <div v-else class="dora-empty">
                        Add prices to your stock items to see what your pantry's worth.
                    </div>
                </DashboardCard>
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
    </div>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import FadeTransition from 'src/components/transitions/FadeTransition.vue';
    import AppSpinner from 'src/components/AppSpinner.vue';
    import AnimatedNumber from 'src/components/AnimatedNumber.vue';
    import DashboardCard from 'src/components/dashboard/DashboardCard.vue';
    import { storeToRefs } from 'pinia';
    import {
        actionsFor as alertActionsFor,
        colorFor as alertColorFor,
        iconFor as alertIconFor,
        kindTheme,
        linkFor as alertLinkFor,
        type Alert,
        type AlertAction,
        type AlertKind,
        type AlertSeverity,
        type Upcoming,
        type UpcomingDay,
    } from 'src/models/alert';
    import type { DashboardSummary, UpcomingMealPlanEntry } from 'src/models/dashboard';
    import type { Product } from 'src/models/product';
    import { discountPercent } from 'src/helpers/scrapedProductOfferLogic';
    import { pickWelcome, pickHint } from 'src/helpers/dashboardMessages';
    import type { Recipe } from 'src/models/recipe';
    import type { ShoppingListDetail } from 'src/models/shoppingList';
    import AlertApiService from 'src/services/api/alertApiService';
    import BudgetApiService, {
        type BudgetStatus,
    } from 'src/services/api/budgetApiService';
    import WasteApiService, {
        type WasteRescue,
    } from 'src/services/api/wasteApiService';
    import { useSuggestionStore } from 'src/stores/suggestionStore';
    import type { DoraSuggestion } from 'src/services/api/suggestionsApiService';
    import DashboardApiService from 'src/services/api/dashboardApiService';
    import OnboardingApiService from 'src/services/api/onboardingApiService';
    import ProductApiService from 'src/services/api/productApiService';
    import ShoppingListApiService from 'src/services/api/shoppingListApiService';
    import ReportsApiService, {
        type ReportRange,
        type SavingsCapturedResponse,
        type StoreSpendResponse,
        type StockValueResponse,
        type KeepsRunningOutResponse,
    } from 'src/services/api/reportsApiService';
    import CreateStockItemDialog from 'src/components/stock/CreateStockItemDialog.vue';
    import { useAuthStore } from 'src/stores/authStore';
    import { useRecipeStore } from 'src/stores/recipeStore';
    import { useShoppingListStore } from 'src/stores/shoppingListStore';
    import { useMoneyEnabled } from 'src/composables/useMoneyEnabled';
    import { useFeatureFlags } from 'src/composables/useFeatureFlags';
    import { useStockItemActions } from 'src/composables/useStockItemActions';
    import { useQuickAdd } from 'src/composables/useQuickAdd';
    import { computed, onMounted, ref, watch } from 'vue';
    import { useRouter } from 'vue-router';

    type CardId =
        | 'attention'
        | 'primary_list'
        | 'budget'
        | 'use_soon'
        | 'suggestions'
        | 'cookable'
        | 'best_deals'
        | 'stock_items'
        | 'meal_plan'
        // Phase 4 — Money zone widgets backed by the reports API.
        | 'savings'
        | 'spend_trend'
        | 'pantry_value'
        // Phase 5 — predictive restock.
        | 'restock'
        // Phase 6 — unified fortnight calendar (D7).
        | 'calendar';

    // Zones group cards into purpose-bands so the eye gets a triage gradient
    // (Phase 2). They're fixed (a card belongs to one zone); the user reorders
    // *within* a zone + toggles visibility. Render order = zone order, then the
    // user's order within each zone (applied via CSS `order`, below).
    type ZoneId = 'act' | 'today' | 'money' | 'kitchen';
    const ZONES: { id: ZoneId; label: string }[] = [
        { id: 'act', label: 'Act now' },
        { id: 'today', label: 'Today' },
        { id: 'money', label: 'Money' },
        { id: 'kitchen', label: 'Your kitchen' },
    ];

    type CardDef = {
        id: CardId;
        label: string;
        icon: string;
        zone: ZoneId;
        // Opt-in-by-default cards (Anti-creep, §2.2) start hidden — e.g. the
        // secondary Money-zone glance widgets (spend trend, pantry value).
        defaultHidden?: boolean;
        // Feature gate: the card is unavailable (hidden from the dashboard AND
        // the Cards menu) unless its gate is on. 'money' → useMoneyEnabled
        // (any dollar surface, ADR-005); 'products' → product data-presence
        // (§2.4 — don't offer product widgets to users with no products).
        gate?: 'money' | 'products';
    };

    // The default order within each zone (and the toggle-menu order). The user
    // can reorder within a zone; their saved order overrides this.
    const CARD_DEFS: CardDef[] = [
        { id: 'attention', label: 'Needs your attention', icon: ICONS.notifications_active, zone: 'act' },
        { id: 'use_soon', label: 'Use soon', icon: ICONS.expiry, zone: 'act' },
        { id: 'suggestions', label: 'Dora suggests', icon: 'auto_awesome', zone: 'act' },
        { id: 'cookable', label: 'Cookable tonight', icon: ICONS.restaurant_menu, zone: 'today' },
        { id: 'meal_plan', label: 'The week ahead', icon: ICONS.calendar_month, zone: 'today' },
        { id: 'primary_list', label: 'Primary shopping list', icon: ICONS.shopping_cart, zone: 'today' },
        { id: 'restock', label: 'Restock radar', icon: ICONS.replay, zone: 'today' },
        // Wide fortnight calendar — opt-in (it's large and overlaps the
        // week-ahead strip; users enable it from the Cards menu).
        { id: 'calendar', label: 'This fortnight', icon: ICONS.calendar_month, zone: 'today', defaultHidden: true },
        // Money zone. Savings leads (the headline payoff, default-on when money
        // is enabled); spend + pantry value are opt-in glances. best_deals is
        // gated on product data-presence (§2.4).
        { id: 'savings', label: 'Savings captured', icon: ICONS.savings, zone: 'money', gate: 'money' },
        { id: 'budget', label: 'Grocery budget', icon: ICONS.savings, zone: 'money' },
        { id: 'best_deals', label: 'Best deals on saved products', icon: ICONS.local_offer, zone: 'money', gate: 'products' },
        { id: 'spend_trend', label: 'Spend by store', icon: ICONS.storefront, zone: 'money', gate: 'money', defaultHidden: true },
        { id: 'pantry_value', label: 'Pantry value', icon: ICONS.inventory, zone: 'money', gate: 'money', defaultHidden: true },
        { id: 'stock_items', label: 'Pantry', icon: 'inventory_2', zone: 'kitchen' },
    ];

    const authStore = useAuthStore();
    const router = useRouter();
    const { currentUser } = storeToRefs(authStore);

    // Feature gates for the Money/Products cards (Phase 4). `moneyEnabled`
    // layers install + per-user money opt-in (ADR-005); `productsEnabled` is the
    // product data-presence flag (§2.4). Read by `cardAvailable`.
    const { moneyEnabled } = useMoneyEnabled();
    const { products: productsEnabled } = useFeatureFlags();
    // Phase 5 — quick actions reuse the shared cross-feature actions so add-to-
    // list / create behave identically to the rest of the app (R-011).
    const { addToList } = useStockItemActions();
    const { openQuickAdd } = useQuickAdd();

    const dashboardApiService = new DashboardApiService();
    const alertApi = new AlertApiService();
    const productApi = new ProductApiService();
    const budgetApi = new BudgetApiService();
    const wasteApi = new WasteApiService();
    const reportsApi = new ReportsApiService();
    // P2-04 — suggestion store shared with the Dora launcher badge and
    // the chat panel so dismiss/snooze here propagates everywhere.
    const suggestionStore = useSuggestionStore();
    const shoppingListApi = new ShoppingListApiService();

    const recipeStore = useRecipeStore();
    const shoppingListStore = useShoppingListStore();

    const { recipes } = storeToRefs(recipeStore);

    const summary = ref<DashboardSummary | null>(null);
    const loading = ref(false);
    const loadError = ref<string | null>(null);
    const welcomeDismissed = ref(false);

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

    // Independent slot loaders. Each card surfaces a small chunk of data
    // beyond what the bulk dashboard summary endpoint returns. They live
    // in parallel and never block each other — a slow alerts response
    // shouldn't gate the rest of the dashboard.
    const alerts = ref<Alert[]>([]);
    const bestDeals = ref<Product[]>([]);
    const primaryListDetail = ref<ShoppingListDetail | null>(null);
    // P2-05 — grocery budget card. Always loads (so the passive "spent
    // this week" state works for users who haven't opted in), but the
    // card is hidden when the loader errors so we never block dashboard
    // render on this slot.
    const budgetStatus = ref<BudgetStatus | null>(null);
    // P2-06 — expiry rescue. Surfaces the top few at-risk items as a
    // peek; the full picture (plus log/freeze/used actions) lives on the
    // /waste page.
    const wasteRescue = ref<WasteRescue | null>(null);

    // Phase 4 — Money zone widgets, each backed by an existing reports endpoint.
    // Only loaded when money is enabled (the cards are gated on it anyway). The
    // savings widget carries its own range toggle; spend/pantry use a sensible
    // default window.
    const savings = ref<SavingsCapturedResponse | null>(null);
    const savingsRange = ref<ReportRange>('30d');
    const spendByStore = ref<StoreSpendResponse | null>(null);
    const pantryValue = ref<StockValueResponse | null>(null);
    // Phase 5 — restock radar (items the user keeps running out of) + the
    // "Add item" quick-action dialog state.
    const keepsRunningOut = ref<KeepsRunningOutResponse | null>(null);
    const showCreateStockItem = ref(false);
    // Phase 6 — the fortnight calendar's server-aggregated dated events + the
    // currently-expanded day.
    const upcoming = ref<Upcoming | null>(null);
    const selectedCalDate = ref<string | null>(null);

    const firstName = computed(() => currentUser.value?.username ?? '');

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

    // CSS `order` per card: a fixed per-zone base (so a card never visually
    // leaves its zone) plus its index in the user's order array (so reorder
    // within a zone sticks). The base spacing (100) ≫ the ≤9 card indices, so
    // zones never interleave. Zone headers sit just before their band.
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
        return CARD_DEFS.some((c) => c.zone === zone && isCardVisible(c.id));
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

    type DonutSegment = { label: string; percent: number; offset: number; colour: string };
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
        const push = (label: string, count: number, colour: string) => {
            if (count <= 0) return;
            const p = pct(count);
            segs.push({ label, percent: p, offset: cursor, colour });
            // Negative offsets walk clockwise around the circle.
            cursor = (cursor - p + 100) % 100;
        };
        // Read the semantic-* tokens off the document so the donut
        // recolours when the user switches theme without a full reload.
        const cs = getComputedStyle(document.documentElement);
        const okColour = cs.getPropertyValue('--semantic-positive').trim() || '#6ba368';
        const warnColour = cs.getPropertyValue('--semantic-warning').trim() || '#e89a45';
        const badColour = cs.getPropertyValue('--semantic-negative').trim() || '#c85a4f';
        push('in stock', inStock, okColour);
        push('low', low, warnColour);
        push('out', out, badColour);
        return segs;
    });

    // ── Week strip ───────────────────────────────────────────────────────
    type StripDay = {
        iso: string;
        dow: string;
        dayNum: number;
        isToday: boolean;
        entries: UpcomingMealPlanEntry[];
    };

    const weekStrip = computed<StripDay[]>(() => {
        if (!summary.value) return [];
        const days: StripDay[] = [];
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        const todayIso = isoOf(today);
        const dowLabels = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

        for (let i = 0; i < 7; i++) {
            const d = new Date(today);
            d.setDate(today.getDate() + i);
            const iso = isoOf(d);
            const entries = summary.value.meal_plan.upcoming_entries.filter(
                (e) => e.scheduled_for === iso
            );
            days.push({
                iso,
                dow: dowLabels[d.getDay()]!,
                dayNum: d.getDate(),
                isToday: iso === todayIso,
                entries
            });
        }
        return days;
    });

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
    const welcomeHint = computed(() => pickHint());
    // Only greet once the user has finished (or skipped past) onboarding —
    // while the skip-reminder is showing, that banner is the message.
    const showWelcome = computed(
        () => !welcomeDismissed.value && !showSkipReminder.value
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

    function formatRelativeDay(iso: string): string {
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        const target = new Date(iso);
        target.setHours(0, 0, 0, 0);
        const diff = Math.round((target.getTime() - today.getTime()) / 86_400_000);
        if (diff === 0) return 'Today';
        if (diff === 1) return 'Tomorrow';
        if (diff > 1 && diff < 7) {
            return target.toLocaleDateString(undefined, { weekday: 'long' });
        }
        return target.toLocaleDateString();
    }

    function goTo(path: string) {
        void router.push(path);
    }

    // ── Needs your attention (D6 two-section card) ───────────────────────
    // Top section: a by-kind summary; bottom: a peek at the most-urgent few.
    // The alerts control page (/alerts) is the canonical surface for the rest.
    const SEVERITY_RANK: Record<AlertSeverity, number> = { high: 0, medium: 1, low: 2 };
    const PEEK_LIMIT = 3;

    const topAlerts = computed(() =>
        [...alerts.value].sort(
            (a, b) => (SEVERITY_RANK[a.severity] ?? 9) - (SEVERITY_RANK[b.severity] ?? 9)
        )
    );

    // By-kind breakdown of the active alerts for the summary chips. This is
    // display grouping of the *already-fetched* alerts list (not a new
    // cross-entity aggregate), so it stays client-side — R-003 note. The
    // per-kind label/icon come from the shared alert model (one source).
    type AlertKindGroup = { kind: AlertKind; count: number; severity: AlertSeverity };
    const alertKindSummary = computed<AlertKindGroup[]>(() => {
        const groups = new Map<AlertKind, AlertKindGroup>();
        for (const a of alerts.value) {
            const g = groups.get(a.kind);
            if (g) {
                g.count += 1;
                if (SEVERITY_RANK[a.severity] < SEVERITY_RANK[g.severity]) g.severity = a.severity;
            } else {
                groups.set(a.kind, { kind: a.kind, count: 1, severity: a.severity });
            }
        }
        return [...groups.values()].sort(
            (x, y) => SEVERITY_RANK[x.severity] - SEVERITY_RANK[y.severity] || y.count - x.count
        );
    });

    // The peek rows (most-urgent first), each with its precomputed deep-link
    // target so the template can render a real <router-link> (a11y).
    const peekAlerts = computed(() =>
        topAlerts.value.slice(0, PEEK_LIMIT).map((alert) => ({
            alert,
            link: alertLinkFor(alert),
        }))
    );

    async function loadAlerts() {
        try {
            const result = await alertApi.getAlertsAsync();
            alerts.value = result.items;
        } catch {
            // Non-fatal — the card just hides itself when empty.
            alerts.value = [];
        }
    }

    async function applyAlertAction(alert: Alert, action: AlertAction) {
        try {
            await alertApi.applyActionAsync(alert.alert_id, action);
            await Promise.all([loadAlerts(), loadSummary()]);
        } catch {
            // Best-effort; the alerts panel page is the canonical surface
            // for retries.
        }
    }

    // ── Cookable tonight ────────────────────────────────────────────────
    // Cookability is server-owned (§3.2): recipes carry `cookable`. A recipe
    // with no ingredients is `cookable` server-side, but "cook tonight" should
    // only suggest real recipes, so require at least one ingredient.
    // Favourites bubble up first within the cookable subset so your usuals
    // show up before the long tail.
    function recipeIsCookable(recipe: Recipe): boolean {
        return recipe.cookable && recipe.ingredients.length > 0;
    }

    const cookableTonight = computed<Recipe[]>(() => {
        const cookable = recipes.value.filter(recipeIsCookable);
        cookable.sort((a, b) => {
            // Favourites win the tiebreak; then last-made-recent (so you
            // rotate your repertoire rather than seeing the same three
            // recipes every night); then alphabetical.
            if (a.is_favourite !== b.is_favourite) return a.is_favourite ? -1 : 1;
            const al = a.last_made_on ?? '';
            const bl = b.last_made_on ?? '';
            if (al !== bl) return bl.localeCompare(al);
            return a.name.localeCompare(b.name);
        });
        return cookable.slice(0, 3);
    });

    function recipeTotalTime(recipe: Recipe): number | null {
        if (recipe.prep_time_minutes === null && recipe.cook_time_minutes === null) {
            return null;
        }
        return (recipe.prep_time_minutes ?? 0) + (recipe.cook_time_minutes ?? 0);
    }

    // ── Best deals on your saved products ────────────────────────────────
    // Ranked + sliced server-side (state-ownership §8.2) — we fetch only the
    // top 3 instead of downloading every product to sort in the browser. The
    // `% off` badge still uses the shared `discountPercent` helper (display).
    async function loadBestDeals() {
        try {
            bestDeals.value = await productApi.getBestDealsAsync(3);
        } catch {
            bestDeals.value = [];
        }
    }

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
            primaryListDetail.value = null;
            return;
        }
        try {
            primaryListDetail.value = await shoppingListApi.getDetailAsync(id);
        } catch {
            primaryListDetail.value = null;
        }
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
            loadError.value = 'Could not load the dashboard. Try refreshing.';

            console.warn('dashboard summary failed', err);
        } finally {
            loading.value = false;
        }
    }

    async function loadBudget() {
        try {
            budgetStatus.value = await budgetApi.getStatusAsync();
        } catch {
            // The card is non-essential — if the backend is too old to
            // serve /api/budget/status, just hide the card.
            budgetStatus.value = null;
        }
    }

    async function loadWasteRescue() {
        try {
            wasteRescue.value = await wasteApi.getRescueAsync(7);
        } catch {
            wasteRescue.value = null;
        }
    }

    // ── Money zone loaders (Phase 4) ─────────────────────────────────────
    // Guarded on `moneyEnabled` — the cards are gated on it, so there's no point
    // fetching dollar reports when money is off. Each is non-fatal (the card
    // shows its empty state on error). The reports endpoints already aggregate
    // server-side (state-ownership) — we just render.
    const RANGE_LABEL: Record<ReportRange, string> = {
        '30d': 'last 30 days',
        '90d': 'last 90 days',
        '1y': 'last year',
        'all': 'all time',
    };
    const savingsRangeLabel = computed(() => RANGE_LABEL[savingsRange.value]);
    // The savings card's range toggle (Month / Year / All).
    const SAVINGS_RANGES: { value: ReportRange; label: string }[] = [
        { value: '30d', label: 'Month' },
        { value: '1y', label: 'Year' },
        { value: 'all', label: 'All' },
    ];

    async function loadSavings() {
        if (!moneyEnabled.value) { savings.value = null; return; }
        try {
            savings.value = await reportsApi.getSavingsCapturedAsync(savingsRange.value);
        } catch {
            savings.value = null;
        }
    }
    // Re-fetch when the user flips the savings range toggle.
    watch(savingsRange, () => { void loadSavings(); });

    async function loadSpendByStore() {
        if (!moneyEnabled.value) { spendByStore.value = null; return; }
        try {
            spendByStore.value = await reportsApi.getSpendByStoreAsync('30d');
        } catch {
            spendByStore.value = null;
        }
    }

    async function loadPantryValue() {
        if (!moneyEnabled.value) { pantryValue.value = null; return; }
        try {
            pantryValue.value = await reportsApi.getStockValueAsync('90d');
        } catch {
            pantryValue.value = null;
        }
    }

    // ── Restock radar (Phase 5) ──────────────────────────────────────────
    async function loadKeepsRunningOut() {
        try {
            keepsRunningOut.value = await reportsApi.getKeepsRunningOutAsync(5);
        } catch {
            keepsRunningOut.value = null;
        }
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
        try {
            upcoming.value = await alertApi.getUpcomingAsync(14);
        } catch {
            upcoming.value = null;
        }
    }

    type CalendarCell = {
        iso: string;
        dayNum: number;
        isToday: boolean;
        hasExpiry: boolean;
        hasShopping: boolean;
        hasMeal: boolean;
    };
    function parseLocalIso(iso: string): Date {
        const p = iso.split('-');
        return new Date(Number(p[0]), Number(p[1]) - 1, Number(p[2]));
    }
    const calendarCells = computed<CalendarCell[]>(() => {
        const u = upcoming.value;
        if (!u) return [];
        const byDate = new Map(u.dates.map((d) => [d.date, d]));
        const todayIso = isoOf(new Date());
        const start = parseLocalIso(u.start);
        const cells: CalendarCell[] = [];
        for (let i = 0; i < u.days; i++) {
            const d = new Date(start);
            d.setDate(start.getDate() + i);
            const iso = isoOf(d);
            const day = byDate.get(iso);
            cells.push({
                iso,
                dayNum: d.getDate(),
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
    // Lazy-load the calendar's data the first time the user enables it.
    watch(
        () => isCardVisible('calendar'),
        (visible) => {
            if (visible && !upcoming.value) void loadUpcoming();
        }
    );

    // Top stores by spend for the spend-trend card (display slice of the
    // server-aggregated rows).
    const topSpendStores = computed(() => spendByStore.value?.rows.slice(0, 3) ?? []);
    const totalSpend = computed(() =>
        (spendByStore.value?.rows ?? []).reduce((sum, r) => sum + r.spend, 0)
    );

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
            loadBestDeals(),
            loadBudget(),
            loadWasteRescue(),
            loadSavings(),
            loadSpendByStore(),
            loadPantryValue(),
            loadKeepsRunningOut(),
            // Calendar is opt-in — only fetch the (heavier) aggregation when
            // the card is actually shown (R-016 lazy hydration).
            isCardVisible('calendar') ? loadUpcoming() : Promise.resolve(),
            suggestionStore.refreshAsync(),
            recipes.value.length === 0
                ? recipeStore.getRecipesAsync()
                : Promise.resolve(),
            shoppingListStore.refreshAsync(),
        ]);
        // Primary list detail depends on the shoppingListStore refresh
        // having landed, so it runs after.
        await loadPrimaryListDetail();
    }

    onMounted(loadAll);
</script>

<style scoped lang="scss">
    /* ───── Palette ─────────────────────────────────────────────────────
       Warm, food-y, deliberately un-corporate. Scoped to this page so it
       doesn't leak. The variables are exported as CSS custom properties on
       the root .dora-dash element so every descendant can reference them.
    */
    .dora-dash {
        /* Dashboard reads the active theme's signature hero gradient as
           its page background — this is the "special touch" per theme.
           Every other surface reference here goes through the global
           tokens so the dashboard reskins automatically with the rest
           of the app. */
        --c-bg-1: var(--surface-elevated);
        --c-bg-2: var(--surface-sunken);
        --c-surface: var(--surface-component);
        --c-ink: var(--text-primary);
        --c-ink-mute: var(--text-secondary);
        --c-line: var(--border-default);
        --c-accent: var(--brand-primary);
        --c-accent-soft: var(--brand-primary-soft);
        --c-ok: var(--semantic-positive);
        --c-ok-soft: var(--semantic-positive-soft);
        --c-warn: var(--semantic-warning);
        --c-warn-soft: var(--semantic-warning-soft);
        --c-bad: var(--semantic-negative);
        --c-bad-soft: var(--semantic-negative-soft);
        --c-pink-soft: var(--brand-secondary-soft);

        min-height: 100%;
        padding: 24px 24px 96px;
        background: var(--hero-gradient);
        color: var(--c-ink);
    }

    /* ───── Hero ─────────────────────────────────────────────────────── */
    .dora-hero {
        display: flex;
        align-items: center;
        gap: 16px;
        padding: 24px;
        margin-bottom: 24px;
        background: var(--c-surface);
        border: 1px solid var(--c-line);
        border-radius: 18px;
        box-shadow: var(--elevation-card);
    }
    .dora-hero-mascot {
        border-radius: 14px;
        background: var(--c-accent-soft);
        padding: 2px;
        flex-shrink: 0;
    }
    .dora-hero-text {
        min-width: 0;
    }
    .dora-hero-greeting {
        font-size: 1.5rem;
        font-weight: 600;
        line-height: 1.2;
    }
    .dora-hero-line {
        margin-top: 2px;
        color: var(--c-ink-mute);
        font-size: 0.95rem;
    }
    .dora-hero-actions {
        display: flex;
        align-items: center;
        gap: 4px;
    }

    /* Phase 5 quick-action bar — sits between the hero and the cards. */
    .dora-quick-actions {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-bottom: 16px;
    }

    /* ───── Cards ────────────────────────────────────────────────────── */
    .dora-cards {
        animation: dora-fade-up 0.4s ease-out both;
    }
    /* Zone band header — a full-width flex item; CSS `order` (set inline)
       places it just before its zone's cards, and being full-width it forces
       the cards onto the next line so each zone reads as a labelled band. */
    .dora-zone-label {
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: var(--c-ink-mute);
        opacity: 0.8;
        margin-top: 6px;
    }
    /* Zone sub-header inside the Cards toggle menu. NB: q-menu teleports to
       <body>, outside `.dora-dash` — so use the GLOBAL `--brand-primary` token
       here, not the page-local `--c-accent` alias (which wouldn't resolve). */
    .dora-cards-menu-zone {
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--brand-primary);
        opacity: 0.9;
        padding-top: 8px;
    }
    /* The card shell (`.dora-card`, head, icon, title, action, link, clickable
       + hover) now lives in `components/dashboard/DashboardCard.vue` (R-001
       de-monolith). Card BODY styles stay below — slotted content keeps this
       page's scope. */

    /* ───── Stat grid (recipes / meals / shopping / products) ────────── */
    .dora-stat-grid {
        display: flex;
        gap: 12px;
    }
    .dora-stat {
        flex: 1 1 0;
        min-width: 0;
        padding: 14px 16px;
        background: var(--surface-elevated);
        border-radius: 12px;
    }
    .dora-stat-num {
        font-size: 1.9rem;
        font-weight: 700;
        line-height: 1;
        letter-spacing: -0.02em;
        color: var(--c-ink);
        display: flex;
        align-items: center;
    }
    .dora-stat-label {
        margin-top: 6px;
        font-size: 0.78rem;
        color: var(--c-ink-mute);
        letter-spacing: 0.01em;
        text-transform: lowercase;
    }
    .dora-stat-ok {
        background: var(--c-ok-soft);
    }
    .dora-stat-ok .dora-stat-num {
        color: var(--semantic-positive);
    }
    .dora-stat-accent {
        background: var(--c-pink-soft);
    }
    .dora-stat-accent .dora-stat-num {
        color: var(--brand-secondary);
    }

    /* ───── Stock donut ──────────────────────────────────────────────── */
    .dora-stock-body {
        display: flex;
        align-items: center;
        gap: 18px;
    }
    .dora-donut {
        width: 132px;
        height: 132px;
        flex-shrink: 0;
        transform: rotate(-90deg);
    }
    .dora-donut-track {
        fill: none;
        stroke: var(--surface-sunken);
        stroke-width: 4;
    }
    .dora-donut-seg {
        transition: stroke-dasharray 0.6s ease, stroke-dashoffset 0.6s ease;
    }
    /* SVG text inherits the parent's -90deg rotation; rotate the text nodes
       back so the centre label reads normally. */
    .dora-donut-big,
    .dora-donut-sub {
        transform: rotate(90deg);
        transform-origin: 18px 18px;
    }
    .dora-donut-big {
        font-size: 7.5px;
        font-weight: 700;
        fill: var(--c-ink);
    }
    .dora-donut-sub {
        font-size: 3px;
        fill: var(--c-ink-mute);
        text-transform: lowercase;
        letter-spacing: 0.05em;
    }
    .dora-legend {
        list-style: none;
        margin: 0;
        padding: 0;
        font-size: 0.85rem;
    }
    .dora-legend li {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 4px 0;
    }
    .dora-dot {
        width: 9px;
        height: 9px;
        border-radius: 999px;
        flex-shrink: 0;
    }
    .dora-dot-ok { background: var(--c-ok); }
    .dora-dot-warn { background: var(--c-warn); }
    .dora-dot-bad { background: var(--c-bad); }
    .dora-legend-num {
        font-weight: 600;
        min-width: 1.4em;
        text-align: right;
    }
    .dora-legend-label {
        color: var(--c-ink-mute);
    }

    /* ───── Meal plan card ───────────────────────────────────────────── */
    .dora-next-up {
        padding: 14px 16px;
        background: var(--c-accent-soft);
        border-radius: 12px;
        margin-bottom: 16px;
    }
    .dora-next-up-label {
        font-size: 0.72rem;
        color: var(--c-ink-mute);
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }
    .dora-next-up-meal {
        margin-top: 2px;
        font-size: 1.25rem;
        font-weight: 700;
        letter-spacing: -0.01em;
        color: var(--brand-secondary);
    }
    .dora-next-up-meta {
        margin-top: 2px;
        font-size: 0.85rem;
        color: var(--c-ink-mute);
    }
    .dora-empty {
        padding: 14px 16px;
        margin-bottom: 16px;
        color: var(--c-ink-mute);
        font-size: 0.9rem;
        background: var(--surface-elevated);
        border-radius: 12px;
    }
    /* P2-05 budget card — visual hierarchy matches the existing P12
       cards: a single big number, a muted denominator, and a small
       remainder chip on the right. */
    .dora-budget-body {
        padding: 4px 4px 8px;
    }
    .dora-budget-headline {
        display: flex;
        align-items: baseline;
        gap: 8px;
        flex-wrap: wrap;
    }
    .dora-budget-spent {
        font-size: 1.6rem;
        font-weight: 700;
    }
    .dora-budget-of {
        font-size: 0.95rem;
        color: var(--c-ink-mute);
    }
    .dora-budget-remaining {
        margin-left: auto;
        font-size: 0.85rem;
        font-weight: 600;
    }

    /* ───── Money zone widgets (Phase 4) ─────────────────────────────── */
    /* Savings card — range toggle + headline amount. */
    .dora-range-toggle {
        display: inline-flex;
        gap: 2px;
        background: var(--surface-elevated);
        border-radius: 999px;
        padding: 2px;
    }
    .dora-range-chip {
        border: none;
        background: transparent;
        color: var(--c-ink-mute);
        font-size: 0.72rem;
        font-weight: 600;
        padding: 3px 9px;
        border-radius: 999px;
        cursor: pointer;
        transition: background 0.15s ease, color 0.15s ease;
    }
    .dora-range-chip.is-active {
        background: var(--c-accent);
        color: var(--text-inverse);
    }
    .dora-savings-amount {
        font-size: 2.2rem;
        font-weight: 700;
        line-height: 1.05;
        letter-spacing: -0.02em;
        color: var(--c-ok);
    }
    .dora-savings-sub {
        margin-top: 2px;
        font-size: 0.85rem;
        font-weight: 600;
        color: var(--c-ink-mute);
    }
    .dora-savings-spent {
        margin-top: 6px;
        font-size: 0.82rem;
        color: var(--c-ink-mute);
    }
    /* Spend-by-store card. */
    .dora-spend-list {
        list-style: none;
        margin: 0;
        padding: 0;
        display: flex;
        flex-direction: column;
        gap: 6px;
    }
    .dora-spend-row {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 6px 10px;
        background: var(--surface-elevated);
        border-radius: 10px;
    }
    .dora-spend-store {
        flex: 1;
        min-width: 0;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        font-weight: 600;
    }
    .dora-spend-amt {
        font-weight: 700;
        white-space: nowrap;
    }
    .dora-spend-total {
        margin-top: 8px;
        font-size: 0.82rem;
        font-weight: 600;
        color: var(--c-ink-mute);
        text-align: right;
    }
    /* Pantry-value card. */
    .dora-pantry-delta {
        margin-top: 4px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .dora-pantry-delta.is-up {
        color: var(--c-ok);
    }
    .dora-pantry-delta.is-down {
        color: var(--c-bad);
    }

    /* ───── Fortnight calendar (Phase 6 / D7) ────────────────────────── */
    .dora-cal-legend {
        display: flex;
        gap: 12px;
        font-size: 0.72rem;
        color: var(--c-ink-mute);
    }
    .dora-cal-leg {
        display: inline-flex;
        align-items: center;
        gap: 4px;
    }
    .dora-cal-grid {
        display: grid;
        grid-template-columns: repeat(7, minmax(0, 1fr));
        gap: 6px;
    }
    .dora-cal-cell {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 4px;
        min-height: 56px;
        padding: 8px 4px 6px;
        border: 1px solid var(--c-line);
        border-radius: 10px;
        background: var(--surface-elevated);
        color: var(--c-ink);
        cursor: pointer;
        transition: border-color 0.15s ease, background 0.15s ease, transform 0.15s ease;
    }
    .dora-cal-cell.has-events:hover {
        border-color: var(--border-strong);
        transform: translateY(-1px);
    }
    .dora-cal-cell.is-today {
        border-color: var(--c-accent);
        font-weight: 700;
    }
    .dora-cal-cell.is-selected {
        background: var(--c-accent-soft);
        border-color: var(--c-accent);
    }
    .dora-cal-num {
        font-size: 0.95rem;
        line-height: 1;
    }
    .dora-cal-dots {
        display: flex;
        gap: 3px;
        min-height: 6px;
    }
    .dora-cal-dot {
        width: 6px;
        height: 6px;
        border-radius: 999px;
        flex-shrink: 0;
    }
    .dora-cal-dot.dot-meal {
        background: var(--c-ok);
    }
    .dora-cal-dot.dot-expiry {
        background: var(--c-bad);
    }
    .dora-cal-dot.dot-shopping {
        background: var(--c-accent);
    }
    .dora-cal-hint {
        margin-top: 12px;
        font-size: 0.82rem;
        color: var(--c-ink-mute);
    }
    .dora-cal-detail {
        margin-top: 14px;
        padding: 12px 14px;
        background: var(--surface-elevated);
        border-radius: 12px;
    }
    .dora-cal-detail-date {
        font-weight: 700;
        margin-bottom: 8px;
    }
    .dora-cal-group {
        margin-top: 8px;
    }
    .dora-cal-group-label {
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: var(--c-ink-mute);
        margin-bottom: 2px;
    }
    .dora-cal-item {
        display: block;
        color: var(--c-ink);
        text-decoration: none;
        font-size: 0.9rem;
        padding: 2px 0;
    }
    .dora-cal-item:hover {
        text-decoration: underline;
    }
    .dora-cal-slot {
        color: var(--c-ink-mute);
        font-size: 0.82rem;
    }
    /* P2-04 — suggestion rows on the dashboard card. Severity drives
       the left border; the rest of the visual weight is on the title
       and the primary action button. */
    .dora-suggest-list {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }
    .dora-suggest-row {
        padding: 8px 10px;
        border-radius: 10px;
        background: var(--surface-elevated);
        border-left: 3px solid var(--c-accent);
    }
    .dora-suggest-row.dora-suggest-high { border-left-color: var(--semantic-negative); }
    .dora-suggest-row.dora-suggest-medium { border-left-color: var(--semantic-warning); }
    .dora-suggest-row.dora-suggest-low { border-left-color: var(--c-accent); }
    .dora-suggest-title {
        font-weight: 600;
        font-size: 0.95rem;
    }
    .dora-suggest-body {
        font-size: 0.85rem;
        color: var(--c-ink-mute);
        margin-top: 2px;
    }
    .dora-empty-cta {
        color: var(--c-accent);
        font-weight: 600;
    }
    .dora-strip {
        display: grid;
        grid-template-columns: repeat(7, minmax(0, 1fr));
        gap: 6px;
    }
    .dora-strip-day {
        position: relative;
        padding: 10px 6px 8px;
        border-radius: 10px;
        background: var(--surface-elevated);
        text-align: center;
        transition: background 0.15s ease, transform 0.15s ease;
        min-height: 76px;
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    .dora-strip-day.has-meals {
        background: var(--c-accent-soft);
    }
    .dora-strip-day.is-today {
        background: var(--c-ink);
        color: var(--text-inverse);
    }
    .dora-strip-day.is-today.has-meals {
        background: linear-gradient(180deg, var(--c-ink) 0%, var(--brand-secondary) 100%);
    }
    .dora-strip-dow {
        font-size: 0.7rem;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        opacity: 0.7;
    }
    .dora-strip-num {
        font-size: 1.3rem;
        font-weight: 700;
        line-height: 1.1;
        margin-top: 2px;
    }
    .dora-strip-meals {
        margin-top: auto;
        display: flex;
        align-items: center;
        gap: 3px;
        min-height: 10px;
    }
    .dora-strip-pip {
        width: 6px;
        height: 6px;
        border-radius: 999px;
        background: var(--c-accent);
    }
    .dora-strip-more {
        font-size: 0.65rem;
        font-weight: 600;
        opacity: 0.7;
    }


    /* Needs your attention — D6 two-section card */
    /* Top: by-kind summary chips. */
    .dora-alert-summary {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        margin-bottom: 12px;
    }
    .dora-alert-chip {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        padding: 4px 10px;
        border-radius: 999px;
        background: var(--surface-elevated);
        border: 1px solid var(--c-line);
        text-decoration: none;
        color: var(--c-ink);
        font-size: 0.8rem;
        transition: border-color 0.15s ease, background 0.15s ease;
    }
    .dora-alert-chip:hover {
        border-color: var(--border-strong);
        background: var(--c-accent-soft);
    }
    .dora-alert-chip-num {
        font-weight: 700;
    }
    .dora-alert-chip-label {
        color: var(--c-ink-mute);
    }
    /* Bottom: peek + "see all". */
    .dora-alert-seeall {
        display: inline-block;
        margin-top: 12px;
        font-size: 0.85rem;
        font-weight: 600;
        color: var(--c-accent);
        text-decoration: none;
    }
    .dora-alert-seeall:hover {
        text-decoration: underline;
    }
    .dora-attn-list {
        list-style: none;
        margin: 0;
        padding: 0;
        display: flex;
        flex-direction: column;
        gap: 8px;
    }
    .dora-attn-row {
        display: grid;
        grid-template-columns: 6px 20px minmax(0, auto) 1fr auto;
        align-items: center;
        gap: 8px;
        padding: 8px 10px;
        background: var(--surface-elevated);
        border-radius: 10px;
    }
    .dora-attn-dot {
        width: 6px;
        height: 100%;
        min-height: 26px;
        border-radius: 3px;
    }
    .dora-attn-dot-high { background: var(--c-bad); }
    .dora-attn-dot-medium { background: var(--c-warn); }
    .dora-attn-dot-low { background: var(--c-accent); }
    .dora-attn-name {
        font-weight: 600;
        color: var(--c-ink);
        text-decoration: none;
        max-width: 220px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    .dora-attn-name:hover {
        text-decoration: underline;
    }
    .dora-attn-msg {
        color: var(--c-ink-mute);
        font-size: 0.85rem;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    /* When the message itself is the deep-link (non-stock nudges) — strip the
       default anchor chrome, reveal an underline on hover. */
    .dora-attn-msg-link {
        text-decoration: none;
    }
    .dora-attn-msg-link:hover {
        text-decoration: underline;
    }
    .dora-attn-actions {
        display: flex;
        gap: 2px;
        flex-shrink: 0;
    }

    /* Primary shopping list */
    .dora-primary-list-name {
        font-size: 1.05rem;
        font-weight: 600;
        color: var(--c-ink);
    }

    /* Cookable tonight */
    .dora-cook-list {
        list-style: none;
        margin: 0;
        padding: 0;
        display: flex;
        flex-direction: column;
        gap: 6px;
    }
    .dora-cook-row {
        display: grid;
        grid-template-columns: minmax(0, 1fr) auto auto;
        align-items: center;
        gap: 10px;
        padding: 8px 10px;
        background: var(--surface-elevated);
        border-radius: 10px;
    }
    .dora-cook-name {
        color: var(--c-ink);
        text-decoration: none;
        font-weight: 600;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    .dora-cook-name:hover {
        text-decoration: underline;
    }
    .dora-cook-meta {
        font-size: 0.8rem;
        color: var(--c-ink-mute);
        white-space: nowrap;
    }

    /* Best deals */
    .dora-deal-list {
        list-style: none;
        margin: 0;
        padding: 0;
        display: flex;
        flex-direction: column;
        gap: 8px;
    }
    .dora-deal-row {
        display: grid;
        grid-template-columns: 36px minmax(0, 1fr) auto auto;
        align-items: center;
        gap: 10px;
        padding: 8px 10px;
        background: var(--surface-elevated);
        border-radius: 10px;
    }
    .dora-deal-img img {
        object-fit: contain;
        max-width: 100%;
        max-height: 100%;
    }
    .dora-deal-text {
        min-width: 0;
    }
    .dora-deal-name {
        font-weight: 600;
        color: var(--c-ink);
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    .dora-deal-meta {
        font-size: 0.78rem;
        color: var(--c-ink-mute);
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    .dora-deal-price {
        text-align: right;
        white-space: nowrap;
    }
    .dora-deal-now {
        font-weight: 700;
        color: var(--c-ink);
    }
    .dora-deal-was {
        font-size: 0.78rem;
        color: var(--c-ink-mute);
        text-decoration: line-through;
        margin-left: 4px;
    }
    .dora-deal-badge {
        font-weight: 700;
    }

    @media (max-width: 600px) {
        .dora-attn-row,
        .dora-deal-row {
            grid-template-columns: auto minmax(0, 1fr) auto;
            grid-template-rows: auto auto;
        }
        .dora-attn-msg,
        .dora-attn-actions {
            grid-column: 1 / -1;
        }
        .dora-deal-price,
        .dora-deal-badge {
            grid-column: 1 / -1;
            text-align: left;
        }
    }

    /* ───── Dora welcome / message banner (D1) ───────────────────────────
       Inline, top-of-dashboard greeting that replaced the old fixed
       bottom-right tip bubble — keeps the warm "Dora says" treatment. The
       `--warn` modifier is the skip-reminder variant. */
    .dora-welcome {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 12px 12px 12px 14px;
        background: var(--c-surface);
        border: 1px solid var(--c-line);
        border-left: 4px solid var(--c-accent);
        border-radius: 14px;
        box-shadow: var(--elevation-card);
    }
    .dora-welcome--warn {
        border-left-color: var(--c-warn);
        background: var(--c-warn-soft);
    }
    .dora-welcome-mascot {
        border-radius: 10px;
        background: var(--c-accent-soft);
        padding: 1px;
    }
    .dora-welcome-body {
        min-width: 0;
        flex: 1;
    }
    .dora-welcome-line {
        font-size: 0.95rem;
        line-height: 1.35;
        color: var(--c-ink);
    }
    .dora-welcome-line strong {
        color: var(--c-accent);
        font-weight: 700;
    }
    .dora-welcome--warn .dora-welcome-line strong {
        color: var(--c-warn);
    }
    .dora-welcome-hint {
        margin-top: 3px;
        font-size: 0.82rem;
        color: var(--c-ink-mute);
    }
    .dora-welcome-actions {
        margin-top: 6px;
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
    }

    /* Positive ("all clear") empty state — softer + green-tinted so a calm
       dashboard reads as reassuring rather than broken (R-014). */
    .dora-empty-ok {
        display: flex;
        align-items: center;
        background: var(--c-ok-soft);
        color: var(--c-ink-mute);
    }
    .dora-empty-ok .q-icon {
        color: var(--c-ok);
    }

    /* Footer link on the primary-list card ("+N other lists →"). */
    .dora-card-footer-link {
        display: inline-block;
        margin-top: 12px;
        font-size: 0.8rem;
        font-weight: 600;
        color: var(--c-accent);
        text-decoration: none;
    }
    .dora-card-footer-link:hover {
        text-decoration: underline;
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
           DashboardCard's own reduced-motion rule. */
        .dora-cards,
        .dora-donut-seg,
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
            padding: 16px 16px 96px;
        }
        /* Phase 7 mobile pass. The zone grid already stacks (cards are
           col-12 below sm); these tidy the new Phase 4/5 bits for touch. */
        /* Quick-action buttons span the row so they're easy thumb targets. */
        .dora-quick-actions {
            gap: 8px;
        }
        .dora-quick-actions :deep(.q-btn) {
            flex: 1 1 auto;
        }
        /* Give the savings range-toggle chips a comfortable tap height. */
        .dora-range-chip {
            padding: 6px 12px;
        }
        /* The summary chips wrap freely; keep them from getting too cramped. */
        .dora-alert-chip {
            padding: 6px 12px;
        }
    }
</style>
