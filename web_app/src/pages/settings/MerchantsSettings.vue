<template>
    <q-card flat bordered>
        <q-card-section class="row items-center q-gutter-sm">
            <div>
                <div class="text-h6">Merchant providers</div>
                <div class="text-caption text-grey">
                    Toggle which supermarkets are searched when you look up products.
                    Disabled merchants are skipped without raising errors.
                </div>
            </div>
            <q-space />
            <q-btn
                color="primary"
                no-caps
                icon="health_and_safety"
                label="Run health check"
                :loading="checking"
                @click="onRunHealthCheck"
            >
                <q-tooltip>Probe each scraper provider once with a sample search</q-tooltip>
            </q-btn>
            <q-btn
                flat
                round
                dense
                icon="refresh"
                :loading="loading"
                @click="loadAll"
            >
                <q-tooltip>Re-fetch merchant + provider state</q-tooltip>
            </q-btn>
        </q-card-section>

        <q-banner v-if="loadError" class="bg-red-1 text-red-9 q-mx-md q-mb-md" dense rounded>
            {{ loadError }}
            <template #action>
                <q-btn flat no-caps label="Retry" @click="loadAll" />
            </template>
        </q-banner>

        <q-separator />

        <!-- API health summary ────────────────────────────────────────── -->
        <q-card-section class="row items-center q-gutter-md">
            <q-chip
                dense
                :color="apiHealthy === true ? 'positive' : apiHealthy === false ? 'negative' : 'grey-5'"
                text-color="white"
                :icon="apiHealthy === true ? 'check_circle' : 'error'"
            >
                Merchant API · {{ apiHealthLabel }}
            </q-chip>
            <span class="text-caption text-grey" v-if="lastCheckedLabel">
                Providers last checked {{ lastCheckedLabel }}
            </span>
        </q-card-section>

        <q-separator />

        <!-- Merchants table ───────────────────────────────────────────── -->
        <q-list separator>
            <q-item v-for="merchant in merchants" :key="merchant.name" class="q-py-md">
                <q-item-section avatar>
                    <q-avatar
                        :color="merchant.is_enabled ? 'amber-3' : 'grey-3'"
                        text-color="grey-10"
                        size="42px"
                    >
                        {{ merchant.name.substring(0, 1).toUpperCase() }}
                    </q-avatar>
                </q-item-section>
                <q-item-section>
                    <q-item-label class="text-weight-medium">{{ merchant.name }}</q-item-label>
                    <q-item-label caption>
                        <ProviderHealthChip
                            v-if="providerForMerchant(merchant.name)"
                            :health="providerForMerchant(merchant.name)!"
                        />
                        <span v-else class="text-grey">
                            No provider reachable for this merchant.
                        </span>
                    </q-item-label>
                </q-item-section>
                <q-item-section side>
                    <q-toggle
                        :model-value="merchant.is_enabled"
                        :disable="togglingMerchant === merchant.name"
                        @update:model-value="onToggle(merchant)"
                    >
                        <template #default>
                            <span class="text-caption text-grey q-ml-sm">
                                {{ merchant.is_enabled ? 'Enabled' : 'Disabled' }}
                            </span>
                        </template>
                    </q-toggle>
                </q-item-section>
            </q-item>

            <q-item v-if="!loading && merchants.length === 0">
                <q-item-section>
                    <q-item-label class="text-grey text-caption">
                        No merchants configured. Make sure the merchant_api is running
                        on port 5172 and accessible from this host.
                    </q-item-label>
                </q-item-section>
            </q-item>
        </q-list>

        <q-inner-loading :showing="loading && merchants.length === 0">
            <q-spinner color="primary" size="48px" />
        </q-inner-loading>

        <!-- Unmatched providers (no merchant by that name) ─────────────── -->
        <q-card-section
            v-if="orphanProviders.length > 0"
            class="q-pt-md"
        >
            <div class="text-subtitle2 q-mb-sm">Other providers</div>
            <div class="text-caption text-grey q-mb-sm">
                Reachable scraper endpoints with no matching configured merchant.
            </div>
            <div class="row q-gutter-sm">
                <q-chip
                    v-for="provider in orphanProviders"
                    :key="provider.base_url"
                    dense
                    :color="provider.is_healthy ? 'positive' : 'negative'"
                    text-color="white"
                >
                    {{ shortHost(provider.base_url) }}
                </q-chip>
            </div>
        </q-card-section>
    </q-card>
</template>

