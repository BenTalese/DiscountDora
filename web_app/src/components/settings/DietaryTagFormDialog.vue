<template>
    <!--
        Settings rebuild §2.11 — single-dialog create/rename for dietary tags.
        Replaces the two sequential `$q.dialog.prompt`s (name, then category)
        with one form so both fields are entered together.
    -->
    <BaseDialog
        :model-value="modelValue"
        :title="tag ? 'Rename dietary tag' : 'New dietary tag'"
        closable
        @update:model-value="(v) => emit('update:modelValue', v)"
        @cancel="emit('update:modelValue', false)"
    >
        <q-card-section class="column q-gutter-md">
            <q-input
                v-model="nameDraft"
                label="Tag name"
                placeholder="e.g. Vegan, Gluten-free"
                outlined
                dense
                autofocus
                :disable="busy"
                @keydown.enter.prevent="onConfirm"
            />
            <q-input
                v-model="categoryDraft"
                label="Group"
                placeholder="e.g. Allergen-free, Dietary pattern"
                outlined
                dense
                hint="Which group does this tag belong to?"
                :disable="busy"
                @keydown.enter.prevent="onConfirm"
            />
        </q-card-section>

        <template #actions="{ cancel }">
            <BaseButton variant="ghost" label="Cancel" :disable="busy" @click="cancel" />
            <BaseButton
                :label="tag ? 'Save' : 'Create'"
                :loading="busy"
                :disable="!canSubmit"
                @click="onConfirm"
            />
        </template>
    </BaseDialog>
</template>

<script lang="ts" setup>
    import BaseButton from 'src/components/BaseButton.vue';
    import BaseDialog from 'src/components/BaseDialog.vue';
    import type { DietaryTag } from 'src/models/recipeVocab';
    import { computed, ref, watch } from 'vue';

    const props = withDefaults(
        defineProps<{
            modelValue: boolean;
            // null = create; populated = rename.
            tag?: DietaryTag | null;
            busy?: boolean;
        }>(),
        { tag: null, busy: false },
    );

    const emit = defineEmits<{
        (e: 'update:modelValue', value: boolean): void;
        (e: 'confirm', payload: { name: string; category: string }): void;
    }>();

    const nameDraft = ref('');
    const categoryDraft = ref('');

    // Seed the drafts each time the dialog opens so a rename pre-fills and a
    // create starts clean (category defaults to "Custom" to match the old
    // create flow's prompt default).
    watch(
        () => props.modelValue,
        (open) => {
            if (!open) return;
            nameDraft.value = props.tag?.name ?? '';
            categoryDraft.value = props.tag?.category ?? (props.tag ? '' : 'Custom');
        },
        { immediate: true },
    );

    const canSubmit = computed(
        () => nameDraft.value.trim().length > 0 && categoryDraft.value.trim().length > 0,
    );

    function onConfirm() {
        if (!canSubmit.value || props.busy) return;
        emit('confirm', {
            name: nameDraft.value.trim(),
            category: categoryDraft.value.trim(),
        });
    }
</script>
