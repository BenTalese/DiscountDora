import type { Recipe, RecipeTagCatalogue } from 'src/models/recipe';
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
    /** P2-08 — curated dietary / allergen-free / nutritional tags.
     *  Validated server-side against the canonical catalogue. */
    tags?: string[];
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
    /** P2-08 — when present, replaces the full tag set on the recipe.
     *  Empty array clears all tags; omit the field to leave tags
     *  untouched. */
    tags?: string[];
};

/** P2-08 — query filters for the recipes endpoint. Mirrors the
 *  `tags_include / tags_exclude / ingredient_exclude` query params the
 *  backend accepts; each is an array that's URL-encoded as repeated
 *  params. */
export type RecipeFilterArgs = {
    tags_include?: string[];
    tags_exclude?: string[];
    ingredient_exclude?: string[];
};

export default class RecipeApiService {
    private httpClient: AxiosHttpClient;

    constructor() {
        this.httpClient = new AxiosHttpClient('dora');
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

    getAllAsync = async (filters?: RecipeFilterArgs): Promise<Page<Recipe>> => {
        const qs = encodeFilterQueryString(filters);
        return await this.httpClient.get<Page<Recipe>>(`/recipes${qs}`);
    };

    /** P2-08 — pulls the canonical tag catalogue + disclaimer. The
     *  SPA caches this for the session; the picker re-renders on
     *  change but the list itself is stable across requests. */
    getTagCatalogueAsync = async (): Promise<RecipeTagCatalogue> =>
        await this.httpClient.get<RecipeTagCatalogue>('/recipes/tags');

    updateAsync = async (recipeToUpdate: UpdateRecipeCommand): Promise<void> => {
        const { recipe_id, ...payload } = recipeToUpdate;
        await this.httpClient.patch<void>(`/recipes/${recipe_id}`, payload);
    };

    markMadeAsync = async (recipeId: string): Promise<void> =>
        await this.httpClient.post<void>(`/recipes/${recipeId}/mark-made`, {});

    importFromUrlAsync = async (url: string): Promise<ImportedRecipe> =>
        await this.httpClient.post<ImportedRecipe, { url: string }>(
            '/recipes/import-from-url',
            { url },
        );
}

// Mirrors ImportedRecipeDto / ImportedIngredientDto from
// dora_api/features/recipes/import_recipe_from_url.py.
export type ImportedIngredient = {
    raw_text: string;
    stock_item_id: string | null;
    stock_item_name: string | null;
    match_score: number;
    quantity: number | null;
    unit: string | null;
    notes: string | null;
};

function encodeFilterQueryString(filters?: RecipeFilterArgs): string {
    if (!filters) return '';
    const params = new URLSearchParams();
    for (const tag of filters.tags_include ?? []) {
        if (tag) params.append('tags_include', tag);
    }
    for (const tag of filters.tags_exclude ?? []) {
        if (tag) params.append('tags_exclude', tag);
    }
    for (const term of filters.ingredient_exclude ?? []) {
        if (term) params.append('ingredient_exclude', term);
    }
    const out = params.toString();
    return out ? `?${out}` : '';
}

export type ImportedRecipe = {
    name: string;
    cuisine: string | null;
    category: string | null;
    difficulty: string | null;
    servings: number | null;
    prep_time_minutes: number | null;
    cook_time_minutes: number | null;
    instructions: string | null;
    nutrition: string | null;
    source_url: string;
    ingredients: ImportedIngredient[];
};
