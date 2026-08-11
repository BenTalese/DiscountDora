import type {
    AutoBuildRequest, AutoBuildResponse, MealPlan, MealPlanIngredient, Shortfall,
} from 'src/models/mealPlan';
import type { CreatedResponse } from './axiosHttpClient';
import AxiosHttpClient from './axiosHttpClient';
import type { Page } from './queryStringBuilder';

export type MealPlanEntryCommand = {
    recipe_id: string;
    scheduled_for: string;
    servings: number;
    slot: string;
    /** PROPOSAL_MEAL_PLANS_PART_2 — transient grouping token; entries sharing a
     *  `cook_key` become one CookBatch (cook once, eat several days). Carry the
     *  saved entry's `cook_batch_id` here to keep a link across edits. */
    cook_key?: string;
};

export type CreateMealPlanCommand = {
    name?: string; // optional — the planner creates nameless week-plans.
    start_date: string;
    entries: MealPlanEntryCommand[];
};

export type UpdateMealPlanCommand = {
    meal_plan_id: string;
    name?: string;
    start_date?: string;
    entries?: MealPlanEntryCommand[];
    /** Required when `entries` is an empty array. Without it the backend
     *  rejects the wipe so a UI bug can't accidentally nuke a plan. */
    confirm_clear_entries?: boolean;
};

export default class MealPlanApiService {
    private httpClient: AxiosHttpClient;

    constructor() {
        this.httpClient = new AxiosHttpClient();
    }

    createAsync = async (command: CreateMealPlanCommand): Promise<CreatedResponse> =>
        await this.httpClient.post<CreatedResponse>('/meal-plans', command);

    deleteAsync = async (mealPlanId: string): Promise<void> =>
        await this.httpClient.delete(`/meal-plans/${mealPlanId}`);

    getAllAsync = async (): Promise<Page<MealPlan>> =>
        await this.httpClient.get<Page<MealPlan>>('/meal-plans');

    updateAsync = async (command: UpdateMealPlanCommand): Promise<void> => {
        const { meal_plan_id, ...payload } = command;
        await this.httpClient.patch<void>(`/meal-plans/${meal_plan_id}`, payload);
    };

    getIngredientsAsync = async (mealPlanId: string): Promise<MealPlanIngredient[]> =>
        await this.httpClient.get<MealPlanIngredient[]>(`/meal-plans/${mealPlanId}/ingredients`);

    getShortfallAsync = async (): Promise<Shortfall[]> =>
        await this.httpClient.get<Shortfall[]>('/meal-plans/shortfall');

    /** The household's current date (ISO) in the install's configured
     *  timezone — the planner trusts this over the browser clock (C-2.K). */
    getTodayAsync = async (): Promise<string> =>
        (await this.httpClient.get<{ today: string }>('/meal-plans/today')).today;

    /** Aggregated ingredient demand for an unsaved recipe selection (C-2.J,
     *  sequential builder). Same scaling math as the saved-plan endpoint. */
    previewIngredientsAsync = async (
        recipes: { recipe_id: string; servings: number }[],
    ): Promise<MealPlanIngredient[]> =>
        await this.httpClient.post<MealPlanIngredient[], { recipes: { recipe_id: string; servings: number }[] }>(
            '/meal-plans/preview-ingredients', { recipes },
        );

    /** FU-596 — "Build my week" auto-planner. Returns a proposed set of
     *  meals (server-selected + slot/day-placed); never persists. The SPA
     *  renders it as an editable preview and commits via the normal
     *  create/update path. */
    autoBuildAsync = async (command: AutoBuildRequest): Promise<AutoBuildResponse> =>
        await this.httpClient.post<AutoBuildResponse, AutoBuildRequest>(
            '/meal-plans/auto-build', command,
        );

    // ── FU-451 — budget-defense recipe swaps ──────────────────────────

    getSwapSuggestionsAsync = async (mealPlanId: string): Promise<SwapSuggestions> =>
        await this.httpClient.get<SwapSuggestions>(`/meal-plans/${mealPlanId}/swap-suggestions`);

    applySwapAsync = async (
        mealPlanId: string, command: ApplySwapCommand,
    ): Promise<ApplySwapResult> =>
        await this.httpClient.post<ApplySwapResult, ApplySwapCommand>(
            `/meal-plans/${mealPlanId}/apply-swap`, command,
        );

