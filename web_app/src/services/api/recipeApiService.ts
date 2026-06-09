import type { Recipe, RecipeTagCatalogue } from 'src/models/recipe';
import type { CreatedResponse } from './axiosHttpClient';
import AxiosHttpClient, { resolveBaseURL } from './axiosHttpClient';
import { type Page } from './queryStringBuilder';

/** C-4 Chunk 5 — URL for a recipe's image (served as raw bytes). Pass a
 *  `version` (e.g. a counter bumped after upload) to bust the browser cache. */
export function recipeImageUrl(recipeId: string, version?: number | string): string {
    const base = resolveBaseURL('dora');
    const suffix = version !== undefined ? `?v=${encodeURIComponent(String(version))}` : '';
    return `${base}/recipes/${recipeId}/image${suffix}`;
}

export type CreateRecipeIngredientCommand = {
    stock_item_id: string;
    quantity: number | null;
    unit: string | null;
    notes: string | null;
    /** C-4 Chunk 6 — optional client-side identifier so a structured step's
     *  `ingredient_client_ids` can reference this row before the server has
     *  assigned a real UUID. Any unique string works; the editor uses crypto
     *  randomUUID. Omit when no step references this ingredient. */
    client_id?: string;
    /** C-4 Chunk 10 — optional section grouping; references one of the
     *  sibling sections by `client_id` (or its real UUID when sections
     *  are not being replaced in this payload). Omit/null = unsectioned. */
    section_client_id?: string | null;
};

/** C-4 Chunk 10 — a named section on the create/update payload. */
export type RecipeSectionCommand = {
    client_id: string;
    sequence: number;
    name: string;
};

/** C-4 Chunk 6 — one structured step (or sub-step) on a create/update
 *  payload. `client_id` is required so steps can refer to one another
 *  (parent_client_id) and to ingredients (ingredient_client_ids) before
 *  the server has issued real ids. `ingredient_client_ids` accepts either
 *  the matching ingredient's `client_id` from the same payload, or — on
 *  update without an `ingredients` replace — the existing
 *  `recipe_ingredient_id`. The server resolves both forms. */
export type RecipeStepCommand = {
    client_id: string;
    parent_client_id: string | null;
    sequence: number;
    text: string;
    hint: string | null;
    ingredient_client_ids: string[];
    tool_ids: string[];
    /** C-4 Chunk 10 — optional section grouping for top-level steps. */
    section_client_id?: string | null;
};

export type CreateRecipeCommand = {
    name: string;
    // C-4 Chunk 2: cuisine + category are FK vocabulary ids (single-select).
    category_id: string | null;
    cook_time_minutes: number | null;
    cuisine_id: string | null;
    difficulty: string | null;
    instructions: string | null;
    nutrition: string | null;
    prep_time_minutes: number | null;
    recipe_collection_id: string | null;
    servings: number | null;
    /** C-4 Chunk 7 — origin URL for imported recipes. */
    source?: string | null;
    time_of_day: string | null;
    ingredients: CreateRecipeIngredientCommand[];
    /** C-4 Chunk 2 — dietary tag ids (FK to DietaryTag). */
    dietary_tag_ids?: string[];
    /** C-4 Chunk 5 — tool ids (FK to Tool). */
    tool_ids?: string[];
    /** C-4 Chunk 5 — image as a data-URL string, or null/omitted for none. */
    image?: string | null;
    /** C-4 Chunk 6 — structured steps. Empty/omitted = unstructured. */
    steps?: RecipeStepCommand[];
    /** C-4 Chunk 9 — simple nutrition kcal. */
    kcal?: number | null;
    /** C-4 Chunk 10 — named sections. Empty/omitted = flat recipe. */
    sections?: RecipeSectionCommand[];
};

export type UpdateRecipeCommand = {
    recipe_id: string;
    name?: string;
    category_id?: string | null;
    cook_time_minutes?: number | null;
    cuisine_id?: string | null;
    difficulty?: string | null;
    instructions?: string | null;
    is_favourite?: boolean;
    nutrition?: string | null;
    prep_time_minutes?: number | null;
    recipe_collection_id?: string | null;
    servings?: number | null;
    /** C-4 Chunk 7 — origin URL. Explicit null clears it. */
    source?: string | null;
    time_of_day?: string | null;
    ingredients?: CreateRecipeIngredientCommand[];
    /** C-4 Chunk 2/5 — when present, replaces the full tag/tool set. Empty
     *  array clears; omit to leave untouched. */
    dietary_tag_ids?: string[];
    tool_ids?: string[];
    /** C-4 Chunk 5 — data-URL string to set the image, null to clear, omit to
     *  leave untouched. */
    image?: string | null;
    /** C-4 Chunk 6 — structured steps. Present (even as []) = replace the
     *  full set; empty list clears all structure and the recipe falls back
     *  to plain `instructions`. Omit to leave existing steps untouched. */
    steps?: RecipeStepCommand[];
    /** C-4 Chunk 9 — simple nutrition kcal. Explicit null clears it. */
    kcal?: number | null;
    /** C-4 Chunk 10 — named sections. Present (even as []) = replace; an
     *  empty list clears all sections and rows fall back to the implicit
     *  "main" group via ON DELETE SET NULL. Omit to leave untouched. */
    sections?: RecipeSectionCommand[];
};

