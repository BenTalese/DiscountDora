<template>
    <!--
        A4 — standard filter bar. One skin for every data-list page:
          • a persistent search box (#search slot) that stays OUTSIDE the
            collapsible panel — clearing/searching is always reachable;
          • a collapsible filter panel (#filters slot);
          • an active-filter count badge on the toggle;
          • a single standard "Clear filters" button that only appears when
            ≥1 filter is active.

        Feedback 2026-06-18: when a page already owns its main toolbar
        row (search, page actions), the toggle + clear buttons live in
        that toolbar via the `<FilterToggleButton>` companion instead of
        a second row here. Pass `:toolbar="false"` so the bar collapses
        to just the slide-out panel; the page wires the same `expanded`
        + `activeCount` to the companion button.
    -->
    <div class="filter-bar q-py-md">
        <div v-if="toolbar" class="filter-bar__top row items-center q-gutter-sm no-wrap">
            <div v-if="$slots.search" class="filter-bar__search col">
                <slot name="search" />
            </div>
            <q-space v-else />

            <BaseButton
                v-if="$slots.filters"
                :variant="expanded ? 'secondary' : 'ghost'"
                :icon="ICONS.tune"
                :label="toggleLabel"
                @click="expanded = !expanded"
            >
                <q-badge v-if="(activeCount ?? 0) > 0" color="primary" floating>
                    {{ activeCount }}
                </q-badge>
            </BaseButton>

            <BaseButton
                v-if="(activeCount ?? 0) > 0"
                variant="ghost"
                :icon="ICONS.filter_alt_off"
                label="Clear filters"
                @click="$emit('clear')"
            />

            <slot name="actions" />
        </div>

        <!-- Round-14: the v-if'd element is the q-slide-transition host —
             keep it bare (no padding/border/margin) so the height animates
             cleanly. Any visual chrome (card background, border, padding)
             lives on the inner `__panel-inner` wrapper instead. Mixing the
             two on a single element snaps the open/close transition. -->
        <q-slide-transition>
            <div v-if="expanded && $slots.filters" class="filter-bar__panel">
                <div class="filter-bar__panel-inner">
                    <slot name="filters" />
                </div>
            </div>
        </q-slide-transition>
    </div>
</template>

<script setup lang="ts">
    import { getCurrentInstance } from 'vue';
    import { ICONS } from 'src/style/icons';
    import BaseButton from 'src/components/BaseButton.vue';

    withDefaults(
        defineProps<{
            /** Number of active filters (drives the badge + Clear visibility). */
            activeCount?: number;
            toggleLabel?: string;
            /** When false, the in-bar toolbar row is suppressed so the page's
             *  own toolbar can host the `<FilterToggleButton>`. */
            toolbar?: boolean;
        }>(),
        { activeCount: 0, toggleLabel: 'Filters', toolbar: true },
    );

    defineEmits<{ (e: 'clear'): void }>();

    // Vue 3.4 defineModel — optional v-model. (defineModel's `default` is
    // hoisted outside setup so it can't read `$q`; we initialise below
    // instead.)
    const expanded = defineModel<boolean>({ default: false });

    // C-1 Chunk 2 / L95 — filter panel hidden by default on desktop too.
    // Previously opened automatically on >sm; flipped to always start
    // closed so the page header reads as one tidy toolbar (the user
    // toggles the panel when they actually want to filter). Parents
    // that v-model the expanded state still own it.
    const instance = getCurrentInstance();
    const parentBound =
        !!instance?.vnode.props &&
        ('modelValue' in instance.vnode.props ||
            'onUpdate:modelValue' in instance.vnode.props);
    if (!parentBound) {
        expanded.value = false;
    }
</script>

<style scoped lang="scss">
    /* FU-012 — calmer "sunken well" panel treatment, standardised across
       every page that uses FilterBar. The collapsible panel reads as a
       recessed tool tray tucked under the toolbar, not another card on
       top of an already-card-heavy page.

       Panel chrome stays on the OUTER `.filter-bar__panel` (the
       q-slide-transition host) so the rounded corners are present from
       frame one of the open animation. Padding lives on `__panel-inner`.

       Outer `.filter-bar` padding is shrunk from the template's q-py-md
       (16px) to 4px so the panel doesn't double-space against the
       toolbar above. */
    .filter-bar {
        padding-top: 4px;
        padding-bottom: 4px;
    }
    .filter-bar__panel {
        background: var(--surface-sunken);
        border-radius: 6px;
        margin-top: 4px;
    }
    .filter-bar__panel-inner {
        padding: 12px 16px;
    }
</style>
