// Shared types for the structured method. A plain .ts module rather than an
// SFC because `<script setup>` can't export — `RecipeStructuredMethod`,
// `RecipeStepLinksDialog` and the host page all read from here.

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

/** The slice of a step that `RecipeStepLinksDialog` owns — what the step
 *  uses, and (top-level only) which section it belongs to. Lives here rather
 *  than in the SFC because `<script setup>` can't export. */
export type StepLinks = {
    ingredient_client_ids: string[];
    tool_ids: string[];
    section_client_id: string | null;
};
