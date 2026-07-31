import { storeToRefs } from 'pinia';
import { useQuasar } from 'quasar';
import { useListState } from 'src/composables/useListState';
import { useMealPlanExport } from 'src/composables/useMealPlanExport';
import { useReducedMotion } from 'src/composables/useReducedMotion';
import { useStockStatus } from 'src/composables/useStockStatus';
import { DEFAULT_MEAL_SLOTS } from 'src/helpers/recipeVocabulary';
import { isoDate as toIso, localTodayIso, mondayOf, shiftDays } from 'src/helpers/weekDates';
import type { MealPlan, MealPlanEntry, MealPlanIngredient } from 'src/models/mealPlan';
import type { Recipe } from 'src/models/recipe';
import type { MealPlanEntryCommand } from 'src/services/api/mealPlanApiService';
import ShoppingListApiService from 'src/services/api/shoppingListApiService';
import { toastCaption } from 'src/services/errorHandling/apiErrorHandler';
import { useMealPlanStore } from 'src/stores/mealPlanStore';
import { useMealPlanTemplateStore } from 'src/stores/mealPlanTemplateStore';
import { useMealPlanTemplateSetStore } from 'src/stores/mealPlanTemplateSetStore';
import { useMealSlotStore } from 'src/stores/mealSlotStore';
import { useRecipeStore } from 'src/stores/recipeStore';
import { useShoppingListStore } from 'src/stores/shoppingListStore';
import { useStockItemStore } from 'src/stores/stockItemStore';
import { useStockLevelStore } from 'src/stores/stockLevelStore';
import { computed, onMounted, onUnmounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';

// Fallback used when the user hasn't set a `meals_per_week` preference
// (FU-181 loose-end 2). Callers should prefer `useMealsPerWeek()` — this
// constant stays as the single source of the fallback so no other file
// re-hardcodes 7.
export const BUILDER_TARGET_MEALS_FALLBACK = 7;
const RECIPE_TRAY_CAP = 10;

export type RecipeTray = {
    key: string;
    title: string;
    recipes: Recipe[];
    defaultOpen: boolean;
};

export type WeekDay = { label: string; iso: string };

/**
 * R-001 / R-003 — the meal planner page's shared core. Both Direction A (the
 * existing carousel) and the upcoming Direction B (week board) consume this so
 * mutation logic, week navigation, ingredient loading, list generation, and
 * template flows live in one place.
 */
export function useMealPlanner() {
    const $q = useQuasar();
    const router = useRouter();
    const route = useRoute();
    const planExport = useMealPlanExport();

    const mealPlanStore = useMealPlanStore();
    const mealPlanTemplateStore = useMealPlanTemplateStore();
    const mealPlanTemplateSetStore = useMealPlanTemplateSetStore();
    const mealSlotStore = useMealSlotStore();
    const recipeStore = useRecipeStore();
    const stockItemStore = useStockItemStore();
    const stockLevelStore = useStockLevelStore();
    const shoppingListStore = useShoppingListStore();
    const shoppingListApi = new ShoppingListApiService();

    const { mealPlans, shortfall, today } = storeToRefs(mealPlanStore);
    const { mealSlotNames } = storeToRefs(mealSlotStore);
    const { templates } = storeToRefs(mealPlanTemplateStore);
    const { sets } = storeToRefs(mealPlanTemplateSetStore);
    const { recipes } = storeToRefs(recipeStore);

    const ingredients = ref<MealPlanIngredient[]>([]);
    const ingredientsLoading = ref(false);
    const generating = ref(false);
    // FU-354 — the picker's search string survives navigate-away-and-back
    // within the session (A8 §3 nav-state policy). Full reload /
    // sign-out (via `clearAllListState` from FU-355) resets it to empty.
    // The composable's other refs (ingredients, generating, ...) reset
    // on remount — they're derived / lifecycle state, not user-picked
    // filters, so they don't want persistence.
    const { recipeSearch } = useListState('meal-plans-overview', () => ({
        recipeSearch: ref(''),
    }));
    // R-Phase 6 §9-I — initial-load flag. The page mounts ~10 parallel store
    // hydrations; until they finish we render skeleton screens so the user
    // sees the grid/list shape instantly (Doherty) instead of a popcorn of
    // cards arriving.
    const isInitialLoading = ref(true);

    // R-021 carve-out — server-owned `today` (household timezone) is the
    // authoritative boundary; `localTodayIso()` is a display-only pre-load
    // fallback that flips the moment `today.value` arrives from the store.
    const currentDayIso = computed(() => today.value ?? localTodayIso());
    function isPastDay(iso: string): boolean {
        return iso < currentDayIso.value;
    }
    // R-003 — the single predicate for "entries the client may resend on a
    // plan PATCH": forward-looking AND not yet consumed. Past + consumed
    // entries are immutable history the server preserves on its own (FU-595);
    // the client must NOT resend a past entry — doing so trips the server's
    // past-date guard and used to freeze the whole week. Every command builder
    // below (add / adjust servings / remove) filters through this.
    function isForwardEditable(entry: MealPlanEntry): boolean {
        return !entry.consumed_at && !isPastDay(toIso(entry.scheduled_for));
    }

    // ── Focused week (the carousel's source of truth) ──────────────────────
    const focusedMonday = ref<string>(mondayOf(localTodayIso()));
    const focusedPlan = computed<MealPlan | null>(
        () => mealPlans.value.find((p) => mondayOf(p.start_date) === focusedMonday.value) ?? null,
    );
    const weekDays = computed<WeekDay[]>(() => {
        const labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
        return labels.map((label, i) => ({ label, iso: shiftDays(focusedMonday.value, i) }));
    });
    const weekRangeLabel = computed(
        () => `${formatDate(focusedMonday.value)} – ${formatDate(shiftDays(focusedMonday.value, 6))}`,
    );

    // ── Slots (household vocabulary, C-2.A) ────────────────────────────────
    const slotNames = computed(() =>
        mealSlotNames.value.length ? mealSlotNames.value : [...DEFAULT_MEAL_SLOTS],
    );
    const slotNameSet = computed(() => new Set(slotNames.value));

    function dayEntries(dayIso: string): MealPlanEntry[] {
        return (focusedPlan.value?.entries ?? []).filter((e) => toIso(e.scheduled_for) === dayIso);
    }
    function slotEntries(dayIso: string, slot: string): MealPlanEntry[] {
        return dayEntries(dayIso).filter((e) => e.slot === slot);
    }
    function otherSlotEntries(dayIso: string): MealPlanEntry[] {
        return dayEntries(dayIso).filter((e) => !slotNameSet.value.has(e.slot));
    }

    const shortfallRecipeIds = computed(() => new Set(shortfall.value.map((s) => s.recipe_id)));
    function isShortfallEntry(entry: MealPlanEntry): boolean {
        return shortfallRecipeIds.value.has(entry.recipe_id);
    }

    // Moved shortfall summary (the page-top banner is gone): one sidebar line,
    // chef-hat not warning-triangle. Deadline = earliest `earliest_needed`.
    const cookByLabel = computed(() => {
        const dates = shortfall.value
            .map((s) => s.earliest_needed)
            .filter((d): d is string => !!d);
        const earliest = dates.length ? dates.reduce((a, b) => (a < b ? a : b)) : null;
        return `${shortfall.value.length} to cook${earliest ? ` by ${formatDate(earliest)}` : ''}`;
    });

    // ── Recipe trays (C-2.I) ───────────────────────────────────────────────
    const filteredRecipes = computed(() => {
        const q = recipeSearch.value?.trim().toLowerCase() ?? '';
        if (!q) return recipes.value;
        return recipes.value.filter((r) => r.name.toLowerCase().includes(q));
    });
    const trays = computed<RecipeTray[]>(() => {
        if (recipeSearch.value?.trim()) {
            return [{
                key: 'results',
                title: `Results (${filteredRecipes.value.length})`,
                recipes: filteredRecipes.value,
                defaultOpen: true,
            }];
        }
        const all = recipes.value;
        const out: RecipeTray[] = [];
        const favs = all.filter((r) => r.is_favourite);
        if (favs.length) out.push({ key: 'fav', title: 'Favourites', recipes: favs, defaultOpen: true });
        const stale = all
            .filter((r) => r.not_made_recently)
            .sort((a, b) => madeMs(a) - madeMs(b))
            .slice(0, RECIPE_TRAY_CAP);
        if (stale.length) out.push({ key: 'stale', title: "Haven't had in a while", recipes: stale, defaultOpen: false });
        const freq = all
            .filter((r) => r.plan_count > 0)
            .sort((a, b) => b.plan_count - a.plan_count)
            .slice(0, RECIPE_TRAY_CAP);
        if (freq.length) out.push({ key: 'freq', title: 'Frequently planned', recipes: freq, defaultOpen: false });
        out.push({ key: 'all', title: `All recipes (${all.length})`, recipes: all, defaultOpen: true });
        return out;
    });
    function madeMs(r: Recipe): number {
        return r.last_made_on ? new Date(r.last_made_on).getTime() : 0;
    }

    // ── Tap-to-add: focus a slot, then pick a recipe ───────────────────────
    const focusedTarget = ref<{ dayIso: string; slot: string } | null>(null);
    function isTargeted(dayIso: string, slot: string): boolean {
        return focusedTarget.value?.dayIso === dayIso && focusedTarget.value?.slot === slot;
    }
    function selectSlot(dayIso: string, slot: string) {
        if (isPastDay(dayIso)) {
            $q.notify({ type: 'warning', position: 'bottom-right', message: 'Past days are read-only.' });
            return;
        }
        focusedTarget.value = isTargeted(dayIso, slot) ? null : { dayIso, slot };
    }
    async function pickRecipe(recipeId: string) {
        if (!focusedTarget.value) {
            $q.notify({
                type: 'info',
                position: 'bottom-right',
                message: "Tap a day's meal slot first, then a recipe.",
            });
            return;
        }
        await addEntry(focusedTarget.value.dayIso, focusedTarget.value.slot, recipeId);
    }
    function clearFocusedTarget() {
        focusedTarget.value = null;
    }

    // ── Drag-to-add (desktop pointer only) ─────────────────────────────────
    const dragAllowed = ref(true);
    const draggingRecipeId = ref<string | null>(null);
    function onRecipePointerDown(e: PointerEvent) {
        dragAllowed.value = e.pointerType === 'mouse';
    }
    function onDragStart(recipeId: string) {
        draggingRecipeId.value = recipeId;
    }
    function onDragEnd() {
        draggingRecipeId.value = null;
    }
    async function onDropOnSlot(dayIso: string, slot: string) {
        const recipeId = draggingRecipeId.value;
        draggingRecipeId.value = null;
        if (!recipeId) return;
        if (isPastDay(dayIso)) {
            $q.notify({ type: 'warning', position: 'bottom-right', message: 'Past days are read-only.' });
            return;
        }
        await addEntry(dayIso, slot, recipeId);
    }

    // ── Entry mutations ────────────────────────────────────────────────────
    function planEntryCommands(plan: MealPlan): MealPlanEntryCommand[] {
        return plan.entries
            .filter(isForwardEditable)
            .map((e) => ({
                recipe_id: e.recipe_id,
                scheduled_for: toIso(e.scheduled_for),
                servings: e.servings,
                slot: e.slot,
            }));
    }

    async function refreshAfterMutation() {
        await Promise.all([
            loadIngredients(),
            mealPlanStore.getShortfallAsync(),
            recipeStore.getRecipesAsync(),
        ]);
    }

    // FU-595(b) — every plan mutation funnels through here or `addEntry`'s
    // create branch, and both toast on failure rather than letting a rejected
    // request escape to the page ErrorBoundary (a stray 400 used to blank the
    // whole planner). Returns whether the write succeeded so callers can gate
    // their success toast.
    function notifyPlanError(err: unknown) {
        $q.notify({
            type: 'negative',
            position: 'bottom-right',
            message: 'Could not update the plan.',
            caption: toastCaption(err),
        });
    }

    async function persistEntries(
        planId: string,
        entries: MealPlanEntryCommand[],
    ): Promise<boolean> {
        // The planner's edits are explicit, so set the clear flag when an
        // action empties the future-entries list. The backend treats an
        // unflagged [] as a probable bug and refuses.
        try {
            await mealPlanStore.updateMealPlanAsync({
                meal_plan_id: planId,
                entries,
                ...(entries.length === 0 ? { confirm_clear_entries: true } : {}),
            });
            await refreshAfterMutation();
            return true;
        } catch (err) {
            notifyPlanError(err);
            return false;
        }
    }

    async function addEntry(dayIso: string, slot: string, recipeId: string) {
        if (isPastDay(dayIso)) return;
        // Bridge until C-2.E: the first add to an unplanned week implicitly
        // creates the plan (auto-named) carrying that entry.
        if (!focusedPlan.value) {
            try {
                await mealPlanStore.createMealPlanAsync({
                    start_date: focusedMonday.value,
                    entries: [{ recipe_id: recipeId, scheduled_for: dayIso, servings: 1, slot }],
                });
                await refreshAfterMutation();
            } catch (err) {
                notifyPlanError(err);
                return;
            }
            $q.notify({ type: 'positive', position: 'bottom-right', message: 'Added to plan.' });
            return;
        }
        const plan = focusedPlan.value;
        const cmds = planEntryCommands(plan);
        const existing = cmds.find(
            (c) => c.recipe_id === recipeId && c.scheduled_for === dayIso && c.slot === slot,
        );
        if (existing) {
            existing.servings += 1; // same recipe + day + slot increments, not duplicates
        } else {
            cmds.push({ recipe_id: recipeId, scheduled_for: dayIso, servings: 1, slot });
        }
        if (await persistEntries(plan.meal_plan_id, cmds)) {
            $q.notify({ type: 'positive', position: 'bottom-right', message: 'Added to plan.' });
        }
    }

    async function adjustEntryServings(entry: MealPlanEntry, delta: number) {
        const plan = focusedPlan.value;
        if (!plan) return;
        const next = entry.servings + delta;
        const cmds = plan.entries
            .filter(isForwardEditable)
            .filter((e) => !(e.meal_plan_entry_id === entry.meal_plan_entry_id && next < 1))
            .map((e) => ({
                recipe_id: e.recipe_id,
                scheduled_for: toIso(e.scheduled_for),
                servings: e.meal_plan_entry_id === entry.meal_plan_entry_id ? next : e.servings,
                slot: e.slot,
            }));
        await persistEntries(plan.meal_plan_id, cmds);
    }

    async function removeEntry(entry: MealPlanEntry) {
        const plan = focusedPlan.value;
        if (!plan) return;
        const remaining = plan.entries
            .filter((e) => e.meal_plan_entry_id !== entry.meal_plan_entry_id && isForwardEditable(e))
            .map((e) => ({
                recipe_id: e.recipe_id,
                scheduled_for: toIso(e.scheduled_for),
                servings: e.servings,
                slot: e.slot,
            }));
        await persistEntries(plan.meal_plan_id, remaining);
    }

    // ── Week navigation (carousel) ─────────────────────────────────────────
    const slideDir = ref<'up' | 'down'>('down');
    const prefersReducedMotion = useReducedMotion();
    const weekTransition = computed(() =>
        prefersReducedMotion.value ? '' : slideDir.value === 'down' ? 'wk-down' : 'wk-up',
    );
    function goPrevWeek() {
        focusedMonday.value = shiftDays(focusedMonday.value, -7);
    }
    function goNextWeek() {
        focusedMonday.value = shiftDays(focusedMonday.value, 7);
    }
    // Any focus change — arrows, ↑/↓ keys, swipe, or a calendar-widget click —
    // sets the slide direction, clears the pending add-target, and tracks the
    // focused week in the URL (F28 refresh-resume).
    watch(focusedMonday, (next, prev) => {
        slideDir.value = next >= prev ? 'down' : 'up';
        focusedTarget.value = null;
        void router.replace({ query: { ...route.query, monday: next } });
    });
    function onKeydown(e: KeyboardEvent) {
        // R-Phase 6 §9-J — global Arrow nav must NOT steal focus from
        // the active control. Skip when typing in any editable region
        // (INPUT/TEXTAREA/contentEditable) OR when an interactive element
        // has focus (button/link/select/details/summary) — arrowing off a
        // slot button used to jump the week.
        const t = e.target as HTMLElement | null;
        if (!t) return;
        if (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.isContentEditable) return;
        if (t.closest('button, a, select, [role="button"], [role="menuitem"], [role="tab"], [contenteditable="true"]')) return;
        if (e.key === 'ArrowUp') { e.preventDefault(); goPrevWeek(); }
        else if (e.key === 'ArrowDown') { e.preventDefault(); goNextWeek(); }
    }
    let touchStartY = 0;
    function onTouchStart(e: TouchEvent) { touchStartY = e.changedTouches[0]?.clientY ?? 0; }
    function onTouchEnd(e: TouchEvent) {
        const dy = (e.changedTouches[0]?.clientY ?? 0) - touchStartY;
        if (Math.abs(dy) < 60) return;
        if (dy > 0) goPrevWeek(); else goNextWeek();
    }

    // ── Stock status (shared composable, R-003) ────────────────────────────
    const { stockStatusLabel, stockStatusColour, needsBuying } = useStockStatus();
    const needToBuy = computed(() =>
        ingredients.value.filter((ing) => needsBuying(ing.stock_item_id)),
    );

    // ── Shopping-list status (F31) + hover-to-highlight (F30, C-2.H) ───────
    function listStatusLabel(stockItemId: string): string {
        const m = shoppingListStore.membership;
        const entry = m?.items.find((i) => i.stock_item_id === stockItemId);
        if (!entry || entry.unticked_list_ids.length === 0) return 'not on a list';
        const byId = new Map(
            (m?.active_lists ?? []).map((l): [string, string] => [l.shopping_list_id, l.name]),
        );
        return `on ${entry.unticked_list_ids.map((id) => byId.get(id) ?? 'a list').join(', ')}`;
    }

    // Hovering a needed ingredient highlights the day cells whose recipes use
    // it (desktop only — mouse events don't fire on touch).
    const hoveredRecipeIds = ref<Set<string>>(new Set());
    function hoverIngredient(ing: MealPlanIngredient) {
        hoveredRecipeIds.value = new Set(ing.used_in_recipe_ids);
    }
    function clearHover() {
        hoveredRecipeIds.value = new Set();
    }

    // ── Recipe pool quick-actions (± / log cook) ───────────────────────────
    async function adjustPaletteMeals(recipeId: string, delta: number) {
        try {
            await recipeStore.adjustMealsAsync(recipeId, delta);
            await Promise.all([recipeStore.getRecipesAsync(), mealPlanStore.getShortfallAsync()]);
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not update meals.',
                caption: toastCaption(err),
            });
        }
    }
    async function logPaletteCook(recipeId: string, count: number) {
        const n = Math.max(1, Math.floor(count || 0));
        await recipeStore.cookAsync(recipeId, n);
        await Promise.all([recipeStore.getRecipesAsync(), mealPlanStore.getShortfallAsync()]);
        return n;
    }

    function goToRecipe(recipeId: string) {
        void router.push(`/cookbook/${recipeId}`);
    }
    function cookRecipe(recipeId: string) {
        void router.push(`/cookbook/${recipeId}/cook`);
    }
    // FU-308 (2026-07-07) — `goToManageTemplates` retired. The Templates
    // drawer now houses per-template CRUD; the drawer itself owns the
    // "Manage rotating sets →" jump to `/meal-plans/templates`, so a
    // composable-level nav helper isn't needed.

    // ── Generate shopping list (composes the C-7 target picker) ────────────
    async function pickGenerateTarget(): Promise<string | null | undefined> {
        const drafts = (shoppingListStore.membership?.active_lists ?? []).filter(
            (l) => l.status === 'draft',
        );
        if (drafts.length === 0) return null;
        const CREATE_NEW = '__create_new__';
        return await new Promise<string | null | undefined>((resolve) => {
            $q.dialog({
                title: 'Add to which list?',
                message: "Generate the week's shopping into an existing draft, or create a new list.",
                options: {
                    type: 'radio',
                    model: drafts[0]!.shopping_list_id,
                    items: [
                        ...drafts.map((d) => ({ label: d.name, value: d.shopping_list_id })),
                        { label: '+ Create new list', value: CREATE_NEW },
                    ],
                },
                cancel: { noCaps: true },
                ok: { label: 'Generate', noCaps: true, color: 'primary' },
                persistent: false,
            })
                .onOk((val: string) => resolve(val === CREATE_NEW ? null : val))
                .onCancel(() => resolve(undefined))
                .onDismiss(() => {});
        });
    }

    // FU-596 — an optional `recipeIds` scopes generation to just those recipes
    // (the "plan a single day → shop for that day" builder path), routed through
    // the existing `recipes` auto-generate source. With no arg the whole focused
    // week is generated via `meal_plan_week` (unchanged default; the sidebar and
    // mobile "Generate list" buttons still call it arg-less).
    async function generateListForWeek(recipeIds?: string[]) {
        const plan = focusedPlan.value;
        if (!plan) return;
        const target = await pickGenerateTarget();
        if (target === undefined) return;
        generating.value = true;
        try {
            const startIso = toIso(plan.start_date);
            const scoped = recipeIds !== undefined && recipeIds.length > 0;
            const result = await shoppingListApi.autoGenerateAsync({
                ...(target ? { merge_into_list_id: target } : { name: `Meals: week of ${formatDate(plan.start_date)}` }),
                sources: scoped ? { recipes: recipeIds } : { meal_plan_week: startIso },
            });
            await shoppingListStore.refreshAsync();
            if (result.nothing_to_add) {
                $q.notify({
                    type: 'info',
                    position: 'bottom-right',
                    message: 'Nothing to add — you have everything for this week already.',
                });
                return;
            }
            const itemWord = result.added_count === 1 ? 'item' : 'items';
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: target
                    ? `Added ${result.added_count} ${itemWord} to your list.`
                    : `Shopping list created with ${result.added_count} ${itemWord}.`,
            });
            // FU-505 — recipe ingredients that aren't linked to any StockItem
            // can't be turned into shopping-list lines (there's no stock-item
            // id to anchor the line). Surface them so the user knows what's
            // still missing rather than silently dropping them.
            if (result.unlinked_skipped && result.unlinked_skipped.length > 0) {
                const lines = result.unlinked_skipped
                    .map((u) => `• ${u.ingredient_name} (${u.recipe_name})`)
                    .join('\n');
                $q.dialog({
                    title: 'Add these manually',
                    message:
                        `${result.unlinked_skipped.length} recipe `
                        + `ingredient${result.unlinked_skipped.length === 1 ? '' : 's'} `
                        + "aren't linked to your pantry, so we couldn't add "
                        + `${result.unlinked_skipped.length === 1 ? 'it' : 'them'} to the list. `
                        + 'Add them by hand or link them from the recipe next time:\n\n'
                        + lines,
                    ok: 'Got it',
                });
            }
            if (result.shopping_list_id) {
                void router.push(`/shopping-lists/${result.shopping_list_id}`);
            }
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not generate the list.',
                caption: toastCaption(err),
            });
        } finally {
            generating.value = false;
        }
    }

    function formatDate(iso: string): string {
        return new Date(iso).toLocaleDateString();
    }
    async function loadIngredients() {
        const id = focusedPlan.value?.meal_plan_id;
        if (!id) { ingredients.value = []; return; }
        ingredientsLoading.value = true;
        try {
            ingredients.value = await mealPlanStore.getIngredientsForPlanAsync(id);
        } finally {
            ingredientsLoading.value = false;
        }
    }

    function confirmClearWeek() {
        const plan = focusedPlan.value;
        if (!plan) return;
        $q.dialog({
            title: 'Clear this week',
            message: `Remove all meals from the week of ${formatDate(plan.start_date)}?`,
            cancel: true,
        }).onOk(() => void doClearWeek(plan.meal_plan_id));
    }
    async function doClearWeek(planId: string) {
        await mealPlanStore.deleteMealPlanAsync(planId);
        await Promise.all([loadIngredients(), mealPlanStore.getShortfallAsync()]);
    }

    // ── Templates (C-2.F) ──────────────────────────────────────────────────
    async function saveFocusedWeekAsTemplate(name: string, description: string): Promise<boolean> {
        if (!focusedPlan.value || !name.trim()) return false;
        try {
            await mealPlanTemplateStore.createFromPlanAsync({
                name: name.trim(),
                source_meal_plan_id: focusedPlan.value.meal_plan_id,
                ...(description.trim() ? { description: description.trim() } : {}),
            });
            $q.notify({ type: 'positive', position: 'bottom-right', message: 'Saved this week as a template.' });
            return true;
        } catch (err) {
            $q.notify({
                type: 'negative', position: 'bottom-right',
                message: 'Could not save the template.',
                caption: toastCaption(err),
            });
            return false;
        }
    }

    /**
     * Warn before replacing the focused week's future meals (Decision 1 copy
     * from C-2). Returns true when the user has explicitly confirmed (or there
     * are no future entries to replace). The templates drawer (§9-E) and any
     * other apply-template entry point both gate on this.
     */
    async function warnBeforeReplaceWeek(): Promise<boolean> {
        const futureCount = (focusedPlan.value?.entries ?? []).filter(
            (e) => !e.consumed_at && !isPastDay(toIso(e.scheduled_for)),
        ).length;
        if (futureCount === 0) return true;
        return await new Promise<boolean>((resolve) => {
            $q.dialog({
                title: 'Replace this week?',
                message: `This week has ${futureCount} planned meal${futureCount === 1 ? '' : 's'}. `
                    + `Applying the template will replace ${futureCount === 1 ? 'it' : 'them'}.`,
                cancel: { noCaps: true },
                ok: { label: 'Replace', noCaps: true, color: 'primary' },
                persistent: false,
            })
                .onOk(() => resolve(true))
                .onCancel(() => resolve(false))
                .onDismiss(() => resolve(false));
        });
    }

    async function applyTemplate(templateId: string) {
        try {
            const result = await mealPlanTemplateStore.applyAsync({
                template_id: templateId,
                monday_of_week: focusedMonday.value,
            });
            await refreshAfterMutation();
            if (result.added_count === 0) {
                $q.notify({ type: 'info', position: 'bottom-right', message: 'Nothing added — those days are in the past.' });
                return;
            }
            let message = `Added ${result.added_count} meal${result.added_count === 1 ? '' : 's'}.`;
            if (result.skipped_past_count) {
                message += ` ${result.skipped_past_count} past day${result.skipped_past_count === 1 ? '' : 's'} skipped.`;
            }
            $q.notify({ type: 'positive', position: 'bottom-right', message });
        } catch (err) {
            $q.notify({
                type: 'negative', position: 'bottom-right',
                message: 'Could not apply the template.',
                caption: toastCaption(err),
            });
        }
    }

    // ── Recurring apply (template or rotating set over a range) ────────────
    const recurringSourceOptions = computed(() => [
        ...templates.value.map((t) => ({ label: `Template · ${t.name}`, value: `t:${t.meal_plan_template_id}` })),
        ...sets.value.map((s) => ({ label: `Set · ${s.name}`, value: `s:${s.meal_plan_template_set_id}` })),
    ]);

    async function loadRecurringSources(): Promise<boolean> {
        await Promise.all([mealPlanTemplateStore.getTemplatesAsync(), mealPlanTemplateSetStore.getSetsAsync()]);
        if (recurringSourceOptions.value.length === 0) {
            $q.notify({ type: 'info', position: 'bottom-right', message: 'Save a template first.' });
            return false;
        }
        return true;
    }

    async function applyRecurring(args: {
        source: string;
        startMonday: string;
        endMonday: string;
    }): Promise<boolean> {
        const [kind, id] = [args.source.slice(0, 1), args.source.slice(2)];
        try {
            const result = await mealPlanTemplateStore.applyRecurringAsync({
                ...(kind === 't' ? { template_id: id } : { template_set_id: id }),
                start_monday: mondayOf(args.startMonday),
                end_monday: mondayOf(args.endMonday),
            });
            await refreshAfterMutation();
            let message = `Planned ${result.weeks_applied} week${result.weeks_applied === 1 ? '' : 's'} `
                + `(${result.total_added} meal${result.total_added === 1 ? '' : 's'}).`;
            if (result.total_skipped_past) message += ` ${result.total_skipped_past} past day(s) skipped.`;
            $q.notify({ type: 'positive', position: 'bottom-right', message });
            if (result.first_meal_plan_id) focusedMonday.value = mondayOf(args.startMonday);
            return true;
        } catch (err) {
            $q.notify({
                type: 'negative', position: 'bottom-right',
                message: 'Could not apply the recurring plan.',
                caption: toastCaption(err),
            });
            return false;
        }
    }

    // ── "Build my week" auto-planner commit (FU-596) ───────────────────────
    // The builder dialog now hands us fully-placed entry commands — recipe +
    // day + slot + servings — authored server-side (or edited by the user in
    // the review step). This replaces the old recipe-ids-only signature whose
    // client-side slot spread defaulted everything to the vocab's first slot
    // (the FU-596 "everything in Breakfast" bug). Placement is no longer
    // computed here; we just persist what the review step committed.
    async function builderBuildPlan(newCmds: MealPlanEntryCommand[]) {
        const upcoming = newCmds.filter((c) => !isPastDay(c.scheduled_for));
        if (upcoming.length === 0) {
            $q.notify({
                type: 'warning', position: 'bottom-right',
                message: 'No upcoming meals to add — pick a future day first.',
            });
            throw new Error('no upcoming entries');
        }
        if (!focusedPlan.value) {
            try {
                await mealPlanStore.createMealPlanAsync({ start_date: focusedMonday.value, entries: upcoming });
                await refreshAfterMutation();
            } catch (err) {
                notifyPlanError(err);
                throw err; // let the builder stay on its Build step, not advance to Done
            }
        } else {
            const ok = await persistEntries(
                focusedPlan.value.meal_plan_id,
                [...planEntryCommands(focusedPlan.value), ...upcoming],
            );
            if (!ok) throw new Error('meal-plan build failed'); // toast already shown by persistEntries
        }
        // §9-B — build is decoupled from generate-list. The builder UI exposes
        // an explicit "Generate shopping list" button on its done step.
    }
    function printFocusedWeek() {
        if (focusedPlan.value) planExport.openPrintView(focusedPlan.value.meal_plan_id);
    }

    watch(() => focusedPlan.value?.meal_plan_id, loadIngredients);

    onMounted(async () => {
        window.addEventListener('keydown', onKeydown);
        try {
            await Promise.all([
                mealPlanStore.getMealPlansAsync(),
                mealPlanStore.getShortfallAsync(),
                mealPlanStore.getTodayAsync(),
                mealSlotStore.ensureLoadedAsync(),
                mealPlanTemplateStore.getTemplatesAsync(),
                mealPlanTemplateSetStore.getSetsAsync(),
                recipeStore.ensureLoadedAsync(),
                stockItemStore.ensureLoadedAsync(),
                stockLevelStore.ensureLoadedAsync(),
                shoppingListStore.ensureLoadedAsync(),
            ]);
            // Resume on the URL's week if present (F28), else the household's
            // current week (server tz, C-2.K).
            const urlMonday = typeof route.query.monday === 'string' ? route.query.monday : null;
            focusedMonday.value = mondayOf(urlMonday ?? today.value ?? localTodayIso());
            await loadIngredients();
        } finally {
            isInitialLoading.value = false;
        }
    });
    onUnmounted(() => window.removeEventListener('keydown', onKeydown));

    return {
        // state
        recipes,
        recipeSearch,
        trays,
        templates,
        sets,
        mealPlans,
        shortfall,
        today,
        ingredients,
        ingredientsLoading,
        isInitialLoading,
        generating,
        focusedMonday,
        focusedPlan,
        weekDays,
        weekRangeLabel,
        slotNames,
        slotNameSet,
        currentDayIso,
        cookByLabel,
        shortfallRecipeIds,
        needToBuy,
        hoveredRecipeIds,
        focusedTarget,
        dragAllowed,
        draggingRecipeId,
        slideDir,
        weekTransition,
        prefersReducedMotion,
        recurringSourceOptions,
        // lookups
        dayEntries,
        slotEntries,
        otherSlotEntries,
        isShortfallEntry,
        isPastDay,
        isTargeted,
        listStatusLabel,
        stockStatusLabel,
        stockStatusColour,
        formatDate,
        // mutations
        addEntry,
        adjustEntryServings,
        removeEntry,
        confirmClearWeek,
        loadIngredients,
        generateListForWeek,
        pickGenerateTarget,
        adjustPaletteMeals,
        logPaletteCook,
        saveFocusedWeekAsTemplate,
        warnBeforeReplaceWeek,
        applyTemplate,
        loadRecurringSources,
        applyRecurring,
        builderBuildPlan,
        printFocusedWeek,
        // nav
        goPrevWeek,
        goNextWeek,
        goToRecipe,
        cookRecipe,
        onKeydown,
        onTouchStart,
        onTouchEnd,
        // tap / drag
        selectSlot,
        pickRecipe,
        clearFocusedTarget,
        onRecipePointerDown,
        onDragStart,
        onDragEnd,
        onDropOnSlot,
        // hover
        hoverIngredient,
        clearHover,
    };
}
