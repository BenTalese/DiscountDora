<template>
    <!-- FU-102 — shared "Import from URL" dialog. Used by RecipesOverview
         (creates a new recipe from the import) and RecipeDetailPage
         (overwrites the current form's fields). The dialog owns the URL
         input, the loading state, the error display, and the
         `importFromUrlAsync` call. It emits `@imported(dto)` on success
         and lets the caller decide what to do next (build a create
         payload + navigate, or confirm-then-patch a local form). The
         caller controls the open state via `v-model`. -->
    <BaseDialog
        v-model="open"
        title="Import from URL"
        closable
        card-style="min-width: 460px; max-width: 600px"
    >
        <q-card-section>
            <div class="text-caption dora-text-muted q-mt-xs">
                Works on recipe sites that publish
                <strong>schema.org Recipe JSON-LD</strong> — the format most
                blogs, BBC Good Food, NYT Cooking, Serious Eats, AllRecipes,
                and similar publishers use. Other URLs still import: we'll
                pull the page title and text into Instructions so you can
                clean it up.<template v-if="degradedHint">
                    {{ ' ' }}{{ degradedHint }}</template>
            </div>
        </q-card-section>
        <q-card-section class="q-pt-none">
            <q-input
                v-model="url"
                outlined
                dense
                label="Recipe URL"
                placeholder="https://example.com/recipes/lasagne"
                :error="!!error"
                :error-message="error ?? ''"
                :disable="importing"
                @keydown.enter.prevent="onConfirm"
            />
        </q-card-section>
        <template #actions>
            <BaseButton variant="ghost" label="Cancel" v-close-popup />
            <BaseButton
                variant="primary"
                label="Import"
                :loading="importing"
                :disable="url.trim().length === 0"
                @click="onConfirm"
            />
        </template>
    </BaseDialog>
</template>

<script setup lang="ts">
    /**
     * FU-102 — extracted from RecipesOverview + RecipeDetailPage. The
     * dialog focuses purely on the import mechanism (URL → API call →
     * structured result). What to *do* with the result lives at the
     * call site, because the two callers diverge meaningfully:
     *
     *   - RecipesOverview wires the imported DTO to `createAsync` and
     *     navigates to the new recipe.
     *   - RecipeDetailPage prompts for confirm-overwrite and then patches
     *     the local form fields.
     *
     * Both flows want the same error wording + degraded-vs-success
     * branching at the toast layer, so the dialog returns the raw
     * `ImportedRecipe` (which carries `is_degraded`) and the caller
     * decides on the toast. The dialog does NOT auto-close on success —
     * the caller may want to keep it open through a follow-up confirm
     * dialog, or close immediately. Cancel obviously closes.
     */
    import { computed, ref, watch } from 'vue';
    import BaseButton from 'src/components/BaseButton.vue';
    import BaseDialog from 'src/components/BaseDialog.vue';
    import RecipeApiService, { type ImportedRecipe } from 'src/services/api/recipeApiService';

    const props = withDefaults(
        defineProps<{
            modelValue: boolean;
            /** Optional extra sentence appended to the schema.org caption.
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
    const url = ref('');
    const error = ref<string | null>(null);
    const importing = ref(false);

    // Reset draft state every time the dialog reopens so a cancelled
    // attempt doesn't leak into the next one.
    watch(
        () => props.modelValue,
        (isOpen) => {
            if (!isOpen) return;
            url.value = '';
            error.value = null;
            importing.value = false;
        },
    );

    async function onConfirm(): Promise<void> {
        const value = url.value.trim();
        if (!value) return;
        importing.value = true;
        error.value = null;
        try {
            const imported = await recipeApi.importFromUrlAsync(value);
            emit('imported', imported);
        } catch (err) {
            error.value =
                'Could not import. The URL might not publish structured recipe data.';
            console.warn('Import failed', err);
        } finally {
            importing.value = false;
        }
    }
</script>
