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
                    icon="refresh"
                    :loading="loading"
                    @click="loadSummary"
                >
                    <q-tooltip>Refresh dashboard</q-tooltip>
                </q-btn>
                <q-btn flat dense no-caps icon="tune" label="Cards">
                    <q-menu anchor="bottom right" self="top right">
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

        <q-banner v-if="loadError" class="bg-red-1 text-red-9 q-mb-md" dense rounded>
            {{ loadError }}
        </q-banner>

        <div v-if="loading && !summary" class="row justify-center q-pa-xl">
            <q-spinner size="48px" color="primary" />
        </div>

        <div v-else-if="summary" class="row q-col-gutter-md dora-cards">
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
                        <q-icon name="calendar_month" size="22px" class="dora-card-icon" />
                        <h3 class="dora-card-title">The week ahead</h3>
                        <span class="dora-card-action">Plan →</span>
                    </header>
                    <div v-if="nextEntry" class="dora-next-up">
                        <div class="dora-next-up-label">Next up</div>
                        <div class="dora-next-up-meal">{{ nextEntry.meal_name }}</div>
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
                                    :key="entry.meal_name + entry.slot"
                                    class="dora-strip-pip"
                                    :title="`${entry.meal_name} (${entry.slot})`"
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
                        <q-icon name="menu_book" size="22px" class="dora-card-icon" />
                        <h3 class="dora-card-title">Recipes</h3>
                        <span class="dora-card-action">Browse →</span>
                    </header>
                    <div class="dora-stat-grid">
                        <div class="dora-stat">
                            <div class="dora-stat-num">{{ summary.recipes.total }}</div>
                            <div class="dora-stat-label">in your book</div>
                        </div>
                        <div class="dora-stat dora-stat-accent">
                            <div class="dora-stat-num">
                                <q-icon name="favorite" size="18px" class="q-mr-xs" />
                                {{ summary.recipes.favourites }}
                            </div>
                            <div class="dora-stat-label">favourites</div>
                        </div>
                    </div>
                </article>
            </div>

            <!-- ───── Meals card ────────────────────────────────────────── -->
            <div v-if="isCardVisible('meals')" class="col-12 col-sm-6 col-lg-4">
                <article class="dora-card dora-card-clickable" @click="goTo('/meals')">
                    <header class="dora-card-head">
                        <q-icon name="restaurant" size="22px" class="dora-card-icon" />
                        <h3 class="dora-card-title">Meals</h3>
                        <span class="dora-card-action">Adjust →</span>
                    </header>
                    <div class="dora-stat-grid">
                        <div class="dora-stat">
                            <div class="dora-stat-num">{{ summary.meals.total_definitions }}</div>
                            <div class="dora-stat-label">defined</div>
                        </div>
                        <div class="dora-stat dora-stat-ok">
                            <div class="dora-stat-num">{{ summary.meals.total_in_stock }}</div>
                            <div class="dora-stat-label">cooked & ready</div>
                        </div>
                    </div>
                </article>
            </div>

            <!-- ───── Shopping lists card ───────────────────────────────── -->
            <div v-if="isCardVisible('shopping_lists')" class="col-12 col-sm-6 col-lg-4">
                <article class="dora-card">
                    <header class="dora-card-head">
                        <q-icon name="shopping_cart" size="22px" class="dora-card-icon" />
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
                        <q-icon name="local_offer" size="22px" class="dora-card-icon" />
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
                <q-banner class="bg-grey-2">
                    All cards are hidden. Use the <q-icon name="tune" /> Cards menu above to show some.
                </q-banner>
            </div>
        </div>

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
                <q-btn flat round dense size="sm" icon="close" @click="tipDismissed = true">
                    <q-tooltip>Hide for today</q-tooltip>
                </q-btn>
            </aside>
        </transition>
    </div>
</template>