/** P2-08 — query filters for the recipes endpoint. Mirrors the
 *  `tags_include / tags_exclude / ingredient_exclude` query params the
 *  backend accepts; each is an array that's URL-encoded as repeated
 *  params. */
export type RecipeFilterArgs = {
    tags_include?: string[];
    tags_exclude?: string[];
    ingredient_exclude?: string[];
    /** State-ownership §3.3 — query cookability server-side instead of
     *  fetching every recipe + the whole pantry to filter in the browser.
     *  `cookable` true/false matches the recipe's `cookable` field;
     *  `max_missing` keeps recipes with at most N missing ingredients. */
    cookable?: boolean;
    max_missing?: number;
};

export default class RecipeApiService {
    private httpClient: AxiosHttpClient;

    constructor() {
        this.httpClient = new AxiosHttpClient('dora');
    }

    createAsync = async (recipeToCreate: CreateRecipeCommand): Promise<CreatedResponse> =>
        await this.httpClient.post<CreatedResponse>('/recipes', recipeToCreate);

    // C-4 Chunk 8 — copies the recipe into a sibling version (same
    // `version_group_id`). If the source had no group id yet, the server
    // allocates one and back-fills the source so both rows form the group.
    createNewVersionAsync = async (recipeId: string): Promise<CreatedResponse> =>
        await this.httpClient.post<CreatedResponse>(
            `/recipes/${recipeId}/new-version`,
            {},
        );

    deleteAsync = async (recipeId: string): Promise<void> =>
        await this.httpClient.delete(`/recipes/${recipeId}`);

    // C-4 Chunk 8 — hits the real detail endpoint so the response carries
    // `steps[]` + `version_siblings[]`. Filtering the list endpoint by id
    // (the old shape) only returned the list-shape DTO, which silently
    // dropped structured-step + version data for everything downstream.
    getAsync = async (recipeId: string): Promise<Recipe> =>
        await this.httpClient.get<Recipe>(`/recipes/${recipeId}`);

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

    cookAsync = async (recipeId: string, mealsCooked: number): Promise<{ available_meals: number } | void> =>
        await this.httpClient.post<{ available_meals: number } | void, { meals_cooked: number }>(
            `/recipes/${recipeId}/cook`,
            { meals_cooked: mealsCooked },
        );

    adjustMealsAsync = async (recipeId: string, delta: number): Promise<{ available_meals: number }> =>
        await this.httpClient.post<{ available_meals: number }, { delta: number }>(
            `/recipes/${recipeId}/adjust-meals`,
            { delta },
        );

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
    if (filters.cookable !== undefined) {
        params.append('cookable', String(filters.cookable));
    }
    if (filters.max_missing !== undefined) {
        params.append('max_missing', String(filters.max_missing));
    }
    const out = params.toString();
    return out ? `?${out}` : '';
}

export type ImportedRecipe = {
    name: string;
    // C-4 Chunk 2: importer resolves scraped names to existing vocab ids when
    // it can; the id is null (with the scraped name kept) when there's no match.
    cuisine_id: string | null;
    cuisine_name: string | null;
    category_id: string | null;
    category_name: string | null;
    difficulty: string | null;
    servings: number | null;
    prep_time_minutes: number | null;
    cook_time_minutes: number | null;
    instructions: string | null;
    nutrition: string | null;
    source_url: string;
    ingredients: ImportedIngredient[];
    /** C-4 Chunk 6 — schema.org HowToStep / HowToSection parsed into
     *  structured steps ready to feed into the create endpoint's `steps[]`.
     *  Empty when the source uses a plain string for `recipeInstructions`;
     *  the freeform `instructions` field above stays populated as fallback. */
    steps: ImportedStep[];
    /** C-4 Chunk 7 — true when no schema.org/Recipe was found and we fell
     *  back to scraping `<title>` / `og:image` / body text. The SPA shows a
     *  "couldn't auto-structure" banner so the user knows to clean up. */
    is_degraded: boolean;
};

export type ImportedStep = {
    client_id: string;
    parent_client_id: string | null;
    sequence: number;
    text: string;
    hint: string | null;
};
