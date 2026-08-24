<template>
    <!--
        The "Start cook mode?" confirm, shared by every surface that can start
        cooking (owner feedback 2026-08-19 — the cookbook skipped it while the
        recipe page showed it).

        Click-out / Esc just close (BaseDialog `v-model`); they never navigate.
        The decision about *whether* to show this at all is
        `helpers/cookModeGuard.needsCookGuard` — the caller checks that before
        opening, so this component only ever renders reasons it actually has.
    -->
    <BaseDialog
        v-model="open"
        title="Start cook mode?"
        closable
        card-style="min-width: 320px; max-width: 460px"
    >
        <q-card-section>
            <ul class="q-mt-sm q-mb-none dora-text-secondary">
                <li v-for="reason in reasons" :key="reason">{{ reasonText(reason) }}</li>
            </ul>
            <!-- Owner feedback 2026-08-24 — "missing" and "missing, but you
                 have something you could use instead" are different answers,
                 and this dialog is the last place the second one can change
                 the decision. Names, not a count: which ingredient it is, is
                 the whole point. -->
            <div v-if="substitutableNames.length > 0" class="cmg__subs">
                <q-icon :name="ICONS.swap_horiz" size="16px" />
                <span>
                    You have a substitute in stock for
                    {{ substitutableNames.join(', ') }} — swap it during cooking.
                </span>
            </div>
        </q-card-section>
        <template #actions>
            <BaseButton variant="ghost" label="Cancel" @click="open = false" />
            <!-- Only the editable surface can be dirty, so only it offers the
                 save fork; elsewhere there is one way forward. -->
            <BaseButton
                v-if="dirty"
                variant="ghost"
                label="Start without saving"
                @click="emit('start')"
            />
            <BaseButton
                v-if="dirty"
                variant="primary"
                label="Save & start"
                :loading="saving"
                @click="emit('save-and-start')"
            />
            <BaseButton
                v-else
                variant="primary"
                label="Start anyway"
                @click="emit('start')"
            />
        </template>
    </BaseDialog>
</template>

<script setup lang="ts">
    import { computed } from 'vue';
    import BaseButton from 'src/components/BaseButton.vue';
    import BaseDialog from 'src/components/BaseDialog.vue';
    import { ICONS } from 'src/style/icons';
    import type { Recipe } from 'src/models/recipe';
    import {
        cookGuardReasons,
        missingStockItemIds,
        type CookGuardReason,
    } from 'src/helpers/cookModeGuard';

    const props = withDefaults(
        defineProps<{
            modelValue: boolean;
            recipe: Recipe | null;
            /** Unsaved edits on the surface that opened this. Editable surfaces
             *  only — the cookbook leaves it false. */
            dirty?: boolean;
            /** Spins the "Save & start" button while the caller's save is in
             *  flight. */
            saving?: boolean;
            /** Names of missing ingredients the cook already has a substitute
             *  for. Supplied by the recipe page, which is the only surface
             *  that loads substitutes; everywhere else leaves it empty. */
            substitutable?: string[];
        }>(),
        { dirty: false, saving: false, substitutable: () => [] },
    );

    const emit = defineEmits<{
        (e: 'update:modelValue', value: boolean): void;
        /** Proceed without saving (or, when not dirty, just proceed). */
        (e: 'start'): void;
        /** Save first, then proceed — the caller owns the save and decides
         *  whether it succeeded. */
        (e: 'save-and-start'): void;
    }>();

    const open = computed({
        get: () => props.modelValue,
        set: (value) => emit('update:modelValue', value),
    });

    const reasons = computed(() => cookGuardReasons(props.recipe, props.dirty));
    const substitutableNames = computed(() => props.substitutable ?? []);

    const missingCount = computed(() =>
        props.recipe ? missingStockItemIds(props.recipe).length : 0,
    );
    const unlinkedCount = computed(() => props.recipe?.unlinked_ingredient_count ?? 0);

    function plural(n: number): string {
        return n === 1 ? '' : 's';
    }

    function reasonText(reason: CookGuardReason): string {
        switch (reason) {
            case 'unsaved':
                return 'You have unsaved changes.';
            case 'unknown-cookability':
                return `Cookability is unknown — ${unlinkedCount.value} ingredient${plural(unlinkedCount.value)} still need linking.`;
            case 'missing-ingredients':
                return `This recipe isn't cookable now — ${missingCount.value} ingredient${plural(missingCount.value)} missing.`;
        }
    }
</script>

<style scoped lang="scss">
    .cmg__subs {
        display: flex;
        align-items: flex-start;
        gap: var(--space-2, 8px);
        margin-top: var(--space-3, 12px);
        padding: var(--space-2, 8px) var(--space-3, 12px);
        border-radius: var(--radius-md, 6px);
        background: var(--semantic-positive-soft);
        color: var(--text-primary);
        font-size: 0.875rem;
    }
</style>
