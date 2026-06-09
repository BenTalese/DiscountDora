<template>
    <!--
        A4 — standard filter bar. One skin for every data-list page:
          • a persistent search box (#search slot) that stays OUTSIDE the
            collapsible panel — clearing/searching is always reachable;
          • a collapsible filter panel (#filters slot) that defaults to
            shown on desktop, hidden on mobile;
          • an active-filter count badge on the toggle;
          • a single standard "Clear filters" button that only appears when
            ≥1 filter is active.
        The page owns its actual filter fields + predicates; this component
        only standardises the mechanics/skin around them.
    -->
    <div class="filter-bar q-py-md">
        <div class="filter-bar__top row items-center q-gutter-sm no-wrap">
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

        <q-slide-transition>
            <div v-if="expanded && $slots.filters" class="filter-bar__panel">
                <slot name="filters" />
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
        }>(),
        { activeCount: 0, toggleLabel: 'Filters' },
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
