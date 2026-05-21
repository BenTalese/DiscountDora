import type { Recipe } from 'src/models/recipe';
import type { CreatedResponse } from './axiosHttpClient';
import AxiosHttpClient from './axiosHttpClient';
import { createQueryString, FilterOperator, type Page } from './queryStringBuilder';

export type CreateRecipeIngredientCommand = {
    stock_item_id: string;
    quantity: number | null;
    unit: string | null;
    notes: string | null;
};

export type CreateRecipeCommand = {
    name: string;
    category: string | null;
    cook_time_minutes: number | null;
    cuisine: string | null;
    difficulty: string | null;
    instructions: string | null;
    nutrition: string | null;
    prep_time_minutes: number | null;
    recipe_collection_id: string | null;
    servings: number | null;
    time_of_day: string | null;
    ingredients: CreateRecipeIngredientCommand[];
};

export type UpdateRecipeCommand = {
    recipe_id: string;
    name?: string;
    category?: string | null;
    cook_time_minutes?: number | null;
    cuisine?: string | null;
    difficulty?: string | null;
    instructions?: string | null;
    is_favourite?: boolean;
    nutrition?: string | null;
    prep_time_minutes?: number | null;
    recipe_collection_id?: string | null;
    servings?: number | null;
    time_of_day?: string | null;
    ingredients?: CreateRecipeIngredientCommand[];
};

export default class RecipeApiService {
    private httpClient: AxiosHttpClient;

    constructor() {
        this.httpClient = new AxiosHttpClient(5170);
    }

    createAsync = async (recipeToCreate: CreateRecipeCommand): Promise<CreatedResponse> =>
        await this.httpClient.post<CreatedResponse>('/recipes', recipeToCreate);

    deleteAsync = async (recipeId: string): Promise<void> =>
        await this.httpClient.delete(`/recipes/${recipeId}`);

    getAsync = async (recipeId: string): Promise<Recipe> => {
        const qs = createQueryString([
            { field: 'recipe_id', operator: FilterOperator.EQUAL, value: recipeId }
        ]);
        const page = await this.httpClient.get<Page<Recipe>>(`/recipes${qs}`);
        return page.items[0]!;
    };

    getAllAsync = async (): Promise<Page<Recipe>> =>
        await this.httpClient.get<Page<Recipe>>('/recipes');

    updateAsync = async (recipeToUpdate: UpdateRecipeCommand): Promise<void> => {
        const { recipe_id, ...payload } = recipeToUpdate;
        await this.httpClient.patch<void>(`/recipes/${recipe_id}`, payload);
    };

    markMadeAsync = async (recipeId: string): Promise<void> =>
        await this.httpClient.post<void>(`/recipes/${recipeId}/mark-made`, {});
}
