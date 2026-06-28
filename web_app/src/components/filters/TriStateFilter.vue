<template>
    <!--
        Generalised tri-state include/exclude filter. Each option cycles
        through +/-/neutral on click; the dropdown stays open while
        cycling so the user can flip several in one pass.

        Generalised in three axes:
        - `options[].category?` — when present, options are grouped under a
          header (matches the original DietaryTagFilter shape). When all
          options omit it, the list renders flat.
        - `options[].dotColour?` — renders a coloured dot in the avatar
          slot alongside the +/- state icon. Used by surfaces that need
          a quick at-a-glance signal per row (e.g. stock-level on the
          "Uses ingredients" filter).
        - `searchable` — adds a typeahead `q-input` at the top of the
          dropdown that case-insensitively filters by label. Essential
          for options lists with more than ~30 rows.

        Single component, multiple consumers (R-001). DietaryTagFilter is
        now a thin wrapper around this one (kept for API stability at
        call sites; new uses should consume `TriStateFilter` directly).
    -->
    <BaseDropdown
        :label="buttonLabel"
        :icon="ICONS.tune"
        outline
        dense
        :color="activeCount > 0 ? 'primary' : undefined"
    >
        <div :style="{ minWidth: '260px', maxWidth: '320px' }">
            <q-input
                v-if="searchable"
                v-model="searchText"
                dense
                outlined
                clearable
                debounce="100"
                :placeholder="searchPlaceholder ?? 'Search…'"
                class="q-ma-sm"
                autofocus
            >
                <template #prepend>
                    <q-icon :name="ICONS.search" size="18px" />
                </template>
            </q-input>
            <!-- Optional sort axis selector. Renders only when the caller
                 hands in `sortOptions`. `q-btn-toggle` with `outline` so
                 the buttons read as distinct segments — the previous
                 `flat` look was too subtle. -->
            <div
                v-if="sortOptionsList.length > 0"
                class="tri-state-filter__sort row items-center q-px-sm q-py-xs q-gutter-sm"
            >
                <span class="text-caption dora-text-muted">Sort by</span>
                <BaseSegmented
                    v-model="activeSort"
                    :options="sortToggleOptions"
                    flat
                    class="tri-state-filter__sort-toggle"
                />
            </div>
            <q-separator v-if="sortOptionsList.length > 0" />

            <q-list dense>
                <template v-for="group in visibleGroups" :key="group.category ?? '__flat__'">
                    <q-item-label
                        v-if="group.category"
                        header
                        class="q-pb-none"
                    >
                        {{ group.category }}
                    </q-item-label>
                    <q-item
                        v-for="opt in group.options"
                        :key="opt.value"
                        clickable
                        @click="cycle(opt.value)"
                    >
                        <q-item-section avatar>
                            <div class="row items-center q-gutter-xs no-wrap">
                                <q-icon
                                    v-if="opt.dotColour !== undefined"
                                    name="circle"
                                    size="10px"
                                    :color="opt.dotColour ?? undefined"
                                    :class="{ 'dora-text-muted': !opt.dotColour }"
                                />
                                <q-icon
                                    :name="stateIcon(opt.value)"
                                    :color="stateColour(opt.value)"
                                />
                            </div>
                        </q-item-section>
                        <q-item-section>{{ opt.label }}</q-item-section>
                    </q-item>
                </template>
                <q-item v-if="visibleGroups.length === 0 && searchText">
                    <q-item-section class="dora-text-muted">
                        No matches for "{{ searchText }}".
                    </q-item-section>
                </q-item>
                <q-item v-else-if="options.length === 0">
                    <q-item-section class="dora-text-muted">
                        Nothing to filter by yet.
                    </q-item-section>
                </q-item>
                <q-separator v-if="activeCount > 0" />
                <q-item v-if="activeCount > 0" clickable @click="clearAll">
                    <q-item-section avatar><q-icon :name="ICONS.filter_alt_off" /></q-item-section>
                    <q-item-section>Clear</q-item-section>
                </q-item>
            </q-list>
        </div>
    </BaseDropdown>
</template>

