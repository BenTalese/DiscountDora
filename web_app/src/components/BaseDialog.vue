<template>
    <!--
        A3 — standard modal shell. Wraps q-dialog + q-card so dialog
        behaviour is defined in one place:
          • NOT persistent by default → backdrop click and Esc both
            dismiss, and dismiss means *cancel* (no commit, no navigation).
            Pass :persistent only for flows that must not be dismissed by
            mistake (e.g. an in-progress scan).
          • token-based radius / max-width so every dialog matches.
          • optional standardised header (title + close) and footer
            (#actions slot, right-aligned).
        Unknown attrs (position, transition-show, …) auto-forward to the
        root q-dialog because it is the single root element.
    -->
    <q-dialog
        :model-value="modelValue"
        :persistent="persistent"
        @update:model-value="(v) => emit('update:modelValue', v)"
        @hide="onHide"
    >
        <q-card class="dora-dialog" :class="cardClass" :style="cardStyle">
            <!-- Standard header: title on the left, optional close on the right -->
            <template v-if="title || $slots.header">
                <q-card-section class="dora-dialog__header row items-center no-wrap">
                    <slot name="header">
                        <div class="text-h6 col">{{ title }}</div>
                    </slot>
                    <BaseButton
                        v-if="closable"
                        variant="icon"
                        :icon="ICONS.close"
                        aria-label="Close"
                        @click="cancel"
                    />
                </q-card-section>
                <q-separator />
            </template>

            <!-- Body -->
            <slot :cancel="cancel" />

            <!-- Standard footer — right-aligned action buttons -->
            <q-card-actions v-if="$slots.actions" align="right" class="dora-dialog__footer">
                <slot name="actions" :cancel="cancel" />
            </q-card-actions>
        </q-card>
    </q-dialog>
</template>

<script setup lang="ts">
    import { ICONS } from 'src/style/icons';
    import BaseButton from 'src/components/BaseButton.vue';

    withDefaults(
        defineProps<{
            modelValue: boolean;
            /** Optional title — renders the standardised header + separator. */
            title?: string;
            /** Only set for flows that must not be dismissed by accident. */
            persistent?: boolean;
            /** Show an X close button in the standardised header. */
            closable?: boolean;
            /** Inline card sizing — defaults to a sensible responsive width. */
            cardStyle?: string;
            cardClass?: string;
        }>(),
        {
            persistent: false,
            closable: false,
            cardStyle: 'min-width: 360px; max-width: 95vw',
        },
    );

    const emit = defineEmits<{
        (e: 'update:modelValue', value: boolean): void;
        // Fired whenever the dialog closes (backdrop, Esc, or cancel button).
        // Per A3, dismissal is always a cancel — never a commit/navigation.
        (e: 'cancel'): void;
    }>();

    // Close the dialog. q-dialog's @hide then fires the `cancel` event, so
    // we don't double-emit here.
    function cancel() {
        emit('update:modelValue', false);
    }

    function onHide() {
        emit('cancel');
    }
</script>

<style scoped lang="scss">
    .dora-dialog {
        border-radius: var(--radius-lg, 12px);
    }
    .dora-dialog__header {
        /* Slightly tighter than the body so the title sits close to its rule. */
        padding-bottom: var(--space-2, 8px);
    }
</style>
