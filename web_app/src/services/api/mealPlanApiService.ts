import type { MealPlan, MealPlanIngredient, Shortfall } from 'src/models/mealPlan';
import type { CreatedResponse } from './axiosHttpClient';
import AxiosHttpClient from './axiosHttpClient';
import type { Page } from './queryStringBuilder';

export type MealPlanEntryCommand = {
    recipe_id: string;
    scheduled_for: string;
    servings: number;
    slot: string;
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
}
