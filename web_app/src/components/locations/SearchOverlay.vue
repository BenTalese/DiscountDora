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
                v-else-if="locationHits.length === 0 && itemHits.length === 0"
                class="text-grey text-caption q-pa-lg text-center"
            >
                No matches for "{{ query }}".
            </q-card-section>

            <template v-else>
                <q-list separator class="search-results">
                    <q-item-label v-if="locationHits.length > 0" header class="search-section-header">
                        Locations
                    </q-item-label>
                    <q-item
                        v-for="hit in locationHits"
                        :key="`loc-${hit.id}`"
                        clickable
                        @click="onSelectLocation(hit.id)"
                    >
                        <q-item-section avatar><q-icon name="place" /></q-item-section>
                        <q-item-section>
                            <q-item-label>{{ hit.title }}</q-item-label>
                            <q-item-label caption>{{ hit.subtitle ?? '' }}</q-item-label>
                        </q-item-section>
                    </q-item>

                    <q-item-label v-if="itemHits.length > 0" header class="search-section-header">
                        Items
                    </q-item-label>
                    <q-item
                        v-for="hit in itemHits"
                        :key="`item-${hit.id}`"
                        clickable
                        @click="onSelectItem(hit.id)"
                    >
                        <q-item-section avatar><q-icon name="inventory_2" /></q-item-section>
                        <q-item-section>
                            <q-item-label>{{ hit.title }}</q-item-label>
                            <q-item-label caption>
                                <span v-if="hit.subtitle">{{ hit.subtitle }}</span>
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
    import SearchApiService, { type SearchResult } from 'src/services/api/searchApiService';
    import { computed, ref } from 'vue';
    import { useRouter } from 'vue-router';

    const props = defineProps<{ modelValue: boolean }>();
    const emit = defineEmits<{ (e: 'update:modelValue', value: boolean): void }>();

    const open = computed({
        get: () => props.modelValue,
        set: (v) => emit('update:modelValue', v),
    });

    const api = new SearchApiService();
    const router = useRouter();

    const query = ref('');
    const results = ref<SearchResult[]>([]);
    const loading = ref(false);
    let debounceTimer: ReturnType<typeof setTimeout> | null = null;

    const itemHits = computed(() => results.value.filter((r) => r.type === 'stock_item'));
    const locationHits = computed(() => results.value.filter((r) => r.type === 'location'));

    function onQueryChange() {
        if (debounceTimer) clearTimeout(debounceTimer);
        if (!query.value.trim()) {
            results.value = [];
            return;
        }
        debounceTimer = setTimeout(() => {
            void (async () => {
                loading.value = true;
                try {
                    const resp = await api.searchAsync(query.value, {
                        types: ['stock_item', 'location'],
                        limit: 25,
                    });
                    results.value = resp.results;
                } finally {
                    loading.value = false;
                }
            })();
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
