<template>
    <!--
        Owner feedback 2026-08-27 — what a step *uses* moved out of the step.

        The structured editor used to carry two multi-selects and a section
        picker on every step, inline. Three roomy controls per row is what made
        the editor read as squished, and it put the rarest edit (which tools
        does step 4 need?) at the same weight as the commonest (what does step
        4 say?). The step now edits its text in place and its links open here,
        one step at a time, where the pickers have the width they want.

        Owns no state beyond a draft: Cancel is a real cancel (R-006), and the
        page's dirty flag is only tripped on Save.
    -->
    <BaseDialog
        v-model="open"
        :title="`What ${stepName} uses`"
        closable
        card-style="min-width: 320px; max-width: 520px"
    >
        <q-card-section v-if="draft" class="column q-gutter-md">
            <BaseSelect
                v-model="draft.ingredient_client_ids"
                label="Ingredients used"
                :options="ingredientOptions"
                emit-value map-options multiple use-chips clearable
                hint="Highlights them on the ingredient list when this step is selected."
            >
                <template #prepend><q-icon :name="ICONS.restaurant_menu" size="18px" /></template>
            </BaseSelect>

            <BaseSelect
                v-model="draft.tool_ids"
                label="Tools"
                :options="toolOptions"
                emit-value map-options multiple use-chips clearable
                hint="The recipe's tool list is the sum of these — it's what the cookbook filters on."
            >
                <template #prepend><q-icon :name="ICONS.blender" size="18px" /></template>
            </BaseSelect>

            <!-- Only top-level steps carry a section; a sub-step inherits its
                 parent's, which is why the picker isn't rendered for one. -->
            <BaseSelect
                v-if="canSetSection && sectionOptions.length > 0"
                v-model="draft.section_client_id"
                label="Section"
                :options="sectionOptions"
                emit-value map-options clearable
                hint="Leave empty to keep it in the main method."
            />
        </q-card-section>

        <template #actions>
            <BaseButton variant="ghost" label="Cancel" @click="open = false" />
            <BaseButton variant="primary" label="Done" @click="onDone" />
        </template>
    </BaseDialog>
</template>

<script lang="ts" setup>
    import { computed, ref, watch } from 'vue';

    import BaseButton from 'src/components/BaseButton.vue';
    import BaseDialog from 'src/components/BaseDialog.vue';
    import BaseSelect from 'src/components/BaseSelect.vue';
    import { ICONS } from 'src/style/icons';
    import type {
        IngredientOption,
        SectionOption,
        StepLinks,
        ToolOption,
    } from 'src/components/recipes/recipeStepEditorTypes';

    const props = defineProps<{
        modelValue: boolean;
        /** "step 3" / "sub-step 1" — used in the title. */
        stepName: string;
        links: StepLinks | null;
        canSetSection: boolean;
        ingredientOptions: IngredientOption[];
        toolOptions: ToolOption[];
        sectionOptions: SectionOption[];
    }>();

    const emit = defineEmits<{
        'update:modelValue': [value: boolean];
        save: [links: StepLinks];
    }>();

    const open = computed({
        get: () => props.modelValue,
        set: (v: boolean) => emit('update:modelValue', v),
    });

    const draft = ref<StepLinks | null>(null);

    // Re-seed on every open so a second visit never shows the previous step's
    // links for a frame — same pattern as the ingredient row editor.
    watch(
        () => [props.modelValue, props.links] as const,
        ([isOpen, links]) => {
            if (!isOpen || !links) return;
            draft.value = {
                ingredient_client_ids: [...links.ingredient_client_ids],
                tool_ids: [...links.tool_ids],
                section_client_id: links.section_client_id,
            };
        },
        { immediate: true },
    );

    function onDone() {
        if (!draft.value) return;
        emit('save', {
            ingredient_client_ids: [...draft.value.ingredient_client_ids],
            tool_ids: [...draft.value.tool_ids],
            section_client_id: draft.value.section_client_id,
        });
        open.value = false;
    }
</script>
