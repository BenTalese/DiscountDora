export type RecipeIngredient = {
    recipe_ingredient_id: string;
    stock_item_id: string;
    stock_item_name: string;
    stock_level_id: string | null;
    stock_location_id: string | null;
    stock_location_name: string | null;
    quantity: number | null;
    unit: string | null;
    notes: string | null;
    /** Server-derived stock status for this ingredient (§3.1 contract).
     *  `is_missing` = out-of-stock or untracked; the client reads these
     *  instead of matching a stock-level name. */
    is_missing: boolean;
    is_low_stock: boolean;
    /** C-4 Chunk 10 — nullable section grouping. NULL = implicit "main"
     *  group; otherwise references one of `Recipe.sections[].section_id`. */
    section_id: string | null;
    /** Cookbook revision §1.9 — optional ingredients are ignored by the
     *  cookability rule (no second cookable value). UI renders them with
     *  an "(optional)" hint, under an Optional separator in the
     *  shopping-list picker (unchecked by default), and dimmed in cook
     *  mode. Default false (column is NOT NULL server-side). */
    is_optional: boolean;
};

/** C-4 Chunk 10 — a named group within a recipe (DEC-3 option A).
 *  Optional — a recipe with no sections renders flat, with all
 *  ingredients/steps under no header. */
export type RecipeSection = {
    section_id: string;
    sequence: number;
    name: string;
};

export type Recipe = {
    recipe_id: string;
    name: string;
    /** Total meals of this recipe currently in the pool (cooked-ahead
     *  portions). User-managed via Cook mode and the ± controls; also
     *  auto-decrements when a meal-plan entry's day passes. */
    available_meals: number;
    /** `available_meals` minus the sum of un-consumed future meal-plan
     *  servings for this recipe. Floored at 0. Derived server-side. */
    unallocated_meals: number;
    /** Raw sum of future un-consumed meal-plan servings (NOT floored).
     *  `committed_meals > available_meals` ⇒ a shortfall (shown red). */
    committed_meals: number;
    // C-4 Chunk 2: cuisine + category are FK vocabularies. The id drives the
    // edit-form selects + filters; the name is carried for display.
    cuisine_id: string | null;
    cuisine_name: string | null;
    category_id: string | null;
    category_name: string | null;
    cook_time_minutes: number | null;
    difficulty: string | null;
    instructions: string | null;
    is_favourite: boolean;
    last_made_on: string | null;
    nutrition: string | null;
    prep_time_minutes: number | null;
    recipe_collection_id: string | null;
    servings: number | null;
    /** C-4 Chunk 7 — origin URL when the recipe was imported.
     *  Null for hand-entered recipes. */
    source: string | null;
    time_of_day: string | null;
    /** C-4 Chunk 8 — version siblings share this id. Null = singleton.
     *  Detail endpoint also returns the populated `version_siblings[]`. */
    version_group_id: string | null;
    /** C-4 Chunk 9 — simple nutrition (kcal). Null when unset. Client
     *  gates render on `useNutritionMode().isSimple`. */
    kcal: number | null;
    ingredients: RecipeIngredient[];
    /** C-4 Chunk 2 — dietary tag ids (FK to DietaryTag). Empty when untagged. */
    dietary_tag_ids: string[];
    /** C-4 Chunk 5 — tool ids (FK to Tool). */
    tool_ids: string[];
    /** C-4 Chunk 5 — whether an image exists (bytes served via
     *  GET /recipes/<id>/image, never inlined here). */
    has_image: boolean;
    /** Server-owned cookability (§3.2). `missing_count` = distinct
     *  out-of-stock/untracked ingredients; `cookable` = `missing_count === 0`.
     *  The client reads these instead of recomputing from stock data. */
    cookable: boolean;
    missing_count: number;
    /** C-4 Chunk 6 — structured steps. The list endpoint sets
     *  `has_structured_steps` (cheap existence check); the detail endpoint
     *  hydrates `steps[]`. Empty `steps[]` + `has_structured_steps === false`
     *  ⇒ unstructured recipe; cook-mode falls back to splitting `instructions`
     *  on newline. */
    has_structured_steps: boolean;
    steps: RecipeStep[];
    /** C-4 Chunk 8 — populated only on the detail endpoint. Empty on
     *  the list endpoint (the client uses `version_group_id` to know
     *  whether siblings might exist). */
    version_siblings: RecipeVersionSibling[];
    /** C-4 Chunk 9 / DEC-5 — server-derived. Populated only on detail.
     *  Null when no estimate could be computed (no linked products on
     *  any ingredient). Client gates render on `useMoneyEnabled()`. */
    estimated_cost: number | null;
    estimated_cost_priced_count: number;
    estimated_cost_total_count: number;
    /** C-4 Chunk 10 — named sections (DEC-3 option A). The list endpoint
     *  populates only `section_count` for the card badge; the detail
     *  endpoint also hydrates `sections[]`. Empty sections +
     *  `section_count === 0` ⇒ recipe is flat. */
    section_count: number;
    sections: RecipeSection[];
};

/** Lightweight view of another recipe in the same version group —
 *  enough to render a "Versions" card row + jump to its detail. */
export type RecipeVersionSibling = {
    recipe_id: string;
    name: string;
    last_made_on: string | null;
    available_meals: number;
};

export type RecipeStep = {
    step_id: string;
    /** Top-level step when null; a sub-step otherwise. Exactly one level
     *  of nesting — sub-steps cannot themselves have sub-steps. */
    parent_step_id: string | null;
    sequence: number;
    text: string;
    hint: string | null;
    /** References RecipeIngredient.recipe_ingredient_id from this recipe. */
    ingredient_ids: string[];
    /** References Tool.id from the user's tools vocabulary. */
    tool_ids: string[];
    /** C-4 Chunk 10 — section grouping for top-level steps. Sub-steps
     *  carry the same id as their parent so the read path stays flat. */
    section_id: string | null;
};

export type RecipeTagDefinition = {
    value: string;
    label: string;
    category: string;
};

export type RecipeTagCatalogue = {
    tags: RecipeTagDefinition[];
    /** Plain-English disclaimer to surface alongside any tag-based UI. */
    disclaimer: string;
};

export type RecipeCollection = {
    recipe_collection_id: string;
    name: string;
};
