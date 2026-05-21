<template>
    <q-dialog v-model="open" maximized-on-mobile transition-show="fade" transition-hide="fade">
        <q-card style="min-width: 380px; max-width: 720px; width: 100%">
            <q-card-section class="row items-center q-pb-none">
                <q-icon name="search" size="22px" class="q-mr-sm" />
                <q-input
                    v-model="query"
                    borderless
                    dense
                    autofocus
                    class="col"
                    placeholder="Search items and locations…"
                    @update:model-value="onQueryChange"
                />
                <q-btn flat round dense icon="close" v-close-popup />
            </q-card-section>

            <q-separator />

            <q-card-section v-if="loading" class="text-center q-pa-lg">
                <q-spinner color="primary" size="32px" />
            </q-card-section>

            <q-card-section
                v-else-if="!query.trim()"
                class="text-grey text-caption q-pa-lg text-center"
            >
                Start typing to find items or locations.
            </q-card-section>

            <q-card-section
                v-else-if="results && results.items.length === 0 && results.locations.length === 0"
                class="text-grey text-caption q-pa-lg text-center"
            >
                No matches for "{{ query }}".
            </q-card-section>

            <template v-else-if="results">
                <q-list separator class="search-results">
                    <q-item-label
                        v-if="results.locations.length > 0"
                        header
                        class="search-section-header"
                    >
                        Locations
                    </q-item-label>
                    <q-item
                        v-for="hit in results.locations"
                        :key="`loc-${hit.id}`"
                        clickable
                        @click="onSelectLocation(hit.id)"
                    >
                        <q-item-section avatar>
                            <q-icon name="place" />
                        </q-item-section>
                        <q-item-section>
                            <q-item-label>{{ hit.name }}</q-item-label>
                            <q-item-label caption>
                                {{ hit.breadcrumb.join(' › ') }}
                            </q-item-label>
                        </q-item-section>
                    </q-item>

                    <q-item-label
                        v-if="results.items.length > 0"
                        header
                        class="search-section-header"
                    >
                        Items
                    </q-item-label>
                    <q-item
                        v-for="hit in results.items"
                        :key="`item-${hit.id}`"
                        clickable
                        @click="onSelectItem(hit.id)"
                    >
                        <q-item-section avatar>
                            <q-icon name="inventory_2" />
                        </q-item-section>
                        <q-item-section>
                            <q-item-label>{{ hit.name }}</q-item-label>
                            <q-item-label caption>
                                <span v-if="hit.breadcrumb.length > 0">
                                    {{ hit.breadcrumb.join(' › ') }}
                                </span>
                                <span v-else class="text-grey">Unassigned</span>
                            </q-item-label>
                        </q-item-section>
                    </q-item>
                </q-list>
            </template>
        </q-card>
    </q-dialog>
</template>

<script lang="ts" setup>
    import SearchApiService, {
        type SearchResults
    } from 'src/services/api/searchApiService';
    import { computed, ref } from 'vue';
    import { useRouter } from 'vue-router';

    const props = defineProps<{ modelValue: boolean }>();
    const emit = defineEmits<{ (e: 'update:modelValue', value: boolean): void }>();

    const open = computed({
        get: () => props.modelValue,
        set: (v) => emit('update:modelValue', v)
    });

    const api = new SearchApiService();
    const router = useRouter();

    const query = ref('');
    const results = ref<SearchResults | null>(null);
    const loading = ref(false);
    let debounceTimer: ReturnType<typeof setTimeout> | null = null;

    function onQueryChange() {
        if (debounceTimer) clearTimeout(debounceTimer);
        if (!query.value.trim()) {
            results.value = null;
            return;
        }
        // 200ms debounce so we don't hammer the API on every keystroke; the
        // overlay-style UX needs to feel snappy but not chatty.
        debounceTimer = setTimeout(async () => {
            loading.value = true;
            try {
                results.value = await api.searchAsync(query.value);
            } finally {
                loading.value = false;
            }
        }, 200);
    }

    function onSelectItem(id: string) {
        open.value = false;
        void router.push(`/stock/${id}`);
    }

    function onSelectLocation(id: string) {
        open.value = false;
        void router.push(`/locations/${id}`);
    }
</script>

<style scoped>
    .search-results {
        max-height: 60vh;
        overflow-y: auto;
    }
    .search-section-header {
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #888;
        padding-top: 8px;
    }
</style>
