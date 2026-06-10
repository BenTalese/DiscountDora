// C-4 Chunk 6 — shared types for the structured-steps editor. Extracted
// from the .vue files so both `RecipeStepsEditor` and `RecipeStepRow` (and
// the host page) import from a plain .ts module (cleaner than importing a
// type from a .vue SFC).

export type EditableStep = {
    client_id: string;
    parent_client_id: string | null;
    sequence: number;
    text: string;
    hint: string | null;
    ingredient_client_ids: string[];
    tool_ids: string[];
};

/** Display row enriched with the sibling index + depth, so the row
 *  component can decide whether move-up/down/sub-step are valid without
 *  re-deriving from the flat array. */
export type StepRowView = EditableStep & {
    depth: 0 | 1;
    sibling_index: number;
    sibling_total: number;
};

export type IngredientOption = {
    /** Either the ingredient's existing `recipe_ingredient_id` (update path
     *  without an ingredient replace) or its `client_id` (create path /
     *  update with ingredient replace). The editor treats both as opaque
     *  strings — matches the server contract. */
    value: string;
    label: string;
};

export type ToolOption = {
    value: string;
    label: string;
};
