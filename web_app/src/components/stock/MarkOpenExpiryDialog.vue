<template>
    <!--
        DR-5 (D-008, FU-578 #2) — the mark-as-open expiry prompt.

        A promise-based `$q.dialog({ component })` prompt (shared by the stock
        row and the detail page via `useStockItemActions.planOpenToggle`), so
        the *whole* action can be aborted. Native `$q.dialog` collapses the
        Cancel button, Escape and backdrop-click all into one `onCancel`, which
        is why the old two-button prompt could only ever govern the expiry, not
        whether the item opened at all. Three explicit buttons split the
        outcomes cleanly:
          • Cancel / Escape / backdrop → `onDialogCancel`/hide ⇒ do NOT open.
          • Skip                       → open, leave expiry unchanged.
          • Update expiry              → open and set the picked expiry.
        Mirrors BaseDialog's card shell (this can't wrap BaseDialog because the
        dialog-plugin needs `dialogRef` on the QDialog itself).
    -->
    <q-dialog ref="dialogRef" @hide="onDialogHide">
        <q-card class="dora-dialog" style="min-width: 360px; max-width: 95vw">
            <q-card-section class="dora-dialog__header">
                <div class="text-h6">Marking “{{ itemName }}” as open</div>
            </q-card-section>
            <q-separator />

            <q-card-section class="column q-gutter-sm">
                <div class="dora-text-secondary">
                    Update its effective expiry? Leave as-is if opening doesn’t
                    change how fast it goes off.
                </div>
                <q-input
                    v-model="draft"
                    type="date"
                    outlined
                    dense
                    label="Effective expiry"
                    :aria-label="`Effective expiry for ${itemName}`"
                    @keydown.enter.prevent="onUpdate"
                />
            </q-card-section>

            <q-card-actions align="right" class="dora-dialog__footer">
                <BaseButton variant="ghost" label="Cancel" @click="onDialogCancel" />
                <BaseButton variant="secondary" label="Skip" @click="onSkip" />
                <BaseButton variant="primary" label="Update expiry" @click="onUpdate" />
            </q-card-actions>
        </q-card>
    </q-dialog>
</template>

<script setup lang="ts">
    import { useDialogPluginComponent } from 'quasar';
    import BaseButton from 'src/components/BaseButton.vue';
    import { ref } from 'vue';

    const props = defineProps<{
        itemName: string;
        /** Current expiry as `YYYY-MM-DD`, or '' when none is set. */
        currentExpiry: string;
    }>();

    defineEmits([...useDialogPluginComponent.emits]);

    const { dialogRef, onDialogHide, onDialogOK, onDialogCancel } =
        useDialogPluginComponent();

    const draft = ref(props.currentExpiry);

    // Skip: open the item but don't touch its expiry (`expiry: undefined`).
    function onSkip() {
        onDialogOK({ expiry: undefined });
    }

    // Update: open and set the picked expiry (empty input ⇒ clear = null).
    function onUpdate() {
        onDialogOK({ expiry: draft.value || null });
    }
</script>