<script setup lang="ts">
    import { computed, ref } from 'vue';
    import { ICONS } from 'src/style/icons';
    import BaseDropdown from 'src/components/BaseDropdown.vue';
    import BaseSegmented from 'src/components/BaseSegmented.vue';

    import type {
        TriStateOption,
        TriStateSort,
    } from 'src/components/filters/triStateFilterTypes';

    const props = withDefaults(
        defineProps<{
            options: TriStateOption[];
            include: string[];
            exclude: string[];
            label?: string;
            searchable?: boolean;
            searchPlaceholder?: string;
            sortOptions?: TriStateSort[];
            defaultSort?: string;
        }>(),
        {
            label: 'Filter',
            searchable: false,
            sortOptions: () => [],
        },
    );

    const emit = defineEmits<{
        (e: 'update:include', value: string[]): void;
        (e: 'update:exclude', value: string[]): void;
    }>();

    const searchText = ref('');
    // Local convenience refs so the template never accesses the optional
    // `sortOptions` prop directly (exactOptionalPropertyTypes — the type
    // resolves to `TriStateSort[] | undefined` in template scope even
    // with the `() => []` default).
    const sortOptionsList = computed<TriStateSort[]>(() => props.sortOptions ?? []);
    const sortToggleOptions = computed(() =>
        sortOptionsList.value.map((s) => ({ label: s.label, value: s.value })),
    );
    const activeSort = ref<string>(
        props.defaultSort ?? sortOptionsList.value[0]?.value ?? '',
    );

    const activeCount = computed(() => props.include.length + props.exclude.length);

    const buttonLabel = computed(() =>
        activeCount.value > 0 ? `${props.label} (${activeCount.value})` : props.label,
    );

    const activeSortFn = computed(() => {
        const list = sortOptionsList.value;
        if (list.length === 0) return null;
        return list.find((s) => s.value === activeSort.value) ?? list[0] ?? null;
    });

    /** Sort → filter → group. Selected items always render even if they
     *  don't match the search, so the user can find what they've already
     *  picked to clear it without dropping the query. Sort runs first
     *  so categorised lists honour the chosen axis within each header. */
    const visibleGroups = computed(() => {
        const query = searchText.value.trim().toLowerCase();
        const matches = (opt: TriStateOption) => {
            if (props.include.includes(opt.value)) return true;
            if (props.exclude.includes(opt.value)) return true;
            if (!query) return true;
            return opt.label.toLowerCase().includes(query);
        };

        const sorted = activeSortFn.value
            ? [...props.options].sort(activeSortFn.value.compare)
            : props.options;

        const buckets = new Map<string | undefined, TriStateOption[]>();
        for (const opt of sorted) {
            if (!matches(opt)) continue;
            const key = opt.category;
            if (!buckets.has(key)) buckets.set(key, []);
            buckets.get(key)!.push(opt);
        }
        return [...buckets.entries()].map(([category, opts]) => ({
            category,
            options: opts,
        }));
    });

    function stateOf(value: string): 'include' | 'exclude' | 'neutral' {
        if (props.include.includes(value)) return 'include';
        if (props.exclude.includes(value)) return 'exclude';
        return 'neutral';
    }

    function stateIcon(value: string): string {
        const s = stateOf(value);
        if (s === 'include') return 'mdi-plus-circle';
        if (s === 'exclude') return 'mdi-minus-circle';
        return 'mdi-circle-outline';
    }

    function stateColour(value: string): string {
        const s = stateOf(value);
        if (s === 'include') return 'positive';
        if (s === 'exclude') return 'negative';
        return 'grey';
    }

    // neutral → include → exclude → neutral.
    function cycle(value: string) {
        const s = stateOf(value);
        const include = props.include.filter((v) => v !== value);
        const exclude = props.exclude.filter((v) => v !== value);
        if (s === 'neutral') {
            include.push(value);
        } else if (s === 'include') {
            exclude.push(value);
        }
        emit('update:include', include);
        emit('update:exclude', exclude);
    }

    function clearAll() {
        emit('update:include', []);
        emit('update:exclude', []);
    }
</script>

<style scoped lang="scss">
    // Sort row sits between the search input and the options list — give
    // it a subtle background to read as its own band rather than floating
    // in the panel padding.
    .tri-state-filter__sort {
        background: var(--surface-sunken);
        border-radius: var(--radius-md);
        margin: 0 8px 4px;
    }
    // Segmented-button look. Quasar's q-btn-toggle in `flat` mode keeps
    // the *background* transparent on the active button (toggle-color
    // only retints the text), which made the active state invisible.
    // Drive the active visual directly from `aria-pressed="true"` —
    // which Quasar always sets on the selected toggle — so we control
    // both background and text-colour ourselves and stay theme-token-
    // aware (R-002).
    .tri-state-filter__sort-toggle {
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-md);
        overflow: hidden;
        background: var(--surface-card);
    }
    .tri-state-filter__sort-toggle :deep(.q-btn) {
        min-height: 28px;
        padding: 0 14px;
        font-size: 0.85em;
        font-weight: 500;
        border-radius: 0;
        color: var(--text-secondary);
    }
    .tri-state-filter__sort-toggle :deep(.q-btn[aria-pressed='true']) {
        background: var(--brand-primary);
        color: var(--text-on-primary, white);
        font-weight: 600;
    }
</style>
