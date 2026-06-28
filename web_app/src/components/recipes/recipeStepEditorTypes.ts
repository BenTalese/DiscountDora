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
    /** FU-117 — section grouping for top-level steps. References one of
     *  the sibling sections by `client_id` (or its real UUID when
     *  sections aren't being replaced), or null for the implicit "main"
     *  group. Sub-steps inherit visually from their parent — the editor
     *  doesn't expose a picker on depth-1 rows. */
    section_client_id: string | null;
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

/** FU-117 — section options for the top-level step picker. `null` value =
 *  the implicit "main" group (no named section). */
export type SectionOption = {
    value: string | null;
    label: string;
};
