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
    <div class="filter-bar q-mb-md">
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
            <div v-show="expanded && $slots.filters" class="filter-bar__panel q-mt-sm">
                <slot name="filters" />
            </div>
        </q-slide-transition>
    </div>
</template>

<script setup lang="ts">
    import { computed, ref } from 'vue';
    import { useQuasar } from 'quasar';
    import { ICONS } from 'src/style/icons';
    import BaseButton from 'src/components/BaseButton.vue';

    const props = withDefaults(
        defineProps<{
            /** Number of active filters (drives the badge + Clear visibility). */
            activeCount?: number;
            /** Optional controlled expand state (v-model). Omit for built-in
                "open on desktop, closed on mobile" default. */
            modelValue?: boolean;
            toggleLabel?: string;
        }>(),
        {
            activeCount: 0,
            // `modelValue` intentionally has no default — omitting it is the
            // uncontrolled signal. (An explicit `undefined` default breaks
            // withDefaults inference under exactOptionalPropertyTypes.)
            toggleLabel: 'Filters',
        },
    );

    const emit = defineEmits<{
        (e: 'update:modelValue', value: boolean): void;
        (e: 'clear'): void;
    }>();

    const $q = useQuasar();
    // Uncontrolled default: shown on desktop (> sm), hidden on mobile.
    // Captured once on mount so a later resize doesn't yank the panel
    // open/closed under the user.
    const internal = ref($q.screen.gt.sm);

    const expanded = computed<boolean>({
        get: () => (props.modelValue === undefined ? internal.value : props.modelValue),
        set: (v) => {
            internal.value = v;
            emit('update:modelValue', v);
        },
    });
</script>
