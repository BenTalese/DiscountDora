<template>
    <!--
        A filter control that IS a form field, with an arbitrary panel behind it.

        Owner feedback 2026-08-19: "some filters or inputs have inconsistent
        styling — the default input from Quasar is being styled with a more
        dull/faded colour and others are getting a bright colour … when I tap
        and hold to drag on the Quasar ones they brighten as they get focus, the
        quick filters and custom input do not" and "custom filters now have
        their dropdown arrow not at the right edge … can we not achieve
        uniformity via base components?"

        The answer to both is the same, and it is not more CSS. The custom
        filters were `q-btn-dropdown`s — buttons — sitting in a row of
        `q-field`s, so they had a button's resting colour, a button's (absent)
        focus treatment, and a caret that trails the label instead of pinning to
        the field's right edge. `RecipesOverview`'s own style block admitted it:
        "a button pretending to be a field". Every one of those differences is
        something `q-field` already gets right, so this wrapper stops
        re-deriving them and renders a real `q-field` instead:

          - resting border / label / text colours come from the same Quasar
            field styles as the neighbouring `q-select`s (R-003 — one authority
            for the field look, not a per-page copy of it);
          - the open state repaints the field's `::after` layer 2px in
            `--brand-primary` — which is *exactly* the mechanism Quasar uses for
            a focused `outlined` field (measured live: a resting field has a 1px
            `::before` and a 2px transparent `::after`). So the control brightens
            on tap-and-hold like its neighbours. QField has no `focused` *prop*
            — only a slot-scope flag — so this can't be delegated;
          - the caret sits in `#append`, which is the field's right edge, and
            uses **Quasar's own** `iconSet.arrow.dropdown` — the same value
            QSelect renders — rather than a glyph we picked to look similar;
          - `clearable` behaves like a `q-select`'s, using the icon set's
            `field.clear`.

        The panel is a slot, so this stays presentation-only: `TriStateFilter`
        keeps owning +/- semantics, and any future multi-select-with-a-custom-
        body filter can reuse the chrome without reinventing the trigger.
    -->
    <div
        class="base-filter-field"
        :class="{
            'base-filter-field--active': active,
            'base-filter-field--open': menuOpen,
        }"
    >
        <q-field
            ref="fieldRef"
            :model-value="summary"
            :label="label"
            outlined
            dense
            stack-label
        >
            <template v-if="icon" #prepend>
                <q-icon :name="icon" size="18px" />
            </template>
            <!-- `#control` is what makes the field non-native: it renders the
                 summary line where a `q-select` renders its selected item. The
                 tabindex is what lets the keyboard reach it, and `role=button`
                 + `aria-haspopup` tell a screen reader it opens something. -->
            <template #control>
                <div
                    class="base-filter-field__control self-center full-width no-outline"
                    tabindex="0"
                    role="button"
                    aria-haspopup="listbox"
                    :aria-expanded="menuOpen"
                    :aria-label="label"
                >
                    <span v-if="summary" class="base-filter-field__summary">{{ summary }}</span>
                    <span v-else class="base-filter-field__placeholder">{{ emptyText }}</span>
                </div>
            </template>
            <template #append>
                <!-- Clear sits before the caret, same order a `q-select` puts
                     them in. `@click.stop` so clearing doesn't also toggle the
                     panel open. -->
                <q-icon
                    v-if="clearable && active"
                    :name="$q.iconSet.field.clear"
                    class="cursor-pointer base-filter-field__clear"
                    size="18px"
                    role="button"
                    :aria-label="`Clear ${label}`"
                    @click.stop="emit('clear')"
                />
                <q-icon
                    :name="$q.iconSet.arrow.dropdown"
                    class="base-filter-field__caret"
                />
            </template>
        </q-field>

        <!-- Anchored to the wrapper (this component's root) rather than to the
             field's inner control, so `fit` matches the control's full width
             and the menu can't sit inset from the border. -->
        <q-menu
            fit
            :offset="[0, 4]"
            @show="onMenuShow"
            @hide="menuOpen = false"
        >
            <slot />
        </q-menu>
    </div>
</template>

<script setup lang="ts">
    import { ref } from 'vue';
    import { useQuasar } from 'quasar';

    const $q = useQuasar();

    withDefaults(
        defineProps<{
            /** Field label. Always stacked — the summary line sits under it. */
            label: string;
            /** Leading glyph, matching the surface the filter narrows. */
            icon?: string | undefined;
            /** One-line description of the current selection. Empty = nothing
             *  chosen, which renders `emptyText` in the muted placeholder ink. */
            summary?: string;
            /** Shown in place of the summary when nothing is selected. */
            emptyText?: string;
            /** Whether anything is selected. Drives the clear affordance and
             *  the active border tint. Kept separate from `summary` so a
             *  caller can render a summary for a neutral state if it wants. */
            active?: boolean;
            /** Renders a clear icon in `#append` when `active`; emits `clear`. */
            clearable?: boolean;
        }>(),
        {
            icon: undefined,
            summary: '',
            emptyText: 'Any',
            active: false,
            clearable: true,
        },
    );

    const emit = defineEmits<{ (e: 'clear'): void }>();

    /** Drives the open/focused paint below, and is moved to the control for
     *  real keyboard focus when the panel opens. */
    const menuOpen = ref(false);
    const fieldRef = ref<{ $el: HTMLElement } | null>(null);

    /** Put real DOM focus on the custom control while the panel is open, so a
     *  keyboard user lands back on the trigger when it closes. The visual
     *  focus state is painted from `--open` rather than read off `:focus`,
     *  because a custom `#control` gives QField nothing native to watch. */
    function onMenuShow() {
        menuOpen.value = true;
        fieldRef.value?.$el
            ?.querySelector<HTMLElement>('.base-filter-field__control')
            ?.focus();
    }
</script>

<style scoped lang="scss">
    .base-filter-field {
        position: relative;
        cursor: pointer;
    }
    .base-filter-field__control {
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        cursor: pointer;
    }
    .base-filter-field__summary {
        color: var(--text-primary);
    }
    /* Matches a `q-select`'s unselected state: the label carries the meaning,
       the value line is a muted stand-in until something is chosen. */
    .base-filter-field__placeholder {
        color: var(--text-muted);
    }
    /* Quasar rotates its own select caret on open; do the same here so the
       control animates like its neighbours rather than sitting static. */
    .base-filter-field__caret {
        transition: transform var(--motion-fast, 150ms) var(--motion-ease, ease);
    }
    .base-filter-field--open .base-filter-field__caret {
        transform: rotate(180deg);
    }
    /* An active filter tints its resting border the way the old dropdown
       tinted its whole button — same signal, field-shaped. */
    .base-filter-field--active :deep(.q-field__control:before) {
        border-color: var(--brand-primary);
    }
    /* Open = focused. `::after` is the layer Quasar itself colours in for a
       focused `outlined` field (it sits there at 2px/transparent when resting),
       so painting it here gives the identical treatment rather than an
       approximation of it. */
    .base-filter-field--open :deep(.q-field__control:after) {
        border-color: var(--brand-primary);
    }
</style>
