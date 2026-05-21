import type { MealPlan, MealPlanIngredient } from 'src/models/meal';
import type { CreatedResponse } from './axiosHttpClient';
import AxiosHttpClient from './axiosHttpClient';
import type { Page } from './queryStringBuilder';

export type MealPlanEntryCommand = {
    meal_id: string;
    scheduled_for: string;
    servings: number;
    slot: string;
};

export type CreateMealPlanCommand = {
    name: string;
    start_date: string;
    entries: MealPlanEntryCommand[];
};

export type UpdateMealPlanCommand = {
    meal_plan_id: string;
    name?: string;
    start_date?: string;
    entries?: MealPlanEntryCommand[];
};

export default class MealPlanApiService {
    private httpClient: AxiosHttpClient;

    constructor() {
        this.httpClient = new AxiosHttpClient(5170);
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
}