    undoSwapAsync = async (
        mealPlanId: string, swapLedgerId: string,
    ): Promise<UndoSwapResult> =>
        await this.httpClient.post<UndoSwapResult, { swap_ledger_id: string }>(
            `/meal-plans/${mealPlanId}/undo-swap`, { swap_ledger_id: swapLedgerId },
        );

    // ── FU-317 — meal-plan reconcile ──────────────────────────────────

    getReconcileQueueAsync = async (
        params: { cursor?: string; limit?: number } = {},
    ): Promise<ReconcileQueue> => {
        const query = new URLSearchParams();
        if (params.cursor) query.set('cursor', params.cursor);
        if (params.limit != null) query.set('limit', String(params.limit));
        const qs = query.toString();
        return await this.httpClient.get<ReconcileQueue>(
            `/meal-plans/reconcile-queue${qs ? `?${qs}` : ''}`,
        );
    };

    submitReconcileVerbAsync = async (
        entryId: string, command: ReconcileVerbCommand,
    ): Promise<ReconcileVerbResult> =>
        await this.httpClient.post<ReconcileVerbResult, ReconcileVerbCommand>(
            `/meal-plans/reconcile/${entryId}`, command,
        );
}

/** Mirrors RecipeSwapCandidate from dora_api swap_suggestions.py. */
export type RecipeSwapCandidate = {
    kind: 'recipe';
    entry_id: string;
    entry_scheduled_for: string;
    entry_slot: string;
    from_recipe_id: string;
    from_recipe_name: string;
    to_recipe_id: string;
    to_recipe_name: string;
    saved: number;
    reason_chip: 'cheaper_recipe_cookable' | 'cheaper_recipe_similar' | 'cheaper_recipe_household_fav';
    missing_ingredient_names: string[];
};

export type SwapSuggestions = {
    projected_over: boolean;
    cost_per_week: number;
    cost_per_week_priced_ratio: { priced: number; total: number; unpriced_recipe_ids: string[] };
    budget_amount: number | null;
    overshoot: number;
    projected_after_applying_all: number;
    candidates: RecipeSwapCandidate[];
};

export type ApplySwapCommand = {
    kind: 'recipe';
    entry_id: string;
    to_recipe_id: string;
    expected_from_recipe_id?: string;
};

export type ApplySwapResult = {
    swap_ledger_id: string;
    new_cost_per_week: number;
    new_projected_over: boolean;
};

export type UndoSwapResult = {
    new_cost_per_week: number;
    new_projected_over: boolean;
};

// ── FU-317 — meal-plan reconcile ────────────────────────────────────────

/** Verb vocabulary — must stay in sync with
 *  `dora_api/features/meal_plans/reconcile.py`'s `_ALLOWED_VERBS`. */
export type ReconcileVerb =
    | 'cooked'
    | 'cooked_adjusted'
    | 'cooked_later'
    | 'not_cooked'
    | 'skip';

/** Receipt state — mirror of
 *  `dora_api/domain/entities/meal_plan_reconcile_receipt.py`. */
export type ReconcileState =
    | 'unresolved_auto'
    | 'unresolved_manual'
    | 'resolved_confirmed'
    | 'resolved_adjusted'
    | 'resolved_not_cooked'
    | 'resolved_deferred';

export type ReconcileEntry = {
    entry_id: string;
    scheduled_for: string;   // ISO date
    slot: string;
    planned_servings: number;
    recipe: { id: string; name: string };
    receipt: {
        state: ReconcileState;
        original_servings: number;
        actual_servings: number | null;
        cooked_on: string | null;
        created_at: string;
    };
};

export type ReconcileQueue = {
    entries: ReconcileEntry[];
    next_cursor: string | null;
    total: number;
};

export type ReconcileVerbCommand = {
    verb: ReconcileVerb;
    /** Required when `verb === 'cooked_adjusted'`. */
    actual_servings?: number;
    /** Required when `verb === 'cooked_later'`. ISO date. */
    cooked_on?: string;
    /** Free-form user note; persisted on the receipt (surfaced in the
     *  history view Chunk 5 doesn't ship). */
    note?: string;
};

export type ReconcileVerbResult = {
    entry_id: string;
    new_pool: number;
    /** True when the verb didn't change anything (same latest-receipt
     *  state + fields as the incoming call). */
    idempotent: boolean;
    receipt: {
        state: ReconcileState;
        original_servings: number;
        actual_servings: number | null;
        cooked_on: string | null;
        created_at: string;
    };
};
