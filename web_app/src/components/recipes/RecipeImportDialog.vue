<template>
    <!-- IMPL_PLAN_RECIPE_IMPORTER §Chunk 5 — shared "Import a recipe" dialog.
         Replaces the pre-Chunk-5 URL-fetching flow with a paste textarea.
         Used by RecipesOverview (creates a new recipe from the import). It
         had a second caller — the old recipe detail page, which overwrote the
         current form's fields — until that page was deleted on 2026-08-26;
         the redesign deliberately doesn't carry Import (FU-689). The dialog
         owns the paste input, the source-URL input, the loading state, the
         error display, and the `importFromContentAsync` call. It emits
         `@imported(dto)` on success and lets the caller decide what to do
         next (build a create payload + navigate, or confirm-then-patch a
         local form). The caller controls the open state via `v-model`.

         Sizing (owner 2026-08-19: "import recipe modal is too large for
         mobile"): the card was `min-width: 520px`, which on a 375px phone
         forced it wider than the viewport. `width: min(720px, 92vw)` keeps the
         desktop size and fits any phone. -->
    <BaseDialog
        v-model="open"
        title="Import a recipe"
        closable
        card-style="min-width: 0; width: min(720px, 92vw)"
    >
        <!-- The "hit Ctrl+A then Ctrl+C, works well on <list of sites>"
             paragraph that used to open this dialog was removed 2026-08-19
             (owner: "remove explanation text from recipe modal"). The
             instruction it carried now lives in the paste field's
             *placeholder* — "Copy the entire recipe webpage text and paste
             here" — so the guidance survives without a block of prose. The
             site list was deliberately NOT rehomed anywhere: owner call, "no
             need to publicly disclose what websites work well" (FU-679).
             `degradedHint` stays — it's a consequence ("your existing recipe
             will be overwritten"), not an explanation, and only the detail
             page passes it. -->
        <q-card-section v-if="degradedHint" class="q-pb-none">
            <div class="text-caption dora-text-muted">{{ degradedHint }}</div>
        </q-card-section>
        <q-card-section>
            <q-input
                v-model="content"
                outlined
                type="textarea"
                autogrow
                rows="14"
                label="Recipe text"
                placeholder="Copy the entire recipe webpage text and paste here"
                :error="!!error"
                :error-message="error ?? ''"
                :disable="importing"
                input-style="max-height: 40vh; min-height: 180px;"
            />
        </q-card-section>
        <q-card-section class="q-pt-none">
            <!-- Owner 2026-08-19: header above the input, and the "(optional)"
                 out of the field's own text. The heading is the field's label
                 (B3 — a placeholder is not a label), wired up with
                 `aria-labelledby` so it counts as one for a screen reader too.
                 The "Nothing fetched — just for your records" hint went with
                 the rest of the explanation text. -->
            <div id="import-source-url-label" class="text-subtitle2 q-mb-xs">
                Source URL (optional)
            </div>
            <q-input
                v-model="sourceUrl"
                outlined
                dense
                placeholder="https://example.com/recipes/lasagne"
                :disable="importing"
                aria-labelledby="import-source-url-label"
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
     * result). What to *do* with the result lives at the call site:
     * RecipesOverview wires the imported DTO to `createAsync` and navigates
     * to the new recipe. The split existed because a second caller
     * (import-over-an-existing-recipe) diverged meaningfully; that caller is
     * gone, but the seam is worth keeping — it is what makes the dialog
     * reusable by the next surface that wants a paste-import.
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
            /** Optional extra sentence appended to the caption — for a caller
             *  whose import has a consequence worth warning about (the old
             *  import-over-a-recipe flow said "Your existing recipe will be
             *  overwritten with the imported fields."). The overview surface,
             *  the only caller today, leaves it null. */
            degradedHint?: string | null;
            /** IMPL_PLAN_RECIPE_IMPORTER §Chunk 6 — content pre-fill for
             *  the PWA share-target landing. When the OS Share sheet
             *  drops a page into Dora, the overview reads the query
             *  params and passes them here so the user only has to hit
             *  Import. Applied on dialog open; a subsequent open
             *  without these props resets to blank as before. */
            prefillContent?: string;
            prefillSourceUrl?: string;
        }>(),
        {
            degradedHint: null,
            prefillContent: '',
            prefillSourceUrl: '',
        },
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
    // attempt doesn't leak into the next one. Share-target prefill
    // (Chunk 6) seeds the fields on open when the props are non-empty;
    // manual reopens (props blank) reset to empty as before.
    watch(
        () => props.modelValue,
        (isOpen) => {
            if (!isOpen) return;
            content.value = props.prefillContent ?? '';
            sourceUrl.value = props.prefillSourceUrl ?? '';
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
