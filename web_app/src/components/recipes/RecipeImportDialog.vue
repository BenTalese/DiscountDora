<template>
    <!-- IMPL_PLAN_RECIPE_IMPORTER §Chunk 5 — shared "Import a recipe" dialog.
         Replaces the pre-Chunk-5 URL-fetching flow with a paste textarea.
         Used by RecipesOverview (creates a new recipe from the import) and
         RecipeDetailPage (overwrites the current form's fields). The dialog
         owns the paste input, the source-URL input, the loading state, the
         error display, and the `importFromContentAsync` call. It emits
         `@imported(dto)` on success and lets the caller decide what to do
         next (build a create payload + navigate, or confirm-then-patch a
         local form). The caller controls the open state via `v-model`. -->
    <BaseDialog
        v-model="open"
        title="Import a recipe"
        closable
        card-style="min-width: 520px; max-width: 720px"
    >
        <q-card-section>
            <div class="text-caption dora-text-muted q-mt-xs">
                Open the recipe page in your browser, hit
                <strong>Ctrl+A</strong> then <strong>Ctrl+C</strong> to copy
                the whole page, then paste it below. Works well on
                RecipeTin Eats, AllRecipes, Half Baked Harvest, Sally's
                Baking, Simply Recipes, Taste, Woolworths, and Smitten
                Kitchen (among many others).<template v-if="degradedHint">
                    {{ ' ' }}{{ degradedHint }}</template>
            </div>
        </q-card-section>
        <q-card-section class="q-pt-none">
            <q-input
                v-model="content"
                outlined
                type="textarea"
                autogrow
                rows="14"
                label="Paste the recipe here"
                placeholder="Ctrl+V (or Cmd+V on Mac)"
                :error="!!error"
                :error-message="error ?? ''"
                :disable="importing"
                input-style="max-height: 40vh; min-height: 180px;"
            />
        </q-card-section>
        <q-card-section class="q-pt-none">
            <q-input
                v-model="sourceUrl"
                outlined
                dense
                label="Where's this from? (optional)"
                placeholder="https://example.com/recipes/lasagne"
                :disable="importing"
                hint="Saved as the recipe's source URL. Nothing fetched — this is just for your records."
            />
        </q-card-section>
        <template #actions>
            <BaseButton variant="ghost" label="Cancel" v-close-popup />
            <BaseButton
                variant="primary"
                label="Import"
                :loading="importing"
                :disable="content.trim().length === 0"
                @click="onConfirm"
            />
        </template>
    </BaseDialog>
</template>

<script setup lang="ts">
    /**
     * IMPL_PLAN_RECIPE_IMPORTER §Chunk 5 — the dialog focuses purely on
     * the import mechanism (paste content → API call → structured
     * result). What to *do* with the result lives at the call site,
     * because the two callers diverge meaningfully:
     *
     *   - RecipesOverview wires the imported DTO to `createAsync` and
     *     navigates to the new recipe.
     *   - RecipeDetailPage prompts for confirm-overwrite and then
     *     patches the local form fields.
     *
     * The dialog returns the raw `ImportedRecipe` (which carries
     * `is_degraded`) and the caller decides on the toast. The dialog
     * does NOT auto-close on success — the caller may want to keep it
     * open through a follow-up confirm dialog, or close immediately.
     * Cancel obviously closes.
     */
    import { computed, ref, watch } from 'vue';
    import BaseButton from 'src/components/BaseButton.vue';
    import BaseDialog from 'src/components/BaseDialog.vue';
    import RecipeApiService, { type ImportedRecipe } from 'src/services/api/recipeApiService';

    const props = withDefaults(
        defineProps<{
            modelValue: boolean;
            /** Optional extra sentence appended to the caption.
             *  RecipeDetailPage adds "Your existing recipe will be
             *  overwritten with the imported fields." here; the overview
             *  surface leaves it null. */
            degradedHint?: string | null;
        }>(),
        { degradedHint: null },
    );

    const emit = defineEmits<{
        (e: 'update:modelValue', value: boolean): void;
        (e: 'imported', dto: ImportedRecipe): void;
    }>();

    const recipeApi = new RecipeApiService();

    const open = computed({
        get: () => props.modelValue,
        set: (value) => emit('update:modelValue', value),
    });
    const content = ref('');
    const sourceUrl = ref('');
    const error = ref<string | null>(null);
    const importing = ref(false);

    // Reset draft state every time the dialog reopens so a cancelled
    // attempt doesn't leak into the next one.
    watch(
        () => props.modelValue,
        (isOpen) => {
            if (!isOpen) return;
            content.value = '';
            sourceUrl.value = '';
            error.value = null;
            importing.value = false;
        },
    );

    async function onConfirm(): Promise<void> {
        const value = content.value.trim();
        if (!value) return;
        importing.value = true;
        error.value = null;
        try {
            const imported = await recipeApi.importFromContentAsync(
                value,
                sourceUrl.value.trim() || undefined,
            );
            emit('imported', imported);
        } catch (err) {
            error.value =
                'Could not import. The paste might not include enough recipe structure — try a different site or copy just the recipe portion.';
            console.warn('Import failed', err);
        } finally {
            importing.value = false;
        }
    }
</script>