<script lang="ts" setup>
    import { useQuasar } from 'quasar';
    import MerchantManagementApiService, {
        type DataProviderHealth,
        type MerchantConfig
    } from 'src/services/api/merchantManagementApiService';
    import { computed, onMounted, ref } from 'vue';
    import ProviderHealthChip from 'src/components/settings/ProviderHealthChip.vue';

    const $q = useQuasar();
    const service = new MerchantManagementApiService();

    const merchants = ref<MerchantConfig[]>([]);
    const providers = ref<DataProviderHealth[]>([]);
    const apiHealthy = ref<boolean | null>(null);
    const lastChecked = ref<Date | null>(null);

    const loading = ref(false);
    const loadError = ref<string | null>(null);
    const checking = ref(false);
    const togglingMerchant = ref<string | null>(null);

    const apiHealthLabel = computed(() => {
        if (apiHealthy.value === true) return 'reachable';
        if (apiHealthy.value === false) return 'unreachable';
        return 'unknown';
    });

    const lastCheckedLabel = computed(() => {
        if (!lastChecked.value) return null;
        const ago = Date.now() - lastChecked.value.getTime();
        const mins = Math.floor(ago / 60_000);
        if (mins < 1) return 'just now';
        if (mins < 60) return `${mins}m ago`;
        const hours = Math.floor(mins / 60);
        if (hours < 24) return `${hours}h ago`;
        return lastChecked.value.toLocaleString();
    });

    /** Map a merchant name to the provider whose URL "best matches" it. The
     *  merchant_api doesn't return a strict link between providers and
     *  merchants, so we fall back to a substring match on the base URL. */
    function providerForMerchant(merchantName: string): DataProviderHealth | undefined {
        const needle = merchantName.toLowerCase();
        return providers.value.find((p) => p.base_url.toLowerCase().includes(needle));
    }

    const orphanProviders = computed(() => {
        const matched = new Set(
            merchants.value
                .map((m) => providerForMerchant(m.name)?.base_url)
                .filter((u): u is string => !!u)
        );
        return providers.value.filter((p) => !matched.has(p.base_url));
    });

    function shortHost(url: string): string {
        try {
            return new URL(url).host;
        } catch {
            return url;
        }
    }

    async function loadAll() {
        loading.value = true;
        loadError.value = null;
        try {
            // Run in parallel; a failure on the health endpoint shouldn't
            // hide the merchant list, and vice-versa.
            const [merchantsResult, providersResult, healthResult] = await Promise.allSettled([
                service.getMerchantsAsync(),
                service.getDataProvidersHealthAsync(),
                service.getApiHealthAsync()
            ]);

            if (merchantsResult.status === 'fulfilled') {
                merchants.value = merchantsResult.value;
            }
            if (providersResult.status === 'fulfilled') {
                providers.value = providersResult.value;
            }
            apiHealthy.value =
                healthResult.status === 'fulfilled' ? healthResult.value === true : false;

            // If the API was completely unreachable, surface a clear banner.
            if (
                merchantsResult.status === 'rejected' &&
                providersResult.status === 'rejected' &&
                healthResult.status === 'rejected'
            ) {
                loadError.value =
                    'Could not reach the merchant API. Confirm it is running on the configured port.';
                apiHealthy.value = false;
            }
        } finally {
            loading.value = false;
        }
    }

    async function onToggle(merchant: MerchantConfig) {
        togglingMerchant.value = merchant.name;
        const previous = merchant.is_enabled;
        // Optimistic flip — restore on error.
        merchant.is_enabled = !previous;
        try {
            await service.toggleMerchantAsync(merchant.name);
            $q.notify({
                type: 'positive',
                position: 'bottom-right',
                message: `${merchant.name} ${merchant.is_enabled ? 'enabled' : 'disabled'}.`
            });
        } catch (err) {
            merchant.is_enabled = previous;
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: `Could not update ${merchant.name}.`,
                caption: String(err)
            });
        } finally {
            togglingMerchant.value = null;
        }
    }

    async function onRunHealthCheck() {
        checking.value = true;
        try {
            providers.value = await service.runDataProviderHealthCheckAsync();
            lastChecked.value = new Date();
            $q.notify({
                type: 'info',
                position: 'bottom-right',
                message: 'Provider health refreshed.'
            });
        } catch (err) {
            $q.notify({
                type: 'negative',
                position: 'bottom-right',
                message: 'Health check failed.',
                caption: String(err)
            });
        } finally {
            checking.value = false;
        }
    }

    onMounted(loadAll);
</script>
