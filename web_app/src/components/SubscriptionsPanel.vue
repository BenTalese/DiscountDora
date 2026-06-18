<template>
    <q-card flat bordered>
        <q-card-section class="row items-center q-pb-none">
            <q-avatar color="primary" text-color="white" size="32px" class="q-mr-sm">
                <q-icon :name="ICONS.price_check" size="18px" />
            </q-avatar>
            <div class="col">
                <div class="text-subtitle1">Price watch</div>
                <div class="text-caption dora-text-muted">
                    Armed price thresholds — these notify you when a product drops below your
                    target. Set new ones from the
                    <router-link to="/price-history">price-history explorer</router-link>.
                </div>
            </div>
            <q-btn flat round dense :icon="ICONS.refresh" :loading="loading" @click="refresh" />
        </q-card-section>

        <q-banner v-if="loadError" class="dora-bg-negative-soft text-negative q-ma-md" dense rounded>
            {{ loadError }}
        </q-banner>

        <div class="relative-position">
            <q-inner-loading :showing="loading && items.length === 0" />

            <q-list v-if="items.length > 0" separator>
                <q-item v-for="alert in items" :key="alert.price_alert_id">
                    <q-item-section avatar>
                        <q-avatar size="32px" class="dora-bg-sunken dora-text-secondary">
                            <q-icon :name="ICONS.trending_down" size="18px" />
                        </q-avatar>
                    </q-item-section>
                    <q-item-section>
                        <q-item-label>{{ alert.product_name }}</q-item-label>
                        <q-item-label caption>
                            {{ alert.store_name }} · notify below
                            <strong>${{ alert.threshold_unit_price.toFixed(2) }}</strong>
                            <span v-if="alert.last_fired_at">
                                · last alerted {{ formatDate(alert.last_fired_at) }}
                            </span>
                        </q-item-label>
                    </q-item-section>
                    <q-item-section side class="row items-center no-wrap q-gutter-x-xs">
                        <q-btn
                            flat
                            dense
                            no-caps
                            size="sm"
                            :icon="ICONS.open_in_new"
                            label="View"
                            @click="openExplorer(alert)"
                        />
                        <q-btn
                            flat
                            dense
                            no-caps
                            size="sm"
                            color="negative"
                            :icon="ICONS.delete"
                            label="Remove"
                            :loading="removing === alert.price_alert_id"
                            @click="onRemove(alert)"
                        />
                    </q-item-section>
                </q-item>
            </q-list>

            <q-card-section
                v-else-if="!loading"
                class="text-center dora-text-muted q-py-lg"
            >
                <q-icon :name="ICONS.notifications" size="40px" />
                <div class="q-mt-sm">No price watches armed.</div>
                <div class="text-caption">
                    Open the price-history explorer and set a "notify below" target to watch a
                    product's price.
                </div>
            </q-card-section>
        </div>
    </q-card>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import { useQuasar } from 'quasar';
    import { onMounted, ref } from 'vue';
    import { useRouter } from 'vue-router';
    import PriceHistoryApiService, { type PriceAlert } from 'src/services/api/priceHistoryApiService';
    import { describeApiError } from 'src/services/errorHandling/apiErrorHandler';

    // C-9.5 — the subscriptions tier on the Alerts hub. Surfaces + manages the
    // user's armed `PriceAlert`s; set-point creation stays on the price-history
    // explorer (R-007 — display/manage only, the scrape/ingestion side fires
    // them). Reuses the existing /price-history/alerts list+delete (R-003 — no
    // duplicate read).
    const $q = useQuasar();
    const router = useRouter();
    const api = new PriceHistoryApiService();

    const items = ref<PriceAlert[]>([]);
    const loading = ref(false);
    const loadError = ref('');
    const removing = ref<string | null>(null);

    function formatDate(iso: string | null): string {
        if (!iso) return '';
        const d = new Date(iso);
        return Number.isFinite(d.getTime()) ? d.toLocaleDateString() : iso;
    }

    async function refresh(): Promise<void> {
        loading.value = true;
        loadError.value = '';
        try {
            items.value = (await api.listAlertsAsync()).items;
        } catch (err) {
            loadError.value = describeApiError(err) || 'Could not load price watches.';
        } finally {
            loading.value = false;
        }
    }

    function openExplorer(alert: PriceAlert): void {
        void router.push({ path: '/price-history', query: { product_id: alert.product_id } });
    }

    async function onRemove(alert: PriceAlert): Promise<void> {
        removing.value = alert.price_alert_id;
        try {
            await api.deleteAlertAsync(alert.price_alert_id);
            items.value = items.value.filter((a) => a.price_alert_id !== alert.price_alert_id);
            $q.notify({ type: 'positive', position: 'bottom-right', message: 'Price watch removed.' });
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Could not remove.',
                caption: describeApiError(err) || '',
            });
        } finally {
            removing.value = null;
        }
    }

    onMounted(refresh);
</script>
