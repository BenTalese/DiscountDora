<template>
    <!--
        One editor surface for all three step styles.

        Owner feedback 2026-08-24, two problems with one answer:
          • the structural editor hid behind a "Reorder steps, link
            ingredients & tools" expansion whose label changed per style —
            awkward, and invisible on a phone until you scrolled past the
            whole method;
          • editing free text through an inline popup on a phone raised the
            keyboard over the field, so a one-line method was typed blind.
        Both are gone if editing the method is one pencil that opens a real
        surface. Maximised on a phone (the field sits at the top, above the
        keyboard, and the sheet — not the page — scrolls); a normal dialog on
        a desktop.

        It owns no state: every change is emitted straight back to the page,
        which holds the form and the dirty flag (R-003).
    -->
    <BaseDialog
        v-model="open"
        :title="title"
        closable
        :maximized="compact"
        card-style="min-width: 0; width: min(760px, 94vw)"
    >
        <q-card-section class="rmed__body">
            <!-- Free text — the field is the whole editor. -->
            <q-input
                v-if="mode === 'freeform'"
                :model-value="instructions ?? ''"
                type="textarea"
                outlined
                autogrow
                autofocus
                label="Instructions"
                hint="One line per step reads best in cook mode."
                @update:model-value="(v) => emit('update:instructions', String(v ?? ''))"
            />

            <RecipeStepsEditor
                v-else-if="mode === 'structured'"
                :steps="steps"
                :ingredient-options="ingredientOptions"
                :tool-options="toolOptions"
                :section-options="sectionOptions"
                @update:steps="(v) => emit('update:steps', v)"
            />

            <RecipeStepImagesEditor
                v-else
                :model-value="stepImages"
                @update:model-value="(v) => emit('update:step-images', v)"
            />
        </q-card-section>

        <template #actions>
            <BaseButton variant="primary" label="Done" @click="open = false" />
        </template>
    </BaseDialog>
</template>

<script lang="ts" setup>
    import { computed } from 'vue';
    import { useQuasar } from 'quasar';

    import BaseButton from 'src/components/BaseButton.vue';
    import BaseDialog from 'src/components/BaseDialog.vue';
    import RecipeStepsEditor from 'src/components/recipes/RecipeStepsEditor.vue';
    import RecipeStepImagesEditor from 'src/components/recipes/RecipeStepImagesEditor.vue';
    import type {
        EditableStep,
        IngredientOption,
        SectionOption,
        ToolOption,
    } from 'src/components/recipes/recipeStepEditorTypes';
    import type { EditableStepImage } from 'src/components/recipes/recipeStepImageEditorTypes';
    import type { RecipeStepsMode } from 'src/models/recipe';

    const props = defineProps<{
        modelValue: boolean;
        mode: RecipeStepsMode;
        steps: EditableStep[];
        instructions: string | null;
        stepImages: EditableStepImage[];
        ingredientOptions: IngredientOption[];
        toolOptions: ToolOption[];
        sectionOptions: SectionOption[];
    }>();

    const emit = defineEmits<{
        (e: 'update:modelValue', value: boolean): void;
        (e: 'update:steps', value: EditableStep[]): void;
        (e: 'update:instructions', value: string): void;
        (e: 'update:step-images', value: EditableStepImage[]): void;
    }>();

    const $q = useQuasar();
    const compact = computed(() => $q.screen.lt.sm);

    const open = computed({
        get: () => props.modelValue,
        set: (v) => emit('update:modelValue', v),
    });

    const title = computed(() => {
        switch (props.mode) {
            case 'structured': return 'Edit steps';
            case 'image': return 'Edit step photos';
            default: return 'Edit instructions';
        }
    });
</script>

<style scoped lang="scss">
    .rmed__body {
        /* The dialog scrolls its own body rather than the page behind it
           (D-011). Maximised on a phone, so the cap only bites on desktop. */
        max-height: 70vh;
        overflow-y: auto;
    }
</style>
