import type { Meal } from 'src/models/meal';
import type { CreatedResponse } from './axiosHttpClient';
import AxiosHttpClient from './axiosHttpClient';
import { createQueryString, FilterOperator, type Page } from './queryStringBuilder';

export type CreateMealCommand = {
    name: string;
    quantity_in_stock: number;
    recipe_ids: string[];
};

export type UpdateMealCommand = {
    meal_id: string;
    name?: string;
    quantity_in_stock?: number;
    recipe_ids?: string[];
};

export default class MealApiService {
    private httpClient: AxiosHttpClient;

    constructor() {
        this.httpClient = new AxiosHttpClient(5170);
    }

    createAsync = async (command: CreateMealCommand): Promise<CreatedResponse> =>
        await this.httpClient.post<CreatedResponse>('/meals', command);

    deleteAsync = async (mealId: string): Promise<void> =>
        await this.httpClient.delete(`/meals/${mealId}`);

    getAsync = async (mealId: string): Promise<Meal> => {
        const qs = createQueryString([
            { field: 'meal_id', operator: FilterOperator.EQUAL, value: mealId }
        ]);
        const page = await this.httpClient.get<Page<Meal>>(`/meals${qs}`);
        return page.items[0]!;
    };

    getAllAsync = async (): Promise<Page<Meal>> =>
        await this.httpClient.get<Page<Meal>>('/meals');

    updateAsync = async (command: UpdateMealCommand): Promise<void> => {
        const { meal_id, ...payload } = command;
        await this.httpClient.patch<void>(`/meals/${meal_id}`, payload);
    };

    adjustStockAsync = async (mealId: string, delta: number): Promise<void> =>
        await this.httpClient.post<void>(`/meals/${mealId}/adjust-stock`, { delta });
}
