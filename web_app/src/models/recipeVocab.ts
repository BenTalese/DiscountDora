// C-4 Chunk 2 — user-configurable recipe vocabularies. Each is a simple
// {id, name, sequence} lookup edited in settings; `recipe_count` is rolled
// up by the list endpoints for the settings delete-warnings.

export type Cuisine = {
    cuisine_id: string;
    name: string;
    sequence: number;
    recipe_count?: number;
};

export type Category = {
    category_id: string;
    name: string;
    sequence: number;
    recipe_count?: number;
};

export type DietaryTag = {
    dietary_tag_id: string;
    name: string;
    // Grouping label for the picker (e.g. "Allergen-free"); not an FK to the
    // recipe Category vocabulary.
    category: string;
    sequence: number;
    recipe_count?: number;
};

export type Tool = {
    tool_id: string;
    name: string;
    sequence: number;
    recipe_count?: number;
};