<script lang="ts" setup>
    import { storeToRefs } from 'pinia';
    import type { DashboardSummary, UpcomingMealPlanEntry } from 'src/models/dashboard';
    import DashboardApiService from 'src/services/api/dashboardApiService';
    import { useAuthStore } from 'src/stores/authStore';
    import { computed, onMounted, ref, watch } from 'vue';
    import { useRouter } from 'vue-router';

    type CardId =
        | 'stock_items'
        | 'recipes'
        | 'meals'
        | 'meal_plan'
        | 'shopping_lists'
        | 'products';

    type CardDef = { id: CardId; label: string; icon: string };

    const CARD_DEFS: CardDef[] = [
        { id: 'stock_items', label: 'Pantry', icon: 'inventory_2' },
        { id: 'meal_plan', label: 'The week ahead', icon: 'calendar_month' },
        { id: 'recipes', label: 'Recipes', icon: 'menu_book' },
        { id: 'meals', label: 'Meals', icon: 'restaurant' },
        { id: 'shopping_lists', label: 'Shopping', icon: 'shopping_cart' },
        { id: 'products', label: 'Products', icon: 'local_offer' }
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

    const summary = ref<DashboardSummary | null>(null);
    const loading = ref(false);
    const loadError = ref<string | null>(null);
    const tipDismissed = ref(false);

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
            return new Set(parsed.filter((id) => known.has(id)) as CardId[]);
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
        push('in stock', inStock, '#6ba368');
        push('low', low, '#e89a45');
        push('out', out, '#c85a4f');
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
            return `${capitalise(when)}: ${nextEntry.value.meal_name} for ${nextEntry.value.servings}.`;
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

    async function loadSummary() {
        loading.value = true;
        loadError.value = null;
        try {
            summary.value = await dashboardApiService.getSummaryAsync();
        } catch (err) {
            loadError.value = 'Could not load the dashboard. Try refreshing.';
            // eslint-disable-next-line no-console
            console.warn('dashboard summary failed', err);
        } finally {
            loading.value = false;
        }
    }

    onMounted(loadSummary);
</script>

<style scoped>
    /* ───── Palette ─────────────────────────────────────────────────────
       Warm, food-y, deliberately un-corporate. Scoped to this page so it
       doesn't leak. The variables are exported as CSS custom properties on
       the root .dora-dash element so every descendant can reference them.
    */
    .dora-dash {
        --c-bg-1: #fdfaf3;
        --c-bg-2: #f4ecdc;
        --c-surface: #ffffff;
        --c-ink: #2e2820;
        --c-ink-mute: #76695a;
        --c-line: #ece1c9;
        --c-accent: #f4b740;
        --c-accent-soft: #fef3d8;
        --c-ok: #6ba368;
        --c-ok-soft: #e9f3e6;
        --c-warn: #e89a45;
        --c-warn-soft: #fdedd6;
        --c-bad: #c85a4f;
        --c-bad-soft: #fbe2de;
        --c-pink-soft: #fbe7ee;

        min-height: 100%;
        padding: 24px 24px 96px;
        background: linear-gradient(160deg, var(--c-bg-1) 0%, var(--c-bg-2) 100%);
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
        box-shadow: 0 10px 30px -18px rgba(74, 56, 26, 0.25);
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
        box-shadow: 0 6px 18px -16px rgba(74, 56, 26, 0.4);
    }
    .dora-card-clickable {
        cursor: pointer;
    }
    .dora-card-clickable:hover {
        transform: translateY(-2px);
        box-shadow: 0 14px 32px -18px rgba(74, 56, 26, 0.45);
        border-color: #e5d5b1;
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
        background: #f9f4e8;
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
        color: #345f31;
    }
    .dora-stat-accent {
        background: var(--c-pink-soft);
    }
    .dora-stat-accent .dora-stat-num {
        color: #8a3556;
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
        stroke: #f0e6d0;
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
        color: #6a4a08;
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
        background: #faf6eb;
        border-radius: 12px;
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
        background: #faf6eb;
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
        color: var(--c-bg-1);
    }
    .dora-strip-day.is-today.has-meals {
        background: linear-gradient(180deg, var(--c-ink) 0%, #4a3b27 100%);
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
        box-shadow: 0 14px 30px -18px rgba(74, 56, 26, 0.5);
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
