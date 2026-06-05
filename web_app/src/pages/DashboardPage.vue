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
                <q-btn
                    flat
                    round
                    dense
                    :icon="ICONS.refresh"
                    :loading="loading"
                    @click="loadAll"
                >
                    <q-tooltip>Refresh dashboard</q-tooltip>
                </q-btn>
                <q-btn flat dense no-caps :icon="ICONS.tune" label="Cards">
                    <q-menu anchor="bottom right" self="top right" transition-show="jump-down" transition-hide="jump-up">
                        <q-list dense style="min-width: 240px">
                            <q-item-label header>Show on dashboard</q-item-label>
                            <q-item
                                v-for="card in CARD_DEFS"
                                :key="card.id"
                                clickable
                                v-ripple
                                @click="toggleCard(card.id)"
                            >
                                <q-item-section avatar>
                                    <q-icon :name="card.icon" />
                                </q-item-section>
                                <q-item-section>{{ card.label }}</q-item-section>
                                <q-item-section side>
                                    <q-toggle
                                        :model-value="isCardVisible(card.id)"
                                        @update:model-value="toggleCard(card.id)"
                                    />
                                </q-item-section>
                            </q-item>
                        </q-list>
                    </q-menu>
                </q-btn>
            </div>
        </section>

        <q-banner v-if="loadError" class="dora-bg-negative-soft text-negative q-mb-md" dense rounded>
            {{ loadError }}
        </q-banner>

        <!-- F1: 24h skip-reminder. Shown when the user pressed
             "Skip everything" in the wizard; gentle nudge with a Continue
             link, plus a dismiss that suppresses for the rest of the
             window. After 24h the skip flag is treated as expired. -->
        <q-banner
            v-if="showSkipReminder"
            class="dora-bg-warning-soft dora-text-primary q-mb-md skip-reminder"
            rounded
            dense
        >
            <template #avatar>
                <q-icon :name="ICONS.auto_awesome" size="20px" color="warning" />
            </template>
            <strong>Welcome —</strong>
            you skipped the setup wizard. Finish in two minutes whenever
            you're ready.
            <template #action>
                <q-btn flat no-caps :icon="ICONS.east" label="Continue" :loading="continuingOnboarding" @click="onContinueOnboarding" />
                <q-btn flat no-caps :icon="ICONS.close" label="Hide" @click="dismissSkipReminder" />
            </template>
        </q-banner>

        <FadeTransition mode="out-in">
        <div v-if="loading && !summary" key="dash-loading" class="row justify-center q-pa-xl">
            <q-spinner size="48px" color="primary" />
        </div>

        <div v-else-if="summary" key="dash-content" class="row q-col-gutter-md dora-cards">
            <!-- ───── Needs your attention (P12) ─────────────────────────── -->
            <div
                v-if="isCardVisible('attention') && topAlerts.length > 0"
                class="col-12 col-lg-6"
            >
                <article class="dora-card">
                    <header class="dora-card-head">
                        <q-icon :name="ICONS.notifications_active" size="22px" class="dora-card-icon" />
                        <h3 class="dora-card-title">Needs your attention</h3>
                        <a
                            class="dora-card-action dora-card-link"
                            href="#"
                            @click.prevent="goTo('/alerts')"
                        >
                            All {{ alerts.length }} →
                        </a>
                    </header>
                    <ul class="dora-attn-list">
                        <li
                            v-for="alert in topAlerts"
                            :key="alert.alert_id"
                            class="dora-attn-row"
                        >
                            <span
                                class="dora-attn-dot"
                                :class="`dora-attn-dot-${alert.severity}`"
                            />
                            <q-icon
                                :name="alertIconFor(alert.kind)"
                                :color="alertColorFor(alert.severity)"
                                size="18px"
                            />
                            <a
                                href="#"
                                class="dora-attn-name"
                                @click.prevent="goTo(`/stock/${alert.stock_item_id}`)"
                            >
                                {{ alert.stock_item_name }}
                            </a>
                            <span class="dora-attn-msg">{{ alert.message }}</span>
                            <span class="dora-attn-actions">
                                <q-btn
                                    v-for="a in alertActionsFor(alert.kind)"
                                    :key="a.action"
                                    flat
                                    dense
                                    size="sm"
                                    no-caps
                                    :icon="a.icon"
                                    :label="a.label"
                                    @click="applyAlertAction(alert, a.action)"
                                />
                            </span>
                        </li>
                    </ul>
                </article>
            </div>

            <!-- ───── Primary shopping list (P12) ─────────────────────────── -->
            <div
                v-if="isCardVisible('primary_list') && primarySummary"
                class="col-12 col-sm-6 col-lg-6"
            >
                <article
                    class="dora-card dora-card-clickable"
                    @click="goTo(`/shopping-lists/${primarySummary.shopping_list_id}`)"
                >
                    <header class="dora-card-head">
                        <q-icon :name="ICONS.shopping_cart" size="22px" class="dora-card-icon" />
                        <h3 class="dora-card-title">Primary shopping list</h3>
                        <span class="dora-card-action">Open list →</span>
                    </header>
                    <div class="dora-primary-list-name">
                        {{ primarySummary.name }}
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
                </article>
            </div>
            <div
                v-else-if="isCardVisible('primary_list') && !primarySummary"
                class="col-12 col-sm-6 col-lg-6"
            >
                <article class="dora-card dora-card-clickable" @click="goTo('/shopping-lists')">
                    <header class="dora-card-head">
                        <q-icon :name="ICONS.shopping_cart" size="22px" class="dora-card-icon" />
                        <h3 class="dora-card-title">Primary shopping list</h3>
                        <span class="dora-card-action">Pick one →</span>
                    </header>
                    <div class="dora-empty">
                        No primary set — the cart button needs one to one-tap items in.
                    </div>
                </article>
            </div>

            <!-- ───── Grocery budget (P2-05) ──────────────────────────────── -->
            <div
                v-if="isCardVisible('budget') && budgetStatus"
                class="col-12 col-sm-6 col-lg-6"
            >
                <article
                    class="dora-card dora-card-clickable"
                    @click="goTo('/settings/preferences')"
                >
                    <header class="dora-card-head">
                        <q-icon :name="ICONS.savings" size="22px" class="dora-card-icon" />
                        <h3 class="dora-card-title">
                            {{ budgetStatus.enabled ? 'Grocery budget' : 'Grocery spend this ' + budgetStatus.period.replace('ly', '') }}
                        </h3>
                        <span class="dora-card-action">
                            {{ budgetStatus.enabled ? 'Settings →' : 'Set a budget →' }}
                        </span>
                    </header>
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
                </article>
            </div>

            <!-- ───── Dora suggests (P2-04) ───────────────────────────────── -->
            <div
                v-if="isCardVisible('suggestions') && suggestionStore.count > 0"
                class="col-12 col-sm-6 col-lg-6"
            >
                <article class="dora-card">
                    <header class="dora-card-head">
                        <q-icon name="auto_awesome" size="22px" class="dora-card-icon" />
                        <h3 class="dora-card-title">Dora suggests</h3>
                        <span
                            v-if="suggestionStore.count > 2"
                            class="dora-card-action"
                        >
                            +{{ suggestionStore.count - 2 }} more in chat
                        </span>
                    </header>
                    <div class="dora-suggest-list">
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
                </article>
            </div>

            <!-- ───── Use soon (P2-06) ────────────────────────────────────── -->
            <div
                v-if="isCardVisible('use_soon') && wasteRescue && wasteRescue.items.length > 0"
                class="col-12 col-sm-6 col-lg-6"
            >
                <article
                    class="dora-card dora-card-clickable"
                    @click="goTo('/waste')"
                >
                    <header class="dora-card-head">
                        <q-icon :name="ICONS.expiry" size="22px" class="dora-card-icon" />
                        <h3 class="dora-card-title">Use soon</h3>
                        <span class="dora-card-action">Rescue ideas →</span>
                    </header>
                    <ul class="dora-attn-list">
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
                            <a
                                href="#"
                                class="dora-attn-name"
                                @click.prevent.stop="goTo(`/stock/${item.stock_item_id}`)"
                            >
                                {{ item.name }}
                            </a>
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
                        v-if="wasteRescue.recipes.length > 0"
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
                </article>
            </div>

            <!-- ───── Cookable tonight (P12) ──────────────────────────────── -->
            <div
                v-if="isCardVisible('cookable')"
                class="col-12 col-sm-6 col-lg-6"
            >
                <article class="dora-card">
                    <header class="dora-card-head">
                        <q-icon :name="ICONS.restaurant_menu" size="22px" class="dora-card-icon" />
                        <h3 class="dora-card-title">Cookable tonight</h3>
                        <a
                            class="dora-card-action dora-card-link"
                            href="#"
                            @click.prevent="goTo('/recipes?cookable=true')"
                        >
                            See more →
                        </a>
                    </header>
                    <ul v-if="cookableTonight.length > 0" class="dora-cook-list">
                        <li
                            v-for="r in cookableTonight"
                            :key="r.recipe_id"
                            class="dora-cook-row"
                        >
                            <a
                                href="#"
                                class="dora-cook-name"
                                @click.prevent="goTo(`/recipes/${r.recipe_id}`)"
                            >
                                <q-icon
                                    v-if="r.is_favourite"
                                    name="favorite"
                                    color="negative"
                                    size="14px"
                                    class="q-mr-xs"
                                />
                                {{ r.name }}
                            </a>
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
                                @click="goTo(`/recipes/${r.recipe_id}/cook`)"
                            />
                        </li>
                    </ul>
                    <div v-else class="dora-empty">
                        Nothing's fully in stock right now.
                        <a
                            class="dora-empty-cta"
                            href="#"
                            @click.prevent="goTo('/recipes')"
                        >Browse recipes →</a>
                    </div>
                </article>
            </div>

            <!-- ───── Best deals on saved products (P12) ──────────────────── -->
            <div
                v-if="isCardVisible('best_deals')"
                class="col-12 col-sm-6 col-lg-6"
            >
                <article class="dora-card">
                    <header class="dora-card-head">
                        <q-icon :name="ICONS.local_offer" size="22px" class="dora-card-icon" />
                        <h3 class="dora-card-title">Best deals on your saved products</h3>
                        <a
                            class="dora-card-action dora-card-link"
                            href="#"
                            @click.prevent="goTo('/my-products')"
                        >
                            My products →
                        </a>
                    </header>
                    <ul v-if="bestDeals.length > 0" class="dora-deal-list">
                        <li
                            v-for="p in bestDeals"
                            :key="p.product_id"
                            class="dora-deal-row"
                        >
                            <q-avatar rounded size="36px" class="dora-bg-sunken dora-deal-img">
                                <img v-if="p.image" :src="p.image" :alt="p.name" />
                                <q-icon v-else :name="ICONS.shopping_bag" size="18px" />
                            </q-avatar>
                            <div class="dora-deal-text">
                                <div class="dora-deal-name">{{ p.name }}</div>
                                <div class="dora-deal-meta">
                                    {{ p.merchant_name }}
                                    <span v-if="p.linked_stock_item_id">
                                        ·
                                        <a
                                            href="#"
                                            class="text-primary"
                                            @click.prevent="goTo(`/stock/${p.linked_stock_item_id}`)"
                                        >
                                            {{ p.linked_stock_item_name }}
                                        </a>
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
                                {{ discountPctFor(p) }}% off
                            </q-badge>
                        </li>
                    </ul>
                    <div v-else class="dora-empty">
                        Nothing on special among your saved products right now.
                        <a
                            class="dora-empty-cta"
                            href="#"
                            @click.prevent="goTo('/product-search')"
                        >Hunt for deals →</a>
                    </div>
                </article>
            </div>

            <!-- ───── Stock card (with donut) ────────────────────────────── -->
            <div v-if="isCardVisible('stock_items')" class="col-12 col-sm-6 col-lg-4">
                <article class="dora-card dora-card-clickable" @click="goTo('/stock')">
                    <header class="dora-card-head">
                        <q-icon name="inventory_2" size="22px" class="dora-card-icon" />
                        <h3 class="dora-card-title">Pantry</h3>
                        <span class="dora-card-action">View →</span>
                    </header>
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
                </article>
            </div>

            <!-- ───── Meal plan card (with 7-day strip) ──────────────────── -->
            <div v-if="isCardVisible('meal_plan')" class="col-12 col-lg-8">
                <article class="dora-card dora-card-clickable" @click="goTo('/meal-plans')">
                    <header class="dora-card-head">
                        <q-icon :name="ICONS.calendar_month" size="22px" class="dora-card-icon" />
                        <h3 class="dora-card-title">The week ahead</h3>
                        <span class="dora-card-action">Plan →</span>
                    </header>
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
                </article>
            </div>

            <!-- ───── Recipes card ──────────────────────────────────────── -->
            <div v-if="isCardVisible('recipes')" class="col-12 col-sm-6 col-lg-4">
                <article class="dora-card dora-card-clickable" @click="goTo('/recipes')">
                    <header class="dora-card-head">
                        <q-icon :name="ICONS.menu_book" size="22px" class="dora-card-icon" />
                        <h3 class="dora-card-title">Recipes</h3>
                        <span class="dora-card-action">Browse →</span>
                    </header>
                    <div class="dora-stat-grid">
                        <div class="dora-stat">
                            <div class="dora-stat-num">
                                <AnimatedNumber :value="summary.recipes.total" />
                            </div>
                            <div class="dora-stat-label">in your book</div>
                        </div>
                        <div class="dora-stat dora-stat-accent">
                            <div class="dora-stat-num">
                                <q-icon :name="ICONS.favorite" size="18px" class="q-mr-xs" />
                                <AnimatedNumber :value="summary.recipes.favourites" />
                            </div>
                            <div class="dora-stat-label">favourites</div>
                        </div>
                    </div>
                </article>
            </div>

            <!-- ───── Meals card ────────────────────────────────────────── -->
            <div v-if="isCardVisible('meals')" class="col-12 col-sm-6 col-lg-4">
                <article class="dora-card dora-card-clickable" @click="goTo('/recipes')">
                    <header class="dora-card-head">
                        <q-icon :name="ICONS.restaurant" size="22px" class="dora-card-icon" />
                        <h3 class="dora-card-title">Meals on hand</h3>
                        <span class="dora-card-action">Open →</span>
                    </header>
                    <div class="dora-stat-grid">
                        <div class="dora-stat dora-stat-ok">
                            <div class="dora-stat-num">{{ summary.meals.total_in_stock }}</div>
                            <div class="dora-stat-label">in the pool</div>
                        </div>
                        <div class="dora-stat">
                            <div class="dora-stat-num">{{ summary.meals.total_definitions }}</div>
                            <div class="dora-stat-label">recipes stocked</div>
                        </div>
                    </div>
                </article>
            </div>

            <!-- ───── Shopping lists card ───────────────────────────────── -->
            <div v-if="isCardVisible('shopping_lists')" class="col-12 col-sm-6 col-lg-4">
                <article class="dora-card">
                    <header class="dora-card-head">
                        <q-icon :name="ICONS.shopping_cart" size="22px" class="dora-card-icon" />
                        <h3 class="dora-card-title">Shopping</h3>
                    </header>
                    <div class="dora-stat-grid">
                        <div class="dora-stat">
                            <div class="dora-stat-num">{{ summary.shopping_lists.total }}</div>
                            <div class="dora-stat-label">lists</div>
                        </div>
                        <div class="dora-stat">
                            <div class="dora-stat-num">{{ summary.shopping_lists.total_items }}</div>
                            <div class="dora-stat-label">items queued</div>
                        </div>
                    </div>
                </article>
            </div>

            <!-- ───── Products card ─────────────────────────────────────── -->
            <div v-if="isCardVisible('products')" class="col-12 col-sm-6 col-lg-4">
                <article class="dora-card dora-card-clickable" @click="goTo('/product-search')">
                    <header class="dora-card-head">
                        <q-icon :name="ICONS.local_offer" size="22px" class="dora-card-icon" />
                        <h3 class="dora-card-title">Products</h3>
                        <span class="dora-card-action">Search →</span>
                    </header>
                    <div class="dora-stat-grid">
                        <div class="dora-stat">
                            <div class="dora-stat-num">{{ summary.products.total }}</div>
                            <div class="dora-stat-label">tracked</div>
                        </div>
                    </div>
                </article>
            </div>

            <div v-if="visibleCardCount === 0" class="col-12">
                <q-banner class="dora-bg-sunken">
                    All cards are hidden. Use the <q-icon :name="ICONS.tune" /> Cards menu above to show some.
                </q-banner>
            </div>
        </div>
        </FadeTransition>

        <!-- ───── Dora tip footer ───────────────────────────────────────── -->
        <transition name="fade">
            <aside
                v-if="tip && !tipDismissed"
                class="dora-tip"
                role="note"
                aria-label="Tip from Dora"
            >
                <q-avatar size="32px" square class="dora-tip-mascot">
                    <img src="../assets/logo-mascot.png" alt="" />
                </q-avatar>
                <div class="dora-tip-body">
                    <strong>Dora says</strong> · {{ tip }}
                </div>
                <q-btn flat round dense size="sm" :icon="ICONS.close" @click="tipDismissed = true">
                    <q-tooltip>Hide for today</q-tooltip>
                </q-btn>
            </aside>
        </transition>
    </div>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import FadeTransition from 'src/components/transitions/FadeTransition.vue';
    import AnimatedNumber from 'src/components/AnimatedNumber.vue';
    import { storeToRefs } from 'pinia';
    import {
        actionsFor as alertActionsFor,
        colorFor as alertColorFor,
        iconFor as alertIconFor,
        type Alert,
        type AlertAction,
    } from 'src/models/alert';
    import type { DashboardSummary, UpcomingMealPlanEntry } from 'src/models/dashboard';
    import type { Product } from 'src/models/product';
    import type { Recipe } from 'src/models/recipe';
    import type { ShoppingListDetail } from 'src/models/shoppingList';
    import { priceOfLine, savingsOfLine } from 'src/models/shoppingList';
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
    import { useAuthStore } from 'src/stores/authStore';
    import { useRecipeStore } from 'src/stores/recipeStore';
    import { useShoppingListStore } from 'src/stores/shoppingListStore';
    import { useStockItemStore } from 'src/stores/stockItemStore';
    import { useStockLevelStore } from 'src/stores/stockLevelStore';
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
        | 'recipes'
        | 'meals'
        | 'meal_plan'
        | 'shopping_lists'
        | 'products';

    type CardDef = { id: CardId; label: string; icon: string };

    // Order matters: this is the visible order in the "Cards" toggle menu,
    // and the default render order on first visit. Newer P12 cards lead so
    // first-time users land on the actionable stuff before the totals.
    const CARD_DEFS: CardDef[] = [
        { id: 'attention', label: 'Needs your attention', icon: ICONS.notifications_active },
        { id: 'primary_list', label: 'Primary shopping list', icon: ICONS.shopping_cart },
        { id: 'budget', label: 'Grocery budget', icon: ICONS.savings },
        { id: 'use_soon', label: 'Use soon', icon: ICONS.expiry },
        { id: 'suggestions', label: 'Dora suggests', icon: 'auto_awesome' },
        { id: 'cookable', label: 'Cookable tonight', icon: ICONS.restaurant_menu },
        { id: 'best_deals', label: 'Best deals on saved products', icon: ICONS.local_offer },
        { id: 'meal_plan', label: 'The week ahead', icon: ICONS.calendar_month },
        { id: 'stock_items', label: 'Pantry', icon: 'inventory_2' },
        { id: 'recipes', label: 'Recipes', icon: ICONS.menu_book },
        { id: 'meals', label: 'Meals', icon: ICONS.restaurant },
        { id: 'shopping_lists', label: 'Shopping', icon: ICONS.shopping_cart },
        { id: 'products', label: 'Products', icon: ICONS.local_offer }
    ];

    // Tip pool. One is picked deterministically per calendar day so the user
    // sees the same one all day but a fresh one tomorrow. New tips can be
    // added without rebalancing — the picker just modulos over the array.
    const TIPS: string[] = [
        "I quietly judge anyone who lets the salmon hit six months in the freezer.",
        "Mark a stock item as 'open' and the opened-on date is recorded automatically.",
        "Recipes greyed out on the list? At least one ingredient is fully out.",
        "Cook mode auto-detects 'X minutes' in your steps and offers a timer.",
        "Setting your default shopping list makes the cart button one-tap.",
        "The 'Mark Made' button on a recipe also bumps its last-cooked date.",
        "Filter recipes by 'all ingredients in stock' to decide what's actually cookable now.",
        "A meal plan entry's servings can exceed the recipe's; quantities scale."
    ];

    const authStore = useAuthStore();
    const router = useRouter();
    const { currentUser } = storeToRefs(authStore);

    const dashboardApiService = new DashboardApiService();
    const alertApi = new AlertApiService();
    const productApi = new ProductApiService();
    const budgetApi = new BudgetApiService();
    const wasteApi = new WasteApiService();
    // P2-04 — suggestion store shared with the Dora launcher badge and
    // the chat panel so dismiss/snooze here propagates everywhere.
    const suggestionStore = useSuggestionStore();
    const shoppingListApi = new ShoppingListApiService();

    const recipeStore = useRecipeStore();
    const stockItemStore = useStockItemStore();
    const stockLevelStore = useStockLevelStore();
    const shoppingListStore = useShoppingListStore();

    const { recipes } = storeToRefs(recipeStore);
    const { stockItems } = storeToRefs(stockItemStore);
    const { stockLevels } = storeToRefs(stockLevelStore);

    const summary = ref<DashboardSummary | null>(null);
    const loading = ref(false);
    const loadError = ref<string | null>(null);
    const tipDismissed = ref(false);

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
    const products = ref<Product[]>([]);
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

    const firstName = computed(() => currentUser.value?.username ?? '');

    const greeting = computed(() => {
        const h = new Date().getHours();
        if (h < 5) return 'Up late';
        if (h < 12) return 'Good morning';
        if (h < 17) return 'Good afternoon';
        return 'Good evening';
    });

    // ── Card-visibility prefs (per user, persisted in localStorage) ──────
    const storageKey = computed(() => {
        const userId = currentUser.value?.user_id ?? 'anonymous';
        return `dora.dashboard.cards.${userId}`;
    });
    const visibleCards = ref<Set<CardId>>(loadVisibleCards(storageKey.value));

    function loadVisibleCards(key: string): Set<CardId> {
        try {
            const raw = localStorage.getItem(key);
            if (!raw) return new Set(CARD_DEFS.map((c) => c.id));
            const parsed = JSON.parse(raw) as string[];
            const known = new Set(CARD_DEFS.map((c) => c.id) as string[]);
            const result = new Set(parsed.filter((id) => known.has(id)) as CardId[]);
            // Default newly-introduced cards to visible — otherwise users
            // with stored state never see them until they open the menu.
            for (const def of CARD_DEFS) {
                if (!parsed.includes(def.id)) result.add(def.id);
            }
            return result;
        } catch {
            return new Set(CARD_DEFS.map((c) => c.id));
        }
    }
    function saveVisibleCards() {
        try {
            localStorage.setItem(storageKey.value, JSON.stringify([...visibleCards.value]));
        } catch {
            // localStorage may be unavailable; skip silently.
        }
    }
    watch(storageKey, (newKey) => {
        visibleCards.value = loadVisibleCards(newKey);
    });

    function isCardVisible(id: CardId): boolean {
        return visibleCards.value.has(id);
    }
    function toggleCard(id: CardId) {
        const next = new Set(visibleCards.value);
        if (next.has(id)) next.delete(id);
        else next.add(id);
        visibleCards.value = next;
        saveVisibleCards();
    }
    const visibleCardCount = computed(() => visibleCards.value.size);

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

    // ── Tip of the day (rotating, stable per calendar day) ───────────────
    const tip = computed(() => {
        const epochDay = Math.floor(Date.now() / 86_400_000);
        return TIPS[epochDay % TIPS.length] ?? null;
    });

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

    // ── Needs your attention ─────────────────────────────────────────────
    // Top-by-severity alerts; the panel page (P13) handles bulk-acknowledge
    // and history. Dashboard only ever shows the most urgent few.
    const ATTENTION_LIMIT = 5;

    const topAlerts = computed(() => {
        const order: Record<string, number> = { high: 0, medium: 1, low: 2 };
        return [...alerts.value]
            .sort((a, b) => (order[a.severity] ?? 9) - (order[b.severity] ?? 9))
            .slice(0, ATTENTION_LIMIT);
    });

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
    // Same "missing = out-of-stock OR untracked" definition the rest of the
    // app uses. Favourites bubble up first within the cookable subset so
    // your usuals show up before the long tail.
    const outOfStockLevelId = computed(
        () => stockLevels.value.find((l) => l.name === 'Out of Stock')?.stock_level_id ?? null,
    );

    function recipeIsCookable(recipe: Recipe): boolean {
        for (const ing of recipe.ingredients) {
            if (!ing.stock_item_id) return false;
            const item = stockItems.value.find((s) => s.stock_item_id === ing.stock_item_id);
            if (!item) return false;
            if (item.stock_level_id === outOfStockLevelId.value) return false;
        }
        return recipe.ingredients.length > 0;
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
    function discountPctFor(product: Product): number | null {
        if (!product.price_was || !product.price_now) return null;
        if (product.price_was <= product.price_now) return null;
        return Math.round(((product.price_was - product.price_now) / product.price_was) * 100);
    }

    const bestDeals = computed<Product[]>(() =>
        [...products.value]
            .filter((p) => p.is_active && discountPctFor(p) !== null)
            .sort((a, b) => (discountPctFor(b) ?? 0) - (discountPctFor(a) ?? 0))
            .slice(0, 3),
    );

    async function loadProducts() {
        try {
            const page = await productApi.getAllAsync();
            products.value = page.items;
        } catch {
            products.value = [];
        }
    }

    // ── Primary shopping list ────────────────────────────────────────────
    const primaryListId = computed(() => shoppingListStore.primaryListId);
    const primarySummary = computed(() => shoppingListStore.primarySummary);

    const primaryListStats = computed(() => {
        const detail = primaryListDetail.value;
        if (!detail) return null;
        let remaining = 0;
        let full = 0;
        let savings = 0;
        let unticked = 0;
        for (const line of detail.lines) {
            const price = priceOfLine(line);
            full += price;
            savings += savingsOfLine(line);
            if (!line.is_ticked) {
                remaining += price;
                unticked++;
            }
        }
        return {
            remaining,
            full,
            savings,
            unticked,
            ticked: detail.lines.length - unticked,
            total: detail.lines.length,
        };
    });

    async function loadPrimaryListDetail() {
        const id = primaryListId.value;
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
    watch(primaryListId, () => {
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
            loadProducts(),
            loadBudget(),
            loadWasteRescue(),
            suggestionStore.refreshAsync(),
            stockItems.value.length === 0
                ? stockItemStore.getStockItemsAsync()
                : Promise.resolve(),
            stockLevels.value.length === 0
                ? stockLevelStore.getStockLevelsAsync()
                : Promise.resolve(),
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

<style scoped>
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
        padding: 20px 24px;
        margin-bottom: 24px;
        background: var(--c-surface);
        border: 1px solid var(--c-line);
        border-radius: 18px;
        box-shadow: var(--elevation-card);
    }
    .dora-hero-mascot {
        border-radius: 14px;
        background: var(--c-accent-soft);
        padding: 4px;
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

    /* ───── Cards ────────────────────────────────────────────────────── */
    .dora-cards {
        animation: dora-fade-up 0.4s ease-out both;
    }
    .dora-card {
        background: var(--c-surface);
        border: 1px solid var(--c-line);
        border-radius: 18px;
        padding: 18px 20px 20px;
        height: 100%;
        transition:
            transform 0.18s ease,
            box-shadow 0.18s ease,
            border-color 0.18s ease;
        box-shadow: var(--elevation-card);
    }
    .dora-card-clickable {
        cursor: pointer;
    }
    .dora-card-clickable:hover {
        transform: translateY(-2px);
        box-shadow: var(--elevation-card-hover);
        border-color: var(--border-strong);
    }
    .dora-card-head {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 14px;
    }
    .dora-card-icon {
        color: var(--c-accent);
    }
    .dora-card-title {
        margin: 0;
        font-size: 1.05rem;
        font-weight: 600;
        flex: 1;
        letter-spacing: 0.005em;
    }
    .dora-card-action {
        font-size: 0.8rem;
        font-weight: 500;
        color: var(--c-ink-mute);
        opacity: 0.85;
        transition: color 0.18s ease, opacity 0.18s ease;
    }
    .dora-card-clickable:hover .dora-card-action {
        color: var(--c-accent);
        opacity: 1;
    }

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

    /* ───── P12 cards ──────────────────────────────────────────────── */
    .dora-card-link {
        color: var(--c-accent);
        text-decoration: none;
        font-weight: 600;
    }
    .dora-card-link:hover {
        text-decoration: underline;
    }

    /* Needs your attention */
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

    /* ───── Dora tip footer ──────────────────────────────────────────── */
    .dora-tip {
        position: fixed;
        bottom: 16px;
        right: 16px;
        max-width: 380px;
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 10px 6px 10px 12px;
        background: var(--c-surface);
        border: 1px solid var(--c-line);
        border-radius: 14px;
        box-shadow: var(--elevation-card-hover);
        z-index: 50;
    }
    .dora-tip-mascot {
        border-radius: 8px;
        background: var(--c-accent-soft);
        padding: 2px;
        flex-shrink: 0;
    }
    .dora-tip-body {
        font-size: 0.85rem;
        line-height: 1.35;
        color: var(--c-ink);
    }
    .dora-tip-body strong {
        color: var(--c-accent);
        font-weight: 700;
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
        .dora-cards,
        .dora-donut-seg,
        .dora-card,
        .dora-card-action,
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
    }
</style>
