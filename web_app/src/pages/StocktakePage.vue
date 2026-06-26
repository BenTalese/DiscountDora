<template>
    <div class="q-pa-md q-gutter-md">
        <PageToolbar title="Stocktake" back-to="/stock">
            <template #actions>
                <BaseButton variant="ghost" :icon="ICONS.refresh" label="Refresh" @click="loadQueue" />
            </template>
        </PageToolbar>

        <q-card flat bordered>
            <q-card-section class="row items-center q-gutter-md">
                <q-icon
                    name="fact_check"
                    size="48px"
                    :color="overdueCount > 0 ? 'warning' : 'positive'"
                />
                <div class="col">
                    <div class="text-h6">
                        {{ overdueCount === 0
                            ? "You're all caught up."
                            : `${overdueCount} item${overdueCount === 1 ? '' : 's'} need a check.` }}
                    </div>
                    <div class="text-caption dora-text-muted">
                        Focused review goes through them one at a time. Most-
                        overdue first; tap "Still correct" to confirm a level
                        without changing it.
                    </div>
                    <div v-if="mostOverdue" class="text-caption dora-text-muted-7 q-mt-xs">
                        Top of the queue:
                        <strong>{{ mostOverdue.name }}</strong>
                        <span v-if="mostOverdue.overdue_days > 0">
                            · {{ mostOverdue.overdue_days }} day(s) overdue
                        </span>
                        <span v-else>· never checked</span>
                    </div>
                </div>
                <BaseButton
                    variant="primary"
                    size="lg"
                    :icon="ICONS.play_arrow"
                    label="Start review"
                    :disable="overdueCount === 0 || loading"
                    @click="onStart"
                />
            </q-card-section>
        </q-card>

        <q-card v-if="overdueCount > 0" flat bordered>
            <q-card-section>
                <div class="text-subtitle2 q-mb-sm">Up next</div>
                <q-list separator dense>
                    <q-item v-for="item in queue.slice(0, 10)" :key="item.stock_item_id">
                        <q-item-section>
                            <q-item-label>{{ item.name }}</q-item-label>
                            <q-item-label caption>
                                {{ item.stock_level_name ?? '—' }}
                                <span v-if="item.stock_location_name">
                                    · {{ item.stock_location_name }}
                                </span>
                            </q-item-label>
                        </q-item-section>
                        <q-item-section side>
                            <q-chip
                                dense
                                size="sm"
                                :color="item.overdue_days < 0 ? 'grey-7' : 'warning'"
                                text-color="white"
                            >
                                {{ item.overdue_days < 0
                                    ? 'never checked'
                                    : `${item.overdue_days}d overdue` }}
                            </q-chip>
                        </q-item-section>
                    </q-item>
                </q-list>
                <div v-if="queue.length > 10" class="text-caption dora-text-muted q-mt-sm">
                    …and {{ queue.length - 10 }} more.
                </div>
            </q-card-section>
        </q-card>
    </div>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import BaseButton from 'src/components/BaseButton.vue';
    import PageToolbar from 'src/components/PageToolbar.vue';
    import { computed, onMounted, ref } from 'vue';
    import { useRouter } from 'vue-router';
    import StocktakeApiService, { type StocktakeQueueItem } from 'src/services/api/stocktakeApiService';

    const router = useRouter();
    const api = new StocktakeApiService();
    const queue = ref<StocktakeQueueItem[]>([]);
    const total = ref(0);
    const loading = ref(false);

    const overdueCount = computed(() => total.value);
    const mostOverdue = computed(() => queue.value[0] ?? null);

    async function loadQueue() {
        loading.value = true;
        try {
            const result = await api.queueAsync(100);
            queue.value = result.items;
            total.value = result.total;
        } finally {
            loading.value = false;
        }
    }

    function onStart() {
        void router.push('/stocktake/run');
    }

    onMounted(loadQueue);
</script>
